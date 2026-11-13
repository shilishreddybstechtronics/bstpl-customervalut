"""
MySQL Database Manager for Sensorise BSTPL
Handles database connection, schema initialization, and record persistence.
"""

import datetime
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, BASIC_FILE_PATH
except ImportError:
    try:
        from backend.sensorise.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, BASIC_FILE_PATH
    except ImportError:
        from sensorise.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, BASIC_FILE_PATH

import re
from typing import Dict, Any, List, Optional
import pymysql
from pymysql.cursors import DictCursor

logger = logging.getLogger("uvicorn.error")

MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9, "sept": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

def clean_field_val(val: Any) -> str:
    """Returns a cleaned non-empty string or blank string."""
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("none", "null", "nan", "nat", "-", "—", "n/a", "0000-00-00", "00-00-0000", "1970-01-01"):
        return ""
    return s


def format_to_dmy(val: Any) -> str:
    """
    Arranges any date value strictly into DAY-MONTH-YEAR (DD-MM-YYYY) format.
    Strict month numbering: Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6,
    Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12.
    Preserves existing DD-MM-YYYY strings untouched to prevent double conversion or month shifts.
    """
    if val is None:
        return ""
    if isinstance(val, (datetime.date, datetime.datetime)):
        if isinstance(val, datetime.datetime) and val.year <= 1970:
            return ""
        return val.strftime("%d-%m-%Y")

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "nat", "0", "false", "-", "n/a", "0000-00-00", "00-00-0000", "1970-01-01"):
        return ""

    # 1. If already strict DD-MM-YYYY, preserve directly without re-parsing
    m_strict = re.match(r"^(\d{2})-(\d{2})-(\d{4})$", s)
    if m_strict:
        d = int(m_strict.group(1))
        m = int(m_strict.group(2))
        y = int(m_strict.group(3))
        if 1 <= d <= 31 and 1 <= m <= 12 and 1990 <= y <= 2099:
            return s

    # 2. Check numeric strings: epoch timestamps or 8-digit compact dates
    try:
        clean_num = s.replace(".", "", 1)
        if clean_num.isdigit():
            # 8-digit compact dates: YYYYMMDD or DDMMYYYY
            if len(clean_num) == 8:
                y8 = int(clean_num[:4])
                m8 = int(clean_num[4:6])
                d8 = int(clean_num[6:])
                if 1990 <= y8 <= 2099 and 1 <= m8 <= 12 and 1 <= d8 <= 31:
                    return f"{d8:02d}-{m8:02d}-{y8:04d}"
                d8_alt = int(clean_num[:2])
                m8_alt = int(clean_num[2:4])
                y8_alt = int(clean_num[4:])
                if 1990 <= y8_alt <= 2099 and 1 <= m8_alt <= 12 and 1 <= d8_alt <= 31:
                    return f"{d8_alt:02d}-{m8_alt:02d}-{y8_alt:04d}"

            # Epoch timestamp: milliseconds (>1e11) or seconds
            ts = float(s)
            if ts > 1e11:
                ts /= 1000.0
            if 1e8 < ts < 3e10:
                dt = datetime.datetime.fromtimestamp(ts)
                if dt.year > 1970:
                    return dt.strftime("%d-%m-%Y")
    except Exception:
        pass

    # Extract clean date segment before time/T
    date_part = s.split("T")[0].split(" ")[0].strip()

    # 3. Month name parsing: DD-Mon-YYYY (e.g. 21-Oct-2025, 22-Sep-2024)
    m_mon1 = re.match(r"^(\d{1,2})[-/. ]([A-Za-z]{3,9})[-/. ](\d{4})", date_part)
    if m_mon1:
        d = int(m_mon1.group(1))
        m_str = m_mon1.group(2).lower()
        y = int(m_mon1.group(3))
        if m_str in MONTH_NAMES and 1 <= d <= 31 and 1990 <= y <= 2099:
            m = MONTH_NAMES[m_str]
            return f"{d:02d}-{m:02d}-{y:04d}"

    # 4. Month name parsing: YYYY-Mon-DD (e.g. 2025-Oct-21)
    m_mon2 = re.match(r"^(\d{4})[-/. ]([A-Za-z]{3,9})[-/. ](\d{1,2})", date_part)
    if m_mon2:
        y = int(m_mon2.group(1))
        m_str = m_mon2.group(2).lower()
        d = int(m_mon2.group(3))
        if m_str in MONTH_NAMES and 1 <= d <= 31 and 1990 <= y <= 2099:
            m = MONTH_NAMES[m_str]
            return f"{d:02d}-{m:02d}-{y:04d}"

    # 5. Month name parsing: Mon DD, YYYY (e.g. October 21, 2025)
    m_mon3 = re.match(r"^([A-Za-z]{3,9})[-/. ](\d{1,2})[-/. ,]+(\d{4})", date_part)
    if m_mon3:
        m_str = m_mon3.group(1).lower()
        d = int(m_mon3.group(2))
        y = int(m_mon3.group(3))
        if m_str in MONTH_NAMES and 1 <= d <= 31 and 1990 <= y <= 2099:
            m = MONTH_NAMES[m_str]
            return f"{d:02d}-{m:02d}-{y:04d}"

    # 6. Pattern: YYYY-MM-DD or YYYY/MM/DD
    m1 = re.match(r"^(\d{4})[-/. ](\d{1,2})[-/. ](\d{1,2})", date_part)
    if m1:
        year, month, day = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31 and 1990 <= year <= 2099:
            return f"{day:02d}-{month:02d}-{year:04d}"

    # 7. Pattern: DD-MM-YYYY or MM-DD-YYYY
    m2 = re.match(r"^(\d{1,2})[-/. ](\d{1,2})[-/. ](\d{4})", date_part)
    if m2:
        p1, p2, year = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        day = p1
        month = p2
        if p1 <= 12 and 12 < p2 <= 31:
            month = p1
            day = p2
        if 1 <= month <= 12 and 1 <= day <= 31 and 1990 <= year <= 2099:
            return f"{day:02d}-{month:02d}-{year:04d}"

    # Try pandas parser fallback
    try:
        import pandas as pd
        parsed = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.notnull(parsed) and parsed.year > 1970:
            return parsed.strftime("%d-%m-%Y")
    except Exception:
        pass

    return s

def sanitize_table_name(filename: str) -> str:
    """
    Derives a clean MySQL table name from the uploaded file name.
    Example: 'Sensorise_SIMs_basic.xlsx' -> 'sensorise_sims_basic'
    """
    if not filename:
        return "uploaded_file_data"
    base = os.path.splitext(filename)[0] if "." in filename else filename
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', base).strip('_').lower()
    if not clean:
        return "uploaded_file_data"
    if clean[0].isdigit():
        clean = f"t_{clean}"
    return clean

def sanitize_column_name(col_name: str, used_names: set) -> str:
    """
    Derives a valid MySQL column name from a table header.
    Example: 'Device SR No' -> 'device_sr_no'
    """
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', str(col_name).strip()).strip('_').lower()
    if not clean:
        clean = "col"
    if clean[0].isdigit():
        clean = f"col_{clean}"
    base = clean
    counter = 1
    while clean in used_names:
        clean = f"{base}_{counter}"
        counter += 1
    used_names.add(clean)
    return clean

def is_db_configured() -> bool:
    """Check if MySQL connection details are provided."""
    return bool(DB_HOST and DB_USER and DB_NAME)

def get_connection() -> Optional[pymysql.Connection]:
    """Establishes a MySQL/TiDB Cloud connection using PyMySQL."""
    if not is_db_configured():
        return None
    
    conn_kwargs = {
        "host": DB_HOST,
        "port": int(DB_PORT or 4000),
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME,
        "cursorclass": DictCursor,
        "autocommit": True,
        "connect_timeout": 10
    }
    if "tidbcloud.com" in str(DB_HOST).lower():
        conn_kwargs["ssl"] = {"ca": None}

    return pymysql.connect(**conn_kwargs)

def test_db_status() -> Dict[str, Any]:
    """Tests the MySQL database connection status."""
    if not is_db_configured():
        return {
            "configured": False,
            "connected": False,
            "message": "MySQL details are empty. Configure DB_HOST, DB_USER, DB_NAME in config.py or .env."
        }
    
    try:
        conn = get_connection()
        if not conn:
            return {
                "configured": True,
                "connected": False,
                "message": "Unable to establish MySQL connection with provided credentials."
            }
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version;")
            version_info = cursor.fetchone()
        conn.close()
        
        return {
            "configured": True,
            "connected": True,
            "version": version_info.get("version") if version_info else "Unknown",
            "message": f"Successfully connected to MySQL database '{DB_NAME}' on {DB_HOST}:{DB_PORT}."
        }
    except Exception as e:
        logger.error(f"MySQL connection error: {e}")
        return {
            "configured": True,
            "connected": False,
            "error": str(e),
            "message": f"Failed to connect to MySQL: {str(e)}"
        }

def init_db() -> Dict[str, Any]:
    """Initializes the required database tables if MySQL is configured."""
    if not is_db_configured():
        return {"status": "skipped", "message": "Database not configured yet."}
    
    try:
        conn = get_connection()
        if not conn:
            return {"status": "failed", "message": "Could not connect to MySQL."}
        
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_uploads (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    row_count INT NOT NULL DEFAULT 0,
                    col_count INT NOT NULL DEFAULT 0,
                    headers_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensorise_token_store (
                    id INT PRIMARY KEY,
                    auth_token TEXT NOT NULL,
                    token_expiry VARCHAR(50),
                    access_key TEXT,
                    calls_remaining INT DEFAULT 100,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            conn.commit()
        
        conn.close()
        return {"status": "success", "message": "Database initialized."}
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return {"status": "error", "error": str(e)}

def save_token_to_db(token: str, expiry: str = "", access_key: str = "", calls_remaining: int = 100) -> bool:
    """Persists active Sensorise API token into TiDB Cloud for seamless cross-deployment lifetime."""
    if not token or not is_db_configured():
        return False
    try:
        conn = get_connection()
        if not conn:
            return False
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sensorise_token_store (id, auth_token, token_expiry, access_key, calls_remaining)
                VALUES (1, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    auth_token = VALUES(auth_token),
                    token_expiry = VALUES(token_expiry),
                    access_key = VALUES(access_key),
                    calls_remaining = VALUES(calls_remaining),
                    updated_at = CURRENT_TIMESTAMP;
            """, (token, expiry, access_key, calls_remaining))
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"Could not persist Sensorise token to TiDB: {e}")
        return False

def get_token_from_db() -> Dict[str, Any]:
    """Retrieves active Sensorise API token from TiDB Cloud."""
    if not is_db_configured():
        return {}
    try:
        conn = get_connection()
        if not conn:
            return {}
        with conn.cursor() as cursor:
            cursor.execute("SELECT auth_token, token_expiry, access_key, calls_remaining FROM sensorise_token_store WHERE id = 1 LIMIT 1;")
            row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "auth_token": row.get("auth_token") or "",
                "token_expiry": row.get("token_expiry") or "",
                "access_key": row.get("access_key") or "",
                "calls_remaining": row.get("calls_remaining") or 100
            }
    except Exception as e:
        logger.debug(f"Could not read Sensorise token from TiDB: {e}")
    return {}

def create_table_from_file_data(filename: str, headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    """
    Creates a dedicated MySQL table named after the file.
    Column names in the table match the headers.
    Rows are inserted as individual database entries.
    """
    if not is_db_configured():
        return {
            "success": False,
            "saved_to_db": False,
            "message": "Database connection details are empty in .env. Showing data on website only."
        }

    if not headers or not rows:
        return {
            "success": False,
            "saved_to_db": False,
            "message": "Headers and rows cannot be empty."
        }

    table_name = sanitize_table_name(filename)
    used_cols = set()
    col_names = [sanitize_column_name(h, used_cols) for h in headers]

    try:
        conn = get_connection()
        if not conn:
            return {"success": False, "saved_to_db": False, "message": "Could not connect to MySQL."}

        with conn.cursor() as cursor:
            col_defs = [f"`{col}` VARCHAR(255) NULL" for col in col_names]
            index_defs = []
            for col in col_names:
                if col in ("iccid", "imei", "device_sr_no"):
                    index_defs.append(f"INDEX `idx_{table_name[:20]}_{col}` (`{col}`)")

            all_defs = ["`id` INT AUTO_INCREMENT PRIMARY KEY"] + col_defs + ["`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP"] + index_defs
            create_sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(all_defs)}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"
            cursor.execute(create_sql)
            cursor.execute(f"TRUNCATE TABLE `{table_name}`;")

            cols_clause = ", ".join([f"`{c}`" for c in col_names])
            placeholders = ", ".join(["%s"] * len(col_names))
            insert_sql = f"INSERT INTO `{table_name}` ({cols_clause}) VALUES ({placeholders});"

            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch_rows = []
                for r in rows[i:i + batch_size]:
                    row_tuple = []
                    for c_idx in range(len(col_names)):
                        val = r[c_idx] if c_idx < len(r) else ""
                        col_id = col_names[c_idx]
                        if "date" in col_id or "activation" in col_id or "expiry" in col_id:
                            val = format_to_dmy(val)
                        row_tuple.append(str(val) if val is not None else "")
                    batch_rows.append(tuple(row_tuple))
                cursor.executemany(insert_sql, batch_rows)

            cursor.execute(
                "INSERT INTO file_uploads (filename, row_count, col_count, headers_json) VALUES (%s, %s, %s, %s);",
                (filename, len(rows), len(headers), json.dumps(headers))
            )

        conn.close()
        return {
            "success": True,
            "saved_to_db": True,
            "table_name": table_name,
            "column_names": col_names,
            "headers": headers,
            "inserted_rows": len(rows),
            "message": f"Successfully created MySQL table '{table_name}' with {len(col_names)} columns and {len(rows)} entries."
        }
    except Exception as e:
        logger.error(f"Error creating table from file data: {e}")
        return {
            "success": False,
            "saved_to_db": False,
            "error": str(e),
            "message": f"MySQL table creation error: {str(e)}"
        }

def save_file_to_db(filename: str, headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    """
    Saves parsed file data into MySQL.
    """
    return create_table_from_file_data(filename, headers, rows)

def ensure_sensorise_basic_table() -> Dict[str, Any]:
    """
    Ensures the MySQL/TiDB Cloud table 'sensorise_sims_basic' exists and is populated.
    """
    if not is_db_configured():
        return {"success": False, "message": "Database not configured."}

    table_name = "sensorise_sims_basic"
    headers = ["Device SR No", "IMEI", "ICCID", "MSISDN1", "MSISDN2", "Activation Date", "Expiry Date"]

    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
                exists = cursor.fetchone()
                if exists:
                    cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{table_name}`;")
                    row_count = cursor.fetchone().get("cnt", 0)
                    if row_count > 0:
                        conn.close()
                        logger.info(f"Database table '{table_name}' already exists with {row_count} entries. Loading directly from database.")
                        return {"success": True, "table_name": table_name, "row_count": row_count, "source": "mysql"}
        except Exception as chk_err:
            logger.warning(f"Error checking existing table '{table_name}': {chk_err}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    try:
        from sensorise import sensorise_client
        cached_data = sensorise_client.raw_telematics_cache
        rows = []
        for iccid, d in cached_data.items():
            if isinstance(d, dict):
                m1 = d.get("primaryMSISDN") or ""
                m2 = d.get("fallbackMSISDN") or ""
                act = format_to_dmy(d.get("commercialActivationDate") or "")
                exp = format_to_dmy(d.get("commercialExpiryDate") or "")
                rows.append(["", "", iccid, m1, m2, act, exp])

        res = create_table_from_file_data(table_name, headers, rows)
        logger.info(f"Initialized table '{table_name}' in database: {len(rows)} entries.")
        return res
    except Exception as e:
        logger.error(f"Error ensuring sensorise_sims_basic table: {e}")
        return {"success": False, "error": str(e)}

def fetch_and_update_basic_sims_telematics() -> Dict[str, Any]:
    """
    Searches Sensorise Company Server by ICCID value for SIMs.
    Selects msisdn1, msisdn2, activation_date, and expiry_date,
    updates MySQL table sensorise_sims_basic, and returns the updated rows.
    """
    from sensorise import sensorise_client

    if not is_db_configured():
        return {"success": False, "message": "Database is not configured in .env."}

    if not (sensorise_client.api_key or sensorise_client.auth_token or (sensorise_client.client_id and sensorise_client.client_secret)):
        return {
            "success": False,
            "message": "Sensorise Company Server credentials are not configured. Please enter your API Key or Bearer Token in Server Settings first."
        }

    try:
        conn = get_connection()
        if not conn:
            return {"success": False, "message": "Could not connect to MySQL."}

        with conn.cursor() as cursor:
            cursor.execute("SELECT id, device_sr_no, imei, iccid FROM sensorise_sims_basic ORDER BY id ASC LIMIT 80;")
            sims = cursor.fetchall()

            if not sims:
                conn.close()
                return {"success": False, "message": "No SIM records found in sensorise_sims_basic."}

            all_iccids = [str(s.get("iccid") or "").strip() for s in sims if str(s.get("iccid") or "").strip()]
            if all_iccids:
                try:
                    sensorise_client.check_sim_bulk_v2(all_iccids)
                except Exception as b_err:
                    logger.warning(f"Bulk SIM query in fetch_and_update_basic_sims_telematics: {b_err}")

            update_sql = """
                UPDATE sensorise_sims_basic
                SET msisdn1 = COALESCE(NULLIF(%s, ''), msisdn1),
                    msisdn2 = COALESCE(NULLIF(%s, ''), msisdn2),
                    activation_date = COALESCE(NULLIF(%s, ''), activation_date),
                    expiry_date = COALESCE(NULLIF(%s, ''), expiry_date)
                WHERE id = %s AND iccid = %s;
            """

            update_params = []
            for sim in sims:
                sim_id = sim["id"]
                iccid = sim["iccid"]
                telematics = sensorise_client.fetch_telematics_by_iccid(iccid)
                if telematics:
                    m1 = str(telematics.get("msisdn1", "") or "").strip()
                    m2 = str(telematics.get("msisdn2", "") or "").strip()
                    act_date_dmy = format_to_dmy(telematics.get("activation_date", ""))
                    exp_date_dmy = format_to_dmy(telematics.get("expiry_date", ""))
                    if m1 or m2 or act_date_dmy or exp_date_dmy:
                        update_params.append((
                            m1,
                            m2,
                            act_date_dmy,
                            exp_date_dmy,
                            sim_id,
                            iccid
                        ))

            if update_params:
                cursor.executemany(update_sql, update_params)
                conn.commit()

        conn.close()

        try:
            import pandas as pd
            excel_path = BASIC_FILE_PATH
            if not os.path.exists(excel_path):
                excel_path = os.path.join(os.path.dirname(__file__), "Sensorise_SIMs_basic.xlsx")
            if os.path.exists(excel_path) and update_params:
                df = pd.read_excel(excel_path, dtype=str).fillna("")
                telematics_map = {p[5]: {"m1": p[0], "m2": p[1], "act": p[2], "exp": p[3]} for p in update_params}
                for i, row in df.iterrows():
                    ic = str(row.get("ICCID", "")).strip()
                    if ic in telematics_map:
                        t = telematics_map[ic]
                        if t["m1"]: df.at[i, "MSISDN1"] = t["m1"]
                        if t["m2"]: df.at[i, "MSISDN2"] = t["m2"]
                        if t["act"]: df.at[i, "Activation Date"] = format_to_dmy(t["act"])
                        if t["exp"]: df.at[i, "Expiry Date"] = format_to_dmy(t["exp"])
                df.iloc[:80].to_excel(excel_path, index=False)
        except Exception as ex_err:
            logger.warning(f"Could not sync Excel file with fetched telematics: {ex_err}")

        regen_res = {}
        try:
            regen_res = sensorise_client.generate_api_token()
            logger.info("Automatically regenerated fresh SenseLCM API token after completing basic SIM telematics fetch.")
        except Exception as t_err:
            logger.warning(f"Auto token regeneration notice: {t_err}")

        updated_res = get_sensorise_basic_records(limit=80, fetch_all=True)
        resp_msg = (
            f"Successfully matched ICCIDs and fetched MSISDN1, MSISDN2, Act Date, and Exp Date from Sensorise server for {len(update_params)} SIMs!"
            if update_params else
            f"Sensorise server reached. Existing {len(sims)} SIM records preserved."
        )
        return {
            "success": True,
            "updated_count": len(update_params),
            "headers": updated_res.get("headers", []),
            "rows": updated_res.get("rows", []),
            "total": updated_res.get("total", len(sims)),
            "token_regenerated": bool(regen_res.get("success")),
            "apiToken": regen_res.get("apiToken") or sensorise_client.auth_token,
            "tokenExpiry": regen_res.get("tokenExpiry") or sensorise_client.get_token_expiry(),
            "message": resp_msg
        }
    except Exception as e:
        logger.error(f"Error fetching telematics from Sensorise server: {e}")
        return {"success": False, "error": str(e), "message": f"Server query error: {str(e)}"}

def search_and_update_sim_by_iccid(iccid: str, mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Searches for telematics by ICCID:
    1. First queries Sensorise server for live telematics (MSISDN1, MSISDN2, Act Date, Expiry Date).
    2. If found on Sensorise, saves and updates them into the database and returns the new values.
    3. If NOT found on Sensorise server, performs a complete lookup across CustomerVault database
       (sim_devices joined with customers, and sensorise_sims_basic) and returns the existing
       database values (Customer Name, Device SR No, IMEI, Model, SIM Provider, Plan, Firmware,
       Flash, SIM Type, MSISDN1, MSISDN2, Act Date, Expiry Date).
    """
    from sensorise import sensorise_client

    iccid_clean = str(iccid).strip()
    if not iccid_clean:
        return {"success": False, "message": "Please enter an ICCID to search."}

    # Step 1: Attempt query on Sensorise company server
    telematics = None
    try:
        telematics = sensorise_client.fetch_telematics_by_iccid(iccid_clean, mapping=mapping)
    except Exception as t_err:
        logger.warning(f"Sensorise server query error for ICCID {iccid_clean}: {t_err}")

    found_in_sensorise = bool(
        telematics and not telematics.get("error") and (
            telematics.get("msisdn1") or telematics.get("primaryMSISDN") or
            telematics.get("activation_date") or telematics.get("commercialActivationDate")
        )
    )

    # Step 2: Comprehensive Database Lookup across sim_devices and sensorise_sims_basic
    db_rec = None
    if is_db_configured():
        try:
            conn = get_connection()
            if conn:
                with conn.cursor() as cur:
                    # 1. Search in sim_devices joined with customers
                    cur.execute("""
                        SELECT d.id, c.name as customer_name, d.device_sr_no, d.imei, d.iccid,
                               d.msisdn1, d.msisdn2, d.act_date, d.expiry_date, d.model,
                               d.sim_provider, d.activation_plan, d.firmware, d.flash, d.sim_type, d.extra
                        FROM sim_devices d
                        LEFT JOIN customers c ON d.customer_id = c.id
                        WHERE d.deleted_at IS NULL AND (
                            d.iccid = %s OR d.iccid = %s OR d.iccid = %s OR d.iccid LIKE %s
                        )
                        LIMIT 1;
                    """, (iccid_clean, iccid_clean + 'F', iccid_clean.rstrip('F'), f"{iccid_clean[:18]}%"))
                    row = cur.fetchone()
                    if row:
                        db_rec = {
                            "customer_name": row.get("customer_name") or "",
                            "device_sr_no": row.get("device_sr_no") or "",
                            "imei": row.get("imei") or "",
                            "iccid": row.get("iccid") or iccid_clean,
                            "msisdn1": row.get("msisdn1") or "",
                            "msisdn2": row.get("msisdn2") or "",
                            "activation_date": format_to_dmy(row.get("act_date")),
                            "expiry_date": format_to_dmy(row.get("expiry_date")),
                            "model": row.get("model") or "",
                            "sim_provider": row.get("sim_provider") or "",
                            "activation_plan": row.get("activation_plan") or "",
                            "firmware": row.get("firmware") or "",
                            "flash": row.get("flash") or "",
                            "sim_type": row.get("sim_type") or "",
                            "extra": row.get("extra") or {}
                        }
                    else:
                        # 2. Search in sensorise_sims_basic
                        cur.execute("""
                            SELECT id, device_sr_no, imei, iccid, msisdn1, msisdn2, activation_date, expiry_date
                            FROM sensorise_sims_basic
                            WHERE iccid = %s OR iccid = %s OR iccid LIKE %s
                            LIMIT 1;
                        """, (iccid_clean, iccid_clean.rstrip('F'), f"{iccid_clean[:18]}%"))
                        b_row = cur.fetchone()
                        if b_row:
                            db_rec = {
                                "customer_name": "Sensorise SIM Inventory",
                                "device_sr_no": b_row.get("device_sr_no") or "",
                                "imei": b_row.get("imei") or "",
                                "iccid": b_row.get("iccid") or iccid_clean,
                                "msisdn1": b_row.get("msisdn1") or "",
                                "msisdn2": b_row.get("msisdn2") or "",
                                "activation_date": format_to_dmy(b_row.get("activation_date")),
                                "expiry_date": format_to_dmy(b_row.get("expiry_date")),
                                "model": "",
                                "sim_provider": "",
                                "activation_plan": "",
                                "firmware": "",
                                "flash": "",
                                "sim_type": "",
                                "extra": {}
                            }
                conn.close()
        except Exception as db_look_err:
            logger.warning(f"Database lookup error for ICCID {iccid_clean}: {db_look_err}")

    # Fallback to database values if NOT found on Sensorise server
    if not found_in_sensorise:
        if db_rec:
            updated_table = get_sensorise_basic_records(limit=80, fetch_all=True)
            return {
                "success": True,
                "source": "website_database",
                "data_source": "website_database",
                "found_in_sensorise": False,
                "found_in_database": True,
                "iccid": clean_field_val(db_rec.get("iccid")) or iccid_clean,
                "customer_name": clean_field_val(db_rec.get("customer_name")),
                "device_sr_no": clean_field_val(db_rec.get("device_sr_no")),
                "imei": clean_field_val(db_rec.get("imei")),
                "msisdn1": clean_field_val(db_rec.get("msisdn1")),
                "msisdn2": clean_field_val(db_rec.get("msisdn2")),
                "activation_date": clean_field_val(db_rec.get("activation_date")),
                "expiry_date": clean_field_val(db_rec.get("expiry_date")),
                "model": clean_field_val(db_rec.get("model")),
                "sim_provider": clean_field_val(db_rec.get("sim_provider")),
                "activation_plan": clean_field_val(db_rec.get("activation_plan")),
                "firmware": clean_field_val(db_rec.get("firmware")),
                "flash": clean_field_val(db_rec.get("flash")),
                "sim_type": clean_field_val(db_rec.get("sim_type")),
                "extra": db_rec.get("extra") or {},
                "headers": updated_table.get("headers", []),
                "rows": updated_table.get("rows", []),
                "message": f"ICCID '{iccid_clean}' was not found on Sensorise server. Displaying existing values from CustomerVault database."
            }
        else:
            return {
                "success": False,
                "source": "none",
                "data_source": "none",
                "found_in_sensorise": False,
                "found_in_database": False,
                "iccid": iccid_clean,
                "customer_name": "",
                "device_sr_no": "",
                "imei": "",
                "msisdn1": "",
                "msisdn2": "",
                "activation_date": "",
                "expiry_date": "",
                "message": f"ICCID '{iccid_clean}' was not found on Sensorise server or in CustomerVault database."
            }

    # Step 3: Extract live telematics from Sensorise and combine with database stored values
    # Rule: If the given ICCID value has no expiry date, activation date, msisdn1, msisdn2 on Sensorise (website),
    # print our database stored values. If at all not there in our database or website, print blank ("") for that column.
    web_m1 = clean_field_val(telematics.get("msisdn1") if telematics else None) or clean_field_val(telematics.get("primaryMSISDN") if telematics else None)
    web_m2 = clean_field_val(telematics.get("msisdn2") if telematics else None) or clean_field_val(telematics.get("fallbackMSISDN") if telematics else None)
    web_act = clean_field_val(format_to_dmy(telematics.get("activation_date") or telematics.get("commercialActivationDate")) if telematics else "")
    web_exp = clean_field_val(format_to_dmy(telematics.get("expiry_date") or telematics.get("commercialExpiryDate")) if telematics else "")

    db_m1 = clean_field_val(db_rec.get("msisdn1")) if db_rec else ""
    db_m2 = clean_field_val(db_rec.get("msisdn2")) if db_rec else ""
    db_act = clean_field_val(db_rec.get("activation_date")) if db_rec else ""
    db_exp = clean_field_val(db_rec.get("expiry_date")) if db_rec else ""

    final_m1 = web_m1 if web_m1 else (db_m1 if db_m1 else "")
    final_m2 = web_m2 if web_m2 else (db_m2 if db_m2 else "")
    final_act = web_act if web_act else (db_act if db_act else "")
    final_exp = web_exp if web_exp else (db_exp if db_exp else "")

    try:
        conn = get_connection()
        if conn:
            with conn.cursor() as cursor:
                # Update / Insert into sensorise_sims_basic
                cursor.execute("SELECT id FROM sensorise_sims_basic WHERE iccid = %s;", (iccid_clean,))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE sensorise_sims_basic
                        SET msisdn1 = %s, msisdn2 = %s, activation_date = %s, expiry_date = %s
                        WHERE iccid = %s;
                    """, (final_m1, final_m2, final_act, final_exp, iccid_clean))
                else:
                    cursor.execute("""
                        INSERT INTO sensorise_sims_basic (device_sr_no, imei, iccid, msisdn1, msisdn2, activation_date, expiry_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (
                        clean_field_val(db_rec.get("device_sr_no")) if db_rec else "",
                        clean_field_val(db_rec.get("imei")) if db_rec else "",
                        iccid_clean, final_m1, final_m2, final_act, final_exp
                    ))

                # Also update sim_devices if present with non-empty values
                act_sql_val = final_act if final_act else None
                exp_sql_val = final_exp if final_exp else None
                cursor.execute("""
                    UPDATE sim_devices
                    SET msisdn1 = COALESCE(NULLIF(%s, ''), msisdn1),
                        msisdn2 = COALESCE(NULLIF(%s, ''), msisdn2),
                        act_date = COALESCE(STR_TO_DATE(NULLIF(%s, ''), '%%d-%%m-%%Y'), act_date),
                        expiry_date = COALESCE(STR_TO_DATE(NULLIF(%s, ''), '%%d-%%m-%%Y'), expiry_date)
                    WHERE iccid = %s OR iccid = %s;
                """, (final_m1, final_m2, act_sql_val, exp_sql_val, iccid_clean, iccid_clean + 'F'))

                conn.commit()
            conn.close()

        regen_res = {}
        try:
            regen_res = sensorise_client.generate_api_token()
        except Exception:
            pass

        updated_table = get_sensorise_basic_records(limit=80, fetch_all=True)

        return {
            "success": True,
            "source": "sensorise" if (web_m1 or web_m2 or web_act or web_exp) else "website_database",
            "data_source": "sensorise" if (web_m1 or web_m2 or web_act or web_exp) else "website_database",
            "found_in_sensorise": bool(web_m1 or web_m2 or web_act or web_exp),
            "found_in_database": True if db_rec else False,
            "iccid": iccid_clean,
            "customer_name": clean_field_val(db_rec.get("customer_name")) if db_rec else "",
            "device_sr_no": clean_field_val(db_rec.get("device_sr_no")) if db_rec else "",
            "imei": clean_field_val(db_rec.get("imei")) if db_rec else "",
            "msisdn1": final_m1,
            "msisdn2": final_m2,
            "activation_date": final_act,
            "expiry_date": final_exp,
            "model": clean_field_val(db_rec.get("model")) if db_rec else "",
            "sim_provider": clean_field_val(db_rec.get("sim_provider")) if db_rec else "",
            "activation_plan": clean_field_val(db_rec.get("activation_plan")) if db_rec else "",
            "firmware": clean_field_val(db_rec.get("firmware")) if db_rec else "",
            "flash": clean_field_val(db_rec.get("flash")) if db_rec else "",
            "sim_type": clean_field_val(db_rec.get("sim_type")) if db_rec else "",
            "headers": updated_table.get("headers", []),
            "rows": updated_table.get("rows", []),
            "token_regenerated": bool(regen_res.get("success")),
            "apiToken": regen_res.get("apiToken") or sensorise_client.auth_token,
            "tokenExpiry": regen_res.get("tokenExpiry") or sensorise_client.get_token_expiry(),
            "message": f"Successfully matched ICCID '{iccid_clean}' — telematics merged with database and displayed."
        }
    except Exception as e:
        logger.error(f"Error searching and updating ICCID {iccid_clean}: {e}")
        return {"success": False, "error": str(e), "message": f"Database update error: {str(e)}"}

def sync_and_match_iccids_from_server(iccids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Connects to the Sensorise server and searches through the ICCID values.
    """
    from sensorise import sensorise_client

    conn_info = sensorise_client.test_connection()
    if not conn_info.get("connected"):
        return {
            "success": False,
            "connected": False,
            "message": f"Cannot connect to Sensorise server: {conn_info.get('message', 'Server unreachable')}",
            "server_status": conn_info,
            "matched_count": 0,
            "total_searched": 0,
            "available_columns": [],
            "preview": []
        }

    if not iccids:
        basic_records = get_sensorise_basic_records(limit=100, fetch_all=True)
        iccids = [r[2] for r in basic_records.get("rows", []) if len(r) > 2 and r[2]]

    if iccids:
        try:
            sensorise_client.check_sim_bulk_v2(iccids)
        except Exception as b_err:
            logger.warning(f"Bulk SIM query in sync_and_match_iccids_from_server: {b_err}")

    matched_records = []
    errors = []
    for iccid in iccids:
        telematics = sensorise_client.fetch_telematics_by_iccid(iccid)
        if telematics and not telematics.get("error"):
            matched_records.append(telematics)
        elif telematics and telematics.get("error"):
            errors.append(telematics.get("error"))

    if not matched_records:
        err_msg = errors[0] if errors else "No telematics records returned by Sensorise server for the given ICCIDs."
        return {
            "success": False,
            "connected": True,
            "message": f"Sensorise server reached, but failed to fetch telematics: {err_msg}",
            "matched_count": 0,
            "total_searched": len(iccids),
            "available_columns": [],
            "preview": []
        }

    conn = get_connection()
    update_params = []
    if conn:
        try:
            with conn.cursor() as cursor:
                update_sql = """
                    UPDATE sensorise_sims_basic
                    SET msisdn1 = COALESCE(NULLIF(%s, ''), msisdn1),
                        msisdn2 = COALESCE(NULLIF(%s, ''), msisdn2),
                        activation_date = COALESCE(NULLIF(%s, ''), activation_date),
                        expiry_date = COALESCE(NULLIF(%s, ''), expiry_date)
                    WHERE iccid = %s OR iccid = %s;
                """
                update_dev_sql = """
                    UPDATE sim_devices
                    SET msisdn1 = COALESCE(NULLIF(%s, ''), msisdn1),
                        msisdn2 = COALESCE(NULLIF(%s, ''), msisdn2),
                        act_date = COALESCE(STR_TO_DATE(NULLIF(%s, ''), '%%d-%%m-%%Y'), act_date),
                        expiry_date = COALESCE(STR_TO_DATE(NULLIF(%s, ''), '%%d-%%m-%%Y'), expiry_date)
                    WHERE iccid = %s OR iccid = %s;
                """
                for rec in matched_records:
                    iccid = str(rec.get("iccid") or "").strip()
                    m1 = str(rec.get("msisdn1") or "").strip()
                    m2 = str(rec.get("msisdn2") or "").strip()
                    act = format_to_dmy(rec.get("activation_date") or "")
                    exp = format_to_dmy(rec.get("expiry_date") or "")
                    if m1 or m2 or act or exp:
                        update_params.append((m1, m2, act, exp, iccid, iccid + 'F'))
                if update_params:
                    cursor.executemany(update_sql, update_params)
                    cursor.executemany(update_dev_sql, update_params)
                    conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating MySQL in sync_and_match_iccids_from_server: {e}")

    updated_records = get_sensorise_basic_records(limit=80, fetch_all=True)

    regen_res = {}
    try:
        regen_res = sensorise_client.generate_api_token()
    except Exception:
        pass

    return {
        "success": True,
        "connected": True,
        "message": f"Successfully matched {len(matched_records)} ICCIDs from Sensorise server and updated database!",
        "total_searched": len(iccids),
        "matched_count": len(matched_records),
        "token_regenerated": bool(regen_res.get("success")),
        "apiToken": regen_res.get("apiToken") or sensorise_client.auth_token,
        "tokenExpiry": regen_res.get("tokenExpiry") or sensorise_client.token_expiry,
        "headers": updated_records.get("headers", []),
        "rows": updated_records.get("rows", []),
        "available_columns": sensorise_client.get_available_columns(),
        "direct_columns": {
            "MSISDN1": "primaryMSISDN",
            "MSISDN2": "fallbackMSISDN",
            "Activation Date": "commercialActivationDate",
            "Expiry Date": "commercialExpiryDate"
        }
    }

def validate_and_preview_column_mapping(mapping: Dict[str, str]) -> Dict[str, Any]:
    from sensorise import sensorise_client

    mandatory_fields = {
        "msisdn1": "MSISDN1",
        "msisdn2": "MSISDN2",
        "activation_date": "Activation Date",
        "expiry_date": "Expiry Date"
    }

    errors = []
    warnings = []

    for field_key, field_name in mandatory_fields.items():
        mapped_col = mapping.get(field_key)
        if not mapped_col or not str(mapped_col).strip():
            errors.append(f"Mandatory column '{field_name}' is not mapped. Please select a Sensorise column.")

    basic_records = get_sensorise_basic_records(limit=5, fetch_all=False)
    reference_rows = basic_records.get("rows", [])
    
    preview = []
    for r in reference_rows[:5]:
        iccid = r[2] if len(r) > 2 else ""
        if not iccid:
            continue
        
        raw = sensorise_client.raw_telematics_cache.get(iccid, {})
        extracted = sensorise_client.extract_telematics_fields(raw, mapping=mapping) if raw else {}

        val_m1 = str(extracted.get("msisdn1") or (r[3] if len(r) > 3 else "") or "").strip()
        val_m2 = str(extracted.get("msisdn2") or (r[4] if len(r) > 4 else "") or "").strip()
        val_act = format_to_dmy(extracted.get("activation_date") or (r[5] if len(r) > 5 else "") or "")
        val_exp = format_to_dmy(extracted.get("expiry_date") or (r[6] if len(r) > 6 else "") or "")

        preview.append({
            "iccid": iccid,
            "device_sr_no": r[0] if len(r) > 0 else "",
            "imei": r[1] if len(r) > 1 else "",
            "msisdn1": val_m1,
            "msisdn2": val_m2,
            "activation_date": val_act,
            "expiry_date": val_exp,
            "status": "Valid" if (val_m1 or val_m2 or val_act or val_exp) else "Pending Server Sync",
            "valid": True
        })

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "preview": preview,
        "mapping": mapping,
        "available_columns": sensorise_client.get_available_columns()
    }

def reset_sensorise_basic_to_blank() -> Dict[str, Any]:
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE sensorise_sims_basic
                    SET msisdn1 = '', msisdn2 = '', activation_date = '', expiry_date = '';
                """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error resetting MySQL to blank: {e}")

    return get_sensorise_basic_records(limit=80, fetch_all=True)

def apply_sensorise_column_mapping(mapping: Dict[str, str]) -> Dict[str, Any]:
    from sensorise import sensorise_client

    validation = validate_and_preview_column_mapping(mapping)
    if not validation.get("valid"):
        return {
            "success": False,
            "message": "Validation failed: " + "; ".join(validation.get("errors", [])),
            "errors": validation.get("errors", []),
            "warnings": validation.get("warnings", [])
        }

    sensorise_client.active_mapping = {
        "msisdn1": mapping.get("msisdn1", "msisdn1"),
        "msisdn2": mapping.get("msisdn2", "msisdn2"),
        "activation_date": mapping.get("activation_date", "activation_date"),
        "expiry_date": mapping.get("expiry_date", "expiry_date")
    }

    conn = get_connection()
    updated_count = 0
    update_params = []
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, device_sr_no, imei, iccid FROM sensorise_sims_basic ORDER BY id ASC;")
                sim_rows = cursor.fetchall()

                all_iccids = [str(s.get("iccid") or "").strip() for s in sim_rows if str(s.get("iccid") or "").strip()]
                if all_iccids:
                    try:
                        bulk_res = sensorise_client.check_sim_bulk_v2(all_iccids)
                        if bulk_res.get("simDetailEntity"):
                            for item in bulk_res.get("simDetailEntity", []):
                                if isinstance(item, dict) and item.get("iccid"):
                                    sensorise_client.raw_telematics_cache[str(item["iccid"]).strip()] = item
                    except Exception as b_err:
                        logger.warning(f"Bulk SIM query during mapping notice: {b_err}")

                for sim in sim_rows:
                    iccid = str(sim.get("iccid") or "").strip()
                    if not iccid:
                        continue
                    telematics = sensorise_client.fetch_telematics_by_iccid(iccid, mapping=mapping) if iccid in sensorise_client.raw_telematics_cache else None

                    if telematics and not telematics.get("error"):
                        m1 = str(telematics.get("msisdn1") or "").strip()
                        m2 = str(telematics.get("msisdn2") or "").strip()
                        act = format_to_dmy(telematics.get("activation_date") or "")
                        exp = format_to_dmy(telematics.get("expiry_date") or "")
                        if m1 or m2 or act or exp:
                            update_params.append((m1, m2, act, exp, iccid))

                if update_params:
                    cursor.executemany("""
                        UPDATE sensorise_sims_basic
                        SET msisdn1 = %s, msisdn2 = %s, activation_date = %s, expiry_date = %s
                        WHERE iccid = %s;
                    """, update_params)
                    conn.commit()
                    updated_count = len(update_params)
            conn.close()
        except Exception as e:
            logger.error(f"Error applying column mapping in MySQL: {e}")

    regen_res = {}
    try:
        regen_res = sensorise_client.generate_api_token()
    except Exception:
        pass

    updated_records = get_sensorise_basic_records(limit=80, fetch_all=True)

    return {
        "success": True,
        "message": f"Column mapping successfully applied for {updated_count} SIMs.",
        "mapping": mapping,
        "updated_count": updated_count,
        "token_regenerated": bool(regen_res.get("success")),
        "apiToken": regen_res.get("apiToken") or sensorise_client.auth_token,
        "tokenExpiry": regen_res.get("tokenExpiry") or sensorise_client.get_token_expiry(),
        "headers": updated_records.get("headers", []),
        "rows": updated_records.get("rows", [])
    }

def get_sensorise_basic_records(limit: int = 500, page: int = 1, search: str = "", fetch_all: bool = False) -> Dict[str, Any]:
    """
    Retrieves records from sensorise_sims_basic table for the website.
    """
    headers = ["Device SR No", "IMEI", "ICCID", "MSISDN1", "MSISDN2", "Activation Date", "Expiry Date"]
    
    if not is_db_configured():
        return {
            "success": False,
            "message": "Database not configured. Please configure DB_HOST, DB_USER, DB_NAME in .env.",
            "headers": headers,
            "rows": [],
            "total": 0
        }

    try:
        conn = get_connection()
        if not conn:
            return {"success": False, "message": "Could not connect to MySQL.", "headers": headers, "rows": []}

        where_clause = ""
        params = []
        if search:
            search_pat = f"%{search}%"
            where_clause = "WHERE device_sr_no LIKE %s OR imei LIKE %s OR iccid LIKE %s OR msisdn1 LIKE %s OR msisdn2 LIKE %s"
            params = [search_pat] * 5

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS total FROM sensorise_sims_basic {where_clause};", params)
            total = cursor.fetchone().get("total", 0)

            if fetch_all:
                cursor.execute(f"""
                    SELECT device_sr_no, imei, iccid, msisdn1, msisdn2, activation_date, expiry_date 
                    FROM sensorise_sims_basic 
                    {where_clause} 
                    ORDER BY id ASC;
                """, params)
            else:
                offset = max(0, (page - 1) * limit)
                cursor.execute(f"""
                    SELECT device_sr_no, imei, iccid, msisdn1, msisdn2, activation_date, expiry_date 
                    FROM sensorise_sims_basic 
                    {where_clause} 
                    ORDER BY id ASC 
                    LIMIT %s OFFSET %s;
                """, params + [limit, offset])

            db_rows = cursor.fetchall()

        conn.close()

        rows = []
        for r in db_rows:
            rows.append([
                clean_field_val(r.get("device_sr_no")),
                clean_field_val(r.get("imei")),
                clean_field_val(r.get("iccid")),
                clean_field_val(r.get("msisdn1")),
                clean_field_val(r.get("msisdn2")),
                clean_field_val(format_to_dmy(r.get("activation_date") or "")),
                clean_field_val(format_to_dmy(r.get("expiry_date") or ""))
            ])

        return {
            "success": True,
            "filename": "Sensorise_SIMs_basic.xlsx",
            "table_name": "sensorise_sims_basic",
            "headers": headers,
            "rows": rows,
            "total": total,
            "page": page,
            "limit": total if fetch_all else limit,
            "source": "mysql"
        }
    except Exception as e:
        logger.error(f"Error querying sensorise_sims_basic: {e}")
        return {
            "success": False,
            "error": str(e),
            "headers": headers,
            "rows": [],
            "message": f"Query error: {str(e)}"
        }

def get_latest_records(limit: int = 500) -> Dict[str, Any]:
    return get_sensorise_basic_records(limit=limit, fetch_all=True)

def upsert_sensorise_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not is_db_configured() or not records:
        return {"success": True, "saved_to_db": False, "affected": 0, "message": "No records or DB unconfigured."}

    try:
        conn = get_connection()
        if not conn:
            return {"success": False, "saved_to_db": False, "message": "Could not connect to MySQL."}

        update_sql = """
            UPDATE sensorise_sims_basic
            SET msisdn1 = %s, msisdn2 = %s, activation_date = %s, expiry_date = %s
            WHERE iccid = %s;
        """

        params = []
        for r in records:
            iccid = str(r.get("iccid") or "").strip()
            if not iccid:
                continue
            m1 = str(r.get("msisdn1") or r.get("msisdn") or "").strip()
            m2 = str(r.get("msisdn2") or "").strip()
            act = format_to_dmy(str(r.get("activation_date") or r.get("act_date") or ""))
            exp = format_to_dmy(str(r.get("expiry_date") or r.get("exp_date") or ""))
            params.append((m1, m2, act, exp, iccid))

        with conn.cursor() as cursor:
            cursor.executemany(update_sql, params)
            conn.commit()

        conn.close()
        return {"success": True, "saved_to_db": True, "affected": len(params)}
    except Exception as e:
        logger.error(f"Error updating sensorise_sims_basic: {e}")
        return {"success": False, "saved_to_db": False, "error": str(e)}

def get_sensorise_records(
    limit: int = 250,
    search: str = "",
    status: str = "",
    page: int = 1
) -> Dict[str, Any]:
    return get_sensorise_basic_records(limit=limit, search=search, page=page, fetch_all=(limit >= 80 and not search))

def get_sensorise_summary_stats() -> Dict[str, Any]:
    if not is_db_configured():
        return {
            "configured": False,
            "connected": False,
            "total_sims": 0,
            "active_sims": 0,
            "expired_sims": 0,
            "suspended_sims": 0,
            "last_synced": ""
        }

    try:
        conn = get_connection()
        if not conn:
            return {"configured": True, "connected": False, "total_sims": 0, "active_sims": 0, "expired_sims": 0}

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) AS total_sims,
                    SUM(CASE WHEN (activation_date IS NOT NULL AND activation_date != '') THEN 1 ELSE 0 END) AS active_sims,
                    SUM(CASE WHEN (expiry_date IS NOT NULL AND expiry_date != '') THEN 1 ELSE 0 END) AS expired_sims
                FROM sensorise_sims_basic;
            """)
            stats = cursor.fetchone() or {}

        conn.close()
        return {
            "configured": True,
            "connected": True,
            "total_sims": int(stats.get("total_sims") or 0),
            "active_sims": int(stats.get("active_sims") or 0),
            "expired_sims": int(stats.get("expired_sims") or 0),
            "other_sims": 0,
            "last_synced": ""
        }
    except Exception as e:
        logger.error(f"Error getting sensorise stats: {e}")
        return {"configured": True, "connected": False, "error": str(e), "total_sims": 0, "active_sims": 0, "expired_sims": 0}

