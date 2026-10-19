/* CustomerVault - front end.
   All data lives in the MySQL database managed by app.py (see database.py).
   Start the server with:  python app.py   and open http://localhost:8000 */

const $ = s => document.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const QUICK = ['IMEI', 'DISPATCHED DATE', 'EXP DATE'];            // the "quick view" in Fetch
const DATE_COLS = ['ACT DATE', 'EXP DATE', 'DISPATCHED DATE'];
const ALIAS = { devicesrno: 'Device Sr No', deviceserialno: 'Device Sr No', pcbno: 'Device Sr No', pcbnumber: 'Device Sr No', pcbsrno: 'Device Sr No', pcbserialno: 'Device Sr No', pcb: 'Device Sr No', imei: 'IMEI', imeinumber: 'IMEI', imeino: 'IMEI', iccid: 'ICCID', ccidno: 'ICCID', ccid: 'ICCID', ccidnumber: 'ICCID', iccidno: 'ICCID', iccidnumber: 'ICCID',
  msisdn1: 'MSISDN1', msisdn2: 'MSISDN2', actdate: 'ACT DATE', activationdate: 'ACT DATE', expdate: 'EXP DATE', expirydate: 'EXP DATE',
  expirationdate: 'EXP DATE', dispatcheddate: 'DISPATCHED DATE', dispatchdate: 'DISPATCHED DATE', model: 'MODEL', simprovider: 'SIM PROVIDER',
  flash: 'FLASH', firmware: 'FIRMWARE', firmwareversion: 'FIRMWARE', activationplan: 'ACTIVATION PLAN', actplan: 'ACTIVATION PLAN', plan: 'ACTIVATION PLAN', simplan: 'ACTIVATION PLAN' };
const canonCol = n => ALIAS[String(n).toLowerCase().replace(/[^a-z0-9]/g, '')] || String(n).replace(/\s+/g, ' ').trim();
const MON = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
function toISO(str) { // understands 2026-09-20, 15-Feb-25, 15/02/2025 (day first) -> "2026-09-20"
  const t = String(str).trim(); let y, m, d, x;
  if ((x = t.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/))) [y, m, d] = [+x[1], +x[2], +x[3]];
  else if ((x = t.match(/^(\d{1,2})[-\/ ]([A-Za-z]{3})[a-z]*[-\/ ,]*(\d{2,4})$/)) && MON[x[2].toLowerCase()]) [d, m, y] = [+x[1], MON[x[2].toLowerCase()], +x[3]];
  else if ((x = t.match(/^(\d{1,2})[-\/.](\d{1,2})[-\/.](\d{2,4})$/))) [d, m, y] = [+x[1], +x[2], +x[3]];
  else return null;
  if (y < 100) y += 2000;
  const dt = new Date(Date.UTC(y, m - 1, d));
  return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d ? dt.toISOString().slice(0, 10) : null;
}

/* ---------- state + server access ---------- */
let prefillIMEI = '', bT = 'auto', pendingFile = '', mLast = null, mItems = [];
let me = null, token = sessionStorage.getItem('cv_token'), results = [], sel = null, pending = null, lastSearch = null, FSIM = '';
let BOOT = { customers: [], columns: [], stats: { customers: 0, devices: 0, mine: 0, columns: 0 } };   // refreshed from the database
const STD = () => BOOT.columns.map(c => c.label);                        // every column in the database (mandatory first)
const MAND = () => BOOT.columns.filter(c => c.mandatory).map(c => c.label);
const hasCol = (r, c) => Object.prototype.hasOwnProperty.call(r.fields || {}, c);
const colsOf = items => STD().filter(c => items.some(r => hasCol(r, c)));   // only the columns that belong to the customers in these records
const isDate = n => { const c = BOOT.columns.find(x => same(x.label, n)); return c ? c.is_date : DATE_COLS.includes(n); };
const today = () => new Date().toLocaleDateString('en-CA');   // LOCAL date (toISOString is UTC: wrong day before 05:30 in India)
const same = (a, b) => String(a).trim().toLowerCase() === String(b).trim().toLowerCase();
const custName = (cl, id) => (cl.find(c => String(c.id) === String(id)) || { name: '(deleted)' }).name;

let busyN = 0, busyT = 0;   // spinning logo in the corner while the server is working
function busy(d) {
  busyN = Math.max(0, busyN + d); clearTimeout(busyT);
  if (busyN) busyT = setTimeout(() => $('#busy').classList.remove('hidden'), 450); else $('#busy').classList.add('hidden');
}
function api(path, o = {}) { busy(1); return _api(path, o).finally(() => busy(-1)); }
async function _api(path, o = {}) {
  let res;
  try {
    res = await fetch((window.API_BASE || '') + '/api' + path, { method: o.method || 'GET', body: o.body ? JSON.stringify(o.body) : undefined,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) } });
  } catch { throw new Error('Cannot reach the server - start it with:  python backend/main.py'); }
  let data = {}; try { data = await res.json(); } catch {}
  if (res.status === 401 && token && !o.quiet && !['/login', '/register'].includes(path)) expire();
  if (!res.ok) { const e = new Error(data.error || 'Server error'); e.data = data; throw e; }
  return data;
}
function expire() {
  token = null; sessionStorage.removeItem('cv_token'); me = null; clearInterval(expTimer); closeModal();
  $('#appView').classList.add('hidden'); $('#authView').classList.remove('hidden');
  toast('Session expired - please login again', true);
}

/* ---------- helpers ---------- */
function toast(msg, err) {
  const t = document.createElement('div');
  t.className = 't' + (err ? ' err' : ''); t.textContent = msg;
  $('#toast').append(t); setTimeout(() => t.remove(), 3500);
  if (!err && /\u2714|saved/i.test(msg)) { const r = t.getBoundingClientRect(); burst(r.left + 24, r.top + r.height / 2); }
  // every event gets the logo animation: green message = success, red message = not successful.
  // (actions that already played a richer logo animation call logoFx themselves, so this is skipped for them)
  const t0 = Date.now(), clean = String(msg).replace(/[\u2714\u2705\uD83D\uDD14\uD83D\uDD15]/g, '').trim().slice(0, 140);
  setTimeout(() => {
    if (fxAt > t0 - 1500) return;
    if (err) logoFx('fail', 'Not successful', clean, 2200); else logoFx('ok', 'Done!', clean, 1700);
  }, 180);
}
function shake(el) { el.classList.remove('shake'); void el.offsetWidth; el.classList.add('shake'); }
function countUp(el, to) {
  const from = +el.textContent || 0, t0 = performance.now();
  (function step(t) {
    const p = Math.min((t - t0) / 700, 1);
    el.textContent = Math.round(from + (to - from) * p);
    if (p < 1) requestAnimationFrame(step);
  })(t0);
}
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };

/* ---------- button ripple + card tilt ---------- */
document.addEventListener('click', e => {
  const b = e.target.closest('.btn'); if (!b) return;
  const r = b.getBoundingClientRect(), s = document.createElement('span'), d = Math.max(r.width, r.height);
  s.className = 'ripple'; s.style.cssText = `width:${d}px;height:${d}px;left:${e.clientX - r.left - d / 2}px;top:${e.clientY - r.top - d / 2}px`;
  b.append(s); setTimeout(() => s.remove(), 600);
});
const ac = $('#authCard');

/* ---------- auth ---------- */
$('#toReg').onclick = e => { e.preventDefault(); $('#loginForm').classList.add('hidden'); $('#regForm').classList.remove('hidden'); };
$('#toLogin').onclick = e => { e.preventDefault(); $('#regForm').classList.add('hidden'); $('#loginForm').classList.remove('hidden'); };

/* ----- password strength + live "name / ID already taken?" hints ----- */
function strength(pw) {
  if (!pw) return { pct: 0, label: '', color: 'var(--line)' };
  let n = 0; if (pw.length >= 6) n++; if (pw.length >= 10) n++; if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) n++; if (/\d/.test(pw)) n++; if (/[^A-Za-z0-9]/.test(pw)) n++;
  n = Math.min(n, 4);
  return { pct: [12, 30, 55, 80, 100][n], label: ['Too weak', 'Weak', 'Okay', 'Good', 'Strong'][n], color: ['var(--err)', 'var(--err)', 'var(--warn)', 'var(--ok)', 'var(--ok)'][n] };
}
function bindMeter(inp, bar, lab) {
  inp.addEventListener('input', () => { const r = strength(inp.value); bar.style.width = r.pct + '%'; bar.style.background = r.color; lab.textContent = r.label ? 'Password strength: ' + r.label : ''; });
}
function addEye(f) {
  const inp = f.querySelector('input[type=password]'); if (!inp || f.querySelector('.eye')) return;
  const b = el('button', 'eye', '\uD83D\uDC41'); b.type = 'button'; b.title = 'Show / hide password'; b.setAttribute('aria-label', 'Show or hide password');
  b.onclick = () => { const show = inp.type === 'password'; inp.type = show ? 'text' : 'password'; b.textContent = show ? '\uD83D\uDE48' : '\uD83D\uDC41'; inp.focus(); };
  f.append(b);
}
bindMeter($('#rPass'), $('#rMeter'), $('#rMeterLbl'));
let availT = 0;
function checkAvail() {
  clearTimeout(availT);
  const name = $('#rName').value.trim(), id = $('#rId').value.trim(), nh = $('#rNameHint'), ih = $('#rIdHint');
  if (!name && !id) { nh.textContent = ih.textContent = ''; return; }
  availT = setTimeout(async () => {
    try {
      const r = await api('/check-user?' + new URLSearchParams({ name, emp_id: id }));
      const set = (h, v, taken, what) => { if (!v) { h.textContent = ''; return; } h.textContent = taken ? `\u2716 This ${what} is already registered` : `\u2714 ${what[0].toUpperCase() + what.slice(1)} is available`; h.className = 'fhint ' + (taken ? 'bad' : 'ok'); };
      set(nh, name, r.name_taken, 'name'); set(ih, id, r.id_taken, 'ID');
    } catch {}
  }, 350);
}
$('#rName').addEventListener('input', checkAvail); $('#rId').addEventListener('input', checkAvail);

function confirmUsername(name, id, onOk) {   // alert for a new user: the username is permanent
  const box = el('div'); box.append(el('h2', '', '\u26A0 Read before you continue'));
  [['Employee Name', name], ['Employee ID', id]].forEach(([k, v]) => { const p = el('p', 'line'); p.append(k + ': ', el('b', '', v)); box.append(p); });
  const ul = el('ul', 'rules');
  ['You can create only ONE username.', 'Your Employee Name and Employee ID can NEVER be changed after this.', 'Only your password can be changed later (use \uD83D\uDD11 Password after login).']
    .forEach(t => ul.append(el('li', '', t)));
  box.append(ul);
  const chk = el('label', 'chk agree'), cb = el('input'); cb.type = 'checkbox'; chk.append(cb, ' I understand and want to create this account'); box.append(chk);
  const act = el('div', 'actions'), back = el('button', 'btn ghost', '\u2190 Go Back & Edit'), ok = el('button', 'btn', '\u2714 Create My Account');
  back.type = ok.type = 'button'; ok.disabled = true;
  cb.onchange = () => ok.disabled = !cb.checked;
  back.onclick = closeModal; ok.onclick = () => { closeModal(); onOk(); };
  act.append(back, ok); box.append(act); openModal('confirm', box);
}
$('#regForm').onsubmit = async e => {
  e.preventDefault();
  const name = $('#rName').value.trim(), id = $('#rId').value.trim(), p1 = $('#rPass').value, p2 = $('#rPass2').value;
  if (p1 !== p2) { shake(ac); logoFx('fail', 'Passwords do not match', 'Type the same password twice', 1300); return toast('Passwords do not match', true); }
  try {
    const r = await api('/check-user?' + new URLSearchParams({ name, emp_id: id }));
    if (r.name_taken || r.id_taken) { shake(ac); checkAvail(); return toast(`This Employee ${r.id_taken ? 'ID' : 'Name'} is already registered - each person can have only one username`, true); }
  } catch (err) { return toast(err.message, true); }
  confirmUsername(name, id, async () => {
    try { await api('/register', { method: 'POST', body: { name, emp_id: id, password: p1 } }); }
    catch (err) { shake(ac); logoFx('fail', 'Could not create account', err.message, 1800); return toast(err.message, true); }
    logoFx('ok', 'Account created!', `Your username "${id}" is now permanent. Please log in.`, 2200);
    $('#regForm').reset(); $('#rMeter').style.width = '0'; $('#rMeterLbl').textContent = ''; $('#rNameHint').textContent = $('#rIdHint').textContent = '';
    $('#toLogin').click(); $('#lUser').value = id; $('#lPass').focus();
  });
};

/* ----- LOGO EFFECT: success / wrong password / goodbye ----- */
let fxTimer = 0, fxAt = 0;   // fxAt = when the logo animation last played
function hideFx() { clearTimeout(fxTimer); $('#logoFx').classList.remove('show'); }
function logoFx(kind, title, sub, ms = 1600) {   // kind: ok | fail | bye
  const f = $('#logoFx'); clearTimeout(fxTimer); fxAt = Date.now();
  f.className = 'logofx ' + kind; void f.offsetWidth;   // restart the animation every time
  $('#fxTitle').textContent = title; $('#fxSub').textContent = sub || '';
  $('#fxBadge').textContent = kind === 'ok' ? '\u2714' : kind === 'fail' ? '\u2716' : '\uD83D\uDC4B';
  f.classList.add('show');
  if (kind === 'ok') setTimeout(() => { const r = $('#fxLogo').getBoundingClientRect(); burst(r.left + r.width / 2, r.top + r.height / 2); }, 650);
  fxTimer = setTimeout(hideFx, ms);
}
$('#logoFx').onclick = hideFx;
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideFx(); });

$('#loginForm').onsubmit = async e => {
  e.preventDefault();
  try {
    const r = await api('/login', { method: 'POST', body: { user: $('#lUser').value, password: $('#lPass').value } });
    token = r.token; sessionStorage.setItem('cv_token', token); e.target.reset();
    logoFx('ok', `Welcome, ${r.employee.name}!`, 'Login successful \u2013 opening your portal\u2026', 1900);
    enter(r.employee);
  } catch (err) {
    shake(ac); ac.classList.add('denied'); setTimeout(() => ac.classList.remove('denied'), 1200);
    logoFx('fail', /invalid/i.test(err.message) ? 'Access denied' : 'Cannot sign in', /invalid/i.test(err.message) ? 'Wrong Employee ID / Name or password' : err.message, 1700);
    toast(err.message, true); $('#lPass').value = ''; $('#lPass').focus();
  }
};

/* ----- change password (the username itself can never be changed) ----- */
function changePasswordModal() {
  const box = el('div'); box.append(el('h2', '', '\uD83D\uDD11 Change Password'));
  box.append(el('p', 'sub', `Signed in as ${me.name} (${me.id}). Your username is permanent \u2013 only the password can be changed.`));
  const form = el('form', 'form');
  const mkf = (label, ac) => { const f = el('label', 'field'), i = el('input'); i.type = 'password'; i.placeholder = ' '; i.autocomplete = ac; i.required = true; f.append(i, el('span', '', label)); addEye(f); return [f, i]; };
  const [f1, cur] = mkf('Current password', 'current-password'), [f2, nw] = mkf('New password (min 6 chars)', 'new-password'), [f3, cf] = mkf('Confirm new password', 'new-password');
  const meter = el('div', 'meter'), bar = el('i'), lab = el('small', 'mlabel'); meter.append(bar); bindMeter(nw, bar, lab);
  const act = el('div', 'actions'), cancel = el('button', 'btn ghost', 'Cancel'), ok = el('button', 'btn', '\uD83D\uDD11 Update Password');
  cancel.type = 'button'; cancel.onclick = closeModal; act.append(cancel, ok);
  form.append(f1, f2, meter, lab, f3, act); box.append(form);
  form.onsubmit = async ev => {
    ev.preventDefault();
    if (nw.value.length < 6) { shake(f2); return toast('New password must be at least 6 characters', true); }
    if (nw.value !== cf.value) { shake(f3); return toast('The new passwords do not match', true); }
    if (nw.value === cur.value) { shake(f2); return toast('The new password must be different from the current one', true); }
    ok.disabled = true;
    try { await api('/change-password', { method: 'POST', body: { current: cur.value, new: nw.value } }); }
    catch (err) { ok.disabled = false; shake(f1); logoFx('fail', 'Password not changed', err.message, 1600); return toast(err.message, true); }
    closeModal(); logoFx('ok', 'Password updated!', 'Use your new password the next time you log in.', 1900); toast('Password changed \u2714');
  };
  openModal('pw', box); cur.focus();
}
$('#chgPw').onclick = changePasswordModal;

const LIM = () => !!me && me.role !== 'admin' && me.role !== 'staff' && me.role !== 'standard';   // 'limited' users: fetch / insert / edit details only
async function enter(emp) {
  me = emp; document.body.dataset.role = LIM() ? 'limited' : (emp.role || 'staff'); sel = null; lastSearch = null; results = [];
  $('#resultHead').classList.add('hidden'); $('#empty').classList.add('hidden'); $('#resultTable').innerHTML = '';
  $('#authView').classList.add('hidden'); $('#appView').classList.remove('hidden');
  { const hr = new Date().getHours(); $('#hello').textContent = `${hr < 12 ? 'Good morning' : hr < 17 ? 'Good afternoon' : 'Good evening'}, ${emp.name} \uD83D\uDC4B`; $('#hello').title = 'Employee ID: ' + emp.id; }
  alertsOn = pref('cv_alerts_on', true); lastActive = Date.now(); paintAlertUi();
  await refreshAll();
  offerMigration();         // data saved in this browser by the old version -> database
  startExpiryReminders();   // popup now, then again every 5 minutes while devices are still due
}
$('#logout').onclick = () => {
  api('/logout', { method: 'POST', quiet: true }).catch(() => {});
  token = null; sessionStorage.removeItem('cv_token'); me = null; clearInterval(expTimer); expiryDeferred = false; closeModal();
  $('#appView').classList.add('hidden'); $('#authView').classList.remove('hidden');
  logoFx('bye', 'See you soon!', 'You have been logged out safely.', 1300);
};

/* ---------- keep the website in step with the MySQL database ---------- */
let bootSig = '';
const bootSigOf = b => JSON.stringify([b.customers, b.columns, b.stats]);
async function syncFromDb() {   // every few seconds: if customers / counts / columns changed in MySQL, redraw the whole site
  if (!token || !me || document.hidden) return;
  const tag = (document.activeElement && document.activeElement.tagName) || '';
  if (!$('#modal').classList.contains('hidden') || /^(INPUT|SELECT|TEXTAREA)$/.test(tag)) return;   // never redraw while the user is typing
  try { const b = await api('/bootstrap', { quiet: true }); if (bootSigOf(b) !== bootSig) refreshAll(); } catch {}
}
setInterval(syncFromDb, 8000);
window.addEventListener('focus', syncFromDb);
document.addEventListener('visibilitychange', syncFromDb);
$('#refreshDb').onclick = async () => { await refreshAll(true); toast('Refreshed from the database ✔'); };

/* ---------- dashboard ---------- */
async function refreshAll(sync = false) {
  try { BOOT = await api('/bootstrap' + (sync ? '?sync=1' : '')); } catch (e) { return toast(e.message, true); }
  bootSig = bootSigOf(BOOT);
  refreshStats(); refreshFields(); renderCustTab(); refreshBulkFetch(); cmFillSelect();
  await Promise.all([refreshAlerts(), refreshResults(), refreshManage(), refreshCM()]).catch(e => toast(e.message, true));
}
function refreshStats() {
  const s = BOOT.stats;
  countUp($('#statCust'), s.customers); countUp($('#sTotal'), s.devices); countUp($('#sMine'), s.mine); countUp($('#sCols'), s.columns);
}
$$('.tab').forEach((t, i) => t.onclick = () => {
  $$('.tab').forEach(x => x.classList.toggle('active', x === t));
  $('.tabs').style.setProperty('--i', i);
  t.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  ['insert', 'customers', 'fetch', 'manage', 'alerts'].forEach(p => $('#' + p).classList.toggle('hidden', t.dataset.tab !== p));
  refreshAll();
});

/* ---------- fetch / search ---------- */
function refreshFields() {
  const cur = $('#sField').value;
  $('#sField').replaceChildren(new Option('All Fields', '*'), new Option('Customer Name', '__cust'), ...STD().map(c => new Option(c, c)));
  if ([...$('#sField').options].some(o => o.value === cur)) $('#sField').value = cur;
  const box = $('#sPick'), keep = new Set($$('#sPick input:checked').map(i => i.value)), first = !box.children.length;
  box.innerHTML = '';
  STD().forEach(c => {
    const l = el('label', 'pk'), i = document.createElement('input');
    i.type = 'checkbox'; i.value = c; i.checked = first ? QUICK.includes(c) : keep.has(c); i.onchange = () => lastSearch && render();
    l.append(i, ' ' + c); box.append(l);
  });
}
function viewCols() { // which columns to show / download
  const m = $('#sView').value, all = colsOf(results);
  if (m === 'quick') return QUICK.filter(c => all.includes(c));
  if (m === 'custom') { const p = $$('#sPick input:checked').map(i => i.value); return all.filter(c => p.includes(c)); }
  return all;
}
$('#sView').onchange = () => { $('#sPick').classList.toggle('hidden', $('#sView').value !== 'custom'); if (lastSearch) render(); };
$('#searchForm').onsubmit = async e => {
  e.preventDefault();
  lastSearch = { f: $('#sField').value, q: $('#sQuery').value.trim() };
  try {
    await runSearch();
    const n = results.length, cs = new Set(results.map(x => x.customer)).size;
    if (n) logoFx('ok', 'Search complete', `${n.toLocaleString()} record(s) found under ${cs} customer(s)`, 1700);
    else logoFx('fail', 'No records found', `Nothing matched "${lastSearch.q}"`, 2000);
  } catch (err) { toast(err.message, true); }
};
async function refreshResults() { if (lastSearch && !$('#fetch').classList.contains('hidden')) await runSearch(); } // keeps Fetch in step with edits
async function runSearch() {   // the search runs inside the database
  const p = { field: lastSearch.f, q: lastSearch.q };
  const r = await api('/devices?' + new URLSearchParams(p));
  results = r.items.filter(simPass); render();
}
function render() {
  const cols = viewCols(), full = $('#sView').value === 'all', tb = $('#resultTable');
  $('#resultHead').classList.remove('hidden');
  $('#count').textContent = `${results.length} record${results.length === 1 ? '' : 's'} found`;
  $('#download').classList.toggle('hidden', !results.length);
  $('#empty').classList.toggle('hidden', !!results.length);
  tb.innerHTML = '';
  if (!results.length) return;
  const th = document.createElement('thead'), tr = document.createElement('tr');
  ['#', 'Customer Name', ...cols, ...(full ? ['Added By', 'Added On'] : []), 'Action'].forEach(h => tr.append(el('th', '', h)));
  th.append(tr); tb.append(th);
  const body = document.createElement('tbody');
  results.forEach((r, i) => {
    const row = document.createElement('tr'); row.style.animationDelay = Math.min(i * 40, 800) + 'ms';
    row.append(el('td', '', i + 1), custTd(r));
    [...cols.map(c => r.fields[c] ?? ''), ...(full ? [r.added_by, r.added_on] : [])].forEach(v => row.append(el('td', '', v)));
    row.append(actionsTd(r)); body.append(row);
  });
  tb.append(body);
}

/* ---------- customer picker, rename, Excel export ---------- */
function custTd(r) {   // customer name + a small pencil to rename it
  const td = el('td', '', r.customer), b = el('button', 'btn ghost ren', '✎');
  b.type = 'button'; b.title = 'Rename this customer'; b.onclick = () => renameCustomer(r.customer_id, r.customer);
  td.append(b); return td;
}
/* ---------- same name already exists: offer to MERGE the two customers ----------
   items = [{ id, name, count, targetId, targetName, targetCount }]  (id = the customer being renamed, target = the customer that already has that name)
   Merge = every record of "name" is moved into "targetName", then "name" leaves the customer list (POST /api/customers/<id>/merge). */
const cntOf = id => { const c = BOOT.customers.find(x => String(x.id) === String(id)); return c ? c.count : 0; };
function nameExistsPopup(items, o = {}) {
  const box = document.createElement('div');
  box.append(el('h2', '', '\u26A0 Same name already exists in records'));
  items.forEach(it => {
    const p = el('p', 'warnbox');
    p.append('A customer named ', el('b', '', it.targetName), ` already exists (${it.targetCount} record${it.targetCount === 1 ? '' : 's'}). `,
      `You are renaming \u201C${it.name}\u201D (${it.count} record${it.count === 1 ? '' : 's'}) to the same name.`);
    box.append(p);
  });
  const one = items.length === 1;
  box.append(el('p', 'sub', one
    ? `If you want, you can MERGE them: all ${items[0].count} record(s) of \u201C${items[0].name}\u201D are moved into \u201C${items[0].targetName}\u201D and \u201C${items[0].name}\u201D is removed from the customer list. \u201C${items[0].targetName}\u201D keeps its name and no record is lost.`
    : `If you want, you can MERGE each pair: the records of the customer you renamed are moved into the customer that already has the name, and the renamed customer is removed from the list. No record is lost.`));
  if (o.note) box.append(el('p', 'sub', o.note));
  const act = el('div', 'actions'), left = el('div'), no = el('button', 'btn ghost', 'Cancel \u2013 change nothing'), ok = el('button', 'btn', one ? `\uD83D\uDD17 Merge into \u201C${items[0].targetName}\u201D` : `\uD83D\uDD17 Merge ${items.length} customers`);
  left.style.display = 'flex'; left.style.gap = '10px'; left.append(no);
  no.type = ok.type = 'button'; no.onclick = closeModal;
  if (o.onBack) { const back = el('button', 'btn ghost', '\u270E Use another name'); back.type = 'button'; back.onclick = () => { closeModal(); o.onBack(); }; left.append(back); }
  ok.onclick = async () => {
    ok.disabled = no.disabled = true; ok.textContent = 'Merging\u2026';
    let moved = 0, done = 0, failed = '';
    for (const it of items) {
      try {
        const r = await api('/customers/' + it.id + '/merge', { method: 'POST', body: { target_id: it.targetId, source_name: it.name, target_name: it.targetName } });
        moved += r.merged || 0; done++; delete custDraft[it.id];
      } catch (err) { failed = err.message; break; }
    }
    closeModal();
    if (done) {
      toast(`${done} customer(s) merged \u2013 ${moved} record(s) moved \u2714`);
      logoFx('ok', 'Customers merged', items.slice(0, done).map(i => `${i.name} \u2192 ${i.targetName}`).join(' \u00B7 ') + ` \u00B7 ${moved} record(s) moved`, 2000);
    }
    if (failed) toast((done ? 'Stopped: ' : '') + failed, true);
    try { if (done && o.onMerged && !failed) await o.onMerged(); } catch (err) { toast(err.message, true); }
    refreshAll();
  };
  act.append(left, ok); box.append(act); openModal('merge', box); ok.focus();
}
const existsItem = (id, name, ex) => ({ id, name, count: cntOf(id), targetId: ex.id, targetName: ex.name, targetCount: ex.records });

function renameCustomer(id, current) {
  const c = BOOT.customers.find(x => String(x.id) === String(id)), box = document.createElement('div');
  box.append(el('h2', '', '✎ Rename customer'));
  box.append(el('p', 'sub', `Current name: ${current}. The new name is saved in the customers table and in the customer_name column of all ${c ? c.count : ''} device record(s) of this customer.`));
  const lab = el('label', 'lbl', 'New customer name'), inp = el('input'); inp.value = current; lab.append(inp); box.append(lab);
  const act = el('div', 'actions'), no = el('button', 'btn ghost', 'Cancel'), ok = el('button', 'btn', '✔ Save Name');
  no.type = ok.type = 'button'; no.onclick = closeModal;
  const save = async () => {
    const name = inp.value.trim().replace(/\s+/g, ' ');
    if (!name) { shake(inp); return toast('Enter the customer name', true); }
    if (name === current) return toast('The name is unchanged', true);
    try {
      const r = await api('/customers/' + id, { method: 'PATCH', body: { name } });
      closeModal(); toast(`Renamed "${r.old}" to "${r.name}" - ${r.devices} record(s) updated ✔`); logoFx('ok', 'Customer renamed', `${r.old} \u2192 ${r.name} \u00B7 ${r.devices} record(s) updated`, 1800); refreshAll();
    } catch (err) {
      if (err.data && err.data.exists) return nameExistsPopup([existsItem(id, current, err.data.exists)], { onBack: () => renameCustomer(id, current) });   // same name -> offer to merge
      toast(err.message, true);
    }
  };
  ok.onclick = save; inp.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); save(); } };
  act.append(no, ok); box.append(act); openModal('rename', box); inp.focus(); inp.select();
}
const custDraft = {};   // names typed but not saved yet (kept while the list is redrawn)
async function saveCustRow(c, inp) {   // the green Rename button / Enter key of one row
  const name = inp.value.trim().replace(/\s+/g, ' ');
  if (!name) { shake(inp); return toast('Enter the customer name', true); }
  if (name === c.name) return toast('The name is unchanged - edit the name first', true);
  try {
    const r = await api('/customers/' + c.id, { method: 'PATCH', body: { name } });
    delete custDraft[c.id]; toast(`Renamed "${r.old}" to "${r.name}" - ${r.devices} record(s) updated ✔`); logoFx('ok', 'Customer renamed', `${r.old} \u2192 ${r.name} \u00B7 ${r.devices} record(s) updated`, 1800); refreshAll();
  } catch (err) {
    if (err.data && err.data.exists) { shake(inp); return nameExistsPopup([existsItem(c.id, c.name, err.data.exists)]); }   // same name -> offer to merge
    shake(inp); toast(err.message, true);
  }
}
async function renameAllCustomers() {   // saves every edited name together (customers table + all device rows, one transaction)
  const inputs = $$('#custTable .cfin'), items = [], typed = new Map();
  for (const inp of inputs) {
    const name = inp.value.trim().replace(/\s+/g, ' ');
    if (!name) { shake(inp); inp.focus(); return toast('Customer names cannot be empty', true); }
    if (name !== inp.dataset.old) {
      const k = name.toLowerCase();
      if (typed.has(k)) { shake(inp); inp.focus(); return toast(`"${name}" is typed for two customers - to join two customers, rename one of them to the name the other already has`, true); }
      typed.set(k, 1); items.push({ id: +inp.dataset.id, name, old: inp.dataset.old });
    }
  }
  if (!items.length) return toast('No names were changed - edit the names in the boxes first', true);
  const changing = new Set(items.map(i => i.id)), conflicts = [];
  for (const it of items) {   // a new name that another (unchanged) customer already has -> offer to merge
    const ex = BOOT.customers.find(c => !changing.has(c.id) && c.name.toLowerCase() === it.name.toLowerCase());
    if (ex) conflicts.push({ id: it.id, name: it.old, count: cntOf(it.id), targetId: ex.id, targetName: ex.name, targetCount: ex.count });
  }
  const run = async list => {
    try {
      const r = await api('/customers/rename-all', { method: 'POST', body: { items: list.map(({ id, name }) => ({ id, name })) } });
      Object.keys(custDraft).forEach(k => delete custDraft[k]);
      toast(`${r.renamed} customer(s) renamed - ${r.devices} device record(s) updated ✔`); logoFx('ok', 'Customers renamed', `${r.renamed} customer(s) \u00B7 ${r.devices} record(s) updated`, 1800); refreshAll();
    } catch (err) {
      toast(err.message, true);
    }
  };
  if (conflicts.length) {
    const merging = new Set(conflicts.map(c => c.id)), rest = items.filter(i => !merging.has(i.id));
    return nameExistsPopup(conflicts, { note: rest.length ? `The other ${rest.length} renamed customer(s) are saved right after the merge.` : '', onMerged: () => rest.length ? run(rest) : null });
  }
  run(items);
}
$('#renAll').onclick = renameAllCustomers;
async function saveExcel(data, fname) {   // real .xlsx built by the server - works even without internet
  try {
    const res = await fetch((window.API_BASE || '') + '/api/export', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
      body: JSON.stringify({ headers: data[0], rows: data.slice(1), filename: fname }) });
    if (!res.ok) return false;
    const url = URL.createObjectURL(await res.blob()), a = document.createElement('a');
    a.href = url; a.download = fname; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 4000);
    return true;
  } catch { return false; }
}
async function exportData(data, base) {
  if (await saveExcel(data, base + '.xlsx')) return toast('Excel file downloaded ✔');
  if (window.XLSX) {   // fallback: browser-side Excel library
    const ws = XLSX.utils.aoa_to_sheet(data), wb = XLSX.utils.book_new();
    ws['!cols'] = data[0].map(() => ({ wch: 22 }));
    XLSX.utils.book_append_sheet(wb, ws, 'Customers');
    XLSX.writeFile(wb, base + '.xlsx');
    toast('Excel file downloaded ✔');
  } else {
    const csv = data.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['\ufeff' + csv], { type: 'text/csv' }));
    a.download = base + '.csv'; a.click();
    toast('Could not build the Excel file - downloaded as CSV (opens in Excel)', true);
  }
}
const fileLabel = s => String(s || '').replace(/[^A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
$('#download').onclick = () => {   // same columns as the table on screen (customer filter included)
  const cols = viewCols(), full = $('#sView').value === 'all';
  const data = [['Customer Name', ...cols, ...(full ? ['Added By', 'Added On'] : [])],
    ...results.map(r => [r.customer, ...cols.map(c => r.fields[c] ?? ''), ...(full ? [r.added_by, r.added_on] : [])])];
  exportData(data, 'customer_data_' + (FSIM ? fileLabel(FSIM).toLowerCase() + '_' : '') + today());
};
async function downloadFull(cid, label) {   // EVERY column of one customer (or of all customers when cid is empty)
  let items;
  try { items = (await api('/devices' + (cid ? '?customer_id=' + cid : ''))).items; } catch (e) { return toast(e.message, true); }
  if (!items.length) return toast('No device records to download yet', true);
  const cols = colsOf(items);
  const data = [['Customer Name', ...cols, 'Added By', 'Added On'],
    ...items.map(r => [r.customer, ...cols.map(c => r.fields[c] ?? ''), r.added_by, r.added_on])];
  exportData(data, 'customer_data_' + (cid ? fileLabel(label) : 'all_customers') + '_' + today());
}
$('#dlAll').onclick = () => downloadFull('', '');
const XL_ICON = '<svg class="xl" viewBox="0 0 24 24" width="22" height="22"><rect x="3" y="2" width="18" height="20" rx="3" fill="#fff"/><path d="M8 7l8 10M16 7L8 17" stroke="#2563eb" stroke-width="2.4" stroke-linecap="round"/></svg>';
function renderCustTab() {   // Customer Files: # | editable name (+ pencil) | Rename | Download File
  const t = $('#custTable'); t.innerHTML = '';
  $('#custEmpty').classList.toggle('hidden', !!BOOT.customers.length);
  $('#custBar').classList.toggle('hidden', !BOOT.customers.length);
  $('#dbInfo').textContent = BOOT.db ? 'MySQL database: ' + BOOT.db + '  |  ' +
    (BOOT.config_sync === 'ok' ? 'config.py (DEFAULT_CUSTOMERS) lists the same ' + BOOT.customers.length + ' customer(s) ✔' : BOOT.config_sync) : '';
  const hid = BOOT.hidden || [];
  $('#dbProblems').textContent = hid.length ? '⚠ ' + hid.length + ' MySQL table(s) are NOT shown: ' + hid.map(x => x.table + ' (' + x.why + ')').join('  |  ') : '';
  if (!BOOT.customers.length) return;
  Object.keys(custDraft).forEach(id => { if (!BOOT.customers.some(c => String(c.id) === id)) delete custDraft[id]; });
  const th = document.createElement('thead'), hr = document.createElement('tr'), body = document.createElement('tbody');
  ['#', 'Customer Name', 'Actions'].forEach(x => hr.append(el('th', '', x)));
  th.append(hr); t.append(th, body);
  BOOT.customers.forEach((c, i) => {
    const tr = document.createElement('tr'), nameTd = el('td'), wrap = el('div', 'cfname'), inp = el('input', 'cfin'), pen = el('button', 'cfpen', '✎');
    if (LIM()) { inp.readOnly = true; pen.style.display = 'none'; }
    inp.value = custDraft[c.id] ?? c.name; inp.dataset.id = c.id; inp.dataset.old = c.name; inp.title = 'Edit the name, then click Rename';
    pen.type = 'button'; pen.title = 'Edit name'; pen.onclick = () => { inp.focus(); inp.select(); };
    const mark = () => inp.classList.toggle('chg', inp.value.trim().replace(/\s+/g, ' ') !== c.name);
    inp.oninput = () => { if (inp.value !== c.name) custDraft[c.id] = inp.value; else delete custDraft[c.id]; mark(); };
    inp.onkeydown = e => {
      if (e.key === 'Enter') { e.preventDefault(); saveCustRow(c, inp); }
      else if (e.key === 'Escape') { inp.value = c.name; inp.oninput(); }
    };
    mark(); wrap.append(inp, pen); nameTd.append(wrap);
    const act = el('td'), box = el('div', 'cfact');
    const rn = el('button', 'btn cfg green'), dl = el('button', 'btn cfg blue');
    rn.type = dl.type = 'button';
    rn.innerHTML = '<span class="pen">✎</span> Rename'; dl.innerHTML = XL_ICON + ' Download File';
    rn.onclick = () => saveCustRow(c, inp); dl.onclick = () => downloadFull(c.id, c.name);
    if (LIM()) box.append(dl); else box.append(rn, dl); act.append(box);
    tr.append(el('td', 'cfnum', i + 1), nameTd, act); body.append(tr);
  });
}

/* ---------- duplicate popup (Device Sr No / IMEI / ICCID can exist only once across ALL customers) ---------- */
function duplicatesPopup(r) {   // bulk upload: the rows that were skipped
  const box = document.createElement('div'), list = r.duplicates;
  box.append(el('h2', '', `⚠ ${list.length} duplicate row(s) were NOT inserted`));
  const st = el('div', 'dupstats');
  st.append(el('span', 'dupstat ok', `✔ Inserted: ${r.imported}`), el('span', 'dupstat bad', `🚫 Skipped (duplicate): ${list.length}`));
  box.append(st);
  box.append(el('p', 'sub', 'Device Sr No, IMEI and ICCID can exist only once across all customers. A row matching any of them was separated and skipped; every other row of the file was inserted.'));
  const t = document.createElement('table'), th = document.createElement('thead'), hr = document.createElement('tr'), tb = document.createElement('tbody');
  ['Matched column', 'Matched value', 'IMEI', 'Customer in file', 'Device Sr No (file)', 'Why it was skipped'].forEach(h => hr.append(el('th', '', h)));
  th.append(hr); t.append(th, tb);
  list.slice(0, 300).forEach(d => {
    const tr = document.createElement('tr');
    [d.matched || 'IMEI', d.value || d.imei, d.imei, d.customer, d.device_sr_no || '', d.reason === 'repeated in the uploaded file' ? `Repeated in the file (first copy went to ${d.exists_in})` : `Already saved under ${d.exists_in}`].forEach(v => tr.append(el('td', '', v)));
    tb.append(tr);
  });
  const w = el('div', 'tablewrap duplist'); w.append(t); box.append(w);
  if (list.length > 300) box.append(el('p', 'sub', `Showing the first 300 of ${list.length} - download the full list below.`));
  const act = el('div', 'actions'), dl = el('button', 'btn ghost', '⬇ Download skipped list (Excel)'), ok = el('button', 'btn', 'OK');
  dl.type = ok.type = 'button'; ok.onclick = closeModal;
  dl.onclick = () => exportData([['Matched column', 'Matched value', 'IMEI', 'Customer in file', 'Device Sr No (file)', 'Already saved under / first copy in', 'Why skipped'],
    ...list.map(d => [d.matched || 'IMEI', d.value || d.imei, d.imei, d.customer, d.device_sr_no || '', d.exists_in, d.reason])], 'skipped_duplicates_' + today());
  act.append(dl, ok); box.append(act); openModal('dups', box); ok.focus();
}

/* ---------- expiry alerts (all customers) ---------- */
const DAY = 86400000;
function daysLeft(iso) {
  const [y, m, d] = iso.split('-').map(Number), n = new Date();
  return Math.round((Date.UTC(y, m - 1, d) - Date.UTC(n.getFullYear(), n.getMonth(), n.getDate())) / DAY);
}
const FOUR_MONTHS = 120;   // days - the "4 months" mark
let aMode = 'before';
const aDays = () => +(aMode === 'before' ? $('#aDaysB') : $('#aDaysA')).value;
const aInView = left => aMode === 'before' ? left <= aDays() : left > FOUR_MONTHS && left <= FOUR_MONTHS + aDays();
const addDays = n => { const d = new Date(); d.setDate(d.getDate() + n); return d.toLocaleDateString('en-CA'); };
async function alertList(win, after) { // after == null: expired or within `win` days | after = N: expiring between day N and N+win
  const r = await api('/alerts?days=' + win + (after != null ? '&after=' + after : ''));
  return r.items.map(x => ({ d: { id: x.id, fields: x.fields }, iso: x.iso, left: x.left, cust: x.customer }));
}
function pill(left) {
  if (left < 0) return ['exp', `Expired ${-left} day(s) ago`];
  if (left === 0) return ['exp', 'Expires today'];
  return [left <= 7 ? 'hot' : left <= 30 ? 'warn' : 'soft', `${left} day(s) left`];
}
async function refreshAlerts() {
  $('#aoB').classList.toggle('on', aMode === 'before'); $('#aoA').classList.toggle('on', aMode === 'after');
  $('#aInfo').textContent = aMode === 'before' ? `Showing devices already expired or expiring up to ${addDays(aDays())} (next ${aDays()} days)`
    : `Showing devices expiring between ${addDays(FOUR_MONTHS + 1)} and ${addDays(FOUR_MONTHS + aDays())}`;
  let list; try { list = await alertList(aDays(), aMode === 'after' ? FOUR_MONTHS : null); } catch { return; }
  const t = $('#alertTable'), b = $('#alertBadge');
  b.textContent = list.length; b.classList.toggle('hidden', !list.length || !alertsOn);
  $('#aCount').textContent = list.length ? `${list.length} device(s) need attention` : '';
  $('#aEmpty').classList.toggle('hidden', !!list.length);
  t.innerHTML = ''; if (!list.length) return;
  const th = document.createElement('thead'), hr = document.createElement('tr');
  ['Customer Name', 'Device Sr No', 'IMEI', 'MSISDN1', 'EXP DATE', 'Status', 'Action'].forEach(h => hr.append(el('th', '', h)));
  th.append(hr); t.append(th);
  const body = document.createElement('tbody');
  list.forEach((it, i) => {
    const tr = document.createElement('tr'); tr.style.animationDelay = Math.min(i * 40, 600) + 'ms';
    const f = it.d.fields, [cls, txt] = pill(it.left);
    [it.cust, f['Device Sr No'] || '', f['IMEI'] || '', f['MSISDN1'] || ''].forEach(v => tr.append(el('td', '', v)));
    const tdExp = el('td', '', it.iso), tdSt = el('td'), tdAct = el('td');
    tdSt.append(el('span', 'pill ' + cls, txt));
    const eb = el('button', 'btn ghost small', '✎ Edit Expiry'); eb.onclick = () => editExpiry(it, tr, tdExp, tdAct);
    tdAct.append(eb); tr.append(tdExp, tdSt, tdAct); body.append(tr);
  });
  t.append(body);
}
function editExpiry(it, tr, tdExp, tdAct, redraw = refreshAlerts, inView = aInView) {
  const inp = el('input', 'dateinp'); inp.type = 'date'; inp.value = it.iso;
  const ok = el('button', 'btn small', 'Save'), no = el('button', 'btn ghost small', 'Cancel');
  tdExp.replaceChildren(inp); tdAct.replaceChildren(ok, no); inp.focus();
  no.onclick = () => redraw();
  ok.onclick = async () => {
    if (!inp.value) { shake(inp); return toast('Pick the new expiry date', true); }
    try { await api('/devices/' + it.d.id, { method: 'PATCH', body: { fields: { 'EXP DATE': inp.value } } }); }
    catch (err) { return toast(err.message, true); }
    const stays = inView(daysLeft(inp.value));
    toast(stays ? 'Expiry updated - it is still inside the alert period' : 'Expiry updated ✔ removed from alerts', stays);
    refreshResults();
    if (stays) { redraw(); return refreshAlerts(); }
    tr.classList.add('gone'); setTimeout(() => { redraw(); refreshAlerts(); }, 450);
  };
}
$('#aDaysB').onchange = () => { aMode = 'before'; refreshAlerts(); };
$('#aDaysA').onchange = () => { aMode = 'after'; refreshAlerts(); };
$('#aoB').onclick = () => { if (aMode !== 'before') { aMode = 'before'; refreshAlerts(); } };
$('#aoA').onclick = () => { if (aMode !== 'after') { aMode = 'after'; refreshAlerts(); } };

/* ---------- popups: (1) review before saving, (2) expiry reminder every 5 minutes ---------- */
const POPUP_DAYS = 3, REMIND_MS = 5 * 60 * 1000;
let modalKind = null, expTimer = null, expiryDeferred = false;
function openModal(kind, node) {
  const box = $('#mbox'); box.replaceChildren(node);
  if (modalKind !== kind) { box.classList.remove('pop'); void box.offsetWidth; box.classList.add('pop'); }
  modalKind = kind; $('#modal').classList.remove('hidden');
}
function closeModal() {
  $('#modal').classList.add('hidden'); $('#mbox').replaceChildren(); $('#mbox').classList.remove('wide'); modalKind = null;
  if (autoOffPending) { autoOffPending = false; setTimeout(showAutoOffPopup, 300); }   // 'alerts switched off' notice that had to wait
  else if (expiryDeferred) { expiryDeferred = false; setTimeout(showExpiryPopup, 400); } // reminder that arrived while another popup was open
}
$('#modal').addEventListener('mousedown', e => { if (e.target.id === 'modal' && modalKind !== 'bulk') closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && modalKind && modalKind !== 'bulk') closeModal(); });

function confirmSave(info, onOk) {
  const box = document.createElement('div');
  box.append(el('h2', '', '📝 Review before saving'));
  const p = el('p', 'sub'); p.append('Customer: ', el('b', '', info.name), info.isNew ? ' - new customer' : ' - existing customer'); box.append(p);
  const t = document.createElement('table'), th = document.createElement('thead'), hr = document.createElement('tr'), tb = document.createElement('tbody');
  hr.append(el('th', '', 'Column'), el('th', '', 'Value')); th.append(hr); t.append(th, tb);
  Object.entries(info.fields).forEach(([k, v]) => {
    const tr = document.createElement('tr'); if (k === 'EXP DATE') tr.className = 'hl';
    tr.append(el('td', '', k), el('td', '', v)); tb.append(tr);
  });
  const w = el('div', 'tablewrap'); w.append(t); box.append(w);
  const newCols = Object.keys(info.fields).filter(k => !STD().some(c => same(c, k)));
  if (newCols.length) box.append(el('p', 'sub', `New column(s) that will be added to the database: ${newCols.join(', ')}`));
  const ex = toISO(info.fields['EXP DATE'] || '');
  if (ex && daysLeft(ex) <= POPUP_DAYS) box.append(el('p', 'warnbox', daysLeft(ex) < 0
    ? `⚠ The expiry date (${ex}) has already passed.` : `⚠ This device expires in ${daysLeft(ex)} day(s) (${ex}).`));
  const act = el('div', 'actions'), back = el('button', 'btn ghost', '← Go Back & Edit'), ok = el('button', 'btn', '✔ Confirm & Save');
  back.type = ok.type = 'button'; back.onclick = closeModal; ok.onclick = () => { closeModal(); onOk(); };
  act.append(back, ok); box.append(act); openModal('confirm', box); ok.focus();
}

function showExpiryPopup() {
  if (!me || !alertsOn) return;   // alerts switched OFF (manually or automatically)
  if (modalKind && modalKind !== 'expiry') { expiryDeferred = true; return; } // wait until the other popup is closed
  renderExpiryPopup();
}
async function renderExpiryPopup() {
  let list; try { list = await alertList(POPUP_DAYS, null); } catch { return; }   // expired or expiring within 3 days, every customer
  if (!me || !alertsOn) return;
  if (!list.length) { if (modalKind === 'expiry') closeModal(); return; }
  if (modalKind && modalKind !== 'expiry') { expiryDeferred = true; return; }
  const box = document.createElement('div');
  box.append(el('h2', '', '⚠ Expiry Reminder'));
  box.append(el('p', 'sub', `${list.length} device(s) expired or expiring within ${POPUP_DAYS} days. Update the expiry date to stop this reminder.`));
  const t = document.createElement('table'), th = document.createElement('thead'), hr = document.createElement('tr'), tb = document.createElement('tbody');
  ['Customer Name', 'Device Sr No', 'IMEI', 'EXP DATE', 'Status', 'Action'].forEach(h => hr.append(el('th', '', h)));
  th.append(hr); t.append(th, tb);
  list.forEach(it => {
    const tr = document.createElement('tr'), f = it.d.fields, [cls, txt] = pill(it.left);
    [it.cust, f['Device Sr No'] || '', f['IMEI'] || ''].forEach(v => tr.append(el('td', '', v)));
    const tdExp = el('td', '', it.iso), tdSt = el('td'), tdAct = el('td');
    tdSt.append(el('span', 'pill ' + cls, txt));
    const eb = el('button', 'btn ghost small', '✎ Edit Expiry');
    eb.onclick = () => editExpiry(it, tr, tdExp, tdAct, renderExpiryPopup, left => left <= POPUP_DAYS);
    tdAct.append(eb); tr.append(tdExp, tdSt, tdAct); tb.append(tr);
  });
  const w = el('div', 'tablewrap'); w.append(t); box.append(w);
  const act = el('div', 'actions'), later = el('button', 'btn ghost', '⏰ Remind me in 5 minutes'), open = el('button', 'btn', 'Open Expiry Alerts');
  later.type = open.type = 'button'; later.onclick = closeModal;
  open.onclick = () => { closeModal(); document.querySelector('[data-tab=alerts]').click(); };
  act.append(later, open); box.append(act); openModal('expiry', box);
}
/* ---------- alerts ON / OFF  +  auto-off after 2 hours without use ---------- */
const IDLE_MS = 2 * 60 * 60 * 1000;
const pref = (k, d) => { try { const v = localStorage.getItem(k); return v === null ? d : v === '1'; } catch { return d; } };
const savePref = (k, v) => { try { localStorage.setItem(k, v ? '1' : '0'); } catch {} };
let alertsOn = pref('cv_alerts_on', true), autoOff = pref('cv_alerts_autooff', true), lastActive = Date.now(), autoOffPending = false;
function paintAlertUi(note) {
  $('#alertOn').checked = alertsOn; $('#autoOff').checked = autoOff;
  $('#alertToggle').textContent = alertsOn ? '🔔 Alerts: ON' : '🔕 Alerts: OFF';
  $('#alertToggle').classList.toggle('off', !alertsOn); $('.alertctl').classList.toggle('off', !alertsOn);
  $('#alertState').textContent = alertsOn ? 'Alerts are ON' : 'Alerts are OFF';
  $('#alertStateNote').textContent = note || (alertsOn
    ? 'Popup reminders and the red badge are active.'
    : 'Popup reminders and the red badge are paused. The list below still works.');
}
function setAlerts(on, opts = {}) {   // opts.auto = switched by the idle timer (not saved, so the next login starts normal)
  alertsOn = on; if (!opts.auto) savePref('cv_alerts_on', on);
  lastActive = Date.now(); paintAlertUi(opts.note);
  if (!on && modalKind === 'expiry') closeModal();
  refreshAlerts();                       // show / hide the red badge
  if (on) setTimeout(showExpiryPopup, 400);
  if (!opts.auto) toast(on ? 'Expiry alerts are ON 🔔' : 'Expiry alerts are OFF 🔕');
}
function showAutoOffPopup() {
  if (!me) return;
  if (modalKind && modalKind !== 'expiry') { autoOffPending = true; return; }   // never cover a form the user is filling
  const box = document.createElement('div');
  box.append(el('h2', '', '🔕 Expiry alerts switched OFF'));
  box.append(el('p', 'sub', 'The app was not used for more than 2 hours, so the Auto-off feature turned the expiry alerts off.'));
  box.append(el('p', 'warnbox', '⚠ While alerts are OFF there are no expiry reminder popups and no red badge. Turn them back ON to keep track of expiring devices.'));
  const act = el('div', 'actions'), keep = el('button', 'btn ghost', 'Keep alerts OFF'), on = el('button', 'btn', '🔔 Turn alerts ON');
  keep.type = on.type = 'button'; keep.onclick = closeModal; on.onclick = () => { closeModal(); setAlerts(true); };
  act.append(keep, on); box.append(act); openModal('autooff', box); on.focus();
}
function idleCheck() {
  if (!me || !alertsOn || !autoOff || Date.now() - lastActive < IDLE_MS) return;
  setAlerts(false, { auto: true, note: 'Switched OFF automatically - the app was not used for 2 hours.' });
  showAutoOffPopup();
}
['mousemove', 'mousedown', 'keydown', 'scroll', 'touchstart', 'click'].forEach(ev =>
  document.addEventListener(ev, () => { idleCheck(); lastActive = Date.now(); }, { passive: true, capture: true }));   // coming back after 2h+ -> switch off first, then count as active
setInterval(idleCheck, 30 * 1000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) idleCheck(); });
$('#alertToggle').onclick = () => setAlerts(!alertsOn);
$('#alertOn').onchange = e => setAlerts(e.target.checked);
$('#autoOff').onchange = e => {
  autoOff = e.target.checked; savePref('cv_alerts_autooff', autoOff); lastActive = Date.now();
  toast(autoOff ? 'Auto-off after 2 hours of no use: ENABLED' : 'Auto-off: disabled - alerts stay ON until you turn them off');
};
paintAlertUi();

function startExpiryReminders() { clearInterval(expTimer); setTimeout(showExpiryPopup, 800); expTimer = setInterval(showExpiryPopup, REMIND_MS); }

/* ---------- edit / delete a device by IMEI ---------- */
function actionsTd(r) {   // Edit + Delete buttons used in Fetch and in the IMEI tab
  const td = el('td', 'acts'), e = el('button', 'btn ghost small', '✎ Edit'), d = el('button', 'btn ghost small dng', '🗑 Delete');
  e.type = d.type = 'button'; e.onclick = () => editDevice(r); d.onclick = () => deleteDevice(r);
  td.append(e, d); return td;
}
async function runManage() {
  const r = await api('/devices?' + new URLSearchParams({ field: 'IMEI', q: mLast })); mItems = r.items; renderManage();
}
async function refreshManage() { if (mLast && !$('#manage').classList.contains('hidden')) await runManage(); }
function renderManage() {
  const t = $('#mTable'); t.innerHTML = '';
  $('#mHead').classList.remove('hidden');
  $('#mCount').textContent = `${mItems.length} device(s) found for "${mLast}"`;
  $('#mEmpty').classList.toggle('hidden', !!mItems.length);
  if (!mItems.length) return;
  const th = document.createElement('thead'), hr = document.createElement('tr'), body = document.createElement('tbody');
  ['Customer Name', 'Device Sr No', 'IMEI', 'MSISDN1', 'MODEL', 'EXP DATE', 'Action'].forEach(h => hr.append(el('th', '', h)));
  th.append(hr); t.append(th, body);
  mItems.forEach((r, i) => {
    const tr = document.createElement('tr'), f = r.fields; tr.style.animationDelay = Math.min(i * 40, 600) + 'ms';
    tr.append(custTd(r));
    [f['Device Sr No'], f['IMEI'], f['MSISDN1'], f['MODEL'], f['EXP DATE']].forEach(v => tr.append(el('td', '', v || '')));
    tr.append(actionsTd(r)); body.append(tr);
  });
}
$('#mForm').onsubmit = async e => {
  e.preventDefault();
  const q = $('#mQuery').value.trim().replace(/[\s-]+/g, '');
  if (!q) { shake($('#mQuery')); return toast('Enter an IMEI number', true); }
  mLast = q; try { await runManage(); } catch (err) { toast(err.message, true); }
};
$('#mAdd').onclick = () => openBulk();
$('#mAddIt').onclick = () => openBulk();

function editDevice(r) {   // popup with every column of this device - IMEI included
  const box = document.createElement('div'), inputs = [];
  box.append(el('h2', '', '✎ Edit device record'));
  const p = el('p', 'sub'); p.append('Customer: ', el('b', '', r.customer), ' · Mandatory columns are marked *'); box.append(p);
  const grid = el('div', 'editgrid');
  const cnl = el('label', 'lbl full', 'Customer Name (changing it renames this customer for ALL of their records)'), cn = el('input');
  cn.value = r.customer; cnl.append(cn); if (!LIM()) grid.append(cnl);   // limited users can never rename a customer
  BOOT.columns.filter(c => hasCol(r, c.label)).forEach(c => {   // only this customer's columns (use 'Add new column' below for another one)
    const orig = r.fields[c.label] || '', lab = el('label', 'lbl' + (c.mandatory ? ' req' : ''), c.label + (c.mandatory ? ' *' : '')), inp = el('input');
    inp.type = c.is_date && (!orig || toISO(orig)) ? 'date' : 'text';   // calendar when the stored value is a clean date
    inp.value = inp.type === 'date' ? (toISO(orig) || '') : orig; inp.dataset.label = c.label; inp.dataset.orig = orig;
    lab.append(inp); grid.append(lab); inputs.push(inp);
  });
  const ncl = el('div', 'lbl full'); ncl.append(el('b', '', 'Add new column (optional) - give the column name and the value for this entry'));
  const ncn = el('input'), ncv = el('input'); ncn.placeholder = 'New column name, e.g. MODEL'; ncv.placeholder = 'Value for this entry';
  ncn.oninput = () => { const w = isDate(canonCol(ncn.value)) ? 'date' : 'text'; if (ncv.type !== w) ncv.type = w; };
  ncl.append(ncn, ncv); if (!LIM()) grid.append(ncl);   // ... nor add a column
  box.append(grid);
  const act = el('div', 'actions'), no = el('button', 'btn ghost', 'Cancel'), ok = el('button', 'btn', '✔ Save Changes');
  no.type = ok.type = 'button'; no.onclick = closeModal;
  ok.onclick = async () => {
    const fields = {};
    inputs.forEach(i => {
      const o = i.dataset.orig, base = i.type === 'date' ? (toISO(o) || '') : o, v = i.value.trim();
      if (v !== base) fields[i.dataset.label] = v;
    });
    const nc = canonCol(ncn.value), ncVal = ncv.value.trim();
    if (nc || ncVal) {
      if (!nc) { shake(ncn); return toast('Enter the new column name', true); }
      if (!ncVal) { shake(ncv); return toast(`Enter the value of "${nc}" for this entry`, true); }
      if (nc in fields) { shake(ncn); return toast(`Column "${nc}" is already being edited above`, true); }
      fields[nc] = isDate(nc) ? (toISO(ncVal) || ncVal) : ncVal;
    }
    const newName = cn.value.trim().replace(/\s+/g, ' '), renamed = !!newName && newName !== r.customer, changed = Object.keys(fields).length > 0;
    if (!changed && !renamed) return toast('No changes to save', true);
    const bad = MAND().find(m => m in fields && !fields[m]);
    if (bad) { const i = inputs.find(x => x.dataset.label === bad); shake(i); i.focus(); return toast(`${bad} is mandatory`, true); }
    try { if (changed) await api('/devices/' + r.id, { method: 'PATCH', body: { fields } }); }
    catch (err) { return toast(err.message, true); }
    if (renamed) {
      try { await api('/customers/' + r.customer_id, { method: 'PATCH', body: { name: newName } }); }
      catch (err) {
        refreshAll();
        if (err.data && err.data.exists) return nameExistsPopup([existsItem(r.customer_id, r.customer, err.data.exists)], { note: changed ? 'The device changes were already saved.' : '' });   // same name -> offer to merge
        return toast((changed ? 'Device saved, but the ' : 'The ') + 'customer could not be renamed: ' + err.message, true);
      }
    }
    closeModal();
    toast((renamed ? `Customer renamed to "${newName}" ✔ ` : '') + (!changed ? '' : 'IMEI' in fields ? `Device updated - IMEI is now ${fields['IMEI']} ✔` : 'Device updated ✔'));
    if (mLast && 'IMEI' in fields) { mLast = fields['IMEI']; $('#mQuery').value = mLast; }   // keep following the device after an IMEI change
    refreshAll();
  };
  act.append(no, ok); box.append(act); openModal('edit', box); inputs[0] && inputs[0].focus();
}
function deleteDevice(r) {
  const f = r.fields, box = document.createElement('div');
  box.append(el('h2', '', '🗑 Delete this entry?'));
  [['Customer', r.customer], ['IMEI', f['IMEI']], ['Device Sr No', f['Device Sr No']], ['MSISDN1', f['MSISDN1']]].forEach(([k, v]) => {
    const p = el('p', 'line'); p.append(k + ': ', el('b', '', v || '-')); box.append(p);
  });
  box.append(el('p', 'sub', '🛒 This device record will be moved to the Cart. You can restore it from the Cart tab, or delete it permanently there.'));
  const act = el('div', 'actions'), no = el('button', 'btn ghost', 'Keep it'), ok = el('button', 'btn danger', '🗑 Yes, Move to Cart');
  no.type = ok.type = 'button'; no.onclick = closeModal;
  ok.onclick = async () => {
    try { await api('/devices/' + r.id, { method: 'DELETE' }); }
    catch (err) { return toast(err.message, true); }
    closeModal(); toast(`Device ${f['IMEI'] || ''} moved to the Cart ✔`); logoFx('ok', 'Moved to Cart', f['IMEI'] ? 'IMEI ' + f['IMEI'] : 'Restore it from the Cart tab', 1700); refreshAll();
  };
  act.append(no, ok); box.append(act); openModal('delete', box); no.focus();
}

/* ---------- one-time: move data saved in this browser by the old version into the database ---------- */
function offerMigration() {
  let dv = [], cl = [];
  try { dv = JSON.parse(localStorage.getItem('cv_devices')) || []; cl = JSON.parse(localStorage.getItem('cv_clients')) || []; } catch {}
  if (!dv.length) return;
  const box = document.createElement('div');
  box.append(el('h2', '', '📥 Move old data into the database'));
  box.append(el('p', 'sub', `This browser still holds ${dv.length} device record(s) for ${cl.length} customer(s) saved by the previous version. Import them into the database now? A backup copy stays in this browser.`));
  const act = el('div', 'actions'), no = el('button', 'btn ghost', 'Not now'), ok = el('button', 'btn', 'Import to Database');
  no.type = ok.type = 'button'; no.onclick = closeModal;
  ok.onclick = async () => {
    const groups = new Map();
    dv.forEach(d => { const nm = custName(cl, d.cid); if (!groups.has(nm)) groups.set(nm, []); groups.get(nm).push(d.fields); });
    try {
      const r = await api('/devices/bulk', { method: 'POST', body: { groups: [...groups].map(([customer, rows]) => ({ customer, rows })) } });
      localStorage.setItem('cv_backup_devices', localStorage.getItem('cv_devices')); localStorage.setItem('cv_backup_clients', localStorage.getItem('cv_clients'));
      localStorage.removeItem('cv_devices'); localStorage.removeItem('cv_clients');
      closeModal(); toast(`Imported ${r.imported} old record(s) into the database ✔`); refreshAll();
      if (r.duplicates && r.duplicates.length) duplicatesPopup(r);
    } catch (err) { toast(err.message, true); }
  };
  act.append(no, ok); box.append(act); openModal('migrate', box);
}

/* ---------- restore session ---------- */
(async () => {
  if (!token) return;
  try { enter((await api('/me', { quiet: true })).employee); }
  catch { token = null; sessionStorage.removeItem('cv_token'); }
})();


/* ---------- Customer Management: All Customers Data ----------
   Columns come from BOOT.columns (= the database), never from a fixed list, so a column added to any customer table
   appears here automatically. Search runs in MySQL; the table is shown 100 rows per page and scrolls. */
const CM = { cust: '', q: '', page: 1, items: [], seq: 0, size: 100 };
function cmFillSelect() {
  const sl = $('#cmCust'); if (!sl) return;
  sl.innerHTML = ''; sl.append(new Option(`All customers  (${BOOT.stats.devices} records)`, ''));
  BOOT.customers.forEach(c => sl.append(new Option(`${c.name}  (${c.count})`, c.id)));
  if (CM.cust && ![...sl.options].some(o => o.value === String(CM.cust))) CM.cust = '';   // that customer was deleted / renamed away
  sl.value = String(CM.cust);
}
async function refreshCM() {
  if ($('#insert').classList.contains('hidden')) return;   // only fetch while the page is on screen
  const my = ++CM.seq, p = { field: '*', q: CM.q };
  if (CM.cust) p.customer_id = CM.cust;
  let r; try { r = await api('/devices?' + new URLSearchParams(p)); } catch (e) { return toast(e.message, true); }
  if (my !== CM.seq) return;   // an older request finished late - ignore it
  CM.items = r.items; renderCM();
}
function renderCM() {
  const t = $('#cmTable'), cols = colsOf(CM.items), total = CM.items.length, pages = Math.max(1, Math.ceil(total / CM.size));
  CM.page = Math.min(Math.max(CM.page, 1), pages);
  const from = (CM.page - 1) * CM.size, rows = CM.items.slice(from, from + CM.size);
  $('#cmCount').textContent = total ? `${total} record${total === 1 ? '' : 's'}${CM.q ? ' match your search' : ''} · showing ${from + 1}–${from + rows.length}` : '';
  $('#cmEmpty').classList.toggle('hidden', !!total);
  $('#cmEmpty').textContent = CM.q ? 'No records match your search.' : 'No customer records found.';
  const pg = $('#cmPager'); pg.innerHTML = '';
  if (pages > 1) {
    const prev = el('button', 'btn ghost small', '‹ Prev'), next = el('button', 'btn ghost small', 'Next ›');
    prev.type = next.type = 'button'; prev.disabled = CM.page <= 1; next.disabled = CM.page >= pages;
    prev.onclick = () => { CM.page--; renderCM(); }; next.onclick = () => { CM.page++; renderCM(); };
    pg.append(prev, el('span', '', ` Page ${CM.page} of ${pages} `), next);
  }
  t.innerHTML = ''; if (!total) return;
  const th = document.createElement('thead'), hr = document.createElement('tr'), tb = document.createElement('tbody');
  ['#', 'Customer Name', ...cols].forEach(h => hr.append(el('th', '', h))); th.append(hr); t.append(th, tb);
  rows.forEach((r, i) => {
    const tr = document.createElement('tr');
    tr.append(el('td', '', from + i + 1), el('td', '', r.customer));
    cols.forEach(c => tr.append(el('td', '', r.fields[c] ?? '')));
    tb.append(tr);
  });
}
$('#cmCust').onchange = e => { CM.cust = e.target.value; CM.page = 1; refreshCM(); };
let cmTimer = null;
$('#cmQuery').oninput = e => { clearTimeout(cmTimer); cmTimer = setTimeout(() => { CM.q = e.target.value.trim(); CM.page = 1; refreshCM(); }, 300); };
$('#cmClear').onclick = () => { $('#cmQuery').value = ''; CM.q = ''; CM.page = 1; refreshCM(); };


/* ---------- Bulk Fetch: Excel list of values -> records -> Excel ----------
   Everything (search columns, output columns) comes from BOOT.columns, i.e. from the database, so a column added to
   any customer table shows up here by itself. */
const BF = { simType: '', wb: null, grid: null, items: [], notFound: [], searched: 0, done: false, searchLabel: '', checked: new Set(), seen: new Set() };
const BF_DEFAULT = ['Customer Name', 'IMEI', 'ICCID', 'MSISDN1', 'ACT DATE', 'EXP DATE'];
const bfAllCols = () => ['Customer Name', ...STD()];
const bfOut = () => bfAllCols().filter(c => BF.checked.has(c) && (c === 'Customer Name' || c === BF.searchLabel || !BF.items.length || BF.items.some(r => hasCol(r, c))));
const bfVal = (r, c) => c === 'Customer Name' ? r.customer : (r.fields[c] ?? '');
const colLetter = i => { let s = '', n = i + 1; while (n) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = (n - m - 1) / 26; } return s; };

function refreshBulkFetch() {   // rebuilds the drop-downs / checkboxes from the database; never touches results or the loaded file
  const sc = $('#bfCol'), cur = sc.value || 'IMEI';
  sc.innerHTML = ''; sc.append(new Option('Customer Name', '__cust'));
  STD().forEach(c => sc.append(new Option(c, c)));
  sc.value = [...sc.options].some(o => o.value === cur) ? cur : (STD().includes('IMEI') ? 'IMEI' : (sc.options[1] ? sc.options[1].value : ''));
  const cc = $('#bfCust'), cv = cc.value;
  cc.innerHTML = ''; cc.append(new Option('All customers', ''));
  BOOT.customers.forEach(c => cc.append(new Option(`${c.name}  (${c.count})`, c.id)));
  if ([...cc.options].some(o => o.value === cv)) cc.value = cv;
  const box = $('#bfPick'); box.innerHTML = '';
  bfAllCols().forEach(c => {
    if (!BF.seen.has(c)) { BF.seen.add(c); if (BF_DEFAULT.includes(c)) BF.checked.add(c); }   // a brand-new column starts unticked
    const l = el('label', 'pk'), i = document.createElement('input');
    i.type = 'checkbox'; i.value = c; i.checked = BF.checked.has(c);
    i.onchange = () => { i.checked ? BF.checked.add(c) : BF.checked.delete(c); if (BF.done) renderBf(); };
    l.append(i, ' ' + c); box.append(l);
  });
  if (BF.grid) bfDetect(false);
  if (BF.done) renderBf();
}
$('#bfAll').onclick = () => { bfAllCols().forEach(c => BF.checked.add(c)); refreshBulkFetch(); };
$('#bfNone').onclick = () => { BF.checked.clear(); refreshBulkFetch(); };

function bfCell(raw, fmt) {   // keep IMEI / ICCID digits exactly - no 8.6E+14
  if (raw instanceof Date) return String(fmt ?? '').trim();
  if (typeof raw === 'number') return Number.isInteger(raw) ? BigInt(raw).toString() : String(raw);
  return String(raw ?? '').trim();
}
function bfHandleFile(f) {
  if (!f) return;
  if (!/\.(xlsx|xls)$/i.test(f.name)) { shake($('#bfDrop')); $('#bfFile').value = ''; return toast('Only Excel files (.xlsx, .xls) are allowed', true); }
  if (!window.XLSX) return toast('Excel reader could not load - check your internet connection', true);
  const rd = new FileReader();
  rd.onload = () => {
    try {
      BF.wb = XLSX.read(rd.result, { type: 'array', cellDates: true });
      const sh = $('#bfSheet'); sh.innerHTML = '';
      BF.wb.SheetNames.forEach(n => sh.append(new Option(n, n)));
      $('#bfSheetWrap').classList.toggle('hidden', BF.wb.SheetNames.length < 2);
      $('#bfDropText').textContent = '✔ ' + f.name;
      bfReadSheet(true);
    } catch { BF.wb = BF.grid = null; toast('Could not read this Excel file', true); }
  };
  rd.readAsArrayBuffer(f);
}
function bfReadSheet(autoPick) {
  const ws = BF.wb.Sheets[$('#bfSheet').value];
  const raw = XLSX.utils.sheet_to_json(ws, { header: 1, raw: true, defval: '' });
  const fmt = XLSX.utils.sheet_to_json(ws, { header: 1, raw: false, dateNF: 'yyyy-mm-dd', defval: '' });
  BF.grid = raw.map((r, ri) => r.map((v, ci) => bfCell(v, (fmt[ri] || [])[ci]))).filter(r => r.some(x => x));
  if (!BF.grid.length) { BF.grid = null; $('#bfFileOpts').classList.add('hidden'); $('#bfInfo').textContent = ''; return toast('No values found in this sheet', true); }
  bfDetect(autoPick);
}
function bfDetect(autoPick) {   // fill the "read values from" list; guess the column + whether row 1 is a heading
  const g = BF.grid, width = Math.max(...g.map(r => r.length)), known = bfAllCols().map(c => c.toLowerCase());
  const isKnown = v => known.includes(canonCol(v).toLowerCase()) || /^(customer|client)([ _]?name)?$/i.test(v);
  const xs = $('#bfXcol'), cur = xs.value;
  xs.innerHTML = '';
  for (let i = 0; i < width; i++) xs.append(new Option(g[0][i] ? `${g[0][i]}  (column ${colLetter(i)})` : `Column ${colLetter(i)}`, i));
  if (autoPick) {
    $('#bfHeader').checked = g[0].some(isKnown);
    const want = $('#bfCol').value === '__cust' ? 'customer name' : $('#bfCol').value.toLowerCase();
    const hit = g[0].findIndex(v => canonCol(v).toLowerCase() === want || (want === 'customer name' && /^(customer|client)([ _]?name)?$/i.test(v)));
    xs.value = hit >= 0 ? hit : 0;
  } else if ([...xs.options].some(o => o.value === cur)) xs.value = cur;
  $('#bfFileOpts').classList.remove('hidden');
  bfInfo();
}
function bfValues() {
  const i = +$('#bfXcol').value, rows = BF.grid.slice($('#bfHeader').checked ? 1 : 0);
  return rows.map(r => (r[i] ?? '').trim()).filter(Boolean);
}
function bfInfo() {
  if (!BF.grid) return;
  const v = bfValues(), u = new Set(v.map(x => x.toLowerCase())).size;
  $('#bfInfo').textContent = `${v.length} value(s) read from the file` + (u < v.length ? ` (${v.length - u} repeated - each is searched once)` : '');
}
$('#bfFile').onchange = e => bfHandleFile(e.target.files[0]);
['dragenter', 'dragover'].forEach(ev => $('#bfDrop').addEventListener(ev, e => { e.preventDefault(); $('#bfDrop').classList.add('over'); }));
['dragleave', 'drop'].forEach(ev => $('#bfDrop').addEventListener(ev, e => { e.preventDefault(); $('#bfDrop').classList.remove('over'); }));
$('#bfDrop').addEventListener('drop', e => bfHandleFile(e.dataTransfer.files[0]));
$('#bfSheet').onchange = () => bfReadSheet(true);
$('#bfXcol').onchange = bfInfo;
$('#bfHeader').onchange = bfInfo;
$('#bfCol').onchange = () => { if (BF.grid) bfDetect(true); };

$('#bfGo').onclick = async () => {
  if (!BF.grid) return toast('Upload an Excel file first', true);
  if (!bfOut().length) return toast('Tick at least one column to include in the result', true);
  const values = bfValues(); if (!values.length) return toast('The selected Excel column has no values', true);
  if (values.some(v => /^\d(\.\d+)?E\+\d+$/i.test(v))) toast('Some values look like 8.6E+14 - Excel shortened them. Format that column as Text in Excel and upload again.', true);
  const btn = $('#bfGo'); btn.disabled = true;
  try {
    const r = await api('/fetch/bulk', { method: 'POST', body: { column: $('#bfCol').value, values, customer_id: $('#bfCust').value || null, sim_type: BF.simType || null } });
    Object.assign(BF, { items: r.items, notFound: r.not_found, searched: r.searched, foundValues: r.found_values, done: true,
      searchLabel: $('#bfCol').value === '__cust' ? 'Customer Name' : $('#bfCol').value });
    renderBf();
    const nf = r.not_found || [];
    if (r.items.length) logoFx('ok', 'Data fetched!', `${r.items.length.toLocaleString()} record(s) found \u00B7 ${r.found_values} of ${r.searched} values matched` + (nf.length ? ` \u00B7 ${nf.length} not found` : ''), 1900);
    else logoFx('fail', 'Nothing matched', `None of the ${r.searched} searched value(s) were found`, 2200);
  } catch (err) { toast(err.message, true); }
  btn.disabled = false;
};
function bfRows() {   // [header, ...rows] exactly as shown on screen / written to Excel
  const cols = bfOut(), inc = $('#bfIncNF').checked && BF.notFound.length, head = inc ? [...cols, 'Status'] : cols;
  const rows = BF.items.map(r => inc ? [...cols.map(c => bfVal(r, c)), 'FOUND'] : cols.map(c => bfVal(r, c)));
  if (inc) BF.notFound.forEach(v => rows.push([...cols.map(c => c === BF.searchLabel ? v : ''), 'NOT FOUND' + (cols.includes(BF.searchLabel) ? '' : ': ' + v)]));
  return [head, ...rows];
}
function renderBf() {
  const nf = BF.notFound, tb = $('#bfTable'), [head, ...rows] = bfRows(), cols = bfOut();
  $('#bfHead').classList.remove('hidden');
  $('#bfCount').textContent = `Records Found: ${BF.items.length}`;
  $('#bfSum').textContent = `${BF.foundValues} of ${BF.searched} searched value(s) found in ${BF.searchLabel}` + (nf.length ? ` · ${nf.length} not found` : '');
  $('#bfDownload').classList.toggle('hidden', !cols.length || !(BF.items.length || (nf.length && $('#bfIncNF').checked)));
  $('#bfEmpty').classList.toggle('hidden', !!BF.items.length);
  tb.innerHTML = '';
  if (cols.length && rows.length) {
    const th = document.createElement('thead'), tr = document.createElement('tr');
    ['#', ...head].forEach(h => tr.append(el('th', '', h))); th.append(tr); tb.append(th);
    const body = document.createElement('tbody');
    rows.forEach((r, i) => {
      const row = document.createElement('tr'), bad = String(r[r.length - 1]).startsWith('NOT FOUND');
      row.style.animationDelay = Math.min(i * 20, 600) + 'ms'; row.append(el('td', '', i + 1));
      r.forEach(v => row.append(el('td', bad ? 'nf' : '', v))); body.append(row);
    });
    tb.append(body);
  }
  const box = $('#bfNF'); box.innerHTML = '';
  box.classList.toggle('hidden', !nf.length);
  if (nf.length) {
    const vals = el('div', 'vals'); nf.slice(0, 300).forEach(v => vals.append(el('span', '', v)));
    if (nf.length > 300) vals.append(el('span', '', `… and ${nf.length - 300} more (all are in the download)`));
    const b = el('button', 'btn ghost small', '⬇ Download NOT FOUND list'); b.type = 'button';
    b.onclick = () => exportData([[BF.searchLabel + ' (not found)'], ...nf.map(v => [v])], 'bulk_fetch_not_found_' + today());
    const title = el('div'); title.append(el('b', '', `${nf.length} value(s) NOT FOUND`), ` in ${BF.searchLabel === 'Customer Name' ? 'the customer list' : 'any customer table'}:`);
    box.append(title, vals, b);
  }
}
$('#bfIncNF').onchange = () => BF.done && renderBf();
$('#bfDownload').onclick = () => exportData(bfRows(), (BF.simType === 'E-SIM' ? 'esim_fetch_' : BF.simType === 'Plastic SIM' ? 'plastic_sim_fetch_' : 'bulk_fetch_') + fileLabel(BF.searchLabel) + '_' + today());


/* ---------- Fetch Data: SIM type (All / E-SIM / Plastic SIM) - one choice shared by Normal Fetch and Bulk Fetch ----------
   Uses the SIM TYPE saved by Bulk Upload (a sheet with ICCID values = E-SIM, without = Plastic SIM). */
const sqz = v => String(v ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');
const simKind = r => {   // the SIM TYPE saved by Bulk Upload; a record without one: with an ICCID value = E-SIM, without = Plastic SIM
  const saved = Object.entries(r.fields).find(([k, v]) => sqz(k) === 'simtype' && String(v ?? '').trim());
  if (saved) return sqz(saved[1]) === 'esim' ? 'E-SIM' : sqz(saved[1]) === 'plasticsim' ? 'Plastic SIM' : String(saved[1]).trim();
  return Object.entries(r.fields).some(([k, v]) => ['iccid', 'ccidno'].includes(sqz(k)) && String(v ?? '').trim()) ? 'E-SIM' : 'Plastic SIM';
};
const simPass = r => !FSIM || simKind(r) === FSIM;
$$('#fSim .segb').forEach(b => b.onclick = async () => {
  $$('#fSim .segb').forEach(x => x.classList.toggle('on', x === b));
  const changed = FSIM !== b.dataset.s;
  FSIM = BF.simType = b.dataset.s;
  if (!changed) return;
  BF.items = []; BF.notFound = []; BF.done = false;   // the old Bulk Fetch result no longer applies
  ['#bfHead', '#bfEmpty', '#bfNF'].forEach(q => { const e = $(q); if (e) e.classList.add('hidden'); });
  $('#bfTable').innerHTML = '';
  if (lastSearch) { try { await runSearch(); } catch (err) { toast(err.message, true); } }   // Normal Fetch: the same search, for the chosen type
});

/* ---------- Fetch Data: switch between Normal Fetch and Bulk Fetch (Excel) ---------- */
$$('#fMode .segb').forEach(b => b.onclick = () => {
  $$('#fMode .segb').forEach(x => x.classList.toggle('on', x === b));
  $('#fNormal').classList.toggle('hidden', b.dataset.f !== 'normal');
  $('#fBulk').classList.toggle('hidden', b.dataset.f !== 'bulk');
});


/* ---------- Customer Management: [Bulk Upload] ---------- */
$('#cmBulk').onclick = () => openBulk();

/* ---------- themes: Classic / Earthy / Ocean / Sunset  x  Light / Dark ---------- */
const THEME_INFO = { classic: ['Classic', '#5b45d6', '\u25C8'], earthy: ['Earthy', '#4f7a3a', '\uD83C\uDF3F'], ocean: ['Ocean', '#0e8aa8', '\uD83C\uDF0A'], sunset: ['Sunset', '#e8604c', '\uD83C\uDF05'] };
const root = document.documentElement;
function paintTheme() {
  $$('#themePop .tp').forEach(b => b.classList.toggle('on', b.dataset.theme === root.dataset.theme));
  $$('#themePop [data-mode]').forEach(b => b.classList.toggle('on', b.dataset.mode === root.dataset.mode));
  const cs = getComputedStyle(root), fav = $('#favicon');
  if (fav) fav.href = 'data:image/svg+xml,' + encodeURIComponent(`<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="lgg" x1="8" y1="4" x2="58" y2="62" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="${cs.getPropertyValue('--a2').trim()}"/><stop offset="1" stop-color="${cs.getPropertyValue('--a').trim()}"/></linearGradient><linearGradient id="shg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs><rect x="4" y="4" width="56" height="56" rx="18" fill="url(#lgg)"/><path d="M4 22a18 18 0 0 1 18-18h20a18 18 0 0 1 18 18v6C46 37 18 37 4 28z" fill="url(#shg)"/><circle class="hd" cx="32" cy="17.5" r="6.2" fill="#fff"/><path d="M17 29.5 32 41l15-11.5" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="M17 40 32 51.5 47 40" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>`);
  const m = $('meta[name=theme-color]'); if (m) m.content = getComputedStyle(root).getPropertyValue('--bg').trim() || THEME_INFO[root.dataset.theme][1];
}
function setTheme(t, mode, say) {
  if (t) { root.dataset.theme = t; try { localStorage.setItem('cv_theme', t); } catch {} }
  if (mode) { root.dataset.mode = mode; try { localStorage.setItem('cv_mode', mode); } catch {} }
  paintTheme();
  if (say) toast(`${THEME_INFO[root.dataset.theme][2]} ${THEME_INFO[root.dataset.theme][0]} theme \u00B7 ${root.dataset.mode} mode`);
}
$$('#themePop .tp').forEach(b => b.onclick = () => setTheme(b.dataset.theme, null, true));
$$('#themePop [data-mode]').forEach(b => b.onclick = () => setTheme(null, b.dataset.mode, true));
$('#themeBtn').onclick = e => { e.stopPropagation(); $('#themePop').classList.toggle('hidden'); paintTheme(); };
document.addEventListener('click', e => { if (!e.target.closest('#themePop') && !e.target.closest('#themeBtn')) $('#themePop').classList.add('hidden'); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') $('#themePop').classList.add('hidden'); });
paintTheme();

/* ---------- friendly extras ---------- */
// show / hide password
$$('.field').forEach(f => {
  const inp = f.querySelector('input[type=password]'); if (!inp) return;
  const b = el('button', 'eye', '\uD83D\uDC41'); b.type = 'button'; b.title = 'Show / hide password'; b.setAttribute('aria-label', 'Show or hide password');
  b.onclick = () => { const show = inp.type === 'password'; inp.type = show ? 'text' : 'password'; b.textContent = show ? '\uD83D\uDE48' : '\uD83D\uDC41'; inp.focus(); };
  f.append(b);
});
// the number cards jump to the matching tab
[['customers'], ['insert'], ['insert']].forEach(([tab], i) => {
  const c = $$('.stat')[i]; if (!c) return;
  c.tabIndex = 0; c.setAttribute('role', 'button'); c.title = 'Open ' + tab;
  const go = () => document.querySelector(`[data-tab=${tab}]`).click();
  c.onclick = go; c.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } };
});
// Alt+1..5 switches tabs
document.addEventListener('keydown', e => {
  if (!e.altKey || !/^[1-5]$/.test(e.key) || $('#appView').classList.contains('hidden')) return;
  e.preventDefault(); $$('.tab')[+e.key - 1]?.click();
});
// double-click a table cell to copy its text
document.addEventListener('dblclick', async e => {
  const td = e.target.closest('td'); if (!td || td.querySelector('input,button,select')) return;
  const text = td.textContent.trim(); if (!text) return;
  try { await navigator.clipboard.writeText(text); }
  catch { const ta = el('textarea'); ta.value = text; document.body.append(ta); ta.select(); try { document.execCommand('copy'); } catch {} ta.remove(); }
  td.classList.add('copied'); setTimeout(() => td.classList.remove('copied'), 700);
  toast(`Copied: ${text.length > 40 ? text.slice(0, 40) + '\u2026' : text}`);
});


/* ---------- 3D interaction: tilt + light on cards, mouse parallax, confetti, back-to-top ---------- */
const FINE = matchMedia('(hover:hover) and (pointer:fine)').matches && !matchMedia('(prefers-reduced-motion:reduce)').matches;
const TILT = '.stat,.cust,.aopt,.tp,.auth';
let tiltEl = null, raf = 0;
function untilt(e) { if (!e) return; e.style.setProperty('--rx', '0deg'); e.style.setProperty('--ry', '0deg'); }
if (FINE) {
  document.addEventListener('pointermove', ev => {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      root.style.setProperty('--px', ((ev.clientX / innerWidth - .5) * 2).toFixed(3));   // parallax for the floating shapes
      root.style.setProperty('--py', ((ev.clientY / innerHeight - .5) * 2).toFixed(3));
      const t = ev.target.closest && ev.target.closest(TILT);
      if (tiltEl && tiltEl !== t) untilt(tiltEl);
      tiltEl = t;
      if (!t) return;
      const r = t.getBoundingClientRect(), x = (ev.clientX - r.left) / r.width, y = (ev.clientY - r.top) / r.height, max = t.matches('.auth') ? 3 : t.matches('.aopt') ? 4 : 8;
      t.style.setProperty('--ry', ((x - .5) * 2 * max).toFixed(2) + 'deg');
      t.style.setProperty('--rx', ((.5 - y) * 2 * max).toFixed(2) + 'deg');
      t.style.setProperty('--mx', (x * 100).toFixed(1) + '%'); t.style.setProperty('--my', (y * 100).toFixed(1) + '%');
    });
  }, { passive: true });
  document.addEventListener('pointerleave', () => { untilt(tiltEl); tiltEl = null; }, true);
}
function burst(x, y) {   // small confetti pop after a successful save
  if (matchMedia('(prefers-reduced-motion:reduce)').matches) return;
  const cs = getComputedStyle(root), cols = [cs.getPropertyValue('--a'), cs.getPropertyValue('--a2'), cs.getPropertyValue('--ok'), '#ffc94d', '#ff7aa8'];
  for (let i = 0; i < 16; i++) {
    const p = el('i', 'confetti'), ang = Math.random() * Math.PI * 2, d = 40 + Math.random() * 70;
    p.style.cssText = `left:${x}px;top:${y}px;background:${cols[i % cols.length].trim()};--dx:${Math.cos(ang) * d}px;--dy:${Math.sin(ang) * d - 30}px;--rot:${Math.random() * 540 - 270}deg`;
    document.body.append(p); setTimeout(() => p.remove(), 950);
  }
}
const toTop = $('#toTop');
addEventListener('scroll', () => toTop.classList.toggle('show', scrollY > 400), { passive: true });
toTop.onclick = () => scrollTo({ top: 0, behavior: 'smooth' });
