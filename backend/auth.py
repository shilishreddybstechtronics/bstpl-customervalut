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

# No fallback on purpose: a key that lives in the source code is a key everybody knows.
SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY is missing or too short. Add a line like SECRET_KEY=<64 random characters> to your .env file.\n"
        "Make one with:  python -c \"import secrets; print(secrets.token_hex(32))\""
    )

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


MASTER_ID = "0001"  # the master account: created once, can never be deleted or demoted


def role_for_id(user_id: str) -> str:
    """Role mapping strictly decided by the ID number:
    - 0001 (master), 0002, 0003: Admin (full access to everything)
    - 0004 to 0010: Standard (full access except customer deletion)
    - Other IDs: Limited (fetch data, edit data, add data, customer icons/photos, alerts)
    """
    norm = normalize_id(user_id)
    if norm in ("0001", "0002", "0003"):
        return "admin"
    if norm in ("0004", "0005", "0006", "0007", "0008", "0009", "0010"):
        return "standard"
    return "limited"


def set_role(user: models.User, role: str):
    """Keeps the old is_admin column in sync with the new role."""
    user.role = role
    user.is_admin = role == "admin"

