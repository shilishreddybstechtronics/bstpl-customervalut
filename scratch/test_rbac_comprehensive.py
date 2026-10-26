"""Comprehensive RBAC Integration and Unit Tests for SIM Upload Application."""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import models, schemas
from auth import (
    MASTER_SUPER_ADMIN_ID,
    MASTER_ADMIN_IDS,
    ADMIN_USER_IDS,
    role_for_id,
    get_user_category,
    can_delete_user,
    normalize_id
)
from database import SessionLocal
from routes_users import delete_user, create_user, update_user
from fastapi import HTTPException

def test_normalization():
    assert normalize_id("1") == "0001"
    assert normalize_id("0001") == "0001"
    assert normalize_id("0002") == "0002"
    assert normalize_id("2") == "0002"
    assert normalize_id("0004") == "0004"
    assert normalize_id("0010") == "0010"
    assert normalize_id("0011") == "0011"
    assert normalize_id("1024") == "1024"
    print("✓ Normalization passed")

def test_role_mapping():
    # 0001 - 0004: Master Admins (admin)
    assert role_for_id("0001") == "admin"
    assert role_for_id("0002") == "admin"
    assert role_for_id("0003") == "admin"
    assert role_for_id("0004") == "admin"

    # 0005 - 0010: Admin Users (admin)
    assert role_for_id("0005") == "admin"
    assert role_for_id("0006") == "admin"
    assert role_for_id("0007") == "admin"
    assert role_for_id("0008") == "admin"
    assert role_for_id("0009") == "admin"
    assert role_for_id("0010") == "admin"

    # After 0010: Regular Users (limited)
    assert role_for_id("0011") == "limited"
    assert role_for_id("0012") == "limited"
    assert role_for_id("0099") == "limited"
    assert role_for_id("1000") == "limited"
    print("✓ Role mapping passed")

def test_categories():
    assert get_user_category("0001")["category"] == "super_admin"
    assert get_user_category("0002")["category"] == "master_admin"
    assert get_user_category("0003")["category"] == "master_admin"
    assert get_user_category("0004")["category"] == "master_admin"
    assert get_user_category("0005")["category"] == "admin_user"
    assert get_user_category("0010")["category"] == "admin_user"
    assert get_user_category("0011")["category"] == "regular_user"
    print("✓ Categories passed")

def make_user(uid: int, user_id: str, role: str):
    u = models.User(id=uid, name=f"User {user_id}", user_id=user_id, role=role, is_admin=(role == "admin"))
    return u

def test_deletion_matrix():
    u0001 = make_user(1, "0001", "admin")
    u0002 = make_user(2, "0002", "admin")
    u0003 = make_user(3, "0003", "admin")
    u0004 = make_user(4, "0004", "admin")
    u0005 = make_user(5, "0005", "admin")
    u0010 = make_user(10, "0010", "admin")
    u0015 = make_user(15, "0015", "limited")
    u0020 = make_user(20, "0020", "limited")

    # 1. Master Admin 0001:
    # Cannot delete self
    can, reason = can_delete_user(u0001, u0001)
    assert not can and "cannot delete your own account" in reason.lower()
    # Can delete 0002, 0003, 0004
    assert can_delete_user(u0001, u0002)[0] is True
    assert can_delete_user(u0001, u0003)[0] is True
    assert can_delete_user(u0001, u0004)[0] is True
    # Can delete 0005-0010
    assert can_delete_user(u0001, u0005)[0] is True
    assert can_delete_user(u0001, u0010)[0] is True
    # Can delete regular users
    assert can_delete_user(u0001, u0015)[0] is True
    print("✓ Master Admin 0001 deletion rules passed")

    # 2. Master Admins 0002, 0003, 0004:
    for actor in [u0002, u0003, u0004]:
        # Cannot delete 0001
        can, reason = can_delete_user(actor, u0001)
        assert not can, f"{actor.user_id} should not be able to delete 0001"
        # Cannot delete self
        can, reason = can_delete_user(actor, actor)
        assert not can and "cannot delete your own account" in reason.lower()
        # Cannot delete one another (0001, 0002, 0003, 0004)
        for target in [u0002, u0003, u0004]:
            if target.id != actor.id:
                can, reason = can_delete_user(actor, target)
                assert not can, f"{actor.user_id} must not be able to delete {target.user_id}"
                assert "cannot delete one another" in reason or "cannot delete" in reason.lower()
        # Can delete Admin Users 0005-0010
        assert can_delete_user(actor, u0005)[0] is True
        assert can_delete_user(actor, u0010)[0] is True
        # Can delete regular users
        assert can_delete_user(actor, u0015)[0] is True
        assert can_delete_user(actor, u0020)[0] is True
    print("✓ Master Admins 0002-0004 deletion rules passed")

    # 3. Admin Users 0005 through 0010:
    for actor in [u0005, u0010]:
        # Cannot delete ANY user account
        for target in [u0001, u0002, u0003, u0004, u0005, u0010, u0015]:
            can, reason = can_delete_user(actor, target)
            assert not can, f"Admin user {actor.user_id} should NOT be able to delete {target.user_id}"
            if actor.id != target.id:
                assert "0005 through 0010" in reason or "protected" in reason.lower()
    print("✓ Admin Users 0005-0010 deletion restriction passed")

    # 4. Regular Users (> 0010):
    for actor in [u0015, u0020]:
        for target in [u0001, u0002, u0005, u0015, u0020]:
            can, reason = can_delete_user(actor, target)
            assert not can
    print("✓ Regular Users deletion restriction passed")

def test_api_endpoint_protections():
    db = SessionLocal()
    try:
        # Check active master user exists
        master = db.query(models.User).filter(models.User.user_id == "0001").first()
        if not master:
            print("Master user 0001 not in DB, skipping DB route tests")
            return

        # Attempt to delete master user by a simulated admin user 0005
        u0005 = make_user(999, "0005", "admin")
        try:
            delete_user(master.id, db=db, admin=u0005)
            assert False, "0005 should not have been allowed to delete 0001!"
        except HTTPException as e:
            assert e.status_code == 403
            print(f"✓ API rejected 0005 deleting 0001 with 403: {e.detail}")

        # Attempt to delete master user by a simulated master admin 0002
        u0002 = make_user(998, "0002", "admin")
        try:
            delete_user(master.id, db=db, admin=u0002)
            assert False, "0002 should not have been allowed to delete 0001!"
        except HTTPException as e:
            assert e.status_code == 403
            print(f"✓ API rejected 0002 deleting 0001 with 403: {e.detail}")

        # Attempt 0005 creating 0002 (Master Admin)
        try:
            create_user(schemas.UserCreate(name="Test 0002", user_id="0002", password="password123"), db=db, admin=u0005)
            assert False, "0005 should not have been allowed to create 0002!"
        except HTTPException as e:
            assert e.status_code == 403
            print(f"✓ API rejected 0005 creating 0002 with 403: {e.detail}")

        print("✓ All direct API protection tests passed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    test_normalization()
    test_role_mapping()
    test_categories()
    test_deletion_matrix()
    test_api_endpoint_protections()
    print("\nALL RBAC TESTS PASSED SUCCESSFULLY!")
