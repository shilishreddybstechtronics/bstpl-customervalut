import sys
import os
import unittest
from datetime import date
from pathlib import Path
import uuid

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import models, schemas
from routes_data import normalize_date_input, bulk_validate, bulk_add
from database import SessionLocal

class TestSimAndBulkFeatures(unittest.TestCase):
    def test_date_conversion_formats(self):
        """Test converting various date formats to standard date"""
        cases = [
            ("2024-05-18", date(2024, 5, 18)),
            ("18-05-2024", date(2024, 5, 18)),
            ("18/05/2024", date(2024, 5, 18)),
            ("05/18/2024", date(2024, 5, 18)),
            ("18.05.2024", date(2024, 5, 18)),
            ("2024.05.18", date(2024, 5, 18)),
            ("18-May-2024", date(2024, 5, 18)),
            ("18 May 2024", date(2024, 5, 18)),
            ("18-05-2024 14:30:00", date(2024, 5, 18)),
            ("2024-05-18T10:15:00", date(2024, 5, 18)),
            (45430, date(2024, 5, 18)), # Excel serial number
            (45430.5, date(2024, 5, 18)),
        ]
        for val, expected in cases:
            res = schemas._to_date(val)
            self.assertEqual(res, expected, f"Failed for input {val}: got {res}, expected {expected}")
            norm = normalize_date_input(val)
            self.assertEqual(norm, expected, f"normalize_date_input failed for {val}")
        print("[PASS] Date conversion tests passed across all formats.")

    def test_error_entries_only_on_duplicate_imei_iccid_srno(self):
        """Verify bulk_validate treats only duplicate imei, duplicate iccid, and duplicate device_sr_no as errors"""
        db = SessionLocal()
        try:
            # Create a mock user
            user = db.query(models.User).first()
            if not user:
                user = models.User(name="Admin", user_id="admin_test", role="admin", password_hash="hash")
                db.add(user)
                db.commit()
                db.refresh(user)

            unique_sfx = uuid.uuid4().hex[:6].upper()
            row_dup_imei_1 = schemas.DeviceIn(imei=f"TEST_IMEI_{unique_sfx}_1", iccid=f"8991{unique_sfx}01", device_sr_no=f"SR_{unique_sfx}_1", customer_name="TestCorp")
            row_dup_imei_2 = schemas.DeviceIn(imei=f"TEST_IMEI_{unique_sfx}_1", iccid=f"8991{unique_sfx}02", device_sr_no=f"SR_{unique_sfx}_2", customer_name="TestCorp")
            row_dup_sr_1 = schemas.DeviceIn(imei=f"TEST_IMEI_{unique_sfx}_3", iccid=f"8991{unique_sfx}03", device_sr_no=f"SR_{unique_sfx}_DUP", customer_name="TestCorp")
            row_dup_sr_2 = schemas.DeviceIn(imei=f"TEST_IMEI_{unique_sfx}_4", iccid=f"8991{unique_sfx}04", device_sr_no=f"SR_{unique_sfx}_DUP", customer_name="TestCorp")
            row_dup_iccid_1 = schemas.DeviceIn(imei=f"TEST_IMEI_{unique_sfx}_5", iccid=f"8991{unique_sfx}_SAME", device_sr_no=f"SR_{unique_sfx}_5", customer_name="TestCorp")
            row_dup_iccid_2 = schemas.DeviceIn(imei=f"TEST_IMEI_{unique_sfx}_6", iccid=f"8991{unique_sfx}_SAME", device_sr_no=f"SR_{unique_sfx}_6", customer_name="TestCorp")

            # Non-duplicate row with missing customer name and invalid IMEI (should be VALID and inserted!)
            row_missing_fields = schemas.DeviceIn(imei="", iccid=f"8991{unique_sfx}99", device_sr_no="", customer_name="")

            rows = [
                row_dup_imei_1,
                row_dup_imei_2,    # duplicate IMEI
                row_dup_sr_1,
                row_dup_sr_2,      # duplicate SR NO
                row_dup_iccid_1,
                row_dup_iccid_2,   # duplicate ICCID
                row_missing_fields # non-duplicate missing fields -> valid to insert
            ]

            val_input = schemas.BulkIn(rows=rows, mode="skip")
            res = bulk_validate(val_input, db=db)

            self.assertEqual(res["invalid_count"], 0, "invalids list should always be empty; all non-duplicates go to valid")
            self.assertEqual(res["duplicate_count"], 3, f"Expected exactly 3 duplicates, got {res['duplicate_count']}")
            self.assertEqual(res["valid_count"], 4, f"Expected 4 valid rows, got {res['valid_count']}")

            dup_reasons = [d["reason"] for d in res["duplicates"]]
            self.assertTrue(any("IMEI" in r for r in dup_reasons))
            self.assertTrue(any("Device Sr No" in r for r in dup_reasons))
            self.assertTrue(any("ICCID" in r for r in dup_reasons))

            # Verify that non-duplicate row with missing customer & IMEI is marked Valid
            valid_rows = res["valid_sample"]
            missing_row = next((r for r in valid_rows if r.get("iccid") == f"8991{unique_sfx}99"), None)
            self.assertIsNotNone(missing_row)
            self.assertEqual(missing_row["status"], "Valid")
            self.assertEqual(missing_row["reason"], "Ready to insert into customer data")
            print("[PASS] bulk_validate correctly classifies only duplicate IMEI/ICCID/SR_NO as errors and marks other rows valid.")
        finally:
            db.close()

    def test_sim_data_strictly_iccid(self):
        """Verify check_sim_data and apply_sim_data enforce iccid matching"""
        import inspect
        from routes_data import check_sim_data, apply_sim_data
        
        check_src = inspect.getsource(check_sim_data)
        apply_src = inspect.getsource(apply_sim_data)

        self.assertIn('match_by = "iccid"', check_src)
        self.assertIn('match_by = "iccid"', apply_src)
        print("[PASS] SIM data upload strictly uses ICCID matching; IMEI is disabled.")

    def test_direct_upload_feature_deleted(self):
        """Verify direct upload endpoints and parameters are completely deleted"""
        import routes_data
        self.assertFalse(hasattr(routes_data, "get_direct_upload_count"))
        
        # Check router routes for /devices/bulk/direct-status
        direct_routes = [r.path for r in routes_data.router.routes if "direct-status" in getattr(r, "path", "")]
        self.assertEqual(len(direct_routes), 0, "direct-status route must be removed")
        print("[PASS] Direct upload route and helper function successfully removed.")

    def test_push_error_to_specified_customer(self):
        """Verify an errored entry can be pushed into a specified customer even with error"""
        from routes_data import push_error_to_customer, bulk_push_errors_to_customer
        db = SessionLocal()
        try:
            user = db.query(models.User).first()
            sfx = uuid.uuid4().hex[:6].upper()
            target_cust = f"Customer_{sfx}"

            # Create an errored record with invalid/missing IMEI and duplicate reasons
            err_rec = models.ErroredRecord(
                customer_name="Original_Broken_Customer",
                imei="", # missing IMEI
                device_sr_no=f"SR_ERR_{sfx}",
                iccid=f"8991{sfx}99",
                error_reason="Missing IMEI and bad sequence"
            )
            db.add(err_rec)
            db.commit()
            db.refresh(err_rec)
            err_id = err_rec.id

            # Push into target customer even with error
            res = push_error_to_customer(err_id, schemas.PushErrorIn(customer_name=target_cust), db=db, user=user)
            self.assertTrue(res["success"])
            self.assertEqual(res["customer_name"], target_cust)
            self.assertTrue(res["imei"].startswith("SRERR") or res["imei"].startswith("INV_"))

            # Verify it was removed from ErroredRecord
            chk = db.query(models.ErroredRecord).filter(models.ErroredRecord.id == err_id).first()
            self.assertIsNone(chk, "Record should be removed from ErroredRecord table")

            # Verify it is in Device table under target_cust
            dev = db.query(models.Device).filter(models.Device.id == res["device_id"]).first()
            self.assertIsNotNone(dev)
            self.assertEqual(dev.customer.name, target_cust)
            self.assertEqual(dev.device_sr_no, f"SR_ERR_{sfx}")
            print("[PASS] push_error_to_customer successfully pushed errored record into specified customer.")

            # Test bulk push with another errored entry
            err2 = models.ErroredRecord(
                customer_name="Broken_Cust_2",
                imei=f"CLASH_{sfx}",
                error_reason="Clash test"
            )
            db.add(err2)
            db.commit()
            db.refresh(err2)

            bulk_res = bulk_push_errors_to_customer(
                schemas.BulkPushErrorsIn(error_ids=[err2.id], customer_name=target_cust),
                db=db,
                user=user
            )
            self.assertEqual(bulk_res["pushed_count"], 1)
            self.assertEqual(bulk_res["customer_name"], target_cust)
            print("[PASS] bulk_push_errors_to_customer successfully pushed entries to specified customer.")

            # Clean up test devices and customer
            db.query(models.Device).filter(models.Device.id.in_([res["device_id"]])).delete()
            cust_obj = db.query(models.Customer).filter(models.Customer.name == target_cust).first()
            if cust_obj:
                db.query(models.Device).filter(models.Device.customer_id == cust_obj.id).delete()
                db.delete(cust_obj)
            db.commit()
        finally:
            db.close()

    def test_sim_upload_iccid_without_error(self):
        """Verify SIM data upload works properly with ICCIDs without throwing errors"""
        from routes_data import check_sim_data, apply_sim_data
        db = SessionLocal()
        try:
            user = db.query(models.User).first()
            sfx = uuid.uuid4().hex[:6].upper()
            target_cust = f"SimTestCust_{sfx}"

            # 1. Check SIM Data with just ICCIDs (no provider, no other fields)
            rows = [
                schemas.SimDataRow(iccid=f"8991{sfx}01"),
                schemas.SimDataRow(iccid=f"8991{sfx}02"),
            ]
            check_req = schemas.SimDataCheckIn(rows=rows, overwrite=True)
            res_check = check_sim_data(check_req, db=db, user=user)

            self.assertEqual(res_check["file_rows_count"], 2)
            self.assertIn("can_insert_count", res_check)
            print("[PASS] check_sim_data succeeded without errors on ICCID-only file.")

            # 2. Apply SIM Data with insert_new=True
            apply_req = schemas.SimDataApplyIn(
                rows=rows,
                insert_new=True,
                target_customer=target_cust,
                overwrite=True
            )
            res_apply = apply_sim_data(apply_req, db=db, user=user)
            self.assertEqual(res_apply["inserted"], 2)
            print("[PASS] apply_sim_data succeeded and inserted new SIM records without errors.")

            # Clean up created SIM devices and customer
            cust_obj = db.query(models.Customer).filter(models.Customer.name == target_cust).first()
            if cust_obj:
                db.query(models.Device).filter(models.Device.customer_id == cust_obj.id).delete()
                db.delete(cust_obj)
            db.commit()
        finally:
            db.close()

    def test_customer_merge_properly(self):
        """Verify merging customer A into customer B properly moves devices, updates tables, and drops old table"""
        import routes_customers
        import customer_tables
        from database import engine
        from sqlalchemy import inspect, text

        db = SessionLocal()
        try:
            user = db.query(models.User).first()
            sfx = uuid.uuid4().hex[:6].upper()
            cname_a = f"MergeSrc_{sfx}"
            cname_b = f"MergeDst_{sfx}"

            cust_a = models.Customer(name=cname_a)
            cust_b = models.Customer(name=cname_b)
            db.add_all([cust_a, cust_b])
            db.commit()
            db.refresh(cust_a)
            db.refresh(cust_b)

            # Add devices to both
            dev_a = models.Device(
                customer_id=cust_a.id,
                imei=f"IMEI_A_{sfx}",
                iccid=f"ICC_A_{sfx}",
                device_sr_no=f"SR_A_{sfx}"
            )
            dev_b = models.Device(
                customer_id=cust_b.id,
                imei=f"IMEI_B_{sfx}",
                iccid=f"ICC_B_{sfx}",
                device_sr_no=f"SR_B_{sfx}"
            )
            db.add_all([dev_a, dev_b])
            db.commit()

            # Ensure customer tables exist
            with engine.begin() as conn:
                customer_tables.ensure_table(conn, cust_a.id, cust_a.name)
                customer_tables.ensure_table(conn, cust_b.id, cust_b.name)

            # Mirror device rows into respective tables
            customer_tables.mirror_rows([
                (cust_a.id, cust_a.name, {"imei": dev_a.imei, "device_sr_no": dev_a.device_sr_no, "iccid": dev_a.iccid}),
                (cust_b.id, cust_b.name, {"imei": dev_b.imei, "device_sr_no": dev_b.device_sr_no, "iccid": dev_b.iccid})
            ])

            # Merge customer A into customer B using schemas.MergeIn with target_customer_id
            merge_payload = schemas.MergeIn(target_customer_id=cust_b.id)
            res = routes_customers.merge(cust_a.id, merge_payload, db=db, user=user)

            self.assertEqual(res["into"], cname_b)
            self.assertEqual(res["moved"], 1)

            # Customer A should be deleted
            chk_a = db.query(models.Customer).filter(models.Customer.id == cust_a.id).first()
            self.assertIsNone(chk_a)

            # Both devices should now belong to Customer B
            devs_now = db.query(models.Device).filter(models.Device.customer_id == cust_b.id).all()
            self.assertEqual(len(devs_now), 2)
            self.assertTrue(any(d.imei == f"IMEI_A_{sfx}" for d in devs_now))
            self.assertTrue(any(d.imei == f"IMEI_B_{sfx}" for d in devs_now))

            # Verify table synchronization
            with engine.begin() as conn:
                insp = inspect(conn)
                tables = insp.get_table_names()
                src_tbl = customer_tables.find_table(conn, cust_a.id, cname_a)
                dst_tbl = customer_tables.find_table(conn, cust_b.id, cname_b)

                self.assertIsNone(src_tbl, "Source customer table must be dropped after merge")
                self.assertIsNotNone(dst_tbl, "Destination customer table must exist")

                # Verify rows in destination table
                cnt = conn.execute(text(f"SELECT COUNT(*) FROM `{dst_tbl}`")).scalar()
                self.assertGreaterEqual(cnt, 2, "Destination table must contain rows from both customers")

            print("[PASS] customer merge properly moved devices, synced SQL customer tables, and dropped source table.")

            # Clean up
            db.query(models.Device).filter(models.Device.customer_id == cust_b.id).delete()
            db.delete(cust_b)
            db.commit()
            with engine.begin() as conn:
                customer_tables.drop_table(cust_b.id, cname_b)
        finally:
            db.close()

    def test_sim_upload_ccid_and_extra_columns(self):
        """Verify CCID is treated identically to ICCID and selected extra columns are added to DB and customer tables"""
        from routes_data import check_sim_data, apply_sim_data
        import customer_tables
        from database import engine
        from sqlalchemy import inspect, text

        db = SessionLocal()
        try:
            user = db.query(models.User).first()
            sfx = uuid.uuid4().hex[:6].upper()
            target_cust = f"SimCust_{sfx}"

            # 1. Verify schema validation with 'ccid' alias and 'extra' columns
            row_dict = {
                "ccid": f"8991{sfx}99",
                "msisdn1": "9876543210",
                "act_date": "2024-05-01",
                "expiry_date": "2025-05-01",
                "extra": {
                    "Circle": "Mumbai",
                    "Plan_Name": "Enterprise_VIP"
                }
            }
            validated_row = schemas.SimDataRow.model_validate(row_dict)
            self.assertEqual(validated_row.iccid, f"8991{sfx}99")
            self.assertEqual(validated_row.extra.get("Circle"), "Mumbai")
            self.assertEqual(validated_row.extra.get("Plan_Name"), "Enterprise_VIP")
            print("[PASS] SimDataRow model_validate successfully mapped 'ccid' -> 'iccid' and preserved extra columns.")

            # 2. Test check_sim_data with CCID and extra columns
            check_req = schemas.SimDataCheckIn(rows=[validated_row], overwrite=True)
            res_check = check_sim_data(check_req, db=db, user=user)
            self.assertEqual(res_check["file_rows_count"], 1)
            self.assertEqual(res_check["can_insert_count"], 1)
            print("[PASS] check_sim_data successfully processed CCID with extra columns.")

            # 3. Test apply_sim_data to insert record into database and customer table
            apply_req = schemas.SimDataApplyIn(
                rows=[validated_row],
                insert_new=True,
                target_customer=target_cust,
                overwrite=True
            )
            res_apply = apply_sim_data(apply_req, db=db, user=user)
            self.assertEqual(res_apply["inserted"], 1)
            print("[PASS] apply_sim_data successfully inserted new SIM record with CCID & extra columns.")

            # 4. Verify in database
            dev = db.query(models.Device).filter(models.Device.iccid == f"8991{sfx}99").first()
            self.assertIsNotNone(dev)
            self.assertEqual(dev.sim_type, "E-SIM")
            self.assertEqual(dev.msisdn1, "9876543210")
            self.assertIsNotNone(dev.extra)
            self.assertEqual(dev.extra.get("Circle"), "Mumbai")
            self.assertEqual(dev.extra.get("Plan_Name"), "Enterprise_VIP")

            # Clean up
            cust_obj = db.query(models.Customer).filter(models.Customer.name == target_cust).first()
            if cust_obj:
                db.query(models.Device).filter(models.Device.customer_id == cust_obj.id).delete()
                db.delete(cust_obj)
            db.commit()
            if cust_obj:
                with engine.begin() as conn:
                    customer_tables.drop_table(cust_obj.id, target_cust)
            print("[PASS] Verified SIM device record in database and cleaned up successfully.")
        finally:
            db.close()

if __name__ == "__main__":
    unittest.main()


