"""Run from the backend folder:  python check_db.py
Checks every table and column the dashboard needs and shows exactly which one fails."""
import traceback

from sqlalchemy import inspect

import models
import routes_activity as ra
import routes_data as r
from database import SessionLocal, engine

insp = inspect(engine)
tables = insp.get_table_names()
print("Tables in database:", tables, "\n")

for model in (models.User, models.Customer, models.Device, models.ColumnRegistry, models.ActivityLog):
    t = model.__table__
    if t.name not in tables:
        print(f"[PROBLEM] table '{t.name}' does not exist (start the server once and it is created)")
        continue
    have = {c["name"] for c in insp.get_columns(t.name)}
    want = {c.name for c in t.columns}
    missing = sorted(want - have)
    print(f"[{'PROBLEM' if missing else 'ok'}] {t.name}: missing columns = {missing or 'none'}; other columns in table = {sorted(have - want) or 'none'}")

print()
db = SessionLocal()
me = db.query(models.User).first()
checks = [
    ("stats", lambda: r.stats(db=db, user=me)),
    ("columns", lambda: r.columns(db=db)),
    ("customers", lambda: r.customers(db=db)),
    ("devices list", lambda: r.list_devices(customer_id=None, q="", page=1, page_size=100, db=db)),
    ("devices search", lambda: r.list_devices(customer_id=None, q="a", page=1, page_size=100, db=db)),
    ("expiry alerts", lambda: r.expiry_alerts(days=30, db=db)),
    ("bin", lambda: r.bin_list(db=db)),
    ("activity list", lambda: ra.list_activity(kind="all", who="", q="a", page=1, page_size=50, db=db, user=me)),
    ("activity summary", lambda: ra.summary(db=db, user=me)),
]
for name, fn in checks:
    try:
        fn()
        print(f"[ok] {name}")
    except Exception:
        db.rollback()
        print(f"[FAILED] {name}")
        print(traceback.format_exc().strip().splitlines()[-1][:400])
