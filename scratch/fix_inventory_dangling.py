file_path = "frontend/inventory.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target_str = """      async function downloadSingleCustomerExcel(customer) {
        // As requested by user: Always prompt for column selection before download!
        openExportColumnsModal(customer);
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
            toast('Exporting customer inventory…');
            const targetQ = typeof invQ !== 'undefined' ? invQ : '';
            const targetCol = typeof invCol !== 'undefined' ? invCol : 'all';
            const targetCid = typeof invCid !== 'undefined' ? invCid : '';
            const d = await api(`/api/devices?page=1&page_size=5000&q=${encodeURIComponent(targetQ)}&column=${targetCol}&sort_by=${sortCol}&sort_dir=${sortDir}${targetCid ? '&customer_id=' + targetCid : ''}`);
            const colMap = {};
            allAvailableCols.forEach(c => { colMap[c.key] = c.label; });

            const headers = ['ID', ...checked.map(k => colMap[k] || k)];
            const rows = (d.items || []).map(dev => [
              dev.id,
              ...checked.map(k => {
                if (k === 'customer_name') return dev.customer_name || '';
                if (dev.extra && dev.extra[k] !== undefined) return dev.extra[k] || '';
                return dev[k] != null ? dev[k] : '';
              })
            ]);
            await exportExcel('Customer_Inventory_Export', headers, rows);
          } catch(err) {
            fail(err);
          }
        };
      }

      if (typeof dlg.showModal === 'function') dlg.showModal();
    }"""

replacement_str = """      async function downloadSingleCustomerExcel(customer) {
        // As requested by user: Always prompt for column selection before download!
        openExportColumnsModal(customer);
      }"""

if target_str in content:
    content = content.replace(target_str, replacement_str, 1)
    print("Found and replaced dangling old export modal block in inventory.html!")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
else:
    print("Target string not found, searching with regex or normalized spacing...")

