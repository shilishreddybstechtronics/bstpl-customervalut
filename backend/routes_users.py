from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import models, schemas
from activity import log_activity
from auth import (
    MASTER_SUPER_ADMIN_ID,
    MASTER_ADMIN_IDS,
    ADMIN_USER_IDS,
    normalize_id,
    role_for_id,
    get_user_category,
    can_delete_user,
    create_token,
    get_current_user,
    hash_password,
    require_admin,
    set_role,
    verify_password
)
from database import get_db

router = APIRouter(prefix="/api")


def user_out(u: models.User, actor: Optional[models.User] = None) -> dict:
    cat = get_user_category(u.user_id)
    can_del = False
    if actor is not None:
        can_del, _ = can_delete_user(actor, u)
    return {
        "id": u.id,
        "name": u.name,
        "user_id": u.user_id,
        "role": u.role,
        "is_admin": u.role == "admin",
        "category": cat["category"],
        "category_label": cat["category_label"],
        "badge": cat["badge"],
        "is_master": cat["is_master"],
        "can_delete": can_del,
        "created_at": u.created_at
    }


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
    return [user_out(u, actor=admin) for u in db.query(models.User).order_by(models.User.id)]


@router.post("/users", status_code=201)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    login_id = data.user_id.strip().lower()
    norm_id = normalize_id(login_id)
    norm_admin = normalize_id(admin.user_id)

    if norm_id == MASTER_SUPER_ADMIN_ID or login_id == MASTER_SUPER_ADMIN_ID:
        raise HTTPException(400, "Master account (0001) is reserved and cannot be created via user management.")

    # Only Master Admin 0001 can provision Master Admin accounts (0002–0004)
    if norm_id in MASTER_ADMIN_IDS and norm_admin != MASTER_SUPER_ADMIN_ID:
        raise HTTPException(403, "Only Master Admin 0001 has permission to provision Master Admin accounts (0002–0004).")

    if db.query(models.User).filter(models.User.user_id == login_id).first():
        raise HTTPException(400, "This ID is already taken. Choose another one.")

    role = role_for_id(norm_id)  # decided strictly by the ID number
    u = models.User(name=data.name.strip(), user_id=login_id, password_hash=hash_password(data.password))
    set_role(u, role)
    db.add(u)
    log_activity(db, "user_create", f"Created {login_id} as {role}", user=admin)
    db.commit()
    db.refresh(u)
    return user_out(u, actor=admin)


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

    # Master Admin 0001 can only be modified by 0001
    if norm_u == MASTER_SUPER_ADMIN_ID and norm_admin != MASTER_SUPER_ADMIN_ID:
        raise HTTPException(403, "Only Master Admin 0001 can modify its own details or password.")

    # Admin Users 0005–0010 cannot modify Master Admins (0001–0004)
    if norm_u in MASTER_ADMIN_IDS and norm_admin in ADMIN_USER_IDS:
        raise HTTPException(403, "Admin users (0005–0010) cannot modify Master Admin accounts.")

    # Master Admins 0002–0004 cannot modify one another's accounts (only 0001 or self can)
    if norm_u in MASTER_ADMIN_IDS and norm_admin in MASTER_ADMIN_IDS and norm_admin != MASTER_SUPER_ADMIN_ID and norm_u != norm_admin:
        raise HTTPException(403, "Master Admins 0002–0004 cannot modify one another's accounts.")

    new_role = role_for_id(u.user_id)  # roles are fixed strictly by ID: 0001-0004 admin, 0005-0010 admin, others limited
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
    return user_out(u, actor=admin)


@router.delete("/users/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    u = db.get(models.User, uid)
    if not u:
        raise HTTPException(404, "User not found.")

    allowed, reason = can_delete_user(admin, u)
    if not allowed:
        raise HTTPException(403, reason)

    if u.role == "admin" and other_admins(db, uid) == 0:
        raise HTTPException(400, "There must be at least one admin.")

    # keep their records, just clear who added them
    db.query(models.Device).filter(models.Device.added_by == uid).update({"added_by": None})
    log_activity(db, "user_delete", f"Deleted user {u.user_id}", user=admin)  # their old log rows stay
    db.delete(u)
    db.commit()
    return {"deleted": uid}

