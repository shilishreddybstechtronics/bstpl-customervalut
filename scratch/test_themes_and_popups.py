import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('frontend/dashboard.html', 'r', encoding='utf-8') as f:
    dhtml = f.read()

# 1. Byte parity
assert html == dhtml, "index.html and dashboard.html must be 100% identical!"
print("✓ Byte parity: index.html and dashboard.html are 100% identical.")

# 2. Dock removed
assert 'id="themeDockRightEnd"' not in html, "themeDockRightEnd must be deleted"
assert 'id="themeDockToggleBtn"' not in html, "themeDockToggleBtn must be deleted"
print("✓ Old floating theme dock at right-end is deleted and disabled.")

# 3. 7 Themes present with Light & Dark Mode in CSS
themes = ['royal_navy', 'midnight', 'emerald', 'crimson_vault', 'ocean', 'violet', 'sunset']
for t in themes:
    assert f'data-palette="{t}"' in html, f"CSS rule for theme {t} missing"
    assert f'data-palette-val="{t}"' in html, f"Theme option button for {t} missing in settings"
print(f"✓ All 7 requested themes ({', '.join(themes)}) verified in CSS and Settings modal.")

# 4. Mode Switchers present in Settings
assert 'id="settingsModeLight"' in html, "Light mode button missing in Settings"
assert 'id="settingsModeDark"' in html, "Dark mode button missing in Settings"
print("✓ Light and Dark mode switchers verified in Settings modal.")

# 5. Edit Name popup dialog
assert 'id="dlgEditName"' in html, "dlgEditName missing"
assert 'id="closeDlgEditName"' in html, "closeDlgEditName missing"
assert 'id="editNamePresent"' in html, "editNamePresent missing"
assert 'id="editNameNew"' in html, "editNameNew missing"
assert 'id="editNameConfirm"' in html, "editNameConfirm missing"
assert 'id="btnConfirmEditName"' in html, "btnConfirmEditName missing"
print("✓ Edit Name popup verified: Present Name, New Name, Confirm New Name, Confirm button, and Cross (X) close button.")

# 6. Change Password popup dialog
assert 'id="pwd"' in html, "pwd dialog missing"
assert 'id="closeDlgChangePassword"' in html, "closeDlgChangePassword missing"
assert 'id="p1"' in html, "p1 (present password) missing"
assert 'id="p2"' in html, "p2 (new password) missing"
assert 'id="p3"' in html, "p3 (confirm password) missing"
assert 'id="btnConfirmChangePw"' in html, "btnConfirmChangePw missing"
print("✓ Change Password popup verified: Present Password, New Password, Confirm Password, Confirm button, and Cross (X) close button.")

print("\nALL THEME & POPUP ENHANCEMENTS SUCCESSFULLY VERIFIED!")

