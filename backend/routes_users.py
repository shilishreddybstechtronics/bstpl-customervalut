from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import models, schemas
from activity import log_activity
from auth import (
    ASSIGNABLE_CATEGORIES,
    DEFAULT_PERMISSIONS,
    MASTER_SUPER_ADMIN_IDS,
    MASTER_SUPER_ADMIN_ID,
    MASTER_ADMIN_IDS,
    ADMIN_USER_IDS,
    normalize_id,
    clean_permissions,
    can_manage_privileges,
    role_for_user,
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
    can_priv = False
    pwd = None
    if actor is not None:
        can_del, _ = can_delete_user(actor, u)
        can_mod, _ = can_modify_user(actor, u)
        can_priv, _ = can_manage_privileges(actor, u)
        actor_norm = normalize_id(actor.user_id)
        target_norm = normalize_id(u.user_id)
        actor_cat = get_user_category(actor)["category"]
        target_cat = cat["category"]
        is_actor_super = actor_norm in MASTER_SUPER_ADMIN_IDS or actor_cat == "super_admin"
        is_actor_master = actor_norm in MASTER_ADMIN_IDS or actor_cat in ("master_admin", "super_admin")
        is_target_super = target_norm in MASTER_SUPER_ADMIN_IDS or target_cat == "super_admin"
        if is_actor_super:
            if is_target_super and target_norm != actor_norm:
                # Mutual Super Admin Protection: Super Admins cannot see each other's passwords
                pwd = None
            else:
                # Super Admins can see everybody else's passwords (and their own)
                pwd = u.plain_password
        elif is_actor_master:
            # Master Admins can see everyone's password
            pwd = u.plain_password

    perms_meta = dict(u.permissions or {})
    prev_name = perms_meta.get("previous_name")
    theme_pal = perms_meta.get("theme_palette", "royal_navy")
    theme_md = perms_meta.get("theme_mode", "light")

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
        "can_manage_privileges": can_priv,
        "password": pwd,
        "permissions": get_user_permissions(u),
        "previous_name": prev_name,
        "theme_palette": theme_pal,
        "theme_mode": theme_md,
        "created_at": u.created_at
    }


@router.get("/me")
@router.get("/users/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    """Returns the authenticated user's current profile."""
    return user_out(current_user, actor=current_user)


@router.post("/me/password")
@router.put("/me/password")
@router.post("/me/change-password")
@router.put("/me/change-password")
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
@router.post("/me/name")
@router.put("/users/me")
@router.post("/users/me")
def update_my_name(data: schemas.UserNameUpdate, request: Request, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    """Allows any logged-in employee to edit their own display name."""
    new_name = (data.name or "").strip()
    if not new_name:
        raise HTTPException(400, "Updated name cannot be empty.")

    # Validation: confirm_name must match updated name if provided
    if data.confirm_name is not None and data.confirm_name.strip():
        if data.confirm_name.strip() != new_name:
            raise HTTPException(400, "Updated name and confirm name do not match.")

    # Validation: confirm_current_name must match existing name if provided
    curr_name = (current_user.name or current_user.user_id or "").strip()
    if data.confirm_current_name is not None and data.confirm_current_name.strip():
        entered_confirm = data.confirm_current_name.strip()
        if curr_name and entered_confirm.lower() != curr_name.lower():
            raise HTTPException(400, f"Confirmed current name does not match registered name '{curr_name}'.")

    # Validation: new name must be different from current registered name
    if curr_name and new_name.lower() == curr_name.lower():
        raise HTTPException(400, "Updated name must be different from your current registered name.")

    perms_meta = dict(current_user.permissions or {})
    old_name = current_user.name or current_user.user_id
    perms_meta["previous_name"] = old_name
    current_user.permissions = perms_meta
    current_user.name = new_name

    log_activity(db, "user_update", f"Updated own display name from '{old_name}' to '{new_name}'", user=current_user, request=request)
    db.commit()
    db.refresh(current_user)
    return {
        "ok": True,
        "message": f"Name successfully updated to '{new_name}'.",
        "previous_name": old_name,
        "name": new_name,
        "user": user_out(current_user, actor=current_user)
    }


@router.put("/me/theme")
@router.post("/me/theme")
def update_my_theme(data: schemas.ThemeUpdate, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    """Persists user theme palette and mode preferences to the database."""
    perms = dict(current_user.permissions or {})
    if data.palette:
        perms["theme_palette"] = data.palette
    if data.mode:
        perms["theme_mode"] = data.mode
    current_user.permissions = perms
    db.commit()
    db.refresh(current_user)
    return {
        "ok": True,
        "palette": perms.get("theme_palette", "royal_navy"),
        "mode": perms.get("theme_mode", "light")
    }


@router.get("/me/theme")
def get_my_theme(current_user: models.User = Depends(get_current_user)):
    """Retrieves user theme preferences."""
    perms = dict(current_user.permissions or {})
    return {
        "palette": perms.get("theme_palette", "royal_navy"),
        "mode": perms.get("theme_mode", "light")
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    return [user_out(u, actor=admin) for u in db.query(models.User).order_by(models.User.id)]


@router.post("/users", status_code=201)
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    login_id = data.user_id.strip().lower()
    norm_id = normalize_id(login_id)
    admin_cat = get_user_category(admin)["category"]
    is_admin_super = admin_cat == "super_admin"

    # Only Super Admins and Master Admins can add users
    if admin_cat not in ("super_admin", "master_admin"):
        raise HTTPException(403, "Only Super Admins and Master Admins have permission to add new users.")

    target_role = (data.role or "").strip().lower() or "regular_user"
    if target_role == "super_admin" or norm_id in MASTER_SUPER_ADMIN_IDS or login_id in MASTER_SUPER_ADMIN_IDS:
        raise HTTPException(403, "Super Admin accounts are fixed (IDs 0001 and 0007) and cannot be created here.")
    if target_role not in ASSIGNABLE_CATEGORIES:
        raise HTTPException(400, "Choose Master Admin, Regular Admin or Regular User.")
    if db.query(models.User).filter(models.User.user_id == login_id).first():
        raise HTTPException(400, "This ID is already taken. Choose another one.")

    # Privileges (individual switches) can only be given by a Super Admin
    overrides = {}
    if data.permissions:
        if not is_admin_super:
            raise HTTPException(403, "Only Super Admins can give privileges.")
        try:
            overrides = clean_permissions(data.permissions)
        except ValueError as e:
            raise HTTPException(400, str(e))

    perms = dict(overrides)
    perms["role"] = target_role          # tier defaults apply live; only the switches that differ are stored
    u = models.User(
        name=data.name.strip(),
        user_id=login_id,
        password_hash=hash_password(data.password),
        plain_password=data.password,
        permissions=perms,
    )
    db_role = role_for_user(u)
    set_role(u, db_role)
    db.add(u)
    log_activity(db, "user_create", f"Created {login_id} as {target_role} ({db_role})", user=admin)
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

    # ---- check everything first, change nothing until all checks pass ----
    ok, why = can_modify_user(admin, u)
    if not ok:
        raise HTTPException(403, why)
    wants_privileges = data.permissions is not None or data.category is not None
    if wants_privileges:
        ok, why = can_manage_privileges(admin, u)
        if not ok:
            raise HTTPException(403, why)
    clean = None
    if data.permissions is not None:
        try:
            clean = clean_permissions(data.permissions)
        except ValueError as e:
            raise HTTPException(400, str(e))

    done = []
    if data.name is not None and data.name.strip():
        u.name = data.name.strip()
        done.append(f"renamed to {u.name}")
    if data.password:
        u.password_hash = hash_password(data.password)
        u.plain_password = data.password
        u.token_version = (u.token_version or 0) + 1  # signs that user out everywhere
        done.append("password reset")
        log_activity(db, "user_password_reset", f"Reset password for {u.user_id}", user=admin)
    if clean is not None or data.category is not None:
        merged = dict(u.permissions or {})
        if clean is not None:
            merged.update(clean)
            done.append("permissions updated")
            log_activity(db, "permission_update", f"Updated permissions for {u.user_id}", user=admin)
        if data.category is not None:
            merged["role"] = data.category
            done.append(f"category set to {data.category}")
            log_activity(db, "permission_update", f"Set {u.user_id} to {data.category}", user=admin)
        u.permissions = merged
    new_role = role_for_user(u)           # keep the stored role in step with the tier
    if new_role != u.role:
        set_role(u, new_role)
        done.append(f"role set to {new_role}")
        if data.category is not None:
            u.token_version = (u.token_version or 0) + 1   # re-login so the new tier applies everywhere
    if done:
        log_activity(db, "user_update", f"{u.user_id}: {', '.join(done)}", user=admin)
    db.commit()
    return user_out(u, actor=admin)


@router.put("/users/{uid}/permissions")
def update_permissions(uid: int, data: schemas.PermissionsUpdate, db: Session = Depends(get_db),
                       admin: models.User = Depends(require_admin)):
    """Super Admins give or remove individual privileges."""
    u = db.get(models.User, uid)
    if not u:
        raise HTTPException(404, "User not found.")
    ok, why = can_manage_privileges(admin, u)
    if not ok:
        raise HTTPException(403, why)
    try:
        clean = clean_permissions(data.permissions)
    except ValueError as e:
        raise HTTPException(400, str(e))
    merged = dict(u.permissions or {})
    merged.update(clean)
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

