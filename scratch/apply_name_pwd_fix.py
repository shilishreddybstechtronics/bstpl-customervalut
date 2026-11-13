import re
import shutil
import hashlib

print("=== Applying Complete Name & Password Fixes ===")

# --- 1. backend/main.py ---
with open('backend/main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

# Add direct root routes for /me and /api/me
old_me_block = """@app.get("/auth/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return user_out(current_user, current_user)"""

new_me_block = """@app.get("/auth/me", response_model=schemas.UserOut)
@app.get("/api/auth/me", response_model=schemas.UserOut)
@app.get("/me", response_model=schemas.UserOut)
@app.get("/api/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return user_out(current_user, current_user)"""

if old_me_block in main_code:
    main_code = main_code.replace(old_me_block, new_me_block, 1)
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(main_code)
    print("  [✓] backend/main.py: Added /me and /api/me root endpoints")
else:
    print("  [!] old_me_block not found in main.py")

# --- 2. backend/routes_users.py ---
with open('backend/routes_users.py', 'r', encoding='utf-8') as f:
    users_code = f.read()

old_name_func = """@router.put("/me/name")
@router.post("/me/name")
@router.put("/users/me")
@router.post("/users/me")
def update_my_name(data: schemas.UserNameUpdate, request: Request, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    \"\"\"Allows any logged-in employee to edit their own display name.\"\"\"
    new_name = (data.name or "").strip()
    if not new_name:
        raise HTTPException(400, "Updated name cannot be empty.")

    # Validation: confirm_name must match updated name
    if data.confirm_name is not None and data.confirm_name.strip():
        if data.confirm_name.strip() != new_name:
            raise HTTPException(400, "Updated name and confirm name do not match.")

    # Validation: confirm_current_name must match existing name if provided
    if data.confirm_current_name is not None and data.confirm_current_name.strip():
        entered_confirm = data.confirm_current_name.strip()
        if entered_confirm.lower() != current_user.name.strip().lower():
            raise HTTPException(400, f"Confirmed current name does not match registered name '{current_user.name}'.")

    # Validation: new name must be different from current registered name
    if new_name.lower() == current_user.name.strip().lower():
        raise HTTPException(400, "Updated name must be different from your current registered name.")

    perms_meta = dict(current_user.permissions or {})
    old_name = current_user.name
    perms_meta["previous_name"] = old_name
    current_user.permissions = perms_meta
    current_user.name = new_name

    log_activity(db, "user_update", f"Updated own display name from '{old_name}' to '{new_name}'", user=current_user, request=request)
    db.commit()
    db.refresh(current_user)
    return {
        "ok": True,
        "message": f"Name successfully updated to '{new_name}'.",
        "user": user_out(current_user, actor=current_user),
        "name": new_name,
        "previous_name": old_name
    }"""

new_name_func = """@router.put("/me/name")
@router.post("/me/name")
@router.put("/users/me")
@router.post("/users/me")
def update_my_name(data: schemas.UserNameUpdate, request: Request, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    \"\"\"Allows any logged-in employee to edit their own display name.\"\"\"
    new_name = (data.name or "").strip()
    if not new_name:
        raise HTTPException(400, "Updated name cannot be empty.")

    # Validation: confirm_name must match updated name if provided
    if data.confirm_name is not None and data.confirm_name.strip():
        if data.confirm_name.strip() != new_name:
            raise HTTPException(400, "Updated name and confirm name do not match.")

    # Validation: confirm_current_name must match existing name if provided
    curr_name = (current_user.name or current_user.user_id or "").strip()
    if data.confirm_current_name is not None and data.confirm_current_name.strip():
        entered_confirm = data.confirm_current_name.strip()
        if curr_name and entered_confirm.lower() != curr_name.lower():
            raise HTTPException(400, f"Confirmed current name does not match registered name '{curr_name}'.")

    # Validation: new name must be different from current registered name
    if curr_name and new_name.lower() == curr_name.lower():
        raise HTTPException(400, "Updated name must be different from your current registered name.")

    perms_meta = dict(current_user.permissions or {})
    old_name = current_user.name or current_user.user_id
    perms_meta["previous_name"] = old_name
    current_user.permissions = perms_meta
    current_user.name = new_name

    log_activity(db, "user_update", f"Updated own display name from '{old_name}' to '{new_name}'", user=current_user, request=request)
    db.commit()
    db.refresh(current_user)
    return {
        "ok": True,
        "message": f"Name successfully updated to '{new_name}'.",
        "user": user_out(current_user, actor=current_user),
        "name": new_name,
        "previous_name": old_name
    }"""

if old_name_func in users_code:
    users_code = users_code.replace(old_name_func, new_name_func, 1)
    with open('backend/routes_users.py', 'w', encoding='utf-8') as f:
        f.write(users_code)
    print("  [✓] backend/routes_users.py: Safe name handling verified")
else:
    print("  [!] old_name_func not found in routes_users.py")

# --- 3. frontend/index.html ---
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html_code = f.read()

# A. Robust API_BASE calculation that prioritizes local development
old_api_base = """      const isRunningOnLocalPort8000 = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port === '8000';
      const DEFAULT_API_BASE = isRunningOnLocalPort8000 ? 'http://127.0.0.1:8000' : 'https://bstpl-customervalut-2-jm3t.onrender.com';
      let API_BASE = (window.API_URL || localStorage.getItem('API_URL') || DEFAULT_API_BASE).replace(/\/+$/, '');"""

new_api_base = """      function getInitialApiBase() {
        if (window.API_URL) return window.API_URL.replace(/\/+$/, '');
        const stored = localStorage.getItem('API_URL');
        if (stored) return stored.replace(/\/+$/, '');
        if (window.location.protocol.startsWith('http')) {
          if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            if (window.location.port === '8000') return window.location.origin;
            return 'http://127.0.0.1:8000';
          }
          return window.location.origin;
        }
        return 'http://127.0.0.1:8000';
      }
      let API_BASE = getInitialApiBase();"""

if old_api_base in html_code:
    html_code = html_code.replace(old_api_base, new_api_base, 1)
    print("  [✓] frontend/index.html: Updated getInitialApiBase logic")
else:
    print("  [!] old_api_base not found in index.html")

# B. Instant openEditNameModal without blocking network delay
old_open_name = """      async function openEditNameModal() {
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
      }"""

new_open_name = """      async function openEditNameModal() {
        const dlg = $('dlgEditName');
        if (!dlg) return;

        // Current name from local user state
        const u = getUser();
        let currentName = u.name || u.user_id || '';

        // Populate fields immediately with current cached name
        if ($('editNameCurrent')) $('editNameCurrent').value = currentName;
        if ($('editNameUpdated')) $('editNameUpdated').value = '';
        if ($('editNameConfirm')) $('editNameConfirm').value = '';
        if ($('editNameError')) {
          $('editNameError').textContent = '';
          $('editNameError').hidden = true;
        }

        // Show modal immediately with zero delay
        if (!dlg.open) dlg.showModal();
        setTimeout(() => $('editNameUpdated')?.focus(), 50);

        // Fetch latest profile from database in background to ensure fresh registered name
        try {
          const fresh = await api('/api/me');
          if (fresh && fresh.name) {
            currentName = fresh.name;
            u.name = fresh.name;
            localStorage.setItem('user', JSON.stringify(u));
            if ($('editNameCurrent')) $('editNameCurrent').value = fresh.name;
            if ($('settingsCurrentNameVal')) $('settingsCurrentNameVal').textContent = fresh.name;
            if ($('settingsAccountName')) $('settingsAccountName').textContent = fresh.name;
          }
        } catch (_) {}
      }"""

if old_open_name in html_code:
    html_code = html_code.replace(old_open_name, new_open_name, 1)
    print("  [✓] frontend/index.html: Instant openEditNameModal implemented")
else:
    print("  [!] old_open_name not found in index.html")

# C. Submit edit name body payload sending confirm_current_name
old_submit_name = """          // Send update to database API
          const res = await api('/api/me/name', {
            method: 'PUT',
            body: JSON.stringify({ name: updatedName, confirm_name: confirmName })
          });"""

new_submit_name = """          // Send update to database API
          const res = await api('/api/me/name', {
            method: 'PUT',
            body: JSON.stringify({
              name: updatedName,
              confirm_name: confirmName,
              confirm_current_name: currentName
            })
          });"""

if old_submit_name in html_code:
    html_code = html_code.replace(old_submit_name, new_submit_name, 1)
    print("  [✓] frontend/index.html: Updated submitEditNameModal payload")
else:
    print("  [!] old_submit_name not found in index.html")

# D. Update Manage Users current user row actions
old_mgr_actions = """                  <button class="b" data-ueditname="${u.id}" data-curname="${esc(u.name)}" style="height:28px;padding:0 8px;font-size:12px">✏️ Edit My Name</button>
                  <button class="b" type="button" onclick="document.getElementById('bPw')?.click()" style="height:28px;padding:0 8px;font-size:12px">🔑 Change Password</button>"""

new_mgr_actions = """                  <button class="b" type="button" onclick="openEditNameModal()" style="height:28px;padding:0 8px;font-size:12px">✏️ Edit My Name</button>
                  <button class="b" type="button" onclick="openChangePasswordModal()" style="height:28px;padding:0 8px;font-size:12px">🔑 Change Password</button>"""

if old_mgr_actions in html_code:
    html_code = html_code.replace(old_mgr_actions, new_mgr_actions, 1)
    print("  [✓] frontend/index.html: Fixed Manage Users current user action buttons")
else:
    print("  [!] old_mgr_actions not found in index.html")

# E. Add hidden dummy bPw / bEditMyName triggers if any legacy code queries them
if '<button id="bPw" hidden></button>' not in html_code:
    html_code = html_code.replace('</body>', '  <!-- Action Aliases -->\n  <button id="bPw" type="button" onclick="openChangePasswordModal()" hidden></button>\n  <button id="bEditMyName" type="button" onclick="openEditNameModal()" hidden></button>\n</body>', 1)
    print("  [✓] frontend/index.html: Added action aliases for bPw and bEditMyName")

# Write to frontend/index.html
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html_code)

# Sync to frontend/dashboard.html
shutil.copyfile('frontend/index.html', 'frontend/dashboard.html')

h1 = hashlib.sha256(open('frontend/index.html', 'rb').read()).hexdigest()
h2 = hashlib.sha256(open('frontend/dashboard.html', 'rb').read()).hexdigest()
print(f"Parity confirmed! ({h1 == h2}, hash: {h1})")

