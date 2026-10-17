/* extras.js - add-on features for CustomerVault. Loads AFTER script.js and only uses its globals
   (api, BOOT, el, $, $$, toast, openModal, exportData, STD, same, daysLeft, today, DATE_COLS).
   Adds: Customer Inventory (Insights / Data Health / Report), Quick Search (Ctrl+K), Bulk Upload, Customer delete, Login Inventory. */
(() => {
  const BUILTIN = ['insert', 'customers', 'fetch', 'manage', 'alerts'];
  let ALL = [];
  const F = (r, n) => { const k = Object.keys(r.fields).find(x => same(x, n)); return k ? String(r.fields[k] ?? '').trim() : ''; };
  const load = async () => { ALL = (await api('/devices')).items; };
  const ISO = /^\d{4}-\d{2}-\d{2}$/;

  /* ---------- Customer Inventory: one tab (right after Customers) holding Insights / Data Health / Customer Report ---------- */
  const panel = Object.assign(el('section', 'panel card hidden'), { id: 'xInventory' });
  const subs = [['insights', '\uD83D\uDCCA Insights', renderInsights], ['health', '\uD83E\uDE7A Data Health', renderHealth], ['report', '\uD83D\uDCD1 Customer Report', renderReport]];
  const invHead = el('div', 'cfhead'), ht = el('div'), subNav = el('div', 'xsubnav'), body = el('div', 'xinvbody');
  ht.append(el('h2', '', 'Customer Inventory'), el('p', 'sub', 'Insights, data health checks and a printable customer report \u2013 all in one place.'));
  invHead.append(el('span', 'cficon', '\uD83D\uDCE6'), ht);
  let cur = 'insights';
  async function showSub(k) {
    cur = k; $$('.xsub', subNav).forEach(x => x.classList.toggle('on', x.dataset.x === k));
    body.replaceChildren(el('p', 'sub', 'Loading\u2026'));
    try { await load(); subs.find(s => s[0] === k)[2](body); } catch (e) { toast(e.message, true); }
  }
  subs.forEach(([k, label]) => { const x = el('button', 'xsub', label); x.type = 'button'; x.dataset.x = k; x.onclick = () => showSub(k); subNav.append(x); });
  panel.append(invHead, subNav, body);
  const invTab = el('button', 'xinvtab', '\uD83D\uDCE6 Customer Inventory'); invTab.type = 'button';
  invTab.onclick = () => {
    $$('.tab').forEach(t => t.classList.remove('active')); BUILTIN.forEach(p => $('#' + p).classList.add('hidden'));
    invTab.classList.add('active'); panel.classList.remove('hidden'); invTab.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' }); showSub(cur);
  };
  $('[data-tab=customers]').after(invTab);
  $('#alerts').after(panel);
  document.addEventListener('click', e => { if (e.target.closest('.tab')) { invTab.classList.remove('active'); panel.classList.add('hidden'); } });

  /* ---------- helpers ---------- */
  const tally = (rows, n) => { const m = new Map(); rows.forEach(r => { const v = F(r, n); if (v) m.set(v, (m.get(v) || 0) + 1); }); return [...m].sort((a, b) => b[1] - a[1]); };
  function bars(title, rows, max = 10, cls = '') {
    const box = el('div', 'xcard'); box.append(el('h3', '', title));
    if (!rows.length) { box.append(el('p', 'sub', 'No data yet')); return box; }
    const top = Math.max(...rows.map(r => r[1]), 1);
    rows.slice(0, max).forEach(([k, v, c]) => {
      const row = el('div', 'xbar'), t = el('div', 'xtrack'), i = el('i', c || cls);
      i.style.width = Math.max(v ? 3 : 0, v / top * 100) + '%'; t.append(i);
      row.append(el('span', '', k), t, el('b', '', v)); row.title = k + ': ' + v; box.append(row);
    });
    return box;
  }
  const kpi = (n, label, cls = '') => { const d = el('div', 'xkpi ' + cls); d.append(el('b', '', n), el('span', '', label)); return d; };
  const head = s => [el('p', 'sub', s)];

  /* ---------- Insights ---------- */
  function renderInsights(p) {
    const left = ALL.map(r => { const v = F(r, 'EXP DATE'); return ISO.test(v) ? daysLeft(v) : null; });
    const has = left.filter(x => x !== null);
    const n = f => has.filter(f).length;
    const buckets = [['Expired', n(x => x < 0), 'bad'], ['0 - 7 days', n(x => x >= 0 && x <= 7), 'bad'], ['8 - 30 days', n(x => x > 7 && x <= 30), 'warn'],
      ['31 - 120 days', n(x => x > 30 && x <= 120), 'warn'], ['Later than 4 months', n(x => x > 120), 'good'], ['No / invalid expiry date', left.length - has.length, '']];
    const perCust = BOOT.customers.map(c => [c.name, c.count]).sort((a, b) => b[1] - a[1]);
    const recent = [...ALL].sort((a, b) => String(b.added_on).localeCompare(String(a.added_on))).slice(0, 8);
    p.replaceChildren(...head('A live summary of every customer table. Numbers are calculated from the database each time you open this tab.'));
    const k = el('div', 'xkpis');
    k.append(kpi(ALL.length, 'Device records'), kpi(BOOT.customers.length, 'Customers'), kpi(n(x => x < 0), 'Expired', 'bad'),
      kpi(n(x => x >= 0 && x <= 30), 'Expiring in 30 days', 'warn'), kpi(n(x => x > 120), 'Valid beyond 4 months', 'good'));
    const g = el('div', 'xgrid');
    g.append(bars('Expiry timeline', buckets, 6), bars('Devices per customer', perCust, 12));
    ['SIM PROVIDER', 'MODEL', 'ACTIVATION PLAN'].forEach(c => g.append(bars('By ' + c.toLowerCase(), tally(ALL, c), 8)));
    const rc = el('div', 'xcard'); rc.append(el('h3', '', 'Recently added'));
    const w = el('div', 'tablewrap'), t = el('table'); w.append(t); rc.append(w);
    const hr = el('tr'); ['IMEI', 'Customer', 'Added by', 'Added on'].forEach(h => hr.append(el('th', '', h))); t.append(hr);
    recent.forEach(r => { const tr = el('tr'); [F(r, 'IMEI'), r.customer, r.added_by, r.added_on].forEach(v => tr.append(el('td', '', v ?? ''))); t.append(tr); });
    g.append(rc); p.append(k, g);
  }

  /* ---------- Data Health ---------- */
  function renderHealth(p) {
    const issues = [];   // [type, value, customer, details]
    ['IMEI', 'ICCID', 'MSISDN1', 'MSISDN2', 'Device Sr No'].forEach(col => {
      const m = new Map(); ALL.forEach(r => { const v = F(r, col); if (v) (m.get(v) || m.set(v, []).get(v)).push(r); });
      m.forEach((a, v) => { if (a.length > 1) issues.push(['Duplicate ' + col, v, [...new Set(a.map(r => r.customer))].join(', '), a.length + ' records']); });
    });
    ALL.forEach(r => {
      const im = F(r, 'IMEI'); if (im && !/^\d{15}$/.test(im)) issues.push(['IMEI is not 15 digits', im, r.customer, im.length + ' characters']);
      DATE_COLS.forEach(c => { const v = F(r, c); if (v && !ISO.test(v)) issues.push(['Invalid date in ' + c, v, r.customer, 'IMEI ' + F(r, 'IMEI')]); });
      const a = F(r, 'ACT DATE'), e = F(r, 'EXP DATE'); if (ISO.test(a) && ISO.test(e) && e < a) issues.push(['Expiry before activation', e, r.customer, 'IMEI ' + F(r, 'IMEI')]);
    });
    const fill = STD().map(c => { const f = ALL.filter(r => F(r, c)).length; return [c, ALL.length ? Math.round(f / ALL.length * 100) : 0]; })
      .map(([c, v]) => [c, v, v < 50 ? 'bad' : v < 90 ? 'warn' : 'good']);
    p.replaceChildren(...head('Finds duplicates, malformed IMEIs, bad dates and empty columns across all customers.'));
    const k = el('div', 'xkpis');
    k.append(kpi(ALL.length, 'Records checked'), kpi(issues.length, 'Issues found', issues.length ? 'bad' : 'good'));
    const g = el('div', 'xgrid'); g.append(bars('Column fill rate (%)', fill, 40));
    const ic = el('div', 'xcard'); ic.append(el('h3', '', 'Issues'));
    const tools = el('div', 'xtools'), dl = el('button', 'btn dl', '\u2B07 Download issues as Excel'); dl.type = 'button';
    dl.onclick = () => issues.length ? exportData([['Issue', 'Value', 'Customer', 'Details'], ...issues], 'data_health_' + today()) : toast('No issues to download', true);
    tools.append(el('span', '', issues.length ? Math.min(issues.length, 200) + ' of ' + issues.length + ' shown' : '\u2714 Everything looks clean'), dl); ic.append(tools);
    if (issues.length) {
      const w = el('div', 'tablewrap'), t = el('table'); w.append(t); ic.append(w);
      const hr = el('tr'); ['Issue', 'Value', 'Customer', 'Details'].forEach(h => hr.append(el('th', '', h))); t.append(hr);
      issues.slice(0, 200).forEach(i => { const tr = el('tr'); i.forEach(v => tr.append(el('td', '', v))); t.append(tr); });
    }
    g.append(ic); p.append(k, g);
  }

  /* ---------- exact match first, similar only when nothing matches exactly ---------- */
  const lc = v => String(v ?? '').trim().toLowerCase();
  function isExact(r, field, q) {
    const want = [lc(q)], iso = toISO(q); if (iso) want.push(iso);
    const vals = field === '__cust' ? [r.customer] : (!field || field === '*') ? [r.customer, ...Object.values(r.fields)]
      : [Object.entries(r.fields).find(([k]) => same(k, field))?.[1]];
    return vals.some(v => want.includes(lc(v)));
  }
  const _origApi = api;
  async function exactFirst(path) {   // all matches come back from the server; keep only the exact ones if there are any
    const res = await _origApi(path), u = new URLSearchParams(path.split('?')[1] || ''), q = (u.get('q') || '').trim();
    if (!q) return { ...res, exact: true };
    const ex = res.items.filter(r => isExact(r, u.get('field'), q));
    return ex.length ? { ...res, items: ex, exact: true } : { ...res, exact: false };
  }
  async function bulkWithSimilar(path, o) {   // Bulk Fetch: exact first; values with no exact match are searched as "similar"
    const r = await _origApi(path, o), nf = r.not_found || [];
    if (!nf.length) return r;
    const col = o.body.column, cid = o.body.customer_id, LIM = 300, items = [...r.items], have = new Set(items.map(x => x.customer + '#' + x.id)), still = [];
    let found = r.found_values || 0, sim = 0;
    for (let i = 0; i < Math.min(nf.length, LIM); i += 10) await Promise.all(nf.slice(i, i + 10).map(async v => {
      try {
        const s = await _origApi('/devices?' + new URLSearchParams({ field: col, q: v, ...(cid ? { customer_id: cid } : {}) }));
        const add = s.items.filter(x => !have.has(x.customer + '#' + x.id) && simPass(x));
        if (add.length) { add.forEach(x => { have.add(x.customer + '#' + x.id); x.similar = true; items.push(x); }); found++; sim++; } else still.push(v);
      } catch { still.push(v); }
    }));
    if (sim) toast(`${sim} value(s) had no exact match \u2013 similar records were added`);
    return { ...r, items, not_found: [...still, ...nf.slice(LIM)], found_values: found };
  }
  const splitVals = q => [...new Map(String(q || '').split(/[,;\n]+/).map(v => v.trim()).filter(Boolean).map(v => [v.toLowerCase(), v])).values()];
  async function multiFetch(path) {   // "imei1, imei2, imei3" -> every record of every value (comma / semicolon / new line separated)
    const u = new URLSearchParams(path.split('?')[1] || ''), vals = splitVals(u.get('q'));
    if (vals.length < 2) return exactFirst(path);
    const whole = await exactFirst(path);
    if (whole.exact && whole.items.length) return whole;   // e.g. the customer called "akhil, dhoni"
    const res = new Array(vals.length);
    for (let i = 0; i < vals.length; i += 8) await Promise.all(vals.slice(i, i + 8).map(async (v, k) => {
      const p = new URLSearchParams(u); p.set('q', v);
      res[i + k] = await exactFirst('/devices?' + p);
    }));
    const have = new Set(), items = [], missing = []; let similar = 0;
    res.forEach((r, i) => {
      if (!r.items.length) return missing.push(vals[i]);
      if (r.exact === false) similar++;
      r.items.forEach(x => { const k = x.customer + '#' + x.id; if (!have.has(k)) { have.add(k); if (r.exact === false) x.similar = true; items.push(x); } });
    });
    return { items, exact: true, multi: vals.length, not_found: missing, similar };
  }
  api = function (path, o = {}) {   // Fetch Data tab (normal) and Bulk Fetch use the new rule; everything else is unchanged
    if (!o.method && /^\/devices\?/.test(path) && !$('#fetch').classList.contains('hidden')) {
      return multiFetch(path).then(r => {
        if (r.multi) {
          const nf = r.not_found;
          if (nf.length || r.similar) toast((nf.length ? `${nf.length} of ${r.multi} value(s) have no record: ${nf.slice(0, 5).join(', ')}${nf.length > 5 ? '\u2026' : ''}` : '') + (r.similar ? `${nf.length ? ' \u00B7 ' : ''}${r.similar} value(s) had no exact match \u2013 similar records shown` : ''), !!nf.length);
        } else if (r.exact === false && r.items.length) toast('No exact match \u2013 showing similar results');
        return r;
      });
    }
    if (o.method === 'POST' && path === '/fetch/bulk') return bulkWithSimilar(path, o);
    return _origApi(path, o);
  };

  /* ---------- Quick Search (Ctrl+K): pick a column, type a value, press Search; duplicates can be edited / deleted ---------- */
  let ALLC = { t: 0, items: [] };
  const allRecords = async () => { if (Date.now() - ALLC.t > 15000) ALLC = { t: Date.now(), items: (await _origApi('/devices')).items }; return ALLC.items; };
  const DUPCOLS = ['IMEI', 'ICCID', 'MSISDN1', 'MSISDN2', 'Device Sr No'];
  function dupGroups(hits, all) {   // groups of records sharing an IMEI / ICCID / phone / serial, that contain at least one search hit
    const idx = new Map();
    all.forEach(r => DUPCOLS.forEach(c => { const v = F(r, c); if (v) { const k = c + '\u0000' + lc(v); (idx.get(k) || idx.set(k, []).get(k)).push(r); } }));
    const out = new Map();
    hits.forEach(h => DUPCOLS.forEach(c => {
      const v = F(h, c); if (!v) return;
      const g = idx.get(c + '\u0000' + lc(v)); if (!g || g.length < 2) return;
      const sig = g.map(r => r.id).sort().join(',');
      if (out.has(sig)) { const o = out.get(sig); if (!o.cols.includes(c)) o.cols.push(c); } else out.set(sig, { cols: [c], val: v, rows: g });
    }));
    return [...out.values()];
  }
  function quickSearch() {
    if ($('#appView').classList.contains('hidden')) return;
    ALLC.t = 0;
    const box = el('div', 'xqs'), row = el('div', 'xqrow'), sel = el('select'), inp = el('input'), go = el('button', 'btn', '\uD83D\uDD0E Search'), res = el('div', 'xqres');
    [['*', 'All columns'], ['__cust', 'Customer Name'], ...STD().map(c => [c, c])].forEach(([v, t]) => { const o = el('option', '', t); o.value = v; sel.append(o); });
    inp.placeholder = 'Customer name, IMEI, ICCID, phone, model\u2026'; go.type = 'button';
    row.append(sel, inp, go);
    box.append(el('h2', '', '\uD83D\uDD0E Quick Search'), row, res, el('p', 'xkbd', 'Choose a column (or All columns), type the value and press Search / Enter \u00B7 Esc closes'));
    const open = r => { closeModal(); $('[data-tab=manage]').click(); $('#mQuery').value = F(r, 'IMEI'); $('#mForm').requestSubmit(); };
    const dupBox = groups => {
      const wrap = el('div', 'xdups');
      wrap.append(el('h3', '', `\u26A0 ${groups.length} duplicate group${groups.length === 1 ? '' : 's'} found`));
      groups.slice(0, 6).forEach(g => {
        const card = el('div', 'xdup'); card.append(el('div', 'xduph', `Same ${g.cols.join(' + ')}: ${g.val} \u00B7 ${g.rows.length} entries`));
        g.rows.forEach(r => {
          const line = el('div', 'xdupr'), bx = el('span', 'xdupb'), ed = el('button', 'btn ghost small', '\u270E Edit'), de = el('button', 'btn danger small', '\uD83D\uDDD1 Delete');
          ed.type = de.type = 'button'; ed.onclick = () => editDevice(r); de.onclick = () => deleteDevice(r);
          bx.append(ed, de); line.append(el('span', '', `${r.customer} \u00B7 IMEI ${F(r, 'IMEI') || '-'} \u00B7 ICCID ${F(r, 'ICCID') || '-'} \u00B7 Exp ${F(r, 'EXP DATE') || '-'}`), bx); card.append(line);
        });
        wrap.append(card);
      });
      if (groups.length > 6) wrap.append(el('p', 'sub', `+ ${groups.length - 6} more \u2013 see Customer Inventory \u25B8 Data Health for the full list`));
      return wrap;
    };
    const paint = (items, exact, q, groups) => {
      res.replaceChildren(); const n = items.length, dupIds = new Set(groups.flatMap(g => g.rows.map(r => r.id)));
      if (!n) return res.append(el('p', 'sub', 'No matching records found.'));
      res.append(el('p', 'sub', `${n} entr${n === 1 ? 'y' : 'ies'} found` + (exact ? ' (exact match)' : ' \u2013 no exact match, showing similar') + (n > 10 ? ` \u00B7 showing first 10 of ${n}` : '')));
      items.slice(0, 10).forEach(r => {
        const d = el('div', 'xhit'), l = el('div'), b = el('b', '', F(r, 'IMEI') || '(no IMEI)');
        l.append(b); if (dupIds.has(r.id)) l.append(el('span', 'xtag', '\u26A0 Duplicate'));
        l.append(el('br'), el('small', '', r.customer + (F(r, 'MODEL') ? ' \u00B7 ' + F(r, 'MODEL') : '')));
        d.append(l, el('small', '', 'Exp: ' + (F(r, 'EXP DATE') || '-'))); d.onclick = () => open(r); res.append(d);
      });
      if (n > 10) {
        const all = el('button', 'btn ghost', `View all ${n} entries in Fetch Data`); all.type = 'button';
        all.onclick = () => { closeModal(); $('[data-tab=fetch]').click(); setTimeout(() => { $('#sField').value = sel.value; $('#sQuery').value = q; $('#searchForm').requestSubmit(); }, 600); };
        res.append(all);
      }
      if (groups.length) res.append(dupBox(groups));
    };
    const run = async () => {
      const q = inp.value.trim(); if (!q) return toast('Type a value to search', true);
      try {
        const r = await exactFirst('/devices?' + new URLSearchParams({ field: sel.value, q })); let groups = [];
        try { groups = dupGroups(r.items, await allRecords()); } catch {}
        paint(r.items, r.exact, q, groups);
      } catch (e) { toast(e.message, true); }
    };
    go.onclick = run; inp.onkeydown = e => { if (e.key === 'Enter') run(); };
    openModal('quick', box); inp.focus();
  }
  const qb = el('button', 'btn ghost', '\uD83D\uDD0E Search'); qb.type = 'button'; qb.title = 'Quick search (Ctrl+K)'; qb.onclick = quickSearch;
  $('#logout').before(qb);
  document.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); quickSearch(); } });

  /* ---------- Customer Report (per-customer expiry summary, Excel + Print) ---------- */
  function renderReport(p) {
    const rows = BOOT.customers.map(c => {
      const mine = ALL.filter(r => r.customer === c.name), l = mine.map(r => { const v = F(r, 'EXP DATE'); return ISO.test(v) ? daysLeft(v) : null; });
      const n = f => l.filter(x => x !== null && f(x)).length;
      return [c.name, mine.length, n(x => x < 0), n(x => x >= 0 && x <= 30), n(x => x > 30 && x <= 120), n(x => x > 120), l.filter(x => x === null).length];
    });
    const heads = ['Customer', 'Records', 'Expired', 'Expiring \u2264 30 days', '31 - 120 days', 'Beyond 4 months', 'No expiry date'];
    const tot = heads.map((_, i) => i ? rows.reduce((s, r) => s + r[i], 0) : 'TOTAL');
    p.replaceChildren(...head('One line per customer. Click a column heading to sort. Use Print for a paper / PDF copy.'));
    const tools = el('div', 'xtools'), dl = el('button', 'btn dl', '\u2B07 Download as Excel'), pr = el('button', 'btn ghost', '\uD83D\uDDA8 Print'), sp = el('span', '', 'Report date: ' + today());
    dl.type = pr.type = 'button'; dl.onclick = () => exportData([heads, ...rows, tot], 'customer_report_' + today()); pr.onclick = () => window.print();
    const bt = el('span'); bt.style.display = 'flex'; bt.style.gap = '8px'; bt.append(dl, pr); tools.append(sp, bt);
    const w = el('div', 'tablewrap'), t = el('table'); w.append(t);
    const hr = el('tr'); heads.forEach(h => hr.append(el('th', '', h))); t.append(hr);
    [...rows, tot].forEach((r, i, a) => { const tr = el('tr'); r.forEach(v => tr.append(el('td', '', v))); if (i === a.length - 1) { tr.style.fontWeight = '700'; tr.dataset.xfixed = '1'; } t.append(tr); });
    p.append(tools, w);
  }

  /* ---------- click any table heading to sort it (works on every existing table) ---------- */
  document.addEventListener('click', e => {
    const th = e.target.closest('th'); if (!th || e.target.closest('input,button,select,a')) return;
    const tbl = th.closest('table'); if (!tbl || tbl.id === 'custTable') return;
    const hr = th.parentElement, i = [...hr.children].indexOf(th);
    const rows = [...tbl.querySelectorAll('tr')].filter(r => !r.querySelector('th') && !r.dataset.xfixed);
    if (rows.length < 2) return;
    const dir = th.dataset.xs === 'asc' ? -1 : 1;
    $$('th', hr).forEach(x => delete x.dataset.xs); th.dataset.xs = dir === 1 ? 'asc' : 'desc';
    const val = r => (r.children[i]?.textContent || '').trim();
    rows.sort((a, b) => val(a).localeCompare(val(b), undefined, { numeric: true, sensitivity: 'base' }) * dir);
    const parent = rows[0].parentElement; rows.forEach(r => parent.append(r));
  });

  /* ---------- Customer Files: filter box + record-count chips (the card design itself is in extras.css) ---------- */
  const cfBox = el('div', 'cfsearch'), cfi = el('input'), cfs = el('span', 'cfsum');
  cfi.placeholder = '\uD83D\uDD0E Filter customers\u2026'; cfBox.append(cfi, cfs); $('#customers .cfhead').after(cfBox);
  const cfApply = () => {
    const q = lc(cfi.value); let shown = 0, total = 0;
    $$('#custTable tbody tr').forEach(tr => { total++; const inp = tr.querySelector('.cfin'), hit = !q || lc(inp ? inp.value + ' ' + inp.dataset.old : '').includes(q); tr.style.display = hit ? '' : 'none'; if (hit) shown++; });
    cfs.textContent = total ? (q ? `${shown} of ${total} customers` : `${total} customers`) : '';
  };
  const cfDecorate = () => {
    $$('#custTable tbody tr').forEach(tr => {
      const inp = tr.querySelector('.cfin'); if (!inp || tr.querySelector('.cfcount')) return;
      const c = BOOT.customers.find(x => String(x.id) === inp.dataset.id); if (!c) return;
      tr.children[1].append(el('small', 'cfcount', c.count + ' record' + (c.count === 1 ? '' : 's')));
    });
    cfApply();
  };
  cfi.oninput = cfApply;
  new MutationObserver(cfDecorate).observe($('#custTable'), { childList: true, subtree: true });
})();


/* =====================================================================================================
   Bulk Upload - plain upload   (replaces the old openBulk window; loads after script.js)
   Flow: choose the Excel file -> Validate -> Preview -> Confirm -> live upload status
   * every sheet = one customer: the SHEET NAME is the customer name (a generic name such as Sheet1 / Page 1 uses the
     FILE NAME instead). The customer is created in MySQL (its own table) and shown on the website automatically.
   * every column of the sheet is saved as it is; a column the database does not have yet is created.
   * the main columns of a file are Device Sr No, IMEI and ICCID. SIM type is decided automatically for each sheet and saved in
     the SIM TYPE column of every record: a sheet that has ICCID values (with its Device Sr No / IMEI) is saved as E-SIM, a sheet
     with NO ICCID value is saved as Plastic SIM. Optionally the form also asks for the customer, model, dispatched date, flash, firmware and SIM provider - these are saved into every record.
     The Fetch Data tab (Normal Fetch / Bulk Fetch) filters on it: E-SIM Fetch / Plastic SIM Fetch.
   * the upload is sent in small parts so a live status (stage, customer, records, percent) can be shown.
   Rows are checked by  POST /devices/bulk/validate  (duplicate Device Sr No / IMEI / ICCID) and saved by  POST /devices/bulk.
   ===================================================================================================== */
(() => {
  const CUST_HDR = /^(customer|client)([ _]?name)?$/i, GENERIC = /^(sheet|page|table)\s*\d*$/i;
  const CHUNK = 400;   // records per request while uploading

  /* ---- choices offered before the upload (they are written into every uploaded record) ---- */
  const MODELS = ['17IS', '17L', '17IS-CAN', '17A', '17S', '13L', '13S', '55L'];     // + "New model" (remembered in this browser)
  const FLASHES = ['Winbond', 'Adesto'];
  const sub4 = n => [n, `${n}(AIRTEL+BSNL)`, `${n}(VI+BSNL)`, `${n}(AIRTEL+VI)`];
  const PROVIDER_GROUPS = [['TAISYS', sub4('TAISYS')], ['SENSORISE', sub4('SENSORISE')], ['GROWSPACE', sub4('GROWSPACE')], ['IOTIVITY', sub4('IOTIVITY')], ['VI', ['VI']]];
  window.cvProviderSelect = (value, onchange) => {   // grouped SIM PROVIDER drop-down (also used by the SIM Data Upload tab)
    const s = document.createElement('select'); s.append(new Option('\u2014 choose \u2014', ''));
    PROVIDER_GROUPS.forEach(([g, opts]) => { const og = document.createElement('optgroup'); og.label = g; opts.forEach(o => og.append(new Option(o, o))); s.append(og); });
    s.value = value || ''; s.onchange = () => onchange(s.value); return s;
  };
  const savedModels = () => { try { return JSON.parse(localStorage.getItem('cv_models') || '[]').filter(m => typeof m === 'string'); } catch { return []; } };
  const rememberModel = m => { try { const l = savedModels(); if (m && !MODELS.some(x => same(x, m)) && !l.some(x => same(x, m))) localStorage.setItem('cv_models', JSON.stringify([...l, m])); } catch { /* storage not available - the model is still used for this upload */ } };
  const allModels = () => [...MODELS, ...savedModels().filter(m => !MODELS.some(x => same(x, m)))];

  const freshOpt = () => ({ customer: '', newCustomer: '', model: '', newModel: '', dispatched: '', flash: '', firmware: '', provider: '' });
  const fresh = () => ({ wb: null, file: '', sheets: [], sel: [], rows: [], verdict: [], cols: [], filter: 'all', added: 0, updated: 0, dupMode: 'skip', repl: new Set(),
                         ignored: 0, failed: '', info: { new_customers: [], new_columns: [] }, opt: freshOpt() });
  let S = fresh();
  const chosenCustomer = () => (S.opt.customer === '__new' ? S.opt.newCustomer : S.opt.customer).replace(/\s+/g, ' ').trim();   // '' = automatic (sheet name)
  const chosenModel = () => (S.opt.model === '__new' ? S.opt.newModel : S.opt.model).replace(/\s+/g, ' ').trim();
  const extraFields = () => {   // [column label, value] written into EVERY row of the file (only the ones that were chosen / typed)
    const o = S.opt, x = [['MODEL', chosenModel()], ['DISPATCHED DATE', o.dispatched], ['FLASH', o.flash], ['FIRMWARE', o.firmware.trim()], ['SIM PROVIDER', o.provider]];
    return x.filter(([, v]) => v);
  };

  const dbDupIdx = () => S.rows.map((_, i) => i).filter(i => S.verdict[i].status === 'duplicate' && S.verdict[i].dups.length && S.verdict[i].dups.every(x => x.where === 'database'));   // already saved in the database
  const headers = g => (g && g[0] ? g[0].cells : []);
  const selSheets = () => S.sheets.filter(x => S.sel.includes(x.name));   // the sheets ticked in the list (all usable sheets by default)
  const baseName = () => String(S.file).replace(/\.[^.]+$/, '').trim();
  const custOf = name => chosenCustomer() || (GENERIC.test(name) ? baseName() : name).replace(/\s+/g, ' ').trim();   // the customer chosen on the form, else sheet name (or file name)
  const fmt = n => Number(n || 0).toLocaleString();
  const SIM_COL = 'SIM TYPE';
  const lowCanon = h => canonCol(h).toLowerCase();
  const sheetType = sh => {   // a sheet with at least one ICCID value = E-SIM, a sheet without any ICCID value = Plastic SIM
    const ic = headers(sh.grid).map((h, i) => (h && lowCanon(h) === 'iccid' ? i : -1)).filter(i => i >= 0);
    return ic.length && sh.grid.slice(1).some(r => ic.some(i => String(r.cells[i] ?? '').trim())) ? 'E-SIM' : 'Plastic SIM';
  };
  const mainMissing = sh => {   // which of the 3 main columns the sheet has no heading for
    const have = new Set(headers(sh.grid).filter(Boolean).map(lowCanon));
    return ['Device Sr No', 'IMEI', 'ICCID'].filter(l => !have.has(l.toLowerCase()));
  };

  function readSheet(name) {   // one sheet -> rows (empty list when it has no heading row + data row)
    const ws = S.wb.Sheets[name];
    const raw = XLSX.utils.sheet_to_json(ws, { header: 1, raw: true, defval: '' });
    const txt = XLSX.utils.sheet_to_json(ws, { header: 1, raw: false, dateNF: 'yyyy-mm-dd', defval: '' });
    const g = raw.map((r, ri) => ({ n: ri + 1, cells: r.map((v, ci) => bfCell(v, (txt[ri] || [])[ci])) })).filter(r => r.cells.some(x => x));
    return g.length < 2 ? [] : g;
  }
  function loadFile(f) {
    if (!f) return;
    if (!/\.(xlsx|xls)$/i.test(f.name)) return toast('Only Excel files (.xlsx, .xls) are allowed', true);
    if (!window.XLSX) return toast('Excel reader could not load - check your internet connection', true);
    const rd = new FileReader();
    rd.onload = () => {
      try {
        S.wb = XLSX.read(rd.result, { type: 'array', cellDates: true }); S.file = f.name;
        S.sheets = S.wb.SheetNames.map(n => { const g = readSheet(n); return { name: n, grid: g, usable: g.length >= 2 }; });
        S.sel = S.sheets.filter(x => x.usable).map(x => x.name);   // every sheet is uploaded automatically
        const skipped = S.sheets.length - S.sel.length;
        if (!S.sel.length) toast('No sheet has a heading row and at least one data row', true);
        else if (skipped) toast(`${skipped} empty sheet(s) skipped (no heading row + data row)`);
      } catch { S.wb = null; S.file = ''; S.sheets = []; S.sel = []; toast('Could not read this Excel file', true); }
      stepForm();
    };
    rd.readAsArrayBuffer(f);
  }

  /* ---------- step 1: choose the file ---------- */
  function optionsBlock() {   // customer / model / dispatched date / flash / firmware / SIM provider
    const box = el('div', 'sb-cols bu-opts'), grid = el('div', 'sb-row'), o = S.opt;
    box.append(el('div', 'lblt', 'More values (optional) \u2013 saved with every record of the file'));
    const field = (label, ...kids) => { const l = el('label', 'lbl', label + ' '); l.append(...kids); grid.append(l); return l; };
    const select = (opts, cur, set, first, extra) => {   // opts = [[value, text]]
      const s = document.createElement('select'); s.append(new Option(first, ''));
      opts.forEach(([v, t]) => s.append(new Option(t, v))); if (extra) s.append(new Option(extra[1], extra[0]));
      s.value = cur; s.onchange = () => set(s.value); return s;
    };
    const text = (cur, set, ph, type = 'text') => { const i = document.createElement('input'); i.type = type; i.value = cur; i.placeholder = ph || ''; i.oninput = () => set(i.value); return i; };

    // model: fixed list + a new entry
    const mNew = text(o.newModel, v => { o.newModel = v; }, 'New model name'); mNew.hidden = o.model !== '__new';
    const mSel = select(allModels().map(m => [m, m]), o.model, v => { o.model = v; mNew.hidden = v !== '__new'; if (!mNew.hidden) mNew.focus(); }, '\u2014 no model \u2014', ['__new', '\u2795 New model\u2026']);
    field('Model', mSel, mNew);

    field('Dispatched date', text(o.dispatched, v => { o.dispatched = v; }, '', 'date'));
    field('Flash', select(FLASHES.map(f => [f, f]), o.flash, v => { o.flash = v; }, '\u2014 no flash \u2014'));
    field('Firmware', text(o.firmware, v => { o.firmware = v; }, 'e.g. v2.4.1'));
    field('SIM provider', window.cvProviderSelect(o.provider, v => { o.provider = v; }));
    box.append(grid, el('small', 'hint', 'A column that is not in the database yet (MODEL, DISPATCHED DATE, FLASH, FIRMWARE, SIM PROVIDER) is created automatically; a column that already exists is simply filled.'));
    return box;
  }
  /* ---- WHICH CUSTOMER?  drop-down: automatic / new customer / every existing customer ---- */
  const refreshForm = () => { const m = $('#mbox'), top = m ? m.scrollTop : 0; stepForm(); if (m) m.scrollTop = top; };
  const NEW = '__new';
  function customerBlock() {
    const box = el('div', 'sb-cols bu-opts bu-cust'), o = S.opt, list = [...BOOT.customers].sort((a, b) => a.name.localeCompare(b.name));
    box.append(el('div', 'lblt', '\uD83D\uDC64 Customer \u2013 who is this file for?'));
    const lab = el('label', 'lbl', 'Choose a customer '), sel = document.createElement('select'), nw = document.createElement('input');
    nw.type = 'text'; nw.placeholder = 'Type the new customer name'; nw.value = o.newCustomer; nw.hidden = o.customer !== NEW;
    sel.append(new Option('Automatic \u2013 sheet name = customer', ''), new Option('\u2795 New customer\u2026', NEW));
    const og = document.createElement('optgroup'); og.label = `Existing customers (${list.length})`;
    list.forEach(c => og.append(new Option(`${c.name}  (${fmt(c.count)} records)`, c.name)));
    if (list.length) sel.append(og);
    sel.value = [...sel.options].some(x => x.value === o.customer) ? o.customer : '';
    o.customer = sel.value;   // a customer that was renamed / deleted meanwhile falls back to Automatic
    const note = el('small', 'hint');
    const paint = () => {
      const typed = o.newCustomer.replace(/\s+/g, ' ').trim(), hit = typed && BOOT.customers.find(c => same(c.name, typed));
      note.textContent = o.customer === NEW
        ? (hit ? `\u201C${hit.name}\u201D already exists \u2013 the records will be added to that existing customer.` : typed ? `A new customer \u201C${typed}\u201D will be created (its own table).` : 'Type the name of the new customer.')
        : o.customer ? `Every record of this file will be added to the existing customer \u201C${o.customer}\u201D.`
        : 'Each sheet becomes its own customer (the sheet name is the customer name). A customer that does not exist yet is created automatically.';
    };
    sel.onchange = () => { o.customer = sel.value; if (o.customer === NEW) S.focusNew = true; refreshForm(); };
    nw.oninput = () => { o.newCustomer = nw.value; paint(); };
    nw.onchange = () => { if (S.sheets.length) refreshForm(); };   // the sheet list below shows the customer name of every sheet
    lab.append(sel, nw); box.append(lab, note); paint();
    if (S.focusNew) { S.focusNew = false; setTimeout(() => nw.focus(), 0); }
    return box;
  }
  function stepForm() {
    const box = el('div', 'sb'), head = el('div', 'sb-head');
    head.append(el('h2', '', '\uD83D\uDCC1 Bulk Upload')); box.append(head);
    box.append(el('p', 'sub', 'Upload Excel \u2192 every sheet becomes a customer (sheet name = customer name, or choose the customer below) \u2192 Validate \u2192 Preview \u2192 Confirm Upload'));
    const g = el('div', 'bu-grid sb-grid'); box.append(g);
    g.append(customerBlock());

    const drop = el('label', 'drop'), fi = document.createElement('input');
    fi.type = 'file'; fi.accept = '.xlsx,.xls'; fi.hidden = true; fi.onchange = () => loadFile(fi.files[0]);
    drop.append(fi, el('b', '', '\u21EA'), el('span', '', S.file ? '\u2714 ' + S.file : 'Click or drag an Excel (.xlsx / .xls) file here'));
    ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
    ['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
    drop.addEventListener('drop', e => loadFile(e.dataTransfer.files[0]));
    g.append(drop);

    if (S.sheets.length) {   // every sheet is ticked by default, any sheet can be switched off by hand
      const sp = el('div', 'sb-cols sb-sheets');
      sp.append(el('div', 'lblt', `Sheets in this file: ${S.sel.length} of ${S.sheets.length} selected \u2013 each sheet becomes one customer`));
      const redraw = () => { const m = $('#mbox'), top = m ? m.scrollTop : 0; stepForm(); if (m) m.scrollTop = top; };
      const bt = el('div', 'sb-shbtns'), all = el('button', 'btn ghost small', 'Select all'), none = el('button', 'btn ghost small', 'Clear');
      all.type = none.type = 'button';
      all.onclick = () => { S.sel = S.sheets.filter(x => x.usable).map(x => x.name); redraw(); };
      none.onclick = () => { S.sel = []; redraw(); };
      bt.append(all, none); sp.append(bt);
      const list = el('div', 'sb-shlist');
      S.sheets.forEach(x => {
        const row = el('label', 'sb-sh' + (x.usable ? '' : ' off')), cb = document.createElement('input'); cb.type = 'checkbox';
        cb.checked = S.sel.includes(x.name); cb.disabled = !x.usable;
        cb.onchange = () => { S.sel = cb.checked ? [...S.sel, x.name] : S.sel.filter(n => n !== x.name); S.sel = S.sheets.map(y => y.name).filter(n => S.sel.includes(n)); redraw(); };
        row.append(cb, el('span', '', x.name), el('small', '', x.usable ? `${x.grid.length - 1} row(s) \u2192 customer \u201C${custOf(x.name)}\u201D \u00B7 ${sheetType(x)}` : 'empty \u2013 no data rows'));
        list.append(row);
      });
      sp.append(list);
      sp.append(el('small', 'hint', 'A generic sheet name (Sheet1, Page 1\u2026) uses the file name as the customer name instead.'));
      g.append(sp);
    }
    g.append(optionsBlock());
    g.append(el('small', 'hint', 'Main columns: Device Sr No, IMEI, ICCID. A sheet with ICCID values is saved as E-SIM; a sheet with no ICCID value is saved as Plastic SIM. Every other column is saved as in the file; a column the database does not have yet is created. The options above are written into every record of the file (a value the Excel row already has is kept).'));


    const act = el('div', 'actions'), cancel = el('button', 'btn ghost', 'Cancel'), go = el('button', 'btn', 'Validate File \u2192');
    cancel.type = go.type = 'button'; cancel.onclick = closeModal; go.onclick = validate;
    act.append(cancel, go); box.append(act); $('#mbox').classList.add('wide'); openModal('bulk', box);
  }

  /* ---------- validation ---------- */
  const dupInfo = d => { const dd = d.dups || []; return [dd.map(x => x.field).join('\n'), dd.map(x => x.value).join('\n'), dd.map(x => x.where === 'file' ? `row ${x.row} of this file` : x.customer).join('\n')]; };
  function buildRows() {   // every row of every selected sheet; the sheet (or file) name is the customer
    const out = [], multi = selSheets().length > 1;
    selSheets().forEach(sh => {
      const hdr = headers(sh.grid), customer = custOf(sh.name), sim = sheetType(sh);
      sh.grid.slice(1).forEach(r => {
        const f = {};
        hdr.forEach((h, i) => {
          const v = String(r.cells[i] ?? '').trim(); if (!h || !v) return;
          if (CUST_HDR.test(String(h).trim())) return;   // the customer comes from the sheet / file name, not from a column
          const l = canonCol(h);
          if (l.toLowerCase() === SIM_COL.toLowerCase()) return;   // SIM TYPE is decided by the ICCID rule, not by the file
          if (!(l in f)) f[l] = isDate(l) ? (toISO(v) || v) : v;
        });
        if (!Object.keys(f).length) { S.ignored++; return; }   // an empty row is ignored (not an error)
        extraFields().forEach(([l, v]) => { if (!(l in f)) f[l] = v; });   // chosen on the form; a value the row already has wins
        f[SIM_COL] = sim;
        out.push({ n: r.n, sheet: sh.name, src: multi ? `${r.n} (${sh.name})` : r.n, customer, sim, fields: f });
      });
    });
    return out;
  }
  async function validate() {
    if (!S.sel.length) return toast(S.sheets.length ? 'Select at least one sheet' : 'Upload an Excel file first', true);
    if (S.opt.customer === '__new' && !chosenCustomer()) return toast('Type the new customer name (or choose \u201CAutomatic\u201D)', true);
    if (S.opt.customer === '__new') {   // the typed name is already a customer -> simply use that customer
      const ex = BOOT.customers.find(c => same(c.name, chosenCustomer()));
      if (ex) { S.opt.customer = ex.name; S.opt.newCustomer = ''; toast(`\u201C${ex.name}\u201D already exists \u2013 records will be added to it`); }
    }
    if (S.opt.model === '__new' && !chosenModel()) return toast('Type the new model name (or choose a model)', true);
    rememberModel(S.opt.model === '__new' ? chosenModel() : '');
    S.ignored = 0; S.rows = buildRows();
    if (!S.rows.length) return toast('No data rows found in the selected sheet(s)', true);
    let r;
    try { r = await api('/devices/bulk/validate', { method: 'POST', body: { rows: S.rows.map(x => ({ customer: x.customer, src: x.src, fields: x.fields })) } }); }
    catch (err) { return toast(err.message, true); }
    S.verdict = r.rows.map(d => ({ status: d.status, reason: d.reason, dups: d.dups || [] }));
    S.info = { new_customers: r.new_customers || [], new_columns: r.new_columns || [] };
    const labels = new Set(); S.rows.forEach(x => Object.keys(x.fields).forEach(k => labels.add(k)));
    S.cols = [...STD().filter(l => labels.has(l)), ...[...labels].filter(l => !STD().includes(l))];
    S.filter = 'all'; stepPreview();
  }

  /* ---------- step 2: preview ---------- */
  function stepPreview() {
    const V = S.verdict, n = k => V.filter(v => v.status === k).length, valid = n('valid');
    const box = el('div', 'sb');
    box.append(el('h2', '', 'Preview & Validation'));
    box.append(el('p', 'sub', `File: ${S.file} \u00B7 ${selSheets().length} sheet(s) \u2192 ${new Set(S.rows.map(r => r.customer)).size} customer(s) \u00B7 each sheet is saved as E-SIM or Plastic SIM`));
    const st = el('div', 'bu-stats');
    [['', V.length, 'Excel Records'], ['ok', valid, 'Valid'], ['dup', n('duplicate'), 'Duplicates'], ['bad', n('invalid'), 'Invalid']]
      .forEach(([c, x, l]) => { const d = el('div', 'bu-stat ' + c); d.append(el('b', '', x), el('span', '', l)); st.append(d); });
    box.append(st);
    const info = [];
    const cnt = t => S.rows.filter((r, i) => r.sim === t && V[i].status === 'valid').length;
    info.push(`E-SIM: ${fmt(cnt('E-SIM'))} record(s) \u00B7 Plastic SIM: ${fmt(cnt('Plastic SIM'))} record(s)  (saved in the SIM TYPE column)`);
    selSheets().forEach(sh => { const m = mainMissing(sh); if (m.length) info.push(`Sheet \u201C${sh.name}\u201D has no ${m.join(' / ')} column` + (m.includes('ICCID') ? ' \u2192 saved as Plastic SIM' : '')); });
    const ex = extraFields(); if (ex.length) info.push('Saved with every record: ' + ex.map(([l, v]) => `${l} = ${v}`).join(' \u00B7 '));
    if (chosenCustomer()) info.push(`All selected sheets are added to customer \u201C${chosenCustomer()}\u201D.`);
    if (S.ignored) info.push(`${S.ignored} empty row(s) were ignored.`);
    if (S.info.new_customers.length) info.push(`New customer table(s) to be created: ${S.info.new_customers.slice(0, 8).join(', ')}`);
    if (S.info.new_columns.length) info.push(`New column(s) to be added to the database: ${S.info.new_columns.join(', ')}`);
    if (n('invalid') + n('duplicate')) info.push('Only valid records will be imported. Invalid and duplicate rows are skipped' + (S.dupMode === 'replace' ? ' \u2013 except the rows that already exist in the database, which replace the saved values.' : '.'));
    if (info.length) { const d = el('div', 'bu-info', info.join('\n')); d.style.whiteSpace = 'pre-line'; box.append(d); }
    const dbd = dbDupIdx();
    if (dbd.length) {   // records that already exist: keep the saved values or replace them with the file's values
      const q = el('div', 'bu-info'); q.style.whiteSpace = 'normal';
      q.append(el('b', '', `${fmt(dbd.length)} row(s) already exist in the database (same Device Sr No / IMEI / ICCID). What should happen to their values?`));
      [['skip', 'Keep the existing values (these rows are skipped)'], ['replace', 'Replace the existing values with the values from this file (a blank cell in the file never erases a saved value)']].forEach(([v, t]) => {
        const l = el('label', 'sb-sh'), r = document.createElement('input'); r.type = 'radio'; r.name = 'bu-dupmode'; r.checked = S.dupMode === v;
        r.onchange = () => { S.dupMode = v; stepPreview(); }; l.append(r, el('span', '', t)); q.append(l);
      });
      box.append(q);
    }
    const seg = el('div', 'seg');
    [['all', 'All', V.length], ['valid', 'Valid', valid], ['duplicate', 'Duplicate', n('duplicate')], ['invalid', 'Invalid', n('invalid')]].forEach(([k, l, c]) => {
      const b = el('button', 'segb' + (S.filter === k ? ' on' : ''), `${l} (${c})`); b.type = 'button'; b.onclick = () => { S.filter = k; stepPreview(); }; seg.append(b);
    });
    box.append(seg);
    const idx = S.rows.map((_, i) => i).filter(i => S.filter === 'all' || V[i].status === S.filter), shown = idx.slice(0, 200);
    const wrap = el('div', 'tablewrap bu-prev'), t = document.createElement('table'), th = document.createElement('thead'), hr = document.createElement('tr');
    ['Excel Row', 'Status', 'Field', 'Value', 'Existing Customer', 'Reason', 'Customer Name', ...S.cols].forEach(h => hr.append(el('th', '', h))); th.append(hr); t.append(th);
    const tb = document.createElement('tbody');
    shown.forEach(i => {
      const r = S.rows[i], d = V[i], tr = document.createElement('tr'), s = el('td', ''); s.append(el('span', 'vst ' + d.status, d.status));
      const di = dupInfo(d).map(x => { const td = el('td', '', x); td.style.whiteSpace = 'pre-line'; return td; });
      tr.append(el('td', '', r.src), s, ...di, el('td', 'why', d.reason), el('td', '', r.customer));
      S.cols.forEach(c => tr.append(el('td', '', r.fields[c] ?? ''))); tb.append(tr);
    });
    t.append(tb); wrap.append(t); box.append(wrap);
    if (!shown.length) box.append(el('p', 'empty', 'No rows in this group.'));
    if (idx.length > shown.length) box.append(el('p', 'sub', `Showing the first ${shown.length} of ${idx.length} rows. Every row is checked and uploaded, not just these.`));
    const act = el('div', 'actions'), left = el('div'), cancel = el('button', 'btn ghost', 'Cancel'), back = el('button', 'btn ghost', '\u2190 Back'),
          ok = el('button', 'btn', (() => { const t = valid + (S.dupMode === 'replace' ? dbd.length : 0); return `Confirm & Upload ${fmt(t)} record${t === 1 ? '' : 's'}` + (S.dupMode === 'replace' && dbd.length ? ` (${fmt(dbd.length)} replace existing)` : ''); })());
    left.style.display = 'flex'; left.style.gap = '10px'; left.append(cancel, back);
    cancel.type = back.type = ok.type = 'button'; cancel.onclick = closeModal; back.onclick = stepForm;
    ok.disabled = !(valid || (S.dupMode === 'replace' && dbd.length)); if (ok.disabled) { ok.style.opacity = .5; ok.title = 'There is no valid record to upload'; }
    ok.onclick = confirmUpload;
    act.append(left, ok); box.append(act); $('#mbox').classList.add('wide'); openModal('bulk', box);
  }

  /* ---------- step 3: upload with a live status ---------- */
  async function confirmUpload() {
    // the valid rows grouped by customer, then cut into parts of CHUNK records
    const groups = new Map();
    const replIdx = new Set(S.dupMode === 'replace' ? dbDupIdx() : []); S.repl = replIdx;
    S.rows.forEach((r, i) => {
      if (S.verdict[i].status !== 'valid' && !replIdx.has(i)) return;   // invalid / duplicate rows are never sent (except the rows that replace saved values)
      const k = r.customer.replace(/\s+/g, ' ').trim(); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(r.fields);
    });
    const parts = [], total = [...groups.values()].reduce((t, a) => t + a.length, 0);
    [...groups].forEach(([customer, rows]) => { for (let i = 0; i < rows.length; i += CHUNK) parts.push({ customer, rows: rows.slice(i, i + CHUNK), size: rows.length }); });

    // status window
    const box = el('div', 'up'), title = el('h2', '', 'Uploading\u2026');
    const stage = el('p', 'sb-msg', ''), bar = el('div', 'up-bar'), fill = el('i'), pct = el('span', 'up-pct', '0%'), line = el('p', 'sub', '');
    bar.append(fill); const log = el('div', 'up-log');
    box.append(title, stage, el('div', 'up-barwrap'), line, el('p', 'hint', 'Please keep this window open until the upload finishes.'), log);
    box.querySelector('.up-barwrap').append(bar, pct);
    openModal('bulk', box);

    const say = (cls, text) => { const d = el('div', 'up-l ' + cls, text); log.append(d); log.scrollTop = log.scrollHeight; return d; };
    let done = 0, imported = 0, updated = 0, skipped = 0, newCust = 0, custDone = 0, shownCust = new Set(), perCust = new Map();
    const setProgress = () => { const p = total ? Math.min(100, Math.round(done / total * 100)) : 100; fill.style.width = p + '%'; pct.textContent = p + '%'; line.textContent = `${fmt(done)} of ${fmt(total)} records processed \u00B7 ${fmt(imported)} added` + (S.dupMode === 'replace' ? ` \u00B7 ${fmt(updated)} replaced` : '') + ` \u00B7 ${fmt(skipped)} skipped`; };
    setProgress();
    S.failed = '';
    try {
      for (let i = 0; i < parts.length; i++) {
        const p = parts[i];
        const nth = [...new Set(parts.map(x => x.customer))].indexOf(p.customer) + 1;
        stage.textContent = `\uD83D\uDCE4 Uploading \u201C${p.customer}\u201D (customer ${nth} of ${groups.size})`;
        const r = await api('/devices/bulk', { method: 'POST', body: { groups: [{ customer: p.customer, rows: p.rows }], on_duplicate: S.dupMode } });
        done += p.rows.length; imported += r.imported || 0; updated += r.updated || 0; skipped += r.skipped || 0;
        newCust += Array.isArray(r.new_customers) ? r.new_customers.length : (+r.new_customers || 0);
        const c = perCust.get(p.customer) || { sent: 0, added: 0 }; c.sent += p.rows.length; c.added += (r.imported || 0) + (r.updated || 0); perCust.set(p.customer, c);
        if (c.sent >= p.size) { custDone++; say('ok', `\u2714 ${p.customer} \u2013 ${fmt(c.added)} of ${fmt(p.size)} record(s) saved`); }
        setProgress();
      }
    } catch (err) {
      S.failed = err.message || 'Upload failed';
      stage.textContent = '\u274C The upload stopped'; title.textContent = 'Upload failed';
      say('bad', `\u2716 ${S.failed}`);
      say('', `${fmt(imported + updated)} record(s) were saved or replaced before the problem.`);
      const act = el('div', 'actions'), close = el('button', 'btn', 'Close'); close.type = 'button'; close.onclick = closeModal;
      act.append(close); box.append(act); refreshAll(); return;
    }
    stage.textContent = '\u2705 Finished'; fill.style.width = '100%'; pct.textContent = '100%';
    S.added = imported; S.updated = updated;
    if (imported || updated) logoFx('ok', newCust ? 'Customers added!' : updated && !imported ? 'Values replaced!' : 'Records added!', `${fmt(imported)} record(s) added` + (updated ? ` \u00B7 ${fmt(updated)} existing record(s) replaced` : '') + (newCust ? ` \u00B7 ${newCust} new customer(s)` : '') + (skipped ? ` \u00B7 ${fmt(skipped)} duplicate(s) skipped` : ''), 1900);
    else logoFx('fail', 'No new records added', skipped ? `${fmt(skipped)} duplicate(s) skipped` : 'Nothing was saved', 2200);
    refreshAll();   // table, counters and customer lists reload from MySQL
    stepDone();
  }
  function stepDone() {
    const rows = S.rows.map((r, i) => [r, S.verdict[i], i]).filter(x => !S.repl.has(x[2])), dup = rows.filter(x => x[1].status === 'duplicate').length, bad = rows.filter(x => x[1].status === 'invalid').length;
    const box = el('div', 'bu-done');
    box.append(el('h2', '', '\u2714 Upload Completed'));
    box.append(el('p', 'sb-msg', `Bulk upload completed successfully. ${fmt(S.added)} record${S.added === 1 ? ' has' : 's have'} been added to the database` + (S.updated ? ` and ${fmt(S.updated)} existing record${S.updated === 1 ? ' was' : 's were'} updated with the new values.` : '.')));
    const st = el('div', 'bu-stats'); st.style.gridTemplateColumns = `repeat(${S.updated ? 4 : 3},1fr)`;
    [['ok', S.added, 'Successfully Added'], ...(S.updated ? [['ok', S.updated, 'Replaced (updated)']] : []), ['dup', dup, 'Duplicate (skipped)'], ['bad', bad, 'Invalid (skipped)']].forEach(([c, x, l]) => { const d = el('div', 'bu-stat ' + c); d.append(el('b', '', fmt(x)), el('span', '', l)); st.append(d); });
    box.append(st);
    const act = el('div', 'actions'), close = el('button', 'btn', 'Close'), left = el('div'); close.type = 'button'; close.onclick = closeModal;
    if (dup + bad) {
      const dl = el('button', 'btn ghost', '\u2B07 Download skipped records (Excel)'); dl.type = 'button';
      dl.onclick = () => exportData([['Excel Row', 'Status', 'Field', 'Value', 'Existing Customer', 'Reason', 'Customer Name', ...S.cols],
        ...rows.filter(x => x[1].status !== 'valid').map(([r, d]) => [r.src, d.status === 'duplicate' ? 'Duplicate' : 'Invalid', ...dupInfo(d).map(x => x.replace(/\n/g, ' / ')), d.reason, r.customer, ...S.cols.map(c => r.fields[c] ?? '')])],
        'bulk_upload_skipped_' + today());
      left.append(dl);
    }
    const again = el('button', 'btn ghost', 'Upload another file'); again.type = 'button'; again.onclick = () => { S = fresh(); stepForm(); }; left.append(again);
    act.append(left, close); box.append(act); openModal('bulk', box);
  }

  window.openBulk = () => { S = fresh(); stepForm(); };   // the existing [Bulk Upload] button calls openBulk()
})();


/* =====================================================================================================
   Customer Files: [Delete] on every customer card (with a confirmation popup) + Hide / Show Customers.
   Deleting drops the customer's MySQL table and removes it from the customer list (DELETE /api/customers/<id>).
   ===================================================================================================== */
(() => {
  const cfBar = $('#customers .cfsearch');
  if (!cfBar) return;
  let hidden = false;

  /* ---------- Hide / Show Customers ---------- */
  const tog = el('button', 'btn ghost small cftoggle'); tog.type = 'button';
  const paint = () => {
    tog.textContent = hidden ? '\uD83D\uDC41 Show Customers' : '\uD83D\uDE48 Hide Customers';
    $('#customers').classList.toggle('cf-hidden', hidden);   // CSS hides the cards, the bottom buttons and the db notes
  };
  tog.onclick = () => { hidden = !hidden; paint(); };
  cfBar.append(tog); paint();

  /* ---------- confirmation popup ---------- */
  function confirmDelete(c) {
    const box = document.createElement('div'), n = c.count || 0;
    box.append(el('h2', '', '\uD83D\uDDD1 Delete customer'));
    const msg = el('div', 'dupbox');
    msg.append('Are you sure you want to delete customer ', el('b', '', c.name), '?');
    box.append(msg);
    box.append(el('p', 'sub', `The customer "${c.name}" and its ${n} device record${n === 1 ? '' : 's'} are moved to the Cart. You can restore them from the Cart tab, or delete them permanently there.`));
    const act = el('div', 'actions'), no = el('button', 'btn ghost', 'Cancel'), ok = el('button', 'btn danger cfdelok');
    no.type = ok.type = 'button'; ok.append('\uD83D\uDDD1 Delete customer \u201C', el('span', 'cfdelname', c.name), '\u201D');
    no.onclick = closeModal;
    ok.onclick = async () => {
      ok.disabled = true; ok.style.opacity = .6;
      try {
        const r = await api('/customers/' + c.id, { method: 'DELETE', body: { name: c.name } });
        if (typeof custDraft === 'object') delete custDraft[c.id];
        closeModal(); toast(`Customer "${r.name}" moved to the Cart \u2014 ${r.records} record(s) can be restored there \u2714`); logoFx('ok', 'Moved to Cart', `${r.name} \u00B7 ${r.records} record(s)`, 1900); refreshAll();
      } catch (err) { ok.disabled = false; ok.style.opacity = 1; toast(err.message, true); }
    };
    act.append(no, ok); box.append(act); openModal('deletecust', box); no.focus();
  }

  /* ---------- a Delete button on every card (cards are redrawn by script.js, so decorate after each redraw) ---------- */
  const decorate = () => {
    $$('#custTable tbody tr').forEach(tr => {
      const inp = tr.querySelector('.cfin'), box = tr.querySelector('.cfact');
      if (!inp || !box || box.querySelector('.cfdel')) return;
      const c = BOOT.customers.find(x => String(x.id) === inp.dataset.id); if (!c) return;
      const b = el('button', 'btn cfg red cfdel', '\uD83D\uDDD1 Delete Customer'); b.type = 'button';
      b.title = `Delete ${c.name}`; b.onclick = () => confirmDelete(c);
      box.append(b);
    });
  };
  new MutationObserver(decorate).observe($('#custTable'), { childList: true, subtree: true }); decorate();

  /* ---------- Login Inventory: who logged in / what each user did, with time stamps + Excel download ---------- */
  function loginInventory() {
    const box = el('div'); box.append(el('h2', '', '\uD83D\uDD52 Login Inventory'),
      el('p', 'sub', 'Every login, logout and change made by each user, newest first. Filter it, then download it as Excel.'));
    const uSel = el('select'), aSel = el('select'), dFrom = el('input'), dTo = el('input'), qIn = el('input');
    dFrom.type = dTo.type = 'date'; qIn.placeholder = 'Search details\u2026';
    const lab = (t, n) => { const l = el('label', 'lbl', t + ' '); l.append(n); return l; };
    const bar = el('div', 'xqrow xlif');
    const go = el('button', 'btn', 'Apply'), clr = el('button', 'btn ghost', 'Clear'), dl = el('button', 'btn dl', '\u2B07 Download as Excel'), cl = el('button', 'btn ghost', 'Close');
    [go, clr, dl, cl].forEach(b => b.type = 'button');
    bar.append(lab('User', uSel), lab('Action', aSel), lab('From', dFrom), lab('To', dTo), lab('Search', qIn));
    const btns = el('div', 'xtools'); const left = el('span', '', ''); const right = el('span'); right.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap';
    right.append(go, clr, dl, cl); btns.append(left, right);
    const chips = el('div', 'sb-chips'), wrap = el('div', 'tablewrap xqres'), tbl = el('table'); wrap.append(tbl);
    box.append(bar, btns, chips, wrap);
    let first = true;
    const qs = lim => new URLSearchParams({ emp: uSel.value, action: aSel.value, from: dFrom.value, to: dTo.value, q: qIn.value.trim(), limit: lim });
    const fill = (sel, first, opts) => { const keep = sel.value; sel.replaceChildren(new Option(first, '')); opts.forEach(([v, t]) => sel.append(new Option(t, v))); sel.value = keep; };
    async function load() {
      let r; try { r = await api('/activity?' + qs(2000)); } catch (e) { return toast(e.message, true); }
      fill(uSel, 'All users', r.users.map(u => [u.emp_id, `${u.name} (${u.emp_id})`]));
      fill(aSel, 'All actions', r.actions.map(a => [a, a]));
      chips.replaceChildren(...r.users.filter(u => u.logins).map(u => el('span', 'sb-chip ok', `${u.name}: last login ${u.last_login} \u00B7 ${u.logins} login(s)`)));
      left.textContent = `Showing ${r.items.length} of ${r.total} entries`;
      tbl.replaceChildren(); const hr = el('tr'); ['#', 'Date & Time', 'User', 'Employee ID', 'Action', 'Details', 'IP address'].forEach(h => hr.append(el('th', '', h))); tbl.append(hr);
      if (!r.items.length) { const tr = el('tr'), td = el('td', '', 'No activity found.'); td.colSpan = 7; tr.append(td); tbl.append(tr); }
      r.items.forEach((x, i) => { const tr = el('tr'); [i + 1, x.at, x.name || '-', x.emp_id || '-', x.action, x.details, x.ip].forEach(v => tr.append(el('td', '', v))); if (x.action === 'Failed login') tr.style.color = 'var(--err)'; tbl.append(tr); });
    }
    go.onclick = load; cl.onclick = closeModal;
    clr.onclick = () => { uSel.value = aSel.value = dFrom.value = dTo.value = qIn.value = ''; load(); };
    qIn.onkeydown = e => { if (e.key === 'Enter') load(); };
    [uSel, aSel, dFrom, dTo].forEach(x => x.onchange = load);
    dl.onclick = async () => {
      let r; try { r = await api('/activity?' + qs(50000)); } catch (e) { return toast(e.message, true); }
      if (!r.items.length) return toast('Nothing to download', true);
      exportData([['Date & Time', 'User', 'Employee ID', 'Action', 'Details', 'IP address'], ...r.items.map(x => [x.at, x.name, x.emp_id, x.action, x.details, x.ip])], 'login_inventory_' + today());
    };
    $('#mbox').classList.add('wide'); openModal('loginlog', box); load();
  }
  const lb = el('button', 'btn ghost', '\uD83D\uDD52 Login Inventory'); lb.type = 'button'; lb.id = 'loginInv'; lb.title = 'Who logged in and what each user did, with time stamps';
  lb.onclick = loginInventory; $('#logout').before(lb);
})();

/* =====================================================================================================
   SIM Data Upload - a separate tab. Upload the Excel file a SIM provider (Sensorise, Taisys, Growspace, Iotivity, VI ...) sent you:
   ICCID + MSISDN1 + MSISDN2 + ACT DATE + EXP DATE.  Every customer record with the same ICCID - in ANY customer - gets those values (values already saved are kept unless you tick replace).
   Nothing is fetched from a provider's server: the file is read in the browser, checked first (nothing saved), then pushed to MySQL
   (server: database.apply_sim_data, route POST /api/simdata/apply).
   ===================================================================================================== */
(() => {
  // [key, label, required, accepted heading names (letters / digits only, lower case)]
  const FIELDS = [
    ['iccid', 'CCIDNO', true, ['ccidno', 'ccid', 'iccid', 'ccidnumber', 'iccidno', 'iccidnumber']],   // the one mandatory column: CCID = CCIDNO = ICCID (all headings are understood)
    ['msisdn1', 'MSISDN1', false, ['msisdn1', 'msisdn', 'primarymsisdn', 'msisdnprimary', 'mobileno', 'mobilenumber', 'mobile', 'phonenumber', 'phoneno', 'mdn', 'primarynumber']],
    ['msisdn2', 'MSISDN2', false, ['msisdn2', 'fallbackmsisdn', 'msisdnfallback', 'secondarymsisdn', 'secondmsisdn', 'secondarynumber', 'alternatenumber']],
    ['act', 'ACT DATE', false, ['actdate', 'activationdate', 'activatedon', 'activateon', 'commercialactivationdate', 'bootstrapactivationdate', 'dateofactivation', 'simactivationdate', 'activatedate', 'activation']],
    ['exp', 'EXP DATE', false, ['expdate', 'expirydate', 'expiredon', 'expireson', 'commercialexpirydate', 'bootstrapexpirydate', 'expirationdate', 'expiry', 'expiration', 'validtill', 'validity']],
  ];
  const nrm = s => String(s ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const kpi = (n, label, cls = '') => { const d = el('div', 'xkpi ' + cls); d.append(el('b', '', n), el('span', '', label)); return d; };
  const BLOCK = ['insert', 'customers', 'fetch', 'manage', 'alerts', 'xInventory'];
  let st = { wb: null, file: '', sheets: [], map: {}, prov: '', overwrite: true, res: null, busy: false };

  const panel = Object.assign(el('section', 'panel card hidden'), { id: 'xSimData' });
  const tab = Object.assign(el('button', 'xinvtab', '\uD83D\uDCF1 SIM Data Upload'), { id: 'simTab', type: 'button' });
  tab.onclick = () => {
    $$('.tab, .xinvtab').forEach(t => t.classList.remove('active'));
    BLOCK.forEach(p => { const n = $('#' + p); if (n) n.classList.add('hidden'); });
    tab.classList.add('active'); panel.classList.remove('hidden');
    tab.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' }); draw();
  };
  (document.querySelector('.xinvtab') || $('[data-tab=customers]')).after(tab);
  $('#alerts').after(panel);
  document.addEventListener('click', e => { const t = e.target.closest('.tab, .xinvtab'); if (t && t !== tab) { tab.classList.remove('active'); panel.classList.add('hidden'); } });

  const serialToISO = n => new Date(Math.round((n - 25569) * 864e5)).toISOString().slice(0, 10);   // Excel day number -> yyyy-mm-dd
  function readSheet(name) {   // heading row = first row (of the top 15) that has an ICCID heading
    const ws = st.wb.Sheets[name];
    const raw = XLSX.utils.sheet_to_json(ws, { header: 1, raw: true, defval: '' });
    const fmt = XLSX.utils.sheet_to_json(ws, { header: 1, raw: false, dateNF: 'yyyy-mm-dd', defval: '' });
    const filled = r => r.filter(v => String(v ?? '').trim()).length;
    let hi = raw.slice(0, 15).findIndex(r => r.some(v => FIELDS[0][3].includes(nrm(v)))), guessed = false;
    if (hi < 0) { hi = raw.slice(0, 15).findIndex(r => filled(r) >= 2); guessed = hi >= 0; }   // no CCID heading recognised: the first row of headings is used, so every column can be listed and chosen by hand
    return { name, raw, fmt, hi, guessed, headers: hi < 0 ? [] : raw[hi].map(v => String(v ?? '').trim()), count: hi < 0 ? 0 : raw.slice(hi + 1).filter(r => r.some(v => String(v ?? '').trim())).length };
  }
  function loadFile(f) {
    if (!f) return;
    if (!/\.(xlsx|xls|csv)$/i.test(f.name)) return toast('Only Excel / CSV files (.xlsx, .xls, .csv) are allowed', true);
    if (!window.XLSX) return toast('Excel reader could not load - check your internet connection', true);
    const rd = new FileReader();
    rd.onload = () => {
      try {
        st.wb = XLSX.read(rd.result, { type: 'array', cellDates: true }); st.file = f.name; st.res = null;
        st.sheets = st.wb.SheetNames.map(readSheet);
        const heads = []; st.sheets.forEach(s => s.headers.forEach(h => { if (h && !heads.some(x => nrm(x) === nrm(h))) heads.push(h); }));
        st.heads = heads; st.map = {};
        const used = new Set();   // every field is matched by its heading; a file column is never used for two fields
        FIELDS.forEach(([k, , , names]) => { for (const n of names) { const h = heads.find(x => nrm(x) === n && !used.has(nrm(x))); if (h) { st.map[k] = nrm(h); used.add(nrm(h)); break; } } });
        if (!st.map.iccid) toast(st.sheets.some(s => s.hi >= 0) ? 'No CCID / CCIDNO / ICCID heading recognised - choose the CCID column from the list below' : 'No headings found in this file', true);
      } catch { st.wb = null; st.file = ''; st.sheets = []; toast('Could not read this file', true); }
      draw(); autoCheck();
    };
    rd.readAsArrayBuffer(f);
  }
  function buildRows() {
    const out = [];
    st.sheets.filter(s => s.hi >= 0).forEach(s => {
      const idx = {}; FIELDS.forEach(([k]) => { idx[k] = st.map[k] ? s.headers.findIndex(h => nrm(h) === st.map[k]) : -1; });
      for (let ri = s.hi + 1; ri < s.raw.length; ri++) {
        const row = {};
        FIELDS.forEach(([k]) => {
          const ci = idx[k]; if (ci < 0) return;
          const v = s.raw[ri][ci];
          const x = (k === 'act' || k === 'exp') && typeof v === 'number' && v > 20000 && v < 80000 ? serialToISO(v) : bfCell(v, (s.fmt[ri] || [])[ci]);
          if (String(x ?? '').trim()) row[k] = x;   // empty cells are ignored (they never blank an existing value)
        });
        if (row.iccid) out.push(row);               // ICCID is the only mandatory value - rows without it are ignored
      }
    });
    return out;
  }
  let tk = 0, timer = 0;
  const hasData = () => FIELDS.slice(1).some(([k]) => st.map[k]) || !!st.prov;
  function autoCheck() {   // the check (nothing is saved) runs by itself whenever the file, a column or the overwrite option changes
    clearTimeout(timer); tk++;
    timer = setTimeout(() => { if (st.map.iccid && hasData()) run(true, true); }, 250);
  }
  async function run(dry, quiet) {
    if (!st.map.iccid) return toast('Choose which column holds the CCIDNO', true);
    const rows = buildRows(); if (!rows.length) return quiet ? undefined : toast('No rows with a CCIDNO found in the file', true);
    if (!st.prov && !rows.some(r => r.msisdn1 || r.msisdn2 || r.act || r.exp)) return quiet ? undefined : toast('Only the CCIDNO column is used - other columns are ignored unless you choose them below (MSISDN1 / MSISDN2 / ACT DATE / EXP DATE)', true);
    if (!dry) return push(rows);   // the real push runs in parts with a live status window
    const my = ++tk; st.busy = true; draw();
    try {
      const r = await api('/simdata/apply', { method: 'POST', body: { rows, overwrite: st.overwrite, dry_run: true, provider: st.prov } });
      if (my !== tk) { st.busy = false; return; }   // something changed meanwhile - a newer check is on its way
      st.res = r;
    } catch (err) { toast(err.message, true); }
    st.busy = false; draw();
  }

  /* ---------- Push: sent in parts of PART file rows, with a live "how many are updated" status ---------- */
  const PART = 1000, nf = n => Number(n || 0).toLocaleString();
  async function push(rows) {
    const parts = []; for (let i = 0; i < rows.length; i += PART) parts.push(rows.slice(i, i + PART));
    const agg = { dry_run: false, provider_rows: 0, valid_iccids: 0, skipped_rows: 0, duplicate_iccids: 0, bad_dates: 0, matched_iccids: 0, matched_records: 0,
                  updated_records: 0, unchanged_records: 0, customers: [], sample: [], created_columns: [], not_found: [], not_found_total: 0 };
    const merge = r => {
      ['provider_rows', 'valid_iccids', 'skipped_rows', 'duplicate_iccids', 'bad_dates', 'matched_iccids', 'matched_records', 'updated_records', 'unchanged_records', 'not_found_total']
        .forEach(k => { agg[k] += r[k] || 0; });
      (r.customers || []).forEach(c => {
        const a = agg.customers.find(x => x.name === c.name);
        if (!a) return agg.customers.push({ ...c, fields: { ...(c.fields || {}) } });
        a.matched += c.matched; a.updated += c.updated;
        Object.entries(c.fields || {}).forEach(([f, n]) => { a.fields[f] = (a.fields[f] || 0) + n; });
      });
      (r.sample || []).forEach(s => { if (agg.sample.length < 300) agg.sample.push(s); });
      (r.created_columns || []).forEach(x => { if (!agg.created_columns.includes(x)) agg.created_columns.push(x); });
      (r.not_found || []).forEach(x => agg.not_found.push(x));
    };
    const box = el('div', 'up'), title = el('h2', '', 'Pushing SIM data\u2026'), stage = el('p', 'sb-msg', ''), line = el('p', 'sub', '');
    const bar = el('div', 'up-bar'), fill = el('i'), pct = el('span', 'up-pct', '0%'), wrap = el('div', 'up-barwrap'), log = el('div', 'up-log');
    bar.append(fill); wrap.append(bar, pct);
    box.append(title, stage, wrap, line, el('p', 'hint', 'Please keep this window open until the push finishes.'), log);
    openModal('bulk', box);
    let done = 0;
    const show = () => {
      const p = rows.length ? Math.min(100, Math.round(done / rows.length * 100)) : 100; fill.style.width = p + '%'; pct.textContent = p + '%';
      line.textContent = `${nf(done)} of ${nf(rows.length)} file rows processed \u00B7 ${nf(agg.updated_records)} record(s) updated \u00B7 ${nf(agg.unchanged_records)} already the same`;
    };
    const say = (cls, t) => { log.append(el('div', 'up-l ' + cls, t)); log.scrollTop = log.scrollHeight; };
    st.busy = true; draw(); show();
    try {
      for (let i = 0; i < parts.length; i++) {
        stage.textContent = `\uD83D\uDCE4 Updating records \u2026 part ${i + 1} of ${parts.length}`;
        const r = await api('/simdata/apply', { method: 'POST', body: { rows: parts[i], overwrite: st.overwrite, dry_run: false, provider: st.prov } });
        merge(r); done += parts[i].length; show();
        say('ok', `\u2714 Part ${i + 1}: ${nf(r.updated_records)} record(s) updated, ${nf(r.unchanged_records)} already the same`);
      }
    } catch (err) {
      stage.textContent = '\u274C The push stopped'; title.textContent = 'Push failed';
      say('bad', `\u2716 ${err.message || 'Push failed'}`); say('', `${nf(agg.updated_records)} record(s) were updated before the problem.`);
      const act = el('div', 'actions'), close = el('button', 'btn', 'Close'); close.type = 'button'; close.onclick = closeModal; act.append(close); box.append(act);
      st.res = agg.updated_records ? agg : st.res; st.busy = false; draw(); refreshAll(); return;
    }
    st.res = agg; st.busy = false; draw();
    stage.textContent = '\u2705 Finished'; title.textContent = 'SIM data pushed'; fill.style.width = '100%'; pct.textContent = '100%';
    say('ok', `${nf(agg.updated_records)} record(s) updated in ${agg.customers.filter(c => c.updated).length} customer(s)`);
    say('', `${nf(agg.unchanged_records)} matched record(s) already had the same values \u2013 left as they are`);
    if (agg.not_found_total) say('bad', `${nf(agg.not_found_total)} CCIDNO(s) from the file were not found in any customer`);
    if (agg.created_columns.length) say('', `New column(s) created: ${agg.created_columns.join(', ')}`);
    const act = el('div', 'actions'), close = el('button', 'btn', 'Close'); close.type = 'button'; close.onclick = closeModal; act.append(close); box.append(act);
    toast(`${agg.updated_records} record(s) updated \u2714`);
    logoFx('ok', 'SIM data pushed', `${nf(agg.updated_records)} record(s) updated \u00B7 ${agg.customers.filter(c => c.updated).length} customer(s)`);
    refreshAll();
  }

  function draw() {
    const head = el('div', 'cfhead'), ht = el('div');
    ht.append(el('h2', '', 'SIM Data Upload'), el('p', 'sub', 'Drop the Excel / CSV file from your SIM provider. Columns are detected by their headings, checked against every customer table automatically, and pushed to each record with the same CCIDNO. The only mandatory column is CCIDNO; empty cells never erase anything.'));
    head.append(el('span', 'cficon', '\uD83D\uDCF1'), ht);
    const kids = [head];

    const row = el('div', 'sb-row');
    const pw = el('label', 'lbl', 'SIM provider (saved in the SIM PROVIDER column of every matched record) ');
    pw.append(window.cvProviderSelect(st.prov, v => { st.prov = v; st.res = null; draw(); autoCheck(); })); row.append(pw);
    const ow = el('label', 'sb-check'), owi = document.createElement('input'); owi.type = 'checkbox'; owi.checked = st.overwrite;
    owi.onchange = () => { st.overwrite = owi.checked; st.res = null; draw(); autoCheck(); };
    ow.append(owi, el('span', '', 'Replace values that are different from the file (CCIDNO, MSISDN1, MSISDN2, ACT / EXP DATE, SIM provider). Values that are already the same are left as they are. Untick to fill empty cells only.'));
    row.append(ow); kids.push(row);

    const drop = el('label', 'drop'), fi = document.createElement('input');
    fi.type = 'file'; fi.accept = '.xlsx,.xls,.csv'; fi.hidden = true; fi.onchange = () => loadFile(fi.files[0]);
    drop.append(fi, el('b', '', '\u21EA'), el('span', '', st.file ? '\u2714 ' + st.file : 'Click or drag the provider\u2019s Excel (.xlsx / .xls / .csv) file here'));
    ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
    ['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
    drop.addEventListener('drop', e => loadFile(e.dataTransfer.files[0]));
    kids.push(drop);

    if (st.sheets.length) {
      const box = el('div', 'sb-cols'), chips = el('div', 'sb-chips');
      st.sheets.forEach(s => chips.append(el('span', 'sb-chip ' + (s.hi < 0 ? 'bad' : s.guessed ? '' : 'ok'), s.hi < 0 ? `${s.name}: skipped (no headings)` : s.guessed ? `${s.name}: ${s.count} row(s) \u2013 CCID heading not recognised, headings read from row ${s.hi + 1}` : `${s.name}: ${s.count} row(s)`)));
      FIELDS.forEach(([k, label]) => { const h = (st.heads || []).find(x => nrm(x) === st.map[k]); chips.append(el('span', 'sb-chip ' + (h ? 'ok' : ''), h ? `${label} \u2190 ${h}` : `${label}: not in file`)); });
      box.append(el('div', 'lblt', 'Columns detected'), chips, el('small', 'hint', !st.map.iccid ? 'The CCID column was not recognised. Every column of your file is listed below \u2013 choose the CCID column and the MSISDN / date columns.' : hasData() ? 'Matched automatically by heading. A column that was not found can be chosen below from all the columns of your file.' : 'Only CCIDNO was found. Choose the MSISDN / date columns below to continue.'));
      const grid = el('div', 'sb-row');
      FIELDS.forEach(([k, label, req]) => {
        const l = el('label', 'lbl', label + (req ? ' *' : '') + ' '), sel = el('select');
        sel.append(new Option(req ? '\u2014 choose the column \u2014' : '\u2014 not in file \u2014', '')); (st.heads || []).forEach(h => sel.append(new Option(h, nrm(h))));
        sel.value = st.map[k] || ''; sel.onchange = () => { st.map[k] = sel.value; st.res = null; draw(); autoCheck(); }; l.append(sel); grid.append(l);
      });
      box.append(grid); kids.push(box);
      if (st.busy && !st.res) kids.push(el('small', 'hint', 'Checking the file against your customers\u2026'));
    }

    const r = st.res;
    if (r) {
      const k = el('div', 'xkpis');
      [[r.provider_rows, 'rows in file', ''], [r.matched_iccids, 'CCIDNOs found in customers', 'good'], [r.matched_records, 'customer records matched', ''],
       [r.updated_records, r.dry_run ? 'records WILL be updated (different values)' : 'records updated', 'good'], [r.unchanged_records, 'already the same \u2013 left as they are', ''],
       [r.not_found_total, 'CCIDNOs in no customer', r.not_found_total ? 'warn' : '']].forEach(([n, t, c]) => k.append(kpi(n, t, c)));
      kids.push(el('h3', '', r.dry_run ? 'Check result \u2013 nothing has been saved' : '\u2714 Saved to the database'), k);
      const notes = [];
      if (r.skipped_rows) notes.push(`${r.skipped_rows} row(s) without a CCIDNO were skipped`);
      if (r.duplicate_iccids) notes.push(`${r.duplicate_iccids} CCIDNO(s) appear more than once in the file (their values were merged)`);
      if (r.bad_dates) notes.push(`${r.bad_dates} date(s) could not be read and were ignored`);
      if (r.created_columns && r.created_columns.length) notes.push((r.dry_run ? 'These columns do not exist yet and WILL be created in every customer table, then filled in each matched entry: ' : 'New column(s) created in every customer table and filled in each matched entry: ') + r.created_columns.join(', '));
      notes.forEach(n => kids.push(el('small', 'hint', '\u2022 ' + n)));
      if (r.customers.length) {   // which customer received how many records
        const FL = ["ICCID", "MSISDN1", "MSISDN2", "ACT DATE", "EXP DATE", "SIM PROVIDER"], wrap = el("div", "tablewrap xqres"), tbl = el("table"), hr = el("tr");
        ["#", "Customer", "Records matched", r.dry_run ? "Records to update" : "Records inserted", ...FL.map(f => f + " updated")].forEach(h => hr.append(el("th", "", h))); tbl.append(hr);
        r.customers.forEach((c, i) => { const tr = el("tr"); [i + 1, c.name, c.matched, c.updated, ...FL.map(f => (c.fields || {})[f] || 0)].forEach(v => tr.append(el("td", "", v))); tbl.append(tr); });
        const tot = el("tr"); tot.style.fontWeight = "700";
        ["", "Total (" + r.customers.length + " customer(s))", r.matched_records, r.updated_records, ...FL.map(f => r.customers.reduce((n, c) => n + ((c.fields || {})[f] || 0), 0))].forEach(v => tot.append(el("td", "", v))); tbl.append(tot);
        wrap.append(tbl); kids.push(el("h3", "", r.dry_run ? "Customers that will receive data" : "Inserted into these customers"), wrap);
      }
      if (r.sample.length) {
        const cols = ['ICCID', 'MSISDN1', 'MSISDN2', 'ACT DATE', 'EXP DATE', 'SIM PROVIDER'], wrap = el('div', 'tablewrap xqres'), tbl = el('table'), hr = el('tr');
        ['Customer', 'IMEI', 'CCIDNO', ...cols.map(c => c === 'ICCID' ? 'CCIDNO (new)' : c)].forEach(h => hr.append(el('th', '', h))); tbl.append(hr);
        r.sample.forEach(s => { const tr = el('tr'); [s.customer, s.imei || '-', s.iccid].forEach(v => tr.append(el('td', '', v)));
          cols.forEach(c => tr.append(el('td', '', s.changes[c] ? `${s.changes[c][0] || '\u2014'} \u2192 ${s.changes[c][1]}` : ''))); tbl.append(tr); });
        wrap.append(tbl); kids.push(el('small', 'hint', r.sample.length < r.updated_records ? `Showing the first ${r.sample.length} of ${r.updated_records} changes` : 'Changes (old \u2192 new)'), wrap);
      }
      const bar = el('div', 'xtools xpush'), left = el('span'), right = el('span'); right.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap';
      if (r.not_found_total) { const nf = el('button', 'btn ghost', `\u2B07 CCIDNOs not found (${r.not_found_total})`); nf.type = 'button';
        nf.onclick = () => exportData([['CCIDNO not found in any customer'], ...r.not_found.map(x => [x])], 'iccid_not_found_' + today()); right.append(nf); }
      if (r.dry_run && r.updated_records) { const go = el('button', 'btn', st.busy ? 'Pushing\u2026' : `\u2705 Push to customers (${r.updated_records} record(s))`); go.type = 'button'; go.disabled = st.busy; go.onclick = () => run(false); right.append(go); }
      else if (r.dry_run) left.textContent = 'Nothing to update - the matching records already have the same values.';
      bar.append(left, right); kids.push(bar);
    }
    panel.replaceChildren(...kids);
  }
})();

/* =====================================================================================================
   Cart - a tab right after Expiry Alerts. Everything deleted on the website (a whole customer, or one device record)
   waits here with its data. Restore puts it back; Delete Permanently asks TWICE and then erases it for good.
   Server: GET /api/trash, GET /api/trash/<id> (the data), POST /api/trash/<id>/restore, DELETE /api/trash/<id>.
   ===================================================================================================== */
(() => {
  const BLOCK = ['insert', 'customers', 'fetch', 'manage', 'alerts', 'xInventory', 'xSimData'];
  let items = [], open = new Set(), kindF = '', textF = '';

  const panel = Object.assign(el('section', 'panel card hidden'), { id: 'xCart' });
  const count = el('span', 'xcartn hidden', '0');
  const tab = Object.assign(el('button', 'xinvtab', '\uD83D\uDED2 Cart '), { id: 'cartTab', type: 'button' });
  tab.append(count);
  $('[data-tab=alerts]').after(tab);
  $('#alerts').after(panel);

  tab.onclick = () => {
    $$('.tab, .xinvtab').forEach(t => t.classList.remove('active'));
    BLOCK.forEach(p => { const n = $('#' + p); if (n) n.classList.add('hidden'); });
    tab.classList.add('active'); panel.classList.remove('hidden');
    tab.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' }); load();
  };
  document.addEventListener('click', e => { const t = e.target.closest('.tab, .xinvtab'); if (t && t !== tab) { tab.classList.remove('active'); panel.classList.add('hidden'); } });

  /* ---------- header + filters ---------- */
  const head = el('div', 'cfhead'), ht = el('div');
  ht.append(el('h2', '', 'Cart'), el('p', 'sub', 'Customers and device records you delete land here with all their data. Restore them, or delete them permanently.'));
  head.append(el('span', 'cficon', '\uD83D\uDED2'), ht);
  const bar = el('div', 'cfsearch'), kindSel = el('select'), txt = el('input'), sum = el('span', 'cfsum'), refresh = el('button', 'btn ghost small', '\u27F3 Refresh');
  kindSel.append(new Option('All items', ''), new Option('Customers', 'customer'), new Option('Device records', 'record'));
  txt.placeholder = 'Search the Cart (name, IMEI, deleted by)\u2026'; refresh.type = 'button';
  bar.append(kindSel, txt, sum, refresh);
  const wrap = el('div', 'tablewrap'), tbl = el('table'), empty = el('p', 'empty hidden');
  wrap.append(tbl); panel.append(head, bar, wrap, empty);

  kindSel.onchange = () => { kindF = kindSel.value; draw(); };
  txt.oninput = () => { textF = txt.value.trim().toLowerCase(); draw(); };
  refresh.onclick = () => load();

  /* ---------- data ---------- */
  async function load() {
    try { items = (await api('/trash')).items; } catch (e) { return toast(e.message, true); }
    open = new Set([...open].filter(id => items.some(i => i.id === id)));
    setCount(); draw();
  }
  function setCount() { count.textContent = items.length; count.classList.toggle('hidden', !items.length); }
  async function updateCount() { try { items = (await api('/trash', { quiet: true })).items; setCount(); } catch {} }

  function shown() {
    return items.filter(i => (!kindF || i.kind === kindF) &&
      (!textF || [i.customer, i.label, i.deleted_by, i.deleted_at].some(v => String(v || '').toLowerCase().includes(textF))));
  }

  function draw() {
    const list = shown();
    sum.textContent = items.length ? `${list.length} of ${items.length} item(s) in the Cart` : '';
    tbl.replaceChildren(); empty.classList.toggle('hidden', !!list.length); wrap.classList.toggle('hidden', !list.length);
    empty.textContent = items.length ? 'Nothing in the Cart matches this search.' : '\uD83D\uDED2 The Cart is empty. Deleted customers and device records will appear here.';
    if (!list.length) return;
    const th = el('thead'), hr = el('tr');
    ['#', 'Type', 'Name', 'Details', 'Deleted by', 'Deleted on', 'Actions'].forEach(h => hr.append(el('th', '', h))); th.append(hr); tbl.append(th);
    const tb = el('tbody');
    list.forEach((it, n) => {
      const isC = it.kind === 'customer', tr = el('tr');
      const tdT = el('td'); tdT.append(el('span', 'pill ' + (isC ? 'soft' : 'warn'), isC ? 'Customer' : 'Record'));
      const detail = isC ? `${it.records} device record${it.records === 1 ? '' : 's'}` : `from customer \u201C${it.customer}\u201D`;
      const tdA = el('td', 'xcartact'), view = el('button', 'btn ghost small', open.has(it.id) ? '\uD83D\uDE48 Hide Data' : '\uD83D\uDC41 View Data'),
        res = el('button', 'btn small xrestore', '\u21A9 Restore'), del = el('button', 'btn danger small', '\uD83D\uDDD1 Delete Permanently');
      [view, res, del].forEach(b => b.type = 'button');
      view.onclick = () => { open.has(it.id) ? open.delete(it.id) : open.add(it.id); draw(); };
      res.onclick = () => restore(it, res); del.onclick = () => confirmPurge(it);
      tdA.append(view, res, del);
      [n + 1].forEach(v => tr.append(el('td', '', v)));
      tr.append(tdT, el('td', 'xcartname', isC ? it.customer : it.label), el('td', '', detail), el('td', '', it.deleted_by || '-'), el('td', '', it.deleted_at), tdA);
      tb.append(tr);
      if (open.has(it.id)) {
        const dr = el('tr', 'xcartd'), dc = el('td'); dc.colSpan = 7; dc.append(el('p', 'sub', 'Loading data\u2026')); dr.append(dc); tb.append(dr);
        showData(it, dc);
      }
    });
    tbl.append(tb);
  }

  async function showData(it, cell) {
    let d; try { d = await api('/trash/' + it.id); } catch (e) { cell.replaceChildren(el('p', 'sub', e.message)); return; }
    cell.replaceChildren();
    if (d.missing) return cell.append(el('p', 'warnbox', '\u26A0 The saved table of this customer is not in MySQL any more, so there is no data to show or restore.'));
    const note = d.kind === 'customer'
      ? (d.total > d.shown ? `Showing the first ${d.shown} of ${d.total} records of \u201C${d.name}\u201D.` : `All ${d.total} record${d.total === 1 ? '' : 's'} of \u201C${d.name}\u201D.`)
      : `Device record deleted from customer \u201C${d.name}\u201D.`;
    cell.append(el('p', 'sub', note));
    const w = el('div', 'tablewrap xcartdata'), t = el('table'), h = el('tr');
    d.columns.forEach(c => h.append(el('th', '', c))); t.append(h);
    if (!d.rows.length) { const r = el('tr'), c = el('td', '', 'No records.'); c.colSpan = Math.max(d.columns.length, 1); r.append(c); t.append(r); }
    d.rows.forEach(row => { const r = el('tr'); row.forEach(v => r.append(el('td', '', v))); t.append(r); });
    w.append(t); cell.append(w);
  }

  /* ---------- restore ---------- */
  async function restore(it, btn) {
    btn.disabled = true;
    try {
      const r = await api('/trash/' + it.id + '/restore', { method: 'POST' });
      toast(`${r.restored === 'customer' ? `Customer \u201C${r.name}\u201D` : `Record ${r.label}`} restored \u2714`);
      logoFx('ok', 'Restored', r.restored === 'customer' ? `${r.name} \u00B7 ${r.records} record(s) are back` : `${r.label} is back in ${r.name}`, 1900);
      await refreshAll(); load();
    } catch (err) { btn.disabled = false; problem('Cannot restore', err.message); }
  }
  function problem(title, msg) {
    const box = el('div'); box.append(el('h2', '', '\u26A0 ' + title), el('p', 'warnbox', msg));
    const act = el('div', 'actions'), ok = el('button', 'btn', 'OK'); ok.type = 'button'; ok.onclick = closeModal; act.append(ok); box.append(act);
    openModal('cartmsg', box); ok.focus();
  }

  /* ---------- delete permanently: TWO popups ---------- */
  function what(it) {
    return it.kind === 'customer' ? `customer \u201C${it.customer}\u201D and its ${it.records} device record${it.records === 1 ? '' : 's'}` : `device record ${it.label} (customer \u201C${it.customer}\u201D)`;
  }
  function confirmPurge(it) {   // popup 1 of 2
    const box = el('div'); box.append(el('h2', '', '\uD83D\uDDD1 Delete permanently?'));
    const m = el('div', 'dupbox'); m.append('You are about to permanently delete the ', el('b', '', what(it)), ' from the Cart.'); box.append(m);
    box.append(el('p', 'sub', 'After this it can no longer be restored.'));
    const act = el('div', 'actions'), no = el('button', 'btn ghost', 'Cancel'), go = el('button', 'btn danger', 'Continue \u2192');
    no.type = go.type = 'button'; no.onclick = closeModal; go.onclick = () => finalPurge(it);
    act.append(no, go); box.append(act); openModal('cartdel1', box); no.focus();
  }
  function finalPurge(it) {   // popup 2 of 2
    const box = el('div'); box.append(el('h2', '', '\u26A0 Final warning \u2013 are you sure?'));
    box.append(el('p', 'warnbox', `This permanently erases the ${what(it)} from the database. This CANNOT be undone and there is no way to get it back.`));
    const act = el('div', 'actions'), no = el('button', 'btn ghost', 'No, keep it in the Cart'), go = el('button', 'btn danger', '\uD83D\uDDD1 Yes, delete permanently');
    no.type = go.type = 'button'; no.onclick = closeModal;
    go.onclick = async () => {
      go.disabled = true; go.style.opacity = .6;
      try {
        const r = await api('/trash/' + it.id, { method: 'DELETE', body: { name: it.customer } });
        closeModal(); toast(`${r.kind === 'customer' ? `Customer \u201C${r.name}\u201D` : `Record ${r.label}`} deleted permanently \u2714`);
        logoFx('ok', 'Deleted permanently', r.kind === 'customer' ? `${r.name} \u00B7 ${r.records} record(s) erased` : `${r.label} erased`, 1900); load();
      } catch (err) { go.disabled = false; go.style.opacity = 1; toast(err.message, true); }
    };
    act.append(no, go); box.append(act); openModal('cartdel2', box); no.focus();
  }

  /* ---------- keep the tab's number current after every refresh of the site ---------- */
  const _refreshAll = refreshAll;
  refreshAll = async function (...a) { const r = await _refreshAll.apply(this, a); updateCount(); return r; };
})();

/* =====================================================================================================
   Manage Users - only the admin sees this button. Lists every registered employee and removes accounts.
   Server: GET /api/users, DELETE /api/users/<employee id>   (both refused for everybody who is not an admin).
   ===================================================================================================== */
(() => {
  const btn = el('button', 'btn ghost', '\uD83D\uDC65 Manage Users'); btn.type = 'button'; btn.id = 'usersBtn';
  btn.title = 'See every registered user and remove accounts (admin only)';
  $('#logout').before(btn);
  async function open() {
    const box = el('div'); box.append(el('h2', '', '\uD83D\uDC65 Manage Users'));
    box.append(el('p', 'sub', 'Removing a user deletes the account and signs that person out. The records they added stay in the customer tables.'));
    const add = el('div', 'actions'), nn = el('input'), ni = el('input'), np = el('input'), nb = el('button', 'btn', '\u2795 Add Member');
    nn.placeholder = 'Employee name'; ni.placeholder = 'Employee ID'; np.placeholder = 'Password (min 6)'; np.type = 'password'; nb.type = 'button';
    [nn, ni, np].forEach(i => { i.autocomplete = 'off'; i.style.flex = '1 1 140px'; }); add.style.flexWrap = 'wrap'; add.style.gap = '8px';
    nb.onclick = async () => {
      try {
        const r = await api('/users', { method: 'POST', body: { name: nn.value, emp_id: ni.value, password: np.value } });
        toast(`Member \u201C${r.name}\u201D added as admin \u2714`); nn.value = ni.value = np.value = ''; load();
      } catch (e) { toast(e.message, true); }
    };
    add.append(nn, ni, np, nb); box.append(el('p', 'sub', 'Add Member: anyone you add here gets full ADMIN access.'), add);
    const wrap = el('div', 'tablewrap xqres xusers'); box.append(wrap);
    const act = el('div', 'actions'), close = el('button', 'btn', 'Close'); close.type = 'button'; close.onclick = closeModal;
    act.append(el('span'), close); box.append(act);
    async function load() {
      let items; try { items = (await api('/users')).items; } catch (e) { return toast(e.message, true); }
      const t = el('table'), hr = el('tr');
      ['#', 'Name', 'Employee ID', 'Access', 'Registered', ''].forEach(h => hr.append(el('th', '', h))); t.append(hr);
      items.forEach((u, i) => {
        const tr = el('tr'), self = me && String(u.id) === String(me.id), b = el('button', 'btn ghost small dng', '\uD83D\uDDD1 Remove'); b.type = 'button';
        const isBoss = me && String(me.id) === '0001', target0001 = String(u.id) === '0001';
        b.disabled = self || !isBoss || target0001;
        b.title = target0001 ? 'The main administrator (ID 0001) cannot be removed' : !isBoss ? 'Only ID 0001 can remove users' : self ? 'You cannot remove your own account' : '';
        b.onclick = async () => {
          if (!confirm(`Remove the user "${u.name}" (ID ${u.id})? This cannot be undone.`)) return;
          try { await api('/users/' + encodeURIComponent(u.id), { method: 'DELETE' }); toast(`User "${u.name}" removed \u2714`); load(); }
          catch (e) { toast(e.message, true); }
        };
        const bt = el('td'); bt.append(b);
        [i + 1, u.name + (self ? ' (you)' : ''), u.id, u.role, u.created_at].forEach(v => tr.append(el('td', self ? 'me' : '', v))); tr.append(bt); t.append(tr);
      });
      wrap.replaceChildren(t);
    }
    $('#mbox').classList.add('wide'); openModal('users', box); load();
  }
  btn.onclick = open;
})();



/* =====================================================================================================
   Upload by Sheet Name - LIMITED USE (2 times), then it is removed from the website
   * every sheet of the Excel file = one customer; the SHEET NAME is the customer name (exactly as written, no file-name rule).
   * a customer that does not exist yet is created automatically in MySQL (own table) and on the website; an existing one just gets the rows.
   * every column of the sheet is saved as it is (new columns are created); rows already saved are skipped, never overwritten.
   * the number of uses left is kept on the SERVER (app_state), so it is shared by everyone and survives restarts / other browsers.
     After the last use the button is hidden and the server refuses the request too.
   * the old [Bulk Upload] is not touched.   Server: POST /api/devices/sheet-upload   (admin / staff only)
   ===================================================================================================== */
(() => {
  const btn = $('#cmSheetUp'), leftTxt = $('#cmSheetLeft'), CHUNK = 400;
  if (!btn) return;
  const CUST_HDR = /^(customer|client)([ _]?name)?$/i;
  const fmt = n => Number(n || 0).toLocaleString();
  const norm = s => String(s || '').replace(/\s+/g, ' ').trim();
  let wb = null, file = '', sheets = [], dupMode = 'skip';

  const left = () => Number((BOOT && BOOT.sheet_upload_left) ?? 0);
  function syncBtn() {   // shown only while uses are left
    const n = left();
    btn.classList.toggle('hidden', n <= 0);
    leftTxt.textContent = n > 0 ? `(${n} use${n === 1 ? '' : 's'} left)` : '';
  }
  const _refreshAll = refreshAll;   // keep the button in step with the database every time the page data reloads
  refreshAll = async function (...a) { const r = await _refreshAll.apply(this, a); syncBtn(); return r; };
  syncBtn();

  function readSheet(name) {   // -> { name, hdr, rows:[{label:value}] }
    const ws = wb.Sheets[name];
    const raw = XLSX.utils.sheet_to_json(ws, { header: 1, raw: true, defval: '' });
    const txt = XLSX.utils.sheet_to_json(ws, { header: 1, raw: false, dateNF: 'yyyy-mm-dd', defval: '' });
    const g = raw.map((r, ri) => r.map((v, ci) => bfCell(v, (txt[ri] || [])[ci]))).filter(r => r.some(x => x));
    const rows = [];
    if (g.length >= 2) g.slice(1).forEach(cells => {
      const f = {};
      g[0].forEach((h, i) => {
        const v = String(cells[i] ?? '').trim(); if (!h || !v || CUST_HDR.test(String(h).trim())) return;
        const l = canonCol(h); if (!(l in f)) f[l] = isDate(l) ? (toISO(v) || v) : v;
      });
      if (Object.keys(f).length) rows.push(f);
    });
    return { name: norm(name), rows };
  }

  function loadFile(f) {
    if (!f) return;
    if (!/\.(xlsx|xls)$/i.test(f.name)) return toast('Only Excel files (.xlsx, .xls) are allowed', true);
    if (!window.XLSX) return toast('Excel reader could not load - check your internet connection', true);
    const rd = new FileReader();
    rd.onload = () => {
      try {
        wb = XLSX.read(rd.result, { type: 'array', cellDates: true }); file = f.name;
        sheets = wb.SheetNames.map(readSheet);
      } catch { wb = null; file = ''; sheets = []; toast('Could not read this Excel file', true); }
      stepForm();
    };
    rd.readAsArrayBuffer(f);
  }

  function stepForm() {
    const box = el('div', 'sb'), head = el('div', 'sb-head');
    head.append(el('h2', '', '\uD83D\uDCD1 Upload by Sheet Name')); box.append(head);
    const n = left();
    box.append(el('p', 'sub', 'Every sheet of the Excel file becomes a customer: the sheet name is the customer name. A customer that does not exist yet is created automatically in the database and on the website.'));
    box.append(el('p', 'sb-msg', `\u26A0 This feature can be used only ${n} more time${n === 1 ? '' : 's'}. After that it is removed from the website. Only an upload that saves records counts as a use.`));
    const g = el('div', 'bu-grid sb-grid'); box.append(g);

    const drop = el('label', 'drop'), fi = document.createElement('input');
    fi.type = 'file'; fi.accept = '.xlsx,.xls'; fi.hidden = true; fi.onchange = () => loadFile(fi.files[0]);
    drop.append(fi, el('b', '', '\u21EA'), el('span', '', file ? '\u2714 ' + file : 'Click or drag an Excel (.xlsx / .xls) file here'));
    ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
    ['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
    drop.addEventListener('drop', e => loadFile(e.dataTransfer.files[0]));
    g.append(drop);

    const use = sheets.filter(s => s.rows.length), empty = sheets.length - use.length;
    if (sheets.length) {
      const have = new Set(BOOT.customers.map(c => c.name.toLowerCase()));
      const sp = el('div', 'sb-cols sb-sheets'), list = el('div', 'sb-shlist');
      sp.append(el('div', 'lblt', `${use.length} sheet(s) will be uploaded \u2192 ${use.length} customer(s)` + (empty ? ` \u00B7 ${empty} empty sheet(s) skipped` : '')));
      sheets.forEach(s => {
        const row = el('div', 'sb-sh' + (s.rows.length ? '' : ' off'));
        const state = !s.rows.length ? 'empty \u2013 no data rows' : `${fmt(s.rows.length)} row(s) \u00B7 ` + (have.has(s.name.toLowerCase()) ? 'existing customer' : 'NEW customer will be created');
        row.append(el('span', '', s.name || '(no name)'), el('small', '', state)); list.append(row);
      });
      sp.append(list); g.append(sp);
    }
    if (sheets.length) {   // rows that already exist in the database: keep the saved values or replace them
      const q = el('div', 'sb-cols');
      q.append(el('div', 'lblt', 'If a record of the file already exists in the database (same Device Sr No / IMEI / ICCID):'));
      [['skip', 'Keep the existing values (the row is skipped)'], ['replace', 'Replace the existing values with the values from the file (a blank cell never erases a saved value)']].forEach(([v, t]) => {
        const l = el('label', 'sb-sh'), r = document.createElement('input'); r.type = 'radio'; r.name = 'ss-dupmode'; r.checked = dupMode === v;
        r.onchange = () => { dupMode = v; }; l.append(r, el('span', '', t)); q.append(l);
      });
      g.append(q);
    }
    const act = el('div', 'actions'), cancel = el('button', 'btn ghost', 'Cancel'), go = el('button', 'btn', 'Upload \u2192');
    cancel.type = go.type = 'button'; cancel.onclick = closeModal; go.disabled = !use.length;
    go.onclick = () => {
      if (!use.length) return toast(sheets.length ? 'No sheet has a heading row and at least one data row' : 'Upload an Excel file first', true);
      if (confirm(`Upload ${use.length} sheet(s) as customers?\n\nThis uses one of the ${left()} remaining use(s) of this feature.`)) run(use);
    };
    act.append(cancel, go); box.append(act); $('#mbox').classList.add('wide'); openModal('bulk', box);
  }

  async function run(use) {
    const parts = [], total = use.reduce((t, s) => t + s.rows.length, 0);
    use.forEach(s => { for (let i = 0; i < s.rows.length; i += CHUNK) parts.push({ customer: s.name, rows: s.rows.slice(i, i + CHUNK), size: s.rows.length }); });
    const box = el('div', 'up'), title = el('h2', '', 'Uploading\u2026'), stage = el('p', 'sb-msg', ''), line = el('p', 'sub', '');
    const bar = el('div', 'up-bar'), fill = el('i'), pct = el('span', 'up-pct', '0%'), wrap = el('div', 'up-barwrap'), log = el('div', 'up-log');
    bar.append(fill); wrap.append(bar, pct);
    box.append(title, stage, wrap, line, el('p', 'hint', 'Please keep this window open until the upload finishes.'), log); openModal('bulk', box);
    const say = (cls, t) => { log.append(el('div', 'up-l ' + cls, t)); log.scrollTop = log.scrollHeight; };
    let done = 0, imported = 0, updated = 0, skipped = 0, newCust = 0; const per = new Map();
    const progress = () => { const p = total ? Math.min(100, Math.round(done / total * 100)) : 100; fill.style.width = p + '%'; pct.textContent = p + '%'; line.textContent = `${fmt(done)} of ${fmt(total)} records processed \u00B7 ${fmt(imported)} added` + (dupMode === 'replace' ? ` \u00B7 ${fmt(updated)} replaced` : '') + ` \u00B7 ${fmt(skipped)} skipped`; };
    progress();
    try {
      for (let i = 0; i < parts.length; i++) {
        const p = parts[i], last = i === parts.length - 1;
        stage.textContent = `\uD83D\uDCE4 Uploading \u201C${p.customer}\u201D`;
        // the last part tells the server to use up one of the allowed uses; the server only counts it if the upload saved records
        const r = await api('/devices/sheet-upload', { method: 'POST', body: { groups: [{ customer: p.customer, rows: p.rows }], finish: last, saved_before: imported + updated > 0, on_duplicate: dupMode } });
        done += p.rows.length; imported += r.imported || 0; updated += r.updated || 0; skipped += r.skipped || 0;
        newCust += Array.isArray(r.new_customers) ? r.new_customers.length : (+r.new_customers || 0);
        const c = per.get(p.customer) || { sent: 0, added: 0 }; c.sent += p.rows.length; c.added += (r.imported || 0) + (r.updated || 0); per.set(p.customer, c);
        if (c.sent >= p.size) say('ok', `\u2714 ${p.customer} \u2013 ${fmt(c.added)} of ${fmt(p.size)} record(s) saved`);
        progress();
      }
    } catch (err) {
      stage.textContent = '\u274C The upload stopped'; title.textContent = 'Upload failed';
      say('bad', `\u2716 ${err.message || 'Upload failed'}`); say('', `${fmt(imported + updated)} record(s) were saved or replaced before the problem. The upload did not use up one of the allowed uses.`);
      const act = el('div', 'actions'), close = el('button', 'btn', 'Close'); close.type = 'button'; close.onclick = closeModal; act.append(close); box.append(act);
      await refreshAll(); return;
    }
    stage.textContent = '\u2705 Finished'; title.textContent = 'Upload Completed'; fill.style.width = '100%'; pct.textContent = '100%';
    await refreshAll();   // reloads customers / counters and hides this button when no use is left
    const n = left();
    say('', imported || updated ? `${fmt(imported)} record(s) added` + (updated ? ` \u00B7 ${fmt(updated)} existing record(s) replaced` : '') + ` \u00B7 ${newCust} new customer(s) \u00B7 ${fmt(skipped)} duplicate(s) skipped` : 'Nothing new was saved (all rows were already in the database) \u2013 this did not use up one of the allowed uses.');
    say('', n > 0 ? `This feature can be used ${n} more time${n === 1 ? '' : 's'}.` : 'This was the last use \u2013 the feature has been removed from the website.');
    const act = el('div', 'actions'), close = el('button', 'btn', 'Close'); close.type = 'button'; close.onclick = closeModal; act.append(close); box.append(act);
  }

  btn.onclick = () => { if (left() <= 0) return syncBtn(); wb = null; file = ''; sheets = []; stepForm(); };
})();
