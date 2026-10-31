import sys
sys.path.insert(0, 'backend')

import schemas
from models import User
from routes_users import user_out, update_my_name, update_my_theme
from fastapi import HTTPException
from unittest.mock import MagicMock

def test_schemas():
    u = schemas.UserOut(
        id=1, name="Test User", user_id="0002", role="admin", is_admin=True,
        category="master_admin", category_label="Master Admin", badge="⭐ Master Admin", is_master=True,
        previous_name="Original Name", theme_palette="sunset", theme_mode="dark"
    )
    assert u.previous_name == "Original Name"
    assert u.theme_palette == "sunset"
    assert u.theme_mode == "dark"

    name_up = schemas.UserNameUpdate(name="New Name", confirm_current_name="Old Name")
    assert name_up.name == "New Name"
    assert name_up.confirm_current_name == "Old Name"

    t_up = schemas.ThemeUpdate(palette="ocean", mode="dark")
    assert t_up.palette == "ocean"
    assert t_up.mode == "dark"
    print("✓ Schemas test passed.")

def test_update_name_validation():
    user = User(id=99, name="Alice Smith", user_id="0005", role="standard", permissions={})
    db = MagicMock()
    req = MagicMock()

    # 1. Empty name should raise 400
    try:
        update_my_name(schemas.UserNameUpdate(name="   ", confirm_current_name="Alice Smith"), req, db, user)
        assert False, "Should have raised 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "empty" in e.detail.lower()

    # 2. Wrong current name confirm should raise 400
    try:
        update_my_name(schemas.UserNameUpdate(name="Alice Johnson", confirm_current_name="Bob Smith"), req, db, user)
        assert False, "Should have raised 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "does not match" in e.detail.lower()

    # 3. Same name should raise 400
    try:
        update_my_name(schemas.UserNameUpdate(name="Alice Smith", confirm_current_name="Alice Smith"), req, db, user)
        assert False, "Should have raised 400"
    except HTTPException as e:
        assert e.status_code == 400
        assert "must be different" in e.detail.lower()

    # 4. Valid update should succeed and record previous_name
    res = update_my_name(schemas.UserNameUpdate(name="Alice Johnson", confirm_current_name="Alice Smith"), req, db, user)
    assert res["ok"] is True
    assert res["name"] == "Alice Johnson"
    assert res["previous_name"] == "Alice Smith"
    assert user.name == "Alice Johnson"
    assert user.permissions["previous_name"] == "Alice Smith"
    print("✓ Update name validation test passed.")

def test_update_theme():
    user = User(id=99, name="Alice Johnson", user_id="0005", role="standard", permissions={})
    db = MagicMock()
    res = update_my_theme(schemas.ThemeUpdate(palette="sunset", mode="dark"), db, user)
    assert res["ok"] is True
    assert res["palette"] == "sunset"
    assert res["mode"] == "dark"
    assert user.permissions["theme_palette"] == "sunset"
    assert user.permissions["theme_mode"] == "dark"
    print("✓ Update theme test passed.")

def test_master_admin_password_view():
    master_admin = User(id=1, name="Master 0001", user_id="0001", role="admin")
    target_user = User(id=2, name="Emp Bob", user_id="0005", role="standard", plain_password="SecretPassword123")
    
    out_dict = user_out(target_user, actor=master_admin)
    assert out_dict["password"] == "SecretPassword123", f"Expected plain password for master admin, got {out_dict['password']}"
    print("✓ Master admin password view test passed.")

def test_frontend_elements():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Edit name modal elements
    assert 'id="dlgEditName"' in html
    assert 'id="editNamePrevious"' in html
    assert 'id="editNameCurrent"' in html
    assert 'id="editNameConfirmCurrent"' in html
    assert 'id="editNameNew"' in html
    assert 'id="btnConfirmEditName"' in html
    assert 'id="closeDlgEditName"' in html

    # Change password modal elements
    assert 'id="pwd"' in html
    assert 'id="p1"' in html
    assert 'id="p2"' in html
    assert 'id="p3"' in html
    assert 'id="btnConfirmChangePw"' in html
    assert 'id="closeDlgChangePassword"' in html
    assert html.count("togglePasswordInputVisibility('p1')") >= 1
    assert html.count("togglePasswordInputVisibility('p2')") >= 1
    assert html.count("togglePasswordInputVisibility('p3')") >= 1

    # Themes in Settings
    themes = ["royal_navy", "midnight", "emerald", "crimson_vault", "ocean", "violet", "sunset"]
    for t in themes:
        assert f'data-palette-val="{t}"' in html, f"Missing theme {t}"
    assert 'id="settingsModeLight"' in html
    assert 'id="settingsModeDark"' in html

    # Cart Modal
    assert 'id="dlgCartModal"' in html
    assert 'id="btnHeaderCart"' in html
    assert 'openCartModal()' in html

    # Floating dock removed
    assert 'id="themeDockRightEnd"' not in html

    # Logout protection
    assert "window.addEventListener('pageshow'" in html
    assert "window.addEventListener('popstate'" in html

    print("✓ Frontend elements and requirements test passed.")

if __name__ == '__main__':
    test_schemas()
    test_update_name_validation()
    test_update_theme()
    test_master_admin_password_view()
    test_frontend_elements()
    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
