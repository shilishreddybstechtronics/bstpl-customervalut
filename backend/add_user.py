#!/usr/bin/env python3
"""add_user.py - create a login directly in MySQL (use this for the admin IDs 0001, 0002, 0003, 1234).
Run:  python backend/add_user.py            -> asks for name, ID, password; the access level comes from config.py (ROLES / DEFAULT_ROLE)
      python backend/add_user.py --admin    -> forces admin access"""
import getpass
import sys

import database as db

try:
    db.init_db()
except Exception as e:
    sys.exit(db.explain_connect_error(e))
name = input("Employee name: ").strip()
emp_id = input("Employee ID  : ").strip()
pw = getpass.getpass("Password (min 6): ")
role = "admin" if "--admin" in sys.argv else None
try:
    db.register(name, emp_id, pw, role=role, allow_reserved=True)
except ValueError as e:
    sys.exit(f"Not created: {e}")
print(f"Created {name} (ID {emp_id}) - access: {db.role_of(emp_id, name, role)}")
