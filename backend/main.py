import os
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import timedelta

from sqlalchemy import func, inspect, text, or_
from sqlalchemy.orm import Session

import models, schemas
from activity import check_login_throttle, client_ip, log_activity, now_utc
from auth import MASTER_ID, normalize_id, role_for_id, DUMMY_HASH, hash_password, verify_password, create_token, get_current_user
from database import engine, get_db
from routes_activity import router as activity_router
from routes_customers import router as customers_router
from routes_data import router as data_router
from routes_users import router as users_router

from contextlib import asynccontextmanager


def upgrade_database():
    """Adds the columns the new features need to tables that already exist, so no manual SQL is required."""
    insp = inspect(engine)
    with engine.begin() as conn:
        ucols = {c["name"] for c in insp.get_columns("users")}
        if "is_admin" not in ucols:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"))
        if "token_version" not in ucols:
            conn.execute(text("ALTER TABLE users ADD COLUMN token_version INT NOT NULL DEFAULT 0"))
        if "plain_password" not in ucols:
            conn.execute(text("ALTER TABLE users ADD COLUMN plain_password VARCHAR(255) NULL"))
        if "role" not in ucols:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(10) NOT NULL DEFAULT 'limited'"))
            # Nobody loses access: current admins stay admins, everyone else becomes "standard" (change it in Manage Users).
            conn.execute(text("UPDATE users SET role = 'admin' WHERE is_admin = TRUE"))
            conn.execute(text("UPDATE users SET role = 'standard' WHERE is_admin = FALSE"))
        ccols = {c["name"] for c in insp.get_columns("customers")}
        if "deleted_at" not in ccols:
            conn.execute(text("ALTER TABLE customers ADD COLUMN deleted_at DATETIME NULL"))
        if "deleted_by" not in ccols:
            conn.execute(text("ALTER TABLE customers ADD COLUMN deleted_by VARCHAR(30) NULL"))
        if "avatar" not in ccols:
            conn.execute(text("ALTER TABLE customers ADD COLUMN avatar MEDIUMTEXT NULL"))
        have = {c["name"] for c in insp.get_columns("sim_devices")}
        for col, ddl in (
            ("dispatched_date", "DATE NULL"),
            ("model", "VARCHAR(100) NULL"),
            ("sim_provider", "VARCHAR(100) NULL"),
            ("activation_plan", "VARCHAR(100) NULL"),
            ("firmware", "VARCHAR(100) NULL"),
            ("flash", "VARCHAR(100) NULL"),
            ("sim_type", "VARCHAR(20) NULL"),
            ("extra", "JSON NULL"),
            ("added_by", "INT NULL"),
            ("deleted_at", "DATETIME NULL"),          # recycle bin
            ("deleted_by", "VARCHAR(30) NULL"),
            ("delete_reason", "VARCHAR(200) NULL"),
        ):
            if col not in have:
                conn.execute(text(f"ALTER TABLE sim_devices ADD COLUMN {col} {ddl}"))
        old_admin = conn.execute(text("SELECT MIN(id) FROM users WHERE is_admin = TRUE")).scalar()
        # Roles strictly follow the ID number: 0001 & 0007 super admin, 0002-0004 master admin, 0005-0010 admin, others limited
        for uid, ident in conn.execute(text("SELECT id, user_id FROM users")).all():
            r = role_for_id(ident)
            conn.execute(text("UPDATE users SET role = :r, is_admin = :a WHERE id = :i"), {"r": r, "a": r == "admin", "i": uid})

        # Ensure user 0007 exists as another master super admin
        u7 = conn.execute(text("SELECT id FROM users WHERE user_id = '0007'")).first()
        if not u7:
            conn.execute(
                text("INSERT INTO users (name, user_id, password_hash, plain_password, is_admin, role, token_version) "
                     "VALUES (:name, :uid, :hash, :plain, TRUE, 'admin', 0)"),
                {
                    "name": "Super Admin 0007",
                    "uid": "0007",
                    "hash": hash_password("Admin@0007"),
                    "plain": "Admin@0007"
                }
            )
            print("NOTICE: Created 0007 as another master super admin with initial password 'Admin@0007'.")
        else:
            conn.execute(text("UPDATE users SET is_admin = TRUE, role = 'admin' WHERE user_id = '0007'"))

        if not conn.execute(text("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1")).first():
            owner = old_admin or conn.execute(text("SELECT MIN(id) FROM users")).scalar()
            taken = conn.execute(text("SELECT 1 FROM users WHERE user_id = :m"), {"m": MASTER_ID}).first()
            if owner and not taken:
                conn.execute(text("UPDATE users SET user_id = :m, role = 'admin', is_admin = TRUE WHERE id = :i"), {"m": MASTER_ID, "i": owner})
                print(f"NOTICE: nobody had an admin ID, so account #{owner} is now the master ID {MASTER_ID} (use it to sign in).")


def widen_avatar():
    """Photos are stored as small data-URLs, so the avatar column must be larger than VARCHAR(500)."""
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE customers MODIFY COLUMN avatar MEDIUMTEXT NULL"))
    except Exception as e:
        print(f"Avatar column note: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform database initialization once upon server startup
    try:
        print("Checking database connection and schema...")
        models.Base.metadata.create_all(bind=engine)
        upgrade_database()
        widen_avatar()
        print("Database connected and schema verified successfully.")
    except Exception as e:
        print(f"Database startup notice: {e}")
    yield


app = FastAPI(title="CustomerVault API", lifespan=lifespan)

# CORS configuration: allows localhost, Render deployment, and custom origins
cors_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
if cors_origins_env:
    allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health/db")
def db_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    # False only on a fresh, empty database: the page then offers the one-time master (0001) setup.
    return {"database": "connected", "master_exists": db.query(models.User).count() > 0}


@app.post("/auth/register", response_model=schemas.TokenOut, status_code=201)
def register(data: schemas.RegisterIn, request: Request, db: Session = Depends(get_db)):
    """One-time master account (0001) setup on a fresh database. Permanently closes once created."""
    master = db.query(models.User).filter(or_(models.User.user_id == MASTER_ID, models.User.user_id == "1")).first()
    if master or db.query(models.User).count() > 0:
        raise HTTPException(status_code=403, detail="Registration is permanently closed. The master account already exists. Please sign in or ask an administrator.")
    ip = client_ip(request)
    since = now_utc() - timedelta(hours=1)
    if ip and db.query(func.count(models.ActivityLog.id)).filter(
            models.ActivityLog.action == "register", models.ActivityLog.ip == ip,
            models.ActivityLog.created_at >= since).scalar() >= 10:
        raise HTTPException(status_code=429, detail="Too many accounts were created from this address. Please try again later.")
    login_id = data.user_id.strip().lower()
    norm_id = normalize_id(login_id)
    if norm_id != MASTER_ID:
        raise HTTPException(status_code=400, detail=f"Initial registration is reserved for master ID {MASTER_ID} only.")
    user = models.User(name=data.name.strip(), user_id=MASTER_ID, password_hash=hash_password(data.password), plain_password=data.password, is_admin=True, role="admin")
    db.add(user)
    db.flush()  # gives the new user an id so the log row can point at it
    log_activity(db, "register", "Master account (0001) created", user=user, request=request)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user), "user": user}


@app.post("/auth/login", response_model=schemas.TokenOut)
def login(data: schemas.LoginIn, request: Request, db: Session = Depends(get_db)):
    login_id = data.user_id.strip().lower()
    norm_id = normalize_id(login_id)
    check_login_throttle(db, login_id, client_ip(request))  # 429 after too many recent failures
    user = db.query(models.User).filter(or_(models.User.user_id == login_id, models.User.user_id == norm_id)).first()
    # Always run one bcrypt check, even for an unknown ID, so both cases take the same time.
    password_ok = verify_password(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not password_ok:
        # The reason goes in the log only; the person always sees the same message.
        log_activity(db, "login_failed", "Wrong password" if user else "Unknown ID",
                     user=user, login_id=login_id, request=request, commit=True)
        raise HTTPException(status_code=401, detail="ID or password is incorrect.")
    log_activity(db, "login", "Signed in", user=user, request=request, commit=True)
    return {"access_token": create_token(user), "user": user}


@app.post("/auth/logout")
def logout(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    log_activity(db, "logout", "Signed out", user=current_user, request=request, commit=True)
    return {"ok": True}


@app.get("/auth/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


app.include_router(customers_router)
app.include_router(data_router)
app.include_router(users_router)
app.include_router(activity_router)


# Serve the website itself (if frontend folder is present)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {
            "status": "online",
            "service": "CustomerVault Backend API",
            "health": "/health/db",
            "docs": "/docs"
        }


if __name__ == "__main__":
    import uvicorn
    is_cloud = bool(os.environ.get("PORT") or os.environ.get("RENDER"))
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0" if is_cloud else "127.0.0.1")
    browser_host = "localhost" if host == "0.0.0.0" else host
    print(f"Starting CustomerVault on http://{browser_host}:{port} ...")
    uvicorn.run("main:app", host=host, port=port, reload=False)


