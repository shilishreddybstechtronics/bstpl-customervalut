"""Activity log: who signed in, and what they changed. Written in the same transaction as the change itself."""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

import models

SIGNIN_ACTIONS = ("login", "login_failed", "logout", "register")

# Login throttling: too many failures in the window and further attempts are refused for a while.
THROTTLE_WINDOW = timedelta(minutes=5)
MAX_FAILS_PER_ID = 8
MAX_FAILS_PER_IP = 30  # higher, because an office can share one address


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def client_ip(request: Optional[Request]) -> str:
    """The caller's address. Set TRUST_PROXY=true in .env ONLY when the site runs behind your own reverse proxy."""
    if not request:
        return ""
    if os.getenv("TRUST_PROXY", "false").lower() == "true":
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[-1].strip()[:45]  # last entry = the one our proxy added (the first can be faked)
    return (request.client.host if request.client else "")[:45]


def check_login_throttle(db: Session, login_id: str, ip: str):
    since = now_utc() - THROTTLE_WINDOW
    L = models.ActivityLog
    fails = db.query(func.count(L.id)).filter(L.action == "login_failed", L.created_at >= since)
    by_id = fails.filter(L.user_login == login_id[:30]).scalar() or 0
    by_ip = fails.filter(L.ip == ip).scalar() or 0 if ip else 0
    if by_id >= MAX_FAILS_PER_ID or by_ip >= MAX_FAILS_PER_IP:
        raise HTTPException(status_code=429, detail="Too many failed sign-in attempts. Please wait a few minutes and try again.")


def log_activity(db: Session, action: str, detail: str = "", user: Optional[models.User] = None,
                 login_id: str = "", request: Optional[Request] = None, commit: bool = False):
    """Adds a log row. Call it BEFORE the caller's db.commit(), or pass commit=True."""
    db.add(models.ActivityLog(
        user_id=user.id if user else None,
        user_login=((user.user_id if user else login_id) or "")[:30],
        user_name=((user.name if user else "") or "")[:100],
        action=action,
        detail=(detail or "")[:500],
        ip=client_ip(request),
        created_at=now_utc(),
    ))
    if commit:
        db.commit()
