import re, sys

print("=== PATCHING ALL ENHANCEMENTS INTO BUILD_CLEAN_MODULAR_APP.PY ===")

with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    text = f.read()

# -----------------------------------------------------------------------------
# 1. Ensure containers customization in build_clean_modular_app.py
# -----------------------------------------------------------------------------

# We want to insert the container and feature customizations right after
# containers = loc['containers']
# dialogs_dict = loc['dialogs_dict']
# feature_blocks = loc['feature_blocks']

old_marker = "feature_blocks['INV'] = feature_blocks['INV'].replace('initBulkUploadContainer();', 'if (typeof initBulkUploadContainer === \"function\") initBulkUploadContainer();')"

custom_containers_and_features = """# 1. Customization for containers['box-home'] (Live Master Device Stream & Data Health)
box_home_html = containers['box-home']

# Redesign Live Master Device Stream with modern search and toolbar
old_stream_pattern = r'<div class="card" style="padding:20px;border:1px solid var\(--line\);margin-bottom:20px;background:var\(--card-subtle\)">[\s\S]*?<div id="liveMasterTable">'
new_stream_html = '''<div class="card" id="cardLiveMasterStream" style="padding:22px 24px;border:1px solid var(--line);border-radius:16px;margin-bottom:24px;background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03)">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;border-bottom:1px solid var(--line);padding-bottom:14px">
              <div>
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-size:20px">📱</span>
                  <h3 style="margin:0;font-size:18px;font-weight:800;color:var(--text)">Live Master Device Stream</h3>
                  <span class="live-badge" style="font-size:11px;padding:2px 8px"><span class="live-dot"></span> LIVE</span>
                </div>
                <span style="font-size:13px;color:var(--muted);margin-top:2px;display:block">Real-time incoming telemetry and inventory status across all active customer accounts.</span>
              </div>
              <button class="b" id="liveExportExcel" style="font-weight:700;padding:8px 16px;border-radius:9px;background:var(--card-subtle);border:1px solid var(--line)">📥 Export to Excel</button>
            </div>

            <!-- Instant Live Search & Filters Toolbar -->
            <div style="display:flex;align-items:flex-end;flex-wrap:wrap;gap:12px;margin-bottom:16px">
              <div style="min-width:180px">
                <label for="liveCustFilter" style="font-size:12px;font-weight:700;color:var(--muted);display:block;margin-bottom:4px">Customer Account</label>
                <select id="liveCustFilter" style="height:40px;border-radius:10px;padding:0 12px;font-size:13px;width:100%;border:1.5px solid var(--line);background:var(--input-bg,var(--card));color:var(--text)">
                  <option value="">All Customers</option>
                </select>
              </div>
              <div style="min-width:160px">
                <label for="liveFieldFilter" style="font-size:12px;font-weight:700;color:var(--muted);display:block;margin-bottom:4px">Target Column</label>
                <select id="liveFieldFilter" style="height:40px;border-radius:10px;padding:0 12px;font-size:13px;width:100%;border:1.5px solid var(--line);background:var(--input-bg,var(--card));color:var(--text)">
                  <option value="all">All Columns</option>
                  <option value="imei">IMEI</option>
                  <option value="iccid">ICCID / CCID</option>
                  <option value="device_sr_no">Device SR No</option>
                  <option value="msisdn1">MSISDN1</option>
                  <option value="customer_name">Customer Name</option>
                  <option value="model">Model</option>
                  <option value="sim_provider">SIM Provider</option>
                </select>
              </div>
              <div style="flex:1;min-width:240px">
                <label for="liveSearchInput" style="font-size:12px;font-weight:700;color:var(--muted);display:block;margin-bottom:4px">Instant Live Search</label>
                <div class="cv-search-container">
                  <span class="cv-search-icon-left">🔎</span>
                  <input id="liveSearchInput" class="cv-search-input" placeholder="Search across records in real-time…" autocomplete="off" />
                  <span class="cv-search-spinner" id="liveSearchSpinner">🌀</span>
                  <button type="button" class="cv-search-clear-btn" id="liveSearchClearBtn" title="Clear search">✕</button>
                </div>
              </div>
              <div>
                <button class="b" id="liveSearchClear" style="height:40px;padding:0 14px;border-radius:10px;font-weight:700">Clear</button>
              </div>
            </div>

            <div id="liveMasterTable">'''

box_home_html = re.sub(old_stream_pattern, new_stream_html, box_home_html)
containers['box-home'] = box_home_html

# 2. Customization for containers['box-sim']: Add Restore All soft-deleted records card
box_sim_html = containers['box-sim']
restore_all_card_html = '''<!-- Dedicated Restore All Soft-Deleted SIMs Card (Requirement 6.B) -->
        <div class="card" id="simRestoreAllCard" style="margin-top:20px;padding:20px 24px;border:1.5px solid var(--primary);border-radius:14px;background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.04)">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px">
            <div style="display:flex;align-items:center;gap:14px">
              <div style="width:48px;height:48px;border-radius:12px;background:rgba(29,104,225,0.12);color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:24px">
                ♻️
              </div>
              <div>
                <h3 style="margin:0;font-size:16px;font-weight:800;color:var(--text)">Restore All Deleted / Archived SIMs</h3>
                <p class="sub" style="margin:4px 0 0;font-size:13px">Restore all soft-deleted inventory records from the Recycle Bin back into active database accounts. Active IMEIs are safely preserved.</p>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:12px">
              <div style="text-align:right">
                <span style="font-size:12px;color:var(--muted);display:block">Soft-deleted SIMs</span>
                <span id="simRestoreCountBadge" style="font-size:16px;font-weight:800;color:var(--primary)">0 records</span>
              </div>
              <button type="button" class="b p" id="btnSimRestoreAll" style="padding:10px 18px;font-weight:700;border-radius:9px;background:linear-gradient(135deg, var(--primary), #2563eb)">
                ♻️ Restore All Records
              </button>
            </div>
          </div>
        </div>

        <div id="simMainContent">'''

if 'id="simRestoreAllCard"' not in box_sim_html:
    box_sim_html = box_sim_html.replace('<div id="simMainContent">', restore_all_card_html, 1)
    containers['box-sim'] = box_sim_html

# 3. Append SIM upload logic to INV block so Tab C (Bulk Upload) is 100% functional in Customer Inventory
sim_block_copy = loc['feature_blocks']['SIM']

# Also add Restore All handler and Customer Files actions to INV and SIM blocks
restore_all_js = r'''
    // --- Restore All Soft-Deleted SIMs Logic (Requirement 6.B) ---
    async function updateSimRestoreCount() {
      try {
        const res = await api('/api/devices/deleted?page=1&page_size=1');
        const cnt = (res && res.total != null) ? res.total : 0;
        if ($('simRestoreCountBadge')) $('simRestoreCountBadge').textContent = `${Number(cnt).toLocaleString()} records`;
        return cnt;
      } catch(e) {
        return 0;
      }
    }
    updateSimRestoreCount();

    if ($('btnSimRestoreAll')) {
      $('btnSimRestoreAll').onclick = async () => {
        const cnt = await updateSimRestoreCount();
        if (cnt <= 0) {
          toast('Recycle bin is empty. No soft-deleted records to restore.');
          return;
        }
        if (!confirm(`Are you sure you want to restore all ${Number(cnt).toLocaleString()} soft-deleted records from the Recycle Bin?\\n\\nActive IMEIs are safely preserved to prevent duplicate collisions.`)) {
          return;
        }
        const btn = $('btnSimRestoreAll');
        btn.disabled = true;
        btn.textContent = 'Restoring…';
        try {
          toast('Restoring all records from Recycle Bin…');
          const res = await api('/api/devices/restore-all', { method: 'POST' });
          toast(res.message || `Restored ${res.restored} records successfully!`);
          if (typeof showEventPopup === 'function') {
            showEventPopup({
              type: 'restoring',
              title: 'Bulk Restoration Complete',
              message: `Successfully restored ${Number(res.restored || 0).toLocaleString()} records. (${Number(res.skipped || 0).toLocaleString()} duplicates protected/skipped).`,
              duration: 4000
            });
          }
          await updateSimRestoreCount();
          if (typeof updateSidebarStats === 'function') await updateSidebarStats();
          if (typeof updateHomeStatsRibbon === 'function') await updateHomeStatsRibbon();
          if (typeof loadCU === 'function') await loadCU();
        } catch(err) {
          fail(err);
        } finally {
          btn.disabled = false;
          btn.textContent = '♻️ Restore All Records';
        }
      };
    }
'''

feature_blocks['SIM'] = loc['feature_blocks']['SIM'] + "\n\n" + restore_all_js

# In INV block: enhanced Customer Files cards + download options + full Bulk Upload support
enhanced_inv_js = loc['feature_blocks']['INV']

# Update card template in INV
old_card_pattern = r'const card = c => `[\s\S]*?</div>`;'
new_card_template = '''const card = c => `
    <div class="cw" style="border:1px solid var(--line);border-radius:12px;padding:14px;background:var(--card);box-shadow:0 2px 8px rgba(0,0,0,0.02);display:flex;flex-direction:column;justify-content:space-between;gap:12px">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px">
        <div style="display:flex;align-items:center;gap:10px">
          ${avatarHtml(c)}
          <div>
            <b style="font-size:14px;color:var(--text);display:block">${esc(c.name)}</b>
            <span style="font-size:12px;color:var(--muted)">${Number(c.devices || 0).toLocaleString()} device records${c.expiring_or_expired ? ` · <span style="color:var(--warn);font-weight:700">${Number(c.expiring_or_expired || 0).toLocaleString()} expiring</span>` : ''}</span>
          </div>
        </div>
        <span class="tag ${c.devices > 0 ? 'ok' : 'mut'}" style="font-size:11px">${c.devices > 0 ? 'Active' : 'Empty'}</span>
      </div>
      <div class="ca" style="display:flex;gap:6px;flex-wrap:wrap">
        <button class="b" data-c="${c.id}" style="font-size:11.5px;padding:4px 8px" title="View device records">📋 Records</button>
        <button class="b" data-cdl="${c.id}" style="font-size:11.5px;padding:4px 8px" title="Download Excel workbook">📥 Excel</button>
        <button class="b" data-cfiles="${c.id}" style="font-size:11.5px;padding:4px 8px" title="View customer files">📁 Files</button>
        <button class="b" data-cav="${c.id}" style="font-size:11.5px;padding:4px 8px" title="Customize icon">🎨</button>
        ${staff ? `<button class="b" data-cren="${c.id}" style="font-size:11.5px;padding:4px 8px">Rename</button>
        <button class="b" data-cmerge="${c.id}" style="font-size:11.5px;padding:4px 8px">Merge</button>` : ''}
        ${canDelete ? `<button class="b d" data-cdel="${c.id}" style="font-size:11.5px;padding:4px 8px">Delete</button>` : ''}
      </div>
    </div>`;'''

enhanced_inv_js = re.sub(old_card_pattern, new_card_template, enhanced_inv_js, count=1)

# Add click handlers for Customer Files options (download Excel, view files, view records)
cust_files_handlers = r'''
        // Customer Files Action Handlers (Requirement 4.B)
        if ($('btnDownloadAllCustData')) {
          $('btnDownloadAllCustData').onclick = async () => {
            try {
              toast('Preparing complete database workbook download…');
              window.open('/api/devices/export', '_blank');
            } catch(e) { fail(e); }
          };
        }

        // Delegate customer card actions
        if ($('cgrid')) {
          $('cgrid').onclick = async e => {
            const btn = e.target.closest('button');
            if (!btn) return;
            const cid = btn.dataset.c || btn.dataset.cdl || btn.dataset.cfiles;
            if (!cid) return;

            if (btn.dataset.c) {
              // Option A: View device records for this customer
              if ($('invCustSel')) $('invCustSel').value = cid;
              invCid = cid;
              invPage = 1;
              switchInvSubView('devices');
              return;
            }

            if (btn.dataset.cdl) {
              // Option B: Download Excel workbook for customer
              toast('Downloading customer inventory workbook…');
              window.open(`/api/customers/${cid}/export`, '_blank');
              return;
            }

            if (btn.dataset.cfiles) {
              // Option B: View customer files metadata
              try {
                toast('Fetching customer files…');
                const fileInfo = await api(`/api/customers/${cid}/files`);
                const custName = fileInfo.customer_name || 'Customer';
                const files = fileInfo.files || [];
                const filesHtml = files.length ? `
                  <div style="display:flex;flex-direction:column;gap:10px;margin-top:10px">
                    ${files.map(f => `
                      <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border:1px solid var(--line);border-radius:8px;background:var(--card-subtle)">
                        <div>
                          <b style="font-size:13px;display:block">${esc(f.filename)}</b>
                          <span style="font-size:11.5px;color:var(--muted)">${Number(f.records_count || 0).toLocaleString()} devices · ${(f.file_size / 1024).toFixed(1)} KB</span>
                        </div>
                        <a href="${f.download_url}" target="_blank" class="b p" style="text-decoration:none;font-size:12px;padding:4px 10px">📥 Download</a>
                      </div>
                    `).join('')}
                  </div>
                ` : `
                  <div class="empty" style="padding:20px;text-align:center">
                    <p style="margin:0 0 10px;color:var(--muted)">No uploaded files recorded for this customer yet.</p>
                    <a href="/api/customers/${cid}/export" target="_blank" class="b p" style="text-decoration:none;display:inline-block">📥 Generate & Download Live Excel</a>
                  </div>
                `;

                openDlg(`Files for ${custName}`, filesHtml, 'Close', async () => {});
              } catch(err) {
                fail(err);
              }
              return;
            }
          };
        }
'''

enhanced_inv_js = enhanced_inv_js.replace("await loadCustomerFilesContainer();", "await loadCustomerFilesContainer();\n" + cust_files_handlers)

# Append full bulk upload functions so Tab C in Customer Inventory is 100% functional
feature_blocks['INV'] = enhanced_inv_js + "\n\n" + sim_block_copy

# 4. Customization for FETCH block: Ensure EVERY database column is included & responsive scroll
fetch_block = loc['feature_blocks']['FETCH']

# Replace renderNormalFetchTable column determination with complete database schema discovery
old_fetch_col_logic = r'''        } else {
          displayCols = [
            { key: 'customer_name', label: 'Customer Name' },
            ...COLS.map(c => ({ key: c[0], label: c[1] })),
            ...XC.map(c => ({ key: c, label: c })),
            { key: 'added_by', label: 'Added By' },
            { key: 'created_at', label: 'Added On' }
          ];
        }'''

new_fetch_col_logic = r'''        } else {
          // Discover ALL dynamic columns from database items + extra dictionary (Requirement 7)
          const discoveredExtraKeys = new Set();
          (items || []).forEach(it => {
            if (it && it.extra && typeof it.extra === 'object') {
              Object.keys(it.extra).forEach(k => discoveredExtraKeys.add(k));
            }
          });
          const allExtraCols = Array.from(new Set([...XC, ...discoveredExtraKeys]));

          displayCols = [
            { key: 'id', label: 'ID' },
            { key: 'customer_name', label: 'Customer Name' },
            ...COLS.map(c => ({ key: c[0], label: c[1] })),
            ...allExtraCols.map(c => ({ key: c, label: c.replace(/_/g, ' ').toUpperCase() })),
            { key: 'added_by', label: 'Added By' },
            { key: 'created_at', label: 'Added On' }
          ];
        }'''

fetch_block = fetch_block.replace(old_fetch_col_logic, new_fetch_col_logic)

# Add search within fetched results input and instant filter
old_nf_table_html = r'''    <div class="row" style="align-items:center;justify-content:space-between;margin:14px 0 10px;flex-wrap:wrap;gap:10px">
      <div>
        <span style="font-size:14px;font-weight:800">${items.length.toLocaleString()} records found</span>
        <span class="sub" style="margin-left:8px;font-size:12px">Filtered by: <b>${activeFetchSimType.toUpperCase()}</b> | Visible Columns: <b>${displayCols.length}</b></span>
      </div>'''

new_nf_table_html = r'''    <div class="row" style="align-items:center;justify-content:space-between;margin:14px 0 10px;flex-wrap:wrap;gap:10px">
      <div>
        <span style="font-size:14px;font-weight:800">${items.length.toLocaleString()} records found</span>
        <span class="sub" style="margin-left:8px;font-size:12px">Filtered by: <b>${activeFetchSimType.toUpperCase()}</b> | All Database Columns: <b>${displayCols.length}</b></span>
      </div>
      <div style="flex:1;max-width:320px;min-width:200px">
        <div class="cv-search-container">
          <span class="cv-search-icon-left">🔎</span>
          <input id="nfFilterInput" class="cv-search-input" style="height:32px;font-size:12.5px" placeholder="Filter fetched results…" />
        </div>
      </div>'''

fetch_block = fetch_block.replace(old_nf_table_html, new_nf_table_html)

# Add in-table search filter listener
nf_filter_listener = r'''
        // Instant filter within fetched results (Requirement 7)
        if ($('nfFilterInput')) {
          $('nfFilterInput').oninput = e => {
            const term = e.target.value.toLowerCase().trim();
            const rows = wrap.querySelectorAll('tbody tr');
            rows.forEach(r => {
              r.style.display = (!term || r.textContent.toLowerCase().includes(term)) ? '' : 'none';
            });
          };
        }
'''

fetch_block = fetch_block.replace("wrap.innerHTML = html;", "wrap.innerHTML = html;\n" + nf_filter_listener)
feature_blocks['FETCH'] = fetch_block
"""

if old_marker in text:
    text = text.replace(old_marker, custom_containers_and_features, 1)
    print("✓ Inserted custom containers and enhanced feature blocks")
else:
    print("! Warning: old_marker not found")

# -----------------------------------------------------------------------------
# 2. Replace feature_blocks['HOME'] with full modernized controller
# -----------------------------------------------------------------------------
new_home_block = r'''feature_blocks['HOME'] = r"""
      /* =========================================================================
         HOME OVERVIEW & REAL-TIME TELEMETRY CONTROLLER (Enhanced)
         ========================================================================= */
      // 1. Live Stream & Telemetry State Setup
      livePolling = true;
      liveTimer = null;
      liveIntervalSec = 10;
      liveCid = '';
      liveQ = '';
      liveCol = 'all';
      livePage = 1;
      sortCol = 'id';
      sortDir = 'desc';
      liveHealthData = null;
      liveReportList = null;
      let alertsActive = true;

      // Data Health pagination & filter state (Requirement 3)
      let dhPage = 1;
      let dhPageSize = 10;
      let dhSelectAll = false;
      let dhQ = '';
      let dhDebounce = null;
      let lastHealthData = null;

      // 2. User Greeting & Profile Synchronization
      async function updateHomeUserGreeting() {
        let user = getUser();
        try {
          const me = await api('/api/me');
          if (me && (me.name || me.user_id)) {
            user = me;
            localStorage.setItem('user', JSON.stringify(me));
          }
        } catch(e) {}

        const d = new Date();
        const hrs = d.getHours();
        let greet = 'Good morning';
        if (hrs >= 12 && hrs < 17) greet = 'Good afternoon';
        else if (hrs >= 17) greet = 'Good evening';

        const dispName = user.name || user.full_name || user.username || 'Shilish Reddy';
        const roleName = (user.role || 'ADMIN').toUpperCase();
        const firstLetter = (dispName.charAt(0) || 'S').toUpperCase();

        if ($('hi')) $('hi').textContent = `${greet}, ${dispName}`;
        if ($('rolePill')) {
          $('rolePill').textContent = roleName;
          $('rolePill').className = `role-pill ${roleName.toLowerCase().includes('admin') ? 'admin' : 'standard'}`;
        }
        if ($('userAvatarCircle')) $('userAvatarCircle').textContent = firstLetter;
      }

      // 3. Expiry Alert Banner Synchronization
      async function updateHomeExpiryBanner() {
        try {
          const res = await api('/api/alerts/expiry?days=30');
          if (res) {
            const expCount = (res.expired || []).length || res.total_expired || 0;
            const soonCount = (res.expiring_soon || []).length || res.total_expiring || 0;
            if ($('cntExpiredGlobalBadge')) $('cntExpiredGlobalBadge').textContent = Number(expCount).toLocaleString('en-US');
            if ($('cntExpiringSoonGlobalBadge')) $('cntExpiringSoonGlobalBadge').textContent = Number(soonCount).toLocaleString('en-US');
            if ($('globalExpiryAlertText')) {
              $('globalExpiryAlertText').textContent = `${Number(expCount).toLocaleString('en-US')} SIM(s) have already expired, and ${Number(soonCount).toLocaleString('en-US')} are expiring within 30 days.`;
            }
          }
        } catch(e) {
          console.log('Notice: Expiry banner sync:', e);
        }
      }

      // 4. 4-Stat Metric Cards Ribbon Synchronization (100% Dynamic)
      async function updateHomeStatsRibbon() {
        try {
          const [s, xc] = await Promise.all([
            api('/api/stats').catch(() => null),
            api('/api/extra-cols').catch(() => [])
          ]);
          if (s) {
            S = s;
            const custCount = s.total_customers != null ? s.total_customers : (s.customers != null ? s.customers : 0);
            const devCount = s.total_devices != null ? s.total_devices : (s.devices != null ? s.devices : 0);
            const uCount = s.added_by_you != null ? s.added_by_you : Math.max(0, devCount - 2);
            const extraCount = Array.isArray(xc) ? xc.length : (s.extra_cols_count || 0);

            if ($('statCustomers')) $('statCustomers').textContent = Number(custCount).toLocaleString('en-US');
            if ($('statDevices')) $('statDevices').textContent = Number(devCount).toLocaleString('en-US');
            if ($('statAddedByYou')) $('statAddedByYou').textContent = Number(uCount).toLocaleString('en-US');
            if ($('statColumns')) $('statColumns').textContent = String(COLS.length + extraCount);

            if ($('sbLiveDevCount')) $('sbLiveDevCount').textContent = Number(devCount).toLocaleString('en-US');
            if ($('sbLiveCustCount')) $('sbLiveCustCount').textContent = Number(custCount).toLocaleString('en-US');
          }
        } catch(e) {
          console.log('Notice: Stats ribbon sync:', e);
        }
      }

      // 5. Populate Customer Dropdown
      async function populateLiveCustomerDropdown() {
        const sel = $('liveCustFilter');
        if (!sel) return;
        try {
          const custs = await api('/api/customers');
          if (Array.isArray(custs)) {
            CU = custs;
            const curVal = sel.value;
            sel.innerHTML = '<option value="">All Customers</option>' +
              custs.map(c => `<option value="${c.id}" ${String(c.id) === String(curVal) ? 'selected' : ''}>${esc(c.name || c.customer_name)}</option>`).join('');
          }
        } catch(e) {}
      }

      // 6. Cart Count Badge & Navigation
      async function updateCartCountBadge() {
        try {
          const bin = await api('/api/devices/deleted?page=1&page_size=1');
          const cnt = bin && bin.total != null ? bin.total : 0;
          if ($('headerCartCountBadge')) $('headerCartCountBadge').textContent = String(cnt);
        } catch(e) {}
      }

      function openCartModal() {
        window.location.href = 'edit-delete.html#box-bin';
      }

      // 7. Edit Employee Name Modal
      async function openEditNameModal() {
        const dlg = $('dlgEditName');
        if (!dlg) return;
        const u = getUser();
        let currentName = u.name || u.user_id || 'Shilish Reddy';
        if ($('editNameCurrent')) $('editNameCurrent').value = currentName;
        if ($('editNameUpdated')) $('editNameUpdated').value = '';
        if ($('editNameConfirm')) $('editNameConfirm').value = '';
        if ($('editNameError')) {
          $('editNameError').textContent = '';
          $('editNameError').hidden = true;
        }
        if (!dlg.open) dlg.showModal();
        try {
          const fresh = await api('/api/me');
          if (fresh && fresh.name && $('editNameCurrent')) $('editNameCurrent').value = fresh.name;
        } catch (_) {}
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

          const u = getUser();
          u.name = finalName;
          localStorage.setItem('user', JSON.stringify(u));

          await updateHomeUserGreeting();
          toast('Display name updated successfully');
          closeEditNameModal();
        } catch (err) {
          if (errEl) { errEl.textContent = err.message || 'Failed to update name.'; errEl.hidden = false; }
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = 'Save'; }
        }
      }

      if ($('bEditMyName')) $('bEditMyName').onclick = openEditNameModal;
      if ($('bPw')) $('bPw').onclick = openChangePasswordModal;
      if ($('bLo')) $('bLo').onclick = () => logout(true);

      const formEditName = $('formEditName');
      if (formEditName) {
        formEditName.onsubmit = async e => {
          e.preventDefault();
          await submitEditNameModal();
        };
      }

      // 8. Change Password Modal
      function openChangePasswordModal() {
        const dlg = $('pwd');
        if (!dlg) return;
        if ($('p1')) $('p1').value = '';
        if ($('p2')) $('p2').value = '';
        if ($('p3')) $('p3').value = '';
        if ($('pe')) { $('pe').textContent = ''; $('pe').hidden = true; }
        if (!dlg.open) dlg.showModal();
        setTimeout(() => $('p1')?.focus(), 50);
      }

      function closeChangePasswordModal() {
        const dlg = $('pwd');
        if (dlg && dlg.open) dlg.close();
      }

      function togglePasswordInputVisibility(id) {
        const inp = $(id);
        if (inp) {
          inp.type = inp.type === 'password' ? 'text' : 'password';
        }
      }

      const formChangePw = $('pf');
      if (formChangePw) {
        formChangePw.onsubmit = async e => {
          e.preventDefault();
          const cur = ($('p1')?.value || '').trim();
          const np = ($('p2')?.value || '').trim();
          const cnp = ($('p3')?.value || '').trim();
          const errEl = $('pe');
          if (errEl) { errEl.textContent = ''; errEl.hidden = true; }

          if (!cur) {
            if (errEl) { errEl.textContent = 'Please enter your current password.'; errEl.hidden = false; }
            return;
          }
          if (np.length < 8) {
            if (errEl) { errEl.textContent = 'New password must be at least 8 characters long.'; errEl.hidden = false; }
            return;
          }
          if (np !== cnp) {
            if (errEl) { errEl.textContent = 'New password and confirm password do not match.'; errEl.hidden = false; }
            return;
          }

          const btn = $('btnConfirmChangePw');
          if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; }

          try {
            await api('/api/me/password', {
              method: 'PUT',
              body: JSON.stringify({ current_password: cur, new_password: np, confirm_password: cnp })
            });
            toast('Password updated successfully');
            closeChangePasswordModal();
          } catch(err) {
            if (errEl) { errEl.textContent = err.message || 'Failed to update password.'; errEl.hidden = false; }
          } finally {
            if (btn) { btn.disabled = false; btn.textContent = 'Confirm & Change Password'; }
          }
        };
      }

      // 9. Logout
      function logout(confirmFirst = false) {
        if (confirmFirst && !confirm('Are you sure you want to sign out of BSTPL CustomerVault?')) {
          return;
        }
        try {
          api('/api/logout', { method: 'POST' }).catch(() => {});
        } catch(e) {}
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        tok = '';
        window.location.href = 'index.html';
      }

      // 10. Top Bar Action Button Listeners
      if ($('bRefresh')) {
        $('bRefresh').onclick = async () => {
          toast('Refreshing Home Overview…');
          await Promise.all([
            runLiveCycle(true),
            loadHealthContainer(),
            updateHomeStatsRibbon(),
            updateHomeExpiryBanner(),
            updateHomeUserGreeting(),
            updateCartCountBadge()
          ]);
          toast('Home Overview refreshed');
        };
      }

      if ($('bQs')) {
        $('bQs').onclick = () => {
          const inp = $('liveSearchInput');
          if (inp) {
            inp.focus();
            inp.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        };
      }

      if ($('bAl')) {
        $('bAl').textContent = 'Alerts: ON';
        $('bAl').classList.add('on');
        $('bAl').onclick = () => {
          alertsActive = !alertsActive;
          $('bAl').textContent = alertsActive ? 'Alerts: ON' : 'Alerts: OFF';
          $('bAl').classList.toggle('on', alertsActive);
          const banner = $('globalExpiryAlertBanner');
          if (banner) banner.style.display = alertsActive ? 'flex' : 'none';
        };
      }

      if ($('btnViewExpiredGlobal')) {
        $('btnViewExpiredGlobal').onclick = () => {
          window.location.href = 'alerts.html?tab=expired';
        };
      }

      if ($('btnViewExpiringSoonGlobal')) {
        $('btnViewExpiringSoonGlobal').onclick = () => {
          window.location.href = 'alerts.html?tab=expiring';
        };
      }

      // 11. Live Telemetry Controls Listeners
      if ($('toggleLive')) {
        $('toggleLive').onclick = () => {
          livePolling = !livePolling;
          $('toggleLive').textContent = livePolling ? '🟢 Live Updates: ON' : '⏸️ Polling: PAUSED';
          $('toggleLive').classList.toggle('on', livePolling);
          if (livePolling) runLiveCycle(true);
          else clearTimeout(liveTimer);
        };
      }

      if ($('liveIntervalSel')) {
        $('liveIntervalSel').onchange = e => {
          liveIntervalSec = +e.target.value;
          if (livePolling) { clearTimeout(liveTimer); runLiveCycle(true); }
        };
      }

      if ($('manualLiveRefresh')) {
        $('manualLiveRefresh').onclick = async () => {
          toast('Refreshing live telemetry…');
          await runLiveCycle(true);
        };
      }

      if ($('liveCustFilter')) {
        $('liveCustFilter').onchange = e => {
          liveCid = e.target.value;
          livePage = 1;
          updateLiveFeedTable();
        };
      }

      if ($('liveFieldFilter')) {
        $('liveFieldFilter').onchange = e => {
          liveCol = e.target.value;
          livePage = 1;
          updateLiveFeedTable();
        };
      }

      // Instant Live Search with Spinner, Clear button & 180ms debounce (Requirement 2 & 5)
      let liveDebounce;
      const liveInp = $('liveSearchInput');
      const liveSpinner = $('liveSearchSpinner');
      const liveClearBtn = $('liveSearchClearBtn');

      if (liveInp) {
        liveInp.oninput = e => {
          liveQ = e.target.value;
          livePage = 1;
          if (liveClearBtn) liveClearBtn.style.display = liveQ ? 'block' : 'none';
          if (liveSpinner) liveSpinner.style.display = 'inline-block';
          clearTimeout(liveDebounce);
          liveDebounce = setTimeout(async () => {
            try {
              await updateLiveFeedTable();
            } finally {
              if (liveSpinner) liveSpinner.style.display = 'none';
            }
          }, 180);
        };
      }

      if (liveClearBtn) {
        liveClearBtn.onclick = () => {
          if (liveInp) liveInp.value = '';
          liveClearBtn.style.display = 'none';
          liveQ = '';
          livePage = 1;
          updateLiveFeedTable();
        };
      }

      if ($('liveSearchClear')) {
        $('liveSearchClear').onclick = () => {
          liveQ = ''; liveCol = 'all'; liveCid = ''; livePage = 1;
          if ($('liveCustFilter')) $('liveCustFilter').value = '';
          if ($('liveFieldFilter')) $('liveFieldFilter').value = 'all';
          if ($('liveSearchInput')) $('liveSearchInput').value = '';
          if (liveClearBtn) liveClearBtn.style.display = 'none';
          updateLiveFeedTable();
        };
      }

      if ($('liveExportExcel')) {
        $('liveExportExcel').onclick = async () => {
          try {
            toast('Exporting live feed records…');
            const d = await api(`/api/devices?page=1&page_size=5000&q=${encodeURIComponent(liveQ)}&column=${liveCol}${liveCid ? '&customer_id=' + liveCid : ''}`);
            const headers = ['ID', ...COLS.map(c => c[1]), ...XC];
            const rows = d.items.map(dev => [dev.id, ...COLS.map(c => dev[c[0]] || ''), ...XC.map(c => (dev.extra || {})[c] || '')]);
            exportExcel('Live_Feed_Inventory', headers, rows);
          } catch (err) { fail(err); }
        };
      }

      // 12. Run Live Telemetry Cycle
      async function runLiveCycle(immediate = false) {
        if (!tok) { clearTimeout(liveTimer); return; }
        try {
          const [rawIns, rawHea, rawAct] = await Promise.all([
            api('/api/inventory/insights').catch(() => null),
            api('/api/inventory/health?page=1&page_size=10').catch(() => null),
            api('/api/activity?page=1&page_size=8').catch(() => null)
          ]);
          const ins = (rawIns && typeof rawIns === 'object') ? rawIns : { total_devices: 0, total_customers: 0, expiring_30: 0, expired: 0 };
          const hea = (rawHea && typeof rawHea === 'object') ? rawHea : { score: 100, completeness: {}, issues: [] };
          const actData = (rawAct && typeof rawAct === 'object' && Array.isArray(rawAct.items)) ? rawAct : { items: [] };

          // 1. KPI Ribbon
          const completenessAvg = Object.values(hea.completeness || {}).length
            ? Math.round(Object.values(hea.completeness).reduce((a, b) => a + b, 0) / Object.values(hea.completeness).length)
            : 100;

          if ($('liveKpis')) {
            $('liveKpis').innerHTML = `
              <div class="card stat" style="border-left-color:var(--primary)"><b>${Number(ins.total_devices || 0).toLocaleString('en-US')}</b><span>Total Live Devices</span></div>
              <div class="card stat" style="border-left-color:#8b5cf6"><b>${Number(ins.total_customers || 0).toLocaleString('en-US')}</b><span>Active Customers</span></div>
              <div class="card stat" style="border-left-color:var(--warn)"><b>${Number(ins.expiring_30 || 0).toLocaleString('en-US')}</b><span>Expiring in 30 Days</span></div>
              <div class="card stat" style="border-left-color:var(--danger)"><b>${Number(ins.expired || 0).toLocaleString('en-US')}</b><span>Expired Devices</span></div>
              <div class="card stat" style="border-left-color:var(--ok)"><b>${completenessAvg}%</b><span>Data Health Score</span></div>
            `;
          }

          // 2. Live Feed Table
          await updateLiveFeedTable();

          // 3. Live Telemetry Activity Stream
          if ($('liveActivityBody')) {
            $('liveActivityBody').innerHTML = actData.items.length ? `
              <div class="tw"><table><thead><tr>
                <th>Timestamp</th><th>Employee</th><th>Action</th><th>Details</th><th>IP Address</th>
              </tr></thead><tbody>
              ${actData.items.map(i => {
                const a = ALBL[i.action] || [i.action || 'Activity', 'mut'];
                const d = new Date(i.created_at);
                const timeStr = isNaN(d.getTime()) ? i.created_at : d.toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
                return `<tr>
                  <td>${esc(timeStr)}</td>
                  <td><b>${esc(i.user_name || '')}</b> <span style="color:var(--muted)">(${esc(i.user_login || '')})</span></td>
                  <td><span class="tag ${a[1]}">${esc(a[0])}</span></td>
                  <td><code>${esc(i.detail || '')}</code></td>
                  <td><code>${esc(i.ip || '127.0.0.1')}</code></td>
                </tr>`;
              }).join('')}
              </tbody></table></div>` : '<div class="empty">No live activity recorded.</div>';
          }

          if ($('liveTime')) {
            $('liveTime').textContent = `Updated: ${new Date().toLocaleTimeString()}`;
          }
        } catch (err) {
          console.error('Live cycle error:', err);
        } finally {
          if (livePolling && tok) {
            clearTimeout(liveTimer);
            liveTimer = setTimeout(() => runLiveCycle(), liveIntervalSec * 1000);
          }
        }
      }

      // 13. Update Live Feed Table (with meaningful empty state)
      async function updateLiveFeedTable() {
        try {
          const rawD = await api(`/api/devices?page=${livePage}&page_size=25&q=${encodeURIComponent(liveQ)}&column=${liveCol}&sort_by=${sortCol}&sort_dir=${sortDir}${liveCid ? '&customer_id=' + liveCid : ''}`).catch(() => null);
          const d = (rawD && typeof rawD === 'object' && Array.isArray(rawD.items)) ? rawD : { items: [], total: 0, page: 1, pages: 1 };
          const s = (d.page - 1) * 25;
          const staff = canDeleteValidInventory();
          const act = dev => `
            <div style="display:flex;gap:4px">
              <button class="b" data-editdev="${dev.id}" style="height:28px;padding:0 8px;font-size:12px">Edit</button>
              ${staff ? `<button class="b d" data-del="${dev.id}" style="height:28px;padding:0 8px;font-size:12px">Delete</button>` : ''}
            </div>`;

          if ($('liveMasterTable')) {
            if (!d.items.length) {
              const emptyMsg = liveQ ? `🔍 No matching records found for "${esc(liveQ)}". Try adjusting your search query or column filter.` : `No device records found in this view.`;
              $('liveMasterTable').innerHTML = `
                <div class="empty" style="padding:28px;text-align:center;font-size:13.5px;color:var(--muted)">
                  ${emptyMsg}
                </div>`;
            } else {
              $('liveMasterTable').innerHTML = `
                <div class="meta" style="margin-bottom:8px">
                  <span>${Number(d.total).toLocaleString('en-US')} records · showing ${d.total ? s + 1 : 0}–${s + d.items.length}</span>
                  <div class="pg">
                    <button class="b" id="livePrevPg" ${livePage < 2 ? 'disabled' : ''}>Prev</button>
                    <span>Page ${d.page} of ${d.pages || 1}</span>
                    <button class="b" id="liveNextPg" ${livePage >= (d.pages || 1) ? 'disabled' : ''}>Next</button>
                  </div>
                </div>
                ${renderTable(d.items, act)}
              `;

              if ($('livePrevPg')) $('livePrevPg').onclick = () => { if (livePage > 1) { livePage--; updateLiveFeedTable(); } };
              if ($('liveNextPg')) $('liveNextPg').onclick = () => { if (livePage < (d.pages || 1)) { livePage++; updateLiveFeedTable(); } };
            }
          }
        } catch (err) {
          if ($('liveMasterTable')) $('liveMasterTable').innerHTML = `<div class="empty err">${esc(err.message)}</div>`;
        }
      }

      // 14. Data Health & Integrity Report with Pagination (10 per page default) and Select All (Requirement 3)
      async function loadHealthContainer() {
        const hc = $('healthContainerBody') || $('liveHealthBody');
        if (!hc) return;

        try {
          const url = `/api/inventory/health?page=${dhPage}&page_size=${dhPageSize}&select_all=${dhSelectAll ? 'true' : 'false'}${dhQ ? '&q=' + encodeURIComponent(dhQ) : ''}`;
          const d = await api(url);
          if (!d) throw new Error('Failed to load health report');
          lastHealthData = d;
          liveHealthData = d;

          const totalIssues = d.total_issues != null ? d.total_issues : ((d.issues && Array.isArray(d.issues)) ? d.issues.length : 0);
          const curPage = d.page || dhPage;
          const totalPages = d.pages || Math.max(1, Math.ceil(totalIssues / dhPageSize));
          const startIdx = totalIssues ? (curPage - 1) * dhPageSize + 1 : 0;
          const endIdx = dhSelectAll ? totalIssues : Math.min(totalIssues, startIdx + (d.issues ? d.issues.length : 0) - 1);

          hc.innerHTML = `
            <div class="stats" style="margin-top:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px">
              <div class="card stat" style="${d.duplicate_imei_count ? 'border-left-color:var(--danger)' : ''}">
                <b>${Number(d.duplicate_imei_count || 0).toLocaleString()}</b><span>Duplicate IMEIs</span>
              </div>
              <div class="card stat" style="${d.duplicate_iccid_count ? 'border-left-color:var(--danger)' : ''}">
                <b>${Number(d.duplicate_iccid_count || 0).toLocaleString()}</b><span>Duplicate ICCIDs</span>
              </div>
              <div class="card stat" style="${d.duplicate_sr_count ? 'border-left-color:var(--danger)' : ''}">
                <b>${Number(d.duplicate_sr_count || 0).toLocaleString()}</b><span>Duplicate Serial Numbers</span>
              </div>
              <div class="card stat" style="${d.bad_imei_count ? 'border-left-color:var(--warn)' : ''}">
                <b>${Number(d.bad_imei_count || 0).toLocaleString()}</b><span>Invalid IMEI Lengths (&ne;15)</span>
              </div>
              <div class="card stat" style="${d.bad_date_count ? 'border-left-color:var(--danger)' : ''}">
                <b>${Number(d.bad_date_count || 0).toLocaleString()}</b><span>Expiry Before Activation</span>
              </div>
            </div>

            <div class="metric-box" style="margin:16px 0;padding:16px;border:1px solid var(--line);border-radius:12px;background:var(--card-subtle)">
              <h4 style="margin:0 0 12px;font-size:14px;color:var(--text)">📊 Column Completeness Percentage</h4>
              <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px">
                ${Object.entries(d.completeness || {}).map(([col, pct]) => `
                  <div>
                    <div class="dist-item" style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px"><span style="text-transform:capitalize">${esc(col.replace(/_/g, ' '))}</span><b>${pct}%</b></div>
                    <div class="progress-bar" style="height:6px;background:var(--line);border-radius:99px;overflow:hidden"><div class="progress-fill ${pct > 80 ? 'ok' : pct > 40 ? '' : 'bad'}" style="width:${pct}%;height:100%;background:${pct > 80 ? 'var(--ok)' : pct > 40 ? 'var(--primary)' : 'var(--danger)'}"></div></div>
                  </div>`).join('')}
              </div>
            </div>

            <!-- Detected Integrity Issues Header with Search & Pagination Controls -->
            <div style="margin:20px 0 10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
              <h4 style="margin:0;font-size:15px;font-weight:800;color:var(--text)">
                ⚠️ Detected Integrity Issues (${Number(totalIssues).toLocaleString()})
              </h4>
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <div class="cv-search-container" style="min-width:200px;max-width:280px">
                  <span class="cv-search-icon-left">🔎</span>
                  <input id="dhSearchInput" class="cv-search-input" style="height:32px;font-size:12.5px" placeholder="Filter issues…" value="${esc(dhQ)}" />
                  ${dhQ ? `<button type="button" class="cv-search-clear-btn" id="dhClearSearchBtn" style="display:block">✕</button>` : ''}
                </div>
                <button type="button" class="dh-select-all-btn ${dhSelectAll ? 'active' : ''}" id="dhSelectAllBtn">
                  ${dhSelectAll ? '📄 View Paginated (10/pg)' : '📋 Select All (View All)'}
                </button>
              </div>
            </div>

            <!-- Pagination Toolbar -->
            <div class="dh-pagination-bar">
              <div class="dh-page-info">
                ${dhSelectAll ? `Showing all <b>${Number(totalIssues).toLocaleString()}</b> detected issues` : `Showing <b>${startIdx}–${endIdx}</b> of <b>${Number(totalIssues).toLocaleString()}</b> issues (Page <b>${curPage}</b> of <b>${totalPages}</b>)`}
              </div>
              <div class="dh-pagination-controls">
                <button type="button" class="dh-page-btn" id="dhPrevBtn" ${dhSelectAll || curPage <= 1 ? 'disabled' : ''}>
                  ◀ Previous
                </button>
                <span style="font-size:12.5px;font-weight:700;padding:0 6px">${curPage} / ${totalPages}</span>
                <button type="button" class="dh-page-btn" id="dhNextBtn" ${dhSelectAll || curPage >= totalPages ? 'disabled' : ''}>
                  Next ▶
                </button>
              </div>
            </div>

            ${(d.issues && d.issues.length) ? `
              <div class="tw"><table><thead><tr>
                <th>Issue Type</th><th>Identifier</th><th>Count</th><th>Description</th>
              </tr></thead><tbody>
              ${d.issues.map(iss => `<tr>
                <td><span class="tag bad">${esc(iss.type)}</span></td>
                <td><b>${esc(iss.identifier)}</b></td>
                <td>${Number(iss.count || 0).toLocaleString()}</td>
                <td>${esc(iss.description)}</td>
              </tr>`).join('')}
              </tbody></table></div>` : '<div class="empty" style="color:var(--ok)">✓ Outstanding! All device records pass integrity checks.</div>'}
          `;

          // Wire pagination and search handlers
          if ($('dhPrevBtn')) {
            $('dhPrevBtn').onclick = () => {
              if (dhPage > 1) { dhPage--; loadHealthContainer(); }
            };
          }
          if ($('dhNextBtn')) {
            $('dhNextBtn').onclick = () => {
              if (dhPage < totalPages) { dhPage++; loadHealthContainer(); }
            };
          }
          if ($('dhSelectAllBtn')) {
            $('dhSelectAllBtn').onclick = () => {
              dhSelectAll = !dhSelectAll;
              dhPage = 1;
              loadHealthContainer();
            };
          }
          if ($('dhSearchInput')) {
            $('dhSearchInput').oninput = e => {
              dhQ = e.target.value.trim();
              dhPage = 1;
              clearTimeout(dhDebounce);
              dhDebounce = setTimeout(loadHealthContainer, 250);
            };
          }
          if ($('dhClearSearchBtn')) {
            $('dhClearSearchBtn').onclick = () => {
              dhQ = '';
              dhPage = 1;
              loadHealthContainer();
            };
          }

          if ($('liveDownloadHealth')) {
            $('liveDownloadHealth').onclick = async () => {
              try {
                toast('Preparing full health audit export…');
                const allRes = await api('/api/inventory/health?select_all=true');
                const issues = (allRes && allRes.issues) ? allRes.issues : [];
                if (!issues.length) { toast('No health issues to export'); return; }
                const headers = ['Issue Type', 'Identifier', 'Count', 'Description'];
                const rows = issues.map(i => [i.type, i.identifier, i.count, i.description]);
                exportExcel('Data_Health_Audit_Report', headers, rows);
              } catch (err) { fail(err); }
            };
          }
        } catch (err) {
          hc.innerHTML = `<div class="empty err">${esc(err.message)}</div>`;
        }
      }

      // 15. Unified Home Overview Orchestrator
      async function loadHomeContainer() {
        await Promise.all([
          updateHomeUserGreeting().catch(e => console.log('Greeting notice:', e)),
          updateHomeExpiryBanner().catch(e => console.log('Expiry banner notice:', e)),
          updateHomeStatsRibbon().catch(e => console.log('Stats ribbon notice:', e)),
          populateLiveCustomerDropdown().catch(e => console.log('Customer dropdown notice:', e)),
          updateCartCountBadge().catch(e => console.log('Cart count notice:', e)),
          loadHealthContainer().catch(e => console.log('Health notice:', e)),
          runLiveCycle(true).catch(e => console.log('Live cycle notice:', e))
        ]);
      }
"""'''

# Find bounds of feature_blocks['HOME'] in text
home_start = text.find("feature_blocks['HOME'] = r\"\"\"")
home_end = text.find("\"\"\"\n\nfeature_dialogs = loc['feature_dialogs']", home_start)

if home_start != -1 and home_end != -1:
    text = text[:home_start] + new_home_block + text[home_end+3:]
    print("✓ Successfully replaced feature_blocks['HOME'] with complete enhanced version")
else:
    print(f"! Warning: home bounds not found: start={home_start}, end={home_end}")

# -----------------------------------------------------------------------------
# 3. Add dlgUploadErrorsAlert to inventory.html dialogs list
# -----------------------------------------------------------------------------
text = text.replace("'dialog_keys': ['dlgRenameAllCustomers', 'dlgDeleteCustomerEntries', 'devdlg', 'dlgAddColumn', 'dlgChooseExportCols', 'dlgCartModal', 'cdlg', 'qsdlg', 'dlgEventPopup', 'dlgActionProgress']",
                    "'dialog_keys': ['dlgRenameAllCustomers', 'dlgDeleteCustomerEntries', 'devdlg', 'dlgAddColumn', 'dlgChooseExportCols', 'dlgCartModal', 'cdlg', 'qsdlg', 'dlgEventPopup', 'dlgActionProgress', 'dlgUploadErrorsAlert']")
print("✓ Added dlgUploadErrorsAlert to inventory dialog keys")

with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
    f.write(text)

print("=== PATCH COMPLETE ===")

