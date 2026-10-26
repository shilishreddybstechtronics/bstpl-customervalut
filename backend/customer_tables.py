"""One SQL table per customer, created and filled automatically on bulk upload.

Put this file in the backend folder (next to routes_data.py).

How it works
- The main table `sim_devices` stays exactly as it is, so search, stats, export, bin and every other feature keep working.
- On top of that, every customer also gets its own table named  c<customer id>_<customer name>
  (example: c7_sharon, c12_simple_track).  Rows are inserted/updated there with the same upload.
- Extra CSV columns become real columns in the customer's table (prefixed x_).
- Re-uploading the same IMEI updates the row (no duplicates), because imei is the primary key of each table.

Back-fill existing data (run once from the backend folder):   python customer_tables.py
"""
import re
from datetime import date

from sqlalchemy import inspect, text

from database import engine

BASE_COLS = [
    ("customer_name", "VARCHAR(100)"),
    ("device_sr_no", "VARCHAR(50)"), ("iccid", "VARCHAR(30)"), ("msisdn1", "VARCHAR(20)"), ("msisdn2", "VARCHAR(20)"),
    ("act_date", "DATE"), ("expiry_date", "DATE"), ("dispatched_date", "DATE"), ("model", "VARCHAR(100)"),
    ("sim_provider", "VARCHAR(100)"), ("activation_plan", "VARCHAR(100)"), ("firmware", "VARCHAR(100)"),
    ("flash", "VARCHAR(100)"), ("sim_type", "VARCHAR(20)"),
]
BASE_NAMES = [c for c, _ in BASE_COLS]
CHUNK = 1000


SYSTEM_TABLES = {"customers", "sim_devices", "sim_activity_log", "sim_column_registry", "users"}


def slug(s: str, n: int = 64) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_]+", "_", (s or "").strip()).strip("_")
    return clean[:n] or "customer"


def table_name(cid: int, name: str) -> str:
    """Matches the exact customer name in database, cloud, and website."""
    base = slug(name)
    if base.lower() in SYSTEM_TABLES:
        return f"customer_{base}"
    return base


def extra_col(key: str) -> str:
    return "x_" + slug(key, 50).lower()


def find_table(conn, cid: int, name: str = ""):
    all_tables = inspect(conn).get_table_names()
    if name:
        target = table_name(cid, name)
        if target in all_tables:
            return target
        for t in all_tables:
            if t.lower() == target.lower():
                return t
    # Fallback to old format c<cid>_ if present
    prefix = f"c{cid}_"
    for t in all_tables:
        if t.startswith(prefix):
            return t
    return None


def ensure_table(conn, cid: int, name: str, extra_keys=()) -> str:
    """Creates the customer's table if missing, and adds any new extra columns. Returns the table name."""
    t = find_table(conn, cid, name)
    if not t:
        t = table_name(cid, name)
        cols = ",\n  ".join(f"`{c}` {ddl} NULL" for c, ddl in BASE_COLS)
        conn.execute(text(
            f"CREATE TABLE IF NOT EXISTS `{t}` (\n"
            f"  `imei` VARCHAR(20) NOT NULL PRIMARY KEY,\n  {cols},\n"
            f"  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP\n)"))
    have = {c["name"] for c in inspect(conn).get_columns(t)}
    for col_name, ddl in BASE_COLS:
        if col_name not in have:
            conn.execute(text(f"ALTER TABLE `{t}` ADD COLUMN `{col_name}` {ddl} NULL"))
            have.add(col_name)
    for k in extra_keys:
        col = extra_col(k)
        if col not in have:
            conn.execute(text(f"ALTER TABLE `{t}` ADD COLUMN `{col}` VARCHAR(500) NULL"))
            have.add(col)
    return t


def mirror_rows(items):
    """items: list of (customer_id, customer_name, row_dict). row_dict has imei, the BASE_NAMES, and 'extra' (dict).
    DDL in MySQL/TiDB commits by itself, so this runs on its own connection AFTER the main upload is committed."""
    by_cust = {}
    for cid, cname, row in items:
        row.setdefault("customer_name", cname)
        by_cust.setdefault((cid, cname), []).append(row)
    for (cid, cname), rows in by_cust.items():
        keys = sorted({k for r in rows for k in (r.get("extra") or {})})
        with engine.begin() as conn:
            t = ensure_table(conn, cid, cname, keys)
            cols = ["imei"] + BASE_NAMES + [extra_col(k) for k in keys]
            col_sql = ",".join(f"`{c}`" for c in cols)
            val_sql = ",".join(f":p{i}" for i in range(len(cols)))
            upd_sql = ",".join(f"`{c}`=VALUES(`{c}`)" for c in cols[1:])
            sql = text(f"INSERT INTO `{t}` ({col_sql}) VALUES ({val_sql}) ON DUPLICATE KEY UPDATE {upd_sql}")
            for i in range(0, len(rows), CHUNK):
                batch = []
                for r in rows[i:i + CHUNK]:
                    ex = r.get("extra") or {}
                    vals = [r.get("imei")] + [r.get(c) for c in BASE_NAMES] + [ex.get(k) for k in keys]
                    batch.append({f"p{j}": v for j, v in enumerate(vals)})
                try:
                    conn.execute(sql, batch)
                except Exception as be:
                    # If batch insert fails due to a bad value, insert row-by-row to ignore the bad value and proceed
                    for b_row in batch:
                        try:
                            conn.execute(sql, [b_row])
                        except Exception as row_err:
                            print(f"Skipping bad mirror row: {row_err}")


def rename_table(cid: int, new_name: str, old_name: str = ""):
    """Call after a customer is renamed so the table name follows in database and cloud."""
    with engine.begin() as conn:
        old = find_table(conn, cid, old_name)
        new = table_name(cid, new_name)
        if old and old != new:
            conn.execute(text(f"RENAME TABLE `{old}` TO `{new}`"))
            t_name = new
        elif old:
            t_name = old
        else:
            t_name = ensure_table(conn, cid, new_name)
        try:
            conn.execute(text(f"UPDATE `{t_name}` SET `customer_name` = :n"), {"n": new_name})
        except Exception as e:
            print(f"Customer table row name update error: {e}")


def drop_table(cid: int, name: str = ""):
    """Call when a customer is deleted forever."""
    with engine.begin() as conn:
        t = find_table(conn, cid, name)
        if t:
            conn.execute(text(f"DROP TABLE IF EXISTS `{t}`"))


def mirror_single_device(cid: int, cname: str, row: dict):
    """Mirrors a single device into the customer's individual table."""
    try:
        row.setdefault("customer_name", cname)
        mirror_rows([(cid, cname, row)])
    except Exception as e:
        print(f"Customer table mirror single device failed: {e}")


def delete_device_from_table(cid: int, imei: str, name: str = ""):
    """Removes a device from the customer's individual table."""
    try:
        with engine.begin() as conn:
            t = find_table(conn, cid, name)
            if t:
                conn.execute(text(f"DELETE FROM `{t}` WHERE `imei` = :i"), {"i": imei})
    except Exception as e:
        print(f"Customer table delete device failed: {e}")


def sync_all():
    """Copies every existing customer's active devices into their own table."""
    import models
    from database import SessionLocal
    db = SessionLocal()
    try:
        total = 0
        for c in db.query(models.Customer).filter(models.Customer.deleted_at.is_(None)).all():
            items = []
            for d in db.query(models.Device).filter(models.Device.customer_id == c.id, models.Device.deleted_at.is_(None)):
                row = {"imei": d.imei, "customer_name": c.name, "extra": d.extra or {}}
                row.update({f: getattr(d, f) for f in BASE_NAMES if f != "customer_name"})
                items.append((c.id, c.name, row))
            if items:
                mirror_rows(items)
            total += len(items)
            print(f"{c.name}: {len(items)} rows -> {table_name(c.id, c.name)}")
        print(f"Done. {total} rows copied.")
    finally:
        db.close()


if __name__ == "__main__":
    sync_all()
