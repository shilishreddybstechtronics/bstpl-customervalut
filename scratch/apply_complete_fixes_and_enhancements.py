import re

print("Applying Complete Fixes and Enhancements to build_clean_modular_app.py...")

with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    text = f.read()

# -----------------------------------------------------------------------------
# 1. FIX BSTPI / BSTPL LOADER (Requirement 3)
# -----------------------------------------------------------------------------
old_loader_block = r'''    // --- Branded 3D Loader & Notification System (Logo + Message on Search/Load) ---
    function showBstplLoader(msg = 'Searching & loading records…') {
      let loader = $('cvGlobalLoader');
      if (!loader) {
        loader = document.createElement('div');
        loader.id = 'cvGlobalLoader';
        loader.className = 'cv-global-loader';
        loader.innerHTML = `
          <div class="cv-loader-backdrop"></div>
          <div class="cv-loader-card">
            <div class="cv-loader-logo-wrap">
              <div class="cv-loader-logo-3d">B</div>
            </div>
            <div class="cv-loader-brand-title">BSTPL <span>CustomerVault</span></div>
            <div class="cv-loader-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>
            <div class="cv-loader-msg" id="cvLoaderMsg">${esc(msg)}</div>
            <div class="cv-loader-progress"><div class="cv-loader-progress-bar"></div></div>
          </div>
        `;
        document.body.appendChild(loader);
      }
      const msgEl = $('cvLoaderMsg');
      if (msgEl) msgEl.textContent = msg;
      loader.style.display = 'flex';
    }

    function hideBstplLoader() {
      const loader = $('cvGlobalLoader');
      if (loader) loader.style.display = 'none';
    }'''

new_loader_block = '''    // --- Branded 3D Loader & Notification System (Logo + Message on Search/Load) ---
    function showBstplLoader(msg = 'Searching & loading records…', pct = null) {
      let loader = $('cvGlobalLoader');
      if (!loader) {
        loader = document.createElement('div');
        loader.id = 'cvGlobalLoader';
        loader.className = 'cv-global-loader';
        loader.innerHTML = `
          <div class="cv-loader-backdrop"></div>
          <div class="cv-loader-card">
            <div class="cv-loader-logo-wrap">
              <div class="cv-loader-logo-3d">B</div>
            </div>
            <div class="cv-loader-brand-title">BSTPL <span>CustomerVault</span></div>
            <div class="cv-loader-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>
            <div class="cv-loader-msg" id="cvLoaderMsg">${esc(msg)}</div>
            <div class="cv-loader-progress"><div class="cv-loader-progress-bar"></div></div>
          </div>
        `;
        document.body.appendChild(loader);
      }
      const msgEl = $('cvLoaderMsg');
      if (msgEl && msg != null) msgEl.textContent = msg;
      const bar = loader.querySelector('.cv-loader-progress-bar');
      if (bar && pct != null) {
        bar.style.width = Math.max(0, Math.min(100, pct)) + '%';
      }
      loader.style.display = 'flex';
    }

    function updateBstplLoader(msg = null, pct = null) {
      let loader = $('cvGlobalLoader');
      if (!loader) {
        showBstplLoader(msg || 'Processing…', pct);
        return;
      }
      if (msg != null) {
        const msgEl = $('cvLoaderMsg');
        if (msgEl) msgEl.textContent = msg;
      }
      if (pct != null) {
        const bar = loader.querySelector('.cv-loader-progress-bar');
        if (bar) bar.style.width = Math.max(0, Math.min(100, pct)) + '%';
      }
    }

    function hideBstplLoader() {
      const loader = $('cvGlobalLoader');
      if (loader) loader.style.display = 'none';
    }

    // Compatibility aliases for BSTPI / BSTPL loader calls (Requirement 3)
    window.showBstplLoader = showBstplLoader;
    window.updateBstplLoader = updateBstplLoader;
    window.hideBstplLoader = hideBstplLoader;
    window.showBSTPILoader = showBstplLoader;
    window.updateBSTPILoader = updateBstplLoader;
    window.hideBSTPILoader = hideBstplLoader;'''

if old_loader_block in text:
    text = text.replace(old_loader_block, new_loader_block)
    print("✓ Updated showBstplLoader, added updateBstplLoader and window.updateBSTPILoader aliases")

# -----------------------------------------------------------------------------
# 2. CUSTOMER INVENTORY – BULK UPLOAD STATUS & CHECK ENTRIES / RECTIFY UPDATE
# -----------------------------------------------------------------------------
# Update containers['box-inv']: Add Metric Cards, Check Entries Button, Rectify Button
old_val_summary_ribbon = r'''            <!-- Bulk Upload Status Metric Cards (Requirement 10: Only New Records & Total Scanned File Count) -->
            <div class="stats" style="margin-top:10px;grid-template-columns:repeat(auto-fit, minmax(170px, 1fr));gap:10px">
              <div class="card stat" style="border-left-color:var(--primary);padding:12px 14px"><b id="vTotalScanned">0</b><span>📄 Total Scanned File Rows</span></div>
              <div class="card stat" style="border-left-color:var(--ok);padding:12px 14px"><b id="vNew" style="color:var(--ok)">0</b><span>✨ Total New Records</span></div>
              <div class="card stat" style="border-left-color:#10b981;padding:12px 14px"><b id="vValid">0</b><span>✅ Ready for Insertion</span></div>
              <div class="card stat" style="border-left-color:#94a3b8;padding:12px 14px"><b id="vExistingCountCard">0</b><span>📋 Skipped Existing Records</span></div>
              <div class="card stat" style="border-left-color:#ef4444;padding:12px 14px"><b id="vDup" style="color:#ef4444">0</b><span>⚠️ Duplicate File Entries</span></div>
            </div>'''

new_val_summary_ribbon = '''            <!-- Complete Bulk Upload Status Metric Cards (Requirements 1 & 2) -->
            <div class="stats" style="margin-top:10px;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:10px">
              <div class="card stat" style="border-left-color:var(--primary);padding:12px 14px"><b id="vTotalScanned">0</b><span>📄 Total Scanned</span></div>
              <div class="card stat" style="border-left-color:#10b981;padding:12px 14px"><b id="vValid">0</b><span>✅ Valid Entries</span></div>
              <div class="card stat" style="border-left-color:var(--ok);padding:12px 14px"><b id="vNew" style="color:var(--ok)">0</b><span>✨ New Entries (Insert)</span></div>
              <div class="card stat" style="border-left-color:var(--warn);padding:12px 14px"><b id="vUpdatedCount" style="color:var(--warn)">0</b><span>🔄 Requires Update</span></div>
              <div class="card stat" style="border-left-color:#94a3b8;padding:12px 14px"><b id="vExistingCountCard">0</b><span>📋 Existing (Identical)</span></div>
              <div class="card stat" style="border-left-color:#f97316;padding:12px 14px"><b id="vDup" style="color:#f97316">0</b><span>⚠️ File Duplicates</span></div>
              <div class="card stat" style="border-left-color:var(--danger);padding:12px 14px"><b id="vInvalidCount" style="color:var(--danger)">0</b><span>❌ Invalid Entries</span></div>
            </div>'''

if old_val_summary_ribbon in text:
    text = text.replace(old_val_summary_ribbon, new_val_summary_ribbon)
    print("✓ Updated Bulk Upload Status metric ribbon with Requires Update & Invalids")

# Update Filter Buttons in subViewUpload to include Requires Update and Invalids
old_val_filter_btns = r'''                <div style="display:flex;gap:6px;flex-wrap:wrap" id="valFilterBtns">
                  <button class="b on" data-valfilter="new" type="button" id="btnFilterNew" style="font-weight:700;color:var(--ok)">✨ New Records Eligible for Insertion (<span id="vNewCount">0</span>)</button>
                  <button class="b" data-valfilter="existing" type="button" id="btnFilterExisting">📋 Skipped Existing in DB (<span id="vExistingCount">0</span>)</button>
                  <button class="b" data-valfilter="duplicate" type="button" id="btnFilterDup">⚠️ File Duplicates (<span id="vDupCount">0</span>)</button>
                </div>'''

new_val_filter_btns = '''                <div style="display:flex;gap:6px;flex-wrap:wrap" id="valFilterBtns">
                  <button class="b on" data-valfilter="new" type="button" id="btnFilterNew" style="font-weight:700;color:var(--ok)">✨ New (<span id="vNewCount">0</span>)</button>
                  <button class="b" data-valfilter="update" type="button" id="btnFilterUpdate" style="font-weight:700;color:var(--warn)">🔄 Requires Update (<span id="vUpdatedBtnCount">0</span>)</button>
                  <button class="b" data-valfilter="existing" type="button" id="btnFilterExisting">📋 Existing (<span id="vExistingCount">0</span>)</button>
                  <button class="b" data-valfilter="duplicate" type="button" id="btnFilterDup">⚠️ Duplicates (<span id="vDupCount">0</span>)</button>
                  <button class="b" data-valfilter="invalid" type="button" id="btnFilterInvalid" style="font-weight:700;color:var(--danger)">❌ Invalids (<span id="vInvalidBtnCount">0</span>)</button>
                </div>'''

if old_val_filter_btns in text:
    text = text.replace(old_val_filter_btns, new_val_filter_btns)
    print("✓ Updated valFilterBtns with Requires Update and Invalids")

# Add "Check Entries" & "Rectify Update" buttons into the subViewUpload action bar
old_upload_actions = r'''            <div style="display:flex;gap:12px;align-items:center;margin-top:14px;flex-wrap:wrap">
              <button class="b p" id="btnConfirmUpload" type="button"
                style="padding:12px 24px;font-size:14.5px;font-weight:800;border-radius:10px;background:linear-gradient(135deg, var(--ok), #059669);display:inline-flex;align-items:center;gap:8px;box-shadow:0 4px 14px rgba(16,185,129,0.3)">
                <span>🚀</span> <span>Upload & Insert Valid Records</span>
              </button>
              <button class="b" id="btnDownloadPreUploadReport" type="button" style="font-size:13px;padding:10px 18px">
                📥 Download Segregated Report (Excel)
              </button>
            </div>'''

new_upload_actions = '''            <!-- Complete Actions: Check Entries, Rectify Update, Insert New, Download Report -->
            <div style="display:flex;gap:10px;align-items:center;margin-top:16px;flex-wrap:wrap">
              <button class="b p" id="btnCheckEntriesModal" type="button"
                style="padding:11px 20px;font-size:14px;font-weight:800;border-radius:9px;background:linear-gradient(135deg, #0284c7, #2563eb);color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 12px rgba(37,99,235,0.25)">
                <span>🔍</span> <span>Check Entries (Inspect Differences)</span>
              </button>
              <button class="b" id="btnRectifyUpdate" type="button"
                style="padding:11px 20px;font-size:14px;font-weight:800;border-radius:9px;background:linear-gradient(135deg, #d97706, #b45309);color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 12px rgba(217,119,6,0.25)">
                <span>🔄</span> <span>Rectify Update (<span id="btnRectifyCountBadge">0</span> Records)</span>
              </button>
              <button class="b p" id="btnConfirmUpload" type="button"
                style="padding:11px 20px;font-size:14px;font-weight:800;border-radius:9px;background:linear-gradient(135deg, var(--ok), #059669);color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 12px rgba(16,185,129,0.25)">
                <span>🚀</span> <span>Upload & Insert New (<span id="btnInsertNewCountBadge">0</span>)</span>
              </button>
              <button class="b" id="btnDownloadPreUploadReport" type="button" style="font-size:13px;padding:10px 16px">
                📥 Download Validation Report (Excel)
              </button>
            </div>'''

if old_upload_actions in text:
    text = text.replace(old_upload_actions, new_upload_actions)
    print("✓ Added Check Entries and Rectify Update action buttons to subViewUpload")

with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Builder preliminary updates applied!")

