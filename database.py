"""database.py - MySQL layer for CustomerVault (uses PyMySQL).

Connection settings live in config.py - edit them there.

ONE TABLE PER CUSTOMER:
  * every customer is its own MySQL table; the table name IS the customer name
  * every customer table has a built-in `customer_name` column that always holds the table name,
    the 3 mandatory columns (Device Sr No, IMEI, ICCID), and every extra column an employee added (added to ALL customer tables)
  * renaming a customer renames its table and updates the customer_name column of all its rows
  * employees / sessions / column_registry / app_state - logins and the column list
  * customers - only a registry (id <-> table name) rebuilt from the real tables, so the website
    always shows exactly the customer tables that exist in MySQL

MySQL note: CREATE / ALTER / RENAME TABLE commit immediately - MySQL cannot roll those back.
"""
import ast
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta

import pymysql
import pymysql.cursors

import config

CFG = config.MYSQL
DB_LABEL = f"mysql://{CFG['user']}@{CFG['host']}:{CFG['port']}/{CFG['database']}"
WRITE_LOCK = threading.RLock()

TABLE_OPTS = "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"

# (SQL column, label shown in the app, is_date)
STANDARD = [   # the 3 built-in columns: every customer table has them and ALL THREE are mandatory
    ("device_sr_no", "Device Sr No", 0),
    ("imei", "IMEI", 0),
    ("iccid", "ICCID", 0),
]
# Former standard columns. They are NOT created any more. If you add a column with one of these names later (Add record /
# Excel upload / Bulk Upload), it gets the same SQL name and date handling as before, so Expiry Alerts and the SIM Data Upload work again.
OPTIONAL_KNOWN = {
    "msisdn1": ("MSISDN1", 0), "msisdn2": ("MSISDN2", 0),
    "activation_date": ("ACT DATE", 1), "expiry_date": ("EXP DATE", 1), "dispatched_date": ("DISPATCHED DATE", 1),
    "model": ("MODEL", 0), "sim_provider": ("SIM PROVIDER", 0), "flash": ("FLASH", 0), "activation_plan": ("ACTIVATION PLAN", 0),
    "firmware": ("FIRMWARE", 0),
}
OPTIONAL_BY_LABEL = {lab.lower(): (db, d) for db, (lab, d) in OPTIONAL_KNOWN.items()}
# The 12 columns EVERY customer file must have, in this order (an Excel heading such as ACTIVATION DATE / EXPIRY DATE / DEVICE SR NO.
# is matched to these labels by ALIAS below). They are created in every customer table at start-up and by every new customer,
# are never removed by the empty-column clean-up and cannot be deleted. Only the first three are mandatory.
ALWAYS_COLUMNS = ["Device Sr No", "IMEI", "ICCID", "MSISDN1", "MSISDN2", "ACT DATE", "EXP DATE", "DISPATCHED DATE",
                  "MODEL", "SIM PROVIDER", "FLASH", "ACTIVATION PLAN"]
ALWAYS_LOWER = {x.lower() for x in ALWAYS_COLUMNS}
# The ONLY mandatory columns (must be filled when a record is added / edited / uploaded). Everything else is optional.
REQUIRED_DB = {"device_sr_no", "imei", "iccid"}
MANDATORY = [x for x in STANDARD if x[0] in REQUIRED_DB]
STANDARD_DB = {x[0] for x in STANDARD}
REMOVED = set()                 # mandatory columns the user deleted on purpose (remembered in app_state, so a restart does not bring them back)
DELETABLE_MANDATORY = {"imei"}  # mandatory columns that may be deleted from the Delete Columns screen
RESERVED_DB = {"id", "customer_id", "customer_name", "added_by", "added_on"}
RESERVED_LABELS = {"customer name", "customer", "added by", "added on", "#"}

# alternative spellings (e.g. in Excel files) -> the standard label
ALIAS = {
    "devicesrno": "Device Sr No", "deviceserialno": "Device Sr No", "devicesrnumber": "Device Sr No",
    "pcbno": "Device Sr No", "pcbnumber": "Device Sr No", "pcbsrno": "Device Sr No", "pcbserialno": "Device Sr No", "pcb": "Device Sr No",   # a PCB No column is the Device Sr No
    "imei": "IMEI", "imeinumber": "IMEI", "imeino": "IMEI", "iccid": "ICCID",
    "ccid": "ICCID", "ccidno": "ICCID", "ccidnumber": "ICCID", "iccidno": "ICCID", "iccidnumber": "ICCID",   # CCID = ICCID
    "msisdn1": "MSISDN1", "msisdn2": "MSISDN2",
    "actdate": "ACT DATE", "activationdate": "ACT DATE",
    "expdate": "EXP DATE", "expirydate": "EXP DATE", "expirationdate": "EXP DATE",
    "dispatcheddate": "DISPATCHED DATE", "dispatchdate": "DISPATCHED DATE",
    "model": "MODEL", "simprovider": "SIM PROVIDER", "flash": "FLASH",
    "activationplan": "ACTIVATION PLAN", "actplan": "ACTIVATION PLAN", "plan": "ACTIVATION PLAN",
    "simplan": "ACTIVATION PLAN",
    "firmware": "FIRMWARE", "firmwareversion": "FIRMWARE", "fwversion": "FIRMWARE",
}
MON = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
LIKE = " LIKE %s"   # MySQL's default LIKE escape character is already the backslash


# --------------------------------------------------------------------------- helpers
def q(name):  # quote an identifier (names are always validated/sanitised before reaching here)
    return "`" + name + "`"


def text(v):
    """Any JSON value -> stripped string ('' for null)."""
    return "" if v is None else str(v).strip()


def now():
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def today():
    return date.today().isoformat()


def to_iso(s):
    """2026-09-20 | 15-Feb-25 | 15/02/2025 (day first) -> '2026-09-20'; None if not a date."""
    t = str(s or "").strip()
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        y, mo, d = map(int, m.groups())
    else:
        m = re.match(r"^(\d{1,2})[-/ ]([A-Za-z]{3})[a-z]*[-/ ,]*(\d{2,4})$", t)
        if m and m.group(2).lower() in MON:
            d, mo, y = int(m.group(1)), MON[m.group(2).lower()], int(m.group(3))
        else:
            m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})$", t)
            if not m:
                return None
            d, mo, y = map(int, m.groups())
    if y < 100:
        y += 2000
    try:
        return date(y, mo, d).isoformat()
    except ValueError:
        return None


def canon_label(name):
    s = re.sub(r"\s+", " ", str(name or "")).strip()
    return ALIAS.get(re.sub(r"[^a-z0-9]", "", s.lower()), s)


def make_db_name(label, taken):
    """Label -> safe SQL column name (MySQL allows max 64 characters)."""
    base = (re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "column")[:50]
    if base[0].isdigit():
        base = "c_" + base
    if base in RESERVED_DB:
        base = "x_" + base
    name, n = base, 2
    while name in taken:
        name, n = f"{base}_{n}", n + 1
    return name


# --------------------------------------------------------------------------- connections
class Conn:
    """Thin wrapper so the rest of the code can write  c.execute(sql, params).fetchone()  etc.
    close() hands a healthy connection back to the pool instead of closing the socket (see POOL below)."""

    def __init__(self, raw, pooled=False, autocommit=False):
        self.raw = raw
        self.pooled = pooled
        self.autocommit = autocommit

    def execute(self, sql, params=None):
        cur = self.raw.cursor()
        cur.execute(sql, params or None)
        return cur

    def executemany(self, sql, seq):
        cur = self.raw.cursor()
        cur.executemany(sql, seq)
        return cur

    def close(self):
        if self.pooled:
            _pool_put(self)
        else:
            _really_close(self.raw)


def _really_close(raw):
    try:
        raw.close()
    except Exception:
        pass


# ---- connection pool -------------------------------------------------------------------------------------------
# Opening a new TCP connection for every query used up all of Windows' local ports (WinError 10048: "Only one usage
# of each socket address ..."). Connections are now reused, so the app only ever holds a handful of sockets.
POOL_MAX = 8            # idle connections kept for reuse
POOL_IDLE_SECONDS = 120   # an idle connection older than this is replaced by a fresh one
_POOL = []              # [(raw_connection, last_used_time)]
_POOL_LOCK = threading.Lock()


def _pool_get():
    while True:
        with _POOL_LOCK:
            if not _POOL:
                return None
            raw, used = _POOL.pop()
        if time.time() - used > POOL_IDLE_SECONDS:
            _really_close(raw)
            continue
        try:
            raw.ping(reconnect=False)   # dead (server restarted / timed out)? -> throw it away and try the next one
            return raw
        except Exception:
            _really_close(raw)


def _pool_put(conn):
    raw = conn.raw
    try:
        if not conn.autocommit:
            raw.rollback()   # never hand out a connection with an open transaction
        with _POOL_LOCK:
            if len(_POOL) < POOL_MAX:
                _POOL.append((raw, time.time()))
                return
    except Exception:
        pass
    _really_close(raw)


def close_pool():
    with _POOL_LOCK:
        items, _POOL[:] = list(_POOL), []
    for raw, _ in items:
        _really_close(raw)


CONNECT_RETRIES = 3        # transient failures (server still starting, network blip) are retried
CONNECT_RETRY_WAIT = 1.0   # seconds between tries; wrong password / unknown database are NOT retried
_NO_RETRY = (1044, 1045, 1049)   # access denied (user / database) and unknown database


def connect(with_db=True, autocommit=False):
    kw = dict(host=CFG["host"], port=int(CFG["port"]), user=CFG["user"], password=CFG["password"],
              charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
              autocommit=autocommit, connect_timeout=10, read_timeout=60, write_timeout=60)
    if with_db:
        kw["database"] = CFG["database"]
    if os.environ.get("MYSQL_SSL", "").lower() in ("1", "true", "yes"):   # cloud MySQL (Aiven, TiDB, ...) requires TLS
        kw["ssl"] = {"ca": None}
        kw["ssl_verify_cert"] = False
    if with_db:
        raw = _pool_get()
        if raw is not None:
            raw.autocommit(autocommit)
            return Conn(raw, pooled=True, autocommit=autocommit)
    last = None
    for attempt in range(1, CONNECT_RETRIES + 1):
        try:
            return Conn(pymysql.connect(**kw), pooled=with_db, autocommit=autocommit)
        except pymysql.err.OperationalError as e:
            last = e
            if (e.args and e.args[0] in _NO_RETRY) or attempt == CONNECT_RETRIES:
                break
            time.sleep(CONNECT_RETRY_WAIT)
    raise last


_OWN = {}          # customer table -> (time, {sql column names (lower case) this customer really uses})
OWN_TTL = 30       # seconds


@contextmanager
def tx():
    """Write transaction - all-or-nothing for inserts/updates."""
    with WRITE_LOCK:
        conn = connect()
        try:
            yield conn
            conn.raw.commit()
            _OWN.clear()   # a write may have filled / emptied a column -> recompute which columns each customer uses
        except BaseException:
            try:
                conn.raw.rollback()
            except pymysql.MySQLError:
                pass
            raise
        finally:
            conn.close()


@contextmanager
def reader():
    conn = connect(autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


def scalar(c, sql, params=None):
    r = c.execute(sql, params).fetchone()
    return next(iter(r.values())) if r else None


def table_columns(c, table="devices"):
    return [r["Field"] for r in c.execute(f"SHOW COLUMNS FROM {q(table)}")]


# --------------------------------------------------------------------------- schema (automatic)
# ONE TABLE PER CUSTOMER.  The table name IS the customer name, and every customer table has a built-in
# `customer_name` column that always holds that table name.  The `customers` table is only a registry
# (id <-> table name) so the website has stable ids; it is rebuilt from the real tables by reconcile().
SYSTEM = {"employees", "sessions", "customers", "devices", "column_registry", "app_state", "activity_log", "trash_bin"}
BAD_NAME = re.compile(r"[`/\\.\x00-\x1f]")
BROKEN = {}   # customer table name -> why it cannot be used right now (shown on the website)
GID = 10_000_000   # the id the website sees for a record = customer_id * GID + row id inside that customer's table


def create_database():
    name = CFG["database"]
    if "`" in name:
        raise ValueError("Database name in config.py must not contain a backtick")
    conn = connect(with_db=False, autocommit=True)
    try:
        conn.execute(f"CREATE DATABASE IF NOT EXISTS {q(name)} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    finally:
        conn.close()


def explain_connect_error(e):
    """Turn a start-up / connection exception into a short message that says what to fix."""
    if isinstance(e, RuntimeError):
        return str(e)
    code = e.args[0] if e.args and isinstance(e.args[0], int) else None
    detail = e.args[1] if len(e.args) > 1 else e
    msg = f"Cannot connect to MySQL ({DB_LABEL}): {detail}"
    if "10048" in str(e):
        msg += ("\nWindows has run out of free local ports (too many recent connections). Wait 2-4 minutes or restart the PC, "
                "stop any other copies of this app that are still running, then start it again.")
    elif code in (2002, 2003, 2013) or "refused" in str(e).lower():
        msg += ("\nMySQL is not reachable. Check that the MySQL service is running and that host / port in "
                "config_local.py are right (MySQL Workbench shows the port; the default is 3306).")
    elif code in (2003, 2006, 2026) or "ssl" in str(e).lower() or "insecure transport" in str(e).lower():
        msg += "\nSSL problem: set MYSQL_SSL=true in the Render environment (your MySQL provider requires an encrypted connection)."
    elif code == 1045:
        msg += ("\nWrong user name or password. Put the real ones in config_local.py "
                "(or set MYSQL_USER / MYSQL_PASSWORD) - the same login you use in MySQL Workbench.")
    elif code == 1044:
        msg += f"\nThis MySQL user has no permission on the database. In MySQL run:  GRANT ALL ON `{CFG['database']}`.* TO '{CFG['user']}'@'%';"
    elif "cryptography" in str(e).lower():
        msg += "\nMySQL 8 login needs an extra package:  pip install cryptography"
    elif code == 1049:   # unknown database -> show what really exists
        try:
            conn = connect(with_db=False, autocommit=True)
            names = [next(iter(r.values())) for r in conn.execute("SHOW DATABASES").fetchall()]
            conn.close()
            msg += ("\nDatabases on this server: " + ", ".join(names) +
                    "\nPut the exact name in config_local.py (MYSQL -> database).")
        except Exception:
            pass
    return msg


def clean_name(name):
    """A customer name becomes a MySQL table name, so it must be a legal one."""
    n = re.sub(r"\s+", " ", str(name or "")).strip()
    if not n:
        raise ValueError("Customer name is required")
    if len(n) > 64:
        raise ValueError("Customer name is too long (it is a MySQL table name: max 64 characters)")
    if BAD_NAME.search(n):
        raise ValueError("Customer name cannot contain  `  /  \\  or  .  (it is used as a MySQL table name)")
    if n.casefold() in SYSTEM or n.startswith("__"):
        raise ValueError(f'"{n}" is reserved for the system - choose another customer name')
    return n


def _real_tables(c):
    return [list(r.values())[0] for r in c.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'").fetchall()]


def customer_like_tables(c):
    return [t for t in _real_tables(c) if t.casefold() not in SYSTEM and not t.startswith("__")]


def customer_names(c):
    return [r["name"] for r in c.execute("SELECT name FROM customers ORDER BY id").fetchall()]


def create_customer_table(c, name):
    mand = ", ".join(f"{q(col)} VARCHAR(255) NOT NULL DEFAULT ''" for col, _, _ in STANDARD if col not in REMOVED)
    keys = [f"KEY ix_{col}({col})" for col in ("imei", "iccid", "device_sr_no") if col not in REMOVED]
    extra = "".join(f"{q(r['db_name'])} TEXT NULL, " for r in
                    c.execute("SELECT db_name FROM column_registry WHERE is_mandatory=0 ORDER BY pos").fetchall()
                    if r["db_name"] not in STANDARD_DB)   # the standard columns are already in `mand`
    c.execute(f"""CREATE TABLE IF NOT EXISTS {q(name)}(
        id INT AUTO_INCREMENT PRIMARY KEY,
        customer_name VARCHAR(255) NOT NULL DEFAULT '',
        {mand}, {extra}
        added_by VARCHAR(100), added_on VARCHAR(30)
        {''.join(', ' + k for k in keys)}) {TABLE_OPTS}""")


def register_unknown(c, tables):
    """Columns that exist in a table but not in column_registry (added by hand in MySQL) become app columns."""
    known = {r["db_name"].lower() for r in c.execute("SELECT db_name FROM column_registry")}
    for t in tables:
        for name in table_columns(c, t):
            if name.lower() in known or name.lower() in RESERVED_DB:
                continue
            pos = int(scalar(c, "SELECT COALESCE(MAX(pos),0)+1 FROM column_registry"))
            c.execute("INSERT IGNORE INTO column_registry(db_name,label,is_mandatory,is_date,pos) VALUES(%s,%s,0,0,%s)",
                      (name, name.replace("_", " ").title(), pos))
            known.add(name.lower())


NAME_CHECK_EVERY = 60     # seconds. The customer_name repair below scans a whole table, so it is not run every 3 s per table
_NAME_CHECKED = {}


def fix_table(c, name, repair_names=None):
    """Make one customer table complete: id, customer_name (= the table name), the standard columns, every extra column.
    repair_names=None: the (full-table) customer_name repair runs at most once per NAME_CHECK_EVERY seconds per table."""
    have = {n.lower() for n in table_columns(c, name)}
    if "id" not in have:
        try:
            c.execute(f"ALTER TABLE {q(name)} ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST")
        except pymysql.MySQLError:   # the table already has another primary key
            c.execute(f"ALTER TABLE {q(name)} ADD COLUMN id INT NOT NULL AUTO_INCREMENT UNIQUE FIRST")
    if "customer_name" not in have:
        c.execute(f"ALTER TABLE {q(name)} ADD COLUMN customer_name VARCHAR(255) NOT NULL DEFAULT '' AFTER id")
    for x in get_columns(c):
        if x["db"].lower() not in have:
            typ = "VARCHAR(255) NOT NULL DEFAULT ''" if x["db"] in STANDARD_DB else "TEXT NULL"
            c.execute(f"ALTER TABLE {q(name)} ADD COLUMN {q(x['db'])} {typ}")
    for col, typ in (("added_by", "VARCHAR(100)"), ("added_on", "VARCHAR(30)")):
        if col not in have:
            c.execute(f"ALTER TABLE {q(name)} ADD COLUMN {q(col)} {typ}")
    if repair_names is None:
        repair_names = time.time() - _NAME_CHECKED.get(name, 0.0) >= NAME_CHECK_EVERY
    if repair_names:
        c.execute(f"UPDATE {q(name)} SET customer_name=%s WHERE customer_name IS NULL OR BINARY customer_name <> BINARY %s",
                  (name, name))
        _NAME_CHECKED[name] = time.time()
    ensure_indexes(c, name)


def ensure_indexes(c, name):
    """Duplicate checks look values up in every customer table, so Device Sr No / IMEI / ICCID need an index each."""
    have = {n.lower() for n in table_columns(c, name)}
    indexed = {r["Column_name"].lower() for r in c.execute(f"SHOW INDEX FROM {q(name)}") if r["Seq_in_index"] == 1}
    for col in ("imei", "iccid", "device_sr_no"):
        if col in have and col not in indexed and col not in REMOVED:
            try:
                c.execute(f"CREATE INDEX {q('ix_' + col)} ON {q(name)} ({q(col)})")
            except pymysql.MySQLError:   # e.g. a hand-made TEXT column cannot be indexed - the app still works, just slower
                pass


def sync_registry(c):
    """`customers` registry <-> real tables.  A table that exists is a customer; a customer whose table is gone is
    dropped from the registry.  Exactly one table renamed directly in MySQL is followed as a RENAME (id kept)."""
    real = customer_like_tables(c)
    reg = c.execute("SELECT id, name FROM customers ORDER BY id").fetchall()
    have_t = {t.casefold() for t in real}
    have_r = {r["name"].casefold() for r in reg}
    gone = [r for r in reg if r["name"].casefold() not in have_t]
    new = [t for t in real if t.casefold() not in have_r]
    msgs = []
    exact = {t.casefold(): t for t in real}
    for r in reg:   # the website must show the name EXACTLY as MySQL spells it (capital letters included)
        t = exact.get(r["name"].casefold())
        if t and t != r["name"]:
            try:
                c.execute("UPDATE customers SET name=%s WHERE id=%s", (t, r["id"]))
                msgs.append(f'name spelled as in MySQL: "{r["name"]}" -> "{t}"')
            except pymysql.MySQLError:
                pass
    if len(gone) == 1 and len(new) == 1:
        c.execute("UPDATE customers SET name=%s WHERE id=%s", (new[0], gone[0]["id"]))
        msgs.append(f'table renamed in MySQL: "{gone[0]["name"]}" -> "{new[0]}"')
    else:
        for r in gone:
            try:
                c.execute("DELETE FROM customers WHERE id=%s", (r["id"],))
            except pymysql.MySQLError as e:
                msgs.append(f'could not remove "{r["name"]}" from the customer list: {e}')
        for t in list(new):   # one failing name must not stop the others from being added
            try:
                c.execute("INSERT INTO customers(name,created_at) VALUES(%s,%s)", (t, now()))
            except pymysql.MySQLError as e:
                new.remove(t)
                msgs.append(f'table "{t}" could not be added to the customer list: {e}')
        if gone:
            msgs.append("no table, removed from the customer list: " + ", ".join(r["name"] for r in gone))
        if new:
            msgs.append("new table(s) found: " + ", ".join(new))
    return " | ".join(msgs)


def _drop_old_triggers():
    conn = connect(autocommit=True)
    try:
        for t in ("cv_customer_rename", "cv_device_customer_name"):
            conn.execute(f"DROP TRIGGER IF EXISTS {t}")
    except pymysql.MySQLError:
        pass
    finally:
        conn.close()


def _migrate_old_devices(c):
    """Older versions kept every record in ONE `devices` table. Copy those rows into per-customer tables (once).
    Nothing is deleted: the old `devices` table stays as a backup that the app no longer reads."""
    if "devices" not in {t.casefold() for t in _real_tables(c)}:
        return
    if scalar(c, "SELECT v FROM app_state WHERE k='migrated_devices'"):
        return
    try:
        dcols = table_columns(c, "devices")
        if "customer_id" not in {x.lower() for x in dcols}:
            return   # not our old table
        register_unknown(c, ["devices"])
        rows = c.execute("SELECT cu.name, COUNT(*) AS n FROM devices d JOIN customers cu ON cu.id=d.customer_id "
                         "GROUP BY cu.name").fetchall()
        for r in rows:
            clean_name(r["name"])   # raises before anything is copied if a name cannot be a table name
        for r in rows:
            name = clean_name(r["name"])
            create_customer_table(c, name)
            fix_table(c, name)
            target = {x.lower() for x in table_columns(c, name)}
            use = [x for x in dcols if x.lower() in target and x.lower() not in ("id", "customer_id", "customer_name")]
            lst = ",".join(q(x) for x in ["customer_name", *use])
            src = ",".join("d." + q(x) for x in use)
            c.execute(f"INSERT INTO {q(name)}({lst}) SELECT %s{',' + src if src else ''} FROM devices d "
                      f"JOIN customers cu ON cu.id=d.customer_id WHERE cu.name=%s "
                      f"AND (d.imei='' OR NOT EXISTS (SELECT 1 FROM {q(name)} x WHERE x.imei=d.imei))", (name, name))
        c.execute("REPLACE INTO app_state(k,v) VALUES('migrated_devices','1')")
        c.raw.commit()
        print(f"  note: moved the rows of the old `devices` table into {len(rows)} customer table(s). "
              "The old `devices` table is left untouched; you can drop it once you have checked the data.")
    except Exception as e:
        c.raw.rollback()
        raise RuntimeError(f"Could not move your old `devices` rows into customer tables: {e}\n"
                           "Nothing was deleted or changed. Fix the problem above (or ask for help) and start again.")


def _drop_devices_fk():
    conn = connect(autocommit=True)
    try:
        for r in conn.execute("SELECT CONSTRAINT_NAME AS n FROM information_schema.TABLE_CONSTRAINTS WHERE "
                              "TABLE_SCHEMA=DATABASE() AND TABLE_NAME='devices' AND CONSTRAINT_TYPE='FOREIGN KEY'").fetchall():
            conn.execute(f"ALTER TABLE `devices` DROP FOREIGN KEY {q(r['n'])}")   # so editing `customers` never touches old rows
    except pymysql.MySQLError:
        pass
    finally:
        conn.close()


def _init_schema():
    """Create every system table that is missing. Safe to run on every start."""
    if getattr(config, "AUTO_CREATE_DATABASE", True):
        create_database()
    with tx() as c:
        c.execute(f"""CREATE TABLE IF NOT EXISTS employees(
            id INT AUTO_INCREMENT PRIMARY KEY, emp_id VARCHAR(100) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL, salt VARCHAR(64) NOT NULL, pass_hash VARCHAR(128) NOT NULL,
            created_at VARCHAR(30)) {TABLE_OPTS}""")
        if "role" not in {n.lower() for n in table_columns(c, "employees")}:   # role given by an admin (Add Member); NULL = decided by config.ROLES
            c.execute("ALTER TABLE employees ADD COLUMN role VARCHAR(20) NULL")
        c.execute(f"""CREATE TABLE IF NOT EXISTS sessions(
            token VARCHAR(64) PRIMARY KEY, emp_id VARCHAR(100) NOT NULL, expires_at VARCHAR(30) NOT NULL) {TABLE_OPTS}""")
        c.execute(f"""CREATE TABLE IF NOT EXISTS customers(
            id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL UNIQUE, created_at VARCHAR(30)) {TABLE_OPTS}""")
        have_c = {n.lower() for n in table_columns(c, "customers")}
        if not {"id", "name"} <= have_c:
            raise RuntimeError("Your existing table `customers` has columns " + ", ".join(sorted(have_c)) +
                               " but the app needs at least: id, name")
        if "created_at" not in have_c:
            c.execute("ALTER TABLE customers ADD COLUMN created_at VARCHAR(30)")
        c.execute(f"""CREATE TABLE IF NOT EXISTS column_registry(
            db_name VARCHAR(64) PRIMARY KEY, label VARCHAR(100) NOT NULL UNIQUE,
            is_mandatory TINYINT NOT NULL DEFAULT 0, is_date TINYINT NOT NULL DEFAULT 0,
            pos INT NOT NULL) {TABLE_OPTS}""")
        c.execute(f"""CREATE TABLE IF NOT EXISTS app_state(
            k VARCHAR(50) PRIMARY KEY, v VARCHAR(255)) {TABLE_OPTS}""")
        c.execute(f"""CREATE TABLE IF NOT EXISTS activity_log(
            id BIGINT AUTO_INCREMENT PRIMARY KEY, emp_id VARCHAR(100) NOT NULL DEFAULT '', emp_name VARCHAR(255) NOT NULL DEFAULT '',
            action VARCHAR(60) NOT NULL, details TEXT, ip VARCHAR(64), created_at VARCHAR(30) NOT NULL,
            INDEX idx_act_time(created_at), INDEX idx_act_emp(emp_id)) {TABLE_OPTS}""")
        # the Cart: everything deleted on the website waits here until it is restored or deleted permanently
        c.execute(f"""CREATE TABLE IF NOT EXISTS trash_bin(
            id INT AUTO_INCREMENT PRIMARY KEY, kind VARCHAR(10) NOT NULL, name VARCHAR(255) NOT NULL,
            label VARCHAR(255) NOT NULL DEFAULT '', records INT NOT NULL DEFAULT 0, data LONGTEXT NULL,
            deleted_by VARCHAR(100), deleted_by_name VARCHAR(255), deleted_at VARCHAR(30) NOT NULL) {TABLE_OPTS}""")
        _load_removed(c)
        mand_sql = ", ".join(f"{q(col)} VARCHAR(255) NOT NULL DEFAULT ''" for col, _, _ in STANDARD if col not in REMOVED)
        # `devices` is the old combined table: created if missing so the database has it, but no longer read
        c.execute(f"""CREATE TABLE IF NOT EXISTS devices(
            id INT AUTO_INCREMENT PRIMARY KEY, customer_id INT NULL, customer_name VARCHAR(255) NOT NULL DEFAULT '',
            {mand_sql}, added_by VARCHAR(100), added_on VARCHAR(30)) {TABLE_OPTS}""")
        for pos, (col, label, is_date) in enumerate(STANDARD, 1):
            if col in REMOVED:
                continue
            c.execute("INSERT IGNORE INTO column_registry(db_name,label,is_mandatory,is_date,pos) VALUES(%s,%s,%s,%s,%s)",
                      (col, label, int(col in REQUIRED_DB), is_date, pos))
            # also fixes databases created earlier, where all 12 standard columns were flagged mandatory
            c.execute("UPDATE column_registry SET is_mandatory=%s WHERE db_name=%s", (int(col in REQUIRED_DB), col))
    _drop_old_triggers()
    with tx() as c:
        _migrate_old_devices(c)
    _drop_devices_fk()


def seed_from_config():
    """Create the table of every customer named in config.py DEFAULT_CUSTOMERS that has none yet (create only)."""
    if not getattr(config, "CREATE_MISSING_CUSTOMER_TABLES", False):
        return
    made = []
    with tx() as c:
        have = {t.casefold() for t in _real_tables(c)}
        for n in config_customers() or []:
            try:
                n = clean_name(n)
            except ValueError as e:
                print(f"  note: config.py customer {n!r} skipped: {e}")
                continue
            if n.casefold() in have:
                continue
            create_customer_table(c, n)
            fix_table(c, n)
            have.add(n.casefold())
            made.append(n)
    if made:
        print("  note: created customer table(s) from config.py: " + ", ".join(made))


def _save_removed(c):
    c.execute("REPLACE INTO app_state(k,v) VALUES('removed_mandatory',%s)", (",".join(sorted(REMOVED)),))


def _sync_unique():
    UNIQUE[:] = [u for u in _UNIQUE_ALL if u[0] not in REMOVED]


def _load_removed(c):
    """Remember which mandatory columns (e.g. IMEI) were deleted on purpose. A column that exists again is not 'removed'."""
    REMOVED.clear()
    r = c.execute("SELECT v FROM app_state WHERE k='removed_mandatory'").fetchone()
    REMOVED.update(x.strip() for x in ((r["v"] if r else "") or "").split(",") if x.strip())
    for x in list(REMOVED):
        if c.execute("SELECT 1 FROM column_registry WHERE db_name=%s", (x,)).fetchone():
            REMOVED.discard(x)
    _save_removed(c)
    _sync_unique()


def init_db():
    _init_schema()
    seed_from_config()
    msg = reconcile()   # tables -> customer list -> website, and MySQL -> config.py
    if msg != "ok":
        print("  note:", msg)
    ensure_standard_columns()
    prune_empty_columns()


def ensure_standard_columns():
    """Make sure the 12 ALWAYS_COLUMNS exist in the column list AND in every customer table (a missing one is added empty),
    and put them first, in that order; every other column follows. Safe to run on every start."""
    try:
        with tx() as c:
            added = []
            for lab in ALWAYS_COLUMNS:
                if not find_column(c, lab):
                    ensure_column(c, lab)       # adds it to the column list and to EVERY customer table
                    added.append(lab)
            rows = c.execute("SELECT db_name, label FROM column_registry ORDER BY pos, db_name").fetchall()
            first = [r for lab in ALWAYS_COLUMNS for r in rows if r["label"].lower() == lab.lower()]
            ids = {r["db_name"] for r in first}
            for i, r in enumerate(first + [r for r in rows if r["db_name"] not in ids], 1):
                c.execute("UPDATE column_registry SET pos=%s WHERE db_name=%s", (i, r["db_name"]))
        if added:
            print("  note: added the standard column(s): " + ", ".join(added))
    except Exception as e:
        print(f"  note: the standard columns could not be checked: {e}")


def prune_empty_columns():
    """Drop every column (except Device Sr No, IMEI, ICCID) that has NO value in any customer table. Columns with data are kept.
    config.py PRUNE_EMPTY_COLUMNS: "once" (default: first start only) | "always" (every start) | "off"."""
    mode = str(getattr(config, "PRUNE_EMPTY_COLUMNS", "once")).lower()
    if mode == "off":
        return
    try:
        with reader() as c:
            if mode != "always" and scalar(c, "SELECT v FROM app_state WHERE k='pruned_empty_columns'"):
                return
            labels = [x["label"] for x in get_columns(c) if x["db"] not in STANDARD_DB and x["label"].lower() not in ALWAYS_LOWER]
        empty = [x["label"] for x in delete_columns(labels, dry_run=True)["columns"] if x["filled"] == 0] if labels else []
        if empty:
            delete_columns(empty)
            print("  note: dropped empty column(s): " + ", ".join(empty))
        with tx() as c:
            c.execute("REPLACE INTO app_state(k,v) VALUES('pruned_empty_columns','1')")
    except Exception as e:
        print(f"  note: empty columns were not removed: {e}")


# --------------------------------------------------------------------------- config.py <-> database mirror (two-way)
# DEFAULT_CUSTOMERS in config.py always lists the customers of the `customers` table (rewritten after every add /
# rename / import, and when MySQL is changed directly). You can ALSO edit that list by hand: a NEW name adds a
# customer, a CHANGED name renames that customer (MySQL + website follow within seconds). A name removed from the
# list is never deleted from MySQL - customers own device records, so nothing is deleted automatically.
CONFIG_PATH = os.path.abspath(config.__file__)
CONFIG_LOCK = threading.Lock()
RECON_LOCK = threading.Lock()
_H = [None]                       # fingerprint of the list that config.py and MySQL last agreed on
NOTE = {"msg": "", "at": 0.0}     # last thing worth telling the user (shown on the website for 2 minutes)
STATE = {"config_sync": "ok"}     # result of the last reconcile(), reported by bootstrap()


def names_hash(names):
    return hashlib.sha1(json.dumps(list(names), ensure_ascii=False).encode("utf-8")).hexdigest()


def _remember(names):
    h = names_hash(names)
    if _H[0] == h:
        return
    with tx() as c:
        c.execute("REPLACE INTO app_state(k,v) VALUES('config_hash',%s)", (h,))
    _H[0] = h


def config_customers():
    """The names currently written in config.py (None if the file cannot be read)."""
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "DEFAULT_CUSTOMERS" for t in node.targets):
                return list(ast.literal_eval(node.value))
    except Exception:
        pass
    return None


def sync_config(names=None):
    """Write the customer names into DEFAULT_CUSTOMERS in config.py (only if they differ). Returns "ok" or a message."""
    try:
        if names is None:
            with reader() as c:
                names = [r["name"] for r in c.execute("SELECT name FROM customers ORDER BY id").fetchall()]
        with CONFIG_LOCK:
            if config_customers() != names:
                with open(CONFIG_PATH, encoding="utf-8") as f:
                    text = f.read()
                tree = ast.parse(text)
                node = next((n for n in tree.body if isinstance(n, ast.Assign)
                             and any(getattr(t, "id", "") == "DEFAULT_CUSTOMERS" for t in n.targets)), None)
                body = "DEFAULT_CUSTOMERS = [" + ("\n" + "".join(f"    {json.dumps(n, ensure_ascii=False)},\n" for n in names) if names else "") + "]"
                lines = text.splitlines(keepends=True)
                if node:
                    lines[node.lineno - 1:node.end_lineno] = [body + "\n"]
                else:
                    lines += ["\n" if lines and lines[-1].endswith("\n") else "\n\n", body + "\n"]
                tmp = CONFIG_PATH + ".tmp"
                with open(tmp, "w", encoding="utf-8", newline="") as f:
                    f.write("".join(lines))
                os.replace(tmp, CONFIG_PATH)
                config.DEFAULT_CUSTOMERS = list(names)
        _remember(names)
        return "ok"
    except Exception as e:   # e.g. config.py is read-only - the database and website still work
        return f"config.py could not be updated: {e}"


def plan_config_edit(cfg, rows):
    """cfg = names now in config.py, rows = [{"id","name"}] from MySQL ordered by id.
    -> (renames [(id, new_name)], adds [name], gone [names missing from config.py])
    A name that changed at the same position as an old one is a RENAME; any other new name is an ADD."""
    clean, seen = [], set()
    for n in cfg:
        n = re.sub(r"\s+", " ", str(n)).strip()
        if n and n.casefold() not in seen:
            seen.add(n.casefold())
            clean.append(n)
    have = {r["name"].casefold() for r in rows}
    added = [n for n in clean if n.casefold() not in have]
    removed = [r for r in rows if r["name"].casefold() not in seen]
    renames, used_add, used_rem = [], set(), set()
    for i in range(min(len(clean), len(rows))):
        a, r = clean[i], rows[i]
        if a in added and r in removed and a not in used_add:
            renames.append((r["id"], a))
            used_add.add(a)
            used_rem.add(r["id"])
    return renames, [n for n in added if n not in used_add], [r["name"] for r in removed if r["id"] not in used_rem]


def reconcile():
    """MySQL is the single source of truth. Makes the customer list (registry) match the real customer tables,
    completes every customer table (columns + customer_name = table name), then mirrors the names into config.py
    (read-only: config.py is never written back into MySQL). Every step is separate, so one problem table can
    never stop the others from working. Returns "ok" or a short message."""
    with WRITE_LOCK, RECON_LOCK:
        msgs = []
        try:
            with tx() as c:
                m = sync_registry(c)
            if m:
                msgs.append(m)
        except Exception as e:
            msgs.append(f"customer list could not be synced: {e}")
        try:
            with tx() as c:
                register_unknown(c, customer_like_tables(c))
        except Exception as e:
            msgs.append(f"columns could not be registered: {e}")
        names = []
        try:
            with reader() as c:
                names = customer_names(c)
        except Exception as e:
            msgs.append(f"customer list could not be read: {e}")
        BROKEN.clear()
        for name in names:
            try:
                with tx() as c:
                    fix_table(c, name)
            except Exception as e:
                BROKEN[name] = str(e)
                msgs.append(f'table "{name}" cannot be used: {e}')
        text = " | ".join(msgs)
        if text:
            if text != NOTE.get("last"):
                print("  note:", text)
            NOTE.update(msg=text, at=time.time(), last=text)
        else:
            NOTE["last"] = ""
        res = sync_config()
        STATE["config_sync"] = NOTE["msg"] if NOTE["msg"] and time.time() - NOTE["at"] < 120 else res
        return STATE["config_sync"]


def synced(fn):
    """After a function that adds / renames customers has succeeded, mirror the names into config.py."""
    def wrapper(*a, **kw):
        out = fn(*a, **kw)
        msg = sync_config()
        if msg != "ok":
            print("  note:", msg)
        return out
    wrapper.__name__, wrapper.__doc__, wrapper.__wrapped__ = fn.__name__, fn.__doc__, fn
    return wrapper


# --------------------------------------------------------------------------- columns
def _col(r):
    return dict(db=r["db_name"], label=r["label"], mandatory=bool(r["is_mandatory"]), is_date=bool(r["is_date"]),
                standard=r["db_name"] in STANDARD_DB)


def get_columns(c):
    return [_col(r) for r in c.execute("SELECT * FROM column_registry ORDER BY pos, db_name")]


def find_column(c, label):
    r = c.execute("SELECT * FROM column_registry WHERE label=%s", (canon_label(label),)).fetchone()
    return _col(r) if r else None


def ensure_column(c, label):
    """Return (column, created). A column that does not exist yet is added to EVERY customer table."""
    label = canon_label(label)
    if not label:
        raise ValueError("Column name is empty")
    if len(label) > 60:
        raise ValueError("Column name is too long (max 60 characters)")
    if label.lower() in RESERVED_LABELS:
        raise ValueError(f'"{label}" is a reserved name - choose another column name')
    if not re.fullmatch(r"[\w .\-/()&#%+:]+", label):
        raise ValueError(f'Column name "{label}" has unsupported characters - use letters, numbers and spaces')
    col = find_column(c, label)
    if col:
        return col, False
    names = customer_names(c)
    taken = {r["db_name"].lower() for r in c.execute("SELECT db_name FROM column_registry")} | RESERVED_DB
    for t in names:
        taken |= {n.lower() for n in table_columns(c, t)}
    known = OPTIONAL_BY_LABEL.get(label.lower())
    name, is_date = (known if known and known[0] not in taken else (make_db_name(label, taken), 0))
    for t in names:
        c.execute(f"ALTER TABLE {q(t)} ADD COLUMN {q(name)} TEXT NULL")
    pos = int(scalar(c, "SELECT COALESCE(MAX(pos),0)+1 FROM column_registry"))
    c.execute("INSERT INTO column_registry(db_name,label,is_mandatory,is_date,pos) VALUES(%s,%s,0,%s,%s)", (name, label, is_date, pos))
    if name in REMOVED:   # e.g. the IMEI column was added back: duplicate checks apply again
        REMOVED.discard(name)
        _save_removed(c)
        _sync_unique()
    return dict(db=name, label=label, mandatory=False, is_date=bool(is_date)), True


def clean_fields(c, fields, cache, stats=None):
    """{label: value} -> {sql_column: value}. Creates unknown columns. `stats` = bulk mode (lenient)."""
    out = {}
    for k, v in (fields or {}).items():
        v = str(v if v is not None else "").strip()
        label = canon_label(k)
        if not v or not label:
            continue
        if stats is not None and label.lower() in RESERVED_LABELS:
            continue
        col = cache.get(label.lower())
        if col is None:
            col, created = ensure_column(c, label)
            cache[label.lower()] = col
            if created and stats is not None:
                stats["new_columns"].append(col["label"])
        if col["db"] in out:
            if stats is not None:
                continue
            raise ValueError(f"Duplicate column: {col['label']}")
        if col["is_date"]:
            iso = to_iso(v)
            if iso is None and stats is not None:
                stats["bad_dates"] += 1
            v = iso or v
        out[col["db"]] = v
    return out


# --------------------------------------------------------------------------- customers / devices
def lc(row):
    return {k.lower(): v for k, v in row.items()}


def val(v):
    return "" if v is None else str(v)


def targets(c, customer_id=None):
    """[{id, name}] of the customer tables to work on (all, or just one)."""
    real = {t.casefold() for t in _real_tables(c)}
    rows = [r for r in c.execute("SELECT id, name FROM customers ORDER BY name").fetchall()
            if r["name"].casefold() in real and r["name"] not in BROKEN]
    if customer_id not in (None, ""):
        rows = [r for r in rows if r["id"] == int(customer_id)]
    return rows


def locate(c, gid):
    """website record id -> (customer_id, row id, table name)"""
    cid, rid = divmod(int(gid), GID)
    r = c.execute("SELECT name FROM customers WHERE id=%s", (cid,)).fetchone()
    if not r:
        raise LookupError("Device record not found")
    return cid, rid, r["name"]


# These three columns must be DIFFERENT for every device, across ALL customers together.
_UNIQUE_ALL = [("device_sr_no", "Device Sr No"), ("imei", "IMEI"), ("iccid", "ICCID")]
UNIQUE = list(_UNIQUE_ALL)   # IMEI drops out of this list while the IMEI column is deleted


class DuplicateIMEI(ValueError):
    """A unique value (Device Sr No / IMEI / ICCID) is already in the database. Carries the details for the website's popup."""
    def __init__(self, value, owner, field="IMEI"):
        super().__init__(f"{field} {value} already exists under customer \"{owner['customer']}\" - not saved. "
                         f"A {field} can exist only once across all customers.")
        self.info = {"field": field, "value": value, "imei": owner.get("imei") or (value if field == "IMEI" else ""),
                     "customer": owner["customer"], "device_sr_no": owner.get("device_sr_no", "")}


class CustomerExists(ValueError):
    """A rename would give a customer the name of ANOTHER existing customer. Carries the details for the website's popup,
    which offers to merge the two customers instead (see merge_customers)."""
    def __init__(self, other, records):
        super().__init__(f'A customer named "{other["name"]}" already exists in the records')
        self.info = {"id": other["id"], "name": other["name"], "records": records}


def owner_of(c, col, value, exclude=None):
    """Where does this value of a unique column already live (ANY customer table)? -> {customer, device_sr_no, imei} or None"""
    for t in targets(c):
        for r in c.execute(f"SELECT * FROM {q(t['name'])} WHERE {q(col)}=%s", (value,)).fetchall():
            if exclude is None or t["id"] * GID + r["id"] != exclude:
                row = lc(r)
                return {"customer": t["name"], "device_sr_no": val(row.get("device_sr_no")), "imei": val(row.get("imei"))}
    return None


def unique_conflict(c, out, exclude=None):
    """out = {sql column: value}. Compare Device Sr No, IMEI and ICCID with every customer table. -> (label, value, owner) or None"""
    for col, label in UNIQUE:
        v = str(out.get(col) or "").strip()
        if v:
            o = owner_of(c, col, v, exclude)
            if o:
                return label, v, o
    return None


def _first_hit(vals, store):
    return next(((label, vals[col], store[col][vals[col].casefold()]) for col, label in UNIQUE
                 if vals[col] and vals[col].casefold() in store[col]), None)


def _dup_list(vals, seen, taken):
    """Every Device Sr No / ICCID / IMEI of one Excel row that is already used: first repeats inside the same file,
    then values already saved under ANY customer. -> [{field, value, where: file|database, row, customer, reason}]"""
    out = []
    for col, label in UNIQUE:
        v = vals.get(col, "")
        if v and v.casefold() in seen[col]:
            r = seen[col][v.casefold()]
            out.append({"field": label, "value": v, "where": "file", "row": r, "customer": "",
                        "reason": f'{label} "{v}" repeated in the file (first on row {r})'})
    for col, label in UNIQUE:
        v = vals.get(col, "")
        if v and v.casefold() in taken[col]:
            cu = taken[col][v.casefold()]
            out.append({"field": label, "value": v, "where": "database", "row": "", "customer": cu,
                        "reason": f'{label} "{v}" already saved under "{cu}"'})
    return out


def _taken_values(c):
    """{unique column: {value: customer}} for everything already saved, over every customer table"""
    taken = {col: {} for col, _ in UNIQUE}
    for t in targets(c):
        for col, _ in UNIQUE:
            for r in c.execute(f"SELECT {q(col)} AS v FROM {q(t['name'])} WHERE {q(col)} IS NOT NULL AND {q(col)}<>''").fetchall():
                taken[col].setdefault(str(r["v"]).strip().casefold(), t["name"])
    return taken


def get_or_create_customer(c, name):
    """A new customer = a new MySQL TABLE named after the customer (with the customer_name column built in)."""
    name = clean_name(name)
    r = c.execute("SELECT id, name FROM customers WHERE name=%s", (name,)).fetchone()
    if r:
        create_customer_table(c, r["name"])   # no-op when the table exists
        return r["id"], False
    create_customer_table(c, name)
    fix_table(c, name)
    return c.execute("INSERT INTO customers(name,created_at) VALUES(%s,%s)", (name, now())).lastrowid, True


def insert_device(c, cid, emp, out):
    cache = c.__dict__.setdefault("_cn", {})   # customer id -> table name, looked up once per import
    if cid not in cache:
        r = c.execute("SELECT name FROM customers WHERE id=%s", (cid,)).fetchone()
        if not r:
            raise LookupError("Customer not found")
        cache[cid] = r["name"]
    names = ["customer_name", "added_by", "added_on", *out.keys()]
    cur = c.execute(f"INSERT INTO {q(cache[cid])}({','.join(q(n) for n in names)}) VALUES({','.join(['%s'] * len(names))})",
                    [cache[cid], emp, today(), *out.values()])
    return cid * GID + cur.lastrowid


def _rename_core(c, changes, cur):
    """changes {customer_id: new name}, cur {customer_id: old name}. Renames the TABLES (through temporary names so
    swaps work), then the registry and the customer_name column. Undone completely if anything goes wrong."""
    tmp = {i: f"__renaming_{i}_{secrets.token_hex(3)}" for i in changes}
    now_name = {i: cur[i] for i in changes}

    def undo():
        for i in changes:
            if now_name[i] != cur[i]:
                try:
                    c.execute(f"RENAME TABLE {q(now_name[i])} TO {q(cur[i])}")
                    now_name[i] = cur[i]
                except pymysql.MySQLError:
                    pass
    try:
        for i in changes:
            c.execute(f"RENAME TABLE {q(now_name[i])} TO {q(tmp[i])}")
            now_name[i] = tmp[i]
        for i, n in changes.items():
            c.execute(f"RENAME TABLE {q(now_name[i])} TO {q(n)}")
            now_name[i] = n
        for i in changes:
            c.execute("UPDATE customers SET name=%s WHERE id=%s", (tmp[i], i))
        devices = 0
        for i, n in changes.items():
            c.execute("UPDATE customers SET name=%s WHERE id=%s", (n, i))
            c.execute(f"UPDATE {q(n)} SET customer_name=%s", (n,))
            devices += int(scalar(c, f"SELECT COUNT(*) FROM {q(n)}"))
        stored = {r["id"]: r["name"] for r in c.execute("SELECT id, name FROM customers").fetchall()}   # read back
        real = {t.casefold() for t in _real_tables(c)}
        drift = sum(int(scalar(c, f"SELECT COUNT(*) FROM {q(n)} WHERE BINARY customer_name <> BINARY %s", (n,)))
                    for n in changes.values())
        if any(stored.get(i) != n or n.casefold() not in real for i, n in changes.items()) or drift:
            raise ValueError("MySQL did not store all the new names")
        c.raw.commit()
        return devices
    except pymysql.err.IntegrityError:
        c.raw.rollback()
        undo()
        raise ValueError("Two customers would have the same name - choose different names")
    except BaseException as e:
        try:
            c.raw.rollback()
        except pymysql.MySQLError:
            pass
        undo()
        if isinstance(e, pymysql.MySQLError):
            raise ValueError(f"MySQL could not rename the table - nothing was changed ({e})")
        raise ValueError(f"{e} - nothing was changed") if isinstance(e, ValueError) else e


@synced
def rename_customer(cid, new_name):
    """Change a customer's name = rename its TABLE and update the customer_name column of every row in it."""
    new = clean_name(new_name)
    with tx() as c:
        r = c.execute("SELECT name FROM customers WHERE id=%s", (cid,)).fetchone()
        if not r:
            raise LookupError("Customer not found")
        if r["name"] == new:
            raise ValueError("The name is unchanged")
        for o in c.execute("SELECT id, name FROM customers WHERE id<>%s", (cid,)).fetchall():
            if o["name"].casefold() == new.casefold():   # MySQL table names may be case-insensitive, so compare that way
                try:
                    recs = int(scalar(c, f"SELECT COUNT(*) FROM {q(o['name'])}") or 0)
                except pymysql.MySQLError:
                    recs = 0
                raise CustomerExists(o, recs)
        n = _rename_core(c, {cid: new}, {cid: r["name"]})
        return {"id": cid, "old": r["name"], "name": new, "devices": n, "saved_in": DB_LABEL}


@synced
def merge_customers(source_id, target_id, source_name=None, target_name=None):
    """MERGE two customers: every record of the SOURCE customer is moved into the TARGET customer's table, then the
    (now empty) source customer is removed from the list. The target keeps its name. No record is lost: the row counts are
    checked before the source table is dropped, and if the source cannot be removed the copied rows are taken out again.
    source_name / target_name (what the person saw on screen) must still match, so a renamed customer is never merged by mistake."""
    try:
        source_id, target_id = int(source_id), int(target_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid customer in the request")
    if source_id == target_id:
        raise ValueError("Choose two different customers to merge")
    with tx() as c:
        src = c.execute("SELECT id, name FROM customers WHERE id=%s", (source_id,)).fetchone()
        tgt = c.execute("SELECT id, name FROM customers WHERE id=%s", (target_id,)).fetchone()
        if not src or not tgt:
            raise LookupError("Customer not found (it may have been renamed or deleted) - reload the page")
        for given, now_name in ((source_name, src["name"]), (target_name, tgt["name"])):
            if given is not None and str(given).strip() and str(given).strip() != now_name:
                raise ValueError(f'A customer is now called "{now_name}" - reload the page and try again. Nothing was merged.')
        exact = {t.casefold(): t for t in _real_tables(c)}
        for nm in (src["name"], tgt["name"]):
            if nm.casefold() not in exact or nm in BROKEN:
                raise ValueError(f'The MySQL table of "{nm}" is missing or cannot be used - nothing was merged')
        s_tab, t_tab = exact[src["name"].casefold()], exact[tgt["name"].casefold()]
        register_unknown(c, [s_tab])                          # a column only the source has becomes an app column ...
        fix_table(c, t_tab, repair_names=False)               # ... and both tables get exactly the same columns
        fix_table(c, s_tab, repair_names=False)
        t_cols = {n.lower(): n for n in table_columns(c, t_tab)}
        cols = [n for n in table_columns(c, s_tab) if n.lower() != "id" and n.lower() in t_cols]
        moving = int(scalar(c, f"SELECT COUNT(*) FROM {q(s_tab)}") or 0)
        before = int(scalar(c, f"SELECT COUNT(*) FROM {q(t_tab)}") or 0)
        top = int(scalar(c, f"SELECT COALESCE(MAX(id),0) FROM {q(t_tab)}") or 0)
        if moving:
            c.execute(f"INSERT INTO {q(t_tab)} ({','.join(q(t_cols[n.lower()]) for n in cols)}) "
                      f"SELECT {','.join(q(n) for n in cols)} FROM {q(s_tab)}")
            c.execute(f"UPDATE {q(t_tab)} SET customer_name=%s WHERE id>%s", (tgt["name"], top))
        after = int(scalar(c, f"SELECT COUNT(*) FROM {q(t_tab)}") or 0)
        if after != before + moving:
            raise ValueError("The records could not all be copied - nothing was merged")
        c.raw.commit()                                         # the records are safely in the target now
        try:
            c.execute(f"DROP TABLE {q(s_tab)}")
        except pymysql.MySQLError as e:                        # could not remove the source: take the copies back out again
            c.execute(f"DELETE FROM {q(t_tab)} WHERE id>%s", (top,))
            c.raw.commit()
            raise ValueError(f"MySQL could not remove the merged customer - nothing was changed ({e})")
        c.execute("DELETE FROM customers WHERE id=%s", (source_id,))
    BROKEN.pop(src["name"], None)
    _NAME_CHECKED.pop(s_tab, None)
    return {"merged": moving, "from": src["name"], "into": tgt["name"], "source_id": source_id, "target_id": target_id,
            "total": after, "saved_in": DB_LABEL}


@synced
def rename_customers(items):
    """Rename SEVERAL customers in one go. items = [{"id": 3, "name": "New name"}, ...]
    Each customer's table is renamed and its customer_name column updated. Swapping two names works too."""
    if not isinstance(items, list) or not items:
        raise ValueError("Nothing to rename")
    want = {}
    for it in items:
        try:
            cid = int(it.get("id"))
        except (TypeError, ValueError, AttributeError):
            raise ValueError("Invalid customer in the request")
        want[cid] = clean_name(it.get("name"))
    with tx() as c:
        cur = {r["id"]: r["name"] for r in c.execute("SELECT id, name FROM customers").fetchall()}
        if any(i not in cur for i in want):
            raise LookupError("Customer not found (it may have been deleted) - reload the page")
        changes = {i: n for i, n in want.items() if cur[i] != n}
        if not changes:
            raise ValueError("No names were changed")
        final = {i: changes.get(i, n) for i, n in cur.items()}
        seen = {}
        for i, n in final.items():   # MySQL table names may be case-insensitive, so compare that way
            k = n.casefold()
            if k in seen:
                raise ValueError(f'Two customers would have the same name: "{n}" / "{final[seen[k]]}"')
            seen[k] = i
        devices = _rename_core(c, changes, {i: cur[i] for i in changes})
        return {"renamed": len(changes), "devices": devices, "saved_in": DB_LABEL,
                "changes": [{"id": i, "old": cur[i], "name": n} for i, n in changes.items()]}


@synced
def create_device(emp, customer_id, new_customer, fields):
    with tx() as c:
        cid = None
        if new_customer:
            nm = clean_name(new_customer)
            if c.execute("SELECT 1 FROM customers WHERE name=%s", (nm,)).fetchone():
                raise ValueError("This customer already exists - select them from the list")
        else:
            r = c.execute("SELECT id FROM customers WHERE id=%s", (customer_id,)).fetchone()
            if not r:
                raise LookupError("Customer not found")
            cid = r["id"]
        cols = get_columns(c)
        out = clean_fields(c, fields, {x["label"].lower(): x for x in cols})
        if not out:
            raise ValueError("Add at least one column with a value")
        missing = [x["label"] for x in cols if x["mandatory"] and not out.get(x["db"])]
        if missing:
            raise ValueError("Mandatory column(s) missing: " + ", ".join(missing))
        hit = unique_conflict(c, out)   # Device Sr No, IMEI and ICCID are compared with every customer table
        if hit:   # checked BEFORE a new customer's table is created, so nothing is left behind
            raise DuplicateIMEI(hit[1], hit[2], hit[0])
        if cid is None:   # everything is valid -> now create the customer's table
            cid, _ = get_or_create_customer(c, nm)
        return {"id": insert_device(c, cid, emp, out), "customer_id": cid}


def _import_groups(emp, groups, on_duplicate=None):
    """Bulk import [{customer, rows:[{label:value}]}]. A customer that does not exist yet gets its own table; new
    columns in the file are added to every customer table.
    An IMEI can exist only ONCE in the whole database (all customers together). A row whose IMEI is already saved -
    under ANY customer - or repeated earlier in the same file is NOT inserted; every other row is. The skipped rows
    come back in `duplicates` so the website can show them.
    on_duplicate = "skip"    (default) keep the saved record exactly as it is
                   "replace" a row that matches a record already saved in the database UPDATES that record: every column the file
                             has a value for is overwritten (empty cells never erase anything; the record stays under its own customer)"""
    stats = {"new_columns": [], "bad_dates": 0}
    imported = missing_rows = new_customers = updated = unchanged = 0
    replace = on_duplicate == "replace"
    upd = []   # (customer table, unique sql column, value, row) - rows that overwrite a record already in the database
    seen, dups = set(), []
    groups = [g for g in (groups or []) if isinstance(g, dict) and g.get("rows")]
    for g in groups:
        g["customer"] = clean_name(g.get("customer"))   # validate every name before touching MySQL

    def pick(row, label):   # value of a column of an uploaded row, whatever the header was spelled like
        for k, v in (row or {}).items():
            if canon_label(k).lower() == label and str(v if v is not None else "").strip():
                return str(v).strip()
        return ""

    with tx() as c:
        # 1) every Device Sr No / IMEI / ICCID already stored, under any customer
        taken = {col: {k: (v, "database") for k, v in d.items()} for col, d in _taken_values(c).items()}
        # 2) decide row by row: a row matching ANY of the three columns is separated (skipped), every other row is inserted
        keep = []
        for g in groups:
            rows = []
            for row in g["rows"]:
                vals = {col: pick(row, label.lower()) for col, label in UNIQUE}
                hit = _first_hit(vals, taken)
                if hit and replace and hit[2][1] == "database":
                    upd.append((hit[2][0], next(col for col, label in UNIQUE if label == hit[0]), hit[1], row))
                    continue
                if hit:
                    dups.append({"imei": vals.get("imei", ""), "matched": hit[0], "value": hit[1], "customer": g["customer"], "exists_in": hit[2][0],
                                 "reason": "already saved in the database" if hit[2][1] == "database" else "repeated in the uploaded file",
                                 "device_sr_no": vals["device_sr_no"]})
                    continue
                for col, _ in UNIQUE:
                    if vals[col]:
                        taken[col][vals[col].casefold()] = (g["customer"], "file")
                rows.append(row)
            if rows:   # a customer whose rows were ALL duplicates is not created
                keep.append((g, rows))
        # MySQL commits on CREATE / ALTER TABLE, so do all of that FIRST - the inserts below then stay all-or-nothing.
        ids = []
        for g, _ in keep:
            cid, new = get_or_create_customer(c, g["customer"])
            new_customers += 1 if new else 0
            ids.append(cid)
        cols = get_columns(c)
        cache = {x["label"].lower(): x for x in cols}
        for g, rows in keep + ([(None, [u[3] for u in upd])] if upd else []):   # new columns for the replacing rows too
            for row in rows:
                for k, v in (row or {}).items():
                    label = canon_label(k)
                    if not label or not str(v if v is not None else "").strip() or label.lower() in RESERVED_LABELS:
                        continue
                    if label.lower() not in cache:
                        col, created = ensure_column(c, label)
                        cache[label.lower()] = col
                        if created:
                            stats["new_columns"].append(col["label"])
        mand = [x["db"] for x in cols if x["mandatory"]]
        for (g, rows), cid in zip(keep, ids):
            seen.add(cid)
            for row in rows:
                out = clean_fields(c, row, cache, stats)
                if not out:
                    continue
                if any(not out.get(m) for m in mand):
                    missing_rows += 1
                insert_device(c, cid, emp, out)
                imported += 1
        for table, col, value, row in upd:   # on_duplicate = "replace": overwrite the saved record with the file's values
            rec = c.execute(f"SELECT * FROM {q(table)} WHERE {q(col)}=%s LIMIT 1", (value,)).fetchone()
            if not rec:
                continue
            cur = lc(rec)
            out = {k: v for k, v in clean_fields(c, row, cache, stats).items() if k not in ("customer_name", "added_by", "added_on")}
            out = {k: v for k, v in out.items() if val(cur.get(k.lower())) != str(v)}   # only what really changes
            if not out:
                unchanged += 1
                continue
            # a new Device Sr No / IMEI / ICCID must not already belong to ANOTHER record (checked in memory, no extra queries)
            clash = next(((label, out[ucol]) for ucol, label in UNIQUE
                          if ucol in out and str(out[ucol]).strip().casefold() in taken[ucol]
                          and str(out[ucol]).strip().casefold() != val(cur.get(ucol)).strip().casefold()), None)
            if clash:
                owner = taken[next(u for u, l in UNIQUE if l == clash[0])][str(clash[1]).strip().casefold()]
                dups.append({"imei": value, "matched": clash[0], "value": clash[1], "customer": table, "exists_in": owner[0],
                             "reason": f'{clash[0]} "{clash[1]}" belongs to another record ({owner[0]}) - not replaced',
                             "device_sr_no": val(cur.get("device_sr_no"))})
                continue
            c.execute(f"UPDATE {q(table)} SET {','.join(q(k) + '=%s' for k in out)} WHERE id=%s", [*out.values(), rec["id"]])
            back = c.execute(f"SELECT {','.join(q(k) for k in out)} FROM {q(table)} WHERE id=%s", (rec["id"],)).fetchone()   # read back from MySQL
            back = lc(back) if back else {}
            if any(val(back.get(k.lower())) != str(v) for k, v in out.items()):
                raise ValueError(f"MySQL did not store the new values for {table} ({col} {value}) - the upload was cancelled and nothing was changed")
            for ucol, _ in UNIQUE:   # the record's new unique values are taken from now on
                if ucol in out:
                    taken[ucol][str(out[ucol]).strip().casefold()] = (table, "file")
            updated += 1
    return {"imported": imported, "updated": updated, "unchanged": unchanged, "skipped": len(dups), "duplicates": dups, "customers": len(seen),
            "new_customers": new_customers, "new_columns": stats["new_columns"],
            "bad_dates": stats["bad_dates"], "missing_mandatory": missing_rows}



def wipe_customer_data():
    """PERMANENTLY delete every customer AND everything in the Cart: all customer tables are dropped (the records are gone,
    not moved to the Cart), the customer list is emptied, every Cart item and its saved table is erased, and config.py's
    customer list is emptied so nothing comes back by itself.
    Users, logins, the Login Inventory and the column list are not touched."""
    with WRITE_LOCK, RECON_LOCK:
        with tx() as c:
            tables = customer_like_tables(c)
            records = sum(int(scalar(c, f"SELECT COUNT(*) FROM {q(t)}") or 0) for t in tables)
            customers = int(scalar(c, "SELECT COUNT(*) FROM customers") or 0)
            cart = int(scalar(c, "SELECT COUNT(*) FROM trash_bin") or 0)
            for t in tables:
                c.execute(f"DROP TABLE {q(t)}")      # MySQL commits a DROP immediately
            for t in [x for x in _real_tables(c) if x.casefold().startswith(TRASH_PREFIX.casefold())]:
                c.execute(f"DROP TABLE {q(t)}")      # the saved tables of customers that were in the Cart
            c.execute("DELETE FROM customers")
            c.execute("DELETE FROM trash_bin")
        BROKEN.clear()
        sync_config([])
    return {"customers": max(customers, len(tables)), "records": records, "cart": cart}


@synced
def import_groups(emp, groups, on_duplicate=None, replace_all=False):
    """Bulk import (see _import_groups). With replace_all=True every existing customer, record and Cart item is deleted first and
    the file becomes the whole database. The names are checked BEFORE anything is deleted, and an upload with no rows never deletes."""
    if not replace_all:
        return _import_groups(emp, groups, on_duplicate)
    ok = [g for g in (groups or []) if isinstance(g, dict) and g.get("rows")]
    if not ok:
        raise ValueError("The file has no rows to upload - nothing was deleted")
    for g in ok:
        clean_name(g.get("customer"))                # a bad customer name stops everything while the old data is still there
    with WRITE_LOCK:                                 # the background checker cannot recreate tables between the wipe and the import
        wiped = wipe_customer_data()
        out = _import_groups(emp, ok, on_duplicate)
    out["wiped"] = wiped
    return out


# ---------------------------------------------------------------- "Upload by Sheet Name" (limited-use feature)
SHEET_UPLOAD_LIMIT = 2                  # how many times it may be used; after that the button disappears from the website
SHEET_UPLOAD_KEY = "sheet_upload_used"  # counter kept in app_state, so it survives restarts and is shared by every user
SHEET_LOCK = threading.Lock()


def sheet_upload_left():
    """Uses still available (0 = the feature is gone)."""
    with reader() as c:
        used = int(scalar(c, "SELECT v FROM app_state WHERE k=%s", (SHEET_UPLOAD_KEY,)) or 0)
    return max(SHEET_UPLOAD_LIMIT - used, 0)


def sheet_upload(emp, groups, finish=False, saved_before=False, on_duplicate="skip"):
    """Sheet-name upload: every group = one sheet, the sheet name is the customer. A missing customer is created in MySQL
    (its own table) and in the customer list. Rows already saved (Device Sr No / IMEI / ICCID) are skipped, never overwritten.
    The upload is sent in parts; the LAST part (finish=True) uses up one of the allowed uses, but only if the upload saved at least
    one record or replaced one (in this part, or in an earlier one: saved_before=True). An upload of nothing but duplicates costs nothing."""
    with SHEET_LOCK:
        if sheet_upload_left() <= 0:
            raise ValueError("This upload feature has already been used the maximum number of times and is no longer available")
        out = import_groups(emp, groups, "replace" if on_duplicate == "replace" else "skip", False)
        if finish and (saved_before or out.get("imported") or out.get("updated")):
            with tx() as c:
                used = int(scalar(c, "SELECT v FROM app_state WHERE k=%s", (SHEET_UPLOAD_KEY,)) or 0)
                c.execute("REPLACE INTO app_state(k,v) VALUES(%s,%s)", (SHEET_UPLOAD_KEY, str(used + 1)))
    out["left"] = sheet_upload_left()
    return out


def _label_problem(label):
    """Why a NEW column could not be created with this name (None = fine). Same rules as ensure_column()."""
    if len(label) > 60:
        return "column name is too long (max 60 characters)"
    if label.lower() in RESERVED_LABELS:
        return f'"{label}" is a reserved column name'
    if not re.fullmatch(r"[\w .\-/()&#%+:]+", label):
        return f'column name "{label}" has unsupported characters'
    return None


def bulk_validate(rows, replace_all=False):
    """Bulk Upload preview. rows = [{"customer": name, "src": excel row no, "fields": {label: value}}].
    Checks every row WITHOUT writing anything and says: valid / duplicate / invalid (+ why).
      invalid   : bad customer name, no IMEI, a date column that is not a date, a value longer than 255 characters,
                  a new column whose name cannot be created
      duplicate : the IMEI is already saved (any customer) or repeats an earlier valid row of the same file
    replace_all : the upload deletes every existing customer first, so nothing already saved counts as a duplicate"""
    if not isinstance(rows, list) or not rows:
        raise ValueError("No rows to check")
    with reader() as c:
        cols = {x["label"].lower(): x for x in get_columns(c)}
        existing = set() if replace_all else {r["name"].casefold() for r in c.execute("SELECT name FROM customers").fetchall()}
        taken = {col: {} for col, _ in UNIQUE} if replace_all else _taken_values(c)
    mand = [x["label"] for x in cols.values() if x["mandatory"]]
    seen, new_customers, new_columns, bad_label = {col: {} for col, _ in UNIQUE}, [], [], {}
    counts = {"valid": 0, "duplicate": 0, "invalid": 0}
    missing = 0
    out = []
    for i, row in enumerate(rows):
        row = row if isinstance(row, dict) else {}
        src = row.get("src", i + 2)
        reasons, name = [], None
        try:
            name = clean_name(row.get("customer"))
        except ValueError as e:
            reasons.append(str(e))
        fields = {}
        for k, v in (row.get("fields") or {}).items():
            v, label = str(v if v is not None else "").strip(), canon_label(k)
            if v and label and label not in fields:
                fields[label] = v
        for label, v in fields.items():
            col = cols.get(label.lower())
            if col:
                if col["is_date"] and to_iso(v) is None:
                    reasons.append(f'{col["label"]} "{v[:30]}" is not a valid date')
                elif col["mandatory"] and len(v) > 255:
                    reasons.append(f'{col["label"]} is longer than 255 characters')
            else:
                if label not in bad_label:
                    bad_label[label] = _label_problem(label)
                if bad_label[label]:
                    reasons.append(bad_label[label])
        imei = fields.get("IMEI", "")
        vals = {col: fields.get(label, "") for col, label in UNIQUE}
        # Bulk Upload: ICCID is the only required value (the website ignores rows without one) - an empty IMEI is not an error
        verdict = {"status": "valid", "reason": "", "exists_in": "", "dups": []}
        if reasons:
            verdict.update(status="invalid", reason="; ".join(dict.fromkeys(reasons)))
        elif (dups := _dup_list(vals, seen, taken)):   # file repeats first, then the database (all customers)
            verdict.update(status="duplicate", reason="; ".join(d["reason"] for d in dups), dups=dups,
                           exists_in=next((d["customer"] for d in dups if d["where"] == "database"), ""))
        else:
            for col, _ in UNIQUE:
                if vals[col]:
                    seen[col][vals[col].casefold()] = src
            if name and name.casefold() not in existing and name not in new_customers:
                new_customers.append(name)
            for label in fields:
                if label.lower() not in cols and label not in new_columns:
                    new_columns.append(label)
            if any(m not in fields for m in mand):
                missing += 1
        counts[verdict["status"]] += 1
        out.append(verdict)
    return {"rows": out, "total": len(rows), **counts, "new_customers": new_customers,
            "new_columns": new_columns, "missing_mandatory": missing}


def owned_columns(c, tname, cols):
    """The columns that belong to ONE customer: the 3 standard columns (Device Sr No / IMEI / ICCID) plus every column that has
    a value in at least one of that customer's records. A column that was added for another customer (and is empty here)
    is NOT part of this customer - it is not fetched, shown, edited or downloaded for them."""
    hit = _OWN.get(tname)
    if hit and time.time() - hit[0] < OWN_TTL:
        return hit[1]
    real = {n.lower() for n in table_columns(c, tname)}
    check = [x["db"] for x in cols if x["db"].lower() in real and x["db"] not in STANDARD_DB]
    own = {x["db"].lower() for x in cols if x["db"] in STANDARD_DB}
    for k in range(0, len(check), 60):   # one scan of the table per 60 columns
        part = check[k:k + 60]
        row = c.execute("SELECT " + ", ".join(f"COALESCE(MAX(TRIM({q(n)}) <> ''), 0) AS {q('c' + str(i))}" for i, n in enumerate(part))
                        + f" FROM {q(tname)}").fetchone()
        if row:
            vals = list(row.values())
            own |= {n.lower() for n, v in zip(part, vals) if v and int(v)}
    _OWN[tname] = (time.time(), own)
    return own


def record(row, cols, t, own=None):
    """own = set of SQL column names this customer uses (see owned_columns); None = every column."""
    row = lc(row)
    return {"id": t["id"] * GID + row["id"], "customer_id": t["id"], "customer": t["name"],
            "added_by": val(row.get("added_by")), "added_on": val(row.get("added_on")),
            "fields": {x["label"]: val(row.get(x["db"].lower())) for x in cols if own is None or x["db"].lower() in own}}


def list_devices(field="*", query="", customer_id=None):
    with reader() as c:
        cols = get_columns(c)
        query = (query or "").strip()
        cond, params, by_name = None, [], False
        if query:
            if field == "__cust":
                by_name = True
            else:
                if field in ("*", "", None):
                    exprs = [q("customer_name")] + [q(x["db"]) for x in cols]
                else:
                    col = find_column(c, field)
                    if not col:
                        raise ValueError("Unknown column: " + str(field))
                    exprs = [q(col["db"])]
                pat = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
                iso, conds = to_iso(query), []
                for e in exprs:   # 15-02-2026 also finds 2026-02-15
                    conds.append(e + LIKE)
                    params.append(pat)
                    if iso:
                        conds.append(e + " = %s")
                        params.append(iso)
                cond = "(" + " OR ".join(conds) + ")"
        out = []
        for t in targets(c, customer_id):
            if by_name and query.casefold() not in t["name"].casefold():
                continue
            sql = f"SELECT * FROM {q(t['name'])}" + (f" WHERE {cond}" if cond else "") + " ORDER BY id"
            own = owned_columns(c, t["name"], cols)
            out += [record(r, cols, t, own) for r in c.execute(sql, params).fetchall()]
        return out


def bulk_fetch(column, values, customer_id=None, sim_type=None):
    """Bulk Fetch: look up many values (e.g. a list of IMEIs) in ONE column, across every customer table (or one).
    `column` is any label from column_registry (so a column added later works with no code change), or "__cust"
    for the customer name. Matching is exact (case-insensitive); date columns also understand 15-02-2026 = 2026-02-15.
    `sim_type` "E-SIM" / "Plastic SIM" keeps only that kind of record: the SIM TYPE saved by Bulk Upload (a sheet with ICCID values is
    E-SIM, a sheet without any is Plastic SIM); a record that has no SIM TYPE falls back to: with an ICCID value = E-SIM, without = Plastic SIM.
    Returns every matching record untouched, plus the searched values that matched nothing (`not_found`)."""
    vals, seen = [], set()
    for v in values or []:
        v = str(v if v is not None else "").strip()
        if v and v.casefold() not in seen:
            seen.add(v.casefold())
            vals.append(v)
    if not vals:
        raise ValueError("The uploaded file has no values to search")
    if len(vals) > 100_000:
        raise ValueError("Too many values in one go (max 100,000) - split the file")
    by_name = column == "__cust"
    want = re.sub(r"[^a-z0-9]", "", str(sim_type or "").lower())   # "esim" / "plasticsim" / "" (= everything)

    def type_ok(rec):
        if not want:
            return True
        norm = lambda x: re.sub(r"[^a-z0-9]", "", str(x or "").lower())
        for k, v in rec["fields"].items():
            if norm(k) == "simtype" and str(v or "").strip():
                return norm(v) == want                     # the SIM TYPE saved at upload
        has = any(norm(k) in ("iccid", "ccidno") and str(v or "").strip() for k, v in rec["fields"].items())
        return (want == "esim") == bool(has)               # no SIM TYPE saved: decide by the ICCID value
    with reader() as c:
        cols = get_columns(c)
        col = None
        if not by_name:
            col = find_column(c, column)
            if not col:
                raise ValueError("Unknown column: " + str(column))
        norm = (lambda v: to_iso(v) or v) if col and col["is_date"] else (lambda v: v)
        keyed = {}                      # normalised value (casefolded) -> position in the uploaded list
        for i, v in enumerate(vals):
            keyed.setdefault(norm(v).casefold(), i)
        wanted = list(dict.fromkeys(norm(v) for v in vals))
        hits, found = set(), []         # found = (position, record)
        for t in targets(c, customer_id):
            own = owned_columns(c, t["name"], cols)
            if by_name:
                i = keyed.get(t["name"].casefold())
                if i is not None:
                    recs = [(i, rec) for rec in (record(r, cols, t, own) for r in c.execute(f"SELECT * FROM {q(t['name'])} ORDER BY id").fetchall()) if type_ok(rec)]
                    if recs:
                        hits.add(i)
                        found += recs
                continue
            for k in range(0, len(wanted), 1000):
                chunk = wanted[k:k + 1000]
                sql = f"SELECT * FROM {q(t['name'])} WHERE {q(col['db'])} IN ({','.join(['%s'] * len(chunk))}) ORDER BY id"
                for r in c.execute(sql, chunk).fetchall():
                    i = keyed.get(val(lc(r).get(col["db"].lower())).strip().casefold())
                    if i is None:       # MySQL treats e.g. e / é as equal; we only accept what was really asked for
                        continue
                    rec = record(r, cols, t, own)
                    if not type_ok(rec):
                        continue
                    hits.add(i)
                    found.append((i, rec))
    found.sort(key=lambda x: (x[0], x[1]["id"]))
    items = []
    for i, rec in found:
        rec["search_value"] = vals[i]
        items.append(rec)
    return {"items": items, "searched": len(vals), "found_values": len(hits),
            "not_found": [v for i, v in enumerate(vals) if i not in hits]}


def update_device(dev_id, fields):
    with tx() as c:
        cid, rid, tname = locate(c, dev_id)
        if not c.execute(f"SELECT 1 FROM {q(tname)} WHERE id=%s", (rid,)).fetchone():
            raise LookupError("Device record not found")
        sets, vals = [], []
        for label, v in (fields or {}).items():
            v = text(v)
            col = find_column(c, label)
            if not col:   # a column that does not exist yet is created (in every customer table) with this value for this entry
                if not v:
                    raise ValueError(f'Give a value for the new column "{label}"')
                col, _ = ensure_column(c, label)
            if col["mandatory"] and not v:
                raise ValueError(f"{col['label']} is mandatory and cannot be empty")
            owner = owner_of(c, col["db"], v, exclude=int(dev_id)) if v and col["db"] in {u[0] for u in UNIQUE} else None
            if owner:
                raise DuplicateIMEI(v, owner, col["label"])
            sets.append(f"{q(col['db'])}=%s")
            vals.append((to_iso(v) or v) if col["is_date"] else v)
        if not sets:
            raise ValueError("Nothing to update")
        c.execute(f"UPDATE {q(tname)} SET {','.join(sets)} WHERE id=%s", [*vals, rid])
        back = c.execute(f"SELECT {','.join(x.split('=')[0] for x in sets)} FROM {q(tname)} WHERE id=%s", (rid,)).fetchone()   # read back
        back = lc(back) if back else back
        if not back or any(val(back[x.split('=')[0].strip('`').lower()]) != str(v) for x, v in zip(sets, vals)):
            raise ValueError("MySQL did not store the change - nothing was changed")
        return {"id": dev_id, "saved_in": DB_LABEL}


# --------------------------------------------------------------------------- SIM data upload (provider file -> customers)
# An Excel file from a SIM provider (Sensorise, Taisys, Growspace, Iotivity, VI ...) holds ICCID, MSISDN1, MSISDN2, ACT DATE and
# EXP DATE.  Every customer record whose ICCID is in the file gets those values - whichever customer table it is in.
SIM_FIELDS = (("iccid", "ICCID", "iccid"), ("msisdn1", "MSISDN1", "MSISDN1"), ("msisdn2", "MSISDN2", "MSISDN2"),
              ("act", "ACT DATE", "activation_date"), ("exp", "EXP DATE", "expiry_date"),
              ("prov", "SIM PROVIDER", "sim_provider"))   # (key from the website, column label, default SQL name)
SAMPLE_MAX, NOT_FOUND_MAX = 300, 20000


def norm_iccid(v):
    """'8991 1000 ...' / 8.99E+18 text / '8991...F' -> the ICCID as plain text ('' if empty)."""
    t = re.sub(r"\s+", "", text(v))
    return t[:-2] if t.endswith(".0") else t


def iccid_key(v):
    """ICCIDs written with / without the last check digit still match: the first 19 characters identify the SIM."""
    t = norm_iccid(v).upper()
    return t[:19] if len(t) >= 19 else t


def clean_sim_rows(rows):
    """Provider rows -> ({iccid_key: {iccid, msisdn1, msisdn2, act, exp}}, stats). A later row for the same ICCID only fills what is still empty."""
    prov, st = {}, {"rows": 0, "skipped": 0, "duplicates": 0, "bad_dates": 0}
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        st["rows"] += 1
        iccid = norm_iccid(r.get("iccid"))
        if not iccid:
            st["skipped"] += 1
            continue
        d = {"msisdn1": norm_iccid(r.get("msisdn1")), "msisdn2": norm_iccid(r.get("msisdn2"))}
        for k in ("act", "exp"):
            raw = re.split(r"[T ](?=\d{1,2}:\d{2})", text(r.get(k)))[0]
            d[k] = to_iso(raw) or ""
            if raw and not d[k]:
                st["bad_dates"] += 1
        key = iccid_key(iccid)
        if key in prov:
            st["duplicates"] += 1
            for k, v in d.items():
                prov[key][k] = prov[key].get(k) or v
        else:
            prov[key] = {"iccid": iccid, **d}
    return prov, st


def plan_sim_updates(records, prov, cols, overwrite, keycount=None):
    """records: [(row id, iccid, {key: current value})] of ONE customer table; cols: {key} that exist (or will exist) there.
    A value that is the same as the provider's stays untouched; a different one is replaced (overwrite) or only filled in when empty.
    The ICCID itself is replaced (e.g. a missing check digit added) only when no other record in the database has the same SIM,
    so ICCIDs stay unique.
    Returns [(row id, {key: (old, new)})] for the records that match the provider data AND change; plus how many matched."""
    plan, matched = [], 0
    for rid, iccid, cur in records:
        p = prov.get(iccid_key(iccid))
        if not p:
            continue
        matched += 1
        ch = {}
        for key in cols:
            new, old = p.get(key) or "", cur.get(key) or ""
            if key == "iccid":
                old = norm_iccid(old)
                if not (new and new != old and overwrite and (keycount or {}).get(iccid_key(iccid)) == 1):
                    continue
            if new and new != old and (overwrite or not old):
                ch[key] = (old, new)
        if ch:
            plan.append((rid, ch))
    return plan, matched


def apply_sim_data(rows, overwrite=True, dry_run=False, provider=""):
    """Push ICCID / MSISDN1 / MSISDN2 / ACT DATE / EXP DATE (and the chosen SIM PROVIDER) from a provider file to EVERY customer record with the same ICCID.
    overwrite=True (default): a value that is different from the provider's is REPLACED, a value that is the same is left as it is.
    overwrite=False         : only empty values are filled (dates edited by hand are kept).
    dry_run=True    : nothing is saved - only reports what would change."""
    prov, st = clean_sim_rows(rows)
    if not prov:
        raise ValueError("No ICCID found in the file - check that the ICCID column is selected")
    provider = re.sub(r"\s+", " ", text(provider)).strip()[:100]
    if provider:   # the SIM provider picked on the website (e.g. TAISYS(VI+BSNL)) goes into the SIM PROVIDER column of every matched record
        for p in prov.values():
            p["prov"] = provider
    used = [f for f in SIM_FIELDS if any(p.get(f[0]) for p in prov.values())]
    if not [f for f in used if f[0] != "iccid"]:
        raise ValueError("The file has no MSISDN / activation date / expiry date values to apply (and no SIM provider was chosen)")
    by_key = {f[0]: f for f in SIM_FIELDS}
    seen, customers, sample, created = set(), [], [], []   # created = columns made now (dry run: the columns that WILL be made)
    matched_records = updated = 0

    def run(c):
        nonlocal matched_records, updated
        if not dry_run:   # the columns a provider file needs are created automatically (in every customer table)
            for _k, label, _d in used:
                col, made = ensure_column(c, label)
                if made:
                    created.append(label)
        colmap = {k: find_column(c, label) for k, label, _d in used}   # key -> registry column (None = not created yet)
        if dry_run:   # tell the website which columns the real run will create
            created.extend(label for k, label, _d in used if k != "iccid" and not colmap[k])
        keycount = {}   # how many records (all customers together) hold each SIM
        for t in targets(c):
            if "iccid" in {n.lower() for n in table_columns(c, t["name"])}:
                for r in c.execute(f"SELECT iccid FROM {q(t['name'])} WHERE iccid IS NOT NULL AND iccid<>''").fetchall():
                    k = iccid_key(lc(r)["iccid"])
                    keycount[k] = keycount.get(k, 0) + 1
        for t in targets(c):
            have = {n.lower() for n in table_columns(c, t["name"])}
            if "iccid" not in have:
                continue
            sql = {k: (colmap[k]["db"] if colmap[k] else dflt) for k, _l, dflt in used}   # SQL column of each field
            cols = list(sql)
            present = {k: v for k, v in sql.items() if v.lower() in have and k != "iccid"}   # (a column that is not created yet counts as empty)
            sel = ["id", "iccid"] + [q(v) for v in present.values()] + (["imei"] if "imei" in have else [])
            recs = []
            for r in c.execute(f"SELECT {', '.join(sel)} FROM {q(t['name'])} WHERE iccid IS NOT NULL AND iccid<>''").fetchall():
                r = lc(r)
                recs.append((r["id"], val(r["iccid"]), {"iccid": val(r["iccid"]), **{k: val(r.get(v.lower())) for k, v in present.items()}}, val(r.get("imei"))))
            plan, matched = plan_sim_updates([x[:3] for x in recs], prov, cols, overwrite, keycount)
            for _id, iccid, _cur, _imei in recs:
                if iccid_key(iccid) in prov:
                    seen.add(iccid_key(iccid))
            matched_records += matched
            updated += len(plan)
            if matched:
                fc = {}
                for _rid, ch in plan:
                    for k in ch:
                        fc[by_key[k][1]] = fc.get(by_key[k][1], 0) + 1   # how many records got each field
                customers.append({"name": t["name"], "matched": matched, "updated": len(plan), "fields": fc})
            info = {x[0]: (x[1], x[3]) for x in recs}
            for rid, ch in plan:
                if len(sample) < SAMPLE_MAX:
                    sample.append({"customer": t["name"], "iccid": info[rid][0], "imei": info[rid][1],
                                   "changes": {by_key[k][1]: list(v) for k, v in ch.items()}})
            if not dry_run:   # one UPDATE statement per set of changed columns
                groups = {}
                for rid, ch in plan:
                    groups.setdefault(tuple(sorted(ch)), []).append((rid, ch))
                for ks, items in groups.items():
                    c.executemany(f"UPDATE {q(t['name'])} SET " + ", ".join(f"{q(sql[k])}=%s" for k in ks) + " WHERE id=%s",
                                  [(*[ch[k][1] for k in ks], rid) for rid, ch in items])

    if dry_run:
        with reader() as c:
            run(c)
    else:
        with tx() as c:
            run(c)
    missing = [p["iccid"] for k, p in prov.items() if k not in seen]
    return {"dry_run": bool(dry_run), "provider_rows": st["rows"], "valid_iccids": len(prov), "skipped_rows": st["skipped"],
            "duplicate_iccids": st["duplicates"], "bad_dates": st["bad_dates"], "matched_iccids": len(seen),
            "matched_records": matched_records, "updated_records": updated, "unchanged_records": matched_records - updated,
            "customers": customers, "sample": sample, "created_columns": created,
            "not_found": missing[:NOT_FOUND_MAX], "not_found_total": len(missing)}


@synced
def delete_customer(cid, expected_name=None, emp=None):
    """Delete a customer = move it to the Cart. Its MySQL table is RENAMED to __trash_<id> (all device records are kept
    untouched, the table is hidden from the customer list) and the customer leaves the list.
    Restore brings it back; Delete permanently (Cart) drops the table.
    `expected_name` (what the person confirmed on screen) must still match, so a renamed / other customer is never moved.
    config.py (DEFAULT_CUSTOMERS) is rewritten afterwards by @synced, so the customer does not come back by itself."""
    emp = emp or {}
    with tx() as c:
        r = c.execute("SELECT name FROM customers WHERE id=%s", (cid,)).fetchone()
        if not r:
            raise LookupError("Customer not found (it may already be deleted) - reload the page")
        name = r["name"]
        if expected_name is not None and str(expected_name).strip() != name:
            raise ValueError(f'This customer is now called "{name}" - reload the page and try again. Nothing was deleted.')
        if "`" in name:
            raise ValueError("This table name cannot be deleted from the website")
        records, tid = 0, None
        exact = {t.casefold(): t for t in _real_tables(c)}
        if name.casefold() in exact:
            table = exact[name.casefold()]
            records = int(scalar(c, f"SELECT COUNT(*) FROM {q(table)}") or 0)
            tid = c.execute("INSERT INTO trash_bin(kind,name,label,records,data,deleted_by,deleted_by_name,deleted_at) "
                            "VALUES('customer',%s,%s,%s,NULL,%s,%s,%s)",
                            (name, name, records, emp.get("id", ""), emp.get("name", ""), now())).lastrowid
            c.execute(f"RENAME TABLE {q(table)} TO {q(TRASH_PREFIX + str(tid))}")   # MySQL commits a RENAME immediately
        c.execute("DELETE FROM customers WHERE id=%s", (cid,))
    BROKEN.pop(name, None)
    return {"deleted": cid, "name": name, "records": records, "trash_id": tid, "saved_in": DB_LABEL}


def delete_device(dev_id, emp=None):
    """Delete one record = copy it into the Cart (as JSON), then remove it from the customer's table."""
    emp = emp or {}
    with tx() as c:
        cid, rid, tname = locate(c, dev_id)
        r = c.execute(f"SELECT * FROM {q(tname)} WHERE id=%s", (rid,)).fetchone()
        if not r:
            raise LookupError("Device record not found (it may already be deleted)")
        row = lc(r)
        imei = val(row.get("imei"))
        label = imei or val(row.get("device_sr_no")) or val(row.get("iccid")) or f"Record #{rid}"
        data = {k: (None if v is None else str(v)) for k, v in row.items()}
        c.execute("INSERT INTO trash_bin(kind,name,label,records,data,deleted_by,deleted_by_name,deleted_at) "
                  "VALUES('record',%s,%s,1,%s,%s,%s,%s)",
                  (tname, label[:255], json.dumps(data, ensure_ascii=False), emp.get("id", ""), emp.get("name", ""), now()))
        c.execute(f"DELETE FROM {q(tname)} WHERE id=%s", (rid,))
        return {"deleted": dev_id, "imei": imei, "in_cart": True}


# --------------------------------------------------------------------------- Cart (deleted customers / records)
TRASH_PREFIX = "__trash_"   # a deleted customer's table; "__" tables are never shown as customers
CORE_DB = {"id", "customer_name", "added_by", "added_on"}


def list_trash():
    with reader() as c:
        rows = c.execute("SELECT id,kind,name,label,records,deleted_by,deleted_by_name,deleted_at "
                         "FROM trash_bin ORDER BY id DESC").fetchall()
    return [{"id": r["id"], "kind": r["kind"], "customer": r["name"], "label": r["label"], "records": r["records"],
             "deleted_by": r["deleted_by_name"] or r["deleted_by"] or "", "deleted_at": r["deleted_at"]} for r in rows]


def trash_view(tid, limit=500):
    """The data of one Cart item: {columns, rows, total, shown}. A customer shows up to `limit` of its records."""
    with reader() as c:
        t = c.execute("SELECT * FROM trash_bin WHERE id=%s", (tid,)).fetchone()
        if not t:
            raise LookupError("This item is no longer in the Cart - reload the page")
        cols = get_columns(c)
        out = {"id": t["id"], "kind": t["kind"], "name": t["name"], "label": t["label"], "total": t["records"]}
        if t["kind"] == "record":
            data = json.loads(t["data"] or "{}")
            out.update(columns=[x["label"] for x in cols], rows=[[val(data.get(x["db"])) for x in cols]], shown=1)
            return out
        tt = TRASH_PREFIX + str(t["id"])
        if tt.casefold() not in {x.casefold() for x in _real_tables(c)}:
            out.update(columns=[], rows=[], shown=0, missing=True)
            return out
        have = {n.lower() for n in table_columns(c, tt)}
        show = [x for x in cols if x["db"].lower() in have]
        rows = c.execute(f"SELECT * FROM {q(tt)} ORDER BY id LIMIT %s", (int(limit),)).fetchall()
        out.update(columns=[x["label"] for x in show],
                   rows=[[val(lc(r).get(x["db"].lower())) for x in show] for r in rows], shown=len(rows))
        return out


def _restore_record(c, t):
    data = json.loads(t["data"] or "{}")
    r = c.execute("SELECT name FROM customers WHERE name=%s", (t["name"],)).fetchone()
    if not r:
        raise ValueError(f'The customer "{t["name"]}" does not exist any more. Restore the customer first '
                         f'(if it is in the Cart) or add it again, then restore this record.')
    tname = r["name"]
    have = {n.lower() for n in table_columns(c, tname)}
    out = {k.lower(): v for k, v in data.items() if k.lower() in have and k.lower() != "id"}   # columns deleted meanwhile are skipped
    hit = unique_conflict(c, out)   # Device Sr No / IMEI / ICCID must still be unique across every customer
    if hit:
        raise DuplicateIMEI(hit[1], hit[2], hit[0])
    out["customer_name"] = tname
    names = list(out)
    c.execute(f"INSERT INTO {q(tname)}({','.join(q(n) for n in names)}) VALUES({','.join(['%s'] * len(names))})", list(out.values()))
    return {"restored": "record", "name": tname, "label": t["label"], "records": 1}


def _restore_customer(c, t):
    name, tt = t["name"], TRASH_PREFIX + str(t["id"])
    real = {x.casefold() for x in _real_tables(c)}
    if tt.casefold() not in real:
        raise LookupError(f'The saved table of "{name}" is not in MySQL any more, so it cannot be restored. '
                          f'Delete it permanently to clear it from the Cart.')
    if name.casefold() in real or c.execute("SELECT 1 FROM customers WHERE name=%s", (name,)).fetchone():
        raise ValueError(f'A customer named "{name}" exists now. Rename or delete that customer first, then restore this one.')
    clean_name(name)
    in_trash = {n.lower() for n in table_columns(c, tt)}
    taken, bad = _taken_values(c), []   # values of the deleted customer that another customer uses now
    for col, label in UNIQUE:
        if col in in_trash:
            for r in c.execute(f"SELECT {q(col)} AS v FROM {q(tt)} WHERE {q(col)} IS NOT NULL AND {q(col)}<>''").fetchall():
                v = str(r["v"]).strip()
                if v.casefold() in taken[col]:
                    bad.append(f'{label} {v} (now under "{taken[col][v.casefold()]}")')
    if bad:
        raise ValueError(f'"{name}" cannot be restored: {len(bad)} value(s) are now used by other customers - '
                         + "; ".join(bad[:5]) + (" ..." if len(bad) > 5 else "") + ". Remove those duplicates first, then restore.")
    reg = {r["db_name"].lower() for r in c.execute("SELECT db_name FROM column_registry")}
    extra = [n for n in table_columns(c, tt) if n.lower() not in reg and n.lower() not in CORE_DB]   # columns deleted meanwhile stay deleted
    c.execute(f"RENAME TABLE {q(tt)} TO {q(name)}")
    try:
        c.execute("INSERT INTO customers(name,created_at) VALUES(%s,%s)", (name, now()))
        for n in extra:
            c.execute(f"ALTER TABLE {q(name)} DROP COLUMN {q(n)}")
        fix_table(c, name, repair_names=True)   # adds columns created while it was in the Cart
    except BaseException:
        try:
            c.execute(f"RENAME TABLE {q(name)} TO {q(tt)}")
        except pymysql.MySQLError:
            pass
        raise
    return {"restored": "customer", "name": name, "label": name, "records": t["records"]}


@synced
def restore_trash(tid, emp=None):
    with tx() as c:
        t = c.execute("SELECT * FROM trash_bin WHERE id=%s", (tid,)).fetchone()
        if not t:
            raise LookupError("This item is no longer in the Cart (already restored or deleted) - reload the page")
        res = _restore_record(c, t) if t["kind"] == "record" else _restore_customer(c, t)
        c.execute("DELETE FROM trash_bin WHERE id=%s", (tid,))
    return res


def purge_trash(tid, expected_name=None):
    """Delete permanently: a customer's saved table is DROPPED, a record's copy is erased. Cannot be undone."""
    with tx() as c:
        t = c.execute("SELECT * FROM trash_bin WHERE id=%s", (tid,)).fetchone()
        if not t:
            raise LookupError("This item is no longer in the Cart (already restored or deleted) - reload the page")
        if expected_name is not None and str(expected_name).strip() != t["name"]:
            raise ValueError("The Cart changed - reload the page and try again. Nothing was deleted.")
        if t["kind"] == "customer":
            tt = TRASH_PREFIX + str(t["id"])
            if tt.casefold() in {x.casefold() for x in _real_tables(c)}:
                c.execute(f"DROP TABLE {q(tt)}")   # MySQL commits a DROP immediately
        c.execute("DELETE FROM trash_bin WHERE id=%s", (tid,))
    return {"purged": tid, "kind": t["kind"], "name": t["name"], "label": t["label"], "records": t["records"]}


def alerts(days, after=None):
    """after=None : everything already expired or expiring within `days` days from today.
    after=N    : only devices expiring AFTER today+N days and up to N+`days` days from today."""
    base = date.today() + timedelta(days=after or 0)
    limit = (base + timedelta(days=days)).isoformat()
    cond, params = ("expiry_date <= %s", [limit]) if after is None else ("expiry_date > %s AND expiry_date <= %s", [base.isoformat(), limit])
    out = []
    with reader() as c:
        cols = get_columns(c)
        for t in targets(c):
            if "expiry_date" not in {n.lower() for n in table_columns(c, t["name"])}:
                continue   # no EXP DATE column in this customer's table
            rows = c.execute(f"""SELECT * FROM {q(t['name'])}
                WHERE expiry_date REGEXP '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$' AND {cond}""", params).fetchall()
            for r in rows:
                r = lc(r)
                try:
                    left = (date.fromisoformat(val(r["expiry_date"])) - date.today()).days
                except ValueError:
                    continue
                rec = record(r, cols, t)
                out.append({"id": rec["id"], "customer": rec["customer"], "fields": rec["fields"],
                            "iso": val(r["expiry_date"]), "left": left})
    out.sort(key=lambda x: (x["iso"], x["id"]))
    return out


# --------------------------------------------------------------------------- dashboard
def bootstrap(emp_id, sync=False):
    """Everything the dashboard needs. sync=True (the Refresh button) re-checks MySQL first; otherwise the
    background thread in app.py, which runs reconcile() every few seconds, keeps the customer list current."""
    cfg_state = reconcile() if sync else STATE["config_sync"]
    with reader() as c:
        cols = get_columns(c)
        custs, total, mine = [], 0, 0
        for t in targets(c):
            try:
                n = int(scalar(c, f"SELECT COUNT(*) FROM {q(t['name'])}"))
                m = int(scalar(c, f"SELECT COUNT(*) FROM {q(t['name'])} WHERE added_by=%s", (emp_id,)))
            except pymysql.MySQLError as e:
                BROKEN[t["name"]] = str(e)
                continue
            total += n
            mine += m
            custs.append({"id": t["id"], "name": t["name"], "count": n})
    shown = {t["name"].casefold() for t in custs}
    with reader() as c:
        hidden = [{"table": t, "why": BROKEN.get(t) or "not in the customer list yet - press Refresh in a few seconds"}
                  for t in customer_like_tables(c) if t.casefold() not in shown]
    return {"hidden": hidden, "db": f"{CFG['database']} on {CFG['host']}:{CFG['port']} (user {CFG['user']})", "config_file": CONFIG_PATH,
            "config_sync": cfg_state, "customers": custs, "columns": cols,
            "stats": {"customers": len(custs), "devices": total, "mine": mine, "columns": len(cols)},
            "sheet_upload_left": sheet_upload_left()}


# --------------------------------------------------------------------------- employees / sessions
def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt, hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()


def register(name, emp_id, password, role=None, allow_reserved=False):
    """One person = one username. Employee Name and Employee ID are both unique and can never be changed afterwards
    (there is no rename function anywhere - only the password can be changed, see change_password)."""
    name, emp_id, password = text(name), text(emp_id), str(password or "")
    if not name or not emp_id:
        raise ValueError("Employee name and ID are required")
    if len(name) > 255 or len(emp_id) > 100:
        raise ValueError("Employee name (max 255) or ID (max 100 characters) is too long")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    if not allow_reserved and config_role(emp_id) == "admin":   # website self-registration can never create an admin
        raise ValueError("This Employee ID is reserved for an administrator - it cannot be registered here. Ask an admin to add you.")
    if role not in (None, "admin", "standard", "limited"):
        raise ValueError("Unknown access level")
    salt, h = hash_pw(password)
    with tx() as c:
        if c.execute("SELECT 1 FROM employees WHERE emp_id=%s", (emp_id,)).fetchone():
            raise ValueError("This Employee ID is already registered - each person can have only one username")
        if c.execute("SELECT 1 FROM employees WHERE LOWER(name)=LOWER(%s)", (name,)).fetchone():
            raise ValueError("This Employee Name is already registered - each person can have only one username")
        c.execute("INSERT INTO employees(emp_id,name,salt,pass_hash,created_at,role) VALUES(%s,%s,%s,%s,%s,%s)",
                  (emp_id, name, salt, h, now(), role))


def create_member(name, emp_id, password, role="admin"):
    """Used by an admin (Manage Users > Add Member) and by add_user.py: the account gets `role` (default admin)."""
    register(name, emp_id, password, role=role, allow_reserved=True)
    return {"id": text(emp_id), "name": text(name), "role": role}


def check_user(name, emp_id):
    """Live 'already taken?' check for the registration form."""
    name, emp_id = text(name), text(emp_id)
    with reader() as c:
        nt = bool(name) and bool(c.execute("SELECT 1 FROM employees WHERE LOWER(name)=LOWER(%s)", (name,)).fetchone())
        it = bool(emp_id) and bool(c.execute("SELECT 1 FROM employees WHERE emp_id=%s", (emp_id,)).fetchone())
    return {"name_taken": nt, "id_taken": it}


def change_password(emp_id, current, new, token):
    """Change the password of a logged-in employee (needs the current password). Other devices are logged out."""
    current, new = str(current or ""), str(new or "")
    if len(new) < 6:
        raise ValueError("New password must be at least 6 characters")
    if new == current:
        raise ValueError("The new password must be different from the current one")
    with tx() as c:
        r = c.execute("SELECT * FROM employees WHERE emp_id=%s", (emp_id,)).fetchone()
        if not r or not hmac.compare_digest(hash_pw(current, r["salt"])[1], r["pass_hash"]):
            raise ValueError("Current password is incorrect")
        salt, h = hash_pw(new)
        c.execute("UPDATE employees SET salt=%s, pass_hash=%s WHERE emp_id=%s", (salt, h, emp_id))
        c.execute("DELETE FROM sessions WHERE emp_id=%s AND token<>%s", (emp_id, token))
    return {"ok": True}


def login(user, password):
    user, password = text(user), str(password or "")
    with reader() as c:   # the slow password hashing happens OUTSIDE the global write lock, so logins never stall other writes
        rows = c.execute("SELECT * FROM employees WHERE emp_id=%s OR name=%s", (user, user)).fetchall()
    for r in rows:
        if hmac.compare_digest(hash_pw(password, r["salt"])[1], r["pass_hash"]):
            token = secrets.token_urlsafe(32)
            with tx() as c:
                c.execute("DELETE FROM sessions WHERE expires_at < %s", (now(),))
                c.execute("INSERT INTO sessions(token,emp_id,expires_at) VALUES(%s,%s,%s)",
                          (token, r["emp_id"], (datetime.now() + timedelta(hours=12)).isoformat(sep=" ", timespec="seconds")))
            return token, {"id": r["emp_id"], "name": r["name"], "role": role_of(r["emp_id"], r["name"], r.get("role"))}
    raise PermissionError("Invalid Employee ID/Name or password")


def config_role(emp_id):
    """Role from config.ROLES by Employee ID only, else config.DEFAULT_ROLE."""
    roles = {str(k).strip().casefold(): str(v).strip().lower() for k, v in (getattr(config, "ROLES", {}) or {}).items()}
    r = roles.get(str(emp_id).strip().casefold()) or str(getattr(config, "DEFAULT_ROLE", "limited")).strip().lower()
    return r if r in ("admin", "standard", "staff", "limited") else "limited"


def role_of(emp_id, name, stored=None):
    """'admin' / 'standard' / 'limited'. A role stored by an admin (Add Member) wins; otherwise config.ROLES by ID; otherwise DEFAULT_ROLE.
    An unknown role word is treated as 'limited' (the safe side)."""
    if stored in ("admin", "standard", "limited"):
        return stored
    return config_role(emp_id)


def session_user(token):
    if not token:
        return None
    with reader() as c:
        r = c.execute("""SELECT e.emp_id, e.name, e.role FROM sessions s JOIN employees e ON e.emp_id=s.emp_id
                         WHERE s.token=%s AND s.expires_at > %s""", (token, now())).fetchone()
    return {"id": r["emp_id"], "name": r["name"], "role": role_of(r["emp_id"], r["name"], r.get("role"))} if r else None


def list_users():
    """Manage Users (admin): every registered employee."""
    with reader() as c:
        rows = c.execute("SELECT emp_id, name, created_at, role FROM employees ORDER BY name").fetchall()
    return [{"id": r["emp_id"], "name": r["name"], "created_at": r["created_at"] or "", "role": role_of(r["emp_id"], r["name"], r.get("role"))} for r in rows]


SUPER_ADMIN_ID = "0001"   # the only account that can remove users, and the only one that can never be removed


def delete_user(emp_id, actor_id):
    """Remove one employee account (and log that person out everywhere). Records they added stay in the customer tables."""
    emp_id = text(emp_id)
    if text(actor_id) != SUPER_ADMIN_ID:   # only the super admin may remove anyone
        raise ValueError("Only the main administrator (ID 0001) can remove users")
    if emp_id == SUPER_ADMIN_ID:           # nobody - not even 0001 himself - can remove ID 0001
        raise ValueError("The main administrator (ID 0001) cannot be removed")
    if emp_id == str(actor_id):
        raise ValueError("You cannot remove your own account")
    with tx() as c:
        r = c.execute("SELECT name FROM employees WHERE emp_id=%s", (emp_id,)).fetchone()
        if not r:
            raise LookupError("This user was not found (already removed?)")
        c.execute("DELETE FROM sessions WHERE emp_id=%s", (emp_id,))
        c.execute("DELETE FROM employees WHERE emp_id=%s", (emp_id,))
    return {"removed": emp_id, "name": r["name"]}


def logout(token):
    with tx() as c:
        c.execute("DELETE FROM sessions WHERE token=%s", (token,))


# --------------------------------------------------------------------------- login inventory (activity log)
def log_activity(emp_id, name, action, details="", ip=""):
    """Record who did what and when. Never raises - a logging problem must not break the real action."""
    try:
        with tx() as c:
            c.execute("INSERT INTO activity_log(emp_id,emp_name,action,details,ip,created_at) VALUES(%s,%s,%s,%s,%s,%s)",
                      (str(emp_id or "")[:100], str(name or "")[:255], str(action)[:60], str(details or "")[:4000], str(ip or "")[:64], now()))
    except Exception as e:
        print("  note: could not write activity log:", e)


def customer_label(cid):
    try:
        with reader() as c:
            r = c.execute("SELECT name FROM customers WHERE id=%s", (int(cid),)).fetchone()
        return r["name"] if r else f"#{cid}"
    except Exception:
        return f"#{cid}"


def list_activity(emp=None, action=None, date_from=None, date_to=None, search=None, limit=2000):
    """Newest first. Filters: employee id, action, date range (YYYY-MM-DD), free text."""
    where, p = [], []
    def add(cond, *params):
        where.append(cond)
        p.extend(params)

    if emp:
        add("emp_id=%s", emp)
    if action:
        add("action=%s", action)
    if date_from and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_from):
        add("created_at >= %s", date_from + " 00:00:00")
    if date_to and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_to):
        add("created_at <= %s", date_to + " 23:59:59")
    if search:
        like = "%" + str(search).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        add("(details LIKE %s OR emp_name LIKE %s OR emp_id LIKE %s OR action LIKE %s)", *[like] * 4)
    w = (" WHERE " + " AND ".join(where)) if where else ""
    limit = max(1, min(int(limit), 50000))
    with reader() as c:
        total = int(scalar(c, f"SELECT COUNT(*) FROM activity_log{w}", p) or 0)
        rows = c.execute(f"SELECT * FROM activity_log{w} ORDER BY created_at DESC, id DESC LIMIT {limit}", p).fetchall()
        emps = c.execute("SELECT emp_id, name FROM employees ORDER BY name").fetchall()
        acts = [r["action"] for r in c.execute("SELECT DISTINCT action FROM activity_log ORDER BY action").fetchall()]
        last = {r["emp_id"]: r for r in c.execute(
            "SELECT emp_id, MAX(created_at) AS t, COUNT(*) AS n FROM activity_log WHERE action='Login' GROUP BY emp_id").fetchall()}
    items = [{"id": r["id"], "emp_id": r["emp_id"], "name": r["emp_name"], "action": r["action"],
              "details": r["details"] or "", "ip": r["ip"] or "", "at": r["created_at"]} for r in rows]
    users = [{"emp_id": e["emp_id"], "name": e["name"], "last_login": (last.get(e["emp_id"]) or {}).get("t", ""),
              "logins": int((last.get(e["emp_id"]) or {}).get("n", 0))} for e in emps]
    return {"items": items, "total": total, "users": users, "actions": acts}


# --------------------------------------------------------------------------- delete columns
def delete_columns(labels, dry_run=False):
    """Delete one or many columns from EVERY customer table (and from the column list). Mandatory columns cannot be deleted, except IMEI
    (DELETABLE_MANDATORY). dry_run only reports how many filled values would be lost."""
    if not isinstance(labels, list) or not labels:
        raise ValueError("Select at least one column to delete")
    with (reader() if dry_run else tx()) as c:
        reg = {x["label"].lower(): x for x in get_columns(c)}
        plan = []
        for lab in dict.fromkeys(canon_label(l) for l in labels):
            col = reg.get(lab.lower())
            if not col:
                raise LookupError(f'Column "{lab}" does not exist (it may already be deleted) - reload the page')
            if col["label"].lower() in ALWAYS_LOWER:
                raise ValueError(f'"{col["label"]}" is one of the 12 standard columns every customer file must have and cannot be deleted')
            if col["db"] in STANDARD_DB and col["db"] not in DELETABLE_MANDATORY:   # the app's own queries use these columns
                raise ValueError(f'"{col["label"]}" is a standard column and cannot be deleted')
            plan.append(col)
        names = customer_names(c)
        info = []
        for col in plan:
            filled = 0
            for t in names:
                if col["db"].lower() in {n.lower() for n in table_columns(c, t)}:
                    filled += int(scalar(c, f"SELECT COUNT(*) FROM {q(t)} WHERE {q(col['db'])} IS NOT NULL AND {q(col['db'])}<>''") or 0)
            info.append({"label": col["label"], "filled": filled})
        if not dry_run:
            for col in plan:
                for t in names:   # MySQL commits each ALTER at once; everything was validated above
                    if col["db"].lower() in {n.lower() for n in table_columns(c, t)}:
                        c.execute(f"ALTER TABLE {q(t)} DROP COLUMN {q(col['db'])}")
                c.execute("DELETE FROM column_registry WHERE db_name=%s", (col["db"],))
                if col["mandatory"] and col["db"] in DELETABLE_MANDATORY:
                    REMOVED.add(col["db"])
            _save_removed(c)
            _sync_unique()
    return {"columns": info, "customers": len(names), "deleted": 0 if dry_run else len(plan)}
