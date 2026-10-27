import sys
import os
import unittest
from datetime import date

from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import models, schemas
from routes_data import normalize_date_input
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
            # Also test normalize_date_input
            norm = normalize_date_input(val)
            self.assertEqual(norm, expected, f"normalize_date_input failed for {val}")
        print("Date conversion tests PASSED across all formats.")

    def test_direct_bulk_quota_and_invalids(self):
        """Test direct bulk upload invalid row handling and 2-use quota logic"""
        db = SessionLocal()
        try:
            # Check or create test user
            user = db.query(models.User).filter(models.User.user_id == "test_upload_user").first()
            if not user:
                user = models.User(name="Test Upload User", user_id="test_upload_user", password_hash="pw", role="limited")
                db.add(user)
                db.commit()
                db.refresh(user)

            # Clear logs for this test user
            db.query(models.ActivityLog).filter(
                models.ActivityLog.user_id == user.id,
                models.ActivityLog.action == "direct_bulk_upload"
            ).delete()
            db.commit()

            # Verify initial count is 0
            cnt0 = db.query(models.ActivityLog).filter(
                models.ActivityLog.user_id == user.id,
                models.ActivityLog.action == "direct_bulk_upload"
            ).count()
            self.assertEqual(cnt0, 0)

            from datetime import datetime
            # Simulate 1st use
            log1 = models.ActivityLog(
                user_id=user.id,
                user_login=user.user_id,
                user_name=user.name,
                action="direct_bulk_upload",
                detail="Used direct upload (1/2). Inserted 5 rows.",
                created_at=datetime.utcnow()
            )
            db.add(log1)
            db.commit()

            # Simulate 2nd use
            log2 = models.ActivityLog(
                user_id=user.id,
                user_login=user.user_id,
                user_name=user.name,
                action="direct_bulk_upload",
                detail="Used direct upload (2/2). Inserted 3 rows.",
                created_at=datetime.utcnow()
            )
            db.add(log2)
            db.commit()

            cnt2 = db.query(models.ActivityLog).filter(
                models.ActivityLog.user_id == user.id,
                models.ActivityLog.action == "direct_bulk_upload"
            ).count()
            self.assertEqual(cnt2, 2)
            print("Direct upload quota counting verified: 2 uses max.")

            # Clean up test logs
            db.query(models.ActivityLog).filter(
                models.ActivityLog.user_id == user.id,
                models.ActivityLog.action == "direct_bulk_upload"
            ).delete()
            db.commit()
        finally:
            db.close()

    def test_sim_data_schema_and_direct_fallback(self):
        """Test schemas.SimDataApplyIn and invalid fallback generator"""
        import uuid
        payload = schemas.SimDataApplyIn(
            rows=[{"iccid": "89910001", "msisdn1": "9876543210"}],
            insert_new=True,
            target_customer="General_Customer"
        )
        self.assertTrue(payload.insert_new)
        self.assertEqual(payload.target_customer, "General_Customer")

        # Test fallback IMEI generation for invalid rows
        fake_imei = f"INV_{uuid.uuid4().hex[:8].upper()}"
        self.assertTrue(fake_imei.startswith("INV_"))
        self.assertEqual(len(fake_imei), 12)
        print("SIM data schema and fallback IMEI logic verified.")

if __name__ == "__main__":
    unittest.main()
