with open('frontend/fetch-data.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Fix btnRunNormalFetch.onclick to directly runNormalFetch(1)
old_btn_click = "$('btnRunNormalFetch').onclick = async () => { if (await askFetchCols('normal')) runNormalFetch(); };"
new_btn_click = "$('btnRunNormalFetch').onclick = () => runNormalFetch(1);"

if old_btn_click in html:
    html = html.replace(old_btn_click, new_btn_click)
    print("Fixed btnRunNormalFetch.onclick")
else:
    print("WARNING: old_btn_click not found.")

# 2. Fix computeDisplayCols fallback
old_compute_custom = """        if (viewOpt === 'custom') {
          const checked = new Set(Array.from(document.querySelectorAll('.nf-col-chk:checked')).map(c => c.value));
          const all = [{ key: 'customer_name', label: 'Customer Name' }, ...COLS.filter(c => c[0] !== 'customer_name').map(c => ({ key: c[0], label: c[1] })), ...Array.from(extraKeys).map(c => ({ key: c, label: c }))];
          return all.filter(c => checked.has(c.key));
        }"""

new_compute_custom = """        if (viewOpt === 'custom') {
          const checked = new Set(Array.from(document.querySelectorAll('.nf-col-chk:checked')).map(c => c.value));
          const all = [{ key: 'customer_name', label: 'Customer Name' }, ...COLS.filter(c => c[0] !== 'customer_name').map(c => ({ key: c[0], label: c[1] })), ...Array.from(extraKeys).map(c => ({ key: c, label: c }))];
          const filtered = all.filter(c => checked.has(c.key));
          if (filtered.length) return filtered;
        }"""

if old_compute_custom in html:
    html = html.replace(old_compute_custom, new_compute_custom)
    print("Fixed computeDisplayCols custom fallback")

# 3. Fix askFetchCols validation
old_ask_cols = """      const picked = await cv.pickColumns(cols, {
        title: kind === 'bulk' ? 'Choose columns for this bulk fetch' : 'Choose columns for this fetch',
        sub: 'Only the selected columns are shown and included in downloads.',
        ok: kind === 'bulk' ? 'Run bulk fetch' : 'Fetch data',
        preselect: cur.length ? cur : undefined
      });
      if (!picked) return false;"""

new_ask_cols = """      const picked = await cv.pickColumns(cols, {
        title: kind === 'bulk' ? 'Choose columns for this bulk fetch' : 'Choose columns for this fetch',
        sub: 'Only the selected columns are shown and included in downloads.',
        ok: kind === 'bulk' ? 'Run bulk fetch' : 'Apply Columns',
        preselect: cur.length ? cur : undefined
      });
      if (!picked || !Array.isArray(picked) || !picked.length) return false;"""

if old_ask_cols in html:
    html = html.replace(old_ask_cols, new_ask_cols)
    print("Fixed askFetchCols validation")

# 4. In _bootPage, auto-run runNormalFetch(1)
old_boot_prompt = """      if (!nfState.hasRun && $('normalFetchResultsWrap')) {
        $('normalFetchResultsWrap').innerHTML = '<div class="empty">Enter one or more values and press <b>Fetch Data</b>, or leave the box empty to list every record.</div>';
      }"""

new_boot_prompt = """      // Auto-fetch page 1 of records immediately so user sees data without delay
      runNormalFetch(1, { silent: false });"""

if old_boot_prompt in html:
    html = html.replace(old_boot_prompt, new_boot_prompt)
    print("Fixed _bootPage to auto-fetch page 1")

# 5. Wire btnNfChooseCols inside renderNormalFetchTable
old_btn_choose = """          <button class="b" id="btnNfChooseCols" type="button" style="font-size:12px;font-weight:700">⚙️ Choose Columns (${displayCols.length})</button>"""
new_btn_choose = """          <button class="b" id="btnNfChooseCols" type="button" onclick="askFetchCols('normal').then(ok => { if(ok) renderNormalFetchTable(nfCurrentList); })" style="font-size:12px;font-weight:700">⚙️ Choose Columns (${displayCols.length})</button>"""

if old_btn_choose in html:
    html = html.replace(old_btn_choose, new_btn_choose)
    print("Wired btnNfChooseCols")

with open('frontend/fetch-data.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("SUCCESS: Updated frontend/fetch-data.html!")

