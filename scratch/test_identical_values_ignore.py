import os
import sys
import uuid
from datetime import date
from sqlalchemy.orm import Session

from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from database import SessionLocal
import models, schemas
from routes_data import check_sim_data, apply_sim_data

def run_test():
    db: Session = SessionLocal()
    try:
        user = db.query(models.User).first()
        cust_name = f"Test_Cust_Ignore_{uuid.uuid4().hex[:6]}"
        cust = models.Customer(name=cust_name)
        db.add(cust)
        db.commit()
        db.refresh(cust)

        test_iccid_same = f"89910000{uuid.uuid4().hex[:10].upper()}"
        test_iccid_diff = f"89910000{uuid.uuid4().hex[:10].upper()}"
        test_iccid_new  = f"89910000{uuid.uuid4().hex[:10].upper()}"

        # Insert 2 existing devices into DB
        d_same = models.Device(
            customer_id=cust.id,
            imei=f"INV_{uuid.uuid4().hex[:10].upper()}",
            iccid=test_iccid_same,
            msisdn1="9876543210",
            msisdn2="9876543211",
            act_date=date(2025, 1, 15),
            sim_provider="TAISYS (Airtel + BSNL)"
        )
        d_diff = models.Device(
            customer_id=cust.id,
            imei=f"INV_{uuid.uuid4().hex[:10].upper()}",
            iccid=test_iccid_diff,
            msisdn1="9111111111",
            msisdn2="9222222222",
            act_date=date(2025, 1, 1),
            sim_provider="TAISYS (Airtel + BSNL)"
        )
        db.add_all([d_same, d_diff])
        db.commit()

        # Input rows:
        # Row 1: Exactly same values as in DB -> MUST BE IGNORED
        # Row 2: Differing values (new msisdn1) -> MUST BE UPDATED
        # Row 3: New ICCID -> MUST BE INSERTED
        check_in = schemas.SimDataCheckIn(
            rows=[
                schemas.SimDataRow(iccid=test_iccid_same, msisdn1="9876543210", msisdn2="9876543211", act_date=date(2025, 1, 15), sim_provider="TAISYS (Airtel + BSNL)"),
                schemas.SimDataRow(iccid=test_iccid_diff, msisdn1="9999999999", msisdn2="9222222222", act_date=date(2025, 1, 1), sim_provider="TAISYS (Airtel + BSNL)"),
                schemas.SimDataRow(iccid=test_iccid_new, msisdn1="9333333333", act_date=date(2025, 2, 1))
            ],
            overwrite=True,
            match_by="iccid"
        )
        chk_res = check_sim_data(check_in, db=db, user=user)
        assert chk_res["records_matched"] == 2, f"Expected 2 matched, got {chk_res['records_matched']}"
        assert chk_res["records_to_update"] == 1, f"Expected 1 differing, got {chk_res['records_to_update']}"
        assert chk_res["records_already_same"] == 1, f"Expected 1 already same, got {chk_res['records_already_same']}"
        assert chk_res["can_insert_count"] == 1, f"Expected 1 can insert, got {chk_res['can_insert_count']}"
        print("[PASS] Validation check verified: 2 matched, 1 differing, 1 identical ignored, 1 can insert.")

        # Now apply with action 'both'
        apply_in = schemas.SimDataApplyIn(
            rows=[
                schemas.SimDataRow(iccid=test_iccid_same, msisdn1="9876543210", msisdn2="9876543211", act_date=date(2025, 1, 15), sim_provider="TAISYS (Airtel + BSNL)"),
                schemas.SimDataRow(iccid=test_iccid_diff, msisdn1="9999999999", msisdn2="9222222222", act_date=date(2025, 1, 1), sim_provider="TAISYS (Airtel + BSNL)"),
                schemas.SimDataRow(iccid=test_iccid_new, msisdn1="9333333333", act_date=date(2025, 2, 1))
            ],
            overwrite=True,
            match_by="iccid",
            action="both",
            insert_new=True,
            target_customer=cust_name
        )
        app_res = apply_sim_data(apply_in, db=db, user=user)
        assert app_res["updated"] == 1, f"Expected 1 updated, got {app_res['updated']}"
        assert app_res["inserted"] == 1, f"Expected 1 inserted, got {app_res['inserted']}"
        assert app_res["already_same"] == 1, f"Expected 1 already same ignored, got {app_res['already_same']}"
        print("[PASS] Apply SIM data verified: 1 updated, 1 inserted, 1 identical ignored.")

        # Cleanup
        db.query(models.Device).filter(models.Device.customer_id == cust.id).delete()
        db.delete(cust)
        db.commit()
        print("[PASS] Test cleanup complete.")
    finally:
        db.close()

if __name__ == "__main__":
    run_test()
