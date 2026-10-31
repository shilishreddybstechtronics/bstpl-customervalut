import re

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update #dlgEditName
    old_dlg_name = re.search(r'<dialog id="dlgEditName"[\s\S]*?</dialog>', content)
    if not old_dlg_name:
        raise Exception("Could not find #dlgEditName in " + filepath)

    new_dlg_name = '''<dialog id="dlgEditName" class="modal-card" style="width:min(500px, 94vw); padding:0; border-radius:18px; border:1px solid var(--line); box-shadow:0 24px 60px rgba(0,0,0,0.35); overflow:hidden">
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
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px">
        <div>
          <label for="editNamePrevious" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">Previous Name</label>
          <input type="text" id="editNamePrevious" readonly disabled style="width:100%; box-sizing:border-box; background:var(--card-subtle); color:var(--text-dim); opacity:0.85; cursor:not-allowed; border:1px solid var(--line); border-radius:8px; padding:9px 12px; font-size:13px; font-weight:600" />
        </div>
        <div>
          <label for="editNameCurrent" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">Current Name</label>
          <input type="text" id="editNameCurrent" readonly disabled style="width:100%; box-sizing:border-box; background:var(--card-subtle); color:var(--text-dim); opacity:0.85; cursor:not-allowed; border:1px solid var(--line); border-radius:8px; padding:9px 12px; font-size:13px; font-weight:600" />
        </div>
      </div>

      <div style="margin-bottom:14px">
        <label for="editNameConfirmCurrent" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">Confirm Current Name <span style="color:var(--danger)">*</span></label>
        <input type="text" id="editNameConfirmCurrent" placeholder="Enter your current registered name to verify" required autocomplete="off" style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 12px; font-size:13.5px" />
      </div>

      <div style="margin-bottom:14px">
        <label for="editNameNew" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">New Name <span style="color:var(--danger)">*</span></label>
        <input type="text" id="editNameNew" placeholder="Enter desired new employee display name" required autocomplete="name" style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 12px; font-size:13.5px" />
      </div>

      <p class="err" id="editNameError" role="alert" style="margin:8px 0 14px; font-size:12.5px; font-weight:600; color:var(--danger)" hidden></p>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:18px">
        <button class="b" type="button" onclick="closeEditNameModal()">Cancel</button>
        <button class="b p" type="submit" id="btnConfirmEditName">Confirm &amp; Update Name</button>
      </div>
    </form>
  </dialog>'''

    content = content[:old_dlg_name.start()] + new_dlg_name + content[old_dlg_name.end():]

    # 2. Update #pwd (Change Password Dialog)
    old_pwd = re.search(r'<dialog id="pwd"[\s\S]*?</dialog>', content)
    if not old_pwd:
        raise Exception("Could not find #pwd in " + filepath)

    new_pwd = '''<dialog id="pwd" class="modal-card" style="width:min(480px, 94vw); padding:0; border-radius:18px; border:1px solid var(--line); box-shadow:0 24px 60px rgba(0,0,0,0.35); overflow:hidden">
    <div style="padding:16px 22px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--line); background:var(--card-subtle)">
      <div style="display:flex; align-items:center; gap:10px">
        <span style="font-size:22px">🔑</span>
        <div>
          <h3 style="margin:0; font-size:16px; font-weight:800; color:var(--text)">Change Account Password</h3>
          <span style="font-size:12px; color:var(--muted)">Update your employee login password credentials</span>
        </div>
      </div>
      <button class="b ghost" id="closeDlgChangePassword" type="button" onclick="closeChangePasswordModal()" style="font-size:18px; min-width:38px; min-height:38px; display:inline-flex; align-items:center; justify-content:center; cursor:pointer; border-radius:8px" aria-label="Close">✕</button>
    </div>

    <form id="pf" style="padding:20px 24px; margin:0">
      <div style="margin-bottom:14px">
        <label for="p1" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">Current Password <span style="color:var(--danger)">*</span></label>
        <div style="position:relative">
          <input type="password" id="p1" autocomplete="current-password" placeholder="Enter current registered password" required style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 38px 10px 12px; font-size:13.5px" />
          <button type="button" class="b ghost" style="position:absolute; right:6px; top:50%; transform:translateY(-50%); padding:2px 6px; font-size:13px; border:none; cursor:pointer" onclick="togglePasswordInputVisibility('p1')">👁️</button>
        </div>
      </div>

      <div style="margin-bottom:14px">
        <label for="p2" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">New Password (min. 8 characters) <span style="color:var(--danger)">*</span></label>
        <div style="position:relative">
          <input type="password" id="p2" autocomplete="new-password" minlength="8" placeholder="Enter new password (min. 8 characters)" required style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 38px 10px 12px; font-size:13.5px" />
          <button type="button" class="b ghost" style="position:absolute; right:6px; top:50%; transform:translateY(-50%); padding:2px 6px; font-size:13px; border:none; cursor:pointer" onclick="togglePasswordInputVisibility('p2')">👁️</button>
        </div>
      </div>

      <div style="margin-bottom:14px">
        <label for="p3" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">Confirm New Password <span style="color:var(--danger)">*</span></label>
        <div style="position:relative">
          <input type="password" id="p3" autocomplete="new-password" placeholder="Re-enter new password to verify" required style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 38px 10px 12px; font-size:13.5px" />
          <button type="button" class="b ghost" style="position:absolute; right:6px; top:50%; transform:translateY(-50%); padding:2px 6px; font-size:13px; border:none; cursor:pointer" onclick="togglePasswordInputVisibility('p3')">👁️</button>
        </div>
      </div>

      <p class="err" id="pe" role="alert" style="margin:8px 0 14px; font-size:12.5px; font-weight:600; color:var(--danger)" hidden></p>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:18px">
        <button class="b" type="button" id="pc" onclick="closeChangePasswordModal()">Cancel</button>
        <button class="b p" type="submit" id="btnConfirmChangePw">Confirm &amp; Change Password</button>
      </div>
    </form>
  </dialog>'''

    content = content[:old_pwd.start()] + new_pwd + content[old_pwd.end():]

    # 3. Update Edit Name and Change Password JS controller functions
    old_edit_js = re.search(r'/\* ---------- Edit Employee Name Modal Controller ---------- \*/[\s\S]*?/\* =========================================================================\s+CONTAINER SWITCHER:', content)
    if not old_edit_js:
        raise Exception("Could not find Edit Employee Name Modal Controller in " + filepath)

    new_edit_js = '''/* ---------- Edit Employee Name Modal Controller ---------- */
      async function openEditNameModal() {
        const dlg = $('dlgEditName');
        if (!dlg) return;
        const u = getUser();
        let currentName = (window.CU && window.CU.name) || u.name || '';
        let prevName = (window.CU && window.CU.previous_name) || (u && u.previous_name) || '';

        // Fetch fresh profile from database
        try {
          const fresh = await api('/api/me');
          if (fresh && fresh.name) {
            currentName = fresh.name;
            prevName = fresh.previous_name || '';
            if (window.CU) Object.assign(window.CU, fresh);
          }
        } catch (_) {}

        if ($('editNamePrevious')) $('editNamePrevious').value = prevName || 'None (Initial registered name)';
        if ($('editNameCurrent')) $('editNameCurrent').value = currentName;
        if ($('editNameConfirmCurrent')) $('editNameConfirmCurrent').value = '';
        if ($('editNameNew')) $('editNameNew').value = '';
        if ($('editNameError')) {
          $('editNameError').textContent = '';
          $('editNameError').hidden = true;
        }
        if (!dlg.open) dlg.showModal();
        setTimeout(() => $('editNameConfirmCurrent')?.focus(), 50);
      }

      function closeEditNameModal() {
        const dlg = $('dlgEditName');
        if (dlg && dlg.open) dlg.close();
      }

      async function submitEditNameModal() {
        const errEl = $('editNameError');
        const currentName = ($('editNameCurrent')?.value || '').trim();
        const confirmCurrent = ($('editNameConfirmCurrent')?.value || '').trim();
        const newName = ($('editNameNew')?.value || '').trim();

        if (errEl) { errEl.textContent = ''; errEl.hidden = true; }

        if (!confirmCurrent) {
          if (errEl) { errEl.textContent = 'Please confirm your current registered name.'; errEl.hidden = false; }
          return;
        }
        if (confirmCurrent.toLowerCase() !== currentName.toLowerCase()) {
          if (errEl) { errEl.textContent = `Entered name "${confirmCurrent}" does not match registered name "${currentName}".`; errEl.hidden = false; }
          return;
        }
        if (!newName) {
          if (errEl) { errEl.textContent = 'Please enter a new employee name.'; errEl.hidden = false; }
          return;
        }
        if (newName.toLowerCase() === currentName.toLowerCase()) {
          if (errEl) { errEl.textContent = 'New name must be different from your current registered name.'; errEl.hidden = false; }
          return;
        }

        const btn = $('btnConfirmEditName');
        if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }

        try {
          const res = await api('/api/me/name', {
            method: 'PUT',
            body: JSON.stringify({ name: newName, confirm_current_name: confirmCurrent })
          });
          const updatedName = res.name || newName;
          const updatedPrevName = res.previous_name || currentName;

          // Update user state in memory & storage
          const u = getUser();
          u.name = updatedName;
          u.previous_name = updatedPrevName;
          localStorage.setItem('user', JSON.stringify(u));
          if (window.CU) {
            window.CU.name = updatedName;
            window.CU.previous_name = updatedPrevName;
          }

          if ($('hi')) {
            const h = new Date().getHours();
            $('hi').textContent = `Good ${h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening'}, ${updatedName}`;
          }
          const uInitial = ((updatedName[0] || 'U')[0] || 'U').toUpperCase();
          if ($('userAvatarCircle')) $('userAvatarCircle').textContent = uInitial;

          closeEditNameModal();
          toast(`Employee name successfully updated to "${updatedName}" in website & database`);

          await loadCU().catch(() => {});
          if (typeof loadUsersContainer === 'function' && $('usersTableWrap')) {
            loadUsersContainer();
          }
        } catch (err) {
          if (errEl) {
            errEl.textContent = err.message || 'Failed to update name.';
            errEl.hidden = false;
          }
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = 'Confirm & Update Name'; }
        }
      }

      /* ---------- Change Account Password Modal Controller ---------- */
      function togglePasswordInputVisibility(id) {
        const el = $(id);
        if (el) el.type = (el.type === 'password') ? 'text' : 'password';
      }

      function openChangePasswordModal() {
        const dlg = $('pwd');
        if (!dlg) return;
        if ($('pf')) $('pf').reset();
        if ($('pe')) { $('pe').textContent = ''; $('pe').hidden = true; }
        if (!dlg.open) dlg.showModal();
        setTimeout(() => $('p1')?.focus(), 50);
      }

      function closeChangePasswordModal() {
        const dlg = $('pwd');
        if (dlg && dlg.open) dlg.close();
      }

      if ($('bEditMyName')) $('bEditMyName').onclick = openEditNameModal;
      if ($('formEditName')) $('formEditName').onsubmit = e => { e.preventDefault(); submitEditNameModal(); };
      if ($('btnConfirmEditName')) $('btnConfirmEditName').onclick = submitEditNameModal;

      if ($('bPw')) $('bPw').onclick = openChangePasswordModal;
      if ($('pc')) $('pc').onclick = closeChangePasswordModal;
      if ($('closeDlgChangePassword')) $('closeDlgChangePassword').onclick = closeChangePasswordModal;
      if ($('btnConfirmChangePw')) $('btnConfirmChangePw').onclick = e => {
        if ($('pf')) {
          if (typeof $('pf').requestSubmit === 'function') {
            $('pf').requestSubmit();
          } else {
            $('pf').dispatchEvent(new Event('submit', { cancelable: true }));
          }
        }
      };

      if ($('pf')) $('pf').onsubmit = async e => {
        e.preventDefault();
        const pe = $('pe');
        if (pe) { pe.textContent = ''; pe.hidden = true; }
        const curPw = $('p1')?.value || '';
        const newPw = $('p2')?.value || '';
        const repPw = $('p3')?.value || '';

        if (!curPw) {
          if (pe) { pe.textContent = 'Please enter your current password.'; pe.hidden = false; }
          return;
        }
        if (!newPw || newPw.length < 8) {
          if (pe) { pe.textContent = 'New password must be at least 8 characters long.'; pe.hidden = false; }
          return;
        }
        if (newPw !== repPw) {
          if (pe) { pe.textContent = 'New password and confirm new password do not match.'; pe.hidden = false; }
          return;
        }

        const btn = $('btnConfirmChangePw');
        if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; }

        try {
          const r = await api('/api/me/password', { method: 'POST', body: JSON.stringify({ current_password: curPw, new_password: newPw }) });
          if (r.access_token) { tok = r.access_token; localStorage.setItem('token', tok); }
          closeChangePasswordModal();
          toast('Password updated successfully in website & database');
        } catch (err) {
          if (pe) { pe.textContent = err.message || 'Failed to update password.'; pe.hidden = false; }
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = 'Confirm & Change Password'; }
        }
      };

      /* =========================================================================
         CONTAINER SWITCHER:'''

    content = content[:old_edit_js.start()] + new_edit_js + content[old_edit_js.end() - len('/* =========================================================================\n         CONTAINER SWITCHER:'):]

    # 4. Update applyTheme with persistToDb and clean Settings wiring
    old_apply_theme = re.search(r'function applyTheme\(palette, mode\)[\s\S]*?function initThemeDock\(\)', content)
    if not old_apply_theme:
        raise Exception("Could not find applyTheme in " + filepath)

    new_apply_theme = '''function applyTheme(palette, mode, persistToDb = false) {
        const pal = palette || localStorage.getItem('valut_palette') || 'royal_navy';
        const m = mode || localStorage.getItem('valut_theme_mode') || 'light';

        document.documentElement.setAttribute('data-palette', pal);
        document.documentElement.setAttribute('data-mode', m);
        document.documentElement.setAttribute('data-theme', m);

        localStorage.setItem('valut_palette', pal);
        localStorage.setItem('valut_theme_mode', m);
        localStorage.setItem('theme', m);

        // Update active class & styles on palette buttons in Settings
        document.querySelectorAll('#dlgSettings .theme-palette-opt').forEach(opt => {
          const isActive = opt.dataset.paletteVal === pal;
          opt.classList.toggle('active', isActive);
          opt.style.borderColor = isActive ? 'var(--primary, #1d68e1)' : 'var(--line)';
          opt.style.background = isActive ? 'rgba(29, 104, 225, 0.08)' : 'var(--card)';
        });

        // Update active class & styles on mode buttons in Settings
        const btnDark = $('settingsModeDark');
        const btnLight = $('settingsModeLight');
        if (btnDark) {
          const isDark = m === 'dark';
          btnDark.classList.toggle('active', isDark);
          btnDark.style.background = isDark ? 'var(--primary, #1d68e1)' : 'transparent';
          btnDark.style.color = isDark ? '#ffffff' : 'var(--text)';
        }
        if (btnLight) {
          const isLight = m === 'light';
          btnLight.classList.toggle('active', isLight);
          btnLight.style.background = isLight ? 'var(--primary, #1d68e1)' : 'transparent';
          btnLight.style.color = isLight ? '#ffffff' : 'var(--text)';
        }

        if (persistToDb && localStorage.getItem('token')) {
          api('/api/me/theme', {
            method: 'PUT',
            body: JSON.stringify({ palette: pal, mode: m })
          }).catch(() => {});
        }
      }

      function initThemeDock()'''

    content = content[:old_apply_theme.start()] + new_apply_theme + content[old_apply_theme.end() - len('function initThemeDock()'):]

    # 5. Add Back-button / pageshow logout guards
    if 'window.addEventListener(\'pageshow\'' not in content:
        guard_code = '''
      // Logout Protection: Prevent browser Back button from accessing protected views
      window.addEventListener('pageshow', () => {
        if (!localStorage.getItem('token')) {
          switchView(false);
        }
      });
      window.addEventListener('popstate', () => {
        if (!localStorage.getItem('token')) {
          switchView(false);
        }
      });
'''
        # insert right before initApp
        pos = content.find('/* ---------- Main App Initialization ---------- */')
        if pos != -1:
            content = content[:pos] + guard_code + content[pos:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {filepath} successfully.")

update_file('frontend/index.html')
update_file('frontend/dashboard.html')

