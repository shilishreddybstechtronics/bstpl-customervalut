import re, sys, os

print("=== Applying Comprehensive Customer Inventory, Check Entries & Fetch Data Enhancements ===")

with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    code = f.read()

# -----------------------------------------------------------------------------
# 1. Add #dlgCheckEntriesModal to dialogs_dict
# -----------------------------------------------------------------------------
dlg_check_entries_html = r'''
  <!-- Check Entries & Rectify Inspection Modal (Requirement 2) -->
  <dialog id="dlgCheckEntriesModal" class="dlg" style="max-width:1100px;width:95vw;max-height:90vh;border-radius:18px;box-shadow:0 24px 60px rgba(0,0,0,0.35);padding:0;overflow:hidden;border:1px solid var(--line)">
    <div style="padding:18px 24px;background:var(--card-subtle);border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between">
      <div style="display:flex;align-items:center;gap:12px">
        <div style="width:38px;height:38px;border-radius:10px;background:rgba(2,132,199,0.15);color:#0284c7;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800">
          🔍
        </div>
        <div>
          <h3 style="margin:0;font-size:17px;font-weight:800;color:var(--text)">Check Entries &amp; Rectify Inspection</h3>
          <p style="margin:2px 0 0;font-size:12px;color:var(--muted)">Side-by-side inspection of existing database records vs incoming Excel upload</p>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <button class="b p" id="btnDoRectifyAll" type="button" style="padding:8px 16px;font-size:13px;font-weight:800;background:linear-gradient(135deg, #d97706, #b45309);color:#fff;border-radius:8px;cursor:pointer">
          🔄 Rectify All Eligible Records (<span id="checkEntriesEligibleCount">0</span>)
        </button>
        <button class="b ghost" type="button" onclick="closeCheckEntriesModal()" style="font-size:20px;padding:4px 10px;cursor:pointer;border-radius:8px">✕</button>
      </div>
    </div>
    <div style="padding:16px 24px;border-bottom:1px solid var(--line);background:var(--card);display:flex;gap:16px;align-items:center;flex-wrap:wrap">
      <div style="font-size:13px;font-weight:700;color:var(--text)">
        Summary: <span id="checkEntriesStatsBadge" style="color:var(--primary);font-weight:800">0 records requiring update</span>
      </div>
      <div style="margin-left:auto;display:flex;gap:10px;align-items:center">
        <input type="text" id="checkEntriesFilter" placeholder="Filter by ICCID, IMEI, Customer…" style="padding:6px 12px;font-size:12.5px;border-radius:8px;border:1px solid var(--line);width:260px" />
        <button class="b" id="btnExportCheckEntriesCsv" type="button" style="font-size:12px;padding:6px 12px;cursor:pointer">
          📥 Export Comparison (Excel)
        </button>
      </div>
    </div>
    <div style="padding:16px 24px;overflow-y:auto;max-height:calc(90vh - 170px)">
      <div id="checkEntriesTableContainer" style="overflow-x:auto">
        <div style="padding:24px;text-align:center;color:var(--muted)">Loading entries requiring verification…</div>
      </div>
    </div>
  </dialog>
'''

if 'dialogs_dict["dlgCheckEntriesModal"]' not in code:
    code = code.replace(
        "dialogs_dict = loc['dialogs_dict']",
        "dialogs_dict = loc['dialogs_dict']\ndialogs_dict['dlgCheckEntriesModal'] = " + repr(dlg_check_entries_html)
    )
    print("✓ Added dlgCheckEntriesModal to dialogs_dict")

# Ensure dlgCheckEntriesModal is included in page_configs for inventory.html and sim-upload.html
code = code.replace(
    "'dlgUploadErrorsAlert']",
    "'dlgUploadErrorsAlert', 'dlgCheckEntriesModal']"
)
print("✓ Added dlgCheckEntriesModal to inventory and sim page configs")

# -----------------------------------------------------------------------------
# 2. Check Entries & Rectify Functions JavaScript Block
# -----------------------------------------------------------------------------
check_entries_js = r'''
    // --- Check Entries & Rectify Update Logic (Requirement 2) ---
    function openCheckEntriesModal() {
      const dlg = $('dlgCheckEntriesModal');
      if (!dlg) return;
      const records = (activeValResult && activeValResult.entries_requiring_update && activeValResult.entries_requiring_update.length)
        ? activeValResult.entries_requiring_update
        : (activeValResult && activeValResult.updated_sample && activeValResult.updated_sample.length)
        ? activeValResult.updated_sample
        : [];

      if (!records.length) {
        toast('ℹ️ No records currently require update. All scanned entries are either brand-new or match the database.');
        return;
      }

      if ($('checkEntriesEligibleCount')) $('checkEntriesEligibleCount').textContent = records.length.toLocaleString();
      if ($('checkEntriesStatsBadge')) $('checkEntriesStatsBadge').textContent = `${records.length.toLocaleString()} records requiring updates`;

      renderCheckEntriesTable(records);
      dlg.showModal();
    }
    window.openCheckEntriesModal = openCheckEntriesModal;

    function closeCheckEntriesModal() {
      const dlg = $('dlgCheckEntriesModal');
      if (dlg) dlg.close();
    }
    window.closeCheckEntriesModal = closeCheckEntriesModal;

    function renderCheckEntriesTable(records) {
      const container = $('checkEntriesTableContainer');
      if (!container) return;

      const filterTerm = ($('checkEntriesFilter')?.value || '').toLowerCase().trim();
      const filtered = filterTerm
        ? records.filter(r => JSON.stringify(r).toLowerCase().includes(filterTerm))
        : records;

      if (!filtered.length) {
        container.innerHTML = '<div style="padding:24px;text-align:center;color:var(--muted)">No records match current filter.</div>';
        return;
      }

      let html = `
        <table class="data-table" style="font-size:12.5px;margin:0;width:100%">
          <thead>
            <tr style="background:var(--card-subtle)">
              <th style="width:40px">#</th>
              <th>Identifier (ICCID / IMEI / Sr)</th>
              <th>Customer</th>
              <th>Detected Field Changes (Existing DB ➔ New Excel)</th>
              <th style="width:120px;text-align:center">Action</th>
            </tr>
          </thead>
          <tbody>
      `;

      filtered.slice(0, 100).forEach((r, idx) => {
        const iden = r.iccid || r.imei || r.device_sr_no || r.id || '—';
        const cust = r.customer_name || '—';
        const changes = r.changed_fields || {};
        let changeSummary = [];

        for (const [field, diff] of Object.entries(changes)) {
          const oldVal = (diff && diff.old != null && diff.old !== '') ? esc(String(diff.old)) : '<i style="color:var(--muted)">empty</i>';
          const newVal = (diff && diff.new != null && diff.new !== '') ? esc(String(diff.new)) : '<i style="color:var(--muted)">empty</i>';
          changeSummary.push(`
            <div style="margin-bottom:4px">
              <b style="color:var(--primary);text-transform:uppercase;font-size:11px">${esc(field.replace(/_/g, ' '))}:</b>
              <span style="color:var(--danger);text-decoration:line-through;margin-right:6px">${oldVal}</span>
              ➔ <span style="color:var(--ok);font-weight:700;margin-left:6px">${newVal}</span>
            </div>
          `);
        }

        if (!changeSummary.length) {
          changeSummary.push('<span style="color:var(--warn)">Pending field verification</span>');
        }

        html += `
          <tr>
            <td>${idx + 1}</td>
            <td><code style="font-weight:700">${esc(iden)}</code></td>
            <td><b>${esc(cust)}</b></td>
            <td>${changeSummary.join('')}</td>
            <td style="text-align:center">
              <button class="b p" data-rectify-idx="${idx}" type="button" style="padding:4px 10px;font-size:11.5px;background:linear-gradient(135deg, #d97706, #b45309);color:#fff;border-radius:6px;cursor:pointer">
                Rectify Row
              </button>
            </td>
          </tr>
        `;
      });

      if (filtered.length > 100) {
        html += `<tr><td colspan="5" style="text-align:center;padding:12px;color:var(--muted)">Showing first 100 of ${filtered.length.toLocaleString()} records requiring update. Use "Rectify All" to update all.</td></tr>`;
      }

      html += `</tbody></table>`;
      container.innerHTML = html;

      container.querySelectorAll('button[data-rectify-idx]').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.rectifyIdx, 10);
          const rec = filtered[idx];
          if (rec) executeRectifyUpdate([rec]);
        };
      });
    }

    async function executeRectifyUpdate(specificRecords = null) {
      const records = specificRecords || (activeValResult && activeValResult.entries_requiring_update) || (activeValResult && activeValResult.updated_sample) || [];
      if (!records.length) {
        toast('⚠️ No eligible records selected for update.');
        return;
      }

      showBstplLoader(`Updating ${records.length.toLocaleString()} database records with validated Excel data…`, 10);

      try {
        const rows = records.map(r => ({
          device_id: r.existing_id || r.id,
          iccid: r.iccid,
          imei: r.imei,
          device_sr_no: r.device_sr_no,
          customer_name: r.customer_name,
          msisdn1: r.msisdn1,
          msisdn2: r.msisdn2,
          act_date: r.act_date,
          expiry_date: r.expiry_date,
          dispatched_date: r.dispatched_date,
          model: r.model,
          sim_provider: r.sim_provider,
          sim_type: r.sim_type,
          activation_plan: r.activation_plan,
          firmware: r.firmware,
          flash: r.flash,
          extra: r.extra,
          changed_fields: r.changed_fields
        }));

        let totalSuccess = 0;
        let totalFailed = 0;
        const batchSize = 2500;

        for (let i = 0; i < rows.length; i += batchSize) {
          const chunk = rows.slice(i, i + batchSize);
          const pct = Math.round((i / rows.length) * 100);
          updateBstplLoader(`Updating database records (${i.toLocaleString()} / ${rows.length.toLocaleString()})…`, pct);

          const res = await api('/api/devices/bulk/rectify', {
            method: 'POST',
            body: JSON.stringify({ rows: chunk, skip_empty: true })
          });

          totalSuccess += (res.success_count || 0);
          totalFailed += (res.failed_count || 0);
        }

        hideBstplLoader();
        closeCheckEntriesModal();
        toast(`✅ Successfully updated ${totalSuccess.toLocaleString()} database records.${totalFailed ? ` (${totalFailed} failed)` : ''}`);

        if (typeof loadDevices === 'function') loadDevices(1);
        if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
      } catch (err) {
        hideBstplLoader();
        toast(`❌ Error updating records: ${err.message}`);
      }
    }
    window.executeRectifyUpdate = executeRectifyUpdate;

    function exportCheckEntriesExcel() {
      const records = (activeValResult && activeValResult.entries_requiring_update) || (activeValResult && activeValResult.updated_sample) || [];
      if (!records.length) {
        toast('No records to export.');
        return;
      }
      const headers = ['#', 'Identifier', 'Customer Name', 'Changed Field', 'Old Database Value', 'New Excel Value', 'Status'];
      const rows = [];
      records.forEach((r, idx) => {
        const iden = r.iccid || r.imei || r.device_sr_no || r.id || '';
        const cust = r.customer_name || '';
        const changes = r.changed_fields || {};
        for (const [field, diff] of Object.entries(changes)) {
          rows.push([
            idx + 1,
            iden,
            cust,
            field,
            diff?.old ?? '',
            diff?.new ?? '',
            'Requires Update'
          ]);
        }
      });
      exportExcel('check_entries_comparison_' + new Date().toISOString().slice(0, 10), headers, rows);
    }
'''

# Wire check entries buttons into INV block
wiring_js = r'''
        // Wire Check Entries & Rectify Buttons (Requirement 2)
        if ($('btnCheckEntriesModal')) $('btnCheckEntriesModal').onclick = openCheckEntriesModal;
        if ($('btnRectifyUpdate')) $('btnRectifyUpdate').onclick = () => executeRectifyUpdate();
        if ($('btnDoRectifyAll')) $('btnDoRectifyAll').onclick = () => executeRectifyUpdate();
        if ($('btnExportCheckEntriesCsv')) $('btnExportCheckEntriesCsv').onclick = exportCheckEntriesExcel;
        if ($('checkEntriesFilter')) {
          $('checkEntriesFilter').oninput = () => {
            const records = (activeValResult && activeValResult.entries_requiring_update) || (activeValResult && activeValResult.updated_sample) || [];
            renderCheckEntriesTable(records);
          };
        }
'''

# Inject check_entries_js and wiring into enhanced_inv_js
if 'function openCheckEntriesModal()' not in code:
    code = code.replace(
        "feature_blocks['INV'] = enhanced_inv_js + \"\\n\\n\" + sim_block_copy",
        "enhanced_inv_js = enhanced_inv_js + \"\\n\\n\" + " + repr(check_entries_js + "\n" + wiring_js) + "\nfeature_blocks['INV'] = enhanced_inv_js + \"\\n\\n\" + sim_block_copy"
    )
    print("✓ Injected Check Entries & Rectify JS into feature_blocks['INV']")

# -----------------------------------------------------------------------------
# 3. Enhance Fetch Data Error Entries Excel Export (Requirement 5)
# -----------------------------------------------------------------------------
fetch_error_export_js = r'''
        // Fetch Data Error Entries Excel Export (Requirement 5)
        const dlErrBtn = $('btnFetchDlErrorsExcel') || $('btnBfDlNotFound');
        if (dlErrBtn) {
          dlErrBtn.onclick = () => {
            if (!notFoundList || notFoundList.length === 0) {
              toast('ℹ️ No error entries recorded from latest fetch.');
              return;
            }
            const headers = [
              'ICCID / CCID',
              'Customer / Device Details',
              'Error Reason',
              'Fetch Status',
              'API Response / Failure Description',
              'Date & Time of Processing'
            ];
            const nowStr = new Date().toLocaleString();
            const rows = notFoundList.map(term => [
              term,
              'Not found in active customer database',
              'Search query term did not match any active IMEI, ICCID, or serial number',
              'FAILED - NOT FOUND',
              '404 No matching database records found',
              nowStr
            ]);
            exportExcel('fetch_data_error_entries_' + new Date().toISOString().slice(0, 10), headers, rows);
          };
        }
'''

if 'fetch_data_error_entries_' not in code:
    code = code.replace(
        "exportExcel(`${prefix}_not_found_list`, ['NOT FOUND Term'], notFoundList.map(t => [t]));\n          };",
        "exportExcel(`${prefix}_not_found_list`, ['NOT FOUND Term'], notFoundList.map(t => [t]));\n          };\n" + fetch_error_export_js
    )
    print("✓ Injected Fetch Data Error Entries Excel download logic")

with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
    f.write(code)

print("=== build_clean_modular_app.py Successfully Patched! ===")

