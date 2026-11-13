import os, re

FILE_PATH = r"frontend/fetch-data.html"

with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Insert <dialog id="dlgFetchChooseCols"> before <dialog id="devdlg"
dlg_fetch_choose_cols_html = '''
  <!-- Modal: Choose Visible & Unique Columns for Fetch Data -->
  <dialog id="dlgFetchChooseCols" class="modal-card" style="width:min(740px, 94vw);border-radius:18px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.45)">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 22px;border-bottom:1px solid var(--line);background:var(--card)">
      <div style="display:flex;align-items:center;gap:10px">
        <span style="font-size:24px">⚙️</span>
        <div>
          <h3 style="margin:0;font-size:17px;font-weight:800;color:var(--text)">Choose Columns to Fetch &amp; Display</h3>
          <p class="sub" style="margin:2px 0 0;font-size:12px">Customize which fields appear in your search results. Unique custom columns adapt dynamically per customer.</p>
        </div>
      </div>
      <button class="b ghost" id="closeDlgFetchChooseCols" type="button" onclick="closeModal('dlgFetchChooseCols')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">✕</button>
    </div>

    <div style="padding:18px 22px;max-height:calc(85vh - 75px);overflow-y:auto">
      <!-- Customer Context Pill -->
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;padding:10px 14px;background:var(--card-subtle);border-radius:10px;border:1px solid var(--line);margin-bottom:14px">
        <div style="font-size:13px;color:var(--text)">
          <span>Customer Scope:</span> <b id="dlgFetchScopeCustName" style="color:var(--primary)">All Customers</b>
        </div>
        <span class="badge" id="dlgFetchTotalColsBadge" style="background:var(--card);border:1px solid var(--line);font-size:11.5px;font-weight:700;padding:4px 10px;border-radius:99px">15 Standard + 0 Dynamic</span>
      </div>

      <!-- Presets Toolbar -->
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px">
        <span style="font-size:12px;font-weight:700;color:var(--muted);text-transform:uppercase">Quick Presets:</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <button class="b" id="btnDlgFetchPresetAll" type="button" style="font-size:11.5px;padding:4px 10px;font-weight:700">📋 All Columns</button>
          <button class="b" id="btnDlgFetchPresetSim" type="button" style="font-size:11.5px;padding:4px 10px;font-weight:700">⚡ SIM &amp; Expiry</button>
          <button class="b" id="btnDlgFetchPresetId" type="button" style="font-size:11.5px;padding:4px 10px;font-weight:700">🏷️ Basic Identifiers</button>
          <button class="b" id="btnDlgFetchPresetUnique" type="button" style="font-size:11.5px;padding:4px 10px;font-weight:700">✨ Unique Custom Only</button>
          <button class="b" id="btnDlgFetchPresetClear" type="button" style="font-size:11.5px;padding:4px 10px">✕ Clear</button>
        </div>
      </div>

      <!-- Search Filter for Columns -->
      <div style="margin-bottom:12px">
        <input id="dlgFetchColsSearchInput" placeholder="Filter columns by name…" style="width:100%;height:38px;padding:0 12px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text);font-size:13px" />
      </div>

      <!-- Column Checkboxes Chips Grid -->
      <div id="dlgFetchColsListGrid" style="display:flex;flex-wrap:wrap;gap:8px;max-height:260px;overflow-y:auto;padding:12px;background:var(--card-subtle);border-radius:10px;border:1px solid var(--line)">
      </div>

      <div style="display:flex;align-items:center;justify-content:space-between;margin-top:16px;padding-top:14px;border-top:1px solid var(--line);flex-wrap:wrap;gap:10px">
        <span style="font-size:12.5px;color:var(--muted);font-weight:600" id="dlgFetchColsCountText">0 columns selected</span>
        <div style="display:flex;gap:8px">
          <button class="b" id="cancelDlgFetchChooseCols" type="button" onclick="closeModal('dlgFetchChooseCols')">Cancel</button>
          <button class="b p" id="btnConfirmFetchChooseCols" type="button" style="font-weight:700;background:var(--primary);color:#fff">Apply &amp; Fetch Data</button>
        </div>
      </div>
    </div>
  </dialog>
'''

if 'id="dlgFetchChooseCols"' not in content:
    target = '<dialog id="devdlg"'
    if target in content:
        content = content.replace(target, dlg_fetch_choose_cols_html + '\n  ' + target, 1)
        print("Inserted dlgFetchChooseCols into fetch-data.html")
    else:
        print("WARNING: Could not find insertion point <dialog id=\"devdlg\" in fetch-data.html")
else:
    print("dlgFetchChooseCols already in fetch-data.html")

# 2. Add Choose Columns (Popup) button to Search Controls bar
old_btn_row = '''<div style="display:flex;gap:8px">
              <button class="b p" id="btnRunNormalFetch" type="button"
                style="height:38px;padding:0 20px;font-weight:700">🔍 Fetch Data</button>
              <button class="b" id="btnResetNormalFetch" type="button" style="height:38px">Reset</button>
            </div>'''

new_btn_row = '''<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
              <button class="b p" id="btnRunNormalFetch" type="button"
                style="height:38px;padding:0 20px;font-weight:700">🔍 Fetch Data</button>
              <button class="b" id="btnOpenFetchColsPopup" type="button" onclick="openFetchChooseColsModal()"
                style="height:38px;padding:0 14px;font-weight:700;display:inline-flex;align-items:center;gap:6px;background:var(--card);border:1.5px solid var(--primary);color:var(--primary);border-radius:8px;cursor:pointer" title="Choose which columns to fetch and display, including customer-specific unique columns">
                <span>⚙️</span> <span>Choose Columns</span>
              </button>
              <button class="b" id="btnResetNormalFetch" type="button" style="height:38px">Reset</button>
            </div>'''

if old_btn_row in content:
    content = content.replace(old_btn_row, new_btn_row, 1)
    print("Added btnOpenFetchColsPopup into Search Controls Bar")
else:
    # Try with CRLF
    old_btn_row_crlf = old_btn_row.replace('\n', '\r\n')
    new_btn_row_crlf = new_btn_row.replace('\n', '\r\n')
    if old_btn_row_crlf in content:
        content = content.replace(old_btn_row_crlf, new_btn_row_crlf, 1)
        print("Added btnOpenFetchColsPopup into Search Controls Bar (CRLF)")
    else:
        print("WARNING: Could not find old_btn_row in fetch-data.html")

# 3. Add openFetchChooseColsModal function into javascript
fetch_cols_js = '''
    let fetchCustomSelectedCols = null;

    async function openFetchChooseColsModal() {
      const dlg = $('dlgFetchChooseCols');
      if (!dlg) return;

      const custSel = $('fCust');
      const selectedCid = custSel ? custSel.value : '';
      const selectedCust = (typeof CU !== 'undefined' && Array.isArray(CU)) ? CU.find(c => String(c.id) === String(selectedCid)) : null;
      const custName = selectedCust ? selectedCust.name : (selectedCid ? `Customer #${selectedCid}` : 'All Customers');

      if ($('dlgFetchScopeCustName')) $('dlgFetchScopeCustName').textContent = custName;

      // Discover all standard columns
      const standardCols = (typeof COLS !== 'undefined' ? COLS : []).map(c => ({ key: c[0], label: c[1], isUnique: false }));

      // Discover unique extra columns for this customer or global column registry
      const extraKeysSet = new Set(typeof XC !== 'undefined' ? XC : []);

      if (selectedCid) {
        try {
          const sampleRes = await api(`/api/devices?customer_id=${selectedCid}&page_size=50`);
          if (sampleRes && sampleRes.items) {
            sampleRes.items.forEach(it => {
              if (it.extra && typeof it.extra === 'object') {
                Object.keys(it.extra).forEach(k => extraKeysSet.add(k));
              }
            });
          }
        } catch(e) {}
      }

      const extraCols = Array.from(extraKeysSet).map(k => ({
        key: k,
        label: k.replace(/_/g, ' '),
        isUnique: true
      }));

      const allCols = [
        { key: 'customer_name', label: 'Customer Name', isUnique: false },
        ...standardCols,
        ...extraCols,
        { key: 'added_by', label: 'Added By', isUnique: false },
        { key: 'created_at', label: 'Added On', isUnique: false }
      ];

      if ($('dlgFetchTotalColsBadge')) {
        $('dlgFetchTotalColsBadge').textContent = `${standardCols.length + 3} Standard + ${extraCols.length} Dynamic`;
      }

      // Pre-selected set
      const activeKeys = fetchCustomSelectedCols ? new Set(fetchCustomSelectedCols) : new Set(allCols.map(c => c.key));

      const renderGrid = (filterTerm = '') => {
        const grid = $('dlgFetchColsListGrid');
        if (!grid) return;
        const term = (filterTerm || '').toLowerCase().trim();
        const visibleCols = term ? allCols.filter(c => c.label.toLowerCase().includes(term) || c.key.toLowerCase().includes(term)) : allCols;

        grid.innerHTML = visibleCols.map(c => {
          const isChecked = activeKeys.has(c.key);
          return `
            <label class="col-pill-chip ${isChecked ? 'active' : ''}" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border:1.5px solid ${isChecked ? 'var(--primary)' : 'var(--line)'};background:${isChecked ? 'var(--card-subtle)' : 'var(--card)'};border-radius:20px;cursor:pointer;font-size:12px;font-weight:600;transition:all .15s">
              <input type="checkbox" class="fetch-dlg-chk" value="${c.key}" ${isChecked ? 'checked' : ''} style="width:14px;height:14px;margin:0;accent-color:var(--primary)" />
              <span>${esc(c.label)}</span>
              ${c.isUnique ? '<span class="tag info" style="font-size:10px;padding:2px 6px;margin-left:2px">Unique</span>' : ''}
            </label>
          `;
        }).join('');

        const updateCount = () => {
          const totalChecked = activeKeys.size;
          if ($('dlgFetchColsCountText')) $('dlgFetchColsCountText').textContent = `${totalChecked} of ${allCols.length} columns selected`;
          if ($('btnConfirmFetchChooseCols')) $('btnConfirmFetchChooseCols').disabled = (totalChecked === 0);
        };

        grid.querySelectorAll('.fetch-dlg-chk').forEach(chk => {
          chk.onchange = e => {
            const val = e.target.value;
            if (e.target.checked) activeKeys.add(val);
            else activeKeys.delete(val);
            const chip = e.target.closest('.col-pill-chip');
            if (chip) {
              chip.classList.toggle('active', e.target.checked);
              chip.style.borderColor = e.target.checked ? 'var(--primary)' : 'var(--line)';
              chip.style.background = e.target.checked ? 'var(--card-subtle)' : 'var(--card)';
            }
            updateCount();
          };
        });

        updateCount();
      };

      renderGrid();

      if ($('dlgFetchColsSearchInput')) {
        $('dlgFetchColsSearchInput').value = '';
        $('dlgFetchColsSearchInput').oninput = e => renderGrid(e.target.value);
      }

      if ($('btnDlgFetchPresetAll')) {
        $('btnDlgFetchPresetAll').onclick = () => {
          allCols.forEach(c => activeKeys.add(c.key));
          renderGrid($('dlgFetchColsSearchInput') ? $('dlgFetchColsSearchInput').value : '');
        };
      }

      if ($('btnDlgFetchPresetClear')) {
        $('btnDlgFetchPresetClear').onclick = () => {
          activeKeys.clear();
          renderGrid($('dlgFetchColsSearchInput') ? $('dlgFetchColsSearchInput').value : '');
        };
      }

      if ($('btnDlgFetchPresetSim')) {
        $('btnDlgFetchPresetSim').onclick = () => {
          activeKeys.clear();
          ['customer_name', 'imei', 'iccid', 'msisdn1', 'msisdn2', 'act_date', 'expiry_date', 'sim_provider', 'sim_type'].forEach(k => activeKeys.add(k));
          renderGrid($('dlgFetchColsSearchInput') ? $('dlgFetchColsSearchInput').value : '');
        };
      }

      if ($('btnDlgFetchPresetId')) {
        $('btnDlgFetchPresetId').onclick = () => {
          activeKeys.clear();
          ['customer_name', 'imei', 'device_sr_no', 'iccid', 'model'].forEach(k => activeKeys.add(k));
          renderGrid($('dlgFetchColsSearchInput') ? $('dlgFetchColsSearchInput').value : '');
        };
      }

      if ($('btnDlgFetchPresetUnique')) {
        $('btnDlgFetchPresetUnique').onclick = () => {
          activeKeys.clear();
          activeKeys.add('customer_name');
          activeKeys.add('imei');
          extraCols.forEach(c => activeKeys.add(c.key));
          renderGrid($('dlgFetchColsSearchInput') ? $('dlgFetchColsSearchInput').value : '');
        };
      }

      if ($('closeDlgFetchChooseCols')) $('closeDlgFetchChooseCols').onclick = () => dlg.close();
      if ($('cancelDlgFetchChooseCols')) $('cancelDlgFetchChooseCols').onclick = () => dlg.close();

      if ($('btnConfirmFetchChooseCols')) {
        $('btnConfirmFetchChooseCols').onclick = () => {
          if (!activeKeys.size) {
            toast('Please select at least one column.');
            return;
          }
          fetchCustomSelectedCols = Array.from(activeKeys);
          dlg.close();

          const rCustom = document.querySelector('input[name="nfViewOpt"][value="custom"]');
          if (rCustom) rCustom.checked = true;
          document.querySelectorAll('#nfViewOptGroup .view-opt-card').forEach(c => c.classList.remove('on'));
          const lblCustom = $('lblOptCustom');
          if (lblCustom) lblCustom.classList.add('on');

          document.querySelectorAll('.nf-col-chk').forEach(chk => {
            chk.checked = activeKeys.has(chk.value);
            const chip = chk.closest('.col-pill-chip');
            if (chip) {
              chip.classList.toggle('active', chk.checked);
              chip.style.borderColor = chk.checked ? 'var(--primary)' : 'var(--line)';
              chip.style.background = chk.checked ? 'var(--card-subtle)' : 'var(--card)';
            }
          });

          toast(`✓ Applied ${activeKeys.size} visible columns.`);
          if (typeof runNormalFetch === 'function') runNormalFetch(1);
        };
      }

      if (typeof dlg.showModal === 'function') dlg.showModal();
    }
    window.openFetchChooseColsModal = openFetchChooseColsModal;
'''

if 'function openFetchChooseColsModal' not in content:
    pos = content.find('function renderNfCustomColsCheckboxes()')
    if pos != -1:
        content = content[:pos] + fetch_cols_js + '\n\n      ' + content[pos:]
        print("Inserted openFetchChooseColsModal into fetch-data.html")
    else:
        pos = content.rfind('</script>')
        content = content[:pos] + fetch_cols_js + '\n' + content[pos:]
        print("Inserted openFetchChooseColsModal before </script> in fetch-data.html")
else:
    print("openFetchChooseColsModal already in fetch-data.html")

# 4. Wire lblOptCustom click to also open openFetchChooseColsModal
content = content.replace(
    "$('lblOptCustom').onclick = () => {",
    "$('lblOptCustom').onclick = () => { openFetchChooseColsModal();"
)

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Fetch-data updates successfully applied!")
