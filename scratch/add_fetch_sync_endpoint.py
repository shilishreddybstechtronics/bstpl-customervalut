with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    text = f.read()

fetch_sync_code = '''
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

    return {
        "total_scanned": len(terms),
        "success_count": len(successful_records),
        "error_count": len(error_entries),
        "successful_records": successful_records[:2000],
        "error_entries": error_entries
    }

'''

target_anchor = '@router.get("/devices/quick-search"'
if target_anchor in text and '/fetch/sync' not in text:
    idx = text.find(target_anchor)
    text = text[:idx] + fetch_sync_code + "\n" + text[idx:]
    with open('backend/routes_data.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("✓ Added /fetch/sync endpoint to backend/routes_data.py")
else:
    print("Already added or target anchor not found")

