with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

export_fn = """
    function openExportColumnsModal() {
      const dlg = $('dlgChooseExportCols');
      if (!dlg) return;

      const allAvailableCols = [
        { key: 'customer_name', label: 'Customer Name' },
        ...COLS.map(c => ({ key: c[0], label: c[1] })),
        ...(XC || []).map(c => ({ key: c, label: c })),
        { key: 'added_by', label: 'Added By' },
        { key: 'created_at', label: 'Added On' }
      ];

      const listEl = $('exportColsList');
      if (listEl) {
        listEl.innerHTML = allAvailableCols.map(c => `
          <label class="col-pill-chip active" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border:1.5px solid var(--primary);background:var(--card);border-radius:20px;cursor:pointer;font-size:12px;font-weight:600;transition:all .15s">
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
    }
"""

anchor = "function openAddColumnModal() {"
assert anchor in text, "anchor not found in build_clean_modular_app.py"

if 'function openExportColumnsModal' not in text:
    text = text.replace(anchor, export_fn + "\n    " + anchor, 1)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added openExportColumnsModal to build_clean_modular_app.py successfully!")

