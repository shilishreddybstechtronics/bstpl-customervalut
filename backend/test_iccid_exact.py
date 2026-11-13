"""Checks that ICCID duplicates are decided on the WHOLE value only.
Run from the backend folder:  python test_iccid_exact.py
Uses a throw-away SQLite file, never your real database."""
import os, tempfile
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "iccid_test.db")

import models, schemas, routes_data as rd
from database import engine, SessionLocal

models.Base.metadata.create_all(engine)
db = SessionLocal()
A, B = "8991200050054843292F", "8991200050054843250F"


def row(i, ic, imei):
    return schemas.DeviceIn(customer_name="Cust_X", imei=imei, device_sr_no=f"SR{i}", iccid=ic)


assert rd.iccid_key(A) != rd.iccid_key(B), "one different digit must be a different ICCID"
assert rd.iccid_key(A) != rd.iccid_key(A[:-1]), "the trailing F is part of the number"
assert rd.iccid_key(" " + A.lower() + " ") == rd.iccid_key(A), "same whole value = same ICCID"

rows = [row(1, A, "111111111111111"), row(2, B, "222222222222222"),
        row(3, A, "333333333333333"), row(4, A[:-1], "444444444444444")]
res = rd.bulk_validate(schemas.BulkIn(rows=rows, mode="skip"), compact=True, db=db)
assert res["row_status"] == "NNDN", res["row_status"]          # only row 3 repeats a complete value

user = models.User(name="t", user_id="0001", password_hash="x", role="admin")
db.add(user); db.commit()
r1 = rd.bulk_add(schemas.BulkIn(rows=rows, mode="skip"), db, user)
assert r1["added"] == 3 and r1["skipped_duplicates"] == 1 and r1["skipped_detail"][0]["row"] == 2
r2 = rd.bulk_add(schemas.BulkIn(rows=[row(5, A, "555555555555555"), row(6, "8991200050054843251F", "666666666666666")],
                                mode="skip"), db, user)
assert r2["added"] == 1 and r2["skipped_detail"][0]["row"] == 0   # existing in DB = identical whole value only
print("ALL ICCID EXACT-MATCH CHECKS PASSED")
