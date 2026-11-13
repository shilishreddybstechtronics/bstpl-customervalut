/* CustomerVault Unified Cart & Recycle Bin Controller
   Supports finding, viewing, restoring, and permanently purging:
   1. Deleted whole customers (customer portfolios)
   2. Deleted entries of customers (device & SIM inventory records, errored entries)
*/
(function () {
  const E = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  let allCartDevs = [];
  let allCartCusts = [];
  let currentTab = 'custs';

  function ensureCartModalHtml() {
    let dlg = document.getElementById('dlgCartModal');
    if (!dlg) {
      dlg = document.createElement('dialog');
      dlg.id = 'dlgCartModal';
      dlg.className = 'modal-card';
      dlg.style.cssText = 'width:min(1150px, 96vw); max-height:92vh; padding:0; border-radius:20px; border:1px solid var(--line); box-shadow:0 30px 80px rgba(0,0,0,.5); overflow:hidden';
      document.body.appendChild(dlg);
    }

    dlg.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--card-subtle);position:sticky;top:0;z-index:20">
        <div style="display:flex;align-items:center;gap:12px">
          <div style="width:48px;height:48px;border-radius:12px;background:#ffffff;border:1.5px solid var(--line);display:flex;align-items:center;justify-content:center;padding:3px;box-shadow:0 3px 8px rgba(0,0,0,0.06);position:relative;flex-shrink:0">
            <img src="logo.svg" onerror="this.src=\'logo.png\'" alt="BSTPL Logo" style="width:100%;height:100%;object-fit:contain;border-radius:8px" />
            <span style="position:absolute;bottom:-4px;right:-4px;font-size:13px;background:var(--card);border:1px solid var(--line);border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 3px rgba(0,0,0,0.15)">🛒</span>
          </div>
          <div>
            <div style="display:flex;align-items:center;gap:8px">
              <h3 style="margin:0;font-size:18px;font-weight:800;color:var(--text)">Cart &amp; Recycle Bin</h3>
              <span class="tag ok" id="cartTotalHeaderBadge" style="font-weight:800;font-size:12px">0 Total Items</span>
            </div>
            <p class="sub" style="margin:2px 0 0;font-size:12.5px;color:var(--muted)">Recover deleted entries of customers or whole customer portfolios. Restore with 1 click or permanently purge forever.</p>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <button class="b" id="btnRestoreAllCart" type="button" style="font-weight:700;font-size:12.5px;padding:8px 14px" title="Restore all deleted customer entries to inventory">🔄 Restore All Entries</button>
          <button class="b d" id="btnEmptyCartForever" type="button" style="font-weight:700;font-size:12.5px;padding:8px 14px" title="Permanently delete all items in the cart">🗑️ Empty Cart Forever</button>
          <button class="b ghost" type="button" onclick="closeCartModal()" style="font-size:18px;min-width:38px;min-height:38px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;border-radius:8px" aria-label="Close Cart">✕</button>
        </div>
      </div>

      <div style="padding:16px 24px 20px; max-height:calc(92vh - 80px); overflow-y:auto" id="cartModalScrollBody">
        <!-- Live Composition & Summary Banner -->
        <div class="card" id="cartSummaryBannerWrap" style="padding:16px 18px;border:1px solid var(--line);margin-bottom:16px;background:var(--card);border-radius:14px;box-shadow:0 2px 10px rgba(0,0,0,0.04)">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:10px">
            <div style="display:flex;align-items:center;gap:10px">
              <b style="font-size:14px;color:var(--text);display:flex;align-items:center;gap:6px">
                <span>📊</span> <span>Cart Composition &amp; Breakdown</span>
              </b>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap" id="cartBreakdownTags">
              <span class="tag" style="background:rgba(2,132,199,0.12);color:#0284c7;font-weight:700" id="cartStatCustTag">🏢 Whole Customers: 0</span>
              <span class="tag" style="background:rgba(37,99,235,0.12);color:#2563eb;font-weight:700" id="cartStatDevTag">📱 Customer Entries: 0</span>
              <span class="tag bad" style="font-weight:700" id="cartStatErrTag">⚠️ Errored Entries: 0</span>
            </div>
          </div>
          <!-- Multi-Segment Visual Progress / Composition Bar -->
          <div style="height:10px;background:var(--card-subtle);border-radius:6px;overflow:hidden;display:flex;border:1px solid var(--line)">
            <div id="cartBarCust" style="width:0%;background:linear-gradient(90deg, #0284c7, #38bdf8);transition:width 0.3s ease" title="Whole Customers"></div>
            <div id="cartBarDev" style="width:0%;background:linear-gradient(90deg, #2563eb, #60a5fa);transition:width 0.3s ease" title="Customer Entries"></div>
            <div id="cartBarErr" style="width:0%;background:linear-gradient(90deg, #ef4444, #f97316);transition:width 0.3s ease" title="Errored Records"></div>
          </div>
        </div>

        <!-- Tab Switcher -->
        <div style="display:flex;gap:12px;border-bottom:2px solid var(--line);margin-bottom:18px">
          <button type="button" class="b ghost" id="tabBtnCartCusts" onclick="switchCartTab('custs')" style="border-radius:0;padding:10px 18px;font-size:14px;border-bottom:3px solid var(--primary);font-weight:800;color:var(--text)">
            🏢 Deleted Customers (<span id="cartTabCountCusts">0</span>)
          </button>
          <button type="button" class="b ghost" id="tabBtnCartDevs" onclick="switchCartTab('devs')" style="border-radius:0;padding:10px 18px;font-size:14px;border-bottom:3px solid transparent;font-weight:600;color:var(--muted)">
            📱 Deleted Entries of Customers (<span id="cartTabCountDevs">0</span>)
          </button>
        </div>

        <!-- Section 1: Deleted Whole Customers Tab -->
        <div id="cartCustsTabSection">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:10px">
            <div>
              <h4 style="margin:0;font-size:15px;font-weight:800;color:var(--text)">🏢 Deleted Whole Customers</h4>
              <p class="sub" style="margin:2px 0 0;font-size:12px">Entire customer accounts that were moved to the Recycle Bin. Restoring a customer brings back their account and all device records.</p>
            </div>
            <div class="cv-search-container" style="min-width:240px">
              <span class="cv-search-icon-left">🔎</span>
              <input id="cartCustSearchInput" class="cv-search-input" style="height:36px;font-size:13px" placeholder="Search customer name…" />
            </div>
          </div>
          <div id="cartCustsTableWrap">
            <div class="empty">Checking for deleted customers…</div>
          </div>
        </div>

        <!-- Section 2: Deleted Entries / Devices Tab -->
        <div id="cartDevsTabSection" hidden>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:10px">
            <div>
              <h4 style="margin:0;font-size:15px;font-weight:800;color:var(--text)">📱 Deleted Customer Entries &amp; Device Records</h4>
              <p class="sub" style="margin:2px 0 0;font-size:12px">Individual device records, SIM entries, and staged errored items that were placed into Cart.</p>
            </div>
            <div class="cv-search-container" style="min-width:280px">
              <span class="cv-search-icon-left">🔎</span>
              <input id="cartDevSearchInput" class="cv-search-input" style="height:36px;font-size:13px" placeholder="Search IMEI, customer name, serial number…" />
            </div>
          </div>
          <div id="cartDevsTableWrap">
            <div class="empty">Checking for deleted entries…</div>
          </div>
        </div>
      </div>
    `;

    // Hook search inputs
    const custSearch = document.getElementById('cartCustSearchInput');
    if (custSearch) {
      custSearch.oninput = () => renderCartCustsTable(allCartCusts);
    }
    const devSearch = document.getElementById('cartDevSearchInput');
    if (devSearch) {
      devSearch.oninput = () => renderCartDevsTable(allCartDevs);
    }

    // Hook Header Actions
    const btnRestoreAll = document.getElementById('btnRestoreAllCart');
    if (btnRestoreAll) {
      btnRestoreAll.onclick = restoreAllCartEntries;
    }
    const btnEmptyAll = document.getElementById('btnEmptyCartForever');
    if (btnEmptyAll) {
      btnEmptyAll.onclick = emptyEntireCartForever;
    }

    // Hook Table Delegations
    const custWrap = document.getElementById('cartCustsTableWrap');
    if (custWrap) {
      custWrap.onclick = handleCustCartAction;
    }
    const devWrap = document.getElementById('cartDevsTableWrap');
    if (devWrap) {
      devWrap.onclick = handleDevCartAction;
    }
  }

  window.openCartModal = async function () {
    window.location.href = 'cart.html';
  };

  window.closeCartModal = function () {
    const dlg = document.getElementById('dlgCartModal');
    if (dlg && dlg.open) {
      dlg.close();
    }
  };

  window.switchCartTab = function (tab) {
    currentTab = tab;
    const isCust = tab === 'custs';
    const tabCusts = document.getElementById('tabBtnCartCusts');
    const tabDevs = document.getElementById('tabBtnCartDevs');
    const secCusts = document.getElementById('cartCustsTabSection');
    const secDevs = document.getElementById('cartDevsTabSection');

    if (tabCusts) {
      tabCusts.style.borderBottom = isCust ? '3px solid var(--primary)' : '3px solid transparent';
      tabCusts.style.fontWeight = isCust ? '800' : '600';
      tabCusts.style.color = isCust ? 'var(--text)' : 'var(--muted)';
    }
    if (tabDevs) {
      tabDevs.style.borderBottom = !isCust ? '3px solid var(--primary)' : '3px solid transparent';
      tabDevs.style.fontWeight = !isCust ? '800' : '600';
      tabDevs.style.color = !isCust ? 'var(--text)' : 'var(--muted)';
    }
    if (secCusts) secCusts.hidden = !isCust;
    if (secDevs) secDevs.hidden = isCust;
  };

  window.loadCartContainer = async function () {
    try {
      const [devsRes, custsRes] = await Promise.all([
        window.api ? window.api('/api/bin').catch(() => []) : fetch('/api/bin').then(r => r.json()).catch(() => []),
        window.api ? window.api('/api/customers/bin').catch(() => []) : fetch('/api/customers/bin').then(r => r.json()).catch(() => [])
      ]);

      allCartDevs = Array.isArray(devsRes) ? devsRes : [];
      allCartCusts = Array.isArray(custsRes) ? custsRes : [];

      const totalItems = allCartDevs.length + allCartCusts.length;

      // Update badge counts across page headers
      const updateBadge = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = String(val);
      };
      updateBadge('cartTotalHeaderBadge', `${totalItems} Total Deleted`);
      updateBadge('headerCartCountBadge', totalItems);
      updateBadge('sidebarCartCountBadge', totalItems);
      updateBadge('topCartCountBadge', totalItems);
      updateBadge('cartCountBadge', totalItems);
      updateBadge('cartTabCountCusts', allCartCusts.length);
      updateBadge('cartTabCountDevs', allCartDevs.length);

      const errCount = allCartDevs.filter(d => (d.delete_reason || '').toLowerCase().includes('errored')).length;
      const devCount = allCartDevs.length - errCount;
      const custCount = allCartCusts.length;

      const tagCust = document.getElementById('cartStatCustTag');
      if (tagCust) tagCust.textContent = `🏢 Whole Customers: ${custCount}`;
      const tagDev = document.getElementById('cartStatDevTag');
      if (tagDev) tagDev.textContent = `📱 Customer Entries: ${devCount}`;
      const tagErr = document.getElementById('cartStatErrTag');
      if (tagErr) tagErr.textContent = `⚠️ Errored Entries: ${errCount}`;

      if (totalItems > 0) {
        const custPct = Math.round((custCount / totalItems) * 100);
        const devPct = Math.round((devCount / totalItems) * 100);
        const errPct = Math.max(0, 100 - custPct - devPct);

        const bCust = document.getElementById('cartBarCust');
        if (bCust) bCust.style.width = custPct + '%';
        const bDev = document.getElementById('cartBarDev');
        if (bDev) bDev.style.width = devPct + '%';
        const bErr = document.getElementById('cartBarErr');
        if (bErr) bErr.style.width = errPct + '%';
      }

      renderCartCustsTable(allCartCusts);
      renderCartDevsTable(allCartDevs);

      // Auto switch to non-empty tab if appropriate
      if (allCartCusts.length === 0 && allCartDevs.length > 0 && currentTab === 'custs') {
        window.switchCartTab('devs');
      } else if (allCartCusts.length > 0 && currentTab === 'custs') {
        window.switchCartTab('custs');
      }
    } catch (err) {
      console.warn('loadCartContainer notice:', err);
    }
  };

  function renderCartCustsTable(custs) {
    const wrap = document.getElementById('cartCustsTableWrap');
    if (!wrap) return;

    const q = (document.getElementById('cartCustSearchInput')?.value || '').trim().toLowerCase();
    const filtered = custs.filter(c => !q || (c.name || '').toLowerCase().includes(q));

    if (!filtered.length) {
      wrap.innerHTML = `
        <div class="empty" style="padding:28px;background:var(--card-subtle);border-radius:12px;border:1px dashed var(--line);text-align:center">
          <div style="font-size:28px;margin-bottom:6px">🏢</div>
          <b style="font-size:14px;color:var(--text);display:block">${q ? 'No deleted customers match your search.' : 'No whole customers currently in Cart.'}</b>
          <span style="font-size:12px;color:var(--muted)">All customer account portfolios are active.</span>
        </div>
      `;
      return;
    }

    wrap.innerHTML = `
      <div class="tw" style="max-height:50vh;overflow:auto;border:1px solid var(--line);border-radius:12px">
        <table style="width:100%;font-size:13px;border-collapse:collapse">
          <thead>
            <tr style="background:var(--card-subtle);text-align:left;position:sticky;top:0;z-index:5">
              <th style="padding:10px 14px">Customer Portfolio</th>
              <th style="padding:10px 14px">Associated Records</th>
              <th style="padding:10px 14px">Deleted On</th>
              <th style="padding:10px 14px">Deleted By</th>
              <th style="padding:10px 14px;text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.map(c => `
              <tr style="border-top:1px solid var(--line);transition:background 0.15s ease">
                <td style="padding:12px 14px">
                  <div style="display:flex;align-items:center;gap:10px">
                    <span style="font-size:18px">🏢</span>
                    <div>
                      <b style="font-size:13.5px;color:var(--text);display:block">${E(c.name)}</b>
                      <span style="font-size:11px;color:var(--muted)">Customer ID #${c.id}</span>
                    </div>
                  </div>
                </td>
                <td style="padding:12px 14px">
                  <span class="tag mut" style="font-weight:700">${Number(c.devices || 0).toLocaleString()} records</span>
                </td>
                <td style="padding:12px 14px;color:var(--muted);font-size:12px">
                  ${E((c.deleted_at || '').slice(0, 19).replace('T', ' '))}
                </td>
                <td style="padding:12px 14px;font-family:monospace;font-size:12px">
                  <code>${E(c.deleted_by || '—')}</code>
                </td>
                <td style="padding:12px 14px;text-align:right">
                  <div style="display:inline-flex;gap:6px">
                    <button class="b" type="button" data-res-cust="${c.id}" data-name="${E(c.name)}" style="height:30px;padding:0 12px;font-size:12px;font-weight:700" title="Restore customer and associated device records">
                      🔄 Restore Customer
                    </button>
                    <button class="b d" type="button" data-purge-cust="${c.id}" data-name="${E(c.name)}" style="height:30px;padding:0 12px;font-size:12px;font-weight:700" title="Permanently delete customer and drop table">
                      🗑️ Delete Forever
                    </button>
                  </div>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderCartDevsTable(devs) {
    const wrap = document.getElementById('cartDevsTableWrap');
    if (!wrap) return;

    const q = (document.getElementById('cartDevSearchInput')?.value || '').trim().toLowerCase();
    const filtered = devs.filter(d => {
      if (!q) return true;
      return (d.imei || '').toLowerCase().includes(q) ||
             (d.customer_name || '').toLowerCase().includes(q) ||
             (d.device_sr_no || '').toLowerCase().includes(q) ||
             (d.iccid || '').toLowerCase().includes(q) ||
             (d.msisdn1 || '').toLowerCase().includes(q) ||
             (d.delete_reason || '').toLowerCase().includes(q);
    });

    if (!filtered.length) {
      wrap.innerHTML = `
        <div class="empty" style="padding:28px;background:var(--card-subtle);border-radius:12px;border:1px dashed var(--line);text-align:center">
          <div style="font-size:28px;margin-bottom:6px">📱</div>
          <b style="font-size:14px;color:var(--text);display:block">${q ? 'No deleted entries match your search.' : 'Cart is empty. No deleted customer entries or device records.'}</b>
          <span style="font-size:12px;color:var(--muted)">All active inventory records are currently active and available.</span>
        </div>
      `;
      return;
    }

    wrap.innerHTML = `
      <div class="tw" style="max-height:50vh;overflow:auto;border:1px solid var(--line);border-radius:12px">
        <table style="width:100%;font-size:12.5px;border-collapse:collapse">
          <thead>
            <tr style="background:var(--card-subtle);text-align:left;position:sticky;top:0;z-index:5">
              <th style="padding:10px 12px">IMEI (15-Digit)</th>
              <th style="padding:10px 12px">Customer Name</th>
              <th style="padding:10px 12px">Serial No</th>
              <th style="padding:10px 12px">ICCID</th>
              <th style="padding:10px 12px">MSISDN1</th>
              <th style="padding:10px 12px">Deleted On</th>
              <th style="padding:10px 12px">Deleted By</th>
              <th style="padding:10px 12px">Reason</th>
              <th style="padding:10px 12px;text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.slice(0, 500).map(d => {
              const isErr = (d.delete_reason || '').toLowerCase().includes('errored');
              return `
                <tr style="border-top:1px solid var(--line);transition:background 0.15s ease">
                  <td style="padding:10px 12px;font-family:monospace;font-weight:700">
                    <span>${isErr ? '⚠️ ' : '📱 '}${E(d.imei || '—')}</span>
                  </td>
                  <td style="padding:10px 12px">
                    <b>${E(d.customer_name || '—')}</b>
                  </td>
                  <td style="padding:10px 12px;font-family:monospace;font-size:12px">${E(d.device_sr_no || '—')}</td>
                  <td style="padding:10px 12px;font-family:monospace;font-size:12px">${E(d.iccid || '—')}</td>
                  <td style="padding:10px 12px;font-family:monospace;font-size:12px">${E(d.msisdn1 || '—')}</td>
                  <td style="padding:10px 12px;color:var(--muted);font-size:11.5px">
                    ${E((d.deleted_at || '').slice(0, 19).replace('T', ' '))}
                  </td>
                  <td style="padding:10px 12px;font-family:monospace;font-size:11.5px">
                    <code>${E(d.deleted_by || '—')}</code>
                  </td>
                  <td style="padding:10px 12px;max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${E(d.delete_reason || '')}">
                    <span class="sub" style="font-size:11.5px;color:var(--muted)">${E(d.delete_reason || 'Manual delete')}</span>
                  </td>
                  <td style="padding:10px 12px;text-align:right">
                    <div style="display:inline-flex;gap:6px">
                      <button class="b" type="button" data-res-dev="${d.id}" data-imei="${E(d.imei)}" style="height:28px;padding:0 10px;font-size:11.5px;font-weight:700" title="Restore this record back to active inventory">
                        🔄 Restore
                      </button>
                      <button class="b d" type="button" data-purge-dev="${d.id}" data-imei="${E(d.imei)}" style="height:28px;padding:0 10px;font-size:11.5px;font-weight:700" title="Permanently erase this record forever">
                        🗑️ Delete
                      </button>
                    </div>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
        ${filtered.length > 500 ? `<div style="padding:8px 14px;text-align:center;font-size:12px;color:var(--muted);background:var(--card-subtle)">Showing first 500 of ${filtered.length} matching entries. Use the search box above to narrow records.</div>` : ''}
      </div>
    `;
  }

  async function handleCustCartAction(e) {
    const btn = e.target.closest('[data-res-cust],[data-purge-cust]');
    if (!btn) return;
    const isPurge = btn.hasAttribute('data-purge-cust');
    const cid = btn.getAttribute(isPurge ? 'data-purge-cust' : 'data-res-cust');
    const custName = btn.dataset.name || `Customer #${cid}`;

    try {
      if (isPurge) {
        const ok = window.cv && window.cv.confirm
          ? await window.cv.confirm(`Are you sure you want to permanently delete customer "${custName}" and all associated data records from the database and TiDB Cloud?\n\nThis cannot be undone.`, {
              title: 'Delete Customer Forever?',
              ok: 'Delete Forever',
              tone: 'danger'
            })
          : confirm(`Permanently delete customer "${custName}" forever?`);
        if (!ok) return;

        btn.disabled = true;
        btn.textContent = 'Purging…';
        if (window.api) {
          await window.api(`/api/customers/${cid}/purge`, { method: 'DELETE' });
        } else {
          await fetch(`/api/customers/${cid}/purge`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
        }
        if (window.cv && window.cv.toast) {
          window.cv.toast(`Customer "${custName}" permanently deleted`, 'ok');
        }
      } else {
        btn.disabled = true;
        btn.textContent = 'Restoring…';
        if (window.api) {
          await window.api(`/api/customers/${cid}/restore`, { method: 'POST' });
        } else {
          await fetch(`/api/customers/${cid}/restore`, { method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
        }
        if (window.cv && window.cv.toast) {
          window.cv.toast(`Customer "${custName}" restored to active inventory!`, 'ok');
        }
      }

      await window.loadCartContainer();
      if (typeof window.updateChrome === 'function') await window.updateChrome();
      if (typeof window.loadCU === 'function') await window.loadCU();
    } catch (err) {
      btn.disabled = false;
      const msg = err.message || 'Operation failed';
      if (window.cv && window.cv.alert) {
        window.cv.alert(msg, { title: 'Action Failed', tone: 'danger' });
      } else {
        alert(msg);
      }
    }
  }

  async function handleDevCartAction(e) {
    const btn = e.target.closest('[data-res-dev],[data-purge-dev]');
    if (!btn) return;
    const isPurge = btn.hasAttribute('data-purge-dev');
    const id = btn.getAttribute(isPurge ? 'data-purge-dev' : 'data-res-dev');
    const imei = btn.dataset.imei || `Device #${id}`;

    try {
      if (isPurge) {
        const ok = window.cv && window.cv.confirm
          ? await window.cv.confirm(`Record with IMEI "${imei}" will be deleted forever from the database and cannot be recovered.`, {
              title: 'Delete Forever?',
              ok: 'Delete Forever',
              tone: 'danger'
            })
          : confirm(`Delete record "${imei}" forever?`);
        if (!ok) return;

        btn.disabled = true;
        if (window.api) {
          await window.api(`/api/bin/${id}`, { method: 'DELETE' });
        } else {
          await fetch(`/api/bin/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
        }
        if (window.cv && window.cv.toast) {
          window.cv.toast(`Record (${imei}) permanently deleted`, 'ok');
        }
      } else {
        btn.disabled = true;
        if (window.api) {
          await window.api(`/api/bin/${id}/restore`, { method: 'POST' });
        } else {
          await fetch(`/api/bin/${id}/restore`, { method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
        }
        if (window.cv && window.cv.toast) {
          window.cv.toast(`Record (${imei}) restored to inventory`, 'ok');
        }
      }

      await window.loadCartContainer();
      if (typeof window.updateChrome === 'function') await window.updateChrome();
    } catch (err) {
      btn.disabled = false;
      const msg = err.message || 'Operation failed';
      if (window.cv && window.cv.alert) {
        window.cv.alert(msg, { title: 'Action Failed', tone: 'danger' });
      } else {
        alert(msg);
      }
    }
  }

  async function restoreAllCartEntries() {
    const total = allCartDevs.length;
    if (!total) {
      if (window.cv && window.cv.toast) {
        window.cv.toast('No deleted entries in the cart to restore.', 'info');
      }
      return;
    }

    const ok = window.cv && window.cv.confirm
      ? await window.cv.confirm(`Are you sure you want to restore all ${total.toLocaleString()} deleted customer entries back to active inventory?`, {
          title: 'Restore All Records?',
          ok: 'Restore All'
        })
      : confirm(`Restore all ${total} entries to active inventory?`);
    if (!ok) return;

    try {
      const btn = document.getElementById('btnRestoreAllCart');
      if (btn) { btn.disabled = true; btn.textContent = 'Restoring…'; }

      let res;
      if (window.api) {
        res = await window.api('/api/bin/restore-all', { method: 'POST' });
      } else {
        res = await fetch('/api/bin/restore-all', { method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }).then(r => r.json());
      }

      if (window.cv && window.cv.toast) {
        window.cv.toast(res.message || `Successfully restored ${res.restored || total} records!`, 'ok');
      }
      await window.loadCartContainer();
      if (typeof window.updateChrome === 'function') await window.updateChrome();
    } catch (err) {
      if (window.cv && window.cv.alert) {
        window.cv.alert(err.message || 'Failed to restore all entries', { title: 'Restore Failed', tone: 'danger' });
      }
    } finally {
      const btn = document.getElementById('btnRestoreAllCart');
      if (btn) { btn.disabled = false; btn.textContent = '🔄 Restore All Entries'; }
    }
  }

  async function emptyEntireCartForever() {
    const totalCusts = allCartCusts.length;
    const totalDevs = allCartDevs.length;
    const grandTotal = totalCusts + totalDevs;

    if (!grandTotal) {
      if (window.cv && window.cv.toast) {
        window.cv.toast('Cart is already empty.', 'info');
      }
      return;
    }

    const ok = window.cv && window.cv.confirm
      ? await window.cv.confirm(`⚠️ PERMANENT PURGE WARNING:\n\nYou are about to permanently erase all ${grandTotal.toLocaleString()} items in the Cart (${totalCusts} whole customer portfolios and ${totalDevs} entries).\n\nThis will drop all customer tables and permanently delete every record from the database and cloud storage forever.\n\nType "EMPTY" to proceed.`, {
          title: 'Permanently Empty Cart Forever?',
          ok: 'Empty Cart Forever',
          tone: 'danger',
          typeToConfirm: 'EMPTY'
        })
      : confirm(`Permanently empty entire cart (${grandTotal} items)? This cannot be undone.`);
    if (!ok) return;

    try {
      const btn = document.getElementById('btnEmptyCartForever');
      if (btn) { btn.disabled = true; btn.textContent = 'Emptying…'; }

      let res;
      if (window.api) {
        res = await window.api('/api/bin', { method: 'DELETE' });
      } else {
        res = await fetch('/api/bin', { method: 'DELETE', headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }).then(r => r.json());
      }

      if (window.cv && window.cv.toast) {
        window.cv.toast(`Cart permanently emptied! Deleted ${res.deleted_forever || grandTotal} items forever.`, 'ok');
      }
      await window.loadCartContainer();
      if (typeof window.updateChrome === 'function') await window.updateChrome();
      if (typeof window.loadCU === 'function') await window.loadCU();
    } catch (err) {
      if (window.cv && window.cv.alert) {
        window.cv.alert(err.message || 'Failed to empty cart', { title: 'Empty Cart Failed', tone: 'danger' });
      }
    } finally {
      const btn = document.getElementById('btnEmptyCartForever');
      if (btn) { btn.disabled = false; btn.textContent = '🗑️ Empty Cart Forever'; }
    }
  }

  // Auto-init on page load
  const bootCart = () => {
    window.loadCartContainer();
    // Check hash for direct cart opening
    if (window.location.hash === '#cart' || window.location.hash === '#box-bin' || window.location.search.includes('cart')) {
      setTimeout(() => window.openCartModal(), 200);
    }
  };

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    bootCart();
  } else {
    document.addEventListener('DOMContentLoaded', bootCart);
  }
})();

