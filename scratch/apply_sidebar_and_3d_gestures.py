import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# -------------------------------------------------------------
# 1. ADD 3D PERSPECTIVE & MINIMAL TACTILE GESTURES CSS
# -------------------------------------------------------------
css_3d_gestures = '''
  /* =========================================================================
     3D PERSPECTIVE & MINIMAL TACTILE GESTURES (Preserving all existing styles)
     ========================================================================= */
  .cv-content-wrap, main, .main-wrap {
    perspective: 1200px;
  }

  /* 3D Container Stage Transition with minimal depth */
  .container-box {
    transform-style: preserve-3d;
    backface-visibility: hidden;
    will-change: transform, opacity;
  }

  .container-box.active {
    animation: cv3DStageEnter 0.36s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
  }

  @keyframes cv3DStageEnter {
    0% {
      opacity: 0;
      transform: perspective(1200px) rotateX(2deg) translateY(12px) scale(0.988);
      filter: blur(0.5px);
    }
    100% {
      opacity: 1;
      transform: perspective(1200px) rotateX(0deg) translateY(0) scale(1);
      filter: blur(0);
    }
  }

  /* 3D Tactile Gestures on Action Tabs */
  .cv-action-tabs .tab-btn {
    transform-style: preserve-3d;
    transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1),
                box-shadow 0.22s ease,
                background 0.2s ease,
                color 0.2s ease,
                border-color 0.2s ease !important;
  }

  .cv-action-tabs .tab-btn:hover {
    transform: perspective(600px) translateY(-2.5px) translateZ(8px);
    box-shadow: 0 8px 20px -4px rgba(29, 104, 225, 0.22);
  }

  .cv-action-tabs .tab-btn:active {
    transform: perspective(600px) translateY(1px) scale(0.975);
  }

  .cv-action-tabs .tab-btn.on {
    transform: perspective(600px) translateZ(4px);
  }

  /* 3D Tactile Gestures on Sidebar Navigation Items */
  .cv-nav-item {
    transform-style: preserve-3d;
    transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1),
                background 0.2s ease,
                box-shadow 0.22s ease !important;
  }

  .cv-nav-item:hover {
    transform: perspective(600px) translateX(4px) translateZ(6px);
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
  }

  .cv-nav-item:active {
    transform: perspective(600px) translateX(2px) scale(0.98);
  }

  .cv-nav-item.on {
    transform: perspective(600px) translateZ(4px);
  }

  /* 3D Hover Depth on Stat Cards & Feature Highlights */
  .stat-card, .cv-overview-card, .cv-feature-item, #homeLiveUpdatesCard {
    transform-style: preserve-3d;
    transition: transform 0.26s cubic-bezier(0.34, 1.56, 0.64, 1),
                box-shadow 0.26s ease !important;
  }

  .stat-card:hover {
    transform: perspective(800px) translateY(-3px) translateZ(8px);
    box-shadow: 0 12px 28px -6px rgba(15, 23, 42, 0.08);
  }

  .cv-feature-item:hover {
    transform: perspective(800px) translateY(-2px) translateX(3px) translateZ(6px);
    box-shadow: 0 8px 22px -4px rgba(37, 99, 235, 0.14);
  }

  #homeLiveUpdatesCard:hover {
    transform: perspective(800px) translateY(-2px) translateZ(6px);
    box-shadow: 0 12px 30px rgba(14, 165, 233, 0.25);
  }
'''

# Insert CSS before closing </style> of first head block
head_style_end = text.find('</style>')
assert head_style_end != -1, "Could not find </style> in head"
text = text[:head_style_end] + css_3d_gestures + text[head_style_end:]

# -------------------------------------------------------------
# 2. UPDATE SIDEBAR MENU ITEMS
# -------------------------------------------------------------
old_sidebar_menu = '''      <nav class="cv-sidebar-menu">
        <button class="cv-nav-item on" data-target="box-home">
          <span class="cv-nav-ico">🏠</span>
          <span class="cv-nav-label">Home</span>
        </button>
        <button class="cv-nav-item" data-target="box-inv" data-sub="cust">
          <span class="cv-nav-ico">👥</span>
          <span class="cv-nav-label">Customers</span>
        </button>
        <button class="cv-nav-item" data-target="box-fetch" style="border:1px solid rgba(255,255,255,0.12);background:rgba(255,255,255,0.03)">
          <span class="cv-nav-ico">📱</span>
          <span class="cv-nav-label">Device Records</span>
        </button>
        <button class="cv-nav-item" data-target="box-inv" data-sub="devices">
          <span class="cv-nav-ico">📦</span>
          <span class="cv-nav-label">Inventory</span>
        </button>
        <button class="cv-nav-item" data-target="box-health">
          <span class="cv-nav-ico">📄</span>
          <span class="cv-nav-label">Reports</span>
        </button>
        <button class="cv-nav-item" data-target="box-sim">
          <span class="cv-nav-ico">📱</span>
          <span class="cv-nav-label">Data Management</span>
        </button>
        <button class="cv-nav-item cv-nav-live" id="sidebarLiveUpdatesBtn" title="Toggle Live Telemetry Stream">
          <div style="display:flex;align-items:center;gap:12px">
            <span class="cv-nav-ico">⚡</span>
            <span class="cv-nav-label">Live Updates</span>
          </div>
          <span class="cv-live-badge on" id="sidebarLiveBadge">
            <span class="cv-live-dot-pulse"></span>
            <span id="sidebarLiveText">ON</span>
          </span>
        </button>
        <button class="cv-nav-item" id="sidebarBtnSettings">
          <span class="cv-nav-ico">⚙️</span>
          <span class="cv-nav-label">Settings</span>
        </button>
      </nav>'''

new_sidebar_menu = '''      <nav class="cv-sidebar-menu">
        <button class="cv-nav-item on" data-target="box-home" title="Home Overview">
          <span class="cv-nav-ico">🏠</span>
          <span class="cv-nav-label">Home</span>
        </button>
        <button class="cv-nav-item" data-target="box-inv" title="Customer Inventory">
          <span class="cv-nav-ico">👥</span>
          <span class="cv-nav-label">Customers</span>
        </button>
        <button class="cv-nav-item" data-target="box-fetch" title="Device Records &amp; Fetch">
          <span class="cv-nav-ico">📱</span>
          <span class="cv-nav-label">Device Records</span>
        </button>
        <button class="cv-nav-item" data-target="box-inv" title="Customer Inventory">
          <span class="cv-nav-ico">📦</span>
          <span class="cv-nav-label">Inventory</span>
        </button>
        <button class="cv-nav-item" data-target="box-errors" id="sidebarBtnErrors" title="Errored Entries &amp; Corrections">
          <span class="cv-nav-ico">🚨</span>
          <span class="cv-nav-label">Errored Entries</span>
          <span class="badge danger" id="sidebarErrorsBadge" style="margin-left:auto;background:#ef4444;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;font-weight:800">2055</span>
        </button>
        <button class="cv-nav-item" data-target="box-sim" title="SIM Data Upload &amp; Management">
          <span class="cv-nav-ico">🗂️</span>
          <span class="cv-nav-label">Data Management</span>
        </button>
        <button class="cv-nav-item" data-target="box-exp" id="sidebarBtnAlerts" title="SIM Expiry Alerts">
          <div style="display:flex;align-items:center;gap:12px">
            <span class="cv-nav-ico">⚠️</span>
            <span class="cv-nav-label">Expiry Alerts</span>
          </div>
          <span class="cv-live-badge" style="margin-left:auto;background:rgba(245,158,11,0.2);color:#f59e0b;border:1px solid rgba(245,158,11,0.4)">ALERTS</span>
        </button>
        <button class="cv-nav-item" id="sidebarBtnSettings" title="User Settings &amp; Theme Options">
          <span class="cv-nav-ico">⚙️</span>
          <span class="cv-nav-label">Settings</span>
        </button>
      </nav>'''

assert old_sidebar_menu in text, "Could not find old_sidebar_menu"
text = text.replace(old_sidebar_menu, new_sidebar_menu, 1)

# -------------------------------------------------------------
# 3. PLACE LIVE UPDATES OPTION IN HOME OVERVIEW
# -------------------------------------------------------------
old_feat_block = '''              <div class="cv-feature-item" id="featSecure">
                <div class="cv-feat-icon-wrap" style="background:rgba(14, 165, 233, 0.12);color:#0ea5e9">
                  <span>🛡️</span>
                </div>
                <div class="cv-feat-text">
                  <div class="cv-feat-title">Secure &amp; Reliable</div>
                  <div class="cv-feat-desc">Your data is always safe with us</div>
                </div>
              </div>
            </div>
          </div>
        </div>'''

new_feat_block = '''              <div class="cv-feature-item" id="featSecure">
                <div class="cv-feat-icon-wrap" style="background:rgba(14, 165, 233, 0.12);color:#0ea5e9">
                  <span>🛡️</span>
                </div>
                <div class="cv-feat-text">
                  <div class="cv-feat-title">Secure &amp; Reliable</div>
                  <div class="cv-feat-desc">Your data is always safe with us</div>
                </div>
              </div>

              <!-- Live Updates Option Placed in Home Overview -->
              <div class="cv-feature-item" id="featLiveUpdates" style="cursor:pointer" onclick="openLiveUpdatesModal()" title="Live Telemetry Stream">
                <div class="cv-feat-icon-wrap" style="background:rgba(56, 189, 248, 0.15);color:#0284c7">
                  <span>⚡</span>
                </div>
                <div class="cv-feat-text">
                  <div class="cv-feat-title" style="display:flex;align-items:center;gap:6px">
                    <span>Live Updates</span>
                    <span class="live-badge" style="background:#10b981;color:#fff;font-size:10px;padding:1px 6px;border-radius:99px;font-weight:800"><span class="cv-live-dot-pulse"></span> LIVE</span>
                  </div>
                  <div class="cv-feat-desc">Real-time device &amp; telemetry monitoring</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Live Updates & Real-Time Telemetry Stream Banner in Home Overview -->
        <div class="card" id="homeLiveUpdatesCard" style="margin:20px 0;padding:16px 22px;border:1px solid #38bdf8;border-radius:16px;background:linear-gradient(90deg, #0f172a 0%, #1e293b 100%);color:#fff;box-shadow:0 8px 24px rgba(14,165,233,0.15)">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px">
            <div style="display:flex;align-items:center;gap:14px">
              <div style="width:44px;height:44px;border-radius:12px;background:rgba(56,189,248,0.2);color:#38bdf8;display:flex;align-items:center;justify-content:center;font-size:22px">⚡</div>
              <div>
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-size:15px;font-weight:800;color:#fff">Live Telemetry &amp; System Stream</span>
                  <span class="live-badge" style="background:#10b981;color:#fff;font-size:11px;padding:2px 8px;border-radius:99px;font-weight:800"><span class="cv-live-dot-pulse"></span> LIVE</span>
                </div>
                <div style="font-size:12px;color:#94a3b8;margin-top:2px">Real-time device tracking, telemetry health, and customer synchronization</div>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:10px">
              <button class="b" id="homeBtnToggleLive" type="button" style="background:#0284c7;color:#fff;font-weight:700;border:none;border-radius:8px;padding:8px 16px;cursor:pointer" onclick="toggleLiveUpdates()">🟢 Live: ON</button>
              <button class="b" id="homeBtnOpenLiveModal" type="button" style="background:rgba(255,255,255,0.12);color:#fff;font-weight:700;border:1px solid rgba(255,255,255,0.2);border-radius:8px;padding:8px 16px;cursor:pointer" onclick="openLiveUpdatesModal()">⚡ Open Full Stream</button>
            </div>
          </div>
        </div>'''

assert old_feat_block in text, "Could not find old_feat_block"
text = text.replace(old_feat_block, new_feat_block, 1)

# -------------------------------------------------------------
# 4. ENHANCE showContainer WITH HASH SYNC & DEFAULT TO HOME
# -------------------------------------------------------------
old_show_container = '''      async function showContainer(boxId) {
        let subView = null;
        if (boxId === 'box-cust') {
          boxId = 'box-inv';
          subView = 'cust';
        } else if (boxId === 'box-upl') {
          boxId = 'box-inv';
          subView = 'upload';
        }

        if (boxId === 'box-log') {
          openAuditLogModal();
          return;
        }
        if (boxId === 'box-users') {
          openManageUsersModal();
          return;
        }
        if (boxId === 'box-bin') {
          openCartModal();
          return;
        }

        currentContainerId = boxId;
        document.querySelectorAll('#mainTabs .tab-btn').forEach(b => {
          b.classList.toggle('on', b.dataset.target === boxId);
        });
        document.querySelectorAll('#cvSidebar .cv-nav-item').forEach(b => {
          b.classList.toggle('on', b.dataset.target === boxId);
        });

        document.querySelectorAll('.container-box').forEach(box => {
          box.classList.toggle('active', box.id === boxId);
        });

        if (boxId === 'box-home') {
          loadHomeContainer();
          return;
        }'''

new_show_container = '''      function getInitialTargetBox() {
        const hash = (window.location.hash || '').replace('#', '').trim().toLowerCase();
        const query = (new URLSearchParams(window.location.search).get('page') || '').trim().toLowerCase();
        const map = {
          'home': 'box-home',
          'box-home': 'box-home',
          'overview': 'box-home',
          'inventory': 'box-inv',
          'box-inv': 'box-inv',
          'customer': 'box-inv',
          'customers': 'box-inv',
          'sim-upload': 'box-sim',
          'box-sim': 'box-sim',
          'upload': 'box-sim',
          'data-management': 'box-sim',
          'fetch': 'box-fetch',
          'fetch-data': 'box-fetch',
          'box-fetch': 'box-fetch',
          'edit': 'box-edit',
          'edit-delete': 'box-edit',
          'box-edit': 'box-edit',
          'alerts': 'box-exp',
          'expiry': 'box-exp',
          'box-exp': 'box-exp',
          'errors': 'box-errors',
          'box-errors': 'box-errors',
          'health': 'box-health'
        };
        return map[hash] || map[query] || 'box-home';
      }

      async function showContainer(boxId) {
        if (!boxId) boxId = getInitialTargetBox() || 'box-home';
        let subView = null;
        if (boxId === 'box-cust') {
          boxId = 'box-inv';
          subView = 'cust';
        } else if (boxId === 'box-upl') {
          boxId = 'box-inv';
          subView = 'upload';
        }

        if (boxId === 'box-log') {
          openAuditLogModal();
          return;
        }
        if (boxId === 'box-users') {
          openManageUsersModal();
          return;
        }
        if (boxId === 'box-bin') {
          openCartModal();
          return;
        }

        currentContainerId = boxId;

        // Friendly URL hash synchronization for clean browser navigation and bookmarking
        const boxToHash = {
          'box-home': 'home',
          'box-inv': 'inventory',
          'box-sim': 'sim-upload',
          'box-fetch': 'fetch-data',
          'box-edit': 'edit-delete',
          'box-exp': 'alerts',
          'box-errors': 'errors',
          'box-health': 'health'
        };
        const expectedHash = boxToHash[boxId] || 'home';
        if ((window.location.hash || '').replace('#', '') !== expectedHash) {
          try {
            history.replaceState(null, '', '#' + expectedHash);
          } catch (_) {}
        }

        document.querySelectorAll('#mainTabs .tab-btn').forEach(b => {
          b.classList.toggle('on', b.dataset.target === boxId);
        });
        document.querySelectorAll('#cvSidebar .cv-nav-item').forEach(b => {
          b.classList.toggle('on', b.dataset.target === boxId);
        });

        document.querySelectorAll('.container-box').forEach(box => {
          const isActive = box.id === boxId;
          box.classList.toggle('active', isActive);
          if (isActive) {
            box.style.display = 'block';
          }
        });

        if (boxId === 'box-home') {
          loadHomeContainer();
          return;
        }'''

assert old_show_container in text, "Could not find old_show_container"
text = text.replace(old_show_container, new_show_container, 1)

# In signedIn(), ensure getInitialTargetBox() is used
text = text.replace("showContainer('box-home');", "showContainer(getInitialTargetBox());")

# Add hashchange listener
if "window.addEventListener('hashchange'" not in text:
    old_init_tail = "if ($('sidebarBtnSettings')) $('sidebarBtnSettings').onclick = openSettingsModal;"
    new_init_tail = """if ($('sidebarBtnSettings')) $('sidebarBtnSettings').onclick = openSettingsModal;
      window.addEventListener('hashchange', () => {
        showContainer(getInitialTargetBox());
      });"""
    text = text.replace(old_init_tail, new_init_tail, 1)

# Write to frontend/index.html
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

# Write identical copy to frontend/dashboard.html
with open('frontend/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("index.html and dashboard.html successfully updated with sidebar items, live updates in home, and 3D gestures!")

