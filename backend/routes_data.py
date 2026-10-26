import io
import re
import time
from datetime import date, datetime, timedelta
from typing import Optional, Literal

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import String, case, cast, func, insert, or_, desc, asc
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, joinedload

import customer_tables
import models, schemas
from activity import log_activity
from auth import get_current_user, require_admin, require_staff
from database import get_db

# Every route here needs a signed-in user.
router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])

Device, Customer = models.Device, models.Customer
ACTIVE = Device.deleted_at.is_(None)
BASE_COLUMNS = ["customer_name", "device_sr_no", "imei", "iccid", "msisdn1", "msisdn2", "act_date", "expiry_date",
                "dispatched_date", "model", "sim_provider", "activation_plan", "firmware", "flash", "sim_type"]
# Plain-text device fields that can be copied straight from an upload / edit form
TEXT_FIELDS = ["device_sr_no", "iccid", "msisdn1", "msisdn2", "model", "sim_provider", "activation_plan",
               "firmware", "flash"]


def escape_like(s: str) -> str:
    """So a search for 50% or a_b means those exact characters, not wildcards."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def classify_sim_type(iccid: Optional[str]) -> str:
    if not iccid:
        return "Plastic SIM"
    s = str(iccid).strip()
    if s.startswith(('8901', '8988', '8986', '8991')) or len(s) == 20:
        return "E-SIM"
    return "Plastic SIM"


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


def out(d: Device) -> dict:
    return {
        "id": d.id, "customer_id": d.customer_id,
        "customer_name": d.customer.name if d.customer else None,
        "device_sr_no": d.device_sr_no, "imei": d.imei, "iccid": d.iccid,
        "msisdn1": d.msisdn1, "msisdn2": d.msisdn2,
        "act_date": d.act_date, "expiry_date": d.expiry_date, "dispatched_date": d.dispatched_date,
        "model": d.model, "sim_provider": d.sim_provider, "activation_plan": d.activation_plan,
        "firmware": d.firmware, "flash": d.flash, "sim_type": d.sim_type,
        "extra": d.extra or {},
        "days_left": (d.expiry_date - date.today()).days if d.expiry_date else None,
        "added_by": d.added_by, "deleted_at": d.deleted_at,
        "deleted_by": d.deleted_by, "delete_reason": d.delete_reason,
    }


def customer_by_name(db: Session, name: str) -> Customer:
    raw = (name or "").strip()
    clean_name = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_") or raw
    c = db.query(Customer).filter(func.lower(Customer.name) == clean_name.lower()).first()
    if c and c.deleted_at:  # adding devices to a deleted customer's name brings the customer back
        c.deleted_at = c.deleted_by = None
    if not c:
        c = Customer(name=clean_name)
        db.add(c)
        db.flush()
        try:
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


# ---------- dashboard ----------
@router.get("/stats")
def stats(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    count = lambda *f: db.query(func.count(Device.id)).filter(*f).scalar()
    return {
        "customers": db.query(func.count(Customer.id)).filter(Customer.deleted_at.is_(None)).scalar(),
        "devices": count(ACTIVE),
        "added_by_you": count(ACTIVE, Device.added_by == user.id),
        "columns": len(BASE_COLUMNS) + db.query(func.count(models.ColumnRegistry.name)).scalar(),
        "deleted": count(Device.deleted_at.isnot(None)),
        "expiring_30_days": count(ACTIVE, Device.expiry_date <= date.today() + timedelta(days=30)),
        "errored_records": db.query(func.count(models.ErroredRecord.id)).scalar() or 0,
    }


@router.get("/columns")
def columns(db: Session = Depends(get_db)):
    """Extra column names found in uploads, shown after the built-in columns."""
    return [n for (n,) in db.query(models.ColumnRegistry.name).order_by(models.ColumnRegistry.name)]


# ---------- customers ----------
@router.get("/customers")
def customers(db: Session = Depends(get_db)):
    soon = date.today() + timedelta(days=30)
    rows = (db.query(Customer.id, Customer.name, Customer.avatar, func.count(Device.id),
                     func.sum(case((Device.expiry_date <= soon, 1), else_=0)))
            .outerjoin(Device, (Device.customer_id == Customer.id) & ACTIVE)
            .filter(Customer.deleted_at.is_(None))
            .group_by(Customer.id, Customer.name, Customer.avatar).order_by(Customer.name).all())
    return [{"id": i, "name": n, "avatar": a, "devices": c, "expiring_or_expired": int(e or 0)} for i, n, a, c, e in rows]


@router.post("/customers", status_code=201)
def add_customer(data: schemas.CustomerIn, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    c = customer_by_name(db, data.name.strip())
    log_activity(db, "customer_add", f"Customer {c.name}", user=user)
    db.commit()
    try:  # give the new customer its own (empty) table right away
        with customer_tables.engine.begin() as conn:
            customer_tables.ensure_table(conn, c.id, c.name)
    except Exception as e:
        print(f"Customer table create failed: {e}")
    return {"id": c.id, "name": c.name}


# ---------- devices ----------
def build_device_query(db: Session, customer_id, q, column, sort_by, sort_dir):
    """Search + sort shared by the table and the Excel export, so both always agree."""
    query = db.query(Device).join(Customer).options(joinedload(Device.customer)).filter(ACTIVE)
    if customer_id:
        query = query.filter(Device.customer_id == customer_id)
    q = q.strip()
    if q:
        like = f"%{escape_like(q)}%"
        col_map = {
            "imei": Device.imei,
            "iccid": Device.iccid,
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
        if column and column in col_map:
            query = query.filter(col_map[column].like(like))
        else:
            cols = [Device.device_sr_no, Device.imei, Device.iccid, Device.msisdn1, Device.msisdn2, Customer.name,
                    Device.model, Device.sim_provider, Device.activation_plan, Device.firmware, Device.flash, Device.sim_type]
            query = query.filter(or_(*[c.like(like) for c in cols],
                                     cast(Device.act_date, String).like(like),
                                     cast(Device.dispatched_date, String).like(like),
                                     cast(Device.expiry_date, String).like(like),
                                     cast(Device.extra, String).like(like)))

    sort_fields = {
        "id": Device.id,
        "imei": Device.imei,
        "customer_name": Customer.name,
        "device_sr_no": Device.device_sr_no,
        "iccid": Device.iccid,
        "act_date": Device.act_date,
        "expiry_date": Device.expiry_date,
        "model": Device.model,
        "sim_provider": Device.sim_provider,
    }
    col_attr = sort_fields.get(sort_by, Device.id)
    return query.order_by(desc(col_attr) if sort_dir == "desc" else asc(col_attr), asc(Device.id))


@router.get("/devices")
def list_devices(customer_id: Optional[int] = None, q: str = "", column: Optional[str] = "all",
                 sort_by: Optional[str] = "id", sort_dir: Optional[str] = "asc",
                 page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=5000),
                 db: Session = Depends(get_db)):
    query = build_device_query(db, customer_id, q, column, sort_by, sort_dir)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size,
            "pages": max(1, -(-total // page_size)), "items": [out(d) for d in items]}


@router.get("/devices/export")
def export_devices(customer_id: Optional[int] = None, q: str = "", column: Optional[str] = "all",
                   sort_by: Optional[str] = "id", sort_dir: Optional[str] = "asc",
                   title: str = "Customer_Inventory_Export",
                   db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """EVERY record that matches the current filters (not just one page) as an Excel file."""
    query = build_device_query(db, customer_id, q, column, sort_by, sort_dir)
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


@router.post("/devices/bulk/validate")
def bulk_validate(data: schemas.BulkIn, db: Session = Depends(get_db)):
    imeis = [r.imei.strip() for r in data.rows if r.imei]
    existing = set()  # only ACTIVE records count: a device sitting in the recycle bin can be uploaded again
    for i in range(0, len(imeis), 2000):
        for (v,) in db.query(Device.imei).filter(Device.imei.in_(imeis[i:i + 2000]), ACTIVE):
            existing.add(v)

    seen = set()
    valid, duplicates, invalids = [], [], []

    for idx, r in enumerate(data.rows, start=1):
        errs = []
        if not r.imei:
            errs.append("Missing IMEI")
        if not r.customer_name:
            errs.append("Missing Customer Name")
        if r.act_date and r.expiry_date and r.expiry_date < r.act_date:
            errs.append("Expiry date is before Activation date")
        if r.imei and (len(r.imei) != 15 or not r.imei.isdigit()):
            errs.append("IMEI should be 15 digits")

        row_dict = r.model_dump()
        row_dict["sim_type"] = r.sim_type or classify_sim_type(r.iccid)
        row_dict["row_num"] = idx

        if errs:
            row_dict["errors"] = errs
            invalids.append(row_dict)
        elif r.imei in seen or r.imei in existing:
            row_dict["reason"] = "Already in database" if r.imei in existing else "Duplicate in this file"
            duplicates.append(row_dict)
            seen.add(r.imei)
        else:
            seen.add(r.imei)
            valid.append(row_dict)

    return {
        "valid_count": len(valid),
        "duplicate_count": len(duplicates),
        "invalid_count": len(invalids),
        "valid_sample": valid[:50],
        "duplicates": duplicates[:20000],
        "invalids": invalids[:20000]
    }


def insert_chunk(db: Session, rows: list):
    """Inserts one chunk in a single multi-row INSERT and commits it. If an error occurs (such as
    invalid values, encoding or integrity issue in any row), falls back to row-by-row insertion
    so that only the bad record is skipped and every valid row in the chunk proceeds successfully."""
    if not rows:
        return
    for attempt in range(3):
        try:
            db.execute(insert(Device), rows)
            db.commit()
            return
        except OperationalError:
            db.rollback()
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            # Multi-row batch failed; retry row-by-row to ignore invalid values and proceed
            db.rollback()
            for r in rows:
                try:
                    db.execute(insert(Device), [r])
                    db.commit()
                except Exception as inner_e:
                    db.rollback()
                    print(f"Skipping problematic row during bulk upload ({r.get('imei')}): {inner_e}")
            return


@router.post("/devices/bulk")
def bulk_add(data: schemas.BulkIn, db: Session = Depends(get_db),
             user: models.User = Depends(get_current_user)):
    imeis = [r.imei.strip() for r in data.rows if r.imei]
    mode = getattr(data, "mode", "skip") or "skip"

    existing_devices = {}
    for i in range(0, len(imeis), 2000):
        for d in db.query(Device).filter(Device.imei.in_(imeis[i:i + 2000])):
            existing_devices[d.imei] = d

    cache, added, updated, skipped, names = {}, 0, 0, [], set()
    seen_in_batch = set()
    mirror = []  # rows to copy into each customer's own table
    new_rows = []  # rows inserted in a few big batches instead of one round trip per row

    for r in data.rows:
        try:
            if not r.imei:
                continue
            raw_imei = str(r.imei).strip()
            if "e+" in raw_imei.lower():
                try:
                    raw_imei = str(int(float(raw_imei)))
                except Exception:
                    pass
            imei = re.sub(r"[^0-9A-Za-z_-]", "", raw_imei)
            if not imei or len(imei) < 5:
                continue

            cust_name = str(r.customer_name or "").strip()
            if not cust_name:
                continue

            if imei in seen_in_batch and mode == "skip":
                skipped.append(imei)
                continue
            seen_in_batch.add(imei)

            key = cust_name.lower()
            if key not in cache:
                cache[key] = customer_by_name(db, cust_name)
            cust = cache[key]

            exp = r.expiry_date or (r.act_date + timedelta(days=365) if r.act_date else None)
            stype = r.sim_type or classify_sim_type(r.iccid)
            extra = clean_extra(r.extra)
            names.update(extra)

            if imei in existing_devices:
                in_bin = getattr(existing_devices[imei], "deleted_at", None)  # deleted earlier: bring it back instead of skipping it
                if mode == "replace" or in_bin:
                    d = existing_devices[imei]
                    d.customer_id = cust.id
                    d.act_date = r.act_date or d.act_date
                    d.expiry_date = exp or d.expiry_date
                    d.dispatched_date = r.dispatched_date or d.dispatched_date
                    d.sim_type = stype or d.sim_type
                    for f in TEXT_FIELDS:
                        val = getattr(r, f, None)
                        if val is not None and val != "":
                            setattr(d, f, str(val)[:150])
                    if extra:
                        merged = {**(d.extra or {}), **extra}
                        d.extra = merged or None
                    if d.deleted_at:
                        d.deleted_at = d.deleted_by = d.delete_reason = None
                    updated += 1
                    mirror.append((cust.id, cust.name, {
                        "imei": imei, "customer_name": cust.name, "act_date": d.act_date, "expiry_date": d.expiry_date, "dispatched_date": d.dispatched_date,
                        "sim_type": d.sim_type, "extra": d.extra or {}, **{f: getattr(d, f) for f in TEXT_FIELDS}}))
                else:
                    skipped.append(imei)
            else:
                row_vals = {f: (str(getattr(r, f))[:150] if getattr(r, f, None) is not None else None) for f in TEXT_FIELDS}
                new_rows.append(dict(
                    customer_id=cust.id, imei=imei, act_date=r.act_date, expiry_date=exp,
                    dispatched_date=r.dispatched_date, sim_type=stype, extra=extra or None,
                    added_by=user.id, **row_vals
                ))
                existing_devices[imei] = True
                added += 1
                mirror.append((cust.id, cust.name, {
                    "imei": imei, "customer_name": cust.name, "act_date": r.act_date, "expiry_date": exp, "dispatched_date": r.dispatched_date,
                    "sim_type": stype, "extra": extra, **row_vals}))
        except Exception as row_err:
            print(f"Skipping row error in bulk_add: {row_err}")
            continue

    try:
        db.commit()  # customers first
    except Exception as ce:
        db.rollback()
        print(f"Commit error during bulk_add customers: {ce}")

    saved = 0
    try:
        for i in range(0, len(new_rows), 500):  # pymysql turns each list into ONE multi-row INSERT
            chunk = new_rows[i:i + 500]
            insert_chunk(db, chunk)
            saved += len(chunk)
        register_columns(db, names)
        if len(data.rows) == 1:
            log_activity(db, "device_add", f"IMEI {data.rows[0].imei}" + (" (updated)" if updated else "" if added else " (skipped)"), user=user)
        else:
            log_activity(db, "device_upload", f"{saved} added, {updated} updated, {len(skipped)} duplicates skipped (batch of {len(data.rows)})", user=user)
        db.commit()
    except OperationalError:
        db.rollback()
        raise HTTPException(503, f"The database did not answer in time. {saved} of {len(new_rows)} new records were saved. "
                                 "Upload the same file again: records already saved are skipped automatically. "
                                 "Then run  python customer_tables.py  once to fill the customer tables.")

    try:  # per-customer tables; a failure here never breaks the upload itself
        customer_tables.mirror_rows(mirror)
    except Exception as e:
        print(f"Customer table sync failed: {e}")
    return {"added": added, "updated": updated, "skipped_duplicates": len(skipped), "skipped_imeis": skipped[:50]}


@router.post("/devices/sheet-upload")
def sheet_upload(data: schemas.BulkIn, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    return bulk_add(data, db, user)


@router.post("/devices", status_code=201)
def add_device(data: schemas.DeviceIn, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    if not data.imei or len(data.imei) < 5 or not data.customer_name:
        raise HTTPException(400, "Customer name and a valid IMEI are required.")
    res = bulk_add(schemas.BulkIn(rows=[data]), db, user)
    if not res["added"]:
        raise HTTPException(400, "A device with this IMEI already exists (it may be in Deleted Customers).")
    return res


@router.post("/simdata/apply")
def apply_sim_data(data: schemas.SimDataApplyIn, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    iccids = [r.iccid.strip() for r in data.rows if r.iccid and len(r.iccid.strip()) >= 5]
    devices = []
    for i in range(0, len(iccids), 2000):
        devices += db.query(Device).filter(ACTIVE, Device.iccid.in_(iccids[i:i + 2000])).all()
    dev_by_iccid = {d.iccid: d for d in devices}

    updated, unmatched = 0, []
    for r in data.rows:
        try:
            if not r.iccid or len(r.iccid.strip()) < 5:
                continue
            iccid = r.iccid.strip()
            if iccid in dev_by_iccid:
                d = dev_by_iccid[iccid]
                if r.sim_provider: d.sim_provider = str(r.sim_provider)[:150]
                if r.model: d.model = str(r.model)[:150]
                if r.activation_plan: d.activation_plan = str(r.activation_plan)[:150]
                if r.firmware: d.firmware = str(r.firmware)[:150]
                if r.flash: d.flash = str(r.flash)[:150]
                if r.sim_type: d.sim_type = str(r.sim_type)[:100]
                elif not d.sim_type: d.sim_type = classify_sim_type(iccid)
                if r.act_date: d.act_date = r.act_date
                if r.expiry_date: d.expiry_date = r.expiry_date
                updated += 1
            else:
                unmatched.append(iccid)
        except Exception as e:
            print(f"Skipping invalid SIM row: {e}")
            continue

    log_activity(db, "simdata_apply", f"Updated {updated} devices from SIM provider data ({len(unmatched)} unmatched)", user=user)
    db.commit()
    return {"updated": updated, "unmatched_count": len(unmatched), "unmatched_iccids": unmatched[:5000]}


@router.post("/fetch/bulk")
def bulk_fetch(data: schemas.BulkFetchIn, db: Session = Depends(get_db)):
    terms = [q.strip() for q in data.queries if q.strip()]
    if not terms:
        return {"exact_matches": [], "similar_matches": [], "total_matches": 0}

    field = data.field or "all"
    query = db.query(Device).options(joinedload(Device.customer)).filter(ACTIVE)

    if field == "imei":
        exact_query = query.filter(Device.imei.in_(terms))
    elif field == "iccid":
        exact_query = query.filter(Device.iccid.in_(terms))
    elif field == "device_sr_no":
        exact_query = query.filter(Device.device_sr_no.in_(terms))
    elif field == "msisdn1":
        exact_query = query.filter(Device.msisdn1.in_(terms))
    else:
        exact_query = query.filter(or_(
            Device.imei.in_(terms),
            Device.iccid.in_(terms),
            Device.device_sr_no.in_(terms),
            Device.msisdn1.in_(terms),
            Device.msisdn2.in_(terms)
        ))
    exact_items = exact_query.all()
    exact_set = {d.id for d in exact_items}

    similar_items = []
    if len(terms) <= 20:
        for t in terms:
            like = f"%{escape_like(t)}%"
            sim_q = query.filter(or_(
                Device.imei.like(like),
                Device.iccid.like(like),
                Device.device_sr_no.like(like),
                Device.msisdn1.like(like)
            )).limit(10).all()
            for s in sim_q:
                if s.id not in exact_set and s.id not in {x.id for x in similar_items}:
                    similar_items.append(s)

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
        "total_matches": len(exact_res) + len(similar_res)
    }


@router.get("/devices/quick-search")
def quick_search(q: str = Query("", min_length=1), db: Session = Depends(get_db)):
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

    return {
        "customers": [{"id": c.id, "name": c.name, "exact": c.name.lower() == term.lower()} for c in custs],
        "devices": [{**out(d), "exact": term.lower() in [str(d.imei or '').lower(), str(d.iccid or '').lower(), str(d.device_sr_no or '').lower()]} for d in devs]
    }


@router.get("/inventory/insights")
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


@router.get("/inventory/health")
def inventory_health(db: Session = Depends(get_db)):
    def find_dups(column):
        return db.query(column, func.count(Device.id)).filter(ACTIVE, column.isnot(None), column != '').group_by(column).having(func.count(Device.id) > 1).all()

    dup_imei = find_dups(Device.imei)
    dup_iccid = find_dups(Device.iccid)
    dup_m1 = find_dups(Device.msisdn1)
    dup_m2 = find_dups(Device.msisdn2)
    dup_sr = find_dups(Device.device_sr_no)

    total = db.query(func.count(Device.id)).filter(ACTIVE).scalar() or 0

    bad_imeis = (db.query(Device).options(joinedload(Device.customer))
                 .filter(ACTIVE, or_(func.length(Device.imei) != 15, Device.imei.op('REGEXP')('^[0-9]+$') == 0))
                 .limit(100).all())

    bad_dates = (db.query(Device).options(joinedload(Device.customer))
                 .filter(ACTIVE, Device.act_date.isnot(None), Device.expiry_date.isnot(None), Device.expiry_date < Device.act_date)
                 .limit(100).all())

    cols = ["customer_name", "device_sr_no", "imei", "iccid", "msisdn1", "msisdn2", "act_date", "expiry_date",
            "dispatched_date", "model", "sim_provider", "activation_plan", "firmware", "flash", "sim_type"]
    completeness = {}
    if total > 0:
        for c in cols:
            if c == "customer_name":
                cnt = db.query(func.count(Device.id)).join(Customer).filter(ACTIVE, Customer.name.isnot(None), Customer.name != '').scalar() or 0
            else:
                attr = getattr(Device, c)
                cnt = db.query(func.count(Device.id)).filter(ACTIVE, attr.isnot(None), attr != '').scalar() or 0
            completeness[c] = round((cnt / total) * 100, 1)

    issues = []
    for val, count in dup_imei[:20]:
        issues.append({"type": "Duplicate IMEI", "identifier": val, "count": count, "description": f"IMEI {val} appears {count} times"})
    for val, count in dup_iccid[:20]:
        issues.append({"type": "Duplicate ICCID", "identifier": val, "count": count, "description": f"ICCID {val} appears {count} times"})
    for val, count in dup_sr[:20]:
        issues.append({"type": "Duplicate Sr No", "identifier": val, "count": count, "description": f"Device Sr No {val} appears {count} times"})
    for d in bad_imeis[:20]:
        issues.append({"type": "Invalid IMEI Length", "identifier": d.imei, "count": 1, "description": f"Device #{d.id} IMEI '{d.imei}' has length {len(d.imei or '')} (expected 15 digits)"})
    for d in bad_dates[:20]:
        issues.append({"type": "Expiry Before Activation", "identifier": d.imei, "count": 1, "description": f"Device #{d.id} expires on {d.expiry_date} before activation on {d.act_date}"})

    return {
        "total_records": total,
        "duplicate_imei_count": len(dup_imei),
        "duplicate_iccid_count": len(dup_iccid),
        "duplicate_msisdn1_count": len(dup_m1),
        "duplicate_msisdn2_count": len(dup_m2),
        "duplicate_sr_count": len(dup_sr),
        "bad_imei_count": len(bad_imeis),
        "bad_date_count": len(bad_dates),
        "completeness": completeness,
        "issues": issues
    }


@router.get("/inventory/report")
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


@router.post("/export")
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


@router.post("/columns/delete", dependencies=[Depends(require_admin)])
def delete_column(data: schemas.DeleteColumnIn, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    col_name = data.column_name.strip()
    norm = col_name.lower().replace(' ', '_')
    if norm in BASE_COLUMNS:
        raise HTTPException(400, f"Cannot delete '{col_name}' because it is a core system column.")

    entry = db.query(models.ColumnRegistry).filter(models.ColumnRegistry.name == col_name).first()
    if entry:
        db.delete(entry)

    devices_with_extra = db.query(Device).filter(Device.extra.isnot(None)).all()
    count_cleaned = 0
    for d in devices_with_extra:
        if d.extra and col_name in d.extra:
            updated_extra = dict(d.extra)
            del updated_extra[col_name]
            d.extra = updated_extra if updated_extra else None
            count_cleaned += 1

    log_activity(db, "column_delete", f"Deleted column '{col_name}' (cleared from {count_cleaned} records)", user=admin)
    db.commit()
    return {"deleted": col_name, "records_affected": count_cleaned}


@router.get("/devices/lookup")
def lookup(value: str, db: Session = Depends(get_db)):
    v = value.strip()
    items = (db.query(Device).options(joinedload(Device.customer))
             .filter(ACTIVE, or_(Device.imei == v, Device.iccid == v, Device.msisdn1 == v,
                                 Device.msisdn2 == v, Device.device_sr_no == v)).limit(50).all())
    return [out(d) for d in items]


@router.get("/devices/{device_id}")
def get_device_by_id(device_id: int, db: Session = Depends(get_db)):
    d = db.query(Device).options(joinedload(Device.customer)).filter(Device.id == device_id, ACTIVE).first()
    if not d:
        raise HTTPException(404, "Device not found.")
    return out(d)


@router.put("/devices/{device_id}")
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
        row.update({f: getattr(d, f) for f in customer_tables.BASE_NAMES})
        customer_tables.mirror_single_device(d.customer_id, cname, row)
    except Exception as e:
        print(f"Customer table mirror failed: {e}")
    return out(d)


@router.get("/devices/by-imei/{imei}")
def get_by_imei(imei: str, db: Session = Depends(get_db)):
    return out(active_by_imei(db, imei))


@router.put("/devices/by-imei/{imei}")
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
        row.update({f: getattr(d, f) for f in customer_tables.BASE_NAMES})
        customer_tables.mirror_single_device(d.customer_id, cname, row)
    except Exception as e:
        print(f"Customer table mirror failed: {e}")
    return out(d)


@router.delete("/devices/by-imei/{imei}", dependencies=[Depends(require_staff)])
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


@router.delete("/devices/{device_id}", dependencies=[Depends(require_staff)])
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
@router.get("/alerts/expiry")
def expiry_alerts(days: int = Query(30, ge=0, le=365), customer_id: Optional[int] = None, limit: int = 5000, db: Session = Depends(get_db)):
    q = (db.query(Device).options(joinedload(Device.customer))
         .filter(ACTIVE, Device.expiry_date.isnot(None), Device.expiry_date <= date.today() + timedelta(days=days)))
    if customer_id:
        q = q.filter(Device.customer_id == customer_id)
    items = q.order_by(Device.expiry_date).limit(limit).all()
    return [out(d) for d in items]


# ---------- deleted customers (recycle bin) ----------
@router.get("/bin", dependencies=[Depends(require_staff)])
def bin_list(db: Session = Depends(get_db)):
    items = (db.query(Device).options(joinedload(Device.customer))
             .filter(Device.deleted_at.isnot(None)).order_by(Device.deleted_at.desc()).all())
    return [out(d) for d in items]


@router.post("/bin/{device_id}/restore", dependencies=[Depends(require_staff)])
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
    return {"restored": d.id}


@router.delete("/bin/{device_id}")
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


@router.delete("/bin")
def bin_empty(db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    # Drop tables for deleted customers permanently
    deleted_custs = db.query(Customer).filter(Customer.deleted_at.isnot(None)).all()
    for c in deleted_custs:
        try:
            customer_tables.drop_table(c.id, c.name)
        except Exception as e:
            print(f"Drop table on empty cart failed: {e}")
        db.delete(c)
    n = db.query(Device).filter(Device.deleted_at.isnot(None)).delete(synchronize_session=False)
    log_activity(db, "bin_empty", f"Emptied the bin ({n} records and {len(deleted_custs)} customers deleted forever)", user=admin)
    db.commit()
    return {"deleted_forever": n, "customers_purged": len(deleted_custs)}


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


@router.get("/errors")
def list_errors(db: Session = Depends(get_db)):
    rows = db.query(models.ErroredRecord).order_by(models.ErroredRecord.created_at.desc(), models.ErroredRecord.id.desc()).all()
    return [errored_out(r) for r in rows]


@router.post("/errors")
def save_errors(data: schemas.BulkErrorsIn, db: Session = Depends(get_db)):
    added = 0
    for item in data.records:
        rec = models.ErroredRecord(
            customer_name=item.customer_name,
            imei=item.imei,
            device_sr_no=item.device_sr_no,
            iccid=item.iccid,
            msisdn1=item.msisdn1,
            msisdn2=item.msisdn2,
            act_date=item.act_date,
            expiry_date=item.expiry_date,
            dispatched_date=item.dispatched_date,
            model=item.model,
            sim_provider=item.sim_provider,
            activation_plan=item.activation_plan,
            firmware=item.firmware,
            flash=item.flash,
            sim_type=item.sim_type,
            extra=item.extra,
            error_reason=item.error_reason or "Invalid entry"
        )
        db.add(rec)
        added += 1
    db.commit()
    return {"saved_errors": added}


@router.put("/errors/{error_id}/upload")
def upload_corrected_error(error_id: int, data: schemas.DeviceIn, db: Session = Depends(get_db),
                           user: models.User = Depends(get_current_user)):
    err = db.query(models.ErroredRecord).filter(models.ErroredRecord.id == error_id).first()
    if not err:
        raise HTTPException(404, "Errored record not found.")

    if not data.imei or len(data.imei.strip()) < 5 or not data.customer_name:
        raise HTTPException(400, "A valid IMEI (at least 5 characters) and Customer Name are required to upload.")

    # Ingest using bulk_add logic so customer and TiDB Cloud table are synchronized
    res = bulk_add(schemas.BulkIn(rows=[data], mode="replace"), db=db, user=user)

    # Remove from errored records table
    db.delete(err)
    db.commit()

    log_activity(db, "error_resolved", f"Corrected and uploaded record IMEI {data.imei} to customer {data.customer_name}", user=user)
    return {"success": True, "result": res}


@router.delete("/errors/{error_id}", dependencies=[Depends(require_staff)])
def move_error_to_cart(error_id: int, db: Session = Depends(get_db),
                       user: models.User = Depends(get_current_user)):
    err = db.query(models.ErroredRecord).filter(models.ErroredRecord.id == error_id).first()
    if not err:
        raise HTTPException(404, "Errored record not found.")

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


@router.post("/errors/empty", dependencies=[Depends(require_staff)])
def move_all_errors_to_cart(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    errors = db.query(models.ErroredRecord).all()
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
        count += 1
    db.commit()
    log_activity(db, "errors_trash_all", f"Moved {count} errored entries to Cart", user=user)
    return {"moved_all_to_cart": count}
