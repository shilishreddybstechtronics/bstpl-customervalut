"""Checks the Manage Users / Login Inventory rules. Run from the backend folder:  python test_user_rules.py
Uses a throw-away SQLite file and never touches your real database."""
import os, tempfile
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "rules_test.db")

import models
import auth
from auth import (can_delete_user, can_modify_user, can_manage_privileges, clean_permissions, get_user_category,
                  is_admin_tier, role_for_user, user_has_permission, require_login_inventory_access, get_user_permissions)

_n = [0]
def U(user_id, category=None, perms=None, role=""):
    _n[0] += 1
    p = dict(perms or {})
    if category:
        p["role"] = category
    u = models.User(name=user_id, user_id=user_id, password_hash="x", role=role, permissions=p or None)
    u.id = _n[0]
    return u

S1, S7 = U("0001"), U("0007")
M2, M3 = U("0002"), U("0003")
A5, A6 = U("0005"), U("0006")
M11 = U("0011", "master_admin")      # master admin created later (ID above 0010)
A12 = U("0012", "admin_user")        # regular admin created later
R13, R14 = U("0013", "regular_user"), U("0014")

def deny(fn, *a):
    ok, _ = fn(*a); assert not ok, f"{fn.__name__}({a[0].user_id}->{a[1].user_id}) should be refused"
def allow(fn, *a):
    ok, why = fn(*a); assert ok, f"{fn.__name__}({a[0].user_id}->{a[1].user_id}) should be allowed: {why}"

# tiers
for u, c in ((S1, "super_admin"), (S7, "super_admin"), (M2, "master_admin"), (A5, "admin_user"),
             (M11, "master_admin"), (A12, "admin_user"), (R13, "regular_user"), (R14, "regular_user")):
    assert get_user_category(u)["category"] == c, (u.user_id, get_user_category(u)["category"])

# created-later admins keep admin access (they used to be demoted to 'limited' on every login/restart)
assert role_for_user(M11) == "admin" and role_for_user(A12) == "admin" and role_for_user(R13) == "limited"
assert is_admin_tier(M11) and is_admin_tier(A12) and not is_admin_tier(R13)

# MASTER ADMINS: delete anyone except themselves (and the protected Super Admins)
for target in (M3, A5, A6, M11, A12, R13, R14):
    allow(can_delete_user, M2, target)
for target in (M2, S1, S7):
    deny(can_delete_user, M2, target)
allow(can_delete_user, M11, M2); deny(can_delete_user, M11, M11)       # a later-created master admin works the same

# SUPER ADMINS: delete anyone except themselves and each other
for target in (M2, M11, A5, A12, R13):
    allow(can_delete_user, S1, target)
for target in (S1, S7):
    deny(can_delete_user, S1, target)
deny(can_delete_user, S7, S1)

# ADMIN USERS / REGULAR USERS
for target in (A6, A12, R13):
    allow(can_delete_user, A5, target)
for target in (A5, M2, M11, S1):
    deny(can_delete_user, A5, target) if target is not A5 else None
deny(can_delete_user, A5, A5)
for target in (R14, A5, M2, S1):
    deny(can_delete_user, R13, target)

# modify: super admins protected, master admins protected from each other, admins cannot touch masters
allow(can_modify_user, S1, M2); deny(can_modify_user, S1, S7); deny(can_modify_user, M2, S1)
deny(can_modify_user, M2, M3); allow(can_modify_user, M2, A5); allow(can_modify_user, M2, M2)
deny(can_modify_user, A5, M2); allow(can_modify_user, A5, R13); deny(can_modify_user, R13, R14)

# PRIVILEGES: only Super Admins, never on a Super Admin
for target in (M2, M11, A5, R13):
    allow(can_manage_privileges, S1, target); allow(can_manage_privileges, S7, target)
    deny(can_manage_privileges, M2, target) if target is not M2 else None
deny(can_manage_privileges, S1, S7); deny(can_manage_privileges, M2, M2); deny(can_manage_privileges, A5, R13)

# permission input is validated
assert clean_permissions({"page_audit": True, "delete": False}) == {"page_audit": True, "delete": False}
for bad in ({"role": True}, {"page_audit": "yes"}, {"made_up": True}):
    try:
        clean_permissions(bad); raise AssertionError(f"{bad} should be rejected")
    except ValueError:
        pass

# LOGIN INVENTORY: super always, master by default, everyone else only if a Super Admin switched it on
assert require_login_inventory_access(S1) is S1 and require_login_inventory_access(M2) is M2
for u in (A5, R13):
    try:
        require_login_inventory_access(u); raise AssertionError(f"{u.user_id} should be refused")
    except auth.HTTPException as e:
        assert e.status_code == 403
granted = U("0015", "regular_user", {"page_audit": True})
assert require_login_inventory_access(granted) is granted                 # a Super Admin granted it
revoked = U("0016", "master_admin", {"page_audit": False})
try:
    require_login_inventory_access(revoked); raise AssertionError("revoked master must be refused")
except auth.HTTPException:
    pass
assert user_has_permission(S1, "page_audit") and not get_user_permissions(S1) == {}

print("ALL MANAGE-USERS / LOGIN-INVENTORY RULE CHECKS PASSED")
