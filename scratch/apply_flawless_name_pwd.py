import os
import shutil

# 1. Update backend/main.py
with open("backend/main.py", "r", encoding="utf-8") as f:
    main_text = f.read()

target_pos = 'def me(current_user: models.User = Depends(get_current_user)):\n    return user_out(current_user, current_user)'
if target_pos not in main_text:
    target_pos = 'def me(current_user: models.User = Depends(get_current_user)):\r\n    return user_out(current_user, current_user)'

assert target_pos in main_text, "target_pos in main.py not found"

root_endpoints = """

@app.put("/me/name")
@app.post("/me/name")
@app.put("/api/me/name")
@app.post("/api/me/name")
def update_my_name_root(data: schemas.UserNameUpdate, request: Request, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    from routes_users import update_my_name
    return update_my_name(data, request, db, current_user)


@app.post("/me/password")
@app.put("/me/password")
@app.post("/api/me/password")
@app.put("/api/me/password")
@app.post("/me/change-password")
@app.put("/me/change-password")
@app.post("/api/me/change-password")
@app.put("/api/me/change-password")
def change_password_root(data: schemas.PasswordIn, request: Request, db: Session = Depends(get_db),
                         user: models.User = Depends(get_current_user)):
    from routes_users import change_password
    return change_password(data, request, db, user)"""

if 'def update_my_name_root' not in main_text:
    main_text = main_text.replace(target_pos, target_pos + root_endpoints)
    with open("backend/main.py", "w", encoding="utf-8") as f:
        f.write(main_text)
    print("✓ Added direct root endpoints to backend/main.py")

# 2. Update frontend/index.html
with open("frontend/index.html", "r", encoding="utf-8") as f:
    html_text = f.read()

# Update HTML Save buttons to type="button" with direct onclick handlers to prevent duplicate form submissions
html_text = html_text.replace(
    '<button class="b p" type="submit" id="btnConfirmEditName">Save</button>',
    '<button class="b p" type="button" id="btnConfirmEditName" onclick="submitEditNameModal()">Save</button>'
)

html_text = html_text.replace(
    '<button class="b p" type="submit" id="btnConfirmChangePw">Confirm &amp; Change Password</button>',
    '<button class="b p" type="button" id="btnConfirmChangePw" onclick="submitChangePasswordModal()">Confirm &amp; Change Password</button>'
)

# Replace the Edit Name and Change Password controllers with clean, robust, easy-to-understand and edit implementations
js_block_old_start = html_text.find("/* ---------- Edit Employee Name Modal Controller ---------- */")
js_block_old_end = html_text.find("/* =========================================================================\n         CONTAINER SWITCHER:", js_block_old_start)
if js_block_old_end == -1:
    js_block_old_end = html_text.find("/* =========================================================================\r\n         CONTAINER SWITCHER:", js_block_old_start)

assert js_block_old_start != -1 and js_block_old_end != -1, "JS block positions not found"

js_replacement = """/* =========================================================================
         SETTINGS & ACCOUNT OPTIONS: EDIT NAME & CHANGE PASSWORD CONTROLLERS
         Easy to read, easy to edit, smoothly synchronized with database & frontend
         ========================================================================= */

      /* ---------- 1. EDIT NAME MODAL CONTROLLER ---------- */
      let isSubmittingEditName = false;

      async function openEditNameModal() {
        const dlg = $('dlgEditName');
        if (!dlg) return;

        // Current name from local user state
        const u = getUser();
        let currentName = u.name || u.user_id || '';

        // Fetch latest profile from database to ensure fresh registered name
        try {
          const fresh = await api('/api/me');
          if (fresh && fresh.name) {
            currentName = fresh.name;
            u.name = fresh.name;
            localStorage.setItem('user', JSON.stringify(u));
          }
        } catch (_) {}

        // Populate fields: Current Name (read-only), reset Updated & Confirm Name
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
        if (isSubmittingEditName) return;

        const errEl = $('editNameError');
        const currentName = ($('editNameCurrent')?.value || '').trim();
        const updatedName = ($('editNameUpdated')?.value || '').trim();
        const confirmName = ($('editNameConfirm')?.value || '').trim();

        if (errEl) { errEl.textContent = ''; errEl.hidden = true; }

        // Validations: non-empty, different from current, confirm matches
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
        isSubmittingEditName = true;

        try {
          // Send update to database API
          const res = await api('/api/me/name', {
            method: 'PUT',
            body: JSON.stringify({ name: updatedName, confirm_name: confirmName })
          });
          const finalName = res.name || updatedName;

          // 1. Immediately update user in local storage
          const u = getUser();
          u.name = finalName;
          localStorage.setItem('user', JSON.stringify(u));

          // 2. Immediately update Top Header Greeting banner
          if ($('hi')) {
            const h = new Date().getHours();
            $('hi').textContent = `Good ${h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening'}, ${finalName}`;
          }

          // 3. Immediately update Top Header Avatar circle initial
          const uInitial = ((finalName[0] || 'U')[0] || 'U').toUpperCase();
          if ($('userAvatarCircle')) $('userAvatarCircle').textContent = uInitial;

          // 4. Immediately update Settings Profile banner & subtitle
          if ($('settingsAccountName')) $('settingsAccountName').textContent = finalName;
          if ($('settingsCurrentNameVal')) $('settingsCurrentNameVal').textContent = finalName;
          if ($('settingsUserAvatarCircle')) $('settingsUserAvatarCircle').textContent = uInitial;

          // 5. Update Current Name field in the modal itself
          if ($('editNameCurrent')) $('editNameCurrent').value = finalName;

          // 6. Refresh Manage Users & Permissions table if loaded
          if (typeof loadUsersContainer === 'function' && $('usersTableWrap')) {
            loadUsersContainer();
          }

          // Close Edit Name modal and reopen Settings so user immediately sees the change
          closeEditNameModal(false);
          openSettingsModal();
          toast(`Name updated successfully to "${finalName}" in website & database`);

          // Background chrome sync
          await updateChrome().catch(() => {});
        } catch (err) {
          if (errEl) {
            errEl.textContent = err.message || 'Failed to update name.';
            errEl.hidden = false;
          }
        } finally {
          isSubmittingEditName = false;
          if (btn) { btn.disabled = false; btn.textContent = 'Save'; }
        }
      }

      window.openEditNameModal = openEditNameModal;
      window.closeEditNameModal = closeEditNameModal;
      window.submitEditNameModal = submitEditNameModal;

      if ($('bEditMyName')) $('bEditMyName').onclick = openEditNameModal;
      if ($('formEditName')) $('formEditName').onsubmit = e => { e.preventDefault(); submitEditNameModal(); };
      if ($('btnConfirmEditName')) $('btnConfirmEditName').onclick = e => { e.preventDefault(); submitEditNameModal(); };

      /* ---------- 2. CHANGE PASSWORD MODAL CONTROLLER ---------- */
      let isSubmittingPassword = false;

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

      function closeChangePasswordModal(reopenSettings = true) {
        const dlg = $('pwd');
        if (dlg && dlg.open) dlg.close();
        if (reopenSettings && $('dlgSettings')) {
          openSettingsModal();
        }
      }

      async function submitChangePasswordModal() {
        if (isSubmittingPassword) return;

        const pe = $('pe');
        if (pe) { pe.textContent = ''; pe.hidden = true; }
        const curPw = $('p1')?.value || '';
        const newPw = $('p2')?.value || '';
        const repPw = $('p3')?.value || '';

        // Validations
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
        isSubmittingPassword = true;

        try {
          // Submit password update to backend database API
          const r = await api('/api/me/password', {
            method: 'POST',
            body: JSON.stringify({ current_password: curPw, new_password: newPw })
          });

          // Refresh JWT token in localStorage
          if (r && r.access_token) {
            tok = r.access_token;
            localStorage.setItem('token', tok);
          }

          if ($('pf')) $('pf').reset();
          closeChangePasswordModal(false);
          openSettingsModal();
          toast('Password updated successfully in website & database');
        } catch (err) {
          if (pe) {
            pe.textContent = err.message || 'Failed to update password.';
            pe.hidden = false;
          }
        } finally {
          isSubmittingPassword = false;
          if (btn) { btn.disabled = false; btn.textContent = 'Confirm & Change Password'; }
        }
      }

      window.togglePasswordInputVisibility = togglePasswordInputVisibility;
      window.openChangePasswordModal = openChangePasswordModal;
      window.closeChangePasswordModal = closeChangePasswordModal;
      window.submitChangePasswordModal = submitChangePasswordModal;

      if ($('bPw')) $('bPw').onclick = openChangePasswordModal;
      if ($('pc')) $('pc').onclick = () => closeChangePasswordModal(true);
      if ($('closeDlgChangePassword')) $('closeDlgChangePassword').onclick = () => closeChangePasswordModal(true);
      if ($('pf')) $('pf').onsubmit = e => { e.preventDefault(); submitChangePasswordModal(); };
      if ($('btnConfirmChangePw')) $('btnConfirmChangePw').onclick = e => { e.preventDefault(); submitChangePasswordModal(); };\n\n      """

html_text = html_text[:js_block_old_start] + js_replacement + html_text[js_block_old_end:]

# Also update openSettingsModal() to use u.name cleanly without undefined window.CU.name
html_text = html_text.replace(
    "const currentName = (window.CU && window.CU.name) || u.name || u.user_id || 'Employee';",
    "const currentName = u.name || u.user_id || 'Employee';"
)

# Write to both frontend/index.html and frontend/dashboard.html
with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(html_text)

with open("frontend/dashboard.html", "w", encoding="utf-8") as f:
    f.write(html_text)

print("✓ Updated frontend/index.html and frontend/dashboard.html with clean, flawless controllers")

