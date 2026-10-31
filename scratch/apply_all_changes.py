import os
import shutil

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove Cart tab from mainTabs
old_tab = '''        <button class="tab-btn cv-pill-danger" data-target="box-errors">🚨 Errored Entries (<span id="errorsCountBadge">0</span>)</button>
        <button class="tab-btn" data-target="box-bin">🛒 Cart (<span id="cartCountBadge">0</span>)</button>
      </nav>'''

new_tab = '''        <button class="tab-btn cv-pill-danger" data-target="box-errors">🚨 Errored Entries (<span id="errorsCountBadge">0</span>)</button>
      </nav>'''

assert old_tab in content, "old_tab not found"
content = content.replace(old_tab, new_tab, 1)

# 2. Update Header Cart button to openCartModal()
old_hdr_cart = '''            <button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="showContainer('box-bin')" style="font-weight:700">
              🛒 Cart (<span id="headerCartCountBadge">0</span>)
            </button>'''

new_hdr_cart = '''            <button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="openCartModal()" style="font-weight:700">
              🛒 Cart (<span id="headerCartCountBadge">0</span>)
            </button>'''

assert old_hdr_cart in content, "old_hdr_cart not found"
content = content.replace(old_hdr_cart, new_hdr_cart, 1)

# 3. Replace Cart section with Modal Dialog
old_cart_sec = '''    <!-- =========================================================================
       CONTAINER 11: SEPARATE CART (RECYCLE BIN)
       ========================================================================= -->
    <section class="container-box" id="box-bin">
      <div class="container-tag">🛒 Cart / Recycle Bin Container</div>
      <div class="row">
        <div class="grow">
          <h2>Cart — Recover Deleted Items</h2>
          <p class="sub" style="margin:0">Items placed in the Cart remain recoverable. Restore with 1 click or
            permanently purge forever.</p>
        </div>
        <button class="b d" id="btnEmptyCart" hidden>Empty Cart Forever</button>
      </div>

      <!-- Cart Deletion Progress Container (matches Upload Data Progress UI) -->
      <div id="cartEmptyProgressWrap" hidden style="margin:18px 0;background:var(--card);padding:20px;border:1.5px solid var(--danger, #ef4444);border-radius:12px;box-shadow:0 6px 20px rgba(239,68,68,0.12)">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px">
          <div style="display:flex;align-items:center;gap:10px">
            <span id="cartProgSpinIcon" class="spin" style="font-size:22px">⏳</span>
            <div>
              <div style="display:flex;align-items:center;gap:8px">
                <img src="logo.svg" alt="Company Logo" style="width:20px;height:20px;object-fit:contain" onerror="this.style.display='none'" />
                <b id="cartProgTitle" style="font-size:15px;color:var(--ink)">Emptying Cart Forever (Permanent Deletion)…</b>
              </div>
              <div id="cartProgStatus" style="font-size:12.5px;color:var(--danger, #dc2626);font-weight:600;margin-top:2px">Preparing batches…</div>
            </div>
          </div>
          <div style="text-align:right">
            <span id="cartProgPct" style="font-size:22px;font-weight:800;color:var(--danger, #dc2626)">0%</span>
            <div id="cartProgRowsCount" style="font-size:12px;font-weight:600;color:var(--muted)">0 / 0 records</div>
          </div>
        </div>

        <!-- Animated Progress Bar -->
        <div class="progress-bar" style="height:14px;background:var(--card-subtle);border-radius:7px;overflow:hidden;margin:10px 0;border:1px solid var(--line)">
          <div class="progress-fill" id="cartProgBar" style="width:0%;height:100%;background:linear-gradient(90deg, #ef4444, #dc2626);transition:width 0.2s ease"></div>
        </div>

        <!-- Live Metric Counters -->
        <div class="stats" style="margin:14px 0 10px;grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:10px">
          <div class="card stat" style="padding:10px 14px"><b id="cartProgTotalCount" style="font-size:16px">0</b><span>Total in Cart</span></div>
          <div class="card stat" style="padding:10px 14px;border-left-color:var(--danger, #ef4444)"><b id="cartProgDeletedCount" style="font-size:16px;color:var(--danger, #dc2626)">0</b><span>Permanently Deleted</span></div>
          <div class="card stat" style="padding:10px 14px;border-left-color:var(--muted)"><b id="cartProgRemainCount" style="font-size:16px">0</b><span>Remaining in Cart</span></div>
          <div class="card stat" style="padding:10px 14px;border-left-color:#f97316"><b id="cartProgCustsCount" style="font-size:16px">0</b><span>Customer Tables Dropped</span></div>
          <div class="card stat" style="padding:10px 14px;border-left-color:var(--primary)"><b id="cartProgElapsed" style="font-size:16px">0.0s</b><span>Time Elapsed</span></div>
        </div>

        <!-- Live Monospace Activity Stream Log Box -->
        <div id="cartProgLiveDetailBox" style="background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px 14px;font-size:12px;max-height:120px;overflow-y:auto;font-family:monospace;margin-top:10px">
          <div style="color:var(--muted)">[Ready] Waiting to start permanent deletion…</div>
        </div>

        <!-- Completion Banner -->
        <div id="cartProgCompleteBanner" hidden style="margin-top:14px;background:var(--ok-bg, rgba(16,185,129,0.1));border:1px solid var(--ok, #10b981);border-radius:10px;padding:14px;color:var(--ink)">
          <div style="font-weight:700;font-size:14px;color:var(--ok, #10b981);margin-bottom:4px">✅ Cart Successfully Emptied!</div>
          <div id="cartProgCompleteSummary" style="font-size:13px">All deleted device records and customer tables have been permanently erased from the database and TiDB Cloud.</div>
        </div>

        <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap">
          <button class="b" id="btnCloseCartProgress" type="button">✕ Dismiss Deletion Status</button>
          <button class="b p" id="btnRefreshCart" type="button">🔄 Refresh Cart</button>
        </div>
      </div>

      <div id="cartBody">
        <div class="empty">Checking Cart items…</div>
      </div>
    </section>'''

new_cart_sec = '''    <!-- =========================================================================
       POPUP MODAL: CART (RECYCLE BIN) - Opens as popup with Cross (X) close
       ========================================================================= -->
    <dialog id="dlgCartModal" class="modal-card" style="width:min(1100px, 95vw); max-height:90vh; padding:0; border-radius:18px; border:1px solid var(--line); box-shadow:0 30px 80px rgba(0,0,0,.45); overflow:hidden">
      <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 22px;border-bottom:1px solid var(--line);background:var(--card-subtle);position:sticky;top:0;z-index:10">
        <div style="display:flex;align-items:center;gap:10px">
          <span style="font-size:24px">🛒</span>
          <div>
            <h3 style="margin:0;font-size:17px;font-weight:800;color:var(--text)">Cart — Recover Deleted Items</h3>
            <p class="sub" style="margin:2px 0 0;font-size:12px">Items placed in the Cart remain recoverable. Restore with 1 click or permanently purge forever.</p>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
          <button class="b d" id="btnEmptyCart" hidden>Empty Cart Forever</button>
          <button class="b ghost" id="closeDlgCart" type="button" onclick="closeCartModal()" style="font-size:18px;min-width:38px;min-height:38px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;border-radius:8px" aria-label="Close Cart">✕</button>
        </div>
      </div>

      <div style="padding:20px 24px; max-height:calc(90vh - 80px); overflow-y:auto" id="box-bin">
        <!-- Cart Deletion Progress Container (matches Upload Data Progress UI) -->
        <div id="cartEmptyProgressWrap" hidden style="margin:0 0 18px;background:var(--card);padding:20px;border:1.5px solid var(--danger, #ef4444);border-radius:12px;box-shadow:0 6px 20px rgba(239,68,68,0.12)">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px">
            <div style="display:flex;align-items:center;gap:10px">
              <span id="cartProgSpinIcon" class="spin" style="font-size:22px">⏳</span>
              <div>
                <div style="display:flex;align-items:center;gap:8px">
                  <img src="logo.svg" alt="Company Logo" style="width:20px;height:20px;object-fit:contain" onerror="this.style.display='none'" />
                  <b id="cartProgTitle" style="font-size:15px;color:var(--ink)">Emptying Cart Forever (Permanent Deletion)…</b>
                </div>
                <div id="cartProgStatus" style="font-size:12.5px;color:var(--danger, #dc2626);font-weight:600;margin-top:2px">Preparing batches…</div>
              </div>
            </div>
            <div style="text-align:right">
              <span id="cartProgPct" style="font-size:22px;font-weight:800;color:var(--danger, #dc2626)">0%</span>
              <div id="cartProgRowsCount" style="font-size:12px;font-weight:600;color:var(--muted)">0 / 0 records</div>
            </div>
          </div>

          <!-- Animated Progress Bar -->
          <div class="progress-bar" style="height:14px;background:var(--card-subtle);border-radius:7px;overflow:hidden;margin:10px 0;border:1px solid var(--line)">
            <div class="progress-fill" id="cartProgBar" style="width:0%;height:100%;background:linear-gradient(90deg, #ef4444, #dc2626);transition:width 0.2s ease"></div>
          </div>

          <!-- Live Metric Counters -->
          <div class="stats" style="margin:14px 0 10px;grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:10px">
            <div class="card stat" style="padding:10px 14px"><b id="cartProgTotalCount" style="font-size:16px">0</b><span>Total in Cart</span></div>
            <div class="card stat" style="padding:10px 14px;border-left-color:var(--danger, #ef4444)"><b id="cartProgDeletedCount" style="font-size:16px;color:var(--danger, #dc2626)">0</b><span>Permanently Deleted</span></div>
            <div class="card stat" style="padding:10px 14px;border-left-color:var(--muted)"><b id="cartProgRemainCount" style="font-size:16px">0</b><span>Remaining in Cart</span></div>
            <div class="card stat" style="padding:10px 14px;border-left-color:#f97316"><b id="cartProgCustsCount" style="font-size:16px">0</b><span>Customer Tables Dropped</span></div>
            <div class="card stat" style="padding:10px 14px;border-left-color:var(--primary)"><b id="cartProgElapsed" style="font-size:16px">0.0s</b><span>Time Elapsed</span></div>
          </div>

          <!-- Live Monospace Activity Stream Log Box -->
          <div id="cartProgLiveDetailBox" style="background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px 14px;font-size:12px;max-height:120px;overflow-y:auto;font-family:monospace;margin-top:10px">
            <div style="color:var(--muted)">[Ready] Waiting to start permanent deletion…</div>
          </div>

          <!-- Completion Banner -->
          <div id="cartProgCompleteBanner" hidden style="margin-top:14px;background:var(--ok-bg, rgba(16,185,129,0.1));border:1px solid var(--ok, #10b981);border-radius:10px;padding:14px;color:var(--ink)">
            <div style="font-weight:700;font-size:14px;color:var(--ok, #10b981);margin-bottom:4px">✅ Cart Successfully Emptied!</div>
            <div id="cartProgCompleteSummary" style="font-size:13px">All deleted device records and customer tables have been permanently erased from the database and TiDB Cloud.</div>
          </div>

          <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap">
            <button class="b" id="btnCloseCartProgress" type="button">✕ Dismiss Deletion Status</button>
            <button class="b p" id="btnRefreshCart" type="button">🔄 Refresh Cart</button>
          </div>
        </div>

        <div id="cartBody">
          <div class="empty">Checking Cart items…</div>
        </div>
      </div>
    </dialog>'''

assert old_cart_sec in content, "old_cart_sec not found"
content = content.replace(old_cart_sec, new_cart_sec, 1)

# 4. In showContainer: intercept box-bin
old_show_container = '''        if (boxId === 'box-users') {
          openManageUsersModal();
          return;
        }'''

new_show_container = '''        if (boxId === 'box-users') {
          openManageUsersModal();
          return;
        }
        if (boxId === 'box-bin') {
          openCartModal();
          return;
        }'''

assert old_show_container in content, "old_show_container not found"
content = content.replace(old_show_container, new_show_container, 1)

# 5. Add openCartModal and closeCartModal helper functions
old_close_live = '''      // Large Live Updates Popup Modal Handler'''
new_close_live = '''      // Cart Popup Modal Handlers (Requirement: Cart opens as popup with Cross X close)
      function openCartModal() {
        const dlg = $('dlgCartModal');
        if (!dlg) return;
        loadCartContainer();
        if (!dlg.open) dlg.showModal();
      }

      function closeCartModal() {
        const dlg = $('dlgCartModal');
        if (dlg && dlg.open) dlg.close();
      }

      // Large Live Updates Popup Modal Handler'''

assert old_close_live in content, "old_close_live not found"
content = content.replace(old_close_live, new_close_live, 1)

# 6. Master Admin Password Visibility in loadUsersContainer
old_users_head = '''        $('usersTableWrap').innerHTML = `
      <div class="tw"><table><thead><tr>
        <th>Employee Name</th><th>Login ID</th><th>Security Role & Tier</th><th>Access Role</th>${isSuperAdmin ? '<th>User Password</th>' : ''}<th>Configured Permissions</th><th>Created Date</th><th>Actions</th>
      </tr></thead><tbody>'''

new_users_head = '''        $('usersTableWrap').innerHTML = `
      <div class="tw"><table><thead><tr>
        <th>Employee Name</th><th>Login ID</th><th>Security Role & Tier</th><th>Access Role</th>${(isSuperAdmin || isMasterAdmin) ? '<th>User Password</th>' : ''}<th>Configured Permissions</th><th>Created Date</th><th>Actions</th>
      </tr></thead><tbody>'''

assert old_users_head in content, "old_users_head not found"
content = content.replace(old_users_head, new_users_head, 1)

old_users_pwd = '''            // Super Admin password visibility (mutual privacy: 0001 and 0007 cannot see each other's passwords)
            let pwdColHtml = '';
            if (isSuperAdmin) {'''

new_users_pwd = '''            // Super Admin and Master Admin password visibility (0001 and 0007 mutual privacy)
            let pwdColHtml = '';
            if (isSuperAdmin || isMasterAdmin) {'''

assert old_users_pwd in content, "old_users_pwd not found"
content = content.replace(old_users_pwd, new_users_pwd, 1)

# 7. In openSettingsModal: role-based visibility and actions wiring
old_open_settings = '''      function openSettingsModal() {
        const dlg = $('dlgSettings');
        if (!dlg) return;
        const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
        const currentMode = localStorage.getItem('valut_theme_mode') || 'light';

        // Highlight active palette and mode'''

new_open_settings = '''      function openSettingsModal() {
        const dlg = $('dlgSettings');
        if (!dlg) return;
        const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
        const currentMode = localStorage.getItem('valut_theme_mode') || 'light';

        // Role-based visibility for Settings actions
        if ($('settingsBtnManageUsers')) {
          $('settingsBtnManageUsers').style.display = canAccessUsersManager() ? 'flex' : 'none';
        }
        if ($('settingsBtnLoginInv')) {
          $('settingsBtnLoginInv').style.display = canAccessLoginInventory() ? 'flex' : 'none';
        }

        // Highlight active palette and mode'''

assert old_open_settings in content, "old_open_settings not found"
content = content.replace(old_open_settings, new_open_settings, 1)

old_settings_btns = '''      // Settings Log Out Button
      if ($('settingsBtnLogout')) {
        $('settingsBtnLogout').onclick = () => {
          $('dlgSettings').close();
          if ($('bLo')) $('bLo').click();
        };
      }'''

new_settings_btns = '''      // Settings Actions Wiring (Edit Name, Change Password, Manage Users, Log Inventory, Logout)
      if ($('settingsBtnEditName')) {
        $('settingsBtnEditName').onclick = async () => {
          $('dlgSettings').close();
          const u = getUser();
          const p = prompt('Enter your new employee display name:', u.name || '');
          if (!p || !p.trim() || p.trim() === u.name) return;
          try {
            const r = await api('/api/me/name', { method: 'PUT', body: JSON.stringify({ name: p.trim() }) });
            toast('Display name updated: ' + (r.name || p.trim()));
            await loadCU();
            await updateChrome();
          } catch (err) { fail(err); }
        };
      }

      if ($('settingsBtnPassword')) {
        $('settingsBtnPassword').onclick = () => {
          $('dlgSettings').close();
          if ($('bPw')) $('bPw').click();
          else if ($('dlgPw')) $('dlgPw').showModal();
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
      }

      // Settings Log Out Button
      if ($('settingsBtnLogout')) {
        $('settingsBtnLogout').onclick = () => {
          $('dlgSettings').close();
          logout(true);
        };
      }'''

assert old_settings_btns in content, "old_settings_btns not found"
content = content.replace(old_settings_btns, new_settings_btns, 1)

# 8. Clean parseCSV quotes
old_parse_csv = '''      /* ---------- CSV Parser Utility ---------- */
      function parseCSV(t) {
        const R = []; let r = [], f = '', q = false;
        for (let i = 0; i < t.length; i++) {
          const c = t[i];
          if (q) {
            if (c === '"') { if (t[i + 1] === '"') { f += '"'; i++; } else q = false; }
            else f += c;
          } else if (c === '"') q = true;
          else if (c === ',') { r.push(f); f = ''; }
          else if (c === '\\n' || c === '\\r') {
            if (c === '\\r' && t[i + 1] === '\\n') i++;
            r.push(f); f = '';
            if (r.some(x => x.trim())) R.push(r);
            r = [];
          } else f += c;
        }
        r.push(f);
        if (r.some(x => x.trim())) R.push(r);
        return R;
      }'''

new_parse_csv = '''      /* ---------- CSV Parser Utility ---------- */
      function parseCSV(t) {
        const R = []; let r = [], f = "", q = false;
        for (let i = 0; i < t.length; i++) {
          const c = t[i];
          if (q) {
            if (c === '"') {
              if (t[i + 1] === '"') { f += '"'; i++; }
              else { q = false; }
            } else {
              f += c;
            }
          } else if (c === '"') {
            q = true;
          } else if (c === ",") {
            r.push(f);
            f = "";
          } else if (c === "\\n" || c === "\\r") {
            if (c === "\\r" && t[i + 1] === "\\n") i++;
            r.push(f);
            f = "";
            if (r.some(x => x.trim())) R.push(r);
            r = [];
          } else {
            f += c;
          }
        }
        r.push(f);
        if (r.some(x => x.trim())) R.push(r);
        return R;
      }'''

assert old_parse_csv in content, "old_parse_csv not found"
content = content.replace(old_parse_csv, new_parse_csv, 1)

# Write back to index.html and dashboard.html with CRLF line endings
with open('frontend/index.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)

with open('frontend/dashboard.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)

print("Successfully updated frontend/index.html and synced frontend/dashboard.html!")
