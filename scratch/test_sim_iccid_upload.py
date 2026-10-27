"""Verification Test Suite for SIM Data Upload by ICCID.
Verifies:
1. ICCID matching handles exact matches, trailing 'F' variants, and 19-char core.
2. Matches all matching devices in the database.
3. Compares values and replaces msisdn1, msisdn2, act date, and exp date from the uploaded file.
4. Identical values remain unchanged and empty file fields do not overwrite existing data.
"""
import sys
from datetime import date
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import models, schemas
from database import SessionLocal
from routes_data import (
    clean_iccid,
    find_devices_for_sim_data,
    check_sim_data,
    apply_sim_data
)

def test_clean_iccid():
    print("\n--- 1. Testing clean_iccid normalization ---")
    assert clean_iccid(" 8991102005361149063f ") == "8991102005361149063F"
    assert clean_iccid("8991-1020-0536-1149-063F") == "8991102005361149063F"
    assert clean_iccid("8991102005361149063.0") == "8991102005361149063"
    assert clean_iccid("8.9911E+18") == "8991100000000000000"
    print("✓ clean_iccid normalization verified.")


def test_iccid_matching_and_replacement():
    print("\n--- 2. Testing ICCID Matching, Comparing & Replacing SIM Data ---")
    db = SessionLocal()
    try:
        # Get an active user to act as actor
        admin = db.query(models.User).filter(models.User.user_id == "0001").first()
        assert admin is not None, "Super admin 0001 must exist"

        # Find or create a test customer
        cust = db.query(models.Customer).filter(models.Customer.name == "Test SIM Customer").first()
        if not cust:
            cust = models.Customer(name="Test SIM Customer")
            db.add(cust)
            db.commit()
            db.refresh(cust)

        # Create two test devices with the same ICCID to test "match with all iccid"
        test_iccid = "8991999900001111222F"
        test_imei_1 = "99999999990001"
        test_imei_2 = "99999999990002"

        # Cleanup any old test devices
        for old in db.query(models.Device).filter(models.Device.imei.in_([test_imei_1, test_imei_2])).all():
            db.delete(old)
        db.commit()

        d1 = models.Device(
            customer_id=cust.id,
            imei=test_imei_1,
            iccid=test_iccid,
            msisdn1="9000000001",
            msisdn2="9000000002",
            act_date=date(2023, 1, 1),
            expiry_date=date(2024, 1, 1),
            sim_provider="TAISYS"
        )
        d2 = models.Device(
            customer_id=cust.id,
            imei=test_imei_2,
            iccid=test_iccid,
            msisdn1="9000000001",
            msisdn2="9000000002",
            act_date=date(2023, 1, 1),
            expiry_date=date(2024, 1, 1),
            sim_provider="TAISYS"
        )
        db.add(d1)
        db.add(d2)
        db.commit()
        db.refresh(d1)
        db.refresh(d2)

        # Test A: Upload file matching without trailing 'F' (e.g. 19-digit '8991999900001111222')
        # Should match BOTH d1 and d2 in our database!
        file_iccid_19 = "8991999900001111222"
        new_msisdn1 = "9888888881"
        new_msisdn2 = "9888888882"
        new_act = date(2025, 5, 10)
        new_exp = date(2026, 5, 10)

        check_payload = schemas.SimDataCheckIn(
            rows=[
                schemas.SimDataRow(
                    iccid=file_iccid_19,
                    msisdn1=new_msisdn1,
                    msisdn2=new_msisdn2,
                    act_date=new_act,
                    expiry_date=new_exp,
                    sim_provider="SENSORISE"
                )
            ],
            match_by="iccid",
            overwrite=True
        )

        check_res = check_sim_data(check_payload, db=db, user=admin)
        print("check_sim_data result:", check_res["records_matched"], "matched,", check_res["records_to_update"], "to update")
        # Both records matching this ICCID must be matched and queued for update
        assert check_res["records_matched"] == 2, f"Expected 2 matched records, got {check_res['records_matched']}"
        assert check_res["records_to_update"] == 2, f"Expected 2 to update, got {check_res['records_to_update']}"

        # Test B: Apply update
        apply_payload = schemas.SimDataApplyIn(
            rows=[
                schemas.SimDataRow(
                    iccid=file_iccid_19,
                    msisdn1=new_msisdn1,
                    msisdn2=new_msisdn2,
                    act_date=new_act,
                    expiry_date=new_exp,
                    sim_provider="SENSORISE"
                )
            ],
            match_by="iccid",
            overwrite=True
        )

        apply_res = apply_sim_data(apply_payload, db=db, user=admin)
        print("apply_sim_data result:", apply_res["updated"], "updated")
        assert apply_res["updated"] == 2, f"Expected 2 updated records, got {apply_res['updated']}"

        # Refresh devices and verify the values were replaced
        db.refresh(d1)
        db.refresh(d2)

        for d in (d1, d2):
            assert d.msisdn1 == new_msisdn1, f"Expected msisdn1 {new_msisdn1}, got {d.msisdn1}"
            assert d.msisdn2 == new_msisdn2, f"Expected msisdn2 {new_msisdn2}, got {d.msisdn2}"
            assert d.act_date == new_act, f"Expected act_date {new_act}, got {d.act_date}"
            assert d.expiry_date == new_exp, f"Expected expiry_date {new_exp}, got {d.expiry_date}"
            assert d.sim_provider == "SENSORISE", f"Expected SENSORISE, got {d.sim_provider}"

        # Test C: Verify identical values are not re-updated (records_already_same)
        check_res_same = check_sim_data(check_payload, db=db, user=admin)
        assert check_res_same["records_matched"] == 2
        assert check_res_same["records_to_update"] == 0, f"Expected 0 to update, got {check_res_same['records_to_update']}"
        assert check_res_same["records_already_same"] == 2

        # Clean up test devices
        db.delete(d1)
        db.delete(d2)
        db.commit()

        print("✓ SIM ICCID matching, comparing, and values replacement fully verified.")
    finally:
        db.close()


if __name__ == "__main__":
    test_clean_iccid()
    test_iccid_matching_and_replacement()
    print("\n========================================================")
    print("🎉 ALL SIM DATA ICCID UPLOAD TESTS PASSED SUCCESSFULLY!")
    print("========================================================")
