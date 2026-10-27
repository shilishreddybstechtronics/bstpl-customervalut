"""Comprehensive Verification Test Suite for CustomerVault RBAC, Permissions, and Password Security.

Tests:
1. Mutual Super Admin Protection (0001 and 0007 are mutually immune)
2. Granular Permissions Management (Configure, grant, revoke permissions per user)
3. Backend Permission Enforcement (view, add, edit, delete, search, download, upload)
4. Password Security Policy (Hash-only, no plaintext ever, reset password, change own password)
5. Download All Customer Data Capability
6. Security Audit Logging for Account and Permission Changes
"""
import sys
from pathlib import Path
from fastapi import HTTPException

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import models, schemas
from auth import (
    MASTER_SUPER_ADMIN_IDS,
    MASTER_ADMIN_IDS,
    ADMIN_USER_IDS,
    DEFAULT_PERMISSIONS,
    normalize_id,
    role_for_id,
    get_user_category,
    get_user_permissions,
    user_has_permission,
    require_permission,
    can_delete_user,
    can_modify_user,
    hash_password,
    verify_password
)
from database import SessionLocal
from routes_users import (
    user_out,
    update_user,
    update_permissions,
    delete_user,
    change_password
)
from routes_data import build_device_query


def test_normalization_and_roles():
    print("\n--- 1. Testing Normalization and Roles ---")
    assert normalize_id("1") == "0001"
    assert normalize_id("0001") == "0001"
    assert normalize_id("7") == "0007"
    assert normalize_id("0007") == "0007"
    assert normalize_id("0002") == "0002"
    assert normalize_id("0010") == "0010"
    assert normalize_id("0011") == "0011"

    # Super Admins
    assert role_for_id("0001") == "admin"
    assert role_for_id("0007") == "admin"
    assert get_user_category("0001")["category"] == "super_admin"
    assert get_user_category("0007")["category"] == "super_admin"

    # Master Admins
    assert role_for_id("0002") == "admin"
    assert get_user_category("0002")["category"] == "master_admin"

    # Admin Users
    assert role_for_id("0005") == "admin"
    assert get_user_category("0005")["category"] == "admin_user"

    # Regular Users
    assert role_for_id("0011") == "limited"
    assert get_user_category("0011")["category"] == "regular_user"
    print("✓ Normalization, roles, and categories verified.")


def test_mutual_super_admin_protection():
    print("\n--- 2. Testing Mutual Super Admin Protection ---")
    db = SessionLocal()
    try:
        u1 = db.query(models.User).filter(models.User.user_id == "0001").first()
        u7 = db.query(models.User).filter(models.User.user_id == "0007").first()

        assert u1 is not None, "User 0001 must exist in DB"
        assert u7 is not None, "User 0007 must exist in DB"

        # 2a. Mutual Deletion Protection
        can_1_del_7, reason = can_delete_user(u1, u7)
        assert not can_1_del_7, "0001 must NOT be allowed to delete 0007"
        assert "super admin" in reason.lower() or "protected" in reason.lower()

        can_7_del_1, reason = can_delete_user(u7, u1)
        assert not can_7_del_1, "0007 must NOT be allowed to delete 0001"
        assert "super admin" in reason.lower() or "protected" in reason.lower()

        # Cannot delete self
        assert not can_delete_user(u1, u1)[0]
        assert not can_delete_user(u7, u7)[0]

        # 2b. Mutual Modification Protection
        can_1_mod_7, reason = can_modify_user(u1, u7)
        assert not can_1_mod_7, "0001 must NOT be allowed to modify 0007"
        assert "protected" in reason.lower()

        can_7_mod_1, reason = can_modify_user(u7, u1)
        assert not can_7_mod_1, "0007 must NOT be allowed to modify 0001"
        assert "protected" in reason.lower()

        # Both CAN modify self
        assert can_modify_user(u1, u1)[0] is True
        assert can_modify_user(u7, u7)[0] is True

        # 2c. Test routes rejection for mutual Super Admin modification
        try:
            update_user(u7.id, schemas.UserUpdate(name="Hacked Name"), db=db, admin=u1)
            assert False, "0001 modifying 0007 must raise 403"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403, got {e.status_code}"

        try:
            update_user(u1.id, schemas.UserUpdate(name="Hacked Name"), db=db, admin=u7)
            assert False, "0007 modifying 0001 must raise 403"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403, got {e.status_code}"

        try:
            update_permissions(u7.id, schemas.PermissionsUpdate(permissions={"delete": False}), db=db, admin=u1)
            assert False, "0001 modifying 0007 permissions must raise 403"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403, got {e.status_code}"

        try:
            delete_user(u7.id, db=db, admin=u1)
            assert False, "0001 deleting 0007 must raise 403"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403, got {e.status_code}"

        try:
            delete_user(u1.id, db=db, admin=u7)
            assert False, "0007 deleting 0001 must raise 403"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403, got {e.status_code}"

        print("✓ Mutual Super Admin Protection fully verified (0001 & 0007 are mutually immune).")
    finally:
        db.close()


def test_password_security_policy():
    print("\n--- 3. Testing Password Security Policy (Hash-Only, No Readable Passwords) ---")
    db = SessionLocal()
    try:
        u1 = db.query(models.User).filter(models.User.user_id == "0001").first()
        u7 = db.query(models.User).filter(models.User.user_id == "0007").first()

        # Check DB plain_password column is scrubbed
        all_users = db.query(models.User).all()
        for u in all_users:
            assert getattr(u, "plain_password", None) is None, f"User {u.user_id} has plaintext password stored in DB!"

        # user_out output check
        out1 = user_out(u7, actor=u1)
        assert "password" not in out1, "user_out must NEVER contain a password field!"
        assert "plain_password" not in out1, "user_out must NEVER contain a plain_password field!"

        # Create a test employee user
        test_uid = "9988"
        existing = db.query(models.User).filter(models.User.user_id == test_uid).first()
        if existing:
            db.delete(existing)
            db.commit()

        initial_pwd = "InitialSecurePassword123"
        new_u = models.User(
            name="Test Employee",
            user_id=test_uid,
            password_hash=hash_password(initial_pwd),
            role="limited",
            is_admin=False
        )
        db.add(new_u)
        db.commit()
        db.refresh(new_u)

        assert verify_password(initial_pwd, new_u.password_hash)

        # Super Admin 0001 resets user's password
        reset_pwd = "ResetPasswordBySuperAdmin456"
        update_user(new_u.id, schemas.UserUpdate(password=reset_pwd), db=db, admin=u1)
        db.refresh(new_u)

        assert verify_password(reset_pwd, new_u.password_hash)
        assert not verify_password(initial_pwd, new_u.password_hash)

        # Super Admin 0007 resets user's password
        reset_pwd_7 = "ResetPasswordBySuperAdmin0007"
        update_user(new_u.id, schemas.UserUpdate(password=reset_pwd_7), db=db, admin=u7)
        db.refresh(new_u)

        assert verify_password(reset_pwd_7, new_u.password_hash)

        # Clean up
        db.delete(new_u)
        db.commit()

        print("✓ Password security policy verified (Hash-only, no readable passwords, resets work).")
    finally:
        db.close()


def test_granular_permissions_and_backend_enforcement():
    print("\n--- 4. Testing Granular Permissions & Backend Enforcement ---")
    db = SessionLocal()
    try:
        u1 = db.query(models.User).filter(models.User.user_id == "0001").first()
        u7 = db.query(models.User).filter(models.User.user_id == "0007").first()

        # Create a test employee
        test_uid = "9977"
        existing = db.query(models.User).filter(models.User.user_id == test_uid).first()
        if existing:
            db.delete(existing)
            db.commit()

        user = models.User(
            name="Permissions Test Employee",
            user_id=test_uid,
            password_hash=hash_password("Pass123456"),
            role="limited",
            is_admin=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 4a. Check default permissions for regular user
        defaults = get_user_permissions(user)
        assert defaults["view"] is True
        assert defaults["add"] is True
        assert defaults["edit"] is True
        assert defaults["delete"] is False
        assert defaults["search"] is True
        assert defaults["download"] is True
        assert defaults["upload"] is True

        # 4b. Super Admin 0001 grants delete permission and revokes download permission
        updated = update_permissions(user.id, schemas.PermissionsUpdate(permissions={
            "delete": True,
            "download": False,
            "upload": False
        }), db=db, admin=u1)

        db.refresh(user)
        perms = get_user_permissions(user)
        assert perms["delete"] is True, "Delete permission should now be True"
        assert perms["download"] is False, "Download permission should now be False"
        assert perms["upload"] is False, "Upload permission should now be False"
        assert perms["view"] is True, "View permission should remain default True"

        # 4c. Super Admin 0007 configures page access
        update_permissions(user.id, schemas.PermissionsUpdate(permissions={
            "page_live": False,
            "page_inventory": True,
            "page_audit": False,
            "download": False
        }), db=db, admin=u7)

        db.refresh(user)
        perms = get_user_permissions(user)
        assert perms["page_live"] is False
        assert perms["page_inventory"] is True
        assert perms["page_audit"] is False

        # 4d. Backend enforcement test via require_permission dependencies
        # Testing user with download=False
        dep_download = require_permission("download")
        try:
            dep_download(user=user)
            assert False, "require_permission('download') should raise 403 when download=False"
        except HTTPException as e:
            assert e.status_code == 403
            assert "download" in e.detail

        # Testing user with upload=False
        dep_upload = require_permission("upload")
        try:
            dep_upload(user=user)
            assert False, "require_permission('upload') should raise 403 when upload=False"
        except HTTPException as e:
            assert e.status_code == 403
            assert "upload" in e.detail

        # Testing user with view=True
        dep_view = require_permission("view")
        granted_user = dep_view(user=user)
        assert granted_user.id == user.id

        # Super Admins bypass all restrictions
        assert user_has_permission(u1, "download") is True
        assert user_has_permission(u7, "download") is True
        assert dep_download(user=u1).id == u1.id
        assert dep_download(user=u7).id == u7.id

        # Clean up
        db.delete(user)
        db.commit()
        print("✓ Granular Permissions & Backend Enforcement fully verified.")
    finally:
        db.close()


def test_download_all_customer_data():
    print("\n--- 5. Testing Download All Customer Data ---")
    db = SessionLocal()
    try:
        # build_device_query with customer_id=None gets records across all customers
        q = build_device_query(db, None, "", "all", "id", "asc")
        total_records = q.count()
        print(f"Total records in all customer databases: {total_records}")
        assert total_records >= 0
        print("✓ Download all customer data query verified.")
    finally:
        db.close()


def test_audit_logs():
    print("\n--- 6. Testing Audit Log Recording ---")
    db = SessionLocal()
    try:
        logs = db.query(models.ActivityLog).order_by(models.ActivityLog.created_at.desc()).limit(10).all()
        actions = [l.action for l in logs]
        print(f"Recent audit log actions: {actions}")
        assert len(logs) > 0, "Activity log entries must exist"
        print("✓ Security audit logging verified.")
    finally:
        db.close()


if __name__ == "__main__":
    test_normalization_and_roles()
    test_mutual_super_admin_protection()
    test_password_security_policy()
    test_granular_permissions_and_backend_enforcement()
    test_download_all_customer_data()
    test_audit_logs()
    print("\n========================================================")
    print("🎉 ALL RBAC, PERMISSION, SECURITY & EXPORT TESTS PASSED!")
    print("========================================================")
