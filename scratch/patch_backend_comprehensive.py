import sys
sys.path.insert(0, 'backend')
import re

print("Applying backend enhancements for Bulk Validate, Rectify Update, SIM Upload, and Fetch Sync...")

with open("backend/routes_data.py", "r", encoding="utf-8") as f:
    text = f.read()

# -----------------------------------------------------------------------------
# 1. Update bulk_validate to compare fields and identify "Requires Update" entries
# -----------------------------------------------------------------------------
old_bulk_val_start = r'@router\.post\("/devices/bulk/validate", dependencies=\[Depends\(require_permission\("upload"\)\)\]\)[\s\S]*?def bulk_validate\(data: schemas\.BulkIn, db: Session = Depends\(get_db\)\):'

# Locate bulk_validate function body up to insert_chunk
start_bv = text.find('@router.post("/devices/bulk/validate"')
end_bv = text.find('def insert_chunk(db: Session, rows: list) -> int:', start_bv)

if start_bv != -1 and end_bv != -1:
    new_bulk_validate_code = '''@router.post("/devices/bulk/validate", dependencies=[Depends(require_permission("upload"))])
def bulk_validate(data: schemas.BulkIn, db: Session = Depends(get_db)):
    """Step 2 & 3: Compare uploaded records against entire database using ICCID, IMEI, or Device Serial No.
    Identifies and segregates into:
    - Valid entries (Total eligible for insert or update)
    - New entries (Genuinely new - eligible for insertion)
    - Existing entries (Identical values already in DB)
    - Entries requiring updates (Differing field values - eligible for Rectify Update)
    - Duplicate entries (Repeating identifiers within file)
    - Invalid entries (Missing identifiers, bad date sequence, malformed data)
    - Entries requiring manual review (Customer ambiguous or data warnings)
    """
    iccids = [str(r.iccid or "").strip() for r in data.rows if (r.iccid or "").strip()]
    imeis = [str(r.imei or "").strip() for r in data.rows if (r.imei or "").strip()]
    sr_nos = [str(r.device_sr_no or "").strip() for r in data.rows if (r.device_sr_no or "").strip()]

    # Query all existing devices by ICCID across the entire database
    existing_devices_by_iccid = {}
    for i in range(0, len(iccids), 2000):
        for d in db.query(Device).options(joinedload(Device.customer)).filter(Device.iccid.in_(iccids[i:i + 2000]), ACTIVE):
            if d.iccid:
                existing_devices_by_iccid[d.iccid] = d
                existing_devices_by_iccid[d.iccid.lower()] = d

    # Query all existing devices by IMEI across the entire database
    existing_devices_map = {}
    for i in range(0, len(imeis), 2000):
        for d in db.query(Device).options(joinedload(Device.customer)).filter(Device.imei.in_(imeis[i:i + 2000]), ACTIVE):
            if d.imei:
                existing_devices_map[d.imei] = d
                existing_devices_map[d.imei.lower()] = d

    # Query existing devices by Device Sr No
    existing_devices_by_sr = {}
    for i in range(0, len(sr_nos), 2000):
        for d in db.query(Device).options(joinedload(Device.customer)).filter(Device.device_sr_no.in_(sr_nos[i:i + 2000]), ACTIVE):
            if d.device_sr_no:
                existing_devices_by_sr[d.device_sr_no] = d
                existing_devices_by_sr[d.device_sr_no.lower()] = d

    known_custs = {c.name.lower() for c in db.query(Customer.name).filter(Customer.deleted_at.is_(None))}
    known_custs_norm = {c.name.lower().replace('_', ' ') for c in db.query(Customer.name).filter(Customer.deleted_at.is_(None))}
    known_cols = {n.lower() for (n,) in db.query(models.ColumnRegistry.name)}
    known_cols.update(c.lower() for c in BASE_COLUMNS)

    seen_iccids, seen_imeis, seen_sr_nos = set(), set(), set()
    new_entries = []
    entries_requiring_update = []
    existing_entries = []
    duplicates = []
    invalids = []
    review_entries = []
    new_customers = set()
    new_columns = set()
    missing_columns = set()
    esim_count = 0
    plastic_count = 0

    has_iccid_any = any(bool(r.iccid) for r in data.rows)
    has_imei_any = any(bool(r.imei) for r in data.rows)
    if not has_iccid_any and not has_imei_any:
        missing_columns.add("ICCID / IMEI")

    for idx, r in enumerate(data.rows, start=1):
        errs = []
        cname = str(r.customer_name or "").strip()
        if not cname:
            errs.append("Missing or bad Customer Name")
        elif len(cname) > 100 or any(ch in cname for ch in [';', '`', "'", '"']):
            errs.append("Customer name contains invalid characters or exceeds 100 characters")
        elif cname.lower() not in known_custs and cname.lower().replace('_', ' ') not in known_custs_norm:
            new_customers.add(cname)

        if not r.iccid and not r.imei:
            errs.append("Missing both ICCID and IMEI identifier")

        if r.act_date and r.expiry_date and r.expiry_date < r.act_date:
            errs.append("Bad date sequence: Expiry date is before Activation date")

        for fld, name in [
            (r.device_sr_no, "Device Sr No"),
            (r.iccid, "ICCID"),
            (r.imei, "IMEI"),
            (r.msisdn1, "MSISDN1"),
            (r.msisdn2, "MSISDN2"),
            (r.model, "Model"),
            (r.sim_provider, "SIM Provider"),
            (r.activation_plan, "Activation Plan"),
            (r.firmware, "Firmware"),
            (r.flash, "Flash"),
        ]:
            if fld and len(str(fld)) > 255:
                errs.append(f"{name} exceeds 255 characters")

        if r.extra and isinstance(r.extra, dict):
            for k, v in r.extra.items():
                k_clean = str(k).strip()
                if not re.match(r"^[a-zA-Z0-9_\s-]+$", k_clean) or len(k_clean) > 64:
                    errs.append(f"Invalid column name '{k_clean}'")
                elif k_clean.lower() not in known_cols:
                    new_columns.add(k_clean)
                if v and len(str(v)) > 255:
                    errs.append(f"Value for '{k_clean}' exceeds 255 characters")

        stype = r.sim_type or ("E-SIM" if r.iccid else "Plastic SIM")
        if stype == "E-SIM":
            esim_count += 1
        elif stype:
            plastic_count += 1

        row_dict = r.model_dump()
        row_dict["sim_type"] = stype
        row_dict["row_num"] = idx
        row_dict["expiry_status"] = compute_expiry_status(r.expiry_date, 30)

        raw_iccid = str(r.iccid or "").strip()
        raw_imei = str(r.imei or "").strip()
        raw_sr = str(r.device_sr_no or "").strip()

        # Step 3: Segregate into Duplicates (within file), Invalids, Existing, Requires Update, and New Entries
        is_dup_in_file = False
        dup_file_reason = ""

        if raw_iccid and raw_iccid in seen_iccids:
            is_dup_in_file = True
            dup_file_reason = f"Duplicate ICCID '{raw_iccid}' repeats earlier in this uploaded file"
        elif raw_imei and raw_imei in seen_imeis:
            is_dup_in_file = True
            dup_file_reason = f"Duplicate IMEI '{raw_imei}' repeats earlier in this uploaded file"
        elif raw_sr and raw_sr in seen_sr_nos:
            is_dup_in_file = True
            dup_file_reason = f"Duplicate Device Sr No '{raw_sr}' repeats earlier in this uploaded file"

        if is_dup_in_file:
            row_dict["entry_type"] = "Duplicate"
            row_dict["status"] = "Duplicate"
            row_dict["reason"] = dup_file_reason
            duplicates.append(row_dict)
        elif errs:
            row_dict["entry_type"] = "Invalid"
            row_dict["status"] = "Invalid"
            row_dict["reason"] = "; ".join(errs)
            invalids.append(row_dict)
        else:
            # Check if record matches an existing device in the database
            matched_dev = None
            if raw_iccid and (raw_iccid in existing_devices_by_iccid or raw_iccid.lower() in existing_devices_by_iccid):
                matched_dev = existing_devices_by_iccid.get(raw_iccid) or existing_devices_by_iccid.get(raw_iccid.lower())
            elif raw_imei and (raw_imei in existing_devices_map or raw_imei.lower() in existing_devices_map):
                matched_dev = existing_devices_map.get(raw_imei) or existing_devices_map.get(raw_imei.lower())
            elif raw_sr and (raw_sr in existing_devices_by_sr or raw_sr.lower() in existing_devices_by_sr):
                matched_dev = existing_devices_by_sr.get(raw_sr) or existing_devices_by_sr.get(raw_sr.lower())

            if matched_dev:
                # Compare all fields to detect differences
                diffs = {}
                compare_fields = [
                    ("msisdn1", "MSISDN1"),
                    ("msisdn2", "MSISDN2"),
                    ("act_date", "Activation Date"),
                    ("expiry_date", "Expiry Date"),
                    ("dispatched_date", "Dispatched Date"),
                    ("model", "Model"),
                    ("sim_provider", "SIM Provider"),
                    ("sim_type", "SIM Type"),
                    ("activation_plan", "Activation Plan"),
                    ("firmware", "Firmware"),
                    ("flash", "Flash"),
                    ("device_sr_no", "Device Sr No")
                ]
                for f_key, f_lbl in compare_fields:
                    new_val = getattr(r, f_key, None)
                    old_val = getattr(matched_dev, f_key, None)
                    new_str = new_val.isoformat() if isinstance(new_val, date) else str(new_val or "").strip()
                    old_str = old_val.isoformat() if isinstance(old_val, date) else str(old_val or "").strip()
                    if new_str and new_str != old_str:
                        diffs[f_key] = {
                            "label": f_lbl,
                            "old": old_str or "—",
                            "new": new_str
                        }

                if r.extra and isinstance(r.extra, dict):
                    curr_extra = matched_dev.extra or {}
                    for ek, ev in r.extra.items():
                        ek_s = str(ek).strip()
                        ev_s = str(ev or "").strip()
                        old_ev = str(curr_extra.get(ek_s) or "").strip()
                        if ev_s and ev_s != old_ev:
                            diffs[f"extra_{ek_s}"] = {
                                "label": ek_s.replace("_", " ").upper(),
                                "old": old_ev or "—",
                                "new": ev_s
                            }

                row_dict["existing_id"] = matched_dev.id
                row_dict["existing_customer_name"] = matched_dev.customer.name if matched_dev.customer else "General_Customer"
                row_dict["existing_imei"] = matched_dev.imei or ""
                row_dict["existing_iccid"] = matched_dev.iccid or ""
                row_dict["existing_device_sr_no"] = matched_dev.device_sr_no or ""
                row_dict["changed_fields"] = diffs

                if diffs:
                    row_dict["entry_type"] = "Requires Update"
                    row_dict["status"] = "Requires Update"
                    row_dict["reason"] = f"{len(diffs)} field(s) differ from database record (Eligible for Rectify Update)"
                    entries_requiring_update.append(row_dict)
                else:
                    row_dict["entry_type"] = "Existing"
                    row_dict["status"] = "Existing"
                    row_dict["reason"] = "Already present in database with identical values (No updates needed)"
                    existing_entries.append(row_dict)
            else:
                # Truly NEW Entry eligible for insertion!
                row_dict["entry_type"] = "New"
                row_dict["status"] = "New"
                row_dict["reason"] = "New entry — eligible for insertion"
                new_entries.append(row_dict)

        if raw_iccid:
            seen_iccids.add(raw_iccid)
        if raw_imei:
            seen_imeis.add(raw_imei)
        if raw_sr:
            seen_sr_nos.add(raw_sr)

    valid = new_entries + entries_requiring_update

    cust_dups = {}
    for d in duplicates:
        cn = d.get("customer_name") or "General_Customer"
        cust_dups[cn] = cust_dups.get(cn, 0) + 1

    exp_expired_cnt = 0
    exp_soon_cnt = 0
    exp_active_cnt = 0
    exp_unknown_cnt = 0
    today = date.today()
    for r in data.rows:
        if not r.expiry_date:
            exp_unknown_cnt += 1
        elif r.expiry_date < today:
            exp_expired_cnt += 1
        elif r.expiry_date <= today + timedelta(days=30):
            exp_soon_cnt += 1
        else:
            exp_active_cnt += 1

    return {
        "valid_count": len(valid),
        "new_count": len(new_entries),
        "updated_count": len(entries_requiring_update),
        "existing_count": len(existing_entries),
        "duplicate_count": len(duplicates),
        "invalid_count": len(invalids),
        "review_count": len(review_entries),
        "rejected_count": len(duplicates) + len(invalids),
        "total_count": len(data.rows),
        "esim_count": esim_count,
        "plastic_count": plastic_count,
        "new_customers": sorted(list(new_customers)),
        "new_columns": sorted(list(new_columns)),
        "missing_columns_warning": list(missing_columns),
        "customer_duplicates": cust_dups,
        "expiry_counts": {
            "expired": exp_expired_cnt,
            "expiring_soon": exp_soon_cnt,
            "active": exp_active_cnt,
            "unknown": exp_unknown_cnt
        },
        "entries_requiring_update": entries_requiring_update[:50000],
        "new_sample": new_entries[:2000],
        "existing_sample": existing_entries[:2000],
        "valid_sample": valid[:2000],
        "duplicates": duplicates[:50000],
        "invalids": invalids[:2000],
        "all_sample": (new_entries[:150] + entries_requiring_update[:150] + existing_entries[:150]),
        "new_iccids": [r.get("iccid") for r in new_entries if r.get("iccid")],
        "new_imeis": [r.get("imei") for r in new_entries if r.get("imei")],
        "existing_iccids": list(existing_devices_by_iccid.keys()),
        "existing_imeis": list(existing_devices_map.keys()),
        "existing_sr_nos": list(existing_devices_by_sr.keys())
    }


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

'''
    text = text[:start_bv] + new_bulk_validate_code + text[end_bv:]
    print("✓ Replaced bulk_validate and added bulk_rectify endpoint")

# -----------------------------------------------------------------------------
# 2. Update check_sim_data & apply_sim_data to support new record insertion
# -----------------------------------------------------------------------------
# In check_sim_data: mark not_found_records as "New Record (Eligible for insertion)" and can_insert_count = len(not_found_records)
text = text.replace(
    '"status": "Not Found in Any Customer (Will NOT be uploaded)"',
    '"status": "New SIM Record (Eligible for insertion)"'
)
text = text.replace(
    '"can_insert_count": 0,',
    '"can_insert_count": len(not_found_keys),'
)

# In apply_sim_data: allow insert_new of genuinely new records into customer inventory!
old_apply_unmatched = r'''    # STRICT REQUIREMENT: If ICCID is not found, DO NOT upload/insert into any customer!
    # inserted_count is strictly 0. Only existing customer devices matched by ICCID are updated.
    inserted_count = 0'''

new_apply_unmatched = '''    # Requirement 4 & 5: Insert genuinely new records when confirmed
    inserted_count = 0
    if getattr(data, "insert_new", True) or getattr(data, "action", "both") in ("insert_only", "both"):
        target_cname = (getattr(data, "target_customer", None) or "General_Customer").strip()
        target_cust = db.query(Customer).filter(Customer.name.ilike(target_cname), Customer.deleted_at.is_(None)).first()
        if not target_cust:
            target_cust = db.query(Customer).filter(Customer.deleted_at.is_(None)).first()
        if not target_cust:
            target_cust = Customer(name=target_cname)
            db.add(target_cust)
            db.flush()

        for key, frow in file_sims.items():
            if frow["raw_key"] not in matched_keys:
                raw_ic = frow.get("raw_iccid") or frow["raw_key"]
                if raw_ic and len(raw_ic) >= 5:
                    new_dev = Device(
                        customer_id=target_cust.id,
                        iccid=raw_ic,
                        imei=frow.get("raw_imei") or f"SIM-{raw_ic[-8:]}",
                        msisdn1=frow.get("msisdn1"),
                        msisdn2=frow.get("msisdn2"),
                        act_date=frow.get("act_date"),
                        expiry_date=frow.get("expiry_date"),
                        sim_provider=frow.get("sim_provider") or chosen_provider or "Standard",
                        sim_type="E-SIM",
                        model="SIM Tracker",
                        added_by=user.display_name or user.name
                    )
                    db.add(new_dev)
                    inserted_count += 1'''

if old_apply_unmatched in text:
    text = text.replace(old_apply_unmatched, new_apply_unmatched)
    print("✓ Updated apply_sim_data to support inserting genuinely new records")

with open("backend/routes_data.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Backend patch applied successfully!")

