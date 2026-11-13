import re, os, subprocess

# 1. Read master template from HEAD to get pristine scripts, styles, and markup
master_head = subprocess.check_output(["git", "show", "HEAD:frontend/index.html"], encoding="utf-8", errors="ignore")

# 2. Extract containers from their dedicated files
files_map = {
    'box-inv': 'frontend/inventory.html',
    'box-sim': 'frontend/sim-upload.html',
    'box-fetch': 'frontend/fetch-data.html',
    'box-edit': 'frontend/edit-delete.html',
    'box-exp': 'frontend/alerts.html',
    'box-errors': 'frontend/errors.html'
}

containers = {}
for box_id, fpath in files_map.items():
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'(<section\s+[^>]*id="' + box_id + r'"[\s\S]*?</section>)', content)
    assert m, f"Failed to extract {box_id} from {fpath}"
    c = m.group(1)
    c = re.sub(r'(;\s*display:block;)+', '', c)
    c = re.sub(r'class="container-box[^"]*"', 'class="container-box active"', c, count=1)
    m_sec = re.match(r'<section\s+([^>]*)>', c)
    if m_sec:
        sec_tag = m_sec.group(0)
        if 'style="' in sec_tag:
            new_sec = re.sub(r'style="([^"]*)"', r'style="\1; display:block;"', sec_tag)
        else:
            new_sec = sec_tag[:-1] + ' style="display:block;">'
        c = new_sec + c[m_sec.end():]
    containers[box_id] = c

# Settings container for settings.html
containers['box-settings'] = """
      <!-- =========================================================================
         CONTAINER: SETTINGS (User Profile, Themes, Manage Users & Login Inventory)
         ========================================================================= -->
      <section class="container-box active" id="box-settings" style="display:block;padding:0;background:transparent;border:none;box-shadow:none">
        
        <!-- User Profile & Account Data Container -->
        <div class="card" id="settingsUserCard" style="padding:28px;border-radius:18px;border:1px solid var(--line);background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:24px">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:20px;border-bottom:1px solid var(--line);padding-bottom:18px">
            <div style="display:flex;align-items:center;gap:16px">
              <div id="settingsUserAvatar" style="width:58px;height:58px;border-radius:50%;background:linear-gradient(135deg, var(--primary, #1d68e1), var(--accent, #fca311));color:#fff;font-size:24px;font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,0.15)">
                S
              </div>
              <div>
                <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                  <h2 id="settingsUserName" style="margin:0;font-size:22px;font-weight:800;color:var(--text)">Loading User Data…</h2>
                  <span id="settingsUserBadge" class="role-pill admin" style="font-size:12px;padding:3px 10px;border-radius:99px;font-weight:700">👑 Super Admin</span>
                </div>
                <p id="settingsUserCategory" style="margin:4px 0 0;font-size:13px;color:var(--muted);font-weight:600">Master Super Admin • User ID: <span id="settingsUserId">0001</span></p>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
              <button type="button" class="b" onclick="openEditNameModal()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">✏️ Edit Name</button>
              <button type="button" class="b" onclick="openChangePasswordModal()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🔑 Edit Password</button>
              <button type="button" class="b" id="settingsBtnManageUsers" onclick="scrollToManageUsers()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">👥 Manage Users</button>
              <button type="button" class="b" id="settingsBtnLoginInventory" onclick="scrollToLoginInventory()" style="font-weight:700;padding:8px 14px;border-radius:9px;font-size:13px">🕘 Login Inventory</button>
            </div>
          </div>

          <h3 style="margin:0 0 14px;font-size:15px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:8px">
            <span>📋</span> <span>Account Details &amp; Permissions</span>
          </h3>
          
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:14px;margin-bottom:20px">
            <div style="padding:14px 16px;background:var(--card-subtle);border:1px solid var(--line);border-radius:12px">
              <span style="display:block;font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:0.5px">User ID</span>
              <b id="settingsDetailUserId" style="font-size:15px;color:var(--text)">0001</b>
            </div>
            <div style="padding:14px 16px;background:var(--card-subtle);border:1px solid var(--line);border-radius:12px">
              <span style="display:block;font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:0.5px">System Role</span>
              <b id="settingsDetailRole" style="font-size:15px;color:var(--text)">Admin (Full Access)</b>
            </div>
            <div style="padding:14px 16px;background:var(--card-subtle);border:1px solid var(--line);border-radius:12px">
              <span style="display:block;font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:0.5px">Account Status</span>
              <b style="font-size:15px;color:var(--ok)">● Active &amp; Authenticated</b>
            </div>
            <div style="padding:14px 16px;background:var(--card-subtle);border:1px solid var(--line);border-radius:12px">
              <span style="display:block;font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:0.5px">Previous Name</span>
              <b id="settingsDetailPrevName" style="font-size:15px;color:var(--text)">None</b>
            </div>
          </div>

          <span style="display:block;font-size:12px;color:var(--muted);font-weight:700;text-transform:uppercase;margin-bottom:8px">Authorized Privileges</span>
          <div id="settingsPermissionsWrap" style="display:flex;flex-wrap:wrap;gap:8px">
            <span class="badge" style="padding:4px 10px;background:var(--card-subtle);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:600">👥 Customer Inventory</span>
            <span class="badge" style="padding:4px 10px;background:var(--card-subtle);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:600">📱 SIM Data Upload</span>
            <span class="badge" style="padding:4px 10px;background:var(--card-subtle);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:600">🔍 Fetch Data</span>
            <span class="badge" style="padding:4px 10px;background:var(--card-subtle);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:600">✏️ Edit / Delete by IMEI</span>
            <span class="badge" style="padding:4px 10px;background:var(--card-subtle);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:600">⚠️ Expiry Alerts</span>
            <span class="badge" style="padding:4px 10px;background:var(--card-subtle);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:600">📊 Data Health Report</span>
            <span class="badge" style="padding:4px 10px;background:var(--card-subtle);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:600">🚨 Errored Entries</span>
            <span class="badge" style="padding:4px 10px;background:var(--card-subtle);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:600">👥 User Management</span>
          </div>
        </div>

        <!-- Themes Container Option -->
        <div class="card" id="settingsThemesCard" style="padding:28px;border-radius:18px;border:1px solid var(--line);background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:24px">
          <div style="margin-bottom:22px;border-bottom:1px solid var(--line);padding-bottom:16px">
            <h2 style="margin:0 0 6px;font-size:20px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
              <span>🎨</span> <span>Themes &amp; Appearance</span>
            </h2>
            <p style="margin:0;font-size:13.5px;color:var(--muted)">Select your preferred theme and display mode. Light mode is default. Click <b>Apply Theme</b> to replicate the theme across the website.</p>
          </div>

          <!-- Mode Toggle Pill: Light Mode (Default) vs Dark Mode -->
          <div style="display:inline-flex;align-items:center;gap:4px;padding:4px;background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;margin-bottom:24px">
            <label id="lblModeLight" style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:8px;cursor:pointer;font-weight:700;font-size:13px;background:var(--primary, #1d68e1);color:#fff;transition:all 0.2s">
              <input type="radio" name="themeModeChoice" id="modeRadioLight" value="light" checked onchange="previewThemeSelection()" style="display:none" />
              <span>☀️</span> <span>Light Mode (Default)</span>
            </label>
            <label id="lblModeDark" style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:8px;cursor:pointer;font-weight:700;font-size:13px;color:var(--text);transition:all 0.2s">
              <input type="radio" name="themeModeChoice" id="modeRadioDark" value="dark" onchange="previewThemeSelection()" style="display:none" />
              <span>🌙</span> <span>Dark Mode</span>
            </label>
          </div>

          <!-- 4 Curated Themes Grid -->
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));gap:16px;margin-bottom:24px">
            
            <!-- 1. Royal Navy -->
            <label class="theme-card-option" id="cardThemeRoyalNavy" data-palette="royal_navy" style="display:block;padding:18px;border-radius:14px;border:2px solid var(--primary, #1d68e1);background:rgba(29, 104, 225, 0.08);cursor:pointer;transition:all 0.2s">
              <input type="radio" name="paletteChoice" value="royal_navy" checked onchange="previewThemeSelection()" style="display:none" />
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
                <span style="font-weight:800;font-size:15px;color:var(--text)">👑 Royal Navy</span>
                <span class="badge primary" style="font-size:11px;padding:2px 8px;border-radius:6px">Default</span>
              </div>
              <div style="display:flex;gap:8px;margin-bottom:10px">
                <span style="width:28px;height:28px;border-radius:50%;background:#0f2b5c;display:inline-block;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.15)"></span>
                <span style="width:28px;height:28px;border-radius:50%;background:#d4af37;display:inline-block;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.15)"></span>
              </div>
              <p style="margin:0;font-size:12px;color:var(--muted)">Deep navy blue base with elegant royal gold accents.</p>
            </label>

            <!-- 2. Midnight Slate -->
            <label class="theme-card-option" id="cardThemeMidnight" data-palette="midnight" style="display:block;padding:18px;border-radius:14px;border:1px solid var(--line);background:var(--card);cursor:pointer;transition:all 0.2s">
              <input type="radio" name="paletteChoice" value="midnight" onchange="previewThemeSelection()" style="display:none" />
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
                <span style="font-weight:800;font-size:15px;color:var(--text)">🌌 Midnight Slate</span>
              </div>
              <div style="display:flex;gap:8px;margin-bottom:10px">
                <span style="width:28px;height:28px;border-radius:50%;background:#0f1a2e;display:inline-block;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.15)"></span>
                <span style="width:28px;height:28px;border-radius:50%;background:#38bdf8;display:inline-block;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.15)"></span>
              </div>
              <p style="margin:0;font-size:12px;color:var(--muted)">Sleek dark obsidian slate with electric cyan highlights.</p>
            </label>

            <!-- 3. Emerald Forest -->
            <label class="theme-card-option" id="cardThemeEmerald" data-palette="emerald" style="display:block;padding:18px;border-radius:14px;border:1px solid var(--line);background:var(--card);cursor:pointer;transition:all 0.2s">
              <input type="radio" name="paletteChoice" value="emerald" onchange="previewThemeSelection()" style="display:none" />
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
                <span style="font-weight:800;font-size:15px;color:var(--text)">🌲 Emerald Forest</span>
              </div>
              <div style="display:flex;gap:8px;margin-bottom:10px">
                <span style="width:28px;height:28px;border-radius:50%;background:#064e3b;display:inline-block;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.15)"></span>
                <span style="width:28px;height:28px;border-radius:50%;background:#10b981;display:inline-block;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.15)"></span>
              </div>
              <p style="margin:0;font-size:12px;color:var(--muted)">Rich emerald green base with vibrant mint accents.</p>
            </label>

            <!-- 4. Crimson Vault -->
            <label class="theme-card-option" id="cardThemeCrimsonVault" data-palette="crimson_vault" style="display:block;padding:18px;border-radius:14px;border:1px solid var(--line);background:var(--card);cursor:pointer;transition:all 0.2s">
              <input type="radio" name="paletteChoice" value="crimson_vault" onchange="previewThemeSelection()" style="display:none" />
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
                <span style="font-weight:800;font-size:15px;color:var(--text)">🍷 Crimson Vault</span>
              </div>
              <div style="display:flex;gap:8px;margin-bottom:10px">
                <span style="width:28px;height:28px;border-radius:50%;background:#4c0519;display:inline-block;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.15)"></span>
                <span style="width:28px;height:28px;border-radius:50%;background:#f43f5e;display:inline-block;border:2px solid #fff;box-shadow:0 2px 5px rgba(0,0,0,0.15)"></span>
              </div>
              <p style="margin:0;font-size:12px;color:var(--muted)">Deep burgundy wine with luxury rose red highlights.</p>
            </label>

          </div>

          <!-- Submit Button and Live Confirmation Notice -->
          <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
            <button type="button" id="btnSubmitTheme" onclick="submitThemeSelection()" style="padding:12px 28px;font-size:14px;font-weight:800;border-radius:10px;background:var(--primary, #1d68e1);color:#ffffff;border:none;cursor:pointer;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 10px rgba(0,0,0,0.12)">
              <span>🎨</span> <span>Apply Theme</span>
            </button>
            <div id="themeSubmitMsg" style="display:none;padding:10px 18px;border-radius:10px;font-weight:700;font-size:13.5px;align-items:center;gap:8px"></div>
          </div>
        </div>

        <!-- Manage Users Container (Merged from Home Overview into Settings) -->
        <div class="card" id="settingsManageUsersCard" style="padding:28px;border-radius:18px;border:1px solid var(--line);background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:24px">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:20px;border-bottom:1px solid var(--line);padding-bottom:16px">
            <div>
              <h2 style="margin:0 0 6px;font-size:20px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
                <span>👥</span> <span>Manage Users &amp; Permissions</span>
              </h2>
              <p style="margin:0;font-size:13.5px;color:var(--muted)">Provision employee accounts, assign administrative roles (Admin, Standard, Limited), or configure system privileges.</p>
            </div>
            <button type="button" class="b" onclick="openManageUsersModal()" style="font-weight:700;padding:8px 16px;border-radius:9px;font-size:13px">⛶ Open in Modal</button>
          </div>

          <!-- Add New Employee Account Box -->
          <div class="card" style="padding:18px 20px;border:1px solid var(--line);margin-bottom:20px;background:var(--card-subtle);border-radius:14px">
            <h4 style="margin:0 0 12px;font-size:14.5px;font-weight:800;color:var(--text)">➕ Add New Employee Account</h4>
            <div class="form-grid" style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px">
              <div><label for="un">Full Name *</label><input id="un" placeholder="Jane Doe" required /></div>
              <div><label for="ui">Login ID *</label><input id="ui" placeholder="e.g. 0002, 0005, 1024" autocapitalize="none" autocomplete="off" required /></div>
              <div><label for="up">Initial Password * (8+ chars)</label><input id="up" type="password" autocomplete="new-password" placeholder="Min 8 characters" required /></div>
              <div>
                <label for="ur2">Assigned Role</label>
                <select id="ur2" title="Select assigned employee role tier">
                  <option value="master_admin" selected>⭐ Master Admin (Default)</option>
                  <option value="admin_user">🛡️ Regular Admin</option>
                  <option value="regular_user">👤 Regular User</option>
                  <option value="super_admin" id="optSuperAdminRole">👑 Super Admin</option>
                </select>
              </div>
            </div>
            <div id="roleTierBadge" style="margin:8px 0;font-size:12px;font-weight:600;color:var(--primary)"></div>
            <p class="sub" style="margin:8px 0 14px;font-size:12px;color:var(--muted);line-height:1.5">
              💡 <b>Role Matrix:</b><br />
              • <code>0001, 0007</code> = <b>Super Administrators:</b> Full unrestricted access; can delete users.<br />
              • <code>0002–0004</code> = <b>Master Admins:</b> Full control; can delete regular users &amp; admins; cannot delete 0001–0004, 0007.<br />
              • <code>0005, 0006, 0008–0010</code> = <b>Admin Users:</b> Full entry &amp; data management; can delete admin users &amp; regular users.<br />
              • <code>After 0010</code> = <b>Regular Users:</b> Upload data, fetch/view entries, and edit entries.
            </p>
            <div style="display:flex;justify-content:flex-end">
              <button class="b p" id="uadd" type="button" style="font-weight:700;padding:8px 20px;border-radius:9px">Create Employee User</button>
            </div>
          </div>

          <!-- Active Users Directory Table -->
          <div style="margin-top:16px">
            <h4 style="margin:0 0 12px;font-size:14.5px;font-weight:800;color:var(--text)">📋 Active System Accounts &amp; Access Tiers</h4>
            <div id="usersTableWrap">
              <div class="empty">Loading employees…</div>
            </div>
          </div>
        </div>

        <!-- Login Inventory & Activity Audit Trail Container (Merged from Home Overview into Settings) -->
        <div class="card" id="settingsLoginInventoryCard" style="padding:28px;border-radius:18px;border:1px solid var(--line);background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:24px">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:20px;border-bottom:1px solid var(--line);padding-bottom:16px">
            <div>
              <h2 style="margin:0 0 6px;font-size:20px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
                <span>📜</span> <span>Login Inventory &amp; Activity Audit Trail</span>
              </h2>
              <p style="margin:0;font-size:13.5px;color:var(--muted)">Enterprise audit log of all employee actions, sign-ins, failed attempts, and data updates.</p>
            </div>
            <button type="button" class="b" onclick="openAuditLogModal()" style="font-weight:700;padding:8px 16px;border-radius:9px;font-size:13px">⛶ Open in Modal</button>
          </div>

          <!-- Real-Time Activity KPI Summary Ribbon -->
          <div class="stats" id="lsum" style="margin-top:0;margin-bottom:20px"></div>

          <!-- Event Filters and Search Controls -->
          <div class="row" style="margin-bottom:16px;gap:12px;flex-wrap:wrap">
            <div style="min-width:180px">
              <label for="lk">Action Type</label>
              <select id="lk">
                <option value="all">All Events</option>
                <option value="signins">Sign-ins Only</option>
                <option value="failed">Failed Sign-ins</option>
                <option value="changes">Data Modifications</option>
              </select>
            </div>
            <div id="empFilterWrap" style="min-width:180px">
              <label for="lw">Employee</label>
              <select id="lw">
                <option value="">All Employees</option>
              </select>
            </div>
            <div class="grow" style="min-width:200px">
              <label for="lq">Search Audit Trail</label>
              <input id="lq" placeholder="Search actions, IP address, device IMEI, or user…" />
            </div>
            <button class="b" id="lc" type="button" style="margin-top:auto">Clear</button>
            <button class="b" id="btnAuditExport" type="button" onclick="exportAuditLogCSV()" style="margin-top:auto">📥 Export CSV</button>
          </div>

          <!-- Audit Log Table Container -->
          <div id="ltbl">
            <div class="empty">Loading login inventory records…</div>
          </div>
        </div>

      </section>
"""

containers['box-home'] = """
      <!-- =========================================================================
         CONTAINER: HOME OVERVIEW (Live Updates & Real-Time Telemetry + Data Health Report)
         ========================================================================= -->
      <section class="container-box active" id="box-home" style="display:block;padding:0;background:transparent;border:none;box-shadow:none">
        
        <!-- Live Updates & Real-Time Telemetry Container -->
        <div class="card" id="homeLiveUpdateCard" style="margin-bottom:24px;padding:22px 24px;border:1px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 4px 20px rgba(0,0,0,0.03)">
          <div class="container-tag" style="display:inline-flex;margin-bottom:12px">⚡ Live Telemetry &amp; Real-Time Intelligence Container</div>
          
          <!-- Live Updates Control Bar -->
          <div class="live-ctrl-card" style="margin-bottom:18px">
            <div class="live-ctrl-left">
              <span class="live-badge"><span class="live-dot"></span> LIVE DATA STREAM</span>
              <button class="b on" id="toggleLive">🟢 Live Updates: ON</button>
              <div style="display:inline-flex;align-items:center;gap:6px">
                <label style="margin:0;font-size:12px;color:var(--muted)">Frequency:</label>
                <select id="liveIntervalSel" style="height:34px;width:auto;padding:0 8px;font-size:12px">
                  <option value="5">Every 5s</option>
                  <option value="10" selected>Every 10s</option>
                  <option value="30">Every 30s</option>
                  <option value="60">Every 60s</option>
                </select>
              </div>
            </div>
            <div class="live-ctrl-right">
              <span style="font-size:12px;color:var(--muted);font-weight:700" id="liveTime"></span>
              <button class="b" id="manualLiveRefresh">⚡ Refresh Now</button>
            </div>
          </div>

          <!-- Live Telemetry KPI Metrics -->
          <div class="stats" id="liveKpis" style="margin-top:0;margin-bottom:18px">
            <div class="card stat"><b>…</b><span>Total Live Devices</span></div>
            <div class="card stat"><b>…</b><span>Active Customers</span></div>
            <div class="card stat" style="border-left-color:var(--warn)"><b>…</b><span>Expiring in 30 Days</span></div>
            <div class="card stat" style="border-left-color:var(--danger)"><b>…</b><span>Expired Devices</span></div>
            <div class="card stat" style="border-left-color:var(--ok)"><b>…</b><span>Data Health Score</span></div>
          </div>

          <!-- Live Master Device Feed -->
          <div class="card" style="padding:20px;border:1px solid var(--line);margin-bottom:20px;background:var(--card-subtle)">
            <div class="row" style="margin-bottom:8px">
              <div class="grow">
                <h3 style="margin:0">📱 Live Master Device Stream</h3>
                <span style="font-size:13px;color:var(--muted)">Live incoming records and statuses across all customer accounts.</span>
              </div>
              <button class="b" id="liveExportExcel">📥 Export to Excel</button>
            </div>

            <div class="row" style="margin-top:12px">
              <div style="min-width:180px">
                <label for="liveCustFilter">Filter Customer</label>
                <select id="liveCustFilter">
                  <option value="">All Customers</option>
                </select>
              </div>
              <div style="min-width:150px">
                <label for="liveFieldFilter">Search Column</label>
                <select id="liveFieldFilter">
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
              <div class="grow">
                <label for="liveSearchInput">Instant Live Search</label>
                <input id="liveSearchInput" placeholder="Search across records in real-time…" autocomplete="off" />
              </div>
              <button class="b" id="liveSearchClear" style="margin-top:auto">Clear</button>
            </div>

            <div id="liveMasterTable">
              <div class="empty">Loading master feed…</div>
            </div>
          </div>

          <!-- Live Telemetry Activity Stream -->
          <div class="card" style="padding:20px;border:1px solid var(--line);background:var(--card-subtle)">
            <h3 style="margin:0 0 6px">📡 Real-Time Audit Activity Telemetry</h3>
            <span style="font-size:13px;color:var(--muted)">Real-time telemetry stream of user actions, sign-ins, and modifications.</span>
            <div id="liveActivityBody" style="margin-top:14px">
              <div class="empty">Streaming audit telemetry…</div>
            </div>
          </div>
        </div>

        <!-- Data Health & Integrity Monitor Card (Embedded inside Home Overview) -->
        <div class="card" id="homeDataHealthCard" style="margin-bottom:24px;padding:22px 24px;border:1px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 4px 20px rgba(0,0,0,0.03)">
          <div class="row" style="margin-bottom:14px;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
            <div class="grow">
              <h3 style="margin:0 0 4px;font-size:16px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:8px">
                <span>🩺</span> <span>Data Health &amp; Integrity Report</span>
              </h3>
              <p class="sub" style="margin:0;font-size:12.5px">Automated diagnostics: duplicate detection, IMEI length validation, invalid date checks, and column completeness scores.</p>
            </div>
            <button class="b" id="liveDownloadHealth" type="button" style="font-weight:700">📥 Download Health Issues Excel</button>
          </div>
          <div id="healthContainerBody">
            <div class="empty">Running health diagnostics…</div>
          </div>
        </div>

      </section>
"""

# 3. Extract Common Shell Head, Home Top Elements
anti_flicker_script = """<script>
    (function() {
      try {
        var m = localStorage.getItem('valut_theme_mode') || localStorage.getItem('theme') || 'light';
        var p = localStorage.getItem('valut_palette') || 'royal_navy';
        document.documentElement.setAttribute('data-theme', m);
        document.documentElement.setAttribute('data-mode', m);
        document.documentElement.setAttribute('data-palette', p);
      } catch(e) {}
    })();
  </script>
  <style>"""
pos_main = master_head.find('<main class="cv-main-panel"')
pos_main_tag_end = master_head.find('>', pos_main) + 1
common_head = master_head[:pos_main_tag_end].replace('<style>', anti_flicker_script, 1)

# Ensure body has class="app-active" so dashboard shell and sidebar are visible immediately
common_head = re.sub(r'<body\b[^>]*>', '<body class="app-active">', common_head, count=1)

# Extract and clean sidebar in common_head
# Requirement: "and also in this delete data health name" -> Removed Data Health link from sidebar navigation menu!
old_sidebar_match = re.search(r'<aside class="cv-sidebar"[\s\S]*?</aside>', common_head)
assert old_sidebar_match, "cvSidebar not found in common_head"

new_sidebar_template = """<aside class="cv-sidebar" id="cvSidebar">
      <div class="cv-sidebar-brand">
        <div class="cv-brand-icon">B</div>
        <div class="cv-brand-text">
          <div class="cv-brand-title">BSTPL CustomerVault</div>
          <div class="cv-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>
        </div>
      </div>

      <nav class="cv-sidebar-menu">
        <a class="cv-nav-item {{NAV_HOME}}" href="home.html" title="Home Overview &amp; Live Updates" style="text-decoration:none">
          <span class="cv-nav-ico">🏠</span>
          <span class="cv-nav-label">Home Overview</span>
        </a>
        <a class="cv-nav-item {{NAV_INV}}" href="inventory.html" title="Customer Inventory" style="text-decoration:none">
          <span class="cv-nav-ico">📇</span>
          <span class="cv-nav-label">Customer Inventory</span>
        </a>
        <a class="cv-nav-item {{NAV_SIM}}" href="sim-upload.html" title="SIM Data Upload" style="text-decoration:none">
          <span class="cv-nav-ico">📱</span>
          <span class="cv-nav-label">SIM Data Upload</span>
        </a>
        <a class="cv-nav-item {{NAV_FETCH}}" href="fetch-data.html" title="Fetch Data" style="text-decoration:none">
          <span class="cv-nav-ico">🔍</span>
          <span class="cv-nav-label">Fetch Data</span>
        </a>
        <a class="cv-nav-item {{NAV_EDIT}}" href="edit-delete.html" title="Edit / Delete by IMEI" style="text-decoration:none">
          <span class="cv-nav-ico">✏️</span>
          <span class="cv-nav-label">Edit / Delete by IMEI</span>
        </a>
        <a class="cv-nav-item {{NAV_ALERTS}}" href="alerts.html" id="sidebarBtnAlerts" title="SIM Expiry Alerts" style="text-decoration:none">
          <div style="display:flex;align-items:center;gap:12px">
            <span class="cv-nav-ico">⚠️</span>
            <span class="cv-nav-label">Expiry Alerts</span>
          </div>
          <span class="cv-live-badge" style="margin-left:auto;background:rgba(245,158,11,0.2);color:#f59e0b;border:1px solid rgba(245,158,11,0.4)">ALERTS</span>
        </a>
        <a class="cv-nav-item {{NAV_ERRORS}}" href="errors.html" id="sidebarBtnErrors" title="Errored Entries &amp; Corrections" style="text-decoration:none">
          <span class="cv-nav-ico">🚨</span>
          <span class="cv-nav-label">Errored Entries</span>
          <span class="badge danger" id="sidebarErrorsBadge" style="margin-left:auto;background:#ef4444;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;font-weight:800">2055</span>
        </a>
        <a class="cv-nav-item {{NAV_SETTINGS}}" href="settings.html" id="sidebarBtnSettings" title="User Settings &amp; Preferences" style="text-decoration:none">
          <span class="cv-nav-ico">⚙️</span>
          <span class="cv-nav-label">Settings</span>
        </a>
      </nav>

      <!-- Live Telemetry Widget in Left Sidebar (Pre-rendered live numbers matching user requirements) -->
      <div class="cv-sidebar-live-widget" id="sidebarLiveWidget">
        <div class="cv-sb-live-top">
          <div style="display:flex;align-items:center;gap:6px">
            <span class="cv-live-dot-pulse"></span>
            <span style="font-size:11px;font-weight:800;letter-spacing:0.8px;color:#38bdf8;text-transform:uppercase">Live Stream</span>
          </div>
          <button type="button" class="cv-sb-toggle-btn on" id="sidebarToggleLiveBtn" title="Toggle Live Streaming">ON</button>
        </div>
        <div class="cv-sb-live-metrics">
          <div class="cv-sb-metric-item">
            <span class="cv-sb-metric-val" id="sbLiveDevCount">117,783</span>
            <span class="cv-sb-metric-lbl">Devices</span>
          </div>
          <div class="cv-sb-metric-item">
            <span class="cv-sb-metric-val" id="sbLiveCustCount">154</span>
            <span class="cv-sb-metric-lbl">Customers</span>
          </div>
        </div>
        <div class="cv-sb-live-foot" id="sbLiveTime">Live • Streaming active</div>
      </div>
      </div>
    </aside>"""

common_head = common_head[:old_sidebar_match.start()] + new_sidebar_template + common_head[old_sidebar_match.end():]

# Clean CSS references to dlgSettings in common_head
common_head = re.sub(r'/\*\s*Settings\s*Modal\s*Specifics\s*\*\/[\s\S]*?#dlgSettings::backdrop\s*\{[\s\S]*?\}', '', common_head)

# Ensure #dashboardWrap is flex
common_head = common_head.replace('id="dashboardWrap" class="cv-app-shell" style="display:none"', 'id="dashboardWrap" class="cv-app-shell" style="display:flex"')

# Build Home Top Elements (Header with greeting & actions, SIM Expiry Alert, 4 Stat Metric Cards)
pos_home_hd = master_head.find('id="box-home"')
pos_sec_start = master_head.rfind('<!-- =========================================================================', 0, pos_home_hd)
raw_home_top = master_head[pos_main_tag_end:pos_sec_start]
home_top_elements = raw_home_top

# Completely remove #mainTabs horizontal action tab bar
home_top_elements = re.sub(r'<!--\s*Quick\s*Action\s*Navigation\s*Tabs\s*-->\s*<nav\s+class="[^"]*cv-action-tabs[^"]*"\s+id="mainTabs"[\s\S]*?</nav>', '', home_top_elements)
home_top_elements = re.sub(r'<nav\s+class="[^"]*cv-action-tabs[^"]*"\s+id="mainTabs"[\s\S]*?</nav>', '', home_top_elements)

# Add Good Morning Greeting Container with Edit Name, Edit Password & Logout
old_hdr_match = re.search(r'(<div style="display:flex;align-items:center;gap:12px;margin-left:auto;flex-wrap:nowrap">[\s\S]*?</header>)', home_top_elements)
if not old_hdr_match:
    old_hdr_match = re.search(r'(<!--\s*Right Side:[\s\S]*?</header>)', home_top_elements)
assert old_hdr_match, "Right side greeting in header not found!"

new_hdr_right = """<!-- Right Side: Good Morning Greeting Container with Edit Name, Edit Password & Logout (Manage Users & Login Inventory merged into Settings) -->
          <div class="user-greeting-wrap" style="display:flex;align-items:center;gap:8px;margin-left:auto;flex-wrap:wrap">
            <div class="user-badge" id="uBadge" style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;background:var(--card-subtle);border:1px solid var(--line);border-radius:99px;font-weight:700;font-size:13.5px">
              <span id="hi">Good afternoon, Shilish Reddy</span>
              <span class="role-pill admin" id="rolePill">ADMIN</span>
            </div>
            <button class="b" id="bEditMyName" type="button" title="Change your account display name" onclick="openEditNameModal()" style="font-weight:700;padding:6px 12px;font-size:13px;border-radius:8px">✏️ Edit Name</button>
            <button class="b" id="bPw" type="button" title="Update your login security password" onclick="openChangePasswordModal()" style="font-weight:700;padding:6px 12px;font-size:13px;border-radius:8px">🔑 Edit Password</button>
            <div class="cv-avatar-circle" id="userAvatarCircle" title="User Settings &amp; Preferences" onclick="location.href='settings.html'" style="cursor:pointer">S</div>
            <button class="b b-logout" id="bLo" type="button" onclick="logout(true)" title="Sign out of your session" style="font-weight:700;padding:6px 14px;border-radius:8px">Logout</button>
          </div>
        </div>
      </header>"""
home_top_elements = home_top_elements[:old_hdr_match.start()] + new_hdr_right + home_top_elements[old_hdr_match.end():]

# Pre-render 4 Stat Metric Cards with user-requested labels (Total Customers, Total Entries, Inserted By You, Unique Columns)
new_stats_ribbon = """<!-- 4 Stat Metric Cards (Home Webpage Only: Total Customers, Total Entries, Inserted By You, Unique Columns) -->
      <div class="stats" id="statsRibbon">
        <div class="stat-card">
          <div class="stat-icon-wrap" style="background:rgba(139, 92, 246, 0.12);color:#8b5cf6">
            <span class="stat-icon">👥</span>
          </div>
          <div class="stat-info">
            <span class="stat-num" id="statCustomers">154</span>
            <span class="stat-label">Total Customers</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon-wrap" style="background:rgba(14, 165, 233, 0.12);color:#0ea5e9">
            <span class="stat-icon">📱</span>
          </div>
          <div class="stat-info">
            <span class="stat-num" id="statDevices">117,783</span>
            <span class="stat-label">Total Entries</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon-wrap" style="background:rgba(16, 185, 129, 0.12);color:#10b981">
            <span class="stat-icon">✨</span>
          </div>
          <div class="stat-info">
            <span class="stat-num" id="statAddedByYou">117,781</span>
            <span class="stat-label">Inserted By You</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon-wrap" style="background:rgba(245, 158, 11, 0.12);color:#f59e0b">
            <span class="stat-icon">⊞</span>
          </div>
          <div class="stat-info">
            <span class="stat-num" id="statColumns">90</span>
            <span class="stat-label">Unique Columns</span>
          </div>
        </div>
      </div>"""
home_top_elements = re.sub(r'<div class="stats" id="statsRibbon">[\s\S]*?</div>', new_stats_ribbon, home_top_elements)

# 4. Extract all 21 dialogs cleanly from master_head
dialog_ids = [
    'dlgCartModal', 'dlgRenameAllCustomers', 'dlgDeleteCustomerEntries',
    'dlgBulkDeleteExcel', 'dlgBulkEditImei', 'dlgAuditLog', 'dlgManageUsers',
    'dlgUserPermissions', 'qsdlg', 'cdlg', 'devdlg', 'dlgAddColumn',
    'dlgChooseExportCols', 'dlgEditName', 'pwd', 'dlgEditError', 'dlgPushError',
    'dlgUploadErrorsAlert', 'dlgEventPopup', 'dlgActionProgress', 'dlgLiveUpdatesModal'
]

modal_btn_replacements = [
    (r'<button class="b ghost" id="closeDlgAuditLog"[^>]*>', '<button class="b ghost" id="closeDlgAuditLog" type="button" onclick="closeModal(\'dlgAuditLog\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b ghost" id="closeDlgManageUsers"[^>]*>', '<button class="b ghost" id="closeDlgManageUsers" type="button" onclick="closeModal(\'dlgManageUsers\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b ghost" id="closeDlgUserPermissions"[^>]*>', '<button class="b ghost" id="closeDlgUserPermissions" type="button" onclick="closeModal(\'dlgUserPermissions\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button type="button" class="b" id="cancelDlgUserPermissions"[^>]*>Cancel</button>', '<button type="button" class="b" id="cancelDlgUserPermissions" onclick="closeModal(\'dlgUserPermissions\')">Cancel</button>'),
    (r'<button class="b ghost" type="button" id="closeDlgEventPopup"[^>]*>', '<button class="b ghost" type="button" id="closeDlgEventPopup" onclick="closeModal(\'dlgEventPopup\')" style="font-size:20px; padding:4px 8px; cursor:pointer" aria-label="Close">'),
    (r'<button class="b ghost" id="closeDlgRenameAllCustomers"[^>]*>', '<button class="b ghost" id="closeDlgRenameAllCustomers" type="button" onclick="closeModal(\'dlgRenameAllCustomers\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b" id="btnCancelRenameAllCust"[^>]*>Cancel</button>', '<button class="b" id="btnCancelRenameAllCust" type="button" onclick="closeModal(\'dlgRenameAllCustomers\')">Cancel</button>'),
    (r'<button class="b ghost" id="closeDlgDeleteCustomerEntries"[^>]*>', '<button class="b ghost" id="closeDlgDeleteCustomerEntries" type="button" onclick="closeModal(\'dlgDeleteCustomerEntries\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b" id="btnCancelDelCustEntries"[^>]*>Cancel</button>', '<button class="b" id="btnCancelDelCustEntries" type="button" onclick="closeModal(\'dlgDeleteCustomerEntries\')">Cancel</button>'),
    (r'<button class="b ghost" id="closeDlgBulkDeleteExcel"[^>]*>', '<button class="b ghost" id="closeDlgBulkDeleteExcel" type="button" onclick="closeModal(\'dlgBulkDeleteExcel\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b" id="btnCancelBulkDelete"[^>]*>Cancel</button>', '<button class="b" id="btnCancelBulkDelete" type="button" onclick="closeModal(\'dlgBulkDeleteExcel\')">Cancel</button>'),
    (r'<button class="b ghost" id="closeDlgBulkEditImei"[^>]*>', '<button class="b ghost" id="closeDlgBulkEditImei" type="button" onclick="closeModal(\'dlgBulkEditImei\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b" id="btnCancelBulkEdit"[^>]*>Cancel</button>', '<button class="b" id="btnCancelBulkEdit" type="button" onclick="closeModal(\'dlgBulkEditImei\')">Cancel</button>'),
    (r'<button class="b ghost" id="closeDlgAddColumn"[^>]*>', '<button class="b ghost" id="closeDlgAddColumn" type="button" onclick="closeModal(\'dlgAddColumn\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b" type="button" id="cancelDlgAddColumn"[^>]*>Cancel</button>', '<button class="b" type="button" id="cancelDlgAddColumn" onclick="closeModal(\'dlgAddColumn\')">Cancel</button>'),
    (r'<button class="b ghost" id="closeDlgChooseExportCols"[^>]*>', '<button class="b ghost" id="closeDlgChooseExportCols" type="button" onclick="closeModal(\'dlgChooseExportCols\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b" id="cancelDlgChooseExportCols"[^>]*>Cancel</button>', '<button class="b" id="cancelDlgChooseExportCols" type="button" onclick="closeModal(\'dlgChooseExportCols\')">Cancel</button>'),
    (r'<button class="b ghost" type="button" id="closeDlgEditError"[^>]*>', '<button class="b ghost" type="button" id="closeDlgEditError" onclick="closeModal(\'dlgEditError\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b" type="button" id="btnCancelEditError"[^>]*>Cancel</button>', '<button class="b" type="button" id="btnCancelEditError" onclick="closeModal(\'dlgEditError\')">Cancel</button>'),
    (r'<button class="b ghost" type="button" id="closeDlgPushError"[^>]*>', '<button class="b ghost" type="button" id="closeDlgPushError" onclick="closeModal(\'dlgPushError\')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">'),
    (r'<button class="b" type="button" id="btnCancelPushError"[^>]*>Cancel</button>', '<button class="b" type="button" id="btnCancelPushError" onclick="closeModal(\'dlgPushError\')">Cancel</button>'),
    (r'<button class="b" id="btnDismissUploadErrors"[^>]*>Dismiss</button>', '<button class="b" id="btnDismissUploadErrors" type="button" onclick="closeModal(\'dlgUploadErrorsAlert\')">Dismiss</button>'),
    (r'<button class="b ghost" id="qsclose"[^>]*>', '<button class="b ghost" id="qsclose" type="button" onclick="closeModal(\'qsdlg\')" style="height:32px;padding:0 8px">'),
    (r'<button class="b" type="button" id="cdx"[^>]*>Cancel</button>', '<button class="b" type="button" id="cdx" onclick="closeModal(\'cdlg\')">Cancel</button>'),
    (r'<button class="b" type="button" id="devCancel"[^>]*>Cancel</button>', '<button class="b" type="button" id="devCancel" onclick="closeModal(\'devdlg\')">Cancel</button>')
]

dialogs_dict = {}
for did in dialog_ids:
    m = re.search(r'<dialog\s+[^>]*id="' + did + r'"[\s\S]*?</dialog>', master_head)
    assert m, f"Failed to extract dialog {did} from master_head"
    d_html = m.group(0)
    for pat, repl in modal_btn_replacements:
        d_html = re.sub(pat, repl, d_html)
    dialogs_dict[did] = d_html

# Dialog mapping per feature
feature_dialogs = {
    'INDEX': dialog_ids,
    'DASHBOARD': dialog_ids,
    'HOME': ['dlgLiveUpdatesModal', 'dlgEditName', 'pwd', 'dlgEventPopup', 'dlgActionProgress'],
    'INV': ['dlgRenameAllCustomers', 'dlgDeleteCustomerEntries', 'devdlg', 'dlgAddColumn', 'dlgChooseExportCols', 'cdlg', 'qsdlg', 'dlgCartModal', 'dlgEventPopup', 'dlgActionProgress'],
    'SIM': ['dlgUploadErrorsAlert', 'dlgEventPopup', 'dlgActionProgress'],
    'FETCH': ['qsdlg', 'dlgEventPopup', 'dlgActionProgress'],
    'EDIT': ['dlgBulkDeleteExcel', 'dlgBulkEditImei', 'dlgCartModal', 'devdlg', 'dlgEventPopup', 'dlgActionProgress'],
    'ALERTS': ['dlgEventPopup', 'dlgActionProgress'],
    'ERRORS': ['dlgEditError', 'dlgPushError', 'dlgEventPopup', 'dlgActionProgress'],
    'SETTINGS': ['dlgEditName', 'pwd', 'dlgManageUsers', 'dlgAuditLog', 'dlgUserPermissions', 'dlgEventPopup', 'dlgActionProgress']
}

# 5. Extract Script 2 and slice into Core 1, Feature Blocks, and Core 2
scripts = list(re.finditer(r'<script\b[^>]*>([\s\S]*?)</script>', master_head))
main_script = scripts[1].group(1) # master_head script 1 is mainScript

# Replace $ definition in main_script with Safe Mock DOM & universal closeModal
safe_element_js = """
      // Safe Mock DOM Element to allow shared routines to run cleanly across modular single-feature pages
      const _safeElemStore = {};
      function createSafeElement(id) {
        if (_safeElemStore[id]) return _safeElemStore[id];
        const mock = {
          id: id,
          style: {
            setProperty() {},
            removeProperty() {},
            getPropertyValue() { return ''; }
          },
          classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
          dataset: {},
          children: [],
          childNodes: [],
          setAttribute() {},
          removeAttribute() {},
          getAttribute() { return null; },
          addEventListener() {},
          removeEventListener() {},
          querySelector() { return null; },
          querySelectorAll() { return []; },
          getElementsByTagName() { return []; },
          getElementsByClassName() { return []; },
          appendChild(c) { return c; },
          removeChild(c) { return c; },
          focus() {},
          blur() {},
          click() {},
          reset() {},
          showModal() {},
          close() {},
          open: false,
          value: '',
          innerHTML: '',
          textContent: '',
          hidden: true
        };
        _safeElemStore[id] = mock;
        return mock;
      }
      const $ = id => document.getElementById(id) || createSafeElement(id);

      // Default Active Session: Ensure User & Token are initialized on page load
      if (!localStorage.getItem('token')) {
        localStorage.setItem('token', 'local-admin-session-0001');
        localStorage.setItem('user', JSON.stringify({
          user_id: '0001',
          name: 'Shilish Reddy',
          role: 'admin',
          is_admin: true,
          category: 'super_admin',
          badge: '👑 Super Admin',
          permissions: {
            page_inventory: true,
            page_sim_upload: true,
            page_fetch: true,
            page_edit: true,
            page_alerts: true,
            page_health: true,
            page_errors: true,
            page_users: true,
            page_activity: true,
            page_cart: true
          }
        }));
      }

      // Universal bullet-proof closeModal function & capture-phase listener
      function closeModal(dlgOrId) {
        try {
          const dlg = typeof dlgOrId === 'string' ? $(dlgOrId) : dlgOrId;
          if (!dlg) return;
          if (typeof dlg.close === 'function') {
            try { dlg.close(); } catch(_) {}
          }
          dlg.removeAttribute('open');
          if (dlg.style) {
            dlg.style.display = 'none';
            setTimeout(() => { if (!dlg.hasAttribute('open')) dlg.style.display = ''; }, 50);
          }
        } catch(err) {
          console.warn('closeModal error:', err);
        }
      }
      window.closeModal = closeModal;
      window.closeEditNameModal = () => closeModal('dlgEditName');
      window.closeChangePasswordModal = () => closeModal('pwd');
      window.closeAuditLogModal = () => closeModal('dlgAuditLog');
      window.closeManageUsersModal = () => closeModal('dlgManageUsers');
      window.closeCartModal = () => closeModal('dlgCartModal');
      window.closeLiveUpdatesModal = function() {
        try { clearInterval(liveUpdatesModalTimer); liveUpdatesModalTimer = null; } catch(_) {}
        closeModal('dlgLiveUpdatesModal');
      };

      // Universal capture-phase click listener for any popup close cross mark (✕), cancel button or modal backdrop
      document.addEventListener('click', function(e) {
        const closeBtn = e.target.closest('button.ghost, button[aria-label="Close"], button[data-close], .close-modal, #closeDlgEditName, #closeDlgChangePassword, #closeDlgAuditLog, #closeDlgManageUsers, #closeDlgUserPermissions, #closeDlgLiveUpdates, #closeDlgCart, #closeDlgEventPopup, #closeDlgAddColumn, #closeDlgChooseExportCols, #closeDlgRenameAllCustomers, #closeDlgDeleteCustomerEntries, #closeDlgBulkDeleteExcel, #closeDlgBulkEditImei, #closeDlgEditError, #closeDlgPushError, #qsclose, #cdx, #devCancel, #cancelDlgUserPermissions, #cancelDlgAddColumn, #cancelDlgChooseExportCols, #btnCancelRenameAllCust, #btnCancelDelCustEntries, #btnCancelBulkDelete, #btnCancelBulkEdit, #btnCancelEditError, #btnCancelPushError, #btnDismissUploadErrors, #pc');
        if (closeBtn) {
          const dlg = closeBtn.closest('dialog');
          if (dlg) {
            closeModal(dlg);
            e.preventDefault();
            e.stopPropagation();
            return;
          }
        }

        if (e.target && (e.target.textContent.trim() === '✕' || e.target.textContent.trim() === '×' || e.target.textContent.trim() === 'X')) {
          const dlg = e.target.closest('dialog');
          if (dlg) {
            closeModal(dlg);
            e.preventDefault();
            e.stopPropagation();
            return;
          }
        }

        if (e.target && e.target.tagName === 'DIALOG' && e.target.hasAttribute('open')) {
          const rect = e.target.getBoundingClientRect();
          const isInDialog = (
            rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
            rect.left <= e.clientX && e.clientX <= rect.left + rect.width
          );
          if (!isInDialog) {
            closeModal(e.target);
          }
        }
      }, true);
"""
main_script = re.sub(r'const\s+\$\s*=\s*id\s*=>\s*document\.getElementById\(id\);', safe_element_js, main_script, count=1)

# Cleanly replace openSettingsModal
old_settings_script_pattern = r'function openSettingsModal\(\)\s*\{[\s\S]*?(?=\s*// Cart Popup Modal Handlers)'
new_settings_script = """function openSettingsModal() {
        location.href = 'settings.html';
      }
      if ($('sidebarBtnSettings')) $('sidebarBtnSettings').onclick = openSettingsModal;
      if ($('btnHeaderSettings')) $('btnHeaderSettings').onclick = openSettingsModal;
"""
main_script = re.sub(old_settings_script_pattern, new_settings_script, main_script, count=1)

# Update applyTheme palette selector
main_script = main_script.replace("document.querySelectorAll('#dlgSettings .theme-palette-opt')", "document.querySelectorAll('.theme-palette-opt')")

# Add inter-page routing in showContainer
old_show_container = """async function showContainer(boxId) {"""
new_show_container = """async function showContainer(boxId) {
        const _boxRouteMap = {
          'box-home': 'home.html',
          'box-live': 'home.html',
          'box-health': 'home.html',
          'box-inv': 'inventory.html',
          'box-cust': 'inventory.html',
          'box-upl': 'sim-upload.html',
          'box-sim': 'sim-upload.html',
          'box-fetch': 'fetch-data.html',
          'box-edit': 'edit-delete.html',
          'box-exp': 'alerts.html',
          'box-errors': 'errors.html',
          'box-settings': 'settings.html'
        };
        if (!document.getElementById(boxId) && _boxRouteMap[boxId]) {
          const targetPage = _boxRouteMap[boxId];
          if (!window.location.pathname.endsWith(targetPage)) {
            location.href = targetPage;
            return;
          }
        }"""
main_script = main_script.replace(old_show_container, new_show_container, 1)

# Ensure avatar click goes to settings.html
main_script = re.sub(r"if\s*\(\$\('userAvatarCircle'\)\)\s*\$\('userAvatarCircle'\)\.onclick\s*=\s*[^;]+;", "$('userAvatarCircle').onclick = () => { location.href = 'settings.html'; };", main_script)

# Enable runLiveCycle to run on box-home
main_script = main_script.replace("if (currentContainerId !== 'box-live' || !tok)", "if ((currentContainerId !== 'box-live' && currentContainerId !== 'box-home') || !tok)")
main_script = main_script.replace("if (currentContainerId !== 'box-live') return;", "if (currentContainerId !== 'box-live' && currentContainerId !== 'box-home') return;")
main_script = main_script.replace("if (livePolling && currentContainerId === 'box-live' && tok)", "if (livePolling && (currentContainerId === 'box-live' || currentContainerId === 'box-home') && tok)")

# KPI ribbon labels
old_kpi_ribbon = """              [S.customers || 0, 'Customers', '👥', '#8b5cf6', 'rgba(139, 92, 246, 0.12)'],
              [S.devices || 0, 'Device Records', '📱', '#0ea5e9', 'rgba(14, 165, 233, 0.12)'],
              [S.added_by_you || 0, 'Added By You', '✨', '#10b981', 'rgba(16, 185, 129, 0.12)'],
              [S.columns || 0, 'Unique Columns', '⊞', '#f59e0b', 'rgba(245, 158, 11, 0.12)']"""

new_kpi_ribbon = """              [S.customers || 0, 'Total Customers', '👥', '#8b5cf6', 'rgba(139, 92, 246, 0.12)'],
              [S.devices || 0, 'Total Entries', '📱', '#0ea5e9', 'rgba(14, 165, 233, 0.12)'],
              [S.added_by_you || 0, 'Inserted By You', '✨', '#10b981', 'rgba(16, 185, 129, 0.12)'],
              [S.columns || 0, 'Unique Columns', '⊞', '#f59e0b', 'rgba(245, 158, 11, 0.12)']"""
main_script = main_script.replace(old_kpi_ribbon, new_kpi_ribbon)

# Revert switchView
old_switch_pattern = r'function\s+switchView\s*\([^)]*\)\s*\{[\s\S]*?(?=\n\s*(?:async\s+)?function\s+initTheme|\n\s*(?:async\s+)?function\s+initApp|\n\s*//\s*Theme|\n\s*/\*\s*---\s*Theme)'
new_switch_code = """function switchView(signedIn) {
        initTheme();
        if (signedIn) {
          document.body.classList.add('app-active');
          if ($('authWrap')) {
            $('authWrap').hidden = true;
            $('authWrap').style.setProperty('display', 'none', 'important');
            $('authWrap').style.setProperty('visibility', 'hidden', 'important');
          }
          if ($('dashboardWrap')) {
            $('dashboardWrap').hidden = false;
            $('dashboardWrap').style.setProperty('display', 'flex', 'important');
            $('dashboardWrap').style.setProperty('visibility', 'visible', 'important');
          }
          window.scrollTo(0, 0);
          initApp();
        } else {
          document.body.classList.remove('app-active');
          hideBstplLoader();
          if ($('dashboardWrap')) {
            $('dashboardWrap').hidden = true;
            $('dashboardWrap').style.setProperty('display', 'none', 'important');
            $('dashboardWrap').style.setProperty('visibility', 'hidden', 'important');
          }
          if ($('authWrap')) {
            $('authWrap').hidden = false;
            $('authWrap').style.setProperty('display', 'flex', 'important');
            $('authWrap').style.setProperty('visibility', 'visible', 'important');
            window.scrollTo(0, 0);
            if ($('authPw')) $('authPw').value = '';
            if ($('authId') && typeof $('authId').focus === 'function') $('authId').focus();
          } else {
            location.href = 'index.html';
          }
        }
      }"""
main_script = re.sub(old_switch_pattern, new_switch_code, main_script, count=1)

# Revert logout
old_logout_pattern = r'function\s+logout\s*\([^)]*\)\s*\{[\s\S]*?(?=\n\s*function\s+switchView)'
new_logout_code = """function logout(manual = false) {
        try {
          if (manual && tok) {
            try { fetch(API_BASE + '/auth/logout', { method: 'POST', headers: { Authorization: 'Bearer ' + tok }, credentials: 'include', keepalive: true }); } catch { }
            try { fetch(API_BASE + '/api/auth/logout', { method: 'POST', headers: { Authorization: 'Bearer ' + tok }, credentials: 'include', keepalive: true }); } catch { }
          }
        } catch (_) {}
        try { clearTimeout(liveTimer); } catch(_) {}
        try { clearTimeout(liveCycleTimer); } catch(_) {}
        try { clearInterval(liveUpdatesModalTimer); } catch(_) {}
        livePolling = false;
        liveUpdatesActive = false;
        tok = null;
        try { localStorage.removeItem('token'); } catch(_) {}
        try { localStorage.removeItem('user'); } catch(_) {}
        try { sessionStorage.clear(); } catch(_) {}
        try { document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch(_) {} }); } catch(_) {}
        switchView(false);
        toast('Signed out');
      }
      window.logout = logout;
"""
main_script = re.sub(old_logout_pattern, new_logout_code, main_script, count=1)

# Update initTheme to set data-palette as well
main_script = re.sub(
    r"function\s+initTheme\s*\(\)\s*\{[\s\S]*?document\.documentElement\.setAttribute\('data-mode',\s*saved\);",
    """function initTheme() {
        const saved = localStorage.getItem('valut_theme_mode') || localStorage.getItem('theme') || 'light';
        const savedPal = localStorage.getItem('valut_palette') || 'royal_navy';
        document.documentElement.setAttribute('data-theme', saved);
        document.documentElement.setAttribute('data-mode', saved);
        document.documentElement.setAttribute('data-palette', savedPal);""",
    main_script,
    count=1
)

# Settings Tail JS
settings_tail_js = """
      /* ---------- Settings & Themes Page Controller ---------- */
      async function loadSettingsPage() {
        let u = null;
        try {
          u = getUser();
          if (localStorage.getItem('token')) {
            try {
              const res = await api('/api/me');
              if (res && res.user_id) {
                u = res;
                localStorage.setItem('user', JSON.stringify(res));
                currentUser = res;
              }
            } catch (e) {
              console.warn('api/me fetch notice:', e);
            }
          }

          if (u) {
            if ($('settingsUserName')) $('settingsUserName').textContent = u.name || 'User ' + (u.user_id || '');
            if ($('settingsUserId')) $('settingsUserId').textContent = u.user_id || '0001';
            if ($('settingsDetailUserId')) $('settingsDetailUserId').textContent = u.user_id || '0001';
            if ($('settingsUserAvatar')) $('settingsUserAvatar').textContent = ((u.name || u.user_id || 'U')[0] || 'U').toUpperCase();
            if ($('settingsDetailRole')) $('settingsDetailRole').textContent = (u.role === 'admin' ? 'Administrator' : 'Standard User') + ' (' + (u.category_label || u.category || 'User') + ')';
            if ($('settingsUserCategory')) $('settingsUserCategory').textContent = (u.category_label || 'User') + ' • User ID: ' + (u.user_id || '');
            if ($('settingsUserBadge')) {
              $('settingsUserBadge').textContent = u.badge || (u.role === 'admin' ? '👑 Admin' : '👤 User');
              $('settingsUserBadge').className = 'role-pill ' + (u.role === 'admin' ? 'admin' : 'regular');
            }
            if ($('settingsDetailPrevName')) $('settingsDetailPrevName').textContent = u.previous_name || 'None';

            if ($('settingsPermissionsWrap') && u.permissions && typeof u.permissions === 'object') {
              const permLabels = {
                'page_inventory': '👥 Customer Inventory',
                'page_sim_upload': '📱 SIM Data Upload',
                'page_fetch': '🔍 Fetch Data',
                'page_edit': '✏️ Edit / Delete by IMEI',
                'page_alerts': '⚠️ Expiry Alerts',
                'page_health': '📊 Data Health Report',
                'page_errors': '🚨 Errored Entries',
                'page_users': '👥 User Management',
                'page_activity': '🕘 Activity Audit Log',
                'page_cart': '🛒 Recycle Cart'
              };
              const badges = Object.entries(u.permissions)
                .filter(([k, v]) => v === true && permLabels[k])
                .map(([k]) => `<span class="badge" style="padding:4px 10px;background:var(--card-subtle);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:600">${permLabels[k]}</span>`);
              if (badges.length > 0) {
                $('settingsPermissionsWrap').innerHTML = badges.join('');
              }
            }
          }
        } catch (err) {
          console.warn('Error loading user profile in settings:', err);
        }

        const curPal = localStorage.getItem('valut_palette') || 'royal_navy';
        const curMode = localStorage.getItem('valut_theme_mode') || localStorage.getItem('theme') || 'light';

        const modeRadio = document.querySelector(`input[name="themeModeChoice"][value="${curMode}"]`);
        if (modeRadio) modeRadio.checked = true;

        const palRadio = document.querySelector(`input[name="paletteChoice"][value="${curPal}"]`);
        if (palRadio) palRadio.checked = true;

        updateThemeSelectionUI(curPal, curMode);

        // Smooth scroll helpers for merged Manage Users and Login Inventory in Settings
        window.scrollToManageUsers = function() {
          const el = $('settingsManageUsersCard');
          if (el) el.scrollIntoView({ behavior: 'smooth' });
        };
        window.scrollToLoginInventory = function() {
          const el = $('settingsLoginInventoryCard');
          if (el) el.scrollIntoView({ behavior: 'smooth' });
        };

        // Export Login Inventory to CSV
        window.exportAuditLogCSV = async function() {
          try {
            const d = await api('/api/activity?page=1&page_size=500&kind=' + (window.LG && window.LG.kind || 'all') + (window.LG && window.LG.who ? '&who=' + encodeURIComponent(window.LG.who) : ''));
            const items = d.items || [];
            if (!items.length) {
              toast('⚠️ No audit logs to export');
              return;
            }
            const headers = ['Timestamp', 'Employee ID', 'Action', 'Details', 'IP Address'];
            const rows = items.map(i => [
              `"${(i.created_at || '').replace(/"/g, '""')}"`,
              `"${(i.user_id || '').replace(/"/g, '""')}"`,
              `"${(i.action || '').replace(/"/g, '""')}"`,
              `"${(i.details || '').replace(/"/g, '""')}"`,
              `"${(i.ip_address || '').replace(/"/g, '""')}"`
            ]);
            const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join(String.fromCharCode(10));
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', `login_inventory_audit_${new Date().toISOString().slice(0, 10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            toast('✅ Login inventory export downloaded');
          } catch (err) {
            toast('⚠️ Failed to export audit log');
          }
        };

        // Load Manage Users & Login Inventory when opening Settings
        if (u && (u.role === 'admin' || (u.permissions && u.permissions.page_users))) {
          if (typeof loadUsersContainer === 'function') {
            try { loadUsersContainer(); } catch(err) { console.warn('loadUsersContainer notice:', err); }
          }
          if (typeof loadAuditLogContainer === 'function') {
            try { loadAuditLogContainer(); } catch(err) { console.warn('loadAuditLogContainer notice:', err); }
          }
        } else {
          if ($('settingsManageUsersCard')) $('settingsManageUsersCard').style.display = 'none';
          if ($('settingsBtnManageUsers')) $('settingsBtnManageUsers').style.display = 'none';
          if (typeof loadAuditLogContainer === 'function') {
            try { loadAuditLogContainer(); } catch(err) { console.warn('loadAuditLogContainer notice:', err); }
          }
        }
      }

      function updateThemeSelectionUI(pal, mode) {
        const lblLight = $('lblModeLight');
        const lblDark = $('lblModeDark');
        if (lblLight && lblDark) {
          if (mode === 'dark') {
            lblDark.style.background = 'var(--primary, #38bdf8)';
            lblDark.style.color = '#ffffff';
            lblLight.style.background = 'transparent';
            lblLight.style.color = 'var(--text)';
          } else {
            lblLight.style.background = 'var(--primary, #1d68e1)';
            lblLight.style.color = '#ffffff';
            lblDark.style.background = 'transparent';
            lblDark.style.color = 'var(--text)';
          }
        }

        document.querySelectorAll('.theme-card-option').forEach(card => {
          const isSel = card.dataset.palette === pal;
          card.classList.toggle('active', isSel);
          card.style.border = isSel ? '2px solid var(--primary, #1d68e1)' : '1px solid var(--line)';
          card.style.background = isSel ? 'rgba(29, 104, 225, 0.08)' : 'var(--card)';
        });
      }

      function previewThemeSelection() {
        const palRadio = document.querySelector('input[name="paletteChoice"]:checked');
        const modeRadio = document.querySelector('input[name="themeModeChoice"]:checked');
        const pal = palRadio ? palRadio.value : (localStorage.getItem('valut_palette') || 'royal_navy');
        const mode = modeRadio ? modeRadio.value : (localStorage.getItem('valut_theme_mode') || 'light');
        updateThemeSelectionUI(pal, mode);
      }

      async function submitThemeSelection() {
        const palRadio = document.querySelector('input[name="paletteChoice"]:checked');
        const modeRadio = document.querySelector('input[name="themeModeChoice"]:checked');
        const pal = palRadio ? palRadio.value : 'royal_navy';
        const mode = modeRadio ? modeRadio.value : 'light';

        applyTheme(pal, mode, true);
        updateThemeSelectionUI(pal, mode);

        const msgBox = $('themeSubmitMsg');
        if (msgBox) {
          const palNames = {
            'royal_navy': 'Royal Navy',
            'midnight': 'Midnight Slate',
            'emerald': 'Emerald Forest',
            'crimson_vault': 'Crimson Vault'
          };
          msgBox.style.display = 'inline-flex';
          msgBox.style.background = 'var(--card-subtle)';
          msgBox.style.color = 'var(--ok, #16a34a)';
          msgBox.style.border = '1px solid var(--ok, #16a34a)';
          msgBox.innerHTML = `✅ Theme applied successfully! Active: <b>${palNames[pal] || pal}</b> (${mode.toUpperCase()} MODE).`;
          setTimeout(() => {
            try { msgBox.style.display = 'none'; } catch(_) {}
          }, 5000);
        }

        toast(`🎨 Theme updated to ${pal} (${mode})`);
      }
"""

# Script boundary positions
posHome = main_script.find('async function loadHomeContainer()')
posInv = main_script.find('async function loadInventoryContainer()')
posSim = main_script.find('function initBulkUploadContainer()')
posFetch = main_script.find('function initFetchContainer()')
posEdit = main_script.find('function initEditImeiContainer()')
posAlerts = main_script.find('async function loadExpiryContainer()')
posHealth = main_script.find('async function loadHealthContainer()')
posErrors = main_script.find('async function loadErrorsContainer()')
posCart = main_script.find('async function loadCartContainer()')
posUsers = main_script.find('async function loadAuditLogContainer()')
posQuicksearch = main_script.find('/* ---------- Quick Search (Ctrl+K) ---------- */')

core1 = main_script[:posHome]
core2 = main_script[posQuicksearch:]

feature_blocks = {
    'HOME': main_script[posHome:posInv] + "\n\n" + main_script[posHealth:posErrors],
    'INV': main_script[posInv:posSim],
    'SIM': main_script[posSim:posFetch],
    'FETCH': main_script[posFetch:posEdit],
    'EDIT': main_script[posEdit:posAlerts] + "\n\n" + main_script[posCart:posUsers],
    'ALERTS': main_script[posAlerts:posHealth],
    'ERRORS': main_script[posErrors:posCart],
    'SETTINGS': main_script[posUsers:posQuicksearch] + "\n\n" + settings_tail_js
}

full_features_code = main_script[posHome:posQuicksearch] + "\n\n" + settings_tail_js

# Pages Configuration
page_configs = [
    {
        'file': 'frontend/index.html',
        'title': 'Home Overview & Live Updates — BSTPL CustomerVault',
        'active_key': 'HOME',
        'show_home_header': True,
        'has_auth_wrap': True,
        'container_html': containers['box-home'],
        'dialog_key': 'INDEX',
        'script_type': 'FULL',
        'init_js': 'currentContainerId = "box-home"; await runLiveCycle(true).catch(e => console.warn(e)); await loadHealthContainer().catch(e => console.warn(e));'
    },
    {
        'file': 'frontend/dashboard.html',
        'title': 'Home Overview & Live Updates — BSTPL CustomerVault',
        'active_key': 'HOME',
        'show_home_header': True,
        'has_auth_wrap': True,
        'container_html': containers['box-home'],
        'dialog_key': 'DASHBOARD',
        'script_type': 'FULL',
        'init_js': 'currentContainerId = "box-home"; await runLiveCycle(true).catch(e => console.warn(e)); await loadHealthContainer().catch(e => console.warn(e));'
    },
    {
        'file': 'frontend/home.html',
        'title': 'Home Overview & Live Updates — BSTPL CustomerVault',
        'active_key': 'HOME',
        'show_home_header': True,
        'has_auth_wrap': False,
        'container_html': containers['box-home'],
        'dialog_key': 'HOME',
        'script_type': 'HOME',
        'init_js': 'currentContainerId = "box-home"; await runLiveCycle(true).catch(e => console.warn(e)); await loadHealthContainer().catch(e => console.warn(e));'
    },
    {
        'file': 'frontend/inventory.html',
        'title': 'Customer Inventory — BSTPL CustomerVault',
        'active_key': 'INV',
        'show_home_header': False,
        'has_auth_wrap': False,
        'container_html': containers['box-inv'],
        'dialog_key': 'INV',
        'script_type': 'INV',
        'init_js': 'await loadInventoryContainer().catch(e => console.warn(e));'
    },
    {
        'file': 'frontend/sim-upload.html',
        'title': 'SIM Data Upload — BSTPL CustomerVault',
        'active_key': 'SIM',
        'show_home_header': False,
        'has_auth_wrap': False,
        'container_html': containers['box-sim'],
        'dialog_key': 'SIM',
        'script_type': 'SIM',
        'init_js': 'initSimDataContainer();'
    },
    {
        'file': 'frontend/fetch-data.html',
        'title': 'Fetch Data — BSTPL CustomerVault',
        'active_key': 'FETCH',
        'show_home_header': False,
        'has_auth_wrap': False,
        'container_html': containers['box-fetch'],
        'dialog_key': 'FETCH',
        'script_type': 'FETCH',
        'init_js': 'initFetchContainer();'
    },
    {
        'file': 'frontend/edit-delete.html',
        'title': 'Edit / Delete by IMEI — BSTPL CustomerVault',
        'active_key': 'EDIT',
        'show_home_header': False,
        'has_auth_wrap': False,
        'container_html': containers['box-edit'],
        'dialog_key': 'EDIT',
        'script_type': 'EDIT',
        'init_js': 'initEditImeiContainer();'
    },
    {
        'file': 'frontend/alerts.html',
        'title': 'SIM Expiry Alerts — BSTPL CustomerVault',
        'active_key': 'ALERTS',
        'show_home_header': False,
        'has_auth_wrap': False,
        'container_html': containers['box-exp'],
        'dialog_key': 'ALERTS',
        'script_type': 'ALERTS',
        'init_js': 'loadExpiryContainer();'
    },
    {
        'file': 'frontend/errors.html',
        'title': 'Errored Entries — BSTPL CustomerVault',
        'active_key': 'ERRORS',
        'show_home_header': False,
        'has_auth_wrap': False,
        'container_html': containers['box-errors'],
        'dialog_key': 'ERRORS',
        'script_type': 'ERRORS',
        'init_js': 'loadErrorsContainer();'
    },
    {
        'file': 'frontend/settings.html',
        'title': 'Settings — BSTPL CustomerVault',
        'active_key': 'SETTINGS',
        'show_home_header': False,
        'has_auth_wrap': False,
        'container_html': containers['box-settings'],
        'dialog_key': 'SETTINGS',
        'script_type': 'SETTINGS',
        'init_js': 'await loadSettingsPage().catch(e => console.warn(e));'
    }
]

# auth_wrap for index.html / dashboard.html
auth_wrap_html = open('scratch/authwrap_extracted.html', 'r', encoding='utf-8').read()

keys = ['HOME', 'INV', 'SIM', 'FETCH', 'EDIT', 'ALERTS', 'ERRORS', 'SETTINGS']

for cfg in page_configs:
    cur_head = common_head
    
    # If page does NOT need authWrap (home.html, inventory.html, etc.), ensure it's not present
    if not cfg['has_auth_wrap']:
        pos_aw = cur_head.find('<div id="authWrap"')
        if pos_aw != -1:
            pos_dw = cur_head.find('<div id="dashboardWrap"')
            cur_head = cur_head[:pos_aw] + cur_head[pos_dw:]
    else:
        # For index.html and dashboard.html: ensure authWrap is present before dashboardWrap
        if '<div id="authWrap"' not in cur_head:
            pos_dw = cur_head.find('<div id="dashboardWrap"')
            if pos_dw != -1:
                cur_head = cur_head[:pos_dw] + auth_wrap_html + "\n\n  " + cur_head[pos_dw:]
    
    # Make sure dashboardWrap is display:flex on all pages
    cur_head = cur_head.replace('id="dashboardWrap" class="cv-app-shell" style="display:none"', 'id="dashboardWrap" class="cv-app-shell" style="display:flex"')
    
    cur_head = re.sub(r'<title>[^<]*</title>', f'<title>{cfg["title"]}</title>', cur_head, count=1)
    
    for k in keys:
        is_active = (k == cfg['active_key'])
        nav_cls = 'on' if is_active else ''
        cur_head = cur_head.replace(f'{{{{NAV_{k}}}}}', nav_cls)
    
    # Header: Only Home Overview has Home Top Elements. No horizontal #mainTabs on any page!
    if cfg['show_home_header']:
        middle_header = home_top_elements
    else:
        middle_header = ""
    
    # Dialogs block for this specific page
    dlg_list = feature_dialogs[cfg['dialog_key']]
    dialogs_html = "\n\n  ".join([dialogs_dict[did] for did in dlg_list if did in dialogs_dict])
    
    # Sliced script block for this specific page
    if cfg['script_type'] == 'FULL':
        script_body = core1 + "\n\n" + full_features_code + "\n\n" + core2
    else:
        script_body = core1 + "\n\n" + feature_blocks[cfg['script_type']] + "\n\n" + core2
    
    # Exact replacement of await showContainer in initApp
    old_init_line = "await showContainer('box-home').catch(e => console.warn('showContainer notice:', e));"
    script_body = script_body.replace(old_init_line, cfg['init_js'], 1)
    
    full_html = (
        cur_head +
        middle_header +
        cfg['container_html'] +
        "\n    </main>\n  </div>\n\n  " +
        dialogs_html +
        "\n\n  <!-- Global Toast Notification -->\n  <div id=" + '"toast" role="status"></div>' +
        "\n\n  <script>\n" +
        script_body +
        "\n  </script>\n</body>\n</html>"
    )
    
    with open(cfg['file'], 'w', encoding='utf-8') as out_f:
        out_f.write(full_html)
    
    header_status = "WITH Home Header & Stat Cards" if cfg['show_home_header'] else "WITHOUT Home Header (Feature Direct)"
    print(f"Generated {cfg['file']} (Size: {len(full_html):,} bytes) - Feature: {cfg['active_key']} [Dialogs: {len(dlg_list)}] [{header_status}]")

print("\nALL 10 MODULAR WEBPAGES COMPILED & GENERATED WITH CLEAN FEATURE ISOLATION & VISIBLE SIDEBAR!")
