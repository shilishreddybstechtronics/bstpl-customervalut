from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import models, schemas
from activity import log_activity
from auth import (
    DEFAULT_PERMISSIONS,
    MASTER_SUPER_ADMIN_IDS,
    MASTER_SUPER_ADMIN_ID,
    MASTER_ADMIN_IDS,
    ADMIN_USER_IDS,
    normalize_id,
    role_for_id,
    get_user_category,
    get_user_permissions,
    can_delete_user,
    can_modify_user,
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
    cat = get_user_category(u)
    can_del = False
    can_mod = False
    pwd = None
    if actor is not None:
        can_del, _ = can_delete_user(actor, u)
        can_mod, _ = can_modify_user(actor, u)
        actor_norm = normalize_id(actor.user_id)
        target_norm = normalize_id(u.user_id)
        actor_cat = get_user_category(actor)["category"]
        target_cat = cat["category"]
        is_actor_super = actor_norm in MASTER_SUPER_ADMIN_IDS or actor_cat == "super_admin"
        is_target_super = target_norm in MASTER_SUPER_ADMIN_IDS or target_cat == "super_admin"
        if is_actor_super:
            if is_target_super and target_norm != actor_norm:
                # Mutual Super Admin Protection: Super Admins cannot see each other's passwords
                pwd = None
            else:
                # Super Admins can see everybody else's passwords (and their own)
                pwd = u.plain_password
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
        "can_modify": can_mod,
        "password": pwd,
        "permissions": get_user_permissions(u),
        "created_at": u.created_at
    }


@router.post("/me/password")
def change_password(data: schemas.PasswordIn, request: Request, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    """Allows each user to securely change their own password."""
    if not verify_password(data.current_password, user.password_hash):
        log_activity(db, "password_failed", "Wrong current password", user=user, request=request, commit=True)
        raise HTTPException(400, "Your current password is incorrect.")
    user.password_hash = hash_password(data.new_password)
    user.plain_password = data.new_password
    user.token_version = (user.token_version or 0) + 1  # every other signed-in device is signed out
    log_activity(db, "password_change", "Changed own password", user=user, request=request)
    db.commit()
    return {"ok": True, "access_token": create_token(user)}


@router.put("/me/name")
def update_my_name(data: schemas.UserNameUpdate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    """Allows any logged-in employee to edit their own display name."""
    new_name = (data.name or "").strip()
    if not new_name:
        raise HTTPException(400, "Name cannot be empty.")
    current_user.name = new_name
    log_activity(db, "user_update", f"Updated own display name to {new_name}", user=current_user)
    db.commit()
    db.refresh(current_user)
    return {"ok": True, "name": current_user.name, "user": user_out(current_user, actor=current_user)}


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    return [user_out(u, actor=admin) for u in db.query(models.User).order_by(models.User.id)]


@router.post("/users", status_code=201)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    login_id = data.user_id.strip().lower()
    norm_id = normalize_id(login_id)
    norm_admin = normalize_id(admin.user_id)
    admin_cat = get_user_category(admin)["category"]

    is_admin_super = norm_admin in MASTER_SUPER_ADMIN_IDS or admin_cat == "super_admin"
    is_admin_master = norm_admin in MASTER_ADMIN_IDS or admin_cat == "master_admin"

    # Only Super Admins and Master Admins can add users in Manage Users and Permissions
    if not (is_admin_super or is_admin_master):
        raise HTTPException(403, "Only Super Admins and Master Admins have permission to add new users.")

    target_role = (data.role or "").strip().lower() or "master_admin"

    # Master Admins have NO authority to add Super Admin
    if (target_role == "super_admin" or norm_id in MASTER_SUPER_ADMIN_IDS or login_id in MASTER_SUPER_ADMIN_IDS) and not is_admin_super:
        raise HTTPException(403, "Master Admins do not have authority to create Super Admin accounts.")

    if (norm_id in MASTER_SUPER_ADMIN_IDS or login_id in MASTER_SUPER_ADMIN_IDS) and not is_admin_super:
        raise HTTPException(400, "Master Super Admin accounts (0001, 0007) are reserved.")

    if db.query(models.User).filter(models.User.user_id == login_id).first():
        raise HTTPException(400, "This ID is already taken. Choose another one.")

    # Determine assigned category: Default is Master Admin
    if is_admin_super:
        assigned_category = target_role if target_role in ("super_admin", "master_admin", "admin_user", "regular_user") else "master_admin"
    else:
        # Master Admin creating: can create master_admin, admin_user, regular_user
        assigned_category = target_role if target_role in ("master_admin", "admin_user", "regular_user") else "master_admin"

    initial_perms = dict(DEFAULT_PERMISSIONS.get(assigned_category, DEFAULT_PERMISSIONS["master_admin"]))
    if data.permissions and isinstance(data.permissions, dict):
        initial_perms.update(data.permissions)
    initial_perms["role"] = assigned_category

    db_role = "admin" if assigned_category in ("master_admin", "admin_user", "super_admin") else "limited"
    u = models.User(
        name=data.name.strip(),
        user_id=login_id,
        password_hash=hash_password(data.password),
        plain_password=data.password,
        permissions=initial_perms
    )
    set_role(u, db_role)
    db.add(u)
    log_activity(db, "user_create", f"Created {login_id} as {assigned_category} ({db_role})", user=admin)
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

    # Mutual Super Admin Protection: Super Admins CANNOT modify each other
    if norm_u in MASTER_SUPER_ADMIN_IDS and norm_u != norm_admin:
        raise HTTPException(403, f"Super Admin {norm_u} is protected and cannot be modified by another Super Admin or user.")

    # Master Admins cannot be modified by Admin Users
    if norm_u in MASTER_ADMIN_IDS and norm_admin in ADMIN_USER_IDS:
        raise HTTPException(403, "Admin users cannot modify Master Admin accounts.")

    # Master Admins cannot modify one another's accounts (only super admins or self can)
    if norm_u in MASTER_ADMIN_IDS and norm_admin in MASTER_ADMIN_IDS and norm_admin not in MASTER_SUPER_ADMIN_IDS and norm_u != norm_admin:
        raise HTTPException(403, "Master Admins cannot modify one another's accounts.")

    new_role = role_for_id(u.user_id)
    done = []
    if data.name is not None and data.name.strip():
        u.name = data.name.strip()
        done.append(f"renamed to {u.name}")
    if new_role and new_role != u.role:
        set_role(u, new_role)
        done.append(f"role set to {new_role}")
    if data.password:
        # Super Admins can reset ordinary users' passwords
        u.password_hash = hash_password(data.password)
        u.plain_password = data.password
        u.token_version = (u.token_version or 0) + 1  # signs that user out everywhere
        done.append("password reset")
        log_activity(db, "user_password_reset", f"Reset password for {u.user_id}", user=admin)
    if data.permissions is not None:
        if norm_admin not in MASTER_SUPER_ADMIN_IDS:
            raise HTTPException(403, "Only Super Admins can configure permissions.")
        merged = dict(u.permissions or {})
        merged.update(data.permissions)
        u.permissions = merged
        done.append("permissions updated")
        log_activity(db, "permission_update", f"Updated permissions for {u.user_id}", user=admin)
    if done:
        log_activity(db, "user_update", f"{u.user_id}: {', '.join(done)}", user=admin)
    db.commit()
    return user_out(u, actor=admin)


@router.put("/users/{uid}/permissions")
def update_permissions(uid: int, data: schemas.PermissionsUpdate, db: Session = Depends(get_db),
                       admin: models.User = Depends(require_admin)):
    """Super Admins can grant or revoke granular permissions for individual users."""
    norm_admin = normalize_id(admin.user_id)
    if norm_admin not in MASTER_SUPER_ADMIN_IDS:
        raise HTTPException(403, "Only Super Admins (0001, 0007) have permission to configure user permissions.")

    u = db.get(models.User, uid)
    if not u:
        raise HTTPException(404, "User not found.")

    norm_u = normalize_id(u.user_id)
    if norm_u in MASTER_SUPER_ADMIN_IDS:
        raise HTTPException(403, "Permissions of a Super Admin are fixed and cannot be modified.")

    merged = dict(u.permissions or {})
    merged.update(data.permissions)
    u.permissions = merged
    log_activity(db, "permission_update", f"Updated permissions for {u.user_id}", user=admin)
    db.commit()
    db.refresh(u)
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
    log_activity(db, "user_delete", f"Deleted user {u.user_id}", user=admin)
    db.delete(u)
    db.commit()
    return {"deleted": uid}

