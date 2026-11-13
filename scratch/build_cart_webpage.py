import os
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
         CONTAINER: CART & RECYCLE BIN (Dedicated Standalone Webpage)
         ========================================================================= -->
      <section class="container-box active" id="box-cart" style="display:block;padding:24px 28px;background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:0 4px 24px rgba(0,0,0,0.03);margin-bottom:28px">
        
        <!-- Cart Header Ribbon -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:22px;flex-wrap:wrap;gap:16px;border-bottom:1px solid var(--line);padding-bottom:18px">
          <div style="display:flex;align-items:center;gap:14px">
            <div style="width:52px;height:52px;border-radius:14px;background:var(--card-subtle);border:1.5px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:26px;box-shadow:0 3px 10px rgba(0,0,0,0.06);flex-shrink:0">
              🛒
            </div>
            <div>
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <h2 style="margin:0;font-size:22px;font-weight:800;color:var(--text)">Cart &amp; Recycle Bin</h2>
                <span class="tag ok" id="cartTotalHeaderBadge" style="font-weight:800;font-size:12.5px;padding:4px 10px;border-radius:99px">0 Total Items</span>
              </div>
              <p class="sub" style="margin:3px 0 0;font-size:13px;color:var(--muted)">Recover deleted entries of customers or whole customer portfolios. Restore with 1 click or permanently purge forever.</p>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <button class="b" id="btnRestoreAllCart" type="button" onclick="restoreAllCartEntries()" style="font-weight:700;font-size:13px;padding:9px 16px" title="Restore all deleted customer entries to inventory">🔄 Restore All Entries</button>
            <button class="b d" id="btnEmptyCartForever" type="button" onclick="emptyEntireCartForever()" style="font-weight:700;font-size:13px;padding:9px 16px" title="Permanently delete all items in the cart">🗑️ Empty Cart Forever</button>
            <a class="b p" href="home.html" style="text-decoration:none;font-weight:700;font-size:13px;padding:9px 16px;display:inline-flex;align-items:center;gap:6px">🏠 Return to Main Page</a>
          </div>
        </div>

        <!-- Live Composition & Summary Banner -->
        <div class="card" id="cartSummaryBannerWrap" style="padding:18px 20px;border:1px solid var(--line);margin-bottom:20px;background:var(--card-subtle);border-radius:14px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:10px">
            <div style="display:flex;align-items:center;gap:10px">
              <b style="font-size:14.5px;color:var(--text);display:flex;align-items:center;gap:6px">
                <span>📊</span> <span>Cart Composition &amp; Breakdown</span>
              </b>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap" id="cartBreakdownTags">
              <span class="tag" style="background:rgba(2,132,199,0.12);color:#0284c7;font-weight:700" id="cartStatCustTag">🏢 Whole Customers: 0</span>
              <span class="tag" style="background:rgba(37,99,235,0.12);color:#2563eb;font-weight:700" id="cartStatDevTag">📱 Customer Entries: 0</span>
              <span class="tag bad" style="font-weight:700" id="cartStatErrTag">⚠️ Errored Entries: 0</span>
            </div>
          </div>
          <!-- Multi-Segment Visual Progress / Composition Bar -->
          <div style="height:12px;background:var(--card);border-radius:6px;overflow:hidden;display:flex;border:1px solid var(--line)">
            <div id="cartBarCust" style="width:0%;background:linear-gradient(90deg, #0284c7, #38bdf8);transition:width 0.3s ease" title="Whole Customers"></div>
            <div id="cartBarDev" style="width:0%;background:linear-gradient(90deg, #2563eb, #60a5fa);transition:width 0.3s ease" title="Customer Entries"></div>
            <div id="cartBarErr" style="width:0%;background:linear-gradient(90deg, #ef4444, #f97316);transition:width 0.3s ease" title="Errored Records"></div>
          </div>
        </div>

        <!-- Cart Deletion Progress Container (when emptying) -->
        <div id="cartEmptyProgressWrap" hidden style="margin:0 0 20px;background:var(--card);padding:20px;border:1.5px solid var(--danger, #ef4444);border-radius:14px;box-shadow:0 6px 20px rgba(239,68,68,0.12)">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px">
            <div style="display:flex;align-items:center;gap:10px">
              <span id="cartProgSpinIcon" class="spin" style="font-size:22px">⏳</span>
              <div>
                <b id="cartProgTitle" style="font-size:15px;color:var(--text)">Emptying Cart Forever (Permanent Deletion)…</b>
                <div id="cartProgStatus" style="font-size:12.5px;color:var(--danger, #dc2626);font-weight:600;margin-top:2px">Preparing deletion…</div>
              </div>
            </div>
            <div style="text-align:right">
              <span id="cartProgPct" style="font-size:20px;font-weight:800;color:var(--danger, #dc2626)">0%</span>
              <div id="cartProgRowsCount" style="font-size:12px;font-weight:600;color:var(--muted)">0 / 0 records</div>
            </div>
          </div>
          <div class="progress-bar" style="height:12px;background:var(--card-subtle);border-radius:6px;overflow:hidden;margin:10px 0;border:1px solid var(--line)">
            <div class="progress-fill" id="cartProgBar" style="width:0%;height:100%;background:linear-gradient(90deg, #ef4444, #dc2626);transition:width 0.2s ease"></div>
          </div>
          <div id="cartProgLiveDetailBox" style="background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font-size:12px;max-height:90px;overflow-y:auto;font-family:monospace;margin-top:10px;color:var(--muted)">
            [Ready] Deletion in progress…
          </div>
        </div>

        <!-- Tab Switcher -->
        <div style="display:flex;gap:12px;border-bottom:2px solid var(--line);margin-bottom:22px">
          <button type="button" class="b ghost" id="tabBtnCartCusts" onclick="switchCartTab('custs')" style="border-radius:0;padding:12px 20px;font-size:14px;border-bottom:3px solid var(--primary);font-weight:800;color:var(--text);cursor:pointer">
            🏢 Deleted Customers (<span id="cartTabCountCusts">0</span>)
          </button>
          <button type="button" class="b ghost" id="tabBtnCartDevs" onclick="switchCartTab('devs')" style="border-radius:0;padding:12px 20px;font-size:14px;border-bottom:3px solid transparent;font-weight:600;color:var(--muted);cursor:pointer">
            📱 Deleted Entries of Customers (<span id="cartTabCountDevs">0</span>)
          </button>
        </div>

        <!-- Section 1: Deleted Whole Customers Tab -->
        <div id="cartCustsTabSection">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:12px">
            <div>
              <h4 style="margin:0;font-size:15.5px;font-weight:800;color:var(--text)">🏢 Deleted Whole Customers</h4>
              <p class="sub" style="margin:3px 0 0;font-size:12.5px">Entire customer accounts that were moved to the Recycle Bin. Restoring brings back the account and all device records.</p>
            </div>
            <div class="cv-search-container" style="min-width:260px">
              <span class="cv-search-icon-left">🔎</span>
              <input id="cartCustSearchInput" class="cv-search-input" style="height:38px;font-size:13px" placeholder="Search customer name…" />
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
              <h4 style="margin:0;font-size:15.5px;font-weight:800;color:var(--text)">📱 Deleted Customer Entries &amp; Device Records</h4>
              <p class="sub" style="margin:3px 0 0;font-size:12.5px">Individual device records, SIM entries, and staged errored items that were placed into Cart.</p>
            </div>
            <div class="cv-search-container" style="min-width:320px">
              <span class="cv-search-icon-left">🔎</span>
              <input id="cartDevSearchInput" class="cv-search-input" style="height:38px;font-size:13px" placeholder="Search IMEI, customer name, serial number…" />
            </div>
          </div>
          <div id="cartDevsTableWrap">
            <div class="empty">Checking for deleted entries…</div>
          </div>
        </div>

      </section>
"""

cart_dialogs = """
  <!-- Custom Confirmation Dialog -->
  <dialog id="dlgCartConfirm" class="modal-card" style="width:min(500px, 94vw); padding:0; border-radius:18px; border:1px solid var(--line); box-shadow:0 30px 80px rgba(0,0,0,0.5); overflow:hidden">
    <div style="padding:18px 22px; display:flex; align-items:center; gap:12px; background:var(--card-subtle); border-bottom:1px solid var(--line)">
      <div id="confirmIconBox" style="width:42px;height:42px;border-radius:10px;background:var(--card);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">
        ⚠️
      </div>
      <div style="flex:1">
        <h3 id="confirmTitle" style="margin:0;font-size:16px;font-weight:800;color:var(--text)">Confirm Action</h3>
        <p id="confirmSubtitle" style="margin:2px 0 0;font-size:12px;color:var(--muted)">Please confirm before proceeding.</p>
      </div>
      <button class="b ghost" type="button" onclick="closeConfirmDialog(false)" style="font-size:18px;min-width:34px;min-height:34px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;border-radius:8px">✕</button>
    </div>
    <div style="padding:20px 22px">
      <p id="confirmMessage" style="margin:0 0 16px;font-size:14px;line-height:1.55;color:var(--text)"></p>
      <div id="confirmTypeWrap" hidden style="margin-bottom:16px">
        <label for="confirmTypeInput" style="display:block;margin-bottom:6px;font-size:12.5px;font-weight:700">Type <code id="confirmTypePrompt" style="color:var(--danger);font-weight:800">CONFIRM</code> to verify:</label>
        <input id="confirmTypeInput" placeholder="Type here…" style="width:100%;height:38px;padding:0 12px;font-size:13px;border-radius:8px;border:1.5px solid var(--line)" />
      </div>
      <div style="display:flex;justify-content:flex-end;gap:10px">
        <button class="b" type="button" onclick="closeConfirmDialog(false)">Cancel</button>
        <button class="b d" id="btnConfirmProceed" type="button" onclick="closeConfirmDialog(true)">Proceed</button>
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
    function askConfirm(msg, { title = 'Confirm Action', subtitle = 'Please confirm before proceeding', okText = 'Proceed', tone = 'danger', typeToConfirm = '' } = {}) {
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
        tabCusts.style.borderBottom = isCust ? '3px solid var(--primary)' : '3px solid transparent';
        tabCusts.style.fontWeight = isCust ? '800' : '600';
        tabCusts.style.color = isCust ? 'var(--text)' : 'var(--muted)';
      }
      if (tabDevs) {
        tabDevs.style.borderBottom = !isCust ? '3px solid var(--primary)' : '3px solid transparent';
        tabDevs.style.fontWeight = !isCust ? '800' : '600';
        tabDevs.style.color = !isCust ? 'var(--text)' : 'var(--muted)';
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

        // Update badge counts
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
          <div class="empty" style="padding:32px 20px;background:var(--card-subtle);border-radius:14px;border:1px dashed var(--line);text-align:center">
            <div style="font-size:32px;margin-bottom:8px">🏢</div>
            <b style="font-size:15px;color:var(--text);display:block">${q ? 'No deleted customers match your search.' : 'No whole customers currently in Cart.'}</b>
            <span style="font-size:12.5px;color:var(--muted)">All customer account portfolios are active.</span>
          </div>
        `;
        return;
      }

      wrap.innerHTML = `
        <div class="tw" style="max-height:55vh;overflow:auto;border:1px solid var(--line);border-radius:14px">
          <table style="width:100%;font-size:13px;border-collapse:collapse">
            <thead>
              <tr style="background:var(--card-subtle);text-align:left;position:sticky;top:0;z-index:5">
                <th style="padding:12px 16px">Customer Portfolio</th>
                <th style="padding:12px 16px">Associated Records</th>
                <th style="padding:12px 16px">Deleted On</th>
                <th style="padding:12px 16px">Deleted By</th>
                <th style="padding:12px 16px;text-align:right">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.map(c => `
                <tr style="border-top:1px solid var(--line);transition:background 0.15s ease">
                  <td style="padding:12px 16px">
                    <div style="display:flex;align-items:center;gap:10px">
                      <span style="font-size:20px">🏢</span>
                      <div>
                        <b style="font-size:14px;color:var(--text);display:block">${E(c.name)}</b>
                        <span style="font-size:11px;color:var(--muted)">Customer ID #${c.id}</span>
                      </div>
                    </div>
                  </td>
                  <td style="padding:12px 16px">
                    <span class="tag mut" style="font-weight:700;font-size:12px">${Number(c.devices || 0).toLocaleString()} records</span>
                  </td>
                  <td style="padding:12px 16px;color:var(--muted);font-size:12.5px">
                    ${E((c.deleted_at || '').slice(0, 19).replace('T', ' '))}
                  </td>
                  <td style="padding:12px 16px;font-family:monospace;font-size:12px">
                    <code>${E(c.deleted_by || '—')}</code>
                  </td>
                  <td style="padding:12px 16px;text-align:right">
                    <div style="display:inline-flex;gap:8px">
                      <button class="b" type="button" onclick="restoreCustomer(${c.id}, '${E(c.name)}')" style="height:32px;padding:0 14px;font-size:12px;font-weight:700" title="Restore customer and associated device records">
                        🔄 Restore Customer
                      </button>
                      <button class="b d" type="button" onclick="purgeCustomerForever(${c.id}, '${E(c.name)}')" style="height:32px;padding:0 14px;font-size:12px;font-weight:700" title="Permanently delete customer and drop table">
                        🗑️ Delete Forever
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
      const filtered = devs.filter(d => {
        if (!q) return true;
        return (d.imei || '').toLowerCase().includes(q) ||
               (d.customer_name || '').toLowerCase().includes(q) ||
               (d.device_sr_no || '').toLowerCase().includes(q) ||
               (d.iccid || '').toLowerCase().includes(q) ||
               (d.msisdn1 || '').toLowerCase().includes(q) ||
               (d.delete_reason || '').toLowerCase().includes(q);
      });

      if (!filtered.length) {
        wrap.innerHTML = `
          <div class="empty" style="padding:32px 20px;background:var(--card-subtle);border-radius:14px;border:1px dashed var(--line);text-align:center">
            <div style="font-size:32px;margin-bottom:8px">📱</div>
            <b style="font-size:15px;color:var(--text);display:block">${q ? 'No deleted entries match your search.' : 'Cart is empty. No deleted customer entries or device records.'}</b>
            <span style="font-size:12.5px;color:var(--muted)">All active inventory records are currently active and available.</span>
          </div>
        `;
        return;
      }

      wrap.innerHTML = `
        <div class="tw" style="max-height:55vh;overflow:auto;border:1px solid var(--line);border-radius:14px">
          <table style="width:100%;font-size:12.5px;border-collapse:collapse">
            <thead>
              <tr style="background:var(--card-subtle);text-align:left;position:sticky;top:0;z-index:5">
                <th style="padding:11px 14px">IMEI (15-Digit)</th>
                <th style="padding:11px 14px">Customer Name</th>
                <th style="padding:11px 14px">Serial No</th>
                <th style="padding:11px 14px">ICCID</th>
                <th style="padding:11px 14px">MSISDN1</th>
                <th style="padding:11px 14px">Deleted On</th>
                <th style="padding:11px 14px">Deleted By</th>
                <th style="padding:11px 14px">Reason</th>
                <th style="padding:11px 14px;text-align:right">Actions</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.slice(0, 500).map(d => {
                const isErr = (d.delete_reason || '').toLowerCase().includes('errored');
                return `
                  <tr style="border-top:1px solid var(--line);transition:background 0.15s ease">
                    <td style="padding:11px 14px;font-family:monospace;font-weight:700">
                      <span>${isErr ? '⚠️ ' : '📱 '}${E(d.imei || '—')}</span>
                    </td>
                    <td style="padding:11px 14px">
                      <b>${E(d.customer_name || '—')}</b>
                    </td>
                    <td style="padding:11px 14px;font-family:monospace;font-size:12px">${E(d.device_sr_no || '—')}</td>
                    <td style="padding:11px 14px;font-family:monospace;font-size:12px">${E(d.iccid || '—')}</td>
                    <td style="padding:11px 14px;font-family:monospace;font-size:12px">${E(d.msisdn1 || '—')}</td>
                    <td style="padding:11px 14px;color:var(--muted);font-size:11.5px">
                      ${E((d.deleted_at || '').slice(0, 19).replace('T', ' '))}
                    </td>
                    <td style="padding:11px 14px;font-family:monospace;font-size:11.5px">
                      <code>${E(d.deleted_by || '—')}</code>
                    </td>
                    <td style="padding:11px 14px;max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${E(d.delete_reason || '')}">
                      <span class="sub" style="font-size:11.5px;color:var(--muted)">${E(d.delete_reason || 'Manual delete')}</span>
                    </td>
                    <td style="padding:11px 14px;text-align:right">
                      <div style="display:inline-flex;gap:6px">
                        <button class="b" type="button" onclick="restoreDevice(${d.id}, '${E(d.imei)}')" style="height:28px;padding:0 12px;font-size:11.5px;font-weight:700" title="Restore this record back to active inventory">
                          🔄 Restore
                        </button>
                        <button class="b d" type="button" onclick="purgeDeviceForever(${d.id}, '${E(d.imei)}')" style="height:28px;padding:0 12px;font-size:11.5px;font-weight:700" title="Permanently erase this record forever">
                          🗑️ Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
          ${filtered.length > 500 ? `<div style="padding:10px 16px;text-align:center;font-size:12px;color:var(--muted);background:var(--card-subtle)">Showing first 500 of ${filtered.length} matching entries. Use search above to narrow down.</div>` : ''}
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

# Clean any remaining references in cart_html
with open('frontend/cart.html', 'w', encoding='utf-8') as f:
    f.write(cart_html)

print("Created frontend/cart.html successfully!")
print("File size:", len(cart_html), "bytes")
