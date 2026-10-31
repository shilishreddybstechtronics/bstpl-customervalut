import re

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update #dlgEditName modal HTML
    old_dlg_name = re.search(r'<dialog id="dlgEditName"[\s\S]*?</dialog>', content)
    if not old_dlg_name:
        raise Exception(f"Could not find #dlgEditName in {filepath}")

    new_dlg_name = '''<dialog id="dlgEditName" class="modal-card" style="width:min(480px, 94vw); padding:0; border-radius:18px; border:1px solid var(--line); box-shadow:0 24px 60px rgba(0,0,0,0.35); overflow:hidden">
    <div style="padding:16px 22px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--line); background:var(--card-subtle)">
      <div style="display:flex; align-items:center; gap:10px">
        <span style="font-size:22px">✏️</span>
        <div>
          <h3 style="margin:0; font-size:16px; font-weight:800; color:var(--text)">Edit Employee Name</h3>
          <span style="font-size:12px; color:var(--muted)">Change your account display name across the platform</span>
        </div>
      </div>
      <button class="b ghost" id="closeDlgEditName" type="button" onclick="closeEditNameModal()" style="font-size:18px; min-width:38px; min-height:38px; display:inline-flex; align-items:center; justify-content:center; cursor:pointer; border-radius:8px" aria-label="Close">✕</button>
    </div>

    <form id="formEditName" style="padding:20px 24px; margin:0">
      <!-- 1. Current Name (Text box down of that showing the present name) -->
      <div style="margin-bottom:16px">
        <label for="editNameCurrent" style="display:block; font-size:12.5px; font-weight:700; color:var(--text); margin-bottom:6px">Current Name</label>
        <input type="text" id="editNameCurrent" readonly disabled style="width:100%; box-sizing:border-box; background:var(--card-subtle); color:var(--text); font-weight:700; opacity:0.95; cursor:not-allowed; border:1.5px solid var(--line); border-radius:8px; padding:10px 12px; font-size:14px" />
        <span style="display:block; font-size:11px; color:var(--muted); margin-top:4px">Your present registered display name</span>
      </div>

      <!-- 2. Updated Name (Text box to enter name externally by user) -->
      <div style="margin-bottom:16px">
        <label for="editNameUpdated" style="display:block; font-size:12.5px; font-weight:700; color:var(--text); margin-bottom:6px">Updated Name <span style="color:var(--danger)">*</span></label>
        <input type="text" id="editNameUpdated" placeholder="Enter updated employee name" required autocomplete="name" style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1.5px solid var(--line); border-radius:8px; padding:10px 12px; font-size:14px" />
      </div>

      <!-- 3. Confirm Name (Text box given by user to confirm updated name) -->
      <div style="margin-bottom:16px">
        <label for="editNameConfirm" style="display:block; font-size:12.5px; font-weight:700; color:var(--text); margin-bottom:6px">Confirm Name <span style="color:var(--danger)">*</span></label>
        <input type="text" id="editNameConfirm" placeholder="Re-enter updated employee name to confirm" required autocomplete="off" style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1.5px solid var(--line); border-radius:8px; padding:10px 12px; font-size:14px" />
      </div>

      <p class="err" id="editNameError" role="alert" style="margin:8px 0 14px; font-size:12.5px; font-weight:600; color:var(--danger)" hidden></p>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px">
        <button class="b" type="button" onclick="closeEditNameModal()">Cancel</button>
        <button class="b p" type="submit" id="btnConfirmEditName">Save</button>
      </div>
    </form>
  </dialog>'''

    content = content[:old_dlg_name.start()] + new_dlg_name + content[old_dlg_name.end():]

    # 2. Update Settings dialog markup to include the Account Header card and current name in Edit Name item
    old_settings_inner = re.search(r'<div style="padding:22px 24px">\s*<!-- Options shifted from top bar into Settings', content)
    if not old_settings_inner:
        raise Exception(f"Could not find settings inner padding div in {filepath}")

    new_settings_inner_header = '''<div style="padding:22px 24px">
      <!-- Signed-in Account Profile Banner (Updated name visible in settings option) -->
      <div id="settingsUserHeaderCard" style="display:flex; align-items:center; gap:12px; padding:12px 16px; background:var(--card-subtle); border:1px solid var(--line); border-radius:12px; margin-bottom:16px">
        <div id="settingsUserAvatarCircle" style="width:40px; height:40px; border-radius:50%; background:linear-gradient(135deg, var(--primary), var(--accent)); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:16px">U</div>
        <div style="flex:1">
          <div id="settingsAccountName" style="font-weight:800; font-size:15px; color:var(--text)">Employee</div>
          <div style="font-size:12px; color:var(--muted)">Signed-in as: <b id="settingsAccountUserId" style="color:var(--primary)">0001</b> &bull; <span id="settingsAccountRole" style="font-weight:600">Admin</span></div>
        </div>
      </div>

      <!-- Options shifted from top bar into Settings'''

    content = content[:old_settings_inner.start()] + new_settings_inner_header + content[old_settings_inner.end() - len('<!-- Options shifted from top bar into Settings'):]

    # Update settingsBtnEditName description to show current name
    old_btn_edit_name = re.search(r'<button type="button" class="settings-action-item" id="settingsBtnEditName">[\s\S]*?</button>', content)
    if old_btn_edit_name:
        new_btn_edit_name = '''<button type="button" class="settings-action-item" id="settingsBtnEditName">
          <div class="settings-action-icon" style="background:#e0f2fe;color:#0284c7">✏️</div>
          <div class="settings-action-text">
            <div class="settings-action-title">Edit Name</div>
            <div class="settings-action-desc" id="settingsEditNameDesc">Current: <b id="settingsCurrentNameVal" style="color:var(--primary)">—</b> &bull; Change display name</div>
          </div>
          <span class="settings-action-arrow">›</span>
        </button>'''
        content = content[:old_btn_edit_name.start()] + new_btn_edit_name + content[old_btn_edit_name.end():]

    # 3. Update JavaScript controllers: openEditNameModal, submitEditNameModal, openSettingsModal
    old_edit_js = re.search(r'/\* ---------- Edit Employee Name Modal Controller ---------- \*/[\s\S]*?/\* ---------- Change Account Password Modal Controller ---------- \*/', content)
    if not old_edit_js:
        raise Exception(f"Could not find Edit Employee Name Modal Controller in {filepath}")

    new_edit_js = '''/* ---------- Edit Employee Name Modal Controller ---------- */
      async function openEditNameModal() {
        const dlg = $('dlgEditName');
        if (!dlg) return;
        const u = getUser();
        let currentName = (window.CU && window.CU.name) || u.name || u.user_id || '';

        // Fetch fresh profile from database
        try {
          const fresh = await api('/api/me');
          if (fresh && fresh.name) {
            currentName = fresh.name;
            if (window.CU) Object.assign(window.CU, fresh);
          }
        } catch (_) {}

        if ($('editNameCurrent')) $('editNameCurrent').value = currentName;
        if ($('editNameUpdated')) $('editNameUpdated').value = '';
        if ($('editNameConfirm')) $('editNameConfirm').value = '';
        if ($('editNameError')) {
          $('editNameError').textContent = '';
          $('editNameError').hidden = true;
        }
        if (!dlg.open) dlg.showModal();
        setTimeout(() => $('editNameUpdated')?.focus(), 50);
      }

      function closeEditNameModal() {
        const dlg = $('dlgEditName');
        if (dlg && dlg.open) dlg.close();
      }

      async function submitEditNameModal() {
        const errEl = $('editNameError');
        const currentName = ($('editNameCurrent')?.value || '').trim();
        const updatedName = ($('editNameUpdated')?.value || '').trim();
        const confirmName = ($('editNameConfirm')?.value || '').trim();

        if (errEl) { errEl.textContent = ''; errEl.hidden = true; }

        if (!updatedName) {
          if (errEl) { errEl.textContent = 'Please enter an updated name.'; errEl.hidden = false; }
          return;
        }
        if (updatedName.toLowerCase() === currentName.toLowerCase()) {
          if (errEl) { errEl.textContent = 'Updated name must be different from current name.'; errEl.hidden = false; }
          return;
        }
        if (updatedName !== confirmName) {
          if (errEl) { errEl.textContent = 'Updated name and confirm name do not match.'; errEl.hidden = false; }
          return;
        }

        const btn = $('btnConfirmEditName');
        if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }

        try {
          const res = await api('/api/me/name', {
            method: 'PUT',
            body: JSON.stringify({ name: updatedName, confirm_name: confirmName })
          });
          const finalName = res.name || updatedName;

          // 1. Update user state in storage & memory
          const u = getUser();
          u.name = finalName;
          localStorage.setItem('user', JSON.stringify(u));
          if (window.CU) window.CU.name = finalName;

          // 2. Update Top Bar Header Greeting
          if ($('hi')) {
            const h = new Date().getHours();
            $('hi').textContent = `Good ${h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening'}, ${finalName}`;
          }

          // 3. Update User Avatar circle
          const uInitial = ((finalName[0] || 'U')[0] || 'U').toUpperCase();
          if ($('userAvatarCircle')) $('userAvatarCircle').textContent = uInitial;

          // 4. Update in Settings Modal options immediately
          if ($('settingsAccountName')) $('settingsAccountName').textContent = finalName;
          if ($('settingsCurrentNameVal')) $('settingsCurrentNameVal').textContent = finalName;
          if ($('settingsUserAvatarCircle')) $('settingsUserAvatarCircle').textContent = uInitial;

          // 5. Update in Manage Users table
          if (typeof loadUsersContainer === 'function' && $('usersTableWrap')) {
            loadUsersContainer();
          }

          closeEditNameModal();
          toast(`Name updated successfully to "${finalName}" across settings, website & database`);
          await updateChrome().catch(() => {});
        } catch (err) {
          if (errEl) {
            errEl.textContent = err.message || 'Failed to update name.';
            errEl.hidden = false;
          }
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = 'Save'; }
        }
      }

      if ($('bEditMyName')) $('bEditMyName').onclick = openEditNameModal;
      if ($('formEditName')) $('formEditName').onsubmit = e => { e.preventDefault(); submitEditNameModal(); };
      if ($('btnConfirmEditName')) $('btnConfirmEditName').onclick = submitEditNameModal;

      /* ---------- Change Account Password Modal Controller ---------- */'''

    content = content[:old_edit_js.start()] + new_edit_js + content[old_edit_js.end() - len('/* ---------- Change Account Password Modal Controller ---------- */'):]

    # 4. Update openSettingsModal in JS to populate Settings account name and current name
    old_settings_js = re.search(r'function openSettingsModal\(\)\s*\{[\s\S]*?if \(!dlg\.open\) dlg\.showModal\(\);[\s\S]*?\}', content)
    if old_settings_js:
        new_settings_js = '''function openSettingsModal() {
        const dlg = $('dlgSettings');
        if (!dlg) return;

        const u = getUser();
        const currentName = (window.CU && window.CU.name) || u.name || u.user_id || 'Employee';
        const uInitial = ((currentName[0] || 'U')[0] || 'U').toUpperCase();

        // Populate Settings profile display with updated name
        if ($('settingsAccountName')) $('settingsAccountName').textContent = currentName;
        if ($('settingsCurrentNameVal')) $('settingsCurrentNameVal').textContent = currentName;
        if ($('settingsUserAvatarCircle')) $('settingsUserAvatarCircle').textContent = uInitial;
        if ($('settingsAccountUserId')) $('settingsAccountUserId').textContent = u.user_id || '0001';
        if ($('settingsAccountRole')) $('settingsAccountRole').textContent = myRole();

        // Role-based visibility for Settings actions
        if ($('settingsBtnManageUsers')) {
          $('settingsBtnManageUsers').style.display = canAccessUsersManager() ? 'flex' : 'none';
        }
        if ($('settingsBtnLoginInv')) {
          $('settingsBtnLoginInv').style.display = canAccessLoginInventory() ? 'flex' : 'none';
        }

        // Apply and highlight active theme in settings
        const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
        const currentMode = localStorage.getItem('valut_theme_mode') || 'light';
        applyTheme(currentPal, currentMode);

        if (!dlg.open) dlg.showModal();
      }'''
        content = content[:old_settings_js.start()] + new_settings_js + content[old_settings_js.end():]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Applied Edit Name spec to {filepath} successfully.")

update_file('frontend/index.html')
update_file('frontend/dashboard.html')

