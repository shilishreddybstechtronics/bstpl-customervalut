import re

def patch_errors():
    with open('frontend/errors.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update filter controls bar in HTML to have Category Switcher (All / Error / Invalid), Sort, and Page Size
    old_filter_section_pattern = r'<div class="card" style="padding:14px 18px;margin:14px 0 10px;background:var(--card-subtle);border-radius:12px">[\s\S]*?<div id="errCategoryPills" style="display:inline-flex;gap:6px;flex-wrap:wrap"></div>\s*</div>\s*</div>'

    new_filter_section = """<div class="card" style="padding:18px 20px;margin:14px 0 16px;background:var(--card);border:1.5px solid var(--line);border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,0.02)">
        <!-- Tab Switcher: All, Error Entries, Invalid Entries -->
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;border-bottom:1px solid var(--line);padding-bottom:14px">
          <div class="subtabs" style="display:inline-flex;background:var(--card-subtle);padding:4px;border-radius:10px;border:1px solid var(--line);gap:4px">
            <button class="subtab on" id="tabErrAll" type="button" onclick="setErrCategoryFilter('all')" style="padding:7px 16px;font-size:13px;font-weight:700;border-radius:8px;border:none;cursor:pointer">
              🌐 All Staged (<span id="errCountAll">0</span>)
            </button>
            <button class="subtab" id="tabErrErrors" type="button" onclick="setErrCategoryFilter('error')" style="padding:7px 16px;font-size:13px;font-weight:700;border-radius:8px;border:none;cursor:pointer;color:var(--warn)">
              ⚠️ Error Entries (<span id="errCountErrors">0</span>)
            </button>
            <button class="subtab" id="tabErrInvalid" type="button" onclick="setErrCategoryFilter('invalid')" style="padding:7px 16px;font-size:13px;font-weight:700;border-radius:8px;border:none;cursor:pointer;color:var(--danger)">
              🚫 Invalid Entries (<span id="errCountInvalid">0</span>)
            </button>
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            <button class="b" id="errFilterClear" type="button" style="height:36px;padding:0 12px;font-size:12px;font-weight:700">Clear All Filters</button>
            <button class="b d" id="btnDeleteFilteredErrors" type="button" style="height:36px;padding:0 14px;background:#dc2626;color:#fff;font-weight:700;border-color:#b91c1c" title="Directly delete all filtered entries from database">🗑️ Delete Filtered (<span id="errFilteredCount">0</span>)</button>
          </div>
        </div>

        <!-- Search, Reason Filter, Sort & Pagination Controls -->
        <div class="row" style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:12px;align-items:end">
          <div style="grid-column:span 2;min-width:260px">
            <label for="errSearchFilter" style="font-size:12px;font-weight:700;margin-bottom:6px;display:block">Search Records</label>
            <input id="errSearchFilter" placeholder="🔍 Search IMEI, ICCID, Customer, or Error description…" style="width:100%;height:38px;font-size:13px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle)" autocomplete="off" />
          </div>
          <div>
            <label for="errReasonFilter" style="font-size:12px;font-weight:700;margin-bottom:6px;display:block">Error Reason</label>
            <select id="errReasonFilter" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
              <option value="">All Error Reasons</option>
            </select>
          </div>
          <div>
            <label for="errSortCol" style="font-size:12px;font-weight:700;margin-bottom:6px;display:block">Sort By</label>
            <select id="errSortCol" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
              <option value="id" selected>Staged ID</option>
              <option value="customer_name">Customer Name</option>
              <option value="imei">IMEI</option>
              <option value="error_reason">Error Reason</option>
            </select>
          </div>
          <div>
            <label for="errSortDir" style="font-size:12px;font-weight:700;margin-bottom:6px;display:block">Order</label>
            <select id="errSortDir" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
              <option value="desc" selected>Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
          <div>
            <label for="errPageSize" style="font-size:12px;font-weight:700;margin-bottom:6px;display:block">Per Page</label>
            <select id="errPageSize" style="width:100%;height:38px;padding:0 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--card-subtle);font-size:13px">
              <option value="15">15</option>
              <option value="25" selected>25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>
        </div>

        <!-- Dynamic Error Reason Pill Badges -->
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:14px;padding-top:12px;border-top:1px dashed var(--line)">
          <span style="font-size:11.5px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:0.5px">Quick Filters:</span>
          <div id="errCategoryPills" style="display:inline-flex;gap:6px;flex-wrap:wrap"></div>
        </div>
      </div>"""

    if re.search(old_filter_section_pattern, html):
        html = re.sub(old_filter_section_pattern, new_filter_section, html, count=1)
    else:
        print("WARNING: old_filter_section_pattern did not match directly.")

    # 2. Add complete redesign logic for renderFilteredErrors with Error vs Invalid classification, Sorting, and Pagination
    new_render_filtered_errors = """
      let _errCategoryFilter = 'all'; // 'all', 'error', 'invalid'
      let _errPage = 1;
      let _errPageSize = 25;

      window.setErrCategoryFilter = function(cat) {
        _errCategoryFilter = cat;
        _errPage = 1;
        ['tabErrAll', 'tabErrErrors', 'tabErrInvalid'].forEach(id => {
          const btn = $(id);
          if (!btn) return;
          btn.classList.remove('on');
          btn.style.background = 'transparent';
        });
        const activeId = cat === 'error' ? 'tabErrErrors' : (cat === 'invalid' ? 'tabErrInvalid' : 'tabErrAll');
        if ($(activeId)) {
          $(activeId).classList.add('on');
          $(activeId).style.background = 'var(--card)';
        }
        renderFilteredErrors();
      };

      function isInvalidEntry(err) {
        const r = (err.error_reason || '').toLowerCase();
        const imei = String(err.imei || '').trim();
        if (r.includes('invalid') || r.includes('format') || r.includes('checksum') || r.includes('luhn') || r.includes('missing imei') || r.includes('corrupt')) return true;
        if (!imei || imei.length !== 15 || !/^\\d{15}$/.test(imei)) return true;
        return false;
      }

      function renderFilteredErrors() {
        const selectedReason = ($('errReasonFilter') ? $('errReasonFilter').value : '').trim().toLowerCase();
        const q = ($('errSearchFilter') ? $('errSearchFilter').value : '').trim().toLowerCase();
        const sortCol = ($('errSortCol') ? $('errSortCol').value : 'id');
        const sortDir = ($('errSortDir') ? $('errSortDir').value : 'desc');
        _errPageSize = $('errPageSize') ? parseInt($('errPageSize').value, 10) : 25;

        // Calculate counts
        let errCount = 0, invCount = 0;
        cachedErrors.forEach(e => {
          if (isInvalidEntry(e)) invCount++;
          else errCount++;
        });
        if ($('errCountAll')) $('errCountAll').textContent = cachedErrors.length.toString();
        if ($('errCountErrors')) $('errCountErrors').textContent = errCount.toString();
        if ($('errCountInvalid')) $('errCountInvalid').textContent = invCount.toString();

        let filtered = cachedErrors;

        // Filter by Category
        if (_errCategoryFilter === 'error') {
          filtered = filtered.filter(e => !isInvalidEntry(e));
        } else if (_errCategoryFilter === 'invalid') {
          filtered = filtered.filter(e => isInvalidEntry(e));
        }

        // Filter by Reason
        if (selectedReason) {
          filtered = filtered.filter(e => (e.error_reason || '').trim().toLowerCase() === selectedReason);
        }

        // Filter by Search Query
        if (q) {
          filtered = filtered.filter(e => {
            return (e.customer_name || '').toLowerCase().includes(q) ||
                   (e.imei || '').toLowerCase().includes(q) ||
                   (e.device_sr_no || '').toLowerCase().includes(q) ||
                   (e.iccid || '').toLowerCase().includes(q) ||
                   (e.msisdn1 || '').toLowerCase().includes(q) ||
                   (e.msisdn2 || '').toLowerCase().includes(q) ||
                   (e.error_reason || '').toLowerCase().includes(q) ||
                   String(e.id).includes(q);
          });
        }

        // Sorting
        filtered.sort((a, b) => {
          let va = a[sortCol] ?? '';
          let vb = b[sortCol] ?? '';
          if (typeof va === 'string') va = va.toLowerCase();
          if (typeof vb === 'string') vb = vb.toLowerCase();
          if (va < vb) return sortDir === 'asc' ? -1 : 1;
          if (va > vb) return sortDir === 'asc' ? 1 : -1;
          return 0;
        });

        if ($('errFilteredCount')) $('errFilteredCount').textContent = filtered.length.toString();
        window._currentFilteredErrors = filtered;

        const canDelInvalid = canDeleteInvalidEntries();
        if ($('btnDeleteFilteredErrors')) {
          $('btnDeleteFilteredErrors').hidden = !canDelInvalid;
          $('btnDeleteFilteredErrors').disabled = filtered.length === 0;
        }

        if (!cachedErrors.length) {
          $('errorsTableWrap').innerHTML = `
            <div class="empty" style="padding:48px 20px">
              <div style="font-size:36px;margin-bottom:10px">✅</div>
              <h3 style="margin:0 0 6px">No Errored or Invalid Entries Found</h3>
              <p class="sub" style="margin:0">All uploaded device records have passed validation and are cleanly synced into the database and cloud.</p>
            </div>
          `;
          return;
        }

        if (!filtered.length) {
          $('errorsTableWrap').innerHTML = `
            <div class="empty" style="padding:40px 20px">
              <div style="font-size:32px;margin-bottom:8px">🔍</div>
              <h4 style="margin:0 0 6px">No Records Match Filter Criteria</h4>
              <p class="sub" style="margin:0 0 14px">Try selecting a different category, error reason, or search term.</p>
              <button class="b" type="button" onclick="document.getElementById('errFilterClear')?.click()">Reset Filters</button>
            </div>
          `;
          return;
        }

        // Pagination calculations
        const totalItems = filtered.length;
        const totalPages = Math.ceil(totalItems / _errPageSize) || 1;
        if (_errPage > totalPages) _errPage = totalPages;
        if (_errPage < 1) _errPage = 1;

        const startIdx = (_errPage - 1) * _errPageSize;
        const pageItems = filtered.slice(startIdx, startIdx + _errPageSize);

        const rowsHtml = pageItems.map(err => {
          const isInv = isInvalidEntry(err);
          const typeBadge = isInv
            ? '<span class="tag bad" style="font-size:11px;font-weight:700;white-space:nowrap">🚫 Invalid Entry</span>'
            : '<span class="tag warn" style="font-size:11px;font-weight:700;white-space:nowrap">⚠️ Error Entry</span>';

          const delBtns = canDelInvalid
            ? `<button class="b d" data-errdel="${err.id}" style="height:28px;padding:0 8px;font-size:12px" title="Move this entry to Cart with percentage progress">🗑️ Cart</button>` +
              `<button class="b d" data-errpurge="${err.id}" style="height:28px;padding:0 8px;font-size:12px;background:#dc2626;color:#fff;font-weight:700" title="Directly and completely delete from database">❌ Delete</button>`
            : '';

          return `
            <tr>
              <td style="text-align:center"><input type="checkbox" class="err-row-chk" data-chkerr="${err.id}" style="cursor:pointer;width:15px;height:15px;vertical-align:middle" /></td>
              <td><b>#${err.id}</b></td>
              <td>${typeBadge}</td>
              <td><b>${esc(err.customer_name || '—')}</b></td>
              <td><code style="font-weight:700;background:var(--card-subtle);padding:2px 6px;border-radius:4px;border:1px solid var(--line)">${esc(err.imei || '—')}</code></td>
              <td>${esc(err.iccid || '—')}</td>
              <td>
                <div style="max-width:280px">
                  <span class="tag ${isInv ? 'bad' : 'warn'}" style="font-size:11.5px;font-weight:700;display:inline-block;white-space:normal;line-height:1.3">${esc(err.error_reason || 'Unknown error')}</span>
                </div>
              </td>
              <td style="white-space:nowrap;font-size:12px">${err.created_at ? new Date(err.created_at).toLocaleDateString() : '—'}</td>
              <td>
                <div style="display:flex;gap:6px;flex-wrap:wrap">
                  <button class="b p" data-errpush="${err.id}" style="height:28px;padding:0 8px;font-size:12px;background:#2563eb;color:#fff;font-weight:700" title="Push this entry into the specified customer even with error">🚀 Push</button>
                  <button class="b" data-erredit="${err.id}" style="height:28px;padding:0 8px;font-size:12px;font-weight:700" title="View, edit fields and upload permanently to customer">✏️ Edit & Upload</button>
                  ${delBtns}
                </div>
              </td>
            </tr>
          `;
        }).join('');

        const startDisp = startIdx + 1;
        const endDisp = Math.min(startIdx + _errPageSize, totalItems);

        const html = `
          <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
            <b id="errorsFoundText">Showing ${startDisp}–${endDisp} of ${totalItems} ${esc(_errCategoryFilter.toUpperCase())} records (${cachedErrors.length} total staged)</b>
            <div class="pg" style="display:flex;align-items:center;gap:8px">
              <button class="b" id="errPrevBtn" ${_errPage <= 1 ? 'disabled' : ''} style="padding:4px 12px;font-size:12px">Prev</button>
              <span style="font-size:12px;font-weight:700">Page ${_errPage} of ${totalPages}</span>
              <button class="b" id="errNextBtn" ${_errPage >= totalPages ? 'disabled' : ''} style="padding:4px 12px;font-size:12px">Next</button>
            </div>
          </div>
          <div class="tw">
            <table>
              <thead>
                <tr>
                  <th style="width:38px;text-align:center"><input type="checkbox" id="chkSelectAllErrors" title="Select all on this page" style="cursor:pointer;width:15px;height:15px;vertical-align:middle" /></th>
                  <th>ID</th>
                  <th>Classification</th>
                  <th>Customer</th>
                  <th>IMEI</th>
                  <th>ICCID</th>
                  <th>Flagged Error Reason / Diagnosis</th>
                  <th>Staged Date</th>
                  <th style="min-width:180px">Actions</th>
                </tr>
              </thead>
              <tbody>
                ${rowsHtml}
              </tbody>
            </table>
          </div>
        `;
        $('errorsTableWrap').innerHTML = html;

        if ($('errPrevBtn')) $('errPrevBtn').onclick = () => { if (_errPage > 1) { _errPage--; renderFilteredErrors(); } };
        if ($('errNextBtn')) $('errNextBtn').onclick = () => { if (_errPage < totalPages) { _errPage++; renderFilteredErrors(); } };

        const updateErrSelection = () => {
          const chks = Array.from(document.querySelectorAll('.err-row-chk:checked'));
          const count = chks.length;
          if ($('errSelectedCount')) $('errSelectedCount').textContent = count.toString();
          if ($('btnDirectDeleteSelectedErrors')) $('btnDirectDeleteSelectedErrors').hidden = !canDelInvalid || (count === 0);
          if ($('chkSelectAllErrors')) {
            const allChks = document.querySelectorAll('.err-row-chk');
            $('chkSelectAllErrors').checked = allChks.length > 0 && chks.length === allChks.length;
          }
        };

        if ($('chkSelectAllErrors')) {
          $('chkSelectAllErrors').onchange = (e) => {
            const val = e.target.checked;
            document.querySelectorAll('.err-row-chk').forEach(c => c.checked = val);
            updateErrSelection();
          };
        }

        document.querySelectorAll('.err-row-chk').forEach(c => {
          c.onchange = updateErrSelection;
        });
        updateErrSelection();
      }
"""
    # Replace renderFilteredErrors function
    old_render_fn_pattern = r'function renderFilteredErrors\(\)\s*\{[\s\S]*?document\.querySelectorAll\(\'\.err-row-chk\'\)\.forEach\(c => \{\s*c\.onchange = updateErrSelection;\s*\}\);\s*updateErrSelection\(\);\s*\}'
    if re.search(old_render_fn_pattern, html):
        html = re.sub(old_render_fn_pattern, new_render_filtered_errors, html, count=1)
    else:
        print("WARNING: old_render_fn_pattern did not match directly.")

    # 3. Hook sort & page size controls in loadErrorsContainer
    sort_hooks = """
        if ($('errSortCol')) $('errSortCol').onchange = () => { _errPage = 1; renderFilteredErrors(); };
        if ($('errSortDir')) $('errSortDir').onchange = () => { _errPage = 1; renderFilteredErrors(); };
        if ($('errPageSize')) $('errPageSize').onchange = () => { _errPage = 1; renderFilteredErrors(); };
"""
    if 'errSortCol' not in html or 'errSortCol' in new_filter_section:
        if 'errFilterClear' in html:
            html = html.replace("$('errFilterClear').onclick = () => {", sort_hooks + "\n        $('errFilterClear').onclick = () => {")

    with open('frontend/errors.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("SUCCESS: Patched frontend/errors.html!")

if __name__ == '__main__':
    patch_errors()

