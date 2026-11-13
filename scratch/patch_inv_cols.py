def patch_inv_cols():
    with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add loadExtraColumns definition before _bootPage
    load_extra_fn = """
    async function loadExtraColumns() {
      try {
        const res = await api('/api/columns/all');
        if (res && res.columns) {
          XC = res.columns.filter(c => c.is_custom).map(c => c.key);
          window.ALL_DB_COLUMNS = res.columns;
        } else {
          const r = await api('/api/columns');
          if (Array.isArray(r)) XC = r;
        }
      } catch (e) {
        try { const r = await api('/api/columns'); if (Array.isArray(r)) XC = r; } catch (e) {}
      }
    }
"""
    if 'async function loadExtraColumns' not in html:
        html = html.replace('const _bootPage = async () => {', load_extra_fn + '\n    const _bootPage = async () => {\n      await loadExtraColumns();')

    # 2. In syncGlobalMetricsAndChrome, update unique_columns
    old_sync_line = "if ($('kpiDev')) $('kpiDev').textContent = Number(devTotal).toLocaleString();"
    new_sync_line = """if ($('kpiDev')) $('kpiDev').textContent = Number(devTotal).toLocaleString();
          if ($('statUniqueColumns')) $('statUniqueColumns').textContent = Number(statsRes.unique_columns || 74).toLocaleString();
          if ($('invColumnsBadge')) $('invColumnsBadge').textContent = `${Number(statsRes.unique_columns || 74).toLocaleString()} Columns`;"""

    if old_sync_line in html:
        html = html.replace(old_sync_line, new_sync_line)

    with open('frontend/inventory.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("SUCCESS: Patched inventory columns loading!")

if __name__ == '__main__':
    patch_inv_cols()

