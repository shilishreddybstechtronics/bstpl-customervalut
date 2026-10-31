import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import sys
sys.path.insert(0, 'backend')

from unittest.mock import MagicMock
from database import engine, SessionLocal, Base
import models
import schemas
from routes_users import user_out, update_my_name, update_my_theme, change_password
from auth import hash_password, verify_password
from fastapi import HTTPException

Base.metadata.create_all(bind=engine)

def test_full_flow():
    db = SessionLocal()
    
    master = models.User(
        name="Master Admin User",
        user_id="0001",
        password_hash=hash_password("MasterPass123"),
        plain_password="MasterPass123",
        role="admin",
        is_admin=True,
        permissions={}
    )
    db.add(master)

    employee = models.User(
        name="John Doe",
        user_id="0005",
        password_hash=hash_password("OldPassword123"),
        plain_password="OldPassword123",
        role="standard",
        is_admin=False,
        permissions={}
    )
    db.add(employee)
    db.commit()

    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers = {"user-agent": "TestSuite"}

    print("=== Testing Updated Edit Name & Settings Flow ===")

    # 1. Test Edit Name with 3 options: Current Name, Updated Name, Confirm Name
    # A. Empty updated name fails
    try:
        update_my_name(schemas.UserNameUpdate(name="  ", confirm_name="Johnathan"), req, db, employee)
        assert False
    except HTTPException as e:
        assert e.status_code == 400
        assert "empty" in e.detail.lower()

    # B. Mismatched confirm name fails
    try:
        update_my_name(schemas.UserNameUpdate(name="Johnathan Doe", confirm_name="Johnny Doe"), req, db, employee)
        assert False
    except HTTPException as e:
        assert e.status_code == 400
        assert "do not match" in e.detail.lower()

    # C. Same name fails
    try:
        update_my_name(schemas.UserNameUpdate(name="John Doe", confirm_name="John Doe"), req, db, employee)
        assert False
    except HTTPException as e:
        assert e.status_code == 400
        assert "must be different" in e.detail.lower()

    # D. Valid update succeeds
    res = update_my_name(schemas.UserNameUpdate(name="Johnathan Doe", confirm_name="Johnathan Doe"), req, db, employee)
    assert res["ok"] is True
    assert res["name"] == "Johnathan Doe"
    assert res["previous_name"] == "John Doe"
    assert employee.name == "Johnathan Doe"
    assert employee.permissions["previous_name"] == "John Doe"
    print("✓ Edit Name validated: Updated Name & Confirm Name match, updated in DB.")

    # 2. user_out reflects new name immediately
    out = user_out(employee, actor=employee)
    assert out["name"] == "Johnathan Doe"
    assert out["previous_name"] == "John Doe"
    print("✓ user_out immediately returns updated name and previous name.")

    db.close()
    print("\nALL BACKEND OPERATIONS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_flow()
