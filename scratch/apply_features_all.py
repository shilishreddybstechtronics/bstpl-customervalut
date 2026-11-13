import os, re

# =========================================================================
# PART 1: UPDATE INVENTORY.HTML
# 1. downloadBulkUploadTemplate() -> Multi-sheet Sample Excel + Guide
# 2. Customer Download -> openExportColumnsModal(customer) with Column Picker
# =========================================================================

INV_PATH = r"frontend/inventory.html"

with open(INV_PATH, "r", encoding="utf-8") as f:
    inv_text = f.read()

# 1. Upgrade downloadBulkUploadTemplate in inventory.html
old_template_fn = re.search(r'function downloadBulkUploadTemplate\(\) \{.*?\n      \}', inv_text, re.DOTALL)
new_template_fn = '''function downloadBulkUploadTemplate() {
        const headers = [
          'customer_name', 'imei', 'device_sr_no', 'iccid', 'msisdn1', 'msisdn2',
          'act_date', 'expiry_date', 'dispatched_date', 'model', 'sim_provider',
          'sim_type', 'activation_plan', 'firmware', 'flash'
        ];

        const sampleRows = [
          [
            'Acme_Corp', '861329086493088', 'SR_10001', '89916441044828311924', '9876543210', '9876543211',
            '2026-01-15', '2027-01-15', '2026-01-10', 'BSTPL-4G-V2', 'TAISYS (Airtel + BSNL)',
            'E-SIM', '1 Year Commercial Plan', 'v3.1.0', '16MB Winbond'
          ],
          [
            'Tata_Motors', '861329086493089', 'SR_10002', '89916441044828311925', '9876543212', '9876543213',
            '2026-02-01', '2027-02-01', '2026-01-28', 'BSTPL-17IS', 'Vodafone-Idea (Vi)',
            'Plastic SIM', '2 Year Fleet Plan', 'v3.1.0', '16MB Macronix'
          ],
          [
            'Reliance_Logistics', '861329086493090', 'SR_10003', '89916441044828311926', '9876543214', '9876543215',
            '2026-03-10', '2027-03-10', '2026-03-05', 'BSTPL-4G-ADV', 'Jio Commercial IoT',
            'E-SIM', '3 Year Commercial Enterprise', 'v3.2.0', '32MB Winbond'
          ],
          [
            'Mahindra_Transport', '861329086493091', 'SR_10004', '89916441044828311927', '9876543216', '9876543217',
            '2026-04-05', '2027-04-05', '2026-04-01', 'BSTPL-17L', 'Airtel IoT',
            'Plastic SIM', 'Annual Transport Plan', 'v3.1.2', '16MB Adesto'
          ]
        ];

        const instructions = [
          ['CustomerVault Bulk Inventory Upload Guidelines & Rules'],
          [''],
          ['Field / Column', 'Requirement', 'Accepted Values / Format', 'Description & Guidance'],
          ['customer_name', 'Required', 'Text (e.g. Acme_Corp, Tata_Motors)', 'The customer account or portfolio name. In Automatic mode, each Excel sheet name becomes a customer portfolio.'],
          ['imei', 'Required', 'Exact 15 numeric digits (e.g. 861329086493088)', 'Primary device identifier. Must be unique across all inventory records.'],
          ['device_sr_no', 'Optional', 'Alphanumeric string (e.g. SR_10001)', 'Hardware serial number assigned to the device unit.'],
          ['iccid', 'Optional / Recommended', '19 to 20 numeric digits (e.g. 89916441044828311924)', 'Integrated Circuit Card Identifier for the SIM card / chip.'],
          ['msisdn1', 'Optional', '10 to 15 numeric digits (e.g. 9876543210)', 'Primary mobile / SIM phone number.'],
          ['msisdn2', 'Optional', '10 to 15 numeric digits', 'Secondary or fallback SIM mobile phone number.'],
          ['act_date', 'Optional', 'YYYY-MM-DD or DD-MM-YYYY (e.g. 2026-01-15)', 'SIM activation date.'],
          ['expiry_date', 'Optional / Recommended', 'YYYY-MM-DD or DD-MM-YYYY (e.g. 2027-01-15)', 'SIM expiry date used for live expiry alerts and renewal tracking.'],
          ['dispatched_date', 'Optional', 'YYYY-MM-DD or DD-MM-YYYY', 'Date when the device was dispatched to the client.'],
          ['model', 'Optional', 'Text (e.g. BSTPL-4G-V2, 17IS, 17L)', 'Device hardware model.'],
          ['sim_provider', 'Optional', 'Text (e.g. Airtel, Vodafone, Jio, TAISYS)', 'Telecom provider powering the SIM.'],
          ['sim_type', 'Optional', 'E-SIM or Plastic SIM', 'Classification of SIM hardware. System auto-tags if omitted.'],
          ['activation_plan', 'Optional', 'Text (e.g. 1 Year Plan, Annual Fleet)', 'Commercial connectivity plan details.'],
          ['firmware', 'Optional', 'Text (e.g. v3.1.0)', 'Installed firmware revision.'],
          ['flash', 'Optional', 'Text (e.g. 16MB Winbond, Adesto)', 'Flash memory hardware component.'],
          [''],
          ['IMPORTANT UPLOAD TIPS:'],
          ['1. Multi-Sheet Uploads: You can upload a workbook with multiple sheets. Each sheet is imported as its own customer table!'],
          ['2. Error Recovery: Records with invalid IMEIs or formatting errors are NOT lost — they are safely held in "Errored & Invalid Entries" where you can rectify and push them.'],
          ['3. Custom Columns: Any additional columns in your sheet are automatically preserved as custom dynamic attributes.']
        ];

        const wb = XLSX.utils.book_new();

        // Sheet 1: Upload Template
        const wsTemplate = XLSX.utils.aoa_to_sheet([headers, ...sampleRows]);
        wsTemplate['!cols'] = [
          { wch: 22 }, { wch: 20 }, { wch: 16 }, { wch: 26 }, { wch: 15 }, { wch: 15 },
          { wch: 14 }, { wch: 14 }, { wch: 16 }, { wch: 16 }, { wch: 24 },
          { wch: 15 }, { wch: 25 }, { wch: 14 }, { wch: 16 }
        ];
        XLSX.utils.book_append_sheet(wb, wsTemplate, 'Upload_Template');

        // Sheet 2: Upload Instructions & Rules
        const wsGuide = XLSX.utils.aoa_to_sheet(instructions);
        wsGuide['!cols'] = [{ wch: 24 }, { wch: 22 }, { wch: 45 }, { wch: 65 }];
        XLSX.utils.book_append_sheet(wb, wsGuide, 'Upload_Instructions');

        XLSX.writeFile(wb, 'CustomerVault_Sample_Bulk_Upload_Template.xlsx');
        toast('📥 Sample Excel file with complete upload details downloaded successfully!');
        if (typeof showEventPopup === 'function') {
          showEventPopup({
            type: 'download',
            title: 'Sample Template Download Complete',
            message: 'Sample Bulk Upload Excel file (.xlsx) with sample data and upload instructions downloaded.',
            meta: { 'File Name': 'CustomerVault_Sample_Bulk_Upload_Template.xlsx', 'Sheets': 'Upload_Template, Upload_Instructions' },
            progress: '100% Downloaded'
          });
        }
      }'''

if old_template_fn:
    inv_text = inv_text.replace(old_template_fn.group(0), new_template_fn, 1)
    print("Updated downloadBulkUploadTemplate in inventory.html")
else:
    print("WARNING: Could not find old_template_fn")

# 2. Update button label in Bulk Upload toolbar
inv_text = inv_text.replace(
    '<span>📥</span> <span>Download Excel Upload Format</span>',
    '<span>📥</span> <span>Download Sample Excel File &amp; Guide</span>'
)

# 3. Overhaul openExportColumnsModal(customer) and downloadSingleCustomerExcel(customer)
old_export_modal_fn = re.search(r'function openExportColumnsModal\(\) \{.*?\n      \}', inv_text, re.DOTALL)
new_export_modal_fn = '''let currentExportCustomer = null;

      function openExportColumnsModal(customer = null) {
        currentExportCustomer = customer;
        const dlg = $('dlgChooseExportCols');
        if (!dlg) return;

        const titleEl = dlg.querySelector('h3 span:last-child');
        const subEl = dlg.querySelector('p.sub');
        if (titleEl) {
          titleEl.textContent = customer ? `Choose Columns to Download — ${customer.name || 'Customer'}` : 'Choose Columns to Download (Excel)';
        }
        if (subEl) {
          subEl.textContent = customer
            ? `Select which columns you want to see in the exported Excel spreadsheet for ${customer.name || 'Customer'}.`
            : 'Select which columns you want to see in your exported Customer Inventory spreadsheet.';
        }

        const allAvailableCols = [
          { key: 'customer_name', label: 'Customer Name' },
          ...COLS.map(c => ({ key: c[0], label: c[1] })),
          ...(XC || []).map(c => ({ key: c, label: c.replace(/_/g, ' ') })),
          { key: 'added_by', label: 'Added By' },
          { key: 'created_at', label: 'Added On' }
        ];

        const listEl = $('exportColsList');
        if (listEl) {
          listEl.innerHTML = allAvailableCols.map(c => `
            <label class="col-pill-chip active" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border:1.5px solid var(--primary);background:var(--card-subtle);border-radius:20px;cursor:pointer;font-size:12px;font-weight:600;transition:all .15s">
              <input type="checkbox" class="exp-modal-chk" value="${c.key}" checked style="width:14px;height:14px;margin:0;accent-color:var(--primary)" />
              <span>${esc(c.label)}</span>
            </label>
          `).join('');

          const updateCountText = () => {
            const checkedCount = document.querySelectorAll('.exp-modal-chk:checked').length;
            if ($('exportColsCountText')) $('exportColsCountText').textContent = `${checkedCount} of ${allAvailableCols.length} columns selected`;
            if ($('btnConfirmExportExcel')) $('btnConfirmExportExcel').disabled = (checkedCount === 0);
          };

          document.querySelectorAll('.exp-modal-chk').forEach(chk => {
            chk.onchange = e => {
              const chip = e.target.closest('.col-pill-chip');
              if (chip) {
                chip.classList.toggle('active', e.target.checked);
                chip.style.borderColor = e.target.checked ? 'var(--primary)' : 'var(--line)';
                chip.style.background = e.target.checked ? 'var(--card-subtle)' : 'var(--card)';
              }
              updateCountText();
            };
          });

          if ($('btnExpPresetAll')) {
            $('btnExpPresetAll').onclick = () => {
              document.querySelectorAll('.exp-modal-chk').forEach(c => {
                c.checked = true;
                const chip = c.closest('.col-pill-chip');
                if (chip) { chip.classList.add('active'); chip.style.borderColor = 'var(--primary)'; chip.style.background = 'var(--card-subtle)'; }
              });
              updateCountText();
            };
          }

          if ($('btnExpPresetClear')) {
            $('btnExpPresetClear').onclick = () => {
              document.querySelectorAll('.exp-modal-chk').forEach(c => {
                c.checked = false;
                const chip = c.closest('.col-pill-chip');
                if (chip) { chip.classList.remove('active'); chip.style.borderColor = 'var(--line)'; chip.style.background = 'var(--card)'; }
              });
              updateCountText();
            };
          }

          if ($('btnExpPresetSim')) {
            $('btnExpPresetSim').onclick = () => {
              const simKeys = new Set(['customer_name', 'imei', 'iccid', 'msisdn1', 'msisdn2', 'act_date', 'expiry_date', 'sim_provider', 'sim_type']);
              document.querySelectorAll('.exp-modal-chk').forEach(c => {
                c.checked = simKeys.has(c.value);
                const chip = c.closest('.col-pill-chip');
                if (chip) {
                  chip.classList.toggle('active', c.checked);
                  chip.style.borderColor = c.checked ? 'var(--primary)' : 'var(--line)';
                  chip.style.background = c.checked ? 'var(--card-subtle)' : 'var(--card)';
                }
              });
              updateCountText();
            };
          }

          if ($('btnExpPresetId')) {
            $('btnExpPresetId').onclick = () => {
              const idKeys = new Set(['customer_name', 'imei', 'device_sr_no', 'iccid', 'model']);
              document.querySelectorAll('.exp-modal-chk').forEach(c => {
                c.checked = idKeys.has(c.value);
                const chip = c.closest('.col-pill-chip');
                if (chip) {
                  chip.classList.toggle('active', c.checked);
                  chip.style.borderColor = c.checked ? 'var(--primary)' : 'var(--line)';
                  chip.style.background = c.checked ? 'var(--card-subtle)' : 'var(--card)';
                }
              });
              updateCountText();
            };
          }

          updateCountText();
        }

        if ($('closeDlgChooseExportCols')) $('closeDlgChooseExportCols').onclick = () => dlg.close();
        if ($('cancelDlgChooseExportCols')) $('cancelDlgChooseExportCols').onclick = () => dlg.close();

        if ($('btnConfirmExportExcel')) {
          $('btnConfirmExportExcel').onclick = async () => {
            const checked = Array.from(document.querySelectorAll('.exp-modal-chk:checked')).map(c => c.value);
            if (!checked.length) {
              toast('Please select at least one column.');
              return;
            }
            dlg.close();

            try {
              const cust = currentExportCustomer;
              const targetCid = cust ? cust.id : (typeof invCid !== 'undefined' ? invCid : '');
              const custName = cust ? cust.name : (targetCid ? `Customer #${targetCid}` : 'Customer Inventory');
              toast(`Exporting ${custName} with ${checked.length} selected columns…`);
              if (typeof showBstplLoader === 'function') showBstplLoader(`Generating Excel file for ${custName}…`);

              const targetQ = typeof invQ !== 'undefined' ? invQ : '';
              const targetCol = typeof invCol !== 'undefined' ? invCol : 'all';
              const queryUrl = `/api/devices?page=1&page_size=5000&q=${encodeURIComponent(targetQ)}&column=${targetCol}&sort_by=${sortCol}&sort_dir=${sortDir}${targetCid ? '&customer_id=' + targetCid : ''}`;
              const d = await api(queryUrl);

              const colMap = {};
              allAvailableCols.forEach(c => { colMap[c.key] = c.label; });

              const headers = ['ID', ...checked.map(k => colMap[k] || k)];
              const rows = (d.items || []).map(dev => [
                dev.id,
                ...checked.map(k => {
                  if (k === 'customer_name') return dev.customer_name || (cust ? cust.name : '');
                  if (dev.extra && dev.extra[k] !== undefined) return dev.extra[k] || '';
                  return dev[k] != null ? dev[k] : '';
                })
              ]);

              const fileName = (cust ? cust.name : 'Customer_Inventory_Export').replace(/[^a-zA-Z0-9_-]/g, '_');
              await exportExcel(fileName, headers, rows);
              toast(`✓ Successfully downloaded ${custName} with ${checked.length} selected columns!`);
            } catch(err) {
              fail(err);
            } finally {
              if (typeof hideBstplLoader === 'function') hideBstplLoader();
            }
          };
        }

        if (typeof dlg.showModal === 'function') dlg.showModal();
      }

      async function downloadSingleCustomerExcel(customer) {
        // As requested by user: Always prompt for column selection before download!
        openExportColumnsModal(customer);
      }'''

if old_export_modal_fn:
    inv_text = inv_text.replace(old_export_modal_fn.group(0), new_export_modal_fn, 1)
    print("Replaced openExportColumnsModal and downloadSingleCustomerExcel in inventory.html")
else:
    print("WARNING: Could not find old_export_modal_fn")

with open(INV_PATH, "w", encoding="utf-8") as f:
    f.write(inv_text)

print("Inventory updates successfully applied!")

