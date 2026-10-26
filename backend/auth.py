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


# Used for unknown IDs so a wrong ID takes as long as a wrong password (no timing leak).
DUMMY_HASH = hash_password("not-a-real-password")


def create_token(user: models.User) -> str:
    # Sign-in lasts 12 hours. "tv" must match the user's token_version, so a password change logs out other devices.
    payload = {"sub": str(user.id), "tv": user.token_version or 0,
               "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.User:
    try:
        data = jwt.decode(creds.credentials, SECRET_KEY, algorithms=["HS256"])
        user = db.get(models.User, int(data["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    if not user:
        raise HTTPException(status_code=401, detail="Account not found.")
    if data.get("tv", 0) != (user.token_version or 0):
        raise HTTPException(status_code=401, detail="Your password changed. Please sign in again.")
    return user


def require_role(*allowed: str):
    """Dependency factory: require_role("admin", "standard") lets those roles in and answers 403 to the rest."""
    def check(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Your role does not allow this.")
        return user
    return check


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only an admin can do this.")
    return user


# admin + standard: everything except admin screens. "limited" users cannot delete, restore or manage customers.
require_staff = require_role("admin", "standard")


def normalize_id(user_id: str) -> str:
    clean = (user_id or "").strip().lower()
    return clean.zfill(4) if clean.isdigit() else clean


MASTER_SUPER_ADMIN_ID = "0001"
MASTER_ADMIN_IDS = {"0001", "0002", "0003", "0004"}
ADMIN_USER_IDS = {"0005", "0006", "0007", "0008", "0009", "0010"}
MASTER_ID = MASTER_SUPER_ADMIN_ID  # backwards compatibility


def role_for_id(user_id: str) -> str:
    """Role mapping strictly decided by the ID number:
    - 0001 (Super Admin), 0002, 0003, 0004 (Master Admins): Admin
    - 0005 through 0010 (Admin Users): Admin
    - Other IDs (created after 0010): Limited (Regular Users)
    """
    norm = normalize_id(user_id)
    if norm in MASTER_ADMIN_IDS or norm in ADMIN_USER_IDS:
        return "admin"
    return "limited"


def get_user_category(user_id: str) -> dict:
    """Classifies user ID into their role tier and security category."""
    norm = normalize_id(user_id)
    if norm == MASTER_SUPER_ADMIN_ID:
        return {
            "category": "super_admin",
            "category_label": "Master Admin 0001 — Super Administrator",
            "badge": "👑 Super Admin",
            "is_master": True,
        }
    if norm in MASTER_ADMIN_IDS:
        return {
            "category": "master_admin",
            "category_label": f"Master Admin ({norm})",
            "badge": "⭐ Master Admin",
            "is_master": True,
        }
    if norm in ADMIN_USER_IDS:
        return {
            "category": "admin_user",
            "category_label": f"Admin User ({norm})",
            "badge": "🛡️ Admin User",
            "is_master": False,
        }
    return {
        "category": "regular_user",
        "category_label": f"Regular User ({norm})",
        "badge": "👤 Regular User",
        "is_master": False,
    }


def can_delete_user(actor: models.User, target: models.User) -> tuple[bool, str]:
    """Evaluates whether actor is permitted to delete target user account.
    RBAC Rules:
    1. Actor cannot delete their own account.
    2. Master Admin 0001 is protected and can NEVER be deleted by anyone.
    3. Master Admin 0001 (Super Administrator) has full deletion authority over 0002, 0003, 0004,
       0005-0010, and all regular users.
    4. Master Admins 0002, 0003, and 0004 can delete Admin Users 0005-0010 and regular users,
       but MUST NOT be allowed to delete Master Admin 0001 or one another (accounts 0001-0004).
    5. Admin Users 0005 through 0010 must not have permission to delete any user account.
    6. Regular users created after 0010 must not have permission to delete any user account.
    """
    actor_norm = normalize_id(actor.user_id)
    target_norm = normalize_id(target.user_id)

    # Rule 1: Cannot delete self
    if actor.id == target.id or actor_norm == target_norm:
        return False, "You cannot delete your own account."

    # Rule 2: Master Admin 0001 is permanently protected against deletion
    if target_norm == MASTER_SUPER_ADMIN_ID:
        return False, "Master Admin 0001 (Super Administrator) is protected and can never be deleted by anyone."

    # Rule 3: Master Admin 0001 has full deletion privileges
    if actor_norm == MASTER_SUPER_ADMIN_ID:
        return True, ""

    # Rule 4: Master Admins 0002, 0003, and 0004
    if actor_norm in MASTER_ADMIN_IDS:
        if target_norm in MASTER_ADMIN_IDS:
            return False, "Master Admins 0002, 0003, and 0004 cannot delete one another or Master Admin 0001."
        return True, ""

    # Rule 5: Admin Users 0005 through 0010
    if actor_norm in ADMIN_USER_IDS:
        return False, "Admin users (0005 through 0010) do not have permission to delete any user account."

    # Rule 6: Regular Users (> 0010)
    return False, "Regular users do not have administrative deletion privileges."


def set_role(user: models.User, role: str):
    """Keeps the old is_admin column in sync with the new role."""
    user.role = role
    user.is_admin = role == "admin"

