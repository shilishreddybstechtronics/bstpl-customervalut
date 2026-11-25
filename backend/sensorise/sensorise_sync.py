"""
Sensorise Telematics Synchronization Engine
Location: backend/sensorise/sensorise_sync.py

Connects CustomerVault device fetching directly to the live Sensorise Company Server (checkSIMBulk/v2).
Given ICCID values, queries Sensorise server for live MSISDN1, MSISDN2, Act Date, and Expiry Date,
replaces them in both the database and the website response, and ensures all other selected columns
(Customer Name, Device SR No, IMEI, ICCID / CCID Dispatched, Model, SIM Provider, Activation Plan,
Firmware, Flash, SIM Type, etc.) remain intact.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from sensorise import sensorise_client
except ImportError:
    try:
        from backend.sensorise import sensorise_client
    except ImportError:
        sensorise_client = None

try:
    import schemas
except ImportError:
    try:
        from backend import schemas
    except ImportError:
        schemas = None

try:
    import customer_tables
except ImportError:
    try:
        from backend import customer_tables
    except ImportError:
        customer_tables = None

logger = logging.getLogger("sensorise_sync")
if not logger.handlers:
    _sh = logging.StreamHandler()
    _sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(_sh)
logger.setLevel(logging.INFO)
logger.propagate = False

# In-memory cache for recent lookups: iccid -> {"data": ent, "ts": datetime}
_RECENT_SYNC_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL_SECONDS = 900  # 15 minutes


def _clean_iccid_term(val: Any) -> str:
    """Normalizes an ICCID string, stripping float suffixes and whitespace."""
    if not val:
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = s.replace(" ", "").replace("'", "").replace('"', "").upper()
    return s.strip()


def _extract_numeric_iccid(val: Any) -> str:
    """
    Extracts the strict numeric 18-22 digit ICCID for Sensorise server queries.
    Sensorise checkSIMBulk rejects trailing 'F' or non-digit characters.
    """
    clean = _clean_iccid_term(val)
    if clean.endswith("F"):
        clean = clean[:-1]
    numeric = re.sub(r"[^0-9]", "", clean)
    return numeric


def _parse_sensorise_date(raw_val: Any) -> Optional[date]:
    """
    Converts Sensorise server date (typically DD-MM-YYYY, e.g. '22-09-2024')
    or ISO string into a Python datetime.date object for database persistence.
    """
    if not raw_val:
        return None
    if isinstance(raw_val, date) and not isinstance(raw_val, datetime):
        return raw_val
    if isinstance(raw_val, datetime):
        return raw_val.date()

    s = str(raw_val).strip()
    if not s or s.lower() in ("nan", "none", "null", "-", "n/a", "0000-00-00", "00-00-0000"):
        return None

    # Case 1: Strict DD-MM-YYYY (standard Sensorise format)
    m_dmy = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", s)
    if m_dmy:
        try:
            return date(int(m_dmy.group(3)), int(m_dmy.group(2)), int(m_dmy.group(1)))
        except ValueError:
            pass

    # Case 2: ISO YYYY-MM-DD
    m_iso = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m_iso:
        try:
            return date(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
        except ValueError:
            pass

    # Case 3: schemas helper fallback
    if schemas and hasattr(schemas, "_to_date"):
        try:
            res = schemas._to_date(s)
            if isinstance(res, date):
                return res
        except Exception:
            pass

    return None


def fetch_sensorise_telematics_for_iccids(raw_iccids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Queries the Sensorise Company Server (checkSIMBulk/v2) for the given ICCID values.
    Returns a dictionary mapping both raw and numeric ICCID -> telematics entity.
    """
    if not raw_iccids or not sensorise_client:
        return {}

    now = datetime.now()
    telematics_results: Dict[str, Dict[str, Any]] = {}
    iccids_to_query: Set[str] = set()
    numeric_to_raw: Dict[str, List[str]] = {}

    for raw in raw_iccids:
        raw_clean = _clean_iccid_term(raw)
        if not raw_clean or len(raw_clean) < 6:
            continue

        num_iccid = _extract_numeric_iccid(raw_clean)
        if num_iccid and 16 <= len(num_iccid) <= 24:
            numeric_to_raw.setdefault(num_iccid, []).append(raw_clean)

            # Check in-memory cache first
            cached = _RECENT_SYNC_CACHE.get(num_iccid)
            if cached and (now - cached["ts"]).total_seconds() < _CACHE_TTL_SECONDS:
                telematics_results[num_iccid] = cached["data"]
                telematics_results[raw_clean] = cached["data"]
            elif num_iccid in getattr(sensorise_client, "raw_telematics_cache", {}):
                cached_data = sensorise_client.raw_telematics_cache[num_iccid]
                telematics_results[num_iccid] = cached_data
                telematics_results[raw_clean] = cached_data
            else:
                iccids_to_query.add(num_iccid)

    # Query Sensorise Server in chunks of 50
    if iccids_to_query:
        query_list = list(iccids_to_query)
        chunk_size = 50
        for i in range(0, len(query_list), chunk_size):
            chunk = query_list[i:i + chunk_size]
            try:
                bulk_res = sensorise_client.check_sim_bulk_v2(chunk)
                entities = bulk_res.get("simDetailEntity") or bulk_res.get("sim_entity") or []
                for ent in entities:
                    if isinstance(ent, dict):
                        ent["_from_sensorise_server"] = True
                        ent_iccid = _extract_numeric_iccid(ent.get("iccid"))
                        if ent_iccid:
                            telematics_results[ent_iccid] = ent
                            _RECENT_SYNC_CACHE[ent_iccid] = {"data": ent, "ts": now}
                            # Map to all raw ICCID representations
                            for raw_repr in numeric_to_raw.get(ent_iccid, []):
                                telematics_results[raw_repr] = ent
            except Exception as e:
                logger.warning(f"Sensorise checkSIMBulk query error: {e}")

    # Fallback to local telematics cache or database table sensorise_sims_basic if server had no record
    for raw in raw_iccids:
        raw_clean = _clean_iccid_term(raw)
        num_iccid = _extract_numeric_iccid(raw_clean)
        if raw_clean not in telematics_results and num_iccid in telematics_results:
            telematics_results[raw_clean] = telematics_results[num_iccid]
        elif raw_clean not in telematics_results and num_iccid in getattr(sensorise_client, "raw_telematics_cache", {}):
            ent = dict(sensorise_client.raw_telematics_cache[num_iccid])
            ent["_from_sensorise_server"] = True
            telematics_results[raw_clean] = ent
            telematics_results[num_iccid] = ent

    # Batch check database sensorise_sims_basic for any remaining ICCIDs
    missing_for_db = [r for r in raw_iccids if _clean_iccid_term(r) not in telematics_results and _extract_numeric_iccid(r) not in telematics_results]
    if missing_for_db:
        try:
            from sqlalchemy import text
            from database import engine
            terms_set = set()
            for raw in missing_for_db:
                clean_raw = _clean_iccid_term(raw)
                num_raw = _extract_numeric_iccid(clean_raw)
                if clean_raw:
                    terms_set.add(clean_raw)
                    terms_set.add(clean_raw + "F")
                if num_raw:
                    terms_set.add(num_raw)
            terms_list = list(terms_set)
            if terms_list:
                with engine.connect() as conn:
                    chunk_sz = 300
                    for c_idx in range(0, len(terms_list), chunk_sz):
                        chunk = terms_list[c_idx:c_idx + chunk_sz]
                        params = {f"ic_{k}": val for k, val in enumerate(chunk)}
                        in_clause = ",".join(f":ic_{k}" for k in range(len(chunk)))
                        sql = text(f"SELECT iccid, msisdn1, msisdn2, activation_date, expiry_date FROM sensorise_sims_basic WHERE iccid IN ({in_clause})")
                        rows = conn.execute(sql, params).fetchall()
                        for row in rows:
                            if row and (row[1] or row[2] or row[3] or row[4]):
                                ent = {
                                    "primaryMSISDN": str(row[1] or "").strip(),
                                    "fallbackMSISDN": str(row[2] or "").strip(),
                                    "commercialActivationDate": str(row[3] or "").strip(),
                                    "commercialExpiryDate": str(row[4] or "").strip(),
                                    "_from_sensorise_server": False
                                }
                                db_ic = str(row[0] or "").strip()
                                telematics_results[db_ic] = ent
                                num_ic = _extract_numeric_iccid(db_ic)
                                if num_ic:
                                    telematics_results[num_ic] = ent
        except Exception as batch_err:
            logger.debug(f"sensorise_sims_basic batch query notice: {batch_err}")

    return telematics_results


def _clean_msisdn(val: Any) -> str:
    """Cleans an MSISDN string, removing placeholders, trailing decimals (.0), and whitespace."""
    if val is None:
        return ""
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "nan", "nat", "-", "—", "n/a", "0", "false", "0000-00-00", "00-00-0000", "1970-01-01"):
        return ""
    if s.endswith(".0"):
        s = s[:-2]
    return s


def _extract_active_sensorise_msisdns(ent: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Extracts MSISDN1 and MSISDN2 from a Sensorise entity or cached record.
    Checks primaryMSISDN and fallbackMSISDN as well as common field variations.
    Preserves valid SIM phone numbers assigned in the Sensorise portal/LCM.
    """
    if not ent or not isinstance(ent, dict):
        return "", ""

    # Primary MSISDN (MSISDN 1)
    m1 = (
        _clean_msisdn(ent.get("primaryMSISDN"))
        or _clean_msisdn(ent.get("primary_msisdn"))
        or _clean_msisdn(ent.get("primaryMsisdn"))
        or _clean_msisdn(ent.get("msisdn1"))
        or _clean_msisdn(ent.get("msisdn"))
        or _clean_msisdn(ent.get("mobileNo"))
        or _clean_msisdn(ent.get("mobileNumber"))
        or _clean_msisdn(ent.get("primaryMobileNo"))
    )

    # Fallback MSISDN (MSISDN 2)
    m2 = (
        _clean_msisdn(ent.get("fallbackMSISDN"))
        or _clean_msisdn(ent.get("fallback_msisdn"))
        or _clean_msisdn(ent.get("fallbackMsisdn"))
        or _clean_msisdn(ent.get("secondaryMSISDN"))
        or _clean_msisdn(ent.get("secondary_msisdn"))
        or _clean_msisdn(ent.get("secondaryMsisdn"))
        or _clean_msisdn(ent.get("msisdn2"))
        or _clean_msisdn(ent.get("secondaryMobileNo"))
    )

    return m1, m2


def _clean_str(val: Any) -> str:
    """Cleans a string and returns empty string if missing, none, or placeholder."""
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("none", "null", "nan", "nat", "-", "—", "n/a", "0000-00-00", "00-00-0000", "1970-01-01"):
        return ""
    return s


def _get_stored_db_telematics(db: Session, iccid: str) -> Dict[str, Any]:
    """Retrieves stored telematics for an ICCID from database (sim_devices or sensorise_sims_basic)."""
    clean_ic = _clean_iccid_term(iccid)
    num_ic = _extract_numeric_iccid(clean_ic)
    res = {"msisdn1": "", "msisdn2": "", "act_date": None, "expiry_date": None}
    if not clean_ic:
        return res
    try:
        # 1. Check sim_devices
        row = db.execute(text("""
            SELECT msisdn1, msisdn2, act_date, expiry_date
            FROM sim_devices
            WHERE deleted_at IS NULL AND (iccid = :ic OR iccid = :ic_f OR iccid = :num_ic)
            LIMIT 1
        """), {"ic": clean_ic, "ic_f": clean_ic + "F", "num_ic": num_ic}).first()
        if row:
            if row[0]: res["msisdn1"] = _clean_str(row[0])
            if row[1]: res["msisdn2"] = _clean_str(row[1])
            if row[2]: res["act_date"] = row[2]
            if row[3]: res["expiry_date"] = row[3]

        # 2. Fallback to sensorise_sims_basic for any remaining missing field
        if not res["msisdn1"] or not res["msisdn2"] or not res["act_date"] or not res["expiry_date"]:
            b_row = db.execute(text("""
                SELECT msisdn1, msisdn2, activation_date, expiry_date
                FROM sensorise_sims_basic
                WHERE iccid = :ic OR iccid = :ic_f OR iccid = :num_ic
                LIMIT 1
            """), {"ic": clean_ic, "ic_f": clean_ic + "F", "num_ic": num_ic}).first()
            if b_row:
                if not res["msisdn1"] and b_row[0]: res["msisdn1"] = _clean_str(b_row[0])
                if not res["msisdn2"] and b_row[1]: res["msisdn2"] = _clean_str(b_row[1])
                if not res["act_date"] and b_row[2]: res["act_date"] = _parse_sensorise_date(b_row[2])
                if not res["expiry_date"] and b_row[3]: res["expiry_date"] = _parse_sensorise_date(b_row[3])
    except Exception:
        pass
    return res


def sync_devices_with_sensorise(db: Session, devices: List[Any]) -> List[Any]:
    """
    Given a list of Device ORM models:
    1. Extracts their ICCID values ('ICCID / CCID Dispatched').
    2. Queries Sensorise server (checkSIMBulk/v2) for live telematics:
       - primaryMSISDN -> MSISDN1
       - fallbackMSISDN -> MSISDN2
       - commercialActivationDate -> Act Date
       - commercialExpiryDate -> Expiry Date
    3. Replaces these values on the device models for the website response.
    4. Updates and persists them in the database (`sim_devices` & customer tables).
    5. Leaves all other selected columns intact.
    """
    if not devices:
        return devices
    if not sensorise_client:
        for dev in devices:
            if not hasattr(dev, "source") or not dev.source:
                dev.source = "website_database"
                dev.data_source = "website_database"
        return devices

    # 1. Collect ICCIDs
    raw_iccids = []
    iccid_to_devices: Dict[str, List[Any]] = {}

    for d in devices:
        raw_ic = getattr(d, "iccid", None)
        if not raw_ic:
            continue
        clean_ic = _clean_iccid_term(raw_ic)
        num_ic = _extract_numeric_iccid(clean_ic)
        if not num_ic or len(num_ic) < 6:
            continue

        raw_iccids.append(clean_ic)
        iccid_to_devices.setdefault(clean_ic, []).append(d)
        if num_ic != clean_ic:
            iccid_to_devices.setdefault(num_ic, []).append(d)

    if not raw_iccids:
        for dev in devices:
            if not hasattr(dev, "source") or not dev.source:
                dev.source = "website_database"
                dev.data_source = "website_database"
        return devices

    # 2. Fetch from Sensorise server
    telematics_map = fetch_sensorise_telematics_for_iccids(raw_iccids)
    if not telematics_map:
        for dev in devices:
            if not hasattr(dev, "source") or not dev.source:
                dev.source = "website_database"
                dev.data_source = "website_database"
        return devices

    # 3. Replace values on models and update database
    updated_count = 0
    updated_device_ids = set()
    sim_updates = []
    cust_updates: Dict[str, List[Dict[str, Any]]] = {}

    for iccid_key, dev_list in iccid_to_devices.items():
        ent = telematics_map.get(iccid_key)
        is_from_server = bool(ent and ent.get("_from_sensorise_server"))

        web_m1, web_m2 = _extract_active_sensorise_msisdns(ent)
        raw_ad = (ent.get("commercialActivationDate") or ent.get("activationDate") or ent.get("activation_date")) if ent else None
        raw_ed = (ent.get("commercialExpiryDate") or ent.get("expiryDate") or ent.get("expiry_date")) if ent else None

        web_ad = _parse_sensorise_date(raw_ad)
        web_ed = _parse_sensorise_date(raw_ed)

        has_server_telematics = bool(is_from_server and (web_m1 or web_m2 or web_ad or web_ed))

        db_stored = None
        for dev in dev_list:
            if dev.id in updated_device_ids:
                continue
            updated_device_ids.add(dev.id)

            # Check database stored values if website didn't provide one
            dev_m1 = _clean_str(getattr(dev, "msisdn1", None))
            dev_m2 = _clean_str(getattr(dev, "msisdn2", None))
            dev_ad = getattr(dev, "act_date", None)
            dev_ed = getattr(dev, "expiry_date", None)

            if not dev_m1 or not dev_m2 or not dev_ad or not dev_ed:
                if db_stored is None:
                    db_stored = _get_stored_db_telematics(db, iccid_key)
                if not dev_m1 and db_stored.get("msisdn1"):
                    dev_m1 = db_stored["msisdn1"]
                if not dev_m2 and db_stored.get("msisdn2"):
                    dev_m2 = db_stored["msisdn2"]
                if not dev_ad and db_stored.get("act_date"):
                    dev_ad = db_stored["act_date"]
                if not dev_ed and db_stored.get("expiry_date"):
                    dev_ed = db_stored["expiry_date"]

            # If fetched from Sensorise, or if found on Sensorise, or if website database & sensorise are same -> Sensorise
            if has_server_telematics or ent:
                dev.source = "sensorise"
                dev.data_source = "sensorise"
            else:
                dev.source = "website_database"
                dev.data_source = "website_database"

            diff = {}
            changed = False

            # Rule: If empty replace them; if same no need to replace; if different show difference and upload
            # 1. MSISDN 1
            final_m1 = dev_m1 or None
            if web_m1:
                if not dev_m1:
                    final_m1 = web_m1
                    changed = True
                elif dev_m1 == web_m1:
                    final_m1 = dev_m1
                else:
                    diff["msisdn1"] = {"field": "MSISDN 1", "old": dev_m1, "new": web_m1}
                    final_m1 = web_m1
                    changed = True

            # 2. MSISDN 2
            final_m2 = dev_m2 or None
            if web_m2:
                if not dev_m2:
                    final_m2 = web_m2
                    changed = True
                elif dev_m2 == web_m2:
                    final_m2 = dev_m2
                else:
                    diff["msisdn2"] = {"field": "MSISDN 2", "old": dev_m2, "new": web_m2}
                    final_m2 = web_m2
                    changed = True

            # 3. Activation Date
            final_ad = dev_ad or None
            if web_ad:
                dev_ad_parsed = _parse_sensorise_date(dev_ad)
                if not dev_ad_parsed:
                    final_ad = web_ad
                    changed = True
                elif dev_ad_parsed == web_ad:
                    final_ad = dev_ad_parsed
                else:
                    diff["act_date"] = {"field": "Activation Date", "old": str(dev_ad_parsed), "new": str(web_ad)}
                    final_ad = web_ad
                    changed = True

            # 4. Expiry Date
            final_ed = dev_ed or None
            if web_ed:
                dev_ed_parsed = _parse_sensorise_date(dev_ed)
                if not dev_ed_parsed:
                    final_ed = web_ed
                    changed = True
                elif dev_ed_parsed == web_ed:
                    final_ed = dev_ed_parsed
                else:
                    diff["expiry_date"] = {"field": "Expiry Date", "old": str(dev_ed_parsed), "new": str(web_ed)}
                    final_ed = web_ed
                    changed = True

            if final_m1 != getattr(dev, "msisdn1", None):
                dev.msisdn1 = final_m1
                changed = True
            if final_m2 != getattr(dev, "msisdn2", None):
                dev.msisdn2 = final_m2
                changed = True
            if final_ad != getattr(dev, "act_date", None):
                dev.act_date = final_ad
                changed = True
            if final_ed != getattr(dev, "expiry_date", None):
                dev.expiry_date = final_ed
                changed = True

            dev.sensorise_diff = diff
            serialized_extra = None
            if diff:
                import json
                cur_extra = getattr(dev, "extra", None) or {}
                if isinstance(cur_extra, str):
                    try:
                        cur_extra = json.loads(cur_extra)
                    except Exception:
                        cur_extra = {}
                elif not isinstance(cur_extra, dict):
                    cur_extra = {}
                cur_extra["_sensorise_diff"] = diff
                cur_extra["_sensorise_diff_at"] = datetime.now().isoformat()
                dev.extra = cur_extra
                try:
                    serialized_extra = json.dumps(cur_extra)
                except Exception:
                    serialized_extra = None
                changed = True

            if changed:
                updated_count += 1
                sim_updates.append({
                    "m1": dev.msisdn1,
                    "m2": dev.msisdn2,
                    "ad": dev.act_date,
                    "ed": dev.expiry_date,
                    "ex": serialized_extra,
                    "id": dev.id
                })
                if customer_tables and getattr(dev, "customer_id", None):
                    t_name = customer_tables.find_table(db, dev.customer_id)
                    if t_name:
                        cust_updates.setdefault(t_name, []).append({
                            "m1": dev.msisdn1,
                            "m2": dev.msisdn2,
                            "ad": dev.act_date,
                            "ed": dev.expiry_date,
                            "im": dev.imei
                        })

    if sim_updates:
        try:
            db.execute(text("""
                UPDATE sim_devices
                SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed,
                    extra = COALESCE(:ex, extra)
                WHERE id = :id
            """), sim_updates)
        except Exception as sql_err:
            logger.debug(f"Direct SQL batch update notice: {sql_err}")

    for t_name, rows_to_update in cust_updates.items():
        try:
            db.execute(text(f"""
                UPDATE `{t_name}`
                SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed
                WHERE imei = :im
            """), rows_to_update)
        except Exception as cust_err:
            logger.debug(f"Customer table mirror batch notice for {t_name}: {cust_err}")

    # Commit all replaced values into the database
    if updated_count > 0:
        try:
            db.commit()
            logger.info(f"Sensorise Sync: Replaced MSISDN1, MSISDN2, Act Date, Expiry Date in database for {updated_count} devices.")
        except Exception as commit_err:
            db.rollback()
            logger.error(f"Error committing Sensorise telematics to database: {commit_err}")

    for dev in devices:
        if not hasattr(dev, "source") or not dev.source:
            dev.source = "website_database"
            dev.data_source = "website_database"

    return devices


def sync_device_dicts_with_sensorise(db: Session, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given a list of device dictionary records (e.g. from bulk_fetch, fetch_sync, or export):
    1. Extracts their ICCID values.
    2. Queries Sensorise server (checkSIMBulk/v2) by ICCID for live telematics:
       - primaryMSISDN -> MSISDN1
       - fallbackMSISDN -> MSISDN2
       - commercialActivationDate -> Act Date
       - commercialExpiryDate -> Expiry Date
    3. Replaces these values in the dictionaries for the website response.
    4. Updates and persists them in the database (`sim_devices` & customer tables).
    """
    if not records:
        return records
    if not sensorise_client:
        for r in records:
            if "source" not in r or not r["source"]:
                r["source"] = "website_database"
                r["data_source"] = "website_database"
        return records

    raw_iccids = []
    iccid_to_records: Dict[str, List[Dict[str, Any]]] = {}

    for r in records:
        raw_ic = r.get("iccid") or r.get("ccid")
        if not raw_ic:
            continue
        clean_ic = _clean_iccid_term(raw_ic)
        num_ic = _extract_numeric_iccid(clean_ic)
        if not num_ic or len(num_ic) < 6:
            continue

        raw_iccids.append(clean_ic)
        iccid_to_records.setdefault(clean_ic, []).append(r)
        if num_ic != clean_ic:
            iccid_to_records.setdefault(num_ic, []).append(r)

    if not raw_iccids:
        for r in records:
            if "source" not in r or not r["source"]:
                r["source"] = "website_database"
                r["data_source"] = "website_database"
        return records

    telematics_map = fetch_sensorise_telematics_for_iccids(raw_iccids)
    if not telematics_map:
        for r in records:
            if "source" not in r or not r["source"]:
                r["source"] = "website_database"
                r["data_source"] = "website_database"
        return records

    updated_count = 0
    updated_imeis = set()
    sim_updates_by_id = []
    sim_updates_by_imei = []
    cust_updates: Dict[str, List[Dict[str, Any]]] = {}

    for iccid_key, r_list in iccid_to_records.items():
        ent = telematics_map.get(iccid_key)
        is_from_server = bool(ent and ent.get("_from_sensorise_server"))

        web_m1, web_m2 = _extract_active_sensorise_msisdns(ent)
        raw_ad = (ent.get("commercialActivationDate") or ent.get("activationDate") or ent.get("activation_date")) if ent else None
        raw_ed = (ent.get("commercialExpiryDate") or ent.get("expiryDate") or ent.get("expiry_date")) if ent else None

        ad_date = _parse_sensorise_date(raw_ad)
        ed_date = _parse_sensorise_date(raw_ed)

        has_server_telematics = bool(is_from_server and (web_m1 or web_m2 or ad_date or ed_date))

        ad_str = ad_date.isoformat() if ad_date else ""
        ed_str = ed_date.isoformat() if ed_date else ""

        db_stored = None
        for r in r_list:
            imei = r.get("imei")
            if imei and imei in updated_imeis:
                continue
            if imei:
                updated_imeis.add(imei)

            dict_m1 = _clean_str(r.get("msisdn1"))
            dict_m2 = _clean_str(r.get("msisdn2"))
            dict_ad = _clean_str(r.get("act_date"))
            dict_ed = _clean_str(r.get("expiry_date"))

            # Fallback to database stored values if missing
            if not dict_m1 or not dict_m2 or not dict_ad or not dict_ed:
                if db_stored is None:
                    db_stored = _get_stored_db_telematics(db, iccid_key)
                if not dict_m1 and db_stored.get("msisdn1"):
                    dict_m1 = db_stored["msisdn1"]
                if not dict_m2 and db_stored.get("msisdn2"):
                    dict_m2 = db_stored["msisdn2"]
                if not dict_ad and db_stored.get("act_date"):
                    ad_val = db_stored["act_date"]
                    dict_ad = ad_val.isoformat() if hasattr(ad_val, "isoformat") else str(ad_val)
                if not dict_ed and db_stored.get("expiry_date"):
                    ed_val = db_stored["expiry_date"]
                    dict_ed = ed_val.isoformat() if hasattr(ed_val, "isoformat") else str(ed_val)

            if has_server_telematics or ent:
                r["source"] = "sensorise"
                r["data_source"] = "sensorise"
            else:
                r["source"] = "website_database"
                r["data_source"] = "website_database"

            diff = {}
            changed = False

            # Rule: If empty replace them; if same no need to replace; if different show difference and upload
            # 1. MSISDN 1
            final_m1 = dict_m1
            if web_m1:
                if not dict_m1:
                    final_m1 = web_m1
                    changed = True
                elif dict_m1 == web_m1:
                    final_m1 = dict_m1
                else:
                    diff["msisdn1"] = {"field": "MSISDN 1", "old": dict_m1, "new": web_m1}
                    final_m1 = web_m1
                    changed = True

            # 2. MSISDN 2
            final_m2 = dict_m2
            if web_m2:
                if not dict_m2:
                    final_m2 = web_m2
                    changed = True
                elif dict_m2 == web_m2:
                    final_m2 = dict_m2
                else:
                    diff["msisdn2"] = {"field": "MSISDN 2", "old": dict_m2, "new": web_m2}
                    final_m2 = web_m2
                    changed = True

            # 3. Activation Date
            final_ad_str = dict_ad
            if ad_str:
                dict_ad_parsed = _parse_sensorise_date(dict_ad)
                if not dict_ad_parsed:
                    final_ad_str = ad_str
                    changed = True
                elif dict_ad_parsed == ad_date:
                    final_ad_str = dict_ad_parsed.isoformat()
                else:
                    diff["act_date"] = {"field": "Activation Date", "old": str(dict_ad_parsed), "new": ad_str}
                    final_ad_str = ad_str
                    changed = True

            # 4. Expiry Date
            final_ed_str = dict_ed
            final_ed_date = _parse_sensorise_date(dict_ed)
            if ed_str:
                dict_ed_parsed = _parse_sensorise_date(dict_ed)
                if not dict_ed_parsed:
                    final_ed_str = ed_str
                    final_ed_date = ed_date
                    changed = True
                elif dict_ed_parsed == ed_date:
                    final_ed_str = dict_ed_parsed.isoformat()
                    final_ed_date = dict_ed_parsed
                else:
                    diff["expiry_date"] = {"field": "Expiry Date", "old": str(dict_ed_parsed), "new": ed_str}
                    final_ed_str = ed_str
                    final_ed_date = ed_date
                    changed = True

            if r.get("msisdn1") != final_m1:
                r["msisdn1"] = final_m1
                changed = True
            if r.get("msisdn2") != final_m2:
                r["msisdn2"] = final_m2
                changed = True
            if r.get("act_date") != final_ad_str:
                r["act_date"] = final_ad_str
                changed = True
            if r.get("expiry_date") != final_ed_str:
                r["expiry_date"] = final_ed_str
                changed = True

            r["sensorise_diff"] = diff
            serialized_extra = None
            if diff:
                import json
                r_extra = r.get("extra") or {}
                if isinstance(r_extra, str):
                    try:
                        r_extra = json.loads(r_extra)
                    except Exception:
                        r_extra = {}
                elif not isinstance(r_extra, dict):
                    r_extra = {}
                r_extra["_sensorise_diff"] = diff
                r_extra["_sensorise_diff_at"] = datetime.now().isoformat()
                r["extra"] = r_extra
                try:
                    serialized_extra = json.dumps(r_extra)
                except Exception:
                    serialized_extra = None
                changed = True

            if final_ed_date:
                r["days_left"] = (final_ed_date - date.today()).days
            else:
                r["days_left"] = ""
                r["expiry_status"] = ""

            if changed:
                updated_count += 1
                ad_obj_to_save = _parse_sensorise_date(final_ad_str)
                ed_obj_to_save = final_ed_date
                m1_to_save = final_m1 if final_m1 else None
                m2_to_save = final_m2 if final_m2 else None

                dev_id = r.get("id")
                if dev_id and (isinstance(dev_id, int) or (isinstance(dev_id, str) and str(dev_id).isdigit())):
                    sim_updates_by_id.append({
                        "m1": m1_to_save, "m2": m2_to_save,
                        "ad": ad_obj_to_save, "ed": ed_obj_to_save,
                        "ex": serialized_extra,
                        "id": int(dev_id)
                    })
                elif imei:
                    sim_updates_by_imei.append({
                        "m1": m1_to_save, "m2": m2_to_save,
                        "ad": ad_obj_to_save, "ed": ed_obj_to_save,
                        "ex": serialized_extra,
                        "im": imei
                    })

                cid = r.get("customer_id")
                if customer_tables and cid and imei:
                    t_name = customer_tables.find_table(db, cid)
                    if t_name:
                        cust_updates.setdefault(t_name, []).append({
                            "m1": m1_to_save, "m2": m2_to_save,
                            "ad": ad_obj_to_save, "ed": ed_obj_to_save,
                            "im": imei
                        })

    if sim_updates_by_id:
        try:
            db.execute(text("""
                UPDATE sim_devices
                SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed,
                    extra = COALESCE(:ex, extra)
                WHERE id = :id
            """), sim_updates_by_id)
        except Exception as sql_err:
            logger.debug(f"Direct SQL batch update by id notice: {sql_err}")

    if sim_updates_by_imei:
        try:
            db.execute(text("""
                UPDATE sim_devices
                SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed,
                    extra = COALESCE(:ex, extra)
                WHERE imei = :im
            """), sim_updates_by_imei)
        except Exception as sql_err:
            logger.debug(f"Direct SQL batch update by imei notice: {sql_err}")

    for t_name, rows_to_update in cust_updates.items():
        try:
            db.execute(text(f"""
                UPDATE `{t_name}`
                SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed
                WHERE imei = :im
            """), rows_to_update)
        except Exception as cust_err:
            logger.debug(f"Customer table mirror batch notice for {t_name}: {cust_err}")

    if updated_count > 0:
        try:
            db.commit()
            logger.info(f"Sensorise Sync: Replaced MSISDN1, MSISDN2, Act Date, Expiry Date in database for {updated_count} dict records.")
        except Exception as commit_err:
            db.rollback()
            logger.error(f"Error committing Sensorise telematics for dicts: {commit_err}")

    for r in records:
        if "source" not in r or not r["source"]:
            r["source"] = "website_database"
            r["data_source"] = "website_database"

    return records

