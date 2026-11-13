with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add import math
if 'import math' not in text:
    text = text.replace('import re\n', 'import re\nimport math\n', 1)

# 2. Update stats
old_stats = """# ---------- dashboard ----------
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
    }"""

new_stats = """# ---------- dashboard ----------
@router.get("/stats")
def stats(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    count = lambda *f: db.query(func.count(Device.id)).filter(*f).scalar()
    total_customers = db.query(func.count(Customer.id)).filter(Customer.deleted_at.is_(None)).scalar() or 0
    total_devices = count(ACTIVE) or 0
    added_by_you = count(ACTIVE, Device.added_by == user.id) or 0
    unique_columns = len(BASE_COLUMNS) + (db.query(func.count(models.ColumnRegistry.name)).scalar() or 0)
    deleted_devices = count(Device.deleted_at.isnot(None)) or 0
    expiring_30_days = count(ACTIVE, Device.expiry_date <= date.today() + timedelta(days=30)) or 0
    expired = count(ACTIVE, Device.expiry_date < date.today()) or 0
    errored_records = db.query(func.count(models.ErroredRecord.id)).scalar() or 0
    return {
        "customers": total_customers,
        "total_customers": total_customers,
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
    }"""

assert old_stats in text, "old_stats pattern not found"
text = text.replace(old_stats, new_stats, 1)

# 3. Update inventory_health
old_health_sig = """@router.get("/inventory/health", dependencies=[Depends(require_permission("view"))])
def inventory_health(db: Session = Depends(get_db)):"""

new_health_sig = """@router.get("/inventory/health", dependencies=[Depends(require_permission("view"))])
def inventory_health(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=5000),
                     select_all: bool = False, q: Optional[str] = None, db: Session = Depends(get_db)):"""

assert old_health_sig in text, "old_health_sig not found"
text = text.replace(old_health_sig, new_health_sig, 1)

old_health_return = """    return {
        "total_records": total,
        "duplicate_imei_count": len(dup_imei),
        "duplicate_iccid_count": len(dup_iccid),
        "duplicate_msisdn1_count": len(dup_m1),
        "duplicate_msisdn2_count": len(dup_m2),
        "duplicate_sr_count": len(dup_sr),
        "bad_imei_count": bad_imei_cnt,
        "bad_date_count": bad_date_cnt,
        "completeness": completeness,
        "issues": issues
    }"""

new_health_return = """    # Filter issues by search term if provided
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
    }"""

assert old_health_return in text, "old_health_return not found"
text = text.replace(old_health_return, new_health_return, 1)

# 4. Add Restore All and Customer Files Endpoints right after bin_restore
old_restore_target = """    return {"restored": d.id}"""
restore_all_code = """    return {"restored": d.id}


@router.post("/bin/restore-all", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
@router.post("/devices/restore-all", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def restore_all_deleted_devices(customer_id: Optional[int] = None, db: Session = Depends(get_db),
                                user: models.User = Depends(get_current_user)):
    q = db.query(Device).filter(Device.deleted_at.isnot(None))
    if customer_id:
        q = q.filter(Device.customer_id == customer_id)
    items = q.all()
    if not items:
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
    return {"customer_id": customer_id, "customer_name": cust.name, "records": count, "files": files}"""

assert old_restore_target in text, "old_restore_target not found"
text = text.replace(old_restore_target, restore_all_code, 1)

with open('backend/routes_data.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("SUCCESS: Updated backend/routes_data.py with dynamic stats, paginated health, restore-all, and customer files!")

