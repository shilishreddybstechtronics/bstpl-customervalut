/* CustomerVault Modern Popups & Modals: confirm / alert / toast / pickColumns */
(function () {
  const E = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const ICON = {
    danger: '🗑️',
    err: '⚠️',
    warn: '⚠️',
    ok: '✅',
    info: 'ℹ️'
  };

  function open(html, { tone = 'info', wide = false, onKey } = {}) {
    return new Promise(res => {
      const back = document.createElement('div');
      back.className = 'cvp-back';
      back.innerHTML = `<div class="cvp-box ${tone} ${wide ? 'wide' : ''}" role="dialog" aria-modal="true">${html}</div>`;
      const prev = document.activeElement;
      const close = v => {
        back.remove();
        document.removeEventListener('keydown', kd, true);
        prev && prev.focus && prev.focus();
        res(v);
      };
      const kd = e => {
        if (e.key === 'Escape') {
          e.stopPropagation();
          close(null);
        }
      };
      document.addEventListener('keydown', kd, true);
      back.addEventListener('mousedown', e => {
        if (e.target === back) close(null);
      });
      document.body.appendChild(back);
      const focusTarget = back.querySelector('[data-focus]') || back.querySelector('.cvp-btn.main') || back.querySelector('button');
      if (focusTarget) focusTarget.focus();
      back._close = close;
      back.querySelectorAll('[data-act]').forEach(b => b.onclick = () => close(b.dataset.act));
      if (onKey) onKey(back, close);
    });
  }

  // WHAT IS HAPPENING BELOW:
  // Standard Popup Header with BSTPL Company Logo Badge:
  // Renders the official BSTPL corporate logo in every confirm, alert, prompt, and custom modal.
  const head = (t, tone, icon) => `
    <div class="cvp-head">
      <div class="cvp-logo-wrap" style="width:48px;height:48px;border-radius:12px;background:#ffffff;border:1.5px solid var(--line, #cbd5e1);display:flex;align-items:center;justify-content:center;padding:3px;box-shadow:0 3px 8px rgba(0,0,0,0.06);position:relative;flex-shrink:0">
        <img src="logo.svg" onerror="this.src=\'logo.png\'" alt="BSTPL Logo" style="width:100%;height:100%;object-fit:contain;border-radius:8px" />
        <span style="position:absolute;bottom:-4px;right:-4px;font-size:12px;background:var(--card,#ffffff);border:1.5px solid var(--line,#cbd5e1);border-radius:50%;width:19px;height:19px;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 3px rgba(0,0,0,0.15);line-height:1">${icon || ICON[tone] || ICON.info}</span>
      </div>
      <h3 class="cvp-title">${E(t)}</h3>
    </div>
  `;

  const cv = window.cv = window.cv || {};

  cv.alert = (msg, { title = 'Notice', tone = 'info' } = {}) =>
    open(head(title, tone) + `
      <div class="cvp-body">${E(msg)}</div>
      <div class="cvp-foot">
        <button class="cvp-btn main" data-act="ok" data-focus>Acknowledge</button>
      </div>
    `, { tone }).then(() => true);

  cv.confirm = (msg, o = {}) => {
    const perm = /permanent|forever|cannot be recovered/i.test(msg);
    const cart = /to cart|recycle bin/i.test(msg);
    let {
      title = perm ? 'Delete permanently?' : cart ? 'Move to Cart?' : 'Please confirm',
      ok = perm ? 'Delete forever' : cart ? 'Move to Cart' : 'Confirm',
      cancel = 'Cancel',
      tone = perm ? 'danger' : cart ? 'warn' : 'warn',
      typeToConfirm = '',
      icon = ''
    } = o;

    msg = String(msg).replace(/^\s*⚠️\s*PERMANENT DELETION WARNING:\s*/i, '');
    const typed = typeToConfirm ? `<input class="cvp-type" placeholder='Type "${E(typeToConfirm)}" to continue' aria-label="Confirmation text">` : '';

    return open(head(title, tone, icon) + `
      <div class="cvp-body">${E(msg)}</div>
      ${typed}
      <div class="cvp-foot">
        <button class="cvp-btn" data-act="no">${E(cancel)}</button>
        <button class="cvp-btn main" data-act="yes" ${typeToConfirm ? 'disabled' : 'data-focus'}>${E(ok)}</button>
      </div>
    `, {
      tone,
      onKey: (b) => {
        const i = b.querySelector('.cvp-type');
        const y = b.querySelector('[data-act=yes]');
        if (i && y) {
          i.oninput = () => {
            y.disabled = i.value.trim().toUpperCase() !== typeToConfirm.toUpperCase();
          };
        }
      }
    }).then(v => v === 'yes');
  };

  cv.toast = (msg, tone = 'ok', ms = 3000) => {
    let box = document.querySelector('.cvp-toasts');
    if (!box) {
      box = document.createElement('div');
      box.className = 'cvp-toasts';
      box.setAttribute('role', 'status');
      box.setAttribute('aria-live', 'polite');
      document.body.appendChild(box);
    }
    const t = document.createElement('div');
    const cleanTone = tone === 'err' || tone === 'danger' ? 'danger' : tone === 'warn' ? 'warn' : tone === 'info' ? 'info' : 'ok';
    t.className = 'cvp-toast ' + cleanTone;
    t.innerHTML = `<img src="logo.svg" onerror="this.src=\'logo.png\'" alt="BSTPL Logo" style="width:20px;height:20px;object-fit:contain;border-radius:4px;background:#ffffff;padding:1px;margin-right:2px;flex-shrink:0" /><span>${ICON[cleanTone] || ICON.ok}</span><span>${E(msg)}</span>`;
    box.appendChild(t);

    setTimeout(() => {
      t.classList.add('hide');
      setTimeout(() => t.remove(), 260);
    }, ms);
  };

  /* Column picker */
  cv.pickColumns = (cols, { title = 'Choose columns', sub = 'Only the selected columns will be fetched.', ok = 'Fetch data', preselect } = {}) => {
    const sel = new Set(preselect || cols.map(c => c.key));
    const list = () => cols.map(c => `
      <label class="cvp-opt" data-l="${E(c.label.toLowerCase())}">
        <input type="checkbox" value="${E(c.key)}" ${sel.has(c.key) ? 'checked' : ''}>
        ${E(c.label)}
      </label>
    `).join('');

    return open(head(title, 'info') + `
      <div class="cvp-body">${E(sub)}</div>
      <div class="cvp-tools">
        <input type="search" placeholder="Search columns…" aria-label="Search columns">
        <button class="cvp-btn" type="button" data-t="all">Select all</button>
        <button class="cvp-btn" type="button" data-t="none">Clear</button>
      </div>
      <div class="cvp-cols">${list()}</div>
      <div class="cvp-foot">
        <span class="cvp-body" style="padding:0;margin-right:auto;font-weight:700" id="cvpCount"></span>
        <button class="cvp-btn" type="button" data-act="no">Cancel</button>
        <button class="cvp-btn main" type="button" data-act="go">${E(ok)}</button>
      </div>
    `, {
      wide: true,
      onKey: (b, close) => {
        const cnt = () => {
          const n = b.querySelectorAll('.cvp-cols input:checked').length;
          b.querySelector('#cvpCount').textContent = `${n} of ${cols.length} selected`;
          b.querySelector('[data-act=go]').disabled = !n;
        };
        b.addEventListener('change', cnt);
        cnt();
        b.querySelector('input[type=search]').oninput = e => {
          const q = e.target.value.toLowerCase();
          b.querySelectorAll('.cvp-opt').forEach(o => o.hidden = !o.dataset.l.includes(q));
        };
        b.querySelectorAll('[data-t]').forEach(x => x.onclick = () => {
          b.querySelectorAll('.cvp-opt:not([hidden]) input').forEach(i => i.checked = x.dataset.t === 'all');
          cnt();
        });
        const noBtn = b.querySelector('[data-act=no]');
        if (noBtn) noBtn.onclick = (e) => { e.stopPropagation(); close(null); };
        const goBtn = b.querySelector('[data-act=go]');
        if (goBtn) goBtn.onclick = (e) => {
          e.stopPropagation();
          const selected = [...b.querySelectorAll('.cvp-cols input:checked')].map(i => i.value);
          close(selected.length ? selected : null);
        };
      }
    });
  };


  /* Text prompt: replaces window.prompt(). Resolves to the typed text, or null when cancelled. */
  cv.prompt = (msg, { title = 'Enter a value', value = '', placeholder = '', ok = 'Save', cancel = 'Cancel', icon = '✏️', tone = 'info', validate } = {}) =>
    open(head(title, tone, icon) + `
      <div class="cvp-body">${E(msg)}</div>
      <input class="cvp-input" type="text" value="${E(value)}" placeholder="${E(placeholder)}" aria-label="${E(title)}" data-focus>
      <div class="cvp-err" role="alert" hidden></div>
      <div class="cvp-foot">
        <button class="cvp-btn" type="button" data-act="no">${E(cancel)}</button>
        <button class="cvp-btn main" type="button" data-act="yes">${E(ok)}</button>
      </div>
    `, {
      tone,
      onKey: (b, close) => {
        const i = b.querySelector('.cvp-input'), y = b.querySelector('[data-act=yes]'), er = b.querySelector('.cvp-err');
        i.focus(); i.select();
        const submit = () => {
          const v = i.value.trim();
          const bad = validate ? validate(v) : (v ? '' : 'Please enter a value.');
          if (bad) { er.textContent = bad; er.hidden = false; i.classList.add('bad'); i.focus(); return; }
          close(v);
        };
        y.onclick = e => { e.stopPropagation(); submit(); };
        i.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); submit(); } };
        i.oninput = () => { er.hidden = true; i.classList.remove('bad'); };
      }
    }).then(v => (v === 'no' ? null : v));

  /* Copy box: shows long text in a selectable area with a Copy button (replaces prompt() used as a clipboard fallback). */
  cv.copyBox = (text, { title = 'Copy text', sub = '' } = {}) =>
    open(head(title, 'info', '📋') + `
      ${sub ? `<div class="cvp-body">${E(sub)}</div>` : ''}
      <textarea class="cvp-area" readonly data-focus>${E(text)}</textarea>
      <div class="cvp-foot">
        <button class="cvp-btn" type="button" data-act="ok">Close</button>
        <button class="cvp-btn main" type="button" data-copy>Copy</button>
      </div>
    `, {
      wide: true,
      onKey: (b) => {
        const ta = b.querySelector('.cvp-area'); ta.select();
        b.querySelector('[data-copy]').onclick = async (e) => {
          e.stopPropagation();
          ta.select();
          try { await navigator.clipboard.writeText(text); } catch (_) { try { document.execCommand('copy'); } catch (__) {} }
          cv.toast('Copied to clipboard', 'ok');
        };
      }
    }).then(() => true);

  /* Intercept standard alert and toast */
  window.alert = m => { cv.alert(m); };
  if (!window.toast || typeof window.toast !== 'function') {
    window.toast = (m, tone) => { cv.toast(m, tone); };
  }
})();

// Auto-load Cart Modal controller
if (!window.openCartModal) {
  const s = document.createElement('script');
  s.src = 'cart-modal.js';
  document.head.appendChild(s);
}

  // =========================================================================
  // WHAT IS HAPPENING BELOW:
  // Universal BSTPL Logo Decorator for all modal dialogs (<dialog> and .modal-card):
  // Automatically ensures every popup across the application has the BSTPL company logo visibly displayed in its header.
  // =========================================================================
  function decorateDialogLogos() {
    try {
      document.querySelectorAll('dialog').forEach(dlg => {
        if (dlg.dataset.logoDecorated) return;
        
        // Check if dialog already contains a logo image
        if (dlg.querySelector('img[src*="logo"]')) {
          dlg.dataset.logoDecorated = 'true';
          return;
        }

        // Find the title element inside the dialog (h2, h3, or modal header)
        const titleEl = dlg.querySelector('h2, h3, .modal-title, .dlg-title');
        if (titleEl) {
          dlg.dataset.logoDecorated = 'true';
          const logoWrap = document.createElement('span');
          logoWrap.className = 'cv-dialog-brand-logo';
          logoWrap.style.cssText = 'display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:8px;background:#ffffff;border:1.5px solid var(--line,#cbd5e1);padding:2px;box-shadow:0 2px 6px rgba(0,0,0,0.06);margin-right:10px;vertical-align:middle;flex-shrink:0';
          logoWrap.innerHTML = '<img src="logo.svg" onerror="this.src=\'logo.png\'" alt="BSTPL Logo" style="width:100%;height:100%;object-fit:contain;border-radius:6px" />';
          
          titleEl.style.display = 'inline-flex';
          titleEl.style.alignItems = 'center';
          titleEl.insertBefore(logoWrap, titleEl.firstChild);
        }
      });
    } catch(e) {
      console.warn('Dialog logo decoration warning:', e);
    }
  }

  // Run on DOM load and observe dynamic dialog insertions
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', decorateDialogLogos);
  } else {
    decorateDialogLogos();
  }

  // Also hook into HTMLDialogElement.prototype.showModal
  if (typeof HTMLDialogElement !== 'undefined' && HTMLDialogElement.prototype.showModal) {
    const origShowModal = HTMLDialogElement.prototype.showModal;
    HTMLDialogElement.prototype.showModal = function() {
      decorateDialogLogos();
      return origShowModal.apply(this, arguments);
    };
  }

  // Hook into window.openModal if present
  const origOpenModal = window.openModal;
  window.openModal = function(id) {
    decorateDialogLogos();
    if (typeof origOpenModal === 'function') return origOpenModal(id);
    const dlg = typeof id === 'string' ? document.getElementById(id) : id;
    if (dlg && typeof dlg.showModal === 'function') dlg.showModal();
  };

  // =========================================================================
  // 3D PAGE TRANSITION ENGINE & TACTILE DEPTH CONTROLLER
  // =========================================================================
  (function init3DPageTransitions() {
    // Reset exit animation when page is revealed (handles back/forward bfcache)
    window.addEventListener('pageshow', function () {
      document.body.classList.remove('cv-page-3d-exit');
    });

    document.addEventListener('click', function (e) {
      // 1. Tactile 3D feedback for Home Toggle button
      const homeBtn = e.target.closest('#sidebarToggleHomeBtn, .cv-home-nav-btn');
      if (homeBtn) {
        homeBtn.classList.add('cv-3d-pressed');
        setTimeout(() => homeBtn.classList.remove('cv-3d-pressed'), 180);
      }

      // 1b. Tactile 3D feedback for BSTPL Company Symbol / Brand
      const brandLogo = e.target.closest('.header-bstpl-brand, .cv-sidebar-brand, #headerBstplBrand, #sidebarBstplBrand');
      if (brandLogo) {
        brandLogo.classList.add('cv-3d-pressed');
        setTimeout(() => brandLogo.classList.remove('cv-3d-pressed'), 200);
      }

      // 2. Smooth 3D Page Transitions between pages
      const link = e.target.closest('a[href]');

      // Dynamic bidirectional navigation for BSTPL Brand Symbol (Home / Inventory <-> Settings)
      const currentPath = (window.location.pathname.split('/').pop() || 'home.html').toLowerCase();
      if (brandLogo) {
        let dest = 'settings.html';
        if (currentPath === 'settings.html') {
          dest = sessionStorage.getItem('last_home_inv_page') || 'home.html';
        } else {
          sessionStorage.setItem('last_home_inv_page', currentPath || 'home.html');
          dest = 'settings.html';
        }
        if (link) {
          link.setAttribute('href', dest);
        } else {
          // Brand symbol was clicked as non-anchor container
          const targetPath = (dest.split('?')[0].split('#')[0].split('/').pop() || '').toLowerCase();
          if (targetPath !== currentPath) {
            e.preventDefault();
            document.body.classList.add('cv-page-3d-exit');
            setTimeout(function () {
              window.location.href = dest;
            }, 160);
            return;
          }
        }
      }

      if (!link) return;

      const href = link.getAttribute('href');
      // Skip anchors, javascript, external sites, target="_blank", or modifier-clicks
      if (!href || href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('mailto:') || href.startsWith('tel:')) return;
      if (link.target === '_blank' || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
      if (href.startsWith('http://') || href.startsWith('https://')) {
        if (!href.startsWith(window.location.origin)) return;
      }

      // If user clicked link to current page, don't trigger exit animation
      const targetPath = (href.split('?')[0].split('#')[0].split('/').pop() || '').toLowerCase();
      if (targetPath === currentPath) return;

      // Trigger 3D Exit Animation on the leaving page before navigating
      e.preventDefault();
      document.body.classList.add('cv-page-3d-exit');
      setTimeout(function () {
        window.location.href = href;
      }, 160);
    });
  })();

  // =========================================================================
  // UNIVERSAL NAVIGATION SIDEBAR & TOP HEADER CONTROLLER
  // (Full-Page Open on Nav Selection, Page-Specific Toggle Icons & Universal Header)
  // =========================================================================
  const PAGE_CONFIG = {
    'home.html': {
      title: 'Home Overview',
      btnTitle: 'Toggle Navigation Sidebar (Home Overview)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><path d="M3 10.5L12 3l9 7.5V20a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>'
    },
    'dashboard.html': {
      title: 'Home Overview',
      btnTitle: 'Toggle Navigation Sidebar (Home Overview)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><path d="M3 10.5L12 3l9 7.5V20a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>'
    },
    'inventory.html': {
      title: 'Customer Inventory',
      btnTitle: 'Toggle Navigation Sidebar (Customer Inventory)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect><path d="M9 14l2 2 4-4"></path></svg>'
    },
    'fetch-data.html': {
      title: 'Fetch Data',
      btnTitle: 'Toggle Navigation Sidebar (Fetch Data)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
    },
    'edit-delete.html': {
      title: 'Edit / Delete by IMEI',
      btnTitle: 'Toggle Navigation Sidebar (Edit / Delete)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>'
    },
    'sim-upload.html': {
      title: 'SIM Data Upload',
      btnTitle: 'Toggle Navigation Sidebar (SIM Upload)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>'
    },
    'alerts.html': {
      title: 'SIM Expiry Alerts',
      btnTitle: 'Toggle Navigation Sidebar (Expiry Alerts)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
    },
    'errors.html': {
      title: 'Errored Entries',
      btnTitle: 'Toggle Navigation Sidebar (Errored Entries)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
    },
    'cart.html': {
      title: 'Cart & Recycle Bin',
      btnTitle: 'Toggle Navigation Sidebar (Cart)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>'
    },
    'settings.html': {
      title: 'User Settings & Preferences',
      btnTitle: 'Toggle Navigation Sidebar (Settings)',
      svg: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display:block"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'
    }
  };

  function getCurrentPageName() {
    const p = (window.location.pathname.split('/').pop() || 'home.html').toLowerCase();
    return p || 'home.html';
  }

  function setSidebarOpen(open) {
    if (open) {
      document.body.classList.add('sidebar-open');
    } else {
      document.body.classList.remove('sidebar-open');
    }
    const btn = document.getElementById('sidebarToggleHomeBtn') || document.querySelector('.cv-home-nav-btn');
    if (btn) {
      const curPage = getCurrentPageName();
      const cfg = PAGE_CONFIG[curPage] || PAGE_CONFIG['home.html'];
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.setAttribute('title', open ? `Close Navigation Sidebar (${cfg.title})` : cfg.btnTitle);
      btn.classList.toggle('is-active', open);
    }
    try { localStorage.setItem('cv_sidebar_open', open ? 'true' : 'false'); } catch (e) { }
  }
  window.setSidebarOpen = setSidebarOpen;

  function toggleSidebar() {
    const isOpen = document.body.classList.toggle('sidebar-open');
    const btn = document.getElementById('sidebarToggleHomeBtn') || document.querySelector('.cv-home-nav-btn');
    if (btn) {
      const curPage = getCurrentPageName();
      const cfg = PAGE_CONFIG[curPage] || PAGE_CONFIG['home.html'];
      btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      btn.setAttribute('title', isOpen ? `Close Navigation Sidebar (${cfg.title})` : cfg.btnTitle);
      btn.classList.toggle('is-active', isOpen);
    }
    try { localStorage.setItem('cv_sidebar_open', isOpen ? 'true' : 'false'); } catch (e) { }
    return isOpen;
  }
  window.toggleSidebar = toggleSidebar;

  function updateUniversalUserGreeting() {
    try {
      let u = null;
      try {
        u = JSON.parse(localStorage.getItem('currentUser') || localStorage.getItem('user') || sessionStorage.getItem('currentUser') || sessionStorage.getItem('user') || 'null');
      } catch (e) { }
      const now = new Date();
      const h = now.getHours();
      let greet = 'Good morning';
      if (h >= 12 && h < 17) greet = 'Good afternoon';
      else if (h >= 17) greet = 'Good evening';

      const dispName = (u && (u.name || u.user_id || u.username)) ? (u.name || u.user_id || u.username) : 'Shilish Reddy';
      const hiEl = document.getElementById('hi');
      if (hiEl) hiEl.textContent = `${greet}, ${dispName}`;

      const firstLetter = (dispName.charAt(0) || 'S').toUpperCase();
      const avEl = document.getElementById('userAvatarCircle');
      if (avEl) avEl.textContent = firstLetter;

      const r = (u && (u.role || (u.is_admin ? 'admin' : 'standard'))) ? String(u.role || (u.is_admin ? 'admin' : 'standard')).toUpperCase() : 'ADMIN';
      const roleEl = document.getElementById('rolePill');
      if (roleEl) {
        roleEl.textContent = r;
        roleEl.className = `role-pill ${r.toLowerCase().includes('admin') ? 'admin' : 'standard'}`;
      }
    } catch (e) {
      console.warn('Greeting update warning:', e);
    }
  }
  window.updateUniversalUserGreeting = updateUniversalUserGreeting;

  function syncTopHeaderPageIcon() {
    try {
      const curPage = getCurrentPageName();
      const cfg = PAGE_CONFIG[curPage] || PAGE_CONFIG['home.html'];
      const btn = document.getElementById('sidebarToggleHomeBtn') || document.querySelector('.cv-home-nav-btn');
      if (btn) {
        btn.setAttribute('aria-label', `Toggle Navigation Sidebar (${cfg.title})`);
        btn.setAttribute('title', cfg.btnTitle);
        const iconSpan = btn.querySelector('.home-btn-icon');
        if (iconSpan && cfg.svg) {
          iconSpan.innerHTML = cfg.svg;
        }
      }
    } catch (e) { }
  }

  function initUniversalHeaderActions() {
    updateUniversalUserGreeting();
    syncTopHeaderPageIcon();

    // Sidebar state initialization:
    // On Home Overview (after login or direct navigation), Home Overview and the nav bar are visible!
    // On destination tool pages (Customer Inventory, Fetch Data, etc.), the page opens fully with sidebar closed.
    const curPage = getCurrentPageName();
    const isHomeOverview = (curPage === 'home.html' || curPage === 'dashboard.html');

    if (isHomeOverview) {
      setSidebarOpen(true);
    } else {
      setSidebarOpen(false);
    }

    // Wire #bNotifBell (Universal Notification Center)
    let bell = document.getElementById('bNotifBell');
    if (!bell && qs && qs.parentNode) {
      bell = document.createElement('button');
      bell.id = 'bNotifBell';
      bell.className = 'b cv-bell-btn';
      bell.title = 'System Notifications & Live Alerts';
      bell.innerHTML = `<span>🔔</span><span class="cv-bell-badge" id="cvBellBadge" style="display:none">0</span>`;
      qs.parentNode.insertBefore(bell, qs);
    }
    if (bell && !bell.dataset.universalBound) {
      bell.dataset.universalBound = 'true';
      bell.addEventListener('click', function (e) {
        e.preventDefault();
        openNotificationDrawer();
      });
      refreshNotificationBadge();
    }

    // Wire #bQs (Quick Search)
    const qs = document.getElementById('bQs');
    if (qs && !qs.dataset.universalBound) {
      qs.dataset.universalBound = 'true';
      qs.addEventListener('click', function (e) {
        if (window.cvCommandPalette && typeof window.cvCommandPalette.open === 'function') {
          e.preventDefault();
          window.cvCommandPalette.open();
          return;
        }
        const inp = document.querySelector('#liveSearchInput, #searchInput, #imeiInput, #invSearchInput, #q, #filterQ, input[type="search"]');
        if (inp) {
          e.preventDefault();
          inp.focus();
          inp.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else if (!window.location.pathname.endsWith('fetch-data.html') && !window.location.pathname.endsWith('inventory.html')) {
          window.location.href = 'inventory.html';
        }
      });
    }

    // Wire #bRefresh (Reload current data)
    const ref = document.getElementById('bRefresh');
    if (ref && !ref.dataset.universalBound) {
      ref.dataset.universalBound = 'true';
      ref.addEventListener('click', function (e) {
        if (window.location.pathname.endsWith('home.html') || window.location.pathname.endsWith('dashboard.html')) {
          return; // handled by page script
        }
        if (typeof window.toast === 'function') window.toast('Refreshing current data…');
        if (typeof window.refreshPageData === 'function') {
          window.refreshPageData();
        } else if (typeof window.loadData === 'function') {
          window.loadData();
        } else if (typeof window.loadInventory === 'function') {
          window.loadInventory();
        } else if (typeof window.loadOverviewData === 'function') {
          window.loadOverviewData();
        } else {
          window.location.reload();
        }
      });
    }

    // Wire #bAl (Toggle Expiry Alerts)
    const al = document.getElementById('bAl');
    if (al && !al.dataset.universalBound) {
      al.dataset.universalBound = 'true';
      al.addEventListener('click', function (e) {
        if (window.location.pathname.endsWith('home.html') || window.location.pathname.endsWith('dashboard.html')) {
          return; // handled by page script
        }
        window.location.href = 'alerts.html';
      });
    }

    // Wire #bLo (Logout)
    const lo = document.getElementById('bLo');
    if (lo && !lo.dataset.universalBound) {
      lo.dataset.universalBound = 'true';
      lo.addEventListener('click', function (e) {
        e.preventDefault();
        if (typeof window.logout === 'function') {
          window.logout(true);
        } else {
          universalLogout(true);
        }
      });
    }
  }

  async function universalLogout(confirmFirst = false) {
    if (confirmFirst && window.cv && typeof window.cv.confirm === 'function') {
      const ok = await window.cv.confirm('Are you sure you want to sign out of BSTPL CustomerVault?');
      if (!ok) return;
    }
    try {
      fetch('/api/logout', { method: 'POST' }).catch(() => {});
    } catch (e) {}
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('currentUser');
    sessionStorage.clear();
    window.location.href = 'login.html';
  }
  window.logout = window.logout || universalLogout;

  // Auto-close sidebar on tool navigation item selection so tools open fully,
  // but keep nav bar open when selecting Home Overview so Home Overview and nav bar are visible!
  document.addEventListener('click', function (e) {
    const navItem = e.target.closest('.cv-sidebar-menu a, .cv-nav-item');
    if (navItem) {
      const href = (navItem.getAttribute('href') || '').toLowerCase();
      const isNavigatingToHome = href.includes('home.html') || href.includes('dashboard.html');
      if (isNavigatingToHome) {
        setSidebarOpen(true);
        try {
          localStorage.setItem('cv_sidebar_open', 'true');
        } catch (err) { }
      } else {
        // Immediately close the sidebar so destination tool page opens fully
        setSidebarOpen(false);
        try {
          localStorage.setItem('cv_sidebar_open', 'false');
        } catch (err) { }
      }
    }
  }, true);

  // =========================================================================
  // UNIVERSAL NOTIFICATION CENTER & BADGE CONTROLLER
  // =========================================================================
  async function refreshNotificationBadge() {
    const badge = document.getElementById('cvBellBadge');
    if (!badge) return;
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const res = await fetch('/api/notifications/summary', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const cnt = data.badge_count || 0;
        if (cnt > 0) {
          badge.textContent = cnt > 99 ? '99+' : cnt;
          badge.style.display = 'flex';
        } else {
          badge.style.display = 'none';
        }
      }
    } catch (_) {}
  }

  async function openNotificationDrawer() {
    let backdrop = document.getElementById('cvNotifBackdrop');
    if (backdrop) {
      backdrop.remove();
      return;
    }

    backdrop = document.createElement('div');
    backdrop.id = 'cvNotifBackdrop';
    backdrop.className = 'cv-notif-backdrop';
    backdrop.innerHTML = `
      <div class="cv-notif-drawer">
        <div class="cv-notif-header">
          <h3 class="cv-notif-title"><span>🔔</span> <span>Notification Center</span></h3>
          <button type="button" class="b" id="btnCloseNotifDrawer" style="padding:4px 10px;font-size:12px">✕</button>
        </div>
        <div class="cv-notif-body" id="cvNotifBody">
          <div style="text-align:center;padding:30px;color:var(--muted)">Loading alerts and live activity…</div>
        </div>
      </div>
    `;
    document.body.appendChild(backdrop);

    backdrop.onclick = e => {
      if (e.target === backdrop) backdrop.remove();
    };
    backdrop.querySelector('#btnCloseNotifDrawer').onclick = () => backdrop.remove();

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/notifications/summary', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to load notifications');
      const data = await res.json();

      const bodyEl = backdrop.querySelector('#cvNotifBody');
      let html = '';

      if (data.expiring_7d > 0) {
        html += `
          <div class="cv-notif-card danger" onclick="window.location.href='alerts.html'">
            <div style="font-size:22px">⚠️</div>
            <div style="flex:1">
              <div style="font-size:13.5px;font-weight:800;color:#ef4444">${data.expiring_7d.toLocaleString()} SIM Devices Expiring in 7 Days</div>
              <div style="font-size:12px;color:var(--muted);margin-top:2px">Immediate renewal required. Click to view devices.</div>
            </div>
            <span style="font-size:12px;color:var(--primary);font-weight:700">Open ➔</span>
          </div>
        `;
      }

      if (data.expiring_30d > 0) {
        html += `
          <div class="cv-notif-card warn" onclick="window.location.href='alerts.html'">
            <div style="font-size:22px">⏳</div>
            <div style="flex:1">
              <div style="font-size:13.5px;font-weight:800;color:#f59e0b">${data.expiring_30d.toLocaleString()} Devices Expiring within 30 Days</div>
              <div style="font-size:12px;color:var(--muted);margin-top:2px">Upcoming commercial renewals. Click to manage.</div>
            </div>
            <span style="font-size:12px;color:var(--primary);font-weight:700">Open ➔</span>
          </div>
        `;
      }

      if (data.expired > 0) {
        html += `
          <div class="cv-notif-card warn" onclick="window.location.href='alerts.html'">
            <div style="font-size:22px">❌</div>
            <div style="flex:1">
              <div style="font-size:13.5px;font-weight:800;color:#64748b">${data.expired.toLocaleString()} Expired Devices in Fleet</div>
              <div style="font-size:12px;color:var(--muted);margin-top:2px">Deactivated or overdue SIM plans.</div>
            </div>
            <span style="font-size:12px;color:var(--primary);font-weight:700">Open ➔</span>
          </div>
        `;
      }

      if (data.errors_count > 0) {
        html += `
          <div class="cv-notif-card danger" onclick="window.location.href='errors.html'">
            <div style="font-size:22px">🚫</div>
            <div style="flex:1">
              <div style="font-size:13.5px;font-weight:800;color:#ef4444">${data.errors_count.toLocaleString()} Upload Errors Pending Review</div>
              <div style="font-size:12px;color:var(--muted);margin-top:2px">Rectify duplicates or missing fields.</div>
            </div>
            <span style="font-size:12px;color:var(--primary);font-weight:700">Fix ➔</span>
          </div>
        `;
      }

      html += `
        <div style="margin-top:10px;padding:12px;background:var(--card-subtle);border-radius:12px;border:1px solid var(--line)">
          <div style="font-size:12px;font-weight:800;margin-bottom:8px;text-transform:uppercase;color:var(--muted)">System Admin Snapshot</div>
          <button class="b" type="button" id="btnDrawerDownloadBackup" style="width:100%;font-size:12.5px;font-weight:700">
            💾 Download Database Backup (.sql)
          </button>
        </div>
      `;

      if (Array.isArray(data.recent_activities) && data.recent_activities.length > 0) {
        html += `
          <div style="margin-top:14px">
            <div style="font-size:12px;font-weight:800;margin-bottom:8px;text-transform:uppercase;color:var(--muted)">Recent Fleet Activity</div>
            <div style="display:flex;flex-direction:column;gap:6px">
              ${data.recent_activities.map(a => `
                <div style="font-size:12px;padding:8px 10px;border-radius:8px;background:var(--card-subtle);border:1px solid var(--line)">
                  <div style="display:flex;justify-content:space-between;color:var(--muted);font-size:10.5px">
                    <span>${E(a.user)}</span>
                    <span>${E(a.time)}</span>
                  </div>
                  <div style="font-weight:600;margin-top:2px;color:var(--text)">${E(a.detail || a.action)}</div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }

      bodyEl.innerHTML = html;

      const btnBackup = bodyEl.querySelector('#btnDrawerDownloadBackup');
      if (btnBackup) {
        btnBackup.onclick = () => {
          if (typeof window.toast === 'function') window.toast('Generating database backup snapshot…');
          window.location.href = '/api/system/backup';
        };
      }
    } catch (err) {
      const bodyEl = backdrop.querySelector('#cvNotifBody');
      if (bodyEl) bodyEl.innerHTML = `<div class="empty err">${E(err.message)}</div>`;
    }
  }

  // =========================================================================
  // DEVICE 360 TIMELINE MODAL CONTROLLER
  // =========================================================================
  cv.openDeviceTimeline = async function (ident) {
    if (!ident) return;
    try {
      if (typeof window.toast === 'function') window.toast(`Fetching 360° history for ${ident}…`);
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/devices/${encodeURIComponent(ident)}/timeline`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Device timeline could not be loaded.');
      const data = await res.json();
      const dev = data.device || {};

      const milestonesHtml = (data.milestones || []).map(m => `
        <div class="cv-timeline-item ${m.status || ''}">
          <div class="cv-timeline-dot">${m.icon || '•'}</div>
          <div>
            <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
              <span style="font-weight:800;font-size:13.5px">${E(m.title)}</span>
              <span style="font-size:11px;color:var(--muted);font-weight:600">${E(m.date)}</span>
            </div>
            <div style="font-size:12px;color:var(--muted);margin-top:3px">${E(m.detail)}</div>
          </div>
        </div>
      `).join('');

      const bodyHtml = `
        <div style="margin-bottom:14px;padding:12px;border-radius:12px;background:var(--card-subtle);border:1px solid var(--line);display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;font-size:12px">
          <div><b style="color:var(--muted)">IMEI:</b> <span>${E(dev.imei)}</span> ${data.is_luhn_valid ? '<span class="tag ok" style="font-size:9.5px;padding:1px 4px">Luhn OK</span>' : '<span class="tag warn" style="font-size:9.5px;padding:1px 4px" title="Luhn check digit mismatch">Luhn Notice</span>'}</div>
          <div><b style="color:var(--muted)">Serial:</b> <span>${E(dev.device_sr_no || 'N/A')}</span></div>
          <div><b style="color:var(--muted)">ICCID:</b> <span>${E(dev.iccid || 'N/A')}</span></div>
          <div><b style="color:var(--muted)">Customer:</b> <span>${E(data.customer_name || 'N/A')}</span></div>
          <div><b style="color:var(--muted)">Provider:</b> <span>${E(dev.sim_provider || 'N/A')}</span></div>
          <div><b style="color:var(--muted)">Plan:</b> <span>${E(dev.activation_plan || 'N/A')}</span></div>
        </div>
        <div class="cv-timeline-wrap">
          ${milestonesHtml}
        </div>
      `;

      open(head(`Device 360° History — ${dev.imei || ident}`, 'info', '📜') + `
        <div class="cvp-body" style="max-height:60vh;overflow-y:auto">${bodyHtml}</div>
        <div class="cvp-foot">
          <button class="b main" data-act="ok">Close History</button>
        </div>
      `, { wide: true });
    } catch (e) {
      if (typeof window.toast === 'function') window.toast('Timeline error: ' + e.message);
    }
  };

  // =========================================================================
  // BULK PLAN RENEWAL ENGINE CONTROLLER
  // =========================================================================
  cv.openBulkRenewModal = function (deviceIds = [], onSuccess) {
    if (!deviceIds || !deviceIds.length) {
      if (typeof window.toast === 'function') window.toast('Please select at least one device to renew.');
      return;
    }

    const modalHtml = `
      <div style="margin-bottom:14px">
        <p style="font-size:13px;color:var(--text);margin:0 0 12px">
          Extending commercial validity for <b>${deviceIds.length.toLocaleString()}</b> selected device(s). Choose duration or a custom expiry date:
        </p>
        <div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap">
          <label class="b p" style="cursor:pointer;font-size:12px;padding:8px 14px;border-radius:8px">
            <input type="radio" name="renewDuration" value="1" checked style="margin-right:6px" /> +1 Year
          </label>
          <label class="b" style="cursor:pointer;font-size:12px;padding:8px 14px;border-radius:8px">
            <input type="radio" name="renewDuration" value="2" style="margin-right:6px" /> +2 Years
          </label>
          <label class="b" style="cursor:pointer;font-size:12px;padding:8px 14px;border-radius:8px">
            <input type="radio" name="renewDuration" value="3" style="margin-right:6px" /> +3 Years
          </label>
        </div>
        <div style="margin-bottom:12px">
          <label style="font-size:12px;font-weight:700;display:block;margin-bottom:4px">Or Exact Custom Expiry Date (Optional):</label>
          <input type="date" id="renewCustomDate" style="width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card)" />
        </div>
        <div style="margin-bottom:12px">
          <label style="font-size:12px;font-weight:700;display:block;margin-bottom:4px">Update Plan Name (Optional):</label>
          <input type="text" id="renewPlanName" placeholder="e.g. BSTPL Commercial Renewal 2027" style="width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card)" />
        </div>
        <div>
          <label style="font-size:12px;font-weight:700;display:block;margin-bottom:4px">Renewal Note / Reference (Optional):</label>
          <input type="text" id="renewNote" placeholder="e.g. Invoice #REC-9821" style="width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card)" />
        </div>
      </div>
    `;

    open(head(`🔄 Renew SIM Plans (${deviceIds.length} Devices)`, 'info', '⚡') + `
      <div class="cvp-body">${modalHtml}</div>
      <div class="cvp-foot">
        <button class="b" data-act="cancel">Cancel</button>
        <button class="b p" id="btnSubmitRenew" style="font-weight:800">Confirm & Extend Plan</button>
      </div>
    `, {
      onKey: (back, close) => {
        const btn = back.querySelector('#btnSubmitRenew');
        if (btn) {
          btn.onclick = async () => {
            btn.disabled = true;
            btn.textContent = 'Extending plans…';
            try {
              const durVal = parseInt(back.querySelector('input[name="renewDuration"]:checked')?.value || '1', 10);
              const customDate = back.querySelector('#renewCustomDate')?.value || null;
              const plan = back.querySelector('#renewPlanName')?.value.trim() || null;
              const note = back.querySelector('#renewNote')?.value.trim() || null;

              const token = localStorage.getItem('token');
              const res = await fetch('/api/devices/bulk-renew', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                  device_ids: deviceIds,
                  years: durVal,
                  new_expiry_date: customDate,
                  activation_plan: plan,
                  note: note
                })
              });
              if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Renewal failed');
              }
              const data = await res.json();
              close('ok');
              if (typeof window.toast === 'function') window.toast(`✓ ${data.message || 'Plans renewed successfully!'}`);
              if (typeof onSuccess === 'function') onSuccess(data);
            } catch (err) {
              btn.disabled = false;
              btn.textContent = 'Confirm & Extend Plan';
              if (typeof window.toast === 'function') window.toast('Renewal error: ' + err.message);
            }
          };
        }
      }
    });
  };

  // =========================================================================
  // LUHN ALGORITHM IMEI VALIDATOR (GSM MOD 10)
  // =========================================================================
  cv.validateImeiLuhn = function (imeiStr) {
    const imei = String(imeiStr || '').replace(/\D/g, '');
    if (imei.length !== 15) return false;
    let total = 0;
    for (let i = 0; i < 14; i++) {
      let digit = parseInt(imei[i], 10);
      if (i % 2 === 1) {
        digit *= 2;
        if (digit > 9) digit = Math.floor(digit / 10) + (digit % 10);
      }
      total += digit;
    }
    const checkDigit = (10 - (total % 10)) % 10;
    return checkDigit === parseInt(imei[14], 10);
  };

  cv.attachImeiValidation = function (inputEl) {
    if (!inputEl || inputEl._cvLuhnAttached) return;
    inputEl._cvLuhnAttached = true;

    let noteEl = inputEl.parentNode ? inputEl.parentNode.querySelector('.cv-luhn-note') : null;
    if (!noteEl && inputEl.parentNode) {
      noteEl = document.createElement('div');
      noteEl.className = 'cv-luhn-note';
      noteEl.style.display = 'none';
      inputEl.parentNode.appendChild(noteEl);
    }

    const check = () => {
      const val = String(inputEl.value || '').trim();
      const digits = val.replace(/\D/g, '');
      if (digits.length === 15) {
        const valid = cv.validateImeiLuhn(digits);
        if (!valid) {
          if (noteEl) {
            noteEl.style.display = 'inline-flex';
            noteEl.className = 'cv-luhn-note warn';
            noteEl.innerHTML = '⚠️ GSM Luhn check digit notice (checksum mismatch)';
            noteEl.title = 'The 15th digit does not match standard Luhn mod-10 formula. Please verify hardware barcode.';
          }
        } else {
          if (noteEl) {
            noteEl.style.display = 'inline-flex';
            noteEl.className = 'cv-luhn-note ok';
            noteEl.innerHTML = '✓ Valid GSM IMEI Checksum';
            noteEl.title = 'IMEI conforms to 15-digit 3GPP/GSM checksum specification.';
          }
        }
      } else {
        if (noteEl) noteEl.style.display = 'none';
      }
    };

    inputEl.addEventListener('input', check);
    inputEl.addEventListener('blur', check);
    if (inputEl.value) check();
  };

  function scanAndAttachImeiInputs() {
    try {
      const inputs = document.querySelectorAll('input[data-devf="imei"], input[id*="imei" i], input[name*="imei" i]');
      inputs.forEach(cv.attachImeiValidation);
    } catch (_) {}
  }

  // =========================================================================
  // ONE-CLICK DATABASE SNAPSHOT & BACKUP (.SQL STREAM)
  // =========================================================================
  cv.downloadDatabaseBackup = async function () {
    try {
      const token = localStorage.getItem('token');
      if (typeof window.toast === 'function') window.toast('Generating database backup snapshot…', 'info');
      const res = await fetch('/api/system/backup', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Snapshot generation failed');
      }
      const blob = await res.blob();
      const disposition = res.headers.get('Content-Disposition') || '';
      let filename = 'customervault_backup_' + new Date().toISOString().slice(0, 10) + '.sql';
      const m = disposition.match(/filename="?([^";]+)"?/);
      if (m && m[1]) filename = m[1];
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        a.remove();
      }, 1000);
      if (typeof window.toast === 'function') window.toast('✓ Database backup downloaded successfully!', 'ok');
    } catch (err) {
      if (typeof cv?.alert === 'function') cv.alert('Backup Error: ' + err.message, 'Backup Notice');
      else alert('Backup Error: ' + err.message);
    }
  };

  // =========================================================================
  // VISUAL BUSINESS INTELLIGENCE & TELEMATICS CHARTS
  // =========================================================================
  cv.renderAnalyticsCharts = async function (containerIdOrEl) {
    const el = typeof containerIdOrEl === 'string' ? document.getElementById(containerIdOrEl) : containerIdOrEl;
    if (!el) return;

    el.innerHTML = '<div style="padding:28px;text-align:center;color:var(--muted);font-weight:700">⏳ Loading fleet telematics &amp; renewal charts…</div>';

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/analytics/charts', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      if (!res.ok) throw new Error('Failed to load analytics charts (' + res.status + ')');
      const data = await res.json();

      const provColors = {
        'Airtel': '#ef4444',
        'Jio': '#0284c7',
        'Vodafone': '#8b5cf6',
        'Vi': '#8b5cf6',
        'BSNL': '#f97316',
        'Sensorise': '#06b6d4',
        'Unknown': '#64748b'
      };

      const providers = data.sim_providers || {};
      const provEntries = Object.entries(providers);
      const totalProvDevs = provEntries.reduce((acc, pair) => acc + pair[1], 0) || 1;

      const trajectory = data.expiry_trajectory || [];
      const maxTraj = Math.max.apply(null, trajectory.map(t => t.count || 0).concat([1]));

      const types = data.sim_types || {};
      const totalTypes = Object.values(types).reduce((a, b) => a + b, 0) || 1;
      const esimCount = types['E-SIM'] || 0;
      const plasticCount = types['Plastic SIM'] || 0;
      const esimPct = Math.round((esimCount / totalTypes) * 100);
      const plasticPct = 100 - esimPct;

      const topCusts = data.top_customers || [];
      const maxCustCount = Math.max.apply(null, topCusts.map(c => c.count || 0).concat([1]));

      // 1. Carrier Distribution Segments & Legend
      let distSegsHtml = '';
      let distLegendHtml = '';
      provEntries.forEach(([prov, cnt]) => {
        const pct = ((cnt / totalProvDevs) * 100).toFixed(1);
        const intPct = Math.round((cnt / totalProvDevs) * 100);
        const color = provColors[prov] || '#3b82f6';
        distSegsHtml += '<div class="cv-dist-seg" style="width:' + pct + '%;background:' + color + '" title="' + prov + ': ' + cnt + ' (' + pct + '%)"></div>';
        distLegendHtml += '<div class="cv-legend-item">' +
          '<div class="cv-legend-left">' +
            '<span class="cv-legend-dot" style="background:' + color + '"></span>' +
            '<span style="font-weight:700;color:var(--text)">' + prov + '</span>' +
          '</div>' +
          '<div><b>' + cnt + '</b> <span style="color:var(--muted);font-size:11px">(' + intPct + '%)</span></div>' +
        '</div>';
      });

      // 2. Trajectory Column Bars
      let trajBarsHtml = '';
      trajectory.forEach(item => {
        const heightPct = Math.max(8, Math.round(((item.count || 0) / maxTraj) * 85));
        const isHeavy = item.count >= 5;
        const hasExp = item.count > 0;
        const barClass = isHeavy ? 'cv-traj-bar heavy-exp' : (hasExp ? 'cv-traj-bar has-exp' : 'cv-traj-bar');
        const parts = (item.label || '').split(' ');
        const mName = parts[0] || '';
        const yr = parts[1] || '';
        const shortLbl = mName.substring(0, 3) + (yr ? " '" + yr.substring(2) : '');
        const valTop = item.count > 0 ? '<span class="cv-traj-val">' + item.count + '</span>' : '';
        trajBarsHtml += '<div class="cv-traj-col" title="' + item.label + ': ' + item.count + ' expiring">' +
          valTop +
          '<div class="' + barClass + '" style="height:' + heightPct + 'px"></div>' +
          '<span class="cv-traj-lbl">' + shortLbl + '</span>' +
        '</div>';
      });

      // 3. Top Customers
      let topCustsHtml = '';
      if (!topCusts.length) {
        topCustsHtml = '<div class="empty">No customer devices found</div>';
      } else {
        topCusts.forEach((c, i) => {
          const pct = Math.round((c.count / maxCustCount) * 100);
          topCustsHtml += '<div class="cv-hbar-row">' +
            '<div class="cv-hbar-meta">' +
              '<span style="color:var(--text);font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px">' +
                '<span style="color:var(--primary);font-size:11px">#' + (i + 1) + '</span> ' + c.name +
              '</span>' +
              '<span style="color:var(--muted)">' + c.count + ' SIMs</span>' +
            '</div>' +
            '<div class="cv-hbar-bg">' +
              '<div class="cv-hbar-fill" style="width:' + pct + '%"></div>' +
            '</div>' +
          '</div>';
        });
      }

      el.innerHTML = '<div class="cv-analytics-grid">' +
        // Card 1
        '<div class="cv-chart-card">' +
          '<div class="cv-chart-title">' +
            '<span>📡 SIM Carrier Fleet Share</span>' +
            '<span class="cv-chart-badge">' + totalProvDevs + ' SIMs Tracked</span>' +
          '</div>' +
          '<div class="cv-dist-track" title="SIM Carrier Breakdown">' + distSegsHtml + '</div>' +
          '<div class="cv-dist-legend">' + distLegendHtml + '</div>' +
        '</div>' +

        // Card 2
        '<div class="cv-chart-card">' +
          '<div class="cv-chart-title">' +
            '<span>📅 12-Month Renewal Forecast</span>' +
            '<span class="cv-chart-badge">Trajectory</span>' +
          '</div>' +
          '<div class="cv-trajectory-chart">' + trajBarsHtml + '</div>' +
          '<div style="margin-top:10px;display:flex;justify-content:space-between;align-items:center;font-size:11.5px;color:var(--muted)">' +
            '<span>Next 30 Days Due: <b>' + (trajectory[0]?.count || 0) + '</b></span>' +
            '<span style="display:inline-flex;align-items:center;gap:4px">' +
              '<span style="width:8px;height:8px;border-radius:2px;background:#f59e0b"></span> Due Renewals' +
            '</span>' +
          '</div>' +
        '</div>' +

        // Card 3
        '<div class="cv-chart-card">' +
          '<div class="cv-chart-title">' +
            '<span>📶 SIM Technology &amp; Form Factor</span>' +
            '<span class="cv-chart-badge">Hardware Ratio</span>' +
          '</div>' +
          '<div style="display:flex;gap:12px;margin-bottom:14px">' +
            '<div style="flex:1;padding:12px;border-radius:10px;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);display:flex;align-items:center;gap:10px">' +
              '<span style="font-size:20px">⚡</span>' +
              '<div>' +
                '<div style="font-size:11px;color:#059669;font-weight:800;text-transform:uppercase">E-SIM Form</div>' +
                '<div style="font-size:18px;font-weight:900;color:var(--text)">' + esimCount + ' <span style="font-size:12px;font-weight:700;color:var(--muted)">(' + esimPct + '%)</span></div>' +
              '</div>' +
            '</div>' +
            '<div style="flex:1;padding:12px;border-radius:10px;background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.25);display:flex;align-items:center;gap:10px">' +
              '<span style="font-size:20px">💳</span>' +
              '<div>' +
                '<div style="font-size:11px;color:#4f46e5;font-weight:800;text-transform:uppercase">Plastic SIM</div>' +
                '<div style="font-size:18px;font-weight:900;color:var(--text)">' + plasticCount + ' <span style="font-size:12px;font-weight:700;color:var(--muted)">(' + plasticPct + '%)</span></div>' +
              '</div>' +
            '</div>' +
          '</div>' +
          '<div class="cv-dist-track" style="height:10px;margin-bottom:8px">' +
            '<div style="width:' + esimPct + '%;background:#10b981" title="E-SIM: ' + esimPct + '%"></div>' +
            '<div style="width:' + plasticPct + '%;background:#6366f1" title="Plastic SIM: ' + plasticPct + '%"></div>' +
          '</div>' +
          '<div style="font-size:11.5px;color:var(--muted);text-align:center;margin-top:auto">' +
            'Automated telecom form-factor detection across active fleet' +
          '</div>' +
        '</div>' +

        // Card 4
        '<div class="cv-chart-card">' +
          '<div class="cv-chart-title">' +
            '<span>🏆 Top Customer Fleets</span>' +
            '<span class="cv-chart-badge">Volume Rankings</span>' +
          '</div>' +
          '<div class="cv-hbar-list">' + topCustsHtml + '</div>' +
        '</div>' +
      '</div>';
    } catch (err) {
      el.innerHTML = '<div style="padding:20px;text-align:center;color:var(--danger)">' +
        '<div>⚠️ Could not load analytics: ' + (err.message || 'Unknown error') + '</div>' +
        '<button class="b" onclick="cv.renderAnalyticsCharts(\'' + (typeof containerIdOrEl === 'string' ? containerIdOrEl : 'homeAnalyticsBody') + '\')" style="margin-top:10px;font-size:12px">🔄 Retry Loading</button>' +
      '</div>';
    }
  };

  function initPageEnhancements() {
    initUniversalHeaderActions();
    scanAndAttachImeiInputs();

    // Auto-render analytics on home/dashboard if element exists
    if (document.getElementById('homeAnalyticsBody')) {
      cv.renderAnalyticsCharts('homeAnalyticsBody');
    }
    if (document.getElementById('dashAnalyticsBody')) {
      cv.renderAnalyticsCharts('dashAnalyticsBody');
    }

    // Mutation observer for dynamically added forms and inputs
    const obs = new MutationObserver(() => scanAndAttachImeiInputs());
    obs.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPageEnhancements);
  } else {
    initPageEnhancements();
  }

