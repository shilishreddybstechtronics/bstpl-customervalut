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

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUniversalHeaderActions);
  } else {
    initUniversalHeaderActions();
  }

