/**
 * CustomerVault Interactive Table Enhancer:
 * - Dynamic Column Width Resizing (drag header borders)
 * - Persistent column widths via localStorage
 * - Floating Bulk Action Dock when table rows are checked
 */
(function() {
  'use strict';

  const STORAGE_PREFIX = 'cv_col_widths_';
  let activeDock = null;

  function initTable(table) {
    if (!table || table.dataset.cvEnhanced === 'true') return;
    table.dataset.cvEnhanced = 'true';

    const ths = table.querySelectorAll('thead th');
    if (!ths.length) return;

    const pageKey = STORAGE_PREFIX + window.location.pathname.split('/').pop().replace('.html', '');
    let savedWidths = {};
    try {
      savedWidths = JSON.parse(localStorage.getItem(pageKey) || '{}');
    } catch (_) {}

    ths.forEach((th, idx) => {
      th.classList.add('cv-resizable-th');

      // Apply saved width if available
      const colId = th.textContent.trim().replace(/[^a-zA-Z0-9]/g, '_').toLowerCase() || `col_${idx}`;
      if (savedWidths[colId]) {
        th.style.width = savedWidths[colId] + 'px';
      }

      // Add resizer handle (except on very last column)
      if (idx < ths.length - 1) {
        let resizer = th.querySelector('.cv-col-resizer');
        if (!resizer) {
          resizer = document.createElement('div');
          resizer.className = 'cv-col-resizer';
          th.appendChild(resizer);
        }

        resizer.addEventListener('mousedown', e => {
          e.preventDefault();
          e.stopPropagation();

          resizer.classList.add('resizing');
          const startX = e.pageX;
          const startWidth = th.offsetWidth;

          function onMouseMove(ev) {
            const newWidth = Math.max(startWidth + (ev.pageX - startX), 40);
            th.style.width = newWidth + 'px';
          }

          function onMouseUp() {
            resizer.classList.remove('resizing');
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('mouseup', onMouseUp);

            // Persist width
            savedWidths[colId] = th.offsetWidth;
            try {
              localStorage.setItem(pageKey, JSON.stringify(savedWidths));
            } catch (_) {}
          }

          window.addEventListener('mousemove', onMouseMove);
          window.addEventListener('mouseup', onMouseUp);
        });

        // Double click resets column width
        resizer.addEventListener('dblclick', e => {
          e.stopPropagation();
          th.style.width = '';
          delete savedWidths[colId];
          try {
            localStorage.setItem(pageKey, JSON.stringify(savedWidths));
          } catch (_) {}
        });
      }
    });

    // Make 15-digit IMEI cells interactive for Device 360° Timeline
    try {
      table.querySelectorAll('tbody td').forEach(td => {
        const txt = td.textContent.trim();
        if (/^\d{15}$/.test(txt) && !td.dataset.timelineBound) {
          td.dataset.timelineBound = '1';
          td.style.cursor = 'pointer';
          td.style.color = 'var(--primary, #1d68e1)';
          td.style.fontWeight = '700';
          td.title = 'Click to open 360° Device Lifecycle Timeline';
          td.addEventListener('click', (e) => {
            e.stopPropagation();
            if (window.cv && typeof window.cv.openDeviceTimeline === 'function') {
              window.cv.openDeviceTimeline(txt);
            }
          });
        }
      });
    } catch (_) {}

    initRowSelection(table);
  }

  function initRowSelection(table) {
    const rowCheckboxes = table.querySelectorAll('tbody input[type="checkbox"]');
    if (!rowCheckboxes.length) return;

    function updateDock() {
      const checkedBoxes = Array.from(table.querySelectorAll('tbody input[type="checkbox"]:checked'));
      const count = checkedBoxes.length;

      if (!activeDock) {
        activeDock = document.createElement('div');
        activeDock.className = 'cv-bulk-dock';
        activeDock.innerHTML = `
          <span class="cv-bulk-dock-count"><span id="cvDockNum">0</span> selected</span>
          <button class="cv-bulk-dock-btn primary" id="btnCvDockExport">📥 Export Selected (Excel)</button>
          <button class="cv-bulk-dock-btn" id="btnCvDockRenew" style="background:#10b981;color:#ffffff;border-color:#10b981">🔄 Renew Plans</button>
          <button class="cv-bulk-dock-btn" id="btnCvDockTimeline" style="background:#0284c7;color:#ffffff;border-color:#0284c7">📜 Device 360°</button>
          <button class="cv-bulk-dock-btn" id="btnCvDockClear">✖ Clear Selection</button>
        `;
        document.body.appendChild(activeDock);

        activeDock.querySelector('#btnCvDockClear').onclick = () => {
          table.querySelectorAll('tbody input[type="checkbox"]').forEach(c => c.checked = false);
          updateDock();
        };

        activeDock.querySelector('#btnCvDockTimeline').onclick = () => {
          const selectedRows = Array.from(table.querySelectorAll('tbody tr')).filter(r => {
            const chk = r.querySelector('input[type="checkbox"]');
            return chk && chk.checked;
          });
          if (!selectedRows.length) return;
          const firstRow = selectedRows[0];
          let ident = firstRow.dataset.imei || firstRow.dataset.id;
          if (!ident) {
            for (const td of firstRow.querySelectorAll('td')) {
              const txt = td.textContent.trim();
              if (/^\d{15}$/.test(txt)) { ident = txt; break; }
            }
            if (!ident) {
              const firstTd = firstRow.querySelector('td:nth-child(2), td');
              ident = firstTd ? firstTd.textContent.trim() : '';
            }
          }
          if (ident && window.cv && typeof window.cv.openDeviceTimeline === 'function') {
            window.cv.openDeviceTimeline(ident);
          } else if (typeof window.toast === 'function') {
            window.toast('Select a device row to view 360° timeline.');
          }
        };

        activeDock.querySelector('#btnCvDockRenew').onclick = () => {
          const selectedRows = Array.from(table.querySelectorAll('tbody tr')).filter(r => {
            const chk = r.querySelector('input[type="checkbox"]');
            return chk && chk.checked;
          });
          if (!selectedRows.length) return;

          const ids = [];
          selectedRows.forEach(r => {
            const chk = r.querySelector('input[type="checkbox"]');
            const v = chk ? chk.value : '';
            if (v && /^\d+$/.test(v) && v !== 'on') {
              ids.push(parseInt(v, 10));
            } else if (r.dataset.id && /^\d+$/.test(r.dataset.id)) {
              ids.push(parseInt(r.dataset.id, 10));
            } else {
              const firstTd = r.querySelector('td:nth-child(2), td');
              const txt = firstTd ? firstTd.textContent.trim() : '';
              if (/^\d+$/.test(txt)) ids.push(parseInt(txt, 10));
            }
          });

          if (!ids.length) {
            if (typeof window.toast === 'function') window.toast('No device records found in selection.');
            return;
          }

          if (window.cv && typeof window.cv.openBulkRenewModal === 'function') {
            window.cv.openBulkRenewModal(ids, () => {
              if (typeof window.refreshPageData === 'function') {
                window.refreshPageData();
              } else if (typeof window.loadInventory === 'function') {
                window.loadInventory();
              } else {
                window.location.reload();
              }
            });
          }
        };

        activeDock.querySelector('#btnCvDockExport').onclick = () => {
          const selectedRows = Array.from(table.querySelectorAll('tbody tr')).filter(r => {
            const chk = r.querySelector('input[type="checkbox"]');
            return chk && chk.checked;
          });
          if (!selectedRows.length) return;

          const ths = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.replace('💎', '').trim()).filter(h => h && h !== '#' && h !== 'Actions');
          const data = selectedRows.map(r => {
            const cells = Array.from(r.querySelectorAll('td'));
            return cells.map(td => td.textContent.trim()).filter((_, i) => i < ths.length);
          });

          if (typeof window.exportExcel === 'function') {
            window.exportExcel('Selected_Records_Export', ths, data);
          } else {
            alert(`Exporting ${selectedRows.length} selected records`);
          }
        };
      }

      const numEl = activeDock.querySelector('#cvDockNum');
      if (numEl) numEl.textContent = count;
      activeDock.classList.toggle('active', count > 0);
    }

    rowCheckboxes.forEach(chk => {
      chk.removeEventListener('change', updateDock);
      chk.addEventListener('change', updateDock);
    });
  }

  function scanTables() {
    document.querySelectorAll('table.data-table').forEach(initTable);
  }

  // Observe dynamically rendered tables (like Fetch Data, Customer Inventory, Live Feed)
  const observer = new MutationObserver(mutations => {
    let shouldScan = false;
    for (const m of mutations) {
      if (m.addedNodes && m.addedNodes.length) {
        shouldScan = true;
        break;
      }
    }
    if (shouldScan) scanTables();
  });

  document.addEventListener('DOMContentLoaded', () => {
    scanTables();
    observer.observe(document.body, { childList: true, subtree: true });
  });

  window.cvTableEnhance = { scanTables };
})();
