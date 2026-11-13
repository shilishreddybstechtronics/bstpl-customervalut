import re

def update_html(filepath):
    print(f"Applying updates to {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Settings cleanup: Remove "✕ Close Settings" footer button
    close_footer_pattern = r'<div style="display:flex; justify-content:flex-end; margin-top:16px; padding-top:14px; border-top:1px solid var\(--line\)">\s*<button type="button" class="b" id="btnCloseDlgSettingsFooter"[^>]*>✕ Close Settings</button>\s*</div>'
    content = re.sub(close_footer_pattern, '', content)

    # 2. Live Updates close button & modal markup
    old_live_close = '<button class="b ghost" id="closeDlgLiveUpdates" type="button" style="color:#fff; font-size:20px; padding:4px 10px; cursor:pointer">✕</button>'
    new_live_close = '<button class="b ghost" id="closeDlgLiveUpdates" type="button" onclick="closeLiveUpdatesModal()" style="color:#fff; font-size:22px; padding:4px 12px; cursor:pointer; border-radius:8px; z-index:9999" aria-label="Close Live Updates">✕</button>'
    content = content.replace(old_live_close, new_live_close)

    # 3. Top header: Good Morning greeting on the RIGHT, Actions and Cart on the LEFT
    old_top_header = """      <!-- Top Navigation Header -->
      <header class="cv-top-header">
        <div class="cv-header-single-line">
          <!-- User Greeting & Role Badge -->
          <div class="user-badge" id="uBadge">
            <span id="hi">Good morning, Shilish Reddy</span>
            <span class="role-pill" id="rolePill">ADMIN</span>
          </div>

          <!-- Top Actions in One Line -->
          <div class="cv-header-actions acts">
            <button class="b" id="bAl" title="Toggle Expiry Alerts">Alerts: OFF</button>
            <button class="b" id="bRefresh" title="Reload current data">🔄 Refresh</button>
            <button class="b" id="bQs" title="Quick Search (Ctrl + K)"><span>🔎 Search</span></button>
            <button class="b b-logout" id="bLo" title="Sign out of your session">Logout</button>
          </div>

          <!-- Right Most Corner: User Profile Avatar Circle (Settings & Expiry Alert container removed from top bar) -->
          <div class="cv-header-icons">
            <div class="cv-avatar-circle" id="userAvatarCircle" title="User Profile">S</div>
          </div>
        </div>
      </header>"""

    new_top_header = """      <!-- Top Navigation Header (Requirement 7: Cart Repositioned; Requirement 8: Good Morning Greeting Restored on Right Side) -->
      <header class="cv-top-header">
        <div class="cv-header-single-line" style="display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap">
          <!-- Left Actions: Quick Search, Refresh, Expiry Alerts & Cart -->
          <div class="cv-header-actions acts" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <button class="b" id="bQs" title="Quick Search (Ctrl + K)"><span>🔎 Search</span></button>
            <button class="b" id="bRefresh" title="Reload current data">🔄 Refresh</button>
            <button class="b" id="bAl" title="Toggle Expiry Alerts">Alerts: OFF</button>
            <button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="showContainer('box-bin')" style="font-weight:700">
              🛒 Cart (<span id="headerCartCountBadge">0</span>)
            </button>
          </div>

          <!-- Right Side: Restored Good Morning Greeting Container & Profile Actions -->
          <div style="display:flex;align-items:center;gap:12px;margin-left:auto;flex-wrap:nowrap">
            <div class="user-badge" id="uBadge" style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;background:var(--card-subtle);border:1px solid var(--line);border-radius:99px;font-weight:700;font-size:13.5px">
              <span id="hi">Good morning, Shilish Reddy</span>
              <span class="role-pill" id="rolePill">ADMIN</span>
            </div>
            <div class="cv-avatar-circle" id="userAvatarCircle" title="User Settings & Account Options" onclick="openSettingsModal()" style="cursor:pointer">S</div>
            <button class="b b-logout" id="bLo" title="Sign out of your session" style="font-weight:700">Logout</button>
          </div>
        </div>
      </header>"""
    content = content.replace(old_top_header, new_top_header)

    # 4. Unhide Cart in mainTabs
    content = content.replace(
        '<button class="tab-btn" data-target="box-bin" hidden>🛒 Cart (<span id="cartCountBadge">0</span>)</button>',
        '<button class="tab-btn" data-target="box-bin">🛒 Cart (<span id="cartCountBadge">0</span>)</button>'
    )

    # 5. Settings Modal options wiring & closeDlg removal
    old_settings_js = """      if ($('settingsBtnEditName')) {
        $('settingsBtnEditName').onclick = () => {
          $('dlgSettings').close();
          const u = getUser();
          openDlg('Edit Display Name', `
            <label for="newName">Full Name</label>
            <input id="newName" value="${esc(u.name || '')}" placeholder="Your display name" required />
            <div class="row" style="margin-top:16px;justify-content:flex-end">
              <button class="b" type="button" id="cEdN">Cancel</button>
              <button class="b p" type="button" id="sEdN">Save</button>
            </div>
          `);
          $('cEdN').onclick = closeDlg;
          $('sEdN').onclick = async () => {
            const name = $('newName').value.trim();
            if (!name) return;
            try {
              const res = await api('/users/me', { method: 'PUT', body: JSON.stringify({ name }) });
              u.name = res.name;
              localStorage.setItem('user', JSON.stringify(u));
              closeDlg();
              await updateChrome();
              toast('Your display name has been updated');
            } catch (err) { fail(err); }
          };
        };
      }

      if ($('settingsBtnPassword')) {
        $('settingsBtnPassword').onclick = () => {
          $('dlgSettings').close();
          if ($('pwd')) $('pwd').showModal();
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

      if ($('settingsBtnLogout')) {
        $('settingsBtnLogout').onclick = () => {
          $('dlgSettings').close();
          if ($('bLo')) $('bLo').click();
        };
      }"""

    new_settings_js = """      // Settings Functionality Fixes (Requirement 2, 3, 4)
      if ($('settingsBtnEditName')) {
        $('settingsBtnEditName').onclick = () => {
          $('dlgSettings').close();
          const u = getUser();
          openDlg('Edit Display Name', `
            <label for="newName" style="font-weight:700;font-size:12.5px;display:block;margin-bottom:6px">Full Name</label>
            <input id="newName" value="${esc(u.name || '')}" placeholder="Your display name" required style="width:100%;padding:9px 12px;border:1px solid var(--line);border-radius:8px;font-size:13px;background:var(--card);color:var(--text)" />
          `, 'Save', async () => {
            const name = $('newName').value.trim();
            if (!name) throw new Error('Name cannot be empty.');
            const res = await api('/api/me/name', { method: 'PUT', body: JSON.stringify({ name }) });
            u.name = res.name || name;
            localStorage.setItem('user', JSON.stringify(u));
            await updateChrome();
            toast('Your display name has been updated');
          });
        };
      }

      if ($('settingsBtnPassword')) {
        $('settingsBtnPassword').onclick = () => {
          $('dlgSettings').close();
          if ($('pf')) $('pf').reset();
          if ($('pe')) $('pe').textContent = '';
          if ($('pwd')) $('pwd').showModal();
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

      if ($('settingsBtnLogout')) {
        $('settingsBtnLogout').onclick = () => {
          $('dlgSettings').close();
          logout(true);
        };
      }"""
    content = content.replace(old_settings_js, new_settings_js)

    # 6. Ensure canAccessUsersManager and canAccessLoginInventory allow admins
    old_can_access = """      const canAccessLoginInventory = () => {
        return isSuperAdminUser() || isMasterAdminUser();
      };
      const canAccessUsersManager = () => {
        return isSuperAdminUser() || isMasterAdminUser();
      };"""

    new_can_access = """      const canAccessLoginInventory = () => {
        const u = getUser();
        return isSuperAdminUser() || isMasterAdminUser() || u.role === 'admin' || Boolean(u.is_admin);
      };
      const canAccessUsersManager = () => {
        const u = getUser();
        return isSuperAdminUser() || isMasterAdminUser() || u.role === 'admin' || Boolean(u.is_admin);
      };"""
    content = content.replace(old_can_access, new_can_access)

    # 7. In logout(manual = false), ensure comprehensive session teardown and redirect
    old_logout = """      function logout(manual = false) {
        if (manual && tok) {
          try { fetch(API_BASE + '/auth/logout', { method: 'POST', headers: { Authorization: 'Bearer ' + tok }, keepalive: true }); } catch { }
        }
        clearTimeout(liveTimer);
        livePolling = false;
        tok = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        switchView(false);
        toast('Signed out');"""

    new_logout = """      function logout(manual = false) {
        if (manual && tok) {
          try { fetch(API_BASE + '/auth/logout', { method: 'POST', headers: { Authorization: 'Bearer ' + tok }, keepalive: true }); } catch { }
          try { fetch(API_BASE + '/api/auth/logout', { method: 'POST', headers: { Authorization: 'Bearer ' + tok }, keepalive: true }); } catch { }
        }
        clearTimeout(liveTimer);
        clearTimeout(liveCycleTimer);
        clearInterval(liveUpdatesModalTimer);
        livePolling = false;
        liveUpdatesActive = false;
        tok = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        try { sessionStorage.clear(); } catch(_) {}
        document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch(_) {} });
        switchView(false);
        toast('Signed out');"""
    content = content.replace(old_logout, new_logout)

    # 8. Prevent sidebarBtnSettings from getting overwritten
    content = content.replace(
        "if ($('sidebarBtnSettings')) $('sidebarBtnSettings').onclick = openManageUsersModal;",
        "if ($('sidebarBtnSettings')) $('sidebarBtnSettings').onclick = openSettingsModal;"
    )

    # 9. Live Updates Modal helpers
    old_live_modal_helpers = """      async function openLiveUpdatesModal() {
        const dlg = $('dlgLiveUpdatesModal');
        if (!dlg) return;
        dlg.showModal();
        await refreshLiveUpdatesModalData();
      }

      async function refreshLiveUpdatesModalData() {"""

    new_live_modal_helpers = """      let liveUpdatesModalTimer = null;
      function closeLiveUpdatesModal() {
        clearInterval(liveUpdatesModalTimer);
        liveUpdatesModalTimer = null;
        if ($('dlgLiveUpdatesModal') && $('dlgLiveUpdatesModal').open) {
          $('dlgLiveUpdatesModal').close();
        }
      }

      async function openLiveUpdatesModal() {
        const dlg = $('dlgLiveUpdatesModal');
        if (!dlg) return;
        if (!dlg.open) dlg.showModal();
        await refreshLiveUpdatesModalData();
        clearInterval(liveUpdatesModalTimer);
        liveUpdatesModalTimer = setInterval(refreshLiveUpdatesModalData, 6000);
      }

      async function refreshLiveUpdatesModalData() {"""
    content = content.replace(old_live_modal_helpers, new_live_modal_helpers)

    content = content.replace(
        "if ($('closeDlgLiveUpdates')) $('closeDlgLiveUpdates').onclick = () => $('dlgLiveUpdatesModal').close();",
        "if ($('closeDlgLiveUpdates')) $('closeDlgLiveUpdates').onclick = closeLiveUpdatesModal;"
    )

    # 10. Data Health: Call loadHealthContainer() inside loadHomeContainer()
    old_load_home = """      async function loadHomeContainer() {
        // Load recent activity from backend
        try {"""

    new_load_home = """      async function loadHomeContainer() {
        // Automatically load real database Data Health on Home (Requirement 6)
        loadHealthContainer();

        // Load recent activity from backend
        try {"""
    content = content.replace(old_load_home, new_load_home)

    # 11. SIM Expiry sorting in loadExpiryContainer()
    old_load_expiry = """          const [l, rep] = await Promise.all([
            api('/api/alerts/expiry?days=' + expDays),
            api('/api/inventory/report')
          ]);"""

    new_load_expiry = """          const [rawL, rep] = await Promise.all([
            api('/api/alerts/expiry?days=' + expDays),
            api('/api/inventory/report')
          ]);
          // Requirement 1: SIM Expiry sorting ascending by days remaining (fewest days left first, expired first)
          const l = (rawL || []).slice().sort((a, b) => {
            const d1 = (a.days_left != null) ? a.days_left : 999999;
            const d2 = (b.days_left != null) ? b.days_left : 999999;
            return d1 - d2;
          });"""
    content = content.replace(old_load_expiry, new_load_expiry)

    # 12. Also in fetchInventoryRows(), sort by expiry_date asc when expFilter is set
    old_fetch_inv = """          const [d, expSummary] = await Promise.all([
            api(`/api/devices?page=${invPage}&page_size=10&q=${encodeURIComponent(invQ)}&column=${invCol}&expiry_filter=${expFilter}&sort_by=${sortCol}&sort_dir=${sortDir}${invCid ? '&customer_id=' + invCid : ''}`),
            api(`/api/devices/expiry-summary${invCid ? '?customer_id=' + invCid : ''}`).catch(() => null)
          ]);"""

    new_fetch_inv = """          const activeSortCol = (expFilter !== 'all' && (!sortCol || sortCol === 'id')) ? 'expiry_date' : sortCol;
          const activeSortDir = (expFilter !== 'all' && (!sortCol || sortCol === 'id')) ? 'asc' : sortDir;
          const [d, expSummary] = await Promise.all([
            api(`/api/devices?page=${invPage}&page_size=10&q=${encodeURIComponent(invQ)}&column=${invCol}&expiry_filter=${expFilter}&sort_by=${activeSortCol}&sort_dir=${activeSortDir}${invCid ? '&customer_id=' + invCid : ''}`),
            api(`/api/devices/expiry-summary${invCid ? '?customer_id=' + invCid : ''}`).catch(() => null)
          ]);"""
    content = content.replace(old_fetch_inv, new_fetch_inv)

    # 13. Update updateChrome to keep headerCartCountBadge synced
    old_cart_badge = "$('cartCountBadge').textContent = (cart.length + (S.deleted_customers || 0)).toString();"
    new_cart_badge = """const cartTotalNum = (cart.length + (S.deleted_customers || 0)).toString();
          if ($('cartCountBadge')) $('cartCountBadge').textContent = cartTotalNum;
          if ($('headerCartCountBadge')) $('headerCartCountBadge').textContent = cartTotalNum;"""
    content = content.replace(old_cart_badge, new_cart_badge)

    # 14. Bulk Upload Status and Review UI (Requirement 9 & 10)
    # Simplify the review filter buttons to focus on NEW records and eliminate update categories
    old_val_filter_btns = """                <div style="display:flex;gap:6px;flex-wrap:wrap" id="valFilterBtns">
                  <button class="b on" data-valfilter="all" type="button" id="btnFilterAll">All (<span id="vAllCount">0</span>)</button>
                  <button class="b" data-valfilter="new" type="button" id="btnFilterNew" style="font-weight:700;color:var(--ok)">✨ New (<span id="vNewCount">0</span>)</button>
                  <button class="b" data-valfilter="updated" type="button" id="btnFilterUpdated" style="font-weight:700;color:#0284c7">🔄 Updated (<span id="vUpdatedCount">0</span>)</button>
                  <button class="b" data-valfilter="existing" type="button" id="btnFilterExisting">📋 Existing (<span id="vExistingCount">0</span>)</button>
                  <button class="b" data-valfilter="review" type="button" id="btnFilterReview" style="font-weight:700;color:#d97706">🔍 Review (<span id="vReviewCount">0</span>)</button>
                  <button class="b" data-valfilter="duplicate" type="button" id="btnFilterDup">⚠️ Duplicates (<span id="vDupCount">0</span>)</button>
                  <button class="b" data-valfilter="cannot" type="button" id="btnFilterCannot" style="font-weight:700;color:#dc2626">⛔ Blocked (<span id="vCannotCount">0</span>)</button>
                </div>"""

    new_val_filter_btns = """                <div style="display:flex;gap:6px;flex-wrap:wrap" id="valFilterBtns">
                  <button class="b on" data-valfilter="new" type="button" id="btnFilterNew" style="font-weight:700;color:var(--ok)">✨ New Records Eligible for Insertion (<span id="vNewCount">0</span>)</button>
                  <button class="b" data-valfilter="existing" type="button" id="btnFilterExisting">📋 Skipped Existing in DB (<span id="vExistingCount">0</span>)</button>
                  <button class="b" data-valfilter="duplicate" type="button" id="btnFilterDup">⚠️ File Duplicates (<span id="vDupCount">0</span>)</button>
                </div>"""
    content = content.replace(old_val_filter_btns, new_val_filter_btns)

    # Simplify the 7 segregation cards to focus on NEW records and exact scanned count (Requirement 10)
    old_val_stat_cards = """            <!-- The 7 Segregation Metric Cards (Requirements 3 & 5) -->
            <div class="stats" style="margin-top:10px;grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:8px">
              <div class="card stat" style="border-left-color:var(--primary);padding:10px 12px"><b id="vTotalScanned">0</b><span>1. Total Scanned</span></div>
              <div class="card stat" style="border-left-color:#10b981;padding:10px 12px"><b id="vValid">0</b><span>2. Valid Entries</span></div>
              <div class="card stat" style="border-left-color:#f59e0b;padding:10px 12px"><b id="vReview">0</b><span>3. Requiring Review</span></div>
              <div class="card stat" style="border-left-color:#ef4444;padding:10px 12px"><b id="vDup">0</b><span>4. Duplicate Entries</span></div>
              <div class="card stat" style="border-left-color:var(--ok);padding:10px 12px"><b id="vNew">0</b><span>5. Eligible to Add</span></div>
              <div class="card stat" style="border-left-color:#38bdf8;padding:10px 12px"><b id="vUpdated">0</b><span>6. Eligible to Update</span></div>
              <div class="card stat" style="border-left-color:#64748b;padding:10px 12px"><b id="vCannotAdd">0</b><span>7. Cannot Add/Update</span></div>
            </div>"""

    new_val_stat_cards = """            <!-- Bulk Upload Status Metric Cards (Requirement 10: Only New Records & Total Scanned File Count) -->
            <div class="stats" style="margin-top:10px;grid-template-columns:repeat(auto-fit, minmax(170px, 1fr));gap:10px">
              <div class="card stat" style="border-left-color:var(--primary);padding:12px 14px"><b id="vTotalScanned">0</b><span>📄 Total Scanned File Rows</span></div>
              <div class="card stat" style="border-left-color:var(--ok);padding:12px 14px"><b id="vNew" style="color:var(--ok)">0</b><span>✨ Total New Records</span></div>
              <div class="card stat" style="border-left-color:#10b981;padding:12px 14px"><b id="vValid">0</b><span>✅ Ready for Insertion</span></div>
              <div class="card stat" style="border-left-color:#94a3b8;padding:12px 14px"><b id="vExistingCountCard">0</b><span>📋 Skipped Existing Records</span></div>
              <div class="card stat" style="border-left-color:#ef4444;padding:12px 14px"><b id="vDup" style="color:#ef4444">0</b><span>⚠️ Duplicate File Entries</span></div>
            </div>"""
    content = content.replace(old_val_stat_cards, new_val_stat_cards)

    # Progress bar metrics: Display ONLY Total New Records, Ready for Insertion, Successfully Inserted, Failed New Records (Requirement 10)
    old_prog_stats = """            <!-- Live Metric Counters -->
            <div class="stats" style="margin:14px 0 10px;grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));gap:10px">
              <div class="card stat" style="padding:10px 14px"><b id="progTotalCount" style="font-size:16px">0</b><span>Total Data</span></div>
              <div class="card stat" style="padding:10px 14px;border-left-color:var(--primary)"><b id="progUploadedCount" style="font-size:16px">0</b><span>Uploaded</span></div>
              <div class="card stat" style="padding:10px 14px;border-left-color:var(--muted)"><b id="progRemainCount" style="font-size:16px">0</b><span>Remaining</span></div>
              <div class="card stat" style="padding:10px 14px;border-left-color:var(--ok)"><b id="progAddedCount" style="font-size:16px">0</b><span>Added New to DB</span></div>
              <div class="card stat" style="padding:10px 14px;border-left-color:#38bdf8"><b id="progUpdatedCount" style="font-size:16px">0</b><span>Updated</span></div>
              <div class="card stat" style="padding:10px 14px;border-left-color:var(--warn)"><b id="progDupCount" style="font-size:16px">0</b><span>Duplicate Errors</span></div>
            </div>"""

    new_prog_stats = """            <!-- Bulk Upload Live Status (Requirement 10: Total New, Ready for Insertion, Successfully Inserted, Failed New) -->
            <div class="stats" style="margin:14px 0 10px;grid-template-columns:repeat(auto-fit, minmax(160px, 1fr));gap:10px">
              <div class="card stat" style="padding:10px 14px;border-left-color:var(--primary)"><b id="progTotalCount" style="font-size:16px">0</b><span>Total New Records</span></div>
              <div class="card stat" style="padding:10px 14px;border-left-color:#0284c7"><b id="progUploadedCount" style="font-size:16px">0</b><span>New Records Ready for Insertion</span></div>
              <div class="card stat" style="padding:10px 14px;border-left-color:var(--ok)"><b id="progAddedCount" style="font-size:16px;color:var(--ok)">0</b><span>Successfully Inserted New Records</span></div>
              <div class="card stat" style="padding:10px 14px;border-left-color:var(--danger)"><b id="progFailedCount" style="font-size:16px;color:var(--danger)">0</b><span>Failed New Records</span></div>
            </div>"""
    content = content.replace(old_prog_stats, new_prog_stats)

    # 15. Default preview filter to 'new'
    content = content.replace(
        "let wbData = null, parsedRows = [], activeValResult = null, activeValFilter = 'all';",
        "let wbData = null, parsedRows = [], activeValResult = null, activeValFilter = 'new';"
    )

    # Update reconciliation text to clarify Insert-Only
    content = content.replace(
        "<span>📐</span> <span>Reconciliation: Total Scan = Eligible Add + Eligible Update + Duplicate/Skip + Review + Cannot Add</span>",
        "<span>📐</span> <span>Reconciliation: Total Scanned = New Eligible Records + Skipped Existing in Database + File Duplicates</span>"
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {filepath} successfully.")

update_html('frontend/index.html')
update_html('frontend/dashboard.html')

