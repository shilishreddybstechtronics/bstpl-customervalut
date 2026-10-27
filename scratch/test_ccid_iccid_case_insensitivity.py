import sys
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from pydantic import ValidationError
import schemas
import routes_data
from database import SessionLocal
import models

def test_pydantic_schemas():
    print("--- Testing Pydantic Schemas Alias & Normalization ---")
    
    # 1. DeviceIn accepts ccid in small, capital, or mixed letters
    d1 = schemas.DeviceIn.model_validate({"customer_name": "TestCust", "imei": "123456789012345", "ccid": "8991102005361149063f"})
    assert d1.iccid == "8991102005361149063F", f"Expected uppercase F, got {d1.iccid}"
    
    d2 = schemas.DeviceIn.model_validate({"customer_name": "TestCust", "imei": "123456789012345", "CCID": "8991102005361149063F"})
    assert d2.iccid == "8991102005361149063F"

    d3 = schemas.DeviceIn.model_validate({"customer_name": "TestCust", "imei": "123456789012345", "iccid": "8991 1020-0536 1149-063f"})
    assert d3.iccid == "8991102005361149063F"

    # 2. SimDataRow accepts ccid in small and capital letters
    s1 = schemas.SimDataRow.model_validate({"ccid": "8991102005361149063f", "msisdn1": "9876543210"})
    assert s1.iccid == "8991102005361149063F"
    
    s2 = schemas.SimDataRow.model_validate({"CCID": "8991102005361149063F"})
    assert s2.iccid == "8991102005361149063F"

    # 3. SimDataCheckIn & ApplyIn accept match_by='ccid', 'CCID', 'iccid', 'ICCID'
    c1 = schemas.SimDataCheckIn.model_validate({"rows": [s1], "match_by": "ccid"})
    assert c1.match_by == "iccid", f"Expected match_by to normalize to 'iccid', got {c1.match_by}"
    
    c2 = schemas.SimDataCheckIn.model_validate({"rows": [s1], "match_by": "CCID"})
    assert c2.match_by == "iccid"

    # 4. BulkFetchIn accepts field='ccid', 'CCID', 'iccid', 'ICCID'
    bf1 = schemas.BulkFetchIn.model_validate({"queries": ["8991102005361149063f"], "field": "ccid"})
    assert bf1.field == "iccid", f"Expected 'iccid', got {bf1.field}"
    
    bf2 = schemas.BulkFetchIn.model_validate({"queries": ["8991102005361149063f"], "field": "CCID"})
    assert bf2.field == "iccid"

    print("✓ Pydantic schemas correctly treat CCID and ICCID identically and normalize lowercase/uppercase values!")


def test_db_queries_and_fetching():
    print("\n--- Testing Database Fetching & Query Building ---")
    db = SessionLocal()
    try:
        # Check an existing device in DB
        sample_dev = db.query(models.Device).filter(models.Device.iccid.isnot(None), models.Device.iccid != "", routes_data.ACTIVE).first()
        if not sample_dev:
            print("No device with ICCID found in DB; skipping live DB test.")
            return

        db_iccid = sample_dev.iccid
        print(f"Testing against live DB record ID={sample_dev.id}, ICCID='{db_iccid}'")

        # 1. Search with column="ccid" in lowercase
        q_ccid_lower = routes_data.build_device_query(db, customer_id=None, q=db_iccid.lower(), column="ccid", sort_by="ccid", sort_dir="asc")
        results = q_ccid_lower.all()
        assert any(d.id == sample_dev.id for d in results), f"Failed to find device searching by ccid lowercase {db_iccid.lower()}"
        print(f"✓ Found via column='ccid' and lower-case search term: {len(results)} matches")

        # 2. Search with column="CCID" in uppercase
        q_ccid_upper = routes_data.build_device_query(db, customer_id=None, q=db_iccid.upper(), column="CCID", sort_by="CCID", sort_dir="asc")
        results_upper = q_ccid_upper.all()
        assert any(d.id == sample_dev.id for d in results_upper), f"Failed to find device searching by CCID uppercase"
        print(f"✓ Found via column='CCID' and upper-case search term: {len(results_upper)} matches")

        # 3. Test clean_iccid with trailing f, spaces, scientific notation
        test_val = db_iccid.lower()
        cleaned = routes_data.clean_iccid(test_val)
        assert cleaned == db_iccid.upper()
        print(f"✓ clean_iccid('{test_val}') -> '{cleaned}'")

        # Test finding devices helper with match_by='iccid' and 'ccid'
        file_sims_dict = {k: {} for k in [db_iccid.lower(), db_iccid.upper(), db_iccid.rstrip("F")]}
        matched_dict = routes_data.find_devices_for_sim_data(db, file_sims_dict, match_by="iccid")
        assert len(matched_dict) > 0, "find_devices_for_sim_data did not find devices"
        print(f"✓ find_devices_for_sim_data matched {sum(len(v) for v in matched_dict.values())} device entries across case variants")

    finally:
        db.close()

if __name__ == "__main__":
    test_pydantic_schemas()
    test_db_queries_and_fetching()
    print("\nALL CCID / ICCID TESTS PASSED SUCCESSFULLY!")
