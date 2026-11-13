import re

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Clean comment on line 16669 if malformed
    content = content.replace(
        '<!-- Options shifted from top bar into Settings<!-- Options shifted from top bar into Settings (Themes option removed) -->',
        '<!-- Options shifted from top bar into Settings -->'
    )

    # 2. Update settingsBtnEditName description to clearly show Current Name
    old_btn_desc = re.search(r'<div class="settings-action-desc" id="settingsEditNameDesc">[\s\S]*?</div>', content)
    if old_btn_desc:
        new_btn_desc = '<div class="settings-action-desc" id="settingsEditNameDesc">Change your account display name &bull; Current: <b id="settingsCurrentNameVal" style="color:var(--primary)">—</b></div>'
        content = content[:old_btn_desc.start()] + new_btn_desc + content[old_btn_desc.end():]

    # 3. Update #dlgEditName modal HTML
    old_dlg_name = re.search(r'<dialog id="dlgEditName"[\s\S]*?</dialog>', content)
    if not old_dlg_name:
        raise Exception(f"Could not find #dlgEditName in {filepath}")

    new_dlg_name = '''<dialog id="dlgEditName" class="modal-card" style="width:min(480px, 94vw); padding:0; border-radius:18px; border:1px solid var(--line); box-shadow:0 30px 90px rgba(0,0,0,0.5); overflow:hidden; z-index:99999">
    <div style="padding:16px 22px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--line); background:var(--card-subtle)">
      <div style="display:flex; align-items:center; gap:10px">
        <span style="font-size:22px">✏️</span>
        <div>
          <h3 style="margin:0; font-size:16px; font-weight:800; color:var(--text)">Edit Name</h3>
          <span style="font-size:12px; color:var(--muted)">Change your account display name across the platform</span>
        </div>
      </div>
      <button class="b ghost" id="closeDlgEditName" type="button" onclick="closeEditNameModal(true)" style="font-size:18px; min-width:38px; min-height:38px; display:inline-flex; align-items:center; justify-content:center; cursor:pointer; border-radius:8px" aria-label="Close">✕</button>
    </div>

    <form id="formEditName" style="padding:20px 24px; margin:0">
      <!-- 1. Current Name (Text box down of that showing the present name) -->
      <div style="margin-bottom:16px">
        <label for="editNameCurrent" style="display:block; font-size:12.5px; font-weight:700; color:var(--text); margin-bottom:6px">Current Name</label>
        <input type="text" id="editNameCurrent" readonly style="width:100%; box-sizing:border-box; background:var(--card-subtle); color:var(--text); font-weight:700; opacity:0.95; cursor:default; border:1.5px solid var(--line); border-radius:8px; padding:10px 12px; font-size:14px" />
        <span style="display:block; font-size:11px; color:var(--muted); margin-top:4px">Your present registered display name</span>
      </div>

      <!-- 2. Updated Name (Text box to enter name externally by user) -->
      <div style="margin-bottom:16px">
        <label for="editNameUpdated" style="display:block; font-size:12.5px; font-weight:700; color:var(--text); margin-bottom:6px">Updated Name <span style="color:var(--danger)">*</span></label>
        <input type="text" id="editNameUpdated" placeholder="Enter updated name" required autocomplete="name" style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1.5px solid var(--line); border-radius:8px; padding:10px 12px; font-size:14px" />
      </div>

      <!-- 3. Confirm Name (Text box given by user to confirm updated name) -->
      <div style="margin-bottom:16px">
        <label for="editNameConfirm" style="display:block; font-size:12.5px; font-weight:700; color:var(--text); margin-bottom:6px">Confirm Name <span style="color:var(--danger)">*</span></label>
        <input type="text" id="editNameConfirm" placeholder="Confirm updated name" required autocomplete="off" style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1.5px solid var(--line); border-radius:8px; padding:10px 12px; font-size:14px" />
      </div>

      <p class="err" id="editNameError" role="alert" style="margin:8px 0 14px; font-size:12.5px; font-weight:600; color:var(--danger)" hidden></p>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px">
        <button class="b" type="button" onclick="closeEditNameModal(true)">Cancel</button>
        <button class="b p" type="submit" id="btnConfirmEditName">Save</button>
      </div>
    </form>
  </dialog>'''

    content = content[:old_dlg_name.start()] + new_dlg_name + content[old_dlg_name.end():]

    # 4. Update Edit Employee Name Controller JS
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

      function closeEditNameModal(reopenSettings = false) {
        const dlg = $('dlgEditName');
        if (dlg && dlg.open) dlg.close();
        if (reopenSettings && $('dlgSettings')) {
          openSettingsModal();
        }
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

          closeEditNameModal(false);
          openSettingsModal();
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

    # 5. Update settingsBtnEditName to close dlgSettings before opening dlgEditName
    content = re.sub(
        r"if \(\$\('settingsBtnEditName'\)\) \{\s*\$\('settingsBtnEditName'\)\.onclick = \(\) => \{\s*openEditNameModal\(\);\s*\};\s*\}",
        "if ($('settingsBtnEditName')) {\n        $('settingsBtnEditName').onclick = () => {\n          $('dlgSettings').close();\n          openEditNameModal();\n        };\n      }",
        content
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Refined {filepath} successfully.")

update_file('frontend/index.html')
update_file('frontend/dashboard.html')

