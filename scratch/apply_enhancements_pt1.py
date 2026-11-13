import os
import re

html_path = r'c:\Users\soumy\OneDrive\Documents\bstpl-view\frontend\inventory.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add CSS for customer grid and modals before </style>
css_to_add = """
    /* Customer Files Modern Grid */
    .customer-file-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 18px;
      margin-top: 16px;
    }
    @media (max-width: 640px) {
      .customer-file-grid {
        grid-template-columns: 1fr;
        gap: 14px;
      }
    }
    .customer-file-card {
      min-height: 220px;
      border: 1.5px solid var(--line);
      border-radius: 16px;
      padding: 20px;
      background: var(--card);
      box-shadow: 0 4px 18px rgba(0,0,0,0.03);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 14px;
      transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
      position: relative;
    }
    .customer-file-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 12px 28px rgba(0,0,0,0.08);
      border-color: var(--primary);
    }

    /* Modal Cards Enhancement */
    dialog.modal-card {
      border: 1px solid var(--line);
      box-shadow: 0 30px 80px rgba(0,0,0,.45);
      border-radius: 18px;
    }
    dialog.modal-card::backdrop {
      background: rgba(0, 0, 0, 0.55);
      backdrop-filter: blur(4px);
    }
"""

if '.customer-file-grid' not in content:
    assert '</style>' in content, "Could not find </style>"
    content = content.replace('</style>', css_to_add + '\n  </style>', 1)
    print("1. Injected CSS for customer grid and modals.")

# 2. Add 'Add Column' and 'Add Record' buttons to Bulk Upload (subViewUpload)
upload_header_old = """            <button class="b" id="btnDownloadUploadTemplate" type="button" onclick="downloadBulkUploadTemplate()"
              style="display:inline-flex;align-items:center;gap:6px;font-weight:700;padding:8px 16px;border-radius:8px;background:var(--card-subtle);border:1.5px solid var(--primary);color:var(--primary);cursor:pointer">
              <span>📥</span> <span>Download Excel Upload Format</span>
            </button>"""

upload_header_new = """            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
              <button class="b" id="btnUploadAddCol" type="button" onclick="openAddColumnModal()"
                style="display:inline-flex;align-items:center;gap:6px;font-weight:700;padding:8px 16px;border-radius:8px;background:var(--card);border:1.5px solid var(--line);color:var(--text);cursor:pointer">
                <span>➕ Add Column</span>
              </button>
              <button class="b" id="btnUploadAddRec" type="button" onclick="openAddDeviceModal()"
                style="display:inline-flex;align-items:center;gap:6px;font-weight:700;padding:8px 16px;border-radius:8px;background:var(--card);border:1.5px solid var(--line);color:var(--text);cursor:pointer">
                <span>📱 Add Record</span>
              </button>
              <button class="b" id="btnDownloadUploadTemplate" type="button" onclick="downloadBulkUploadTemplate()"
                style="display:inline-flex;align-items:center;gap:6px;font-weight:700;padding:8px 16px;border-radius:8px;background:var(--card-subtle);border:1.5px solid var(--primary);color:var(--primary);cursor:pointer">
                <span>📥</span> <span>Download Excel Upload Format</span>
              </button>
            </div>"""

if upload_header_old in content:
    content = content.replace(upload_header_old, upload_header_new, 1)
    print("2. Added 'Add Column' and 'Add Record' buttons in Bulk Upload view.")
else:
    print("2. Bulk upload header already updated or not found.")

# 3. Replace dialog block (dlgDeleteCustomerEntries, devdlg, dlgAddColumn) with upgraded modals including dlgSingleCustomerRename
dialog_block_start = '<dialog id="dlgDeleteCustomerEntries"'
dialog_block_end = '<dialog id="dlgChooseExportCols"'

start_idx = content.find(dialog_block_start)
end_idx = content.find(dialog_block_end)
assert start_idx != -1 and end_idx != -1, f"Could not find dialog boundaries: {start_idx}, {end_idx}"

new_dialogs = """<!-- Single Customer Rename Modal -->
  <dialog id="dlgSingleCustomerRename" class="modal-card" style="width:min(540px, 95vw);border-radius:18px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.45);padding:0">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--card)">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:24px">✏️</span>
        <div>
          <h3 style="margin:0;font-size:17.5px;font-weight:800;color:var(--text)">Rename Customer Portfolio</h3>
          <p class="sub" style="margin:2px 0 0;font-size:12px">Update portfolio name across database records and cloud tables</p>
        </div>
      </div>
      <button class="b ghost" id="closeDlgSingleCustomerRename" type="button" onclick="closeModal('dlgSingleCustomerRename')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">✕</button>
    </div>

    <form id="formSingleCustomerRename" style="padding:22px 24px">
      <!-- Current Info Chip -->
      <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 16px;background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;margin-bottom:18px">
        <div style="display:flex;align-items:center;gap:10px;min-width:0">
          <div id="renCustAvatar" style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg, #4f46e5, #6366f1);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px;flex-shrink:0">C</div>
          <div style="min-width:0">
            <span style="font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px">Current Name</span>
            <div id="renCustCurrentName" style="font-size:14.5px;font-weight:800;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">—</div>
          </div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <span style="font-size:11px;color:var(--muted);font-weight:600">Customer ID</span>
          <div id="renCustCurrentId" style="font-size:13.5px;font-weight:800;color:var(--primary)">#—</div>
        </div>
      </div>

      <div style="margin-bottom:16px">
        <label for="singleRenNameInput" style="font-size:13px;font-weight:800;display:block;margin-bottom:6px;color:var(--text)">
          New Customer Name <span style="color:var(--danger)">*</span>
        </label>
        <input type="text" id="singleRenNameInput" placeholder="Enter new customer name" required autocomplete="off"
          style="width:100%;height:44px;padding:0 14px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:14.5px;font-weight:600;box-sizing:border-box" />
        <span class="sub" style="font-size:12px;color:var(--muted);margin-top:6px;display:block">
          ℹ️ TiDB Cloud dedicated table and all SIM inventory references will be automatically updated.
        </span>
      </div>

      <div id="singleRenErr" style="color:var(--danger);font-size:13px;font-weight:700;margin-bottom:14px;padding:10px 14px;border-radius:8px;background:rgba(239,68,68,0.08);border:1px solid #ef4444;display:none"></div>

      <div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;margin-top:20px;border-top:1px solid var(--line);padding-top:16px">
        <button class="b" id="btnCancelSingleRen" type="button" onclick="closeModal('dlgSingleCustomerRename')">Cancel</button>
        <button class="b p" id="btnSaveSingleRen" type="submit" style="background:#4f46e5;border-color:#4f46e5;color:#fff;font-weight:700;padding:8px 22px;display:inline-flex;align-items:center;gap:6px;box-shadow:0 3px 12px rgba(79,70,229,0.25)">
          <span>💾</span> <span>Save New Name</span>
        </button>
      </div>
    </form>
  </dialog>

  <!-- Delete Customer Portfolio Modal -->
  <dialog id="dlgDeleteCustomerEntries" class="modal-card" style="width:min(600px, 95vw);border-radius:18px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.45);padding:0">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--card)">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:24px">🗑️</span>
        <div>
          <h3 style="margin:0;font-size:17.5px;font-weight:800;color:#dc2626">Delete Customer Portfolio</h3>
          <p class="sub" style="margin:2px 0 0;font-size:12px">Safe archiving into Cart (Recycle Bin) or direct permanent erasure</p>
        </div>
      </div>
      <button class="b ghost" id="closeDlgDeleteCustomerEntries" type="button" onclick="closeModal('dlgDeleteCustomerEntries')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">✕</button>
    </div>

    <div style="padding:22px 24px">
      <!-- Target Customer Card -->
      <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 16px;background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;margin-bottom:16px">
        <div style="display:flex;align-items:center;gap:10px;min-width:0">
          <div id="delCustAvatar" style="width:38px;height:38px;border-radius:10px;background:#ef4444;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px;flex-shrink:0">C</div>
          <div style="min-width:0">
            <span style="font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px">Target Portfolio</span>
            <div id="delCustDetailName" style="font-size:15px;font-weight:800;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">—</div>
          </div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <span style="font-size:11px;color:var(--muted);font-weight:600">Affected Records</span>
          <div id="delCustRecordsCount" style="font-size:14px;font-weight:800;color:#dc2626">0 records</div>
        </div>
      </div>

      <!-- Warning notice -->
      <div style="background:rgba(239,68,68,0.08);border:1.5px solid #ef4444;border-radius:10px;padding:12px 14px;margin-bottom:16px;color:var(--ink)">
        <div style="display:flex;align-items:center;gap:8px;font-weight:800;color:#dc2626;font-size:13.5px;margin-bottom:4px">
          <span>⚠️</span> <span>Action Confirmation</span>
        </div>
        <p style="margin:0;font-size:12.5px;line-height:1.5;color:var(--text)">
          You are targeting customer portfolio <b id="delCustTargetName" style="color:#b91c1c">—</b>.
          Other customers and configuration remain strictly unaffected.
        </p>
      </div>

      <!-- Options -->
      <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:16px">
        <label style="display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border:1.5px solid var(--line);border-radius:10px;background:var(--card);cursor:pointer">
          <input type="checkbox" id="delWholeCustChk" checked style="width:18px;height:18px;margin-top:2px" />
          <div>
            <b style="font-size:13px;display:block;color:var(--text)">Move portfolio to Cart (Recommended)</b>
            <span style="font-size:12px;color:var(--muted)">Safely moves customer and SIM entries to Cart recycle bin. Can be restored anytime.</span>
          </div>
        </label>
        <label style="display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border:1.5px solid var(--line);border-radius:10px;background:var(--card);cursor:pointer">
          <input type="checkbox" id="delCustPermanentChk" style="width:18px;height:18px;margin-top:2px" />
          <div>
            <b style="font-size:13px;display:block;color:#dc2626">Permanently erase (bypass Cart)</b>
            <span style="font-size:12px;color:var(--muted)">Immediately purges the customer and all associated SIM records from TiDB Cloud.</span>
          </div>
        </label>
      </div>

      <!-- Typing confirmation -->
      <div style="margin-bottom:16px">
        <label for="delCustConfirmInput" style="font-size:13px;font-weight:700;display:block;margin-bottom:6px">
          To confirm, type the exact customer name "<span id="delCustConfirmExpected" style="color:#b91c1c;user-select:all;font-weight:800"></span>":
        </label>
        <input type="text" id="delCustConfirmInput" placeholder="Type customer name to enable delete button"
          style="width:100%;height:42px;padding:0 14px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:14px;box-sizing:border-box" autocomplete="off" />
      </div>

      <div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;border-top:1px solid var(--line);padding-top:16px">
        <button class="b" id="btnCancelDelCustEntries" type="button" onclick="closeModal('dlgDeleteCustomerEntries')">Cancel</button>
        <button class="b d" id="btnConfirmDelCustEntries" type="button" disabled
          style="background:#dc2626;border-color:#dc2626;color:#fff;font-weight:700;padding:8px 22px;cursor:not-allowed">
          🗑️ Confirm & Delete Customer
        </button>
      </div>
    </div>
  </dialog>

  <!-- Add / Edit Device Record Modal -->
  <dialog id="devdlg" class="modal-card" style="width:min(820px, 95vw);border-radius:18px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.45);padding:0">
    <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--card)">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:24px" id="devIcon">📱</span>
        <div>
          <h3 id="devTitle" style="margin:0;font-size:18px;font-weight:800;color:var(--text)">Add Device Record</h3>
          <p class="sub" id="devSubTitle" style="margin:2px 0 0;font-size:12px">Register a new SIM / hardware record into customer inventory</p>
        </div>
      </div>
      <button class="b ghost" id="devCloseBtn" type="button" onclick="closeModal('devdlg')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">✕</button>
    </div>

    <form id="devform" style="padding:22px 24px;max-height:calc(85vh - 75px);overflow-y:auto">
      <div class="dlg-body" id="devFields"></div>
      <p class="err" id="devErr" role="alert" style="display:none;color:var(--danger);font-size:13px;font-weight:700;margin:12px 0;padding:10px 14px;border-radius:8px;background:rgba(239,68,68,0.08);border:1px solid #ef4444"></p>
      <div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;margin-top:20px;border-top:1px solid var(--line);padding-top:16px">
        <button class="b" type="button" id="devCancel" onclick="closeModal('devdlg')">Cancel</button>
        <button class="b p" type="submit" id="devSave" style="background:linear-gradient(135deg, #2563eb, #1d4ed8);border-color:#2563eb;color:#fff;font-weight:700;padding:8px 24px;box-shadow:0 4px 12px rgba(37,99,235,0.25)">Save Record</button>
      </div>
    </form>
  </dialog>

  <!-- Add Column Modal -->
  <dialog id="dlgAddColumn" class="modal-card"
    style="width:min(620px, 95vw);border-radius:18px;padding:0;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.45)">
    <div
      style="display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--card)">
      <div style="display:flex;align-items:center;gap:12px">
        <span style="font-size:24px">➕</span>
        <div>
          <h3 style="margin:0;font-size:17.5px;font-weight:800;color:var(--text)">Add Column to Customer Inventory</h3>
          <p class="sub" style="margin:2px 0 0;font-size:12px">Create a dynamic custom field across customer inventory records</p>
        </div>
      </div>
      <button class="b ghost" id="closeDlgAddColumn" type="button" onclick="closeModal('dlgAddColumn')" style="font-size:20px;padding:4px 10px;cursor:pointer" aria-label="Close">✕</button>
    </div>
    <form id="formAddColumn" style="padding:22px 24px">
      <div style="margin-bottom:16px">
        <label for="newColName" style="font-weight:800;font-size:13px;display:block;margin-bottom:6px;color:var(--text)">
          Column Header Name <span style="color:var(--danger)">*</span>
        </label>
        <input id="newColName" placeholder="e.g. Warranty Status, Batch No, Vendor Code" required
          style="width:100%;height:42px;padding:0 14px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:14px;box-sizing:border-box"
          autocomplete="off" />
        <span style="font-size:11.5px;color:var(--muted);margin-top:4px;display:block">Unique identifier for this column across inventory tables.</span>
      </div>

      <div style="margin-bottom:16px">
        <label for="newColTarget" style="font-weight:800;font-size:13px;display:block;margin-bottom:6px;color:var(--text)">
          Target Scope (Apply To)
        </label>
        <select id="newColTarget" style="width:100%;height:42px;padding:0 12px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box">
          <option value="all">🌐 All entries (Entire Customer Inventory)</option>
          <option value="customer">👤 All entries of a specific Customer</option>
          <option value="specified">🎯 Specific entries (Filter by IMEI list)</option>
        </select>
      </div>

      <div id="newColCustWrap" style="margin-bottom:16px;display:none;background:var(--card-subtle);padding:14px;border-radius:10px;border:1px solid var(--line)">
        <label for="newColCustSel" style="font-weight:800;font-size:13px;display:block;margin-bottom:6px;color:var(--text)">
          Select Customer Portfolio
        </label>
        <select id="newColCustSel" style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box"></select>
      </div>

      <div id="newColImeisWrap" style="margin-bottom:16px;display:none;background:var(--card-subtle);padding:14px;border-radius:10px;border:1px solid var(--line)">
        <label for="newColImeis" style="font-weight:800;font-size:13px;display:block;margin-bottom:6px;color:var(--text)">
          Target Device IMEIs (One per line or comma-separated)
        </label>
        <textarea id="newColImeis" rows="4" placeholder="869402050123456&#10;869402050123457&#10;..."
          style="width:100%;padding:10px 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-family:monospace;font-size:12.5px;line-height:1.4;box-sizing:border-box"></textarea>
        <span style="font-size:11.5px;color:var(--muted);margin-top:4px;display:block">Paste the list of device IMEIs that should receive this column and value.</span>
      </div>

      <div style="margin-bottom:18px">
        <label for="newColValue" style="font-weight:800;font-size:13px;display:block;margin-bottom:6px;color:var(--text)">
          Initial / Default Value (Optional)
        </label>
        <input id="newColValue" placeholder="e.g. Active, Batch-1, Verified (leave blank for empty cells)"
          style="width:100%;height:42px;padding:0 14px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:14px;box-sizing:border-box"
          autocomplete="off" />
        <span style="font-size:11.5px;color:var(--muted);margin-top:4px;display:block">Assigned to matching records in database. Leave empty to add column with NULL values.</span>
      </div>

      <div class="err" id="newColErr"
        style="display:none;color:var(--danger);font-size:13px;font-weight:700;margin:0 0 14px;padding:10px 14px;border-radius:8px;background:rgba(239,68,68,0.08);border:1px solid #ef4444"></div>

      <div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;border-top:1px solid var(--line);padding-top:16px">
        <button class="b" type="button" id="cancelDlgAddColumn" onclick="closeModal('dlgAddColumn')">Cancel</button>
        <button class="b p" type="submit" id="btnSubmitAddColumn"
          style="background:linear-gradient(135deg, #2563eb, #1d4ed8);border-color:#2563eb;color:#fff;font-weight:700;padding:8px 22px;box-shadow:0 4px 12px rgba(37,99,235,0.25)">
          ➕ Create Column
        </button>
      </div>
    </form>
  </dialog>

  """

content = content[:start_idx] + new_dialogs + content[end_idx:]
print("3. Replaced dialog HTML block.")

# Save modified content
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Part 1 successfully applied!")

