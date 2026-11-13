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
