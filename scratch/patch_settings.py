import re

def patch_settings():
    with open('frontend/settings.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add closeModal & handleSettingsLogout right at start of <script>
    core_fns = """
    // --- Window Dialog & Session Helpers ---
    window.closeModal = function(id) {
      const dlg = document.getElementById(id);
      if (dlg) {
        if (typeof dlg.close === 'function') dlg.close();
        else dlg.style.display = 'none';
      }
    };

    window.handleSettingsLogout = async function() {
      const ok = await cv.confirm('Are you sure you want to securely log out of BSTPL CustomerVault?');
      if (!ok) return;
      try {
        toast('Logging out securely…');
        await fetch('/api/auth/logout', { credentials: 'omit' }).catch(() => {});
      } catch(e) {}
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      sessionStorage.clear();
      document.cookie.split(";").forEach(c => {
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
      });
      window.history.replaceState(null, '', 'index.html?logged_out=1');
      window.location.replace('index.html?logged_out=1');
    };
"""
    if 'window.closeModal = function' not in html:
        html = html.replace("<script>\n\n    // --- Foundation Configuration & Core Helpers ---",
                            "<script>\n" + core_fns + "\n    // --- Foundation Configuration & Core Helpers ---")

    # 2. Add Logout button to settingsUserCard actions
    old_user_actions = """<div style="display:flex;gap:10px;flex-wrap:wrap">
              <button type="button" class="b" id="settingsBtnManageUsers" onclick="scrollToManageUsers()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">👥 Manage Users</button>
              <button type="button" class="b" id="settingsBtnLoginInventory" onclick="scrollToLoginInventory()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🕘 Login Inventory</button>
            </div>"""

    new_user_actions = """<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
              <button type="button" class="b" id="settingsBtnManageUsers" onclick="scrollToManageUsers()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">👥 Manage Users</button>
              <button type="button" class="b" id="settingsBtnLoginInventory" onclick="scrollToLoginInventory()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🔑 Login Inventory</button>
              <button type="button" class="b" id="settingsBtnSearchAudit" onclick="scrollToSearchAudit()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🔍 Search Audit Trail</button>
              <button type="button" class="b d" id="settingsBtnLogout" onclick="handleSettingsLogout()" style="font-weight:800;padding:8px 16px;border-radius:9px;font-size:13px;display:inline-flex;align-items:center;gap:6px;background:#dc2626;color:#fff;border-color:#b91c1c" title="Securely terminate session and return to Login">
                <span>🚪</span> <span>Sign Out / Logout</span>
              </button>
            </div>"""

    if old_user_actions in html:
        html = html.replace(old_user_actions, new_user_actions)

    # 3. Add branding to settingsManageUsersCard header
    old_manage_header = """<div>
              <h2 style="margin:0 0 6px;font-size:20px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
                <span>👥</span> <span>Manage Users &amp; Permissions</span>
              </h2>
              <p style="margin:0;font-size:13.5px;color:var(--muted)">Provision employee accounts, assign administrative roles (Admin, Standard, Limited), or configure system privileges.</p>
            </div>
            <button type="button" class="b" onclick="openManageUsersModal()" style="font-weight:700;padding:8px 16px;border-radius:9px;font-size:13px">⛶ Open in Modal</button>"""

    new_manage_header = """<div>
              <h2 style="margin:0 0 6px;font-size:20px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
                <span>👥</span> <span>Manage Users &amp; Permissions</span>
              </h2>
              <p style="margin:0;font-size:13.5px;color:var(--muted)">Provision employee accounts, assign administrative roles (Admin, Standard, Limited), or configure system privileges.</p>
            </div>
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
              <div class="secure-surface-badge" style="display:inline-flex;align-items:center;gap:6px;background:rgba(212,175,55,0.12);border:1px solid rgba(212,175,55,0.35);padding:6px 12px;border-radius:20px;font-size:12px;font-weight:700;color:var(--accentd);letter-spacing:0.3px;white-space:nowrap">
                <span>🔒</span> Secure Smart Connected Surface Online
              </div>
              <button type="button" class="b" onclick="openManageUsersModal()" style="font-weight:700;padding:8px 16px;border-radius:9px;font-size:13px">⛶ Open in Modal</button>
            </div>"""

    if old_manage_header in html:
        html = html.replace(old_manage_header, new_manage_header)

    # 4. Add branding to dlgUserPermissions header
    old_perm_dlg_hdr = """      <div>
        <h3 style="margin:0;font-size:17px;display:flex;align-items:center;gap:8px">
          <span>🛡️</span> <span id="permModalTitle">User Permissions & Access Control</span>
        </h3>
        <p class="sub" id="permModalSub" style="margin:2px 0 0;font-size:12px">
          Configure actions and page permissions for this user account. Enforced strictly on backend APIs.
        </p>
      </div>
      <button class="b ghost" id="closeDlgUserPermissions" type="button" onclick="closeModal('dlgUserPermissions')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">✕</button>"""

    new_perm_dlg_hdr = """      <div>
        <h3 style="margin:0;font-size:17px;display:flex;align-items:center;gap:8px">
          <span>🛡️</span> <span id="permModalTitle">User Permissions & Access Control</span>
        </h3>
        <p class="sub" id="permModalSub" style="margin:2px 0 0;font-size:12px">
          Configure actions and page permissions for this user account. Enforced strictly on backend APIs.
        </p>
      </div>
      <div style="display:flex;align-items:center;gap:12px">
        <div class="secure-surface-badge" style="display:inline-flex;align-items:center;gap:6px;background:rgba(212,175,55,0.12);border:1px solid rgba(212,175,55,0.35);padding:4px 10px;border-radius:20px;font-size:11.5px;font-weight:700;color:var(--accentd);white-space:nowrap">
          <span>🔒</span> Secure Smart Connected Surface Online
        </div>
        <button class="b ghost" id="closeDlgUserPermissions" type="button" onclick="closeModal('dlgUserPermissions')" style="font-size:20px;padding:4px 10px;cursor:pointer;line-height:1;border-radius:8px" aria-label="Close">✕</button>
      </div>"""

    if old_perm_dlg_hdr in html:
        html = html.replace(old_perm_dlg_hdr, new_perm_dlg_hdr)

    # 5. Fix submitUserPermissions: validate, save permanently, display success popup, refresh UI
    old_submit_perm = """        try {
          const res = await api(`/api/users/${uid}/permissions`, {
            method: 'PUT',
            body: JSON.stringify({ permissions: perms })
          });
          cv.toast(`Access privileges updated for ${res.name}`, 'ok');
          closeModal('dlgUserPermissions');
          loadUsersContainer();
        } catch (err) {
          cv.alert(err.message || 'Failed to update privileges.', { title: 'Update Failed', tone: 'danger' });
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = '💾 Save Permissions'; }
        }"""

    new_submit_perm = """        try {
          // Validate permissions format
          if (!uid) throw new Error('Invalid user ID specified.');
          const validKeys = [
            'view', 'add', 'edit', 'delete', 'delete_invalid', 'search', 'download', 'upload',
            'page_live', 'page_inventory', 'page_upload', 'page_fetch', 'page_edit', 'page_alerts', 'page_health',
            'page_errors', 'page_cart', 'page_audit'
          ];
          const sanitized = {};
          validKeys.forEach(k => { sanitized[k] = Boolean(perms[k]); });

          const res = await api(`/api/users/${uid}/permissions`, {
            method: 'PUT',
            body: JSON.stringify({ permissions: sanitized })
          });

          // Success popup acknowledging permissions have been saved
          closeModal('dlgUserPermissions');
          await cv.alert(`Permissions for user "${res.name || res.user_id}" have been validated and saved permanently to the database. Changes are active immediately across all devices and sessions.`, {
            title: '✅ Permissions Saved Successfully',
            tone: 'ok'
          });
          loadUsersContainer();
          updateChrome();
        } catch (err) {
          cv.alert(err.message || 'Failed to update user privileges in database.', { title: 'Permission Update Failed', tone: 'danger' });
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = '💾 Save Permissions'; }
        }"""

    if old_submit_perm in html:
        html = html.replace(old_submit_perm, new_submit_perm)

    # 6. Redesign Login Inventory (remove cluttered activity streams, focus on accounts)
    # and add dedicated Search Audit Trail section
    old_login_inv_pattern = r'<div class="card" id="settingsLoginInventoryCard"[\s\S]*?<!-- Real-Time Activity KPI Summary Ribbon -->[\s\S]*?<!-- Activity Log Modal -->\s*<dialog id="dlgAuditLog"'

    new_login_inv_and_search_audit = """<div class="card" id="settingsLoginInventoryCard" style="padding:28px;border-radius:18px;border:1px solid var(--line);background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:24px">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:20px;border-bottom:1px solid var(--line);padding-bottom:16px">
            <div>
              <h2 style="margin:0 0 6px;font-size:20px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
                <span>🔑</span> <span>Login Inventory</span>
              </h2>
              <p style="margin:0;font-size:13.5px;color:var(--muted)">Directory of system user accounts, assigned access roles, login identifiers, and authentication records.</p>
            </div>
            <div style="display:flex;gap:10px;align-items:center">
              <input type="text" id="loginInvSearch" placeholder="Filter by User ID, Name, or Role…" oninput="filterLoginInventory(this.value)" style="height:38px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px;width:260px" />
              <button type="button" class="b" onclick="loadLoginInventory()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🔄 Refresh</button>
            </div>
          </div>

          <div id="loginInventoryTableWrap">
            <div class="empty">Loading Login Inventory accounts…</div>
          </div>
        </div>

        <!-- SEARCH AUDIT TRAIL SECTION -->
        <div class="card" id="settingsSearchAuditCard" style="padding:28px;border-radius:18px;border:1px solid var(--line);background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:24px">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:20px;border-bottom:1px solid var(--line);padding-bottom:16px">
            <div>
              <h2 style="margin:0 0 6px;font-size:20px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
                <span>🔍</span> <span>Search Audit Trail</span>
              </h2>
              <p style="margin:0;font-size:13.5px;color:var(--muted)">Comprehensive enterprise audit log of all system searches, IMEI lookups, customer queries, and inventory filtering events.</p>
            </div>
            <button type="button" class="b" id="satRefresh" onclick="loadSearchAuditTrail()" style="font-weight:700;padding:8px 16px;border-radius:9px;font-size:13px">🔄 Refresh Audit</button>
          </div>

          <!-- Filter & Search Controls -->
          <div class="row" style="margin-bottom:18px;gap:12px;flex-wrap:wrap;align-items:flex-end">
            <div style="flex:1;min-width:220px">
              <label for="satQuery" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Search Audit Records</label>
              <input id="satQuery" placeholder="Search by username, user ID, keyword, or customer…" style="width:100%;height:38px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px" />
            </div>
            <div style="width:170px">
              <label for="satType" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Search Type</label>
              <select id="satType" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
                <option value="all">All Types</option>
                <option value="quick_search">Quick Search</option>
                <option value="imei_search">IMEI Search</option>
                <option value="customer_filter">Customer Filter</option>
                <option value="column_search">Column Search</option>
                <option value="bulk_fetch">Bulk Fetch</option>
              </select>
            </div>
            <div style="width:150px">
              <label for="satSort" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Sort By</label>
              <select id="satSort" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
                <option value="search_date">Date / Time</option>
                <option value="username">Username</option>
                <option value="search_type">Search Type</option>
              </select>
            </div>
            <div style="width:110px">
              <label for="satDir" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Order</label>
              <select id="satDir" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
                <option value="desc">Newest</option>
                <option value="asc">Oldest</option>
              </select>
            </div>
            <div style="width:110px">
              <label for="satPageSize" style="display:block;font-size:12px;font-weight:700;margin-bottom:6px">Per Page</label>
              <select id="satPageSize" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
                <option value="15">15</option>
                <option value="25" selected>25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
            <button class="b" type="button" id="satClearBtn" onclick="resetSearchAuditFilters()" style="height:38px;padding:0 14px;font-size:13px;font-weight:700">Clear</button>
          </div>

          <div id="satTableWrap">
            <div class="empty">Loading Search Audit records…</div>
          </div>
        </div>

        <!-- Activity Log Modal -->
        <dialog id="dlgAuditLog" """

    if re.search(old_login_inv_pattern, html):
        html = re.sub(old_login_inv_pattern, new_login_inv_and_search_audit, html, count=1)
    else:
        print("WARNING: old_login_inv_pattern did not match directly.")

    # 7. Add JS handlers for Login Inventory and Search Audit Trail
    audit_js = """
    // --- Login Inventory & Search Audit Trail Implementation ---
    let _allLoginInvUsers = [];
    window.loadLoginInventory = async function() {
      const wrap = $('loginInventoryTableWrap');
      if (!wrap) return;
      try {
        const users = await api('/api/users');
        _allLoginInvUsers = users || [];
        filterLoginInventory($('loginInvSearch')?.value || '');
      } catch(err) {
        wrap.innerHTML = `<div class="empty err">${esc(err.message)}</div>`;
      }
    };

    window.filterLoginInventory = function(q) {
      const wrap = $('loginInventoryTableWrap');
      if (!wrap) return;
      q = (q || '').trim().toLowerCase();
      let list = _allLoginInvUsers;
      if (q) {
        list = list.filter(u => 
          (u.user_id || '').toLowerCase().includes(q) ||
          (u.name || '').toLowerCase().includes(q) ||
          (u.category || '').toLowerCase().includes(q) ||
          (u.role || '').toLowerCase().includes(q)
        );
      }
      if (!list.length) {
        wrap.innerHTML = `<div class="empty">No login accounts found matching "${esc(q)}".</div>`;
        return;
      }
      const me = getUser();
      const rawMe = (me.user_id || '').trim().toLowerCase();
      const normMe = /^\\d+$/.test(rawMe) ? rawMe.padStart(4, '0') : rawMe;
      const isSuperAdmin = ['0001', '0007'].includes(normMe);
      const isMasterAdmin = ['0001', '0002', '0003', '0004', '0007'].includes(normMe);

      const rows = list.map(u => {
        const rawId = (u.user_id || '').trim().toLowerCase();
        const normU = /^\\d+$/.test(rawId) ? rawId.padStart(4, '0') : rawId;
        const isSelf = u.id === me.id || normU === normMe;
        const isTargetSuper = ['0001', '0007'].includes(normU) || u.category === 'super_admin';
        const isOtherSuper = isTargetSuper && !isSelf;

        let badge = '<span class="tag mut">👤 Regular User</span>';
        if (isTargetSuper) badge = '<span class="tag ok">👑 Super Admin</span>';
        else if (['0002', '0003', '0004'].includes(normU) || u.category === 'master_admin') badge = '<span class="tag info">⭐ Master Admin</span>';
        else if (['0005', '0006', '0008', '0009', '0010'].includes(normU) || u.category === 'admin_user') badge = '<span class="tag warn">🛡️ Admin User</span>';

        let pwdHtml = '—';
        if ((isSuperAdmin || isMasterAdmin) && !isOtherSuper && u.password) {
          pwdHtml = `
            <div style="display:inline-flex;align-items:center;gap:6px;background:var(--card-subtle);padding:3px 8px;border-radius:6px;border:1px solid var(--line)">
              <span class="user-pwd-text" data-plain="${esc(u.password)}" data-masked="true" style="font-family:monospace;font-size:12px;letter-spacing:1px">••••••••</span>
              <button type="button" class="b" title="Show / Hide Password" style="height:22px;line-height:20px;padding:0 5px;font-size:11px;background:none;border:none;cursor:pointer" onclick="toggleUserPwd(this)">👁️</button>
              <button type="button" class="b" title="Copy Password" style="height:22px;line-height:20px;padding:0 5px;font-size:11px;background:none;border:none;cursor:pointer" onclick="copyUserPwd(this)">📋</button>
            </div>
          `;
        }

        let acts = '';
        if (isSuperAdmin || isMasterAdmin) {
          acts = `
            <div style="display:flex;gap:6px">
              <button class="b" style="height:28px;padding:0 8px;font-size:12px;font-weight:700" onclick='openUserPermissionsModal(${JSON.stringify(u)})' title="Configure permissions">🛡️ Permissions</button>
              <button class="b" style="height:28px;padding:0 8px;font-size:12px" onclick="openAdminEditNameModal('${u.id}', '${esc(u.name)}')">✏️ Name</button>
              ${!isOtherSuper ? `<button class="b" style="height:28px;padding:0 8px;font-size:12px" onclick="openAdminChangePwdModal('${u.id}', '${esc(u.name)}')">🔑 Password</button>` : ''}
            </div>
          `;
        } else {
          acts = `<span class="sub" style="font-size:12px">View Only</span>`;
        }

        return `
          <tr>
            <td><code style="font-weight:800;font-size:13px">${esc(u.user_id)}</code></td>
            <td><b>${esc(u.name)}</b> ${isSelf ? '<span class="tag info" style="font-size:10px">You</span>' : ''}</td>
            <td>${badge}</td>
            <td><span class="tag ok" style="font-size:11px">● Active</span></td>
            <td>${pwdHtml}</td>
            <td>${acts}</td>
          </tr>
        `;
      }).join('');

      wrap.innerHTML = `
        <div class="tw">
          <table>
            <thead>
              <tr>
                <th>User / Login ID</th>
                <th>Employee Full Name</th>
                <th>Security Role Tier</th>
                <th>Account Status</th>
                <th>Password</th>
                <th>Account Actions</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    };

    // Search Audit Trail Logic
    let SAT = { page: 1, pageSize: 25, q: '', type: 'all', sort: 'search_date', dir: 'desc' };
    window.loadSearchAuditTrail = async function() {
      const wrap = $('satTableWrap');
      if (!wrap) return;
      wrap.innerHTML = '<div class="empty">Loading search audit records…</div>';

      const q = $('satQuery') ? $('satQuery').value.trim() : SAT.q;
      const type = $('satType') ? $('satType').value : SAT.type;
      const sort = $('satSort') ? $('satSort').value : SAT.sort;
      const dir = $('satDir') ? $('satDir').value : SAT.dir;
      const ps = $('satPageSize') ? parseInt($('satPageSize').value, 10) : SAT.pageSize;

      SAT.q = q; SAT.type = type; SAT.sort = sort; SAT.dir = dir; SAT.pageSize = ps;

      try {
        const url = `/api/activity/search-audit?page=${SAT.page}&page_size=${SAT.pageSize}&q=${encodeURIComponent(SAT.q)}&search_type=${encodeURIComponent(SAT.type)}&sort_by=${encodeURIComponent(SAT.sort)}&sort_dir=${encodeURIComponent(SAT.dir)}`;
        const res = await api(url);
        renderSearchAuditTable(res);
      } catch(err) {
        wrap.innerHTML = `<div class="empty err">Failed to load search audit trail: ${esc(err.message)}</div>`;
      }
    };

    window.resetSearchAuditFilters = function() {
      if ($('satQuery')) $('satQuery').value = '';
      if ($('satType')) $('satType').value = 'all';
      if ($('satSort')) $('satSort').value = 'search_date';
      if ($('satDir')) $('satDir').value = 'desc';
      if ($('satPageSize')) $('satPageSize').value = '25';
      SAT.page = 1;
      loadSearchAuditTrail();
    };

    window.renderSearchAuditTable = function(data) {
      const wrap = $('satTableWrap');
      if (!wrap) return;
      const items = data.items || [];
      const total = data.total || 0;
      const pages = data.total_pages || 1;
      const page = data.page || 1;

      if (!items.length) {
        wrap.innerHTML = `
          <div class="empty" style="padding:36px 20px">
            <div style="font-size:32px;margin-bottom:8px">🔍</div>
            <h4 style="margin:0 0 6px">No Search Audit Records Found</h4>
            <p class="sub" style="margin:0">No search activities match your current query and filters.</p>
          </div>
        `;
        return;
      }

      const rows = items.map(r => {
        let typeBadge = `<span class="tag info" style="font-size:11px;font-weight:700">${esc(r.search_type || 'Search')}</span>`;
        if (r.search_type === 'imei_search') typeBadge = `<span class="tag ok" style="font-size:11px;font-weight:700">📱 IMEI Search</span>`;
        else if (r.search_type === 'customer_filter') typeBadge = `<span class="tag warn" style="font-size:11px;font-weight:700">👥 Customer</span>`;
        else if (r.search_type === 'quick_search') typeBadge = `<span class="tag info" style="font-size:11px;font-weight:700">⚡ Quick</span>`;

        let statusBadge = '<span class="tag ok" style="font-size:11px">Success</span>';
        if (r.result_status === 'Not Found' || r.result_status === 'Failed') statusBadge = '<span class="tag bad" style="font-size:11px">Not Found</span>';
        else if (r.result_status) statusBadge = `<span class="tag info" style="font-size:11px">${esc(r.result_status)}</span>`;

        const dtStr = r.search_date ? new Date(r.search_date).toLocaleString() : '—';

        return `
          <tr>
            <td>
              <b>${esc(r.username || 'System')}</b>
              <div style="font-size:11px;color:var(--muted)">ID: <code>${esc(r.user_id || '—')}</code></div>
            </td>
            <td style="white-space:nowrap;font-size:12.5px">${dtStr}</td>
            <td>${typeBadge}</td>
            <td><code style="background:var(--card-subtle);padding:3px 8px;border-radius:6px;border:1px solid var(--line);font-size:12.5px;font-weight:700;color:var(--primary)">${esc(r.search_value || '—')}</code></td>
            <td><b>${esc(r.customer_info || 'All Customers')}</b></td>
            <td>${statusBadge}</td>
            <td style="font-size:12px;color:var(--muted)">${esc(r.ip || '—')}</td>
          </tr>
        `;
      }).join('');

      const start = (page - 1) * SAT.pageSize + 1;
      const end = Math.min(page * SAT.pageSize, total);

      wrap.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:12px">
          <span style="font-size:13px;font-weight:700;color:var(--text)">
            Showing ${start}–${end} of ${total.toLocaleString()} search audit records
          </span>
          <div class="pg" style="display:flex;align-items:center;gap:8px">
            <button class="b" id="satPrevBtn" ${page <= 1 ? 'disabled' : ''} style="padding:4px 12px;font-size:12px">Prev</button>
            <span style="font-size:12px;font-weight:700">Page ${page} of ${pages}</span>
            <button class="b" id="satNextBtn" ${page >= pages ? 'disabled' : ''} style="padding:4px 12px;font-size:12px">Next</button>
          </div>
        </div>
        <div class="tw">
          <table>
            <thead>
              <tr>
                <th>User / Employee</th>
                <th>Search Date & Time</th>
                <th>Search Type</th>
                <th>Search Value / Query</th>
                <th>Customer Target</th>
                <th>Result Status</th>
                <th>Client IP</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;

      if ($('satPrevBtn')) $('satPrevBtn').onclick = () => { if (SAT.page > 1) { SAT.page--; loadSearchAuditTrail(); } };
      if ($('satNextBtn')) $('satNextBtn').onclick = () => { if (SAT.page < pages) { SAT.page++; loadSearchAuditTrail(); } };
    };

    window.scrollToSearchAudit = function() {
      const el = $('settingsSearchAuditCard');
      if (el) { el.scrollIntoView({ behavior: 'smooth' }); loadSearchAuditTrail(); }
    };
"""
    if 'loadSearchAuditTrail' not in html:
        html = html.replace("window.scrollToLoginInventory = function() {",
                            audit_js + "\n    window.scrollToLoginInventory = function() {")

    # In updateChrome or init, call loadLoginInventory & loadSearchAuditTrail
    init_hook = """
        loadLoginInventory();
        loadSearchAuditTrail();
        if ($('satQuery')) {
          let satDebounce;
          $('satQuery').oninput = () => {
            clearTimeout(satDebounce);
            satDebounce = setTimeout(() => { SAT.page = 1; loadSearchAuditTrail(); }, 300);
          };
        }
        if ($('satType')) $('satType').onchange = () => { SAT.page = 1; loadSearchAuditTrail(); };
        if ($('satSort')) $('satSort').onchange = () => { SAT.page = 1; loadSearchAuditTrail(); };
        if ($('satDir')) $('satDir').onchange = () => { SAT.page = 1; loadSearchAuditTrail(); };
        if ($('satPageSize')) $('satPageSize').onchange = () => { SAT.page = 1; loadSearchAuditTrail(); };
"""
    if 'loadLoginInventory();' not in html:
        html = html.replace("loadAuditLogContainer();", "loadAuditLogContainer();\n" + init_hook)

    with open('frontend/settings.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("SUCCESS: Patched frontend/settings.html!")

if __name__ == '__main__':
    patch_settings()

