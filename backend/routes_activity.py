from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
from activity import SIGNIN_ACTIONS, now_utc
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api/activity", dependencies=[Depends(get_current_user)])
Log = models.ActivityLog


def scoped(db: Session, user: models.User):
    """Admins see everyone's activity. Other users only see their own."""
    q = db.query(Log)
    return q if user.role == "admin" else q.filter(Log.user_id == user.id)


def escape_like(s: str) -> str:
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def row(r: Log) -> dict:
    return {"id": r.id, "user_login": r.user_login, "user_name": r.user_name, "action": r.action,
            "detail": r.detail, "ip": r.ip, "created_at": r.created_at.isoformat() + "Z"}  # stored in UTC


@router.get("")
def list_activity(kind: str = "all", who: str = "", q: str = "",
                  page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
                  db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    query = scoped(db, user)
    if who and user.role == "admin":
        query = query.filter(Log.user_login == who.strip().lower())
    if kind == "signins":
        query = query.filter(Log.action.in_(SIGNIN_ACTIONS))
    elif kind == "failed":
        query = query.filter(Log.action == "login_failed")
    elif kind == "changes":
        query = query.filter(Log.action.notin_(SIGNIN_ACTIONS))
    q = q.strip()
    if q:
        like = f"%{escape_like(q)}%"
        query = query.filter(or_(*[c.like(like, escape="\\") for c in (Log.user_login, Log.user_name, Log.detail, Log.ip, Log.action)]))
    total = query.count()
    items = query.order_by(Log.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size,
            "pages": max(1, -(-total // page_size)), "items": [row(r) for r in items]}


@router.get("/summary")
def summary(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    since = now_utc() - timedelta(hours=24)
    base = scoped(db, user).filter(Log.created_at >= since)
    count = lambda *f: base.filter(*f).count()
    # the sign-in BEFORE the current one (the current session's own sign-in is the newest)
    logins = (db.query(Log.created_at).filter(Log.user_id == user.id, Log.action == "login")
              .order_by(Log.id.desc()).limit(2).all())
    prev: Optional[object] = logins[1][0] if len(logins) > 1 else None
    return {"signins_24h": count(Log.action == "login"),
            "failed_24h": count(Log.action == "login_failed"),
            "changes_24h": count(Log.action.notin_(SIGNIN_ACTIONS)),
            "active_users_24h": base.filter(Log.action == "login").with_entities(func.count(func.distinct(Log.user_login))).scalar(),
            "last_login": prev.isoformat() + "Z" if prev else None,
            "scope": "everyone" if user.role == "admin" else "you"}
