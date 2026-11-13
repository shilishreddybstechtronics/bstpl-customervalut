"""
CustomerVault Main Application Service (backend/main.py)
Configures FastAPI routes, security middleware, database migrations, and static asset serving.
"""
import json
import os
from pathlib import Path
from datetime import timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, inspect, text, or_
from sqlalchemy.orm import Session

import models, schemas
from activity import check_login_throttle, client_ip, log_activity, now_utc
from auth import (
    MASTER_ID, normalize_id, role_for_row, role_for_user,
    DUMMY_HASH, hash_password, verify_password, create_token, get_current_user
)
from database import engine, get_db
from routes_activity import router as activity_router
from routes_customers import router as customers_router
from routes_data import router as data_router
from routes_users import router as users_router, user_out


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Database Auto-Migration & Schema Upgrade Routine:
# Runs at server startup to verify all tables and columns exist in the active database.
# 1. Inspects existing columns in `users`, `customers`, and `sim_devices`.
# 2. Automatically executes ALTER TABLE statements to add missing columns (e.g. is_admin,
#    token_version, plain_password, permissions, role, deleted_at, avatar, extra fields).
# 3. Ensures master account 0001 and super admin account 0007 exist with proper role permissions.
# 4. Eliminates the need for manual SQL migration scripts when deploying new features.
# ==============================================================================
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
        if "permissions" not in ucols:
            conn.execute(text("ALTER TABLE users ADD COLUMN permissions JSON NULL"))
        if "role" not in ucols:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(10) NOT NULL DEFAULT 'limited'"))
            # Nobody loses access: current admins stay admins, everyone else becomes "standard"
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
        # Tier rules: 0001 & 0007 super admin, 0002-0004 master admin, 0005-0010 admin; anyone created later keeps the
        # category a Super/Master Admin gave them (so an admin created as ID 0011+ is NOT demoted on restart).
        for uid, ident, cur_role, perms in conn.execute(text("SELECT id, user_id, role, permissions FROM users")).all():
            if isinstance(perms, (str, bytes)):
                try:
                    perms = json.loads(perms)
                except Exception:
                    perms = None
            r = role_for_row(ident, cur_role or "", perms)
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


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Avatar Column Sizing:
# Customer logos/avatars are uploaded as Base64 data URIs. This helper executes
# ALTER TABLE to expand the avatar column to MEDIUMTEXT (16MB capacity) so long
# image data strings are stored without truncation errors.
# ==============================================================================
def widen_avatar():
    """Photos are stored as small data-URLs, so the avatar column must be larger than VARCHAR(500)."""
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE customers MODIFY COLUMN avatar MEDIUMTEXT NULL"))
    except Exception as e:
        print(f"Avatar column note: {e}")


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Application Lifespan Context Manager:
# Replaces deprecated FastAPI `on_event("startup")` hooks:
# 1. Triggers metadata table creation (`Base.metadata.create_all`).
# 2. Runs schema auto-migration (`upgrade_database`).
# 3. Ensures column capacities are verified (`widen_avatar`).
# 4. Yields control to serve requests, then cleans up resources on shutdown.
# ==============================================================================
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


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# FastAPI Application Instantiation:
# Initializes the primary FastAPI server with customized title and the lifespan manager.
# ==============================================================================
app = FastAPI(title="CustomerVault API", lifespan=lifespan)


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Cross-Origin Resource Sharing (CORS) Middleware:
# Configures browser access policies:
# Checks the ALLOWED_ORIGINS environment variable (e.g. Netlify, Render domains).
# If specified, allows requests from those origins; otherwise permits all origins (*)
# so development and frontend testing operate without CORS header blocks.
# ==============================================================================
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
        allow_origins=[],
        allow_origin_regex=r".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# HTTP Cache Prevention Middleware:
# Intercepts all outgoing responses and attaches `no-cache, no-store, must-revalidate`
# headers. This prevents browsers from caching dynamic API data or returning stale 304
# responses, ensuring live inventory and user metrics are always up-to-date.
# ==============================================================================
@app.middleware("http")
async def disable_cache_middleware(request: Request, call_next):
    response = await call_next(request)
    # Never return 304 Not Modified; force browser to always receive 200 with fresh content
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# System & Cloud Health Check Endpoints (/health, /healthz, /api/health):
# Dedicated health probes for Render, Netlify reverse proxy, Docker, and uptime monitors.
# Checks active database connectivity and returns a standardized JSON health status.
# ==============================================================================
@app.get("/health")
@app.get("/healthz")
@app.get("/api/health")
def system_health(db: Session = Depends(get_db)):
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        print(f"[Health] DB check notice: {e}")
    return {
        "status": "healthy" if db_connected else "degraded",
        "service": "CustomerVault API",
        "database": "connected" if db_connected else "disconnected",
        "cloud": "Render",
        "timestamp": now_utc().isoformat()
    }


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Database Health Check & Bootstrap Status Endpoint (/health/db):
# Executes a lightweight `SELECT 1` query to verify active connectivity with TiDB/MySQL.
# Checks whether any user accounts exist, signaling to the frontend whether the initial
# master admin registration screen (0001) should be presented.
# ==============================================================================
@app.get("/health/db")
def db_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    # False only on a fresh, empty database: the page then offers the one-time master (0001) setup.
    return {"database": "connected", "master_exists": db.query(models.User).count() > 0}


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Initial Master Registration Endpoint (/auth/register):
# Accessible ONLY ONCE on a clean installation:
# 1. Rejects request with 403 Forbidden if a master account or users already exist.
# 2. Applies IP rate throttling (max 10 attempts per hour).
# 3. Ensures registration is strictly for master account '0001'.
# 4. Hashes password using bcrypt, stores plain password for admin recovery,
#    logs activity audit, and returns an authenticated JWT access token.
# ==============================================================================
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
    return {"access_token": create_token(user), "user": user_out(user, user)}


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# User Authentication / Login Endpoints (/auth/login & /api/auth/login):
# 1. Normalizes user ID (strips whitespace, case-folds).
# 2. Applies brute-force rate limiting via `check_login_throttle` (returns 429 if too many failed attempts).
# 3. Always executes bcrypt verification—even for non-existent users via DUMMY_HASH—to prevent
#    timing side-channel attacks that could reveal valid user IDs.
# 4. Synchronizes role and admin flags in the database if user ID belongs to fixed system tiers.
# 5. Records successful or failed sign-in audit logs.
# 6. Returns a signed JWT token with user permissions and profile metadata.
# ==============================================================================
@app.post("/auth/login", response_model=schemas.TokenOut)
@app.post("/api/auth/login", response_model=schemas.TokenOut)
def login(data: schemas.LoginIn, request: Request, db: Session = Depends(get_db)):
    login_id = data.user_id.strip().lower()
    norm_id = normalize_id(login_id)
    check_login_throttle(db, login_id, client_ip(request))  # 429 after too many recent failures
    user = db.query(models.User).filter(or_(models.User.user_id == login_id, models.User.user_id == norm_id)).first()
    # Always run one bcrypt check, even for an unknown ID, so both cases take the same time.
    password_ok = verify_password(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not password_ok:
        # The reason goes in the log only; the person always sees the same generic message.
        log_activity(db, "login_failed", "Wrong password" if user else "Unknown ID",
                     user=user, login_id=login_id, request=request, commit=True)
        raise HTTPException(status_code=401, detail="ID or password is incorrect.")
    # Keep the stored role in step with the user's tier upon login
    expected_role = role_for_user(user)
    expected_is_admin = (expected_role == "admin")
    if user.role != expected_role or user.is_admin != expected_is_admin:
        user.role = expected_role
        user.is_admin = expected_is_admin
        db.commit()
        db.refresh(user)

    log_activity(db, "login", "Signed in", user=user, request=request, commit=True)
    return {"access_token": create_token(user), "user": user_out(user, user)}


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# User Sign-Out Endpoint (/auth/logout):
# Accepts POST or GET requests to revoke the current session, records the sign-out
# in the activity audit log, and returns an acknowledgment `{"ok": True}`.
# ==============================================================================
@app.post("/auth/logout")
@app.post("/api/auth/logout")
@app.get("/auth/logout")
@app.get("/api/auth/logout")
def logout(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    log_activity(db, "logout", "Signed out", user=current_user, request=request, commit=True)
    return {"ok": True}


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Session Identification Endpoint (/auth/me, /api/auth/me, /me):
# Inspects the Bearer JWT token in the Authorization header via `get_current_user`.
# Returns the authenticated user's profile, role, avatar, and granular permissions.
# ==============================================================================
@app.get("/auth/me", response_model=schemas.UserOut)
@app.get("/api/auth/me", response_model=schemas.UserOut)
@app.get("/me", response_model=schemas.UserOut)
@app.get("/api/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return user_out(current_user, current_user)


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Self-Service Display Name Update (/me/name):
# Delegates to routes_users.update_my_name to allow users to update their own
# profile display name without requiring full administrative privileges.
# ==============================================================================
@app.put("/me/name")
@app.post("/me/name")
@app.put("/api/me/name")
@app.post("/api/me/name")
def update_my_name_root(data: schemas.UserNameUpdate, request: Request, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    from routes_users import update_my_name
    return update_my_name(data, request, db, current_user)


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Self-Service Password Change (/me/password, /me/change-password):
# Delegates to routes_users.change_password: verifies current password, validates
# new password complexity, updates hash & plain password, and increments token version.
# ==============================================================================
@app.post("/me/password")
@app.put("/me/password")
@app.post("/api/me/password")
@app.put("/api/me/password")
@app.post("/me/change-password")
@app.put("/me/change-password")
@app.post("/api/me/change-password")
@app.put("/api/me/change-password")
def change_password_root(data: schemas.PasswordIn, request: Request, db: Session = Depends(get_db),
                         user: models.User = Depends(get_current_user)):
    from routes_users import change_password
    return change_password(data, request, db, user)


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Router Subsystem Registration:
# Mounts modular route collections for:
# - `customers_router`: Customer CRUD, portfolios, documents.
# - `data_router`: Inventory queries, device lookups, Excel ingestion, cart.
# - `users_router`: User accounts, privilege management, password resets.
# - `activity_router`: Audit trail logs and security event telemetry.
# ==============================================================================
app.include_router(customers_router)
app.include_router(data_router)
app.include_router(users_router)
app.include_router(activity_router)

# ==============================================================================
# Sensorise SenseLCM Integration Subsystem:
# Mounts Sensorise API endpoints (/api/sensorise/*) for live SIM queries & telemetry
# ==============================================================================
try:
    from sensorise.main import app as sensorise_app
    app.mount("/sensorise", sensorise_app)
    for r in sensorise_app.routes:
        path = getattr(r, "path", "")
        if path.startswith("/api/sensorise") or path.startswith("/api/sensorise-basic") or path in ("/api/status", "/api/logs/latest"):
            if r not in app.router.routes:
                app.router.routes.append(r)
except Exception as s_mount_err:
    print(f"[Notice] Sensorise routes mount: {s_mount_err}")



# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Deprecated Feature Redirects:
# Clean 301 Permanent Redirects for legacy SIM Upload links to the Home dashboard,
# ensuring users and bookmarks land safely on an active view.
# ==============================================================================
@app.get("/sim-upload.html")
@app.get("/sim-upload")
def redirect_sim_upload():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/home.html", status_code=301)


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Static Frontend Asset Serving:
# Inspects filesystem for the `frontend/` directory (containing HTML, CSS, JS, SVG).
# If found, mounts it as root `/` with `html=True` for single-page and multi-page routing;
# otherwise falls back to a JSON API welcome and health-status response.
# ==============================================================================
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


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Port Conflict Protection Function:
# Iterates socket ports starting from `starting_port` upwards to guarantee an
# unoccupied TCP port is selected when launching the server locally.
# ==============================================================================
def find_available_port(host: str, starting_port: int, max_attempts: int = 20) -> int:
    import socket
    for p in range(starting_port, starting_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, p))
                return p
            except OSError:
                continue
    return starting_port


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Direct Execution Runner:
# When executing `python backend/main.py`:
# Configures host and port, checks port conflicts, and launches Uvicorn.
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    is_cloud = bool(os.environ.get("PORT") or os.environ.get("RENDER"))
    env_port = os.environ.get("PORT")
    host = os.environ.get("HOST", "0.0.0.0" if is_cloud else "127.0.0.1")

    if env_port:
        port = int(env_port)
    else:
        req_port = 8000
        port = find_available_port(host, req_port)
        if port != req_port:
            print(f"\n⚠️  Port {req_port} is already in use by another process.")
            print(f"👉 Automatically switching to free port {port}.")
            print(f"   (To use port {req_port}, stop the other process occupying it)\n")

    browser_host = "localhost" if host == "0.0.0.0" else host
    print(f"Starting CustomerVault on http://{browser_host}:{port} ...")
    uvicorn.run("main:app", host=host, port=port, reload=False)
