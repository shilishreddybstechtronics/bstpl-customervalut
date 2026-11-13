import re, sys

print("=== Implementing Universal Inter-Page Interlinking & Data Sync System ===")

with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update subnav in containers['box-inv']: Remove hardcoded 154
text = text.replace(
    '<span>📁</span> <span>Customer Files</span> (<span id="invCustCountBadge">154</span>)',
    '<span>📁</span> <span>Customer Files</span> (<span id="invCustCountBadge">0</span>)'
)
text = text.replace(
    "(CU || []).length || '154'",
    "(CU || []).length || 0"
)

# 2. Update sidebar template: Remove hardcoded 2055
old_err_badge = '<span class="badge danger" id="sidebarErrorsBadge" style="margin-left:auto;background:#ef4444;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;font-weight:800">2055</span>'
new_err_badge = '<span class="badge danger" id="sidebarErrorsBadge" style="margin-left:auto;background:#ef4444;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;font-weight:800;display:none">0</span>'
text = text.replace(old_err_badge, new_err_badge)

# 3. Add automatic notifyDataUpdated trigger in api() function for mutating requests (POST, PUT, DELETE, PATCH)
old_api_return = "return r.json();"
new_api_return = """const _resData = await r.json();
      const _reqMethod = (opt.method || 'GET').toUpperCase();
      if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(_reqMethod)) {
        if (!path.includes('/auth/') && !path.includes('/logs') && !path.includes('/audit')) {
          if (typeof notifyDataUpdated === 'function') {
            notifyDataUpdated({ path, method: _reqMethod });
          }
        }
      }
      return _resData;"""

if old_api_return in text and new_api_return not in text:
    text = text.replace(old_api_return, new_api_return, 1)
    print("✓ Added automatic mutation detection to api() wrapper")

# 4. Add Universal Inter-Page Data Synchronization System to LEAN_FOUNDATION_JS
sync_system_code = r'''
    // --- Universal Inter-Page Interlinking & Data Synchronization System ---
    let lastKnownDbUpdate = parseInt(localStorage.getItem('customervault_db_updated') || '0', 10);

    function notifyDataUpdated(detail = {}) {
      const now = Date.now();
      lastKnownDbUpdate = now;
      try {
        localStorage.setItem('customervault_db_updated', String(now));
        if (window.BroadcastChannel) {
          const bc = new BroadcastChannel('customervault_sync_channel');
          bc.postMessage({ type: 'DB_UPDATED', timestamp: now, detail });
          bc.close();
        }
      } catch (e) {}
    }
    window.notifyDataUpdated = notifyDataUpdated;

    async function syncGlobalMetricsAndChrome() {
      try {
        const [statsRes, custsRes] = await Promise.all([
          api('/api/stats').catch(() => null),
          api('/api/customers').catch(() => null)
        ]);

        if (statsRes) {
          S = statsRes;
          const devTotal = statsRes.total_devices != null ? statsRes.total_devices : (statsRes.devices || 0);
          const custTotal = statsRes.total_customers != null ? statsRes.total_customers : (statsRes.customers || 0);
          const errTotal = statsRes.errored_records != null ? statsRes.errored_records : 0;
          const cartTotal = statsRes.deleted_devices != null ? statsRes.deleted_devices : (statsRes.deleted || 0);
          const exp30Total = statsRes.expiring_30_days != null ? statsRes.expiring_30_days : (statsRes.total_expiring || 0);
          const expiredTotal = statsRes.expired != null ? statsRes.expired : (statsRes.total_expired || 0);

          // Update sidebar badges and widgets
          if ($('sbLiveDevCount')) $('sbLiveDevCount').textContent = Number(devTotal).toLocaleString();
          if ($('sbLiveCustCount')) $('sbLiveCustCount').textContent = Number(custTotal).toLocaleString();
          if ($('sidebarErrorsBadge')) {
            $('sidebarErrorsBadge').textContent = Number(errTotal).toLocaleString();
            $('sidebarErrorsBadge').style.display = errTotal > 0 ? 'inline-block' : 'none';
          }
          if ($('invCustCountBadge')) $('invCustCountBadge').textContent = Number(custTotal).toLocaleString();
          if ($('topCartCountBadge')) $('topCartCountBadge').textContent = cartTotal;
          if ($('cartCountText')) $('cartCountText').textContent = cartTotal;
          if ($('simRestoreCountBadge')) $('simRestoreCountBadge').textContent = `${Number(cartTotal).toLocaleString()} records`;

          // Update Home Overview & Live Stream KPI cards if present
          if ($('kpiDev')) $('kpiDev').textContent = Number(devTotal).toLocaleString();
          if ($('kpiCust')) $('kpiCust').textContent = Number(custTotal).toLocaleString();
          if ($('kpiExp30')) $('kpiExp30').textContent = Number(exp30Total).toLocaleString();
          if ($('kpiExpired')) $('kpiExpired').textContent = Number(expiredTotal).toLocaleString();
        }

        if (custsRes && Array.isArray(custsRes)) {
          CU = custsRes;
          if ($('invCustCountBadge')) $('invCustCountBadge').textContent = CU.length.toLocaleString();
          if (typeof populateNfCustomerDropdown === 'function') populateNfCustomerDropdown();
          if (typeof populateBfCustomerFilter === 'function') populateBfCustomerFilter();
          if (typeof populateLiveCustomerDropdown === 'function') populateLiveCustomerDropdown();
          if (typeof refreshUploadCustDropdown === 'function') refreshUploadCustDropdown();
        }
      } catch(e) {
        console.warn('Sync metrics error:', e);
      }
    }
    window.syncGlobalMetricsAndChrome = syncGlobalMetricsAndChrome;

    let _refreshDebounceTimer = null;
    function triggerLivePageRefresh() {
      clearTimeout(_refreshDebounceTimer);
      _refreshDebounceTimer = setTimeout(async () => {
        await syncGlobalMetricsAndChrome();

        // Dynamically re-fetch container data on active page
        const path = window.location.pathname.toLowerCase();
        if (path.endsWith('home.html') || path.endsWith('dashboard.html') || path.endsWith('index.html')) {
          if (typeof updateHomeStatsRibbon === 'function') updateHomeStatsRibbon();
          if (typeof updateHomeExpiryBanner === 'function') updateHomeExpiryBanner();
          if (typeof runLiveCycle === 'function') runLiveCycle(true);
          if (typeof loadHealthContainer === 'function') loadHealthContainer();
        } else if (path.endsWith('inventory.html')) {
          if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
          if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
        } else if (path.endsWith('sim-upload.html')) {
          if (typeof refreshUploadCustDropdown === 'function') refreshUploadCustDropdown();
          if (typeof updateSimRestoreCount === 'function') updateSimRestoreCount();
        } else if (path.endsWith('fetch-data.html')) {
          if (typeof populateNfCustomerDropdown === 'function') populateNfCustomerDropdown();
          if (typeof populateBfCustomerFilter === 'function') populateBfCustomerFilter();
          if (typeof runNormalFetch === 'function' && $('fq') && $('fq').value.trim()) runNormalFetch();
        } else if (path.endsWith('edit-delete.html')) {
          if (typeof runSearch === 'function' && $('qImei') && $('qImei').value.trim()) runSearch();
        } else if (path.endsWith('alerts.html')) {
          if (typeof loadExpiryContainer === 'function') loadExpiryContainer();
        } else if (path.endsWith('errors.html')) {
          if (typeof loadErrorsContainer === 'function') loadErrorsContainer();
        } else if (path.endsWith('settings.html')) {
          if (typeof loadSettingsPage === 'function') loadSettingsPage();
        }
      }, 200);
    }
    window.triggerLivePageRefresh = triggerLivePageRefresh;

    // Cross-tab broadcast listener
    if (window.BroadcastChannel) {
      try {
        const syncBc = new BroadcastChannel('customervault_sync_channel');
        syncBc.onmessage = e => {
          if (e.data && e.data.type === 'DB_UPDATED') {
            lastKnownDbUpdate = e.data.timestamp;
            triggerLivePageRefresh();
          }
        };
      } catch (e) {}
    }

    // Storage event listener (cross-window fallback)
    window.addEventListener('storage', e => {
      if (e.key === 'customervault_db_updated') {
        const ts = parseInt(e.newValue || '0', 10);
        if (ts > lastKnownDbUpdate) {
          lastKnownDbUpdate = ts;
          triggerLivePageRefresh();
        }
      }
    });

    // Window focus listener: When user switches back to this tab/window, refresh immediately
    window.addEventListener('focus', () => {
      const cur = parseInt(localStorage.getItem('customervault_db_updated') || '0', 10);
      if (cur > lastKnownDbUpdate) {
        lastKnownDbUpdate = cur;
        triggerLivePageRefresh();
      } else {
        syncGlobalMetricsAndChrome();
      }
    });
'''

# Replace updateSidebarStats with syncGlobalMetricsAndChrome
old_sidebar_stats = r'''    async function updateSidebarStats() {
      try {
        const s = await api('/api/stats');
        if (s) {
          S = s;
          if ($('sbLiveDevCount') && s.total_devices != null) $('sbLiveDevCount').textContent = Number(s.total_devices).toLocaleString();
          if ($('sbLiveCustCount') && s.total_customers != null) $('sbLiveCustCount').textContent = Number(s.total_customers).toLocaleString();
        }
      } catch(e) {}
    }
    updateSidebarStats();'''

if old_sidebar_stats in text:
    text = text.replace(old_sidebar_stats, sync_system_code + "\n    syncGlobalMetricsAndChrome();")
    print("✓ Replaced updateSidebarStats with syncGlobalMetricsAndChrome & cross-page synchronization system")
else:
    print("! Could not find exact old_sidebar_stats block, checking fallback")

# 5. Ensure _bootPage calls await syncGlobalMetricsAndChrome(); across all pages
old_boot_snippet = """    // Page Boot
    const _bootPage = async () => {
      {p['init_js']}
    };"""

new_boot_snippet = """    // Page Boot
    const _bootPage = async () => {
      await syncGlobalMetricsAndChrome();
      {p['init_js']}
    };"""

if old_boot_snippet in text:
    text = text.replace(old_boot_snippet, new_boot_snippet)
    print("✓ Enhanced _bootPage to await syncGlobalMetricsAndChrome() on every page")

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("=== Patch complete! ===")

