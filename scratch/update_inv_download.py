file_path = 'frontend/inventory.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update openCustomerEntriesView page_size
old_entries = "const res = await api(`/api/devices?customer_id=${customer.id}&page_size=50000`);"
new_entries = "const res = await api(`/api/devices?customer_id=${customer.id}&page_size=5000`);"

assert old_entries in content, "Could not find old_entries in inventory.html"
content = content.replace(old_entries, new_entries, 1)
print("1. Updated openCustomerEntriesView page_size to 5000.")

# 2. Update downloadSingleCustomerExcel
old_dl_start = 'async function downloadSingleCustomerExcel(customer) {'
old_dl_end = 'function openDownloadAllColumnChooser() {'

idx1 = content.find(old_dl_start)
idx2 = content.find(old_dl_end)

assert idx1 != -1 and idx2 != -1, f"Could not find downloadSingleCustomerExcel boundaries: {idx1}, {idx2}"

new_dl_func = """async function downloadSingleCustomerExcel(customer) {
          try {
            toast(`Generating Excel for ${customer.name}…`);
            if (typeof showBstplLoader === 'function') showBstplLoader(`Generating Excel file for ${customer.name}…`);

            const dlUrl = `/api/devices/export?customer_id=${customer.id}&title=${encodeURIComponent(customer.name)}`;
            const res = await fetch(dlUrl, {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
              }
            });

            if (res.ok) {
              const blob = await res.blob();
              const blobUrl = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = blobUrl;
              const safeName = (customer.name || 'Customer').replace(/[^a-zA-Z0-9_-]/g, '_');
              a.download = `${safeName}_Inventory.xlsx`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              window.URL.revokeObjectURL(blobUrl);
              toast(`✓ Successfully downloaded inventory for ${customer.name}`);
              return;
            }

            // Fallback: client-side Excel builder with 5000 page size
            const jsonRes = await api(`/api/devices?customer_id=${customer.id}&page_size=5000`);
            const items = (jsonRes && jsonRes.items) ? jsonRes.items : [];
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
            toast(`✓ Successfully downloaded inventory for ${customer.name}`);
          } catch(err) {
            fail(err);
          } finally {
            if (typeof hideBstplLoader === 'function') hideBstplLoader();
          }
        }

        // --- 5. "Download All": Multi-Sheet Excel with Customer Names & User-Chosen Columns ---
        """

content = content[:idx1] + new_dl_func + content[idx2:]
print("2. Replaced downloadSingleCustomerExcel function.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated frontend/inventory.html!")
