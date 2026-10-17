#!/usr/bin/env python3
"""init_db.py - check the CustomerVault database and show what the app sees.   Run:  python init_db.py
If the website shows a server error, run this and read the output."""
import sys
import traceback

import database as db

try:
    db.init_db()
except Exception as e:
    print("\nSTARTUP FAILED:\n")
    traceback.print_exc()
    sys.exit(db.explain_connect_error(e))


def txt(v):
    return v.decode() if isinstance(v, bytes) else v


print(f"Database: {db.DB_LABEL}\n")
with db.reader() as c:
    have = {t.casefold() for t in db._real_tables(c)}
    print("System tables       :", ", ".join(f"{t} {'OK' if t in have else 'MISSING'}" for t in sorted(db.SYSTEM)))
    print("All tables in MySQL :", ", ".join(db._real_tables(c)))
    print("Customer tables     :", ", ".join(db.customer_like_tables(c)) or "(none)")
    print("Customer list (app) :", ", ".join(db.customer_names(c)) or "(none)")
    for name in db.customer_names(c):
        try:
            n = db.scalar(c, f"SELECT COUNT(*) FROM {db.q(name)}")
            print(f"\n[{name}]  {n} row(s)   columns: " + ", ".join(txt(r['Field']) for r in c.execute(f"SHOW COLUMNS FROM {db.q(name)}")))
        except Exception as e:
            print(f"\n[{name}]  PROBLEM: {e}")
print("\nTables the app cannot use:", db.BROKEN or "none")

for label, fn in (("bootstrap", lambda: db.bootstrap("x")), ("list_devices", lambda: db.list_devices()), ("alerts", lambda: db.alerts(30))):
    try:
        r = fn()
        print(f"OK  {label}" + (f": {len(r)} item(s)" if isinstance(r, list) else f": {len(r['customers'])} customer(s), {r['stats']['devices']} record(s)"))
    except Exception:
        print(f"FAILED  {label}:")
        traceback.print_exc()
