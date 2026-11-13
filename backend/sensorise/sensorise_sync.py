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
from typing import List, Dict, Any, Optional, Set
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
            ent = sensorise_client.raw_telematics_cache[num_iccid]
            telematics_results[raw_clean] = ent
            telematics_results[num_iccid] = ent

    # Check database sensorise_sims_basic for any remaining ICCIDs
    missing_for_db = [r for r in raw_iccids if _clean_iccid_term(r) not in telematics_results and _extract_numeric_iccid(r) not in telematics_results]
    if missing_for_db:
        try:
            from sqlalchemy import text
            from database import engine
            with engine.connect() as conn:
                for raw in missing_for_db:
                    clean_raw = _clean_iccid_term(raw)
                    row = conn.execute(
                        text("SELECT msisdn1, msisdn2, activation_date, expiry_date FROM sensorise_sims_basic WHERE iccid = :ic OR iccid = :ic_f LIMIT 1"),
                        {"ic": clean_raw, "ic_f": clean_raw + "F"}
                    ).first()
                    if row and (row[0] or row[2]):
                        ent = {
                            "primaryMSISDN": str(row[0] or "").strip(),
                            "fallbackMSISDN": str(row[1] or "").strip(),
                            "commercialActivationDate": str(row[2] or "").strip(),
                            "commercialExpiryDate": str(row[3] or "").strip()
                        }
                        telematics_results[clean_raw] = ent
                        num_ic = _extract_numeric_iccid(clean_raw)
                        if num_ic:
                            telematics_results[num_ic] = ent
        except Exception:
            pass

    return telematics_results


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
    if not devices or not sensorise_client:
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
        return devices

    # 2. Fetch from Sensorise server
    telematics_map = fetch_sensorise_telematics_for_iccids(raw_iccids)
    if not telematics_map:
        return devices

    # 3. Replace values on models and update database
    updated_count = 0
    updated_device_ids = set()

    for iccid_key, dev_list in iccid_to_devices.items():
        ent = telematics_map.get(iccid_key)
        if not ent:
            continue

        m1 = ent.get("primaryMSISDN") or ent.get("msisdn1") or ""
        m2 = ent.get("fallbackMSISDN") or ent.get("msisdn2") or ""
        raw_ad = ent.get("commercialActivationDate") or ent.get("activationDate") or ent.get("activation_date")
        raw_ed = ent.get("commercialExpiryDate") or ent.get("expiryDate") or ent.get("expiry_date")

        ad = _parse_sensorise_date(raw_ad)
        ed = _parse_sensorise_date(raw_ed)

        for dev in dev_list:
            if dev.id in updated_device_ids:
                continue
            updated_device_ids.add(dev.id)

            changed = False
            # Replace MSISDN1
            if m1 and str(m1).strip():
                clean_m1 = str(m1).strip()
                if getattr(dev, "msisdn1", None) != clean_m1:
                    dev.msisdn1 = clean_m1
                    changed = True

            # Replace MSISDN2
            if m2 and str(m2).strip():
                clean_m2 = str(m2).strip()
                if getattr(dev, "msisdn2", None) != clean_m2:
                    dev.msisdn2 = clean_m2
                    changed = True

            # Replace Act Date
            if ad and getattr(dev, "act_date", None) != ad:
                dev.act_date = ad
                changed = True

            # Replace Expiry Date
            if ed and getattr(dev, "expiry_date", None) != ed:
                dev.expiry_date = ed
                changed = True

            if changed:
                updated_count += 1
                # Execute direct SQL update on sim_devices
                try:
                    db.execute(text("""
                        UPDATE sim_devices
                        SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed
                        WHERE id = :id
                    """), {
                        "m1": dev.msisdn1,
                        "m2": dev.msisdn2,
                        "ad": dev.act_date,
                        "ed": dev.expiry_date,
                        "id": dev.id
                    })
                except Exception as sql_err:
                    logger.debug(f"Direct SQL update notice for device {dev.id}: {sql_err}")

                # Mirror update to customer-specific table if present
                if customer_tables and getattr(dev, "customer_id", None):
                    try:
                        t_name = customer_tables.find_table(db, dev.customer_id)
                        if t_name:
                            db.execute(text(f"""
                                UPDATE `{t_name}`
                                SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed
                                WHERE imei = :im
                            """), {
                                "m1": dev.msisdn1,
                                "m2": dev.msisdn2,
                                "ad": dev.act_date,
                                "ed": dev.expiry_date,
                                "im": dev.imei
                            })
                    except Exception as cust_err:
                        logger.debug(f"Customer table mirror notice for device {dev.imei}: {cust_err}")

    # Commit all replaced values into the database
    if updated_count > 0:
        try:
            db.commit()
            logger.info(f"Sensorise Sync: Replaced MSISDN1, MSISDN2, Act Date, Expiry Date in database for {updated_count} devices.")
        except Exception as commit_err:
            db.rollback()
            logger.error(f"Error committing Sensorise telematics to database: {commit_err}")

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
    if not records or not sensorise_client:
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
        return records

    telematics_map = fetch_sensorise_telematics_for_iccids(raw_iccids)
    if not telematics_map:
        return records

    updated_count = 0
    updated_imeis = set()

    for iccid_key, r_list in iccid_to_records.items():
        ent = telematics_map.get(iccid_key)
        if not ent:
            continue

        m1 = ent.get("primaryMSISDN") or ent.get("msisdn1") or ""
        m2 = ent.get("fallbackMSISDN") or ent.get("msisdn2") or ""
        raw_ad = ent.get("commercialActivationDate") or ent.get("activationDate") or ent.get("activation_date")
        raw_ed = ent.get("commercialExpiryDate") or ent.get("expiryDate") or ent.get("expiry_date")

        ad_date = _parse_sensorise_date(raw_ad)
        ed_date = _parse_sensorise_date(raw_ed)

        ad_str = ad_date.isoformat() if ad_date else (str(raw_ad) if raw_ad else "")
        ed_str = ed_date.isoformat() if ed_date else (str(raw_ed) if raw_ed else "")

        for r in r_list:
            imei = r.get("imei")
            if imei and imei in updated_imeis:
                continue
            if imei:
                updated_imeis.add(imei)

            changed = False
            if m1 and str(m1).strip():
                clean_m1 = str(m1).strip()
                if r.get("msisdn1") != clean_m1:
                    r["msisdn1"] = clean_m1
                    changed = True

            if m2 and str(m2).strip():
                clean_m2 = str(m2).strip()
                if r.get("msisdn2") != clean_m2:
                    r["msisdn2"] = clean_m2
                    changed = True

            if ad_str and r.get("act_date") != ad_str:
                r["act_date"] = ad_str
                changed = True

            if ed_str and r.get("expiry_date") != ed_str:
                r["expiry_date"] = ed_str
                changed = True
                if ed_date:
                    r["days_left"] = (ed_date - date.today()).days

            if changed:
                updated_count += 1
                # Update in database
                try:
                    dev_id = r.get("id")
                    if dev_id:
                        db.execute(text("""
                            UPDATE sim_devices
                            SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed
                            WHERE id = :id
                        """), {
                            "m1": r.get("msisdn1"),
                            "m2": r.get("msisdn2"),
                            "ad": ad_date,
                            "ed": ed_date,
                            "id": dev_id
                        })
                    elif imei:
                        db.execute(text("""
                            UPDATE sim_devices
                            SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed
                            WHERE imei = :im
                        """), {
                            "m1": r.get("msisdn1"),
                            "m2": r.get("msisdn2"),
                            "ad": ad_date,
                            "ed": ed_date,
                            "im": imei
                        })
                except Exception as db_err:
                    logger.debug(f"Direct SQL update notice for dict device {imei}: {db_err}")

                # Update customer dynamic table if customer_id present
                cid = r.get("customer_id")
                if customer_tables and cid and imei:
                    try:
                        t_name = customer_tables.find_table(db, cid)
                        if t_name:
                            db.execute(text(f"""
                                UPDATE `{t_name}`
                                SET msisdn1 = :m1, msisdn2 = :m2, act_date = :ad, expiry_date = :ed
                                WHERE imei = :im
                            """), {
                                "m1": r.get("msisdn1"),
                                "m2": r.get("msisdn2"),
                                "ad": ad_date,
                                "ed": ed_date,
                                "im": imei
                            })
                    except Exception as cust_err:
                        logger.debug(f"Customer table mirror notice for dict device {imei}: {cust_err}")

    if updated_count > 0:
        try:
            db.commit()
            logger.info(f"Sensorise Sync: Replaced MSISDN1, MSISDN2, Act Date, Expiry Date in database for {updated_count} dict records.")
        except Exception as commit_err:
            db.rollback()
            logger.error(f"Error committing Sensorise telematics for dicts: {commit_err}")

    return records

