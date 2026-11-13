import re

def patch_inventory():
    with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update card template for Customer Files (Equal card dimensions, consistent spacing, professional styling)
    old_card_pattern = r'const card = c => `[\s\S]*?</div>\s*</div>`;'
    new_card = """const card = c => `
          <div class="cw customer-file-card" style="min-height:220px;border:1.5px solid var(--line);border-radius:16px;padding:20px;background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);display:flex;flex-direction:column;justify-content:space-between;gap:14px;transition:all 0.25s cubic-bezier(0.16,1,0.3,1)">
            <div>
              <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:12px;min-width:0">
                  ${avatarHtml(c)}
                  <div style="min-width:0">
                    <b style="font-size:15.5px;font-weight:800;color:var(--text);display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${esc(c.name)}">${esc(c.name)}</b>
                    <span style="font-size:12px;color:var(--muted);font-weight:600">Customer ID: #${c.id}</span>
                  </div>
                </div>
                <span class="tag ${c.devices > 0 ? 'ok' : 'mut'}" style="font-size:11px;font-weight:700;flex-shrink:0">${c.devices > 0 ? 'Active' : 'Empty'}</span>
              </div>
              <div style="font-size:13px;color:var(--muted);margin-top:6px;line-height:1.4">
                <b style="color:var(--text);font-weight:800">${Number(c.devices || 0).toLocaleString()}</b> device records
                ${c.expiring_or_expired ? ` · <span style="color:var(--warn);font-weight:800">${Number(c.expiring_or_expired || 0).toLocaleString()} expiring</span>` : ''}
              </div>
            </div>
            <div class="ca" style="display:flex;gap:6px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:14px">
              <button class="b p" data-cview="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="View all device records for this customer">👁️ Files</button>
              <button class="b" data-cdl="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="Download Excel with all columns and values">📥 Download</button>
              <button class="b" data-cren="${c.id}" style="font-size:12px;padding:6px 10px;font-weight:700" title="Rename customer">✏️ Rename</button>
              ${staff ? `<button class="b" data-cmerge="${c.id}" style="font-size:12px;padding:6px 10px;font-weight:700" title="Merge into another customer">🔀 Merge</button>
              <button class="b" data-cav="${c.id}" style="font-size:12px;padding:6px 8px" title="Change icon">🎨</button>
              <button class="b d" data-cdel="${c.id}" style="font-size:12px;padding:6px 10px;font-weight:700" title="Move customer to Cart">🗑️ Delete</button>` : ''}
            </div>
          </div>`;"""

    # Replace the card template function
    html = re.sub(old_card_pattern, new_card, html, count=1)

    # 2. Add openEditExpiryModal definition before openEditDeviceModal
    expiry_modal_fn = """
    async function openEditExpiryModal(devId) {
      try {
        toast('Loading device expiry details…');
        const dev = await api('/api/devices/' + devId);
        const currDate = dev.expiry_date || '';
        const imei = dev.imei || '—';
        const cname = dev.customer_name || 'Customer';

        const dlgHtml = `
          <div style="margin-bottom:14px">
            <div style="padding:14px 16px;background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;margin-bottom:16px">
              <div style="font-size:14px;font-weight:800;color:var(--text);margin-bottom:4px">Device #${dev.id} · IMEI: <code>${esc(imei)}</code></div>
              <div style="font-size:12.5px;color:var(--muted)">Customer: <b>${esc(cname)}</b> · SIM Type: <b>${esc(dev.sim_type || 'SIM')}</b></div>
              <div style="font-size:12.5px;color:var(--muted);margin-top:4px">Current Expiry Date: <b style="color:var(--primary)">${currDate ? esc(currDate) : 'Not Set'}</b></div>
            </div>
            <label for="newExpDateInput" style="display:block;font-size:12.5px;font-weight:800;margin-bottom:6px;color:var(--text)">
              New Expiry Date * (YYYY-MM-DD)
            </label>
            <input type="date" id="newExpDateInput" value="${esc(currDate)}" style="width:100%;height:44px;padding:0 14px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:14px;font-weight:600" required />
            <div id="newExpDateErr" style="color:var(--danger);font-size:12px;font-weight:700;margin-top:6px;display:none"></div>
          </div>
        `;

        openDlg('📅 Edit SIM Expiry Date', dlgHtml, 'Save Expiry Date', async () => {
          const inp = $('newExpDateInput');
          const errEl = $('newExpDateErr');
          const val = (inp ? inp.value : '').trim();

          if (!val) {
            if (errEl) { errEl.textContent = 'Please select a valid expiry date.'; errEl.style.display = 'block'; }
            throw new Error('Please select a valid expiry date.');
          }

          if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(val) || isNaN(Date.parse(val))) {
            if (errEl) { errEl.textContent = 'Invalid date format. Expected YYYY-MM-DD.'; errEl.style.display = 'block'; }
            throw new Error('Invalid date format.');
          }

          toast('Updating expiry date in database…');
          await api('/api/devices/' + dev.id + '/expiry-date', {
            method: 'PUT',
            body: JSON.stringify({ expiry_date: val })
          });
          toast('SIM expiry date permanently updated to ' + val);
          await fetchInventoryRows();
          await updateChrome();
        }, false);
      } catch(err) {
        fail(err);
      }
    }
"""
    if 'async function openEditExpiryModal' not in html:
        html = html.replace('async function openEditDeviceModal(id) {', expiry_modal_fn + '\n    async function openEditDeviceModal(id) {')

    # 3. Update table actions column to have Edit, Expiry, and Delete with clear styling
    old_act = """const act = dev => `
      <div style="display:flex;gap:4px">
        <button class="b" data-editdev="${dev.id}" style="height:30px;padding:0 8px;font-size:12px">Edit</button>
        ${staff ? `<button class="b d" data-del="${dev.id}" style="height:30px;padding:0 8px;font-size:12px">Delete</button>` : ''}
      </div>`;"""

    new_act = """const act = dev => `
      <div style="display:flex;gap:6px;align-items:center;flex-wrap:nowrap">
        <button class="b" data-editdev="${dev.id}" title="Edit device record" style="height:28px;padding:0 8px;font-size:11.5px;font-weight:700">✏️ Edit</button>
        <button class="b" data-editexp="${dev.id}" title="Edit SIM Expiry Date" style="height:28px;padding:0 8px;font-size:11.5px;font-weight:700">📅 Expiry</button>
        ${staff ? `<button class="b d" data-del="${dev.id}" title="Delete record (Move to Cart)" style="height:28px;padding:0 8px;font-size:11.5px;font-weight:700">🗑️ Delete</button>` : ''}
      </div>`;"""

    html = html.replace(old_act, new_act)

    # 4. Wire invTableWrap.onclick
    table_onclick = """
          // Wire click events inside invTableWrap
          if ($('invTableWrap')) {
            $('invTableWrap').onclick = async e => {
              const editBtn = e.target.closest('[data-editdev]');
              if (editBtn) {
                openEditDeviceModal(editBtn.dataset.editdev);
                return;
              }
              const expBtn = e.target.closest('[data-editexp]');
              if (expBtn) {
                openEditExpiryModal(expBtn.dataset.editexp);
                return;
              }
              const delBtn = e.target.closest('[data-del]');
              if (delBtn) {
                if (!canDeleteValidInventory()) {
                  toast('Access Denied: Master Admins do not have permission to delete inventory records.');
                  return;
                }
                const devId = delBtn.dataset.del;
                const ok = await cv.confirm('Are you sure you want to move device record #' + devId + ' to the Cart?');
                if (!ok) return;
                try {
                  toast('Moving record to Cart…');
                  await api('/api/devices/' + devId, { method: 'DELETE' });
                  toast('Device record moved to Cart successfully');
                  await fetchInventoryRows();
                  await updateChrome();
                } catch(err) {
                  fail(err);
                }
              }
            };
          }
"""
    if 'data-editexp' not in html or 'invTableWrap.onclick' not in html:
        html = html.replace("if ($('invNext')) $('invNext').onclick = () => { invPage++; fetchInventoryRows(); };",
                            "if ($('invNext')) $('invNext').onclick = () => { invPage++; fetchInventoryRows(); };\n" + table_onclick)

    # 5. Wire cgrid.onclick for ALL customer card actions
    cgrid_onclick = """
        // Delegate Customer Card Actions
        if ($('cgrid')) {
          $('cgrid').onclick = async e => {
            const btn = e.target.closest('button');
            if (!btn) return;
            const cid = btn.dataset.cview || btn.dataset.cdl || btn.dataset.c || btn.dataset.cfiles || btn.dataset.cren || btn.dataset.cmerge || btn.dataset.cdel || btn.dataset.cav;
            if (!cid) return;

            const customer = (CU || []).find(x => String(x.id) === String(cid)) || { id: parseInt(cid, 10), name: `Customer #${cid}` };

            if (btn.dataset.cview || btn.dataset.cfiles) {
              await openCustomerEntriesView(customer);
              return;
            }
            if (btn.dataset.cdl) {
              await downloadSingleCustomerExcel(customer);
              return;
            }
            if (btn.dataset.cren) {
              if (typeof openSingleCustomerRename === 'function') openSingleCustomerRename(customer.id);
              else {
                openDlg('Rename Customer', `<label>New Customer Name</label><input id="renCustInp" value="${esc(customer.name)}" required />`, 'Save Name', async () => {
                  const nn = ($('renCustInp').value || '').trim();
                  if (!nn) throw new Error('Name cannot be blank');
                  await api('/api/customers/' + customer.id, { method: 'PATCH', body: JSON.stringify({ name: nn }) });
                  toast('Customer renamed successfully');
                  await loadCU(); await updateChrome(); drawCustCards();
                });
              }
              return;
            }
            if (btn.dataset.cmerge) {
              if (typeof openMergeCustomerModal === 'function') openMergeCustomerModal(customer.id);
              return;
            }
            if (btn.dataset.cdel) {
              if (typeof openDeleteCustomerEntriesModal === 'function') openDeleteCustomerEntriesModal(customer.id);
              else {
                const ok = await cv.confirm('Move customer portfolio "' + customer.name + '" and all its entries to the Cart?');
                if (ok) {
                  await api('/api/customers/' + customer.id, { method: 'DELETE' });
                  toast('Customer moved to Cart');
                  await loadCU(); await updateChrome(); drawCustCards();
                }
              }
              return;
            }
            if (btn.dataset.cav) {
              if (typeof editCustAvatar === 'function') editCustAvatar(customer);
              return;
            }
            if (btn.dataset.c) {
              if ($('invCustSel')) $('invCustSel').value = customer.id;
              invCid = customer.id;
              invPage = 1;
              switchInvSubView('devices');
              fetchInventoryRows();
              return;
            }
          };
        }
"""
    # Replace existing cgrid click delegate block
    old_cgrid_block = re.search(r'// Delegate Customer Card Actions[\s\S]*?switchInvSubView\(currentInvSubView\);', html)
    if old_cgrid_block:
        html = html[:old_cgrid_block.start()] + cgrid_onclick + "\n        initBulkUploadContainer();\n        switchInvSubView(currentInvSubView);" + html[old_cgrid_block.end():]

    with open('frontend/inventory.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("SUCCESS: Patched frontend/inventory.html!")

if __name__ == '__main__':
    patch_inventory()

