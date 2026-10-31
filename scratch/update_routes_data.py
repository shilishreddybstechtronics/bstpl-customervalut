with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update sort logic in build_device_query for SIM expiry
old_sort = """    sort_fields = {
        "id": Device.id,
        "imei": Device.imei,
        "customer_name": Customer.name,
        "device_sr_no": Device.device_sr_no,
        "iccid": Device.iccid,
        "ccid": Device.iccid,
        "act_date": Device.act_date,
        "expiry_date": Device.expiry_date,
        "model": Device.model,
        "sim_provider": Device.sim_provider,
    }
    col_attr = sort_fields.get((sort_by or "").lower(), Device.id)
    return query.order_by(desc(col_attr) if sort_dir == "desc" else asc(col_attr), asc(Device.id))"""

new_sort = """    sort_fields = {
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
    return query.order_by(desc(col_attr) if sort_dir == "desc" else asc(col_attr), asc(Device.id))"""

if old_sort in code:
    code = code.replace(old_sort, new_sort)
    print("Updated build_device_query sorting successfully")
else:
    print("Could not find old_sort in routes_data.py")

# 2. Update inventory_health to be fast, accurate, and robust
old_health = """@router.get("/inventory/health", dependencies=[Depends(require_permission("view"))])
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
    }"""

new_health = """@router.get("/inventory/health", dependencies=[Depends(require_permission("view"))])
def inventory_health(db: Session = Depends(get_db)):
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

    return {
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

if old_health in code:
    code = code.replace(old_health, new_health)
    print("Updated inventory_health successfully")
else:
    print("Could not find old_health in routes_data.py")

with open('backend/routes_data.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Finished updating backend/routes_data.py")

