import os

html_path = r'c:\Users\soumy\OneDrive\Documents\bstpl-view\frontend\alerts.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add modal-card styles before </style>
css_to_add = """
    /* Modal Cards Enhancement */
    dialog.modal-card {
      border: 1px solid var(--line);
      box-shadow: 0 30px 80px rgba(0,0,0,.45);
      border-radius: 18px;
      animation: modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes modalPop {
      from { opacity: 0; transform: scale(0.96) translateY(8px); }
      to { opacity: 1; transform: scale(1) translateY(0); }
    }
"""

if 'animation: modalPop' not in content:
    content = content.replace('</style>', css_to_add + '\n  </style>', 1)
    print("1. Injected modal-card CSS.")

# 2. Add <dialog id="devdlg"> right after </dialog> for dlgActionProgress
target_dlg = '</dialog>\n\n  <div id="toast"'
if target_dlg not in content:
    target_dlg = '</dialog>\n  <div id="toast"'

devdlg_html = """<!-- Add / Edit Device Record Modal -->
  <dialog id="devdlg" class="modal-card" style="width:min(820px, 95vw);border-radius:18px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.45);padding:0">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--card)">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:24px" id="devIcon">📱</span>
        <div>
          <h3 id="devTitle" style="margin:0;font-size:18px;font-weight:800;color:var(--text)">Edit Device Record &amp; Expiry</h3>
          <p class="sub" id="devSubTitle" style="margin:2px 0 0;font-size:12px">Update SIM expiry date or device specifications</p>
        </div>
      </div>
      <button class="b ghost" id="devCloseBtn" type="button" onclick="closeModal('devdlg')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">✕</button>
    </div>

    <form id="devform" style="padding:22px 24px;max-height:calc(85vh - 75px);overflow-y:auto">
      <div class="dlg-body" id="devFields"></div>
      <p class="err" id="devErr" role="alert" style="display:none;color:var(--danger);font-size:13px;font-weight:700;margin:12px 0;padding:10px 14px;border-radius:8px;background:rgba(239,68,68,0.08);border:1px solid #ef4444"></p>
      <div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;margin-top:20px;border-top:1px solid var(--line);padding-top:16px">
        <button class="b" type="button" id="devCancel" onclick="closeModal('devdlg')">Cancel</button>
        <button class="b p" type="submit" id="devSave" style="background:linear-gradient(135deg, #2563eb, #1d4ed8);border-color:#2563eb;color:#fff;font-weight:700;padding:8px 24px;box-shadow:0 4px 12px rgba(37,99,235,0.25)">Save Changes</button>
      </div>
    </form>
  </dialog>

  """

if '<dialog id="devdlg"' not in content:
    # insert before <div id="toast"
    toast_idx = content.find('<div id="toast"')
    assert toast_idx != -1, "Could not find <div id=\"toast\""
    content = content[:toast_idx] + devdlg_html + content[toast_idx:]
    print("2. Injected devdlg modal HTML.")

# 3. Add closeModal and extendAlertExpiry helpers
helpers_js = """
    function closeModal(id) {
      const d = typeof id === 'string' ? document.getElementById(id) : id;
      if (d && typeof d.close === 'function') d.close();
    }

    function extendAlertExpiry(days) {
      const inp = document.getElementById('devFieldExpiryDate');
      if (!inp) return;
      const base = inp.value ? new Date(inp.value) : new Date();
      const startDate = (isNaN(base.getTime()) || base < new Date()) ? new Date() : base;
      startDate.setDate(startDate.getDate() + days);
      const yyyy = startDate.getFullYear();
      const mm = String(startDate.getMonth() + 1).padStart(2, '0');
      const dd = String(startDate.getDate()).padStart(2, '0');
      inp.value = `${yyyy}-${mm}-${dd}`;
      toast(`Set expiry date to ${inp.value}`);
    }
"""

if 'function extendAlertExpiry' not in content:
    script_idx = content.find('<script>')
    assert script_idx != -1, "Could not find <script>"
    content = content[:script_idx + len('<script>')] + helpers_js + content[script_idx + len('<script>'):]
    print("3. Injected closeModal and extendAlertExpiry helpers.")

# 4. Replace buildDeviceFormFields and openEditDeviceModal
old_bdf_start = 'function buildDeviceFormFields(dev = {}) {'
old_bdf_end = 'function openExportColumnsModal() {'

start_idx = content.find(old_bdf_start)
end_idx = content.find(old_bdf_end)
assert start_idx != -1 and end_idx != -1, f"Could not find buildDeviceFormFields boundaries: {start_idx}, {end_idx}"

new_bdf_and_edit = """function buildDeviceFormFields(dev = {}) {
      const custOptions = (CU || []).map(c => `<option value="${esc(c.name)}">${esc(c.name)}</option>`).join('');
      const currExp = dev.expiry_date || '';
      const daysLeft = dev.days_left != null ? dev.days_left : null;
      let expBadgeHtml = '';
      if (daysLeft != null) {
        if (daysLeft < 0) {
          expBadgeHtml = `<span style="font-size:11.5px;font-weight:800;color:#dc2626;background:rgba(239,68,68,0.1);padding:2px 8px;border-radius:6px;border:1px solid rgba(239,68,68,0.3)">⚠️ Expired ${Math.abs(daysLeft)} days ago</span>`;
        } else if (daysLeft === 0) {
          expBadgeHtml = `<span style="font-size:11.5px;font-weight:800;color:#d97706;background:rgba(217,119,6,0.1);padding:2px 8px;border-radius:6px;border:1px solid rgba(217,119,6,0.3)">⏳ Expires Today</span>`;
        } else {
          expBadgeHtml = `<span style="font-size:11.5px;font-weight:800;color:#d97706;background:rgba(217,119,6,0.1);padding:2px 8px;border-radius:6px;border:1px solid rgba(217,119,6,0.3)">⏳ ${daysLeft} days remaining</span>`;
        }
      }

      return `
        <datalist id="custNameDatalist">
          ${custOptions}
        </datalist>

        <!-- Highlighted Expiry Section in Alerts -->
        <div style="background:rgba(37,99,235,0.04);border:1.5px solid var(--primary);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px">
            <div style="font-size:13.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:8px">
              <span style="font-size:18px">📅</span> <span>SIM Expiry Date Management</span>
            </div>
            ${expBadgeHtml}
          </div>
          <div style="display:grid;grid-template-columns:1fr;gap:10px">
            <div>
              <label style="font-size:12.5px;font-weight:800;margin-bottom:6px;display:block;color:var(--text)">
                Expiry Date * (YYYY-MM-DD)
              </label>
              <input type="date" id="devFieldExpiryDate" data-devf="expiry_date" value="${esc(currExp)}" required
                style="width:100%;height:44px;padding:0 14px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:14.5px;font-weight:700;box-sizing:border-box" />
            </div>
            <!-- Quick Extend Preset Buttons -->
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:2px">
              <span style="font-size:12px;font-weight:700;color:var(--muted)">Quick Extend:</span>
              <button type="button" class="b" onclick="extendAlertExpiry(180)" style="font-size:11.5px;padding:3px 10px;height:28px;border-radius:6px">+6 Months</button>
              <button type="button" class="b" onclick="extendAlertExpiry(365)" style="font-size:11.5px;padding:3px 10px;height:28px;border-radius:6px;font-weight:700;background:var(--card-subtle);border-color:var(--primary);color:var(--primary)">+1 Year</button>
              <button type="button" class="b" onclick="extendAlertExpiry(730)" style="font-size:11.5px;padding:3px 10px;height:28px;border-radius:6px">+2 Years</button>
            </div>
            <span style="font-size:12px;color:var(--muted);margin-top:2px;display:block">
              ℹ️ Extending the expiry date will update the record in the database. Because the new date is beyond the alert threshold, this SIM will immediately vanish from Expiry Alerts and only reappear when it is near expiry again.
            </span>
          </div>
        </div>

        <!-- Section 1: Customer & Hardware Identity -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-size:13.5px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">👤</span> <span>Customer & Device Identification</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Customer Name <span style="color:var(--danger)">*</span></label>
              <input data-devf="customer_name" list="custNameDatalist" value="${esc(dev.customer_name || '')}" placeholder="Type or select customer" required
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Device SR No</label>
              <input data-devf="device_sr_no" value="${esc(dev.device_sr_no || '')}" placeholder="e.g. SR-89042"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">IMEI Number <span style="color:var(--danger)">*</span></label>
              <input data-devf="imei" value="${esc(dev.imei || '')}" placeholder="15-digit IMEI" required
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box;font-family:monospace" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">ICCID</label>
              <input data-devf="iccid" value="${esc(dev.iccid || '')}" placeholder="20-digit SIM ICCID"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box;font-family:monospace" />
            </div>
          </div>
        </div>

        <!-- Section 2: SIM & Connectivity Details -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-size:13.5px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">📶</span> <span>SIM & Connectivity Details</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">SIM Type</label>
              <select data-devf="sim_type" style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box">
                <option value="">Select SIM Type</option>
                <option value="E-SIM" ${dev.sim_type === 'E-SIM' ? 'selected' : ''}>E-SIM</option>
                <option value="Plastic SIM" ${dev.sim_type === 'Plastic SIM' ? 'selected' : ''}>Plastic SIM</option>
              </select>
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">SIM Provider</label>
              <input data-devf="sim_provider" value="${esc(dev.sim_provider || '')}" placeholder="e.g. Airtel, Vodafone, Jio"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">MSISDN 1 (Primary Phone)</label>
              <input data-devf="msisdn1" value="${esc(dev.msisdn1 || '')}" placeholder="Primary SIM Phone #"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">MSISDN 2 (Secondary Phone)</label>
              <input data-devf="msisdn2" value="${esc(dev.msisdn2 || '')}" placeholder="Secondary SIM Phone #"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Activation Plan</label>
              <input data-devf="activation_plan" value="${esc(dev.activation_plan || '')}" placeholder="e.g. 1 Year Standard"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
          </div>
        </div>

        <!-- Section 3: Other Dates & Specs -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-size:13.5px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">⚙️</span> <span>Timeline & Specifications</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Activation Date</label>
              <input type="date" data-devf="act_date" value="${esc(dev.act_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Dispatched Date</label>
              <input type="date" data-devf="dispatched_date" value="${esc(dev.dispatched_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Model</label>
              <input data-devf="model" value="${esc(dev.model || '')}" placeholder="e.g. BST-01"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Firmware</label>
              <input data-devf="firmware" value="${esc(dev.firmware || '')}" placeholder="e.g. v2.1.0"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
          </div>
        </div>
      `;
    }

    async function openEditDeviceModal(id) {
      try {
        toast('Loading record details…');
        const dev = await api('/api/devices/' + id);
        const dlg = $('devdlg');
        if (!dlg) return;

        if ($('devIcon')) $('devIcon').textContent = '✏️';
        if ($('devTitle')) $('devTitle').textContent = `Edit SIM Expiry & Device #${dev.id}`;
        if ($('devSubTitle')) $('devSubTitle').textContent = `Customer: ${dev.customer_name || '—'} · IMEI: ${dev.imei || '—'}`;
        $('devFields').innerHTML = buildDeviceFormFields(dev);
        if ($('devErr')) { $('devErr').textContent = ''; $('devErr').style.display = 'none'; }
        if ($('devSave')) $('devSave').textContent = '💾 Save Changes';

        if ($('devCloseBtn')) $('devCloseBtn').onclick = () => dlg.close();
        if ($('devCancel')) $('devCancel').onclick = () => dlg.close();

        $('devform').onsubmit = async e => {
          e.preventDefault();
          const errEl = $('devErr');
          if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }

          const body = {};
          document.querySelectorAll('#devdlg [data-devf]').forEach(i => {
            const k = i.dataset.devf, v = i.value.trim();
            body[k] = v || null;
          });

          if (!body.customer_name) {
            if (errEl) { errEl.textContent = 'Customer Name is required.'; errEl.style.display = 'block'; }
            return;
          }
          if (!body.imei) {
            if (errEl) { errEl.textContent = 'IMEI is required.'; errEl.style.display = 'block'; }
            return;
          }

          const btnSave = $('devSave');
          if (btnSave) { btnSave.disabled = true; btnSave.textContent = 'Saving…'; }

          try {
            await api('/api/devices/' + dev.id, { method: 'PUT', body: JSON.stringify(body) });
            dlg.close();
            toast(`✓ SIM expiry date and device record updated successfully`);
            await loadExpiryContainer();
            if (typeof updateChrome === 'function') await updateChrome();
          } catch(err) {
            if (errEl) { errEl.textContent = err.message || 'Failed to update record'; errEl.style.display = 'block'; }
          } finally {
            if (btnSave) { btnSave.disabled = false; btnSave.textContent = '💾 Save Changes'; }
          }
        };

        dlg.showModal();
      } catch(err) { fail(err); }
    }

    """

content = content[:start_idx] + new_bdf_and_edit + content[end_idx:]
print("4. Replaced buildDeviceFormFields and openEditDeviceModal.")

# 5. Update delete action handler in loadExpiryContainer
old_del_block = """            const delBtn = e.target.closest('[data-del]');
            if (delBtn) {
              if (!canDeleteValidInventory()) {
                toast('Access Denied: Master Admins do not have permission to delete inventory records.');
                return;
              }
              if (!await cv.confirm('Move this device record to Cart?')) return;
              try {
                await api('/api/devices/' + delBtn.dataset.del, { method: 'DELETE' });
                toast('Device moved to Cart');
                loadExpiryContainer();
                updateChrome();
              } catch (err) { fail(err); }
            }"""

new_del_block = """            const delBtn = e.target.closest('[data-del]');
            if (delBtn) {
              if (!canDeleteValidInventory()) {
                toast('Access Denied: Master Admins do not have permission to delete inventory records.');
                return;
              }
              const devId = delBtn.dataset.del;
              const ok = await cv.confirm('Delete this device record and move it to the Cart (Recycle Bin)?', {
                title: 'Move Record to Cart',
                confirmText: 'Move to Cart',
                danger: true
              });
              if (!ok) return;

              try {
                toast('Moving record to Cart…');
                await api('/api/devices/' + devId, { method: 'DELETE' });
                toast('✓ Device record moved to Cart successfully');
                await loadExpiryContainer();
                if (typeof updateChrome === 'function') await updateChrome();
              } catch (err) { fail(err); }
              return;
            }"""

assert old_del_block in content, "Could not find exact old_del_block in loadExpiryContainer"
content = content.replace(old_del_block, new_del_block, 1)
print("5. Updated Delete handler in loadExpiryContainer.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("alerts.html successfully updated!")

