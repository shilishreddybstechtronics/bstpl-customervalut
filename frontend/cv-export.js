/**
 * CustomerVault Unified Excel Exporter (frontend/cv-export.js)
 * High-performance export utility with text-typing for 10+ digits, auto-fitted widths, multi-sheet support, and binary blob downloads.
 */
(function() {
  'use strict';

  function sanitizeSheetName(name, existingNames = []) {
    let clean = String(name || 'Sheet').replace(new RegExp('[\\\\/?*\\[\\]:]', 'g'), '_').trim();
    if (!clean) clean = 'Sheet';
    if (clean.length > 31) clean = clean.substring(0, 31);
    let unique = clean;
    let counter = 1;
    while (existingNames.includes(unique)) {
      unique = clean.substring(0, 27) + '_' + counter++;
    }
    return unique;
  }

  function prepareWorksheet(headers, rows) {
    if (typeof window.XLSX === 'undefined') return null;

    const cleanHeaders = (headers || []).map(h => String(h ?? '').trim());
    const cleanRows = (rows || []).map(r => {
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

    // Explicit string cell typing to protect IMEIs, ICCIDs, and phone numbers from scientific notation
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
          } else if (/^\d{9,}$/.test(sVal) || /^8\d{13,}/i.test(sVal) || /^[0-9A-Fa-f]{15,}$/.test(sVal) || /^0\d+/.test(sVal)) {
            cell.t = 's';
            cell.v = sVal;
          }
        }
      }
    }

    // Auto-fit column widths
    const colWidths = cleanHeaders.map((h, colIdx) => {
      let maxLen = h.length;
      for (let rowIdx = 0; rowIdx < Math.min(cleanRows.length, 200); rowIdx++) {
        const cellVal = cleanRows[rowIdx][colIdx];
        if (cellVal) maxLen = Math.max(maxLen, String(cellVal).length);
      }
      return { wch: Math.min(Math.max(maxLen + 3, 12), 55) };
    });
    ws['!cols'] = colWidths;

    return ws;
  }

  function downloadBlob(blob, fileName) {
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    }, 800);
  }

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
        const ws = prepareWorksheet(headers, rows);
        const wb = window.XLSX.utils.book_new();
        window.XLSX.utils.book_append_sheet(wb, ws, 'Data');

        const wbout = window.XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        downloadBlob(blob, fileName);

        if (typeof window.toast === 'function') window.toast(`✓ Excel file "${fileName}" downloaded successfully!`);
        return;
      }

      // Fallback: UTF-8 BOM CSV (only when SheetJS is missing)
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
      downloadBlob(blob, `${safeTitle}_${new Date().toISOString().slice(0, 10)}.csv`);
      if (typeof window.toast === 'function') window.toast(`✓ File "${safeTitle}.csv" downloaded successfully!`);
    } catch (e) {
      console.error('Export Excel failed:', e);
      if (typeof window.toast === 'function') window.toast('Export failed: ' + e.message);
    }
  }

  function exportMultiSheetExcel(title, sheets = []) {
    try {
      if (!sheets || !sheets.length) {
        if (typeof window.toast === 'function') window.toast('⚠️ No sheets to export.');
        return;
      }
      if (typeof window.toast === 'function') window.toast('Generating multi-sheet Excel workbook…');

      const safeTitle = (title || 'Multi_Customer_Export').replace(/[^a-zA-Z0-9_-]/g, '_');
      const fileName = `${safeTitle}_${new Date().toISOString().slice(0, 10)}.xlsx`;

      if (typeof window.XLSX !== 'undefined') {
        const wb = window.XLSX.utils.book_new();
        sheets.forEach(s => {
          const sheetName = sanitizeSheetName(s.name, wb.SheetNames);
          const ws = prepareWorksheet(s.headers, s.rows);
          if (ws) {
            window.XLSX.utils.book_append_sheet(wb, ws, sheetName);
          }
        });

        const wbout = window.XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        downloadBlob(blob, fileName);

        if (typeof window.toast === 'function') window.toast(`✓ Multi-sheet workbook "${fileName}" downloaded successfully!`);
        return;
      }

      // Fallback: If XLSX not available, combine rows into single CSV with Sheet column
      const combinedHeaders = ['Sheet / Customer', ...(sheets[0] ? sheets[0].headers : [])];
      const combinedRows = [];
      sheets.forEach(s => {
        (s.rows || []).forEach(r => {
          combinedRows.push([s.name, ...(Array.isArray(r) ? r : Object.values(r))]);
        });
      });
      exportExcel(safeTitle, combinedHeaders, combinedRows);
    } catch (e) {
      console.error('Export multi-sheet Excel failed:', e);
      if (typeof window.toast === 'function') window.toast('Export failed: ' + e.message);
    }
  }

  window.exportExcel = exportExcel;
  window.exportMultiSheetExcel = exportMultiSheetExcel;
  window.cvExport = {
    exportExcel,
    exportMultiSheetExcel,
    prepareWorksheet
  };
})();
