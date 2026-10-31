import os

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Sunset theme to CSS right after Violet dark mode
violet_end = '''      --cv-sidebar-bg: linear-gradient(180deg, #10021e 0%, #1a052e 100%);
    }'''

sunset_css = '''      --cv-sidebar-bg: linear-gradient(180deg, #10021e 0%, #1a052e 100%);
    }

    /* 7. SUNSET (Burnt Orange and Warm Amber) */
    [data-palette="sunset"][data-mode="light"],
    [data-palette="sunset"]:not([data-mode="dark"]) {
      --bg: #fffbf5;
      --bg-gradient: linear-gradient(180deg, #fffbf5 0%, #fef3e2 100%);
      --card: #ffffff;
      --card-subtle: #fef3e2;
      --text: #431407;
      --text-dim: #7c2d12;
      --ink: #431407;
      --ink2: #7c2d12;
      --line: #fed7aa;
      --primary: #c2410c;
      --primary-hover: #9a3412;
      --accent: #f59e0b;
      --accentd: #d97706;
      --accent-light: #fef3c7;
      --muted: #9a3412;
      --ok: #16a34a;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #7c2d12 0%, #9a3412 100%);
    }
    [data-palette="sunset"][data-mode="dark"] {
      --bg: #1c0f0a;
      --bg-gradient: linear-gradient(180deg, #1c0f0a 0%, #2b170e 100%);
      --card: #2b170e;
      --card-subtle: #3d2014;
      --text: #ffedd5;
      --text-dim: #fdba74;
      --ink: #ffedd5;
      --ink2: #fed7aa;
      --line: #7c2d12;
      --primary: #ea580c;
      --primary-hover: #f97316;
      --accent: #f59e0b;
      --accentd: #fbbf24;
      --accent-light: rgba(245, 158, 11, 0.2);
      --muted: #fdba74;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #fbbf24;
      --cv-sidebar-bg: linear-gradient(180deg, #120906 0%, #1c0f0a 100%);
    }'''

assert violet_end in content, "violet_end not found"
content = content.replace(violet_end, sunset_css, 1)

# Update comment "6 THEMES" to "7 THEMES"
content = content.replace('/* ===== 6 THEMES (with Light & Dark Mode Support) ===== */', '/* ===== 7 THEMES (with Light & Dark Mode Support) ===== */', 1)

# 2. Upgrade Password dialog and add Edit Name dialog
old_pwd_dialog = '''  <!-- Password Change Dialog -->
  <dialog id="pwd">
    <form id="pf">
      <h2>Change Account Password</h2>
      <label for="p1">Current Password</label>
      <input type="password" id="p1" autocomplete="current-password" required />
      <label for="p2" style="margin-top:12px">New Password (at least 8 characters)</label>
      <input type="password" id="p2" autocomplete="new-password" minlength="8" required />
      <label for="p3" style="margin-top:12px">Repeat New Password</label>
      <input type="password" id="p3" autocomplete="new-password" required />
      <p class="err" id="pe" role="alert"></p>
      <div class="row" style="margin:16px 0 0; justify-content: flex-end;">
        <button class="b" type="button" id="pc">Cancel</button>
        <button class="b p" type="submit">Update Password</button>
      </div>
    </form>
  </dialog>'''

new_dialogs = '''  <!-- =========================================================================
     POPUP: EDIT EMPLOYEE NAME (Present Name, New Name, Confirm New Name + Cross (X) Close)
     ========================================================================= -->
  <dialog id="dlgEditName" class="modal-card" style="width:min(480px, 94vw); padding:0; border-radius:18px; border:1px solid var(--line); box-shadow:0 24px 60px rgba(0,0,0,0.35); overflow:hidden">
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
      <div style="margin-bottom:14px">
        <label for="editNamePresent" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">Present Name</label>
        <input type="text" id="editNamePresent" readonly disabled style="width:100%; box-sizing:border-box; background:var(--card-subtle); color:var(--text-dim); opacity:0.85; cursor:not-allowed; border:1px solid var(--line); border-radius:8px; padding:10px 12px; font-size:13.5px; font-weight:600" />
      </div>

      <div style="margin-bottom:14px">
        <label for="editNameNew" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">New Name</label>
        <input type="text" id="editNameNew" placeholder="Enter new employee display name" required style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 12px; font-size:13.5px" />
      </div>

      <div style="margin-bottom:14px">
        <label for="editNameConfirm" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">Confirm New Name</label>
        <input type="text" id="editNameConfirm" placeholder="Re-enter new employee display name" required style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 12px; font-size:13.5px" />
      </div>

      <p class="err" id="editNameError" role="alert" style="margin:8px 0 14px; font-size:12.5px; font-weight:600; color:var(--danger)" hidden></p>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:18px">
        <button class="b" type="button" onclick="closeEditNameModal()">Cancel</button>
        <button class="b p" type="submit" id="btnConfirmEditName">Confirm Name Change</button>
      </div>
    </form>
  </dialog>

  <!-- =========================================================================
     POPUP: CHANGE ACCOUNT PASSWORD (Present Password, New Password, Confirm Password + Cross (X) Close)
     ========================================================================= -->
  <dialog id="pwd" class="modal-card" style="width:min(480px, 94vw); padding:0; border-radius:18px; border:1px solid var(--line); box-shadow:0 24px 60px rgba(0,0,0,0.35); overflow:hidden">
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
        <label for="p1" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">Present Password</label>
        <div style="position:relative">
          <input type="password" id="p1" autocomplete="current-password" placeholder="Enter present password" required style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 38px 10px 12px; font-size:13.5px" />
          <button type="button" class="b ghost" style="position:absolute; right:6px; top:50%; transform:translateY(-50%); padding:2px 6px; font-size:13px; border:none; cursor:pointer" onclick="togglePasswordInputVisibility('p1')">👁️</button>
        </div>
      </div>

      <div style="margin-bottom:14px">
        <label for="p2" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">New Password</label>
        <div style="position:relative">
          <input type="password" id="p2" autocomplete="new-password" minlength="8" placeholder="Enter new password (min. 8 characters)" required style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 38px 10px 12px; font-size:13.5px" />
          <button type="button" class="b ghost" style="position:absolute; right:6px; top:50%; transform:translateY(-50%); padding:2px 6px; font-size:13px; border:none; cursor:pointer" onclick="togglePasswordInputVisibility('p2')">👁️</button>
        </div>
      </div>

      <div style="margin-bottom:14px">
        <label for="p3" style="display:block; font-size:12px; font-weight:700; color:var(--text); margin-bottom:6px">Confirm Password</label>
        <div style="position:relative">
          <input type="password" id="p3" autocomplete="new-password" placeholder="Confirm new password" required style="width:100%; box-sizing:border-box; background:var(--card); color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px 38px 10px 12px; font-size:13.5px" />
          <button type="button" class="b ghost" style="position:absolute; right:6px; top:50%; transform:translateY(-50%); padding:2px 6px; font-size:13px; border:none; cursor:pointer" onclick="togglePasswordInputVisibility('p3')">👁️</button>
        </div>
      </div>

      <p class="err" id="pe" role="alert" style="margin:8px 0 14px; font-size:12.5px; font-weight:600; color:var(--danger)"></p>

      <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:18px">
        <button class="b" type="button" id="pc" onclick="closeChangePasswordModal()">Cancel</button>
        <button class="b p" type="submit" id="btnConfirmChangePw">Confirm Password Change</button>
      </div>
    </form>
  </dialog>'''

assert old_pwd_dialog in content, "old_pwd_dialog not found"
content = content.replace(old_pwd_dialog, new_dialogs, 1)

# 3. Delete #themeDockRightEnd completely
old_dock_html = '''  <!-- =========================================================================
     DOCKED THEME SELECTOR AT RIGHT-END (6 Themes + Dark/Light Mode)
     ========================================================================= -->
  <div id="themeDockRightEnd" class="theme-dock-container">
    <button id="themeDockToggleBtn" class="theme-dock-tab" type="button" title="Switch Theme (6 Styles + Dark/Light)">
      <span class="theme-dock-icon">🎨</span>
      <span class="theme-dock-label">THEMES</span>
    </button>
    <div id="themeDockPanel" class="theme-dock-panel" hidden>
      <div class="theme-dock-header">
        <div style="font-weight:800;font-size:14px;display:flex;align-items:center;gap:6px">
          <span>🎨</span> <span>Theme Selector</span>
        </div>
        <button class="b ghost" id="themeDockCloseBtn" type="button" style="font-size:16px;padding:2px 8px;cursor:pointer">✕</button>
      </div>
      <div style="padding:14px 16px">
        <!-- Dark / Light Mode Switcher -->
        <div style="margin-bottom:14px">
          <label style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--muted);letter-spacing:0.5px;display:block;margin-bottom:6px">Mode Variant</label>
          <div class="theme-mode-switch" style="display:grid;grid-template-columns:1fr 1fr;gap:6px;background:var(--bg);padding:4px;border-radius:8px;border:1px solid var(--line)">
            <button type="button" class="theme-mode-btn" data-mode-val="dark" id="btnModeDark" style="display:flex;align-items:center;justify-content:center;gap:6px;padding:7px;font-size:12px;font-weight:700;border-radius:6px;border:none;cursor:pointer">
              <span>🌙</span> <span>Dark</span>
            </button>
            <button type="button" class="theme-mode-btn" data-mode-val="light" id="btnModeLight" style="display:flex;align-items:center;justify-content:center;gap:6px;padding:7px;font-size:12px;font-weight:700;border-radius:6px;border:none;cursor:pointer">
              <span>☀️</span> <span>Light</span>
            </button>
          </div>
        </div>

        <!-- 6 Requested Themes Selector -->
        <div>
          <label style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--muted);letter-spacing:0.5px;display:block;margin-bottom:8px">Theme Style</label>
          <div style="display:flex;flex-direction:column;gap:6px">
            <button type="button" class="theme-palette-opt" data-palette-val="royal_navy">
              <div class="theme-swatch-group">
                <span style="background:#0f2b5c"></span>
                <span style="background:#d4af37"></span>
                <span style="background:#f8fafc"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Royal Navy</div>
                <div class="theme-desc">Navy and gold (Default, Light Page)</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="midnight">
              <div class="theme-swatch-group">
                <span style="background:#070d19"></span>
                <span style="background:#1e3a8a"></span>
                <span style="background:#eab308"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Midnight</div>
                <div class="theme-desc">Dark navy with soft gold</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="emerald">
              <div class="theme-swatch-group">
                <span style="background:#065f46"></span>
                <span style="background:#10b981"></span>
                <span style="background:#d4af37"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Emerald</div>
                <div class="theme-desc">Deep green with gold</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="crimson_vault">
              <div class="theme-swatch-group">
                <span style="background:#881337"></span>
                <span style="background:#e11d48"></span>
                <span style="background:#d4af37"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Crimson Vault</div>
                <div class="theme-desc">Wine red, close to your brand</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="ocean">
              <div class="theme-swatch-group">
                <span style="background:#0f766e"></span>
                <span style="background:#0284c7"></span>
                <span style="background:#f59e0b"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Ocean</div>
                <div class="theme-desc">Teal-blue with amber</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="violet">
              <div class="theme-swatch-group">
                <span style="background:#581c87"></span>
                <span style="background:#7e22ce"></span>
                <span style="background:#d4af37"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Violet</div>
                <div class="theme-desc">Rich purple with gold</div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>'''

assert old_dock_html in content, "old_dock_html not found"
content = content.replace(old_dock_html, '', 1)

# 4. Add the 7 Themes + Light/Dark mode inside #dlgSettings
old_dlg_settings_body = '''        <button type="button" class="settings-action-item" id="settingsBtnLoginInv">
          <div class="settings-action-icon" style="background:#f3e8ff;color:#9333ea">🕘</div>
          <div class="settings-action-text">
            <div class="settings-action-title">Login Inventory (Activity Log)</div>
            <div class="settings-action-desc">Audit user sign-ins, uploads &amp; deletions</div>
          </div>
          <span class="settings-action-arrow">›</span>
        </button>

        <hr style="border:none; border-top:1px solid var(--line); margin:6px 0" />

        <button type="button" class="settings-action-item danger" id="settingsBtnLogout">'''

new_dlg_settings_body = '''        <button type="button" class="settings-action-item" id="settingsBtnLoginInv">
          <div class="settings-action-icon" style="background:#f3e8ff;color:#9333ea">🕘</div>
          <div class="settings-action-text">
            <div class="settings-action-title">Login Inventory (Activity Log)</div>
            <div class="settings-action-desc">Audit user sign-ins, uploads &amp; deletions</div>
          </div>
          <span class="settings-action-arrow">›</span>
        </button>

        <!-- Themes & Look (7 Themes + Light/Dark Mode) -->
        <div style="margin-top:14px; border-top:1px solid var(--line); padding-top:14px">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px">
            <div>
              <div style="font-weight:700; font-size:13px; color:var(--text)">🎨 Theme &amp; Look</div>
              <div style="font-size:11.5px; color:var(--muted)">7 Custom themes with Light &amp; Dark mode</div>
            </div>
            <!-- Mode Switcher -->
            <div style="display:inline-flex; gap:4px; background:var(--bg); padding:3px; border-radius:8px; border:1px solid var(--line)">
              <button type="button" class="theme-mode-btn" data-mode-val="light" id="settingsModeLight" style="display:flex; align-items:center; gap:4px; padding:5px 10px; font-size:12px; font-weight:700; border-radius:6px; border:1px solid transparent; cursor:pointer">
                <span>☀️</span> <span>Light</span>
              </button>
              <button type="button" class="theme-mode-btn" data-mode-val="dark" id="settingsModeDark" style="display:flex; align-items:center; gap:4px; padding:5px 10px; font-size:12px; font-weight:700; border-radius:6px; border:1px solid transparent; cursor:pointer">
                <span>🌙</span> <span>Dark</span>
              </button>
            </div>
          </div>

          <!-- 7 Theme Choices -->
          <div style="display:flex; flex-direction:column; gap:6px; max-height:220px; overflow-y:auto; padding-right:4px">
            <button type="button" class="theme-palette-opt" data-palette-val="royal_navy" style="display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:10px; border:1.5px solid var(--line); background:var(--card); cursor:pointer; text-align:left; transition:all 0.15s ease">
              <div class="theme-swatch-group" style="display:inline-flex; gap:3px">
                <span style="width:14px; height:14px; border-radius:50%; background:#0f2b5c; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#d4af37; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#f8fafc; border:1px solid #cbd5e1; display:inline-block"></span>
              </div>
              <div class="theme-palette-info" style="flex:1">
                <div class="theme-name" style="font-weight:700; font-size:12.5px; color:var(--text)">Royal Navy</div>
                <div class="theme-desc" style="font-size:11px; color:var(--muted)">The default: navy and gold, light page</div>
              </div>
            </button>

            <button type="button" class="theme-palette-opt" data-palette-val="midnight" style="display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:10px; border:1.5px solid var(--line); background:var(--card); cursor:pointer; text-align:left; transition:all 0.15s ease">
              <div class="theme-swatch-group" style="display:inline-flex; gap:3px">
                <span style="width:14px; height:14px; border-radius:50%; background:#070d19; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#1e3a8a; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#eab308; display:inline-block"></span>
              </div>
              <div class="theme-palette-info" style="flex:1">
                <div class="theme-name" style="font-weight:700; font-size:12.5px; color:var(--text)">Midnight</div>
                <div class="theme-desc" style="font-size:11px; color:var(--muted)">Dark navy with soft gold</div>
              </div>
            </button>

            <button type="button" class="theme-palette-opt" data-palette-val="emerald" style="display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:10px; border:1.5px solid var(--line); background:var(--card); cursor:pointer; text-align:left; transition:all 0.15s ease">
              <div class="theme-swatch-group" style="display:inline-flex; gap:3px">
                <span style="width:14px; height:14px; border-radius:50%; background:#065f46; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#10b981; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#d4af37; display:inline-block"></span>
              </div>
              <div class="theme-palette-info" style="flex:1">
                <div class="theme-name" style="font-weight:700; font-size:12.5px; color:var(--text)">Emerald</div>
                <div class="theme-desc" style="font-size:11px; color:var(--muted)">Deep green with gold</div>
              </div>
            </button>

            <button type="button" class="theme-palette-opt" data-palette-val="crimson_vault" style="display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:10px; border:1.5px solid var(--line); background:var(--card); cursor:pointer; text-align:left; transition:all 0.15s ease">
              <div class="theme-swatch-group" style="display:inline-flex; gap:3px">
                <span style="width:14px; height:14px; border-radius:50%; background:#881337; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#e11d48; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#d4af37; display:inline-block"></span>
              </div>
              <div class="theme-palette-info" style="flex:1">
                <div class="theme-name" style="font-weight:700; font-size:12.5px; color:var(--text)">Crimson Vault</div>
                <div class="theme-desc" style="font-size:11px; color:var(--muted)">Wine red, close to your current brand</div>
              </div>
            </button>

            <button type="button" class="theme-palette-opt" data-palette-val="ocean" style="display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:10px; border:1.5px solid var(--line); background:var(--card); cursor:pointer; text-align:left; transition:all 0.15s ease">
              <div class="theme-swatch-group" style="display:inline-flex; gap:3px">
                <span style="width:14px; height:14px; border-radius:50%; background:#0f766e; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#0284c7; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#f59e0b; display:inline-block"></span>
              </div>
              <div class="theme-palette-info" style="flex:1">
                <div class="theme-name" style="font-weight:700; font-size:12.5px; color:var(--text)">Ocean</div>
                <div class="theme-desc" style="font-size:11px; color:var(--muted)">Teal-blue with amber</div>
              </div>
            </button>

            <button type="button" class="theme-palette-opt" data-palette-val="violet" style="display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:10px; border:1.5px solid var(--line); background:var(--card); cursor:pointer; text-align:left; transition:all 0.15s ease">
              <div class="theme-swatch-group" style="display:inline-flex; gap:3px">
                <span style="width:14px; height:14px; border-radius:50%; background:#581c87; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#7e22ce; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#d4af37; display:inline-block"></span>
              </div>
              <div class="theme-palette-info" style="flex:1">
                <div class="theme-name" style="font-weight:700; font-size:12.5px; color:var(--text)">Violet</div>
                <div class="theme-desc" style="font-size:11px; color:var(--muted)">Rich purple with gold</div>
              </div>
            </button>

            <button type="button" class="theme-palette-opt" data-palette-val="sunset" style="display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:10px; border:1.5px solid var(--line); background:var(--card); cursor:pointer; text-align:left; transition:all 0.15s ease">
              <div class="theme-swatch-group" style="display:inline-flex; gap:3px">
                <span style="width:14px; height:14px; border-radius:50%; background:#c2410c; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#ea580c; display:inline-block"></span>
                <span style="width:14px; height:14px; border-radius:50%; background:#f59e0b; display:inline-block"></span>
              </div>
              <div class="theme-palette-info" style="flex:1">
                <div class="theme-name" style="font-weight:700; font-size:12.5px; color:var(--text)">Sunset</div>
                <div class="theme-desc" style="font-size:11px; color:var(--muted)">Burnt orange and warm amber</div>
              </div>
            </button>
          </div>
        </div>

        <hr style="border:none; border-top:1px solid var(--line); margin:12px 0 6px" />

        <button type="button" class="settings-action-item danger" id="settingsBtnLogout">'''

assert old_dlg_settings_body in content, "old_dlg_settings_body not found"
content = content.replace(old_dlg_settings_body, new_dlg_settings_body, 1)

# Make dlgSettings scrollable and slightly wider
content = content.replace('id="dlgSettings" class="modal-card" style="width:min(520px, 94vw); padding:0; border-radius:20px; border:1px solid var(--line); box-shadow:0 24px 60px rgba(0,0,0,0.35); overflow:hidden"',
                          'id="dlgSettings" class="modal-card" style="width:min(560px, 95vw); max-height:88vh; padding:0; border-radius:20px; border:1px solid var(--line); box-shadow:0 24px 60px rgba(0,0,0,0.35); overflow-y:auto"', 1)

# 5. Wire Edit Name and Change Password JS modal functions
old_pw_wiring = '''      if ($('bEditMyName')) {
        $('bEditMyName').onclick = async () => {
          const u = getUser();
          const p = prompt('Enter your new display name:', u.name || '');
          if (!p || !p.trim() || p.trim() === u.name) return;
          try {
            const r = await api('/api/me/name', { method: 'PUT', body: JSON.stringify({ name: p.trim() }) });
            u.name = r.name;
            localStorage.setItem('user', JSON.stringify(u));
            const h = new Date().getHours();
            $('hi').textContent = `Good ${h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening'}, ${u.name || u.user_id}`;
        const uInitial = ((u.name || u.user_id || 'U')[0] || 'U').toUpperCase();
        if ($('userAvatarCircle')) $('userAvatarCircle').textContent = uInitial;
            toast('Your display name has been updated');
            if (typeof loadUsersContainer === 'function') loadUsersContainer();
          } catch (err) { fail(err); }
        };
      }
      if ($('bPw')) $('bPw').onclick = () => { if ($('pf')) $('pf').reset(); if ($('pe')) $('pe').textContent = ''; if ($('pwd')) $('pwd').showModal(); };
      if ($('pc')) $('pc').onclick = () => { if ($('pwd')) $('pwd').close(); };
      if ($('pf')) $('pf').onsubmit = async e => {
        e.preventDefault(); $('pe').textContent = '';
        if ($('p2').value !== $('p3').value) { $('pe').textContent = 'New passwords do not match.'; return; }
        try {
          const r = await api('/api/me/password', { method: 'POST', body: JSON.stringify({ current_password: $('p1').value, new_password: $('p2').value }) });
          if (r.access_token) { tok = r.access_token; localStorage.setItem('token', tok); }
          $('pwd').close();
          toast('Password changed successfully');
        } catch (err) { $('pe').textContent = err.message; }
      };'''

new_pw_wiring = '''      /* ---------- Edit Employee Name Modal Controller ---------- */
      function openEditNameModal() {
        const dlg = $('dlgEditName');
        if (!dlg) return;
        const u = getUser();
        const currentName = (window.CU && window.CU.name) || u.name || '';
        if ($('editNamePresent')) $('editNamePresent').value = currentName;
        if ($('editNameNew')) $('editNameNew').value = '';
        if ($('editNameConfirm')) $('editNameConfirm').value = '';
        if ($('editNameError')) {
          $('editNameError').textContent = '';
          $('editNameError').hidden = true;
        }
        if (!dlg.open) dlg.showModal();
        setTimeout(() => $('editNameNew')?.focus(), 50);
      }

      function closeEditNameModal() {
        const dlg = $('dlgEditName');
        if (dlg && dlg.open) dlg.close();
      }

      async function submitEditNameModal() {
        const errEl = $('editNameError');
        const newName = ($('editNameNew')?.value || '').trim();
        const confirmName = ($('editNameConfirm')?.value || '').trim();
        const presentName = ($('editNamePresent')?.value || '').trim();

        if (errEl) { errEl.textContent = ''; errEl.hidden = true; }

        if (!newName) {
          if (errEl) { errEl.textContent = 'Please enter a new employee name.'; errEl.hidden = false; }
          return;
        }
        if (newName !== confirmName) {
          if (errEl) { errEl.textContent = 'New name and confirm new name do not match.'; errEl.hidden = false; }
          return;
        }
        if (newName === presentName) {
          if (errEl) { errEl.textContent = 'New name is identical to present name. Please enter a different name.'; errEl.hidden = false; }
          return;
        }

        const btn = $('btnConfirmEditName');
        if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }

        try {
          const res = await api('/api/me/name', {
            method: 'PUT',
            body: JSON.stringify({ name: newName })
          });
          const updatedName = res.name || newName;

          // Update user in memory, storage, and website UI
          const u = getUser();
          u.name = updatedName;
          localStorage.setItem('user', JSON.stringify(u));
          if (window.CU) window.CU.name = updatedName;

          if ($('hi')) {
            const h = new Date().getHours();
            $('hi').textContent = `Good ${h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening'}, ${updatedName}`;
          }
          const uInitial = ((updatedName[0] || 'U')[0] || 'U').toUpperCase();
          if ($('userAvatarCircle')) $('userAvatarCircle').textContent = uInitial;

          closeEditNameModal();
          toast('Employee name updated successfully in website & database');

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
          if (btn) { btn.disabled = false; btn.textContent = 'Confirm Name Change'; }
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
      if ($('pf')) $('pf').onsubmit = async e => {
        e.preventDefault();
        const pe = $('pe');
        if (pe) { pe.textContent = ''; pe.hidden = true; }
        const curPw = $('p1')?.value || '';
        const newPw = $('p2')?.value || '';
        const repPw = $('p3')?.value || '';

        if (!curPw) {
          if (pe) { pe.textContent = 'Please enter your present password.'; pe.hidden = false; }
          return;
        }
        if (!newPw || newPw.length < 8) {
          if (pe) { pe.textContent = 'New password must be at least 8 characters long.'; pe.hidden = false; }
          return;
        }
        if (newPw !== repPw) {
          if (pe) { pe.textContent = 'New password and confirm password do not match.'; pe.hidden = false; }
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
          if (btn) { btn.disabled = false; btn.textContent = 'Confirm Password Change'; }
        }
      };'''

assert old_pw_wiring in content, "old_pw_wiring not found"
content = content.replace(old_pw_wiring, new_pw_wiring, 1)

# 6. Update applyTheme and initThemeDock
old_apply_theme = '''      /* ---------- Docked Theme Manager (6 Themes + Dark/Light) ---------- */
      function applyTheme(palette, mode) {
        const pal = palette || localStorage.getItem('valut_palette') || 'royal_navy';
        const m = mode || localStorage.getItem('valut_theme_mode') || 'light';

        document.documentElement.setAttribute('data-palette', pal);
        document.documentElement.setAttribute('data-mode', m);

        localStorage.setItem('valut_palette', pal);
        localStorage.setItem('valut_theme_mode', m);

        // Update active class on palette buttons
        document.querySelectorAll('.theme-palette-opt').forEach(opt => {
          opt.classList.toggle('active', opt.dataset.paletteVal === pal);
        });

        // Update active class on mode buttons
        const btnDark = $('btnModeDark');
        const btnLight = $('btnModeLight');
        if (btnDark) btnDark.classList.toggle('active', m === 'dark');
        if (btnLight) btnLight.classList.toggle('active', m === 'light');
      }

      function initThemeDock() {
        const dockPanel = $('themeDockPanel');
        const toggleBtn = $('themeDockToggleBtn');
        const closeBtn = $('themeDockCloseBtn');

        if (toggleBtn && dockPanel) {
          toggleBtn.onclick = () => {
            dockPanel.hidden = !dockPanel.hidden;
          };
        }
        if (closeBtn && dockPanel) {
          closeBtn.onclick = () => {
            dockPanel.hidden = true;
          };
        }

        // Palette selector buttons
        document.querySelectorAll('.theme-palette-opt').forEach(btn => {
          btn.onclick = () => {
            const pal = btn.dataset.paletteVal;
            const currentMode = localStorage.getItem('valut_theme_mode') || 'light';
            applyTheme(pal, currentMode);
            toast(`Applied theme: ${btn.querySelector('.theme-name')?.textContent || pal}`);
          };
        });

        // Dark / Light mode buttons
        const btnDark = $('btnModeDark');
        const btnLight = $('btnModeLight');
        if (btnDark) {
          btnDark.onclick = () => {
            const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
            applyTheme(currentPal, 'dark');
          };
        }
        if (btnLight) {
          btnLight.onclick = () => {
            const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
            applyTheme(currentPal, 'light');
          };
        }

        // Apply saved or default theme immediately
        applyTheme(localStorage.getItem('valut_palette') || 'royal_navy', localStorage.getItem('valut_theme_mode') || 'light');
      }'''

new_apply_theme = '''      /* ---------- Theme Manager (7 Themes + Dark/Light in Settings) ---------- */
      function applyTheme(palette, mode) {
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
      }

      function initThemeDock() {
        // Theme selection is managed directly inside Settings
        applyTheme(localStorage.getItem('valut_palette') || 'royal_navy', localStorage.getItem('valut_theme_mode') || 'light');
      }'''

assert old_apply_theme in content, "old_apply_theme not found"
content = content.replace(old_apply_theme, new_apply_theme, 1)

# 7. Update openSettingsModal and Settings Actions Wiring
old_settings_open = '''      function openSettingsModal() {
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

        // Highlight active palette and mode
        document.querySelectorAll('#dlgSettings .theme-palette-opt').forEach(btn => {
          btn.style.borderColor = (btn.dataset.paletteVal === currentPal) ? 'var(--primary, #1d68e1)' : 'var(--line)';
          btn.style.background = (btn.dataset.paletteVal === currentPal) ? 'rgba(29, 104, 225, 0.08)' : 'var(--card)';
        });
        if ($('settingsModeDark')) {
          $('settingsModeDark').style.borderColor = (currentMode === 'dark') ? 'var(--primary, #1d68e1)' : 'var(--line)';
          $('settingsModeDark').style.background = (currentMode === 'dark') ? 'rgba(29, 104, 225, 0.12)' : 'var(--card)';
        }
        if ($('settingsModeLight')) {
          $('settingsModeLight').style.borderColor = (currentMode === 'light') ? 'var(--primary, #1d68e1)' : 'var(--line)';
          $('settingsModeLight').style.background = (currentMode === 'light') ? 'rgba(29, 104, 225, 0.12)' : 'var(--card)';
        }

        dlg.showModal();
      }'''

new_settings_open = '''      function openSettingsModal() {
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
      }'''

assert old_settings_open in content, "old_settings_open not found"
content = content.replace(old_settings_open, new_settings_open, 1)

old_settings_actions = '''      // Settings Actions Wiring (Edit Name, Change Password, Manage Users, Log Inventory, Logout)
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

new_settings_actions = '''      // Settings Actions Wiring (Edit Name, Change Password, Manage Users, Log Inventory, Logout)
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

      // Settings Theme Mode Switchers (Light / Dark)
      if ($('settingsModeDark')) {
        $('settingsModeDark').onclick = () => {
          const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
          applyTheme(currentPal, 'dark');
        };
      }
      if ($('settingsModeLight')) {
        $('settingsModeLight').onclick = () => {
          const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
          applyTheme(currentPal, 'light');
        };
      }

      // Settings 7 Theme Palette Buttons
      document.querySelectorAll('#dlgSettings .theme-palette-opt').forEach(btn => {
        btn.onclick = () => {
          const pal = btn.dataset.paletteVal;
          const currentMode = localStorage.getItem('valut_theme_mode') || 'light';
          applyTheme(pal, currentMode);
          toast(`Applied theme: ${btn.querySelector('.theme-name')?.textContent || pal}`);
        };
      });

      // Settings Log Out Button
      if ($('settingsBtnLogout')) {
        $('settingsBtnLogout').onclick = () => {
          $('dlgSettings').close();
          logout(true);
        };
      }'''

assert old_settings_actions in content, "old_settings_actions not found"
content = content.replace(old_settings_actions, new_settings_actions, 1)

# Write to index.html and dashboard.html with CRLF line endings
with open('frontend/index.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)

with open('frontend/dashboard.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)

print("Successfully applied Sunset theme, Edit Name popup, Change Password popup, and Settings theme controls!")

