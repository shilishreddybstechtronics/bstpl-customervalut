content = open('frontend/inventory.html', encoding='utf-8').read()

actions = [
    'cview', 'cdl', 'cren', 'cmerge', 'cav', 'cdel',
    'btnRenameAllCust', 'btnDeleteAllCust', 'cadd', 'chide', 'cs', 'invExport'
]

print("=== CHECKING CUSTOMER INVENTORY ACTION HANDLERS ===")
for act in actions:
    found = act in content
    print(f"Action '{act}': {'FOUND' if found else 'MISSING'}")

# Check dlgChooseExportCols
print("dlgChooseExportCols in DOM:", 'id="dlgChooseExportCols"' in content)
print("openExportColumnsModal in JS:", 'function openExportColumnsModal' in content)
print("downloadSingleCustomerExcel in JS:", 'function downloadSingleCustomerExcel' in content)
print("openDeleteCustomerEntriesModal in JS:", 'function openDeleteCustomerEntriesModal' in content)
print("openSingleCustomerRename in JS:", 'function openSingleCustomerRename' in content)
print("openMergeCustomerModal in JS:", 'function openMergeCustomerModal' in content)
print("openAddCustomerModal in JS:", 'function openAddCustomerModal' in content)
print("openRenameAllCustomersModal in JS:", 'function openRenameAllCustomersModal' in content)

