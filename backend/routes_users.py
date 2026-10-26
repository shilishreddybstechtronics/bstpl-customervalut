from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import models, schemas
from activity import log_activity
from auth import MASTER_ID, normalize_id, role_for_id, create_token, get_current_user, hash_password, require_admin, set_role, verify_password
from database import get_db

router = APIRouter(prefix="/api")


def user_out(u: models.User) -> dict:
    return {"id": u.id, "name": u.name, "user_id": u.user_id, "role": u.role, "is_admin": u.role == "admin",
            "created_at": u.created_at}


@router.post("/me/password")
def change_password(data: schemas.PasswordIn, request: Request, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    if not verify_password(data.current_password, user.password_hash):
        log_activity(db, "password_failed", "Wrong current password", user=user, request=request, commit=True)
        raise HTTPException(400, "Your current password is incorrect.")
    user.password_hash = hash_password(data.new_password)
    user.token_version = (user.token_version or 0) + 1  # every other signed-in device is signed out
    log_activity(db, "password_change", "Changed own password", user=user, request=request)
    db.commit()
    return {"ok": True, "access_token": create_token(user)}  # this device keeps working with a fresh token


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    return [user_out(u) for u in db.query(models.User).order_by(models.User.id)]


@router.post("/users", status_code=201)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    login_id = data.user_id.strip().lower()
    norm_id = normalize_id(login_id)
    if norm_id == MASTER_ID or login_id == MASTER_ID:
        raise HTTPException(400, "Master account (0001) is reserved and cannot be created via user management.")
    if db.query(models.User).filter(models.User.user_id == login_id).first():
        raise HTTPException(400, "This ID is already taken. Choose another one.")
    role = role_for_id(norm_id)  # decided strictly by the ID number
    u = models.User(name=data.name.strip(), user_id=login_id, password_hash=hash_password(data.password))
    set_role(u, role)
    db.add(u)
    log_activity(db, "user_create", f"Created {login_id} as {role}", user=admin)
    db.commit()
    db.refresh(u)
    return user_out(u)


def other_admins(db: Session, uid: int) -> int:
    return db.query(models.User).filter(models.User.role == "admin", models.User.id != uid).count()


@router.put("/users/{uid}")
def update_user(uid: int, data: schemas.UserUpdate, db: Session = Depends(get_db),
                admin: models.User = Depends(require_admin)):
    u = db.get(models.User, uid)
    if not u:
        raise HTTPException(404, "User not found.")
    norm_u = normalize_id(u.user_id)
    norm_admin = normalize_id(admin.user_id)
    if norm_u == MASTER_ID and norm_admin != MASTER_ID:
        raise HTTPException(403, "Only the master account (0001) can modify its own details or password.")
    new_role = role_for_id(u.user_id)  # roles are fixed strictly by ID: 0001-0003 admin, 0004-0010 standard, others limited
    done = []
    if data.name is not None:
        u.name = data.name.strip()
        done.append("renamed")
    if new_role and new_role != u.role:
        set_role(u, new_role)
        done.append(f"role set to {new_role}")
    if data.password:
        u.password_hash = hash_password(data.password)
        u.token_version = (u.token_version or 0) + 1  # signs that user out everywhere
        done.append("password reset")
    if done:
        log_activity(db, "user_update", f"{u.user_id}: {', '.join(done)}", user=admin)
    db.commit()
    return user_out(u)


@router.delete("/users/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    u = db.get(models.User, uid)
    if not u:
        raise HTTPException(404, "User not found.")
    norm_u = normalize_id(u.user_id)
    if norm_u == MASTER_ID or u.user_id == MASTER_ID:
        raise HTTPException(403, "The master account (0001) is protected and can never be deleted by anyone.")
    if u.id == admin.id:
        raise HTTPException(400, "You cannot delete your own account.")
    if u.role == "admin" and other_admins(db, uid) == 0:
        raise HTTPException(400, "There must be at least one admin.")
    # keep their records, just clear who added them
    db.query(models.Device).filter(models.Device.added_by == uid).update({"added_by": None})
    log_activity(db, "user_delete", f"Deleted user {u.user_id}", user=admin)  # their old log rows stay
    db.delete(u)
    db.commit()
    return {"deleted": uid}

