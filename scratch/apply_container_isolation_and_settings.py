with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Isolate banners and tabs: Move them INSIDE #box-home
banner_marker = '      <!-- Global SIM Expiry Alert Banner'
home_sec_marker = '      <section class="container-box active" id="box-home">'

banner_idx = text.find(banner_marker)
home_sec_idx = text.find(home_sec_marker)

assert banner_idx != -1, "banner_marker not found"
assert home_sec_idx != -1, "home_sec_marker not found"

slice_to_move = text[banner_idx:home_sec_idx]

# Remove slice from above home_sec
text = text[:banner_idx] + text[home_sec_idx:]

# Insert slice immediately after <section class="container-box active" id="box-home">
home_sec_new_idx = text.find(home_sec_marker) + len(home_sec_marker)
text = text[:home_sec_new_idx] + '\n' + slice_to_move + text[home_sec_new_idx:]

# 2. Fix static active on box-inv
text = text.replace('<section class="container-box active" id="box-inv">', '<section class="container-box" id="box-inv">')

# 3. Add box-settings container right after box-errors
box_settings_html = '''
      <!-- =========================================================================
         CONTAINER: SETTINGS & ACCOUNT PREFERENCES (Dedicated Webpage View)
         ========================================================================= -->
      <section class="container-box" id="box-settings">
        <!-- Settings Header Card -->
        <div class="card" style="margin-bottom:20px;padding:22px 26px;border:1px solid var(--line);border-radius:18px;background:var(--card);box-shadow:0 2px 12px rgba(15,23,42,0.04)">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px">
            <div style="display:flex;align-items:center;gap:14px">
              <div style="width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg, var(--primary), var(--accent));color:#fff;display:flex;align-items:center;justify-content:center;font-size:24px">⚙️</div>
              <div>
                <h2 style="margin:0;font-size:20px;font-weight:800;color:var(--text)">Settings &amp; Account Preferences</h2>
                <p style="margin:3px 0 0;font-size:13px;color:var(--muted)">Manage your profile, display name, security credentials, and platform appearance</p>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:10px">
              <button class="b" type="button" onclick="showContainer('box-home')" style="font-weight:700">← Back to Home</button>
            </div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(360px, 1fr));gap:20px">
          <!-- Card 1: Account Profile & Display Name -->
          <div class="card" style="padding:22px 24px;border:1px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 2px 10px rgba(0,0,0,0.03)">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--line)">
              <div id="settingsPageAvatar" style="width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg, var(--primary), var(--accent));color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px">U</div>
              <div style="flex:1">
                <div id="settingsPageAccountName" style="font-weight:800;font-size:16px;color:var(--text)">Employee</div>
                <div style="font-size:12px;color:var(--muted)">User ID: <b id="settingsPageUserId" style="color:var(--primary)">0001</b> &bull; <span id="settingsPageRole" class="role-pill admin">ADMIN</span></div>
              </div>
            </div>

            <h4 style="margin:0 0 12px;font-size:14px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:8px">
              <span>✏️</span> <span>Update Display Name</span>
            </h4>
            <form id="settingsPageNameForm" onsubmit="event.preventDefault(); submitSettingsPageName();" style="margin:0">
              <div style="margin-bottom:12px">
                <label style="display:block;font-size:12px;font-weight:700;color:var(--text);margin-bottom:4px">Current Name</label>
                <input type="text" id="settingsPageCurrentName" readonly style="width:100%;box-sizing:border-box;background:var(--card-subtle);color:var(--text);font-weight:700;border:1.5px solid var(--line);border-radius:8px;padding:9px 12px;font-size:13.5px" />
              </div>
              <div style="margin-bottom:12px">
                <label style="display:block;font-size:12px;font-weight:700;color:var(--text);margin-bottom:4px">New Display Name <span style="color:var(--danger)">*</span></label>
                <input type="text" id="settingsPageUpdatedName" placeholder="Enter updated name" required style="width:100%;box-sizing:border-box;background:var(--card);color:var(--text);border:1.5px solid var(--line);border-radius:8px;padding:9px 12px;font-size:13.5px" />
              </div>
              <div style="margin-bottom:14px">
                <label style="display:block;font-size:12px;font-weight:700;color:var(--text);margin-bottom:4px">Confirm Name <span style="color:var(--danger)">*</span></label>
                <input type="text" id="settingsPageConfirmName" placeholder="Confirm updated name" required style="width:100%;box-sizing:border-box;background:var(--card);color:var(--text);border:1.5px solid var(--line);border-radius:8px;padding:9px 12px;font-size:13.5px" />
              </div>
              <p class="err" id="settingsPageNameErr" role="alert" style="margin:6px 0 10px;font-size:12px;font-weight:600;color:var(--danger)" hidden></p>
              <button class="b p" type="submit" id="settingsPageNameBtn" style="width:100%;font-weight:700;justify-content:center;height:38px">💾 Save New Display Name</button>
            </form>
          </div>

          <!-- Card 2: Security & Password Management -->
          <div class="card" style="padding:22px 24px;border:1px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 2px 10px rgba(0,0,0,0.03)">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--line)">
              <div style="width:40px;height:40px;border-radius:10px;background:#fef3c7;color:#d97706;display:flex;align-items:center;justify-content:center;font-size:20px">🔑</div>
              <div>
                <h4 style="margin:0;font-size:15px;font-weight:800;color:var(--text)">Login Security &amp; Password</h4>
                <div style="font-size:12px;color:var(--muted)">Update your employee password credentials</div>
              </div>
            </div>

            <form id="settingsPagePwForm" onsubmit="event.preventDefault(); submitSettingsPagePw();" style="margin:0">
              <div style="margin-bottom:12px">
                <label style="display:block;font-size:12px;font-weight:700;color:var(--text);margin-bottom:4px">Current Password <span style="color:var(--danger)">*</span></label>
                <div style="position:relative">
                  <input type="password" id="settingsPageCurPw" placeholder="Enter current password" required style="width:100%;box-sizing:border-box;background:var(--card);color:var(--text);border:1.5px solid var(--line);border-radius:8px;padding:9px 38px 9px 12px;font-size:13.5px" />
                  <button type="button" class="b ghost" style="position:absolute;right:6px;top:50%;transform:translateY(-50%);padding:2px 6px;font-size:13px;border:none;cursor:pointer" onclick="togglePasswordInputVisibility('settingsPageCurPw')">👁️</button>
                </div>
              </div>
              <div style="margin-bottom:12px">
                <label style="display:block;font-size:12px;font-weight:700;color:var(--text);margin-bottom:4px">New Password (min. 8 characters) <span style="color:var(--danger)">*</span></label>
                <div style="position:relative">
                  <input type="password" id="settingsPageNewPw" minlength="8" placeholder="Enter new password" required style="width:100%;box-sizing:border-box;background:var(--card);color:var(--text);border:1.5px solid var(--line);border-radius:8px;padding:9px 38px 9px 12px;font-size:13.5px" />
                  <button type="button" class="b ghost" style="position:absolute;right:6px;top:50%;transform:translateY(-50%);padding:2px 6px;font-size:13px;border:none;cursor:pointer" onclick="togglePasswordInputVisibility('settingsPageNewPw')">👁️</button>
                </div>
              </div>
              <div style="margin-bottom:14px">
                <label style="display:block;font-size:12px;font-weight:700;color:var(--text);margin-bottom:4px">Confirm New Password <span style="color:var(--danger)">*</span></label>
                <div style="position:relative">
                  <input type="password" id="settingsPageConfirmPw" minlength="8" placeholder="Confirm new password" required style="width:100%;box-sizing:border-box;background:var(--card);color:var(--text);border:1.5px solid var(--line);border-radius:8px;padding:9px 38px 9px 12px;font-size:13.5px" />
                  <button type="button" class="b ghost" style="position:absolute;right:6px;top:50%;transform:translateY(-50%);padding:2px 6px;font-size:13px;border:none;cursor:pointer" onclick="togglePasswordInputVisibility('settingsPageConfirmPw')">👁️</button>
                </div>
              </div>
              <p class="err" id="settingsPagePwErr" role="alert" style="margin:6px 0 10px;font-size:12px;font-weight:600;color:var(--danger)" hidden></p>
              <button class="b p" type="submit" id="settingsPagePwBtn" style="width:100%;font-weight:700;justify-content:center;height:38px">🔒 Update Password</button>
            </form>
          </div>

          <!-- Card 3: Theme & Look (7 Palettes + Light/Dark) -->
          <div class="card" style="padding:22px 24px;border:1px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 2px 10px rgba(0,0,0,0.03);grid-column:1/-1">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--line)">
              <div style="display:flex;align-items:center;gap:10px">
                <div style="width:40px;height:40px;border-radius:10px;background:#e0f2fe;color:#0284c7;display:flex;align-items:center;justify-content:center;font-size:20px">🎨</div>
                <div>
                  <h4 style="margin:0;font-size:15px;font-weight:800;color:var(--text)">Theme &amp; Appearance</h4>
                  <div style="font-size:12px;color:var(--muted)">7 Custom curated themes with Light &amp; Dark mode</div>
                </div>
              </div>
              <!-- Light/Dark Mode Switcher -->
              <div style="display:inline-flex;gap:4px;background:var(--bg);padding:4px;border-radius:10px;border:1px solid var(--line)">
                <button type="button" class="theme-mode-btn" data-mode-val="light" id="settingsPageModeLight" style="display:flex;align-items:center;gap:6px;padding:6px 14px;font-size:12.5px;font-weight:700;border-radius:8px;border:1px solid transparent;cursor:pointer">
                  <span>☀️</span> <span>Light Mode</span>
                </button>
                <button type="button" class="theme-mode-btn" data-mode-val="dark" id="settingsPageModeDark" style="display:flex;align-items:center;gap:6px;padding:6px 14px;font-size:12.5px;font-weight:700;border-radius:8px;border:1px solid transparent;cursor:pointer">
                  <span>🌙</span> <span>Dark Mode</span>
                </button>
              </div>
            </div>

            <!-- 7 Themes Palette Grid -->
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:12px">
              <button type="button" class="theme-palette-opt" data-palette-val="royal_navy" style="display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);cursor:pointer;text-align:left;transition:all 0.2s ease">
                <div class="theme-swatch-group" style="display:inline-flex;gap:4px">
                  <span style="width:16px;height:16px;border-radius:50%;background:#0f2b5c;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#d4af37;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#f8fafc;border:1px solid #cbd5e1;display:inline-block"></span>
                </div>
                <div style="flex:1">
                  <div style="font-weight:700;font-size:13px;color:var(--text)">Royal Navy</div>
                  <div style="font-size:11.5px;color:var(--muted)">The default: navy and gold, light page</div>
                </div>
              </button>

              <button type="button" class="theme-palette-opt" data-palette-val="midnight" style="display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);cursor:pointer;text-align:left;transition:all 0.2s ease">
                <div class="theme-swatch-group" style="display:inline-flex;gap:4px">
                  <span style="width:16px;height:16px;border-radius:50%;background:#070d19;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#1e3a8a;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#eab308;display:inline-block"></span>
                </div>
                <div style="flex:1">
                  <div style="font-weight:700;font-size:13px;color:var(--text)">Midnight</div>
                  <div style="font-size:11.5px;color:var(--muted)">Dark navy with soft gold</div>
                </div>
              </button>

              <button type="button" class="theme-palette-opt" data-palette-val="emerald" style="display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);cursor:pointer;text-align:left;transition:all 0.2s ease">
                <div class="theme-swatch-group" style="display:inline-flex;gap:4px">
                  <span style="width:16px;height:16px;border-radius:50%;background:#064e3b;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#059669;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#d4af37;display:inline-block"></span>
                </div>
                <div style="flex:1">
                  <div style="font-weight:700;font-size:13px;color:var(--text)">Emerald</div>
                  <div style="font-size:11.5px;color:var(--muted)">Deep green with gold</div>
                </div>
              </button>

              <button type="button" class="theme-palette-opt" data-palette-val="crimson_vault" style="display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);cursor:pointer;text-align:left;transition:all 0.2s ease">
                <div class="theme-swatch-group" style="display:inline-flex;gap:4px">
                  <span style="width:16px;height:16px;border-radius:50%;background:#881337;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#e11d48;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#d4af37;display:inline-block"></span>
                </div>
                <div style="flex:1">
                  <div style="font-weight:700;font-size:13px;color:var(--text)">Crimson Vault</div>
                  <div style="font-size:11.5px;color:var(--muted)">Wine red, close to your current brand</div>
                </div>
              </button>

              <button type="button" class="theme-palette-opt" data-palette-val="ocean" style="display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);cursor:pointer;text-align:left;transition:all 0.2s ease">
                <div class="theme-swatch-group" style="display:inline-flex;gap:4px">
                  <span style="width:16px;height:16px;border-radius:50%;background:#0f766e;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#0284c7;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#f59e0b;display:inline-block"></span>
                </div>
                <div style="flex:1">
                  <div style="font-weight:700;font-size:13px;color:var(--text)">Ocean</div>
                  <div style="font-size:11.5px;color:var(--muted)">Teal-blue with amber</div>
                </div>
              </button>

              <button type="button" class="theme-palette-opt" data-palette-val="violet" style="display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);cursor:pointer;text-align:left;transition:all 0.2s ease">
                <div class="theme-swatch-group" style="display:inline-flex;gap:4px">
                  <span style="width:16px;height:16px;border-radius:50%;background:#581c87;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#7e22ce;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#d4af37;display:inline-block"></span>
                </div>
                <div style="flex:1">
                  <div style="font-weight:700;font-size:13px;color:var(--text)">Violet</div>
                  <div style="font-size:11.5px;color:var(--muted)">Rich purple with gold</div>
                </div>
              </button>

              <button type="button" class="theme-palette-opt" data-palette-val="sunset" style="display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);cursor:pointer;text-align:left;transition:all 0.2s ease">
                <div class="theme-swatch-group" style="display:inline-flex;gap:4px">
                  <span style="width:16px;height:16px;border-radius:50%;background:#c2410c;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#ea580c;display:inline-block"></span>
                  <span style="width:16px;height:16px;border-radius:50%;background:#f59e0b;display:inline-block"></span>
                </div>
                <div style="flex:1">
                  <div style="font-weight:700;font-size:13px;color:var(--text)">Sunset</div>
                  <div style="font-size:11.5px;color:var(--muted)">Burnt orange and warm amber</div>
                </div>
              </button>
            </div>
          </div>

          <!-- Card 4: Session & Sign Out -->
          <div class="card" style="padding:22px 24px;border:1px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 2px 10px rgba(0,0,0,0.03);grid-column:1/-1">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px">
              <div style="display:flex;align-items:center;gap:12px">
                <div style="width:40px;height:40px;border-radius:10px;background:#fee2e2;color:#dc2626;display:flex;align-items:center;justify-content:center;font-size:20px">🚪</div>
                <div>
                  <div style="font-weight:800;font-size:15px;color:var(--text)">Active Session Management</div>
                  <div style="font-size:12px;color:var(--muted)">End your current authenticated session and securely sign out</div>
                </div>
              </div>
              <button class="b" type="button" onclick="logout(true)" style="background:#dc2626;color:#fff;font-weight:700;border:none;padding:10px 22px;border-radius:10px;cursor:pointer">🚪 Log Out of Device</button>
            </div>
          </div>
        </div>
      </section>
'''

errors_box_end = text.find('</section>', text.find('id="box-errors"')) + 10
text = text[:errors_box_end] + '\n' + box_settings_html + text[errors_box_end:]

# 4. Update sidebarBtnSettings and userAvatarCircle to open box-settings
text = text.replace('<button class="cv-nav-item" id="sidebarBtnSettings" title="User Settings &amp; Theme Options">', '<button class="cv-nav-item" data-target="box-settings" id="sidebarBtnSettings" title="User Settings &amp; Theme Options">')
text = text.replace('onclick="openSettingsModal()"', 'onclick="showContainer(\'box-settings\')"')

# 5. In JS: Update boxToHash & getInitialTargetBox to include box-settings
text = text.replace("'box-health': 'health'", "'box-health': 'health',\n          'box-settings': 'settings'")
text = text.replace("'health': 'box-health'", "'health': 'box-health',\n          'settings': 'box-settings',\n          'box-settings': 'box-settings'")

# 6. In showContainer: Add call to loadSettingsContainer()
text = text.replace("else if (boxId === 'box-bin') { loadCartContainer(); }", "else if (boxId === 'box-bin') { loadCartContainer(); }\n        else if (boxId === 'box-settings') { loadSettingsContainer(); }")

# 7. Add loadSettingsContainer & helper functions in JS
js_settings_code = '''
      async function loadSettingsContainer() {
        const u = getUser();
        const currentName = u.name || u.user_id || 'Employee';
        const uInitial = ((currentName[0] || 'U')[0] || 'U').toUpperCase();

        if ($('settingsPageAccountName')) $('settingsPageAccountName').textContent = currentName;
        if ($('settingsPageCurrentName')) $('settingsPageCurrentName').value = currentName;
        if ($('settingsPageUpdatedName')) $('settingsPageUpdatedName').value = '';
        if ($('settingsPageConfirmName')) $('settingsPageConfirmName').value = '';
        if ($('settingsPageAvatar')) $('settingsPageAvatar').textContent = uInitial;
        if ($('settingsPageUserId')) $('settingsPageUserId').textContent = u.user_id || '0001';
        if ($('settingsPageRole')) {
          const r = myRole();
          $('settingsPageRole').textContent = r.toUpperCase();
          $('settingsPageRole').className = `role-pill ${r}`;
        }
        if ($('settingsPageNameErr')) $('settingsPageNameErr').hidden = true;
        if ($('settingsPagePwErr')) $('settingsPagePwErr').hidden = true;
        if ($('settingsPagePwForm')) $('settingsPagePwForm').reset();

        const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
        const currentMode = localStorage.getItem('valut_theme_mode') || 'light';
        highlightSettingsThemeUI(currentPal, currentMode);
      }

      function highlightSettingsThemeUI(currentPal, currentMode) {
        document.querySelectorAll('#box-settings .theme-palette-opt, #dlgSettings .theme-palette-opt').forEach(btn => {
          const isAct = btn.dataset.paletteVal === currentPal;
          btn.style.borderColor = isAct ? 'var(--primary, #1d68e1)' : 'var(--line)';
          btn.style.background = isAct ? 'rgba(29, 104, 225, 0.08)' : 'var(--card)';
        });
        if ($('settingsPageModeLight')) {
          $('settingsPageModeLight').style.borderColor = currentMode === 'light' ? 'var(--primary, #1d68e1)' : 'transparent';
          $('settingsPageModeLight').style.background = currentMode === 'light' ? 'var(--primary, #1d68e1)' : 'transparent';
          $('settingsPageModeLight').style.color = currentMode === 'light' ? '#fff' : 'var(--text)';
        }
        if ($('settingsPageModeDark')) {
          $('settingsPageModeDark').style.borderColor = currentMode === 'dark' ? 'var(--primary, #1d68e1)' : 'transparent';
          $('settingsPageModeDark').style.background = currentMode === 'dark' ? 'var(--primary, #1d68e1)' : 'transparent';
          $('settingsPageModeDark').style.color = currentMode === 'dark' ? '#fff' : 'var(--text)';
        }
      }

      async function submitSettingsPageName() {
        const errEl = $('settingsPageNameErr');
        const currentName = ($('settingsPageCurrentName')?.value || '').trim();
        const updatedName = ($('settingsPageUpdatedName')?.value || '').trim();
        const confirmName = ($('settingsPageConfirmName')?.value || '').trim();

        if (errEl) { errEl.textContent = ''; errEl.hidden = true; }

        if (!updatedName) {
          if (errEl) { errEl.textContent = 'Please enter an updated display name.'; errEl.hidden = false; }
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

        const btn = $('settingsPageNameBtn');
        if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }

        try {
          const res = await api('/api/me/name', {
            method: 'PUT',
            body: JSON.stringify({
              name: updatedName,
              confirm_name: confirmName,
              confirm_current_name: currentName
            })
          });
          const finalName = res.name || updatedName;

          const u = getUser();
          u.name = finalName;
          localStorage.setItem('user', JSON.stringify(u));

          // Immediate UI reflections
          if ($('hi')) {
            const h = new Date().getHours();
            $('hi').textContent = `Good ${h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening'}, ${finalName}`;
          }
          const uInitial = ((finalName[0] || 'U')[0] || 'U').toUpperCase();
          if ($('userAvatarCircle')) $('userAvatarCircle').textContent = uInitial;
          if ($('settingsPageAvatar')) $('settingsPageAvatar').textContent = uInitial;
          if ($('settingsPageAccountName')) $('settingsPageAccountName').textContent = finalName;
          if ($('settingsPageCurrentName')) $('settingsPageCurrentName').value = finalName;
          if ($('settingsAccountName')) $('settingsAccountName').textContent = finalName;
          if ($('settingsUserAvatarCircle')) $('settingsUserAvatarCircle').textContent = uInitial;
          if ($('editNameCurrent')) $('editNameCurrent').value = finalName;

          toast(`Display name successfully updated to "${finalName}" in database!`);
        } catch (err) {
          if (errEl) {
            errEl.textContent = err.message || 'Failed to update display name.';
            errEl.hidden = false;
          }
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = '💾 Save New Display Name'; }
        }
      }

      async function submitSettingsPagePw() {
        const pe = $('settingsPagePwErr');
        if (pe) { pe.textContent = ''; pe.hidden = true; }
        const curPw = $('settingsPageCurPw')?.value || '';
        const newPw = $('settingsPageNewPw')?.value || '';
        const repPw = $('settingsPageConfirmPw')?.value || '';

        if (!curPw) {
          if (pe) { pe.textContent = 'Please enter your current registered password.'; pe.hidden = false; }
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

        const btn = $('settingsPagePwBtn');
        if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; }

        try {
          const r = await api('/api/me/password', {
            method: 'POST',
            body: JSON.stringify({ current_password: curPw, new_password: newPw })
          });

          if (r && r.access_token) {
            tok = r.access_token;
            localStorage.setItem('token', tok);
          }

          if ($('settingsPagePwForm')) $('settingsPagePwForm').reset();
          toast('Password successfully updated and encrypted in database!');
        } catch (err) {
          if (pe) {
            pe.textContent = err.message || 'Failed to update password.';
            pe.hidden = false;
          }
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = '🔒 Update Password'; }
        }
      }
'''

# Insert js_settings_code right before function openSettingsModal
open_settings_idx = text.find('function openSettingsModal() {')
assert open_settings_idx != -1, "openSettingsModal not found"
text = text[:open_settings_idx] + js_settings_code + '\n      ' + text[open_settings_idx:]

# Hook settingsPage buttons
hook_marker = "if ($('sidebarBtnSettings')) $('sidebarBtnSettings').onclick = openSettingsModal;"
hook_replacement = """if ($('sidebarBtnSettings')) $('sidebarBtnSettings').onclick = () => showContainer('box-settings');
      if ($('settingsPageModeLight')) {
        $('settingsPageModeLight').onclick = () => {
          const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
          applyTheme(currentPal, 'light', true);
          highlightSettingsThemeUI(currentPal, 'light');
        };
      }
      if ($('settingsPageModeDark')) {
        $('settingsPageModeDark').onclick = () => {
          const currentPal = localStorage.getItem('valut_palette') || 'royal_navy';
          applyTheme(currentPal, 'dark', true);
          highlightSettingsThemeUI(currentPal, 'dark');
        };
      }
      document.querySelectorAll('#box-settings .theme-palette-opt').forEach(btn => {
        btn.onclick = () => {
          const pal = btn.dataset.paletteVal;
          const currentMode = localStorage.getItem('valut_theme_mode') || 'light';
          applyTheme(pal, currentMode, true);
          highlightSettingsThemeUI(pal, currentMode);
          toast(`Applied theme: ${btn.querySelector('div[style*="font-weight:700"]')?.textContent || pal}`);
        };
      });"""

text = text.replace(hook_marker, hook_replacement, 1)

# Write to frontend/index.html
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

# Write identical copy to frontend/dashboard.html
with open('frontend/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied container isolation and settings page to index.html and dashboard.html successfully!")

