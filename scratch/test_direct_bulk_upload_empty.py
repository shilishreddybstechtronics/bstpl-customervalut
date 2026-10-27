import sys
import os
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import schemas
import routes_data
from database import SessionLocal
import models

def test_direct_bulk_upload():
    print("--- 1. Testing Bulk Validate with direct_empty=True ---")
    
    unique_suffix = str(uuid.uuid4())[:8]
    test_cust = f"DirectCust_{unique_suffix}"
    test_imei = f"8600000{unique_suffix}"

    row_minimal = schemas.DeviceIn(
        customer_name=test_cust,
        imei=test_imei
        # all other columns intentionally omitted / None
    )

    data_val = schemas.BulkIn(
        rows=[row_minimal],
        mode="skip",
        direct_empty=True
    )

    db = SessionLocal()
    try:
        val_res = routes_data.bulk_validate(data_val, db=db)
        assert val_res["valid_count"] == 1, f"Expected 1 valid row, got {val_res}"
        assert "Device Sr No" not in val_res["missing_columns_warning"], "Device Sr No should not be in missing_columns_warning in direct_empty mode"
        print("✓ bulk_validate_devices passed without missing column warnings!")

        print("\n--- 2. Testing Bulk Add with direct_empty=True (All remaining columns left empty) ---")
        fake_user = models.User(id=1, name="Admin", user_id="admin01", is_admin=True, role="admin")

        add_res = routes_data.bulk_add(data_val, db=db, user=fake_user)
        print(f"bulk_add response: {add_res}")

        # Fetch inserted device from DB
        dev = db.query(models.Device).filter(models.Device.imei == test_imei).first()
        assert dev is not None, "Device was not inserted into DB!"
        
        print(f"Inserted Device ID={dev.id}, IMEI={dev.imei}, Customer={dev.customer.name}")
        
        # Verify that all remaining columns are None / empty
        assert dev.device_sr_no is None, f"Expected device_sr_no to be None, got {dev.device_sr_no}"
        assert dev.iccid is None, f"Expected iccid to be None, got {dev.iccid}"
        assert dev.msisdn1 is None, f"Expected msisdn1 to be None, got {dev.msisdn1}"
        assert dev.msisdn2 is None, f"Expected msisdn2 to be None, got {dev.msisdn2}"
        assert dev.act_date is None, f"Expected act_date to be None, got {dev.act_date}"
        assert dev.expiry_date is None, f"Expected expiry_date to be None (not auto-computed +365 days), got {dev.expiry_date}"
        assert dev.dispatched_date is None, f"Expected dispatched_date to be None, got {dev.dispatched_date}"
        assert dev.model is None, f"Expected model to be None, got {dev.model}"
        assert dev.sim_provider is None, f"Expected sim_provider to be None, got {dev.sim_provider}"
        assert dev.activation_plan is None, f"Expected activation_plan to be None, got {dev.activation_plan}"
        assert dev.firmware is None, f"Expected firmware to be None, got {dev.firmware}"
        assert dev.flash is None, f"Expected flash to be None, got {dev.flash}"
        assert dev.sim_type is None, f"Expected sim_type to be None, got {dev.sim_type}"
        assert dev.extra is None, f"Expected extra to be None, got {dev.extra}"

        print("✓ All remaining columns verified to be completely empty / NULL in database!")

        # Clean up test device and test customer
        cust_id = dev.customer_id
        db.delete(dev)
        cust = db.query(models.Customer).filter(models.Customer.id == cust_id).first()
        if cust and cust.name.startswith("DirectCust_"):
            db.delete(cust)
        db.commit()
        print("✓ Test cleanup completed.")

    finally:
        db.close()

if __name__ == "__main__":
    test_direct_bulk_upload()
    print("\nALL DIRECT BULK UPLOAD TESTS PASSED SUCCESSFULLY!")
