import re

with open('frontend/dashboard.html', 'r', encoding='utf-8') as f:
    dash_content = f.read()

# 1. Head part from <!DOCTYPE html> to </style>
pos_style_end = dash_content.find('</style>') + len('</style>')
head_part = dash_content[:pos_style_end]

# Update Title
head_part = re.sub(r'<title>.*?</title>', '<title>Cart & Recycle Bin — BSTPL CustomerVault</title>', head_part)

# 2. Extract Sidebar from dashboard.html
aside_m = re.search(r'<aside class="cv-sidebar" id="cvSidebar"[\s\S]*?</aside>', dash_content)
assert aside_m, "Could not find cvSidebar in dashboard.html"
sidebar_html = aside_m.group(0)

# In sidebar: ensure Home Overview is NOT active
sidebar_html = re.sub(r'<a class="cv-nav-item\s+on"', '<a class="cv-nav-item"', sidebar_html)

# Set cart active and change href to cart.html
sidebar_html = re.sub(
    r'<a class="cv-nav-item\s*"\s+href="[^"]*"\s*(?:onclick="[^"]*")?\s*id="sidebarBtnCart"[^>]*>',
    '<a class="cv-nav-item on active" href="cart.html" id="sidebarBtnCart" title="Cart &amp; Recycle Bin" style="text-decoration:none">',
    sidebar_html
)

# 3. Extract Top Header
hdr_m = re.search(r'<header class="cv-top-header"[\s\S]*?</header>', dash_content)
assert hdr_m, "Could not find cv-top-header"
header_html = hdr_m.group(0)

# In header: add "Main Page" button and update cart button
header_html = header_html.replace(
    '<button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="openCartModal()" style="font-weight:700">\n              🛒 Cart (<span id="headerCartCountBadge">0</span>)\n            </button>',
    '<a class="b p" id="btnHeaderHome" href="home.html" title="Return to Home Overview" style="text-decoration:none;font-weight:700;display:inline-flex;align-items:center;gap:6px">🏠 Main Page</a>\n            <button class="b" id="btnHeaderCart" title="Refresh Cart Data" onclick="loadCartContainer()" style="font-weight:700">🛒 Cart (<span id="headerCartCountBadge">0</span>)</button>'
)

# 4. Extract Global Expiry Banner
banner_m = re.search(r'<div class="cv-expiry-global-banner" id="globalExpiryAlertBanner"[\s\S]*?</div>\s*</div>', dash_content)
assert banner_m, "Could not find globalExpiryAlertBanner"
banner_html = banner_m.group(0)

cart_main_content = """
      <!-- =========================================================================
         CONTAINER: CART & RECYCLE BIN (Redesigned High-Impact Enterprise View)
         ========================================================================= -->
      <section class="container-box active" id="box-cart" style="display:block;padding:0;background:transparent;border:none;box-shadow:none;margin-bottom:28px">
        
        <!-- Top Hero Ribbon Card -->
        <div class="card" style="padding:24px 28px;border:1px solid var(--line);border-radius:18px;background:var(--card);box-shadow:0 4px 20px rgba(0,0,0,0.03);margin-bottom:20px;position:relative;overflow:hidden">
          <div style="position:absolute;top:0;right:0;width:340px;height:100%;background:radial-gradient(circle at 80% 20%, rgba(56, 189, 248, 0.08) 0%, transparent 70%);pointer-events:none"></div>
          
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:18px">
            <div style="display:flex;align-items:center;gap:16px">
              <div style="width:58px;height:58px;border-radius:16px;background:linear-gradient(135deg, rgba(56, 189, 248, 0.16), rgba(37, 99, 235, 0.16));border:1.5px solid rgba(56, 189, 248, 0.3);color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:28px;box-shadow:0 4px 14px rgba(37,99,235,0.12);flex-shrink:0">
                🛒
              </div>
              <div>
                <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                  <h2 style="margin:0;font-size:24px;font-weight:800;color:var(--text);letter-spacing:-0.02em">Cart &amp; Recycle Bin</h2>
                  <span class="tag ok" id="cartTotalHeaderBadge" style="font-weight:800;font-size:12.5px;padding:4px 12px;border-radius:99px;box-shadow:0 2px 6px rgba(16,185,129,0.15)">
                    0 Total Items
                  </span>
                  <span class="badge" style="background:var(--card-subtle);border:1px solid var(--line);font-size:11.5px;font-weight:700;padding:3px 10px;border-radius:99px">
                    ● Safe Recycle Mode Active
                  </span>
                </div>
                <p class="sub" style="margin:4px 0 0;font-size:13.5px;color:var(--muted);max-width:720px;line-height:1.5">
                  Centralized recovery vault for deleted customer portfolios and device inventory entries. Restore records with 1-click or permanently purge forever.
                </p>
              </div>
            </div>

            <!-- Toolbar Actions -->
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
              <button class="b" id="btnRestoreAllCart" type="button" onclick="restoreAllCartEntries()" style="font-weight:700;font-size:13px;padding:9px 18px;border-radius:10px;display:inline-flex;align-items:center;gap:8px" title="Restore all deleted customer entries to inventory">
                <span>🔄</span> <span>Restore All Entries</span>
              </button>
              <button class="b d" id="btnEmptyCartForever" type="button" onclick="emptyEntireCartForever()" style="font-weight:700;font-size:13px;padding:9px 18px;border-radius:10px;display:inline-flex;align-items:center;gap:8px" title="Permanently delete all items in the cart">
                <span>🗑️</span> <span>Empty Cart Forever</span>
              </button>
              <a class="b p" href="home.html" style="text-decoration:none;font-weight:700;font-size:13px;padding:9px 18px;border-radius:10px;display:inline-flex;align-items:center;gap:8px">
                <span>🏠</span> <span>Main Page</span>
              </a>
            </div>
          </div>
        </div>

        <!-- 4 High-Impact KPI Metrics Strip -->
        <div class="stats" style="grid-template-columns:repeat(auto-fit, minmax(210px, 1fr));gap:14px;margin-top:0;margin-bottom:20px">
          
          <!-- Card 1: Total Deleted Items -->
          <div class="card stat" style="padding:16px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--primary);box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Total in Cart</span>
              <span style="font-size:20px">📦</span>
            </div>
            <b id="statTotalItems" style="font-size:24px;font-weight:800;color:var(--text);display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Recoverable records</span>
          </div>

          <!-- Card 2: Deleted Customers -->
          <div class="card stat" style="padding:16px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid #0284c7;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Deleted Customers</span>
              <span style="font-size:20px">🏢</span>
            </div>
            <b id="statTotalCusts" style="font-size:24px;font-weight:800;color:#0284c7;display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Whole account portfolios</span>
          </div>

          <!-- Card 3: Deleted Customer Entries -->
          <div class="card stat" style="padding:16px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid #2563eb;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Customer Entries</span>
              <span style="font-size:20px">📱</span>
            </div>
            <b id="statTotalDevs" style="font-size:24px;font-weight:800;color:#2563eb;display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Inventory &amp; SIM rows</span>
          </div>

          <!-- Card 4: Errored Records -->
          <div class="card stat" style="padding:16px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid #ef4444;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Errored Entries</span>
              <span style="font-size:20px">⚠️</span>
            </div>
            <b id="statTotalErrs" style="font-size:24px;font-weight:800;color:#ef4444;display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Flagged for review</span>
          </div>

        </div>

        <!-- Live Composition & Breakdown Card -->
        <div class="card" id="cartSummaryBannerWrap" style="padding:20px 24px;border:1px solid var(--line);margin-bottom:20px;background:var(--card);border-radius:16px;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:12px">
            <div style="display:flex;align-items:center;gap:10px">
              <b style="font-size:14.5px;color:var(--text);display:flex;align-items:center;gap:8px">
                <span style="font-size:17px">📊</span> <span>Cart Composition &amp; Breakdown Ratio</span>
              </b>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap" id="cartBreakdownTags">
              <span class="tag" style="background:rgba(2,132,199,0.12);color:#0284c7;font-weight:700;font-size:12px;padding:4px 10px;border-radius:8px" id="cartStatCustTag">🏢 Whole Customers: 0</span>
              <span class="tag" style="background:rgba(37,99,235,0.12);color:#2563eb;font-weight:700;font-size:12px;padding:4px 10px;border-radius:8px" id="cartStatDevTag">📱 Customer Entries: 0</span>
              <span class="tag bad" style="font-weight:700;font-size:12px;padding:4px 10px;border-radius:8px" id="cartStatErrTag">⚠️ Errored Entries: 0</span>
            </div>
          </div>
          <!-- Multi-Segment Visual Progress / Composition Bar -->
          <div style="height:14px;background:var(--card-subtle);border-radius:8px;overflow:hidden;display:flex;border:1px solid var(--line)">
            <div id="cartBarCust" style="width:0%;background:linear-gradient(90deg, #0284c7, #38bdf8);transition:width 0.3s ease" title="Whole Customers"></div>
            <div id="cartBarDev" style="width:0%;background:linear-gradient(90deg, #2563eb, #60a5fa);transition:width 0.3s ease" title="Customer Entries"></div>
            <div id="cartBarErr" style="width:0%;background:linear-gradient(90deg, #ef4444, #f97316);transition:width 0.3s ease" title="Errored Records"></div>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;font-size:11.5px;color:var(--muted);flex-wrap:wrap;gap:8px">
            <span>Hover over segments to view category ratio</span>
            <span>Auto-refreshes with database status</span>
          </div>
        </div>

        <!-- Cart Deletion Progress Container (when emptying) -->
        <div id="cartEmptyProgressWrap" hidden style="margin:0 0 20px;background:var(--card);padding:22px;border:1.5px solid var(--danger, #ef4444);border-radius:16px;box-shadow:0 8px 30px rgba(239,68,68,0.15)">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:8px">
            <div style="display:flex;align-items:center;gap:12px">
              <span id="cartProgSpinIcon" class="spin" style="font-size:24px">⏳</span>
              <div>
                <b id="cartProgTitle" style="font-size:15.5px;color:var(--text)">Emptying Cart Forever (Permanent Deletion)…</b>
                <div id="cartProgStatus" style="font-size:12.5px;color:var(--danger, #dc2626);font-weight:600;margin-top:2px">Preparing deletion…</div>
              </div>
            </div>
            <div style="text-align:right">
              <span id="cartProgPct" style="font-size:22px;font-weight:800;color:var(--danger, #dc2626)">0%</span>
              <div id="cartProgRowsCount" style="font-size:12px;font-weight:600;color:var(--muted)">0 / 0 records</div>
            </div>
          </div>
          <div class="progress-bar" style="height:12px;background:var(--card-subtle);border-radius:6px;overflow:hidden;margin:10px 0;border:1px solid var(--line)">
            <div class="progress-fill" id="cartProgBar" style="width:0%;height:100%;background:linear-gradient(90deg, #ef4444, #dc2626);transition:width 0.2s ease"></div>
          </div>
          <div id="cartProgLiveDetailBox" style="background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px 14px;font-size:12px;max-height:100px;overflow-y:auto;font-family:monospace;margin-top:10px;color:var(--muted)">
            [Ready] Deletion in progress…
          </div>
        </div>

        <!-- Modern Tabs & Filter Controls Card -->
        <div class="card" style="padding:22px 24px;border:1px solid var(--line);border-radius:18px;background:var(--card);box-shadow:0 4px 20px rgba(0,0,0,0.03)">
          
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;flex-wrap:wrap;gap:14px;border-bottom:1px solid var(--line);padding-bottom:16px">
            <!-- Modern Pill Segmented Tabs -->
            <div style="display:inline-flex;padding:4px;background:var(--card-subtle);border-radius:12px;border:1px solid var(--line);gap:4px">
              <button type="button" class="b" id="tabBtnCartCusts" onclick="switchCartTab('custs')" style="padding:8px 18px;font-size:13px;font-weight:800;border-radius:8px;background:var(--primary);color:#fff;border:none;cursor:pointer;display:inline-flex;align-items:center;gap:6px;transition:all 0.2s">
                <span>🏢</span> <span>Deleted Customers</span> (<span id="cartTabCountCusts">0</span>)
              </button>
              <button type="button" class="b ghost" id="tabBtnCartDevs" onclick="switchCartTab('devs')" style="padding:8px 18px;font-size:13px;font-weight:700;border-radius:8px;color:var(--muted);border:none;cursor:pointer;display:inline-flex;align-items:center;gap:6px;transition:all 0.2s">
                <span>📱</span> <span>Deleted Customer Entries</span> (<span id="cartTabCountDevs">0</span>)
              </button>
            </div>

            <!-- Export / Quick Tools -->
            <div style="display:flex;align-items:center;gap:8px">
              <button class="b" type="button" onclick="loadCartContainer()" style="font-weight:700;font-size:12.5px;padding:7px 14px;border-radius:8px" title="Refresh Cart Data">
                🔄 Refresh
              </button>
              <button class="b" type="button" onclick="exportCartListCsv()" style="font-weight:700;font-size:12.5px;padding:7px 14px;border-radius:8px" title="Download Excel CSV of deleted records">
                📥 Export CSV
              </button>
            </div>
          </div>

          <!-- Section 1: Deleted Whole Customers Tab -->
          <div id="cartCustsTabSection">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:12px">
              <div>
                <h4 style="margin:0;font-size:15.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:8px">
                  <span>🏢</span> <span>Deleted Whole Customers</span>
                </h4>
                <p class="sub" style="margin:3px 0 0;font-size:12.5px;color:var(--muted)">Entire customer accounts placed into the Recycle Bin. Restoring brings back their account and all associated device records.</p>
              </div>
              <div class="cv-search-container" style="min-width:280px;position:relative">
                <span class="cv-search-icon-left" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);pointer-events:none;color:var(--muted)">🔎</span>
                <input id="cartCustSearchInput" class="cv-search-input" style="width:100%;height:38px;padding-left:36px;padding-right:12px;font-size:13px;border-radius:9px;border:1px solid var(--line);background:var(--card-subtle);color:var(--text)" placeholder="Search customer name…" />
              </div>
            </div>
            <div id="cartCustsTableWrap">
              <div class="empty">Checking for deleted customers…</div>
            </div>
          </div>

          <!-- Section 2: Deleted Entries / Devices Tab -->
          <div id="cartDevsTabSection" hidden>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:12px">
              <div>
                <h4 style="margin:0;font-size:15.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:8px">
                  <span>📱</span> <span>Deleted Customer Entries &amp; Device Records</span>
                </h4>
                <p class="sub" style="margin:3px 0 0;font-size:12.5px;color:var(--muted)">Individual device records, SIM entries, and staged errored items that were placed into Cart.</p>
              </div>
              <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
                <select id="cartDevColFilter" style="height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:9px;border:1px solid var(--line);background:var(--card-subtle);color:var(--text)" onchange="renderCartDevsTable(allCartDevs)">
                  <option value="all">Search: All Columns</option>
                  <option value="imei">IMEI</option>
                  <option value="customer_name">Customer</option>
                  <option value="device_sr_no">Serial No</option>
                  <option value="iccid">ICCID</option>
                  <option value="msisdn1">MSISDN1</option>
                  <option value="delete_reason">Reason</option>
                </select>
                <div class="cv-search-container" style="min-width:280px;position:relative">
                  <span class="cv-search-icon-left" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);pointer-events:none;color:var(--muted)">🔎</span>
                  <input id="cartDevSearchInput" class="cv-search-input" style="width:100%;height:38px;padding-left:36px;padding-right:12px;font-size:13px;border-radius:9px;border:1px solid var(--line);background:var(--card-subtle);color:var(--text)" placeholder="Search IMEI, customer, serial, ICCID…" />
                </div>
              </div>
            </div>
            <div id="cartDevsTableWrap">
              <div class="empty">Checking for deleted entries…</div>
            </div>
          </div>

        </div>

      </section>
"""

cart_dialogs = """
  <!-- Custom Confirmation Dialog -->
  <dialog id="dlgCartConfirm" class="modal-card" style="width:min(520px, 94vw); padding:0; border-radius:18px; border:1px solid var(--line); box-shadow:0 30px 80px rgba(0,0,0,0.5); overflow:hidden">
    <div style="padding:18px 22px; display:flex; align-items:center; gap:12px; background:var(--card-subtle); border-bottom:1px solid var(--line)">
      <div id="confirmIconBox" style="width:44px;height:44px;border-radius:12px;background:var(--card);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">
        ⚠️
      </div>
      <div style="flex:1">
        <h3 id="confirmTitle" style="margin:0;font-size:16.5px;font-weight:800;color:var(--text)">Confirm Action</h3>
        <p id="confirmSubtitle" style="margin:2px 0 0;font-size:12.5px;color:var(--muted)">Please review before proceeding.</p>
      </div>
      <button class="b ghost" type="button" onclick="closeConfirmDialog(false)" style="font-size:18px;min-width:34px;min-height:34px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;border-radius:8px">✕</button>
    </div>
    <div style="padding:22px">
      <p id="confirmMessage" style="margin:0 0 16px;font-size:14px;line-height:1.6;color:var(--text)"></p>
      <div id="confirmTypeWrap" hidden style="margin-bottom:16px;background:var(--card-subtle);padding:12px 14px;border-radius:10px;border:1px solid var(--line)">
        <label for="confirmTypeInput" style="display:block;margin-bottom:6px;font-size:12.5px;font-weight:700">Type <code id="confirmTypePrompt" style="color:var(--danger);font-weight:800;padding:2px 6px;background:var(--card);border-radius:4px;border:1px solid var(--line)">CONFIRM</code> to verify:</label>
        <input id="confirmTypeInput" placeholder="Type here…" style="width:100%;height:38px;padding:0 12px;font-size:13px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text)" />
      </div>
      <div style="display:flex;justify-content:flex-end;gap:10px">
        <button class="b" type="button" onclick="closeConfirmDialog(false)" style="font-weight:700;padding:8px 16px">Cancel</button>
        <button class="b d" id="btnConfirmProceed" type="button" onclick="closeConfirmDialog(true)" style="font-weight:700;padding:8px 18px">Proceed</button>
      </div>
    </div>
  </dialog>

  <div id="toast" class="toast"></div>
"""

cart_script = """
  <script>
    // --- Foundation Configuration & Core Logic for Cart Webpage ---
    const API_BASE = window.location.origin;
    let tok = localStorage.getItem('token') || '';
    
    // Auth Check: Redirect to login/index if not authenticated
    if (!tok) {
      window.location.href = 'index.html';
    }

    const E = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

    let allCartDevs = [];
    let allCartCusts = [];
    let currentTab = 'custs';
    let confirmResolver = null;

    // Standard API Fetch Wrapper with Auth Token
    async function api(path, opts = {}) {
      opts.headers = opts.headers || {};
      if (tok) opts.headers['Authorization'] = 'Bearer ' + tok;
      if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(opts.body);
      }
      const res = await fetch(API_BASE + path, opts);
      if (res.status === 401) {
        localStorage.removeItem('token');
        window.location.href = 'index.html';
        return;
      }
      if (!res.ok) {
        let errJson = null;
        try { errJson = await res.json(); } catch(_) {}
        const msg = (errJson && (errJson.detail || errJson.message)) || ('Request failed: ' + res.status);
        throw new Error(msg);
      }
      const cType = res.headers.get('content-type') || '';
      if (cType.includes('application/json')) {
        return await res.json();
      }
      return await res.text();
    }

    // Toast Notification Display
    function showToast(msg, tone = 'ok') {
      if (window.cv && window.cv.toast) {
        window.cv.toast(msg, tone);
        return;
      }
      const t = document.getElementById('toast');
      if (!t) return;
      t.textContent = msg;
      t.className = 'toast ' + tone + ' show';
      setTimeout(() => { t.className = 'toast'; }, 3500);
    }

    // Confirmation Modal Helper
    function askConfirm(msg, { title = 'Confirm Action', subtitle = 'Please review before proceeding', okText = 'Proceed', tone = 'danger', typeToConfirm = '' } = {}) {
      return new Promise((resolve) => {
        confirmResolver = resolve;
        const dlg = document.getElementById('dlgCartConfirm');
        const iconBox = document.getElementById('confirmIconBox');
        const titleEl = document.getElementById('confirmTitle');
        const subEl = document.getElementById('confirmSubtitle');
        const msgEl = document.getElementById('confirmMessage');
        const typeWrap = document.getElementById('confirmTypeWrap');
        const typePrompt = document.getElementById('confirmTypePrompt');
        const typeInput = document.getElementById('confirmTypeInput');
        const btnProc = document.getElementById('btnConfirmProceed');

        if (titleEl) titleEl.textContent = title;
        if (subEl) subEl.textContent = subtitle;
        if (msgEl) msgEl.innerHTML = E(msg).replace(/\\n/g, '<br />');
        if (iconBox) {
          iconBox.textContent = tone === 'danger' ? '🗑️' : '⚠️';
          iconBox.style.color = tone === 'danger' ? 'var(--danger)' : 'var(--warn)';
        }
        if (btnProc) {
          btnProc.textContent = okText;
          btnProc.className = tone === 'danger' ? 'b d' : 'b p';
        }

        if (typeToConfirm) {
          if (typeWrap) typeWrap.hidden = false;
          if (typePrompt) typePrompt.textContent = typeToConfirm;
          if (typeInput) {
            typeInput.value = '';
            typeInput.dataset.required = typeToConfirm;
          }
        } else {
          if (typeWrap) typeWrap.hidden = true;
          if (typeInput) typeInput.dataset.required = '';
        }

        if (dlg) {
          if (!dlg.open) {
            try { dlg.showModal(); } catch(_) { dlg.style.display = 'block'; }
          }
        } else {
          resolve(confirm(msg));
        }
      });
    }

    function closeConfirmDialog(confirmed) {
      const dlg = document.getElementById('dlgCartConfirm');
      const typeInput = document.getElementById('confirmTypeInput');
      if (confirmed && typeInput && typeInput.dataset.required) {
        if (typeInput.value.trim().toUpperCase() !== typeInput.dataset.required.toUpperCase()) {
          typeInput.style.borderColor = 'var(--danger)';
          typeInput.focus();
          return;
        }
      }
      if (dlg && dlg.open) dlg.close();
      if (confirmResolver) {
        confirmResolver(confirmed);
        confirmResolver = null;
      }
    }

    // Load Current User Profile & Greeting
    async function loadUserProfile() {
      try {
        let u = null;
        try { u = JSON.parse(localStorage.getItem('user')); } catch(_) {}
        if (!u) {
          u = await api('/auth/me');
          if (u) localStorage.setItem('user', JSON.stringify(u));
        }
        if (u) {
          const name = u.name || u.user_id || 'User';
          const hr = new Date().getHours();
          const greet = hr < 12 ? 'Good morning' : hr < 17 ? 'Good afternoon' : 'Good evening';
          const hiEl = document.getElementById('hi');
          if (hiEl) hiEl.textContent = `${greet}, ${name}`;
          const avEl = document.getElementById('userAvatarCircle');
          if (avEl) avEl.textContent = (name.charAt(0) || 'U').toUpperCase();
          const pill = document.getElementById('rolePill');
          if (pill) {
            const r = (u.role || '').toUpperCase();
            pill.textContent = r === 'ADMIN' ? 'ADMIN' : r || 'USER';
          }
        }
      } catch(err) {
        console.warn('loadUserProfile error:', err);
      }
    }

    // Load Live Sidebar Telemetry
    async function loadTelemetry() {
      try {
        const [devs, custs] = await Promise.all([
          api('/api/devices/count').catch(() => null),
          api('/api/customers').catch(() => [])
        ]);
        const devCount = devs && devs.count != null ? devs.count : (Array.isArray(devs) ? devs.length : null);
        const custCount = Array.isArray(custs) ? custs.length : null;

        const devEl = document.getElementById('sbLiveDevCount');
        if (devEl && devCount != null) devEl.textContent = Number(devCount).toLocaleString();
        const custEl = document.getElementById('sbLiveCustCount');
        if (custEl && custCount != null) custEl.textContent = Number(custCount).toLocaleString();
      } catch(_) {}
    }

    // Tab Switching
    window.switchCartTab = function(tab) {
      currentTab = tab;
      const isCust = tab === 'custs';
      const tabCusts = document.getElementById('tabBtnCartCusts');
      const tabDevs = document.getElementById('tabBtnCartDevs');
      const secCusts = document.getElementById('cartCustsTabSection');
      const secDevs = document.getElementById('cartDevsTabSection');

      if (tabCusts) {
        tabCusts.style.background = isCust ? 'var(--primary)' : 'transparent';
        tabCusts.style.color = isCust ? '#fff' : 'var(--muted)';
        tabCusts.style.fontWeight = isCust ? '800' : '600';
      }
      if (tabDevs) {
        tabDevs.style.background = !isCust ? 'var(--primary)' : 'transparent';
        tabDevs.style.color = !isCust ? '#fff' : 'var(--muted)';
        tabDevs.style.fontWeight = !isCust ? '800' : '600';
      }
      if (secCusts) secCusts.hidden = !isCust;
      if (secDevs) secDevs.hidden = isCust;
    };

    // Load Cart Data
    window.loadCartContainer = async function() {
      try {
        const [devsRes, custsRes] = await Promise.all([
          api('/api/bin').catch(() => []),
          api('/api/customers/bin').catch(() => [])
        ]);

        allCartDevs = Array.isArray(devsRes) ? devsRes : [];
        allCartCusts = Array.isArray(custsRes) ? custsRes : [];

        const totalItems = allCartDevs.length + allCartCusts.length;

        // Update badge counts across page
        const updateText = (id, val) => {
          const el = document.getElementById(id);
          if (el) el.textContent = String(val);
        };
        updateText('cartTotalHeaderBadge', `${totalItems} Total Deleted`);
        updateText('headerCartCountBadge', totalItems);
        updateText('sidebarCartCountBadge', totalItems);
        updateText('cartTabCountCusts', allCartCusts.length);
        updateText('cartTabCountDevs', allCartDevs.length);

        const errCount = allCartDevs.filter(d => (d.delete_reason || '').toLowerCase().includes('errored')).length;
        const devCount = allCartDevs.length - errCount;
        const custCount = allCartCusts.length;

        // KPI strip numbers
        updateText('statTotalItems', Number(totalItems).toLocaleString());
        updateText('statTotalCusts', Number(custCount).toLocaleString());
        updateText('statTotalDevs', Number(devCount).toLocaleString());
        updateText('statTotalErrs', Number(errCount).toLocaleString());

        updateText('cartStatCustTag', `🏢 Whole Customers: ${custCount}`);
        updateText('cartStatDevTag', `📱 Customer Entries: ${devCount}`);
        updateText('cartStatErrTag', `⚠️ Errored Entries: ${errCount}`);

        if (totalItems > 0) {
          const custPct = Math.round((custCount / totalItems) * 100);
          const devPct = Math.round((devCount / totalItems) * 100);
          const errPct = Math.max(0, 100 - custPct - devPct);

          const bCust = document.getElementById('cartBarCust');
          if (bCust) bCust.style.width = custPct + '%';
          const bDev = document.getElementById('cartBarDev');
          if (bDev) bDev.style.width = devPct + '%';
          const bErr = document.getElementById('cartBarErr');
          if (bErr) bErr.style.width = errPct + '%';
        } else {
          const bCust = document.getElementById('cartBarCust');
          if (bCust) bCust.style.width = '0%';
          const bDev = document.getElementById('cartBarDev');
          if (bDev) bDev.style.width = '0%';
          const bErr = document.getElementById('cartBarErr');
          if (bErr) bErr.style.width = '0%';
        }

        renderCartCustsTable(allCartCusts);
        renderCartDevsTable(allCartDevs);

        if (allCartCusts.length === 0 && allCartDevs.length > 0 && currentTab === 'custs') {
          switchCartTab('devs');
        }
      } catch (err) {
        console.warn('loadCartContainer notice:', err);
      }
    };

    // Render Deleted Customers Table
    function renderCartCustsTable(custs) {
      const wrap = document.getElementById('cartCustsTableWrap');
      if (!wrap) return;

      const q = (document.getElementById('cartCustSearchInput')?.value || '').trim().toLowerCase();
      const filtered = custs.filter(c => !q || (c.name || '').toLowerCase().includes(q));

      if (!filtered.length) {
        wrap.innerHTML = `
          <div class="empty" style="padding:40px 24px;background:var(--card-subtle);border-radius:16px;border:1.5px dashed var(--line);text-align:center">
            <div style="font-size:38px;margin-bottom:10px">🏢✨</div>
            <b style="font-size:16px;color:var(--text);display:block;margin-bottom:4px">${q ? 'No deleted customers match your search.' : 'Cart is clear — No deleted customers.'}</b>
            <span style="font-size:13px;color:var(--muted);display:block;margin-bottom:14px">All customer account portfolios are currently active and available in inventory.</span>
            <a class="b p" href="inventory.html" style="text-decoration:none;font-size:12.5px;font-weight:700;display:inline-flex;align-items:center;gap:6px">
              <span>📇</span> <span>View Active Customer Inventory</span>
            </a>
          </div>
        `;
        return;
      }

      wrap.innerHTML = `
        <div class="tw" style="max-height:55vh;overflow:auto;border:1px solid var(--line);border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,0.02)">
          <table style="width:100%;font-size:13px;border-collapse:collapse">
            <thead>
              <tr style="background:var(--card-subtle);text-align:left;position:sticky;top:0;z-index:5">
                <th style="padding:13px 18px">Customer Portfolio</th>
                <th style="padding:13px 18px">Associated Records</th>
                <th style="padding:13px 18px">Deleted Date</th>
                <th style="padding:13px 18px">Deleted By</th>
                <th style="padding:13px 18px;text-align:right">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.map(c => `
                <tr style="border-top:1px solid var(--line);transition:background 0.15s ease">
                  <td style="padding:14px 18px">
                    <div style="display:flex;align-items:center;gap:12px">
                      <div style="width:36px;height:36px;border-radius:10px;background:var(--card-subtle);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0">
                        🏢
                      </div>
                      <div>
                        <b style="font-size:14px;color:var(--text);display:block">${E(c.name)}</b>
                        <span style="font-size:11.5px;color:var(--muted)">Account ID #${c.id}</span>
                      </div>
                    </div>
                  </td>
                  <td style="padding:14px 18px">
                    <span class="tag mut" style="font-weight:800;font-size:12px;padding:3px 10px;border-radius:6px;background:var(--card-subtle);border:1px solid var(--line)">
                      📱 ${Number(c.devices || 0).toLocaleString()} records
                    </span>
                  </td>
                  <td style="padding:14px 18px;color:var(--muted);font-size:12.5px">
                    <span>📅 ${E((c.deleted_at || '').slice(0, 19).replace('T', ' '))}</span>
                  </td>
                  <td style="padding:14px 18px;font-family:monospace;font-size:12.5px">
                    <span style="display:inline-flex;align-items:center;gap:4px;background:var(--card-subtle);padding:2px 8px;border-radius:6px;border:1px solid var(--line)">
                      👤 <code>${E(c.deleted_by || '—')}</code>
                    </span>
                  </td>
                  <td style="padding:14px 18px;text-align:right">
                    <div style="display:inline-flex;gap:8px">
                      <button class="b" type="button" onclick="restoreCustomer(${c.id}, '${E(c.name)}')" style="height:32px;padding:0 14px;font-size:12px;font-weight:700;display:inline-flex;align-items:center;gap:6px" title="Restore customer and associated device records">
                        <span>🔄</span> <span>Restore Customer</span>
                      </button>
                      <button class="b d" type="button" onclick="purgeCustomerForever(${c.id}, '${E(c.name)}')" style="height:32px;padding:0 14px;font-size:12px;font-weight:700;display:inline-flex;align-items:center;gap:6px" title="Permanently delete customer and drop table">
                        <span>🗑️</span> <span>Delete Forever</span>
                      </button>
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }

    // Render Deleted Device Entries Table
    function renderCartDevsTable(devs) {
      const wrap = document.getElementById('cartDevsTableWrap');
      if (!wrap) return;

      const q = (document.getElementById('cartDevSearchInput')?.value || '').trim().toLowerCase();
      const colFilter = (document.getElementById('cartDevColFilter')?.value || 'all');

      const filtered = devs.filter(d => {
        if (!q) return true;
        if (colFilter === 'imei') return (d.imei || '').toLowerCase().includes(q);
        if (colFilter === 'customer_name') return (d.customer_name || '').toLowerCase().includes(q);
        if (colFilter === 'device_sr_no') return (d.device_sr_no || '').toLowerCase().includes(q);
        if (colFilter === 'iccid') return (d.iccid || '').toLowerCase().includes(q);
        if (colFilter === 'msisdn1') return (d.msisdn1 || '').toLowerCase().includes(q);
        if (colFilter === 'delete_reason') return (d.delete_reason || '').toLowerCase().includes(q);

        return (d.imei || '').toLowerCase().includes(q) ||
               (d.customer_name || '').toLowerCase().includes(q) ||
               (d.device_sr_no || '').toLowerCase().includes(q) ||
               (d.iccid || '').toLowerCase().includes(q) ||
               (d.msisdn1 || '').toLowerCase().includes(q) ||
               (d.delete_reason || '').toLowerCase().includes(q);
      });

      if (!filtered.length) {
        wrap.innerHTML = `
          <div class="empty" style="padding:40px 24px;background:var(--card-subtle);border-radius:16px;border:1.5px dashed var(--line);text-align:center">
            <div style="font-size:38px;margin-bottom:10px">📱✨</div>
            <b style="font-size:16px;color:var(--text);display:block;margin-bottom:4px">${q ? 'No deleted entries match your search.' : 'Cart is clear — No deleted device entries.'}</b>
            <span style="font-size:13px;color:var(--muted);display:block;margin-bottom:14px">All active inventory records and SIM entries are currently active and available.</span>
            <a class="b p" href="inventory.html" style="text-decoration:none;font-size:12.5px;font-weight:700;display:inline-flex;align-items:center;gap:6px">
              <span>📇</span> <span>View Active Inventory</span>
            </a>
          </div>
        `;
        return;
      }

      wrap.innerHTML = `
        <div class="tw" style="max-height:55vh;overflow:auto;border:1px solid var(--line);border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,0.02)">
          <table style="width:100%;font-size:12.5px;border-collapse:collapse">
            <thead>
              <tr style="background:var(--card-subtle);text-align:left;position:sticky;top:0;z-index:5">
                <th style="padding:12px 14px">IMEI (15-Digit)</th>
                <th style="padding:12px 14px">Customer Name</th>
                <th style="padding:12px 14px">Serial No</th>
                <th style="padding:12px 14px">ICCID / CCID</th>
                <th style="padding:12px 14px">MSISDN1</th>
                <th style="padding:12px 14px">Deleted Date</th>
                <th style="padding:12px 14px">Deleted By</th>
                <th style="padding:12px 14px">Reason</th>
                <th style="padding:12px 14px;text-align:right">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.slice(0, 500).map(d => {
                const isErr = (d.delete_reason || '').toLowerCase().includes('errored');
                return `
                  <tr style="border-top:1px solid var(--line);transition:background 0.15s ease">
                    <td style="padding:12px 14px;font-family:monospace;font-weight:800">
                      <div style="display:flex;align-items:center;gap:6px">
                        <span>${isErr ? '⚠️' : '📱'}</span>
                        <span style="letter-spacing:0.3px">${E(d.imei || '—')}</span>
                        <button class="b ghost" type="button" onclick="navigator.clipboard.writeText('${E(d.imei || '')}');showToast('IMEI Copied!','ok')" style="padding:2px 5px;height:auto;font-size:10px" title="Copy IMEI">📋</button>
                      </div>
                    </td>
                    <td style="padding:12px 14px">
                      <b style="font-size:13px;color:var(--text)">${E(d.customer_name || '—')}</b>
                    </td>
                    <td style="padding:12px 14px;font-family:monospace;font-size:12px">${E(d.device_sr_no || '—')}</td>
                    <td style="padding:12px 14px;font-family:monospace;font-size:12px">${E(d.iccid || '—')}</td>
                    <td style="padding:12px 14px;font-family:monospace;font-size:12px">${E(d.msisdn1 || '—')}</td>
                    <td style="padding:12px 14px;color:var(--muted);font-size:11.5px">
                      ${E((d.deleted_at || '').slice(0, 19).replace('T', ' '))}
                    </td>
                    <td style="padding:12px 14px;font-family:monospace;font-size:11.5px">
                      <code>${E(d.deleted_by || '—')}</code>
                    </td>
                    <td style="padding:12px 14px;max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${E(d.delete_reason || '')}">
                      <span class="sub" style="font-size:11.5px;color:var(--muted)">${E(d.delete_reason || 'Manual delete')}</span>
                    </td>
                    <td style="padding:12px 14px;text-align:right">
                      <div style="display:inline-flex;gap:6px">
                        <button class="b" type="button" onclick="restoreDevice(${d.id}, '${E(d.imei)}')" style="height:30px;padding:0 12px;font-size:11.5px;font-weight:700;display:inline-flex;align-items:center;gap:4px" title="Restore this record back to active inventory">
                          <span>🔄</span> <span>Restore</span>
                        </button>
                        <button class="b d" type="button" onclick="purgeDeviceForever(${d.id}, '${E(d.imei)}')" style="height:30px;padding:0 12px;font-size:11.5px;font-weight:700;display:inline-flex;align-items:center;gap:4px" title="Permanently erase this record forever">
                          <span>🗑️</span> <span>Delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
          ${filtered.length > 500 ? `<div style="padding:10px 16px;text-align:center;font-size:12px;color:var(--muted);background:var(--card-subtle);border-top:1px solid var(--line)">Showing first 500 of ${filtered.length} matching entries. Use search above to narrow down records.</div>` : ''}
        </div>
      `;
    }

    // Actions: Restore Customer
    window.restoreCustomer = async function(cid, custName) {
      try {
        await api(`/api/customers/${cid}/restore`, { method: 'POST' });
        showToast(`Customer "${custName}" restored to active inventory!`, 'ok');
        await loadCartContainer();
      } catch (err) {
        showToast(err.message || 'Failed to restore customer', 'bad');
      }
    };

    // Actions: Purge Customer Forever
    window.purgeCustomerForever = async function(cid, custName) {
      const ok = await askConfirm(
        `Are you sure you want to permanently delete customer "${custName}" and all associated data records from the database and TiDB Cloud?\\n\\nThis action cannot be undone.`,
        { title: 'Delete Customer Forever?', okText: 'Delete Forever', tone: 'danger' }
      );
      if (!ok) return;

      try {
        await api(`/api/customers/${cid}/purge`, { method: 'DELETE' });
        showToast(`Customer "${custName}" permanently deleted`, 'ok');
        await loadCartContainer();
      } catch (err) {
        showToast(err.message || 'Failed to permanently delete customer', 'bad');
      }
    };

    // Actions: Restore Device
    window.restoreDevice = async function(id, imei) {
      try {
        await api(`/api/bin/${id}/restore`, { method: 'POST' });
        showToast(`Record (${imei}) restored to inventory`, 'ok');
        await loadCartContainer();
      } catch (err) {
        showToast(err.message || 'Failed to restore device', 'bad');
      }
    };

    // Actions: Purge Device Forever
    window.purgeDeviceForever = async function(id, imei) {
      const ok = await askConfirm(
        `Record with IMEI "${imei}" will be permanently erased from the database and cannot be recovered.`,
        { title: 'Delete Record Forever?', okText: 'Delete Forever', tone: 'danger' }
      );
      if (!ok) return;

      try {
        await api(`/api/bin/${id}`, { method: 'DELETE' });
        showToast(`Record (${imei}) permanently deleted`, 'ok');
        await loadCartContainer();
      } catch (err) {
        showToast(err.message || 'Failed to permanently delete record', 'bad');
      }
    };

    // Actions: Restore All Entries
    window.restoreAllCartEntries = async function() {
      const total = allCartDevs.length;
      if (!total) {
        showToast('No deleted customer entries in the cart to restore.', 'info');
        return;
      }

      const ok = await askConfirm(
        `Are you sure you want to restore all ${total.toLocaleString()} deleted customer entries back to active inventory?`,
        { title: 'Restore All Records?', okText: 'Restore All', tone: 'ok' }
      );
      if (!ok) return;

      const btn = document.getElementById('btnRestoreAllCart');
      if (btn) { btn.disabled = true; btn.textContent = 'Restoring…'; }

      try {
        const res = await api('/api/bin/restore-all', { method: 'POST' });
        showToast(res.message || `Successfully restored ${res.restored || total} records!`, 'ok');
        await loadCartContainer();
      } catch (err) {
        showToast(err.message || 'Failed to restore all entries', 'bad');
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = '🔄 Restore All Entries'; }
      }
    };

    // Actions: Empty Entire Cart Forever
    window.emptyEntireCartForever = async function() {
      const totalCusts = allCartCusts.length;
      const totalDevs = allCartDevs.length;
      const grandTotal = totalCusts + totalDevs;

      if (!grandTotal) {
        showToast('Cart is already empty.', 'info');
        return;
      }

      const ok = await askConfirm(
        `⚠️ PERMANENT PURGE WARNING:\\n\\nYou are about to permanently erase all ${grandTotal.toLocaleString()} items in the Cart (${totalCusts} whole customer portfolios and ${totalDevs} customer device entries).\\n\\nThis will drop all customer tables and permanently delete every record from the database and cloud storage forever.\\n\\nType "EMPTY" to proceed.`,
        { title: 'Permanently Empty Cart Forever?', okText: 'Empty Cart Forever', tone: 'danger', typeToConfirm: 'EMPTY' }
      );
      if (!ok) return;

      const btn = document.getElementById('btnEmptyCartForever');
      const progWrap = document.getElementById('cartEmptyProgressWrap');
      const progPct = document.getElementById('cartProgPct');
      const progBar = document.getElementById('cartProgBar');
      const progRows = document.getElementById('cartProgRowsCount');
      const progLog = document.getElementById('cartProgLiveDetailBox');

      if (btn) { btn.disabled = true; btn.textContent = 'Emptying…'; }
      if (progWrap) progWrap.hidden = false;
      if (progPct) progPct.textContent = '50%';
      if (progBar) progBar.style.width = '50%';
      if (progRows) progRows.textContent = `0 / ${grandTotal} items`;
      if (progLog) progLog.innerHTML = `<div>[Starting] Dropping customer tables and purging records…</div>`;

      try {
        const res = await api('/api/bin', { method: 'DELETE' });
        if (progPct) progPct.textContent = '100%';
        if (progBar) progBar.style.width = '100%';
        if (progRows) progRows.textContent = `${grandTotal} / ${grandTotal} items`;
        if (progLog) progLog.innerHTML += `<div>[Success] Emptied ${res.deleted_forever || grandTotal} items forever!</div>`;
        showToast(`Cart permanently emptied! Deleted ${res.deleted_forever || grandTotal} items forever.`, 'ok');
        await loadCartContainer();
        setTimeout(() => { if (progWrap) progWrap.hidden = true; }, 2500);
      } catch (err) {
        showToast(err.message || 'Failed to empty cart', 'bad');
        if (progWrap) progWrap.hidden = true;
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = '🗑️ Empty Cart Forever'; }
      }
    };

    // Client-Side CSV Export
    window.exportCartListCsv = function() {
      const isCust = currentTab === 'custs';
      let csv = '';
      let filename = '';

      if (isCust) {
        if (!allCartCusts.length) { showToast('No customers to export.', 'info'); return; }
        filename = `deleted_customers_${new Date().toISOString().slice(0, 10)}.csv`;
        csv = 'Customer ID,Customer Name,Associated Records,Deleted Date,Deleted By\\n' +
          allCartCusts.map(c => `"${c.id}","${(c.name || '').replace(/"/g, '""')}","${c.devices || 0}","${c.deleted_at || ''}","${c.deleted_by || ''}"`).join('\\n');
      } else {
        if (!allCartDevs.length) { showToast('No device records to export.', 'info'); return; }
        filename = `deleted_records_${new Date().toISOString().slice(0, 10)}.csv`;
        csv = 'ID,IMEI,Customer Name,Device Serial,ICCID,MSISDN1,Deleted Date,Deleted By,Reason\\n' +
          allCartDevs.map(d => `"${d.id}","${d.imei || ''}","${(d.customer_name || '').replace(/"/g, '""')}","${d.device_sr_no || ''}","${d.iccid || ''}","${d.msisdn1 || ''}","${d.deleted_at || ''}","${d.deleted_by || ''}","${(d.delete_reason || '').replace(/"/g, '""')}"`).join('\\n');
      }

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(`Exported ${filename} successfully!`, 'ok');
    };

    // Logout Functionality
    window.logout = function(prompt = true) {
      if (prompt && !confirm('Are you sure you want to sign out?')) return;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = 'index.html';
    };

    // Initialize Page
    document.addEventListener('DOMContentLoaded', () => {
      // Hook search inputs
      const custSearch = document.getElementById('cartCustSearchInput');
      if (custSearch) {
        custSearch.addEventListener('input', () => renderCartCustsTable(allCartCusts));
      }
      const devSearch = document.getElementById('cartDevSearchInput');
      if (devSearch) {
        devSearch.addEventListener('input', () => renderCartDevsTable(allCartDevs));
      }

      loadUserProfile();
      loadTelemetry();
      loadCartContainer();

      // Poll telemetry and cart every 15 seconds
      setInterval(() => {
        loadTelemetry();
      }, 15000);
    });
  </script>
"""

# Construct full cart.html
cart_html = f"""{head_part}
<link rel="stylesheet" href="cv-popup.css">
<script src="cv-popup.js"></script>
</head>
<body class="app-active">
  <div id="dashboardWrap" class="cv-app-shell" style="display:flex">

    {sidebar_html}

    <main class="cv-main-panel" id="cvMainPanel">

      {header_html}

      {banner_html}

      {cart_main_content}

    </main>
  </div>

  {cart_dialogs}

  {cart_script}
</body>
</html>
"""

with open('frontend/cart.html', 'w', encoding='utf-8') as f:
    f.write(cart_html)

print("Redesigned frontend/cart.html successfully!")
print("New file size:", len(cart_html), "bytes")

