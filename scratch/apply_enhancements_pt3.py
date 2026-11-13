import os

html_path = r'c:\Users\soumy\OneDrive\Documents\bstpl-view\frontend\inventory.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace lines around 4030 to 4095 to:
# 1. Elevate drawCustCards to window.drawCustCards
# 2. Use .customer-file-grid and modern card layout
# 3. Call loadCustomerFilesContainer after drawCustCards is set up

old_chunk = """        if ($('btnBulkDeleteExcel')) {
          $('btnBulkDeleteExcel').onclick = openBulkDeleteExcelModal;
          $('btnBulkDeleteExcel').hidden = !canDeleteValidInventory();
        }

        await loadCustomerFilesContainer();

        // --- 1. Dynamic Subnav & Badge Count ---
        if ($('invCustCountBadge')) $('invCustCountBadge').textContent = (CU || []).length || 0;

        // --- 2. Customer Cards Grid & Search (Requirement: Grid Format & Search) ---
        const card = c => `
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
        }"""

new_chunk = """        if ($('btnBulkDeleteExcel')) {
          $('btnBulkDeleteExcel').onclick = openBulkDeleteExcelModal;
          $('btnBulkDeleteExcel').hidden = !canDeleteValidInventory();
        }

        // --- 1. Dynamic Subnav & Badge Count ---
        if ($('invCustCountBadge')) $('invCustCountBadge').textContent = (CU || []).length || 0;

        // --- 2. Customer Cards Grid & Search (Clean Responsive Grid Layout) ---
        const card = c => {
          const devs = Number(c.devices || 0);
          const exp = Number(c.expiring_or_expired || 0);
          const isStaff = myRole() !== 'limited';
          const canDel = canDeleteValidInventory();

          return `
          <div class="cw customer-file-card" data-cid="${c.id}">
            <div>
              <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:12px;min-width:0">
                  ${avatarHtml(c)}
                  <div style="min-width:0">
                    <b style="font-size:15.5px;font-weight:800;color:var(--text);display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${esc(c.name)}">${esc(c.name)}</b>
                    <span style="font-size:12px;color:var(--muted);font-weight:600">Customer ID: #${c.id}</span>
                  </div>
                </div>
                <span class="tag ${devs > 0 ? 'ok' : 'mut'}" style="font-size:11px;font-weight:700;flex-shrink:0">${devs > 0 ? 'Active' : 'Empty'}</span>
              </div>
              <div style="font-size:13px;color:var(--muted);margin-top:8px;line-height:1.4;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                <span style="display:inline-flex;align-items:center;gap:4px;background:var(--card-subtle);padding:3px 8px;border-radius:6px;border:1px solid var(--line);font-size:12px">
                  <span>📱</span> <b style="color:var(--text);font-weight:800">${devs.toLocaleString()}</b> records
                </span>
                ${exp > 0 ? `
                <span style="display:inline-flex;align-items:center;gap:4px;background:rgba(245,158,11,0.1);color:var(--warn);border:1px solid rgba(245,158,11,0.25);padding:3px 8px;border-radius:6px;font-size:12px;font-weight:700">
                  <span>⚠️</span> ${exp.toLocaleString()} expiring
                </span>` : ''}
              </div>
            </div>
            <div class="ca" style="display:flex;gap:6px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:14px">
              <button class="b p" data-cview="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="View all device records for this customer">👁️ Files</button>
              <button class="b" data-cdl="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="Download Excel with all columns and values">📥 Download</button>
              <button class="b" data-cren="${c.id}" style="font-size:12px;padding:6px 10px;font-weight:700" title="Rename customer portfolio">✏️ Rename</button>
              ${isStaff ? `<button class="b" data-cmerge="${c.id}" style="font-size:12px;padding:6px 10px;font-weight:700" title="Merge into another customer">🔀 Merge</button>
              <button class="b" data-cav="${c.id}" style="font-size:12px;padding:6px 8px" title="Change icon">🎨</button>` : ''}
              ${canDel ? `<button class="b d" data-cdel="${c.id}" style="font-size:12px;padding:6px 10px;font-weight:700" title="Delete customer portfolio">🗑️ Delete</button>` : ''}
            </div>
          </div>`;
        };

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
            <div class="customer-file-grid">
              ${gridHtml || `<div class="empty">${CU.length ? 'No customer matches your search.' : 'No customers found.'}</div>`}
            </div>`;
        };

        window.drawCustCards = drawCustCards;

        if ($('cs')) $('cs').oninput = drawCustCards;
        if ($('csClearBtn')) {
          $('csClearBtn').onclick = () => {
            if ($('cs')) $('cs').value = '';
            $('csClearBtn').style.display = 'none';
            drawCustCards();
          };
        }

        await loadCustomerFilesContainer();"""

assert old_chunk in content, "Could not find exact old_chunk"
content = content.replace(old_chunk, new_chunk, 1)
print("Updated drawCustCards, window.drawCustCards, and customer card grid rendering.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Part 3 successfully applied!")

