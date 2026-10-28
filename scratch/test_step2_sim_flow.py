import sys
from pathlib import Path
import uuid
from datetime import date

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import models, schemas, customer_tables
from database import SessionLocal
from routes_data import check_sim_data, apply_sim_data

def run_test():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.role == "admin").first()
        test_uid = uuid.uuid4().hex[:6].upper()
        cust_name = f"Test_Cust_{test_uid}"

        # 1. Test check_sim_data with ICCID/CCID variations and dates
        test_rows = [
            schemas.SimDataRow(
                iccid=f"8991000{test_uid}01",
                msisdn1="9876543210",
                act_date="15-05-2024",
                expiry_date="15-05-2025",
                sim_provider="TAISYS (Airtel + BSNL)",
                extra={"Model": "VT01", "Batch": "B1"}
            ),
            schemas.SimDataRow(
                iccid=f"8991000{test_uid}02",
                msisdn1="9876543211",
                act_date="2024/06/20",
                expiry_date="2025/06/20",
                sim_provider="SENSORISE (VI + BSNL)",
                extra={"Model": "VT02"}
            )
        ]

        check_in = schemas.SimDataCheckIn(
            rows=test_rows,
            overwrite=True,
            match_by="iccid",
            sim_provider="TAISYS (Airtel + BSNL)"
        )

        res_check = check_sim_data(check_in, db, user)
        assert res_check["file_rows_count"] == 2, f"Expected 2 rows, got {res_check['file_rows_count']}"
        assert res_check["can_insert_count"] == 2, f"Expected 2 can_insert_count, got {res_check['can_insert_count']}"
        print(f"[PASS] check_sim_data verified: {res_check['can_insert_count']} records can be inserted.")

        # 2. Test apply_sim_data with action="insert_only"
        apply_in = schemas.SimDataApplyIn(
            rows=test_rows,
            overwrite=True,
            match_by="iccid",
            action="insert_only",
            insert_new=True,
            target_customer=cust_name
        )

        res_apply = apply_sim_data(apply_in, db, user)
        assert res_apply["inserted"] == 2, f"Expected 2 inserted, got {res_apply['inserted']}"
        print(f"[PASS] apply_sim_data insert_only verified: {res_apply['inserted']} inserted into '{cust_name}'.")

        # 3. Verify in database (sim_devices)
        inserted_devs = db.query(models.Device).filter(
            models.Device.iccid.in_([f"8991000{test_uid}01", f"8991000{test_uid}02"])
        ).all()
        assert len(inserted_devs) == 2, f"Expected 2 in sim_devices, found {len(inserted_devs)}"
        print("[PASS] Verified records exist in database sim_devices table.")

        # 4. Clean up test records
        for d in inserted_devs:
            db.delete(d)
        target_c = db.query(models.Customer).filter(models.Customer.name == cust_name).first()
        if target_c:
            db.delete(target_c)
        db.commit()
        print("[PASS] Cleaned up test data.")

    finally:
        db.close()

if __name__ == "__main__":
    run_test()
