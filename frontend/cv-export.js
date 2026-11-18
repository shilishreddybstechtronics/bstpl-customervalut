/**
 * CustomerVault Unified Excel & CSV Exporter (frontend/cv-export.js)
 * High-performance export utility with text-typing for 10+ digits, auto-fitted widths, and blob downloads.
 */
(function() {
  'use strict';

  function exportExcel(title, headers, rows) {
    try {
      if (!rows || !rows.length) {
        if (typeof window.toast === 'function') window.toast('⚠️ No data records to export.');
        return;
      }
      if (typeof window.toast === 'function') window.toast('Generating Excel file…');

      const safeTitle = (title || 'Export').replace(/[^a-zA-Z0-9_-]/g, '_');
      const fileName = `${safeTitle}_${new Date().toISOString().slice(0, 10)}.xlsx`;

      if (typeof window.XLSX !== 'undefined') {
        const cleanHeaders = (headers || []).map(h => String(h ?? '').trim());
        const cleanRows = rows.map(r => {
          return (headers || []).map((_, i) => {
            const val = Array.isArray(r) ? r[i] : (r && typeof r === 'object' ? r[cleanHeaders[i]] : '');
            if (val == null) return '';
            if (typeof val === 'object') {
              try { return JSON.stringify(val); } catch (_) { return String(val); }
            }
            return String(val).trim();
          });
        });

        const data = [cleanHeaders, ...cleanRows];
        const ws = window.XLSX.utils.aoa_to_sheet(data, { raw: true });

        const range = window.XLSX.utils.decode_range(ws['!ref'] || 'A1:A1');
        for (let R = range.s.r; R <= range.e.r; ++R) {
          for (let C = range.s.c; C <= range.e.c; ++C) {
            const cellRef = window.XLSX.utils.encode_cell({ r: R, c: C });
            const cell = ws[cellRef];
            if (cell && cell.v != null) {
              const sVal = String(cell.v).trim();
              if (R === 0) {
                cell.t = 's';
                cell.v = sVal;
              } else if (/^\d{9,}$/.test(sVal) || /^8\d{13,}/i.test(sVal) || /^[0-9A-Fa-f]{15,}$/.test(sVal)) {
                cell.t = 's';
                cell.v = sVal;
              }
            }
          }
        }

        const colWidths = cleanHeaders.map((h, colIdx) => {
          let maxLen = h.length;
          for (let rowIdx = 0; rowIdx < Math.min(cleanRows.length, 150); rowIdx++) {
            const cellVal = cleanRows[rowIdx][colIdx];
            if (cellVal) maxLen = Math.max(maxLen, String(cellVal).length);
          }
          return { wch: Math.min(Math.max(maxLen + 3, 12), 50) };
        });
        ws['!cols'] = colWidths;

        const wb = window.XLSX.utils.book_new();
        window.XLSX.utils.book_append_sheet(wb, ws, 'Data');

        const wbout = window.XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const blobUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        setTimeout(() => {
          document.body.removeChild(link);
          window.URL.revokeObjectURL(blobUrl);
        }, 600);

        if (typeof window.toast === 'function') window.toast(`✓ Excel file "${fileName}" downloaded successfully!`);
        return;
      }

      // Fallback: UTF-8 BOM CSV
      const csvRows = [headers.map(h => `"${String(h ?? '').replace(/"/g, '""')}"`).join(',')];
      rows.forEach(r => {
        const rowVals = (headers || []).map((_, i) => {
          const v = Array.isArray(r) ? r[i] : (r && typeof r === 'object' ? r[headers[i]] : '');
          return `"${String(v ?? '').replace(/"/g, '""')}"`;
        });
        csvRows.push(rowVals.join(','));
      });
      const BOM = '\uFEFF';
      const blob = new Blob([BOM + csvRows.join('\r\n')], { type: 'text/csv;charset=utf-8' });
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${safeTitle}_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);
      }, 600);
      if (typeof window.toast === 'function') window.toast(`✓ File "${safeTitle}.csv" downloaded successfully!`);
    } catch (e) {
      console.error('Export Excel failed:', e);
      if (typeof window.toast === 'function') window.toast('Export failed: ' + e.message);
    }
  }

  window.exportExcel = exportExcel;
  window.cvExport = { exportExcel };
})();
