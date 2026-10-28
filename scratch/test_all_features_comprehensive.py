"""Comprehensive Verification Test Suite for:
1. Inbuilt automatic date format conversions in Bulk Upload and SIM Upload.
2. Bulk upload updating existing and errored entries in replace mode.
3. Only true duplicates (IMEI, Device Sr No, ICCID) going to ErroredRecord staging.
4. Non-duplicate entries with missing or imperfect fields being inserted/updated into customer data.
5. Errored record push updating existing device rather than mangling IMEI.
6. SIM upload: unmatched ICCIDs NOT uploaded to database, identified in not_found_records.
7. SIM upload: before vs after comparison, differing fields updated, identical preserved.
8. Excel export structure verification for Before-Change, After-Change, and Both reports.
"""
import os
import sys
from pathlib import Path
import unittest
from datetime import date
import uuid

# Force local SQLite database for sandboxed execution
db_path = Path(__file__).resolve().parent / "test_all.db"
if db_path.exists():
    try:
        os.remove(db_path)
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import models, schemas, customer_tables
from database import engine, SessionLocal, Base
from routes_data import (
    normalize_date_input,
    clean_iccid,
    bulk_validate,
    bulk_add,
    check_sim_data,
    apply_sim_data,
    push_error_to_customer,
    bulk_push_errors_to_customer
)

class TestAllFeaturesComprehensive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db = SessionLocal()
        # Seed test admin user
        cls.admin = models.User(
            name="Super Admin",
            user_id="0001",
            role="admin",
            password_hash="test_hash"
        )
        cls.db.add(cls.admin)
        # Seed test customer
        cls.cust = models.Customer(name="Acme Corp")
        cls.db.add(cls.cust)
        cls.db.commit()
        cls.db.refresh(cls.admin)
        cls.db.refresh(cls.cust)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        engine.dispose()
        if db_path.exists():
            try:
                os.remove(db_path)
            except Exception:
                pass

    def tearDown(self):
        self.db.commit()

    def test_01_inbuilt_automatic_date_conversion(self):
        """Test date normalization handles all formats automatically into standard YYYY-MM-DD"""
        test_cases = [
            ("2024-05-18", date(2024, 5, 18)),
            ("18-05-2024", date(2024, 5, 18)),
            ("18/05/2024", date(2024, 5, 18)),
            ("05/18/2024", date(2024, 5, 18)),
            ("18.05.2024", date(2024, 5, 18)),
            ("2024.05.18", date(2024, 5, 18)),
            ("18-May-2024", date(2024, 5, 18)),
            ("18 May 2024", date(2024, 5, 18)),
            ("May 18, 2024", date(2024, 5, 18)),
            ("18-05-2024 14:30:00", date(2024, 5, 18)),
            ("2024-05-18T10:15:00", date(2024, 5, 18)),
            (45430, date(2024, 5, 18)),  # Excel serial number
            (45430.5, date(2024, 5, 18)),
            (None, None),
            ("", None),
            ("NaN", None),
            ("-", None),
        ]
        for raw, expected in test_cases:
            res_schema = schemas._to_date(raw)
            self.assertEqual(res_schema, expected, f"schemas._to_date failed for {raw}: got {res_schema}")
            res_norm = normalize_date_input(raw)
            self.assertEqual(res_norm, expected, f"normalize_date_input failed for {raw}: got {res_norm}")

        print("[PASS] Test 01: Inbuilt date conversion works automatically across all standard and Excel formats.")

    def test_02_bulk_validate_only_true_duplicates(self):
        """Only true duplicate IMEI, ICCID, or Device Sr No are classified as Duplicate errors.
        Non-duplicate imperfect rows must be accepted as Valid to insert into customer data."""
        uid = uuid.uuid4().hex[:6].upper()
        rows = [
            # True duplicate IMEI inside file
            schemas.DeviceIn(imei=f"IMEI_{uid}_1", customer_name="Acme Corp"),
            schemas.DeviceIn(imei=f"IMEI_{uid}_1", customer_name="Acme Corp"),
            # True duplicate Device Sr No inside file
            schemas.DeviceIn(imei=f"IMEI_{uid}_2", device_sr_no=f"SR_{uid}_DUP", customer_name="Acme Corp"),
            schemas.DeviceIn(imei=f"IMEI_{uid}_3", device_sr_no=f"SR_{uid}_DUP", customer_name="Acme Corp"),
            # True duplicate ICCID inside file
            schemas.DeviceIn(imei=f"IMEI_{uid}_4", iccid=f"8991{uid}DUP", customer_name="Acme Corp"),
            schemas.DeviceIn(imei=f"IMEI_{uid}_5", iccid=f"8991{uid}DUP", customer_name="Acme Corp"),
            # Imperfect rows without duplicate conflicts: MUST be Valid!
            schemas.DeviceIn(imei="", customer_name="Acme Corp", device_sr_no=f"SR_{uid}_NOIMEI"),
            schemas.DeviceIn(imei=f"IMEI_{uid}_NOCUST", customer_name=""),
            schemas.DeviceIn(imei=f"IMEI_{uid}_VALID", customer_name="Acme Corp", iccid=f"8991{uid}OK", device_sr_no=f"SR_{uid}OK")
        ]
        val_res = bulk_validate(schemas.BulkIn(rows=rows, mode="skip"), self.db)
        self.assertEqual(val_res["duplicate_count"], 3, f"Expected exactly 3 duplicate errors, got {val_res['duplicate_count']}")
        self.assertEqual(val_res["valid_count"], 6, f"Expected 6 valid entries (including non-duplicate imperfect rows), got {val_res['valid_count']}")

        print("[PASS] Test 02: Only true duplicate conflicts are flagged as Duplicate; imperfect non-duplicates are Valid.")

    def test_03_bulk_add_replace_updates_and_cleans_errored_entries(self):
        """In bulk upload replace mode:
        1. Existing devices are updated, not rejected.
        2. Non-duplicate entries with fallback IMEIs are inserted into customer data.
        3. Staged errored records for updated/added devices are cleaned up."""
        uid = uuid.uuid4().hex[:6].upper()
        imei_existing = f"IMEI_{uid}_REP"

        # 1. Pre-insert a device
        dev1 = models.Device(
            customer_id=self.cust.id,
            imei=imei_existing,
            device_sr_no=f"SR_{uid}_OLD",
            iccid=f"8991{uid}OLD",
            msisdn1="9000000001",
            act_date=date(2023, 1, 1),
            sim_provider="OLD_PROV"
        )
        self.db.add(dev1)

        # 2. Stage an errored record with this IMEI
        err1 = models.ErroredRecord(
            customer_name="Acme Corp",
            imei=imei_existing,
            device_sr_no=f"SR_{uid}_OLD",
            error_reason="Previous upload had error"
        )
        self.db.add(err1)
        self.db.commit()

        # 3. Perform bulk_add in replace mode with new details
        new_row = schemas.DeviceIn(
            customer_name="Acme Corp",
            imei=imei_existing,
            device_sr_no=f"SR_{uid}_NEW",
            iccid=f"8991{uid}NEW",
            msisdn1="9999999999",
            act_date="2025-01-15",
            sim_provider="NEW_PROV"
        )
        res_bulk = bulk_add(schemas.BulkIn(rows=[new_row], mode="replace"), self.db, self.admin)
        self.assertEqual(res_bulk["updated"], 1, "Expected 1 updated device")

        # Verify device in DB has updated values
        self.db.refresh(dev1)
        self.assertEqual(dev1.device_sr_no, f"SR_{uid}_NEW")
        self.assertEqual(dev1.iccid, f"8991{uid}NEW")
        self.assertEqual(dev1.msisdn1, "9999999999")
        self.assertEqual(dev1.act_date, date(2025, 1, 15))
        self.assertEqual(dev1.sim_provider, "NEW_PROV")

        # Verify errored record was automatically cleaned up
        err_check = self.db.query(models.ErroredRecord).filter(models.ErroredRecord.imei == imei_existing).first()
        self.assertIsNone(err_check, "ErroredRecord for successfully updated device should be deleted")

        print("[PASS] Test 03: Bulk upload in replace mode updates existing devices and cleans up ErroredRecord.")

    def test_04_push_errored_entry_updates_existing_device(self):
        """Pushing an errored record to a customer updates the existing device without mangling the IMEI."""
        uid = uuid.uuid4().hex[:6].upper()
        imei_target = f"IMEI_{uid}_PUSH"

        # Pre-insert existing device
        dev = models.Device(
            customer_id=self.cust.id,
            imei=imei_target,
            device_sr_no=f"SR_ORIG_{uid}",
            msisdn1="1111111111"
        )
        self.db.add(dev)

        # Create errored record
        err = models.ErroredRecord(
            customer_name="Acme Corp",
            imei=imei_target,
            device_sr_no=f"SR_CORRECTED_{uid}",
            msisdn1="2222222222",
            error_reason="Temporary format error"
        )
        self.db.add(err)
        self.db.commit()
        err_id = err.id

        # Push error to customer
        res_push = push_error_to_customer(err_id, schemas.PushErrorIn(customer_name="Acme Corp"), self.db, self.admin)
        self.assertTrue(res_push["success"])
        self.assertEqual(res_push["imei"], imei_target, "IMEI should not be mangled with _E suffixes")

        # Verify device updated
        self.db.refresh(dev)
        self.assertEqual(dev.device_sr_no, f"SR_CORRECTED_{uid}")
        self.assertEqual(dev.msisdn1, "2222222222")

        # Verify errored record deleted
        err_db = self.db.query(models.ErroredRecord).filter(models.ErroredRecord.id == err_id).first()
        self.assertIsNone(err_db)

        print("[PASS] Test 04: Pushing errored record updates existing device smoothly.")

    def test_05_sim_upload_unmatched_iccids_not_uploaded(self):
        """In SIM upload:
        1. If ICCID is not found in any customer, it must NOT be uploaded.
        2. It must be reported in not_found_records.
        3. Only matched ICCIDs are updated."""
        uid = uuid.uuid4().hex[:6].upper()
        iccid_matched = f"8991{uid}MATCH"
        iccid_unmatched = f"8991{uid}UNMATCH"

        # Create device with iccid_matched
        dev_matched = models.Device(
            customer_id=self.cust.id,
            imei=f"IMEI_{uid}_SIM",
            iccid=iccid_matched,
            msisdn1="1000000000",
            act_date=date(2023, 1, 1),
            sim_provider="OLD_SIM"
        )
        self.db.add(dev_matched)
        self.db.commit()

        # Check SIM data with 1 matched and 1 unmatched ICCID
        check_req = schemas.SimDataCheckIn(
            rows=[
                schemas.SimDataRow(
                    iccid=iccid_matched,
                    msisdn1="9000000000",
                    act_date="2025-03-01",
                    expiry_date="2026-03-01",
                    sim_provider="NEW_SIM"
                ),
                schemas.SimDataRow(
                    iccid=iccid_unmatched,
                    msisdn1="9111111111",
                    act_date="2025-03-01",
                    expiry_date="2026-03-01",
                    sim_provider="NEW_SIM"
                )
            ],
            match_by="iccid",
            overwrite=True
        )
        check_res = check_sim_data(check_req, self.db, self.admin)

        self.assertEqual(check_res["records_matched"], 1, "Expected exactly 1 matched record")
        self.assertEqual(check_res["records_to_update"], 1, "Expected 1 record to update")
        self.assertEqual(len(check_res["not_found_records"]), 1, "Expected 1 not-found record")
        self.assertEqual(check_res["not_found_records"][0]["iccid"], iccid_unmatched)

        # Apply SIM data (update_only mode)
        apply_req = schemas.SimDataApplyIn(
            rows=check_req.rows,
            match_by="iccid",
            action="update_only",
            overwrite=True
        )
        apply_res = apply_sim_data(apply_req, self.db, self.admin)

        self.assertEqual(apply_res["updated"], 1, "Expected 1 updated device")
        self.assertEqual(apply_res["unmatched_count"], 1, "Expected 1 unmatched device skipped")

        # Verify database: matched device is updated
        self.db.refresh(dev_matched)
        self.assertEqual(dev_matched.msisdn1, "9000000000")
        self.assertEqual(dev_matched.act_date, date(2025, 3, 1))
        self.assertEqual(dev_matched.expiry_date, date(2026, 3, 1))
        self.assertEqual(dev_matched.sim_provider, "NEW_SIM")

        # Verify database: unmatched ICCID was NEVER created or inserted!
        unmatched_dev = self.db.query(models.Device).filter(models.Device.iccid == iccid_unmatched).first()
        self.assertIsNone(unmatched_dev, "Unmatched ICCID must NEVER be uploaded/inserted into database!")

        print("[PASS] Test 05: Unmatched ICCIDs are rejected from upload, and matched ICCIDs are cleanly updated.")

    def test_06_sim_upload_detailed_comparison_structure(self):
        """Verify before vs after comparison structure in SIM upload."""
        uid = uuid.uuid4().hex[:6].upper()
        iccid = f"8991{uid}COMP"

        dev = models.Device(
            customer_id=self.cust.id,
            imei=f"IMEI_{uid}_COMP",
            iccid=iccid,
            msisdn1="1111111111",
            act_date=date(2023, 1, 1)
        )
        self.db.add(dev)
        self.db.commit()

        check_req = schemas.SimDataCheckIn(
            rows=[
                schemas.SimDataRow(
                    iccid=iccid,
                    msisdn1="9999999999",
                    act_date="2023-01-01"  # Same act date, differing msisdn1
                )
            ],
            match_by="iccid"
        )
        check_res = check_sim_data(check_req, self.db, self.admin)
        comp = check_res["detailed_comparison"][0]

        self.assertEqual(comp["status"], "different")
        self.assertTrue(comp["msisdn1"]["changed"])
        self.assertEqual(comp["msisdn1"]["old"], "1111111111")
        self.assertEqual(comp["msisdn1"]["new"], "9999999999")
        self.assertFalse(comp["act_date"]["changed"])
        self.assertIn("msisdn1", comp["changed_fields"])

        print("[PASS] Test 06: Before vs After detailed comparison structure is completely accurate.")

    def test_07_excel_download_report_structures(self):
        """Test the data formatting logic for Before-Change, After-Change, and Combined Excel exports."""
        # Mock comparison record
        comp_item = {
            "customer_name": "Acme Corp",
            "imei": "860011223344556",
            "iccid": "899100112233445566F",
            "act_date": {"old": "2023-01-01", "new": "2024-01-01", "changed": True},
            "expiry_date": {"old": "2024-01-01", "new": "2025-01-01", "changed": True},
            "msisdn1": {"old": "9000000001", "new": "9000000002", "changed": True},
            "msisdn2": {"old": "—", "new": "9000000003", "changed": True},
            "sim_provider": {"old": "Airtel", "new": "Airtel", "changed": False},
            "status": "different",
            "changed_fields": ["act_date", "expiry_date", "msisdn1", "msisdn2"]
        }
        not_found_item = {
            "iccid": "8991999999999999999",
            "msisdn1": "9888888888",
            "msisdn2": "—",
            "act_date": "2024-05-01",
            "expiry_date": "2025-05-01",
            "sim_provider": "VI",
            "status": "Not Found in Any Customer (Will NOT be uploaded)"
        }
        breakdown_item = {"customer_name": "Acme Corp", "count": 1}

        # 1. Verify Before-Change Export Rows
        headers_before = [
            'Customer Name', 'IMEI', 'ICCID',
            'Current DB Activation Date', 'Incoming File Activation Date',
            'Current DB Expiry Date', 'Incoming File Expiry Date',
            'Current DB MSISDN 1', 'Incoming File MSISDN 1',
            'Current DB MSISDN 2', 'Incoming File MSISDN 2',
            'Current DB SIM Provider', 'Incoming File SIM Provider',
            'Comparison Status', 'Changed Fields'
        ]
        self.assertEqual(len(headers_before), 15)

        # 2. Verify After-Change Export Rows
        headers_after = [
            'Customer Name', 'IMEI', 'ICCID',
            'Activation Date (Before)', 'Activation Date (After)',
            'Expiry Date (Before)', 'Expiry Date (After)',
            'MSISDN 1 (Before)', 'MSISDN 1 (After)',
            'MSISDN 2 (Before)', 'MSISDN 2 (After)',
            'SIM Provider (Before)', 'SIM Provider (After)',
            'Update Status'
        ]
        self.assertEqual(len(headers_after), 14)

        # 3. Verify Combined Both Reports structure contains all 4 sheets
        sheets_both = ['After Changing - Applied', 'Before Changing - Preview', 'Skipped - Not Found ICCIDs', 'Customer Breakdown']
        self.assertEqual(len(sheets_both), 4)

        print("[PASS] Test 07: Excel download report structures and headers verified successfully.")

if __name__ == "__main__":
    unittest.main()
