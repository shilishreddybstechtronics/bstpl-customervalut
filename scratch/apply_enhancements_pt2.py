import os

html_path = r'c:\Users\soumy\OneDrive\Documents\bstpl-view\frontend\inventory.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace buildDeviceFormFields and openEditDeviceModal
old_bdf_start = 'function buildDeviceFormFields(dev = {}) {'
old_bdf_end = 'function openExportColumnsModal() {'

start_idx = content.find(old_bdf_start)
end_idx = content.find(old_bdf_end)
assert start_idx != -1 and end_idx != -1, f"Could not find buildDeviceFormFields boundaries: {start_idx}, {end_idx}"

# Let's see what is inside old block:
# It contains buildDeviceFormFields, openEditExpiryModal, openEditDeviceModal, and devCancelBtn
# We want to replace buildDeviceFormFields and openEditDeviceModal, keeping openEditExpiryModal intact!

# Let's do targeted replacement for buildDeviceFormFields
old_bdf = """    function buildDeviceFormFields(dev = {}) {
      const extra = dev.extra || {};
      return `
        <div class="form-grid">
          <div><label>Customer Name *</label><input data-devf="customer_name" value="${esc(dev.customer_name || '')}" placeholder="Customer name" required /></div>
          <div><label>Device SR No</label><input data-devf="device_sr_no" value="${esc(dev.device_sr_no || '')}" /></div>
          <div><label>IMEI *</label><input data-devf="imei" value="${esc(dev.imei || '')}" required /></div>
          <div><label>ICCID</label><input data-devf="iccid" value="${esc(dev.iccid || '')}" /></div>
          <div><label>MSISDN 1</label><input data-devf="msisdn1" value="${esc(dev.msisdn1 || '')}" /></div>
          <div><label>MSISDN 2</label><input data-devf="msisdn2" value="${esc(dev.msisdn2 || '')}" /></div>
          <div><label>Act Date</label><input type="date" data-devf="act_date" value="${esc(dev.act_date || '')}" /></div>
          <div><label>Expiry Date</label><input type="date" data-devf="expiry_date" value="${esc(dev.expiry_date || '')}" /></div>
          <div><label>Dispatched Date</label><input type="date" data-devf="dispatched_date" value="${esc(dev.dispatched_date || '')}" /></div>
          <div><label>Model</label><input data-devf="model" value="${esc(dev.model || '')}" /></div>
          <div><label>SIM Provider</label><input data-devf="sim_provider" value="${esc(dev.sim_provider || '')}" /></div>
          <div><label>Activation Plan</label><input data-devf="activation_plan" value="${esc(dev.activation_plan || '')}" /></div>
          <div><label>Firmware</label><input data-devf="firmware" value="${esc(dev.firmware || '')}" /></div>
          <div><label>Flash</label><input data-devf="flash" value="${esc(dev.flash || '')}" /></div>
          <div><label>SIM Type</label><select data-devf="sim_type"><option value="">Select type</option><option value="E-SIM" ${dev.sim_type==='E-SIM'?'selected':''}>E-SIM</option><option value="Plastic SIM" ${dev.sim_type==='Plastic SIM'?'selected':''}>Plastic SIM</option></select></div>
        </div>
      `;
    }"""

new_bdf = """    function buildDeviceFormFields(dev = {}) {
      const custOptions = (CU || []).map(c => `<option value="${esc(c.name)}">${esc(c.name)}</option>`).join('');
      return `
        <datalist id="custNameDatalist">
          ${custOptions}
        </datalist>

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

        <!-- Section 3: Dates & Timeline -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-size:13.5px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">📅</span> <span>Lifecycle Dates & Timeline</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Activation Date</label>
              <input type="date" data-devf="act_date" value="${esc(dev.act_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Expiry Date</label>
              <input type="date" data-devf="expiry_date" value="${esc(dev.expiry_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Dispatched Date</label>
              <input type="date" data-devf="dispatched_date" value="${esc(dev.dispatched_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
          </div>
        </div>

        <!-- Section 4: Specifications -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-size:13.5px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">⚙️</span> <span>Hardware & Software Specs</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Model</label>
              <input data-devf="model" value="${esc(dev.model || '')}" placeholder="e.g. BST-01"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Firmware Version</label>
              <input data-devf="firmware" value="${esc(dev.firmware || '')}" placeholder="e.g. v2.1.0"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Flash Memory</label>
              <input data-devf="flash" value="${esc(dev.flash || '')}" placeholder="e.g. 16MB SPI"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
          </div>
        </div>
      `;
    }"""

assert old_bdf in content, "Could not find exact old_bdf"
content = content.replace(old_bdf, new_bdf, 1)
print("1. Replaced buildDeviceFormFields.")

# 2. Replace openEditDeviceModal
old_edm = """    async function openEditDeviceModal(id) {
      try {
        toast('Loading record…');
        const dev = await api('/api/devices/' + id);
        $('devTitle').textContent = `Edit Device #${dev.id} (IMEI ${dev.imei})`;
        $('devFields').innerHTML = buildDeviceFormFields(dev);
        $('devErr').textContent = '';
        $('devSave').textContent = 'Save Changes';
        $('devform').onsubmit = async e => {
          e.preventDefault();
          $('devErr').textContent = '';
          const body = {};
          document.querySelectorAll('#devdlg [data-devf]').forEach(i => {
            const k = i.dataset.devf, v = i.value.trim();
            body[k] = v || null;
          });
          try {
            await api('/api/devices/' + dev.id, { method: 'PUT', body: JSON.stringify(body) });
            $('devdlg').close();
            toast('Device record updated');
            if (typeof refreshActiveContainer === 'function') refreshActiveContainer();
            else if (typeof loadInventoryContainer === 'function') loadInventoryContainer();
          } catch(err) { $('devErr').textContent = err.message; }
        };
        $('devdlg').showModal();
      } catch(err) { fail(err); }
    }"""

new_edm = """    async function openEditDeviceModal(id) {
      try {
        toast('Loading record…');
        const dev = await api('/api/devices/' + id);
        if ($('devIcon')) $('devIcon').textContent = '✏️';
        if ($('devTitle')) $('devTitle').textContent = `Edit Device #${dev.id} (IMEI ${dev.imei || '—'})`;
        if ($('devSubTitle')) $('devSubTitle').textContent = `Customer: ${dev.customer_name || '—'} · SIM: ${dev.sim_type || 'SIM'}`;
        $('devFields').innerHTML = buildDeviceFormFields(dev);
        if ($('devErr')) { $('devErr').textContent = ''; $('devErr').style.display = 'none'; }
        if ($('devSave')) $('devSave').textContent = '💾 Save Changes';

        if ($('devCloseBtn')) $('devCloseBtn').onclick = () => $('devdlg').close();
        if ($('devCancel')) $('devCancel').onclick = () => $('devdlg').close();

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
            $('devdlg').close();
            toast(`✓ Device record #${dev.id} updated successfully`);
            if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
            if (typeof drawCustCards === 'function') drawCustCards();
            if (typeof refreshActiveContainer === 'function') refreshActiveContainer();
            else if (typeof loadInventoryContainer === 'function') loadInventoryContainer();
          } catch(err) {
            if (errEl) { errEl.textContent = err.message || 'Failed to update record'; errEl.style.display = 'block'; }
          } finally {
            if (btnSave) { btnSave.disabled = false; btnSave.textContent = '💾 Save Changes'; }
          }
        };
        $('devdlg').showModal();
      } catch(err) { fail(err); }
    }"""

assert old_edm in content, "Could not find exact old_edm"
content = content.replace(old_edm, new_edm, 1)
print("2. Replaced openEditDeviceModal.")

# 3. Replace openAddDeviceModal
old_adm = """    function openAddDeviceModal() {
      const dlg = $('devdlg');
      if (!dlg) return;
      $('devTitle').textContent = 'Add Device Record';
      $('devFields').innerHTML = buildDeviceFormFields();
      $('devErr').textContent = '';
      $('devSave').textContent = 'Create Record';
      $('devform').onsubmit = async e => {
        e.preventDefault();
        $('devErr').textContent = '';
        const body = {};
        document.querySelectorAll('#devdlg [data-devf]').forEach(i => {
          const k = i.dataset.devf, v = i.value.trim();
          if (v) body[k] = v;
        });
        const extra = {};
        document.querySelectorAll('#devdlg [data-devx]').forEach(i => {
          const k = i.dataset.devx, v = i.value.trim();
          if (v) extra[k] = v;
        });
        if (Object.keys(extra).length) body.extra = extra;

        try {
          await api('/api/devices', { method: 'POST', body: JSON.stringify(body) });
          dlg.close();
          toast('Device record created successfully');
          if (typeof loadInventoryContainer === 'function') loadInventoryContainer();
          else if (typeof refreshActiveContainer === 'function') refreshActiveContainer();
        } catch (err) { $('devErr').textContent = err.message; }
      };
      if (typeof dlg.showModal === 'function') dlg.showModal();
    }"""

new_adm = """    function openAddDeviceModal() {
      const dlg = $('devdlg');
      if (!dlg) return;
      if ($('devIcon')) $('devIcon').textContent = '📱';
      if ($('devTitle')) $('devTitle').textContent = 'Add Device Record';
      if ($('devSubTitle')) $('devSubTitle').textContent = 'Register a new SIM / hardware record into customer inventory';
      $('devFields').innerHTML = buildDeviceFormFields();
      if ($('devErr')) { $('devErr').textContent = ''; $('devErr').style.display = 'none'; }
      if ($('devSave')) $('devSave').textContent = '➕ Create Record';

      if ($('devCloseBtn')) $('devCloseBtn').onclick = () => dlg.close();
      if ($('devCancel')) $('devCancel').onclick = () => dlg.close();

      $('devform').onsubmit = async e => {
        e.preventDefault();
        const errEl = $('devErr');
        if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }
        const body = {};
        document.querySelectorAll('#devdlg [data-devf]').forEach(i => {
          const k = i.dataset.devf, v = i.value.trim();
          if (v) body[k] = v;
        });
        const extra = {};
        document.querySelectorAll('#devdlg [data-devx]').forEach(i => {
          const k = i.dataset.devx, v = i.value.trim();
          if (v) extra[k] = v;
        });
        if (Object.keys(extra).length) body.extra = extra;

        if (!body.customer_name) {
          if (errEl) { errEl.textContent = 'Customer Name is required.'; errEl.style.display = 'block'; }
          return;
        }
        if (!body.imei) {
          if (errEl) { errEl.textContent = 'IMEI is required.'; errEl.style.display = 'block'; }
          return;
        }

        const btnSave = $('devSave');
        if (btnSave) { btnSave.disabled = true; btnSave.textContent = 'Creating Record…'; }

        try {
          await api('/api/devices', { method: 'POST', body: JSON.stringify(body) });
          dlg.close();
          toast(`✓ Device record (IMEI ${body.imei}) created successfully`);
          await loadCU();
          await updateChrome();
          if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
          if (typeof drawCustCards === 'function') drawCustCards();
          if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
        } catch (err) {
          if (errEl) { errEl.textContent = err.message || 'Failed to create record'; errEl.style.display = 'block'; }
        } finally {
          if (btnSave) { btnSave.disabled = false; btnSave.textContent = '➕ Create Record'; }
        }
      };
      if (typeof dlg.showModal === 'function') dlg.showModal();
    }"""

assert old_adm in content, "Could not find exact old_adm"
content = content.replace(old_adm, new_adm, 1)
print("3. Replaced openAddDeviceModal.")

# 4. Replace openSingleCustomerRename and openDeleteCustomerEntriesModal
old_ren = """      function openSingleCustomerRename(cid) {
        const cust = CU.find(c => c.id === cid);
        if (!cust) return;
        openDlg(`Rename Customer: ${cust.name}`, `
          <div class="note" style="margin-bottom:12px">
            <b>ℹ️ Website & Database Synchronization:</b> Renaming will update the customer name across the website, database records, and its dedicated table in TiDB Cloud. All SIM records remain intact.
          </div>
          <label for="singleRenName">New Customer Name</label>
          <input id="singleRenName" value="${esc(cust.name)}" required />
          <span class="sub" id="singleRenHint" style="font-size:12px;color:var(--ok);margin-top:4px;display:block"></span>
        `, 'Save & Update Everywhere', async () => {
          const name = $('singleRenName').value.trim();
          if (!name) throw new Error('Please enter a new name');
          showBstplLoader(`Renaming customer "${cust.name}" to "${name}"…`);
          try {
            const r = await api('/api/customers/' + cid, { method: 'PATCH', body: JSON.stringify({ name }) });
            toast(`✓ Customer renamed to "${r.name}" in database, cloud table, and website!`);
            await loadCU(); await updateChrome(); loadCustomerFilesContainer();
          } finally {
            hideBstplLoader();
          }
        });
      }"""

new_ren = """      function openSingleCustomerRename(cid) {
        const cust = (CU || []).find(c => String(c.id) === String(cid));
        if (!cust) {
          toast('Customer portfolio not found');
          return;
        }

        const dlg = $('dlgSingleCustomerRename');
        if (!dlg) return;

        if ($('renCustCurrentName')) $('renCustCurrentName').textContent = cust.name;
        if ($('renCustCurrentId')) $('renCustCurrentId').textContent = '#' + cust.id;
        if ($('renCustAvatar')) $('renCustAvatar').textContent = (cust.name || 'C').charAt(0).toUpperCase();
        if ($('singleRenNameInput')) {
          $('singleRenNameInput').value = cust.name;
          setTimeout(() => {
            $('singleRenNameInput').focus();
            $('singleRenNameInput').select();
          }, 50);
        }
        if ($('singleRenErr')) {
          $('singleRenErr').textContent = '';
          $('singleRenErr').style.display = 'none';
        }

        if ($('closeDlgSingleCustomerRename')) $('closeDlgSingleCustomerRename').onclick = () => dlg.close();
        if ($('btnCancelSingleRen')) $('btnCancelSingleRen').onclick = () => dlg.close();

        const form = $('formSingleCustomerRename');
        if (form) {
          form.onsubmit = async e => {
            e.preventDefault();
            const errEl = $('singleRenErr');
            if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }

            const newName = ($('singleRenNameInput')?.value || '').trim();
            if (!newName) {
              if (errEl) { errEl.textContent = 'Please enter a valid customer name.'; errEl.style.display = 'block'; }
              return;
            }
            if (newName === cust.name) {
              if (errEl) { errEl.textContent = 'New name is identical to the current customer name.'; errEl.style.display = 'block'; }
              return;
            }

            const btnSave = $('btnSaveSingleRen');
            if (btnSave) { btnSave.disabled = true; btnSave.textContent = 'Saving…'; }

            try {
              if (typeof showBstplLoader === 'function') showBstplLoader(`Renaming customer "${cust.name}" to "${newName}"…`);
              const r = await api('/api/customers/' + cust.id, {
                method: 'PATCH',
                body: JSON.stringify({ name: newName })
              });
              dlg.close();
              toast(`✓ Customer renamed to "${r.name}" in database, cloud table, and website!`);
              await loadCU();
              await updateChrome();
              if (typeof drawCustCards === 'function') drawCustCards();
              loadCustomerFilesContainer();
            } catch (err) {
              if (errEl) { errEl.textContent = err.message || 'Failed to rename customer.'; errEl.style.display = 'block'; }
              else fail(err);
            } finally {
              if (typeof hideBstplLoader === 'function') hideBstplLoader();
              if (btnSave) { btnSave.disabled = false; btnSave.innerHTML = '<span>💾</span> <span>Save New Name</span>'; }
            }
          };
        }

        dlg.showModal();
      }"""

assert old_ren in content, "Could not find exact old_ren"
content = content.replace(old_ren, new_ren, 1)
print("4. Replaced openSingleCustomerRename.")

# 5. Replace openDeleteCustomerEntriesModal
old_del = """      function openDeleteCustomerEntriesModal(cid) {
        if (!canDeleteValidInventory()) {
          toast('⚠️ Master Admins are not permitted to delete valid inventory records.');
          return;
        }
        const cust = CU.find(c => c.id === cid);
        if (!cust) return;

        const dlg = $('dlgDeleteCustomerEntries');
        if (!dlg) return;

        $('delCustTargetName').textContent = cust.name;
        $('delCustDetailName').textContent = cust.name;
        $('delCustRecordsCount').textContent = (cust.devices || 0).toLocaleString() + ' records';
        $('delCustConfirmExpected').textContent = cust.name;
        $('delCustConfirmInput').value = '';
        $('btnConfirmDelCustEntries').disabled = true;

        if ($('closeDlgDeleteCustomerEntries')) $('closeDlgDeleteCustomerEntries').onclick = () => dlg.close();
        if ($('btnCancelDelCustEntries')) $('btnCancelDelCustEntries').onclick = () => dlg.close();

        $('delCustConfirmInput').oninput = () => {
          const val = $('delCustConfirmInput').value.trim();
          $('btnConfirmDelCustEntries').disabled = (val.toLowerCase() !== cust.name.toLowerCase());
        };

        $('btnConfirmDelCustEntries').onclick = async () => {
          const perm = $('delCustPermanentChk').checked;
          const wholeCust = $('delWholeCustChk') ? $('delWholeCustChk').checked : true;
          dlg.close();
          showBstplLoader(`Deleting customer "${cust.name}"…`, 0);

          try {
            if (wholeCust && !perm) {
              await api(`/api/customers/${cid}`, { method: 'DELETE' });
              toast(`✓ Customer "${cust.name}" moved to Cart.`);
            } else {
              const res = await api(`/api/customers/${cid}/delete-all-entries`, {
                method: 'POST',
                body: JSON.stringify({
                  confirm_name: $('delCustConfirmInput').value.trim(),
                  permanent: perm,
                  reason: `Direct deletion of all entries for ${cust.name}`
                })
              });
              toast(`✓ Successfully deleted ${res.deleted_count.toLocaleString()} records for customer "${cust.name}".`);
            }
            await loadCU();
            await updateChrome();
            loadCustomerFilesContainer();
            if (currentInvSubView === 'devices') fetchInventoryRows();
          } catch (err) {
            fail(err);
          } finally {
            hideBstplLoader();
          }
        };

        dlg.showModal();
      }"""

new_del = """      function openDeleteCustomerEntriesModal(cid) {
        if (!canDeleteValidInventory()) {
          toast('⚠️ Master Admins are not permitted to delete valid inventory records.');
          return;
        }
        const cust = (CU || []).find(c => String(c.id) === String(cid));
        if (!cust) return;

        const dlg = $('dlgDeleteCustomerEntries');
        if (!dlg) return;

        if ($('delCustTargetName')) $('delCustTargetName').textContent = cust.name;
        if ($('delCustDetailName')) $('delCustDetailName').textContent = cust.name;
        if ($('delCustRecordsCount')) $('delCustRecordsCount').textContent = (cust.devices || 0).toLocaleString() + ' records';
        if ($('delCustConfirmExpected')) $('delCustConfirmExpected').textContent = cust.name;
        if ($('delCustAvatar')) $('delCustAvatar').textContent = (cust.name || 'C').charAt(0).toUpperCase();
        if ($('delCustConfirmInput')) $('delCustConfirmInput').value = '';
        if ($('btnConfirmDelCustEntries')) {
          $('btnConfirmDelCustEntries').disabled = true;
          $('btnConfirmDelCustEntries').style.cursor = 'not-allowed';
        }

        if ($('closeDlgDeleteCustomerEntries')) $('closeDlgDeleteCustomerEntries').onclick = () => dlg.close();
        if ($('btnCancelDelCustEntries')) $('btnCancelDelCustEntries').onclick = () => dlg.close();

        if ($('delCustConfirmInput')) {
          $('delCustConfirmInput').oninput = () => {
            const val = $('delCustConfirmInput').value.trim();
            const matched = (val.toLowerCase() === cust.name.toLowerCase());
            if ($('btnConfirmDelCustEntries')) {
              $('btnConfirmDelCustEntries').disabled = !matched;
              $('btnConfirmDelCustEntries').style.cursor = matched ? 'pointer' : 'not-allowed';
            }
          };
        }

        if ($('btnConfirmDelCustEntries')) {
          $('btnConfirmDelCustEntries').onclick = async () => {
            const perm = $('delCustPermanentChk') ? $('delCustPermanentChk').checked : false;
            const wholeCust = $('delWholeCustChk') ? $('delWholeCustChk').checked : true;
            dlg.close();
            if (typeof showBstplLoader === 'function') showBstplLoader(`Deleting customer "${cust.name}"…`, 0);

            try {
              if (wholeCust && !perm) {
                await api(`/api/customers/${cust.id}`, { method: 'DELETE' });
                toast(`✓ Customer "${cust.name}" moved to Cart.`);
              } else {
                const res = await api(`/api/customers/${cust.id}/delete-all-entries`, {
                  method: 'POST',
                  body: JSON.stringify({
                    confirm_name: $('delCustConfirmInput').value.trim(),
                    permanent: perm,
                    reason: `Direct deletion of all entries for ${cust.name}`
                  })
                });
                toast(`✓ Successfully deleted ${res.deleted_count.toLocaleString()} records for customer "${cust.name}".`);
              }
              await loadCU();
              await updateChrome();
              if (typeof drawCustCards === 'function') drawCustCards();
              loadCustomerFilesContainer();
              if (currentInvSubView === 'devices') fetchInventoryRows();
            } catch (err) {
              fail(err);
            } finally {
              if (typeof hideBstplLoader === 'function') hideBstplLoader();
            }
          };
        }

        dlg.showModal();
      }"""

assert old_del in content, "Could not find exact old_del"
content = content.replace(old_del, new_del, 1)
print("5. Replaced openDeleteCustomerEntriesModal.")

# 6. Simplify loadCustomerFilesContainer so it doesn't overwrite drawCustCards with old duplicate
old_lcf_start = 'async function loadCustomerFilesContainer() {'
old_lcf_end = 'function openDeleteAllCustomersModal() {'

start_idx = content.find(old_lcf_start)
end_idx = content.find(old_lcf_end)
assert start_idx != -1 and end_idx != -1, f"Could not find loadCustomerFilesContainer boundaries: {start_idx}, {end_idx}"

new_lcf = """async function loadCustomerFilesContainer() {
        await loadCU();
        if ($('invCustCountBadge')) $('invCustCountBadge').textContent = (CU || []).length;
        const staff = myRole() !== 'limited', canDelete = canDeleteValidInventory();
        if ($('cadd')) $('cadd').hidden = false;
        if ($('cbulk')) $('cbulk').hidden = !staff || CU.length < 1;
        if ($('btnRenameAllCust')) $('btnRenameAllCust').hidden = !staff || CU.length < 1;
        if ($('btnDeleteAllCust')) $('btnDeleteAllCust').hidden = !staff || !canDelete || CU.length < 1;

        if ($('chide')) {
          $('chide').onclick = e => {
            custHide = !custHide;
            e.target.textContent = custHide ? 'Show Cards' : 'Hide Cards';
            if (typeof drawCustCards === 'function') drawCustCards();
          };
        }
        if ($('cadd')) {
          $('cadd').onclick = () => {
            openDlg('Add New Customer', `
              <label for="newCName">Customer Name</label>
              <input id="newCName" placeholder="Enter customer name" maxlength="150" required />
            `, 'Create Customer', async () => {
              const n = $('newCName').value.trim();
              if (!n) throw new Error('Please enter customer name');
              await api('/api/customers', { method: 'POST', body: JSON.stringify({ name: n }) });
              toast('Customer created');
              showEventPopup({
                type: 'inserting',
                title: 'Customer Portfolio Created',
                message: `Successfully created new customer portfolio "${n}".`,
                meta: { 'Customer Name': n, 'Status': 'Active' },
                progress: '100% Complete'
              });
              await loadCU();
              await updateChrome();
              loadCustomerFilesContainer();
            });
          };
        }
        if ($('cbulk')) $('cbulk').onclick = bulkRename;
        if ($('btnRenameAllCust')) $('btnRenameAllCust').onclick = () => openRenameAllCustomersModal();
        if ($('btnDeleteAllCust')) $('btnDeleteAllCust').onclick = () => openDeleteAllCustomersModal();

        if (typeof drawCustCards === 'function') {
          drawCustCards();
        }
      }

      """

content = content[:start_idx] + new_lcf + content[end_idx:]
print("6. Simplified loadCustomerFilesContainer to use drawCustCards.")

# Save modified content
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Part 2 successfully applied!")

