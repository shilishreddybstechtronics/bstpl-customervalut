import re

with open("frontend/index.html", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update Sidebar
old_sb_menu = """        <button class="cv-nav-item" data-target="box-exp" id="sidebarBtnAlerts" title="SIM Expiry Alerts">
          <div style="display:flex;align-items:center;gap:12px">
            <span class="cv-nav-ico">⚠️</span>
            <span class="cv-nav-label">Expiry Alerts</span>
          </div>
          <span class="cv-live-badge" style="margin-left:auto;background:rgba(245,158,11,0.2);color:#f59e0b;border:1px solid rgba(245,158,11,0.4)">ALERTS</span>
        </button>
        <button class="cv-nav-item" data-target="box-settings" id="sidebarBtnSettings" title="User Settings &amp; Theme Options">
          <span class="cv-nav-ico">⚙️</span>
          <span class="cv-nav-label">Settings</span>
        </button>"""

new_sb_menu = """        <button class="cv-nav-item" data-target="box-exp" id="sidebarBtnAlerts" title="SIM Expiry Alerts">
          <div style="display:flex;align-items:center;gap:12px">
            <span class="cv-nav-ico">⚠️</span>
            <span class="cv-nav-label">Expiry Alerts</span>
          </div>
          <span class="cv-live-badge" style="margin-left:auto;background:rgba(245,158,11,0.2);color:#f59e0b;border:1px solid rgba(245,158,11,0.4)">ALERTS</span>
        </button>
        <button class="cv-nav-item" type="button" id="sidebarBtnLiveUpdates" title="Live Updates &amp; Telemetry Stream" onclick="openLiveUpdatesModal()">
          <div style="display:flex;align-items:center;gap:12px">
            <span class="cv-nav-ico">⚡</span>
            <span class="cv-nav-label">Live Updates</span>
          </div>
          <span class="live-badge" style="margin-left:auto;background:#10b981;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;font-weight:800">ON</span>
        </button>
        <button class="cv-nav-item" data-target="box-settings" id="sidebarBtnSettings" title="User Settings &amp; Theme Options">
          <span class="cv-nav-ico">⚙️</span>
          <span class="cv-nav-label">Settings</span>
        </button>"""

assert old_sb_menu in text, "old_sb_menu not found!"
text = text.replace(old_sb_menu, new_sb_menu, 1)

old_sb_widget = '<div class="cv-sidebar-live-widget" id="sidebarLiveWidget">'
new_sb_widget = '<div class="cv-sidebar-live-widget" id="sidebarLiveWidget" onclick="openLiveUpdatesModal()" style="cursor:pointer" title="Click to view Live Telemetry Stream">'
if old_sb_widget in text:
    text = text.replace(old_sb_widget, new_sb_widget, 1)

# 2. Main panel header, banner, KPI ribbon, tabs, and box-home
pos_hdr = text.find('<header class="cv-top-header">')
target_pattern = r'<!--\s*=+\s*CONTAINER 1:\s*SEPARATE DEDICATED LIVE UPDATES'
match_box1 = re.search(target_pattern, text[pos_hdr:])
assert match_box1, "Container 1 comment not found after header!"
pos_box1 = pos_hdr + match_box1.start()

new_main_top = """<header class="cv-top-header">
        <div class="cv-header-single-line" style="display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap">
          <!-- Left Actions: Quick Search, Refresh, Alerts Toggle & Cart (Exact visual match to picture) -->
          <div class="cv-header-actions acts" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <button class="b" id="bQs" title="Quick Search (Ctrl + K)"><span>🔎 Search</span></button>
            <button class="b" id="bRefresh" title="Reload current data">🔄 Refresh</button>
            <button class="b on" id="bAl" title="Toggle Expiry Alerts">Alerts: ON</button>
            <button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="openCartModal()" style="font-weight:700">
              🛒 Cart ( <span id="headerCartCountBadge">0</span> )
            </button>
          </div>

          <!-- Right Side: Good afternoon Greeting & Profile Actions (Exact visual match to picture) -->
          <div style="display:flex;align-items:center;gap:12px;margin-left:auto;flex-wrap:nowrap">
            <div class="user-badge" id="uBadge" style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;background:var(--card-subtle);border:1px solid var(--line);border-radius:99px;font-weight:700;font-size:13.5px">
              <span id="hi">Good afternoon, Shilish Reddy</span>
              <span class="role-pill admin" id="rolePill">ADMIN</span>
            </div>
            <div class="cv-avatar-circle" id="userAvatarCircle" title="User Settings &amp; Account Options" onclick="showContainer('box-settings')" style="cursor:pointer">S</div>
            <button class="b b-logout" id="bLo" title="Sign out of your session" style="font-weight:700">Logout</button>
          </div>
        </div>
      </header>

      <!-- SIM Expiry Alert Global Banner (Exact Visual Match to Picture) -->
      <div class="cv-expiry-global-banner" id="globalExpiryAlertBanner">
        <div class="cv-exp-banner-left">
          <span class="cv-exp-clock">⏰</span>
          <div>
            <span class="cv-exp-label">SIM Expiry Alert:</span>
            <span class="cv-exp-msg" id="globalExpiryAlertText"><span id="cntExpiredGlobalText">40,928</span> SIM(s) have already expired, and <span id="cntExpiringSoonGlobalText">2,936</span> are expiring within 30 days.</span>
          </div>
        </div>
        <div class="cv-exp-banner-actions">
          <button type="button" class="cv-exp-btn expired" id="btnViewExpiredGlobal" onclick="showContainer('box-exp'); if(typeof switchExpiryTab==='function') switchExpiryTab('expired');">
            <span>⚠️</span> <span>View Expired (<b id="cntExpiredGlobalBadge">40,928</b>)</span>
          </button>
          <button type="button" class="cv-exp-btn expiring" id="btnViewExpiringSoonGlobal" onclick="showContainer('box-exp'); if(typeof switchExpiryTab==='function') switchExpiryTab('expiring');">
            <span>⏳</span> <span>View Expiring Soon (<b id="cntExpiringSoonGlobalBadge">2,936</b>)</span>
          </button>
        </div>
      </div>

      <!-- 4 Stat Metric KPI Ribbon (Exact Visual Match to Picture) -->
      <div class="stats" id="statsRibbon">
        <div class="stat-card">
          <div class="stat-icon-wrap" style="background:rgba(139, 92, 246, 0.12);color:#8b5cf6">
            <span class="stat-icon">👥</span>
          </div>
          <div class="stat-info">
            <div class="stat-num" id="statNumCust">154</div>
            <div class="stat-lbl">Customers</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon-wrap" style="background:rgba(14, 165, 233, 0.12);color:#0ea5e9">
            <span class="stat-icon">📱</span>
          </div>
          <div class="stat-info">
            <div class="stat-num" id="statNumDev">117,783</div>
            <div class="stat-lbl">Device Records</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon-wrap" style="background:rgba(16, 185, 129, 0.12);color:#10b981">
            <span class="stat-icon">✨</span>
          </div>
          <div class="stat-info">
            <div class="stat-num" id="statNumAdded">117,781</div>
            <div class="stat-lbl">Added By You</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon-wrap" style="background:rgba(245, 158, 11, 0.12);color:#f59e0b">
            <span class="stat-icon">⊞</span>
          </div>
          <div class="stat-info">
            <div class="stat-num" id="statNumCols">90</div>
            <div class="stat-lbl">Unique Columns</div>
          </div>
        </div>
      </div>

      <!-- Quick Action Navigation Tabs (Exact Visual Match to Picture) -->
      <nav class="card nav-tabs cv-action-tabs" id="mainTabs" role="tablist">
        <button class="tab-btn on" data-target="box-home">🏠 Home Overview</button>
        <button class="tab-btn" data-target="box-inv">📇 Customer Inventory</button>
        <button class="tab-btn" data-target="box-sim">📱 SIM Data Upload</button>
        <button class="tab-btn" data-target="box-fetch">🔍 Fetch Data</button>
        <button class="tab-btn" data-target="box-edit">✏️ Edit / Delete by IMEI</button>
        <button class="tab-btn" data-target="box-exp">⚠️ Expiry Alerts</button>
        <button class="tab-btn" data-target="box-health">📊 Data Health</button>
        <button class="tab-btn cv-pill-danger" data-target="box-errors">🚨 Errored Entries (<span id="errorsCountBadge">2055</span>)</button>
      </nav>

      <!-- =========================================================================
         CONTAINER 0: HOME OVERVIEW (Customer Data Overview + 3D Database Diagram)
         ========================================================================= -->
      <section class="container-box active" id="box-home" style="padding:0;background:transparent;border:none;box-shadow:none">
        <!-- Customer Data Overview Card -->
        <div class="cv-overview-card">
          <div class="cv-overview-header">
            <div>
              <h2 class="cv-overview-title">Customer Data Overview</h2>
              <p class="cv-overview-sub">Access, manage and edit customer data with ease.</p>
            </div>
            <div class="cv-search-wrap">
              <span class="cv-search-ico">🔍</span>
              <input type="text" id="homeSearchInput" class="cv-search-input" placeholder="Search by name, ICCID, or IMEI..." onkeydown="if(event.key==='Enter') executeHomeSearch()" />
              <button class="cv-search-btn" id="homeSearchBtn" onclick="executeHomeSearch()">Search</button>
            </div>
          </div>

          <div class="cv-overview-body">
            <!-- 3D Flow Architecture Diagram -->
            <div class="cv-flow-diagram">
              <div class="cv-flow-satellite sat-fetch" id="flowSatFetch" title="Click to Fetch Data" onclick="showContainer('box-fetch')">
                <div class="sat-bubble"><span class="sat-ico">☁️</span></div>
                <div class="sat-label">Fetch Data</div>
              </div>
              <div class="cv-flow-satellite sat-edit" id="flowSatEdit" title="Click to Edit Data" onclick="showContainer('box-edit')">
                <div class="sat-bubble"><span class="sat-ico">✏️</span></div>
                <div class="sat-label">Edit Data</div>
              </div>

              <!-- Central 3D Database Cylinder -->
              <div class="cv-flow-cylinder" id="flowCylinder" title="BSTPL CustomerVault Database Core - Click for Live Updates &amp; Telemetry" onclick="openLiveUpdatesModal()">
                <div class="flow-cyl-disk"></div>
                <div class="flow-cyl-core"></div>
                <div class="flow-cyl-disk" style="margin-top:28px"></div>
              </div>

              <div class="cv-flow-satellite sat-view" id="flowSatView" title="Click to View Customers" onclick="showContainer('box-inv')">
                <div class="sat-bubble"><span class="sat-ico">👤</span></div>
                <div class="sat-label">Customers</div>
              </div>
              <div class="cv-flow-satellite sat-inv" id="flowSatInv" title="Click to Manage Inventory" onclick="showContainer('box-inv')">
                <div class="sat-bubble"><span class="sat-ico">📦</span></div>
                <div class="sat-label">Inventory</div>
              </div>

              <!-- SVG Connection Lines -->
              <svg class="cv-flow-svg" viewBox="0 0 520 240">
                <line x1="140" y1="50" x2="220" y2="100" stroke="#38bdf8" stroke-width="2" stroke-dasharray="5 5" />
                <line x1="380" y1="50" x2="300" y2="100" stroke="#38bdf8" stroke-width="2" stroke-dasharray="5 5" />
                <line x1="140" y1="190" x2="220" y2="140" stroke="#38bdf8" stroke-width="2" stroke-dasharray="5 5" />
                <line x1="380" y1="190" x2="300" y2="140" stroke="#38bdf8" stroke-width="2" stroke-dasharray="5 5" />
              </svg>
            </div>

            <!-- 4 Highlights on Right -->
            <div class="cv-overview-features">
              <div class="cv-feature-item" id="featFetch" onclick="showContainer('box-fetch')">
                <div class="cv-feat-icon-wrap" style="background:rgba(16, 185, 129, 0.12);color:#10b981">
                  <span>☁️</span>
                </div>
                <div class="cv-feat-text">
                  <div class="cv-feat-title">Fetch Data</div>
                  <div class="cv-feat-desc">Get data from website or database</div>
                </div>
              </div>

              <div class="cv-feature-item" id="featEdit" onclick="showContainer('box-edit')">
                <div class="cv-feat-icon-wrap" style="background:rgba(168, 85, 247, 0.12);color:#a855f7">
                  <span>✏️</span>
                </div>
                <div class="cv-feat-text">
                  <div class="cv-feat-title">Edit Data</div>
                  <div class="cv-feat-desc">Update customer information easily</div>
                </div>
              </div>

              <div class="cv-feature-item" id="featLiveUpdates" onclick="openLiveUpdatesModal()" style="border:1.5px solid rgba(56,189,248,0.4);background:linear-gradient(135deg, rgba(2,132,199,0.06), rgba(37,99,235,0.06))">
                <div class="cv-feat-icon-wrap" style="background:rgba(56, 189, 248, 0.15);color:#0284c7">
                  <span>⚡</span>
                </div>
                <div class="cv-feat-text">
                  <div class="cv-feat-title" style="display:flex;align-items:center;gap:6px">
                    Live Updates <span class="live-badge" style="background:#10b981;color:#fff;font-size:10px;padding:1px 6px;border-radius:99px;font-weight:800">LIVE</span>
                  </div>
                  <div class="cv-feat-desc">Real-time telemetry stream &amp; diagnostics</div>
                </div>
              </div>

              <div class="cv-feature-item" id="featSecure">
                <div class="cv-feat-icon-wrap" style="background:rgba(14, 165, 233, 0.12);color:#0ea5e9">
                  <span>🛡️</span>
                </div>
                <div class="cv-feat-text">
                  <div class="cv-feat-title">Secure &amp; Reliable</div>
                  <div class="cv-feat-desc">Database verified &amp; RBAC protected</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      """

text = text[:pos_hdr] + new_main_top + text[pos_box1:]

# 3. Update showContainer in JS to toggle globalExpiryAlertBanner and statsRibbon
old_show_container_hook = """        document.querySelectorAll('.container-box').forEach(box => {
          const isActive = box.id === boxId;
          box.classList.toggle('active', isActive);
          box.style.display = isActive ? 'block' : 'none';
        });"""

new_show_container_hook = """        // Display banner & KPI ribbon on Home Overview as shown in visual layout
        if ($('globalExpiryAlertBanner')) {
          $('globalExpiryAlertBanner').style.display = (boxId === 'box-home') ? 'flex' : 'none';
        }
        if ($('statsRibbon')) {
          $('statsRibbon').style.display = (boxId === 'box-home') ? 'grid' : 'none';
        }

        document.querySelectorAll('.container-box').forEach(box => {
          const isActive = box.id === boxId;
          box.classList.toggle('active', isActive);
          box.style.display = isActive ? 'block' : 'none';
        });"""

assert old_show_container_hook in text, "old_show_container_hook not found!"
text = text.replace(old_show_container_hook, new_show_container_hook, 1)

# 4. Add executeHomeSearch if not present
if "function executeHomeSearch" not in text:
    target_js_insert = "function showContainer(boxId) {"
    home_search_js = """function executeHomeSearch() {
        const val = ($('homeSearchInput') ? $('homeSearchInput').value : '').trim();
        if (!val) return;
        showContainer('box-inv');
        if ($('invSearch')) {
          $('invSearch').value = val;
          if (typeof loadInventoryData === 'function') loadInventoryData(true);
        }
      }
      window.executeHomeSearch = executeHomeSearch;

      """
    assert target_js_insert in text, "target_js_insert not found!"
    text = text.replace(target_js_insert, home_search_js + target_js_insert, 1)

# Write updated index.html
with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(text)

# Also copy 100% byte-for-byte to dashboard.html
with open("frontend/dashboard.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Successfully applied exact mockup layout to frontend/index.html & frontend/dashboard.html!")

