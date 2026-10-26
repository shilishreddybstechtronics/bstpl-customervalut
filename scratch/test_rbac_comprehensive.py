"""Comprehensive RBAC Integration and Unit Tests for SIM Upload Application."""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import models, schemas
from auth import (
    MASTER_SUPER_ADMIN_IDS,
    MASTER_SUPER_ADMIN_ID,
    MASTER_ADMIN_IDS,
    ADMIN_USER_IDS,
    role_for_id,
    get_user_category,
    can_delete_user,
    normalize_id
)
from database import SessionLocal
from routes_users import delete_user, create_user, update_user, update_my_name, user_out
from fastapi import HTTPException

def test_normalization():
    assert normalize_id("1") == "0001"
    assert normalize_id("0001") == "0001"
    assert normalize_id("0002") == "0002"
    assert normalize_id("2") == "0002"
    assert normalize_id("0004") == "0004"
    assert normalize_id("0007") == "0007"
    assert normalize_id("7") == "0007"
    assert normalize_id("0010") == "0010"
    assert normalize_id("0011") == "0011"
    assert normalize_id("1024") == "1024"
    print("✓ Normalization passed")

def test_role_mapping():
    # 0001 & 0007: Super Admins (admin)
    assert role_for_id("0001") == "admin"
    assert role_for_id("0007") == "admin"

    # 0002, 0003, 0004: Master Admins (admin)
    assert role_for_id("0002") == "admin"
    assert role_for_id("0003") == "admin"
    assert role_for_id("0004") == "admin"

    # 0005, 0006, 0008, 0009, 0010: Admin Users (admin)
    assert role_for_id("0005") == "admin"
    assert role_for_id("0006") == "admin"
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
    assert get_user_category("0007")["category"] == "super_admin"
    assert get_user_category("0002")["category"] == "master_admin"
    assert get_user_category("0003")["category"] == "master_admin"
    assert get_user_category("0004")["category"] == "master_admin"
    assert get_user_category("0005")["category"] == "admin_user"
    assert get_user_category("0006")["category"] == "admin_user"
    assert get_user_category("0008")["category"] == "admin_user"
    assert get_user_category("0010")["category"] == "admin_user"
    assert get_user_category("0011")["category"] == "regular_user"
    print("✓ Categories passed")

def make_user(uid: int, user_id: str, role: str, plain_password: str = "Secret123"):
    u = models.User(id=uid, name=f"User {user_id}", user_id=user_id, role=role, is_admin=(role == "admin"), plain_password=plain_password)
    return u

def test_deletion_matrix():
    u0001 = make_user(1, "0001", "admin")
    u0007 = make_user(7, "0007", "admin")
    u0002 = make_user(2, "0002", "admin")
    u0003 = make_user(3, "0003", "admin")
    u0004 = make_user(4, "0004", "admin")
    u0005 = make_user(5, "0005", "admin")
    u0006 = make_user(6, "0006", "admin")
    u0010 = make_user(10, "0010", "admin")
    u0015 = make_user(15, "0015", "limited")
    u0020 = make_user(20, "0020", "limited")

    # 1. Master Super Admins (0001, 0007):
    for super_admin in [u0001, u0007]:
        # Cannot delete self
        can, reason = can_delete_user(super_admin, super_admin)
        assert not can and "cannot delete your own account" in reason.lower()
        # Can delete 0002, 0003, 0004
        assert can_delete_user(super_admin, u0002)[0] is True
        assert can_delete_user(super_admin, u0003)[0] is True
        assert can_delete_user(super_admin, u0004)[0] is True
        # Can delete 0005, 0006, 0010
        assert can_delete_user(super_admin, u0005)[0] is True
        assert can_delete_user(super_admin, u0006)[0] is True
        assert can_delete_user(super_admin, u0010)[0] is True
        # Can delete regular users
        assert can_delete_user(super_admin, u0015)[0] is True
    print("✓ Master Super Admins 0001 and 0007 deletion rules passed")

    # 2. Master Admins 0002, 0003, 0004:
    for actor in [u0002, u0003, u0004]:
        # Cannot delete Super Admins 0001, 0007
        assert not can_delete_user(actor, u0001)[0]
        assert not can_delete_user(actor, u0007)[0]
        # Cannot delete self
        can, reason = can_delete_user(actor, actor)
        assert not can and "cannot delete your own account" in reason.lower()
        # Cannot delete one another
        for target in [u0002, u0003, u0004]:
            if target.id != actor.id:
                can, reason = can_delete_user(actor, target)
                assert not can
        # Can delete Admin Users 0005, 0006, 0010
        assert can_delete_user(actor, u0005)[0] is True
        assert can_delete_user(actor, u0006)[0] is True
        assert can_delete_user(actor, u0010)[0] is True
        # Can delete regular users
        assert can_delete_user(actor, u0015)[0] is True
    print("✓ Master Admins 0002-0004 deletion rules passed")

    # 3. Admin Users (0005, 0006, 0010): CAN delete Admin Users and regular users!
    for actor in [u0005, u0006, u0010]:
        # Cannot delete Super Admins (0001, 0007)
        assert not can_delete_user(actor, u0001)[0]
        assert not can_delete_user(actor, u0007)[0]
        # Cannot delete Master Admins (0002, 0003, 0004)
        assert not can_delete_user(actor, u0002)[0]
        assert not can_delete_user(actor, u0003)[0]
        assert not can_delete_user(actor, u0004)[0]
        # Cannot delete self
        assert not can_delete_user(actor, actor)[0]
        # CAN delete other Admin Users!
        other_admins = [x for x in [u0005, u0006, u0010] if x.id != actor.id]
        for target in other_admins:
            can, _ = can_delete_user(actor, target)
            assert can is True, f"Admin {actor.user_id} should be allowed to delete admin {target.user_id}"
        # CAN delete regular users!
        assert can_delete_user(actor, u0015)[0] is True
    print("✓ Admin Users deletion rules passed (admin can delete admin user & regular users)")

    # 4. Regular Users (> 0010):
    for actor in [u0015, u0020]:
        for target in [u0001, u0007, u0002, u0005, u0015]:
            can, _ = can_delete_user(actor, target)
            assert not can
    print("✓ Regular Users deletion restriction passed")

def test_password_visibility():
    u0001 = make_user(1, "0001", "admin", "SuperSecret0001")
    u0007 = make_user(7, "0007", "admin", "SuperSecret0007")
    u0002 = make_user(2, "0002", "admin", "Secret0002")
    u0005 = make_user(5, "0005", "admin", "UserPass0005")
    u0015 = make_user(15, "0015", "limited", "RegPass0015")

    # Viewed by Master Super Admin (0001):
    out = user_out(u0005, actor=u0001)
    assert out["password"] == "UserPass0005", "Master Admin 0001 must see user password"

    # Viewed by Master Super Admin (0007):
    out7 = user_out(u0015, actor=u0007)
    assert out7["password"] == "RegPass0015", "Master Admin 0007 must see user password"

    # Viewed by Master Admin (0002):
    out2 = user_out(u0005, actor=u0002)
    assert out2["password"] == "UserPass0005", "Master Admin 0002 must see user password"

    # Viewed by non-master Admin (0005):
    out5 = user_out(u0015, actor=u0005)
    assert out5["password"] is None, "Non-master admin must NOT see password"

    print("✓ Password visibility for master admins passed")

if __name__ == "__main__":
    test_normalization()
    test_role_mapping()
    test_categories()
    test_deletion_matrix()
    test_password_visibility()
    print("\nALL RBAC & USER TESTS PASSED SUCCESSFULLY!")
