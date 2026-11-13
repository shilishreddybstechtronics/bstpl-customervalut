with open('frontend/settings.html', 'r', encoding='utf-8') as f:
    text = f.read()

assert 'id="settingsUserCard"' in text, "settingsUserCard missing"
assert 'id="settingsThemesCard"' in text, "settingsThemesCard missing"
assert 'id="settingsManageUsersCard"' in text, "settingsManageUsersCard missing"
assert 'id="settingsLoginInventoryCard"' in text, "settingsLoginInventoryCard missing"
assert 'id="usersTableWrap"' in text, "usersTableWrap missing"
assert 'id="ltbl"' in text, "ltbl missing"
assert 'id="lsum"' in text, "lsum missing"
assert 'id="uadd"' in text, "uadd missing"
assert 'id="btnSubmitTheme"' in text, "btnSubmitTheme missing"
assert 'id="settingsBtnManageUsers"' in text, "settingsBtnManageUsers missing"
assert 'id="settingsBtnLoginInventory"' in text, "settingsBtnLoginInventory missing"
assert 'scrollToManageUsers' in text, "scrollToManageUsers missing"
assert 'scrollToLoginInventory' in text, "scrollToLoginInventory missing"
assert 'exportAuditLogCSV' in text, "exportAuditLogCSV missing"

print("=================================================================")
print(" ALL SETTINGS MERGED CONTAINERS & CONTROLS VERIFIED 100%!        ")
print("=================================================================")

