import re

def verify_frontend():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    print("==================================================")
    print("      BSTPL CUSTOMERVAULT - DEEP FRONTEND DOM AUDIT")
    print("==================================================")

    # 1. Check all <dialog> tags and their IDs
    dialog_ids = re.findall(r'<dialog[^>]*\bid=["\']([^"\']+)["\']', html)
    print(f"Discovered {len(dialog_ids)} <dialog> elements:")
    for did in dialog_ids:
        print(f"  - <dialog id=\"{did}\">")

    critical_dialogs = ["dlgSettings", "dlgEditName", "pwd", "dlgCartModal"]
    for cd in critical_dialogs:
        assert cd in dialog_ids, f"CRITICAL: Dialog #{cd} is missing from HTML!"
    print("✓ All critical modals present in DOM.")

    # 2. Check 3 fields for Edit Name
    edit_name_checks = [
        ('id="editNameCurrent"', 'Current Name field'),
        ('id="editNameUpdated"', 'Updated Name field'),
        ('id="editNameConfirm"', 'Confirm Name field'),
        ('id="btnConfirmEditName"', 'Save / Confirm button'),
        ('id="btnCancelEditName"', 'Cancel button'),
        ('id="closeDlgEditName"', 'Modal Close (X) button')
    ]
    for pattern, name in edit_name_checks:
        assert pattern in html, f"CRITICAL: {name} ({pattern}) missing from HTML!"
        print(f"✓ Found: {name}")

    # Check that editNameCurrent has readonly attribute
    assert re.search(r'<input[^>]*id=["\']editNameCurrent["\'][^>]*readonly', html) or \
           re.search(r'<input[^>]*readonly[^>]*id=["\']editNameCurrent["\']', html), \
           "Current Name field must have 'readonly' attribute"
    print("✓ Current Name field correctly marked as read-only.")

    # 3. Check Settings Display Targets
    settings_targets = [
        ('id="settingsCurrentNameVal"', 'Settings current name value span'),
        ('id="settingsAccountName"', 'Settings account profile name'),
        ('id="settingsUserAvatarCircle"', 'Settings account profile avatar circle'),
        ('id="settingsAccountUserId"', 'Settings account user ID'),
        ('id="settingsAccountRole"', 'Settings account user role'),
        ('id="settingsBtnEditName"', 'Settings Edit Name menu row'),
        ('id="settingsBtnPassword"', 'Settings Change Password menu row'),
        ('id="settingsBtnManageUsers"', 'Settings Manage Users menu row'),
        ('id="settingsBtnLoginInv"', 'Settings Login Inventory menu row'),
        ('id="settingsBtnLogout"', 'Settings Logout button')
    ]
    for pattern, name in settings_targets:
        assert pattern in html, f"CRITICAL: {name} ({pattern}) missing from HTML!"
        print(f"✓ Found: {name}")

    # 4. Check Change Password modal inputs and eye toggles
    pwd_targets = [
        ('id="p1"', 'Current Password input'),
        ('id="p2"', 'New Password input'),
        ('id="p3"', 'Confirm New Password input'),
        ("togglePasswordInputVisibility('p1')", 'Current Password Eye Toggle'),
        ("togglePasswordInputVisibility('p2')", 'New Password Eye Toggle'),
        ("togglePasswordInputVisibility('p3')", 'Confirm Password Eye Toggle'),
        ('id="btnConfirmChangePw"', 'Change Password Submit Button'),
        ('id="pc"', 'Change Password Cancel Button')
    ]
    for pattern, name in pwd_targets:
        assert pattern in html, f"CRITICAL: {name} ({pattern}) missing from HTML!"
        print(f"✓ Found: {name}")

    # 5. Check 7 Themes in CSS and UI
    themes = ["royal_navy", "midnight", "emerald", "crimson_vault", "ocean", "violet", "sunset"]
    for t in themes:
        # Check UI button
        assert f'data-palette-val="{t}"' in html, f"Theme choice button for '{t}' missing from Settings"
        # Check CSS root or [data-palette="..."] rule
        assert f'[data-palette="{t}"]' in html or t == "royal_navy", f"CSS theme definition for '{t}' missing!"
        print(f"✓ Theme '{t}' verified in UI choices & CSS styling.")

    # 6. Check Cart Pop-up Modal
    cart_targets = [
        ('id="btnHeaderCart"', 'Header Cart Button'),
        ('id="dlgCartModal"', 'Cart Modal Dialog'),
        ('id="closeDlgCart"', 'Cart Modal Close (X) button')
    ]
    for pattern, name in cart_targets:
        assert pattern in html, f"CRITICAL: {name} ({pattern}) missing from HTML!"
        print(f"✓ Found: {name}")

    # 7. Check Javascript functions existence
    js_funcs = [
        "openSettingsModal",
        "openEditNameModal",
        "submitEditNameModal",
        "closeEditNameModal",
        "openChangePasswordModal",
        "submitChangePasswordModal",
        "applyTheme",
        "toggleTheme",
        "openCartModal",
        "closeCartModal"
    ]
    for jf in js_funcs:
        assert f"function {jf}" in html or f"{jf} = function" in html or f"window.{jf}" in html or f"const {jf}" in html or f"let {jf}" in html or f"var {jf}" in html, \
            f"CRITICAL: JS function '{jf}' is missing!"
        print(f"✓ JS Function '{jf}' verified.")

    print("\n==================================================")
    print("  ALL FRONTEND DOM & FUNCTION CHECKS PASSED (100%)!")
    print("==================================================")

if __name__ == "__main__":
    verify_frontend()
