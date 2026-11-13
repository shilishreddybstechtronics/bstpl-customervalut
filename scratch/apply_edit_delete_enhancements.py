import os

file_path = 'frontend/edit-delete.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace HTML section (Bulk Operations & IMEI search card)
old_html_start = '<!-- Shifted Bulk Operations Toolbar Card -->'
old_html_end = '</section>\n    </main>'

idx1 = content.find(old_html_start)
idx2 = content.find(old_html_end, idx1)
assert idx1 != -1 and idx2 != -1, f"Could not find HTML section boundaries: {idx1}, {idx2}"

new_html_section = """<!-- Shifted Bulk Operations Toolbar Card (Redesigned Executive Styling) -->
      <div class="card" style="padding:22px 26px;margin-bottom:20px;border:1px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03)">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px">
          <div>
            <h3 style="margin:0;font-size:17.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
              <span style="font-size:22px">⚡</span> <span>Bulk Operations (Excel / Identifiers)</span>
            </h3>
            <p class="sub" style="margin:3px 0 0;font-size:13px;color:var(--muted)">Batch update metadata or delete records matching Excel files or multiple IMEI numbers.</p>
          </div>
          <div style="display:flex;gap:10px;flex-wrap:wrap">
            <button class="b" id="btnBulkEditImei" type="button" style="font-weight:700;font-size:13px;padding:9px 18px;border-radius:10px;background:linear-gradient(135deg, #0284c7, #0369a1);border-color:#0284c7;color:#fff;box-shadow:0 3px 10px rgba(2,132,199,0.25);display:inline-flex;align-items:center;gap:6px;cursor:pointer" title="Bulk update inventory records by matching IMEI from an Excel file">
              <span>✏️</span> <span>Bulk Edit (IMEI)</span>
            </button>
            <button class="b d" id="btnBulkDeleteImei" type="button" style="font-weight:700;font-size:13px;padding:9px 18px;border-radius:10px;background:rgba(239,68,68,0.08);border:1.5px solid rgba(239,68,68,0.35);color:#dc2626;display:inline-flex;align-items:center;gap:6px;cursor:pointer" title="Bulk delete inventory records by entering or pasting multiple IMEI numbers">
              <span>🗑️</span> <span>Bulk Delete (IMEI)</span>
            </button>
            <button class="b d" id="btnBulkDeleteExcel" type="button" style="font-weight:700;font-size:13px;padding:9px 18px;border-radius:10px;background:linear-gradient(135deg, #dc2626, #b91c1c);border-color:#dc2626;color:#fff;box-shadow:0 3px 10px rgba(220,38,38,0.25);display:inline-flex;align-items:center;gap:6px;cursor:pointer" title="Bulk delete inventory records by matching identifiers in an uploaded Excel file">
              <span>🗑️</span> <span>Bulk Delete (Excel)</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Single IMEI Record Editor (Redesigned Modern Card) -->
      <div class="card" style="padding:24px 26px;border:1px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:20px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;flex-wrap:wrap;gap:10px">
          <div>
            <h3 style="margin:0 0 4px 0;font-size:17.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:10px">
              <span style="font-size:22px">📱</span> <span>Edit / Delete Individual Record</span>
            </h3>
            <p class="sub" style="margin:0;font-size:13px;color:var(--muted)">Find an individual device record by its unique 15-digit IMEI to update metadata or delete.</p>
          </div>
          <span class="badge" style="background:var(--card-subtle);border:1px solid var(--line);color:var(--text);font-size:12px;font-weight:800;padding:5px 12px;border-radius:99px;display:inline-flex;align-items:center;gap:6px">
            <span>🔢</span> <span>Standard 15 Digits</span>
          </span>
        </div>

        <div style="display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap">
          <div style="flex:1;min-width:300px">
            <label for="ei" style="font-size:13px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:8px">
              <span>IMEI</span> <span style="font-size:11.5px;font-weight:600;color:var(--muted)">(15-Digit Device Identifier)</span>
            </label>
            <div style="position:relative;display:flex;align-items:center">
              <span style="position:absolute;left:14px;color:var(--primary);font-size:18px;pointer-events:none;opacity:0.9">📱</span>
              <input id="ei" placeholder="Enter 15-digit IMEI number (e.g. 861329086493088)…" maxlength="20" autocomplete="off"
                style="width:100%;height:46px;padding:0 38px 0 44px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-family:monospace;font-size:15px;font-weight:800;letter-spacing:0.8px;box-shadow:inset 0 1px 3px rgba(0,0,0,0.03);box-sizing:border-box" />
              <button class="b ghost" id="btnClearImeiInput" type="button" onclick="$('ei').value='';$('btnClearImeiInput').style.display='none';$('ei').focus()"
                style="position:absolute;right:10px;padding:4px 8px;font-size:16px;color:var(--muted);display:none;cursor:pointer" title="Clear">✕</button>
            </div>
          </div>
          <button class="b p" id="eg" type="button"
            style="height:46px;padding:0 26px;border-radius:12px;font-size:14px;font-weight:800;display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg, #2563eb, #1d4ed8);border-color:#2563eb;color:#fff;box-shadow:0 4px 14px rgba(37,99,235,0.25);cursor:pointer">
            <span>🔍</span> <span>Find Record</span>
          </button>
        </div>
        <div id="er" style="margin-top:18px"></div>
      </div>
"""

content = content[:idx1] + new_html_section + content[idx2:]
print("1. Replaced HTML Section.")

# 2. Add dlgBulkDeleteImei dialog right after </dialog> of dlgBulkDeleteExcel
target_dlg = '</dialog>\n\n  <dialog id="dlgBulkEditImei"'
if target_dlg not in content:
    target_dlg = '</dialog>\n  <dialog id="dlgBulkEditImei"'

idx_dlg = content.find(target_dlg)
assert idx_dlg != -1, "Could not find dlgBulkDeleteExcel closing dialog"

dlg_bulk_del_imei = """</dialog>

  <!-- Dedicated Bulk Delete (IMEI) Modal -->
  <dialog id="dlgBulkDeleteImei" class="modal-card" style="width:min(780px, 95vw);border-radius:18px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.45);padding:0">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--card)">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:24px">🗑️</span>
        <div>
          <h3 style="margin:0;font-size:17.5px;font-weight:800;color:var(--text)">Bulk Delete Records by IMEI</h3>
          <p class="sub" style="margin:2px 0 0;font-size:12px">Enter or paste one or more 15-digit IMEI numbers to match and delete</p>
        </div>
      </div>
      <button class="b ghost" type="button" onclick="closeModal('dlgBulkDeleteImei')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">✕</button>
    </div>

    <div style="padding:22px 26px;max-height:calc(85vh - 75px);overflow-y:auto">
      <div style="margin-bottom:16px">
        <label for="bulkDelImeiTextarea" style="font-size:13px;font-weight:800;display:block;margin-bottom:6px;color:var(--text)">
          Paste or Enter 15-Digit IMEIs (One per line or comma-separated) <span style="color:var(--danger)">*</span>
        </label>
        <textarea id="bulkDelImeiTextarea" placeholder="861329086493088&#10;865006049188783&#10;865006049188692" rows="6"
          style="width:100%;padding:12px 14px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-family:monospace;font-size:13.5px;line-height:1.5;box-sizing:border-box"></textarea>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:6px;font-size:12px;color:var(--muted)">
          <span id="bulkDelImeiCountPill" style="font-weight:700">0 IMEIs entered</span>
          <button class="b" type="button" id="btnPreviewBulkDelImeis" style="padding:4px 12px;font-size:12px;font-weight:700">🔍 Check &amp; Preview Matches</button>
        </div>
      </div>

      <div id="bulkDelImeiPreviewBox" style="display:none;margin-bottom:16px;border:1px solid var(--line);border-radius:10px;padding:14px;background:var(--card-subtle)">
        <!-- Injected preview stats and sample table -->
      </div>

      <div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;border-top:1px solid var(--line);padding-top:16px">
        <button class="b" type="button" onclick="closeModal('dlgBulkDeleteImei')">Cancel</button>
        <button class="b d" id="btnExecuteBulkDelImei" disabled style="background:#dc2626;border-color:#dc2626;color:#fff;font-weight:700;padding:8px 22px;cursor:not-allowed">
          🗑️ Move Matched to Cart
        </button>
      </div>
    </div>
  </dialog>"""

content = content[:idx_dlg] + dlg_bulk_del_imei + content[idx_dlg + len('</dialog>'):]
print("2. Injected dlgBulkDeleteImei dialog.")

# 3. Replace buildDeviceFormFields in script
idx_bdf = content.find('function buildDeviceFormFields(')
idx_bdf_end = content.find('async function openEditExpiryModal(', idx_bdf)
assert idx_bdf != -1 and idx_bdf_end != -1, f"Could not find buildDeviceFormFields boundaries"

new_bdf = """function buildDeviceFormFields(dev = {}) {
      const extra = dev.extra || {};
      const custOptions = (CU || []).map(c => `<option value="${esc(c.name)}">${esc(c.name)}</option>`).join('');

      // Dynamic extra keys
      const allExtraKeys = Array.from(new Set([...(typeof XC !== 'undefined' ? XC : []), ...Object.keys(extra)]));
      const extraFieldsHtml = allExtraKeys.map(k => `
        <div>
          <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
            ${esc(k.replace(/_/g, ' ').toUpperCase())}
          </label>
          <input data-devx="${esc(k)}" value="${esc(extra[k] != null ? extra[k] : '')}" placeholder="${esc(k)}"
            style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
        </div>
      `).join('');

      return `
        <datalist id="custNameDatalist">
          ${custOptions}
        </datalist>

        <!-- Section 1: Customer & Hardware Identity -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:16px">
          <div style="font-size:14px;font-weight:800;color:var(--text);margin-bottom:14px;display:flex;align-items:center;gap:8px">
            <span style="font-size:18px">👤</span> <span>Customer &amp; Hardware Identity</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(230px, 1fr));gap:14px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                Customer Name <span style="color:var(--danger)">*</span>
              </label>
              <input data-devf="customer_name" list="custNameDatalist" value="${esc(dev.customer_name || '')}" placeholder="Customer name" required
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;font-weight:600;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                Device SR No
              </label>
              <input data-devf="device_sr_no" value="${esc(dev.device_sr_no || '')}" placeholder="e.g. SR-89042"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                IMEI Number <span style="color:var(--danger)">*</span>
              </label>
              <input data-devf="imei" value="${esc(dev.imei || '')}" placeholder="15-digit IMEI" required
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-family:monospace;font-size:14px;font-weight:800;letter-spacing:0.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                ICCID
              </label>
              <input data-devf="iccid" value="${esc(dev.iccid || '')}" placeholder="20-digit SIM ICCID"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-family:monospace;font-size:14px;box-sizing:border-box" />
            </div>
          </div>
        </div>

        <!-- Section 2: SIM & Connectivity Details -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:16px">
          <div style="font-size:14px;font-weight:800;color:var(--text);margin-bottom:14px;display:flex;align-items:center;gap:8px">
            <span style="font-size:18px">📶</span> <span>SIM &amp; Connectivity Details</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(230px, 1fr));gap:14px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                SIM Type
              </label>
              <select data-devf="sim_type" style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;font-weight:600;box-sizing:border-box">
                <option value="">Select SIM Type</option>
                <option value="E-SIM" ${dev.sim_type === 'E-SIM' ? 'selected' : ''}>E-SIM</option>
                <option value="Plastic SIM" ${dev.sim_type === 'Plastic SIM' ? 'selected' : ''}>Plastic SIM</option>
              </select>
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                SIM Provider
              </label>
              <input data-devf="sim_provider" value="${esc(dev.sim_provider || '')}" placeholder="e.g. Airtel, Vodafone, Jio"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                MSISDN 1 (Primary Phone)
              </label>
              <input data-devf="msisdn1" value="${esc(dev.msisdn1 || '')}" placeholder="Primary SIM Phone #"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                MSISDN 2 (Secondary Phone)
              </label>
              <input data-devf="msisdn2" value="${esc(dev.msisdn2 || '')}" placeholder="Secondary SIM Phone #"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                Activation Plan
              </label>
              <input data-devf="activation_plan" value="${esc(dev.activation_plan || '')}" placeholder="e.g. 1 Year Standard"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
          </div>
        </div>

        <!-- Section 3: Timeline & Specifications -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:16px">
          <div style="font-size:14px;font-weight:800;color:var(--text);margin-bottom:14px;display:flex;align-items:center;gap:8px">
            <span style="font-size:18px">⚙️</span> <span>Timeline &amp; Specifications</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(230px, 1fr));gap:14px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                Act Date (Activation)
              </label>
              <input type="date" data-devf="act_date" value="${esc(dev.act_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                Expiry Date
              </label>
              <input type="date" data-devf="expiry_date" value="${esc(dev.expiry_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;font-weight:700;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                Dispatched Date
              </label>
              <input type="date" data-devf="dispatched_date" value="${esc(dev.dispatched_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                Model
              </label>
              <input data-devf="model" value="${esc(dev.model || '')}" placeholder="e.g. BST-01"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                Firmware
              </label>
              <input data-devf="firmware" value="${esc(dev.firmware || '')}" placeholder="e.g. v2.1.0"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block;color:var(--text)">
                Flash
              </label>
              <input data-devf="flash" value="${esc(dev.flash || '')}" placeholder="e.g. 32MB"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
          </div>
        </div>

        ${extraFieldsHtml ? `
        <!-- Section 4: Additional Dynamic Columns -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:16px">
          <div style="font-size:14px;font-weight:800;color:var(--text);margin-bottom:14px;display:flex;align-items:center;gap:8px">
            <span style="font-size:18px">🏷️</span> <span>Additional Dynamic Columns</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(230px, 1fr));gap:14px">
            ${extraFieldsHtml}
          </div>
        </div>` : ''}
      `;
    }

    """

content = content[:idx_bdf] + new_bdf + content[idx_bdf_end:]
print("3. Replaced buildDeviceFormFields.")

# 4. Replace initEditImeiContainer
idx_init = content.find('function initEditImeiContainer() {')
idx_init_end = content.find('/* =========================================================================\n         CONTAINER 8: SEPARATE EXPIRY ALERTS', idx_init)
assert idx_init != -1 and idx_init_end != -1, f"Could not find initEditImeiContainer boundaries"

new_init_js = """function initEditImeiContainer() {
        // Wire up bulk operations buttons
        if ($('btnBulkEditImei')) $('btnBulkEditImei').onclick = () => openBulkEditImeiModal();
        if ($('btnBulkDeleteImei')) $('btnBulkDeleteImei').onclick = () => openBulkDeleteImeiModal();
        if ($('btnBulkDeleteExcel')) $('btnBulkDeleteExcel').onclick = () => openBulkDeleteExcelModal();

        // Wire up IMEI input clear button
        const imeiInp = $('ei');
        const clearBtn = $('btnClearImeiInput');
        if (imeiInp && clearBtn) {
          imeiInp.oninput = () => {
            clearBtn.style.display = imeiInp.value.trim() ? 'block' : 'none';
          };
        }

        const run = async () => {
          const v = ($('ei')?.value || '').trim();
          if (!v) { toast('Please enter an IMEI to find.'); return; }
          const btnFind = $('eg');
          if (btnFind) { btnFind.disabled = true; btnFind.innerHTML = '<span>⏳</span> <span>Searching…</span>'; }

          try {
            toast('Finding record in database…');
            const d = await api('/api/devices/by-imei/' + encodeURIComponent(v));
            if (!d || !d.id) throw new Error('Device not found with IMEI ' + v);

            const staff = canDeleteValidInventory();

            // Calculate Expiry Status Pill
            let expBadgeHtml = '<span class="tag mut" style="font-size:11.5px;font-weight:700">SIM Expiry: Not Set</span>';
            if (d.expiry_date) {
              const expD = new Date(d.expiry_date);
              const now = new Date();
              now.setHours(0,0,0,0); expD.setHours(0,0,0,0);
              const daysLeft = Math.round((expD - now) / 864e5);
              if (daysLeft < 0) {
                expBadgeHtml = `<span style="font-size:11.5px;font-weight:800;color:#dc2626;background:rgba(239,68,68,0.1);padding:3px 8px;border-radius:6px;border:1px solid rgba(239,68,68,0.3)">⚠️ Expired ${Math.abs(daysLeft)} days ago</span>`;
              } else if (daysLeft === 0) {
                expBadgeHtml = `<span style="font-size:11.5px;font-weight:800;color:#d97706;background:rgba(217,119,6,0.1);padding:3px 8px;border-radius:6px;border:1px solid rgba(217,119,6,0.3)">⏳ Expires Today</span>`;
              } else {
                expBadgeHtml = `<span style="font-size:11.5px;font-weight:800;color:#d97706;background:rgba(217,119,6,0.1);padding:3px 8px;border-radius:6px;border:1px solid rgba(217,119,6,0.3)">⏳ ${daysLeft} days remaining (${esc(d.expiry_date)})</span>`;
              }
            }

            $('er').innerHTML = `
              <div style="padding:16px 20px;background:var(--card);border:1.5px solid var(--line);border-radius:14px;box-shadow:0 4px 16px rgba(0,0,0,0.03);margin:16px 0 16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
                <div style="display:flex;align-items:center;gap:12px;min-width:0">
                  <div style="width:42px;height:42px;border-radius:10px;background:rgba(37,99,235,0.08);border:1px solid rgba(37,99,235,0.25);color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">
                    📱
                  </div>
                  <div style="min-width:0">
                    <b style="font-size:16px;color:var(--text);display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                      <span>Device #${d.id}</span>
                      <span style="font-family:monospace;color:var(--primary);background:var(--card-subtle);padding:2px 8px;border-radius:6px;border:1px solid var(--line);font-size:14px">IMEI: ${esc(d.imei)}</span>
                    </b>
                    <div style="font-size:12.5px;color:var(--muted);margin-top:4px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                      <span>Customer: <b style="color:var(--text)">${esc(d.customer_name || '—')}</b></span>
                      <span>·</span>
                      ${expBadgeHtml}
                    </div>
                  </div>
                </div>
                <button type="button" class="b" id="btnQuickEditExp" style="font-weight:700;font-size:12.5px;padding:8px 16px;border-radius:9px;background:var(--card);border:1.5px solid var(--primary);color:var(--primary);display:inline-flex;align-items:center;gap:6px;cursor:pointer">
                  <span>📅</span> <span>Edit Expiry Date</span>
                </button>
              </div>

              <div style="margin:16px 0">${buildDeviceFormFields(d)}</div>

              <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-top:20px;border-top:1px solid var(--line);padding-top:16px">
                <button class="b p" id="sv" style="background:linear-gradient(135deg, #2563eb, #1d4ed8);border-color:#2563eb;color:#fff;font-weight:700;padding:10px 26px;border-radius:10px;box-shadow:0 4px 14px rgba(37,99,235,0.25);cursor:pointer;display:inline-flex;align-items:center;gap:8px">
                  <span>💾</span> <span>Save Changes</span>
                </button>
                ${staff ? '<button class="b d" id="dl" style="font-weight:700;padding:10px 20px;border-radius:10px;background:rgba(239,68,68,0.08);border:1.5px solid rgba(239,68,68,0.35);color:#dc2626;cursor:pointer;display:inline-flex;align-items:center;gap:6px"><span>🗑️</span> <span>Move to Cart (Delete)</span></button>' : ''}
              </div>`;

            if ($('btnQuickEditExp')) {
              $('btnQuickEditExp').onclick = () => openEditExpiryModal(d.id);
            }

            $('sv').onclick = async () => {
              const body = {};
              document.querySelectorAll('#er [data-devf]').forEach(i => {
                const k = i.dataset.devf, val = i.value.trim();
                body[k] = val || null;
              });
              const extra = {};
              document.querySelectorAll('#er [data-devx]').forEach(i => {
                const k = i.dataset.devx, val = i.value.trim();
                extra[k] = val || null;
              });
              if (Object.keys(extra).length) body.extra = extra;

              const btnSave = $('sv');
              if (btnSave) { btnSave.disabled = true; btnSave.innerHTML = '<span>⏳</span> <span>Saving…</span>'; }

              try {
                toast('Saving record permanently to database…');
                await api('/api/devices/by-imei/' + encodeURIComponent(d.imei), { method: 'PUT', body: JSON.stringify(body) });
                toast('✓ Changes saved permanently to database');
                if (typeof showEventPopup === 'function') {
                  showEventPopup({
                    type: 'inserting',
                    title: 'Device Record Updated',
                    message: `Device record ${body.imei || d.imei} was successfully saved and updated.`,
                    meta: { 'IMEI': body.imei || d.imei, 'Status': 'Updated in Database' },
                    progress: '100% Complete'
                  });
                }
                await updateChrome();
                if (body.imei && body.imei !== d.imei) $('ei').value = body.imei;
                await run();
              } catch (e) {
                fail(e);
              } finally {
                if (btnSave) { btnSave.disabled = false; btnSave.innerHTML = '<span>💾</span> <span>Save Changes</span>'; }
              }
            };

            if (staff && $('dl')) {
              $('dl').onclick = async () => {
                const ok = await cv.confirm(`Move device record with IMEI ${d.imei} to the Cart (Recycle Bin)?`, {
                  title: 'Move Record to Cart',
                  danger: true
                });
                if (!ok) return;

                try {
                  toast('Moving record to Cart…');
                  await api('/api/devices/by-imei/' + encodeURIComponent(d.imei), { method: 'DELETE' });
                  toast(`✓ Device ${d.imei} moved to Cart.`);
                  $('er').innerHTML = `
                    <div style="padding:32px 24px;border:1.5px dashed var(--line);border-radius:14px;background:var(--card-subtle);text-align:center;color:var(--muted);margin-top:16px">
                      <div style="font-size:36px;margin-bottom:8px">🗑️</div>
                      <b style="font-size:16px;color:var(--text);display:block;margin-bottom:4px">Device Record Moved to Cart</b>
                      <span style="font-size:13px;display:block;margin-bottom:14px">Record with IMEI <code>${esc(d.imei)}</code> has been safely moved to the Cart recycle bin.</span>
                      <a class="b p" href="cart.html" style="text-decoration:none;font-size:12.5px;font-weight:700">View in Cart</a>
                    </div>
                  `;
                  await updateChrome();
                } catch (e) { fail(e); }
              };
            }
          } catch (e) {
            $('er').innerHTML = `
              <div class="empty err" style="padding:22px;border:1.5px solid #ef4444;background:rgba(239,68,68,0.06);border-radius:12px;color:#dc2626;font-size:13.5px;font-weight:700">
                ⚠️ ${esc(e.message)}
              </div>
            `;
          } finally {
            if (btnFind) { btnFind.disabled = false; btnFind.innerHTML = '<span>🔍</span> <span>Find Record</span>'; }
          }
        };

        if ($('eg')) $('eg').onclick = run;
        if ($('ei')) $('ei').onkeydown = e => { if (e.key === 'Enter') run(); };
      }

      // --- Dedicated Bulk Delete (IMEI) Modal Handler ---
      window.openBulkDeleteImeiModal = function() {
        const dlg = $('dlgBulkDeleteImei');
        if (!dlg) return;

        const ta = $('bulkDelImeiTextarea');
        const pill = $('bulkDelImeiCountPill');
        const previewBox = $('bulkDelImeiPreviewBox');
        const btnExec = $('btnExecuteBulkDelImei');
        const btnPrev = $('btnPreviewBulkDelImeis');

        if (ta) ta.value = '';
        if (pill) pill.textContent = '0 IMEIs entered';
        if (previewBox) { previewBox.style.display = 'none'; previewBox.innerHTML = ''; }
        if (btnExec) { btnExec.disabled = true; btnExec.style.cursor = 'not-allowed'; }

        let currentImeis = [];

        if (ta && pill) {
          ta.oninput = () => {
            const raw = ta.value.split(/[\\r\\n,]+/).map(s => s.trim()).filter(Boolean);
            currentImeis = Array.from(new Set(raw));
            pill.textContent = `${currentImeis.length} unique IMEI(s) entered`;
          };
        }

        if (btnPrev) {
          btnPrev.onclick = async () => {
            const raw = (ta?.value || '').split(/[\\r\\n,]+/).map(s => s.trim()).filter(Boolean);
            currentImeis = Array.from(new Set(raw));
            if (!currentImeis.length) { toast('Please enter at least one IMEI number.'); return; }

            btnPrev.disabled = true; btnPrev.textContent = 'Checking…';
            try {
              const res = await api('/api/devices/bulk-delete/preview', {
                method: 'POST',
                body: JSON.stringify({ column: 'imei', values: currentImeis })
              });

              if (previewBox) {
                previewBox.style.display = 'block';
                previewBox.innerHTML = `
                  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px">
                    <b style="font-size:13.5px;color:var(--text)">Matched: <span style="color:var(--ok)">${res.matching_records || 0}</span> of ${res.total_values || currentImeis.length} IMEIs</b>
                    <span style="font-size:12px;color:var(--muted)">Unmatched: ${res.unmatched_values || 0}</span>
                  </div>
                  ${res.sample_matches && res.sample_matches.length ? `
                    <div style="max-height:160px;overflow-y:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)">
                      <table style="width:100%;font-size:12px;border-collapse:collapse">
                        <thead>
                          <tr style="background:var(--card-subtle);text-align:left">
                            <th style="padding:6px 10px">ID</th>
                            <th style="padding:6px 10px">Customer</th>
                            <th style="padding:6px 10px">IMEI</th>
                          </tr>
                        </thead>
                        <tbody>
                          ${res.sample_matches.slice(0, 10).map(m => `
                            <tr style="border-top:1px solid var(--line)">
                              <td style="padding:6px 10px">#${m.id}</td>
                              <td style="padding:6px 10px">${esc(m.customer_name || '—')}</td>
                              <td style="padding:6px 10px;font-family:monospace"><b>${esc(m.imei || '—')}</b></td>
                            </tr>
                          `).join('')}
                        </tbody>
                      </table>
                    </div>
                  ` : '<div style="font-size:12px;color:var(--muted)">No active inventory records matched these IMEIs.</div>'}
                `;
              }

              if (btnExec) {
                const canExec = (res.matching_records > 0);
                btnExec.disabled = !canExec;
                btnExec.style.cursor = canExec ? 'pointer' : 'not-allowed';
                btnExec.textContent = `🗑️ Move ${res.matching_records || 0} Matched to Cart`;
              }
            } catch(err) {
              fail(err);
            } finally {
              btnPrev.disabled = false; btnPrev.textContent = '🔍 Check & Preview Matches';
            }
          };
        }

        if (btnExec) {
          btnExec.onclick = async () => {
            if (!currentImeis.length) return;
            const ok = await cv.confirm(`Move all matched IMEI records to the Cart (Recycle Bin)?`, {
              title: 'Bulk Delete to Cart',
              danger: true
            });
            if (!ok) return;

            dlg.close();
            if (typeof showBstplLoader === 'function') showBstplLoader(`Moving records to Cart…`);

            try {
              const res = await api('/api/devices/bulk-delete/execute', {
                method: 'POST',
                body: JSON.stringify({ column: 'imei', values: currentImeis, permanent: false })
              });
              toast(`✓ Successfully moved ${res.deleted_count || currentImeis.length} records to Cart.`);
              await updateChrome();
            } catch(err) {
              fail(err);
            } finally {
              if (typeof hideBstplLoader === 'function') hideBstplLoader();
            }
          };
        }

        dlg.showModal();
      };

      """

content = content[:idx_init] + new_init_js + content[idx_init_end:]
print("4. Replaced initEditImeiContainer and bulk operations.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated frontend/edit-delete.html!")

