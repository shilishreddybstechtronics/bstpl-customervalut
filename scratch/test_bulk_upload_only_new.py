import sys
import os

sys.path.insert(0, os.path.abspath('backend'))

from database import SessionLocal
import models
import routes_data
import schemas

def test_only_new_upload():
    print("=== Testing Bulk Upload: ONLY NEW ENTRIES UPLOAD ===")
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.user_id == "0001").first()
    if not user:
        user = db.query(models.User).first()
    assert user is not None, "A user must exist"

    # Pick or insert a test existing device
    existing_imei = "998877665544332"
    new_imei_1 = "889911223344551"
    new_imei_2 = "889911223344552"

    cust = routes_data.customer_by_name(db, "Test_Upload_Customer")

    # Ensure existing device exists in DB
    dev = db.query(models.Device).filter(models.Device.imei == existing_imei).first()
    if not dev:
        dev = models.Device(imei=existing_imei, customer_id=cust.id, model="TestModelOld")
        db.add(dev)
        db.commit()
    print(f"Existing device prepared: IMEI={existing_imei}")

    # Clean up test new devices if present
    db.query(models.Device).filter(models.Device.imei.in_([new_imei_1, new_imei_2])).delete(synchronize_session=False)
    db.commit()

    # Now create batch with: 1 existing device + 2 new devices
    batch_rows = [
        schemas.DeviceIn(customer_name="Test_Upload_Customer", imei=existing_imei, model="AttemptedOverwrite"),
        schemas.DeviceIn(customer_name="Test_Upload_Customer", imei=new_imei_1, model="NewModel1"),
        schemas.DeviceIn(customer_name="Test_Upload_Customer", imei=new_imei_2, model="NewModel2"),
    ]

    bulk_in = schemas.BulkIn(rows=batch_rows, mode="skip")

    # 1. Test validate
    val_res = routes_data.bulk_validate(bulk_in, db=db)
    print("Validate Result:", {
        "new_count": val_res.get("new_count"),
        "existing_count": val_res.get("existing_count"),
        "total_count": val_res.get("total_count"),
        "new_imeis": val_res.get("new_imeis"),
        "has_existing_imeis": existing_imei in val_res.get("existing_imeis", [])
    })

    assert val_res.get("new_count") == 2, f"Expected 2 new entries, got {val_res.get('new_count')}"
    assert existing_imei in val_res.get("existing_imeis", []), "existing_imei should be in existing_imeis"
    assert new_imei_1 in val_res.get("new_imeis", []), "new_imei_1 should be in new_imeis"

    # 2. Test bulk_add
    add_res = routes_data.bulk_add(bulk_in, db=db, user=user)
    print("Bulk Add Result:", add_res)

    assert add_res["added"] == 2, f"Expected added=2, got {add_res['added']}"
    assert add_res["skipped_duplicates"] >= 1, f"Expected skipped >= 1, got {add_res['skipped_duplicates']}"
    assert existing_imei in add_res["skipped_imeis"], f"existing_imei should be in skipped_imeis"

    # Verify that existing device was NOT overwritten
    dev_after = db.query(models.Device).filter(models.Device.imei == existing_imei).first()
    assert dev_after.model != "AttemptedOverwrite", "Existing device must NOT be overwritten!"

    # Verify new devices were added
    dev_new1 = db.query(models.Device).filter(models.Device.imei == new_imei_1).first()
    dev_new2 = db.query(models.Device).filter(models.Device.imei == new_imei_2).first()
    assert dev_new1 is not None and dev_new1.model == "NewModel1"
    assert dev_new2 is not None and dev_new2.model == "NewModel2"

    print("SUCCESS: Bulk upload ONLY uploaded new entries and preserved existing entries!")

    # Clean up test new devices
    db.query(models.Device).filter(models.Device.imei.in_([new_imei_1, new_imei_2, existing_imei])).delete(synchronize_session=False)
    db.commit()
    db.close()

if __name__ == "__main__":
    test_only_new_upload()

