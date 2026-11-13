with open('frontend/settings.html', 'r', encoding='utf-8') as f:
    c = f.read()

target = """<button type="button" class="b" id="settingsBtnManageUsers" onclick="scrollToManageUsers()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">👥 Manage Users</button>
              <button type="button" class="b" id="settingsBtnLoginInventory" onclick="scrollToLoginInventory()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🕘 Login Inventory</button>"""

replacement = """<button type="button" class="b" id="settingsBtnManageUsers" onclick="scrollToManageUsers()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">👥 Manage Users</button>
              <button type="button" class="b" id="settingsBtnLoginInventory" onclick="scrollToLoginInventory()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🔑 Login Inventory</button>
              <button type="button" class="b" id="settingsBtnSearchAudit" onclick="scrollToSearchAudit()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🔍 Search Audit Trail</button>
              <button type="button" class="b d" id="settingsBtnLogout" onclick="handleSettingsLogout()" style="font-weight:800;padding:8px 16px;border-radius:9px;font-size:13px;display:inline-flex;align-items:center;gap:6px;background:#dc2626;color:#fff;border-color:#b91c1c" title="Securely terminate session and return to Login">
                <span>🚪</span> <span>Sign Out / Logout</span>
              </button>"""

if target in c:
    c = c.replace(target, replacement)
    with open('frontend/settings.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print("SUCCESS: Added settingsBtnLogout to settings.html!")
else:
    print("WARNING: target not found.")

