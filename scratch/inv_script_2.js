

    // --- Foundation Configuration & Core Helpers ---
    const API_BASE = window.location.origin;
    let tok = localStorage.getItem('token') || '';
    let S = {}, CU = [], XC = [];
        let currentContainerId = '';
    let alertsOn = localStorage.getItem('alerts') === '1';
    let livePolling = true, liveTimer = null, liveIntervalSec = 10;
    let liveCid = '', liveQ = '', liveCol = 'all', livePage = 1, sortCol = 'id', sortDir = 'desc';
    let liveHealthData = null, liveReportList = null;
    let invPage = 1, invQ = '', invCol = 'all', invCid = '';

    const ALBL = {
      login: ['Signed In', 'ok'], login_failed: ['Failed Login', 'bad'], logout: ['Signed Out', 'mut'],
      register: ['Account Registered', 'warn'], password_change: ['Password Changed', 'mut'],
      device_add: ['Device Added', 'ok'], device_upload: ['Bulk Upload', 'ok'],
      device_edit: ['Device Edited', 'warn'], device_delete: ['Device Deleted', 'bad'],
      device_restore: ['Device Restored', 'ok'], device_purge: ['Purged Forever', 'bad'],
      bin_empty: ['Cart Emptied', 'bad'], user_create: ['User Created', 'ok'],
      user_update: ['User Updated', 'warn'], user_delete: ['User Deleted', 'bad'],
      customer_add: ['Customer Added', 'ok'], customer_rename: ['Customer Renamed', 'warn'],
      customer_rename_all: ['Customers Bulk Renamed', 'warn'], customer_merge: ['Customers Merged', 'warn'],
      customer_delete: ['Customer Deleted', 'bad'], customer_restore: ['Customer Restored', 'ok'],
      customer_purge: ['Customer Purged', 'bad'], simdata_apply: ['SIM Data Applied', 'ok'],
      column_delete: ['Column Deleted', 'bad'], export_excel: ['Excel Exported', 'ok']
    };

    const _safeElemStore = {};
    function _safeElem(id) {
      if (_safeElemStore[id]) return _safeElemStore[id];
      return (_safeElemStore[id] = {
        id: id,
        style: { setProperty() {}, removeProperty() {}, getPropertyValue() { return ''; } },
        classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
        dataset: {},
        children: [],
        childNodes: [],
        setAttribute() {},
        removeAttribute() {},
        getAttribute() { return null; },
        addEventListener() {},
        removeEventListener() {},
        querySelector() { return null; },
        querySelectorAll() { return []; },
        getElementsByTagName() { return []; },
        getElementsByClassName() { return []; },
        focus() {}, blur() {}, click() {}, showModal() {}, close() {},
        appendChild() {}, removeChild() {}, replaceChild() {}, insertAdjacentHTML() {},
        reset() {}, value: '', textContent: '', innerHTML: ''
      });
    }

    const $ = id => document.getElementById(id) || _safeElem(id);
    const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    const toast = m => {
      const t = $('toast');
      if (!t || !t.classList) return;
      t.textContent = m;
      t.classList.add('show');
      clearTimeout(toast.t);
      toast.t = setTimeout(() => t.classList.remove('show'), 2800);
    };
    const fail = e => toast(e instanceof TypeError ? 'Cannot reach server. Is backend running?' : e.message);

    const getUser = () => {
      try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch(e) { return {}; }
    };
    const getUserNormId = () => {
      const u = getUser();
      const raw = (u.user_id || '').trim().toLowerCase();
      return /^\d+$/.test(raw) ? raw.padStart(4, '0') : raw;
    };
    const isSuperAdminUser = () => {
      const u = getUser();
      const r = (u.role || '').toLowerCase();
      const uid = getUserNormId();
      return r === 'super_admin' || uid === '0001' || uid === 'bstpl001';
    };
    const isMasterAdminUser = () => {
      const u = getUser();
      const r = (u.role || '').toLowerCase();
      const uid = getUserNormId();
      return r === 'master_admin' || uid === '0002';
    };
    function applyTheme(pal, mode, save = true) {
      pal = pal || localStorage.getItem('valut_palette') || 'royal_navy';
      mode = mode || localStorage.getItem('valut_theme_mode') || 'light';
      document.documentElement.setAttribute('data-theme', mode);
      document.documentElement.setAttribute('data-mode', mode);
      document.documentElement.setAttribute('data-palette', pal);
      if (save) {
        try {
          localStorage.setItem('valut_palette', pal);
          localStorage.setItem('valut_theme_mode', mode);
        } catch(e) {}
      }
    }

    function initTheme() {
      const m = localStorage.getItem('valut_theme_mode') || 'light';
      const p = localStorage.getItem('valut_palette') || 'royal_navy';
      applyTheme(p, m, false);
    }

    const canDeleteValidInventory = () => {
      if (isSuperAdminUser()) return true;
      if (isMasterAdminUser()) return false;
      return true;
    };

    async function api(path, opt = {}) {
      const r = await fetch(API_BASE + path, {
        ...opt,
        headers: {
          Authorization: 'Bearer ' + tok,
          ...(opt.body && !(opt.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
          ...(opt.headers || {})
        }
      });
      if (r.status === 401) {
        localStorage.removeItem('token');
        if (!window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('index.html')) {
          window.location.href = 'index.html';
        }
        throw new Error('Session expired. Please sign in.');
      }
      if (!r.ok) {
        const text = await r.text();
        let msg = text;
        try {
          const j = JSON.parse(text);
          msg = (typeof j.detail === 'string' ? j.detail : Array.isArray(j.detail) ? j.detail.map(d => (d && d.msg ? ((d.loc || []).filter(x => x !== 'body').join(' > ') + ': ' + d.msg) : (typeof d === 'string' ? d : JSON.stringify(d)))).slice(0, 5).join(' | ') : (j.detail ? JSON.stringify(j.detail) : (j.message || text)));
        } catch(e) {}
        throw new Error(msg || ('Request failed (' + r.status + ')'));
      }
      const _resData = await r.json();
      const _reqMethod = (opt.method || 'GET').toUpperCase();
      if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(_reqMethod)) {
        if (!path.includes('/auth/') && !path.includes('/logs') && !path.includes('/audit')) {
          if (typeof notifyDataUpdated === 'function') {
            notifyDataUpdated({ path, method: _reqMethod });
          }
        }
      }
      return _resData;
    }

    const COLS = [
      ['customer_name', 'Customer Name'],
      ['device_sr_no', 'Device SR No'],
      ['imei', 'IMEI'],
      ['iccid', 'ICCID / CCID'],
      ['msisdn1', 'MSISDN1'],
      ['msisdn2', 'MSISDN2'],
      ['act_date', 'Act Date'],
      ['expiry_date', 'Expiry Date'],
      ['dispatched_date', 'Dispatched'],
      ['model', 'Model'],
      ['sim_provider', 'SIM Provider'],
      ['activation_plan', 'Activation Plan'],
      ['firmware', 'Firmware'],
      ['flash', 'Flash'],
      ['sim_type', 'SIM Type']
    ];

    const expTag = d => {
      if (d.days_left == null) return '';
      if (d.days_left < 0) return `<span class="tag bad">Expired ${-d.days_left}d ago</span>`;
      if (d.days_left <= 30) return `<span class="tag warn">${d.days_left}d left</span>`;
      return `<span class="tag ok">${d.days_left}d left</span>`;
    };

    const cell = (d, k) => {
      const val = d[k];
      if (k === 'expiry_date') {
        return val ? `${esc(val)} ${expTag(d)}` : '<span style="color:var(--muted)">—</span>';
      }
      if (k === 'customer_name') {
        return val ? `<b style="color:var(--text)">${esc(val)}</b>` : '<span style="color:var(--muted)">—</span>';
      }
      if (k === 'imei') {
        return val ? `<code><b>${esc(val)}</b></code>` : '<span style="color:var(--muted)">—</span>';
      }
      if (k === 'iccid') {
        return val ? `<code>${esc(val)}</code>` : '<span style="color:var(--muted)">—</span>';
      }
      if (k === 'sim_type') {
        if (!val) return '<span style="color:var(--muted)">—</span>';
        if (val === 'E-SIM') return `<span class="tag" style="background:#38bdf8;color:#000;font-weight:700">E-SIM</span>`;
        if (val === 'Plastic SIM') return `<span class="tag" style="background:#fbbf24;color:#000;font-weight:700">Plastic SIM</span>`;
        return esc(val);
      }
      return val ? esc(val) : '<span style="color:var(--muted)">—</span>';
    };

    function renderTable(list, act, extraCols = [], isSortable = true) {
      if (!list.length) return '<div class="empty">No records found matching current criteria.</div>';
      const ex = extraCols;
      return `<div class="tw"><table><thead><tr>
        <th>#</th>
        ${COLS.map(c => `<th>${c[1]}</th>`).join('')}
        ${XC.map(c => `<th>${esc(c)}</th>`).join('')}
        ${ex.map(c => `<th>${c[1]}</th>`).join('')}
        ${act ? '<th>Actions</th>' : ''}
      </tr></thead><tbody>
      ${list.map(d => `<tr>
        <td><b>${d.id}</b></td>
        ${COLS.map(c => `<td>${cell(d, c[0])}</td>`).join('')}
        ${XC.map(c => `<td>${esc((d.extra || {})[c])}</td>`).join('')}
        ${ex.map(c => `<td>${esc(d[c[0]] || '')}</td>`).join('')}
        ${act ? `<td>${act(d)}</td>` : ''}
      </tr>`).join('')}
      </tbody></table></div>`;
    }

    function exportExcel(title, headers, rows) {
      try {
        toast('Generating Excel file…');
        if (typeof XLSX !== 'undefined') {
          const data = [headers, ...(rows || [])];
          const ws = XLSX.utils.aoa_to_sheet(data);
          const wb = XLSX.utils.book_new();
          XLSX.utils.book_append_sheet(wb, ws, 'Data');
          const safeTitle = (title || 'Export').replace(/[^a-zA-Z0-9_-]/g, '_');
          const fileName = `${safeTitle}_${new Date().toISOString().slice(0, 10)}.xlsx`;
          XLSX.writeFile(wb, fileName);
          toast('Excel downloaded successfully');
        } else {
          const csv = [headers.join(','), ...(rows || []).map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(','))].join('\n');
          const blob = new Blob([csv], { type: 'text/csv' });
          const a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          a.download = `${title || 'export'}.csv`;
          a.click();
          toast('CSV downloaded');
        }
      } catch(e) {
        toast('Export failed: ' + e.message);
      }
    }

    // Modal helpers
    function openDlg(title, bodyHtml, confirmLabel, onConfirm, isDanger = false) {
      $('cdt').textContent = title;
      $('cdb').innerHTML = bodyHtml;
      $('cde').textContent = '';
      $('cdok').textContent = confirmLabel || 'Confirm';
      $('cdok').className = isDanger ? 'b d' : 'b p';
      $('cdok').onclick = async e => {
        e.preventDefault();
        try {
          $('cde').textContent = '';
          await onConfirm();
          $('cdlg').close();
        } catch(err) { $('cde').textContent = err.message; }
      };
      $('cdx').onclick = () => $('cdlg').close();
      $('cdlg').showModal();
    }

    function buildDeviceFormFields(dev = {}) {
      const custOptions = (CU || []).map(c => `<option value="${esc(c.name)}">${esc(c.name)}</option>`).join('');
      return `
        <datalist id="custNameDatalist">
          ${custOptions}
        </datalist>

        <!-- Section 1: Customer & Hardware Identity -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-size:13.5px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">👤</span> <span>Customer & Device Identification</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Customer Name <span style="color:var(--danger)">*</span></label>
              <input data-devf="customer_name" list="custNameDatalist" value="${esc(dev.customer_name || '')}" placeholder="Type or select customer" required
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Device SR No</label>
              <input data-devf="device_sr_no" value="${esc(dev.device_sr_no || '')}" placeholder="e.g. SR-89042"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">IMEI Number <span style="color:var(--danger)">*</span></label>
              <input data-devf="imei" value="${esc(dev.imei || '')}" placeholder="15-digit IMEI" required
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box;font-family:monospace" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">ICCID</label>
              <input data-devf="iccid" value="${esc(dev.iccid || '')}" placeholder="20-digit SIM ICCID"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box;font-family:monospace" />
            </div>
          </div>
        </div>

        <!-- Section 2: SIM & Connectivity Details -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-size:13.5px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">📶</span> <span>SIM & Connectivity Details</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">SIM Type</label>
              <select data-devf="sim_type" style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box">
                <option value="">Select SIM Type</option>
                <option value="E-SIM" ${dev.sim_type === 'E-SIM' ? 'selected' : ''}>E-SIM</option>
                <option value="Plastic SIM" ${dev.sim_type === 'Plastic SIM' ? 'selected' : ''}>Plastic SIM</option>
              </select>
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">SIM Provider</label>
              <input data-devf="sim_provider" value="${esc(dev.sim_provider || '')}" placeholder="e.g. Airtel, Vodafone, Jio"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">MSISDN 1 (Primary Phone)</label>
              <input data-devf="msisdn1" value="${esc(dev.msisdn1 || '')}" placeholder="Primary SIM Phone #"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">MSISDN 2 (Secondary Phone)</label>
              <input data-devf="msisdn2" value="${esc(dev.msisdn2 || '')}" placeholder="Secondary SIM Phone #"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Activation Plan</label>
              <input data-devf="activation_plan" value="${esc(dev.activation_plan || '')}" placeholder="e.g. 1 Year Standard"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
          </div>
        </div>

        <!-- Section 3: Dates & Timeline -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-size:13.5px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">📅</span> <span>Lifecycle Dates & Timeline</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Activation Date</label>
              <input type="date" data-devf="act_date" value="${esc(dev.act_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Expiry Date</label>
              <input type="date" data-devf="expiry_date" value="${esc(dev.expiry_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Dispatched Date</label>
              <input type="date" data-devf="dispatched_date" value="${esc(dev.dispatched_date || '')}"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
          </div>
        </div>

        <!-- Section 4: Specifications -->
        <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-size:13.5px;font-weight:800;color:var(--text);margin-bottom:12px;display:flex;align-items:center;gap:8px">
            <span style="font-size:16px">⚙️</span> <span>Hardware & Software Specs</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:12px">
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Model</label>
              <input data-devf="model" value="${esc(dev.model || '')}" placeholder="e.g. BST-01"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Firmware Version</label>
              <input data-devf="firmware" value="${esc(dev.firmware || '')}" placeholder="e.g. v2.1.0"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
            <div>
              <label style="font-size:12px;font-weight:700;margin-bottom:4px;display:block">Flash Memory</label>
              <input data-devf="flash" value="${esc(dev.flash || '')}" placeholder="e.g. 16MB SPI"
                style="width:100%;height:40px;padding:0 12px;border-radius:8px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;box-sizing:border-box" />
            </div>
          </div>
        </div>
      `;
    }

    
    async function openEditExpiryModal(devId) {
      try {
        toast('Loading device expiry details…');
        const dev = await api('/api/devices/' + devId);
        const currDate = dev.expiry_date || '';
        const imei = dev.imei || '—';
        const cname = dev.customer_name || 'Customer';

        const dlgHtml = `
          <div style="margin-bottom:14px">
            <div style="padding:14px 16px;background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;margin-bottom:16px">
              <div style="font-size:14px;font-weight:800;color:var(--text);margin-bottom:4px">Device #${dev.id} · IMEI: <code>${esc(imei)}</code></div>
              <div style="font-size:12.5px;color:var(--muted)">Customer: <b>${esc(cname)}</b> · SIM Type: <b>${esc(dev.sim_type || 'SIM')}</b></div>
              <div style="font-size:12.5px;color:var(--muted);margin-top:4px">Current Expiry Date: <b style="color:var(--primary)">${currDate ? esc(currDate) : 'Not Set'}</b></div>
            </div>
            <label for="newExpDateInput" style="display:block;font-size:12.5px;font-weight:800;margin-bottom:6px;color:var(--text)">
              New Expiry Date * (YYYY-MM-DD)
            </label>
            <input type="date" id="newExpDateInput" value="${esc(currDate)}" style="width:100%;height:44px;padding:0 14px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:14px;font-weight:600" required />
            <div id="newExpDateErr" style="color:var(--danger);font-size:12px;font-weight:700;margin-top:6px;display:none"></div>
          </div>
        `;

        openDlg('📅 Edit SIM Expiry Date', dlgHtml, 'Save Expiry Date', async () => {
          const inp = $('newExpDateInput');
          const errEl = $('newExpDateErr');
          const val = (inp ? inp.value : '').trim();

          if (!val) {
            if (errEl) { errEl.textContent = 'Please select a valid expiry date.'; errEl.style.display = 'block'; }
            throw new Error('Please select a valid expiry date.');
          }

          if (!/^\d{4}-\d{2}-\d{2}$/.test(val) || isNaN(Date.parse(val))) {
            if (errEl) { errEl.textContent = 'Invalid date format. Expected YYYY-MM-DD.'; errEl.style.display = 'block'; }
            throw new Error('Invalid date format.');
          }

          toast('Updating expiry date in database…');
          await api('/api/devices/' + dev.id + '/expiry-date', {
            method: 'PUT',
            body: JSON.stringify({ expiry_date: val })
          });
          toast('SIM expiry date permanently updated to ' + val);
          await fetchInventoryRows();
          await updateChrome();
        }, false);
      } catch(err) {
        fail(err);
      }
    }

    async function openEditDeviceModal(id) {
      try {
        toast('Loading record…');
        const dev = await api('/api/devices/' + id);
        if ($('devIcon')) $('devIcon').textContent = '✏️';
        if ($('devTitle')) $('devTitle').textContent = `Edit Device #${dev.id} (IMEI ${dev.imei || '—'})`;
        if ($('devSubTitle')) $('devSubTitle').textContent = `Customer: ${dev.customer_name || '—'} · SIM: ${dev.sim_type || 'SIM'}`;
        $('devFields').innerHTML = buildDeviceFormFields(dev);
        if ($('devErr')) { $('devErr').textContent = ''; $('devErr').style.display = 'none'; }
        if ($('devSave')) $('devSave').textContent = '💾 Save Changes';

        if ($('devCloseBtn')) $('devCloseBtn').onclick = () => $('devdlg').close();
        if ($('devCancel')) $('devCancel').onclick = () => $('devdlg').close();

        $('devform').onsubmit = async e => {
          e.preventDefault();
          const errEl = $('devErr');
          if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }
          const body = {};
          document.querySelectorAll('#devdlg [data-devf]').forEach(i => {
            const k = i.dataset.devf, v = i.value.trim();
            body[k] = v || null;
          });

          if (!body.customer_name) {
            if (errEl) { errEl.textContent = 'Customer Name is required.'; errEl.style.display = 'block'; }
            return;
          }
          if (!body.imei) {
            if (errEl) { errEl.textContent = 'IMEI is required.'; errEl.style.display = 'block'; }
            return;
          }

          const btnSave = $('devSave');
          if (btnSave) { btnSave.disabled = true; btnSave.textContent = 'Saving…'; }

          try {
            await api('/api/devices/' + dev.id, { method: 'PUT', body: JSON.stringify(body) });
            $('devdlg').close();
            toast(`✓ Device record #${dev.id} updated successfully`);
            if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
            if (typeof drawCustCards === 'function') drawCustCards();
            if (typeof refreshActiveContainer === 'function') refreshActiveContainer();
            else if (typeof loadInventoryContainer === 'function') loadInventoryContainer();
          } catch(err) {
            if (errEl) { errEl.textContent = err.message || 'Failed to update record'; errEl.style.display = 'block'; }
          } finally {
            if (btnSave) { btnSave.disabled = false; btnSave.textContent = '💾 Save Changes'; }
          }
        };
        $('devdlg').showModal();
      } catch(err) { fail(err); }
    }
    const devCancelBtn = $('devCancel');
    if (devCancelBtn) devCancelBtn.onclick = () => $('devdlg').close();

    
    
    let currentExportCustomer = null;

      function openExportColumnsModal(customer = null) {
        currentExportCustomer = customer;
        const dlg = $('dlgChooseExportCols');
        if (!dlg) return;

        const titleEl = dlg.querySelector('h3 span:last-child');
        const subEl = dlg.querySelector('p.sub');
        if (titleEl) {
          titleEl.textContent = customer ? `Choose Columns to Download — ${customer.name || 'Customer'}` : 'Choose Columns to Download (Excel)';
        }
        if (subEl) {
          subEl.textContent = customer
            ? `Select which columns you want to see in the exported Excel spreadsheet for ${customer.name || 'Customer'}.`
            : 'Select which columns you want to see in your exported Customer Inventory spreadsheet.';
        }

        const allAvailableCols = [
          { key: 'customer_name', label: 'Customer Name' },
          ...COLS.map(c => ({ key: c[0], label: c[1] })),
          ...(XC || []).map(c => ({ key: c, label: c.replace(/_/g, ' ') })),
          { key: 'added_by', label: 'Added By' },
          { key: 'created_at', label: 'Added On' }
        ];

        const listEl = $('exportColsList');
        if (listEl) {
          listEl.innerHTML = allAvailableCols.map(c => `
            <label class="col-pill-chip active" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border:1.5px solid var(--primary);background:var(--card-subtle);border-radius:20px;cursor:pointer;font-size:12px;font-weight:600;transition:all .15s">
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
              const cust = currentExportCustomer;
              const targetCid = cust ? cust.id : (typeof invCid !== 'undefined' ? invCid : '');
              const custName = cust ? cust.name : (targetCid ? `Customer #${targetCid}` : 'Customer Inventory');
              toast(`Exporting ${custName} with ${checked.length} selected columns…`);
              if (typeof showBstplLoader === 'function') showBstplLoader(`Generating Excel file for ${custName}…`);

              const targetQ = typeof invQ !== 'undefined' ? invQ : '';
              const targetCol = typeof invCol !== 'undefined' ? invCol : 'all';
              const queryUrl = `/api/devices?page=1&page_size=5000&q=${encodeURIComponent(targetQ)}&column=${targetCol}&sort_by=${sortCol}&sort_dir=${sortDir}${targetCid ? '&customer_id=' + targetCid : ''}`;
              const d = await api(queryUrl);

              const colMap = {};
              allAvailableCols.forEach(c => { colMap[c.key] = c.label; });

              const headers = ['ID', ...checked.map(k => colMap[k] || k)];
              const rows = (d.items || []).map(dev => [
                dev.id,
                ...checked.map(k => {
                  if (k === 'customer_name') return dev.customer_name || (cust ? cust.name : '');
                  if (dev.extra && dev.extra[k] !== undefined) return dev.extra[k] || '';
                  return dev[k] != null ? dev[k] : '';
                })
              ]);

              const fileName = (cust ? cust.name : 'Customer_Inventory_Export').replace(/[^a-zA-Z0-9_-]/g, '_');
              await exportExcel(fileName, headers, rows);
              toast(`✓ Successfully downloaded ${custName} with ${checked.length} selected columns!`);
            } catch(err) {
              fail(err);
            } finally {
              if (typeof hideBstplLoader === 'function') hideBstplLoader();
            }
          };
        }

        if (typeof dlg.showModal === 'function') dlg.showModal();
      }

      async function downloadSingleCustomerExcel(customer) {
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
    }

    
    
    const myRole = () => {
      const u = getUser();
      return u.role || (u.is_admin ? 'admin' : 'standard');
    };

    
    function avatarHtml(c) {
      const a = (c && c.avatar) || '';
      return a.startsWith('data:image/') ? `<img class="av" alt="" src="${esc(a)}">` : `<span class="av">${esc(a || '🏢')}</span>`;
    }

    function alertSummary(list) {
      if (!Array.isArray(list)) return '';
      const t = new Date(); t.setHours(0, 0, 0, 0);
      let x = 0, w = 0, m = 0;
      list.forEach(d => {
        if (!d.expiry_date) return;
        const n = Math.round((new Date(d.expiry_date) - t) / 864e5);
        if (n < 0) x++; else if (n <= 7) w++; else m++;
      });
      return `🔴 ${x} expired · 🟠 ${w} within 7 days · 🟡 ${m} within 30 days`;
    }

    async function loadCU() {
      try {
        const res = await api('/api/customers');
        if (Array.isArray(res)) CU = res;
      } catch(e) {}
      return CU;
    }

    async function updateChrome() {
      try {
        const u = getUser();
        const h = new Date().getHours();
        let greet = 'Good morning';
        if (h >= 12 && h < 17) greet = 'Good afternoon';
        else if (h >= 17) greet = 'Good evening';
        if ($('hi')) $('hi').textContent = `${greet}, ${u.name || u.user_id || 'Shilish Reddy'}`;
        const uInitial = ((u.name || u.user_id || 'U')[0] || 'U').toUpperCase();
        if ($('userAvatarCircle')) $('userAvatarCircle').textContent = uInitial;
        const r = (u.role || (u.is_admin ? 'admin' : 'standard')).toUpperCase();
        if ($('rolePill')) {
          $('rolePill').textContent = r;
          $('rolePill').className = `role-pill ${r.toLowerCase().includes('admin') ? 'admin' : 'standard'}`;
        }
      } catch(e) {}
    }

    
    // --- Branded 3D Loader & Notification System (Logo + Message on Search/Load) ---
    function showBstplLoader(msg = 'Searching & loading records…', pct = null) {
      let loader = $('cvGlobalLoader');
      if (!loader) {
        loader = document.createElement('div');
        loader.id = 'cvGlobalLoader';
        loader.className = 'cv-global-loader';
        loader.innerHTML = `
          <div class="cv-loader-backdrop"></div>
          <div class="cv-loader-card">
            <div class="cv-loader-logo-wrap">
              <div class="cv-loader-logo-3d">B</div>
            </div>
            <div class="cv-loader-brand-title">BSTPL <span>CustomerVault</span></div>
            <div class="cv-loader-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>
            <div class="cv-loader-msg" id="cvLoaderMsg">${esc(msg)}</div>
            <div class="cv-loader-progress"><div class="cv-loader-progress-bar"></div></div>
          </div>
        `;
        document.body.appendChild(loader);
      }
      const msgEl = $('cvLoaderMsg');
      if (msgEl && msg != null) msgEl.textContent = msg;
      const bar = loader.querySelector('.cv-loader-progress-bar');
      if (bar && pct != null) {
        bar.style.width = Math.max(0, Math.min(100, pct)) + '%';
      }
      loader.style.display = 'flex';
    }

    function updateBstplLoader(msg = null, pct = null) {
      let loader = $('cvGlobalLoader');
      if (!loader) {
        showBstplLoader(msg || 'Processing…', pct);
        return;
      }
      if (msg != null) {
        const msgEl = $('cvLoaderMsg');
        if (msgEl) msgEl.textContent = msg;
      }
      if (pct != null) {
        const bar = loader.querySelector('.cv-loader-progress-bar');
        if (bar) bar.style.width = Math.max(0, Math.min(100, pct)) + '%';
      }
    }

    function hideBstplLoader() {
      const loader = $('cvGlobalLoader');
      if (loader) loader.style.display = 'none';
    }

    // Compatibility aliases for BSTPI / BSTPL loader calls (Requirement 3)
    window.showBstplLoader = showBstplLoader;
    window.updateBstplLoader = updateBstplLoader;
    window.hideBstplLoader = hideBstplLoader;
    window.showBSTPILoader = showBstplLoader;
    window.updateBSTPILoader = updateBstplLoader;
    window.hideBSTPILoader = hideBstplLoader;

    // Minimal 3D Page Transitions while navigating between files (e.g. errors.html -> inventory.html)
    document.addEventListener('DOMContentLoaded', () => {
      document.querySelectorAll('a.cv-nav-item, .cv-header-actions a, a.nav-link, aside a').forEach(link => {
        link.addEventListener('click', e => {
          const href = link.getAttribute('href');
          if (href && !href.startsWith('#') && !href.startsWith('javascript:') && !link.target) {
            const currentFile = window.location.pathname.split('/').pop() || 'home.html';
            if (href !== currentFile) {
              e.preventDefault();
              document.body.classList.add('cv-page-3d-exit');
              const linkText = link.textContent.replace(/[^\w\s]/gi, '').trim();
              showBstplLoader(`Opening ${linkText || 'CustomerVault'}…`);
              setTimeout(() => { window.location.href = href; }, 160);
            }
          }
        });
      });
    });


    function openBulkEditImeiModal() {
      const dlg = $('dlgBulkEditImei');
      if (dlg && typeof dlg.showModal === 'function') {
        dlg.showModal();
      } else {
        window.location.href = 'edit-delete.html?mode=bulk-edit';
      }
    }

    function openBulkDeleteExcelModal() {
      const dlg = $('dlgBulkDeleteExcel');
      if (dlg && typeof dlg.showModal === 'function') {
        dlg.showModal();
      } else {
        window.location.href = 'edit-delete.html?mode=bulk-delete';
      }
    }

    function openAddColumnModal() {
      const dlg = $('dlgAddColumn');
      if (!dlg) return;
      if ($('newColName')) $('newColName').value = '';
      if ($('newColValue')) $('newColValue').value = '';
      if ($('newColImeis')) $('newColImeis').value = '';
      if ($('newColErr')) { $('newColErr').textContent = ''; $('newColErr').style.display = 'none'; }
      if ($('newColTarget')) $('newColTarget').value = 'all';
      if ($('newColCustWrap')) $('newColCustWrap').style.display = 'none';
      if ($('newColImeisWrap')) $('newColImeisWrap').style.display = 'none';

      // Populate customer options
      if ($('newColCustSel')) {
        let custOpts = '<option value="">-- Choose Customer --</option>';
        custOpts += (CU || []).map(c => `<option value="${c.id}">${esc(c.name || c.customer_name)}</option>`).join('');
        $('newColCustSel').innerHTML = custOpts;
        if (typeof invCid !== 'undefined' && invCid) $('newColCustSel').value = invCid;
      }

      if ($('newColTarget')) {
        $('newColTarget').onchange = () => {
          const t = $('newColTarget').value;
          if ($('newColCustWrap')) $('newColCustWrap').style.display = (t === 'customer') ? 'block' : 'none';
          if ($('newColImeisWrap')) $('newColImeisWrap').style.display = (t === 'specified') ? 'block' : 'none';
        };
      }

      if ($('closeDlgAddColumn')) $('closeDlgAddColumn').onclick = () => dlg.close();
      if ($('cancelDlgAddColumn')) $('cancelDlgAddColumn').onclick = () => dlg.close();

      if ($('formAddColumn')) {
        $('formAddColumn').onsubmit = async e => {
          e.preventDefault();
          if ($('newColErr')) { $('newColErr').textContent = ''; $('newColErr').style.display = 'none'; }
          const colName = ($('newColName')?.value || '').trim();
          if (!colName) {
            if ($('newColErr')) { $('newColErr').textContent = 'Please enter a column name.'; $('newColErr').style.display = 'block'; }
            return;
          }

          const target = $('newColTarget')?.value || 'all';
          let customerId = null;
          let imeis = null;

          if (target === 'customer') {
            const cid = parseInt($('newColCustSel')?.value);
            if (!cid) {
              if ($('newColErr')) { $('newColErr').textContent = 'Please select a customer.'; $('newColErr').style.display = 'block'; }
              return;
            }
            customerId = cid;
          } else if (target === 'specified') {
            const raw = ($('newColImeis')?.value || '').split(/[\r\n,]+/).map(s => s.trim()).filter(Boolean);
            if (!raw.length) {
              if ($('newColErr')) { $('newColErr').textContent = 'Please enter at least one IMEI.'; $('newColErr').style.display = 'block'; }
              return;
            }
            imeis = raw;
            if (typeof invCid !== 'undefined' && invCid) customerId = parseInt(invCid);
          } else if (target === 'all' && typeof invCid !== 'undefined' && invCid) {
            customerId = parseInt(invCid);
          }

          const val = $('newColValue')?.value || '';
          const btn = $('btnSubmitAddColumn');
          if (btn) { btn.disabled = true; btn.textContent = 'Adding Column…'; }

          try {
            const res = await api('/api/columns/add', {
              method: 'POST',
              body: JSON.stringify({
                column_name: colName,
                target: target,
                customer_id: customerId,
                imeis: imeis,
                value: val !== '' ? val : null
              })
            });
            dlg.close();
            toast(`Column "${res.column || colName}" added successfully`);
            if (typeof fetchInventoryRows === 'function') await fetchInventoryRows();
          } catch(err) {
            if ($('newColErr')) { $('newColErr').textContent = err.message || 'Failed to add column'; $('newColErr').style.display = 'block'; }
          } finally {
            if (btn) { btn.disabled = false; btn.textContent = '➕ Add Column'; }
          }
        };
      }

      if (typeof dlg.showModal === 'function') dlg.showModal();
    }

    function openAddDeviceModal() {
      const dlg = $('devdlg');
      if (!dlg) return;
      if ($('devIcon')) $('devIcon').textContent = '📱';
      if ($('devTitle')) $('devTitle').textContent = 'Add Device Record';
      if ($('devSubTitle')) $('devSubTitle').textContent = 'Register a new SIM / hardware record into customer inventory';
      $('devFields').innerHTML = buildDeviceFormFields();
      if ($('devErr')) { $('devErr').textContent = ''; $('devErr').style.display = 'none'; }
      if ($('devSave')) $('devSave').textContent = '➕ Create Record';

      if ($('devCloseBtn')) $('devCloseBtn').onclick = () => dlg.close();
      if ($('devCancel')) $('devCancel').onclick = () => dlg.close();

      $('devform').onsubmit = async e => {
        e.preventDefault();
        const errEl = $('devErr');
        if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }
        const body = {};
        document.querySelectorAll('#devdlg [data-devf]').forEach(i => {
          const k = i.dataset.devf, v = i.value.trim();
          if (v) body[k] = v;
        });
        const extra = {};
        document.querySelectorAll('#devdlg [data-devx]').forEach(i => {
          const k = i.dataset.devx, v = i.value.trim();
          if (v) extra[k] = v;
        });
        if (Object.keys(extra).length) body.extra = extra;

        if (!body.customer_name) {
          if (errEl) { errEl.textContent = 'Customer Name is required.'; errEl.style.display = 'block'; }
          return;
        }
        if (!body.imei) {
          if (errEl) { errEl.textContent = 'IMEI is required.'; errEl.style.display = 'block'; }
          return;
        }

        const btnSave = $('devSave');
        if (btnSave) { btnSave.disabled = true; btnSave.textContent = 'Creating Record…'; }

        try {
          await api('/api/devices', { method: 'POST', body: JSON.stringify(body) });
          dlg.close();
          toast(`✓ Device record (IMEI ${body.imei}) created successfully`);
          await loadCU();
          await updateChrome();
          if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
          if (typeof drawCustCards === 'function') drawCustCards();
          if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
        } catch (err) {
          if (errEl) { errEl.textContent = err.message || 'Failed to create record'; errEl.style.display = 'block'; }
        } finally {
          if (btnSave) { btnSave.disabled = false; btnSave.textContent = '➕ Create Record'; }
        }
      };
      if (typeof dlg.showModal === 'function') dlg.showModal();
    }

    function loadCustomModels() {
      const sel = $('optModel');
      if (!sel) return;
      try {
        const saved = JSON.parse(localStorage.getItem('custom_models') || '[]');
        sel.querySelectorAll('.custom-model-opt').forEach(o => o.remove());
        const newOpt = sel.querySelector('option[value="__new__"]');
        saved.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m;
          opt.textContent = m;
          opt.className = 'custom-model-opt';
          if (newOpt) sel.insertBefore(opt, newOpt);
          else sel.appendChild(opt);
        });
      } catch(e) {}
    }

    function showEventPopup(opts) {
      opts = opts || {};
      const title = opts.title || 'Notification';
      const message = opts.message || '';
      const dlg = $('dlgEventPopup');
      if (!dlg || typeof dlg.showModal !== 'function') {
        toast((title ? title + ': ' : '') + message);
        return;
      }
      if ($('eventPopupTitle')) $('eventPopupTitle').textContent = title;
      if ($('eventPopupMessage')) $('eventPopupMessage').textContent = message;
      try {
        dlg.showModal();
        setTimeout(() => { try { dlg.close(); } catch(e){} }, opts.duration || 3500);
      } catch(e) { toast(message); }
    }


    // Live sidebar telemetry
    function updateLiveStreamClock() {
      const el = $('sbLiveTime');
      if (!el) return;
      const now = new Date();
      el.textContent = 'Live • ' + now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    if (typeof setInterval === 'function') setInterval(updateLiveStreamClock, 1000);
    updateLiveStreamClock();


    // --- Universal Inter-Page Interlinking & Data Synchronization System ---
    let lastKnownDbUpdate = parseInt(localStorage.getItem('customervault_db_updated') || '0', 10);

    function notifyDataUpdated(detail = {}) {
      const now = Date.now();
      lastKnownDbUpdate = now;
      try {
        localStorage.setItem('customervault_db_updated', String(now));
        if (window.BroadcastChannel) {
          const bc = new BroadcastChannel('customervault_sync_channel');
          bc.postMessage({ type: 'DB_UPDATED', timestamp: now, detail });
          bc.close();
        }
      } catch (e) {}
    }
    window.notifyDataUpdated = notifyDataUpdated;

    async function syncGlobalMetricsAndChrome() {
      try {
        const [statsRes, custsRes] = await Promise.all([
          api('/api/stats').catch(() => null),
          api('/api/customers').catch(() => null)
        ]);

        if (statsRes) {
          S = statsRes;
          const devTotal = statsRes.total_devices != null ? statsRes.total_devices : (statsRes.devices || 0);
          const custTotal = statsRes.total_customers != null ? statsRes.total_customers : (statsRes.customers || 0);
          const errTotal = statsRes.errored_records != null ? statsRes.errored_records : 0;
          const cartTotal = statsRes.deleted_devices != null ? statsRes.deleted_devices : (statsRes.deleted || 0);
          const exp30Total = statsRes.expiring_30_days != null ? statsRes.expiring_30_days : (statsRes.total_expiring || 0);
          const expiredTotal = statsRes.expired != null ? statsRes.expired : (statsRes.total_expired || 0);

          // Update sidebar badges and widgets
          if ($('sbLiveDevCount')) $('sbLiveDevCount').textContent = Number(devTotal).toLocaleString();
          if ($('sbLiveCustCount')) $('sbLiveCustCount').textContent = Number(custTotal).toLocaleString();
          if ($('sidebarErrorsBadge')) {
            $('sidebarErrorsBadge').textContent = Number(errTotal).toLocaleString();
            $('sidebarErrorsBadge').style.display = errTotal > 0 ? 'inline-block' : 'none';
          }
          if ($('invCustCountBadge')) $('invCustCountBadge').textContent = Number(custTotal).toLocaleString();
          if ($('topCartCountBadge')) $('topCartCountBadge').textContent = cartTotal;
          if ($('cartCountText')) $('cartCountText').textContent = cartTotal;
          if ($('simRestoreCountBadge')) $('simRestoreCountBadge').textContent = `${Number(cartTotal).toLocaleString()} records`;

          // Update Home Overview & Live Stream KPI cards if present
          if ($('kpiDev')) $('kpiDev').textContent = Number(devTotal).toLocaleString();
          if ($('statUniqueColumns')) $('statUniqueColumns').textContent = Number(statsRes.unique_columns || 74).toLocaleString();
          if ($('invColumnsBadge')) $('invColumnsBadge').textContent = `${Number(statsRes.unique_columns || 74).toLocaleString()} Columns`;
          if ($('kpiCust')) $('kpiCust').textContent = Number(custTotal).toLocaleString();
          if ($('kpiExp30')) $('kpiExp30').textContent = Number(exp30Total).toLocaleString();
          if ($('kpiExpired')) $('kpiExpired').textContent = Number(expiredTotal).toLocaleString();
        }

        if (custsRes && Array.isArray(custsRes)) {
          CU = custsRes;
          if ($('invCustCountBadge')) $('invCustCountBadge').textContent = CU.length.toLocaleString();
          if (typeof populateNfCustomerDropdown === 'function') populateNfCustomerDropdown();
          if (typeof populateBfCustomerFilter === 'function') populateBfCustomerFilter();
          if (typeof populateLiveCustomerDropdown === 'function') populateLiveCustomerDropdown();
          if (typeof refreshUploadCustDropdown === 'function') refreshUploadCustDropdown();
        }
      } catch(e) {
        console.warn('Sync metrics error:', e);
      }
    }
    window.syncGlobalMetricsAndChrome = syncGlobalMetricsAndChrome;

    let _refreshDebounceTimer = null;
    function triggerLivePageRefresh() {
      clearTimeout(_refreshDebounceTimer);
      _refreshDebounceTimer = setTimeout(async () => {
        await syncGlobalMetricsAndChrome();

        // Dynamically re-fetch container data on active page
        const path = window.location.pathname.toLowerCase();
        if (path.endsWith('home.html') || path.endsWith('dashboard.html') || path.endsWith('index.html')) {
          if (typeof updateHomeStatsRibbon === 'function') updateHomeStatsRibbon();
          if (typeof updateHomeExpiryBanner === 'function') updateHomeExpiryBanner();
          if (typeof runLiveCycle === 'function') runLiveCycle(true);
          if (typeof loadHealthContainer === 'function') loadHealthContainer();
        } else if (path.endsWith('inventory.html')) {
          if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
          if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
        } else if (path.endsWith('sim-upload.html')) {
          if (typeof refreshUploadCustDropdown === 'function') refreshUploadCustDropdown();
          if (typeof updateSimRestoreCount === 'function') updateSimRestoreCount();
        } else if (path.endsWith('fetch-data.html')) {
          if (typeof populateNfCustomerDropdown === 'function') populateNfCustomerDropdown();
          if (typeof populateBfCustomerFilter === 'function') populateBfCustomerFilter();
          if (typeof runNormalFetch === 'function' && $('fq') && $('fq').value.trim()) runNormalFetch();
        } else if (path.endsWith('edit-delete.html')) {
          if (typeof runSearch === 'function' && $('qImei') && $('qImei').value.trim()) runSearch();
        } else if (path.endsWith('alerts.html')) {
          if (typeof loadExpiryContainer === 'function') loadExpiryContainer();
        } else if (path.endsWith('errors.html')) {
          if (typeof loadErrorsContainer === 'function') loadErrorsContainer();
        } else if (path.endsWith('settings.html')) {
          if (typeof loadSettingsPage === 'function') loadSettingsPage();
        }
      }, 200);
    }
    window.triggerLivePageRefresh = triggerLivePageRefresh;

    // Cross-tab broadcast listener
    if (window.BroadcastChannel) {
      try {
        const syncBc = new BroadcastChannel('customervault_sync_channel');
        syncBc.onmessage = e => {
          if (e.data && e.data.type === 'DB_UPDATED') {
            lastKnownDbUpdate = e.data.timestamp;
            triggerLivePageRefresh();
          }
        };
      } catch (e) {}
    }

    // Storage event listener (cross-window fallback)
    window.addEventListener('storage', e => {
      if (e.key === 'customervault_db_updated') {
        const ts = parseInt(e.newValue || '0', 10);
        if (ts > lastKnownDbUpdate) {
          lastKnownDbUpdate = ts;
          triggerLivePageRefresh();
        }
      }
    });

    // Window focus listener: When user switches back to this tab/window, refresh immediately
    window.addEventListener('focus', () => {
      const cur = parseInt(localStorage.getItem('customervault_db_updated') || '0', 10);
      if (cur > lastKnownDbUpdate) {
        lastKnownDbUpdate = cur;
        triggerLivePageRefresh();
      } else {
        syncGlobalMetricsAndChrome();
      }
    });

    syncGlobalMetricsAndChrome();

    const toggleLiveBtn = $('sidebarToggleLiveBtn');
    if (toggleLiveBtn) {
      toggleLiveBtn.onclick = function() {
        if (this.classList.contains('on')) {
          this.classList.remove('on');
          this.classList.add('off');
          this.textContent = 'OFF';
          toast('Live stream paused');
        } else {
          this.classList.remove('off');
          this.classList.add('on');
          this.textContent = 'ON';
          toast('Live stream active');
          updateSidebarStats();
        }
      };
    }

    // Sub-view switcher for Inventory and Upload
    let currentInvSubView = 'devices';
    function switchInvSubView(view) {
      currentInvSubView = view;
      document.querySelectorAll('.inv-sub-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.sub === view);
      });
      const vDev = $('subViewDevices'), vCust = $('subViewCust'), vUpl = $('subViewUpload');
      if (vDev) vDev.hidden = (view !== 'devices');
      if (vCust) vCust.hidden = (view !== 'cust');
      if (vUpl) vUpl.hidden = (view !== 'upload');

      if (view === 'devices') {
        if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
      } else if (view === 'cust') {
        if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
      } else if (view === 'upload') {
        if (typeof initBulkUploadContainer === 'function') initBulkUploadContainer();
      }
    }


async function loadInventoryContainer() {
        const staff = canDeleteValidInventory();
        $('invAddDev').hidden = false;  // every role may add data

        document.querySelectorAll('.inv-sub-btn').forEach(b => {
          b.onclick = () => switchInvSubView(b.dataset.sub);
        });

        if ($('btnViewUploadedInInv')) $('btnViewUploadedInInv').onclick = () => switchInvSubView('devices');
        if ($('btnViewCustAfterUpload')) $('btnViewCustAfterUpload').onclick = () => switchInvSubView('cust');

        $('invCustSel').onchange = e => { invCid = e.target.value; invPage = 1; fetchInventoryRows(); };
        $('invColSel').onchange = e => { invCol = e.target.value; invPage = 1; fetchInventoryRows(); };
        let invDebounce;
        $('invQuery').oninput = e => { invQ = e.target.value; invPage = 1; clearTimeout(invDebounce); invDebounce = setTimeout(fetchInventoryRows, 250); };
        $('invClear').onclick = () => { invQ = ''; invCol = 'all'; invCid = ''; invPage = 1; $('invCustSel').value = ''; $('invColSel').value = 'all'; $('invQuery').value = ''; fetchInventoryRows(); };
        $('invAddDev').onclick = openAddDeviceModal;
        if ($('invAddColumn')) $('invAddColumn').onclick = openAddColumnModal;
        $('invExport').onclick = openExportColumnsModal;
        if ($('btnBulkEditImei')) $('btnBulkEditImei').onclick = openBulkEditImeiModal;
        if ($('btnBulkDeleteImei')) {
          $('btnBulkDeleteImei').onclick = () => {
            if (!canDeleteValidInventory()) {
              toast('Access Denied: Master Admins do not have permission to delete inventory records.');
              return;
            }
            openBulkDeleteExcelModal();
            if ($('selBulkDelDbCol')) $('selBulkDelDbCol').value = 'imei';
            if ($('bulkDelTargetColBadge')) $('bulkDelTargetColBadge').textContent = 'Matching Column: IMEI';
          };
          $('btnBulkDeleteImei').hidden = !canDeleteValidInventory();
        }
        if ($('btnBulkDeleteExcel')) {
          $('btnBulkDeleteExcel').onclick = openBulkDeleteExcelModal;
          $('btnBulkDeleteExcel').hidden = !canDeleteValidInventory();
        }

        // --- 1. Dynamic Subnav & Badge Count ---
        if ($('invCustCountBadge')) $('invCustCountBadge').textContent = (CU || []).length || 0;

        // --- 2. Customer Cards Grid & Search (Clean Responsive Grid Layout) ---
        const card = c => {
          const devs = Number(c.devices || 0);
          const exp = Number(c.expiring_or_expired || 0);
          const isStaff = myRole() !== 'limited';
          const canDel = canDeleteValidInventory();

          return `
          <div class="cw customer-file-card" data-cid="${c.id}">
            <div>
              <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:12px;min-width:0">
                  ${avatarHtml(c)}
                  <div style="min-width:0">
                    <b style="font-size:15.5px;font-weight:800;color:var(--text);display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${esc(c.name)}">${esc(c.name)}</b>
                    <span style="font-size:12px;color:var(--muted);font-weight:600">Customer ID: #${c.id}</span>
                  </div>
                </div>
                <span class="tag ${devs > 0 ? 'ok' : 'mut'}" style="font-size:11px;font-weight:700;flex-shrink:0">${devs > 0 ? 'Active' : 'Empty'}</span>
              </div>
              <div style="font-size:13px;color:var(--muted);margin-top:8px;line-height:1.4;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                <span style="display:inline-flex;align-items:center;gap:4px;background:var(--card-subtle);padding:3px 8px;border-radius:6px;border:1px solid var(--line);font-size:12px">
                  <span>📱</span> <b style="color:var(--text);font-weight:800">${devs.toLocaleString()}</b> records
                </span>
                ${exp > 0 ? `
                <span style="display:inline-flex;align-items:center;gap:4px;background:rgba(245,158,11,0.1);color:var(--warn);border:1px solid rgba(245,158,11,0.25);padding:3px 8px;border-radius:6px;font-size:12px;font-weight:700">
                  <span>⚠️</span> ${exp.toLocaleString()} expiring
                </span>` : ''}
              </div>
            </div>
            <div class="ca" style="display:flex;gap:6px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:14px">
              <button class="b p" data-cview="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="View all device records for this customer">👁️ Files</button>
              <button class="b" data-cdl="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="Download Excel with all columns and values">📥 Download</button>
              <button class="b" data-cren="${c.id}" style="font-size:12px;padding:6px 10px;font-weight:700" title="Rename customer portfolio">✏️ Rename</button>
              ${isStaff ? `<button class="b" data-cmerge="${c.id}" style="font-size:12px;padding:6px 10px;font-weight:700" title="Merge into another customer">🔀 Merge</button>
              <button class="b" data-cav="${c.id}" style="font-size:12px;padding:6px 8px" title="Change icon">🎨</button>` : ''}
              ${canDel ? `<button class="b d" data-cdel="${c.id}" style="font-size:12px;padding:6px 10px;font-weight:700" title="Delete customer portfolio">🗑️ Delete</button>` : ''}
            </div>
          </div>`;
        };

        const drawCustCards = () => {
          const inp = $('cs');
          const q = (inp ? inp.value : '').trim().toLowerCase();
          const clearBtn = $('csClearBtn');
          if (clearBtn) clearBtn.style.display = q ? 'block' : 'none';

          const filtered = (CU || []).filter(c => (c.name || '').toLowerCase().includes(q));
          if ($('csFilterCount')) {
            $('csFilterCount').textContent = q ? `Showing ${filtered.length} of ${CU.length} portfolios` : `Showing all ${CU.length} customer portfolios`;
          }

          const gridHtml = filtered.map(card).join('');
          $('cgrid').innerHTML = custHide ? '<div class="empty">Customer cards are hidden.</div>' : `
            <div class="customer-file-grid">
              ${gridHtml || `<div class="empty">${CU.length ? 'No customer matches your search.' : 'No customers found.'}</div>`}
            </div>`;
        };

        window.drawCustCards = drawCustCards;

        if ($('cs')) $('cs').oninput = drawCustCards;
        if ($('csClearBtn')) {
          $('csClearBtn').onclick = () => {
            if ($('cs')) $('cs').value = '';
            $('csClearBtn').style.display = 'none';
            drawCustCards();
          };
        }

        await loadCustomerFilesContainer();

        // --- 3. Files Option as View Option: Display All Entries for Customer ---
        async function openCustomerEntriesView(customer) {
          try {
            toast(`Loading entries for ${customer.name}…`);
            if (typeof showBstplLoader === 'function') showBstplLoader(`Fetching all entries for ${customer.name}…`);

            const res = await api(`/api/devices?customer_id=${customer.id}&page_size=5000`);
            const items = (res && res.items) ? res.items : [];

            // Discover all dynamic columns
            const extraKeys = new Set();
            items.forEach(it => {
              if (it.extra && typeof it.extra === 'object') {
                Object.keys(it.extra).forEach(k => extraKeys.add(k));
              }
            });
            const allExtras = Array.from(new Set([...XC, ...extraKeys]));

            const viewCols = [
              { key: 'id', label: 'ID' },
              { key: 'customer_name', label: 'Customer' },
              ...COLS.map(c => ({ key: c[0], label: c[1] })),
              ...allExtras.map(k => ({ key: k, label: k.replace(/_/g, ' ').toUpperCase() })),
              { key: 'added_by', label: 'Added By' },
              { key: 'created_at', label: 'Created At' }
            ];

            const dlgHtml = `
              <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:14px;border-bottom:1px solid var(--line);padding-bottom:12px">
                <div>
                  <h4 style="margin:0;font-size:15px;color:var(--text)">${esc(customer.name)}</h4>
                  <span style="font-size:12.5px;color:var(--muted)">${items.length.toLocaleString()} device entries</span>
                </div>
                <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
                  <div class="cv-search-container" style="min-width:200px">
                    <span class="cv-search-icon-left">🔎</span>
                    <input id="dlgViewCustSearch" class="cv-search-input" style="height:34px;font-size:12.5px" placeholder="Search within entries…" />
                  </div>
                  <button type="button" class="b p" id="btnDlgCustDlExcel" style="font-size:12.5px;font-weight:700">📥 Download Excel</button>
                  <button type="button" class="b" id="btnDlgJumpToEditor" style="font-size:12.5px">📋 Edit in Inventory</button>
                </div>
              </div>
              <div class="tw" style="max-height:56vh;overflow:auto" id="dlgCustViewTableWrap">
                <table style="font-size:12px">
                  <thead>
                    <tr>
                      ${viewCols.map(c => `<th>${esc(c.label)}</th>`).join('')}
                    </tr>
                  </thead>
                  <tbody>
                    ${items.length ? items.map(d => `
                      <tr>
                        <td><b>${d.id}</b></td>
                        <td>${esc(customer.name)}</td>
                        ${COLS.map(c => `<td>${cell(d, c[0])}</td>`).join('')}
                        ${allExtras.map(k => `<td>${esc((d.extra || {})[k] != null ? (d.extra || {})[k] : '')}</td>`).join('')}
                        <td>${esc(d.added_by || '')}</td>
                        <td>${esc(d.created_at || '')}</td>
                      </tr>
                    `).join('') : '<tr><td colspan="30" class="empty">No device entries found for this customer.</td></tr>'}
                  </tbody>
                </table>
              </div>
            `;

            openDlg(`📁 Customer Entries — ${customer.name} (${items.length.toLocaleString()})`, dlgHtml, 'Close', async () => {});

            if ($('dlgViewCustSearch')) {
              $('dlgViewCustSearch').oninput = e => {
                const term = e.target.value.toLowerCase().trim();
                const rows = document.querySelectorAll('#dlgCustViewTableWrap tbody tr');
                rows.forEach(r => {
                  r.style.display = (!term || r.textContent.toLowerCase().includes(term)) ? '' : 'none';
                });
              };
            }

            if ($('btnDlgCustDlExcel')) {
              $('btnDlgCustDlExcel').onclick = () => downloadSingleCustomerExcel(customer);
            }

            if ($('btnDlgJumpToEditor')) {
              $('btnDlgJumpToEditor').onclick = () => {
                closeDlg();
                if ($('invCustSel')) $('invCustSel').value = customer.id;
                invCid = customer.id;
                invPage = 1;
                switchInvSubView('devices');
              };
            }
          } catch(err) {
            fail(err);
          } finally {
            if (typeof hideBstplLoader === 'function') hideBstplLoader();
          }
        }

        // --- 4. Single Customer Excel Download with ALL Columns & Values ---
        async function downloadSingleCustomerExcel(customer) {
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
        function openDownloadAllColumnChooser() {
          const allCols = [
            { key: 'id', label: 'ID', checked: true },
            { key: 'customer_name', label: 'Customer Name', checked: true },
            ...COLS.map(c => ({ key: c[0], label: c[1], checked: true })),
            ...XC.map(c => ({ key: c, label: c.replace(/_/g, ' ').toUpperCase(), checked: true })),
            { key: 'added_by', label: 'Added By', checked: false },
            { key: 'created_at', label: 'Created At', checked: false }
          ];

          const dlgHtml = `
            <div style="margin-bottom:12px">
              <p style="font-size:13px;color:var(--text);margin:0 0 10px">
                Choose the columns to include in the multi-customer workbook. <b>Each customer will have an individual sheet named after the customer</b>.
              </p>
              <div style="display:flex;gap:8px;margin-bottom:10px">
                <button type="button" class="b" id="btnDlgChooseSelectAll" style="font-size:12px;padding:4px 10px">Select All</button>
                <button type="button" class="b" id="btnDlgChooseDeselectAll" style="font-size:12px;padding:4px 10px">Deselect All</button>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px;max-height:46vh;overflow:auto;padding:8px;border:1px solid var(--line);border-radius:10px;background:var(--card-subtle)" id="dlgChooseColList">
              ${allCols.map(col => `
                <label style="display:flex;align-items:center;gap:8px;font-size:12px;padding:6px 10px;background:var(--card);border:1px solid var(--line);border-radius:6px;cursor:pointer">
                  <input type="checkbox" class="export-col-chk" value="${col.key}" data-label="${esc(col.label)}" ${col.checked ? 'checked' : ''} style="width:16px;height:16px;margin:0" />
                  <span>${esc(col.label)}</span>
                </label>
              `).join('')}
            </div>
          `;

          openDlg('📥 Download All Customers (Individual Sheets)', dlgHtml, '🚀 Download Workbook', async () => {
            const checkedInps = Array.from(document.querySelectorAll('.export-col-chk:checked'));
            if (!checkedInps.length) throw new Error('Please select at least one column to download.');
            const chosenCols = checkedInps.map(inp => ({ key: inp.value, label: inp.dataset.label }));
            await executeMultiCustomerDownload(chosenCols);
          });

          if ($('btnDlgChooseSelectAll')) {
            $('btnDlgChooseSelectAll').onclick = () => {
              document.querySelectorAll('.export-col-chk').forEach(c => c.checked = true);
            };
          }
          if ($('btnDlgChooseDeselectAll')) {
            $('btnDlgChooseDeselectAll').onclick = () => {
              document.querySelectorAll('.export-col-chk').forEach(c => c.checked = false);
            };
          }
        }

        async function executeMultiCustomerDownload(chosenCols) {
          try {
            toast('Fetching database records for multi-sheet workbook…');
            if (typeof showBstplLoader === 'function') {
              showBstplLoader('Generating multi-sheet Excel workbook with customer sheets…');
            }

            const [custs, rawDevs] = await Promise.all([
              api('/api/customers'),
              api('/api/devices?page=1&page_size=100000')
            ]);

            const customers = Array.isArray(custs) ? custs : (CU || []);
            const devices = (rawDevs && Array.isArray(rawDevs.items)) ? rawDevs.items : [];

            if (!customers.length) {
              toast('No customers found.');
              return;
            }

            const devsByCust = new Map();
            devices.forEach(d => {
              const cid = d.customer_id;
              if (!devsByCust.has(cid)) devsByCust.set(cid, []);
              devsByCust.get(cid).push(d);
            });

            const wb = XLSX.utils.book_new();
            let sheetsCount = 0;

            customers.forEach(c => {
              const custDevs = devsByCust.get(c.id) || [];
              let sheetName = (c.name || `Customer_${c.id}`).replace(/[\\/?*\[\]:]/g, '_').trim();
              if (!sheetName) sheetName = `Customer_${c.id}`;
              if (sheetName.length > 31) sheetName = sheetName.substring(0, 31);

              let uniqueName = sheetName;
              let counter = 1;
              while (wb.SheetNames.includes(uniqueName)) {
                uniqueName = sheetName.substring(0, 28) + '_' + counter++;
              }

              const headers = chosenCols.map(col => col.label);
              const rows = custDevs.map(d => chosenCols.map(col => {
                if (col.key === 'id') return d.id;
                if (col.key === 'customer_name') return c.name;
                if (col.key in d) return d[col.key] != null ? d[col.key] : '';
                if (d.extra && col.key in d.extra) return d.extra[col.key] != null ? d.extra[col.key] : '';
                return '';
              }));

              const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
              XLSX.utils.book_append_sheet(wb, ws, uniqueName);
              sheetsCount++;
            });

            const dateStr = new Date().toISOString().slice(0, 10);
            XLSX.writeFile(wb, `BSTPL_CustomerVault_All_Portfolios_${dateStr}.xlsx`);
            toast(`Multi-customer workbook downloaded with ${sheetsCount} customer sheets!`);
          } catch(err) {
            fail(err);
          } finally {
            if (typeof hideBstplLoader === 'function') hideBstplLoader();
          }
        }

        if ($('btnDownloadAllCustData')) {
          $('btnDownloadAllCustData').onclick = openDownloadAllColumnChooser;
        }

        
        // Delegate Customer Card Actions
        if ($('cgrid')) {
          $('cgrid').onclick = async e => {
            const btn = e.target.closest('button');
            if (!btn) return;
            const cid = btn.dataset.cview || btn.dataset.cdl || btn.dataset.c || btn.dataset.cfiles || btn.dataset.cren || btn.dataset.cmerge || btn.dataset.cdel || btn.dataset.cav;
            if (!cid) return;

            const customer = (CU || []).find(x => String(x.id) === String(cid)) || { id: parseInt(cid, 10), name: `Customer #${cid}` };

            if (btn.dataset.cview || btn.dataset.cfiles) {
              await openCustomerEntriesView(customer);
              return;
            }
            if (btn.dataset.cdl) {
              await downloadSingleCustomerExcel(customer);
              return;
            }
            if (btn.dataset.cren) {
              if (typeof openSingleCustomerRename === 'function') openSingleCustomerRename(customer.id);
              else {
                openDlg('Rename Customer', `<label>New Customer Name</label><input id="renCustInp" value="${esc(customer.name)}" required />`, 'Save Name', async () => {
                  const nn = ($('renCustInp').value || '').trim();
                  if (!nn) throw new Error('Name cannot be blank');
                  await api('/api/customers/' + customer.id, { method: 'PATCH', body: JSON.stringify({ name: nn }) });
                  toast('Customer renamed successfully');
                  await loadCU(); await updateChrome(); drawCustCards();
                });
              }
              return;
            }
            if (btn.dataset.cmerge) {
              if (typeof openMergeCustomerModal === 'function') openMergeCustomerModal(customer.id);
              return;
            }
            if (btn.dataset.cdel) {
              if (typeof openDeleteCustomerEntriesModal === 'function') openDeleteCustomerEntriesModal(customer.id);
              else {
                const ok = await cv.confirm('Move customer portfolio "' + customer.name + '" and all its entries to the Cart?');
                if (ok) {
                  await api('/api/customers/' + customer.id, { method: 'DELETE' });
                  toast('Customer moved to Cart');
                  await loadCU(); await updateChrome(); drawCustCards();
                }
              }
              return;
            }
            if (btn.dataset.cav) {
              if (typeof editCustAvatar === 'function') editCustAvatar(customer);
              return;
            }
            if (btn.dataset.c) {
              if ($('invCustSel')) $('invCustSel').value = customer.id;
              invCid = customer.id;
              invPage = 1;
              switchInvSubView('devices');
              fetchInventoryRows();
              return;
            }
          };
        }

        initBulkUploadContainer();
        switchInvSubView(currentInvSubView);
      }

      async function fetchInventoryRows() {
        try {
          const expFilter = ($('invExpiryFilter') ? $('invExpiryFilter').value : 'all') || 'all';
          showBstplLoader('Fetching inventory records from database…');

          const activeSortCol = (expFilter !== 'all' && (!sortCol || sortCol === 'id')) ? 'expiry_date' : sortCol;
          const activeSortDir = (expFilter !== 'all' && (!sortCol || sortCol === 'id')) ? 'asc' : sortDir;
          const [d, expSummary] = await Promise.all([
            api(`/api/devices?page=${invPage}&page_size=10&q=${encodeURIComponent(invQ)}&column=${invCol}&expiry_filter=${expFilter}&sort_by=${activeSortCol}&sort_dir=${activeSortDir}${invCid ? '&customer_id=' + invCid : ''}`),
            api(`/api/devices/expiry-summary${invCid ? '?customer_id=' + invCid : ''}`).catch(() => null)
          ]);

          // Update Expiry Alert Banner (Requirement 9)
          const invBanner = $('invExpiryAlertBanner');
          if (expSummary) {
            const nExp = Number(expSummary.expired_count) || 0;
            const nSoon = Number(expSummary.expiring_30_days) || 0;
            if (invBanner) {   // inline display:flex beats the hidden attribute, so drive display directly
              invBanner.hidden = !(nExp || nSoon);
              invBanner.style.display = (nExp || nSoon) ? 'flex' : 'none';
            }
            if ($('invExpiryAlertText')) {
              $('invExpiryAlertText').textContent = `${nExp.toLocaleString()} SIM(s) have already expired, and ${nSoon.toLocaleString()} are expiring within 30 days.`;
            }
            if ($('cntExpiredBadge')) $('cntExpiredBadge').textContent = nExp.toLocaleString();
            if ($('cntExpiringSoonBadge')) $('cntExpiringSoonBadge').textContent = nSoon.toLocaleString();
          } else if ($('invExpiryAlertText')) {
            $('invExpiryAlertText').textContent = 'Could not load SIM expiry counts.';
          }

          const s = (d.page - 1) * 10;
          const staff = canDeleteValidInventory();
          const act = dev => `
      <div style="display:flex;gap:6px;align-items:center;flex-wrap:nowrap">
        <button class="b" data-editdev="${dev.id}" title="Edit device record" style="height:28px;padding:0 8px;font-size:11.5px;font-weight:700">✏️ Edit</button>
        <button class="b" data-editexp="${dev.id}" title="Edit SIM Expiry Date" style="height:28px;padding:0 8px;font-size:11.5px;font-weight:700">📅 Expiry</button>
        ${staff ? `<button class="b d" data-del="${dev.id}" title="Delete record (Move to Cart)" style="height:28px;padding:0 8px;font-size:11.5px;font-weight:700">🗑️ Delete</button>` : ''}
      </div>`;

          $('invTableWrap').innerHTML = `
      <div class="meta">
        <span>${d.total.toLocaleString()} records · showing ${d.total ? s + 1 : 0}–${s + d.items.length}</span>
        <div class="pg">
          <button class="b" id="invPrev" ${invPage < 2 ? 'disabled' : ''}>Prev</button>
          <span>Page ${d.page} of ${d.pages}</span>
          <button class="b" id="invNext" ${invPage >= d.pages ? 'disabled' : ''}>Next</button>
        </div>
      </div>
      ${renderTable(d.items, act)}`;

          if ($('invPrev')) $('invPrev').onclick = () => { invPage--; fetchInventoryRows(); };
          if ($('invNext')) $('invNext').onclick = () => { invPage++; fetchInventoryRows(); };

          // Wire click events inside invTableWrap
          if ($('invTableWrap')) {
            $('invTableWrap').onclick = async e => {
              const editBtn = e.target.closest('[data-editdev]');
              if (editBtn) {
                openEditDeviceModal(editBtn.dataset.editdev);
                return;
              }
              const expBtn = e.target.closest('[data-editexp]');
              if (expBtn) {
                openEditExpiryModal(expBtn.dataset.editexp);
                return;
              }
              const delBtn = e.target.closest('[data-del]');
              if (delBtn) {
                if (!canDeleteValidInventory()) {
                  toast('Access Denied: Master Admins do not have permission to delete inventory records.');
                  return;
                }
                const devId = delBtn.dataset.del;
                const ok = await cv.confirm('Are you sure you want to move device record #' + devId + ' to the Cart?');
                if (!ok) return;
                try {
                  toast('Moving record to Cart…');
                  await api('/api/devices/' + devId, { method: 'DELETE' });
                  toast('Device record moved to Cart successfully');
                  await fetchInventoryRows();
                  await updateChrome();
                } catch(err) {
                  fail(err);
                }
              }
            };
          }


          document.querySelectorAll('#invTableWrap th.sortable').forEach(th => {
            th.onclick = () => {
              const c = th.dataset.sort;
              if (sortCol === c) { sortDir = sortDir === 'asc' ? 'desc' : 'asc'; }
              else { sortCol = c; sortDir = 'asc'; }
              fetchInventoryRows();
            };
          });
        } catch (e) {
          $('invTableWrap').innerHTML = `<div class="empty err">${esc(e.message)}</div>`;
        } finally {
          hideBstplLoader();
        }
      }

      // Wire Expiry Filter controls
      if ($('invExpiryFilter')) {
        $('invExpiryFilter').onchange = () => { invPage = 1; fetchInventoryRows(); };
      }
      if ($('btnFilterExpiredSims')) {
        $('btnFilterExpiredSims').onclick = () => {
          if ($('invExpiryFilter')) $('invExpiryFilter').value = 'expired';
          invPage = 1;
          fetchInventoryRows();
        };
      }
      if ($('btnFilterExpiringSoonSims')) {
        $('btnFilterExpiringSoonSims').onclick = () => {
          if ($('invExpiryFilter')) $('invExpiryFilter').value = 'expiring_30';
          invPage = 1;
          fetchInventoryRows();
        };
      }

      /* =========================================================================
         INTEGRATED CUSTOMER FILES (Cards Portfolio within Customer Inventory)
         ========================================================================= */
      let custHide = false;
      async function loadCustomerFilesContainer() {
        await loadCU();
        if ($('invCustCountBadge')) $('invCustCountBadge').textContent = (CU || []).length;
        const staff = myRole() !== 'limited', canDelete = canDeleteValidInventory();
        if ($('cadd')) $('cadd').hidden = false;
        if ($('cbulk')) $('cbulk').hidden = !staff || CU.length < 1;
        if ($('btnRenameAllCust')) $('btnRenameAllCust').hidden = !staff || CU.length < 1;
        if ($('btnDeleteAllCust')) $('btnDeleteAllCust').hidden = !staff || !canDelete || CU.length < 1;

        if ($('chide')) {
          $('chide').onclick = e => {
            custHide = !custHide;
            e.target.textContent = custHide ? 'Show Cards' : 'Hide Cards';
            if (typeof drawCustCards === 'function') drawCustCards();
          };
        }
        if ($('cadd')) {
          $('cadd').onclick = () => openAddCustomerModal();
        }
        if ($('cbulk')) $('cbulk').onclick = bulkRename;
        if ($('btnRenameAllCust')) $('btnRenameAllCust').onclick = () => openRenameAllCustomersModal();
        if ($('btnDeleteAllCust')) $('btnDeleteAllCust').onclick = () => openDeleteAllCustomersModal();

        if (typeof drawCustCards === 'function') {
          drawCustCards();
        }
      }

      function openDeleteAllCustomersModal() {
        if (!canDeleteValidInventory()) {
          toast('⚠️ You are not permitted to delete customer data.');
          return;
        }
        const PHRASE = 'DELETE ALL CUSTOMERS';
        const nCust = CU.length;
        const nDev = CU.reduce((a, c) => a + Number(c.devices || 0), 0);
        openDlg('Delete ALL Customers Permanently', `
          <div class="note" style="margin-bottom:12px;border:1.5px solid var(--danger);background:var(--danger-bg, #fee2e2);color:var(--danger)">
            <b>⚠️ This cannot be undone.</b> It permanently deletes <b>${nCust.toLocaleString()} customer(s)</b> and <b>every device record</b>
            (${nDev.toLocaleString()} active records, plus anything in the Recycle Bin and Deleted Customers), and drops every customer table in the database.
            Nothing is moved to the bin. User accounts, the activity log and Errored Entries are kept.
          </div>
          <p class="sub" style="margin:0 0 8px">Download the data first if you may need it (<b>📥 Download All Customer Data</b>).</p>
          <label for="delAllConfirmInput">Type <b><code>${PHRASE}</code></b> to confirm</label>
          <input id="delAllConfirmInput" autocomplete="off" spellcheck="false" placeholder="${PHRASE}" />
        `, 'Delete Everything Permanently', async () => {
          const typed = $('delAllConfirmInput').value.trim();
          if (typed !== PHRASE) throw new Error(`Type exactly: ${PHRASE}`);
          showBstplLoader('Permanently deleting all customers and their data…');
          try {
            const r = await api('/api/customers/delete-all-permanent', { method: 'POST', body: JSON.stringify({ confirm_text: typed }) });
            toast(`✓ Permanently deleted ${Number(r.deleted_customers || 0).toLocaleString()} customer(s) and ${Number(r.deleted_devices || 0).toLocaleString()} device record(s).`);
            showEventPopup({
              type: 'deleting',
              title: 'All Customers Deleted Permanently',
              message: `${Number(r.deleted_customers || 0).toLocaleString()} customers, ${Number(r.deleted_devices || 0).toLocaleString()} device records and ${Number(r.dropped_tables || 0).toLocaleString()} customer tables were permanently removed.`,
              meta: { 'Customers Deleted': r.deleted_customers, 'Device Records Deleted': r.deleted_devices, 'Customer Tables Dropped': r.dropped_tables },
              progress: '100% Complete'
            });
            await loadCU(); await updateChrome(); loadCustomerFilesContainer();
            if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
          } finally {
            hideBstplLoader();
          }
        }, true);
      }

      function openSingleCustomerRename(cid) {
        const cust = (CU || []).find(c => String(c.id) === String(cid));
        if (!cust) {
          toast('Customer portfolio not found');
          return;
        }

        const dlg = $('dlgSingleCustomerRename');
        if (!dlg) return;

        if ($('renCustCurrentName')) $('renCustCurrentName').textContent = cust.name;
        if ($('renCustCurrentId')) $('renCustCurrentId').textContent = '#' + cust.id;
        if ($('renCustRecordsCount')) $('renCustRecordsCount').textContent = (cust.devices || 0).toLocaleString();
        if ($('renCustAvatar')) $('renCustAvatar').textContent = cust.avatar || (cust.name || 'C').charAt(0).toUpperCase();

        const updateTablePreview = val => {
          const clean = (val || '').trim().replace(/[^a-zA-Z0-9_]+/g, '_').replace(/^_+|_+$/g, '') || 'customer';
          if ($('singleRenTableCode')) $('singleRenTableCode').textContent = `customer_${clean.toLowerCase()}`;
        };

        if ($('singleRenNameInput')) {
          $('singleRenNameInput').value = cust.name;
          updateTablePreview(cust.name);
          $('singleRenNameInput').oninput = e => updateTablePreview(e.target.value);
          setTimeout(() => {
            $('singleRenNameInput').focus();
            $('singleRenNameInput').select();
          }, 50);
        }
        if ($('singleRenErr')) {
          $('singleRenErr').textContent = '';
          $('singleRenErr').style.display = 'none';
        }

        if ($('closeDlgSingleCustomerRename')) $('closeDlgSingleCustomerRename').onclick = () => dlg.close();
        if ($('btnCancelSingleRen')) $('btnCancelSingleRen').onclick = () => dlg.close();

        const form = $('formSingleCustomerRename');
        if (form) {
          form.onsubmit = async e => {
            e.preventDefault();
            const errEl = $('singleRenErr');
            if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }

            const newName = ($('singleRenNameInput')?.value || '').trim();
            if (!newName) {
              if (errEl) { errEl.textContent = 'Please enter a valid customer name.'; errEl.style.display = 'block'; }
              return;
            }
            if (newName === cust.name) {
              if (errEl) { errEl.textContent = 'New name is identical to the current customer name.'; errEl.style.display = 'block'; }
              return;
            }

            const btnSave = $('btnSaveSingleRen');
            if (btnSave) { btnSave.disabled = true; btnSave.textContent = 'Saving…'; }

            try {
              if (typeof showBstplLoader === 'function') showBstplLoader(`Renaming customer "${cust.name}" to "${newName}"…`);
              const r = await api('/api/customers/' + cust.id, {
                method: 'PATCH',
                body: JSON.stringify({ name: newName })
              });
              dlg.close();
              toast(`✓ Customer renamed to "${r.name}" in database, cloud table, and website!`);
              await loadCU();
              await updateChrome();
              if (typeof drawCustCards === 'function') drawCustCards();
              loadCustomerFilesContainer();
              if (currentInvSubView === 'devices') fetchInventoryRows();
            } catch (err) {
              if (errEl) { errEl.textContent = err.message || 'Failed to rename customer'; errEl.style.display = 'block'; }
            } finally {
              if (btnSave) { btnSave.disabled = false; btnSave.textContent = '💾 Save New Name'; }
              if (typeof hideBstplLoader === 'function') hideBstplLoader();
            }
          };
        }

        dlg.showModal();
      }

      function openRenameAllCustomersModal() {
        const dlg = $('dlgRenameAllCustomers');
        if (!dlg) return;
        const tbody = CU.map((c, idx) => `
          <tr data-cid="${c.id}">
            <td style="width:40px;text-align:center">${idx + 1}</td>
            <td style="width:200px"><b>${esc(c.name)}</b></td>
            <td>
              <input type="text" class="rename-cust-input" data-cid="${c.id}" value="${esc(c.name)}" style="width:100%;padding:6px 10px;font-size:13px;border-radius:6px;border:1px solid var(--line)" />
            </td>
            <td style="width:120px;text-align:right;color:var(--muted)">${(c.devices || 0).toLocaleString()} SIMs</td>
          </tr>
        `).join('');

        $('renameAllCustTableWrap').innerHTML = `
          <table class="data-table" style="font-size:13px;margin:0">
            <thead>
              <tr style="background:var(--card-subtle)">
                <th style="width:40px">#</th>
                <th style="width:200px">Current Customer Name</th>
                <th>New Customer Name</th>
                <th style="width:120px;text-align:right">Total SIMs</th>
              </tr>
            </thead>
            <tbody>${tbody}</tbody>
          </table>
        `;

        if ($('closeDlgRenameAllCustomers')) $('closeDlgRenameAllCustomers').onclick = () => dlg.close();
        if ($('btnCancelRenameAllCust')) $('btnCancelRenameAllCust').onclick = () => dlg.close();

        if ($('btnSaveRenameAllCust')) {
          $('btnSaveRenameAllCust').onclick = async () => {
            const inputs = document.querySelectorAll('.rename-cust-input');
            const renames = [];
            inputs.forEach(inp => {
              const cid = parseInt(inp.dataset.cid, 10);
              const newName = inp.value.trim();
              const original = (CU.find(c => c.id === cid) || {}).name || '';
              if (newName && newName !== original) {
                renames.push({ id: cid, name: newName });
              }
            });

            if (!renames.length) {
              toast('No customer names were changed.');
              dlg.close();
              return;
            }

            dlg.close();
            showBstplLoader(`Renaming ${renames.length} customer portfolio(s)…`);
            try {
              const res = await api('/api/customers/rename-all', {
                method: 'POST',
                body: JSON.stringify({ renames })
              });
              toast(`✓ Successfully renamed ${res.renamed_count} customer(s)!`);
              await loadCU();
              await updateChrome();
              loadCustomerFilesContainer();
            } catch (err) {
              fail(err);
            } finally {
              hideBstplLoader();
            }
          };
        }

        dlg.showModal();
      }

      function openDeleteCustomerEntriesModal(cid) {
        if (!canDeleteValidInventory()) {
          toast('⚠️ Master Admins are not permitted to delete valid inventory records.');
          return;
        }
        const cust = (CU || []).find(c => String(c.id) === String(cid));
        if (!cust) return;

        const dlg = $('dlgDeleteCustomerEntries');
        if (!dlg) return;

        if ($('delCustDetailName')) $('delCustDetailName').textContent = cust.name;
        if ($('delCustCartTargetName')) $('delCustCartTargetName').textContent = cust.name;
        if ($('delCustRecordsCount')) $('delCustRecordsCount').textContent = (cust.devices || 0).toLocaleString() + ' records';
        if ($('delCustConfirmExpected')) $('delCustConfirmExpected').textContent = cust.name;
        if ($('delCustAvatar')) $('delCustAvatar').textContent = cust.avatar || (cust.name || 'C').charAt(0).toUpperCase();

        // Reset radio and state
        let currentMode = 'cart';
        if ($('delModeCart')) $('delModeCart').checked = true;
        if ($('delModePerm')) $('delModePerm').checked = false;
        if ($('delCartConfirmWrap')) $('delCartConfirmWrap').style.display = 'block';
        if ($('delPermConfirmWrap')) $('delPermConfirmWrap').style.display = 'none';
        if ($('delCustConfirmInput')) $('delCustConfirmInput').value = '';

        const updateDelBtnState = () => {
          const btn = $('btnConfirmDelCustEntries');
          if (!btn) return;
          if (currentMode === 'cart') {
            btn.disabled = false;
            btn.style.cursor = 'pointer';
            btn.style.background = 'linear-gradient(135deg, #2563eb, #1d4ed8)';
            btn.style.borderColor = '#2563eb';
            btn.textContent = '📦 Move Customer to Cart';
            if ($('delModeCartCard')) {
              $('delModeCartCard').style.borderColor = 'var(--primary)';
              $('delModeCartCard').style.background = 'rgba(37,99,235,0.04)';
            }
            if ($('delModePermCard')) {
              $('delModePermCard').style.borderColor = 'var(--line)';
              $('delModePermCard').style.background = 'var(--card)';
            }
          } else {
            const val = ($('delCustConfirmInput')?.value || '').trim();
            const matched = (val.toLowerCase() === cust.name.toLowerCase());
            btn.disabled = !matched;
            btn.style.cursor = matched ? 'pointer' : 'not-allowed';
            btn.style.background = matched ? '#dc2626' : '#9ca3af';
            btn.style.borderColor = matched ? '#b91c1c' : '#9ca3af';
            btn.textContent = '⚠️ Permanently Delete Customer';
            if ($('delModePermCard')) {
              $('delModePermCard').style.borderColor = '#dc2626';
              $('delModePermCard').style.background = 'rgba(239,68,68,0.04)';
            }
            if ($('delModeCartCard')) {
              $('delModeCartCard').style.borderColor = 'var(--line)';
              $('delModeCartCard').style.background = 'var(--card)';
            }
          }
        };

        if ($('delModeCart')) {
          $('delModeCart').onchange = () => {
            currentMode = 'cart';
            if ($('delCartConfirmWrap')) $('delCartConfirmWrap').style.display = 'block';
            if ($('delPermConfirmWrap')) $('delPermConfirmWrap').style.display = 'none';
            updateDelBtnState();
          };
        }
        if ($('delModePerm')) {
          $('delModePerm').onchange = () => {
            currentMode = 'perm';
            if ($('delCartConfirmWrap')) $('delCartConfirmWrap').style.display = 'none';
            if ($('delPermConfirmWrap')) $('delPermConfirmWrap').style.display = 'block';
            updateDelBtnState();
            setTimeout(() => { $('delCustConfirmInput')?.focus(); }, 50);
          };
        }
        if ($('delCustConfirmInput')) {
          $('delCustConfirmInput').oninput = updateDelBtnState;
        }

        updateDelBtnState();

        if ($('closeDlgDeleteCustomerEntries')) $('closeDlgDeleteCustomerEntries').onclick = () => dlg.close();
        if ($('btnCancelDelCustEntries')) $('btnCancelDelCustEntries').onclick = () => dlg.close();

        if ($('btnConfirmDelCustEntries')) {
          $('btnConfirmDelCustEntries').onclick = async () => {
            const isPerm = (currentMode === 'perm');
            dlg.close();
            if (typeof showBstplLoader === 'function') showBstplLoader(`Processing deletion for "${cust.name}"…`, 0);

            try {
              if (!isPerm) {
                await api(`/api/customers/${cust.id}`, { method: 'DELETE' });
                toast(`✓ Customer portfolio "${cust.name}" moved to Cart.`);
              } else {
                const res = await api(`/api/customers/${cust.id}/delete-all-entries`, {
                  method: 'POST',
                  body: JSON.stringify({
                    confirm_name: ($('delCustConfirmInput')?.value || '').trim(),
                    permanent: true,
                    reason: `Direct permanent erasure of customer ${cust.name}`
                  })
                });
                toast(`✓ Successfully erased customer "${cust.name}" and ${res.deleted_count.toLocaleString()} SIM entries.`);
              }
              await loadCU();
              await updateChrome();
              if (typeof drawCustCards === 'function') drawCustCards();
              loadCustomerFilesContainer();
              if (currentInvSubView === 'devices') fetchInventoryRows();
            } catch (err) {
              fail(err);
            } finally {
              if (typeof hideBstplLoader === 'function') hideBstplLoader();
            }
          };
        }

        dlg.showModal();
      }

      // --- Change Customer Portfolio Icon/Avatar (🎨) ---
      window.editCustAvatar = function(customer) {
        if (!customer) return;
        const dlg = $('dlgEditCustAvatar');
        if (!dlg) return;

        if ($('custAvatarCustName')) $('custAvatarCustName').textContent = customer.name;
        let selectedAvatar = customer.avatar || '🏢';
        const updatePreview = av => {
          selectedAvatar = av;
          if ($('custAvatarPreviewLarge')) $('custAvatarPreviewLarge').textContent = av || '🏢';
        };
        updatePreview(selectedAvatar);

        const popularIcons = ['🏢', '🏬', '🏭', '🏛️', '🌐', '💼', '📦', '🚚', '🚗', '📱', '📡', '🏷️', '⚡', '⭐', '🛡️', '🔧', '🏥', '🛒', '🔌', '✈️'];
        const gridEl = $('custAvatarPresetGrid');
        if (gridEl) {
          gridEl.innerHTML = popularIcons.map(ic => `
            <button type="button" class="b cust-icon-pick-btn" data-icon="${ic}"
              style="width:38px;height:38px;padding:0;font-size:18px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1.5px solid ${ic === selectedAvatar ? 'var(--primary)' : 'var(--line)'};background:${ic === selectedAvatar ? 'rgba(37,99,235,0.1)' : 'var(--card)'}">
              ${ic}
            </button>
          `).join('');

          gridEl.onclick = e => {
            const btn = e.target.closest('[data-icon]');
            if (!btn) return;
            const ic = btn.dataset.icon;
            updatePreview(ic);
            if ($('custAvatarCustomInp')) $('custAvatarCustomInp').value = ic;
            gridEl.querySelectorAll('.cust-icon-pick-btn').forEach(b => {
              const active = b.dataset.icon === ic;
              b.style.borderColor = active ? 'var(--primary)' : 'var(--line)';
              b.style.background = active ? 'rgba(37,99,235,0.1)' : 'var(--card)';
            });
          };
        }

        if ($('custAvatarCustomInp')) {
          $('custAvatarCustomInp').value = selectedAvatar;
          $('custAvatarCustomInp').oninput = e => updatePreview(e.target.value.trim() || '🏢');
        }

        if ($('btnSaveCustAvatar')) {
          $('btnSaveCustAvatar').onclick = async () => {
            const av = selectedAvatar.trim() || '🏢';
            dlg.close();
            toast('Updating customer icon…');
            try {
              await api(`/api/customers/${customer.id}/avatar`, {
                method: 'PUT',
                body: JSON.stringify({ avatar: av })
              });
              customer.avatar = av;
              toast(`✓ Customer icon updated to ${av}`);
              await loadCU();
              if (typeof drawCustCards === 'function') drawCustCards();
            } catch(err) {
              fail(err);
            }
          };
        }

        dlg.showModal();
      };

      // --- Add Customer Portfolio Modal ---
      window.openAddCustomerModal = function() {
        const dlg = $('dlgAddCustomer');
        if (!dlg) return;

        if ($('addCustNameInp')) $('addCustNameInp').value = '';
        if ($('addCustErr')) { $('addCustErr').textContent = ''; $('addCustErr').style.display = 'none'; }
        if ($('addCustTablePreview')) $('addCustTablePreview').textContent = 'customer_...';

        let chosenAvatar = '🏢';
        const iconsStrip = $('addCustIconsStrip');
        if (iconsStrip) {
          const quickIcons = ['🏢', '🏬', '🏭', '💼', '📦', '🌐', '📱', '⚡'];
          iconsStrip.innerHTML = quickIcons.map(ic => `
            <button type="button" class="b add-icon-btn" data-addic="${ic}"
              style="width:36px;height:36px;font-size:18px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1.5px solid ${ic === chosenAvatar ? 'var(--ok)' : 'var(--line)'};background:${ic === chosenAvatar ? 'rgba(16,185,129,0.1)' : 'var(--card)'}">
              ${ic}
            </button>
          `).join('');

          iconsStrip.onclick = e => {
            const btn = e.target.closest('[data-addic]');
            if (!btn) return;
            chosenAvatar = btn.dataset.addic;
            iconsStrip.querySelectorAll('.add-icon-btn').forEach(b => {
              const active = b.dataset.addic === chosenAvatar;
              b.style.borderColor = active ? 'var(--ok)' : 'var(--line)';
              b.style.background = active ? 'rgba(16,185,129,0.1)' : 'var(--card)';
            });
          };
        }

        if ($('addCustNameInp')) {
          $('addCustNameInp').oninput = e => {
            const val = e.target.value.trim();
            const clean = val.replace(/[^a-zA-Z0-9_]+/g, '_').replace(/^_+|_+$/g, '') || '...';
            if ($('addCustTablePreview')) $('addCustTablePreview').textContent = `customer_${clean.toLowerCase()}`;
          };
          setTimeout(() => { $('addCustNameInp').focus(); }, 50);
        }

        const form = $('formAddCustomer');
        if (form) {
          form.onsubmit = async e => {
            e.preventDefault();
            const errEl = $('addCustErr');
            if (errEl) { errEl.textContent = ''; errEl.style.display = 'none'; }

            const name = ($('addCustNameInp')?.value || '').trim();
            if (!name) {
              if (errEl) { errEl.textContent = 'Please enter a customer name.'; errEl.style.display = 'block'; }
              return;
            }

            const btnSub = $('btnSubmitAddCustomer');
            if (btnSub) { btnSub.disabled = true; btnSub.textContent = 'Creating…'; }

            try {
              if (typeof showBstplLoader === 'function') showBstplLoader(`Creating portfolio "${name}"…`);
              const res = await api('/api/customers', {
                method: 'POST',
                body: JSON.stringify({ name, avatar: chosenAvatar })
              });
              dlg.close();
              toast(`✓ Customer portfolio "${name}" created successfully!`);
              if (typeof showEventPopup === 'function') {
                showEventPopup({
                  type: 'inserting',
                  title: 'Customer Portfolio Created',
                  message: `Successfully created new customer portfolio "${name}".`,
                  meta: { 'Customer Name': name, 'Customer ID': `#${res.id || ''}`, 'Status': 'Active' },
                  progress: '100% Complete'
                });
              }
              await loadCU();
              await updateChrome();
              loadCustomerFilesContainer();
            } catch(err) {
              if (errEl) { errEl.textContent = err.message || 'Failed to create customer'; errEl.style.display = 'block'; }
            } finally {
              if (btnSub) { btnSub.disabled = false; btnSub.textContent = '➕ Create Portfolio'; }
              if (typeof hideBstplLoader === 'function') hideBstplLoader();
            }
          };
        }

        dlg.showModal();
      };

      // --- Merge Customer Modal ---
      window.openMergeCustomerModal = function(srcCid) {
        const srcCust = (CU || []).find(c => c.id === srcCid);
        if (!srcCust) return;
        const targets = (CU || []).filter(c => c.id !== srcCid);
        if (!targets.length) {
          toast('No other customer available to merge into.');
          return;
        }

        const dlg = $('dlgMergeCustomer');
        if (!dlg) return;

        if ($('mergeCustSrcName')) $('mergeCustSrcName').textContent = srcCust.name;
        if ($('mergeCustSrcCount')) $('mergeCustSrcCount').textContent = `${(srcCust.devices || 0).toLocaleString()} SIM records`;

        const sel = $('mergeCustDstSel');
        if (sel) {
          sel.innerHTML = targets.map(c => `
            <option value="${c.id}">${esc(c.name)} (#${c.id}) — ${(c.devices || 0).toLocaleString()} SIM records</option>
          `).join('');
        }

        if ($('btnConfirmMergeCustomer')) {
          $('btnConfirmMergeCustomer').onclick = async () => {
            const dstId = parseInt(sel.value, 10);
            const dstCust = (CU || []).find(c => c.id === dstId);
            dlg.close();
            if (typeof showBstplLoader === 'function') showBstplLoader(`Merging "${srcCust.name}" into "${dstCust?.name || 'destination'}"…`);

            try {
              await api(`/api/customers/${srcCid}/merge/${dstId}`, { method: 'POST' });
              toast(`✓ Successfully merged "${srcCust.name}" into "${dstCust?.name || 'destination'}".`);
              await loadCU();
              await updateChrome();
              loadCustomerFilesContainer();
            } catch(err) {
              fail(err);
            } finally {
              if (typeof hideBstplLoader === 'function') hideBstplLoader();
            }
          };
        }

        dlg.showModal();
      };

      // --- Toolbar Rename Customer Action ---
      window.bulkRename = function() {
        if (!CU || !CU.length) { toast('No customer portfolios found.'); return; }
        // Open single rename on the first or active customer
        const target = (invCid && CU.find(c => c.id === invCid)) || CU[0];
        if (target) openSingleCustomerRename(target.id);
      };

      /* =========================================================================
         CONTAINER 4: BULK UPLOAD (EXCEL)
         ========================================================================= */
      let wbData = null, parsedRows = [], activeValResult = null, activeValFilter = 'new';

      function isBlankDateCell(val) {
        if (val === null || val === undefined) return true;
        const s = String(val).trim().toLowerCase();
        return !s || ['nan', 'nat', 'null', 'undefined', 'none', 'nil', '-', '--', '---', '—', '–', '#n/a', 'n/a', 'na', 'blank', '0', '0000-00-00', '00/00/0000', '0.0'].includes(s);
      }


      // ---- File status (shown after "Validate File & Check Entries" and inside "Check Entries") ----
      window.buildFileStatusHtml = function (stateOverride) {
        const vr = activeValResult;
        const fileLabel = ($('wbFileName') ? $('wbFileName').textContent : '') || 'Selected file';
        const box = (bg, bd, icon, title, msg, extra) => `
          <div style="border:1.5px solid ${bd};background:${bg};border-radius:12px;padding:14px 16px;margin:12px 0">
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
              <span style="font-size:22px">${icon}</span>
              <div style="flex:1;min-width:220px">
                <div style="font-weight:800;font-size:15px;color:var(--ink)">File Status: ${title}</div>
                <div style="font-size:12.5px;color:var(--muted);margin-top:2px">${esc(fileLabel)}</div>
              </div>
            </div>
            <div style="font-size:13px;margin-top:8px;color:var(--ink)">${msg}</div>
            ${extra || ''}
          </div>`;
        if (stateOverride === 'checking') return box('var(--card-subtle)', 'var(--line)', '⏳', 'Checking…', 'Comparing every row with the database. Please wait.');
        if (stateOverride && stateOverride.error) return box('rgba(220,38,38,.08)', 'var(--danger)', '❌', 'Could not be checked', esc(stateOverride.error));
        if (!vr) return '';
        const total = vr.total_count || 0, nw = vr.new_count || 0, up = vr.updated_count || 0, ex = vr.existing_count || 0;
        const du = vr.duplicate_count || 0, inv = vr.invalid_count || 0;
        const valid = Math.max(0, total - du - inv);            // rows that passed every check (new + changed + identical)
        const custs = (window._currentCustSummaryList || []).length;
        const chip = (label, v, c) => `<span style="display:inline-block;margin:4px 6px 0 0;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700;border:1px solid ${c};color:${c}">${label}: ${Number(v).toLocaleString()}</span>`;
        const chips = '<div style="margin-top:8px">' +
          chip('✅ Valid Entries', valid, 'var(--ok)') + chip('✨ New', nw, 'var(--ok)') + chip('🔄 Update', up, 'var(--primary)') +
          chip('📋 Unchanged', ex, 'var(--muted)') + chip('⚠️ Duplicates', du, 'var(--warn)') + chip('❌ Invalid (pushed as is)', inv, 'var(--danger)') +
          chip('📄 Total rows', total, 'var(--ink)') + chip('👥 Customers', custs, 'var(--ink)') + '</div>';
        const idLine = du === 0
          ? '🔐 <b>Unique identifiers:</b> ✅ no repeated Device Sr No, IMEI or ICCID/CCID found (in the file or in the database).'
          : `🔐 <b>Unique identifiers:</b> ⚠️ ${du.toLocaleString()} row(s) repeat a Device Sr No, IMEI or ICCID/CCID (in the file or already in the database). They are blocked and never added twice.`;
        const dateLine = '📅 <b>Dates:</b> Activation, Expiry and Dispatched dates are accepted as given (any year; expiry may be before activation). Only impossible dates such as 31-Sep are left blank.';
        const extra = chips + `<div style="margin-top:8px;font-size:12.5px;line-height:1.6">${idLine}<br>${dateLine}</div>`;
        if (!total) return box('var(--card-subtle)', 'var(--line)', 'ℹ️', 'Empty', 'No data rows were found in the selected sheets.');
        const pushed = nw + up + inv;                           // rows that really go to the database
        if (pushed === 0) return box(ex > 0 && du === 0 ? 'var(--card-subtle)' : 'rgba(220,38,38,.08)', ex > 0 && du === 0 ? 'var(--ok)' : 'var(--danger)', ex > 0 && du === 0 ? 'ℹ️' : '❌',
          ex > 0 && du === 0 ? 'Valid — nothing to change' : 'Rejected', ex > 0 && du === 0 ? 'All rows already exist with identical values.' : 'Every row is a duplicate, so nothing can be uploaded.', extra);
        if (du + inv > 0) return box('rgba(217,119,6,.10)', 'var(--warn)', '⚠️', 'Has Issues — will upload',
          `<b>${pushed.toLocaleString()}</b> of <b>${total.toLocaleString()}</b> rows will be uploaded (${nw.toLocaleString()} new, ${up.toLocaleString()} updated${inv ? `, <b>${inv.toLocaleString()} invalid pushed as they are</b>` : ''}). ` +
          `${du ? `<b>${du.toLocaleString()}</b> duplicate row(s) are NOT uploaded.` : ''}`, extra);
        if (nw + up === 0) return box('var(--card-subtle)', 'var(--ok)', 'ℹ️', 'Valid — nothing to change', 'All rows are valid and already identical to the database.', extra);
        return box('rgba(16,185,129,.10)', 'var(--ok)', '✅', 'Valid — ready to upload',
          `All <b>${total.toLocaleString()}</b> rows are valid: <b>${nw.toLocaleString()}</b> will be added and <b>${up.toLocaleString()}</b> updated.`, extra);
      };
      window.renderFileStatus = function (stateOverride) {
        const html = window.buildFileStatusHtml(stateOverride);
        const el = $('valFileStatus');
        if (el) { el.innerHTML = html; el.hidden = !html; }
        return html;
      };

      // Impossible calendar dates (31-Sep, 30-Feb) become blank instead of failing the whole upload. No year restriction.
      function convertDateToStandardFormat(val) {
        const out = _convertDateRaw(val);
        if (!out) return null;
        const m = /^(\d{1,4})-(\d{2})-(\d{2})$/.exec(out);
        if (!m) return null;
        const y = +m[1], mo = +m[2], d = +m[3];
        if (y < 1 || y > 9999 || mo < 1 || mo > 12 || d < 1) return null;
        const dim = [31, (y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1];
        if (d > dim) return null;
        return `${String(y).padStart(4, '0')}-${m[2]}-${m[3]}`;
      }

      function _convertDateRaw(val) {
        if (isBlankDateCell(val)) return null;
        if (val instanceof Date) {
          if (isNaN(val.getTime())) return null;
          return val.toISOString().slice(0, 10);
        }
        let str = String(val).trim();

        // 1. Strip time portion if present (e.g. ' 00:00:00', 'T00:00:00', ' 10:30:15 AM', ' 02:30 PM', '.000Z')
        str = str.replace(/[T\s]\d{1,2}:\d{2}(:\d{2})?(\.\d+)?(\s*[APap][Mm])?.*$/i, '').trim();

        // Remove wrapping quotes, brackets, or leading/trailing separators
        str = str.replace(/^["'\[\(\s\-_/.]+|["'\]\)\s\-_/.]+$/g, '').trim();
        if (!str || isBlankDateCell(str)) return null;

        // 2. Excel serial number: e.g. 44561 or 44561.5 or '44561.0'
        if (/^\d{4,6}(\.\d+)?$/.test(str)) {
          try {
            const num = parseFloat(str);
            if (num > 20000 && num < 80000) {
              if (typeof XLSX !== 'undefined' && XLSX.SSF && XLSX.SSF.parse_date_code) {
                const d = XLSX.SSF.parse_date_code(Math.floor(num));
                if (d && d.y) {
                  const mm = String(d.m).padStart(2, '0');
                  const dd = String(d.d).padStart(2, '0');
                  return `${d.y}-${mm}-${dd}`;
                }
              }
              const excelEpoch = new Date(Date.UTC(1899, 11, 30));
              const dateObj = new Date(excelEpoch.getTime() + num * 86400000);
              if (!isNaN(dateObj.getTime())) {
                return dateObj.toISOString().slice(0, 10);
              }
            }
          } catch (_) { }
        }

        // 3. Compact 8-digit date: YYYYMMDD (e.g. 20240518) or DDMMYYYY (e.g. 18052024)
        if (/^\d{8}$/.test(str)) {
          const y1 = parseInt(str.slice(0, 4), 10);
          const m1 = parseInt(str.slice(4, 6), 10);
          const d1 = parseInt(str.slice(6, 8), 10);
          if (y1 >= 1000 && y1 <= 9999 && m1 >= 1 && m1 <= 12 && d1 >= 1 && d1 <= 31) {
            return `${y1}-${String(m1).padStart(2, '0')}-${String(d1).padStart(2, '0')}`;
          }
          const d2 = parseInt(str.slice(0, 2), 10);
          const m2 = parseInt(str.slice(2, 4), 10);
          const y2 = parseInt(str.slice(4, 8), 10);
          if (y2 >= 1000 && y2 <= 9999 && m2 >= 1 && m2 <= 12 && d2 >= 1 && d2 <= 31) {
            return `${y2}-${String(m2).padStart(2, '0')}-${String(d2).padStart(2, '0')}`;
          }
        }

        // 4. Compact 6-digit date: YYMMDD (e.g. 240518) or DDMMYY (e.g. 180524)
        if (/^\d{6}$/.test(str)) {
          const c0 = parseInt(str.slice(0, 2), 10);
          const c1 = parseInt(str.slice(2, 4), 10);
          const c2 = parseInt(str.slice(4, 6), 10);
          if (c0 >= 20 && c0 <= 50 && c1 >= 1 && c1 <= 12 && c2 >= 1 && c2 <= 31) {
            return `20${c0}-${String(c1).padStart(2, '0')}-${String(c2).padStart(2, '0')}`;
          }
          if (c2 >= 20 && c2 <= 50 && c1 >= 1 && c1 <= 12 && c0 >= 1 && c0 <= 31) {
            return `20${c2}-${String(c1).padStart(2, '0')}-${String(c0).padStart(2, '0')}`;
          }
        }

        // 5. Month name formats (e.g. '18-May-2024', '18-May-24', '18 May 2024', 'May 18, 2024', '18-January-2024', 'Jan 18, 2024')
        const months = {
          jan: '01', feb: '02', mar: '03', apr: '04', may: '05', jun: '06',
          jul: '07', aug: '08', sep: '09', oct: '10', nov: '11', dec: '12'
        };
        const monthRegex = /(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)/i;
        if (monthRegex.test(str)) {
          const mMatch = str.match(monthRegex);
          const monKey = mMatch[1].toLowerCase().slice(0, 3);
          const mm = months[monKey];
          const stripped = str.replace(monthRegex, ' ').trim();
          const parts = stripped.split(/[-/. ,\\]+/).filter(Boolean);
          const nums = parts.filter(p => /^\d+$/.test(p)).map(n => parseInt(n, 10));
          if (nums.length >= 2 && mm) {
            let year = nums.find(n => (n >= 1000 && n <= 9999));
            let day = nums.find(n => n !== year && n >= 1 && n <= 31);
            if (!year && nums.length >= 2) {
              const potentialYear = nums.find(n => n !== day);
              if (potentialYear != null) {
                year = potentialYear < 70 ? 2000 + potentialYear : (potentialYear < 100 ? 1900 + potentialYear : potentialYear);
              }
            }
            if (year && day) {
              return `${year}-${mm}-${String(day).padStart(2, '0')}`;
            }
          }
        }

        // 6. Delimited numeric dates: with separators -, /, ., space, or backslash
        const parts = str.split(/[-/. ,\\]+/).filter(Boolean);
        if (parts.length === 3 && parts.every(p => /^\d+$/.test(p))) {
          let p0 = parseInt(parts[0], 10);
          let p1 = parseInt(parts[1], 10);
          let p2 = parseInt(parts[2], 10);

          // Case A: Year first (YYYY-MM-DD or YY-MM-DD)
          if (p0 >= 1000 && p0 <= 9999 && p1 >= 1 && p1 <= 12 && p2 >= 1 && p2 <= 31) {
            return `${p0}-${String(p1).padStart(2, '0')}-${String(p2).padStart(2, '0')}`;
          }
          if (parts[0].length === 2 && p0 >= 20 && p0 <= 50 && p1 >= 1 && p1 <= 12 && p2 >= 1 && p2 <= 31) {
            return `20${p0}-${String(p1).padStart(2, '0')}-${String(p2).padStart(2, '0')}`;
          }

          // Case B: Year last (DD-MM-YYYY, MM-DD-YYYY, DD-MM-YY, MM-DD-YY)
          let year = p2;
          if (parts[2].length === 2) {
            year = p2 < 70 ? 2000 + p2 : 1900 + p2;
          }
          if (year >= 1000 && year <= 9999) {
            // Decide p0 (day/month) and p1 (month/day)
            if (p1 > 12 && p0 <= 12) {
              // MM-DD-YYYY
              return `${year}-${String(p0).padStart(2, '0')}-${String(p1).padStart(2, '0')}`;
            }
            if (p0 > 12 && p1 <= 12) {
              // DD-MM-YYYY
              return `${year}-${String(p1).padStart(2, '0')}-${String(p0).padStart(2, '0')}`;
            }
            // Standard telecom default (Day first): DD-MM-YYYY
            if (p0 >= 1 && p0 <= 31 && p1 >= 1 && p1 <= 12) {
              return `${year}-${String(p1).padStart(2, '0')}-${String(p0).padStart(2, '0')}`;
            }
          }
        }

        // 7. Native Date parse fallback
        const parsed = Date.parse(str);
        if (!isNaN(parsed)) {
          const d = new Date(parsed);
          if (!isNaN(d.getTime())) {
            const yr = d.getFullYear();
            if (yr >= 1000 && yr <= 9999) {
              return `${yr}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
            }
          }
        }

        return null;
      }

      function parseExcelDate(val) {
        return convertDateToStandardFormat(val);
      }

      function normalizeExcelRow(r) {
        const norm = {}, extra = {};
        const HMAP = {
          devicesrno: 'device_sr_no',
          srno: 'device_sr_no',
          serialno: 'device_sr_no',
          deviceserialnumber: 'device_sr_no',
          deviceserialno: 'device_sr_no',
          imei: 'imei',
          imeino: 'imei',
          iccid: 'iccid',
          iccidno: 'iccid',
          iccidnumber: 'iccid',
          iccidnum: 'iccid',
          ccid: 'iccid',
          ccidno: 'iccid',
          ccidnumber: 'iccid',
          ccidnum: 'iccid',
          simiccid: 'iccid',
          simccid: 'iccid',
          simno: 'iccid',
          simnumber: 'iccid',
          simnum: 'iccid',
          esimiccid: 'iccid',
          esimccid: 'iccid',
          msisdn1: 'msisdn1',
          msisdn2: 'msisdn2',
          actdate: 'act_date',
          activationdate: 'act_date',
          activatedon: 'act_date',
          activation: 'act_date',
          activateddate: 'act_date',
          expiry: 'expiry_date',
          expirydate: 'expiry_date',
          expdate: 'expiry_date',
          exp: 'expiry_date',
          validity: 'expiry_date',
          validtill: 'expiry_date',
          validupto: 'expiry_date',
          expiredate: 'expiry_date',
          dispatcheddate: 'dispatched_date',
          dispatchdate: 'dispatched_date',
          model: 'model',
          devicemodel: 'model',
          simprovider: 'sim_provider',
          provider: 'sim_provider',
          activationplan: 'activation_plan',
          plan: 'activation_plan',
          firmware: 'firmware',
          firmwareversion: 'firmware',
          flash: 'flash',
          flashtype: 'flash',
          customer: 'customer_name',
          customername: 'customer_name',
          custname: 'customer_name',
          client: 'customer_name',
          clientname: 'customer_name'
        };

        const IGNORE_COLS = new Set([
          'simtype', 'sim', 'typeofsim'
        ]);

        Object.keys(r).forEach(k => {
          const cleanKey = k.toLowerCase().replace(/[^a-z0-9]/g, '');
          if (IGNORE_COLS.has(cleanKey)) return;

          const mapped = HMAP[cleanKey];
          let val = r[k];
          if (val === null || val === undefined) val = '';
          else val = String(val).trim();
          if (val.toLowerCase() === 'nan' || val.toLowerCase() === 'null' || val.toLowerCase() === 'undefined') val = '';

          // Auto-clean numbers & scientific notation for IDs/IMEIs
          if (mapped === 'imei' || mapped === 'iccid' || mapped === 'msisdn1' || mapped === 'msisdn2' || mapped === 'device_sr_no') {
            if (val.endsWith('.0') && /^\d+\.0$/.test(val)) val = val.slice(0, -2);
            if (/[eE]\+?/.test(val)) {
              try {
                const num = Number(val);
                if (!isNaN(num) && Number.isFinite(num)) val = BigInt(Math.round(num)).toString();
              } catch { }
            }
          }

          if (mapped === 'iccid') {
            val = val.replace(/[\s\-_]+/g, '').toUpperCase();
          }

          if (mapped === 'act_date' || mapped === 'expiry_date' || mapped === 'dispatched_date') {
            val = parseExcelDate(val);
          }

          if (mapped) {
            norm[mapped] = val;
          } else if (val) {
            extra[k.trim()] = val;
          }
        });

        if (Object.keys(extra).length) norm.extra = extra;
        return norm;
      }

      function loadCustomModels() {
        const sel = $('optModel');
        if (!sel) return;
        const saved = JSON.parse(localStorage.getItem('custom_models') || '[]');
        sel.querySelectorAll('.custom-model-opt').forEach(o => o.remove());
        const newOpt = sel.querySelector('option[value="__new__"]');
        saved.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m;
          opt.textContent = m;
          opt.className = 'custom-model-opt';
          sel.insertBefore(opt, newOpt);
        });
      }

      function downloadBulkUploadTemplate() {
        const headers = [
          'customer_name', 'imei', 'device_sr_no', 'iccid', 'msisdn1', 'msisdn2',
          'act_date', 'expiry_date', 'dispatched_date', 'model', 'sim_provider',
          'sim_type', 'activation_plan', 'firmware', 'flash'
        ];

        const sampleRows = [
          [
            'Acme_Corp', '861329086493088', 'SR_10001', '89916441044828311924', '9876543210', '9876543211',
            '2026-01-15', '2027-01-15', '2026-01-10', 'BSTPL-4G-V2', 'TAISYS (Airtel + BSNL)',
            'E-SIM', '1 Year Commercial Plan', 'v3.1.0', '16MB Winbond'
          ],
          [
            'Tata_Motors', '861329086493089', 'SR_10002', '89916441044828311925', '9876543212', '9876543213',
            '2026-02-01', '2027-02-01', '2026-01-28', 'BSTPL-17IS', 'Vodafone-Idea (Vi)',
            'Plastic SIM', '2 Year Fleet Plan', 'v3.1.0', '16MB Macronix'
          ],
          [
            'Reliance_Logistics', '861329086493090', 'SR_10003', '89916441044828311926', '9876543214', '9876543215',
            '2026-03-10', '2027-03-10', '2026-03-05', 'BSTPL-4G-ADV', 'Jio Commercial IoT',
            'E-SIM', '3 Year Commercial Enterprise', 'v3.2.0', '32MB Winbond'
          ],
          [
            'Mahindra_Transport', '861329086493091', 'SR_10004', '89916441044828311927', '9876543216', '9876543217',
            '2026-04-05', '2027-04-05', '2026-04-01', 'BSTPL-17L', 'Airtel IoT',
            'Plastic SIM', 'Annual Transport Plan', 'v3.1.2', '16MB Adesto'
          ]
        ];

        const instructions = [
          ['CustomerVault Bulk Inventory Upload Guidelines & Rules'],
          [''],
          ['Field / Column', 'Requirement', 'Accepted Values / Format', 'Description & Guidance'],
          ['customer_name', 'Required', 'Text (e.g. Acme_Corp, Tata_Motors)', 'The customer account or portfolio name. In Automatic mode, each Excel sheet name becomes a customer portfolio.'],
          ['imei', 'Required', 'Exact 15 numeric digits (e.g. 861329086493088)', 'Primary device identifier. Must be unique across all inventory records.'],
          ['device_sr_no', 'Optional', 'Alphanumeric string (e.g. SR_10001)', 'Hardware serial number assigned to the device unit.'],
          ['iccid', 'Optional / Recommended', '19 to 20 numeric digits (e.g. 89916441044828311924)', 'Integrated Circuit Card Identifier for the SIM card / chip.'],
          ['msisdn1', 'Optional', '10 to 15 numeric digits (e.g. 9876543210)', 'Primary mobile / SIM phone number.'],
          ['msisdn2', 'Optional', '10 to 15 numeric digits', 'Secondary or fallback SIM mobile phone number.'],
          ['act_date', 'Optional', 'YYYY-MM-DD or DD-MM-YYYY (e.g. 2026-01-15)', 'SIM activation date.'],
          ['expiry_date', 'Optional / Recommended', 'YYYY-MM-DD or DD-MM-YYYY (e.g. 2027-01-15)', 'SIM expiry date used for live expiry alerts and renewal tracking.'],
          ['dispatched_date', 'Optional', 'YYYY-MM-DD or DD-MM-YYYY', 'Date when the device was dispatched to the client.'],
          ['model', 'Optional', 'Text (e.g. BSTPL-4G-V2, 17IS, 17L)', 'Device hardware model.'],
          ['sim_provider', 'Optional', 'Text (e.g. Airtel, Vodafone, Jio, TAISYS)', 'Telecom provider powering the SIM.'],
          ['sim_type', 'Optional', 'E-SIM or Plastic SIM', 'Classification of SIM hardware. System auto-tags if omitted.'],
          ['activation_plan', 'Optional', 'Text (e.g. 1 Year Plan, Annual Fleet)', 'Commercial connectivity plan details.'],
          ['firmware', 'Optional', 'Text (e.g. v3.1.0)', 'Installed firmware revision.'],
          ['flash', 'Optional', 'Text (e.g. 16MB Winbond, Adesto)', 'Flash memory hardware component.'],
          [''],
          ['IMPORTANT UPLOAD TIPS:'],
          ['1. Multi-Sheet Uploads: You can upload a workbook with multiple sheets. Each sheet is imported as its own customer table!'],
          ['2. Error Recovery: Records with invalid IMEIs or formatting errors are NOT lost — they are safely held in "Errored & Invalid Entries" where you can rectify and push them.'],
          ['3. Custom Columns: Any additional columns in your sheet are automatically preserved as custom dynamic attributes.']
        ];

        const wb = XLSX.utils.book_new();

        // Sheet 1: Upload Template
        const wsTemplate = XLSX.utils.aoa_to_sheet([headers, ...sampleRows]);
        wsTemplate['!cols'] = [
          { wch: 22 }, { wch: 20 }, { wch: 16 }, { wch: 26 }, { wch: 15 }, { wch: 15 },
          { wch: 14 }, { wch: 14 }, { wch: 16 }, { wch: 16 }, { wch: 24 },
          { wch: 15 }, { wch: 25 }, { wch: 14 }, { wch: 16 }
        ];
        XLSX.utils.book_append_sheet(wb, wsTemplate, 'Upload_Template');

        // Sheet 2: Upload Instructions & Rules
        const wsGuide = XLSX.utils.aoa_to_sheet(instructions);
        wsGuide['!cols'] = [{ wch: 24 }, { wch: 22 }, { wch: 45 }, { wch: 65 }];
        XLSX.utils.book_append_sheet(wb, wsGuide, 'Upload_Instructions');

        XLSX.writeFile(wb, 'CustomerVault_Sample_Bulk_Upload_Template.xlsx');
        toast('📥 Sample Excel file with complete upload details downloaded successfully!');
        if (typeof showEventPopup === 'function') {
          showEventPopup({
            type: 'download',
            title: 'Sample Template Download Complete',
            message: 'Sample Bulk Upload Excel file (.xlsx) with sample data and upload instructions downloaded.',
            meta: { 'File Name': 'CustomerVault_Sample_Bulk_Upload_Template.xlsx', 'Sheets': 'Upload_Template, Upload_Instructions' },
            progress: '100% Downloaded'
          });
        }
      }
      window.downloadBulkUploadTemplate = downloadBulkUploadTemplate;

      


    // --- Check Entries & Rectify Update Logic (Requirement 2) ---
    function openCheckEntriesModal() {
      const dlg = $('dlgCheckEntriesModal');
      if (!dlg) return;
      const records = (activeValResult && activeValResult.entries_requiring_update && activeValResult.entries_requiring_update.length)
        ? activeValResult.entries_requiring_update
        : (activeValResult && activeValResult.updated_sample && activeValResult.updated_sample.length)
        ? activeValResult.updated_sample
        : [];

      if ($('checkEntriesFileStatus')) $('checkEntriesFileStatus').innerHTML = window.buildFileStatusHtml ? window.buildFileStatusHtml() : '';
      if ($('btnDoRectifyAll')) $('btnDoRectifyAll').disabled = !records.length;

      if (!records.length) {
        if ($('checkEntriesEligibleCount')) $('checkEntriesEligibleCount').textContent = '0';
        if ($('checkEntriesStatsBadge')) $('checkEntriesStatsBadge').textContent = '0 records requiring updates';
        if ($('checkEntriesTableContainer')) $('checkEntriesTableContainer').innerHTML = '<div style="padding:24px;text-align:center;color:var(--muted)">No existing records need an update. New entries are added and identical entries are left as they are.</div>';
        dlg.showModal();
        return;
      }

      renderCheckEntriesTable(records);
      dlg.showModal();
    }
    window.openCheckEntriesModal = openCheckEntriesModal;

    function closeCheckEntriesModal() {
      const dlg = $('dlgCheckEntriesModal');
      if (dlg) dlg.close();
    }
    window.closeCheckEntriesModal = closeCheckEntriesModal;

    function renderCheckEntriesTable(records) {
      const container = $('checkEntriesTableContainer');
      if (!container) return;

      const filterTerm = ($('checkEntriesFilter')?.value || '').toLowerCase().trim();
      const filtered = filterTerm
        ? records.filter(r => JSON.stringify(r).toLowerCase().includes(filterTerm))
        : records;

      if (!filtered.length) {
        container.innerHTML = '<div style="padding:24px;text-align:center;color:var(--muted)">No records match current filter.</div>';
        return;
      }

      let html = `
        <table class="data-table" style="font-size:12.5px;margin:0;width:100%">
          <thead>
            <tr style="background:var(--card-subtle)">
              <th style="width:40px">#</th>
              <th>Identifier (ICCID / IMEI / Sr)</th>
              <th>Customer</th>
              <th>Detected Field Changes (Existing DB ➔ New Excel)</th>
              <th style="width:120px;text-align:center">Action</th>
            </tr>
          </thead>
          <tbody>
      `;

      filtered.slice(0, 100).forEach((r, idx) => {
        const iden = r.iccid || r.imei || r.device_sr_no || r.id || '—';
        const cust = r.customer_name || '—';
        const changes = r.changed_fields || {};
        let changeSummary = [];

        for (const [field, diff] of Object.entries(changes)) {
          const oldVal = (diff && diff.old != null && diff.old !== '') ? esc(String(diff.old)) : '<i style="color:var(--muted)">empty</i>';
          const newVal = (diff && diff.new != null && diff.new !== '') ? esc(String(diff.new)) : '<i style="color:var(--muted)">empty</i>';
          changeSummary.push(`
            <div style="margin-bottom:4px">
              <b style="color:var(--primary);text-transform:uppercase;font-size:11px">${esc(field.replace(/_/g, ' '))}:</b>
              <span style="color:var(--danger);text-decoration:line-through;margin-right:6px">${oldVal}</span>
              ➔ <span style="color:var(--ok);font-weight:700;margin-left:6px">${newVal}</span>
            </div>
          `);
        }

        if (!changeSummary.length) {
          changeSummary.push('<span style="color:var(--warn)">Pending field verification</span>');
        }

        html += `
          <tr>
            <td>${idx + 1}</td>
            <td><code style="font-weight:700">${esc(iden)}</code></td>
            <td><b>${esc(cust)}</b></td>
            <td>${changeSummary.join('')}</td>
            <td style="text-align:center">
              <button class="b p" data-rectify-idx="${idx}" type="button" style="padding:4px 10px;font-size:11.5px;background:linear-gradient(135deg, #d97706, #b45309);color:#fff;border-radius:6px;cursor:pointer">
                Rectify Row
              </button>
            </td>
          </tr>
        `;
      });

      if (filtered.length > 100) {
        html += `<tr><td colspan="5" style="text-align:center;padding:12px;color:var(--muted)">Showing first 100 of ${filtered.length.toLocaleString()} records requiring update. Use "Rectify All" to update all.</td></tr>`;
      }

      html += `</tbody></table>`;
      container.innerHTML = html;

      container.querySelectorAll('button[data-rectify-idx]').forEach(btn => {
        btn.onclick = () => {
          const idx = parseInt(btn.dataset.rectifyIdx, 10);
          const rec = filtered[idx];
          if (rec) executeRectifyUpdate([rec]);
        };
      });
    }

    async function executeRectifyUpdate(specificRecords = null) {
      const records = specificRecords || (activeValResult && activeValResult.entries_requiring_update) || (activeValResult && activeValResult.updated_sample) || [];
      if (!records.length) {
        toast('⚠️ No eligible records selected for update.');
        return;
      }

      showBstplLoader(`Updating ${records.length.toLocaleString()} database records with validated Excel data…`, 10);

      try {
        const rows = records.map(r => ({
          device_id: r.existing_id || r.id,
          iccid: r.iccid,
          imei: r.imei,
          device_sr_no: r.device_sr_no,
          customer_name: r.customer_name,
          msisdn1: r.msisdn1,
          msisdn2: r.msisdn2,
          act_date: r.act_date,
          expiry_date: r.expiry_date,
          dispatched_date: r.dispatched_date,
          model: r.model,
          sim_provider: r.sim_provider,
          sim_type: r.sim_type,
          activation_plan: r.activation_plan,
          firmware: r.firmware,
          flash: r.flash,
          extra: r.extra,
          changed_fields: r.changed_fields
        }));

        let totalSuccess = 0;
        let totalFailed = 0;
        const batchSize = 2500;

        for (let i = 0; i < rows.length; i += batchSize) {
          const chunk = rows.slice(i, i + batchSize);
          const pct = Math.round((i / rows.length) * 100);
          updateBstplLoader(`Updating database records (${i.toLocaleString()} / ${rows.length.toLocaleString()})…`, pct);

          const res = await api('/api/devices/bulk/rectify', {
            method: 'POST',
            body: JSON.stringify({ rows: chunk, skip_empty: true })
          });

          totalSuccess += (res.success_count || 0);
          totalFailed += (res.failed_count || 0);
        }

        hideBstplLoader();
        closeCheckEntriesModal();
        toast(`✅ Successfully updated ${totalSuccess.toLocaleString()} database records.${totalFailed ? ` (${totalFailed} failed)` : ''}`);

        if (typeof loadDevices === 'function') loadDevices(1);
        if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
      } catch (err) {
        hideBstplLoader();
        toast(`❌ Error updating records: ${err.message}`);
      }
    }
    window.executeRectifyUpdate = executeRectifyUpdate;

    function exportCheckEntriesExcel() {
      const records = (activeValResult && activeValResult.entries_requiring_update) || (activeValResult && activeValResult.updated_sample) || [];
      if (!records.length) {
        toast('No records to export.');
        return;
      }
      const headers = ['#', 'Identifier', 'Customer Name', 'Changed Field', 'Old Database Value', 'New Excel Value', 'Status'];
      const rows = [];
      records.forEach((r, idx) => {
        const iden = r.iccid || r.imei || r.device_sr_no || r.id || '';
        const cust = r.customer_name || '';
        const changes = r.changed_fields || {};
        for (const [field, diff] of Object.entries(changes)) {
          rows.push([
            idx + 1,
            iden,
            cust,
            field,
            diff?.old ?? '',
            diff?.new ?? '',
            'Requires Update'
          ]);
        }
      });
      exportExcel('check_entries_comparison_' + new Date().toISOString().slice(0, 10), headers, rows);
    }


        // Wire Check Entries & Rectify Buttons (Requirement 2)
        if ($('btnCheckEntriesModal')) $('btnCheckEntriesModal').onclick = openCheckEntriesModal;
        if ($('btnRectifyUpdate')) $('btnRectifyUpdate').onclick = () => executeRectifyUpdate();
        if ($('btnDoRectifyAll')) $('btnDoRectifyAll').onclick = () => executeRectifyUpdate();
        if ($('btnExportCheckEntriesCsv')) $('btnExportCheckEntriesCsv').onclick = exportCheckEntriesExcel;
        if ($('checkEntriesFilter')) {
          $('checkEntriesFilter').oninput = () => {
            const records = (activeValResult && activeValResult.entries_requiring_update) || (activeValResult && activeValResult.updated_sample) || [];
            renderCheckEntriesTable(records);
          };
        }


function initBulkUploadContainer() {
        loadCustomModels();

        if ($('btnCustBulkUpload')) {
          $('btnCustBulkUpload').onclick = () => {
            switchInvSubView('upload');
          };
        }

        const syncCustMode = () => {
          const isAuto = $('choiceCustAuto') && $('choiceCustAuto').checked;
          const isExisting = $('choiceCustExisting') && $('choiceCustExisting').checked;
          const isNew = $('choiceCustNew') && $('choiceCustNew').checked;

          if ($('wrapCustAuto')) $('wrapCustAuto').hidden = !isAuto;
          if ($('wrapCustExisting')) $('wrapCustExisting').hidden = !isExisting;
          if ($('wrapCustNew')) $('wrapCustNew').hidden = !isNew;

          if ($('lblCustAuto')) {
            $('lblCustAuto').style.background = isAuto ? 'var(--primary)' : 'transparent';
            $('lblCustAuto').style.color = isAuto ? '#fff' : 'inherit';
          }
          if ($('lblCustExisting')) {
            $('lblCustExisting').style.background = isExisting ? 'var(--primary)' : 'transparent';
            $('lblCustExisting').style.color = isExisting ? '#fff' : 'inherit';
          }
          if ($('lblCustNew')) {
            $('lblCustNew').style.background = isNew ? 'var(--primary)' : 'transparent';
            $('lblCustNew').style.color = isNew ? '#fff' : 'inherit';
          }

          if (window._lastUploadedFile) reprocessCurrentFile();
        };
        window.syncUploadCustMode = syncCustMode;

        document.querySelectorAll('input[name="uploadCustChoice"]').forEach(r => {
          r.onchange = syncCustMode;
        });

        // Populate existing customer selector
        const populateCustDropdown = () => {
          if (!$('uploadExistingCustSel')) return;
          const cur = $('uploadExistingCustSel').value;
          const opts = (CU || []).map(c => {
            const count = c.device_count || c.count || 0;
            return `<option value="${esc(c.name)}">${esc(c.name)} (${count.toLocaleString()} records)</option>`;
          }).join('');
          $('uploadExistingCustSel').innerHTML = `<option value="">-- Choose Existing Customer --</option>` + opts;
          if (cur) $('uploadExistingCustSel').value = cur;
        };
        populateCustDropdown();
        window.refreshUploadCustDropdown = populateCustDropdown;

        if ($('uploadExistingCustSel')) {
          $('uploadExistingCustSel').onchange = () => {
            const val = $('uploadExistingCustSel').value.trim();
            if (val) {
              if ($('uploadExistingCustInfo')) {
                $('uploadExistingCustInfo').innerHTML = `<span style="color:var(--ok);font-weight:600">✓ Customer "${esc(val)}" selected</span> &bull; MySQL Table: <code>${esc(val)}</code>`;
              }
            } else {
              if ($('uploadExistingCustInfo')) $('uploadExistingCustInfo').textContent = '';
            }
            if (window._lastUploadedFile) reprocessCurrentFile();
          };
        }

        if ($('uploadNewCustName')) {
          $('uploadNewCustName').oninput = () => {
            const val = $('uploadNewCustName').value.trim();
            if (val) {
              const match = (CU || []).find(c => c.name.toLowerCase() === val.toLowerCase());
              const clean = val.replace(/[^a-zA-Z0-9_]+/g, '_').replace(/^_+|_+$/g, '') || val;
              if ($('uploadNewCustHint')) {
                if (match) {
                  $('uploadNewCustHint').innerHTML = `<span style="color:var(--primary);font-weight:600">Matches existing customer <b>"${esc(match.name)}"</b> (will add to it)</span>`;
                } else {
                  $('uploadNewCustHint').innerHTML = `Cloud Table & Website Name: <b><code>${esc(clean)}</code></b>`;
                }
              }
            } else {
              if ($('uploadNewCustHint')) $('uploadNewCustHint').textContent = '';
            }
            if (window._lastUploadedFile) reprocessCurrentFile();
          };
        }

        // Model and "+ New model" handler
        const optModelSel = $('optModel');
        const optNewModelInp = $('optNewModel');
        if (optModelSel) {
          optModelSel.onchange = () => {
            if (optModelSel.value === '__new__') {
              optNewModelInp.hidden = false;
              optNewModelInp.focus();
            } else {
              optNewModelInp.hidden = true;
              if (window._lastUploadedFile) reprocessCurrentFile();
            }
          };
        }
        if (optNewModelInp) {
          optNewModelInp.onchange = () => {
            const val = optNewModelInp.value.trim();
            if (val) {
              const saved = JSON.parse(localStorage.getItem('custom_models') || '[]');
              if (!saved.includes(val)) {
                saved.push(val);
                localStorage.setItem('custom_models', JSON.stringify(saved));
              }
              loadCustomModels();
              optModelSel.value = val;
              optNewModelInp.hidden = true;
              if (window._lastUploadedFile) reprocessCurrentFile();
            }
          };
        }

        ['optDispatchedDate', 'optActDate', 'optExpiryDate', 'optFlash', 'optFirmware', 'optSimProvider', 'dupMode'].forEach(id => {
          if ($(id)) {
            $(id).onchange = () => {
              if (window._lastUploadedFile) reprocessCurrentFile();
            };
          }
        });

        const resolveSheetCustomer = (sheetName, fileName) => {
          const s = (sheetName || '').trim();
          const baseFile = (fileName || '').replace(/\.[^/.]+$/, '').trim();

          // 1. If user explicitly chose "Pick Existing Customer"
          if ($('choiceCustExisting') && $('choiceCustExisting').checked) {
            const picked = $('uploadExistingCustSel') ? $('uploadExistingCustSel').value.trim() : '';
            if (picked) return { name: picked, isExisting: true, isManual: true, originalSheet: s };
          }

          // 2. If user explicitly chose "Type New Customer"
          if ($('choiceCustNew') && $('choiceCustNew').checked) {
            const typed = $('uploadNewCustName') ? $('uploadNewCustName').value.trim() : '';
            if (typed) {
              const m = (CU || []).find(c => (c.name || '').toLowerCase() === typed.toLowerCase());
              return { name: m ? m.name : typed, isExisting: !!m, isManual: true, originalSheet: s };
            }
          }

          // 3. Automatic Mode: Check if sheet name is in our database!
          const findInCU = name => {
            if (!name) return null;
            const lower = name.toLowerCase();
            const clean = lower.replace(/[^a-z0-9]/g, '');
            // Case-insensitive exact match
            let found = (CU || []).find(c => (c.name || '').trim().toLowerCase() === lower);
            if (found) return found;
            // Normalized match (ignoring spaces, underscores, symbols)
            found = (CU || []).find(c => (c.name || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '') === clean);
            if (found) return found;
            return null;
          };

          // Check if sheet name exists in database
          let match = findInCU(s);
          if (match) {
            // Sheet name IS in database -> push those records into that existing customer!
            return { name: match.name, isExisting: true, originalSheet: s, matchedBy: 'sheet_db' };
          }

          // If sheet name is a generic placeholder like "Sheet1", check if base fileName is in DB
          const isGeneric = /^(sheet\s*\d+|page\s*\d+|tab\s*\d+|worksheet\s*\d+)$/i.test(s);
          if (isGeneric && baseFile) {
            const fileMatch = findInCU(baseFile);
            if (fileMatch) {
              return { name: fileMatch.name, isExisting: true, originalSheet: s, matchedBy: 'file_db' };
            }
          }

          // Sheet name is not in database: create a new customer with this sheet name and add records
          let target = s;
          if (isGeneric && baseFile) target = baseFile;
          const cleanNew = target.replace(/[^a-zA-Z0-9_\s-]/g, '').trim().replace(/\s+/g, '_') || target;
          return { name: cleanNew, isExisting: false, originalSheet: s, matchedBy: 'new' };
        };

        const getSheetCustomerName = (sheetName, fileName) => {
          return resolveSheetCustomer(sheetName, fileName).name;
        };

        const getEffectiveCustomer = (sheetName, fileName) => {
          return resolveSheetCustomer(sheetName, fileName).name;
        };

        const reprocessCurrentFile = () => {
          if (window._lastUploadedFile) {
            handleFileSelected(window._lastUploadedFile);
          }
        };

        const handleFileSelected = async file => {
          window._lastUploadedFile = file;
          if ($('wbFileName')) {
            $('wbFileName').hidden = false;
            $('wbFileName').innerHTML = `📄 <b>${esc(file.name)}</b> (${(file.size / 1024).toFixed(1)} KB)`;
          }

          toast('Reading workbook…');
          try {
            await loadCU(); // ensure customer database cache is up-to-date
            const buf = await file.arrayBuffer();
            wbData = XLSX.read(new Uint8Array(buf), { type: 'array' });
            const sheets = wbData.SheetNames;

            // Filter out empty sheets automatically (needs header row + at least 1 data row)
            const validSheets = [];
            sheets.forEach(sName => {
              const sheet = wbData.Sheets[sName];
              if (!sheet) return;
              const rows2D = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
              const nonEmptyRows = rows2D.filter(r => Array.isArray(r) && r.some(c => c !== null && c !== undefined && String(c).trim() !== ''));
              if (nonEmptyRows.length >= 2) {
                validSheets.push({
                  sheetName: sName,
                  rowCount: nonEmptyRows.length - 1
                });
              }
            });

            if (!validSheets.length) {
              toast('⚠️ No non-empty sheets found in workbook.');
              $('sheetSelectWrap').hidden = true;
              $('valSummaryWrap').hidden = true;
              return;
            }

            $('sheetSelectWrap').hidden = false;
            $('sheetList').innerHTML = validSheets.map(item => {
              const s = item.sheetName;
              const count = item.rowCount;
              const custInfo = resolveSheetCustomer(s, file.name);
              return `
          <label style="display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:13px;background:var(--card);padding:10px 14px;border:1.5px solid ${custInfo.isExisting ? 'var(--primary)' : 'var(--ok)'};border-radius:10px;cursor:pointer;flex:1;min-width:280px">
            <div style="display:flex;align-items:center;gap:10px">
              <input type="checkbox" class="sheet-chk" value="${esc(s)}" checked style="width:16px;height:16px;margin:0;accent-color:var(--primary)" />
              <div>
                <div style="font-weight:700;font-size:13.5px;color:var(--ink)">
                  📄 <b>${esc(s)}</b> <span style="font-size:12px;font-weight:normal;color:var(--muted)">(${count.toLocaleString()} data rows)</span>
                </div>
                <div style="font-size:12px;margin-top:2px">
                  ${custInfo.isExisting 
                    ? `<span style="color:var(--primary);font-weight:700">✓ In Database:</span> Push records to customer <b>${esc(custInfo.name)}</b>` 
                    : `<span style="color:var(--ok);font-weight:700">✨ Not in Database:</span> Create new customer <b>${esc(custInfo.name)}</b> and add records`}
                </div>
              </div>
            </div>
            <span class="badge" style="background:${custInfo.isExisting ? 'var(--primary)' : 'var(--ok)'};color:#fff;font-size:11px;font-weight:700;padding:4px 8px;border-radius:6px;white-space:nowrap">
              ${custInfo.isExisting ? 'Existing Customer' : '+ New Customer'}
            </span>
          </label>`;
            }).join('');

            const processSheets = () => {
              const selected = [...document.querySelectorAll('.sheet-chk:checked')].map(c => c.value);
              if (!selected.length) {
                parsedRows = [];
                $('valSummaryWrap').hidden = true;
                toast('⚠️ Please select at least one worksheet.');
                return;
              }

              // Auto-populate optional fields from file if currently unselected / blank in UI
              selected.forEach(sName => {
                const sheet = wbData.Sheets[sName];
                const rawSample = XLSX.utils.sheet_to_json(sheet, { defval: '' });
                for (const r of rawSample) {
                  const dev = normalizeExcelRow(r);
                  if ($('optModel') && !$('optModel').value && dev.model) {
                    const exists = [...$('optModel').options].some(o => o.value === dev.model);
                    if (exists) $('optModel').value = dev.model;
                    else {
                      $('optModel').value = '__new__';
                      if ($('optNewModel')) {
                        $('optNewModel').hidden = false;
                        $('optNewModel').value = dev.model;
                      }
                    }
                  }
                  if ($('optDispatchedDate') && !$('optDispatchedDate').value && dev.dispatched_date) $('optDispatchedDate').value = dev.dispatched_date;
                  if ($('optActDate') && !$('optActDate').value && dev.act_date) $('optActDate').value = dev.act_date;
                  if ($('optExpiryDate') && !$('optExpiryDate').value && dev.expiry_date) $('optExpiryDate').value = dev.expiry_date;
                  if ($('optFlash') && !$('optFlash').value && dev.flash) $('optFlash').value = dev.flash;
                  if ($('optFirmware') && !$('optFirmware').value && dev.firmware) $('optFirmware').value = dev.firmware;
                  if ($('optSimProvider') && !$('optSimProvider').value && dev.sim_provider) $('optSimProvider').value = dev.sim_provider;
                }
              });

              const optModel = (optModelSel && optModelSel.value !== '__new__') ? optModelSel.value.trim() : ($('optNewModel') ? $('optNewModel').value.trim() : '');
              const optDispatchedDate = $('optDispatchedDate') ? $('optDispatchedDate').value.trim() : '';
              const optActDate = $('optActDate') ? $('optActDate').value.trim() : '';
              const optExpiryDate = $('optExpiryDate') ? $('optExpiryDate').value.trim() : '';
              const optFlash = $('optFlash') ? $('optFlash').value.trim() : '';
              const optFirmware = $('optFirmware') ? $('optFirmware').value.trim() : '';
              const optSimProvider = $('optSimProvider') ? $('optSimProvider').value.trim() : '';

              const allRows = [];
              const sheetCustSummaries = [];
              let totalIgnoredEmptyRows = 0;

              selected.forEach(sName => {
                const sheet = wbData.Sheets[sName];
                const raw = XLSX.utils.sheet_to_json(sheet, { defval: '' });
                const custInfo = resolveSheetCustomer(sName, file.name);
                const assignedCust = custInfo.name;

                // Detect if sheet has any non-empty ICCID
                let sheetHasIccid = false;
                const preRows = [];
                raw.forEach(r => {
                  const isRowEmpty = Object.values(r).every(v => v === null || v === undefined || String(v).trim() === '');
                  if (isRowEmpty) {
                    totalIgnoredEmptyRows++;
                    return;
                  }
                  const dev = normalizeExcelRow(r);
                  if (dev.iccid && String(dev.iccid).trim()) {
                    sheetHasIccid = true;
                  }
                  preRows.push(dev);
                });

                sheetCustSummaries.push({
                  sheetName: sName,
                  customerName: assignedCust,
                  isExisting: custInfo.isExisting,
                  rowCount: preRows.length
                });

                // Automatic SIM Type: ICCID present = E-SIM, otherwise Plastic SIM
                const sheetSimType = sheetHasIccid ? 'E-SIM' : 'Plastic SIM';

                preRows.forEach(dev => {
                  // Determine customer for this record: row-level customer takes precedence if present
                  let rowCustName = assignedCust;
                  if (dev.customer_name && String(dev.customer_name).trim()) {
                    const rowCustRaw = String(dev.customer_name).trim();
                    const lower = rowCustRaw.toLowerCase();
                    const clean = lower.replace(/[^a-z0-9]/g, '');
                    const m = (CU || []).find(c => (c.name || '').trim().toLowerCase() === lower || (c.name || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '') === clean);
                    if (m) {
                      rowCustName = m.name;
                    } else {
                      rowCustName = rowCustRaw.replace(/[^a-zA-Z0-9_\s-]/g, '').trim().replace(/\s+/g, '_') || rowCustRaw;
                    }
                  }
                  dev.customer_name = rowCustName;
                  dev.sim_type = sheetSimType;

                  // Optional defaults: if row already has a value, row's value wins
                  if (!dev.model && optModel) dev.model = optModel;
                  if (!dev.dispatched_date && optDispatchedDate) dev.dispatched_date = optDispatchedDate;
                  if (!dev.act_date && optActDate) dev.act_date = optActDate;
                  if (!dev.expiry_date && optExpiryDate) dev.expiry_date = optExpiryDate;
                  if (!dev.flash && optFlash) dev.flash = optFlash;
                  if (!dev.firmware && optFirmware) dev.firmware = optFirmware;
                  if (!dev.sim_provider && optSimProvider) dev.sim_provider = optSimProvider;

                  allRows.push(dev);
                });
              });

              // Map of all identified customers across the scanned file
              const custSummaryMap = new Map();
              allRows.forEach(dev => {
                const cn = dev.customer_name || 'General_Customer';
                if (!custSummaryMap.has(cn)) {
                  const lower = cn.toLowerCase();
                  const clean = lower.replace(/[^a-z0-9]/g, '');
                  const isEx = (CU || []).some(c => (c.name || '').trim().toLowerCase() === lower || (c.name || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '') === clean);
                  custSummaryMap.set(cn, { name: cn, isExisting: isEx, count: 0, duplicateCount: 0 });
                }
                custSummaryMap.get(cn).count++;
              });
              window._currentCustSummaryList = Array.from(custSummaryMap.values());

              // Render Target Customer Banner
              if ($('valTargetCustBanner')) {
                const existingList = window._currentCustSummaryList.filter(s => s.isExisting);
                const newList = window._currentCustSummaryList.filter(s => !s.isExisting);
                $('valTargetCustBanner').innerHTML = `
                  <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin-bottom:12px">
                    <div style="font-weight:700;font-size:14px;color:var(--ink);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
                      <span>📊 Total Data Scanned: <b>${allRows.length.toLocaleString()} records</b> from <b>${selected.length} sheet(s)</b> across <b>${window._currentCustSummaryList.length} customer(s)</b>${totalIgnoredEmptyRows > 0 ? ` <span style="font-weight:400;color:var(--muted);font-size:12px">(${totalIgnoredEmptyRows.toLocaleString()} empty rows ignored)</span>` : ''}</span>
                      <span style="font-size:12px;color:var(--muted)">Existing Customers in DB &rarr; Update/Add | New Customers &rarr; Create Table Automatically</span>
                    </div>
                    <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:8px">
                      ${existingList.map(s => `<span class="badge" style="background:rgba(37,99,235,0.12);color:var(--primary);border:1px solid var(--primary);font-size:12px;padding:4px 10px;border-radius:6px">📋 <b>${esc(s.name)}</b> (${s.count.toLocaleString()} rows, Existing Customer)</span>`).join('')}
                      ${newList.map(s => `<span class="badge" style="background:rgba(16,185,129,0.12);color:var(--ok);border:1.5px solid var(--ok);font-size:12px;padding:4px 10px;border-radius:6px;box-shadow:0 0 6px rgba(16,185,129,0.25)">✨ <b>${esc(s.name)}</b> (${s.count.toLocaleString()} rows, New Customer)</span>`).join('')}
                    </div>
                  </div>
                `;
              }

              parsedRows = allRows;
              validateAndPreview(parsedRows);
            };

            window._processSheets = processSheets;
            if ($('btnValidateFile')) {
              $('btnValidateFile').onclick = () => {
                toast('🔍 Validating sheets against database…');
                processSheets();
              };
            }
            $('valSummaryWrap').hidden = true;
            toast('Worksheets scanned! Click "Validate File & Check Entries" to verify database tables and segregate entries.');
          } catch (err) { fail(err); }
        };

        // Sheet Select all and Clear
        if ($('btnSheetSelectAll')) {
          $('btnSheetSelectAll').onclick = () => {
            document.querySelectorAll('.sheet-chk').forEach(c => c.checked = true);
            if (window._processSheets && !$('valSummaryWrap').hidden) window._processSheets();
          };
        }
        if ($('btnSheetClear')) {
          $('btnSheetClear').onclick = () => {
            document.querySelectorAll('.sheet-chk').forEach(c => c.checked = false);
            if (window._processSheets && !$('valSummaryWrap').hidden) window._processSheets();
          };
        }

        // Dropzone setup
        const dropzone = $('wbDropzone');
        const fileInput = $('wbFile');
        if (dropzone && fileInput) {
          dropzone.onclick = () => fileInput.click();
          dropzone.ondragover = e => {
            e.preventDefault();
            dropzone.style.borderColor = 'var(--primary)';
            dropzone.style.background = 'var(--card-subtle)';
          };
          dropzone.ondragleave = () => {
            dropzone.style.borderColor = 'var(--line)';
            dropzone.style.background = 'var(--bg)';
          };
          dropzone.ondrop = async e => {
            e.preventDefault();
            dropzone.style.borderColor = 'var(--line)';
            dropzone.style.background = 'var(--bg)';
            const file = e.dataTransfer.files[0];
            if (file) {
              if (!file.name.match(/\.(xlsx|xls)$/i)) {
                toast('⚠️ Please select an Excel (.xlsx or .xls) file.');
                return;
              }
              await handleFileSelected(file);
            }
          };
          fileInput.onchange = async e => {
            const file = e.target.files[0];
            if (!file) return;
            await handleFileSelected(file);
          };
        }

        function renderValidationTable(sampleRows) {
          if (!sampleRows || !sampleRows.length) {
            return '<div class="empty">No records in this segregation category.</div>';
          }
          return `
      <table class="data-table" style="font-size:12px">
        <thead>
          <tr>
            <th>#</th>
            <th>Segregation Status</th>
            <th>Expiry Status</th>
            <th>Reason & Changed Fields</th>
            <th>Customer</th>
            <th>Device Sr No</th>
            <th>IMEI</th>
            <th>ICCID</th>
            <th>SIM Type</th>
            <th>Model</th>
            <th>SIM Provider</th>
            <th>Act Date</th>
            <th>Expiry Date</th>
            <th>Dispatched Date</th>
            <th>Flash</th>
            <th>Firmware</th>
            <th>Extra Columns</th>
          </tr>
        </thead>
        <tbody>
          ${sampleRows.map(r => {
            const st = r.entry_type || r.status || 'New';
            let badgeBg = 'var(--ok)';
            let badgeText = '✨ New Entry (Eligible for Insertion)';
            if (st === 'Requires Update' || st === 'Updated') {
              badgeBg = '#0284c7';
              badgeText = '🔄 Existing in DB (Changed Values Will Be Updated)';
            } else if (st === 'Existing') {
              badgeBg = '#64748b';
              badgeText = '📋 Existing in DB (Identical — Left Unchanged)';
            } else if (st === 'Duplicate') {
              badgeBg = 'var(--warn)';
              badgeText = '⚠️ In-File Duplicate (Skipped)';
            } else if (st === 'Invalid') {
              badgeBg = 'var(--danger)';
              badgeText = '❌ Invalid Record (Skipped)';
            }

            const normExp = String(r.expiry_status || '').toLowerCase().replace(/[\s_-]+/g, '');
            let expBadge = '—';
            if (normExp === 'expired') {
              expBadge = '<span class="exp-badge-expired">🚨 Expired</span>';
            } else if (normExp.includes('soon')) {
              expBadge = '<span class="exp-badge-soon">⏰ Expiring Soon</span>';
            } else if (normExp === 'active') {
              expBadge = '<span class="exp-badge-active">✅ Active</span>';
            } else if (normExp === 'unknown') {
              expBadge = '<span class="exp-badge-unknown">❓ Unknown</span>';
            }

            const extraStr = r.extra ? Object.entries(r.extra).map(([k, v]) => `${esc(k)}: ${esc(v)}`).join(', ') : '—';
            return `
              <tr>
                <td>${r.row_num || '—'}</td>
                <td><span class="badge" style="background:${badgeBg};color:${st === 'Duplicate' ? '#111' : '#fff'};font-weight:700;padding:3px 8px;border-radius:4px">${badgeText}</span></td>
                <td>${expBadge}</td>
                <td style="color:${st === 'Invalid' ? 'var(--danger)' : (st === 'Duplicate' ? 'var(--warn)' : ((st === 'Updated' || st === 'Requires Update') ? '#0284c7' : (st === 'Existing' ? 'var(--muted)' : 'var(--ok)')))}">${esc(r.reason || '')}</td>
                <td><b>${esc(r.customer_name || '—')}</b></td>
                <td><code>${esc(r.device_sr_no || '—')}</code></td>
                <td><b><code>${esc(r.imei || '—')}</code></b></td>
                <td><code>${esc(r.iccid || '—')}</code></td>
                <td><span class="badge" style="background:${r.sim_type === 'E-SIM' ? '#38bdf8' : '#a855f7'};color:#fff">${esc(r.sim_type || '—')}</span></td>
                <td>${esc(r.model || '—')}</td>
                <td>${esc(r.sim_provider || '—')}</td>
                <td>${esc(r.act_date || '—')}</td>
                <td><b>${esc(r.expiry_date || '—')}</b></td>
                <td>${esc(r.dispatched_date || '—')}</td>
                <td>${esc(r.flash || '—')}</td>
                <td>${esc(r.firmware || '—')}</td>
                <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(extraStr)}">${extraStr}</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
        }

        function applyPreviewFilter(filter) {
          activeValFilter = filter || 'new';
          document.querySelectorAll('#valFilterBtns button').forEach(b => {
            b.classList.toggle('on', b.dataset.valfilter === activeValFilter);
          });
          if (!activeValResult) return;
          let list = [];
          if (activeValFilter === 'new') list = activeValResult.new_sample || [];
          else if (activeValFilter === 'updated' || activeValFilter === 'update') list = activeValResult.updated_sample || [];
          else if (activeValFilter === 'existing') list = activeValResult.existing_sample || [];
          else if (activeValFilter === 'review' || activeValFilter === 'invalid') list = activeValResult.invalid_sample || activeValResult.invalids || [];
          else if (activeValFilter === 'duplicate') list = activeValResult.duplicates || [];
          else if (activeValFilter === 'cannot') {
            list = (activeValResult.duplicates || []).concat(activeValResult.existing_sample || []);
          }
          else list = activeValResult.all_sample || [];

          // Search filtering
          const searchVal = $('valReviewSearch') ? $('valReviewSearch').value.trim().toLowerCase() : '';
          if (searchVal) {
            list = list.filter(r => {
              const imei = String(r.imei || '').toLowerCase();
              const sr = String(r.device_sr_no || '').toLowerCase();
              const iccid = String(r.iccid || '').toLowerCase();
              const cust = String(r.customer_name || '').toLowerCase();
              const model = String(r.model || '').toLowerCase();
              const reason = String(r.reason || '').toLowerCase();
              return imei.includes(searchVal) || sr.includes(searchVal) || iccid.includes(searchVal) || cust.includes(searchVal) || model.includes(searchVal) || reason.includes(searchVal);
            });
          }

          // Row display limit
          const limitVal = $('valReviewLimit') ? $('valReviewLimit').value : '100';
          let displayList = list;
          if (limitVal !== 'all') {
            const num = parseInt(limitVal, 10) || 100;
            displayList = list.slice(0, num);
          }

          if ($('valPreviewTableNote')) {
            $('valPreviewTableNote').textContent = `Showing ${displayList.length.toLocaleString()} of ${list.length.toLocaleString()} records in this view (Total parsed: ${parsedRows.length.toLocaleString()}).`;
          }

          $('valPreviewTable').innerHTML = renderValidationTable(displayList);
        }

        document.querySelectorAll('#valFilterBtns button').forEach(b => {
          b.onclick = () => applyPreviewFilter(b.dataset.valfilter);
        });

        if ($('valReviewSearch')) {
          $('valReviewSearch').oninput = () => applyPreviewFilter(activeValFilter);
        }
        if ($('valReviewLimit')) {
          $('valReviewLimit').onchange = () => applyPreviewFilter(activeValFilter);
        }

        async function validateAndPreview(rows) {
          if (!rows.length) {
            $('valSummaryWrap').hidden = true;
            return;
          }
          $('valSummaryWrap').hidden = false;
          $('valPreviewTable').innerHTML = '<div class="empty">Validating against database and segregating into New, Updated, and Existing records…</div>';
          showBstplLoader(`Validating ${rows.length.toLocaleString()} entries against database…`, 0);
          if (window.renderFileStatus) window.renderFileStatus('checking');

          // Show the customer identification card immediately (it only needs the file + customer list), so it never stays at 0 if the server check fails.
          try {
            const _cl = window._currentCustSummaryList || [];
            const _setT = (id, v) => { if ($(id)) $(id).textContent = Number(v).toLocaleString(); };
            _setT('vExistingCustCount', _cl.filter(c => c.isExisting).length);
            _setT('vNewCustCount', _cl.filter(c => !c.isExisting).length);
            _setT('vTotalScannedSummary', rows.length);
            _setT('vTotalScanned', rows.length);
            if ($('custIdentTableWrap')) {
              $('custIdentTableWrap').innerHTML = '<table class="data-table" style="font-size:12px;margin:0"><thead><tr><th style="width:50px">#</th><th>Customer Name</th><th>Scanned Entries</th><th>Customer Status</th></tr></thead><tbody>' +
                _cl.map((c, i) => `<tr class="${c.isExisting ? '' : 'cust-highlight-new'}"><td>${i + 1}</td><td><b>${esc(c.name)}</b></td><td><b>${c.count.toLocaleString()}</b> entries</td><td>${c.isExisting ? '📋 Already Existing Customer' : '✨ New Customer'}</td></tr>`).join('') +
                '</tbody></table>';
            }
          } catch (_e) { /* summary is cosmetic */ }

          try {
            // Every row ends up as exactly one of: N new | U in database but values differ | E in database, identical | D duplicate | I invalid
            const runId = window._valRunId = (window._valRunId || 0) + 1;   // a newer validation replaces this one
            const stale = () => runId !== window._valRunId;
            const N = rows.length;
            const rowStatus = new Array(N).fill('N');
            const rowReasons = new Map();               // row index -> reason (rows that are NOT added)

            // 1) Duplicates inside the file, looked for across the WHOLE file (not batch by batch).
            const nk = v => String(v ?? '').trim().replace(/\.0+$/, '').toLowerCase();
            const nIccid = v => nk(v).replace(/[\s\-_]+/g, '');
            const seenIccid = new Map(), seenImei = new Map(), seenSr = new Map();   // value -> first row number
            const fileDups = [];
            const uniq = [];                            // indexes of rows sent to the server
            const fileCustDups = {};
            rows.forEach((r, i) => {
              const kc = nIccid(r.iccid), ki = nk(r.imei), ks = nk(r.device_sr_no);
              let why = '';
              if (kc && seenIccid.has(kc)) why = `Duplicate ICCID '${String(r.iccid).trim()}' repeats earlier in this uploaded file (same full value as row ${seenIccid.get(kc)})`;
              else if (ki && seenImei.has(ki)) why = `Duplicate IMEI '${String(r.imei).trim()}' repeats earlier in this uploaded file (same full value as row ${seenImei.get(ki)})`;
              else if (ks && seenSr.has(ks)) why = `Duplicate Device Sr No '${String(r.device_sr_no).trim()}' repeats earlier in this uploaded file (same full value as row ${seenSr.get(ks)})`;
              if (kc && !seenIccid.has(kc)) seenIccid.set(kc, i + 1);
              if (ki && !seenImei.has(ki)) seenImei.set(ki, i + 1);
              if (ks && !seenSr.has(ks)) seenSr.set(ks, i + 1);
              if (why) {
                rowStatus[i] = 'D';
                rowReasons.set(i, why);
                fileDups.push(Object.assign({}, r, { row_num: i + 1, entry_type: 'Duplicate', status: 'Duplicate', reason: why }));
                const cn = r.customer_name || 'General_Customer';
                fileCustDups[cn] = (fileCustDups[cn] || 0) + 1;
              } else {
                uniq.push(i);
              }
            });

            // 2) The rest is compared with the database in batches, a few at a time.
            const valResult = {
              total_count: N, valid_count: 0, new_count: 0, updated_count: 0, existing_count: 0,
              duplicate_count: fileDups.length, invalid_count: 0,
              new_sample: [], updated_sample: [], existing_sample: [], invalid_sample: [], invalids: [],
              duplicates: fileDups.slice(0, 50000), all_sample: [],
              customer_duplicates: fileCustDups, new_customers: [], new_columns: [], missing_columns_warning: [],
              expiry_counts: { expired: 0, expiring_soon: 0, active: 0, unknown: 0 }
            };
            const CAP = 2000;
            const newCustSet = new Set(), newColSet = new Set();
            const fixRow = (x, off) => Object.assign({}, x, { row_num: uniq[off + (x.row_num - 1)] + 1 });
            const push = (arr, list, off) => { for (const x of (list || [])) { if (arr.length >= CAP) break; arr.push(fixRow(x, off)); } };

            const BATCH = 2000, tasks = [];
            for (let off = 0; off < uniq.length; off += BATCH) tasks.push(off);
            let done = 0;
            const runBatch = async (off) => {
              if (stale()) return;
              const idxs = uniq.slice(off, off + BATCH);
              const res = await api('/api/devices/bulk/validate?compact=1', {
                method: 'POST',
                body: JSON.stringify({ rows: idxs.map(i => rows[i]), mode: 'skip' })
              });
              if (stale()) return;
              const rs = res.row_status || '';
              if (rs.length !== idxs.length) throw new Error('The server answered with a different number of rows than were sent. Please reload the page and try again.');
              for (let j = 0; j < idxs.length; j++) rowStatus[idxs[j]] = rs[j];
              const rr = res.row_reasons || {}, tbl = res.reason_table || [];
              for (const k in rr) rowReasons.set(idxs[+k], tbl[rr[k]]);

              valResult.new_count += res.new_count || 0;
              valResult.updated_count += res.updated_count || 0;
              valResult.existing_count += res.existing_count || 0;
              valResult.duplicate_count += res.duplicate_count || 0;
              valResult.invalid_count += res.invalid_count || 0;
              push(valResult.new_sample, res.new_sample, off);
              push(valResult.updated_sample, res.updated_sample, off);
              push(valResult.existing_sample, res.existing_sample, off);
              push(valResult.invalid_sample, res.invalid_sample, off);
              for (const x of (res.duplicates || [])) {
                if (valResult.duplicates.length >= 50000) break;
                valResult.duplicates.push(fixRow(x, off));
                const cn = x.customer_name || 'General_Customer';
                valResult.customer_duplicates[cn] = (valResult.customer_duplicates[cn] || 0) + 1;
              }
              (res.new_customers || []).forEach(c => newCustSet.add(c));
              (res.new_columns || []).forEach(c => newColSet.add(c));
              (res.missing_columns_warning || []).forEach(c => { if (!valResult.missing_columns_warning.includes(c)) valResult.missing_columns_warning.push(c); });
              const ec = res.expiry_counts || {};
              ['expired', 'expiring_soon', 'active', 'unknown'].forEach(k => { valResult.expiry_counts[k] += ec[k] || 0; });
              done += idxs.length;
              updateBstplLoader(`Validating rows against database (${done.toLocaleString()} / ${uniq.length.toLocaleString()})…`, Math.round(done / Math.max(1, uniq.length) * 100));
            };
            let nextTask = 0, failure = null;
            const worker = async () => {
              while (nextTask < tasks.length && !failure && !stale()) {
                const off = tasks[nextTask++];
                try { await runBatch(off); } catch (e) { failure = failure || e; }
              }
            };
            await Promise.all([worker(), worker(), worker()]);
            if (stale()) return;
            if (failure) throw failure;

            valResult.new_customers = Array.from(newCustSet);
            valResult.new_columns = Array.from(newColSet);
            valResult.valid_count = valResult.new_count + valResult.updated_count;
            valResult.entries_requiring_update = valResult.updated_sample;   // used by the older "rectify" buttons
            valResult.all_sample = valResult.new_sample.slice(0, 150).concat(valResult.updated_sample.slice(0, 150), valResult.existing_sample.slice(0, 150));
            valResult.rowStatus = rowStatus;
            valResult.rowReasons = rowReasons;
            activeValResult = valResult;

            const newCnt = valResult.new_count || 0;
            const updatedCnt = valResult.updated_count || 0;
            const existingCnt = valResult.existing_count || 0;
            const dupCnt = valResult.duplicate_count || 0;
            const invalidCnt = valResult.invalid_count || 0;
            const totalCnt = valResult.total_count || rows.length;

            const validCnt = Math.max(0, totalCnt - dupCnt - invalidCnt);   // every row that passed all checks (new + changed + identical)
            const reviewCnt = invalidCnt;
            const eligibleToAdd = newCnt + invalidCnt;        // not in the database yet -> inserted (invalid rows are pushed as they are)
            const eligibleToUpdate = updatedCnt;              // in the database, values differ -> only the changed values are replaced
            const cannotAdd = Math.max(0, totalCnt - eligibleToAdd - updatedCnt);   // duplicates + identical-to-database (NOT uploaded)

            // Update 7 Metric Cards (Requirement 3, 5 & 7)
            if ($('vTotalScanned')) $('vTotalScanned').textContent = totalCnt.toLocaleString();
            if ($('vValid')) $('vValid').textContent = validCnt.toLocaleString();
            if ($('vReview')) $('vReview').textContent = reviewCnt.toLocaleString();
            if ($('vDup')) $('vDup').textContent = dupCnt.toLocaleString();
            if ($('vNew')) $('vNew').textContent = newCnt.toLocaleString();
            if ($('vUpdated')) $('vUpdated').textContent = eligibleToUpdate.toLocaleString();
            if ($('vCannotAdd')) $('vCannotAdd').textContent = cannotAdd.toLocaleString();

            // Reconciliation Math Container (Requirement 7)
            if ($('valReconciliationBox')) $('valReconciliationBox').hidden = false;
            if ($('reconcileEquation')) {
              $('reconcileEquation').textContent = `${totalCnt.toLocaleString()} = ${newCnt.toLocaleString()} (Add) + ${eligibleToUpdate.toLocaleString()} (Update) + ${existingCnt.toLocaleString()} (Unchanged) + ${dupCnt.toLocaleString()} (Duplicates) + ${invalidCnt.toLocaleString()} (Invalid, uploaded as is)`;
            }
            if ($('reconcileBadge')) {
              const accounted = newCnt + updatedCnt + existingCnt + dupCnt + invalidCnt;
              const balanced = accounted === totalCnt;
              $('reconcileBadge').textContent = balanced ? '✅ 100% Fully Accounted & Reconciled' : `⚠️ ${Math.abs(totalCnt - accounted).toLocaleString()} row(s) not accounted for`;
              $('reconcileBadge').className = balanced ? 'tag ok' : 'tag warn';
            }

            // Upload Expiry Date Tracking Summary (Requirement 10)
            if ($('valUploadExpirySummaryBox')) $('valUploadExpirySummaryBox').hidden = false;
            const expCounts = valResult.expiry_counts || {};
            if ($('valExpExpired')) $('valExpExpired').textContent = (expCounts.expired || 0).toLocaleString();
            if ($('valExpSoon')) $('valExpSoon').textContent = (expCounts.expiring_soon || 0).toLocaleString();
            if ($('valExpActive')) $('valExpActive').textContent = (expCounts.active || 0).toLocaleString();
            if ($('valExpUnknown')) $('valExpUnknown').textContent = (expCounts.unknown || 0).toLocaleString();

            // Update Filter Badges
            if ($('vAllCount')) $('vAllCount').textContent = totalCnt.toLocaleString();
            if ($('vNewCount')) $('vNewCount').textContent = eligibleToAdd.toLocaleString();
            if ($('vUpdatedCount')) $('vUpdatedCount').textContent = updatedCnt.toLocaleString();
            if ($('vUpdatedBtnCount')) $('vUpdatedBtnCount').textContent = updatedCnt.toLocaleString();
            if ($('vExistingCountCard')) $('vExistingCountCard').textContent = existingCnt.toLocaleString();
            if ($('vInvalidCount')) $('vInvalidCount').textContent = invalidCnt.toLocaleString();
            if ($('vInvalidBtnCount')) $('vInvalidBtnCount').textContent = invalidCnt.toLocaleString();
            if ($('vExistingCount')) $('vExistingCount').textContent = existingCnt.toLocaleString();
            if ($('vReviewCount')) $('vReviewCount').textContent = reviewCnt.toLocaleString();
            if ($('vDupCount')) $('vDupCount').textContent = dupCnt.toLocaleString();
            if ($('vCannotCount')) $('vCannotCount').textContent = cannotAdd.toLocaleString();

            // Customer Identification & Duplicate Summary Card (Requirements 2 & 6)
            const custDups = valResult.customer_duplicates || {};
            const custSummaryList = (window._currentCustSummaryList || []).map(c => {
              return {
                name: c.name,
                isExisting: c.isExisting,
                count: c.count,
                duplicateCount: custDups[c.name] || 0
              };
            });

            const existingCustList = custSummaryList.filter(c => c.isExisting);
            const newCustList = custSummaryList.filter(c => !c.isExisting);

            if ($('vExistingCustCount')) $('vExistingCustCount').textContent = existingCustList.length.toLocaleString();
            if ($('vNewCustCount')) $('vNewCustCount').textContent = newCustList.length.toLocaleString();
            if ($('vDupCustSummary')) $('vDupCustSummary').textContent = dupCnt.toLocaleString();
            if ($('vTotalScannedSummary')) $('vTotalScannedSummary').textContent = totalCnt.toLocaleString();

            if ($('custIdentTableWrap')) {
              $('custIdentTableWrap').innerHTML = `
                <table class="data-table" style="font-size:12px;margin:0">
                  <thead>
                    <tr style="background:var(--card-subtle)">
                      <th style="width:50px">#</th>
                      <th>Customer Name</th>
                      <th>Scanned Entries</th>
                      <th>Duplicate Entries</th>
                      <th>Customer Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${custSummaryList.map((c, i) => `
                      <tr class="${c.isExisting ? '' : 'cust-highlight-new'}">
                        <td>${i + 1}</td>
                        <td><b>${esc(c.name)}</b></td>
                        <td><b>${c.count.toLocaleString()}</b> entries</td>
                        <td style="${c.duplicateCount > 0 ? 'color:var(--warn);font-weight:700' : 'color:var(--muted)'}">${c.duplicateCount.toLocaleString()}</td>
                        <td>
                          ${c.isExisting
                            ? `<span class="cust-badge-existing">📋 Already Existing Customer</span>`
                            : `<span class="cust-badge-new">✨ New Customer</span>`}
                        </td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              `;
            }

            $('valColWarnings').hidden = true;

            // Metadata badges (New customers, new cloud columns)
            const badges = [];
            if (valResult.new_customers && valResult.new_customers.length) {
              badges.push(`<span class="badge" style="background:var(--ok);color:#fff;padding:4px 10px;border-radius:6px">📁 New Customers (${valResult.new_customers.length}): <b>${esc(valResult.new_customers.join(', '))}</b> (tables created automatically)</span>`);
            }
            if (valResult.new_columns && valResult.new_columns.length) {
              badges.push(`<span class="badge" style="background:var(--primary);color:#fff;padding:4px 10px;border-radius:6px">📊 New Cloud Columns (${valResult.new_columns.length}): <b>${esc(valResult.new_columns.join(', '))}</b></span>`);
            }
            $('valMetaBadges').innerHTML = badges.join('');

            if (window.renderFileStatus) window.renderFileStatus();

            applyPreviewFilter(activeValFilter || 'all');

            // Submit Button Control: new entries are added, changed existing entries are updated, identical ones are left alone.
            const eligibleTotal = eligibleToAdd + eligibleToUpdate;
            if ($('btnRectifyCountBadge')) $('btnRectifyCountBadge').textContent = eligibleToUpdate.toLocaleString();
            if ($('btnRectifyUpdate')) $('btnRectifyUpdate').hidden = eligibleToUpdate === 0;
            if ($('btnCheckEntriesModal')) $('btnCheckEntriesModal').hidden = false;
            if (eligibleTotal > 0) {
              if ($('btnConfirmUpload')) {
                $('btnConfirmUpload').disabled = false;
                $('btnConfirmUpload').hidden = false;
                $('btnConfirmUpload').innerHTML = `<span>🚀</span> <span>Confirm & Upload: Add ${newCnt.toLocaleString()} New${invalidCnt ? ` + ${invalidCnt.toLocaleString()} Invalid (as is)` : ''}, Update ${eligibleToUpdate.toLocaleString()} Changed (Unchanged Left As Is)</span>`;
              }
              if ($('msgNoEligibleUpload')) $('msgNoEligibleUpload').hidden = true;
            } else {
              if ($('btnConfirmUpload')) {
                $('btnConfirmUpload').disabled = true;
                $('btnConfirmUpload').textContent = `No New or Changed Entries to Upload`;
              }
              if ($('msgNoEligibleUpload')) {
                $('msgNoEligibleUpload').hidden = false;
                $('msgNoEligibleUpload').innerHTML = `
                  <span style="font-size:20px">⚠️</span>
                  <span><b>Nothing to add or update.</b> All entries are either duplicate conflicts, invalid, or already identical to the database.</span>
                `;
              }
            }

            // Download 2-Sheet Excel (Requirement 8)
            if ($('btnDlSkipped')) {
              $('btnDlSkipped').hidden = (dupCnt === 0);
              $('btnDlSkipped').onclick = () => {
                downloadDuplicateErrorsExcel(valResult, custSummaryList, totalCnt);
              };
            }
          } catch (err) {
            if (window.renderFileStatus) window.renderFileStatus({ error: (err && err.message) || String(err) });
            $('valPreviewTable').innerHTML = `<div class="empty err">Validation failed: ${esc((err && err.message) || String(err))}<br><small>Fix the item above (or send me this message) and press Validate again.</small></div>`;
          } finally {
            hideBstplLoader();
          }
        }

        async function executeBulkUpload() {
          if (!parsedRows.length) {
            toast('⚠️ Please select an Excel file first.');
            return;
          }

          const mode = 'replace';
          const policy = ($('dupMode') && $('dupMode').value) || 'both';
          if (!activeValResult || !activeValResult.rowStatus || activeValResult.rowStatus.length !== parsedRows.length) {
            toast('⚠️ Validation is not finished for this file yet. Please wait for it to complete.');
            return;
          }
          if (window._bulkUploadBusy) return;
          window._bulkUploadBusy = true;

          // What happens to each row was decided by the validation (whole file, whole database, recycle bin included).
          const st = activeValResult.rowStatus;
          const why = activeValResult.rowReasons || new Map();
          const FALLBACK_WHY = { E: 'Already exists in database with identical values', D: 'Duplicate entry', I: 'Invalid entry', U: 'Already exists in database (values differ)' };
          const validRowsToUpload = [];     // N: not in the database yet -> inserted
          const rowsToUpdate = [];          // U: in the database, some values differ -> only those values are replaced
          const duplicatesToStage = [];
          let duplicateRecordsSkipped = 0;

          parsedRows.forEach((r, idx) => {
            if ((st[idx] === 'N' || st[idx] === 'I') && policy === 'update') { duplicateRecordsSkipped++; return; }   // update-only: never add
            if (st[idx] === 'N' || st[idx] === 'I') {   // Invalid rows are uploaded as they are; only duplicates are held back
              const rowCopy = Object.assign({}, r);
              if (!rowCopy.customer_name || !String(rowCopy.customer_name).trim()) rowCopy.customer_name = 'General_Customer';
              const cleanImei = String(rowCopy.imei || '').replace(/[^0-9A-Za-z_-]/g, '');
              if (!cleanImei || cleanImei.length < 5) {
                const alt = String(rowCopy.device_sr_no || rowCopy.iccid || '').replace(/[^0-9A-Za-z_-]/g, '');
                rowCopy.imei = (alt && alt.length >= 5) ? alt.substring(0, 20) : 'INV_' + Math.random().toString(36).substring(2, 8).toUpperCase() + (idx + 1);
              }
              validRowsToUpload.push(rowCopy);
              return;
            }
            if (st[idx] === 'U' && policy !== 'skip') {
              // sent exactly as read from the file: the server finds the record the same way validation did
              const rowCopy = Object.assign({}, r);
              if (!rowCopy.customer_name || !String(rowCopy.customer_name).trim()) rowCopy.customer_name = 'General_Customer';
              rowsToUpdate.push(rowCopy);
              return;
            }
            duplicateRecordsSkipped++;
            duplicatesToStage.push({
              customer_name: r.customer_name || 'General_Customer', imei: r.imei || '', device_sr_no: r.device_sr_no || '',
              iccid: r.iccid || '', msisdn1: r.msisdn1 || '', msisdn2: r.msisdn2 || '',
              act_date: r.act_date || null, expiry_date: r.expiry_date || null, dispatched_date: r.dispatched_date || null,
              model: r.model || '', sim_provider: r.sim_provider || '', activation_plan: r.activation_plan || '',
              firmware: r.firmware || '', flash: r.flash || '', sim_type: r.sim_type || '',
              extra: r.extra || null, error_reason: why.get(idx) || FALLBACK_WHY[st[idx]] || 'Not uploaded'
            });
          });
          const workTotal = validRowsToUpload.length + rowsToUpdate.length;   // everything that goes to the server

          if (!workTotal && !duplicatesToStage.length) {
            window._bulkUploadBusy = false;
            toast(duplicateRecordsSkipped && policy === 'update' ? 'Nothing to update: every record in this file is new, and the policy is Update values only.' : '⚠️ No device records found to upload.');
            return;
          }

          $('uploadProgressWrap').hidden = false;
          if ($('progCompleteBanner')) $('progCompleteBanner').hidden = true;
          if ($('btnConfirmUpload')) $('btnConfirmUpload').disabled = true;

          const totalDataCount = workTotal + duplicatesToStage.length;
          if ($('progTotalCount')) $('progTotalCount').textContent = totalDataCount.toLocaleString();
          if ($('progUploadedCount')) $('progUploadedCount').textContent = '0';
          if ($('progRemainCount')) $('progRemainCount').textContent = workTotal.toLocaleString();
          if ($('progAddedCount')) $('progAddedCount').textContent = '0';
          if ($('progUpdatedCount')) $('progUpdatedCount').textContent = '0';
          if ($('progDupCount')) $('progDupCount').textContent = duplicatesToStage.length.toLocaleString();
          if ($('progBar')) $('progBar').style.width = '0%';
          if ($('progPct')) $('progPct').textContent = '0%';
          if ($('progRowsCount')) $('progRowsCount').textContent = `0 / ${workTotal.toLocaleString()} records`;
          if ($('progFailedCount')) $('progFailedCount').textContent = '0';
          if ($('progAddedOf')) $('progAddedOf').textContent = `of ${validRowsToUpload.length.toLocaleString()}`;
          if ($('progUpdatedOf')) $('progUpdatedOf').textContent = `of ${rowsToUpdate.length.toLocaleString()}`;
          if ($('progTitle')) $('progTitle').textContent = 'Uploading Data to Customers…';
          if ($('progSpinIcon')) { $('progSpinIcon').textContent = '⏳'; $('progSpinIcon').classList.add('spin'); }
          if ($('progBar')) $('progBar').style.background = 'linear-gradient(90deg, #2563eb, #38bdf8)';
          const STEP_STYLE = {
            wait: 'opacity:.55',
            run: 'background:#2563eb;color:#fff;opacity:1',
            done: 'background:var(--ok);color:#fff;opacity:1',
            skip: 'opacity:.4;text-decoration:line-through',
            fail: 'background:var(--danger);color:#fff;opacity:1'
          };
          const setStep = (n, state) => { const el = $('progStep' + n); if (el) el.setAttribute('style', STEP_STYLE[state] || ''); };
          [1, 2, 3, 4].forEach(n => setStep(n, 'wait'));
          let failedNew = 0;
          const setOverall = (done) => {
            const pctAll = workTotal ? Math.min(100, Math.round((done / workTotal) * 100)) : 100;
            if ($('progBar')) $('progBar').style.width = pctAll + '%';
            if ($('progPct')) $('progPct').textContent = pctAll + '%';
            if ($('progRowsCount')) $('progRowsCount').textContent = `${Math.min(done, workTotal).toLocaleString()} / ${workTotal.toLocaleString()} records`;
            if ($('progUploadedCount')) $('progUploadedCount').textContent = Math.min(done, workTotal).toLocaleString();
            updateBstplLoader(`Uploading records to database: ${Math.min(done, workTotal).toLocaleString()} / ${workTotal.toLocaleString()} (${pctAll}%)…`, pctAll);
          };

          // Setup Live New Entries Table: ONLY show new entries while loading!
          const newEntriesTableBox = $('progNewEntriesTable');
          let newEntriesRenderedCount = 0;
          if (newEntriesTableBox) {
            newEntriesTableBox.innerHTML = `
              <table class="data-table" style="font-size:12px;margin:0;width:100%">
                <thead>
                  <tr style="background:var(--card-subtle)">
                    <th style="width:45px">#</th>
                    <th style="width:110px">Status</th>
                    <th>Customer Name</th>
                    <th>IMEI</th>
                    <th>Device Sr No</th>
                    <th>ICCID</th>
                    <th>SIM Type</th>
                    <th>Model</th>
                  </tr>
                </thead>
                <tbody id="progNewTbody"></tbody>
              </table>
            `;
          }
          if ($('progNewEntriesCount')) {
            $('progNewEntriesCount').textContent = `0 / ${validRowsToUpload.length.toLocaleString()} new records`;
          }

          const logBox = $('progLiveDetailBox');
          const addLog = msg => {
            if (!logBox) return;
            const time = new Date().toLocaleTimeString();
            const div = document.createElement('div');
            div.textContent = `[${time}] ${msg}`;
            logBox.appendChild(div);
            logBox.scrollTop = logBox.scrollHeight;
          };
          if (logBox) logBox.innerHTML = '';
          addLog(`Starting upload: ${validRowsToUpload.length.toLocaleString()} new entries to add, ${rowsToUpdate.length.toLocaleString()} existing entries with changed values to update, ${duplicatesToStage.length.toLocaleString()} rows left alone (duplicates / identical to database / invalid).`);

          // Stage duplicate error entries to Errored Entries container
          if (duplicatesToStage.length > 0) {
            addLog(`Staging ${duplicatesToStage.length.toLocaleString()} left-alone records to Errored Entries container…`);
            setStep(1, 'run');
            if ($('progStatus')) $('progStatus').textContent = `Step 1 of 4: saving ${duplicatesToStage.length.toLocaleString()} left-alone rows to Errored Entries…`;
            try {
              await api('/api/errors', {
                method: 'POST',
                body: JSON.stringify({ records: duplicatesToStage })
              });
              addLog(`Duplicate records staged successfully.`);
              setStep(1, 'done');
            } catch (errPost) {
              console.warn('Could not stage duplicate errored records:', errPost);
              addLog(`Notice: Duplicate staging: ${errPost.message}`);
              setStep(1, 'fail');
            }
          } else {
            setStep(1, 'skip');
          }

          const serverSkippedToStage = [];   // rows the server refused as duplicates: kept in Errored Entries, never lost
          let addedTotal = 0, updatedTotal = 0, skippedTotal = duplicateRecordsSkipped;
          const chunkSize = 500;
          showBstplLoader(`Uploading ${workTotal.toLocaleString()} records to database…`, 0);
          try {
            setStep(2, validRowsToUpload.length ? 'run' : 'skip');
            for (let i = 0; i < validRowsToUpload.length; i += chunkSize) {
              const chunk = validRowsToUpload.slice(i, i + chunkSize);
              const chunkNum = Math.floor(i / chunkSize) + 1;
              const totalChunks = Math.ceil(validRowsToUpload.length / chunkSize);
              setOverall(i);
              if ($('progStatus')) $('progStatus').textContent = `Step 2 of 4: adding new records — batch ${chunkNum} of ${totalChunks}…`;

              try {
                const r = await api('/api/devices/bulk', { method: 'POST', body: JSON.stringify({ rows: chunk, mode: mode }) });
                (r.skipped_detail || []).forEach(sk => {
                  const x = chunk[sk.row]; if (!x) return;
                  serverSkippedToStage.push({
                    customer_name: x.customer_name || 'General_Customer', imei: x.imei || '', device_sr_no: x.device_sr_no || '',
                    iccid: x.iccid || '', msisdn1: x.msisdn1 || '', msisdn2: x.msisdn2 || '',
                    act_date: x.act_date || null, expiry_date: x.expiry_date || null, dispatched_date: x.dispatched_date || null,
                    model: x.model || '', sim_provider: x.sim_provider || '', activation_plan: x.activation_plan || '',
                    firmware: x.firmware || '', flash: x.flash || '', sim_type: x.sim_type || '',
                    extra: x.extra || null, error_reason: sk.reason
                  });
                });
                addedTotal += (r.added || 0);
                updatedTotal += (r.updated || 0);
                skippedTotal += (r.skipped_duplicates || 0);

                // Stream ONLY NEW ENTRIES into the live loading display table!
                const newRowsInChunk = (r.added || 0) > 0 ? chunk : [];
                const tbody = $('progNewTbody');
                if (tbody && newRowsInChunk.length > 0) {
                  newRowsInChunk.forEach(r => {
                    newEntriesRenderedCount++;
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                      <td>${newEntriesRenderedCount}</td>
                      <td><span class="badge" style="background:var(--ok);color:#fff;font-weight:700;padding:2px 7px;border-radius:4px">✨ Added New</span></td>
                      <td><b>${esc(r.customer_name || '—')}</b></td>
                      <td><code><b>${esc(r.imei || '—')}</b></code></td>
                      <td><code>${esc(r.device_sr_no || '—')}</code></td>
                      <td><code>${esc(r.iccid || '—')}</code></td>
                      <td><span class="badge" style="background:${r.sim_type === 'E-SIM' ? '#38bdf8' : '#a855f7'};color:#fff">${esc(r.sim_type || '—')}</span></td>
                      <td>${esc(r.model || '—')}</td>
                    `;
                    tbody.appendChild(tr);
                  });
                  if (newEntriesTableBox) {
                    newEntriesTableBox.scrollTop = newEntriesTableBox.scrollHeight;
                  }
                  if ($('progNewEntriesCount')) {
                    $('progNewEntriesCount').textContent = `${newEntriesRenderedCount.toLocaleString()} / ${validRowsToUpload.length.toLocaleString()}`;
                  }
                }

                if (newRowsInChunk.length > 0) {
                  addLog(`✨ Added ${newRowsInChunk.length} new entries to database (e.g. IMEI: ${newRowsInChunk[0].imei})`);
                } else {
                  addLog(`Batch ${chunkNum}/${totalChunks} processed (+${r.updated || 0} updated).`);
                }
              } catch (chunkErr) {
                console.warn('Batch encountered error, falling back to sub-batches:', chunkErr);
                addLog(`⚠️ Batch ${chunkNum} retry with smaller chunks (${chunkErr.message})…`);
                const subSize = 100;
                for (let j = 0; j < chunk.length; j += subSize) {
                  const sub = chunk.slice(j, j + subSize);
                  try {
                    const r = await api('/api/devices/bulk', { method: 'POST', body: JSON.stringify({ rows: sub, mode: mode }) });
                    addedTotal += (r.added || 0);
                    updatedTotal += (r.updated || 0);
                    skippedTotal += (r.skipped_duplicates || 0);

                    const subNew = (r.added || 0) > 0 ? sub : [];
                    const tbody = $('progNewTbody');
                    if (tbody && subNew.length > 0) {
                      subNew.forEach(r => {
                        newEntriesRenderedCount++;
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                          <td>${newEntriesRenderedCount}</td>
                          <td><span class="badge" style="background:var(--ok);color:#fff;font-weight:700;padding:2px 7px;border-radius:4px">✨ Added New</span></td>
                          <td><b>${esc(r.customer_name || '—')}</b></td>
                          <td><code><b>${esc(r.imei || '—')}</b></code></td>
                          <td><code>${esc(r.device_sr_no || '—')}</code></td>
                          <td><code>${esc(r.iccid || '—')}</code></td>
                          <td><span class="badge" style="background:${r.sim_type === 'E-SIM' ? '#38bdf8' : '#a855f7'};color:#fff">${esc(r.sim_type || '—')}</span></td>
                          <td>${esc(r.model || '—')}</td>
                        `;
                        tbody.appendChild(tr);
                      });
                      if (newEntriesTableBox) newEntriesTableBox.scrollTop = newEntriesTableBox.scrollHeight;
                      if ($('progNewEntriesCount')) $('progNewEntriesCount').textContent = `${newEntriesRenderedCount.toLocaleString()} / ${validRowsToUpload.length.toLocaleString()}`;
                    }
                  } catch (subErr) {
                    console.warn('Ignored problematic sub-batch:', subErr);
                    addLog(`Skipped problematic row in sub-batch: ${subErr.message}`);
                    skippedTotal += sub.length;
                    failedNew += sub.length;
                  }
                }
              }

              if ($('progAddedCount')) $('progAddedCount').textContent = addedTotal.toLocaleString();
              if ($('progUpdatedCount')) $('progUpdatedCount').textContent = updatedTotal.toLocaleString();
              if ($('progFailedCount')) $('progFailedCount').textContent = failedNew.toLocaleString();
              setOverall(i + chunk.length);
              await new Promise(r => setTimeout(r, 40));
            }

            if (serverSkippedToStage.length) {
              addLog(`Saving ${serverSkippedToStage.length.toLocaleString()} duplicate rows refused during upload to Errored Entries…`);
              for (let k = 0; k < serverSkippedToStage.length; k += 1000) {
                try { await api('/api/errors', { method: 'POST', body: JSON.stringify({ records: serverSkippedToStage.slice(k, k + 1000) }) }); }
                catch (e2) { addLog(`Notice: could not save some duplicate rows: ${e2.message}`); }
              }
            }

            // Existing records whose values changed: only the changed values are replaced, everything else stays as it was.
            if (validRowsToUpload.length) setStep(2, failedNew ? 'fail' : 'done');
            let updateFailed = 0, updateUnchanged = 0;
            const updateFailedRows = [];
            const UPD_CHUNK = 500;
            setStep(3, rowsToUpdate.length ? 'run' : 'skip');
            for (let i = 0; i < rowsToUpdate.length; i += UPD_CHUNK) {
              const chunk = rowsToUpdate.slice(i, i + UPD_CHUNK);
              setOverall(validRowsToUpload.length + i);
              if ($('progStatus')) $('progStatus').textContent = `Step 3 of 4: updating changed values — ${i.toLocaleString()} of ${rowsToUpdate.length.toLocaleString()} existing records…`;
              let r = null, lastErr = null;
              for (let attempt = 0; attempt < 3 && !r; attempt++) {   // safe to resend: re-applying a change changes nothing
                try { r = await api('/api/devices/bulk/update', { method: 'POST', body: JSON.stringify({ rows: chunk, mode: 'replace' }) }); }
                catch (e) { lastErr = e; await new Promise(res => setTimeout(res, 1000 * (attempt + 1))); }
              }
              if (!r) {
                updateFailed += chunk.length;
                chunk.forEach(x => updateFailedRows.push(Object.assign({}, x, { error_reason: 'Update failed: ' + ((lastErr && lastErr.message) || 'unknown error') })));
                addLog(`❌ Update batch failed: ${(lastErr && lastErr.message) || 'unknown error'}. Existing values were not changed; the rows are kept in Errored Entries.`);
                if ($('progFailedCount')) $('progFailedCount').textContent = (failedNew + updateFailed).toLocaleString();
                setOverall(validRowsToUpload.length + i + chunk.length);
                continue;
              }
              updatedTotal += (r.updated || 0);
              updateUnchanged += (r.unchanged || 0) + (r.skipped || 0);
              updateFailed += (r.failed || 0);
              (r.failed_rows || []).forEach(f => updateFailedRows.push({ imei: f.imei, customer_name: 'General_Customer', error_reason: 'Update failed: ' + f.reason }));
              addLog(`🔄 Updated ${r.updated || 0} existing record(s)${r.unchanged ? `, ${r.unchanged} already identical` : ''}${r.skipped ? `, ${r.skipped} skipped` : ''}${r.failed ? `, ${r.failed} failed` : ''}.`);
              (r.updated_detail || []).slice(0, 5).forEach(u => addLog(`   IMEI ${u.imei}: ` + u.changed.map(c => `${c.field}: ${c.old} → ${c.new}`).join('; ')));
              if (r.mirror_ok === false) addLog('⚠️ Saved to the main table, but not copied to the customer table. Run "python customer_tables.py" on the server to sync.');
              const tbodyU = $('progNewTbody');
              if (tbodyU && (r.updated || 0) > 0) {
                const doneSet = new Set((r.updated_detail || []).map(u => String(u.imei).toLowerCase()));
                chunk.filter(x => doneSet.has(String(x.imei || '').trim().toLowerCase())).slice(-150).forEach(x => {
                  newEntriesRenderedCount++;
                  const tr = document.createElement('tr');
                  tr.innerHTML = `
                    <td>${newEntriesRenderedCount}</td>
                    <td><span class="badge" style="background:#0284c7;color:#fff;font-weight:700;padding:2px 7px;border-radius:4px">🔄 Updated</span></td>
                    <td><b>${esc(x.customer_name || '—')}</b></td>
                    <td><code><b>${esc(x.imei || '—')}</b></code></td>
                    <td><code>${esc(x.device_sr_no || '—')}</code></td>
                    <td><code>${esc(x.iccid || '—')}</code></td>
                    <td><span class="badge" style="background:${x.sim_type === 'E-SIM' ? '#38bdf8' : '#a855f7'};color:#fff">${esc(x.sim_type || '—')}</span></td>
                    <td>${esc(x.model || '—')}</td>`;
                  tbodyU.appendChild(tr);
                });
                if (newEntriesTableBox) newEntriesTableBox.scrollTop = newEntriesTableBox.scrollHeight;
              }
              if ($('progUpdatedCount')) $('progUpdatedCount').textContent = updatedTotal.toLocaleString();
              if ($('progFailedCount')) $('progFailedCount').textContent = (failedNew + updateFailed).toLocaleString();
              setOverall(validRowsToUpload.length + i + chunk.length);
              await new Promise(res => setTimeout(res, 40));
            }
            if (rowsToUpdate.length) setStep(3, updateFailed ? 'fail' : 'done');
            setStep(4, 'run');
            if (updateFailedRows.length) {
              try { await api('/api/errors', { method: 'POST', body: JSON.stringify({ records: updateFailedRows.slice(0, 5000) }) }); }
              catch (e) { addLog(`Notice: could not stage failed update rows: ${e.message}`); }
            }

            if ($('progBar')) $('progBar').style.width = '100%';
            if ($('progPct')) $('progPct').textContent = '100%';
            if ($('progRowsCount')) $('progRowsCount').textContent = `${workTotal.toLocaleString()} / ${workTotal.toLocaleString()} records`;
            if ($('progUploadedCount')) $('progUploadedCount').textContent = workTotal.toLocaleString();
            if ($('progRemainCount')) $('progRemainCount').textContent = '0';
            if ($('progAddedCount')) $('progAddedCount').textContent = addedTotal.toLocaleString();
            if ($('progUpdatedCount')) $('progUpdatedCount').textContent = updatedTotal.toLocaleString();
            const totalFailedAll = failedNew + updateFailed;
            setStep(4, 'done');
            if ($('progFailedCount')) $('progFailedCount').textContent = totalFailedAll.toLocaleString();
            if ($('progTitle')) $('progTitle').textContent = totalFailedAll ? 'Upload Finished With Some Failures' : 'Upload Completed Successfully';
            if ($('progSpinIcon')) { $('progSpinIcon').classList.remove('spin'); $('progSpinIcon').textContent = totalFailedAll ? '⚠️' : '✅'; }
            if ($('progBar') && totalFailedAll) $('progBar').style.background = 'linear-gradient(90deg, #f59e0b, #fbbf24)';
            if ($('progStatus')) $('progStatus').textContent = `Done: ${addedTotal} new added, ${updatedTotal} existing updated, ${duplicatesToStage.length} left as is${totalFailedAll ? `, ${totalFailedAll} failed` : ''}.`;
            addLog(`✅ Upload finished. ${addedTotal} new entries added, ${updatedTotal} existing entries updated${updateFailed ? `, ${updateFailed} update(s) failed` : ''}.`);

            // Compute customer breakdown for complete banner
            const custBreakdown = {};
            validRowsToUpload.concat(rowsToUpdate).forEach(r => {
              const cn = r.customer_name || 'General_Customer';
              custBreakdown[cn] = (custBreakdown[cn] || 0) + 1;
            });

            const breakdownHtml = Object.entries(custBreakdown).map(([cname, cnt]) => {
              const isEx = (CU || []).some(c => (c.name || '').toLowerCase() === cname.toLowerCase());
              return `<li><b>${esc(cname)}</b>: ${cnt.toLocaleString()} records ${isEx ? '(Pushed to existing customer)' : '(New customer created & added)'}</li>`;
            }).join('');

            const totalScannedAll = workTotal + duplicatesToStage.length;
            const distinctCustNames = Object.keys(custBreakdown);
            const existingCustProcessed = distinctCustNames.filter(cn => (CU || []).some(c => (c.name || '').toLowerCase() === cn.toLowerCase())).length;
            const newCustCreated = distinctCustNames.length - existingCustProcessed;
            const duplicateEntriesDetected = duplicatesToStage.length;
            const entriesAdded = addedTotal;
            const entriesUpdated = updatedTotal;
            const entriesSkipped = skippedTotal;
            const entriesFailed = failedNew + updateFailed;
            const finalUploadStatus = entriesFailed === 0 ? 'File Processed Completely (100% Success)' : 'File Processed Partially';

            if ($('progCompleteBanner')) {
              $('progCompleteBanner').hidden = false;
              if ($('progCompleteSummary')) {
                $('progCompleteSummary').innerHTML = `
                  <div style="margin-bottom:12px">
                    <b>Upload Status & Final Processing Summary:</b>
                    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:8px;margin-top:8px">
                      <div>• <b>Total Scanned:</b> ${totalScannedAll.toLocaleString()} entries</div>
                      <div>• <b>Existing Customers:</b> ${existingCustProcessed.toLocaleString()}</div>
                      <div>• <b>New Customers:</b> ${newCustCreated.toLocaleString()}</div>
                      <div>• <b>Left Alone (duplicate / identical / invalid):</b> ${duplicateEntriesDetected.toLocaleString()}</div>
                      <div>• <b>Successfully Added:</b> <span style="color:var(--ok);font-weight:700">${entriesAdded.toLocaleString()}</span></div>
                      <div>• <b>Existing Records Updated (changed values only):</b> <span style="color:#0284c7;font-weight:700">${entriesUpdated.toLocaleString()}</span></div>
                      <div>• <b>Entries Skipped:</b> ${entriesSkipped.toLocaleString()}</div>
                      <div>• <b>Failed Entries:</b> ${entriesFailed.toLocaleString()}</div>
                      <div style="grid-column:1/-1;margin-top:4px">
                        • <b>Final Upload Status:</b> <span class="badge" style="background:${entriesFailed === 0 ? 'var(--ok)' : 'var(--warn)'};color:#fff;font-weight:800;padding:4px 10px;border-radius:6px">${finalUploadStatus}</span>
                      </div>
                    </div>
                  </div>
                  <b>Processed Customers Breakdown:</b>
                  <ul style="margin:6px 0 0;padding-left:20px;font-size:12.5px">${breakdownHtml}</ul>
                `;
              }
            }

            toast(`Upload finished! ${addedTotal} new entries added, ${updatedTotal} existing records updated, ${duplicatesToStage.length} left alone.`);
            showEventPopup({
              type: 'uploading',
              title: 'Bulk File Upload Completed',
              message: `Bulk spreadsheet processed: ${addedTotal} new records added, ${updatedTotal} existing records updated, ${duplicatesToStage.length} rows left alone.`,
              meta: {
                'Total Processed': workTotal + duplicatesToStage.length,
                'New Records Added': addedTotal,
                'Records Updated': updatedTotal,
                'Rows Left Alone': duplicatesToStage.length,
                'Upload Mode': 'Add new + update changed values'
              },
              progress: '100% Complete'
            });

            await loadCU(); await updateChrome();
            loadCustomerFilesContainer();
            fetchInventoryRows();
            if ($('invCustCountBadge')) $('invCustCountBadge').textContent = CU.length;

            if (duplicatesToStage.length > 0) {
              $('dlgUploadErrorsAlertBody').innerHTML = `
          <div style="background:var(--ok-bg);border:1px solid var(--ok);padding:12px;border-radius:8px;margin-bottom:12px">
            <b>${addedTotal}</b> new records were added and <b>${updatedTotal}</b> existing records had their changed values updated.
          </div>
          <p><b>${duplicatesToStage.length}</b> rows (duplicates, identical to the database, or invalid) were left alone and saved into the <b>Errored / Invalid Entries</b> container.</p>
          <p class="sub" style="margin:0">Only values that differed from your file were replaced; every other value of those records stayed as it was.</p>
        `;
              $('dlgUploadErrorsAlert').showModal();
            }

            // stay on this page so the upload status stays visible; "View Records in Inventory Table" jumps to the records
            try { $('uploadProgressWrap').scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (_) {}
          } catch (err) {
            fail(err);
            $('progStatus').textContent = 'Upload error: ' + err.message;
            if ($('progTitle')) $('progTitle').textContent = 'Upload Stopped — Error';
            if ($('progSpinIcon')) { $('progSpinIcon').classList.remove('spin'); $('progSpinIcon').textContent = '❌'; }
            [1, 2, 3, 4].forEach(n => { const el = $('progStep' + n); if (el && /background:#2563eb/.test(el.getAttribute('style') || '')) setStep(n, 'fail'); });
            if ($('btnConfirmUpload')) $('btnConfirmUpload').disabled = false;
          } finally {
            window._bulkUploadBusy = false;
            hideBstplLoader();
          }
        }

        if ($('btnConfirmUpload')) {
          $('btnConfirmUpload').onclick = () => executeBulkUpload();
        }

        syncCustMode();
      }

      /* =========================================================================
         CONTAINER 5: SEPARATE SIM DATA UPLOAD
         ========================================================================= */
      let simRawFileRows = []; // Array of raw row objects from the parsed file
      let simDetectedHeaders = []; // Header strings
      let simActiveCheckResult = null; // Last check result from /api/simdata/check
      let simDebounceTimer = null; // Debounce timer for auto-check (~250ms)
      let currentSimMatchMode = 'iccid'; // 'iccid' | 'imei'
      let simDiffFilterMode = 'all'; // 'all' | 'updated' | 'same'
      let simPostFilterMode = 'all'; // 'all' | 'updated' | 'same'
      let simLastPostUploadResult = null; // Stored results after upload for post-upload filtering/export

      function initSimDataContainer() {
        if ($('simRoleAlert')) $('simRoleAlert').hidden = true;
        if ($('simMainContent')) $('simMainContent').hidden = false;

        const dropzone = $('simDropzone');
        const fileInput = $('simFileInput');

        if (dropzone && fileInput) {
          dropzone.onclick = () => fileInput.click();
          dropzone.ondragover = e => {
            e.preventDefault();
            dropzone.style.borderColor = 'var(--primary)';
            dropzone.style.background = 'var(--card-subtle)';
          };
          dropzone.ondragleave = () => {
            dropzone.style.borderColor = 'var(--line)';
            dropzone.style.background = 'var(--bg)';
          };
          dropzone.ondrop = async e => {
            e.preventDefault();
            dropzone.style.borderColor = 'var(--line)';
            dropzone.style.background = 'var(--bg)';
            const file = e.dataTransfer.files[0];
            if (file) handleSimFileSelected(file);
          };
          fileInput.onchange = e => {
            const file = e.target.files[0];
            if (file) handleSimFileSelected(file);
          };
        }

        if ($('simResetFileBtn')) {
          $('simResetFileBtn').onclick = () => {
            simRawFileRows = [];
            simDetectedHeaders = [];
            simActiveCheckResult = null;
            simLastPostUploadResult = null;
            if ($('simConfigCard')) $('simConfigCard').hidden = true;
            if ($('simCheckResults')) $('simCheckResults').hidden = true;
            if ($('simPostUploadResults')) $('simPostUploadResults').hidden = true;
            if ($('simDropzone')) $('simDropzone').hidden = false;
            if ($('simFileInput')) $('simFileInput').value = '';
          };
        }

        // Trigger auto-check whenever user changes options or mappings
        ['colMapKey', 'colMapActDate', 'colMapExpDate', 'colMapMsisdn1', 'colMapMsisdn2', 'colMapSimProvider', 'simProviderSelect'].forEach(id => {
          const el = $(id);
          if (el) el.onchange = () => scheduleSimAutoCheck();
        });
        if ($('simOverwriteChk')) {
          $('simOverwriteChk').onchange = () => scheduleSimAutoCheck();
        }

        // Compare & Validate Records Button (Step 2)
        if ($('btnRunSimCompare')) {
          $('btnRunSimCompare').onclick = () => runSimAutoCheck(true);
        }

        // Comparison Filter Pills (Before Upload)
        if ($('btnDiffFilterAll')) {
          $('btnDiffFilterAll').onclick = () => setSimDiffFilter('all');
        }
        if ($('btnDiffFilterUpd')) {
          $('btnDiffFilterUpd').onclick = () => setSimDiffFilter('updated');
        }
        if ($('btnDiffFilterSame')) {
          $('btnDiffFilterSame').onclick = () => setSimDiffFilter('same');
        }

        // Step 2 Before-Upload Sub-tab Switcher
        const switchSimCompTab = (tab) => {
          ['tabSimCompMatched', 'tabSimCompNotFound', 'tabSimCompBreakdown'].forEach(id => {
            if ($(id)) $(id).classList.toggle('on', id === tab);
          });
          if ($('viewSimCompMatched')) $('viewSimCompMatched').hidden = (tab !== 'tabSimCompMatched');
          if ($('viewSimCompNotFound')) $('viewSimCompNotFound').hidden = (tab !== 'tabSimCompNotFound');
          if ($('viewSimCompBreakdown')) $('viewSimCompBreakdown').hidden = (tab !== 'tabSimCompBreakdown');
        };
        if ($('tabSimCompMatched')) $('tabSimCompMatched').onclick = () => switchSimCompTab('tabSimCompMatched');
        if ($('tabSimCompNotFound')) $('tabSimCompNotFound').onclick = () => switchSimCompTab('tabSimCompNotFound');
        if ($('tabSimCompBreakdown')) $('tabSimCompBreakdown').onclick = () => switchSimCompTab('tabSimCompBreakdown');

        // Step 3 Post-Upload Sub-tab Switcher
        const switchPostUploadTab = (tab) => {
          ['tabPostDiffUpdated', 'tabPostDiffNotFound', 'tabPostDiffBefore'].forEach(id => {
            if ($(id)) $(id).classList.toggle('on', id === tab);
          });
          if ($('viewPostDiffUpdated')) $('viewPostDiffUpdated').hidden = (tab !== 'tabPostDiffUpdated');
          if ($('viewPostDiffNotFound')) $('viewPostDiffNotFound').hidden = (tab !== 'tabPostDiffNotFound');
          if ($('viewPostDiffBefore')) $('viewPostDiffBefore').hidden = (tab !== 'tabPostDiffBefore');
          if ($('postDiffFilterGroup')) $('postDiffFilterGroup').style.display = (tab === 'tabPostDiffUpdated') ? 'flex' : 'none';
        };
        if ($('tabPostDiffUpdated')) $('tabPostDiffUpdated').onclick = () => switchPostUploadTab('tabPostDiffUpdated');
        if ($('tabPostDiffNotFound')) $('tabPostDiffNotFound').onclick = () => switchPostUploadTab('tabPostDiffNotFound');
        if ($('tabPostDiffBefore')) $('tabPostDiffBefore').onclick = () => switchPostUploadTab('tabPostDiffBefore');

        // Post-Upload Filter Pills
        if ($('btnPostFilterAll')) {
          $('btnPostFilterAll').onclick = () => setSimPostFilter('all');
        }
        if ($('btnPostFilterUpd')) {
          $('btnPostFilterUpd').onclick = () => setSimPostFilter('updated');
        }
        if ($('btnPostFilterSame')) {
          $('btnPostFilterSame').onclick = () => setSimPostFilter('same');
        }

        // Action Execution button
        if ($('btnExecuteSelectedAction')) {
          $('btnExecuteSelectedAction').onclick = () => executeSimPush();
        }

        // Download Not Found buttons
        const downloadNotFoundExcel = () => {
          if (!simActiveCheckResult || !simActiveCheckResult.not_found_records || !simActiveCheckResult.not_found_records.length) {
            toast('No unmatched / not-found entries to download.');
            return;
          }
          const headers = ['ICCID / CCID', 'MSISDN 1', 'MSISDN 2', 'Activation Date', 'Expiry Date', 'SIM Provider', 'Status'];
          const rows = simActiveCheckResult.not_found_records.map(r => [
            r.iccid, r.msisdn1 || '', r.msisdn2 || '', r.act_date || '', r.expiry_date || '', r.sim_provider || '', r.status || 'Not Found in Any Customer (Will NOT be uploaded)'
          ]);
          exportExcel('Not_Found_ICCIDs_SIM_Upload', headers, rows);
        };
        if ($('btnSimDlNotFound')) $('btnSimDlNotFound').onclick = downloadNotFoundExcel;
        if ($('btnDlNotFoundView')) $('btnDlNotFoundView').onclick = downloadNotFoundExcel;

        // Download Before-Change Excel Preview (Step 2)
        if ($('btnSimDlPreUploadExcel')) {
          $('btnSimDlPreUploadExcel').onclick = () => {
            if (!simActiveCheckResult || !simActiveCheckResult.detailed_comparison || !simActiveCheckResult.detailed_comparison.length) {
              toast('No comparison preview data available to export.');
              return;
            }
            exportSimPreUploadReportExcel(simActiveCheckResult);
          };
        }

        // Download Before-Change Excel (Step 3)
        if ($('btnDownloadPreUploadReport')) {
          $('btnDownloadPreUploadReport').onclick = () => {
            const dataToExport = simActiveCheckResult || (simLastPostUploadResult ? {
              detailed_comparison: simLastPostUploadResult.before_comparison,
              not_found_records: simLastPostUploadResult.not_found_records
            } : null);
            if (!dataToExport || !dataToExport.detailed_comparison || !dataToExport.detailed_comparison.length) {
              toast('No before-change data available to export.');
              return;
            }
            exportSimPreUploadReportExcel(dataToExport);
          };
        }

        // Download Both Reports (Combined Excel - Step 3)
        if ($('btnDownloadBothReports')) {
          $('btnDownloadBothReports').onclick = () => {
            if (!simLastPostUploadResult) {
              toast('No post-upload data available.');
              return;
            }
            exportSimBothReportsExcel(simLastPostUploadResult, simActiveCheckResult);
          };
        }

        // Copy Not Found ICCIDs button
        if ($('btnCopyNotFoundIccids')) {
          $('btnCopyNotFoundIccids').onclick = () => {
            const list = simActiveCheckResult && simActiveCheckResult.not_found_keys ? simActiveCheckResult.not_found_keys : [];
            if (!list.length) {
              toast('No not-found ICCIDs to copy.');
              return;
            }
            const text = list.join('\n');
            if (navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(text).then(() => {
                toast(`Copied ${list.length.toLocaleString()} not-found ICCIDs to clipboard.`);
              }).catch(() => {
                cv.copyBox(text, { title: 'Not-found ICCIDs', sub: 'Copy the list below.' });
              });
            } else {
              cv.copyBox(text, { title: 'Not-found ICCIDs', sub: 'Copy the list below.' });
            }
          };
        }

        // Download Post-Upload Comparison Report (Excel)
        if ($('btnDownloadPostUploadReport')) {
          $('btnDownloadPostUploadReport').onclick = () => {
            if (!simLastPostUploadResult) {
              toast('No post-upload data available.');
              return;
            }
            exportSimPostUploadReportExcel(simLastPostUploadResult);
          };
        }

        // Upload Another File button
        if ($('btnSimUploadAnother')) {
          $('btnSimUploadAnother').onclick = () => {
            if ($('simResetFileBtn')) $('simResetFileBtn').click();
            if ($('simPostUploadResults')) $('simPostUploadResults').hidden = true;
            if ($('simDropzone')) $('simDropzone').scrollIntoView({ behavior: 'smooth' });
          };
        }
      }

      function setSimMatchMode(mode) {
        currentSimMatchMode = 'iccid';

        if ($('simMatchModeBadge')) {
          $('simMatchModeBadge').textContent = 'Matching by ICCID';
        }
        if ($('titleColMapKey')) {
          $('titleColMapKey').textContent = '💳 ICCID / CCID Column * (Required - Both are Same)';
        }
        if ($('simModeDesc')) {
          $('simModeDesc').textContent = 'Matches device records across our database strictly by ICCID / CCID (both are identical) and updates selected columns.';
        }

        if (simDetectedHeaders.length) {
          populateSimColumnDropdowns(simDetectedHeaders);
          scheduleSimAutoCheck(50);
        }
      }

      function setSimDiffFilter(filter) {
        simDiffFilterMode = filter;
        if ($('btnDiffFilterAll')) $('btnDiffFilterAll').classList.toggle('on', filter === 'all');
        if ($('btnDiffFilterUpd')) $('btnDiffFilterUpd').classList.toggle('on', filter === 'updated');
        if ($('btnDiffFilterSame')) $('btnDiffFilterSame').classList.toggle('on', filter === 'same');

        if (simActiveCheckResult && simActiveCheckResult.detailed_comparison) {
          renderSimComparisonTable(simActiveCheckResult.detailed_comparison, simDiffFilterMode);
        }
      }

      function setSimPostFilter(filter) {
        simPostFilterMode = filter;
        if ($('btnPostFilterAll')) $('btnPostFilterAll').classList.toggle('on', filter === 'all');
        if ($('btnPostFilterUpd')) $('btnPostFilterUpd').classList.toggle('on', filter === 'updated');
        if ($('btnPostFilterSame')) $('btnPostFilterSame').classList.toggle('on', filter === 'same');

        if (simLastPostUploadResult && simLastPostUploadResult.applied_comparison) {
          renderSimPostComparisonTable(simLastPostUploadResult.applied_comparison, simPostFilterMode);
        }
      }

      async function handleSimFileSelected(file) {
        if (!file.name.match(/\.(xlsx|xls|csv)$/i)) {
          toast('⚠️ Please select an Excel (.xlsx, .xls) or CSV (.csv) file.');
          return;
        }

        const uploadWrap = $('simUploadProgressWrap');
        const uploadBar = $('simUploadProgressBar');
        const uploadPct = $('simUploadProgressPct');
        const uploadTitle = $('simUploadProgressTitle');
        const uploadDetail = $('simUploadProgressDetail');
        const uploadRows = $('simUploadProgressRows');

        if (uploadWrap) {
          uploadWrap.hidden = false;
          if (uploadBar) uploadBar.style.width = '15%';
          if (uploadPct) uploadPct.textContent = '15%';
          if (uploadTitle) uploadTitle.textContent = 'Step 1: Uploading & Reading SIM File…';
          if (uploadDetail) uploadDetail.textContent = `Reading "${file.name}" (${Math.round(file.size / 1024)} KB) into memory…`;
          if (uploadRows) uploadRows.textContent = 'Reading bytes…';
        }
        if ($('simDropzone')) $('simDropzone').hidden = true;
        if ($('simConfigCard')) $('simConfigCard').hidden = true;
        if ($('simCheckResults')) $('simCheckResults').hidden = true;
        simActiveCheckResult = null;

        try {
          await new Promise(r => setTimeout(r, 120));

          let sheetData = [];
          if (file.name.match(/\.csv$/i)) {
            if (uploadBar) uploadBar.style.width = '35%';
            if (uploadPct) uploadPct.textContent = '35%';
            if (uploadDetail) uploadDetail.textContent = 'Parsing CSV rows…';
            const text = await file.text();
            sheetData = parseCSV(text);
          } else {
            if (uploadBar) uploadBar.style.width = '35%';
            if (uploadPct) uploadPct.textContent = '35%';
            if (uploadDetail) uploadDetail.textContent = 'Parsing Excel spreadsheet sheets…';
            const buf = await file.arrayBuffer();
            const wb = XLSX.read(new Uint8Array(buf), { type: 'array', cellDates: false });
            let chosenSheet = null;
            for (const sname of wb.SheetNames) {
              const ws = wb.Sheets[sname];
              const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '', raw: false });
              if (rows && rows.length >= 2) {
                chosenSheet = rows;
                break;
              }
            }
            if (!chosenSheet) {
              toast('⚠️ No non-empty sheets found in this workbook.');
              if (uploadWrap) uploadWrap.hidden = true;
              if ($('simDropzone')) $('simDropzone').hidden = false;
              return;
            }
            sheetData = chosenSheet;
          }

          if (uploadBar) uploadBar.style.width = '60%';
          if (uploadPct) uploadPct.textContent = '60%';
          if (uploadDetail) uploadDetail.textContent = `Analyzing ${sheetData.length.toLocaleString()} rows for header columns…`;

          function isSimIdHeaderCandidate(str) {
            if (!str) return false;
            const c = String(str).trim().toLowerCase().replace(/[^a-z0-9]/g, '');
            if (!c) return false;
            if (c.includes('iccid') || c.includes('ccid')) return true;
            if (c.includes('imei')) return true;
            if (c.startsWith('sim') && (c.includes('no') || c.includes('num') || c.includes('card') || c === 'sim' || c === 'simid')) return true;
            if (c.includes('msisdn') || c.includes('mobileno') || c.includes('phoneno') || c.includes('mobile')) return true;
            if (c.includes('actdate') || c.includes('activation') || c.includes('expdate') || c.includes('expiry') || c.includes('validity')) return true;
            return false;
          }

          let headerRowIdx = -1;
          const maxSearch = Math.min(25, sheetData.length);

          for (let r = 0; r < maxSearch; r++) {
            const row = sheetData[r] || [];
            const hasIdHeader = row.some(cell => isSimIdHeaderCandidate(cell));
            if (hasIdHeader) {
              headerRowIdx = r;
              break;
            }
          }

          if (headerRowIdx === -1) {
            for (let r = 0; r < maxSearch; r++) {
              const filled = (sheetData[r] || []).filter(c => String(c || '').trim() !== '').length;
              if (filled >= 2) {
                headerRowIdx = r;
                break;
              }
            }
          }

          if (headerRowIdx === -1) {
            toast('⚠️ Could not find a valid header row in the file.');
            if (uploadWrap) uploadWrap.hidden = true;
            if ($('simDropzone')) $('simDropzone').hidden = false;
            return;
          }

          const rawHeaderRow = (sheetData[headerRowIdx] || []).map(h => String(h || '').trim());
          const validHeaders = rawHeaderRow.filter((h, idx) => h || idx < 30);
          
          if (uploadBar) uploadBar.style.width = '80%';
          if (uploadPct) uploadPct.textContent = '80%';
          if (uploadDetail) uploadDetail.textContent = 'Arranging headers according to database schema (ICCID/CCID, MSISDN, Dates)…';

          // Arrange headers according to our standard database schema order regardless of CAPITAL or small letters!
          simDetectedHeaders = classifyAndArrangeHeaders(validHeaders);
          const rawRows = sheetData.slice(headerRowIdx + 1);

          simRawFileRows = [];
          rawRows.forEach(rowArr => {
            if (!rowArr || !rowArr.some(c => String(c || '').trim() !== '')) return;
            const obj = {};
            validHeaders.forEach((h, idx) => {
              const val = rowArr[idx] != null ? String(rowArr[idx]).trim() : '';
              obj[h || `Column_${idx + 1}`] = val;
            });
            simRawFileRows.push(obj);
          });

          if (!simRawFileRows.length) {
            toast('⚠️ The file contains no data rows after the header row.');
            if (uploadWrap) uploadWrap.hidden = true;
            if ($('simDropzone')) $('simDropzone').hidden = false;
            return;
          }

          if (uploadBar) uploadBar.style.width = '100%';
          if (uploadPct) uploadPct.textContent = '100%';
          if (uploadTitle) uploadTitle.textContent = '✅ File Upload & Reading Complete (100%)';
          if (uploadDetail) uploadDetail.textContent = `Loaded ${simRawFileRows.length.toLocaleString()} rows and ${simDetectedHeaders.length} columns. Ready for Step 2 Validation.`;
          if (uploadRows) uploadRows.textContent = `${simRawFileRows.length.toLocaleString()} rows parsed`;

          await new Promise(r => setTimeout(r, 200));

          // Strictly match by ICCID for SIM data upload (handles CCID identically)
          setSimMatchMode('iccid');

          populateSimColumnDropdowns(simDetectedHeaders);

          $('simFileName').textContent = file.name;
          $('simFileSize').textContent = Math.round(file.size / 1024) + ' KB';
          $('simTotalRowsBadge').textContent = simRawFileRows.length.toLocaleString() + ' rows';

          if (uploadWrap) uploadWrap.hidden = true;
          $('simDropzone').hidden = true;
          $('simConfigCard').hidden = false;

          showEventPopup({
            type: 'uploading',
            title: 'SIM File Uploaded (Step 1)',
            message: `Uploaded and parsed ${simRawFileRows.length.toLocaleString()} rows and ${simDetectedHeaders.length} columns from "${file.name}". Please review column mappings below and click "Validate Rows against Database".`,
            meta: {
              'File Name': file.name,
              'Total Rows': simRawFileRows.length,
              'Columns Detected': simDetectedHeaders.length,
              'ICCID / CCID Column': 'Identified & Matched'
            },
            progress: '100% Uploaded'
          });

          // Wait for user to validate rows in Step 2; do not auto-check
        } catch (err) {
          if (uploadWrap) uploadWrap.hidden = true;
          if ($('simDropzone')) $('simDropzone').hidden = false;
          fail(err);
        }
      }

      function matchColumnToField(header, fieldKey) {
        if (!header) return false;
        const clean = String(header).toLowerCase().replace(/[^a-z0-9]/g, '');
        if (!clean) return false;

        if (fieldKey === 'key') {
          // ICCID / CCID / SIM NO
          if (clean.includes('iccid') || clean.includes('ccid')) return true;
          if (clean.startsWith('sim') && (clean.includes('no') || clean.includes('num') || clean.includes('card') || clean === 'sim' || clean === 'simid')) return true;
          if (clean === 'cardno' || clean === 'cardnumber' || clean === 'simcardno') return true;
          return false;
        }
        if (fieldKey === 'act_date') {
          if (clean.includes('act') || clean.includes('activat')) {
            if (clean.includes('date') || clean.includes('dt') || clean.includes('on') || clean.includes('time') || clean === 'actdate' || clean === 'activationdate' || clean === 'activated') return true;
          }
          return false;
        }
        if (fieldKey === 'exp_date') {
          if (clean.includes('exp') || clean.includes('valid')) {
            if (clean.includes('date') || clean.includes('dt') || clean.includes('on') || clean.includes('till') || clean.includes('upto') || clean === 'expdate' || clean === 'expirydate' || clean === 'validity' || clean === 'validupto') return true;
          }
          return false;
        }
        if (fieldKey === 'msisdn1') {
          if (clean.includes('msisdn1') || clean.includes('mobile1') || clean.includes('phone1') || clean.includes('sim1')) return true;
          if (clean.includes('primary') && (clean.includes('mobile') || clean.includes('phone') || clean.includes('number') || clean.includes('no') || clean.includes('msisdn'))) return true;
          if (clean === 'msisdn' || clean === 'mobile' || clean === 'mobileno' || clean === 'mobilenumber' || clean === 'phone' || clean === 'phoneno') return true;
          return false;
        }
        if (fieldKey === 'msisdn2') {
          if (clean.includes('msisdn2') || clean.includes('mobile2') || clean.includes('phone2') || clean.includes('sim2')) return true;
          if (clean.includes('secondary') && (clean.includes('mobile') || clean.includes('phone') || clean.includes('number') || clean.includes('no') || clean.includes('msisdn'))) return true;
          return false;
        }
        if (fieldKey === 'sim_provider') {
          if (clean.includes('provider') || clean.includes('operator') || clean.includes('carrier') || clean.includes('telecom') || clean === 'simprovider') return true;
          return false;
        }
        return false;
      }

      function classifyAndArrangeHeaders(headers) {
        if (!headers || !headers.length) return [];

        // Schema order: 1. ICCID/CCID, 2. MSISDN 1, 3. MSISDN 2, 4. Act Date, 5. Exp Date, 6. SIM Provider, 7. Other standard cols, 8. Extras
        const schemaPriorities = [
          { key: 'key', test: h => matchColumnToField(h, 'key') },
          { key: 'msisdn1', test: h => matchColumnToField(h, 'msisdn1') },
          { key: 'msisdn2', test: h => matchColumnToField(h, 'msisdn2') },
          { key: 'act_date', test: h => matchColumnToField(h, 'act_date') },
          { key: 'exp_date', test: h => matchColumnToField(h, 'exp_date') },
          { key: 'sim_provider', test: h => matchColumnToField(h, 'sim_provider') },
          { key: 'imei', test: h => String(h).toLowerCase().replace(/[^a-z0-9]/g, '').includes('imei') },
          { key: 'device_sr_no', test: h => { const c = String(h).toLowerCase().replace(/[^a-z0-9]/g, ''); return c.includes('srno') || c.includes('serial') || c.includes('devicesr'); } },
          { key: 'model', test: h => String(h).toLowerCase().replace(/[^a-z0-9]/g, '').includes('model') },
          { key: 'firmware', test: h => String(h).toLowerCase().replace(/[^a-z0-9]/g, '').includes('firmware') },
          { key: 'flash', test: h => String(h).toLowerCase().replace(/[^a-z0-9]/g, '').includes('flash') },
          { key: 'plan', test: h => String(h).toLowerCase().replace(/[^a-z0-9]/g, '').includes('plan') },
          { key: 'sim_type', test: h => { const c = String(h).toLowerCase().replace(/[^a-z0-9]/g, ''); return c.includes('simtype') || c === 'type'; } }
        ];

        const matched = new Set();
        const arranged = [];

        schemaPriorities.forEach(p => {
          for (const h of headers) {
            if (!matched.has(h) && p.test(h)) {
              arranged.push(h);
              matched.add(h);
              break;
            }
          }
        });

        headers.forEach(h => {
          if (!matched.has(h)) {
            arranged.push(h);
            matched.add(h);
          }
        });

        return arranged;
      }

      function populateSimColumnDropdowns(headers) {
        const fields = [
          { id: 'colMapKey', fieldKey: 'key', required: true },
          { id: 'colMapActDate', fieldKey: 'act_date' },
          { id: 'colMapExpDate', fieldKey: 'exp_date' },
          { id: 'colMapMsisdn1', fieldKey: 'msisdn1' },
          { id: 'colMapMsisdn2', fieldKey: 'msisdn2' },
          { id: 'colMapSimProvider', fieldKey: 'sim_provider' }
        ];

        fields.forEach(f => {
          const sel = $(f.id);
          if (!sel) return;
          sel.innerHTML = `<option value="">-- None (Do not update) --</option>` + headers.map(h => `<option value="${esc(h)}">${esc(h)}</option>`).join('');

          let matchedCol = '';
          for (const h of headers) {
            if (matchColumnToField(h, f.fieldKey)) {
              matchedCol = h;
              break;
            }
          }

          if (matchedCol) sel.value = matchedCol;
          else sel.value = '';
        });
      }

      function scheduleSimAutoCheck(delayMs = 250) {
        clearTimeout(simDebounceTimer);
        simDebounceTimer = setTimeout(() => {
          runSimAutoCheck();
        }, delayMs);
      }

      function parseDateCell(val) {
        return convertDateToStandardFormat(val);
      }

      async function runSimAutoCheck(isManual = false) {
        if (!simRawFileRows.length) {
          if (isManual) toast('⚠️ Please select or upload a SIM file first in Step 1.');
          return;
        }

        const keyLabel = 'ICCID / CCID';
        const keyCol = $('colMapKey') ? $('colMapKey').value : '';
        const msisdn1Col = $('colMapMsisdn1') ? $('colMapMsisdn1').value : '';
        const msisdn2Col = $('colMapMsisdn2') ? $('colMapMsisdn2').value : '';
        const actDateCol = $('colMapActDate') ? $('colMapActDate').value : '';
        const expDateCol = $('colMapExpDate') ? $('colMapExpDate').value : '';
        const providerCol = $('colMapSimProvider') ? $('colMapSimProvider').value : '';
        const chosenProvider = $('simProviderSelect') ? $('simProviderSelect').value : '';
        const overwrite = $('simOverwriteChk') ? $('simOverwriteChk').checked : true;

        if (!keyCol) {
          if ($('simCheckProgressWrap')) $('simCheckProgressWrap').hidden = true;
          $('simCheckResults').hidden = false;
          $('kpiSimFileRows').textContent = simRawFileRows.length.toLocaleString();
          $('simNotesBox').hidden = false;
          $('simNotesBox').innerHTML = '⚠️ <b>ICCID / CCID Column Required:</b> Please select which column in your file represents the ICCID / CCID in the dropdown above.';
          $('simPushMsg').textContent = 'Please select the ICCID / CCID column to continue.';
          return;
        }

        const compareBtn = $('btnRunSimCompare');
        const compareIcon = $('btnRunSimCompareIcon');
        const compareText = $('btnRunSimCompareText');

        if (compareBtn) {
          compareBtn.disabled = true;
          if (compareIcon) compareIcon.textContent = '⏳';
          if (compareText) compareText.textContent = 'Comparing & Checking Records…';
        }

        const progressWrap = $('simCheckProgressWrap');
        const progressBar = $('simCheckProgressBar');
        const progressPct = $('simCheckProgressPct');
        const progressTitle = $('simCheckProgressTitle');
        const progressDetail = $('simCheckProgressDetail');
        const progressCounts = $('simCheckProgressCounts');

        if (progressWrap) {
          progressWrap.hidden = false;
          if (progressBar) progressBar.style.width = '10%';
          if (progressPct) progressPct.textContent = '10%';
          if (progressTitle) progressTitle.textContent = 'Step 2: Checking & Comparing Records against Database…';
          if (progressDetail) progressDetail.textContent = 'Reading and normalizing file rows & date formats…';
          if (progressCounts) progressCounts.textContent = `0 / ${simRawFileRows.length.toLocaleString()} rows`;
        }

        const payloadRows = [];
        let unreadableDatesCount = 0;
        let convertedDatesCount = 0;

        simRawFileRows.forEach(rawObj => {
          let rawKey = rawObj[keyCol] != null ? String(rawObj[keyCol]).trim() : '';
          if (rawKey.endsWith('.0') && /^\d+\.0$/.test(rawKey)) rawKey = rawKey.slice(0, -2);
          if (/[eE]\+?/.test(rawKey)) {
            try {
              const num = Number(rawKey);
              if (!isNaN(num) && Number.isFinite(num)) rawKey = BigInt(Math.round(num)).toString();
            } catch { }
          }
          rawKey = rawKey.replace(/[\s\-_]+/g, '').toUpperCase();

          const m1 = msisdn1Col ? (rawObj[msisdn1Col] || '').trim() : '';
          const m2 = msisdn2Col ? (rawObj[msisdn2Col] || '').trim() : '';
          const rawAct = actDateCol ? rawObj[actDateCol] : '';
          const rawExp = expDateCol ? rawObj[expDateCol] : '';
          const rowProv = providerCol ? (rawObj[providerCol] || '').trim() : '';

          const hasAct = !isBlankDateCell(rawAct);
          const hasExp = !isBlankDateCell(rawExp);

          const actParsed = hasAct ? convertDateToStandardFormat(rawAct) : null;
          const expParsed = hasExp ? convertDateToStandardFormat(rawExp) : null;

          if (hasAct) {
            if (actParsed) convertedDatesCount++;
            else unreadableDatesCount++;
          }
          if (hasExp) {
            if (expParsed) convertedDatesCount++;
            else unreadableDatesCount++;
          }

          payloadRows.push({
            iccid: rawKey,
            msisdn1: m1 || null,
            msisdn2: m2 || null,
            act_date: actParsed || null,
            expiry_date: expParsed || null,
            sim_provider: rowProv || chosenProvider || null
          });
        });

        if (progressBar) progressBar.style.width = '25%';
        if (progressPct) progressPct.textContent = '25%';
        if (progressDetail) progressDetail.textContent = 'Querying database to validate ICCID/CCID keys against customer records…';

        try {
          let aggregatedRes = null;
          const chunkSize = 1500;

          if (payloadRows.length > chunkSize) {
            let totalMatched = 0, totalToUpdate = 0, totalAlreadySame = 0, totalSkipped = 0, totalRepeated = 0;
            const notFoundSet = new Set();
            const allDetailed = [];
            const allNotFoundRecords = [];
            const custBreakdownMap = {};

            for (let i = 0; i < payloadRows.length; i += chunkSize) {
              const chunk = payloadRows.slice(i, i + chunkSize);
              const pct = Math.min(94, Math.round(25 + ((i + chunk.length) / payloadRows.length) * 70));
              if (progressBar) progressBar.style.width = pct + '%';
              if (progressPct) progressPct.textContent = pct + '%';
              if (progressDetail) progressDetail.textContent = `Comparing rows ${i + 1} to ${Math.min(i + chunkSize, payloadRows.length)} of ${payloadRows.length.toLocaleString()} against customer database (${pct}% complete)…`;
              if (progressCounts) progressCounts.textContent = `${Math.min(i + chunkSize, payloadRows.length).toLocaleString()} / ${payloadRows.length.toLocaleString()} rows`;

              const chunkRes = await api('/api/simdata/check', {
                method: 'POST',
                body: JSON.stringify({
                  rows: chunk,
                  overwrite: overwrite,
                  match_by: currentSimMatchMode,
                  sim_provider: chosenProvider || null
                })
              });

              totalMatched += (chunkRes.records_matched || 0);
              totalToUpdate += (chunkRes.records_to_update || 0);
              totalAlreadySame += (chunkRes.records_already_same || 0);
              totalSkipped += (chunkRes.skipped_rows || 0);
              totalRepeated += (chunkRes.repeated_keys_count || 0);

              (chunkRes.not_found_keys || []).forEach(k => notFoundSet.add(k));
              if (chunkRes.not_found_records) allNotFoundRecords.push(...chunkRes.not_found_records);
              if (chunkRes.detailed_comparison) allDetailed.push(...chunkRes.detailed_comparison);

              (chunkRes.customer_breakdown || []).forEach(cb => {
                if (!custBreakdownMap[cb.customer_id]) {
                  custBreakdownMap[cb.customer_id] = { ...cb };
                } else {
                  const target = custBreakdownMap[cb.customer_id];
                  target.matched_count += cb.matched_count;
                  target.to_update_count += cb.to_update_count;
                  target.already_same_count += cb.already_same_count;
                  target.msisdn1_changes += cb.msisdn1_changes || 0;
                  target.msisdn2_changes += cb.msisdn2_changes || 0;
                  target.act_date_changes += cb.act_date_changes || 0;
                  target.expiry_date_changes += cb.expiry_date_changes || 0;
                  target.sim_provider_changes += cb.sim_provider_changes || 0;
                }
              });
            }

            aggregatedRes = {
              file_rows_count: payloadRows.length,
              match_by: currentSimMatchMode,
              records_matched: totalMatched,
              records_to_update: totalToUpdate,
              records_already_same: totalAlreadySame,
              skipped_rows: totalSkipped,
              repeated_keys_count: totalRepeated,
              not_found_keys_count: notFoundSet.size,
              not_found_keys: Array.from(notFoundSet),
              not_found_records: allNotFoundRecords,
              customer_breakdown: Object.values(custBreakdownMap),
              detailed_comparison: allDetailed
            };
          } else {
            if (progressBar) progressBar.style.width = '50%';
            if (progressPct) progressPct.textContent = '50%';
            if (progressDetail) progressDetail.textContent = `Comparing ${payloadRows.length.toLocaleString()} records against database…`;

            aggregatedRes = await api('/api/simdata/check', {
              method: 'POST',
              body: JSON.stringify({
                rows: payloadRows,
                overwrite: overwrite,
                match_by: currentSimMatchMode,
                sim_provider: chosenProvider || null
              })
            });
          }

          const res = aggregatedRes;
          simActiveCheckResult = res;

          const notFoundCount = (res.not_found_keys_count != null ? res.not_found_keys_count : (res.not_found_keys ? res.not_found_keys.length : 0));

          if (progressBar) progressBar.style.width = '100%';
          if (progressPct) progressPct.textContent = '100%';
          if (progressTitle) progressTitle.textContent = '✅ Step 2 Complete: Checked & Compared Against Database (100%)';
          if (progressDetail) progressDetail.textContent = `Comparison complete: ${res.records_matched.toLocaleString()} found in customers (${res.records_to_update.toLocaleString()} differing to replace, ${res.records_already_same.toLocaleString()} already identical). ${notFoundCount.toLocaleString()} ICCIDs not found (will NOT be uploaded).`;
          if (progressCounts) progressCounts.textContent = `${res.file_rows_count.toLocaleString()} / ${res.file_rows_count.toLocaleString()} rows checked (100%)`;

          $('kpiSimFileRows').textContent = res.file_rows_count.toLocaleString();
          if ($('kpiSimDuplicates')) $('kpiSimDuplicates').textContent = (res.repeated_keys_count || 0).toLocaleString();
          $('kpiSimMatched').textContent = res.records_matched.toLocaleString();
          $('kpiSimToUpdate').textContent = res.records_to_update.toLocaleString();
          $('kpiSimAlreadySame').textContent = res.records_already_same.toLocaleString();
          if ($('kpiSimNotFound')) $('kpiSimNotFound').textContent = notFoundCount.toLocaleString();
          if ($('kpiSimCanInsert')) $('kpiSimCanInsert').textContent = notFoundCount.toLocaleString();

          // Button and message updates
          if ($('btnExecuteSelectedActionText')) {
            $('btnExecuteSelectedActionText').textContent = `Upload & Update SIM Data (${res.records_matched.toLocaleString()} Matched Records)`;
          }
          if ($('btnExecuteSelectedAction')) {
            $('btnExecuteSelectedAction').disabled = (res.records_matched === 0);
          }

          if ($('cntCompMatchedTab')) $('cntCompMatchedTab').textContent = res.records_matched.toLocaleString();
          if ($('cntCompNotFoundTab')) $('cntCompNotFoundTab').textContent = notFoundCount.toLocaleString();
          if ($('cntNotFoundBanner')) $('cntNotFoundBanner').textContent = notFoundCount.toLocaleString();

          const notes = [];
          if (res.skipped_rows > 0) {
            notes.push(`• <b>${res.skipped_rows} rows skipped:</b> ${keyLabel} was missing or too short.`);
          }
          if (res.repeated_keys_count > 0) {
            notes.push(`• <b>${res.repeated_keys_count} duplicate ${keyLabel}s in file:</b> earlier rows were preserved; duplicates will not be processed twice.`);
          }
          if (notFoundCount > 0) {
            notes.push(`• ⚠️ <b>${notFoundCount.toLocaleString()} ICCIDs NOT found:</b> these do not belong to any customer and will <b>NOT</b> be uploaded.`);
          }
          if (convertedDatesCount > 0) {
            notes.push(`• <b>${convertedDatesCount} dates successfully converted</b> into standard YYYY-MM-DD format.`);
          }
          if (unreadableDatesCount > 0) {
            notes.push(`• ⚠️ <b>${unreadableDatesCount} unreadable date cells:</b> left blank so database values are preserved.`);
          }
          if (notes.length) {
            $('simNotesBox').hidden = false;
            $('simNotesBox').innerHTML = notes.join('<br />');
          } else {
            $('simNotesBox').hidden = true;
          }

          if (res.records_matched > 0) {
            $('simPushMsg').innerHTML = `<b>${res.records_matched.toLocaleString()}</b> matched in customers (<b>${res.records_to_update.toLocaleString()}</b> will update, <b>${res.records_already_same.toLocaleString()}</b> already identical). <b>${notFoundCount.toLocaleString()}</b> not found (skipped).`;
            $('simPushMsg').style.color = 'var(--ink)';
          } else {
            $('simPushMsg').innerHTML = `⚠️ None of the ${res.file_rows_count.toLocaleString()} ICCIDs in the file were found in any customer account. Nothing will be uploaded.`;
            $('simPushMsg').style.color = 'var(--danger)';
          }

          if ($('btnSimDlNotFound')) $('btnSimDlNotFound').disabled = (notFoundCount === 0);

          // Update filter pill counts
          const compList = res.detailed_comparison || [];
          if ($('cntDiffFilterAll')) $('cntDiffFilterAll').textContent = compList.length;
          if ($('cntDiffFilterUpd')) $('cntDiffFilterUpd').textContent = compList.filter(c => c.status === 'different').length;
          if ($('cntDiffFilterSame')) $('cntDiffFilterSame').textContent = compList.filter(c => c.status === 'same').length;

          renderSimComparisonTable(compList, simDiffFilterMode);
          renderSimNotFoundTable(res.not_found_records || [], 'simNotFoundTableWrap');
          renderSimCustomerBreakdown(res.customer_breakdown || []);

          $('simCheckResults').hidden = false;

          if (isManual) {
            setTimeout(() => {
              if ($('simCheckResults')) {
                $('simCheckResults').scrollIntoView({ behavior: 'smooth', block: 'start' });
              }
            }, 100);
          }

          showEventPopup({
            type: 'uploading',
            title: 'Rows Validated Against Customer Records (Step 2)',
            message: `Validation complete: ${res.records_matched.toLocaleString()} customer records matched (${res.records_to_update.toLocaleString()} differing to update, ${res.records_already_same.toLocaleString()} already identical). ${notFoundCount.toLocaleString()} ICCIDs were NOT found in any customer and will NOT be uploaded.`,
            meta: {
              'Total File Rows': res.file_rows_count,
              'Found in Customers': res.records_matched,
              'Differing (To Update)': res.records_to_update,
              'Already Identical (Kept)': res.records_already_same,
              'ICCIDs Not Found (Will NOT Upload)': notFoundCount
            },
            progress: '100% Validated'
          });
        } catch (err) {
          if (progressBar) progressBar.style.width = '0%';
          if (progressPct) progressPct.textContent = 'Error';
          if (progressDetail) progressDetail.textContent = '⚠️ Check failed: ' + (err.message || err);
          fail(err);
        } finally {
          if (compareBtn) {
            compareBtn.disabled = false;
            if (compareIcon) compareIcon.textContent = '🔍';
            if (compareText) compareText.textContent = 'Compare & Check Records (Step 2)';
          }
        }
      }

      function renderSimComparisonTable(list, filter = 'all') {
        const wrap = $('simComparisonTableWrap');
        if (!wrap) return;

        const filtered = list.filter(r => {
          if (filter === 'updated') return r.status === 'different';
          if (filter === 'same') return r.status === 'same';
          return true;
        });

        if (!filtered.length) {
          wrap.innerHTML = `<div class="empty">No records found matching filter "${filter}".</div>`;
          return;
        }

        const formatCell = (item) => {
          if (!item) return '<span style="color:var(--muted)">—</span>';
          if (item.changed) {
            return `<span class="diff-chip diff-changed"><span class="diff-old">${esc(item.old)}</span> <span class="diff-arrow">➔</span> <span class="diff-new">${esc(item.new)}</span></span>`;
          }
          if (item.old && item.old !== '—') {
            return `<span class="diff-chip"><span class="diff-new">${esc(item.old)}</span> <span style="color:var(--ok);font-weight:800">✓</span></span>`;
          }
          return '<span style="color:var(--muted)">—</span>';
        };

        const rows = filtered.map(r => {
          const isUpd = r.status === 'different';
          const statusBadge = isUpd
            ? `<span class="diff-badge-diff">⚡ Differing (Replace ${r.changed_fields ? r.changed_fields.length : ''})</span>`
            : `<span class="diff-badge-same">🟢 Identical (Keep Existing)</span>`;

          return `
            <tr style="${isUpd ? 'background:rgba(217,119,6,0.03)' : ''}">
              <td><span style="font-size:12px;font-weight:700;color:var(--ink)">${esc(r.customer_name || '—')}</span></td>
              <td><b>${esc(r.imei || '—')}</b></td>
              <td><code>${esc(r.iccid || '—')}</code></td>
              <td>${formatCell(r.act_date)}</td>
              <td>${formatCell(r.expiry_date)}</td>
              <td>${formatCell(r.msisdn1)}</td>
              <td>${formatCell(r.msisdn2)}</td>
              <td>${formatCell(r.sim_provider)}</td>
              <td>${statusBadge}</td>
            </tr>
          `;
        }).join('');

        wrap.innerHTML = `
          <table class="data-table" style="font-size:12px">
            <thead>
              <tr>
                <th>Customer Name</th>
                <th>IMEI</th>
                <th>ICCID</th>
                <th>Activation Date</th>
                <th>Expiry Date</th>
                <th>MSISDN 1</th>
                <th>MSISDN 2</th>
                <th>SIM Provider</th>
                <th>Comparison Status</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        `;
      }

      function renderSimNotFoundTable(records, targetElementId = 'simNotFoundTableWrap') {
        const wrap = $(targetElementId);
        if (!wrap) return;

        if (!records || !records.length) {
          wrap.innerHTML = '<div class="empty" style="color:var(--ok);font-weight:700">✅ All ICCIDs in the uploaded file were found in existing customer accounts!</div>';
          return;
        }

        const rows = records.map((r, idx) => `
          <tr style="background:rgba(239,68,68,0.02)">
            <td style="color:var(--muted);font-size:11px">${idx + 1}</td>
            <td><b style="color:var(--danger);font-family:monospace">${esc(r.iccid || '—')}</b></td>
            <td>${esc(r.msisdn1 || '—')}</td>
            <td>${esc(r.msisdn2 || '—')}</td>
            <td>${esc(r.act_date || '—')}</td>
            <td>${esc(r.expiry_date || '—')}</td>
            <td>${esc(r.sim_provider || '—')}</td>
            <td><span class="badge" style="background:rgba(239,68,68,0.1);color:var(--danger);font-weight:700">❌ Not Found in Any Customer (Will NOT Upload)</span></td>
          </tr>
        `).join('');

        wrap.innerHTML = `
          <table class="data-table" style="font-size:12px">
            <thead>
              <tr>
                <th style="width:40px">#</th>
                <th>ICCID / CCID (Not Found)</th>
                <th>MSISDN 1</th>
                <th>MSISDN 2</th>
                <th>Activation Date</th>
                <th>Expiry Date</th>
                <th>SIM Provider</th>
                <th>Upload Status</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        `;
      }

      function renderSimCustomerBreakdown(list) {
        const wrap = $('simCustomerTableWrap');
        if (!wrap) return;
        if (!list.length) {
          wrap.innerHTML = '<div class="empty">No customers matched any entries in the file.</div>';
          return;
        }
        let totalMatched = 0, totalToUpdate = 0, totalSame = 0;
        const rows = list.map(c => {
          totalMatched += c.matched_count;
          totalToUpdate += c.to_update_count;
          totalSame += c.already_same_count;
          return `
            <tr>
              <td><b>${esc(c.customer_name)}</b></td>
              <td><b>${c.matched_count.toLocaleString()}</b></td>
              <td><span class="badge" style="background:${c.to_update_count ? 'var(--warn-bg)' : 'transparent'};color:${c.to_update_count ? 'var(--warn)' : 'var(--muted)'};font-weight:700">${c.to_update_count.toLocaleString()}</span></td>
              <td>${c.already_same_count.toLocaleString()}</td>
              <td>${c.msisdn1_changes || 0}</td>
              <td>${c.msisdn2_changes || 0}</td>
              <td>${c.act_date_changes || 0}</td>
              <td>${c.expiry_date_changes || 0}</td>
              <td>${c.sim_provider_changes || 0}</td>
            </tr>
          `;
        }).join('');

        wrap.innerHTML = `
          <table class="data-table" style="font-size:12px">
            <thead>
              <tr>
                <th>Customer Name</th>
                <th>Records Matched</th>
                <th>Will Update</th>
                <th>Already Same</th>
                <th>MSISDN 1</th>
                <th>MSISDN 2</th>
                <th>Act Date</th>
                <th>Exp Date</th>
                <th>SIM Provider</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
            <tfoot>
              <tr style="font-weight:800;border-top:2px solid var(--line);background:var(--card-subtle)">
                <td>Total Across All Customers</td>
                <td>${totalMatched.toLocaleString()}</td>
                <td>${totalToUpdate.toLocaleString()}</td>
                <td>${totalSame.toLocaleString()}</td>
                <td colspan="5"></td>
              </tr>
            </tfoot>
          </table>
        `;
      }

      async function executeSimPush() {
        if (!simActiveCheckResult) return;

        const keyCol = $('colMapKey') ? $('colMapKey').value : '';
        const msisdn1Col = $('colMapMsisdn1') ? $('colMapMsisdn1').value : '';
        const msisdn2Col = $('colMapMsisdn2') ? $('colMapMsisdn2').value : '';
        const actDateCol = $('colMapActDate') ? $('colMapActDate').value : '';
        const expDateCol = $('colMapExpDate') ? $('colMapExpDate').value : '';
        const providerCol = $('colMapSimProvider') ? $('colMapSimProvider').value : '';
        const chosenProvider = $('simProviderSelect') ? $('simProviderSelect').value : '';
        const overwrite = $('simOverwriteChk') ? $('simOverwriteChk').checked : true;

        const matchedCount = simActiveCheckResult.records_matched || 0;
        const toUpdate = simActiveCheckResult.records_to_update || 0;
        const notFoundCount = simActiveCheckResult.not_found_keys_count || 0;

        if (matchedCount === 0) {
          toast('⚠️ No matching customer records found for these ICCIDs. Nothing to upload.');
          return;
        }

        const confirmMsg = `Apply SIM data to database?\n\n• ${matchedCount.toLocaleString()} matching customer records will be processed (${toUpdate.toLocaleString()} differing will be replaced, identical values preserved).\n• ${notFoundCount.toLocaleString()} ICCIDs NOT found in any customer will NOT be uploaded.\n\nProceed with upload?`;

        if (!await cv.confirm(confirmMsg)) {
          return;
        }

        const fullPayload = [];
        simRawFileRows.forEach(rawObj => {
          let rawKey = rawObj[keyCol] != null ? String(rawObj[keyCol]).trim() : '';
          if (rawKey.endsWith('.0') && /^\d+\.0$/.test(rawKey)) rawKey = rawKey.slice(0, -2);
          if (/[eE]\+?/.test(rawKey)) {
            try {
              const num = Number(rawKey);
              if (!isNaN(num) && Number.isFinite(num)) rawKey = BigInt(Math.round(num)).toString();
            } catch { }
          }
          rawKey = rawKey.replace(/[\s\-_]+/g, '').toUpperCase();
          if (!rawKey || rawKey.length < 5) return;

          const rowProv = providerCol ? (rawObj[providerCol] || '').trim() : '';

          fullPayload.push({
            iccid: rawKey,
            msisdn1: msisdn1Col ? (rawObj[msisdn1Col] || '').trim() || null : null,
            msisdn2: msisdn2Col ? (rawObj[msisdn2Col] || '').trim() || null : null,
            act_date: actDateCol ? convertDateToStandardFormat(rawObj[actDateCol]) : null,
            expiry_date: expDateCol ? convertDateToStandardFormat(rawObj[expDateCol]) : null,
            sim_provider: rowProv || chosenProvider || null
          });
        });

        const progressWrap = $('simPushProgressWrap');
        const progressBar = $('simPushBar');
        const progressPct = $('simPushPct');
        const progressStatus = $('simPushStatus');
        const liveCount = $('simPushLiveCount');
        const logsEl = $('simPushLogs');

        progressWrap.hidden = false;
        if ($('btnExecuteSelectedAction')) $('btnExecuteSelectedAction').disabled = true;
        logsEl.innerHTML = '';

        const chunkSize = 1000;
        let runningUpdated = 0;
        let runningAlreadySame = 0;
        let runningUnmatched = 0;
        const allAppliedComparison = [];
        const allNotFoundRecords = [];

        try {
          for (let i = 0; i < fullPayload.length; i += chunkSize) {
            const partNum = Math.floor(i / chunkSize) + 1;
            const totalParts = Math.ceil(fullPayload.length / chunkSize);
            const chunk = fullPayload.slice(i, i + chunkSize);
            const pct = Math.min(99, Math.round(((i + chunk.length) / (fullPayload.length || 1)) * 100));

            progressBar.style.width = pct + '%';
            progressPct.textContent = pct + '%';
            progressStatus.textContent = `Uploading & applying batch ${partNum} of ${totalParts} (${pct}% complete)…`;

            const res = await api('/api/simdata/apply', {
              method: 'POST',
              body: JSON.stringify({
                rows: chunk,
                overwrite: overwrite,
                match_by: currentSimMatchMode,
                sim_provider: chosenProvider || null,
                insert_new: false,
                action: 'update_only'
              })
            });

            runningUpdated += (res.updated || 0);
            runningAlreadySame += (res.already_same || res.ignored_identical || 0);
            runningUnmatched += (res.unmatched_count || 0);

            if (res.applied_comparison) allAppliedComparison.push(...res.applied_comparison);
            if (res.not_found_records) allNotFoundRecords.push(...res.not_found_records);

            liveCount.textContent = `${runningUpdated.toLocaleString()} updated, ${runningAlreadySame.toLocaleString()} identical kept, ${runningUnmatched.toLocaleString()} not found skipped…`;
            const logLine = document.createElement('div');
            logLine.textContent = `[Part ${partNum}/${totalParts}] Differing updated: ${res.updated || 0}, Identical kept: ${res.already_same || 0}, Not found skipped: ${res.unmatched_count || 0}.`;
            logsEl.appendChild(logLine);
            logsEl.scrollTop = logsEl.scrollHeight;
          }

          progressBar.style.width = '100%';
          progressPct.textContent = '100%';
          progressStatus.textContent = `✅ Process Complete (100%): ${runningUpdated.toLocaleString()} updated in database (${runningAlreadySame.toLocaleString()} already identical preserved, ${notFoundCount.toLocaleString()} not found skipped).`;

          toast(`Upload complete! ${runningUpdated.toLocaleString()} customer records updated in database.`);

          // Render Post-Upload Comparison & Results View
          const postResult = {
            total_file_rows: fullPayload.length,
            updated: runningUpdated,
            already_same: runningAlreadySame,
            not_found_count: notFoundCount,
            applied_comparison: allAppliedComparison,
            not_found_records: allNotFoundRecords.length ? allNotFoundRecords : (simActiveCheckResult.not_found_records || []),
            before_comparison: (simActiveCheckResult.detailed_comparison || [])
          };
          simLastPostUploadResult = postResult;
          renderSimPostUploadResults(postResult);

          showEventPopup({
            type: 'uploading',
            title: 'SIM Data Successfully Applied to Customer Records (Step 3)',
            message: `SIM Data Upload Complete: ${runningUpdated.toLocaleString()} differing records updated in database and mirrored to website tables. ${runningAlreadySame.toLocaleString()} identical records preserved. ${notFoundCount.toLocaleString()} ICCIDs not found were NOT uploaded.`,
            meta: {
              'Records Updated in DB': runningUpdated,
              'Already Identical (Kept)': runningAlreadySame,
              'ICCIDs Not Found (Skipped)': notFoundCount,
              'Total Rows Processed': fullPayload.length
            },
            progress: '100% Complete'
          });

          await loadCU(); await updateChrome();
          if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
          if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
          if (typeof loadStats === 'function') loadStats();
          if (typeof loadTableForCustomer === 'function' && typeof activeCid !== 'undefined' && activeCid) {
            loadTableForCustomer(activeCid);
          }
        } catch (err) {
          fail(err);
          progressStatus.textContent = `⚠️ Push failed partway: ${err.message}.`;
        } finally {
          if ($('btnExecuteSelectedAction')) $('btnExecuteSelectedAction').disabled = false;
        }
      }

      function renderSimPostUploadResults(data) {
        const wrap = $('simPostUploadResults');
        if (!wrap) return;

        wrap.hidden = false;

        $('kpiPostTotalRows').textContent = (data.total_file_rows || 0).toLocaleString();
        $('kpiPostUpdated').textContent = (data.updated || 0).toLocaleString();
        $('kpiPostAlreadySame').textContent = (data.already_same || 0).toLocaleString();
        $('kpiPostNotFound').textContent = (data.not_found_count || 0).toLocaleString();

        const compList = data.applied_comparison || [];
        const notFoundList = data.not_found_records || [];

        if ($('cntPostUpdatedTab')) $('cntPostUpdatedTab').textContent = compList.length.toLocaleString();
        if ($('cntPostNotFoundTab')) $('cntPostNotFoundTab').textContent = notFoundList.length.toLocaleString();

        if ($('cntPostFilterAll')) $('cntPostFilterAll').textContent = compList.length;
        if ($('cntPostFilterUpd')) $('cntPostFilterUpd').textContent = compList.filter(c => c.status === 'updated').length;
        if ($('cntPostFilterSame')) $('cntPostFilterSame').textContent = compList.filter(c => c.status === 'same').length;

        renderSimPostComparisonTable(compList, simPostFilterMode);
        renderSimNotFoundTable(notFoundList, 'simPostNotFoundTableWrap');

        // Populate Before-Upload copy
        const beforeWrap = $('simPostBeforeTableWrap');
        if (beforeWrap && data.before_comparison) {
          renderSimComparisonTableDirect(data.before_comparison, beforeWrap);
        }

        setTimeout(() => {
          wrap.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 150);
      }

      function renderSimPostComparisonTable(list, filter = 'all') {
        const wrap = $('simPostComparisonTableWrap');
        if (!wrap) return;

        const filtered = list.filter(r => {
          if (filter === 'updated') return r.status === 'updated';
          if (filter === 'same') return r.status === 'same';
          return true;
        });

        if (!filtered.length) {
          wrap.innerHTML = `<div class="empty">No records found matching filter "${filter}".</div>`;
          return;
        }

        const formatCell = (item) => {
          if (!item) return '<span style="color:var(--muted)">—</span>';
          if (item.changed) {
            return `<span class="diff-chip diff-changed"><span class="diff-old">${esc(item.old)}</span> <span class="diff-arrow">➔</span> <span class="diff-new">${esc(item.new)}</span></span>`;
          }
          if (item.old && item.old !== '—') {
            return `<span class="diff-chip"><span class="diff-new">${esc(item.old)}</span> <span style="color:var(--ok);font-weight:800">✓</span></span>`;
          }
          return '<span style="color:var(--muted)">—</span>';
        };

        const rows = filtered.map(r => {
          const isUpd = r.status === 'updated';
          const statusBadge = isUpd
            ? `<span class="diff-badge-diff" style="background:rgba(16,185,129,0.1);color:var(--ok);border-color:rgba(16,185,129,0.3)">✅ Updated in DB</span>`
            : `<span class="diff-badge-same">🟢 Kept Same (Identical)</span>`;

          return `
            <tr style="${isUpd ? 'background:rgba(16,185,129,0.03)' : ''}">
              <td><span style="font-size:12px;font-weight:700;color:var(--ink)">${esc(r.customer_name || '—')}</span></td>
              <td><b>${esc(r.imei || '—')}</b></td>
              <td><code>${esc(r.iccid || '—')}</code></td>
              <td>${formatCell(r.act_date)}</td>
              <td>${formatCell(r.expiry_date)}</td>
              <td>${formatCell(r.msisdn1)}</td>
              <td>${formatCell(r.msisdn2)}</td>
              <td>${formatCell(r.sim_provider)}</td>
              <td>${statusBadge}</td>
            </tr>
          `;
        }).join('');

        wrap.innerHTML = `
          <table class="data-table" style="font-size:12px">
            <thead>
              <tr>
                <th>Customer Name</th>
                <th>IMEI</th>
                <th>ICCID</th>
                <th>Activation Date (Before ➔ After)</th>
                <th>Expiry Date (Before ➔ After)</th>
                <th>MSISDN 1 (Before ➔ After)</th>
                <th>MSISDN 2 (Before ➔ After)</th>
                <th>SIM Provider (Before ➔ After)</th>
                <th>Post-Upload Status</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        `;
      }

      function renderSimComparisonTableDirect(list, wrap) {
        if (!wrap) return;
        if (!list || !list.length) {
          wrap.innerHTML = '<div class="empty">No before-upload records available.</div>';
          return;
        }
        const formatCell = (item) => {
          if (!item) return '<span style="color:var(--muted)">—</span>';
          if (item.changed) {
            return `<span class="diff-chip diff-changed"><span class="diff-old">${esc(item.old)}</span> <span class="diff-arrow">➔</span> <span class="diff-new">${esc(item.new)}</span></span>`;
          }
          if (item.old && item.old !== '—') {
            return `<span class="diff-chip"><span class="diff-new">${esc(item.old)}</span> <span style="color:var(--ok);font-weight:800">✓</span></span>`;
          }
          return '<span style="color:var(--muted)">—</span>';
        };

        const rows = list.map(r => {
          const isUpd = r.status === 'different';
          const statusBadge = isUpd
            ? `<span class="diff-badge-diff">⚡ Differing</span>`
            : `<span class="diff-badge-same">🟢 Identical</span>`;

          return `
            <tr style="${isUpd ? 'background:rgba(217,119,6,0.03)' : ''}">
              <td><span style="font-size:12px;font-weight:700;color:var(--ink)">${esc(r.customer_name || '—')}</span></td>
              <td><b>${esc(r.imei || '—')}</b></td>
              <td><code>${esc(r.iccid || '—')}</code></td>
              <td>${formatCell(r.act_date)}</td>
              <td>${formatCell(r.expiry_date)}</td>
              <td>${formatCell(r.msisdn1)}</td>
              <td>${formatCell(r.msisdn2)}</td>
              <td>${formatCell(r.sim_provider)}</td>
              <td>${statusBadge}</td>
            </tr>
          `;
        }).join('');

        wrap.innerHTML = `
          <table class="data-table" style="font-size:12px">
            <thead>
              <tr>
                <th>Customer Name</th>
                <th>IMEI</th>
                <th>ICCID</th>
                <th>Activation Date</th>
                <th>Expiry Date</th>
                <th>MSISDN 1</th>
                <th>MSISDN 2</th>
                <th>SIM Provider</th>
                <th>Before Status</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        `;
      }

      function exportSimPostUploadReportExcel(data) {
        if (!data) return;
        const compList = data.applied_comparison || [];
        const notFoundList = data.not_found_records || [];

        if (typeof XLSX === 'undefined') {
          toast('⚠️ XLSX library not available for export.');
          return;
        }

        const wb = XLSX.utils.book_new();

        // Sheet 1: Matched & Updated Records
        const headers1 = [
          'Customer Name', 'IMEI', 'ICCID',
          'Activation Date (Before)', 'Activation Date (After)',
          'Expiry Date (Before)', 'Expiry Date (After)',
          'MSISDN 1 (Before)', 'MSISDN 1 (After)',
          'MSISDN 2 (Before)', 'MSISDN 2 (After)',
          'SIM Provider (Before)', 'SIM Provider (After)',
          'Update Status'
        ];
        const rows1 = [headers1];
        compList.forEach(r => {
          rows1.push([
            r.customer_name || '',
            r.imei || '',
            r.iccid || '',
            (r.act_date && r.act_date.old !== '—') ? r.act_date.old : '',
            (r.act_date && r.act_date.new !== '—') ? r.act_date.new : '',
            (r.expiry_date && r.expiry_date.old !== '—') ? r.expiry_date.old : '',
            (r.expiry_date && r.expiry_date.new !== '—') ? r.expiry_date.new : '',
            (r.msisdn1 && r.msisdn1.old !== '—') ? r.msisdn1.old : '',
            (r.msisdn1 && r.msisdn1.new !== '—') ? r.msisdn1.new : '',
            (r.msisdn2 && r.msisdn2.old !== '—') ? r.msisdn2.old : '',
            (r.msisdn2 && r.msisdn2.new !== '—') ? r.msisdn2.new : '',
            (r.sim_provider && r.sim_provider.old !== '—') ? r.sim_provider.old : '',
            (r.sim_provider && r.sim_provider.new !== '—') ? r.sim_provider.new : '',
            r.status === 'updated' ? 'Successfully Updated in DB' : 'Kept Same (Identical)'
          ]);
        });
        const ws1 = XLSX.utils.aoa_to_sheet(rows1);
        XLSX.utils.book_append_sheet(wb, ws1, 'Matched & Updated Records');

        // Sheet 2: Not Found ICCIDs
        if (notFoundList.length) {
          const headers2 = ['ICCID / CCID', 'MSISDN 1', 'MSISDN 2', 'Activation Date', 'Expiry Date', 'SIM Provider', 'Reason'];
          const rows2 = [headers2];
          notFoundList.forEach(r => {
            rows2.push([
              r.iccid || '',
              (r.msisdn1 && r.msisdn1 !== '—') ? r.msisdn1 : '',
              (r.msisdn2 && r.msisdn2 !== '—') ? r.msisdn2 : '',
              (r.act_date && r.act_date !== '—') ? r.act_date : '',
              (r.expiry_date && r.expiry_date !== '—') ? r.expiry_date : '',
              (r.sim_provider && r.sim_provider !== '—') ? r.sim_provider : '',
              'ICCID Not Found in Any Customer - NOT Uploaded'
            ]);
          });
          const ws2 = XLSX.utils.aoa_to_sheet(rows2);
          XLSX.utils.book_append_sheet(wb, ws2, 'Not Found (Not Uploaded)');
        }

        const dateStr = new Date().toISOString().slice(0, 10);
        XLSX.writeFile(wb, `SIM_Upload_After_Change_Report_${dateStr}.xlsx`);
        toast('After-change comparison report downloaded successfully.');
      }

      function exportSimPreUploadReportExcel(data) {
        if (!data) {
          toast('⚠️ No data available to export.');
          return;
        }
        const compList = data.detailed_comparison || data.before_comparison || [];
        const notFoundList = data.not_found_records || [];
        const breakdownList = data.customer_breakdown || [];

        if (typeof XLSX === 'undefined') {
          toast('⚠️ XLSX library not available for export.');
          return;
        }

        const wb = XLSX.utils.book_new();

        // Sheet 1: Matched Records - Before Change Preview
        const headers1 = [
          'Customer Name', 'IMEI', 'ICCID',
          'Current DB Activation Date', 'Incoming File Activation Date',
          'Current DB Expiry Date', 'Incoming File Expiry Date',
          'Current DB MSISDN 1', 'Incoming File MSISDN 1',
          'Current DB MSISDN 2', 'Incoming File MSISDN 2',
          'Current DB SIM Provider', 'Incoming File SIM Provider',
          'Comparison Status', 'Changed Fields'
        ];
        const rows1 = [headers1];
        compList.forEach(r => {
          const changedFields = (r.changed_fields && r.changed_fields.length) ? r.changed_fields.join(', ') : 'None';
          rows1.push([
            r.customer_name || '',
            r.imei || '',
            r.iccid || '',
            (r.act_date && r.act_date.old !== '—') ? r.act_date.old : '',
            (r.act_date && r.act_date.new !== '—') ? r.act_date.new : '',
            (r.expiry_date && r.expiry_date.old !== '—') ? r.expiry_date.old : '',
            (r.expiry_date && r.expiry_date.new !== '—') ? r.expiry_date.new : '',
            (r.msisdn1 && r.msisdn1.old !== '—') ? r.msisdn1.old : '',
            (r.msisdn1 && r.msisdn1.new !== '—') ? r.msisdn1.new : '',
            (r.msisdn2 && r.msisdn2.old !== '—') ? r.msisdn2.old : '',
            (r.msisdn2 && r.msisdn2.new !== '—') ? r.msisdn2.new : '',
            (r.sim_provider && r.sim_provider.old !== '—') ? r.sim_provider.old : '',
            (r.sim_provider && r.sim_provider.new !== '—') ? r.sim_provider.new : '',
            r.status === 'different' ? 'Will Update (Differing)' : 'Already Identical (Keep Existing)',
            changedFields
          ]);
        });
        const ws1 = XLSX.utils.aoa_to_sheet(rows1);
        XLSX.utils.book_append_sheet(wb, ws1, 'Matched - Before Change');

        // Sheet 2: Not Found ICCIDs
        if (notFoundList.length) {
          const headers2 = ['ICCID / CCID', 'MSISDN 1', 'MSISDN 2', 'Activation Date', 'Expiry Date', 'SIM Provider', 'Action Status'];
          const rows2 = [headers2];
          notFoundList.forEach(r => {
            rows2.push([
              r.iccid || '',
              (r.msisdn1 && r.msisdn1 !== '—') ? r.msisdn1 : '',
              (r.msisdn2 && r.msisdn2 !== '—') ? r.msisdn2 : '',
              (r.act_date && r.act_date !== '—') ? r.act_date : '',
              (r.expiry_date && r.expiry_date !== '—') ? r.expiry_date : '',
              (r.sim_provider && r.sim_provider !== '—') ? r.sim_provider : '',
              'ICCID Not Found in Any Customer - Will NOT be uploaded'
            ]);
          });
          const ws2 = XLSX.utils.aoa_to_sheet(rows2);
          XLSX.utils.book_append_sheet(wb, ws2, 'Not Found (Skipped)');
        }

        // Sheet 3: Customer Breakdown
        if (breakdownList.length) {
          const headers3 = ['Customer Name', 'Matched Device Count'];
          const rows3 = [headers3];
          breakdownList.forEach(b => {
            rows3.push([b.customer_name || '', b.count || 0]);
          });
          const ws3 = XLSX.utils.aoa_to_sheet(rows3);
          XLSX.utils.book_append_sheet(wb, ws3, 'Customer Breakdown');
        }

        const dateStr = new Date().toISOString().slice(0, 10);
        XLSX.writeFile(wb, `SIM_Upload_Before_Change_Report_${dateStr}.xlsx`);
        toast('Before-change Excel report downloaded successfully.');
      }

      function exportSimBothReportsExcel(postData, preData) {
        if (!postData && !preData) {
          toast('⚠️ No data available to export.');
          return;
        }
        if (typeof XLSX === 'undefined') {
          toast('⚠️ XLSX library not available for export.');
          return;
        }

        const wb = XLSX.utils.book_new();

        // Sheet 1: After Changing - Applied Updates
        const appliedList = (postData && postData.applied_comparison) ? postData.applied_comparison : [];
        const headers1 = [
          'Customer Name', 'IMEI', 'ICCID',
          'Activation Date (Before)', 'Activation Date (After)',
          'Expiry Date (Before)', 'Expiry Date (After)',
          'MSISDN 1 (Before)', 'MSISDN 1 (After)',
          'MSISDN 2 (Before)', 'MSISDN 2 (After)',
          'SIM Provider (Before)', 'SIM Provider (After)',
          'Upload Result'
        ];
        const rows1 = [headers1];
        appliedList.forEach(r => {
          rows1.push([
            r.customer_name || '',
            r.imei || '',
            r.iccid || '',
            (r.act_date && r.act_date.old !== '—') ? r.act_date.old : '',
            (r.act_date && r.act_date.new !== '—') ? r.act_date.new : '',
            (r.expiry_date && r.expiry_date.old !== '—') ? r.expiry_date.old : '',
            (r.expiry_date && r.expiry_date.new !== '—') ? r.expiry_date.new : '',
            (r.msisdn1 && r.msisdn1.old !== '—') ? r.msisdn1.old : '',
            (r.msisdn1 && r.msisdn1.new !== '—') ? r.msisdn1.new : '',
            (r.msisdn2 && r.msisdn2.old !== '—') ? r.msisdn2.old : '',
            (r.msisdn2 && r.msisdn2.new !== '—') ? r.msisdn2.new : '',
            (r.sim_provider && r.sim_provider.old !== '—') ? r.sim_provider.old : '',
            (r.sim_provider && r.sim_provider.new !== '—') ? r.sim_provider.new : '',
            r.status === 'updated' ? 'Successfully Updated in DB' : 'Kept Same (Identical)'
          ]);
        });
        const ws1 = XLSX.utils.aoa_to_sheet(rows1);
        XLSX.utils.book_append_sheet(wb, ws1, 'After Changing - Applied');

        // Sheet 2: Before Changing - Preview
        const beforeList = (postData && postData.before_comparison) ? postData.before_comparison : ((preData && preData.detailed_comparison) ? preData.detailed_comparison : []);
        const headers2 = [
          'Customer Name', 'IMEI', 'ICCID',
          'Current DB Activation Date', 'Incoming File Activation Date',
          'Current DB Expiry Date', 'Incoming File Expiry Date',
          'Current DB MSISDN 1', 'Incoming File MSISDN 1',
          'Current DB MSISDN 2', 'Incoming File MSISDN 2',
          'Current DB SIM Provider', 'Incoming File SIM Provider',
          'Comparison Status'
        ];
        const rows2 = [headers2];
        beforeList.forEach(r => {
          rows2.push([
            r.customer_name || '',
            r.imei || '',
            r.iccid || '',
            (r.act_date && r.act_date.old !== '—') ? r.act_date.old : '',
            (r.act_date && r.act_date.new !== '—') ? r.act_date.new : '',
            (r.expiry_date && r.expiry_date.old !== '—') ? r.expiry_date.old : '',
            (r.expiry_date && r.expiry_date.new !== '—') ? r.expiry_date.new : '',
            (r.msisdn1 && r.msisdn1.old !== '—') ? r.msisdn1.old : '',
            (r.msisdn1 && r.msisdn1.new !== '—') ? r.msisdn1.new : '',
            (r.msisdn2 && r.msisdn2.old !== '—') ? r.msisdn2.old : '',
            (r.msisdn2 && r.msisdn2.new !== '—') ? r.msisdn2.new : '',
            (r.sim_provider && r.sim_provider.old !== '—') ? r.sim_provider.old : '',
            (r.sim_provider && r.sim_provider.new !== '—') ? r.sim_provider.new : '',
            r.status === 'different' ? 'Will Update (Differing)' : 'Already Identical (Keep Existing)'
          ]);
        });
        const ws2 = XLSX.utils.aoa_to_sheet(rows2);
        XLSX.utils.book_append_sheet(wb, ws2, 'Before Changing - Preview');

        // Sheet 3: ICCIDs Not Found
        const notFoundList = (postData && postData.not_found_records) ? postData.not_found_records : ((preData && preData.not_found_records) ? preData.not_found_records : []);
        if (notFoundList.length) {
          const headers3 = ['ICCID / CCID', 'MSISDN 1', 'MSISDN 2', 'Activation Date', 'Expiry Date', 'SIM Provider', 'Action Status'];
          const rows3 = [headers3];
          notFoundList.forEach(r => {
            rows3.push([
              r.iccid || '',
              (r.msisdn1 && r.msisdn1 !== '—') ? r.msisdn1 : '',
              (r.msisdn2 && r.msisdn2 !== '—') ? r.msisdn2 : '',
              (r.act_date && r.act_date !== '—') ? r.act_date : '',
              (r.expiry_date && r.expiry_date !== '—') ? r.expiry_date : '',
              (r.sim_provider && r.sim_provider !== '—') ? r.sim_provider : '',
              'ICCID Not Found in Any Customer - NOT Uploaded'
            ]);
          });
          const ws3 = XLSX.utils.aoa_to_sheet(rows3);
          XLSX.utils.book_append_sheet(wb, ws3, 'Skipped - Not Found ICCIDs');
        }

        // Sheet 4: Customer Breakdown (if available)
        const breakdownList = (preData && preData.customer_breakdown) ? preData.customer_breakdown : [];
        if (breakdownList.length) {
          const headers4 = ['Customer Name', 'Matched Device Count'];
          const rows4 = [headers4];
          breakdownList.forEach(b => {
            rows4.push([b.customer_name || '', b.count || 0]);
          });
          const ws4 = XLSX.utils.aoa_to_sheet(rows4);
          XLSX.utils.book_append_sheet(wb, ws4, 'Customer Breakdown');
        }

        const dateStr = new Date().toISOString().slice(0, 10);
        XLSX.writeFile(wb, `SIM_Upload_Complete_Both_Reports_${dateStr}.xlsx`);
        toast('Complete Before & After comparison Excel report downloaded successfully.');
      }

      /* =========================================================================
         CONTAINER 6: SEPARATE FETCH DATA (Normal & Bulk)
         ========================================================================= */
      let activeFetchSimType = 'all'; // 'all' | 'esim' | 'plastic'
      let activeFetchMode = 'normal'; // 'normal' | 'bulk'
      let nfCurrentList = []; // Last results in Normal Fetch
      let bfReadValues = []; // Values read from Excel for Bulk Fetch
      let bfLastResult = null; // Result from /api/fetch/bulk

      
    // Page Boot
    
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

    const _bootPage = async () => {
      await loadExtraColumns();
      await syncGlobalMetricsAndChrome();
      await loadInventoryContainer().catch(e => console.warn(e));
    };
    document.addEventListener('DOMContentLoaded', _bootPage);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      _bootPage();
    }
    
  

    // --- Universal Modal Dialog Close & Cancel Engine ---
    window.closeModal = function(id) {
      try {
        const dlg = typeof id === 'string' ? document.getElementById(id) : id;
        if (dlg) {
          if (typeof dlg.close === 'function') {
            dlg.close();
          } else {
            dlg.removeAttribute('open');
            dlg.style.display = 'none';
          }
        }
      } catch(e) {
        console.warn('Error closing modal:', id, e);
      }
    };

    document.addEventListener('DOMContentLoaded', () => {
      // Wire up all dialog backdrop clicks & close buttons
      document.querySelectorAll('dialog').forEach(dlg => {
        dlg.addEventListener('click', (e) => {
          const rect = dlg.getBoundingClientRect();
          const isInDialog = (rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
            rect.left <= e.clientX && e.clientX <= rect.left + rect.width);
          if (!isInDialog) {
            if (typeof dlg.close === 'function') dlg.close();
          }
        });

        // Wire up all cancel and close buttons inside dialogs
        dlg.querySelectorAll('button[data-close], .btn-close, .modal-close, [aria-label="Close"]').forEach(btn => {
          btn.addEventListener('click', () => {
            if (typeof dlg.close === 'function') dlg.close();
          });
        });
      });
    });

