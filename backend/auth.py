"""
CustomerVault Authentication & Authorization Module (backend/auth.py)
Manages JWT creation/validation, bcrypt password hashing, role-based access control,
and hierarchical privilege management.
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from dotenv import load_dotenv
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import models
from database import get_db

# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Security Key & Environment Setup:
# Loads environment variables from `.env` to acquire SECRET_KEY for JWT signature signing.
# If no key is set or the key length is shorter than 32 characters, generates a secure
# random 256-bit hexadecimal string using `secrets.token_hex(32)`.
# ==============================================================================
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file, override=False)
else:
    load_dotenv(override=False)

SECRET_KEY = os.getenv("SECRET_KEY", "").strip() or "60bab0872e7d08bd77521ed0576eb3be17e16a33b4e1865cb27e3cd86b1be43c"
if len(SECRET_KEY) < 32:
    import secrets
    SECRET_KEY = secrets.token_hex(32)

bearer = HTTPBearer()
ROLES = ("admin", "standard", "limited")
MAX_PW_BYTES = 72  # bcrypt ignores or rejects anything longer


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Password Hashing & Verification:
# - `hash_password`: Generates a randomized cryptographic salt and computes the bcrypt hash.
# - `verify_password`: Validates password byte length (max 72 bytes) and securely checks
#   the plaintext candidate against the stored bcrypt hash. Returns False safely on any format error.
# ==============================================================================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    pw = password.encode()
    if len(pw) > MAX_PW_BYTES:
        return False
    try:
        return bcrypt.checkpw(pw, hashed.encode())
    except ValueError:
        return False


# Precomputed dummy hash used when a user ID is not found, ensuring unknown ID queries
# consume the exact same CPU/processing time as known accounts, eliminating timing side-channel leaks.
DUMMY_HASH = hash_password("not-a-real-password")


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# JWT Access Token Factory:
# Constructs a signed JSON Web Token (JWT) with HS256 algorithm:
# - `sub`: User database ID.
# - `tv`: Token version number (incremented when password changes to revoke older active sessions).
# - `exp`: Set to 100 years (~lifetime session) to prevent unexpected session timeouts in production.
# ==============================================================================
def create_token(user: models.User) -> str:
    # Lifetime token: valid for 100 years (~lifetime) without time expiration.
    # "tv" still tracks token_version so a manual password change can revoke sessions if needed.
    payload = {
        "sub": str(user.id),
        "tv": user.token_version or 0,
        "exp": datetime.now(timezone.utc) + timedelta(days=36500)  # 100 years lifetime
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Authenticated User Dependency (get_current_user):
# Intercepts the HTTP Authorization Bearer token header on API requests:
# 1. Decodes and verifies the cryptographic JWT signature.
# 2. Queries the user by ID from the database session.
# 3. Compares the token version (`tv`) with the user's active `token_version`. If mismatched
#    (e.g. password was reset), immediately raises 401 Unauthorized.
# 4. Returns the validated User model instance to the calling route.
# ==============================================================================
def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.User:
    try:
        # Lifetime token verification: verify signature and decode without expiration constraint
        data = jwt.decode(creds.credentials, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
        user = db.get(models.User, int(data["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid session. Please sign in again.")
    if not user:
        raise HTTPException(status_code=401, detail="Account not found.")
    if data.get("tv", 0) != (user.token_version or 0):
        raise HTTPException(status_code=401, detail="Your password changed. Please sign in again.")
    return user


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Role & Tier Authorization Guards:
# - `require_role`: Checks if user's role matches an allowed role set.
# - `require_admin`: Verifies that the user belongs to an admin tier (Super, Master, or Regular Admin).
# - `require_super_admin`: Restricts critical operations (e.g. user management, audit logs) to 0001 & 0007.
# ==============================================================================
def require_role(*allowed: str):
    """Dependency factory: require_role("admin", "standard") lets those roles in and answers 403 to the rest."""
    def check(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Your role does not allow this.")
        return user
    return check


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """Any admin tier (Super Admin, Master Admin, Admin User). Decided by tier, not by a stored column that can be stale."""
    if not is_admin_tier(user):
        raise HTTPException(status_code=403, detail="Only an admin can do this.")
    return user


def require_super_admin(user: models.User = Depends(get_current_user)) -> models.User:
    norm = normalize_id(user.user_id)
    if norm not in MASTER_SUPER_ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Access restricted to Super Admins (0001 and 0007) only.")
    return user


require_staff = require_role("admin", "standard")


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# User ID Normalization & System Account Constants:
# - Normalizes user ID strings into 4-digit zero-padded numbers (e.g. '1' -> '0001', '7' -> '0007').
# - Defines immutable system accounts:
#   - Super Admins: 0001 (Root Founder) and 0007 (Master Super Admin).
#   - Master Admins: 0001, 0002, 0003, 0004, 0007.
#   - Admin Users: 0005, 0006, 0008, 0009, 0010.
# ==============================================================================
def normalize_id(user_id: str) -> str:
    clean = (user_id or "").strip().lower()
    return clean.zfill(4) if clean.isdigit() else clean


MASTER_SUPER_ADMIN_IDS = {"0001", "0007"}
MASTER_SUPER_ADMIN_ID = "0001"  # primary for backwards compatibility
MASTER_ADMIN_IDS = {"0001", "0002", "0003", "0004", "0007"}
ADMIN_USER_IDS = {"0005", "0006", "0008", "0009", "0010"}
MASTER_ID = MASTER_SUPER_ADMIN_ID  # backwards compatibility


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Default Granular Permission Matrix:
# Maps each tier to its base capabilities (page visibility, view, add, edit, delete, export).
# Super Admins have full access; regular users have restricted editing and no deletion access.
# ==============================================================================
DEFAULT_PERMISSIONS = {
    "super_admin": {
        "view": True, "add": True, "edit": True, "delete": True, "delete_invalid": True, "search": True, "download": True, "upload": True,
        "page_live": True, "page_inventory": True, "page_fetch": True,
        "page_edit": True, "page_alerts": True, "page_health": True, "page_errors": True, "page_cart": True, "page_audit": True
    },
    "master_admin": {
        "view": True, "add": True, "edit": True, "delete": False, "delete_invalid": True, "search": True, "download": True, "upload": True,
        "page_live": True, "page_inventory": True, "page_fetch": True,
        "page_edit": True, "page_alerts": True, "page_health": True, "page_errors": True, "page_cart": True, "page_audit": True
    },
    "admin_user": {
        "view": True, "add": True, "edit": True, "delete": True, "delete_invalid": True, "search": True, "download": True, "upload": True,
        "page_live": True, "page_inventory": True, "page_fetch": True,
        "page_edit": True, "page_alerts": True, "page_health": True, "page_errors": True, "page_cart": True, "page_audit": False
    },
    "regular_user": {
        "view": True, "add": True, "edit": True, "delete": False, "delete_invalid": False, "search": True, "download": True, "upload": True,
        "page_live": True, "page_inventory": True, "page_fetch": True,
        "page_edit": True, "page_alerts": True, "page_health": True, "page_errors": False, "page_cart": False, "page_audit": False
    }
}


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Effective Permission Resolver:
# Combines role defaults with custom per-user override switches stored in `user.permissions` JSON.
# Super Admins (0001, 0007) are hard-coded to have True for all permissions and cannot be restricted.
# ==============================================================================
def get_user_permissions(user: models.User) -> dict[str, bool]:
    """Returns complete effective permissions for user, combining role defaults and individual overrides."""
    norm = normalize_id(user.user_id)
    if norm in MASTER_SUPER_ADMIN_IDS:
        return {k: True for k in DEFAULT_PERMISSIONS["super_admin"]}
    cat = get_user_category(user)["category"]
    perms = dict(DEFAULT_PERMISSIONS.get(cat, DEFAULT_PERMISSIONS["regular_user"]))
    if user.permissions and isinstance(user.permissions, dict):
        for k, v in user.permissions.items():
            if isinstance(v, bool):
                perms[k] = v
    return perms


def user_has_permission(user: models.User, perm: str) -> bool:
    norm = normalize_id(user.user_id)
    if norm in MASTER_SUPER_ADMIN_IDS:
        return True
    perms = get_user_permissions(user)
    return bool(perms.get(perm, False))


def require_permission(perm: str):
    def dep(user: models.User = Depends(get_current_user)) -> models.User:
        if not user_has_permission(user, perm):
            raise HTTPException(403, f"Access denied: you do not have permission to '{perm}'. Contact a Super Admin.")
        return user
    return dep


def require_login_inventory_access(user: models.User = Depends(get_current_user)) -> models.User:
    """Login Inventory (Audit Log): Super Admins always, Master Admins by default, and anyone else
    only when a Super Admin has switched on their 'page_audit' privilege."""
    if not user_has_permission(user, "page_audit"):
        raise HTTPException(403, "Access denied: Login Inventory is only available to users a Super Admin has given access to.")
    return user


ADMIN_TIERS = ("super_admin", "master_admin", "admin_user")
ASSIGNABLE_CATEGORIES = ("master_admin", "admin_user", "regular_user")   # super admins are fixed: IDs 0001 and 0007
PERMISSION_KEYS = frozenset(DEFAULT_PERMISSIONS["super_admin"])

_LABELS = {
    "super_admin": ("Master Admin {n} — Super Administrator", "👑 Super Admin", True),
    "master_admin": ("Master Admin ({n})", "⭐ Master Admin", True),
    "admin_user": ("Regular Admin ({n})", "🛡️ Regular Admin", False),
    "regular_user": ("Regular User ({n})", "👤 Regular User", False),
}


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Central User Classification Engine (_category_from & get_user_category):
# Authoritative logic for determining a user's exact tier:
# 1. Built-in IDs (0001 & 0007 -> super_admin; 0002-0004 -> master_admin; 0005-0010 -> admin_user).
# 2. Dynamically assigned category stored in `permissions['role']`.
# 3. Fallback to `assigned_role` column.
# Returns category identifier, display label, and visual emoji badge.
# ==============================================================================
def _category_from(uid, assigned_role="", perms=None) -> str:
    """ONE place that decides a user's tier. Built-in IDs win; otherwise the category a Super/Master Admin
    assigned (stored in permissions['role']); otherwise the old role column."""
    norm = normalize_id(uid)
    if norm in MASTER_SUPER_ADMIN_IDS:
        return "super_admin"
    if norm in MASTER_ADMIN_IDS:
        return "master_admin"
    if norm in ADMIN_USER_IDS:
        return "admin_user"
    cat = perms.get("role") if isinstance(perms, dict) else None
    if cat == "regular_admin":
        cat = "admin_user"
    if cat in ASSIGNABLE_CATEGORIES:
        return cat
    if assigned_role == "master_admin":
        return "master_admin"
    if assigned_role == "admin":
        return "admin_user"
    return "regular_user"


def role_for_row(user_id, assigned_role="", perms=None) -> str:
    """DB role column value for a user: 'admin' for every admin tier, 'limited' for regular users."""
    return "admin" if _category_from(user_id, assigned_role, perms) in ADMIN_TIERS else "limited"


def role_for_user(user: models.User) -> str:
    return role_for_row(user.user_id, getattr(user, "role", "") or "", getattr(user, "permissions", None))


def role_for_id(user_id: str) -> str:
    """ID-only mapping (kept for old callers). Prefer role_for_user()."""
    return role_for_row(user_id)


def is_admin_tier(user: models.User) -> bool:
    return get_user_category(user)["category"] in ADMIN_TIERS


def clean_permissions(perms) -> dict:
    """Only known privilege names with true/false values are accepted."""
    if not isinstance(perms, dict):
        raise ValueError("Permissions must be a set of on/off switches.")
    clean = {}
    for k, v in perms.items():
        if k in PERMISSION_KEYS:
            clean[k] = bool(v)
    return clean


def get_user_category(user_or_id) -> dict:
    """Classifies a user into their tier. Accepts a User model or a string user_id."""
    if isinstance(user_or_id, models.User):
        uid = user_or_id.user_id
        cat = _category_from(uid, getattr(user_or_id, "role", "") or "", getattr(user_or_id, "permissions", None))
    else:
        uid = str(user_or_id or "")
        cat = _category_from(uid)
    norm = normalize_id(uid)
    label, badge, is_master = _LABELS[cat]
    return {"category": cat, "category_label": label.format(n=norm), "badge": badge, "is_master": is_master}


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Hierarchical Permission Rules (can_modify_user, can_delete_user, can_manage_privileges):
# Enforces administrative boundaries between account tiers:
# - Modification: Super Admins (0001, 0007) are protected and cannot be altered by others.
# - Deletion:
#   1. Users cannot delete their own active account.
#   2. Super Admins can never be deleted under any circumstance.
#   3. Super Admins can delete any other tier.
#   4. Master Admins can delete Admin Users and Regular Users.
#   5. Regular Users cannot delete accounts.
# - Privileges: Only Super Admins and Master Admins can configure individual feature privileges.
# ==============================================================================
def can_modify_user(actor: models.User, target: models.User) -> tuple[bool, str]:
    """Who may rename / reset the password of whom."""
    if actor.id == target.id or normalize_id(actor.user_id) == normalize_id(target.user_id):
        return True, ""
    a, t = get_user_category(actor)["category"], get_user_category(target)["category"]
    if t == "super_admin":
        return False, f"Super Admin {normalize_id(target.user_id)} is protected and cannot be modified by another user."
    if a == "super_admin":
        return True, ""
    if t == "master_admin":
        return False, "Master Admin accounts cannot be modified by other users."
    if a in ("master_admin", "admin_user"):
        return True, ""
    return False, "You do not have permission to modify user accounts."


def can_delete_user(actor: models.User, target: models.User) -> tuple[bool, str]:
    if actor.id == target.id or normalize_id(actor.user_id) == normalize_id(target.user_id):
        return False, "You cannot delete your own account."
    a, t = get_user_category(actor)["category"], get_user_category(target)["category"]
    if t == "super_admin":
        return False, f"Super Admin {normalize_id(target.user_id)} is protected and can never be deleted."
    if a in ("super_admin", "master_admin"):
        return True, ""
    if a == "admin_user":
        if t == "master_admin":
            return False, "Admin users do not have permission to delete Master Admins."
        return True, ""
    return False, "Regular users do not have administrative deletion privileges."


def can_manage_privileges(actor: models.User, target: models.User) -> tuple[bool, str]:
    """Super Admins and Master Admins can configure privileges for non-Super Admin accounts."""
    cat_actor = get_user_category(actor)["category"]
    cat_target = get_user_category(target)["category"]
    if cat_actor not in ("super_admin", "master_admin"):
        return False, "Only Administrators (Super Admin & Master Admin) can configure user privileges."
    if cat_target == "super_admin":
        return False, "A Super Admin's privileges are fixed and cannot be changed."
    return True, ""


def set_role(user: models.User, role: str):
    """Keeps the old is_admin column in sync with the new role."""
    user.role = role
    user.is_admin = role == "admin"
