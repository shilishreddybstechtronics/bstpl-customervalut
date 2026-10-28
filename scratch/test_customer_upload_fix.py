import sys
import os
import re

# Use SQLite for standalone unit test
os.environ["DATABASE_URL"] = "sqlite:///scratch/test_upload.db"
sys.path.insert(0, "backend")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models, schemas, routes_data, customer_tables

# Setup test sqlite db
test_engine = create_engine("sqlite:///scratch/test_upload.db")
models.Base.metadata.create_all(bind=test_engine)
TestSession = sessionmaker(bind=test_engine)

def test_device_in_validation():
    print("Test 1: DeviceIn validation with None and scientific notation...")
    dev = schemas.DeviceIn(
        customer_name=None,
        imei=None,
        device_sr_no="SR-1.23E+04",
        iccid="8.991E+19",
        msisdn1="9876543210.0",
        extra={"custom_field": 12345, "status": "active"}
    )
    assert dev.customer_name == ""
    assert dev.imei == ""
    assert dev.iccid == "89910000000000000000"
    assert dev.msisdn1 == "9876543210"
    assert dev.extra == {"custom_field": "12345", "status": "active"}
    print("  DeviceIn validation passed successfully!")

def test_customer_resolution_and_push():
    print("\nTest 2: Customer matching (existing vs new)...")
    db = TestSession()
    
    # Pre-create an existing customer named "Tata_Motors"
    c_existing = models.Customer(name="Tata_Motors")
    db.add(c_existing)
    db.commit()
    print(f"  Created existing customer ID={c_existing.id}, Name='{c_existing.name}'")

    # Match sheet name "Tata Motors" (with space) -> should resolve to existing "Tata_Motors"
    c_matched = routes_data.customer_by_name(db, "Tata Motors")
    assert c_matched.id == c_existing.id, f"Expected matching existing ID {c_existing.id}, got {c_matched.id}"
    print(f"  Sheet name 'Tata Motors' successfully matched existing customer: ID={c_matched.id}, Name='{c_matched.name}'")

    # Match sheet name "tata_motors" (lowercase) -> should resolve to existing "Tata_Motors"
    c_matched_lower = routes_data.customer_by_name(db, "tata_motors")
    assert c_matched_lower.id == c_existing.id
    print(f"  Sheet name 'tata_motors' successfully matched existing customer: ID={c_matched_lower.id}")

    # Sheet name "Reliance_IoT" (NOT in database) -> should create a new customer
    c_new = routes_data.customer_by_name(db, "Reliance_IoT")
    assert c_new.id != c_existing.id
    assert c_new.name == "Reliance_IoT"
    print(f"  Sheet name 'Reliance_IoT' successfully created NEW customer: ID={c_new.id}, Name='{c_new.name}'")

    db.close()

def test_bulk_add_and_table_push():
    print("\nTest 3: Bulk add with existing customer and new customer...")
    db = TestSession()
    user = models.User(name="Test Admin", user_id="0001", password_hash="dummy")
    db.add(user)
    db.commit()

    rows = [
        # 2 records for existing customer "Tata Motors"
        schemas.DeviceIn(
            customer_name="Tata Motors",
            imei="11111222223333344444555", # 23 chars, will be truncated to 20
            device_sr_no="SR-TATA-01",
            iccid="8991001234567890",
            model="Model-X"
        ),
        schemas.DeviceIn(
            customer_name="Tata_Motors",
            imei="11111222223333344445",
            device_sr_no="SR-TATA-02",
            iccid="8991001234567891",
            model="Model-X"
        ),
        # 2 records for new customer "Adani_Power"
        schemas.DeviceIn(
            customer_name="Adani Power",
            imei="99999888887777766661",
            device_sr_no="SR-ADANI-01",
            iccid="8991009988776655",
            model="Model-Y"
        ),
        schemas.DeviceIn(
            customer_name="Adani_Power",
            imei="99999888887777766662",
            device_sr_no="SR-ADANI-02",
            iccid="8991009988776656",
            model="Model-Y"
        )
    ]

    bulk_in = schemas.BulkIn(rows=rows, mode="replace")
    result = routes_data.bulk_add(bulk_in, db=db, user=user)
    print("  Bulk Add Result:", result)
    assert result["added"] == 4, f"Expected 4 added, got {result['added']}"

    # Verify Tata_Motors devices
    c_tata = db.query(models.Customer).filter(models.Customer.name == "Tata_Motors").first()
    tata_devs = db.query(models.Device).filter(models.Device.customer_id == c_tata.id).all()
    assert len(tata_devs) == 2, f"Expected 2 devices for Tata_Motors, got {len(tata_devs)}"
    print(f"  Tata_Motors has {len(tata_devs)} devices pushed into its customer account!")

    # Verify Adani_Power customer was created and has 2 devices
    c_adani = db.query(models.Customer).filter(models.Customer.name == "Adani_Power").first()
    assert c_adani is not None, "Expected Adani_Power customer to be created"
    adani_devs = db.query(models.Device).filter(models.Device.customer_id == c_adani.id).all()
    assert len(adani_devs) == 2, f"Expected 2 devices for Adani_Power, got {len(adani_devs)}"
    print(f"  Adani_Power was created and has {len(adani_devs)} devices added to its customer account!")

    db.close()

if __name__ == "__main__":
    try:
        test_device_in_validation()
        test_customer_resolution_and_push()
        test_bulk_add_and_table_push()
        print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")
    finally:
        if os.path.exists("scratch/test_upload.db"):
            try:
                os.remove("scratch/test_upload.db")
            except Exception:
                pass

