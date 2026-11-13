from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

import models
from activity import SIGNIN_ACTIONS, now_utc
from auth import get_current_user, is_admin_tier, require_login_inventory_access
from database import get_db

router = APIRouter(prefix="/api/activity", dependencies=[Depends(require_login_inventory_access)])
Log = models.ActivityLog


def scoped(db: Session, user: models.User):
    """Admins see everyone's activity. Other users only see their own."""
    q = db.query(Log)
    return q if is_admin_tier(user) else q.filter(Log.user_id == user.id)


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
    if who and is_admin_tier(user):
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
            "scope": "everyone" if is_admin_tier(user) else "you"}


@router.get("/search-audit")
def search_audit_trail(q: str = "", who: str = "", search_type: str = "all",
                       sort_by: str = "date", sort_dir: str = "desc",
                       page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200),
                       db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Enterprise search audit trail logging and retrieval."""
    import re
    p = int(getattr(page, "default", page) if hasattr(page, "default") else page)
    ps = int(getattr(page_size, "default", page_size) if hasattr(page_size, "default") else page_size)
    query = scoped(db, user)
    # Include search actions or any log with search terms
    query = query.filter(or_(
        Log.action == "search",
        Log.action.ilike("%search%"),
        Log.detail.ilike("%search%"),
        Log.detail.ilike("%lookup%")
    ))
    
    if who and who.strip():
        query = query.filter(Log.user_login == who.strip().lower())

    if search_type and search_type != "all":
        if search_type == "quick":
            query = query.filter(Log.detail.ilike("%Quick Search%"))
        elif search_type == "device":
            query = query.filter(Log.detail.ilike("%Device Search%"))
        elif search_type == "fetch":
            query = query.filter(Log.detail.ilike("%Fetch%"))

    term = q.strip()
    if term:
        like = f"%{escape_like(term)}%"
        query = query.filter(or_(*[c.like(like, escape="\\") for c in (Log.user_login, Log.user_name, Log.detail, Log.ip)]))

    total = query.count()

    if sort_by == "user":
        order_col = Log.user_name if sort_dir == "asc" else Log.user_name.desc()
    elif sort_by == "type":
        order_col = Log.action if sort_dir == "asc" else Log.action.desc()
    else:
        order_col = Log.id.asc() if sort_dir == "asc" else Log.id.desc()

    items = query.order_by(order_col).offset((p - 1) * ps).limit(ps).all()

    def parse_item(r: Log):
        dtl = r.detail or ""
        stype = "Quick Search" if "Quick Search" in dtl else ("Device Search" if "Device Search" in dtl else ("Fetch Search" if "Fetch" in dtl else "Inventory Search"))
        sval = ""
        cust = "All Customers"
        status = "Completed"

        m_q = re.search(r"(?:Search|Term|Value|Searched for):\s*['\"]([^'\"]*)['\"]", dtl, re.IGNORECASE)
        if m_q:
            sval = m_q.group(1)
        elif "'" in dtl:
            m_alt = re.search(r"'([^']*)'", dtl)
            if m_alt:
                sval = m_alt.group(1)
        if not sval:
            sval = dtl

        m_c = re.search(r"Customer:\s*([^,\]]+)", dtl, re.IGNORECASE)
        if m_c:
            cust = m_c.group(1).strip()

        m_res = re.search(r"(?:Results|Matches):\s*(\d+)", dtl, re.IGNORECASE)
        if m_res:
            status = f"{m_res.group(1)} Results"
        elif "No matches" in dtl or "Results: 0" in dtl:
            status = "0 Results"

        return {
            "id": r.id,
            "username": r.user_name or r.user_login or "System User",
            "user_id": r.user_login or "—",
            "search_date": r.created_at.strftime("%Y-%m-%d %H:%M:%S") + " UTC",
            "search_type": stype,
            "search_value": sval,
            "customer_info": cust,
            "result_status": status,
            "detail": dtl,
            "ip": r.ip or "—"
        }

    return {
        "total": total,
        "page": p,
        "page_size": ps,
        "pages": max(1, -(-total // ps)),
        "items": [parse_item(r) for r in items]
    }

