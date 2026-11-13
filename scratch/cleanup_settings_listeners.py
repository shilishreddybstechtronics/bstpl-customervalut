import re

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the region between `function openSettingsModal() {` and `// Global Expiry Banner Action Buttons`
    start_str = 'function openSettingsModal() {'
    start_pos = content.find(start_str)
    if start_pos == -1:
        raise Exception("Could not find openSettingsModal in " + filepath)

    end_str = '// Global Expiry Banner Action Buttons'
    end_pos = content.find(end_str)
    if end_pos == -1:
        raise Exception("Could not find end marker in " + filepath)

    clean_settings_block = '''function openSettingsModal() {
        const dlg = $('dlgSettings');
        if (!dlg) return;

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
      }

      if ($('closeDlgSettings')) $('closeDlgSettings').onclick = () => $('dlgSettings').close();
      if ($('btnCloseDlgSettingsFooter')) $('btnCloseDlgSettingsFooter').onclick = () => $('dlgSettings').close();
      if ($('sidebarBtnSettings')) $('sidebarBtnSettings').onclick = openSettingsModal;
      if ($('btnHeaderSettings')) $('btnHeaderSettings').onclick = openSettingsModal;

      // Settings Theme Mode Switchers (Light / Dark)
      if ($('settingsModeDark')) {
        $('settingsModeDark').onclick = () => {
          const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
          applyTheme(currentPal, 'dark', true);
        };
      }
      if ($('settingsModeLight')) {
        $('settingsModeLight').onclick = () => {
          const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
          applyTheme(currentPal, 'light', true);
        };
      }

      // Settings 7 Theme Palette Buttons
      document.querySelectorAll('#dlgSettings .theme-palette-opt').forEach(btn => {
        btn.onclick = () => {
          const pal = btn.dataset.paletteVal;
          const currentMode = localStorage.getItem('valut_theme_mode') || 'light';
          applyTheme(pal, currentMode, true);
          toast(`Applied theme: ${btn.querySelector('.theme-name')?.textContent || pal}`);
        };
      });

      // Settings Actions Wiring (Edit Name, Change Password, Manage Users, Log Inventory, Logout)
      if ($('settingsBtnEditName')) {
        $('settingsBtnEditName').onclick = () => {
          $('dlgSettings').close();
          openEditNameModal();
        };
      }

      if ($('settingsBtnPassword')) {
        $('settingsBtnPassword').onclick = () => {
          $('dlgSettings').close();
          openChangePasswordModal();
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
      }

      // Cart Popup Modal Handlers (Cart opens as popup with Cross X close)
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

      // Large Live Updates Popup Modal Handler
      let liveUpdatesModalTimer = null;
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

      async function refreshLiveUpdatesModalData() {
        try {
          const [rawIns, rawHea, rawAct] = await Promise.all([
            api('/api/inventory/insights').catch(() => null),
            api('/api/inventory/health').catch(() => null),
            api('/api/activity?page=1&page_size=10').catch(() => null)
          ]);
          const ins = (rawIns && typeof rawIns === 'object') ? rawIns : { total_devices: 0, total_customers: 0, expiring_30: 0, expired: 0 };
          const hea = (rawHea && typeof rawHea === 'object') ? rawHea : { score: 100, completeness: {}, issues: [] };
          const actData = (rawAct && typeof rawAct === 'object' && Array.isArray(rawAct.items)) ? rawAct : { items: [] };

          if (ins) {
            if ($('kpiDev')) $('kpiDev').textContent = (ins.total_devices || 0).toLocaleString();
            if ($('kpiCust')) $('kpiCust').textContent = (ins.total_customers || 0).toLocaleString();
            if ($('kpiExp30')) $('kpiExp30').textContent = (ins.expiring_30 || 0).toLocaleString();
            if ($('kpiExpired')) $('kpiExpired').textContent = (ins.expired || 0).toLocaleString();
          }

          if (hea && hea.score !== undefined) {
            if ($('kpiHealth')) $('kpiHealth').textContent = `${Math.round(hea.score || 98)}%`;
          }

          if ($('dlgLiveTime')) {
            $('dlgLiveTime').textContent = new Date().toLocaleTimeString();
          }

          if (actData && actData.items && $('dlgLiveLogTbody')) {
            $('dlgLiveLogTbody').innerHTML = actData.items.map(it => {
              const d = new Date(it.created_at);
              const dStr = isNaN(d.getTime()) ? it.created_at : d.toLocaleTimeString([], { hour:'2-digit', minute:'2-digit', second:'2-digit' });
              return `
                <tr>
                  <td>${esc(dStr)}</td>
                  <td><b>${esc(it.action || 'Event')}</b></td>
                  <td>${esc(it.user_name || it.user_login || 'System')}</td>
                  <td><code>${esc((it.detail || '—').substring(0, 45))}</code></td>
                  <td><span class="badge" style="background:var(--ok);color:#fff;font-weight:700">Success</span></td>
                </tr>
              `;
            }).join('');
          }
        } catch(e) {
          console.log('Error refreshing live telemetry popup:', e);
        }
      }

      if ($('sidebarLiveUpdatesBtn')) $('sidebarLiveUpdatesBtn').onclick = openLiveUpdatesModal;
      if ($('closeDlgLiveUpdates')) $('closeDlgLiveUpdates').onclick = closeLiveUpdatesModal;
      if ($('dlgManualLiveRefresh')) $('dlgManualLiveRefresh').onclick = refreshLiveUpdatesModalData;

      '''

    content = content[:start_pos] + clean_settings_block + content[end_pos:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Cleaned {filepath} successfully.")

clean_file('frontend/index.html')
clean_file('frontend/dashboard.html')

