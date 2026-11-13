import sys
import re
from database import engine, SessionLocal
from sqlalchemy import text, inspect
import models, schemas
import routes_data, customer_tables

def run_test():
    print("=== Testing Bulk Upload & Customer Table Creation ===")
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.user_id == "0001").first()
    if not user:
        print("Master user 0001 not found!")
        return

    test_cust_name = "Tata_Motors"

    # Step 1: Clean up any previous test table / customer
    with engine.begin() as conn:
        t = customer_tables.find_table(conn, 9999, test_cust_name)
        if t:
            conn.execute(text(f"DROP TABLE IF EXISTS `{t}`"))
            print(f"Cleaned up previous table: {t}")
    c_existing = db.query(models.Customer).filter(models.Customer.name == test_cust_name).first()
    if c_existing:
        db.query(models.Device).filter(models.Device.customer_id == c_existing.id).delete()
        db.delete(c_existing)
        db.commit()
        print(f"Cleaned up previous customer {test_cust_name}")

    # Step 2: Test Bulk Upload with NEW Customer
    print(f"\n1. Testing bulk upload for new customer: '{test_cust_name}'...")
    test_rows = [
        schemas.DeviceIn(
            customer_name=test_cust_name,
            imei="998877665544331",
            device_sr_no="SR-001",
            iccid="89910012345678901234",
            sim_provider="Airtel",
            model="Tracker-Pro"
        ),
        schemas.DeviceIn(
            customer_name=test_cust_name,
            imei="998877665544332",
            device_sr_no="SR-002",
            iccid="89910012345678901235",
            sim_provider="Jio",
            model="Tracker-Mini"
        )
    ]
    bulk_data = schemas.BulkIn(rows=test_rows, mode="replace")
    result = routes_data.bulk_add(bulk_data, db, user)
    print("Bulk upload result:", result)
    assert result["added"] == 2, f"Expected 2 added, got {result['added']}"

    # Step 3: Verify customer created in DB
    c = db.query(models.Customer).filter(models.Customer.name == test_cust_name).first()
    assert c is not None, "Customer was not created in customers table!"
    print(f"Customer in DB: ID={c.id}, Name='{c.name}'")

    # Step 4: Verify dedicated table created in TiDB Cloud with identical name
    with engine.connect() as conn:
        tables = inspect(conn).get_table_names()
        print("All tables in TiDB Cloud:", tables)
        assert test_cust_name in tables, f"Expected table '{test_cust_name}' in database, but found {tables}"
        print(f"Table '{test_cust_name}' successfully exists in TiDB Cloud with identical name!")

        # Check records in the customer table
        res = conn.execute(text(f"SELECT imei, customer_name, device_sr_no, sim_provider FROM `{test_cust_name}`")).fetchall()
        print(f"Rows inside table '{test_cust_name}':", res)
        assert len(res) == 2, f"Expected 2 rows in `{test_cust_name}`, got {len(res)}"
        assert res[0][1] == test_cust_name, f"Expected customer_name '{test_cust_name}', got {res[0][1]}"

    # Step 5: Test uploading to EXISTING customer ("if it is existing let it be")
    print(f"\n2. Testing upload to EXISTING customer: '{test_cust_name}'...")
    more_rows = [
        schemas.DeviceIn(
            customer_name=test_cust_name,
            imei="998877665544333",
            device_sr_no="SR-003",
            iccid="89910012345678901236",
            sim_provider="Vodafone",
            model="Tracker-Plus"
        )
    ]
    result2 = routes_data.bulk_add(schemas.BulkIn(rows=more_rows, mode="replace"), db, user)
    print("Existing customer upload result:", result2)
    assert result2["added"] == 1

    # Verify rows in existing customer table
    with engine.connect() as conn:
        res2 = conn.execute(text(f"SELECT imei, customer_name, device_sr_no FROM `{test_cust_name}`")).fetchall()
        print(f"Rows inside table '{test_cust_name}' after 2nd upload:", res2)
        assert len(res2) == 3, f"Expected 3 rows in `{test_cust_name}`, got {len(res2)}"

    # Step 6: Verify website API query
    devs = routes_data.devices(customer_id=c.id, db=db)
    print(f"API /devices for customer {c.id}: count={devs['total']}")
    assert devs["total"] == 3

    print("\n ALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("1. Bulk upload chose customer correctly.")
    print("2. If existing, it added to existing customer and its table.")
    print("3. If new, it created the customer and dedicated table in database and cloud.")
    print("4. Exact same name matches across Website, Database, and TiDB Cloud!")

    # Clean up test table and records
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS `{test_cust_name}`"))
    db.query(models.Device).filter(models.Device.customer_id == c.id).delete()
    db.delete(c)
    db.commit()
    print("Cleaned up test data.")

if __name__ == "__main__":
    run_test()
