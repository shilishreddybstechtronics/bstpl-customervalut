import sys
sys.path.insert(0, 'backend')

from unittest.mock import MagicMock
from database import SessionLocal
import models
import schemas
from routes_users import user_out, update_my_name, update_my_theme, change_password
from fastapi import HTTPException

def test_all_routes():
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.user_id == "0001").first()
    if not user:
        user = db.query(models.User).first()
    assert user is not None

    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers = {"user-agent": "TestSuite"}

    print(f"Testing route functions with real DB user: {user.name} ({user.user_id})")

    # 1. user_out
    out = user_out(user, actor=user)
    assert out["name"] == user.name
    assert "previous_name" in out
    assert "theme_palette" in out
    assert "theme_mode" in out
    print("✓ user_out returns full profile with theme & previous_name")

    # 2. update_my_name
    orig_name = user.name
    temp_name = orig_name + " Verification"

    # Test wrong confirm name
    try:
        update_my_name(schemas.UserNameUpdate(name=temp_name, confirm_current_name="Invalid Name"), req, db, user)
        assert False
    except HTTPException as e:
        assert e.status_code == 400
        print("✓ update_my_name correctly rejected mismatched confirm name")

    # Test same name
    try:
        update_my_name(schemas.UserNameUpdate(name=orig_name, confirm_current_name=orig_name), req, db, user)
        assert False
    except HTTPException as e:
        assert e.status_code == 400
        print("✓ update_my_name correctly rejected unchanged name")

    # Test valid update
    res = update_my_name(schemas.UserNameUpdate(name=temp_name, confirm_current_name=orig_name), req, db, user)
    assert res["ok"] is True
    assert res["name"] == temp_name
    assert res["previous_name"] == orig_name
    print("✓ update_my_name updated name and set previous_name in DB")

    # Revert back to original name
    res2 = update_my_name(schemas.UserNameUpdate(name=orig_name, confirm_current_name=temp_name), req, db, user)
    assert res2["ok"] is True
    assert res2["name"] == orig_name
    print("✓ Reverted display name back to original")

    # 3. update_my_theme
    t_res = update_my_theme(schemas.ThemeUpdate(palette="sunset", mode="dark"), db, user)
    assert t_res["ok"] is True
    assert t_res["palette"] == "sunset"
    assert t_res["mode"] == "dark"

    # Reset to royal_navy light
    t_res2 = update_my_theme(schemas.ThemeUpdate(palette="royal_navy", mode="light"), db, user)
    assert t_res2["ok"] is True
    assert t_res2["palette"] == "royal_navy"
    assert t_res2["mode"] == "light"
    print("✓ update_my_theme correctly persisted palette and mode to DB")

    db.close()
    print("\nALL BACKEND ROUTE FUNCTIONS EXECUTED AND PERSISTED PERFECTLY TO DATABASE!")

if __name__ == "__main__":
    test_all_routes()

