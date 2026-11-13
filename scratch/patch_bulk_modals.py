with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

bulk_fns = """
    function openBulkEditImeiModal() {
      const dlg = $('dlgBulkEditImei');
      if (dlg && typeof dlg.showModal === 'function') {
        dlg.showModal();
      } else {
        window.location.href = 'edit-delete.html?mode=bulk-edit';
      }
    }

    function openBulkDeleteExcelModal() {
      const dlg = $('dlgBulkDeleteExcel');
      if (dlg && typeof dlg.showModal === 'function') {
        dlg.showModal();
      } else {
        window.location.href = 'edit-delete.html?mode=bulk-delete';
      }
    }
"""

anchor = "function openAddColumnModal() {"
assert anchor in text, "anchor not found in build_clean_modular_app.py"

if 'function openBulkEditImeiModal' not in text:
    text = text.replace(anchor, bulk_fns + "\n    " + anchor, 1)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added openBulkEditImeiModal and openBulkDeleteExcelModal to build_clean_modular_app.py!")

