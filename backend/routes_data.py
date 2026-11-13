import io
import re
import math
import time
import uuid
from datetime import date, datetime, timedelta
from typing import Optional, Literal
from pydantic import BaseModel, field_validator

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import String, case, cast, func, insert, or_, and_, desc, asc, text, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, joinedload

import customer_tables
import models, schemas
try:
    from sensorise_sync import sync_devices_with_sensorise, sync_device_dicts_with_sensorise
except ImportError:
    try:
        from backend.sensorise_sync import sync_devices_with_sensorise, sync_device_dicts_with_sensorise
    except ImportError:
        sync_devices_with_sensorise = lambda db, devs: devs
        sync_device_dicts_with_sensorise = lambda db, recs: recs

from activity import log_activity
from auth import get_current_user, require_admin, require_staff, require_permission, get_user_permissions
from database import get_db, SessionLocal

# Every route here needs a signed-in user.
router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])

Device, Customer = models.Device, models.Customer
ACTIVE = Device.deleted_at.is_(None)
BASE_COLUMNS = ["customer_name", "device_sr_no", "imei", "iccid", "msisdn1", "msisdn2", "act_date", "expiry_date",
                "dispatched_date", "model", "sim_provider", "activation_plan", "firmware", "flash", "sim_type"]
# Plain-text device fields that can be copied straight from an upload / edit form
TEXT_FIELDS = ["device_sr_no", "iccid", "msisdn1", "msisdn2", "model", "sim_provider", "activation_plan",
               "firmware", "flash"]

FIELD_MAX_LEN = {
    "imei": 20,
    "device_sr_no": 50,
    "iccid": 30,
    "msisdn1": 20,
    "msisdn2": 20,
    "model": 100,
    "sim_provider": 100,
    "activation_plan": 100,
    "firmware": 100,
    "flash": 100,
    "sim_type": 20,
    "customer_name": 150
}


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# String & Identifier Sanitization Helpers:
# - clean_str: Strips leading/trailing whitespace and converts empty strings to None.
# - clean_iccid: Normalizes SIM ICCID strings (removes scientific notation e.g. 8.6E+14,
#   strips trailing .0, removes hyphens/spaces, and converts to uppercase).
# - iccid_key: Strict exact comparison key for duplicate checks (preserves trailing 'F').
# - escape_like: Escapes SQL wildcard characters (% and _) to perform safe literal LIKE queries.
# - classify_sim_type: Automatically categorizes a device as 'E-SIM' if it has an ICCID,
#   or 'Plastic SIM' if no electronic ICCID is present.
# ==============================================================================
def clean_str(val) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s if s != "" else None


def clean_iccid(val: Optional[str]) -> str:
    if not val:
        return ""
    s = str(val).strip()
    if re.search(r"e\+", s, re.I):
        try:
            s = str(int(float(s)))
        except Exception:
            pass
    if s.endswith(".0"):
        s = s[:-2]
    s = re.sub(r"[\s\-_]+", "", s)
    return s.strip().upper()


def iccid_key(val) -> str:
    """The ONE definition of 'same ICCID/CCID' for every duplicate check (in-file, database, update, conflict).
    The WHOLE value is compared, character by character. Only blanks around the value and upper/lower case are
    ignored. There is NO prefix, suffix, substring, word or similarity matching, and the trailing F is part of the
    number: 8991200050054843292F and 8991200050054843250F are different ICCIDs."""
    return str(val or "").strip().lower()


def normalize_date_input(val):
    return schemas._to_date(val)


def escape_like(s: str) -> str:
    """So a search for 50% or a_b means those exact characters, not wildcards."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def classify_sim_type(iccid: Optional[str]) -> str:
    if iccid and str(iccid).strip():
        return "E-SIM"
    return "Plastic SIM"


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Dynamic Column Schema Registry:
# Dynamically discovers custom column names uploaded by customers and persists them
# into `column_registry`. This allows customer-specific metadata fields to appear
# dynamically across column pickers, export dialogs, and search dropdowns.
# ==============================================================================
def register_columns(db: Session, names):
    known = {n for (n,) in db.query(models.ColumnRegistry.name)}
    for n in set(names) - known:
        db.add(models.ColumnRegistry(name=n))


def clean_extra(extra):
    # keep it small and safe: short names, string values, no clash with built-in columns
    out = {}
    for k, v in (extra or {}).items():
        if v is None:
            continue
        k = str(k).strip()[:100]
        if k and k.lower().replace(' ', '_') not in BASE_COLUMNS and len(out) < 100:
            out[k] = str(v).strip()[:500]
    return out


def merge_extra(old, new):
    """Edit form: a filled value sets the column, a blank one clears it."""
    merged = dict(old or {})
    for k, v in (new or {}).items():
        k = str(k).strip()[:100]
        if not k or k.lower().replace(' ', '_') in BASE_COLUMNS:
            continue
        if v is None or str(v).strip() == "":
            merged.pop(k, None)
        else:
            merged[k] = str(v).strip()[:500]
    return merged


def compute_expiry_status(exp_date: Optional[date], window_days: int = 30) -> str:
    if not exp_date:
        return "Unknown"
    today = date.today()
    if exp_date < today:
        return "Expired"
    elif exp_date <= today + timedelta(days=window_days):
        return "Expiring Soon"
    else:
        return "Active"


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Device Model Serializer:
# Converts a SQLAlchemy Device ORM instance into a JSON-serializable dictionary:
# 1. Resolves customer name from joined relationship.
# 2. Determines active SIM type ('E-SIM' vs 'Plastic SIM').
# 3. Computes days remaining until expiry and sets status tag ('Active', 'Expiring Soon', 'Expired').
# 4. Formats extra customer-specific dynamic attributes.
# ==============================================================================
def out(d: Device) -> dict:
    saved_stype = (d.sim_type or "").strip()
    stype = saved_stype if saved_stype else ("E-SIM" if d.iccid and str(d.iccid).strip() else "Plastic SIM")
    extra_data = d.extra or {}
    if isinstance(extra_data, str):
        try:
            import json
            extra_data = json.loads(extra_data)
        except Exception:
            extra_data = {}
    return {
        "id": d.id, "customer_id": d.customer_id,
        "customer_name": d.customer.name if d.customer else None,
        "device_sr_no": d.device_sr_no, "imei": d.imei, "iccid": d.iccid,
        "msisdn1": d.msisdn1, "msisdn2": d.msisdn2,
        "act_date": d.act_date, "expiry_date": d.expiry_date, "dispatched_date": d.dispatched_date,
        "model": d.model, "sim_provider": d.sim_provider, "activation_plan": d.activation_plan,
        "firmware": d.firmware, "flash": d.flash, "sim_type": stype,
        "extra": extra_data,
        "days_left": (d.expiry_date - date.today()).days if d.expiry_date else None,
        "expiry_status": compute_expiry_status(d.expiry_date, 30),
        "added_by": d.added_by, "created_at": d.created_at, "deleted_at": d.deleted_at,
        "deleted_by": d.deleted_by, "delete_reason": d.delete_reason,
    }


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Customer Resolution & Auto-Resurrection:
# Finds or creates a customer by name:
# 1. Matches case-insensitively, handling underscores and spaces interchangeably.
# 2. If the customer exists in the Recycle Bin (deleted_at is set), adding new devices
#    automatically revives the customer portfolio by clearing deleted_at.
# 3. If no matching customer exists, creates a new Customer entity with a sanitized name.
# ==============================================================================
def customer_by_name(db: Session, name: str) -> Customer:
    raw = (name or "").strip()
    clean_name = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_") or raw
    
    # 1. Check if customer exists by exact name, clean name, or normalized name (ignoring spaces/underscores)
    c = db.query(Customer).filter(
        or_(
            func.lower(Customer.name) == raw.lower(),
            func.lower(Customer.name) == clean_name.lower(),
            func.replace(func.lower(Customer.name), '_', ' ') == func.replace(raw.lower(), '_', ' '),
            func.replace(func.lower(Customer.name), '_', ' ') == func.replace(clean_name.lower(), '_', ' ')
        )
    ).first()
    
    if c and c.deleted_at:  # adding devices to a deleted customer's name brings the customer back
        c.deleted_at = c.deleted_by = None
        
    if not c:
        try:
            c = Customer(name=clean_name[:150])
            db.add(c)
            db.flush()
        except Exception:
            db.rollback()
            c = db.query(Customer).filter(
                or_(
                    func.lower(Customer.name) == raw.lower(),
                    func.lower(Customer.name) == clean_name.lower(),
                    func.replace(func.lower(Customer.name), '_', ' ') == func.replace(raw.lower(), '_', ' '),
                    func.replace(func.lower(Customer.name), '_', ' ') == func.replace(clean_name.lower(), '_', ' ')
                )
            ).first()
            if not c:
                raise
        try:
            if getattr(getattr(db, "bind", None), "dialect", None) and getattr(db.bind.dialect, "name", "") == "sqlite":
                customer_tables.ensure_table(db.connection(), c.id, c.name)
            else:
                with customer_tables.engine.begin() as conn:
                    customer_tables.ensure_table(conn, c.id, c.name)
        except Exception as e:
            print(f"Customer table create failed for {c.name}: {e}")
    return c


def active_by_imei(db: Session, imei: str) -> Device:
    d = (db.query(Device).options(joinedload(Device.customer))
         .filter(Device.imei == imei.strip(), ACTIVE).first())
    if not d:
        raise HTTPException(404, "No device found with that IMEI.")
    return d


def trash(d: Device, user: models.User, reason: Optional[str]):
    d.deleted_at = datetime.utcnow()
    d.deleted_by = user.user_id
    d.delete_reason = reason or "Deleted by user"


def in_chunks(db: Session, column, values, size: int = 2000):
    """Yields (column value) rows for `column IN values`, a slice at a time, so 80,000-row files never build one giant IN()."""
    values = list(values)
    for i in range(0, len(values), size):
        yield from db.query(column).filter(column.in_(values[i:i + size]))


EXPORT_COLS = [("customer_name", "Customer Name"), ("device_sr_no", "Device SR No"), ("imei", "IMEI"), ("iccid", "ICCID"),
               ("msisdn1", "MSISDN1"), ("msisdn2", "MSISDN2"), ("act_date", "Act Date"), ("expiry_date", "Expiry Date"),
               ("dispatched_date", "Dispatched"), ("model", "Model"), ("sim_provider", "SIM Provider"),
               ("activation_plan", "Activation Plan"), ("firmware", "Firmware"), ("flash", "Flash"), ("sim_type", "SIM Type")]


def make_excel(title: str, headers: list[str], rows: list[list]) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = (re.sub(r'[\\/*?:\[\]]', '_', title or "Report"))[:31]

    header_fill = PatternFill(start_color="14213D", end_color="14213D", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=10)
    zebra = PatternFill(start_color="F9FAFD", end_color="F9FAFD", fill_type="solid")
    border_side = Side(style='thin', color='D5D9E6')
    thin_border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    fancy = len(rows) <= 5000  # cell-by-cell styling is too slow for tens of thousands of rows
    widths = [len(str(h)) for h in headers]
    for r_idx, r in enumerate(rows, start=2):
        vals = [str(v) if v is not None else "" for v in r]
        ws.append(vals)
        for i, v in enumerate(vals[:len(widths)]):
            if len(v) > widths[i]:
                widths[i] = len(v)
        if fancy:
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=r_idx, column=col_idx)
                cell.font = data_font
                cell.border = thin_border
                if r_idx % 2 == 1:
                    cell.fill = zebra

    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = min(max(w + 3, 12), 60)
    ws.row_dimensions[1].height = 26
    ws.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def get_dynamic_unique_columns(db: Session) -> list[str]:
    """Computes all unique columns dynamically from the database structure, registry, and customer records without duplicates."""
    cols = set()
    for c in BASE_COLUMNS:
        if c:
            cols.add(c.lower().strip())
    for (name,) in db.query(models.ColumnRegistry.name):
        if name and name.strip():
            cols.add(name.lower().strip())
    try:
        extra_rows = db.query(Device.extra).filter(ACTIVE, Device.extra.isnot(None)).limit(200).all()
        for (ex,) in extra_rows:
            if isinstance(ex, dict):
                for k in ex.keys():
                    if k and k.strip():
                        cols.add(k.lower().strip())
    except Exception:
        pass
    return sorted(cols)


# ---------- dashboard ----------
# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Global Inventory Telemetry Endpoint (/api/stats):
# Queries aggregate statistics across the entire database:
# - Total active devices and customer portfolios.
# - Counts of devices expiring within 30 days and already expired devices.
# - Cart / Recycle bin item counts and errored entries count.
# Powers the live status bar, sidebar indicators, and dashboard KPI cards.
# ==============================================================================
@router.get("/stats")
def stats(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    count = lambda *f: db.query(func.count(Device.id)).filter(*f).scalar()
    total_customers = db.query(func.count(Customer.id)).filter(Customer.deleted_at.is_(None)).scalar() or 0
    deleted_customers = db.query(func.count(Customer.id)).filter(Customer.deleted_at.isnot(None)).scalar() or 0
    customer_errors = db.query(func.count(func.distinct(models.ErroredRecord.customer_name))).filter(
        models.ErroredRecord.customer_name.isnot(None),
        models.ErroredRecord.customer_name != ""
    ).scalar() or 0
    total_devices = count(ACTIVE) or 0
    added_by_you = (count(ACTIVE, Device.added_by == user.id) or 0) if (user and hasattr(user, "id")) else 0
    unique_cols_list = get_dynamic_unique_columns(db)
    unique_columns = len(unique_cols_list)
    deleted_devices = count(Device.deleted_at.isnot(None)) or 0
    # expired SIMs are counted separately below, so "expiring in 30 days" starts today
    expiring_30_days = count(ACTIVE, Device.expiry_date >= date.today(), Device.expiry_date <= date.today() + timedelta(days=30)) or 0
    expired = count(ACTIVE, Device.expiry_date < date.today()) or 0
    errored_records = db.query(func.count(models.ErroredRecord.id)).scalar() or 0
    return {
        "customers": total_customers,
        "total_customers": total_customers,
        "deleted_customers": deleted_customers,
        "customer_errors": customer_errors,
        "error_entries": errored_records,
        "devices": total_devices,
        "total_devices": total_devices,
        "added_by_you": added_by_you,
        "columns": unique_columns,
        "unique_columns": unique_columns,
        "deleted": deleted_devices,
        "deleted_devices": deleted_devices,
        "expiring_30_days": expiring_30_days,
        "total_expiring": expiring_30_days,
        "expired": expired,
        "total_expired": expired,
        "errored_records": errored_records,
    }


@router.get("/columns", dependencies=[Depends(require_permission("view"))])
def columns(db: Session = Depends(get_db)):
    """Extra column names found in uploads, shown after the built-in columns."""
    base_set = {c.lower() for c in BASE_COLUMNS}
    return [n for (n,) in db.query(models.ColumnRegistry.name).order_by(models.ColumnRegistry.name) if n and n.lower() not in base_set]


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Dynamic Schema Discovery Endpoint (/api/columns/all):
# Returns the complete list of available database columns:
# Combines the 15 standard base columns (IMEI, ICCID, Serial, Customer Name, Dates, SIM Type)
# with all dynamically registered customer-specific extra columns found in `column_registry`.
# ==============================================================================
@router.get("/columns/all", dependencies=[Depends(require_permission("view"))])
def all_columns(db: Session = Depends(get_db)):
    """Dynamically retrieves all available database columns with metadata."""
    base_info = [
        ("customer_name", "Customer Name", False),
        ("device_sr_no", "Device Sr No", False),
        ("imei", "IMEI", False),
        ("iccid", "ICCID", False),
        ("msisdn1", "MSISDN 1", False),
        ("msisdn2", "MSISDN 2", False),
        ("act_date", "Act Date", False),
        ("expiry_date", "Expiry Date", False),
        ("dispatched_date", "Dispatched Date", False),
        ("model", "Model", False),
        ("sim_provider", "SIM Provider", False),
        ("activation_plan", "Activation Plan", False),
        ("firmware", "Firmware", False),
        ("flash", "Flash", False),
        ("sim_type", "SIM Type", False),
    ]
    base_keys = {k.lower() for k, _, _ in base_info}
    reg = db.query(models.ColumnRegistry.name).order_by(models.ColumnRegistry.name).all()
    extra_info = [(n, n, True) for (n,) in reg if n and n.strip().lower() not in base_keys]
    all_cols = base_info + extra_info
    return {
        "columns": [{"key": k, "label": lbl, "is_extra": is_ex} for k, lbl, is_ex in all_cols],
        "total": len(all_cols)
    }


# ---------- customers ----------
@router.get("/customers", dependencies=[Depends(require_permission("view"))])
def customers(db: Session = Depends(get_db)):
    soon = date.today() + timedelta(days=30)
    rows = (db.query(Customer.id, Customer.name, Customer.avatar, func.count(Device.id),
                     func.sum(case((Device.expiry_date <= soon, 1), else_=0)))
            .outerjoin(Device, (Device.customer_id == Customer.id) & ACTIVE)
            .filter(Customer.deleted_at.is_(None))
            .group_by(Customer.id, Customer.name, Customer.avatar).order_by(Customer.name).all())
    return [{"id": i, "name": n, "avatar": a, "devices": c, "expiring_or_expired": int(e or 0)} for i, n, a, c, e in rows]


_CUSTOMER_COLS_CACHE = {}


@router.get("/customers/{customer_id}/columns", dependencies=[Depends(require_permission("view"))])
def get_customer_columns(customer_id: int, db: Session = Depends(get_db)):
    """Retrieves standard columns plus unique/custom columns specific to this customer."""
    now = time.time()
    if customer_id in _CUSTOMER_COLS_CACHE:
        cached_ts, cached_res = _CUSTOMER_COLS_CACHE[customer_id]
        if now - cached_ts < 300:
            return cached_res

    c = db.query(Customer).filter(Customer.id == customer_id, Customer.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(404, "Customer not found.")

    base_info = [
        {"key": "customer_name", "label": "Customer Name", "is_unique": False},
        {"key": "device_sr_no", "label": "Device SR No", "is_unique": False},
        {"key": "imei", "label": "IMEI", "is_unique": False},
        {"key": "iccid", "label": "ICCID / CCID Dispatched", "is_unique": False},
        {"key": "msisdn1", "label": "MSISDN1", "is_unique": False},
        {"key": "msisdn2", "label": "MSISDN2", "is_unique": False},
        {"key": "act_date", "label": "Act Date", "is_unique": False},
        {"key": "expiry_date", "label": "Expiry Date", "is_unique": False},
        {"key": "dispatched_date", "label": "Dispatched", "is_unique": False},
        {"key": "model", "label": "Model", "is_unique": False},
        {"key": "sim_provider", "label": "SIM Provider", "is_unique": False},
        {"key": "activation_plan", "label": "Activation Plan", "is_unique": False},
        {"key": "firmware", "label": "Firmware", "is_unique": False},
        {"key": "flash", "label": "Flash", "is_unique": False},
        {"key": "sim_type", "label": "SIM Type", "is_unique": False},
    ]
    base_keys = {item["key"].lower() for item in base_info}

    reg_names = [r[0] for r in db.query(models.ColumnRegistry.name).all() if r[0]]
    slug_to_reg = {customer_tables.extra_col(n): n for n in reg_names}

    unique_cols_map = {}

    # 1. Discover from customer's dedicated table
    try:
        conn = db.connection()
        tbl = customer_tables.find_table(conn, c.id, c.name)
        if tbl:
            insp = inspect(conn)
            for col_info in insp.get_columns(tbl):
                cn = col_info["name"]
                if cn in customer_tables.BASE_NAMES or cn in ("imei", "updated_at"):
                    continue
                orig_label = slug_to_reg.get(cn)
                clean_k = cn[2:] if cn.startswith("x_") else cn
                label = orig_label or clean_k.replace("_", " ").upper()
                key_id = orig_label or cn
                if key_id.lower() not in base_keys:
                    unique_cols_map[key_id] = {
                        "key": key_id,
                        "table_col": cn,
                        "label": label,
                        "is_unique": True
                    }
    except Exception as e:
        print(f"Error inspecting customer table {c.name}: {e}")

    # 2. Discover from sim_devices.extra for this customer
    try:
        sample_extras = db.execute(
            text("SELECT extra FROM sim_devices WHERE customer_id = :cid AND extra IS NOT NULL AND extra != '' AND extra != '{}' LIMIT 200"),
            {"cid": c.id}
        ).fetchall()
        import json
        for (ex,) in sample_extras:
            d_ex = None
            if isinstance(ex, dict):
                d_ex = ex
            elif isinstance(ex, str):
                try:
                    d_ex = json.loads(ex)
                except Exception:
                    pass
            if isinstance(d_ex, dict):
                for k in d_ex.keys():
                    if k and k.strip().lower() not in base_keys:
                        k_clean = k.strip()
                        if k_clean not in unique_cols_map:
                            unique_cols_map[k_clean] = {
                                "key": k_clean,
                                "table_col": customer_tables.extra_col(k_clean),
                                "label": k_clean,
                                "is_unique": True
                            }
    except Exception as e:
        print(f"Error inspecting extra for {c.name}: {e}")

    unique_cols = list(unique_cols_map.values())
    unique_cols.sort(key=lambda x: x["label"].lower())

    res = {
        "customer_id": c.id,
        "customer_name": c.name,
        "has_unique_columns": len(unique_cols) > 0,
        "standard_columns": base_info,
        "unique_columns": unique_cols,
        "all_columns": base_info + unique_cols,
        "total_unique": len(unique_cols),
    }
    _CUSTOMER_COLS_CACHE[customer_id] = (now, res)
    return res


@router.get("/customers/columns/summary", dependencies=[Depends(require_permission("view"))])
def get_all_customers_unique_columns_summary(db: Session = Depends(get_db)):
    """Summary of unique columns across all active customers in 1 fast query."""
    custs = db.query(Customer.id, Customer.name).filter(Customer.deleted_at.is_(None)).order_by(Customer.name).all()
    reg_names = [r[0] for r in db.query(models.ColumnRegistry.name).all() if r[0]]
    slug_to_reg = {customer_tables.extra_col(n): n for n in reg_names}

    # Query information_schema once for speed
    try:
        col_rows = db.execute(text("""
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
              AND column_name LIKE 'x_%'
            ORDER BY table_name, column_name
        """)).fetchall()
        tbl_cols = {}
        for t, c in col_rows:
            tbl_cols.setdefault(t.lower(), []).append(c)
    except Exception:
        tbl_cols = {}

    summary = []
    for cid, cname in custs:
        target_tbl = customer_tables.slug(cname).lower()
        cols = tbl_cols.get(target_tbl, [])
        if not cols:
            # check customer_ prefix
            cols = tbl_cols.get(f"customer_{target_tbl}", [])
        if not cols:
            # check c<cid>_ prefix
            for t_name, c_list in tbl_cols.items():
                if t_name.startswith(f"c{cid}_"):
                    cols = c_list
                    break
        if cols:
            u_cols = []
            for cn in cols:
                orig = slug_to_reg.get(cn, cn[2:].replace("_", " ").upper() if cn.startswith("x_") else cn)
                u_cols.append({"key": orig, "table_col": cn, "label": orig})
            summary.append({
                "customer_id": cid,
                "customer_name": cname,
                "unique_columns": u_cols,
                "count": len(u_cols)
            })

    return {"customers_with_unique_columns": summary, "total_customers": len(summary)}


@router.post("/customers", status_code=201, dependencies=[Depends(require_permission("add"))])
def add_customer(data: schemas.CustomerIn, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    cname = (data.name or "").strip()
    if not cname:
        raise HTTPException(400, "Customer name cannot be blank.")
    if len(cname) > 150 or re.search(r"[;\`\'\"]", cname):
        raise HTTPException(400, "Customer name contains invalid characters or exceeds 150 characters.")
    c = customer_by_name(db, cname)
    log_activity(db, "customer_add", f"Customer {c.name}", user=user)
    db.commit()
    try:  # give the new customer its own (empty) table right away
        if getattr(getattr(db, "bind", None), "dialect", None) and getattr(db.bind.dialect, "name", "") == "sqlite":
            customer_tables.ensure_table(db.connection(), c.id, c.name)
            db.commit()
        else:
            with customer_tables.engine.begin() as conn:
                customer_tables.ensure_table(conn, c.id, c.name)
    except Exception as e:
        print(f"Customer table create failed: {e}")
    return {"id": c.id, "name": c.name}


@router.patch("/customers/{customer_id}", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def rename_customer(customer_id: int, data: schemas.CustomerRenameIn, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    c = db.query(Customer).filter(Customer.id == customer_id, Customer.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(404, "Customer not found.")
    new_name = data.name.strip()
    if not new_name:
        raise HTTPException(400, "Customer name cannot be empty.")
    if len(new_name) > 150 or re.search(r"[;\`\'\"]", new_name):
        raise HTTPException(400, "Customer name contains invalid characters or exceeds 150 characters.")

    # Check if another active customer already uses this name
    existing = db.query(Customer).filter(
        Customer.id != customer_id,
        Customer.deleted_at.is_(None),
        or_(
            func.lower(Customer.name) == new_name.lower(),
            func.replace(func.lower(Customer.name), '_', ' ') == func.replace(new_name.lower(), '_', ' ')
        )
    ).first()
    if existing:
        raise HTTPException(400, f"A customer named '{existing.name}' already exists.")

    old_name = c.name
    c.name = new_name
    db.commit()

    # Synchronize dedicated table in cloud database
    try:
        customer_tables.rename_table(c.id, new_name, old_name)
    except Exception as e:
        print(f"Customer table rename error: {e}")

    log_activity(db, "customer_rename", f"Renamed customer ID {c.id} from '{old_name}' to '{new_name}'", user=user)
    db.commit()
    return {"id": c.id, "name": c.name, "old_name": old_name}


@router.post("/customers/rename-all", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def rename_all_customers(data: schemas.CustomerRenameAllIn, db: Session = Depends(get_db),
                         user: models.User = Depends(get_current_user)):
    if not data.renames:
        raise HTTPException(400, "No customer renames provided.")

    seen_names = set()
    for item in data.renames:
        cid = item.id
        new_name = item.name.strip()
        if not new_name:
            raise HTTPException(400, f"Customer name for ID {cid} cannot be empty.")
        if len(new_name) > 150 or re.search(r"[;\`\'\"]", new_name):
            raise HTTPException(400, f"Customer name '{new_name}' contains invalid characters or exceeds 150 characters.")
        norm_name = new_name.lower().replace("_", " ")
        if norm_name in seen_names:
            raise HTTPException(400, f"Duplicate customer name '{new_name}' in request.")
        seen_names.add(norm_name)

    renamed_items = []
    for item in data.renames:
        cid = item.id
        new_name = item.name.strip()
        c = db.query(Customer).filter(Customer.id == cid, Customer.deleted_at.is_(None)).first()
        if not c:
            continue
        if c.name == new_name:
            continue
        old_name = c.name
        c.name = new_name
        db.flush()
        try:
            customer_tables.rename_table(c.id, new_name, old_name)
        except Exception as e:
            print(f"Error renaming table for {cid}: {e}")
        renamed_items.append({"id": cid, "old_name": old_name, "new_name": new_name})

    db.commit()
    log_activity(db, "customer_rename_all", f"Renamed {len(renamed_items)} customer portfolios", user=user)
    db.commit()
    return {"success": True, "renamed_count": len(renamed_items), "renames": renamed_items}


@router.post("/customers/{customer_id}/delete-all-entries", dependencies=[Depends(require_staff), Depends(require_permission("delete"))])
def delete_all_entries_for_customer(customer_id: int, data: schemas.CustomerDeleteAllEntriesIn, db: Session = Depends(get_db),
                                    user: models.User = Depends(get_current_user)):
    # Master Admin restriction: Master Admins are NOT permitted to delete valid inventory!
    if user.role == "master_admin" or not get_user_permissions(user).get("delete", False):
        raise HTTPException(status_code=403, detail="Master Admins are not permitted to delete valid inventory records.")

    c = db.query(Customer).filter(Customer.id == customer_id, Customer.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(404, "Customer not found.")

    clean_expected = c.name.strip().lower()
    clean_provided = data.confirm_name.strip().lower()
    if clean_provided != clean_expected and clean_provided.replace(" ", "_") != clean_expected.replace(" ", "_"):
        raise HTTPException(400, f"Confirmation name mismatch. Expected '{c.name}'.")

    total_to_delete = db.query(Device).filter(Device.customer_id == customer_id, ACTIVE).count()
    if total_to_delete == 0:
        return {"success": True, "customer_id": customer_id, "customer_name": c.name, "deleted_count": 0, "message": "No active entries found for this customer."}

    deleted_so_far = 0
    now_utc = datetime.utcnow()
    batch_size = 2000

    while True:
        batch_ids = [d_id for (d_id,) in db.query(Device.id).filter(Device.customer_id == customer_id, ACTIVE).limit(batch_size).all()]
        if not batch_ids:
            break
        if data.permanent:
            db.query(Device).filter(Device.id.in_(batch_ids)).delete(synchronize_session=False)
        else:
            db.query(Device).filter(Device.id.in_(batch_ids)).update({
                Device.deleted_at: now_utc,
                Device.deleted_by: user.user_id,
                Device.delete_reason: data.reason or f"Deleted all entries for customer '{c.name}'"
            }, synchronize_session=False)
        db.commit()
        deleted_so_far += len(batch_ids)

    try:
        customer_tables.clear_table(c.id, c.name)
    except Exception as e:
        print(f"Customer table clear rows error: {e}")

    log_activity(db, "customer_delete_all_entries", f"Deleted all {deleted_so_far} entries for customer '{c.name}' (ID {c.id})", user=user)
    db.commit()
    return {
        "success": True,
        "customer_id": c.id,
        "customer_name": c.name,
        "deleted_count": deleted_so_far
    }


DELETE_ALL_PHRASE = "DELETE ALL CUSTOMERS"


@router.post("/customers/delete-all-permanent", dependencies=[Depends(require_staff), Depends(require_permission("delete"))])
def delete_all_customers_permanently(data: dict = Body(...), db: Session = Depends(get_db),
                                     user: models.User = Depends(get_current_user)):
    """PERMANENT, cannot be undone: removes EVERY customer (including those in the bin), every device record (recycle bin included),
    every per-customer SQL table and the list of extra column names. Users, activity log and Errored Entries are kept.
    The caller must send  {"confirm_text": "DELETE ALL CUSTOMERS"}."""
    if user.role == "master_admin" or not get_user_permissions(user).get("delete", False):
        raise HTTPException(status_code=403, detail="You are not permitted to delete customer data.")
    if str(data.get("confirm_text") or "").strip() != DELETE_ALL_PHRASE:
        raise HTTPException(400, f"Confirmation text mismatch. Type exactly: {DELETE_ALL_PHRASE}")

    customers = [(cid, name) for cid, name in db.query(Customer.id, Customer.name).all()]
    total_devices = db.query(func.count(Device.id)).scalar() or 0

    deleted_devices = 0
    while True:  # in slices, so a huge table never becomes one giant statement
        ids = [i for (i,) in db.query(Device.id).limit(5000).all()]
        if not ids:
            break
        db.query(Device).filter(Device.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        deleted_devices += len(ids)
    db.query(Customer).delete(synchronize_session=False)
    db.query(models.ColumnRegistry).delete(synchronize_session=False)
    db.commit()

    # The per-customer tables. Never touch an application table, whatever a customer was called.
    dropped, skipped = 0, []
    for cid, name in customers:
        try:
            with customer_tables.engine.begin() as conn:
                t = customer_tables.find_table(conn, cid, name)
                if not t:
                    continue
                if t.lower() in customer_tables.SYSTEM_TABLES:
                    skipped.append(t)
                    continue
                conn.execute(text(f"DROP TABLE IF EXISTS `{t}`"))
                customer_tables._VERIFIED_TABLES.discard(t)
                dropped += 1
        except Exception as e:
            print(f"Customer table drop failed for {name}: {e}")

    log_activity(db, "customer_delete_all",
                 f"PERMANENTLY deleted ALL customers ({len(customers)}), {deleted_devices} device records, {dropped} customer tables",
                 user=user, commit=True)
    return {"success": True, "deleted_customers": len(customers), "deleted_devices": deleted_devices,
            "expected_devices": total_devices, "dropped_tables": dropped}


@router.delete("/customers/{customer_id}", dependencies=[Depends(require_staff), Depends(require_permission("delete"))])
def delete_customer(customer_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    if user.role == "master_admin" or not get_user_permissions(user).get("delete", False):
        raise HTTPException(status_code=403, detail="Master Admins are not permitted to delete customer portfolios.")

    c = db.query(Customer).filter(Customer.id == customer_id, Customer.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(404, "Customer not found.")

    c.deleted_at = datetime.utcnow()
    c.deleted_by = user.user_id

    db.query(Device).filter(Device.customer_id == customer_id, ACTIVE).update({
        Device.deleted_at: datetime.utcnow(),
        Device.deleted_by: user.user_id,
        Device.delete_reason: f"Customer '{c.name}' deleted"
    }, synchronize_session=False)

    log_activity(db, "customer_delete", f"Customer '{c.name}' (ID {c.id}) moved to bin", user=user)
    db.commit()
    return {"success": True, "customer_id": c.id, "customer_name": c.name}


@router.put("/customers/{customer_id}/avatar", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
@router.patch("/customers/{customer_id}/avatar", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def update_customer_avatar(customer_id: int, data: dict, db: Session = Depends(get_db),
                           user: models.User = Depends(get_current_user)):
    c = db.query(Customer).filter(Customer.id == customer_id, Customer.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(404, "Customer not found.")
    c.avatar = data.get("avatar")
    db.commit()
    return {"id": c.id, "avatar": c.avatar}



# ---------- devices ----------
# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Master Device Query Builder:
# Constructs dynamic SQLAlchemy queries for inventory search, fetch, and exports:
# 1. Filters by active status (excludes soft-deleted items in the Cart).
# 2. Filters by customer scope if `customer_id` is supplied.
# 3. Handles SIM type filtering ('esim', 'plastic', or 'all').
# 4. Supports multi-identifier search across single or multiple fields (IMEI, ICCID, Serial, MSISDN).
# 5. Applies date range windows for SIM expiry tracking.
# 6. Sorts by specified column in ascending or descending order.
# ==============================================================================
def build_device_query(db: Session, customer_id, q, column, sort_by, sort_dir, sim_type="all",
                       expiry_filter="all", expiry_days=30, exp_start=None, exp_end=None):
    """Search + sort shared by the table and the Excel export, so both always agree."""
    query = db.query(Device).join(Customer).options(joinedload(Device.customer)).filter(ACTIVE)
    if customer_id:
        query = query.filter(Device.customer_id == customer_id)

    if sim_type == "esim":
        query = query.filter(or_(
            func.upper(Device.sim_type) == 'E-SIM',
            and_(or_(Device.sim_type.is_(None), Device.sim_type == ''), Device.iccid.isnot(None), Device.iccid != '')
        ))
    elif sim_type == "plastic":
        query = query.filter(or_(
            func.upper(Device.sim_type).in_(['PLASTIC SIM', 'PLASTIC']),
            and_(or_(Device.sim_type.is_(None), Device.sim_type == ''), or_(Device.iccid.is_(None), Device.iccid == ''))
        ))

    today = date.today()
    if expiry_filter == "expired":
        query = query.filter(Device.expiry_date.isnot(None), Device.expiry_date < today)
    elif expiry_filter == "expiring_7":
        query = query.filter(Device.expiry_date.isnot(None), Device.expiry_date >= today, Device.expiry_date <= today + timedelta(days=7))
    elif expiry_filter == "expiring_15":
        query = query.filter(Device.expiry_date.isnot(None), Device.expiry_date >= today, Device.expiry_date <= today + timedelta(days=15))
    elif expiry_filter in ("expiring_30", "expiring_soon"):
        query = query.filter(Device.expiry_date.isnot(None), Device.expiry_date >= today, Device.expiry_date <= today + timedelta(days=expiry_days or 30))
    elif expiry_filter == "active":
        query = query.filter(Device.expiry_date.isnot(None), Device.expiry_date > today + timedelta(days=expiry_days or 30))
    elif expiry_filter == "unknown":
        query = query.filter(Device.expiry_date.is_(None))  # (comparing a DATE column to "" raises an error on MySQL/TiDB)
    elif expiry_filter == "custom" and exp_start and exp_end:
        query = query.filter(Device.expiry_date.isnot(None), Device.expiry_date >= exp_start, Device.expiry_date <= exp_end)

    q = (q or "").strip()
    if q:
        raw_parts = [p.strip() for p in re.split(r"[,;\r\n]+", q) if p.strip()]
        if not raw_parts:
            raw_parts = [q]

        col_map = {
            "imei": Device.imei,
            "iccid": Device.iccid,
            "ccid": Device.iccid,
            "device_sr_no": Device.device_sr_no,
            "msisdn1": Device.msisdn1,
            "msisdn2": Device.msisdn2,
            "customer_name": Customer.name,
            "model": Device.model,
            "sim_provider": Device.sim_provider,
            "activation_plan": Device.activation_plan,
            "firmware": Device.firmware,
            "flash": Device.flash,
            "sim_type": Device.sim_type,
        }

        term_filters = []
        for part in raw_parts:
            like = f"%{escape_like(part)}%"
            norm_dt = normalize_date_input(part)
            dt_like = f"%{norm_dt.isoformat()}%" if norm_dt else None
            clean_part = clean_iccid(part)

            if column and column.lower() in ("iccid", "ccid"):
                iccid_likes = [Device.iccid.like(like)]
                if clean_part:
                    iccid_likes.append(Device.iccid.like(f"%{escape_like(clean_part)}%"))
                    stripped = clean_part.rstrip("F")
                    if stripped and stripped != clean_part:
                        iccid_likes.append(Device.iccid.like(f"%{escape_like(stripped)}%"))
                    if len(clean_part) >= 19:
                        iccid_likes.append(func.left(Device.iccid, 19) == clean_part[:19])
                term_filters.append(or_(*iccid_likes))
            elif column and column in col_map:
                f_expr = col_map[column].like(like)
                if dt_like and column in ("act_date", "expiry_date", "dispatched_date"):
                    f_expr = or_(f_expr, col_map[column].like(dt_like))
                term_filters.append(f_expr)
            elif column and column.lower() != "all":
                # Specific search by a unique/custom column (e.g. "PCB NO", "DISPATCH DETAILS", etc.)
                clean_col = column.strip()
                term_filters.append(or_(
                    func.json_unquote(func.json_extract(Device.extra, f'$."{clean_col}"')).like(like),
                    cast(Device.extra, String).like(like)
                ))
            else:
                # Fast indexed search for IMEIs, serial numbers, phone numbers
                if part.isdigit() and len(part) >= 10:
                    sub_or = [
                        Device.imei == part,
                        Device.imei.like(like),
                        Device.iccid.like(like),
                        Device.device_sr_no.like(like),
                        Device.msisdn1.like(like),
                        Customer.name.like(like),
                        cast(Device.extra, String).like(like),
                    ]
                else:
                    cols = [Customer.name, Device.imei, Device.iccid, Device.device_sr_no, Device.msisdn1, Device.msisdn2,
                            Device.model, Device.sim_provider, Device.activation_plan, Device.firmware, Device.flash, Device.sim_type]
                    sub_or = [c.like(like) for c in cols]
                    sub_or.append(cast(Device.extra, String).like(like))
                if clean_part:
                    sub_or.append(Device.iccid.like(f"%{escape_like(clean_part)}%"))
                    stripped = clean_part.rstrip("F")
                    if stripped and stripped != clean_part:
                        sub_or.append(Device.iccid.like(f"%{escape_like(stripped)}%"))
                if norm_dt:
                    sub_or.extend([
                        Device.act_date == norm_dt,
                        Device.dispatched_date == norm_dt,
                        Device.expiry_date == norm_dt
                    ])
                term_filters.append(or_(*sub_or))

        if len(term_filters) == 1:
            query = query.filter(term_filters[0])
        elif len(term_filters) > 1:
            query = query.filter(or_(*term_filters))

    sort_fields = {
        "id": Device.id,
        "imei": Device.imei,
        "customer_name": Customer.name,
        "device_sr_no": Device.device_sr_no,
        "iccid": Device.iccid,
        "ccid": Device.iccid,
        "act_date": Device.act_date,
        "expiry_date": Device.expiry_date,
        "days_left": Device.expiry_date,
        "model": Device.model,
        "sim_provider": Device.sim_provider,
    }
    sort_key = (sort_by or "").lower()
    
    # Requirement 1: In SIM Expiry section / expiry sorting, display in ascending order of days remaining (fewest days left first, expired SIMs first)
    if sort_key in ("expiry_date", "days_left") or (expiry_filter and expiry_filter != "all" and sort_key in ("", "id", "expiry_date", "days_left")):
        if sort_dir == "desc":
            return query.order_by(desc(Device.expiry_date), desc(Device.id))
        else:
            return query.order_by(Device.expiry_date.is_(None), asc(Device.expiry_date), asc(Device.id))

    col_attr = sort_fields.get(sort_key, Device.id)
    return query.order_by(desc(col_attr) if sort_dir == "desc" else asc(col_attr), asc(Device.id))


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Device Pagination & Query Endpoint (/api/devices):
# Primary endpoint used by Normal Fetch and Customer Inventory:
# 1. Calls `build_device_query` with client search terms, filters, and pagination parameters.
# 2. Computes total count and extracts the target page window (offset & limit).
# 3. Logs the search event into the audit trail for security and telemetry tracking.
# 4. Returns formatted device records and pagination metadata.
# ==============================================================================
@router.get("/devices", dependencies=[Depends(require_permission("view"))])
def list_devices(customer_id: Optional[int] = None, q: str = "", column: Optional[str] = "all",
                 sim_type: Optional[str] = "all",
                 expiry_filter: Optional[str] = "all", expiry_days: int = Query(30, ge=1, le=365),
                 exp_start: Optional[date] = None, exp_end: Optional[date] = None,
                 sort_by: Optional[str] = "id", sort_dir: Optional[str] = "asc",
                 page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=5000),
                 db: Session = Depends(get_db), user: Optional[models.User] = Depends(get_current_user)):
    query = build_device_query(db, customer_id, q, column, sort_by, sort_dir, sim_type=sim_type,
                               expiry_filter=expiry_filter, expiry_days=expiry_days, exp_start=exp_start, exp_end=exp_end)
    cur_page = int(page.default if hasattr(page, 'default') else page)
    cur_page_size = int(page_size.default if hasattr(page_size, 'default') else page_size)
    total = query.count()
    items = query.offset((cur_page - 1) * cur_page_size).limit(cur_page_size).all()
    # Fetch live MSISDN1, MSISDN2, Act Date, Expiry Date from Sensorise server and update DB
    try:
        items = sync_devices_with_sensorise(db, items)
    except Exception as _sync_err:
        pass
    if q and q.strip():
        cust_str = f"Customer ID {customer_id}" if customer_id else "All Customers"
        try:
            log_activity(db, "search", f"Device Search: '{q.strip()}' [Field: {column or 'all'}, {cust_str}, Results: {total}]", user=user, commit=True)
        except Exception:
            pass
    return {"total": total, "page": cur_page, "page_size": cur_page_size,
            "pages": max(1, -(-total // cur_page_size)), "items": [out(d) for d in items]}


# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Full Inventory Excel Export Endpoint (/api/devices/export):
# Generates a formatted Excel (.xlsx) workbook containing all records matching
# the current search/filter criteria (streamed in memory, not limited to visible page).
# Includes standard fields, dynamic customer columns, and styled headers.
# ==============================================================================
@router.get("/devices/export", dependencies=[Depends(require_permission("download"))])
def export_devices(customer_id: Optional[int] = None, q: str = "", column: Optional[str] = "all",
                   sim_type: Optional[str] = "all",
                   expiry_filter: Optional[str] = "all", expiry_days: int = Query(30, ge=1, le=365),
                   exp_start: Optional[date] = None, exp_end: Optional[date] = None,
                   sort_by: Optional[str] = "id", sort_dir: Optional[str] = "asc",
                   title: str = "Customer_Inventory_Export",
                   db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """EVERY record that matches the current filters (not just one page) as an Excel file."""
    query = build_device_query(db, customer_id, q, column, sort_by, sort_dir, sim_type=sim_type,
                               expiry_filter=expiry_filter, expiry_days=expiry_days, exp_start=exp_start, exp_end=exp_end)
    if customer_id:
        cust_cols = get_customer_columns(customer_id, db)
        extra_cols = [c["key"] for c in cust_cols.get("unique_columns", [])]
    else:
        extra_cols = [n for (n,) in db.query(models.ColumnRegistry.name).order_by(models.ColumnRegistry.name)]
    headers = ["ID"] + [label for _, label in EXPORT_COLS] + extra_cols
    rows, offset, batch = [], 0, 2000
    while True:
        part = query.offset(offset).limit(batch).all()
        if not part:
            break
        for d in part:
            o = out(d)
            rows.append([d.id] + [o.get(k) for k, _ in EXPORT_COLS] + [(d.extra or {}).get(c) for c in extra_cols])
        offset += batch
        for d in part:
            db.expunge(d)  # keep memory flat while reading tens of thousands of rows
    clean_title = re.sub(r"[^a-zA-Z0-9_-]", "_", title or "Export")
    filename = f"{clean_title}_{date.today().isoformat()}.xlsx"
    buf = make_excel(clean_title, headers, rows)
    log_activity(db, "export_excel", f"Exported {len(rows)} rows ({clean_title})", user=user)
    db.commit()
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/devices/expiry-summary", dependencies=[Depends(require_permission("view"))])
def get_expiry_summary(customer_id: Optional[int] = None, days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    today = date.today()
    base_q = db.query(Device).filter(ACTIVE)
    if customer_id:
        base_q = base_q.filter(Device.customer_id == customer_id)

    total = base_q.count()
    expired = base_q.filter(Device.expiry_date.isnot(None), Device.expiry_date < today).count()
    exp_7 = base_q.filter(Device.expiry_date.isnot(None), Device.expiry_date >= today, Device.expiry_date <= today + timedelta(days=7)).count()
    exp_15 = base_q.filter(Device.expiry_date.isnot(None), Device.expiry_date >= today, Device.expiry_date <= today + timedelta(days=15)).count()
    exp_30 = base_q.filter(Device.expiry_date.isnot(None), Device.expiry_date >= today, Device.expiry_date <= today + timedelta(days=days)).count()
    active = base_q.filter(Device.expiry_date.isnot(None), Device.expiry_date > today + timedelta(days=days)).count()
    unknown = base_q.filter(Device.expiry_date.is_(None)).count()  # DATE == "" raises on MySQL/TiDB and made this whole endpoint fail

    return {
        "total_count": total,
        "expired_count": expired,
        "expiring_7_days": exp_7,
        "expiring_15_days": exp_15,
        "expiring_30_days": exp_30,
        "active_count": active,
        "unknown_count": unknown,
        "alert_triggered": (expired > 0 or exp_30 > 0)
    }



_IMEI_STRIP = re.compile(r"[^0-9A-Za-z_-]")


def effective_imei(raw_imei, raw_sr, raw_iccid) -> Optional[str]:
    """The IMEI that will really be stored for an upload row (validate and insert use this same rule).
    Uses the IMEI if it is usable, else the Device Sr No, else the ICCID. None = nothing usable (a unique INV_ id is made on insert)."""
    for cand in (raw_imei, raw_sr, raw_iccid):
        s = _IMEI_STRIP.sub("", str(cand or "").strip())
        if len(s) >= 5:
            return s[:20]
    return None


def _lookup_existing(db: Session, iccids, imeis, srs):
    """Existing devices (active AND recycle bin) keyed by lower-case ICCID / IMEI / Sr No.
    Plain column queries, 2,000 keys at a time. No per-row lazy loading."""
    by_iccid, by_imei, by_sr = {}, {}, {}

    def put(m, key, d):
        if not key:
            return
        k = str(key).strip().lower()
        cur = m.get(k)
        if cur is None or (cur.deleted_at is not None and d.deleted_at is None):  # an active record wins over a bin record
            m[k] = d

    for col, keys, m, attr in ((Device.iccid, iccids, by_iccid, "iccid"),
                               (Device.imei, imeis, by_imei, "imei"),
                               (Device.device_sr_no, srs, by_sr, "device_sr_no")):
        keys = sorted(set(keys))
        for i in range(0, len(keys), 2000):
            for d in db.query(Device).filter(col.in_(keys[i:i + 2000])):
                put(m, getattr(d, attr), d)
    return by_iccid, by_imei, by_sr


def _identifier_conflict(r, matched, by_iccid, by_imei, by_sr):
    """Device Sr No, IMEI and ICCID/CCID must each belong to ONE record only.
    Returns a reason text when the row would make an identifier repeat, otherwise ''."""
    def s_(v):
        return str(v or "").strip()

    def n_ic(v):
        # Whole-number comparison: every character must match (a trailing F is part of the number).
        return iccid_key(re.sub(r"[\s\-_]+", "", s_(v)))

    ic, im, sr = s_(r.iccid), _IMEI_STRIP.sub("", s_(r.imei))[:20], s_(r.device_sr_no)
    # 1) another ACTIVE record already owns one of the identifiers in this row
    for label, m, key, shown in (("ICCID/CCID", by_iccid, iccid_key(ic), ic), ("IMEI", by_imei, im.lower(), im),
                                 ("Device Sr No", by_sr, sr.lower(), sr)):
        other = m.get(key) if key else None
        if other is not None and other.id != matched.id and other.deleted_at is None:
            return f"{label} '{shown}' already belongs to a different record (IMEI {other.imei}); identifiers must not repeat"
    # 2) the record found by one identifier already holds a DIFFERENT value for another one
    if ic and matched.iccid and n_ic(ic) != n_ic(matched.iccid):
        return f"This row matches an existing record but its ICCID/CCID differs from the stored one ('{matched.iccid}')"
    if im and matched.imei and not str(matched.imei).startswith("INV_") and im.lower() != str(matched.imei).strip().lower():
        return f"This row matches an existing record but its IMEI differs from the stored one ('{matched.imei}')"
    return ""


_VALIDATE_COMPARE = (("msisdn1", "MSISDN1"), ("msisdn2", "MSISDN2"), ("act_date", "Activation Date"),
                     ("expiry_date", "Expiry Date"), ("dispatched_date", "Dispatched Date"), ("model", "Model"),
                     ("sim_provider", "SIM Provider"), ("sim_type", "SIM Type"), ("activation_plan", "Activation Plan"),
                     ("firmware", "Firmware"), ("flash", "Flash"), ("device_sr_no", "Device Sr No"))


def _row_diffs(r, matched) -> dict:
    """What an uploaded row would CHANGE on an existing device. Blank cells in the file never count (they never erase data).
    Used by BOTH validation (to label a row 'Requires Update') and the update step, so the two can never disagree."""
    diffs = {}
    for f_key, f_lbl in _VALIDATE_COMPARE:
        new_val, old_val = getattr(r, f_key, None), getattr(matched, f_key, None)
        new_str = new_val.isoformat() if isinstance(new_val, date) else str(new_val or "").strip()
        old_str = old_val.isoformat() if isinstance(old_val, date) else str(old_val or "").strip()
        if new_str and new_str != old_str:
            diffs[f_key] = {"label": f_lbl, "old": old_str or "—", "new": new_str}
    if isinstance(r.extra, dict):
        curr_extra = matched.extra or {}
        for ek, ev in r.extra.items():
            ek_s, ev_s = str(ek).strip(), str(ev or "").strip()
            old_ev = str(curr_extra.get(ek_s) or "").strip()
            if ev_s and ev_s != old_ev:
                diffs[f"extra_{ek_s}"] = {"label": ek_s.replace("_", " ").upper(), "old": old_ev or "—", "new": ev_s}
    return diffs


@router.post("/devices/bulk/validate", dependencies=[Depends(require_permission("upload"))])
def bulk_validate(data: schemas.BulkIn, compact: bool = False, db: Session = Depends(get_db)):
    """Compares uploaded rows with the whole database (ICCID, IMEI, Device Sr No), recycle bin included.

    Each row ends up as exactly one of:  New (N) | Requires Update (U) | Existing (E) | Duplicate (D) | Invalid (I).
    compact=true additionally returns `row_status` (one letter per row, in request order)
    and `row_reasons`, and leaves out the huge key lists that older pages still read.
    """
    rows = data.rows
    n_rows = len(rows)

    def s(v):
        return str(v or "").strip()

    iccids = {s(r.iccid) for r in rows if s(r.iccid)}
    imeis, srs = set(), set()
    eff_cache = []
    for r in rows:
        e = effective_imei(r.imei, r.device_sr_no, r.iccid)
        eff_cache.append(e)
        if s(r.imei):
            imeis.add(s(r.imei))
        if e:
            imeis.add(e)
        if s(r.device_sr_no):
            srs.add(s(r.device_sr_no))

    by_iccid, by_imei, by_sr = _lookup_existing(db, iccids, imeis, srs)
    cust_names = {cid: name for cid, name in db.query(Customer.id, Customer.name)}

    live = [(name or "") for _id, name in db.query(Customer.id, Customer.name).filter(Customer.deleted_at.is_(None))]
    known_custs = {n.lower() for n in live}
    known_custs_norm = {n.lower().replace("_", " ") for n in live}
    known_cols = {n.lower() for (n,) in db.query(models.ColumnRegistry.name)}
    known_cols.update(c.lower() for c in BASE_COLUMNS)

    seen_iccids, seen_imeis, seen_sr_nos = {}, {}, {}   # value -> first row number
    new_entries, entries_requiring_update, existing_entries = [], [], []
    duplicates, invalids = [], []
    new_customers, new_columns = set(), set()
    esim_count = plastic_count = 0
    status = []                # one letter per row
    reason_ix, reason_tbl = {}, []
    row_reasons = {}           # row index -> index in reason_tbl (only rows that will NOT be inserted)

    def set_reason(i, text_):
        k = reason_ix.get(text_)
        if k is None:
            k = reason_ix[text_] = len(reason_tbl)
            reason_tbl.append(text_)
        row_reasons[i] = k

    if not any(s(r.iccid) for r in rows) and not any(s(r.imei) for r in rows):
        missing_columns = ["ICCID / IMEI"]
    else:
        missing_columns = []

    today = date.today()
    exp_counts = {"expired": 0, "expiring_soon": 0, "active": 0, "unknown": 0}

    for i, r in enumerate(rows):
        idx = i + 1
        errs = []
        cname = s(r.customer_name)
        if not cname:
            errs.append("Missing or bad Customer Name")
        elif len(cname) > 100 or any(ch in cname for ch in (";", "`", "'", '"')):
            errs.append("Customer name contains invalid characters or exceeds 100 characters")
        elif cname.lower() not in known_custs and cname.lower().replace("_", " ") not in known_custs_norm:
            new_customers.add(cname)

        raw_iccid, raw_imei, raw_sr = s(r.iccid), s(r.imei), s(r.device_sr_no)
        if not raw_iccid and not raw_imei and not raw_sr:
            errs.append("Missing ICCID, IMEI and Device Sr No (no identifier)")
        # No restriction on activation / expiry / dispatched dates: any order and any year is accepted.

        for fld, key, nm in ((r.device_sr_no, "device_sr_no", "Device Sr No"), (r.iccid, "iccid", "ICCID"),
                             (r.imei, "imei", "IMEI"), (r.msisdn1, "msisdn1", "MSISDN1"), (r.msisdn2, "msisdn2", "MSISDN2"),
                             (r.model, "model", "Model"), (r.sim_provider, "sim_provider", "SIM Provider"),
                             (r.activation_plan, "activation_plan", "Activation Plan"), (r.firmware, "firmware", "Firmware"),
                             (r.flash, "flash", "Flash")):
            limit = FIELD_MAX_LEN.get(key, 100)
            if fld and len(str(fld).strip()) > limit:  # would be cut off on insert, so refuse instead of silently corrupting it
                errs.append(f"{nm} is longer than {limit} characters")

        if r.extra and isinstance(r.extra, dict):
            for k, v in r.extra.items():
                k_clean = str(k).strip()
                if not re.match(r"^[a-zA-Z0-9_\s-]+$", k_clean) or len(k_clean) > 64:
                    errs.append(f"Invalid column name '{k_clean}'")
                elif k_clean.lower() not in known_cols:
                    new_columns.add(k_clean)
                if v and len(str(v)) > 255:
                    errs.append(f"Value for '{k_clean}' exceeds 255 characters")

        stype = r.sim_type or ("E-SIM" if raw_iccid else "Plastic SIM")
        if stype == "E-SIM":
            esim_count += 1
        else:
            plastic_count += 1

        if not r.expiry_date:
            exp_counts["unknown"] += 1
        elif r.expiry_date < today:
            exp_counts["expired"] += 1
        elif r.expiry_date <= today + timedelta(days=30):
            exp_counts["expiring_soon"] += 1
        else:
            exp_counts["active"] += 1

        row_dict = r.model_dump()
        row_dict["sim_type"] = stype
        row_dict["row_num"] = idx
        row_dict["expiry_status"] = compute_expiry_status(r.expiry_date, 30)

        k_iccid, k_imei, k_sr = iccid_key(raw_iccid), raw_imei.lower(), raw_sr.lower()
        dup_reason = ""
        if k_iccid and k_iccid in seen_iccids:
            dup_reason = f"Duplicate ICCID '{raw_iccid}' repeats earlier in this uploaded file (same full value as row {seen_iccids[k_iccid]})"
        elif k_imei and k_imei in seen_imeis:
            dup_reason = f"Duplicate IMEI '{raw_imei}' repeats earlier in this uploaded file (same full value as row {seen_imeis[k_imei]})"
        elif k_sr and k_sr in seen_sr_nos:
            dup_reason = f"Duplicate Device Sr No '{raw_sr}' repeats earlier in this uploaded file (same full value as row {seen_sr_nos[k_sr]})"
        if k_iccid:
            seen_iccids.setdefault(k_iccid, idx)
        if k_imei:
            seen_imeis.setdefault(k_imei, idx)
        if k_sr:
            seen_sr_nos.setdefault(k_sr, idx)

        if dup_reason:
            row_dict.update(entry_type="Duplicate", status="Duplicate", reason=dup_reason)
            duplicates.append(row_dict)
            status.append("D")
            set_reason(i, dup_reason)
            continue
        if errs:
            reason = "; ".join(errs)
            eff_i = eff_cache[i]
            hit, hit_by = None, ""
            for lbl, mp, key in (("ICCID", by_iccid, k_iccid), ("IMEI", by_imei, k_imei or (eff_i or "").lower()),
                                 ("Device Sr No", by_sr, k_sr)):
                if key and key in mp:
                    hit, hit_by = mp[key], lbl
                    break
            if hit is not None:   # invalid AND already in the database -> duplicate, never pushed again
                reason = f"{reason}; {hit_by} already exists in the database" + (" (Recycle Bin)" if hit.deleted_at is not None else "")
                row_dict.update(entry_type="Duplicate", status="Duplicate", reason=reason,
                                existing_id=hit.id, existing_customer_name=cust_names.get(hit.customer_id, ""))
                duplicates.append(row_dict)
                status.append("D")
                set_reason(i, reason)
                continue
            row_dict.update(entry_type="Invalid", status="Invalid", reason=reason + " (will still be uploaded as it is)")
            invalids.append(row_dict)
            status.append("I")
            set_reason(i, reason)
            continue

        eff = eff_cache[i]
        matched, matched_by = None, ""
        for label, m, key in (("ICCID", by_iccid, k_iccid), ("IMEI", by_imei, k_imei or (eff or "").lower()),
                              ("Device Sr No", by_sr, k_sr)):
            if key and key in m:
                matched, matched_by = m[key], label
                break
        if not matched and eff and eff.lower() in by_imei:
            matched, matched_by = by_imei[eff.lower()], "IMEI"

        if matched is not None and matched.deleted_at is not None:
            reason = f"{matched_by} already exists in the Recycle Bin (restore it instead of uploading again)"
            row_dict.update(entry_type="Duplicate", status="Duplicate", reason=reason,
                            existing_id=matched.id, existing_customer_name=cust_names.get(matched.customer_id, ""))
            duplicates.append(row_dict)
            status.append("D")
            set_reason(i, reason)
        elif matched is not None and _identifier_conflict(r, matched, by_iccid, by_imei, by_sr):
            reason = _identifier_conflict(r, matched, by_iccid, by_imei, by_sr)
            row_dict.update(entry_type="Duplicate", status="Duplicate", reason=reason,
                            existing_id=matched.id, existing_customer_name=cust_names.get(matched.customer_id, ""))
            duplicates.append(row_dict)
            status.append("D")
            set_reason(i, reason)
        elif matched is not None:
            diffs = _row_diffs(r, matched)
            row_dict.update(existing_id=matched.id,
                            existing_customer_name=cust_names.get(matched.customer_id) or "General_Customer",
                            existing_imei=matched.imei or "", existing_iccid=matched.iccid or "",
                            existing_device_sr_no=matched.device_sr_no or "", changed_fields=diffs)
            if diffs:
                reason = f"{matched_by} already exists in database; {len(diffs)} field(s) differ and will be updated: " + ", ".join(d["label"] for d in diffs.values())
                row_dict.update(entry_type="Requires Update", status="Requires Update", reason=reason)
                entries_requiring_update.append(row_dict)
                status.append("U")
            else:
                reason = f"{matched_by} already exists in database with identical values (left unchanged)"
                row_dict.update(entry_type="Existing", status="Existing", reason=reason)
                existing_entries.append(row_dict)
                status.append("E")
            set_reason(i, reason)
        else:
            row_dict.update(entry_type="New", status="New", reason="New entry — eligible for insertion")
            new_entries.append(row_dict)
            status.append("N")

    valid = new_entries + entries_requiring_update
    cust_dups = {}
    for d in duplicates:
        cn = d.get("customer_name") or "General_Customer"
        cust_dups[cn] = cust_dups.get(cn, 0) + 1

    res = {
        "valid_count": len(valid),
        "new_count": len(new_entries),
        "updated_count": len(entries_requiring_update),
        "existing_count": len(existing_entries),
        "duplicate_count": len(duplicates),
        "invalid_count": len(invalids),
        "review_count": 0,
        "rejected_count": len(duplicates) + len(invalids),
        "total_count": n_rows,
        "esim_count": esim_count,
        "plastic_count": plastic_count,
        "new_customers": sorted(new_customers),
        "new_columns": sorted(new_columns),
        "missing_columns_warning": missing_columns,
        "customer_duplicates": cust_dups,
        "expiry_counts": exp_counts,
        "entries_requiring_update": entries_requiring_update[:2000],
        "updated_sample": entries_requiring_update[:2000],
        "new_sample": new_entries[:2000],
        "existing_sample": existing_entries[:2000],
        "valid_sample": valid[:2000],
        "duplicates": duplicates[:50000],
        "invalids": invalids[:2000],
        "invalid_sample": invalids[:2000],
        "all_sample": new_entries[:150] + entries_requiring_update[:150] + existing_entries[:150],
    }
    if compact:
        res["row_status"] = "".join(status)
        res["reason_table"] = reason_tbl
        res["row_reasons"] = row_reasons
    else:  # older pages (inventory.html) still read these lists
        res["new_iccids"] = [d.get("iccid") for d in new_entries if d.get("iccid")]
        res["new_imeis"] = [d.get("imei") for d in new_entries if d.get("imei")]
        res["existing_iccids"] = list(by_iccid.keys())
        res["existing_imeis"] = list(by_imei.keys())
        res["existing_sr_nos"] = list(by_sr.keys())
    return res


@router.post("/devices/bulk/rectify", dependencies=[Depends(require_permission("edit"))])
def bulk_rectify(data: schemas.BulkRectifyIn, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    """Rectify Update: Updates existing customer inventory records using validated Excel data.
    Does not overwrite existing valid information with blank cells.
    Preserves all existing relationships and logs telemetry."""
    rows = data.rows
    if not rows:
        return {"success_count": 0, "failed_count": 0, "successful_records": [], "failed_records": [], "message": "No rows provided for rectify update."}

    success_count = 0
    failed_count = 0
    successful_records = []
    failed_records = []

    for r in rows:
        try:
            dev = None
            if r.id:
                dev = db.query(Device).filter(Device.id == r.id, ACTIVE).first()
            if not dev and r.iccid:
                raw_iccid = clean_iccid(r.iccid)
                dev = db.query(Device).filter(Device.iccid == raw_iccid, ACTIVE).first()
            if not dev and r.imei:
                raw_imei = clean_imei(r.imei)
                dev = db.query(Device).filter(Device.imei == raw_imei, ACTIVE).first()
            if not dev and r.device_sr_no:
                dev = db.query(Device).filter(Device.device_sr_no == str(r.device_sr_no).strip(), ACTIVE).first()

            if not dev:
                failed_count += 1
                failed_records.append({
                    "identifier": r.iccid or r.imei or r.device_sr_no or str(r.id),
                    "reason": "Device record not found in database"
                })
                continue

            updated_fields = []
            updateable = [
                ("msisdn1", r.msisdn1),
                ("msisdn2", r.msisdn2),
                ("act_date", r.act_date),
                ("expiry_date", r.expiry_date),
                ("dispatched_date", r.dispatched_date),
                ("model", r.model),
                ("sim_provider", r.sim_provider),
                ("sim_type", r.sim_type),
                ("activation_plan", r.activation_plan),
                ("firmware", r.firmware),
                ("flash", r.flash),
                ("device_sr_no", r.device_sr_no)
            ]
            for f_name, f_val in updateable:
                if f_val is not None:
                    val_str = f_val.isoformat() if isinstance(f_val, date) else str(f_val).strip()
                    if val_str:
                        curr = getattr(dev, f_name)
                        curr_str = curr.isoformat() if isinstance(curr, date) else str(curr or "").strip()
                        if val_str != curr_str:
                            setattr(dev, f_name, f_val)
                            updated_fields.append(f_name)

            if r.extra and isinstance(r.extra, dict):
                curr_extra = dict(dev.extra or {})
                for ek, ev in r.extra.items():
                    if ev is not None and str(ev).strip():
                        curr_extra[str(ek).strip()] = str(ev).strip()
                dev.extra = curr_extra

            if updated_fields or (r.extra and isinstance(r.extra, dict)):
                success_count += 1
                successful_records.append({
                    "id": dev.id,
                    "imei": dev.imei,
                    "iccid": dev.iccid,
                    "customer_name": dev.customer.name if dev.customer else "",
                    "updated_fields": updated_fields
                })
            else:
                success_count += 1
        except Exception as e:
            failed_count += 1
            failed_records.append({
                "identifier": r.iccid or r.imei or str(r.id),
                "reason": str(e)
            })

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database commit failed during rectify update: {str(e)}")

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "successful_records": successful_records[:500],
        "failed_records": failed_records[:500],
        "message": f"Successfully rectified and updated {success_count} record(s) in customer inventory."
    }

def _short_err(e: Exception) -> str:
    return str(getattr(e, "orig", e))[:160]


def insert_chunk(db: Session, rows: list):
    """Inserts one chunk with a single multi-row INSERT and commits it.
    Returns (inserted_rows, failed) where failed = [{"imei", "reason"}].
    - Connection trouble: retried, then raised (nothing was saved, so the caller may safely resend the chunk).
    - A conflicting row: the clashing rows are removed and the rest is inserted in ONE more statement;
      only if that fails too are rows tried one by one, so a bad row never costs the good ones."""
    if not rows:
        return [], []
    last = None
    for attempt in range(3):
        try:
            db.execute(insert(Device), rows)
            db.commit()
            return list(rows), []
        except OperationalError as e:
            db.rollback()
            last = e
            time.sleep(1.0 * (attempt + 1))
        except Exception:
            db.rollback()
            last = None
            break
    else:
        raise HTTPException(503, f"Database is busy or unreachable, nothing from this batch was saved: {_short_err(last)}")

    # Something in this batch conflicts. Find the rows that already exist and drop them.
    failed, keep = [], []
    clash = set()
    imeis = [r["imei"] for r in rows]
    for i in range(0, len(imeis), 2000):
        for (v,) in db.query(Device.imei).filter(Device.imei.in_(imeis[i:i + 2000])):
            if v:
                clash.add(v.lower())
    for r in rows:
        if r["imei"].lower() in clash:
            failed.append({"imei": r["imei"], "reason": "IMEI already exists (saved by another upload a moment ago)"})
        else:
            keep.append(r)
    if keep:
        try:
            db.execute(insert(Device), keep)
            db.commit()
            return keep, failed
        except Exception:
            db.rollback()
    inserted = []
    for r in keep:
        try:
            db.execute(insert(Device), [r])
            db.commit()
            inserted.append(r)
        except Exception as e:
            db.rollback()
            failed.append({"imei": r["imei"], "reason": _short_err(e)})
    return inserted, failed


@router.post("/devices/bulk/prepare", dependencies=[Depends(require_permission("upload"))])
def bulk_prepare(data: dict = Body(...), db: Session = Depends(get_db)):
    """Creates (or revives) the customers of an upload BEFORE the batches start, so batches can run side by side
    without two of them trying to create the same customer."""
    names = []
    for n in (data.get("customers") or [])[:1000]:
        n = str(n or "").strip() or "General_Customer"
        if n not in names:
            names.append(n)
    made = []
    for n in names:
        c = customer_by_name(db, n)
        made.append({"id": c.id, "name": c.name})
    db.commit()
    return {"customers": made}


@router.post("/devices/bulk", dependencies=[Depends(require_permission("upload"))])
def bulk_add(data: schemas.BulkIn, db: Session = Depends(get_db),
             user: models.User = Depends(get_current_user)):
    """INSERT-ONLY (updates of existing rows go through /devices/bulk/update). Adds rows whose ICCID and IMEI are not in the database yet (recycle bin included) and not repeated
    inside the batch. Never updates or overwrites anything that exists.
    The answer says exactly what happened to every row: added, skipped (with the reason) or failed (with the reason)."""
    rows = data.rows
    iccids, imeis, srnos, prepared = set(), set(), set(), []
    for r in rows:
        raw_iccid = str(r.iccid or "").strip()
        raw_imei = str(r.imei or "").strip()
        raw_sr = str(r.device_sr_no or "").strip()
        imei = effective_imei(raw_imei, raw_sr, raw_iccid)  # the value that will really be stored
        prepared.append((r, raw_iccid, raw_imei, raw_sr, imei))
        if raw_iccid:
            iccids.add(raw_iccid)
        if imei:
            imeis.add(imei)
        if raw_sr:
            srnos.add(raw_sr)

    # What already exists? (lower-case key -> "is in recycle bin")
    ex_iccid, ex_imei, ex_sr = {}, {}, {}
    for keys, col, target in ((sorted(iccids), Device.iccid, ex_iccid), (sorted(imeis), Device.imei, ex_imei),
                              (sorted(srnos), Device.device_sr_no, ex_sr)):
        for i in range(0, len(keys), 2000):
            for v, gone in db.query(col, Device.deleted_at).filter(col.in_(keys[i:i + 2000])):
                if v:
                    k = v.lower()
                    target[k] = target.get(k, True) and gone is not None

    cache, skipped, failed = {}, [], []
    seen_iccid, seen_imei, seen_sr = set(), set(), set()
    new_rows, mirror_by_imei, names = [], {}, set()

    for row_ix, (r, raw_iccid, raw_imei, raw_sr, imei) in enumerate(prepared):
        label = raw_iccid or raw_imei or raw_sr or "(blank row)"
        try:
            generated = imei is None   # no usable identifier at all: a unique INV_ id is generated so the row is still saved
            if generated:
                imei = "INV_" + uuid.uuid4().hex[:12].upper()
            ck, ik = iccid_key(raw_iccid), imei.lower()

            reason = None
            if ck and ck in seen_iccid:
                reason = f"Duplicate ICCID '{raw_iccid}' repeats earlier in this upload (whole value identical)"
            elif not generated and ik in seen_imei:
                reason = "IMEI repeats earlier in this upload"
            elif ck and ck in ex_iccid:
                reason = f"Duplicate ICCID '{raw_iccid}' already exists in the database (whole value identical)" + (" (in Recycle Bin)" if ex_iccid[ck] else "")
            elif not generated and ik in ex_imei:
                reason = "IMEI already exists" + (" (in Recycle Bin)" if ex_imei[ik] else "")
            elif raw_sr and raw_sr.lower() in seen_sr:
                reason = "Device Sr No repeats earlier in this upload"
            elif raw_sr and raw_sr.lower() in ex_sr:
                reason = "Device Sr No already exists" + (" (in Recycle Bin)" if ex_sr[raw_sr.lower()] else "")
            if reason:
                skipped.append({"key": label, "reason": reason, "row": row_ix})
                continue

            cust_name = str(r.customer_name or "").strip() or "General_Customer"
            ckey = cust_name.lower().replace("_", " ")
            if ckey not in cache:
                cache[ckey] = customer_by_name(db, cust_name)
            cust = cache[ckey]

            exp = r.expiry_date or (r.act_date + timedelta(days=365) if r.act_date else None)
            stype = (r.sim_type or classify_sim_type(raw_iccid))[:20]
            extra = clean_extra(r.extra)
            names.update(extra)

            row_vals = {}
            for f in TEXT_FIELDS:
                val = getattr(r, f, None)
                row_vals[f] = str(val).strip()[:FIELD_MAX_LEN.get(f, 100)] if val is not None and str(val).strip() != "" else None

            new_rows.append(dict(customer_id=cust.id, imei=imei, act_date=r.act_date, expiry_date=exp,
                                 dispatched_date=r.dispatched_date, sim_type=stype, extra=extra or None,
                                 added_by=user.id, **row_vals))
            mirror_by_imei[imei] = (cust.id, cust.name, {"imei": imei, "customer_name": cust.name, "act_date": r.act_date,
                                                        "expiry_date": exp, "dispatched_date": r.dispatched_date,
                                                        "sim_type": stype, "extra": extra, **row_vals})
            if raw_iccid:
                seen_iccid.add(ck)
            if not generated:
                seen_imei.add(ik)
            if raw_sr:
                seen_sr.add(raw_sr.lower())
        except Exception as row_err:
            failed.append({"imei": label, "reason": _short_err(row_err)})

    try:
        db.commit()  # customers created above
    except Exception as ce:
        db.rollback()
        raise HTTPException(500, f"Could not save the customer records, nothing from this batch was saved: {_short_err(ce)}")

    inserted, insert_failed = insert_chunk(db, new_rows)
    failed.extend(insert_failed)

    if names:
        try:
            register_columns(db, names)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Column registry update failed: {e}")

    # Customer tables: ONLY rows that were really inserted.
    mirror_ok = True
    mirror = [mirror_by_imei[r["imei"]] for r in inserted if r["imei"] in mirror_by_imei]
    if mirror:
        try:
            if getattr(getattr(db, "bind", None), "dialect", None) and getattr(db.bind.dialect, "name", "") == "sqlite":
                customer_tables.mirror_rows(mirror, conn=db.connection())
                db.commit()
            else:
                customer_tables.mirror_rows(mirror)
        except Exception as e:
            mirror_ok = False
            print(f"Customer table sync failed: {e}")

    log_activity(db, "device_upload",
                 f"{len(inserted)} new entries added, {len(skipped)} existing/duplicate skipped, {len(failed)} failed (batch of {len(rows)})",
                 user=user)

    return {
        "ok": True,
        "added": len(inserted),
        "updated": 0,
        "skipped_duplicates": len(skipped),
        "skipped_imeis": [s["key"] for s in skipped[:50]],
        "skipped_detail": skipped,   # every skipped row with its position in the batch, so the page keeps them in Errored Entries
        "total_processed": len(rows),
        "failed": len(failed),
        "failed_rows": failed[:200],
        "mirror_ok": mirror_ok,
    }


@router.post("/devices/bulk/update", dependencies=[Depends(require_permission("upload")), Depends(require_permission("edit"))])
def bulk_update_existing(data: schemas.BulkIn, db: Session = Depends(get_db),
                         user: models.User = Depends(get_current_user)):
    """UPDATE-ONLY companion of /devices/bulk. For rows whose ICCID / IMEI / Sr No is already in the database (validation: 'Requires Update'),
    writes ONLY the cells that are filled in the file AND different from the stored value.
    Every other value of that record stays as it is, blank cells never erase data, identical records are not touched,
    customer and identifiers are never changed, recycle-bin records are never touched. Safe to resend (re-applying changes nothing)."""
    rows = data.rows
    s_ = lambda v: str(v or "").strip()
    iccids, imeis, srs, effs = set(), set(), set(), []
    for r in rows:
        e = effective_imei(r.imei, r.device_sr_no, r.iccid)
        effs.append(e)
        if s_(r.iccid):
            iccids.add(s_(r.iccid))
        if s_(r.imei):
            imeis.add(s_(r.imei))
        if e:
            imeis.add(e)
        if s_(r.device_sr_no):
            srs.add(s_(r.device_sr_no))
    by_iccid, by_imei, by_sr = _lookup_existing(db, iccids, imeis, srs)
    cust_names = {cid: name for cid, name in db.query(Customer.id, Customer.name)}

    updated, unchanged, skipped, failed = [], 0, [], []
    touched, mirror, new_cols = set(), [], set()
    for r, eff in zip(rows, effs):
        label = s_(r.imei) or s_(r.iccid) or s_(r.device_sr_no) or "(blank row)"
        try:
            k_iccid, k_imei, k_sr = iccid_key(r.iccid), s_(r.imei).lower(), s_(r.device_sr_no).lower()
            matched = None
            for m, key in ((by_iccid, k_iccid), (by_imei, k_imei or (eff or "").lower()), (by_sr, k_sr)):
                if key and key in m:
                    matched = m[key]
                    break
            if not matched and eff and eff.lower() in by_imei:
                matched = by_imei[eff.lower()]
            if matched is None:
                failed.append({"imei": label, "reason": "No existing record to update"})
                continue
            if matched.deleted_at is not None:
                skipped.append({"key": label, "reason": "Record is in the Recycle Bin (restore it first)"})
                continue
            if matched.id in touched:
                skipped.append({"key": label, "reason": "Same record was already updated by an earlier row of this upload"})
                continue
            conflict = _identifier_conflict(r, matched, by_iccid, by_imei, by_sr)
            if conflict:
                skipped.append({"key": label, "reason": conflict})
                continue
            diffs = _row_diffs(r, matched)
            touched.add(matched.id)
            if not diffs:
                unchanged += 1
                continue

            extra_changes = {}
            for key, d in diffs.items():
                if key.startswith("extra_"):
                    extra_changes[key[6:]] = d["new"]
                    continue
                val = getattr(r, key)
                if key in FIELD_MAX_LEN and isinstance(val, str):
                    val = val.strip()[:FIELD_MAX_LEN[key]]
                setattr(matched, key, val)
            if extra_changes:
                merged = dict(matched.extra or {})  # a NEW dict, so the JSON column change is noticed
                for k, v in extra_changes.items():
                    merged[k[:100]] = v[:500]
                matched.extra = merged
                new_cols.update(k[:100] for k in extra_changes)

            cname = cust_names.get(matched.customer_id) or "General_Customer"
            row = {"imei": matched.imei, "customer_name": cname, "extra": dict(matched.extra or {})}
            row.update({f: getattr(matched, f) for f in customer_tables.BASE_NAMES if f != "customer_name"})
            mirror.append((matched.customer_id, cname, row))
            updated.append({"imei": matched.imei, "customer": cname,
                            "changed": [{"field": d["label"], "old": d["old"], "new": d["new"]} for d in diffs.values()]})
        except Exception as row_err:
            failed.append({"imei": label, "reason": _short_err(row_err)})

    try:
        if new_cols:
            register_columns(db, new_cols)
        db.commit()
    except Exception as ce:
        db.rollback()
        # nothing of this batch was saved; the page retries it (re-applying is harmless)
        raise HTTPException(503, f"Could not save the updates, nothing from this batch was changed: {_short_err(ce)}")

    mirror_ok = True
    if mirror:
        try:
            if getattr(getattr(db, "bind", None), "dialect", None) and getattr(db.bind.dialect, "name", "") == "sqlite":
                customer_tables.mirror_rows(mirror, conn=db.connection())
                db.commit()
            else:
                customer_tables.mirror_rows(mirror)
        except Exception as e:
            mirror_ok = False
            print(f"Customer table sync failed after update: {e}")

    log_activity(db, "device_upload_update",
                 f"{len(updated)} existing entries updated, {unchanged} unchanged, {len(skipped)} skipped, {len(failed)} failed (batch of {len(rows)})",
                 user=user, commit=True)
    return {"ok": True, "updated": len(updated), "unchanged": unchanged, "skipped": len(skipped),
            "skipped_detail": skipped[:200], "failed": len(failed), "failed_rows": failed[:200],
            "updated_detail": updated[:200], "total_processed": len(rows), "mirror_ok": mirror_ok}


@router.post("/devices/sheet-upload", dependencies=[Depends(require_permission("upload"))])
def sheet_upload(data: schemas.BulkIn, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    return bulk_add(data, db, user)


@router.post("/devices", status_code=201, dependencies=[Depends(require_permission("add"))])
def add_device(data: schemas.DeviceIn, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    if not data.imei or len(data.imei) < 5 or not data.customer_name:
        raise HTTPException(400, "Customer name and a valid IMEI are required.")
    res = bulk_add(schemas.BulkIn(rows=[data]), db, user)
    if not res["added"]:
        raise HTTPException(400, "A device with this IMEI already exists (it may be in Deleted Customers).")
    return res


def clean_imei(val) -> str:
    if not val:
        return ""
    s = str(val).strip()
    if re.search(r"e\+", s, re.I):
        try:
            return str(int(float(s)))
        except Exception:
            pass
    s = re.sub(r"[^0-9A-Za-z_-]", "", s)
    return s.strip()




# ==============================================================================
# WHAT IS HAPPENING BELOW:
# High-Volume Batch Lookup Engine (/api/fetch/bulk):
# Powers the Bulk Fetch (from Excel) feature:
# 1. Accepts thousands of query terms (IMEIs, ICCIDs, Serials) in a single request.
# 2. Cleans and normalizes all terms (protecting against Excel scientific notation truncation).
# 3. Executes high-performance chunked exact-match database queries.
# 4. Distinguishes exact hits from partial hits: partial hits are returned separately
#    and never reported as found, guaranteeing data integrity.
# ==============================================================================
@router.post("/fetch/bulk", dependencies=[Depends(require_permission("search"))])
def bulk_fetch(data: schemas.BulkFetchIn, db: Session = Depends(get_db)):
    raw_terms = [q.strip() for q in data.queries if q.strip()]
    if not raw_terms:
        return {
            "exact_matches": [], "similar_matches": [],
            "total_matches": 0, "values_searched_count": 0,
            "values_found_count": 0, "not_found_values": []
        }

    seen = set()
    terms = []
    for t in raw_terms:
        if t not in seen:
            seen.add(t)
            terms.append(t)

    field = (data.field or "all").strip().lower()
    if field in ("iccid", "ccid"):
        field = "iccid"
    cust_id = data.customer_id
    sim_type = data.sim_type or "all"

    base_query = db.query(Device).options(joinedload(Device.customer)).filter(ACTIVE)
    if cust_id:
        base_query = base_query.filter(Device.customer_id == cust_id)

    if sim_type == "esim":
        base_query = base_query.filter(or_(
            func.upper(Device.sim_type) == 'E-SIM',
            and_(or_(Device.sim_type.is_(None), Device.sim_type == ''), Device.iccid.isnot(None), Device.iccid != '')
        ))
    elif sim_type == "plastic":
        base_query = base_query.filter(or_(
            func.upper(Device.sim_type).in_(['PLASTIC SIM', 'PLASTIC']),
            and_(or_(Device.sim_type.is_(None), Device.sim_type == ''), or_(Device.iccid.is_(None), Device.iccid == ''))
        ))

    exact_items = []
    chunk_size = 2000
    for i in range(0, len(terms), chunk_size):
        sub_terms = terms[i:i + chunk_size]
        q = base_query
        if field == "imei":
            q = q.filter(Device.imei.in_(sub_terms))
        elif field in ("iccid", "ccid"):
            clean_terms = [clean_iccid(x) for x in sub_terms if x]
            stripped_terms = [c.rstrip("F") for c in clean_terms if c]
            f_terms = [c.rstrip("F") + "F" for c in clean_terms if c]
            p19 = [c[:19] for c in clean_terms if len(c) >= 19]
            iccid_search = list(set(sub_terms + clean_terms + stripped_terms + f_terms))
            iccid_conds = [Device.iccid.in_(iccid_search)]
            if p19:
                iccid_conds.append(func.left(Device.iccid, 19).in_(p19))
            q = q.filter(or_(*iccid_conds))
        elif field == "device_sr_no":
            q = q.filter(Device.device_sr_no.in_(sub_terms))
        elif field == "msisdn1":
            q = q.filter(Device.msisdn1.in_(sub_terms))
        elif field == "customer_name":
            q = q.join(Customer).filter(Customer.name.in_(sub_terms))
        elif field not in ("all", ""):
            # Specific unique/custom column search in bulk fetch
            unique_conds = []
            for t in sub_terms:
                unique_conds.append(func.json_unquote(func.json_extract(Device.extra, f'$."{field}"')) == t)
                unique_conds.append(cast(Device.extra, String).like(f'%"{t}"%'))
            q = q.filter(or_(*unique_conds))
        else:
            clean_terms = [clean_iccid(x) for x in sub_terms if x]
            stripped_terms = [c.rstrip("F") for c in clean_terms if c]
            f_terms = [c.rstrip("F") + "F" for c in clean_terms if c]
            iccid_search = list(set(sub_terms + clean_terms + stripped_terms + f_terms))
            extra_matches = [cast(Device.extra, String).like(f'%"{t}"%') for t in sub_terms[:50]]
            q = q.filter(or_(
                Device.imei.in_(sub_terms),
                Device.iccid.in_(iccid_search),
                Device.device_sr_no.in_(sub_terms),
                Device.msisdn1.in_(sub_terms),
                Device.msisdn2.in_(sub_terms),
                *extra_matches
            ))
        exact_items.extend(q.all())

    # Fetch live MSISDN1, MSISDN2, Act Date, Expiry Date from Sensorise server and update DB
    try:
        exact_items = sync_devices_with_sensorise(db, exact_items)
    except Exception as _sync_err:
        pass

    exact_ids = {d.id for d in exact_items}

    matched_term_set = set()
    for d in exact_items:
        d_iccid_clean = clean_iccid(d.iccid) if d.iccid else ""
        for t in (d.imei, d.iccid, d.device_sr_no, d.msisdn1, d.msisdn2, (d.customer.name if d.customer else "")):
            if t and t in seen:
                matched_term_set.add(t)
            elif t and clean_iccid(t) in seen:
                matched_term_set.add(clean_iccid(t))
        d_extra = d.extra or {}
        if isinstance(d_extra, str):
            try:
                import json
                d_extra = json.loads(d_extra)
            except Exception:
                d_extra = {}
        for ev in d_extra.values():
            if ev and str(ev).strip() in seen:
                matched_term_set.add(str(ev).strip())
        for t in terms:
            t_clean = clean_iccid(t)
            if t_clean and d_iccid_clean and (
                t_clean == d_iccid_clean or
                t_clean.rstrip("F") == d_iccid_clean.rstrip("F") or
                (len(t_clean) >= 19 and len(d_iccid_clean) >= 19 and t_clean[:19] == d_iccid_clean[:19])
            ):
                matched_term_set.add(t)

    unmatched_terms = [t for t in terms if t not in matched_term_set]
    similar_items = []
    similar_terms_to_check = unmatched_terms[:300] if getattr(data, "include_similar", True) else []

    for t in similar_terms_to_check:
        like = f"%{escape_like(t)}%"
        sim_q = base_query
        if field == "imei":
            sim_q = sim_q.filter(Device.imei.like(like))
        elif field in ("iccid", "ccid"):
            clean_t = clean_iccid(t)
            sim_conds = [Device.iccid.like(like)]
            if clean_t:
                sim_conds.append(Device.iccid.like(f"%{escape_like(clean_t)}%"))
                if clean_t.rstrip("F") != clean_t:
                    sim_conds.append(Device.iccid.like(f"%{escape_like(clean_t.rstrip('F'))}%"))
            sim_q = sim_q.filter(or_(*sim_conds))
        elif field == "customer_name":
            sim_q = sim_q.join(Customer).filter(Customer.name.like(like))
        else:
            clean_t = clean_iccid(t)
            sim_or = [
                Device.imei.like(like),
                Device.iccid.like(like),
                Device.device_sr_no.like(like),
                Device.msisdn1.like(like)
            ]
            if clean_t:
                sim_or.append(Device.iccid.like(f"%{escape_like(clean_t)}%"))
            sim_q = sim_q.filter(or_(*sim_or))
        found = sim_q.limit(10).all()
        for s in found:
            if s.id not in exact_ids and s.id not in {x.id for x in similar_items}:
                similar_items.append(s)
                matched_term_set.add(t)

    not_found_values = [t for t in terms if t not in matched_term_set]

    all_returned = exact_items + similar_items
    all_imeis = [d.imei for d in all_returned if d.imei]
    all_iccids = [d.iccid for d in all_returned if d.iccid]
    all_srnos = [d.device_sr_no for d in all_returned if d.device_sr_no]

    dup_imeis = {i for i, in db.query(Device.imei).filter(ACTIVE, Device.imei.in_(all_imeis)).group_by(Device.imei).having(func.count(Device.id) > 1)} if all_imeis else set()
    dup_iccids = {i for i, in db.query(Device.iccid).filter(ACTIVE, Device.iccid.in_(all_iccids)).group_by(Device.iccid).having(func.count(Device.id) > 1)} if all_iccids else set()
    dup_srnos = {i for i, in db.query(Device.device_sr_no).filter(ACTIVE, Device.device_sr_no.in_(all_srnos)).group_by(Device.device_sr_no).having(func.count(Device.id) > 1)} if all_srnos else set()

    def format_item(d, is_exact):
        res = out(d)
        res["is_exact"] = is_exact
        res["has_duplicates"] = (d.imei in dup_imeis or d.iccid in dup_iccids or d.device_sr_no in dup_srnos)
        res["duplicate_fields"] = [f for f, is_dup in [("IMEI", d.imei in dup_imeis), ("ICCID", d.iccid in dup_iccids), ("Sr No", d.device_sr_no in dup_srnos)] if is_dup]
        return res

    exact_res = [format_item(d, True) for d in exact_items]
    similar_res = [format_item(d, False) for d in similar_items]

    return {
        "exact_matches": exact_res,
        "similar_matches": similar_res,
        "total_matches": len(exact_res) + len(similar_res),
        "values_searched_count": len(terms),
        "values_found_count": len(terms) - len(not_found_values),
        "not_found_values": not_found_values
    }



@router.post("/fetch/sync", dependencies=[Depends(require_permission("search"))])
def fetch_sync(data: schemas.FetchSyncIn, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    """Fetch Data: Validates queries, matches records using ICCID/CCID or other identifiers,
    retrieves/updates available fields, and returns separate successful and error entries."""
    terms = [q.strip() for q in data.queries if q.strip()]
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    if not terms:
        return {
            "total_scanned": 0,
            "success_count": 0,
            "error_count": 0,
            "successful_records": [],
            "error_entries": []
        }

    # Query matching devices by ICCID, IMEI, device_sr_no
    clean_iccids = [clean_iccid(t) for t in terms if t]
    clean_imeis = [clean_imei(t) for t in terms if t]

    devs_by_iccid = {}
    for i in range(0, len(clean_iccids), 2000):
        for d in db.query(Device).options(joinedload(Device.customer)).filter(Device.iccid.in_(clean_iccids[i:i+2000]), ACTIVE):
            if d.iccid:
                devs_by_iccid[d.iccid] = d
                devs_by_iccid[clean_iccid(d.iccid)] = d

    devs_by_imei = {}
    for i in range(0, len(clean_imeis), 2000):
        for d in db.query(Device).options(joinedload(Device.customer)).filter(Device.imei.in_(clean_imeis[i:i+2000]), ACTIVE):
            if d.imei:
                devs_by_imei[d.imei] = d
                devs_by_imei[clean_imei(d.imei)] = d

    # Optional update map by ICCID
    update_map = {}
    if data.update_data:
        for u in data.update_data:
            ic = clean_iccid(u.get("iccid") or u.get("ccid") or "")
            if ic:
                update_map[ic] = u

    successful_records = []
    error_entries = []
    seen_error_keys = set()

    for term in terms:
        clean_ic = clean_iccid(term)
        clean_im = clean_imei(term)

        matched_dev = None
        if clean_ic and clean_ic in devs_by_iccid:
            matched_dev = devs_by_iccid[clean_ic]
        elif clean_im and clean_im in devs_by_imei:
            matched_dev = devs_by_imei[clean_im]

        if matched_dev:
            # Check if there is incoming data to update
            u_data = update_map.get(clean_ic) or update_map.get(clean_im)
            if u_data:
                for f_name in ("msisdn1", "msisdn2", "act_date", "expiry_date", "sim_provider"):
                    if u_data.get(f_name) is not None:
                        val = u_data.get(f_name)
                        val_str = val.isoformat() if isinstance(val, date) else str(val).strip()
                        if val_str:
                            setattr(matched_dev, f_name, val)

            successful_records.append({
                "id": matched_dev.id,
                "customer_name": matched_dev.customer.name if matched_dev.customer else "General_Customer",
                "imei": matched_dev.imei,
                "iccid": matched_dev.iccid,
                "msisdn1": matched_dev.msisdn1 or "—",
                "msisdn2": matched_dev.msisdn2 or "—",
                "act_date": matched_dev.act_date.isoformat() if matched_dev.act_date else "—",
                "expiry_date": matched_dev.expiry_date.isoformat() if matched_dev.expiry_date else "—",
                "sim_provider": matched_dev.sim_provider or "—",
                "model": matched_dev.model or "—",
                "status": "SUCCESS"
            })
        else:
            # Check sensorise_sims_basic table before marking as not found
            basic_row = None
            try:
                basic_row = db.execute(text("""
                    SELECT device_sr_no, imei, iccid, msisdn1, msisdn2, activation_date, expiry_date
                    FROM sensorise_sims_basic
                    WHERE iccid = :t OR iccid = :t_f OR iccid = :t_strip OR imei = :t
                    LIMIT 1
                """), {
                    "t": term,
                    "t_f": term + "F",
                    "t_strip": term.rstrip("F")
                }).first()
            except Exception:
                pass

            if basic_row:
                successful_records.append({
                    "id": f"sensorise_{basic_row[2]}",
                    "customer_name": "Sensorise SIM Inventory",
                    "imei": basic_row[1] or "—",
                    "iccid": basic_row[2] or term,
                    "msisdn1": basic_row[3] or "—",
                    "msisdn2": basic_row[4] or "—",
                    "act_date": str(basic_row[5] or "—"),
                    "expiry_date": str(basic_row[6] or "—"),
                    "sim_provider": "Sensorise",
                    "model": "—",
                    "status": "SUCCESS"
                })
            else:
                # Error / Unmatched Entry
                if term not in seen_error_keys:
                    seen_error_keys.add(term)
                    err_reason = "No matching device record found in database"
                    if not clean_ic and not clean_im:
                        err_reason = "Invalid or empty identifier format"
                    error_entries.append({
                        "iccid": term,
                        "customer_name": "—",
                        "error_reason": err_reason,
                        "fetch_status": "NOT FOUND",
                        "api_response": "Device record not found across active customer tables",
                        "processed_at": now_str
                    })

    if data.update_data:
        try:
            db.commit()
        except Exception as e:
            db.rollback()

    # Fetch live MSISDN1, MSISDN2, Act Date, Expiry Date from Sensorise server and update DB
    try:
        successful_records = sync_device_dicts_with_sensorise(db, successful_records)
    except Exception as _sync_err:
        pass

    return {
        "total_scanned": len(terms),
        "success_count": len(successful_records),
        "error_count": len(error_entries),
        "successful_records": successful_records[:2000],
        "error_entries": error_entries
    }


@router.get("/devices/quick-search", dependencies=[Depends(require_permission("search"))])
def quick_search(q: str = Query("", min_length=1), db: Session = Depends(get_db),
                 user: Optional[models.User] = Depends(get_current_user)):
    term = q.strip()
    if not term:
        return {"customers": [], "devices": []}
    like = f"%{escape_like(term)}%"

    custs = db.query(Customer).filter(Customer.deleted_at.is_(None), Customer.name.like(like)).limit(5).all()

    devs = (db.query(Device).options(joinedload(Device.customer))
            .filter(ACTIVE, or_(
                Device.imei == term,
                Device.iccid == term,
                Device.device_sr_no == term,
                Device.imei.like(like),
                Device.iccid.like(like),
                Device.device_sr_no.like(like),
                Device.msisdn1.like(like),
                Device.model.like(like)
            )).limit(10).all())

    res_count = len(custs) + len(devs)
    try:
        log_activity(db, "search", f"Quick Search: '{term}' [Results: {res_count}]", user=user, commit=True)
    except Exception:
        pass

    return {
        "customers": [{"id": c.id, "name": c.name, "exact": c.name.lower() == term.lower()} for c in custs],
        "devices": [{**out(d), "exact": term.lower() in [str(d.imei or '').lower(), str(d.iccid or '').lower(), str(d.device_sr_no or '').lower()]} for d in devs]
    }


@router.get("/inventory/insights", dependencies=[Depends(require_permission("view"))])
def inventory_insights(db: Session = Depends(get_db)):
    today = date.today()
    soon_30 = today + timedelta(days=30)
    over_4m = today + timedelta(days=120)

    total_devices = db.query(func.count(Device.id)).filter(ACTIVE).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).filter(Customer.deleted_at.is_(None)).scalar() or 0
    expired = db.query(func.count(Device.id)).filter(ACTIVE, Device.expiry_date < today).scalar() or 0
    expiring_30 = db.query(func.count(Device.id)).filter(ACTIVE, Device.expiry_date >= today, Device.expiry_date <= soon_30).scalar() or 0
    expiring_over_4m = db.query(func.count(Device.id)).filter(ACTIVE, Device.expiry_date > over_4m).scalar() or 0

    timeline_raw = (db.query(func.date_format(Device.expiry_date, '%Y-%m').label('month'), func.count(Device.id))
                    .filter(ACTIVE, Device.expiry_date.isnot(None))
                    .group_by('month').order_by('month').all())
    timeline = [{"month": m, "count": c} for m, c in timeline_raw if m]

    by_cust = (db.query(Customer.name, func.count(Device.id).label('cnt'))
               .join(Device, (Device.customer_id == Customer.id) & ACTIVE)
               .filter(Customer.deleted_at.is_(None))
               .group_by(Customer.id, Customer.name).order_by(desc('cnt')).limit(10).all())

    by_provider = (db.query(func.coalesce(Device.sim_provider, 'Not specified'), func.count(Device.id))
                   .filter(ACTIVE).group_by(Device.sim_provider).order_by(desc(func.count(Device.id))).all())

    by_model = (db.query(func.coalesce(Device.model, 'Not specified'), func.count(Device.id))
                .filter(ACTIVE).group_by(Device.model).order_by(desc(func.count(Device.id))).all())

    by_plan = (db.query(func.coalesce(Device.activation_plan, 'Not specified'), func.count(Device.id))
               .filter(ACTIVE).group_by(Device.activation_plan).order_by(desc(func.count(Device.id))).all())

    recent = (db.query(Device).options(joinedload(Device.customer))
              .filter(ACTIVE).order_by(Device.id.desc()).limit(10).all())

    user_ids = {d.added_by for d in recent if d.added_by}
    user_map = {u.id: u.name for u in db.query(models.User).filter(models.User.id.in_(list(user_ids))).all()} if user_ids else {}

    recent_list = []
    for d in recent:
        item = out(d)
        item["added_by_name"] = user_map.get(d.added_by, f"User #{d.added_by}" if d.added_by else "System / Bulk")
        recent_list.append(item)

    return {
        "total_devices": total_devices,
        "total_customers": total_customers,
        "expired": expired,
        "expiring_30": expiring_30,
        "expiring_over_4m": expiring_over_4m,
        "timeline": timeline,
        "by_customer": [{"name": n, "count": c} for n, c in by_cust],
        "by_provider": [{"name": n, "count": c} for n, c in by_provider[:10]],
        "by_model": [{"name": n, "count": c} for n, c in by_model[:10]],
        "by_plan": [{"name": n, "count": c} for n, c in by_plan[:10]],
        "recent_added": recent_list
    }


@router.get("/inventory/health", dependencies=[Depends(require_permission("view"))])
def inventory_health(page: int = 1, page_size: int = 10,
                     select_all: bool = False, q: Optional[str] = None, db: Session = Depends(get_db)):
    if hasattr(page, "query"):
        db = page
        page = 1
        page_size = 10
    else:
        if hasattr(page_size, "default"):
            page_size = int(page_size.default)
        else:
            page_size = int(page_size) if page_size else 10
        if hasattr(page, "default"):
            page = int(page.default)
        else:
            page = int(page) if page else 1
    def find_dups(column):
        return db.query(column, func.count(Device.id)).filter(ACTIVE, column.isnot(None), column != '').group_by(column).having(func.count(Device.id) > 1).all()

    dup_imei = find_dups(Device.imei)
    dup_iccid = find_dups(Device.iccid)
    dup_m1 = find_dups(Device.msisdn1)
    dup_m2 = find_dups(Device.msisdn2)
    dup_sr = find_dups(Device.device_sr_no)

    total = db.query(func.count(Device.id)).filter(ACTIVE).scalar() or 0

    # Accurate, safe counts for bad IMEIs and bad date sequences
    bad_imei_cnt = db.query(func.count(Device.id)).filter(ACTIVE, or_(Device.imei.is_(None), func.length(Device.imei) != 15)).scalar() or 0
    bad_date_cnt = db.query(func.count(Device.id)).filter(ACTIVE, Device.act_date.isnot(None), Device.expiry_date.isnot(None), Device.expiry_date < Device.act_date).scalar() or 0

    bad_imeis = (db.query(Device).options(joinedload(Device.customer))
                 .filter(ACTIVE, or_(Device.imei.is_(None), func.length(Device.imei) != 15))
                 .limit(50).all())

    bad_dates = (db.query(Device).options(joinedload(Device.customer))
                 .filter(ACTIVE, Device.act_date.isnot(None), Device.expiry_date.isnot(None), Device.expiry_date < Device.act_date)
                 .limit(50).all())

    cols = ["customer_name", "device_sr_no", "imei", "iccid", "msisdn1", "msisdn2", "act_date", "expiry_date",
            "dispatched_date", "model", "sim_provider", "activation_plan", "firmware", "flash", "sim_type"]
    completeness = {}
    if total > 0:
        try:
            from sqlalchemy import case, and_
            comp_exprs = [
                func.count(case((and_(Customer.name.isnot(None), Customer.name != ''), 1))).label("customer_name")
            ] + [
                func.count(case((and_(getattr(Device, c).isnot(None), getattr(Device, c) != ''), 1))).label(c)
                for c in cols if c != "customer_name"
            ]
            row = db.query(*comp_exprs).outerjoin(Customer, Device.customer_id == Customer.id).filter(ACTIVE).first()
            if row:
                for idx, c in enumerate(cols):
                    cnt = row[idx] or 0
                    completeness[c] = round((cnt / total) * 100, 1)
        except Exception as e:
            print(f"Fast completeness query fallback: {e}")
            for c in cols:
                if c == "customer_name":
                    cnt = db.query(func.count(Device.id)).join(Customer).filter(ACTIVE, Customer.name.isnot(None), Customer.name != '').scalar() or 0
                else:
                    attr = getattr(Device, c)
                    cnt = db.query(func.count(Device.id)).filter(ACTIVE, attr.isnot(None), attr != '').scalar() or 0
                completeness[c] = round((cnt / total) * 100, 1)

    issues = []
    for val, count in dup_imei[:25]:
        issues.append({"type": "Duplicate IMEI", "identifier": val, "count": count, "description": f"IMEI {val} appears {count} times"})
    for val, count in dup_iccid[:25]:
        issues.append({"type": "Duplicate ICCID", "identifier": val, "count": count, "description": f"ICCID {val} appears {count} times"})
    for val, count in dup_sr[:25]:
        issues.append({"type": "Duplicate Sr No", "identifier": val, "count": count, "description": f"Device Sr No {val} appears {count} times"})
    for d in bad_imeis[:25]:
        issues.append({"type": "Invalid IMEI Length", "identifier": d.imei, "count": 1, "description": f"Device #{d.id} IMEI '{d.imei}' has length {len(d.imei or '')} (expected 15 digits)"})
    for d in bad_dates[:25]:
        issues.append({"type": "Expiry Before Activation", "identifier": d.imei, "count": 1, "description": f"Device #{d.id} expires on {d.expiry_date} before activation on {d.act_date}"})

    # Filter issues by search term if provided
    filtered_issues = issues
    if q and q.strip():
        term = q.strip().lower()
        filtered_issues = [
            iss for iss in issues
            if term in str(iss.get("type", "")).lower()
            or term in str(iss.get("identifier", "")).lower()
            or term in str(iss.get("description", "")).lower()
        ]

    total_issues = len(filtered_issues)
    total_pages = math.ceil(total_issues / page_size) if page_size > 0 else 1
    if total_pages < 1:
        total_pages = 1

    if select_all:
        displayed_issues = filtered_issues
    else:
        start_idx = (page - 1) * page_size
        displayed_issues = filtered_issues[start_idx : start_idx + page_size]

    health_score = round(max(0, 100 - ((len(dup_imei) * 2 + len(dup_iccid) * 2 + bad_imei_cnt + bad_date_cnt) / max(1, total)) * 100), 1) if total else 100

    return {
        "score": health_score,
        "total_records": total,
        "duplicate_imei_count": len(dup_imei),
        "duplicate_iccid_count": len(dup_iccid),
        "duplicate_msisdn1_count": len(dup_m1),
        "duplicate_msisdn2_count": len(dup_m2),
        "duplicate_sr_count": len(dup_sr),
        "bad_imei_count": bad_imei_cnt,
        "bad_date_count": bad_date_cnt,
        "completeness": completeness,
        "total_issues": total_issues,
        "page": page,
        "page_size": page_size,
        "pages": total_pages,
        "select_all": select_all,
        "issues": displayed_issues
    }


@router.get("/inventory/report", dependencies=[Depends(require_permission("download"))])
def inventory_report(db: Session = Depends(get_db)):
    today = date.today()
    soon_30 = today + timedelta(days=30)

    rows = (db.query(
                Customer.id, Customer.name,
                func.count(Device.id).label('total'),
                func.sum(case((Device.expiry_date > soon_30, 1), else_=0)).label('active'),
                func.sum(case(((Device.expiry_date >= today) & (Device.expiry_date <= soon_30), 1), else_=0)).label('expiring'),
                func.sum(case((Device.expiry_date < today, 1), else_=0)).label('expired')
            )
            .outerjoin(Device, (Device.customer_id == Customer.id) & ACTIVE)
            .filter(Customer.deleted_at.is_(None))
            .group_by(Customer.id, Customer.name).order_by(Customer.name).all())

    return [{"id": i, "name": n, "total": int(t or 0), "active": int(a or 0), "expiring_30": int(e or 0), "expired": int(x or 0)} for i, n, t, a, e, x in rows]


@router.post("/export", dependencies=[Depends(require_permission("download"))])
def export_excel(data: schemas.ExportIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    buf = make_excel(data.title or "CustomerVault_Export", data.headers, data.rows)
    clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', data.title or 'Export')
    filename = f"{clean_title}_{date.today().isoformat()}.xlsx"
    log_activity(db, "export_excel", f"Exported {len(data.rows)} rows ({data.title})", user=user)
    db.commit()
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )


@router.post("/columns/add", dependencies=[Depends(require_permission("add"))])
def add_column(data: schemas.AddColumnIn, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    col_name = data.column_name.strip()
    if not col_name:
        raise HTTPException(400, "Column name cannot be blank.")
    norm = col_name.lower().replace(' ', '_')
    if norm in BASE_COLUMNS:
        raise HTTPException(400, f"'{col_name}' is a core system column and cannot be added as a custom column.")

    # 1. Register the column in ColumnRegistry
    register_columns(db, [col_name])

    # 2. Select target devices
    query = db.query(Device).options(joinedload(Device.customer)).filter(ACTIVE)
    if data.target == "customer" and data.customer_id:
        query = query.filter(Device.customer_id == data.customer_id)
    elif data.target == "specified":
        raw_imeis = data.imeis or []
        cleaned_imeis = [re.sub(r"\D", "", str(s)) for s in raw_imeis if re.sub(r"\D", "", str(s))]
        if not cleaned_imeis:
            raise HTTPException(400, "Please provide at least one valid IMEI for specified entries.")
        query = query.filter(Device.imei.in_(cleaned_imeis))
        if data.customer_id:
            query = query.filter(Device.customer_id == data.customer_id)
    elif data.target == "all" and data.customer_id:
        query = query.filter(Device.customer_id == data.customer_id)

    val_to_set = str(data.value).strip() if data.value is not None else ""
    if data.value is None or (data.target != "specified" and not val_to_set):
        db.commit()
        log_activity(db, "column_add", f"Added column '{col_name}'", user=user)
        return {"column": col_name, "value": None, "records_affected": 0}

    # 2. Fast SQL JSON_SET update
    json_path = f"$.\"{col_name}\""
    where_clauses = ["deleted_at IS NULL"]
    params = {"path": json_path, "val": val_to_set}

    if data.target == "customer" and data.customer_id:
        where_clauses.append("customer_id = :cid")
        params["cid"] = data.customer_id
    elif data.target == "specified":
        raw_imeis = data.imeis or []
        cleaned_imeis = [re.sub(r"\D", "", str(s)) for s in raw_imeis if re.sub(r"\D", "", str(s))]
        if not cleaned_imeis:
            raise HTTPException(400, "Please provide at least one valid IMEI for specified entries.")
        where_clauses.append("imei IN :imeis")
        params["imeis"] = tuple(cleaned_imeis)
        if data.customer_id:
            where_clauses.append("customer_id = :cid")
            params["cid"] = data.customer_id
    elif data.target == "all" and data.customer_id:
        where_clauses.append("customer_id = :cid")
        params["cid"] = data.customer_id

    sql = f"UPDATE sim_devices SET extra = JSON_SET(COALESCE(extra, '{{}}'), :path, :val) WHERE {' AND '.join(where_clauses)}"
    res = db.execute(text(sql), params)
    count_affected = res.rowcount
    db.commit()

    # 3. Mirror to customer tables
    if data.target == "customer" and data.customer_id:
        cust = db.query(models.Customer).filter(models.Customer.id == data.customer_id).first()
        if cust:
            def _mirror_cust(cid, cname, col, v):
                try:
                    with customer_tables.engine.begin() as conn:
                        t = customer_tables.ensure_table(conn, cid, cname, [col])
                        c_col = customer_tables.extra_col(col)
                        conn.execute(text(f"UPDATE `{t}` SET `{c_col}` = :v"), {"v": v})
                except Exception as e:
                    print(f"Error updating customer table for column add: {e}")
            import threading
            threading.Thread(target=_mirror_cust, args=(cust.id, cust.name, col_name, val_to_set), daemon=True).start()
    elif data.target == "specified":
        cleaned_imeis = [re.sub(r"\D", "", str(s)) for s in (data.imeis or []) if re.sub(r"\D", "", str(s))]
        if cleaned_imeis:
            def _mirror_specified(imeis_list):
                try:
                    with SessionLocal() as s_db:
                        devs = s_db.query(Device).options(joinedload(Device.customer)).filter(Device.imei.in_(imeis_list), ACTIVE).all()
                        m_items = []
                        for d in devs:
                            cname = d.customer.name if d.customer else "Unknown"
                            r_dict = {
                                "imei": d.imei,
                                "device_sr_no": d.device_sr_no,
                                "iccid": d.iccid,
                                "msisdn1": d.msisdn1,
                                "msisdn2": d.msisdn2,
                                "act_date": d.act_date,
                                "expiry_date": d.expiry_date,
                                "dispatched_date": d.dispatched_date,
                                "model": d.model,
                                "sim_provider": d.sim_provider,
                                "activation_plan": d.activation_plan,
                                "firmware": d.firmware,
                                "flash": d.flash,
                                "sim_type": d.sim_type,
                                "extra": dict(d.extra or {})
                            }
                            m_items.append((d.customer_id, cname, r_dict))
                        if m_items:
                            customer_tables.mirror_rows(m_items)
                except Exception as e:
                    print(f"Error mirroring specified items: {e}")
            import threading
            threading.Thread(target=_mirror_specified, args=(cleaned_imeis,), daemon=True).start()

    log_activity(db, "column_add", f"Added column '{col_name}' (value '{val_to_set}' applied to {count_affected} records)", user=user)
    return {"column": col_name, "value": val_to_set, "records_affected": count_affected}


@router.post("/columns/delete", dependencies=[Depends(require_admin), Depends(require_permission("delete"))])
def delete_column(data: schemas.DeleteColumnIn, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    col_name = data.column_name.strip()
    norm = col_name.lower().replace(' ', '_')
    if norm in BASE_COLUMNS:
        raise HTTPException(400, f"Cannot delete '{col_name}' because it is a core system column.")

    entry = db.query(models.ColumnRegistry).filter(models.ColumnRegistry.name == col_name).first()
    if entry:
        db.delete(entry)

    json_path = f"$.\"{col_name}\""
    sql = "UPDATE sim_devices SET extra = JSON_REMOVE(extra, :path) WHERE extra IS NOT NULL AND JSON_CONTAINS_PATH(extra, 'one', :path)"
    res = db.execute(text(sql), {"path": json_path})
    count_cleaned = res.rowcount

    log_activity(db, "column_delete", f"Deleted column '{col_name}' (cleared from {count_cleaned} records)", user=admin)
    db.commit()
    return {"deleted": col_name, "records_affected": count_cleaned}


@router.get("/devices/lookup", dependencies=[Depends(require_permission("view"))])
def lookup(value: str, db: Session = Depends(get_db)):
    v = value.strip()
    items = (db.query(Device).options(joinedload(Device.customer))
             .filter(ACTIVE, or_(Device.imei == v, Device.iccid == v, Device.msisdn1 == v,
                                 Device.msisdn2 == v, Device.device_sr_no == v)).limit(50).all())
    return [out(d) for d in items]


@router.get("/devices/{device_id}", dependencies=[Depends(require_permission("view"))])
def get_device_by_id(device_id: int, db: Session = Depends(get_db)):
    d = db.query(Device).options(joinedload(Device.customer)).filter(Device.id == device_id, ACTIVE).first()
    if not d:
        raise HTTPException(404, "Device not found.")
    if d.iccid:
        try:
            sync_devices_with_sensorise(db, [d])
        except Exception as _sync_err:
            pass
    return out(d)


@router.put("/devices/{device_id}", dependencies=[Depends(require_permission("edit"))])
def update_device_by_id(device_id: int, data: schemas.DeviceUpdate, db: Session = Depends(get_db),
                        user: models.User = Depends(get_current_user)):
    d = db.query(Device).options(joinedload(Device.customer)).filter(Device.id == device_id, ACTIVE).first()
    if not d:
        raise HTTPException(404, "Device not found.")
    changes = data.model_dump(exclude_unset=True)
    fields = sorted(changes)
    if "extra" in changes:
        merged = merge_extra(d.extra, changes.pop("extra"))
        d.extra = merged or None
        register_columns(db, merged)
    if "customer_name" in changes:
        cn = (changes.pop("customer_name") or "").strip()
        if cn:
            d.customer_id = customer_by_name(db, cn).id
    for k, v in changes.items():
        setattr(d, k, v)
    log_activity(db, "device_edit", f"Device #{d.id} (IMEI {d.imei}): {', '.join(fields) or 'no changes'}", user=user)
    db.commit()
    db.refresh(d)
    try:
        cname = d.customer.name if d.customer else "customer"
        row = {"imei": d.imei, "extra": d.extra or {}}
        row.update({f: (cname if f == "customer_name" else getattr(d, f, None)) for f in customer_tables.BASE_NAMES})
        customer_tables.mirror_single_device(d.customer_id, cname, row)
    except Exception as e:
        print(f"Customer table mirror failed: {e}")
    return out(d)


class ExpiryDateIn(BaseModel):
    expiry_date: Optional[date] = None

    @field_validator("expiry_date", mode="before")
    @classmethod
    def _parse_exp(cls, v):
        return schemas._to_date(v)


@router.put("/devices/{device_id}/expiry-date", dependencies=[Depends(require_permission("edit"))])
@router.post("/devices/{device_id}/expiry-date", dependencies=[Depends(require_permission("edit"))])
def update_device_expiry_date(device_id: int, data: ExpiryDateIn, db: Session = Depends(get_db),
                              user: models.User = Depends(get_current_user)):
    """Dedicated endpoint to update SIM expiry date permanently with strict validation."""
    d = db.query(Device).options(joinedload(Device.customer)).filter(Device.id == device_id, ACTIVE).first()
    if not d:
        raise HTTPException(404, "Device not found.")
    old_date = str(d.expiry_date or "None")
    d.expiry_date = data.expiry_date
    log_activity(db, "device_edit", f"Updated expiry date for Device #{d.id} (IMEI {d.imei}) from '{old_date}' to '{d.expiry_date}'", user=user)
    db.commit()
    db.refresh(d)
    try:
        cname = d.customer.name if d.customer else "customer"
        row = {"imei": d.imei, "extra": d.extra or {}}
        row.update({f: (cname if f == "customer_name" else getattr(d, f, None)) for f in customer_tables.BASE_NAMES})
        customer_tables.mirror_single_device(d.customer_id, cname, row)
    except Exception as e:
        print(f"Customer table mirror failed: {e}")
    return out(d)


@router.get("/devices/by-imei/{imei}", dependencies=[Depends(require_permission("view"))])
def get_by_imei(imei: str, db: Session = Depends(get_db)):
    return out(active_by_imei(db, imei))


@router.put("/devices/by-imei/{imei}", dependencies=[Depends(require_permission("edit"))])
def update_by_imei(imei: str, data: schemas.DeviceUpdate, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    d = active_by_imei(db, imei)
    changes = data.model_dump(exclude_unset=True)
    fields = sorted(changes)
    if "extra" in changes:
        merged = merge_extra(d.extra, changes.pop("extra"))
        d.extra = merged or None
        register_columns(db, merged)
    if "customer_name" in changes:
        cn = (changes.pop("customer_name") or "").strip()
        if cn:
            d.customer_id = customer_by_name(db, cn).id
    for k, v in changes.items():
        setattr(d, k, v)
    log_activity(db, "device_edit", f"IMEI {d.imei}: {', '.join(fields) or 'no changes'}", user=user)
    db.commit()
    db.refresh(d)
    try:
        cname = d.customer.name if d.customer else "customer"
        row = {"imei": d.imei, "extra": d.extra or {}}
        row.update({f: (cname if f == "customer_name" else getattr(d, f, None)) for f in customer_tables.BASE_NAMES})
        customer_tables.mirror_single_device(d.customer_id, cname, row)
    except Exception as e:
        print(f"Customer table mirror failed: {e}")
    return out(d)


@router.delete("/devices/by-imei/{imei}", dependencies=[Depends(require_staff), Depends(require_permission("delete"))])
def delete_by_imei(imei: str, data: Optional[schemas.ReasonIn] = None, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    d = active_by_imei(db, imei)
    cid = d.customer_id
    trash(d, user, (data.reason if data else None) or "Deleted by IMEI")
    log_activity(db, "device_delete", f"IMEI {d.imei} moved to bin", user=user)
    db.commit()
    try:
        customer_tables.delete_device_from_table(cid, d.imei)
    except Exception as e:
        print(f"Customer table delete device failed: {e}")
    return {"moved_to_bin": d.imei}


@router.delete("/devices/{device_id}", dependencies=[Depends(require_staff), Depends(require_permission("delete"))])
def delete_device(device_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    d = db.query(Device).filter(Device.id == device_id, ACTIVE).first()
    if not d:
        raise HTTPException(404, "Record not found.")
    cid = d.customer_id
    imei = d.imei
    trash(d, user, "Deleted from list")
    log_activity(db, "device_delete", f"IMEI {d.imei} moved to bin", user=user)
    db.commit()
    try:
        customer_tables.delete_device_from_table(cid, imei)
    except Exception as e:
        print(f"Customer table delete device failed: {e}")
    return {"moved_to_bin": d.id}


# ---------- expiry alerts ----------
@router.get("/alerts/expiry", dependencies=[Depends(require_permission("view"))])
def expiry_alerts(days: int = Query(30, ge=0, le=365), customer_id: Optional[int] = None,
                  limit: int = Query(5000, ge=1, le=20000),
                  status: str = Query("all", description="all | expired | expiring"),
                  db: Session = Depends(get_db)):
    """status=expired -> already expired; status=expiring -> expires today .. today+days; all -> both (old behaviour).
    Filtering on the server matters: with tens of thousands of expired SIMs the 5,000-row cap would otherwise hide
    every \"expiring soon\" SIM."""
    today = date.today()
    q = db.query(Device).options(joinedload(Device.customer)).filter(ACTIVE, Device.expiry_date.isnot(None))
    s = (status or "all").strip().lower()
    if s == "expired":
        q = q.filter(Device.expiry_date < today)
    elif s in ("expiring", "expiring_soon"):
        q = q.filter(Device.expiry_date >= today, Device.expiry_date <= today + timedelta(days=days))
    else:
        q = q.filter(Device.expiry_date <= today + timedelta(days=days))
    if customer_id:
        q = q.filter(Device.customer_id == customer_id)
    items = q.order_by(Device.expiry_date).limit(limit).all()
    return [out(d) for d in items]


# ---------- deleted customers (recycle bin) ----------
# ==============================================================================
# WHAT IS HAPPENING BELOW:
# Cart / Recycle Bin Endpoints:
# - GET /api/bin: Lists all soft-deleted devices with deletion timestamps and reasons.
# - POST /api/bin/{id}/restore: Restores a device back to active inventory.
# - POST /api/bin/restore-all: Restores all deleted devices in bulk.
# - DELETE /api/bin/{id}: Permanently purges a record from the database.
# ==============================================================================
@router.get("/bin", dependencies=[Depends(require_staff), Depends(require_permission("view"))])
def bin_list(db: Session = Depends(get_db)):
    items = (db.query(Device).options(joinedload(Device.customer))
             .filter(Device.deleted_at.isnot(None)).order_by(Device.deleted_at.desc()).all())
    return [out(d) for d in items]


@router.post("/bin/{device_id}/restore", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def bin_restore(device_id: int, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    d = db.query(Device).filter(Device.id == device_id, Device.deleted_at.isnot(None)).first()
    if not d:
        raise HTTPException(404, "Not in the bin.")
    d.deleted_at = d.deleted_by = d.delete_reason = None
    if d.customer and d.customer.deleted_at:
        d.customer.deleted_at = d.customer.deleted_by = None
    log_activity(db, "device_restore", f"IMEI {d.imei} restored", user=user)
    db.commit()
    try:
        cname = d.customer.name if d.customer else ""
        customer_tables.mirror_single_device(d.customer_id, cname, out(d))
    except Exception as e:
        print(f"Customer table mirror single device on restore failed: {e}")
    return {"restored": d.id}


@router.post("/bin/restore-all", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
@router.post("/devices/restore-all", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def restore_all_deleted_devices(customer_id: Optional[int] = None, db: Session = Depends(get_db),
                                user: models.User = Depends(get_current_user)):
    # Restore any soft-deleted customers if restoring all
    restored_custs = 0
    if not customer_id:
        del_custs = db.query(Customer).filter(Customer.deleted_at.isnot(None)).all()
        for c in del_custs:
            c.deleted_at = None
            c.deleted_by = None
            restored_custs += 1

    q = db.query(Device).filter(Device.deleted_at.isnot(None))
    if customer_id:
        q = q.filter(Device.customer_id == customer_id)
    items = q.all()
    if not items and restored_custs == 0:
        return {
            "restored": 0, "skipped": 0, "failed": 0, "total": 0,
            "message": "No deleted or archived records found to restore."
        }

    # Fetch active IMEIs to prevent conflicts
    active_imeis = {imei for (imei,) in db.query(Device.imei).filter(Device.deleted_at.is_(None)).all()}

    restored = 0
    skipped = 0
    failed = 0

    for d in items:
        try:
            if d.imei in active_imeis:
                # Active record already exists with this IMEI: skip to prevent duplicate collision
                skipped += 1
                continue
            d.deleted_at = None
            d.deleted_by = None
            d.delete_reason = None
            if d.customer and d.customer.deleted_at:
                d.customer.deleted_at = None
                d.customer.deleted_by = None
            active_imeis.add(d.imei)
            restored += 1
        except Exception:
            failed += 1

    db.commit()
    log_activity(db, "device_restore", f"Restore All executed: {restored} restored, {skipped} skipped, {failed} failed", user=user)

    for d in items:
        if d.deleted_at is None:
            try:
                cname = d.customer.name if d.customer else ""
                customer_tables.mirror_single_device(d.customer_id, cname, out(d))
            except Exception:
                pass

    return {
        "restored": restored,
        "skipped": skipped,
        "failed": failed,
        "total": len(items),
        "message": f"Successfully restored {restored} record(s). {skipped} skipped to avoid duplicates."
    }


@router.get("/customers/{customer_id}/export", dependencies=[Depends(require_permission("download"))])
def export_customer_devices(customer_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    cust_name = cust.name if cust else f"Customer_{customer_id}"
    return export_devices(customer_id=customer_id, title=f"Customer_{cust_name}_Inventory", db=db, user=user)


@router.get("/customers/{customer_id}/files", dependencies=[Depends(require_permission("view"))])
def list_customer_files(customer_id: int, db: Session = Depends(get_db)):
    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    if not cust:
        raise HTTPException(404, "Customer not found")
    count = db.query(func.count(Device.id)).filter(ACTIVE, Device.customer_id == customer_id).scalar() or 0
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", cust.name)
    files = []
    if count > 0:
        files.append({
            "name": f"{safe_name}_Complete_Inventory_{date.today().isoformat()}.xlsx",
            "type": "Excel Workbook",
            "records": count,
            "url": f"/api/devices/export?customer_id={customer_id}",
            "created_at": date.today().isoformat(),
            "description": f"Complete device records for {cust.name} ({count} active entries)"
        })
    return {"customer_id": customer_id, "customer_name": cust.name, "records": count, "files": files}


@router.delete("/bin/{device_id}", dependencies=[Depends(require_admin), Depends(require_permission("delete"))])
def bin_purge(device_id: int, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    d = db.query(Device).filter(Device.id == device_id, Device.deleted_at.isnot(None)).first()
    if not d:
        raise HTTPException(404, "Not in the bin.")
    cid, imei = d.customer_id, d.imei
    cname = d.customer.name if d.customer else ""
    log_activity(db, "device_purge", f"IMEI {d.imei} deleted forever", user=admin)
    db.delete(d)
    db.commit()
    try:
        customer_tables.delete_device_from_table(cid, imei, cname)
    except Exception as e:
        print(f"Customer table delete device failed: {e}")
    return {"deleted_forever": device_id}


@router.delete("/bin", dependencies=[Depends(require_staff), Depends(require_permission("delete"))])
def bin_empty(limit: int = 0, db: Session = Depends(get_db), admin: models.User = Depends(get_current_user)):
    total_remaining_devices = db.query(Device).filter(Device.deleted_at.isnot(None)).count()
    deleted_custs = db.query(Customer).filter(Customer.deleted_at.isnot(None)).all()

    if limit > 0:
        dev_objs = db.query(Device).options(joinedload(Device.customer)).filter(Device.deleted_at.isnot(None)).limit(limit).all()
        dev_ids = [d.id for d in dev_objs]
        for d in dev_objs:
            try:
                cname = d.customer.name if d.customer else ""
                customer_tables.delete_device_from_table(d.customer_id, d.imei, cname)
            except Exception:
                pass
        if dev_ids:
            n = db.query(Device).filter(Device.id.in_(dev_ids)).delete(synchronize_session=False)
        else:
            n = 0
        db.commit()
        remaining = max(0, total_remaining_devices - n)
        cust_purged = 0
        if remaining == 0 and deleted_custs:
            for c in deleted_custs:
                try:
                    customer_tables.drop_table(c.id, c.name)
                except Exception as e:
                    print(f"Drop table on empty cart failed: {e}")
                db.delete(c)
            cust_purged = len(deleted_custs)
            db.commit()
        log_activity(db, "bin_empty_chunk", f"Permanently deleted {n} records from bin ({remaining} remaining)", user=admin)
        return {"deleted_forever": n, "remaining_count": remaining, "customers_purged": cust_purged}
    else:
        # Drop tables for deleted customers permanently
        for c in deleted_custs:
            try:
                customer_tables.drop_table(c.id, c.name)
            except Exception as e:
                print(f"Drop table on empty cart failed: {e}")
            db.delete(c)
        dev_objs = db.query(Device).options(joinedload(Device.customer)).filter(Device.deleted_at.isnot(None)).all()
        for d in dev_objs:
            try:
                cname = d.customer.name if d.customer else ""
                customer_tables.delete_device_from_table(d.customer_id, d.imei, cname)
            except Exception:
                pass
        n = db.query(Device).filter(Device.deleted_at.isnot(None)).delete(synchronize_session=False)
        log_activity(db, "bin_empty", f"Emptied the bin ({n} records and {len(deleted_custs)} customers deleted forever)", user=admin)
        db.commit()
        return {"deleted_forever": n, "remaining_count": 0, "customers_purged": len(deleted_custs)}


# ---------- errored / invalid records staging ----------
def errored_out(r: models.ErroredRecord):
    return {
        "id": r.id,
        "customer_name": r.customer_name or "",
        "imei": r.imei or "",
        "device_sr_no": r.device_sr_no or "",
        "iccid": r.iccid or "",
        "msisdn1": r.msisdn1 or "",
        "msisdn2": r.msisdn2 or "",
        "act_date": r.act_date.isoformat() if r.act_date else None,
        "expiry_date": r.expiry_date.isoformat() if r.expiry_date else None,
        "dispatched_date": r.dispatched_date.isoformat() if r.dispatched_date else None,
        "model": r.model or "",
        "sim_provider": r.sim_provider or "",
        "activation_plan": r.activation_plan or "",
        "firmware": r.firmware or "",
        "flash": r.flash or "",
        "sim_type": r.sim_type or "",
        "extra": r.extra or {},
        "error_reason": r.error_reason or "Invalid data",
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/errors", dependencies=[Depends(require_permission("view"))])
def list_errors(reason: Optional[str] = None, q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.ErroredRecord)
    if reason and reason.strip():
        query = query.filter(models.ErroredRecord.error_reason.ilike(f"%{reason.strip()}%"))
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                models.ErroredRecord.imei.ilike(term),
                models.ErroredRecord.customer_name.ilike(term),
                models.ErroredRecord.iccid.ilike(term),
                models.ErroredRecord.device_sr_no.ilike(term),
                models.ErroredRecord.msisdn1.ilike(term),
                models.ErroredRecord.error_reason.ilike(term)
            )
        )
    rows = query.order_by(models.ErroredRecord.created_at.desc(), models.ErroredRecord.id.desc()).all()
    return [errored_out(r) for r in rows]


@router.get("/errors/summary", dependencies=[Depends(require_permission("view"))])
def errors_summary(db: Session = Depends(get_db)):
    rows = db.query(models.ErroredRecord.error_reason, func.count(models.ErroredRecord.id)).group_by(models.ErroredRecord.error_reason).all()
    total = sum(c for _, c in rows)
    reasons = [{"reason": r or "Unknown Error", "count": c} for r, c in rows]
    reasons.sort(key=lambda x: x["count"], reverse=True)
    return {"total": total, "reasons": reasons}


@router.post("/errors", dependencies=[Depends(require_permission("view"))])
def save_errors(data: schemas.BulkErrorsIn, db: Session = Depends(get_db)):
    def cut(v, n):
        return None if v is None else str(v)[:n]
    rows = [dict(customer_name=cut(i.customer_name, 150), imei=cut(i.imei, 100), device_sr_no=cut(i.device_sr_no, 100),
                 iccid=cut(i.iccid, 100), msisdn1=cut(i.msisdn1, 100), msisdn2=cut(i.msisdn2, 100),
                 act_date=i.act_date, expiry_date=i.expiry_date, dispatched_date=i.dispatched_date,
                 model=cut(i.model, 150), sim_provider=cut(i.sim_provider, 150), activation_plan=cut(i.activation_plan, 150),
                 firmware=cut(i.firmware, 150), flash=cut(i.flash, 150), sim_type=cut(i.sim_type, 100),
                 extra=i.extra, error_reason=cut(i.error_reason or "Invalid entry", 500)) for i in data.records]
    for k in range(0, len(rows), 1000):
        db.execute(insert(models.ErroredRecord), rows[k:k + 1000])
    db.commit()
    return {"saved_errors": len(rows)}


@router.put("/errors/{error_id}/upload", dependencies=[Depends(require_permission("upload"))])
def upload_corrected_error(error_id: int, data: schemas.DeviceIn, db: Session = Depends(get_db),
                           user: models.User = Depends(get_current_user)):
    err = db.query(models.ErroredRecord).filter(models.ErroredRecord.id == error_id).first()
    if not err:
        raise HTTPException(404, "Errored record not found.")

    cname = (data.customer_name or err.customer_name or "").strip() or "General_Customer"
    imei_val = (data.imei or "").strip()
    if not imei_val or len(imei_val) < 5:
        alt = clean_imei(data.device_sr_no or data.iccid or err.device_sr_no or err.iccid or "")
        if alt and len(alt) >= 5:
            imei_val = alt[:20]
        else:
            imei_val = f"INV_{uuid.uuid4().hex[:10].upper()}"
    data.imei = imei_val
    data.customer_name = cname

    # Ingest using bulk_add logic so customer and TiDB Cloud table are synchronized
    res = bulk_add(schemas.BulkIn(rows=[data], mode="replace"), db=db, user=user)

    # Remove from errored records table
    db.delete(err)
    db.commit()

    log_activity(db, "error_resolved", f"Corrected and uploaded record IMEI {data.imei} to customer {data.customer_name}", user=user)
    return {"success": True, "result": res}


@router.post("/errors/{error_id}/push", dependencies=[Depends(require_permission("upload"))])
def push_error_to_customer(error_id: int, data: Optional[schemas.PushErrorIn] = None,
                           db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Pushes an errored entry directly into the specified customer even if it contains errors or duplicate attributes."""
    err = db.query(models.ErroredRecord).filter(models.ErroredRecord.id == error_id).first()
    if not err:
        raise HTTPException(404, "Errored record not found.")

    target_cname = ""
    if data and data.customer_name:
        target_cname = data.customer_name.strip()
    if not target_cname:
        target_cname = (err.customer_name or "").strip()
    if not target_cname:
        target_cname = "General_Customer"

    cust = customer_by_name(db, target_cname)

    raw_imei = clean_imei(err.imei) if err.imei else ""
    extra = dict(err.extra or {})
    extra["pushed_with_error"] = True
    if err.error_reason:
        extra["original_error"] = err.error_reason

    if not raw_imei or len(raw_imei) < 5:
        alt = clean_imei(err.device_sr_no or err.iccid or "")
        if alt and len(alt) >= 5:
            raw_imei = alt[:20]
        else:
            raw_imei = f"INV_{uuid.uuid4().hex[:10].upper()}"

    final_imei = raw_imei[:20]
    stype = err.sim_type or ("E-SIM" if err.iccid else "Plastic SIM")
    existing_dev = db.query(Device).filter(Device.imei == final_imei).first()
    if existing_dev:
        dev = existing_dev
        dev.customer_id = cust.id
        if err.device_sr_no:
            dev.device_sr_no = err.device_sr_no
        if err.iccid:
            dev.iccid = err.iccid
        if err.msisdn1:
            dev.msisdn1 = err.msisdn1
        if err.msisdn2:
            dev.msisdn2 = err.msisdn2
        if err.act_date:
            dev.act_date = err.act_date
        if err.expiry_date:
            dev.expiry_date = err.expiry_date
        if err.dispatched_date:
            dev.dispatched_date = err.dispatched_date
        if err.model:
            dev.model = err.model
        if err.sim_provider:
            dev.sim_provider = err.sim_provider
        if err.activation_plan:
            dev.activation_plan = err.activation_plan
        if err.firmware:
            dev.firmware = err.firmware
        if err.flash:
            dev.flash = err.flash
        if stype:
            dev.sim_type = stype
        merged_extra = {**(dev.extra or {}), **extra}
        dev.extra = merged_extra or None
        if dev.deleted_at:
            dev.deleted_at = dev.deleted_by = dev.delete_reason = None
    else:
        dev = Device(
            customer_id=cust.id,
            imei=final_imei,
            device_sr_no=err.device_sr_no,
            iccid=err.iccid,
            msisdn1=err.msisdn1,
            msisdn2=err.msisdn2,
            act_date=err.act_date,
            expiry_date=err.expiry_date,
            dispatched_date=err.dispatched_date,
            model=err.model,
            sim_provider=err.sim_provider,
            activation_plan=err.activation_plan,
            firmware=err.firmware,
            flash=err.flash,
            sim_type=stype,
            extra=extra or None,
            added_by=user.id if user else None
        )
        db.add(dev)
    db.delete(err)
    db.commit()
    db.refresh(dev)

    row_mirror = {
        "imei": dev.imei,
        "customer_name": cust.name,
        "device_sr_no": dev.device_sr_no,
        "iccid": dev.iccid,
        "msisdn1": dev.msisdn1,
        "msisdn2": dev.msisdn2,
        "act_date": dev.act_date,
        "expiry_date": dev.expiry_date,
        "dispatched_date": dev.dispatched_date,
        "model": dev.model,
        "sim_provider": dev.sim_provider,
        "activation_plan": dev.activation_plan,
        "firmware": dev.firmware,
        "flash": dev.flash,
        "sim_type": dev.sim_type,
        "extra": dev.extra or {}
    }
    try:
        if getattr(getattr(db, "bind", None), "dialect", None) and getattr(db.bind.dialect, "name", "") == "sqlite":
            customer_tables.mirror_rows([(cust.id, cust.name, row_mirror)], conn=db.connection())
            db.commit()
        else:
            customer_tables.mirror_rows([(cust.id, cust.name, row_mirror)])
    except Exception as me:
        print(f"Customer table mirror notice: {me}")

    log_activity(db, "error_force_pushed", f"Pushed errored entry #{error_id} (IMEI {final_imei}) to customer '{cust.name}'", user=user)
    db.commit()

    return {"success": True, "device_id": dev.id, "imei": final_imei, "customer_name": cust.name}


@router.post("/errors/bulk-push", dependencies=[Depends(require_permission("upload"))])
def bulk_push_errors_to_customer(data: schemas.BulkPushErrorsIn, db: Session = Depends(get_db),
                                 user: models.User = Depends(get_current_user)):
    """Bulk pushes errored entries directly into a specified customer."""
    query = db.query(models.ErroredRecord)
    if data.error_ids:
        query = query.filter(models.ErroredRecord.id.in_(data.error_ids))
    records = query.all()
    if not records:
        return {"pushed_count": 0, "customer_name": data.customer_name or "General_Customer"}

    target_cname = (data.customer_name or "").strip() or "General_Customer"
    cust = customer_by_name(db, target_cname)

    mirror_items = []
    pushed = 0
    for err in records:
        raw_imei = clean_imei(err.imei) if err.imei else ""
        extra = dict(err.extra or {})
        extra["pushed_with_error"] = True
        if err.error_reason:
            extra["original_error"] = err.error_reason

        if not raw_imei or len(raw_imei) < 5:
            alt = clean_imei(err.device_sr_no or err.iccid or "")
            if alt and len(alt) >= 5:
                raw_imei = alt[:20]
            else:
                raw_imei = f"INV_{uuid.uuid4().hex[:10].upper()}"

        final_imei = raw_imei[:20]
        stype = err.sim_type or ("E-SIM" if err.iccid else "Plastic SIM")
        existing_dev = db.query(Device).filter(Device.imei == final_imei).first()
        if existing_dev:
            dev = existing_dev
            dev.customer_id = cust.id
            if err.device_sr_no:
                dev.device_sr_no = err.device_sr_no
            if err.iccid:
                dev.iccid = err.iccid
            if err.msisdn1:
                dev.msisdn1 = err.msisdn1
            if err.msisdn2:
                dev.msisdn2 = err.msisdn2
            if err.act_date:
                dev.act_date = err.act_date
            if err.expiry_date:
                dev.expiry_date = err.expiry_date
            if err.dispatched_date:
                dev.dispatched_date = err.dispatched_date
            if err.model:
                dev.model = err.model
            if err.sim_provider:
                dev.sim_provider = err.sim_provider
            if err.activation_plan:
                dev.activation_plan = err.activation_plan
            if err.firmware:
                dev.firmware = err.firmware
            if err.flash:
                dev.flash = err.flash
            if stype:
                dev.sim_type = stype
            merged_extra = {**(dev.extra or {}), **extra}
            dev.extra = merged_extra or None
            if dev.deleted_at:
                dev.deleted_at = dev.deleted_by = dev.delete_reason = None
        else:
            dev = Device(
                customer_id=cust.id,
                imei=final_imei,
                device_sr_no=err.device_sr_no,
                iccid=err.iccid,
                msisdn1=err.msisdn1,
                msisdn2=err.msisdn2,
                act_date=err.act_date,
                expiry_date=err.expiry_date,
                dispatched_date=err.dispatched_date,
                model=err.model,
                sim_provider=err.sim_provider,
                activation_plan=err.activation_plan,
                firmware=err.firmware,
                flash=err.flash,
                sim_type=stype,
                extra=extra or None,
                added_by=user.id if user else None
            )
            db.add(dev)
        db.delete(err)
        pushed += 1
        mirror_items.append((cust.id, cust.name, {
            "imei": final_imei, "customer_name": cust.name, "device_sr_no": dev.device_sr_no,
            "iccid": dev.iccid, "msisdn1": dev.msisdn1, "msisdn2": dev.msisdn2,
            "act_date": dev.act_date, "expiry_date": dev.expiry_date, "dispatched_date": dev.dispatched_date,
            "model": dev.model, "sim_provider": dev.sim_provider, "activation_plan": dev.activation_plan,
            "firmware": dev.firmware, "flash": dev.flash, "sim_type": dev.sim_type, "extra": extra
        }))

    db.commit()
    if mirror_items:
        try:
            if getattr(getattr(db, "bind", None), "dialect", None) and getattr(db.bind.dialect, "name", "") == "sqlite":
                customer_tables.mirror_rows(mirror_items, conn=db.connection())
                db.commit()
            else:
                customer_tables.mirror_rows(mirror_items)
        except Exception as me:
            print(f"Customer table mirror notice: {me}")

    log_activity(db, "error_bulk_force_pushed", f"Bulk pushed {pushed} errored entries to customer '{cust.name}'", user=user)
    db.commit()

    return {"pushed_count": pushed, "customer_name": cust.name}


@router.delete("/errors/{error_id:int}", dependencies=[Depends(require_staff), Depends(require_permission("delete_invalid"))])
def move_error_to_cart(error_id: int, permanent: bool = False, db: Session = Depends(get_db),
                       user: models.User = Depends(get_current_user)):
    err = db.query(models.ErroredRecord).filter(models.ErroredRecord.id == error_id).first()
    if not err:
        raise HTTPException(404, "Errored record not found.")

    if permanent:
        db.delete(err)
        db.commit()
        log_activity(db, "error_permanent_delete", f"Permanently deleted errored entry #{error_id} from database", user=user)
        return {"deleted_forever": error_id, "permanent": True}

    # Find or create customer for this record so it can be held in Cart
    cname = (err.customer_name or "").strip() or "Unassigned Errors"
    cust = customer_by_name(db, cname)

    imei_val = (err.imei or "").strip()
    if not imei_val or len(imei_val) < 5 or db.query(Device).filter(Device.imei == imei_val).first():
        imei_val = f"ERR-{err.id}-{int(time.time())}"

    # Move to Cart (deleted_at set)
    dev = Device(
        customer_id=cust.id,
        imei=imei_val,
        device_sr_no=err.device_sr_no,
        iccid=err.iccid,
        msisdn1=err.msisdn1,
        msisdn2=err.msisdn2,
        act_date=err.act_date,
        expiry_date=err.expiry_date,
        dispatched_date=err.dispatched_date,
        model=err.model,
        sim_provider=err.sim_provider,
        activation_plan=err.activation_plan,
        firmware=err.firmware,
        flash=err.flash,
        sim_type=err.sim_type,
        extra=err.extra,
        added_by=user.id,
        deleted_at=datetime.utcnow(),
        deleted_by=user.user_id,
        delete_reason=f"Moved from Errored Entries: {err.error_reason[:150]}"
    )
    db.add(dev)
    db.delete(err)
    db.commit()

    log_activity(db, "error_trash", f"Errored entry #{error_id} moved to Cart", user=user)
    return {"moved_to_cart": error_id}


@router.post("/errors/empty", dependencies=[Depends(require_staff), Depends(require_permission("delete_invalid"))])
def move_all_errors_to_cart(limit: int = 0, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    total_remaining = db.query(models.ErroredRecord).count()
    query = db.query(models.ErroredRecord)
    if limit > 0:
        errors = query.limit(limit).all()
    else:
        errors = query.all()
    count = 0
    cust = customer_by_name(db, "Unassigned Errors")
    for err in errors:
        cname = (err.customer_name or "").strip()
        c = customer_by_name(db, cname) if cname else cust
        imei_val = (err.imei or "").strip()
        if not imei_val or len(imei_val) < 5 or db.query(Device).filter(Device.imei == imei_val).first():
            imei_val = f"ERR-{err.id}-{int(time.time())}"
        dev = Device(
            customer_id=c.id,
            imei=imei_val[:20],
            device_sr_no=str(err.device_sr_no or "")[:50] if err.device_sr_no else None,
            iccid=str(err.iccid or "")[:30] if err.iccid else None,
            msisdn1=str(err.msisdn1 or "")[:20] if err.msisdn1 else None,
            msisdn2=str(err.msisdn2 or "")[:20] if err.msisdn2 else None,
            act_date=err.act_date,
            expiry_date=err.expiry_date,
            dispatched_date=err.dispatched_date,
            model=str(err.model or "")[:100] if err.model else None,
            sim_provider=str(err.sim_provider or "")[:100] if err.sim_provider else None,
            activation_plan=str(err.activation_plan or "")[:100] if err.activation_plan else None,
            firmware=str(err.firmware or "")[:100] if err.firmware else None,
            flash=str(err.flash or "")[:100] if err.flash else None,
            sim_type=str(err.sim_type or "")[:20] if err.sim_type else None,
            extra=err.extra,
            added_by=user.id,
            deleted_at=datetime.utcnow(),
            deleted_by=user.user_id,
            delete_reason=f"Moved from Errored Entries: {err.error_reason[:150]}"
        )
        db.add(dev)
        db.delete(err)
        count += 1
    db.commit()
    remaining = max(0, total_remaining - count)
    log_activity(db, "errors_trash_all", f"Moved {count} errored entries to Cart", user=user)
    return {"moved_count": count, "remaining_count": remaining, "moved_all_to_cart": count}


@router.delete("/errors/permanent", dependencies=[Depends(require_staff), Depends(require_permission("delete_invalid"))])
def direct_delete_all_errors_permanent(limit: int = 0, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Directly and permanently deletes errored entries from the database forever."""
    total_remaining = db.query(models.ErroredRecord).count()
    if limit > 0:
        err_ids = [r.id for r in db.query(models.ErroredRecord.id).order_by(models.ErroredRecord.id.asc()).limit(limit).all()]
        if err_ids:
            count = db.query(models.ErroredRecord).filter(models.ErroredRecord.id.in_(err_ids)).delete(synchronize_session=False)
        else:
            count = 0
        db.commit()
        remaining = max(0, total_remaining - count)
        log_activity(db, "errors_permanent_purge", f"Permanently deleted {count} errored entries from database", user=user)
        return {"deleted_count": count, "remaining_count": remaining, "deleted_forever": count}
    else:
        count = db.query(models.ErroredRecord).delete(synchronize_session=False)
        db.commit()
        log_activity(db, "errors_permanent_purge", f"Permanently deleted all {count} errored entries from database", user=user)
        return {"deleted_count": count, "remaining_count": 0, "deleted_forever": count}


@router.delete("/errors/{error_id}/permanent", dependencies=[Depends(require_staff), Depends(require_permission("delete_invalid"))])
def direct_delete_single_error_permanent(error_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Directly and permanently deletes a single errored entry from the database forever."""
    err = db.query(models.ErroredRecord).filter(models.ErroredRecord.id == error_id).first()
    if not err:
        raise HTTPException(404, "Errored record not found.")
    db.delete(err)
    db.commit()
    log_activity(db, "error_permanent_delete", f"Permanently deleted errored entry #{error_id} from database", user=user)
    return {"deleted_forever": error_id}


@router.post("/errors/batch-delete", dependencies=[Depends(require_staff), Depends(require_permission("delete_invalid"))])
def direct_delete_batch_errors(data: schemas.BatchDeleteErrorsIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Directly and permanently deletes specific errored records by ID from the database forever."""
    if not data.error_ids:
        return {"deleted_count": 0, "deleted_forever": 0}
    count = db.query(models.ErroredRecord).filter(models.ErroredRecord.id.in_(data.error_ids)).delete(synchronize_session=False)
    db.commit()
    log_activity(db, "errors_batch_delete", f"Permanently deleted {count} errored entries from database", user=user)
    return {"deleted_count": count, "deleted_forever": count}


# ---------- Bulk Deletion via Excel matching ----------
@router.post("/devices/bulk-delete/preview", dependencies=[Depends(require_staff), Depends(require_permission("delete"))])
def bulk_delete_preview(data: schemas.BulkDeletePreviewIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Analyzes an uploaded Excel list of identifiers and previews matches in valid inventory."""
    col_name = (data.column or "imei").strip().lower()
    raw_vals = [str(v).strip() for v in data.values if v is not None and str(v).strip()]
    total_vals = len(raw_vals)
    if not total_vals:
        return {
            "total_values": 0, "unique_values": 0, "duplicate_values": 0,
            "matching_records": 0, "unmatched_values": 0, "eligible_for_deletion": 0,
            "column": col_name, "sample_matches": []
        }

    unique_vals = list(dict.fromkeys(raw_vals))
    dup_count = total_vals - len(unique_vals)

    col_map = {
        "imei": Device.imei,
        "iccid": Device.iccid,
        "device_sr_no": Device.device_sr_no,
        "msisdn1": Device.msisdn1,
        "customer_name": None
    }
    target_col = col_map.get(col_name, Device.imei)

    matched_ids = []
    matched_sample = []
    matched_val_set = set()
    chunk_size = 500

    for i in range(0, len(unique_vals), chunk_size):
        chunk = unique_vals[i:i + chunk_size]
        if target_col is not None:
            rows = db.query(Device.id, target_col).filter(
                Device.deleted_at.is_(None),
                target_col.in_(chunk)
            ).all()
            for dev_id, val in rows:
                matched_ids.append(dev_id)
                if val:
                    matched_val_set.add(str(val).strip().lower())
                if len(matched_sample) < 10:
                    matched_sample.append({"id": dev_id, "matched_value": val})
        else:
            rows = db.query(Device.id, Customer.name).join(Customer, Customer.id == Device.customer_id).filter(
                Device.deleted_at.is_(None),
                Customer.name.in_(chunk)
            ).all()
            for dev_id, val in rows:
                matched_ids.append(dev_id)
                if val:
                    matched_val_set.add(str(val).strip().lower())
                if len(matched_sample) < 10:
                    matched_sample.append({"id": dev_id, "matched_value": val})

    unique_lower = {v.lower() for v in unique_vals}
    unmatched_count = len(unique_lower - matched_val_set)

    return {
        "total_values": total_vals,
        "unique_values": len(unique_vals),
        "duplicate_values": dup_count,
        "matching_records": len(matched_ids),
        "unmatched_values": max(0, unmatched_count),
        "eligible_for_deletion": len(matched_ids),
        "column": col_name,
        "sample_matches": matched_sample
    }


@router.post("/devices/bulk-delete/execute", dependencies=[Depends(require_staff), Depends(require_permission("delete"))])
def bulk_delete_execute(data: schemas.BulkDeleteExecuteIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Executes bulk deletion of inventory based on uploaded Excel column matching."""
    col_name = (data.column or "imei").strip().lower()
    raw_vals = [str(v).strip() for v in data.values if v is not None and str(v).strip()]
    if not raw_vals:
        return {"success": True, "deleted_count": 0, "skipped_count": 0, "unmatched_count": 0, "failures_count": 0, "permanent": data.permanent, "column": col_name}

    unique_vals = list(dict.fromkeys(raw_vals))

    col_map = {
        "imei": Device.imei,
        "iccid": Device.iccid,
        "device_sr_no": Device.device_sr_no,
        "msisdn1": Device.msisdn1,
        "customer_name": None
    }
    target_col = col_map.get(col_name, Device.imei)

    deleted_count = 0
    matched_val_set = set()
    chunk_size = 500

    for i in range(0, len(unique_vals), chunk_size):
        chunk = unique_vals[i:i + chunk_size]
        if target_col is not None:
            dev_objs = db.query(Device).options(joinedload(Device.customer)).filter(
                Device.deleted_at.is_(None),
                target_col.in_(chunk)
            ).all()
        else:
            dev_objs = db.query(Device).options(joinedload(Device.customer)).join(Customer, Customer.id == Device.customer_id).filter(
                Device.deleted_at.is_(None),
                Customer.name.in_(chunk)
            ).all()

        if not dev_objs:
            continue

        for d in dev_objs:
            val = getattr(d, col_name, None) if col_name != "customer_name" else (d.customer.name if d.customer else None)
            if val:
                matched_val_set.add(str(val).strip().lower())

            cid, imei = d.customer_id, d.imei
            cname = d.customer.name if d.customer else ""

            if data.permanent:
                try:
                    customer_tables.delete_device_from_table(cid, imei, cname)
                except Exception:
                    pass
                db.delete(d)
            else:
                trash(d, user, data.reason or f"Bulk deleted via Excel matching {col_name}")
                try:
                    customer_tables.delete_device_from_table(cid, imei, cname)
                except Exception:
                    pass

            deleted_count += 1

        db.commit()

    unique_lower = {v.lower() for v in unique_vals}
    unmatched_count = max(0, len(unique_lower - matched_val_set))

    action_tag = "device_bulk_permanent_delete" if data.permanent else "device_bulk_trash"
    log_activity(
        db,
        action_tag,
        f"Bulk deleted {deleted_count} records via Excel (Column: {col_name}, Permanent: {data.permanent})",
        user=user
    )

    return {
        "success": True,
        "deleted_count": deleted_count,
        "skipped_count": 0,
        "unmatched_count": unmatched_count,
        "failures_count": 0,
        "permanent": data.permanent,
        "column": col_name
    }


# ---------- Bulk Edit by IMEI ----------
@router.post("/devices/bulk-edit/preview", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def bulk_edit_preview(data: schemas.BulkEditPreviewIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Previews bulk editing of inventory records matched by IMEI."""
    input_rows = data.file_rows if data.file_rows is not None else (data.rows or [])
    total_rows = len(input_rows)
    imei_col_raw = (data.imei_col or data.imei_column or "imei").strip()
    mappings = data.field_mappings or {}

    if not total_rows:
        return {
            "total_rows": 0, "total_values": 0, "matching_imeis": 0, "matching_records": 0,
            "unmatched_imeis": 0, "unmatched_values": 0, "duplicates_in_file": 0, "duplicate_imeis": 0,
            "invalid_imeis": 0, "eligible_to_update": 0, "eligible_for_update": 0,
            "sample_changes": []
        }

    raw_imeis = []
    invalid_count = 0
    valid_row_map = {}
    seen_imeis = set()
    duplicate_count = 0

    for r in input_rows:
        # Extract row dictionary mapped to db fields
        if mappings:
            row_dict = {}
            for ex_col, db_fld in mappings.items():
                if ex_col in r:
                    row_dict[db_fld] = r[ex_col]
            raw_imei = str(r.get(imei_col_raw) or r.get("imei") or r.get(imei_col_raw.lower()) or "").strip()
        else:
            row_dict = dict(r)
            raw_imei = str(r.get(imei_col_raw) or r.get("imei") or r.get(imei_col_raw.lower()) or "").strip()

        if re.search(r"e\+", raw_imei, re.I):
            try:
                raw_imei = str(int(float(raw_imei)))
            except Exception:
                pass
        clean = re.sub(r"[^0-9A-Za-z_-]", "", raw_imei).strip()
        if not clean or len(clean) < 5:
            invalid_count += 1
            continue
        if clean in seen_imeis:
            duplicate_count += 1
        else:
            seen_imeis.add(clean)
            raw_imeis.append(clean)
            valid_row_map[clean] = row_dict

    matching_devices = {}
    chunk_size = 500
    for i in range(0, len(raw_imeis), chunk_size):
        chunk = raw_imeis[i:i + chunk_size]
        devs = db.query(Device).options(joinedload(Device.customer)).filter(
            Device.deleted_at.is_(None),
            Device.imei.in_(chunk)
        ).all()
        for d in devs:
            matching_devices[d.imei] = d

    matching_count = len(matching_devices)
    unmatched_count = max(0, len(raw_imeis) - matching_count)
    eligible_count = matching_count

    sample_changes_grouped = []
    sample_changes_flat = []
    for imei, d in list(matching_devices.items())[:25]:
        new_row = valid_row_map.get(imei, {})
        changes = {}
        for fld in ["model", "sim_provider", "activation_plan", "firmware", "flash", "sim_type", "device_sr_no", "iccid", "msisdn1", "msisdn2"]:
            new_val = new_row.get(fld)
            if new_val is not None and str(new_val).strip() != "":
                old_val = getattr(d, fld, None)
                if str(new_val).strip() != str(old_val or "").strip():
                    changes[fld] = {"old": str(old_val or ""), "new": str(new_val).strip()}

        for fld in ["act_date", "expiry_date", "dispatched_date"]:
            new_val = new_row.get(fld)
            if new_val is not None and str(new_val).strip() != "":
                old_val = getattr(d, fld, None)
                parsed_val = normalize_date_input(str(new_val).strip())
                if parsed_val and str(old_val or "") != str(parsed_val):
                    changes[fld] = {"old": str(old_val or ""), "new": str(parsed_val)}

        new_cust = new_row.get("customer_name")
        if new_cust and str(new_cust).strip():
            old_cust = d.customer.name if d.customer else ""
            if new_cust.strip().lower() != old_cust.lower():
                changes["customer_name"] = {"old": old_cust, "new": new_cust.strip()}

        for fld, diff in changes.items():
            sample_changes_flat.append({
                "imei": imei,
                "field": fld,
                "old_val": diff["old"],
                "new_val": diff["new"]
            })

        sample_changes_grouped.append({
            "id": d.id,
            "imei": imei,
            "customer_name": d.customer.name if d.customer else "",
            "changes": changes,
            "fields_changed_count": len(changes)
        })

    return {
        "total_rows": total_rows,
        "total_values": total_rows,
        "matching_imeis": matching_count,
        "matching_records": matching_count,
        "unmatched_imeis": unmatched_count,
        "unmatched_values": unmatched_count,
        "duplicates_in_file": duplicate_count,
        "duplicate_imeis": duplicate_count,
        "invalid_imeis": invalid_count,
        "eligible_to_update": eligible_count,
        "eligible_for_update": eligible_count,
        "sample_changes": sample_changes_flat if mappings else sample_changes_grouped,
        "detailed_samples": sample_changes_grouped
    }


@router.post("/devices/bulk-edit/execute", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def bulk_edit_execute(data: schemas.BulkEditExecuteIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Executes bulk update of matching inventory records by IMEI."""
    input_rows = data.file_rows if data.file_rows is not None else (data.rows or [])
    total_input = len(input_rows)
    imei_col_raw = (data.imei_col or data.imei_column or "imei").strip()
    mappings = data.field_mappings or {}

    if not total_input:
        return {"success": True, "total_submitted": 0, "total_processed": 0, "updated": 0, "updated_count": 0, "skipped": 0, "skipped_count": 0, "unmatched": 0, "unmatched_count": 0, "duplicate_count": 0, "failures_count": 0, "errors": []}

    row_map = {}
    seen = set()
    dup_count = 0
    invalid_count = 0

    for r in input_rows:
        if mappings:
            row_dict = {}
            for ex_col, db_fld in mappings.items():
                if ex_col in r:
                    row_dict[db_fld] = r[ex_col]
            raw_imei = str(r.get(imei_col_raw) or r.get("imei") or r.get(imei_col_raw.lower()) or "").strip()
        else:
            row_dict = dict(r)
            raw_imei = str(r.get(imei_col_raw) or r.get("imei") or r.get(imei_col_raw.lower()) or "").strip()

        if re.search(r"e\+", raw_imei, re.I):
            try:
                raw_imei = str(int(float(raw_imei)))
            except Exception:
                pass
        clean = re.sub(r"[^0-9A-Za-z_-]", "", raw_imei).strip()
        if not clean or len(clean) < 5:
            invalid_count += 1
            continue
        if clean in seen:
            dup_count += 1
        else:
            seen.add(clean)
            row_map[clean] = row_dict

    unique_imeis = list(row_map.keys())
    updated_count = 0
    matched_set = set()
    failures_count = 0
    chunk_size = 500

    cust_cache = {c.name.lower(): c.id for c in db.query(Customer.id, Customer.name).filter(Customer.deleted_at.is_(None))}

    for i in range(0, len(unique_imeis), chunk_size):
        chunk = unique_imeis[i:i + chunk_size]
        devs = db.query(Device).options(joinedload(Device.customer)).filter(
            Device.deleted_at.is_(None),
            Device.imei.in_(chunk)
        ).all()

        for d in devs:
            matched_set.add(d.imei)
            new_data = row_map.get(d.imei, {})
            try:
                has_change = False
                for fld in ["model", "sim_provider", "activation_plan", "firmware", "flash", "sim_type", "device_sr_no", "iccid", "msisdn1", "msisdn2"]:
                    if fld in new_data:
                        v = new_data[fld]
                        if v is not None and str(v).strip() != "":
                            setattr(d, fld, str(v).strip())
                            has_change = True

                for fld in ["act_date", "expiry_date", "dispatched_date"]:
                    if fld in new_data:
                        v = new_data[fld]
                        if v is not None and str(v).strip() != "":
                            parsed_d = normalize_date_input(str(v).strip())
                            if parsed_d:
                                setattr(d, fld, parsed_d)
                                has_change = True

                if "customer_name" in new_data and str(new_data["customer_name"]).strip():
                    new_cname = str(new_data["customer_name"]).strip()
                    lower_c = new_cname.lower()
                    if lower_c not in cust_cache:
                        new_cust_obj = Customer(name=new_cname)
                        db.add(new_cust_obj)
                        db.flush()
                        cust_cache[lower_c] = new_cust_obj.id
                    d.customer_id = cust_cache[lower_c]
                    has_change = True

                if "extra" in new_data and isinstance(new_data["extra"], dict):
                    cur_extra = dict(d.extra or {})
                    for ek, ev in new_data["extra"].items():
                        if ev is not None and str(ev).strip() != "":
                            cur_extra[str(ek).strip()] = str(ev).strip()
                    d.extra = cur_extra
                    has_change = True

                if has_change:
                    updated_count += 1
            except Exception:
                failures_count += 1

        db.commit()

    unmatched_count = max(0, len(unique_imeis) - len(matched_set))
    log_activity(db, "bulk_edit", f"Bulk updated {updated_count} devices by IMEI (processed {total_input})", user=user)

    return {
        "success": True,
        "total_submitted": total_input,
        "total_processed": total_input,
        "updated": updated_count,
        "updated_count": updated_count,
        "unmatched": unmatched_count,
        "unmatched_count": unmatched_count,
        "skipped": dup_count + invalid_count,
        "skipped_count": dup_count + invalid_count,
        "duplicate_count": dup_count,
        "invalid_count": invalid_count,
        "failures_count": failures_count,
        "errors": []
    }

