with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Clean up openSettingsModal lines
old_settings_visibility = '''        // Role-based visibility for Settings actions
        if ($('settingsBtnManageUsers')) {
          $('settingsBtnManageUsers').style.display = canAccessUsersManager() ? 'flex' : 'none';
        }
        if ($('settingsBtnLoginInv')) {
          $('settingsBtnLoginInv').style.display = canAccessLoginInventory() ? 'flex' : 'none';
        }'''

if old_settings_visibility in text:
    text = text.replace(old_settings_visibility, '')

# 2. Clean up settings action wiring lines
old_settings_actions = '''      // Settings Actions Wiring (Edit Name, Change Password, Manage Users, Log Inventory, Logout)
      if ($('settingsBtnEditName')) {
        $('settingsBtnEditName').onclick = () => {
          $('dlgSettings').close();
          openEditNameModal();
        };
      }

      if ($('settingsBtnPassword')) {
        $('settingsBtnPassword').onclick = () => {
          $('dlgSettings').close();
          openChangePasswordModal();
        };
      }

      if ($('settingsBtnManageUsers')) {
        $('settingsBtnManageUsers').onclick = () => {
          $('dlgSettings').close();
          openManageUsersModal();
        };
      }

      if ($('settingsBtnLoginInv')) {
        $('settingsBtnLoginInv').onclick = () => {
          $('dlgSettings').close();
          openAuditLogModal();
        };
      }'''

if old_settings_actions in text:
    text = text.replace(old_settings_actions, '')

# Write to both frontend/index.html and frontend/dashboard.html
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('frontend/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Settings listeners cleaned up and saved to both index.html and dashboard.html!")

