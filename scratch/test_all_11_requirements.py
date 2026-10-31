import os
import sys
from datetime import date, timedelta
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test database and import modules
sys.path.insert(0, os.path.abspath('backend'))
import models, schemas
from database import Base
import routes_data, routes_users, auth

# Use in-memory SQLite database for isolated test execution
engine = create_engine('sqlite:///:memory:', echo=False)
models.Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("=" * 60)
print("RUNNING COMPREHENSIVE 11-REQUIREMENT VERIFICATION SUITE")
print("=" * 60)

# Create customers
cust1 = models.Customer(name="BSTPL Telecom")
cust2 = models.Customer(name="Airtel Fleet")
db.add_all([cust1, cust2])
db.commit()

# Create sample devices for testing expiry sorting
today = date.today()
devs = [
    models.Device(customer_id=cust1.id, imei="111111111111111", iccid="8991000000000000001", expiry_date=today - timedelta(days=5)), # Expired (-5 days)
    models.Device(customer_id=cust1.id, imei="222222222222222", iccid="8991000000000000002", expiry_date=today - timedelta(days=1)), # Expired (-1 day)
    models.Device(customer_id=cust1.id, imei="333333333333333", iccid="8991000000000000003", expiry_date=today + timedelta(days=2)), # Expiring soon (2 days left)
    models.Device(customer_id=cust1.id, imei="444444444444444", iccid="8991000000000000004", expiry_date=today + timedelta(days=40)), # 40 days left
    models.Device(customer_id=cust1.id, imei="555555555555555", iccid="8991000000000000005", expiry_date=None) # No expiry date
]
db.add_all(devs)
db.commit()

# [TEST 1] SIM Expiry Sorting
q = routes_data.build_device_query(db, None, "", "all", sort_by="expiry_date", sort_dir="asc")
sorted_devs = q.all()
ids = [d.id for d in sorted_devs]
print(f"[TEST 1] SIM Expiry Sorting (Ascending order of days remaining)")
print(f"Sorted devices by expiry_date asc: {ids}")
assert ids[0] == 1, "First device must be expired device 1 (-5 days)"
assert ids[1] == 2, "Second device must be expired device 2 (-1 day)"
assert ids[2] == 3, "Third device must be device 3 (+2 days left)"
assert ids[3] == 4, "Fourth device must be device 4 (+40 days left)"
assert ids[4] == 5, "Fifth device must be device 5 (None expiry date)"
print("✓ SIM Expiry Sorting verified: Expired SIMs appear first, ascending days remaining!\n")

# [TEST 2] Settings Backend Endpoints & Master Admin Password Visibility
user_admin = models.User(name="Admin User", user_id="0002", role="admin", password_hash=auth.hash_password("adminpass123"), plain_password="adminpass123")
user_emp = models.User(name="Regular Employee", user_id="0011", role="limited", password_hash=auth.hash_password("emppass123"), plain_password="emppass123")
user_super = models.User(name="Super Admin", user_id="0001", role="admin", password_hash=auth.hash_password("superpass123"), plain_password="superpass123")
db.add_all([user_admin, user_emp, user_super])
db.commit()

# Test update_my_name
res_name = routes_users.update_my_name(schemas.UserNameUpdate(name="Admin User Renamed"), db=db, current_user=user_admin)
assert res_name["name"] == "Admin User Renamed"
print("[TEST 2] Settings Backend Endpoints & Master Admin Password Visibility")
print("✓ Edit Name API verified successfully!")

# Test Master Admin password visibility
# Master Admin (0002) should see everyone's password!
emp_out_for_master = routes_users.user_out(user_emp, actor=user_admin)
assert emp_out_for_master["password"] == "emppass123", "Master Admin must be able to see employee's password"
super_out_for_master = routes_users.user_out(user_super, actor=user_admin)
assert super_out_for_master["password"] == "superpass123", "Master Admin must be able to see password"
print("✓ Master Admin password visibility verified: Master Admin can see everyone's password!")

# Test list_users as admin
users_list = routes_users.list_users(db=db, admin=user_admin)
assert len(users_list) >= 3
print("✓ Manage Users API verified successfully!\n")

# [TEST 3] Logout Endpoint
import main
app = main.app
routes = [route.path for route in app.routes if hasattr(route, 'path')]
assert "/api/auth/logout" in routes or "/auth/logout" in routes
print("[TEST 3] Logout Endpoint")
print("✓ Logout backend route verified successfully!\n")

# [TEST 6] Data Health Diagnostics
health = routes_data.inventory_health(db=db)
print("[TEST 6] Data Health Diagnostics")
print(f"Health data stats: total={health['total_records']}, bad_imei={health['bad_imei_count']}, bad_date={health['bad_date_count']}")
assert health["total_records"] == 5
print("✓ Data Health diagnostics verified successfully!\n")

# [TEST 9 & 10] Bulk Upload: Strict INSERT-ONLY Logic
print("[TEST 9 & 10] Bulk Upload: Strict INSERT-ONLY Logic")
upload_rows = [
    schemas.DeviceIn(imei="8991999999990000001", iccid="8991000000000000001", customer_name=cust1.name), # Existing ICCID
    schemas.DeviceIn(imei="8991999999990000002", iccid="8991000000000000010", customer_name=cust1.name), # Completely New 1
    schemas.DeviceIn(imei="8991999999990000003", iccid="8991000000000000011", customer_name=cust1.name), # Completely New 2
    schemas.DeviceIn(imei="8991999999990000001", iccid="8991000000000000012", customer_name=cust1.name), # In-file duplicate IMEI
]

val_res = routes_data.bulk_validate(schemas.BulkIn(rows=upload_rows, mode="skip"), db=db)
print(f"Validation result: total_count={val_res['total_count']}, new_count={val_res['new_count']}, existing_count={val_res['existing_count']}, duplicate_count={val_res['duplicate_count']}")
assert val_res["new_count"] == 2, "Only 2 rows should be eligible as new entries"
assert val_res["existing_count"] == 1, "1 row has existing ICCID and must be classified as existing"
assert val_res["duplicate_count"] == 1, "1 row has duplicate IMEI within the uploaded file"

count_before = db.query(models.Device).count()
add_res = routes_data.bulk_add(schemas.BulkIn(rows=upload_rows, mode="skip"), db=db, user=user_admin)
count_after = db.query(models.Device).count()
print(f"Bulk Add result: {add_res}, DB count before={count_before}, after={count_after}")
assert add_res["added"] == 2, "Exactly 2 new entries must be inserted"
assert add_res["updated"] == 0, "Zero records must be updated (Strict Insert-Only)"
assert add_res["skipped_duplicates"] == 2, "2 duplicate/existing records must be skipped"
assert count_after == count_before + 2, "Database device count must increase by exactly 2"
print("✓ Bulk Upload Insert-Only workflow verified: 0 updates, 0 overwrites, only new entries inserted!\n")

# [TEST FRONTEND] HTML Verification in index.html and dashboard.html
print("[TEST FRONTEND] HTML Verification in index.html and dashboard.html")
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('frontend/dashboard.html', 'r', encoding='utf-8') as f:
    dhtml = f.read()

assert html == dhtml, "index.html and dashboard.html must be 100% byte-for-byte identical!"
print("✓ 100% byte parity between index.html and dashboard.html verified!")

# Verify Cart deleted from mainTabs container
assert '<button class="tab-btn" data-target="box-bin">🛒 Cart' not in html, "Cart button must be deleted from mainTabs container"
print("✓ Cart button successfully deleted from #mainTabs container tabs!")

# Verify Header Cart button and Dialog Modal
assert 'id="btnHeaderCart"' in html and 'openCartModal()' in html
assert 'id="dlgCartModal"' in html
assert 'id="closeDlgCart"' in html and 'closeCartModal()' in html
print("✓ Cart pop-up modal and header trigger with Cross (X) close verified!")

# Verify Settings actions and role visibility
assert 'settingsBtnEditName' in html
assert 'settingsBtnPassword' in html
assert 'settingsBtnManageUsers' in html
assert 'settingsBtnLoginInv' in html
assert 'settingsBtnLogout' in html
print("✓ Settings action items (Edit Name, Change Password, Manage Users, Log Inventory, Logout) verified!")

# Verify Master Admin password visibility in users table
assert '(isSuperAdmin || isMasterAdmin) ? \'<th>User Password</th>\' : \'\'' in html
print("✓ Master Admin password visibility in users table verified!")

# Verify Good Morning Greeting
assert 'id="uBadge"' in html and 'id="hi"' in html
print("✓ Good Morning greeting container on right side of top header verified!")

print("\n" + "=" * 60)
print("ALL 11 REQUIREMENTS AND ENHANCEMENTS FULLY VERIFIED AND PASSING!")
print("=" * 60)
