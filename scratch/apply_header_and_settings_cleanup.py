import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Top Header Actions
old_header_acts = '''          <!-- Left Actions: Quick Search, Refresh, Expiry Alerts & Cart -->
          <div class="cv-header-actions acts" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <button class="b" id="bQs" title="Quick Search (Ctrl + K)"><span>🔎 Search</span></button>
            <button class="b" id="bRefresh" title="Reload current data">🔄 Refresh</button>
            <button class="b on" id="bAl" title="Toggle Expiry Alerts">Alerts: ON</button>
            <button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="openCartModal()" style="font-weight:700">
              🛒 Cart ( <span id="headerCartCountBadge">0</span> )
            </button>
          </div>'''

new_header_acts = '''          <!-- Left Actions: Quick Search, Refresh, Restored Action Options, Expiry Alerts & Cart -->
          <div class="cv-header-actions acts" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <button class="b" id="bQs" title="Quick Search (Ctrl + K)"><span>🔎 Search</span></button>
            <button class="b" id="bRefresh" title="Reload current data">🔄 Refresh</button>
            <button class="b" id="bEditMyName" title="Change your account display name" onclick="openEditNameModal()">✏️ Edit Name</button>
            <button class="b" id="bPw" title="Update your login security password" onclick="openChangePasswordModal()">🔑 Edit Password</button>
            <button class="b" id="bManInv" title="Manage Customer Inventory" onclick="showContainer('box-inv')">📋 Manage Inventory</button>
            <button class="b" id="bLogInv" title="Login Inventory (Activity Log)" onclick="openAuditLogModal()">🕘 Login Inventory</button>
            <button class="b" id="bUsers" title="Manage Users & Permissions" onclick="openManageUsersModal()" hidden>👥 Manage Users</button>
            <button class="b on" id="bAl" title="Toggle Expiry Alerts">Alerts: ON</button>
            <button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="openCartModal()" style="font-weight:700">
              🛒 Cart ( <span id="headerCartCountBadge">0</span> )
            </button>
          </div>'''

assert old_header_acts in text, "Could not find old_header_acts"
text = text.replace(old_header_acts, new_header_acts, 1)

# 2. Remove the 4 action buttons from dlgSettings
btn_slice_start = text.find('        <button type="button" class="settings-action-item" id="settingsBtnEditName">')
btn_slice_end = text.find('        <!-- Themes & Look (7 Themes + Light/Dark Mode) -->')
assert btn_slice_start != -1 and btn_slice_end != -1, "Could not find settings buttons slice"

# Replace slice with empty string
text = text[:btn_slice_start] + text[btn_slice_end:]

# Update the comment above
text = text.replace('<!-- Options shifted from top bar into Settings -->\n      <div class="settings-action-list">', '<div class="settings-action-list">')

# 3. Remove the hidden dummy buttons at the bottom of the body
dummy_buttons = '''    <button id="bPw" type="button" onclick="openChangePasswordModal()" hidden></button>
    <button id="bEditMyName" type="button" onclick="openEditNameModal()" hidden></button>'''
if dummy_buttons in text:
    text = text.replace(dummy_buttons, '')

# 4. In submitEditNameModal, remove openSettingsModal() call
old_submit_edit_name_open_settings = '''          // Close Edit Name modal and reopen Settings so user immediately sees the change
          closeEditNameModal(false);
          openSettingsModal();
          toast(`Name updated successfully to "${finalName}" in website & database`);'''

new_submit_edit_name_open_settings = '''          // Close Edit Name modal cleanly
          closeEditNameModal(false);
          toast(`Name updated successfully to "${finalName}" in website & database`);'''

assert old_submit_edit_name_open_settings in text, "Could not find old_submit_edit_name_open_settings"
text = text.replace(old_submit_edit_name_open_settings, new_submit_edit_name_open_settings, 1)

# 5. In submitChangePasswordModal, remove openSettingsModal() call
old_submit_pwd_open_settings = '''          if ($('pf')) $('pf').reset();
          closeChangePasswordModal(false);
          openSettingsModal();
          toast('Password updated successfully in website & database');'''

new_submit_pwd_open_settings = '''          if ($('pf')) $('pf').reset();
          closeChangePasswordModal(false);
          toast('Password updated successfully in website & database');'''

assert old_submit_pwd_open_settings in text, "Could not find old_submit_pwd_open_settings"
text = text.replace(old_submit_pwd_open_settings, new_submit_pwd_open_settings, 1)

# 6. In closeDlgEditName and closeDlgChangePassword onclick in HTML, ensure reopenSettings is false
text = text.replace('onclick="closeEditNameModal(true)"', 'onclick="closeEditNameModal(false)"')
text = text.replace('onclick="closeChangePasswordModal(true)"', 'onclick="closeChangePasswordModal(false)"')

# 7. In bManInv hook, ensure showContainer('box-inv') is called
text = text.replace("if ($('bManInv')) $('bManInv').onclick = () => goTab('box-inv');", "if ($('bManInv')) $('bManInv').onclick = () => showContainer('box-inv');")

# 8. Write to frontend/index.html
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

# Also write identical copy to frontend/dashboard.html
with open('frontend/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied changes to both frontend/index.html and frontend/dashboard.html successfully!")
