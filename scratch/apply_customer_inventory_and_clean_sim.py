import re, sys

print("Applying Customer Inventory enhancements and removing Restore All card...")

with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    text = f.read()

# -----------------------------------------------------------------------------
# 1. REMOVE simRestoreAllCard completely (HTML & JS)
# -----------------------------------------------------------------------------
# Remove the HTML injection
old_restore_all_card_block = r'''# 2. Customization for containers['box-sim']: Add Restore All soft-deleted records card
box_sim_html = containers['box-sim']
restore_all_card_html = '''<!-- Dedicated Restore All Soft-Deleted SIMs Card (Requirement 6.B) -->
        <div class="card" id="simRestoreAllCard" style="margin-top:20px;padding:20px 24px;border:1.5px solid var(--primary);border-radius:14px;background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.04)">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px">
            <div style="display:flex;align-items:center;gap:14px">
              <div style="width:48px;height:48px;border-radius:12px;background:rgba(29,104,225,0.12);color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:24px">
                ♻️
              </div>
              <div>
                <h3 style="margin:0;font-size:16px;font-weight:800;color:var(--text)">Restore All Deleted / Archived SIMs</h3>
                <p class="sub" style="margin:4px 0 0;font-size:13px">Restore all soft-deleted inventory records from the Recycle Bin back into active database accounts. Active IMEIs are safely preserved.</p>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:12px">
              <div style="text-align:right">
                <span style="font-size:12px;color:var(--muted);display:block">Soft-deleted SIMs</span>
                <span id="simRestoreCountBadge" style="font-size:16px;font-weight:800;color:var(--primary)">0 records</span>
              </div>
              <button type="button" class="b p" id="btnSimRestoreAll" style="padding:10px 18px;font-weight:700;border-radius:9px;background:linear-gradient(135deg, var(--primary), #2563eb)">
                ♻️ Restore All Records
              </button>
            </div>
          </div>
        </div>

        <div id="simMainContent">'''

if 'id="simRestoreAllCard"' not in box_sim_html:
    box_sim_html = box_sim_html.replace('<div id="simMainContent">', restore_all_card_html, 1)
    containers['box-sim'] = box_sim_html'''

new_restore_all_cleanup = '''# 2. Ensure Restore All card is removed per user request
box_sim_html = containers['box-sim']
box_sim_html = re.sub(r'<!--\s*Dedicated\s*Restore\s*All\s*Soft-Deleted\s*SIMs\s*Card[\s\S]*?</div>\s*</div>\s*</div>', '', box_sim_html)
containers['box-sim'] = box_sim_html'''

if old_restore_all_card_block in text:
    text = text.replace(old_restore_all_card_block, new_restore_all_cleanup, 1)
    print("✓ Removed simRestoreAllCard HTML injection")

# Remove the JS restore_all_js block
old_restore_js_call = "feature_blocks['SIM'] = loc['feature_blocks']['SIM'] + \"\\n\\n\" + restore_all_js"
new_restore_js_call = "feature_blocks['SIM'] = loc['feature_blocks']['SIM']"

if old_restore_js_call in text:
    text = text.replace(old_restore_js_call, new_restore_js_call, 1)
    print("✓ Removed restore_all_js attachment to SIM block")

# -----------------------------------------------------------------------------
# 2. Enhance containers['box-inv']: Design Subnav & Search Customer Cards
# -----------------------------------------------------------------------------
box_inv_customization = '''
# 2.5 Customize containers['box-inv'] (Subnav & Search Customer Cards)
box_inv_html = containers['box-inv']

# Design Subnav: 📋 Device Records | 📁 Customer Files (154) | 📤 Bulk Upload
old_subnav = r'<div class="inv-subnav" role="tablist">[\s\S]*?</div>'
new_subnav = """<div class="inv-subnav" role="tablist" style="display:flex;gap:10px;margin:18px 0;border-bottom:1px solid var(--line);padding-bottom:12px;flex-wrap:wrap">
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
box_inv_html = re.sub(old_subnav, new_subnav, box_inv_html, count=1)

# Design Search Customer Cards Bar & Action Toolbar in subViewCust
old_cust_search = r'<div class="row" style="margin-top:14px">\s*<div class="grow">\s*<label for="cs">Search Customer Cards</label>\s*<input id="cs" placeholder="Filter by customer name…" />\s*</div>\s*</div>'
new_cust_search = """<div style="margin-top:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
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
box_inv_html = re.sub(old_cust_search, new_cust_search, box_inv_html, count=1)

# Ensure #cgrid uses modern grid styling
box_inv_html = box_inv_html.replace('<div id="cgrid"></div>', '<div id="cgrid" style="margin-top:16px"></div>')

containers['box-inv'] = box_inv_html
'''

if "# 2.5 Customize containers['box-inv']" not in text:
    anchor = "containers['box-sim'] = box_sim_html"
    idx_a = text.find(anchor)
    if idx_a != -1:
        text = text[:idx_a + len(anchor)] + "\n" + box_inv_customization + text[idx_a + len(anchor):]
        print("✓ Injected box-inv customizations (Subnav & Search Customer Cards)")

# -----------------------------------------------------------------------------
# 3. Enhance feature_blocks['INV']:
# - Customer card: "Files (View Entries)" + "Download Excel" (all columns)
# - View Entries modal: displays all entries and columns
# - Single Customer Download: exports all column names & values
# - "Download All": multi-sheet Excel with customer sheets and user-chosen columns
# -----------------------------------------------------------------------------

enhanced_inv_code = r'''
        // --- 1. Dynamic Subnav & Badge Count ---
        if ($('invCustCountBadge')) $('invCustCountBadge').textContent = (CU || []).length || '154';

        // --- 2. Customer Cards Grid & Search (Requirement: Grid Format & Search) ---
        const card = c => `
          <div class="cw" style="border:1.5px solid var(--line);border-radius:14px;padding:16px 18px;background:var(--card);box-shadow:0 2px 10px rgba(0,0,0,0.03);display:flex;flex-direction:column;justify-content:space-between;gap:14px;transition:all 0.25s cubic-bezier(0.16,1,0.3,1)">
            <div>
              <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px">
                <div style="display:flex;align-items:center;gap:10px">
                  ${avatarHtml(c)}
                  <div>
                    <b style="font-size:15px;color:var(--text);display:block">${esc(c.name)}</b>
                    <span style="font-size:12px;color:var(--muted)">Customer ID: #${c.id}</span>
                  </div>
                </div>
                <span class="tag ${c.devices > 0 ? 'ok' : 'mut'}" style="font-size:11px">${c.devices > 0 ? 'Active' : 'Empty'}</span>
              </div>
              <div style="font-size:12.5px;color:var(--muted);margin-top:6px">
                <b style="color:var(--text)">${Number(c.devices || 0).toLocaleString()}</b> device records
                ${c.expiring_or_expired ? ` · <span style="color:var(--warn);font-weight:700">${Number(c.expiring_or_expired || 0).toLocaleString()} expiring</span>` : ''}
              </div>
            </div>
            <div class="ca" style="display:flex;gap:6px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:12px">
              <button class="b p" data-cview="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="View all device entries for this customer">👁️ Files (View Entries)</button>
              <button class="b" data-cdl="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="Download Excel with all columns and values">📥 Download Excel</button>
              <button class="b" data-cav="${c.id}" style="font-size:12px;padding:6px 8px" title="Change icon">🎨</button>
              ${staff ? `<button class="b" data-cren="${c.id}" style="font-size:12px;padding:6px 8px">Rename</button>
              <button class="b" data-cmerge="${c.id}" style="font-size:12px;padding:6px 8px">Merge</button>` : ''}
              ${canDelete ? `<button class="b d" data-cdel="${c.id}" style="font-size:12px;padding:6px 8px">Delete</button>` : ''}
            </div>
          </div>`;

        const drawCustCards = () => {
          const inp = $('cs');
          const q = (inp ? inp.value : '').trim().toLowerCase();
          const clearBtn = $('csClearBtn');
          if (clearBtn) clearBtn.style.display = q ? 'block' : 'none';

          const filtered = (CU || []).filter(c => (c.name || '').toLowerCase().includes(q));
          if ($('csFilterCount')) {
            $('csFilterCount').textContent = q ? `Showing ${filtered.length} of ${CU.length} portfolios` : `Showing all ${CU.length} customer portfolios`;
          }

          const gridHtml = filtered.map(card).join('');
          $('cgrid').innerHTML = custHide ? '<div class="empty">Customer cards are hidden.</div>' : `
            <div class="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px">
              ${gridHtml || `<div class="empty">${CU.length ? 'No customer matches your search.' : 'No customers found.'}</div>`}
            </div>`;
        };

        if ($('cs')) $('cs').oninput = drawCustCards;
        if ($('csClearBtn')) {
          $('csClearBtn').onclick = () => {
            if ($('cs')) $('cs').value = '';
            $('csClearBtn').style.display = 'none';
            drawCustCards();
          };
        }

        // --- 3. Files Option as View Option: Display All Entries for Customer ---
        async function openCustomerEntriesView(customer) {
          try {
            toast(`Loading entries for ${customer.name}…`);
            if (typeof showBstplLoader === 'function') showBstplLoader(`Fetching all entries for ${customer.name}…`);

            const res = await api(`/api/devices?customer_id=${customer.id}&page_size=50000`);
            const items = (res && res.items) ? res.items : [];

            // Discover all dynamic columns
            const extraKeys = new Set();
            items.forEach(it => {
              if (it.extra && typeof it.extra === 'object') {
                Object.keys(it.extra).forEach(k => extraKeys.add(k));
              }
            });
            const allExtras = Array.from(new Set([...XC, ...extraKeys]));

            const viewCols = [
              { key: 'id', label: 'ID' },
              { key: 'customer_name', label: 'Customer' },
              ...COLS.map(c => ({ key: c[0], label: c[1] })),
              ...allExtras.map(k => ({ key: k, label: k.replace(/_/g, ' ').toUpperCase() })),
              { key: 'added_by', label: 'Added By' },
              { key: 'created_at', label: 'Created At' }
            ];

            const dlgHtml = `
              <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:14px;border-bottom:1px solid var(--line);padding-bottom:12px">
                <div>
                  <h4 style="margin:0;font-size:15px;color:var(--text)">${esc(customer.name)}</h4>
                  <span style="font-size:12.5px;color:var(--muted)">${items.length.toLocaleString()} device entries</span>
                </div>
                <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
                  <div class="cv-search-container" style="min-width:200px">
                    <span class="cv-search-icon-left">🔎</span>
                    <input id="dlgViewCustSearch" class="cv-search-input" style="height:34px;font-size:12.5px" placeholder="Search within entries…" />
                  </div>
                  <button type="button" class="b p" id="btnDlgCustDlExcel" style="font-size:12.5px;font-weight:700">📥 Download Excel</button>
                  <button type="button" class="b" id="btnDlgJumpToEditor" style="font-size:12.5px">📋 Edit in Inventory</button>
                </div>
              </div>
              <div class="tw" style="max-height:56vh;overflow:auto" id="dlgCustViewTableWrap">
                <table style="font-size:12px">
                  <thead>
                    <tr>
                      ${viewCols.map(c => `<th>${esc(c.label)}</th>`).join('')}
                    </tr>
                  </thead>
                  <tbody>
                    ${items.length ? items.map(d => `
                      <tr>
                        <td><b>${d.id}</b></td>
                        <td>${esc(customer.name)}</td>
                        ${COLS.map(c => `<td>${cell(d, c[0])}</td>`).join('')}
                        ${allExtras.map(k => `<td>${esc((d.extra || {})[k] != null ? (d.extra || {})[k] : '')}</td>`).join('')}
                        <td>${esc(d.added_by || '')}</td>
                        <td>${esc(d.created_at || '')}</td>
                      </tr>
                    `).join('') : '<tr><td colspan="30" class="empty">No device entries found for this customer.</td></tr>'}
                  </tbody>
                </table>
              </div>
            `;

            openDlg(`📁 Customer Entries — ${customer.name} (${items.length.toLocaleString()})`, dlgHtml, 'Close', async () => {});

            if ($('dlgViewCustSearch')) {
              $('dlgViewCustSearch').oninput = e => {
                const term = e.target.value.toLowerCase().trim();
                const rows = document.querySelectorAll('#dlgCustViewTableWrap tbody tr');
                rows.forEach(r => {
                  r.style.display = (!term || r.textContent.toLowerCase().includes(term)) ? '' : 'none';
                });
              };
            }

            if ($('btnDlgCustDlExcel')) {
              $('btnDlgCustDlExcel').onclick = () => downloadSingleCustomerExcel(customer);
            }

            if ($('btnDlgJumpToEditor')) {
              $('btnDlgJumpToEditor').onclick = () => {
                closeDlg();
                if ($('invCustSel')) $('invCustSel').value = customer.id;
                invCid = customer.id;
                invPage = 1;
                switchInvSubView('devices');
              };
            }
          } catch(err) {
            fail(err);
          } finally {
            if (typeof hideBstplLoader === 'function') hideBstplLoader();
          }
        }

        // --- 4. Single Customer Excel Download with ALL Columns & Values ---
        async function downloadSingleCustomerExcel(customer) {
          try {
            toast(`Generating Excel for ${customer.name}…`);
            if (typeof showBstplLoader === 'function') showBstplLoader(`Generating Excel file for ${customer.name}…`);

            const res = await api(`/api/devices?customer_id=${customer.id}&page_size=50000`);
            const items = (res && res.items) ? res.items : [];
            if (!items.length) {
              toast(`No records found for ${customer.name}.`);
              return;
            }

            const extraKeys = new Set();
            items.forEach(it => {
              if (it.extra && typeof it.extra === 'object') {
                Object.keys(it.extra).forEach(k => extraKeys.add(k));
              }
            });
            const allExtras = Array.from(new Set([...XC, ...extraKeys]));

            const headers = ['ID', 'Customer Name', ...COLS.map(c => c[1]), ...allExtras.map(k => k.replace(/_/g, ' ').toUpperCase()), 'Added By', 'Created At'];
            const rows = items.map(d => [
              d.id,
              customer.name,
              ...COLS.map(c => d[c[0]] != null ? d[c[0]] : ''),
              ...allExtras.map(k => (d.extra || {})[k] != null ? (d.extra || {})[k] : ''),
              d.added_by != null ? d.added_by : '',
              d.created_at != null ? d.created_at : ''
            ]);

            const safeName = (customer.name || 'Customer').replace(/[^a-zA-Z0-9_-]/g, '_');
            exportExcel(`${safeName}_Complete_Inventory`, headers, rows);
          } catch(err) {
            fail(err);
          } finally {
            if (typeof hideBstplLoader === 'function') hideBstplLoader();
          }
        }

        // --- 5. "Download All": Multi-Sheet Excel with Customer Names & User-Chosen Columns ---
        function openDownloadAllColumnChooser() {
          const allCols = [
            { key: 'id', label: 'ID', checked: true },
            { key: 'customer_name', label: 'Customer Name', checked: true },
            ...COLS.map(c => ({ key: c[0], label: c[1], checked: true })),
            ...XC.map(c => ({ key: c, label: c.replace(/_/g, ' ').toUpperCase(), checked: true })),
            { key: 'added_by', label: 'Added By', checked: false },
            { key: 'created_at', label: 'Created At', checked: false }
          ];

          const dlgHtml = `
            <div style="margin-bottom:12px">
              <p style="font-size:13px;color:var(--text);margin:0 0 10px">
                Choose the columns to include in the multi-customer workbook. <b>Each customer will have an individual sheet named after the customer</b>.
              </p>
              <div style="display:flex;gap:8px;margin-bottom:10px">
                <button type="button" class="b" id="btnDlgChooseSelectAll" style="font-size:12px;padding:4px 10px">Select All</button>
                <button type="button" class="b" id="btnDlgChooseDeselectAll" style="font-size:12px;padding:4px 10px">Deselect All</button>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px;max-height:46vh;overflow:auto;padding:8px;border:1px solid var(--line);border-radius:10px;background:var(--card-subtle)" id="dlgChooseColList">
              ${allCols.map(col => `
                <label style="display:flex;align-items:center;gap:8px;font-size:12px;padding:6px 10px;background:var(--card);border:1px solid var(--line);border-radius:6px;cursor:pointer">
                  <input type="checkbox" class="export-col-chk" value="${col.key}" data-label="${esc(col.label)}" ${col.checked ? 'checked' : ''} style="width:16px;height:16px;margin:0" />
                  <span>${esc(col.label)}</span>
                </label>
              `).join('')}
            </div>
          `;

          openDlg('📥 Download All Customers (Individual Sheets)', dlgHtml, '🚀 Download Workbook', async () => {
            const checkedInps = Array.from(document.querySelectorAll('.export-col-chk:checked'));
            if (!checkedInps.length) throw new Error('Please select at least one column to download.');
            const chosenCols = checkedInps.map(inp => ({ key: inp.value, label: inp.dataset.label }));
            await executeMultiCustomerDownload(chosenCols);
          });

          if ($('btnDlgChooseSelectAll')) {
            $('btnDlgChooseSelectAll').onclick = () => {
              document.querySelectorAll('.export-col-chk').forEach(c => c.checked = true);
            };
          }
          if ($('btnDlgChooseDeselectAll')) {
            $('btnDlgChooseDeselectAll').onclick = () => {
              document.querySelectorAll('.export-col-chk').forEach(c => c.checked = false);
            };
          }
        }

        async function executeMultiCustomerDownload(chosenCols) {
          try {
            toast('Fetching database records for multi-sheet workbook…');
            if (typeof showBstplLoader === 'function') {
              showBstplLoader('Generating multi-sheet Excel workbook with customer sheets…');
            }

            const [custs, rawDevs] = await Promise.all([
              api('/api/customers'),
              api('/api/devices?page=1&page_size=100000')
            ]);

            const customers = Array.isArray(custs) ? custs : (CU || []);
            const devices = (rawDevs && Array.isArray(rawDevs.items)) ? rawDevs.items : [];

            if (!customers.length) {
              toast('No customers found.');
              return;
            }

            const devsByCust = new Map();
            devices.forEach(d => {
              const cid = d.customer_id;
              if (!devsByCust.has(cid)) devsByCust.set(cid, []);
              devsByCust.get(cid).push(d);
            });

            const wb = XLSX.utils.book_new();
            let sheetsCount = 0;

            customers.forEach(c => {
              const custDevs = devsByCust.get(c.id) || [];
              let sheetName = (c.name || `Customer_${c.id}`).replace(/[\\/?*\[\]:]/g, '_').trim();
              if (!sheetName) sheetName = `Customer_${c.id}`;
              if (sheetName.length > 31) sheetName = sheetName.substring(0, 31);

              let uniqueName = sheetName;
              let counter = 1;
              while (wb.SheetNames.includes(uniqueName)) {
                uniqueName = sheetName.substring(0, 28) + '_' + counter++;
              }

              const headers = chosenCols.map(col => col.label);
              const rows = custDevs.map(d => chosenCols.map(col => {
                if (col.key === 'id') return d.id;
                if (col.key === 'customer_name') return c.name;
                if (col.key in d) return d[col.key] != null ? d[col.key] : '';
                if (d.extra && col.key in d.extra) return d.extra[col.key] != null ? d.extra[col.key] : '';
                return '';
              }));

              const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
              XLSX.utils.book_append_sheet(wb, ws, uniqueName);
              sheetsCount++;
            });

            const dateStr = new Date().toISOString().slice(0, 10);
            XLSX.writeFile(wb, `BSTPL_CustomerVault_All_Portfolios_${dateStr}.xlsx`);
            toast(`Multi-customer workbook downloaded with ${sheetsCount} customer sheets!`);
          } catch(err) {
            fail(err);
          } finally {
            if (typeof hideBstplLoader === 'function') hideBstplLoader();
          }
        }

        if ($('btnDownloadAllCustData')) {
          $('btnDownloadAllCustData').onclick = openDownloadAllColumnChooser;
        }

        // Delegate Customer Card Actions
        if ($('cgrid')) {
          $('cgrid').onclick = async e => {
            const btn = e.target.closest('button');
            if (!btn) return;
            const cid = btn.dataset.cview || btn.dataset.cdl || btn.dataset.c || btn.dataset.cfiles;
            if (!cid) return;

            const customer = (CU || []).find(x => String(x.id) === String(cid)) || { id: cid, name: `Customer #${cid}` };

            if (btn.dataset.cview || btn.dataset.cfiles) {
              // Files option works as View Option (displays all entries)
              await openCustomerEntriesView(customer);
              return;
            }

            if (btn.dataset.cdl) {
              // Download option in Excel with all column names and values
              await downloadSingleCustomerExcel(customer);
              return;
            }

            if (btn.dataset.c) {
              if ($('invCustSel')) $('invCustSel').value = cid;
              invCid = cid;
              invPage = 1;
              switchInvSubView('devices');
              return;
            }
          };
        }
'''

# Replace previous cust_files_handlers and card template in enhanced_inv_js
old_cust_files_handlers_anchor = "cust_files_handlers = r'''"
idx_cfh = text.find(old_cust_files_handlers_anchor)
if idx_cfh != -1:
    end_cfh = text.find("'''", idx_cfh + len(old_cust_files_handlers_anchor))
    text = text[:idx_cfh] + "cust_files_handlers = r'''" + enhanced_inv_code + text[end_cfh:]
    print("✓ Replaced cust_files_handlers with multi-sheet chooser, single download, and view entries modal")

# Save updated builder
with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Builder updated successfully with Customer Inventory & Multi-sheet Excel export!")

