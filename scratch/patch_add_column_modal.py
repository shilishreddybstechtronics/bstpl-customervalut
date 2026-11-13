with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

add_col_fn = """
    function openAddColumnModal() {
      const dlg = $('dlgAddColumn');
      if (!dlg) return;
      if ($('newColName')) $('newColName').value = '';
      if ($('newColValue')) $('newColValue').value = '';
      if ($('newColImeis')) $('newColImeis').value = '';
      if ($('newColErr')) { $('newColErr').textContent = ''; $('newColErr').style.display = 'none'; }
      if ($('newColTarget')) $('newColTarget').value = 'all';
      if ($('newColCustWrap')) $('newColCustWrap').style.display = 'none';
      if ($('newColImeisWrap')) $('newColImeisWrap').style.display = 'none';

      // Populate customer options
      if ($('newColCustSel')) {
        let custOpts = '<option value="">-- Choose Customer --</option>';
        custOpts += (CU || []).map(c => `<option value="${c.id}">${esc(c.name || c.customer_name)}</option>`).join('');
        $('newColCustSel').innerHTML = custOpts;
        if (typeof invCid !== 'undefined' && invCid) $('newColCustSel').value = invCid;
      }

      if ($('newColTarget')) {
        $('newColTarget').onchange = () => {
          const t = $('newColTarget').value;
          if ($('newColCustWrap')) $('newColCustWrap').style.display = (t === 'customer') ? 'block' : 'none';
          if ($('newColImeisWrap')) $('newColImeisWrap').style.display = (t === 'specified') ? 'block' : 'none';
        };
      }

      if ($('closeDlgAddColumn')) $('closeDlgAddColumn').onclick = () => dlg.close();
      if ($('cancelDlgAddColumn')) $('cancelDlgAddColumn').onclick = () => dlg.close();

      if ($('formAddColumn')) {
        $('formAddColumn').onsubmit = async e => {
          e.preventDefault();
          if ($('newColErr')) { $('newColErr').textContent = ''; $('newColErr').style.display = 'none'; }
          const colName = ($('newColName')?.value || '').trim();
          if (!colName) {
            if ($('newColErr')) { $('newColErr').textContent = 'Please enter a column name.'; $('newColErr').style.display = 'block'; }
            return;
          }

          const target = $('newColTarget')?.value || 'all';
          let customerId = null;
          let imeis = null;

          if (target === 'customer') {
            const cid = parseInt($('newColCustSel')?.value);
            if (!cid) {
              if ($('newColErr')) { $('newColErr').textContent = 'Please select a customer.'; $('newColErr').style.display = 'block'; }
              return;
            }
            customerId = cid;
          } else if (target === 'specified') {
            const raw = ($('newColImeis')?.value || '').split(/[\\r\\n,]+/).map(s => s.trim()).filter(Boolean);
            if (!raw.length) {
              if ($('newColErr')) { $('newColErr').textContent = 'Please enter at least one IMEI.'; $('newColErr').style.display = 'block'; }
              return;
            }
            imeis = raw;
            if (typeof invCid !== 'undefined' && invCid) customerId = parseInt(invCid);
          } else if (target === 'all' && typeof invCid !== 'undefined' && invCid) {
            customerId = parseInt(invCid);
          }

          const val = $('newColValue')?.value || '';
          const btn = $('btnSubmitAddColumn');
          if (btn) { btn.disabled = true; btn.textContent = 'Adding Column…'; }

          try {
            const res = await api('/api/columns/add', {
              method: 'POST',
              body: JSON.stringify({
                column_name: colName,
                target: target,
                customer_id: customerId,
                imeis: imeis,
                value: val !== '' ? val : null
              })
            });
            dlg.close();
            toast(`Column "${res.column || colName}" added successfully`);
            if (typeof fetchInventoryRows === 'function') await fetchInventoryRows();
          } catch(err) {
            if ($('newColErr')) { $('newColErr').textContent = err.message || 'Failed to add column'; $('newColErr').style.display = 'block'; }
          } finally {
            if (btn) { btn.disabled = false; btn.textContent = '➕ Add Column'; }
          }
        };
      }

      if (typeof dlg.showModal === 'function') dlg.showModal();
    }
"""

anchor = "function openAddDeviceModal() {"
assert anchor in text, "anchor not found in build_clean_modular_app.py"

if 'function openAddColumnModal' not in text:
    text = text.replace(anchor, add_col_fn + "\n    " + anchor, 1)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added openAddColumnModal to build_clean_modular_app.py successfully!")

