import re, sys

print("Building complete comprehensive patch for build_clean_modular_app.py...")

with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    text = f.read()

# -----------------------------------------------------------------------------
# 1. UPDATE containers['box-inv'] in builder
# -----------------------------------------------------------------------------
anchor_start = "# 2.5 Customize containers['box-inv']"
anchor_end = "containers['box-inv'] = box_inv_html"

idx_start = text.find(anchor_start)
idx_end = text.find(anchor_end, idx_start)

if idx_start != -1 and idx_end != -1:
    new_inv_custom_block = r'''# 2.5 Customize containers['box-inv'] (Subnav, Search, Metrics Ribbon, Check Entries & Rectify)
box_inv_html = containers['box-inv']

# Design Subnav: 📋 Device Records | 📁 Customer Files (154) | 📤 Bulk Upload
old_subnav_re = r'<div class="inv-subnav" role="tablist">[\s\S]*?</div>'
new_subnav_html = """<div class="inv-subnav" role="tablist" style="display:flex;gap:10px;margin:18px 0;border-bottom:1px solid var(--line);padding-bottom:12px;flex-wrap:wrap">
        <button class="inv-sub-btn active" id="btnSubDevices" data-sub="devices" type="button" style="display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:10px;font-size:13.5px;font-weight:700;cursor:pointer;border:1.5px solid var(--line);background:var(--card);color:var(--text);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)">
          <span>📋</span> <span>Device Records</span>
        </button>
        <button class="inv-sub-btn" id="btnSubCust" data-sub="cust" type="button" style="display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:10px;font-size:13.5px;font-weight:700;cursor:pointer;border:1.5px solid var(--line);background:var(--card);color:var(--text);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)">
          <span>📁</span> <span>Customer Files</span> (<span id="invCustCountBadge">154</span>)
        </button>
        <button class="inv-sub-btn" id="btnSubUpload" data-sub="upload" type="button" style="display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:10px;font-size:13.5px;font-weight:700;cursor:pointer;border:1.5px solid var(--line);background:var(--card);color:var(--text);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)">
          <span>📤</span> <span>Bulk Upload</span>
        </button>
      </div>"""
box_inv_html = re.sub(old_subnav_re, new_subnav_html, box_inv_html, count=1)

# Design Search Customer Cards Bar & Action Toolbar in subViewCust
old_cust_search_re = r'<div class="row" style="margin-top:14px">\s*<div class="grow">\s*<label for="cs">Search Customer Cards</label>\s*<input id="cs" placeholder="Filter by customer name…" />\s*</div>\s*</div>'
new_cust_search_html = """<div style="margin-top:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
            <div style="flex:1;max-width:480px;min-width:240px">
              <label for="cs" style="font-size:13px;font-weight:800;color:var(--text);display:block;margin-bottom:6px">
                Search Customer Cards
              </label>
              <div class="cv-search-container">
                <span class="cv-search-icon-left">🔎</span>
                <input id="cs" class="cv-search-input" placeholder="Filter by customer name…" autocomplete="off" />
                <button type="button" class="cv-search-clear-btn" id="csClearBtn" title="Clear filter" style="display:none">✕</button>
              </div>
            </div>
            <div style="font-size:12.5px;color:var(--muted);font-weight:700;margin-top:auto" id="csFilterCount">
              Showing all customer portfolios
            </div>
          </div>"""
box_inv_html = re.sub(old_cust_search_re, new_cust_search_html, box_inv_html, count=1)
box_inv_html = box_inv_html.replace('<div id="cgrid"></div>', '<div id="cgrid" style="margin-top:16px"></div>')

# Upgrade Bulk Upload Status Metrics Ribbon (Requirement 1 & 2)
old_stats_ribbon_re = r'<div class="stats"[^>]*>\s*<div class="card stat"[^>]*><b id="vTotalScanned">[\s\S]*?</div>\s*</div>'
new_stats_ribbon_html = """<div class="stats" style="margin-top:10px;grid-template-columns:repeat(auto-fit, minmax(135px, 1fr));gap:10px">
              <div class="card stat" style="border-left-color:var(--primary);padding:12px 14px"><b id="vTotalScanned">0</b><span>📄 Total Scanned</span></div>
              <div class="card stat" style="border-left-color:#10b981;padding:12px 14px"><b id="vValid">0</b><span>✅ Valid Entries</span></div>
              <div class="card stat" style="border-left-color:var(--ok);padding:12px 14px"><b id="vNew" style="color:var(--ok)">0</b><span>✨ New (Insert)</span></div>
              <div class="card stat" style="border-left-color:var(--warn);padding:12px 14px"><b id="vUpdatedCount" style="color:var(--warn)">0</b><span>🔄 Requires Update</span></div>
              <div class="card stat" style="border-left-color:#94a3b8;padding:12px 14px"><b id="vExistingCountCard">0</b><span>📋 Existing in DB</span></div>
              <div class="card stat" style="border-left-color:#f97316;padding:12px 14px"><b id="vDup" style="color:#f97316">0</b><span>⚠️ Duplicates</span></div>
              <div class="card stat" style="border-left-color:var(--danger);padding:12px 14px"><b id="vInvalidCount" style="color:var(--danger)">0</b><span>❌ Invalids</span></div>
            </div>"""
box_inv_html = re.sub(old_stats_ribbon_re, new_stats_ribbon_html, box_inv_html, count=1)

# Upgrade Filter Buttons in subViewUpload
old_filter_btns_re = r'<div style="display:flex;gap:6px;flex-wrap:wrap" id="valFilterBtns">[\s\S]*?</div>'
new_filter_btns_html = """<div style="display:flex;gap:6px;flex-wrap:wrap" id="valFilterBtns">
                  <button class="b on" data-valfilter="new" type="button" id="btnFilterNew" style="font-weight:700;color:var(--ok)">✨ New (<span id="vNewCount">0</span>)</button>
                  <button class="b" data-valfilter="update" type="button" id="btnFilterUpdate" style="font-weight:700;color:var(--warn)">🔄 Requires Update (<span id="vUpdatedBtnCount">0</span>)</button>
                  <button class="b" data-valfilter="existing" type="button" id="btnFilterExisting">📋 Existing (<span id="vExistingCount">0</span>)</button>
                  <button class="b" data-valfilter="duplicate" type="button" id="btnFilterDup">⚠️ Duplicates (<span id="vDupCount">0</span>)</button>
                  <button class="b" data-valfilter="invalid" type="button" id="btnFilterInvalid" style="font-weight:700;color:var(--danger)">❌ Invalids (<span id="vInvalidBtnCount">0</span>)</button>
                </div>"""
box_inv_html = re.sub(old_filter_btns_re, new_filter_btns_html, box_inv_html, count=1)

# Add Check Entries & Rectify Update Action Buttons
old_action_bar_re = r'<div style="display:flex;gap:12px;align-items:center;margin-top:14px;flex-wrap:wrap">[\s\S]*?</div>'
new_action_bar_html = """<div style="display:flex;gap:10px;align-items:center;margin-top:16px;flex-wrap:wrap">
              <button class="b p" id="btnCheckEntriesModal" type="button"
                style="padding:11px 20px;font-size:14px;font-weight:800;border-radius:9px;background:linear-gradient(135deg, #0284c7, #2563eb);color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 12px rgba(37,99,235,0.25);cursor:pointer">
                <span>🔍</span> <span>Check Entries (Inspect Differences)</span>
              </button>
              <button class="b p" id="btnRectifyUpdate" type="button"
                style="padding:11px 20px;font-size:14px;font-weight:800;border-radius:9px;background:linear-gradient(135deg, #d97706, #b45309);color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 12px rgba(217,119,6,0.25);cursor:pointer">
                <span>🔄</span> <span>Rectify Update (<span id="btnRectifyCountBadge">0</span> Records)</span>
              </button>
              <button class="b p" id="btnConfirmUpload" type="button"
                style="padding:11px 20px;font-size:14px;font-weight:800;border-radius:9px;background:linear-gradient(135deg, var(--ok), #059669);color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 12px rgba(16,185,129,0.25);cursor:pointer">
                <span>🚀</span> <span>Upload & Insert New (<span id="btnInsertNewCountBadge">0</span>)</span>
              </button>
              <button class="b" id="btnDownloadPreUploadReport" type="button" style="font-size:13px;padding:10px 16px;cursor:pointer">
                📥 Download Validation Report (Excel)
              </button>
            </div>"""
box_inv_html = re.sub(old_action_bar_re, new_action_bar_html, box_inv_html, count=1)

containers['box-inv'] = box_inv_html'''

    text = text[:idx_start] + new_inv_custom_block + text[idx_end + len(anchor_end):]
    print("✓ Successfully injected updated containers['box-inv'] with slice replacement")

with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Patch complete!")
