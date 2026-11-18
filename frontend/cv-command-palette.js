/**
 * CustomerVault Global Command Palette (Ctrl + K) Engine
 * Self-bootstrapping utility providing instant search, navigation, and shortcuts.
 */
(function() {
  'use strict';

  let overlayEl = null;
  let activeIndex = 0;
  let currentResults = [];
  let cachedCustomers = [];

  const PAGES = [
    { title: 'Home Overview', desc: 'Summary metrics, quick tools & alerts', url: 'home.html', icon: '📊', category: 'Navigation' },
    { title: 'Customer Inventory', desc: 'Customer portfolios & device records', url: 'inventory.html', icon: '📋', category: 'Navigation' },
    { title: 'Fetch Data & Search', desc: 'Single, exact, and bulk Excel lookup', url: 'fetch-data.html', icon: '🔍', category: 'Navigation' },
    { title: 'Sensorise Dashboard', desc: 'Server health, telemetry & analytics', url: 'dashboard.html', icon: '📈', category: 'Navigation' },
    { title: 'SIM Upload (eSIM & Plastic)', desc: 'Bulk ingestion & mirror sync', url: 'sim-upload.html', icon: '📤', category: 'Navigation' },
    { title: 'Alerts & Expiry Center', desc: 'Expiry notifications & compliance', url: 'alerts.html', icon: '⚠️', category: 'Navigation' },
    { title: 'Settings & Themes', desc: 'Theme colors, API keys & account config', url: 'settings.html', icon: '⚙️', category: 'Navigation' },
    { title: 'Errored Upload Entries', desc: 'Fix and re-ingest duplicate errors', url: 'errors.html', icon: '🚫', category: 'Navigation' }
  ];

  async function loadCustomers() {
    if (typeof window.CU !== 'undefined' && Array.isArray(window.CU) && window.CU.length > 0) {
      cachedCustomers = window.CU;
      return cachedCustomers;
    }
    try {
      const token = localStorage.getItem('token');
      if (!token) return [];
      const res = await fetch('/api/customers', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        cachedCustomers = Array.isArray(data) ? data : (data.items || []);
        return cachedCustomers;
      }
    } catch (_) {}
    return [];
  }

  function getActions() {
    return [
      {
        title: 'Toggle Theme (Dark / Light)',
        desc: 'Switch between light and dark visual themes',
        icon: '🌓',
        category: 'Quick Action',
        action: () => {
          const curr = document.documentElement.getAttribute('data-theme') || localStorage.getItem('cv_theme') || 'dark';
          const next = curr === 'dark' ? 'light' : 'dark';
          document.documentElement.setAttribute('data-theme', next);
          localStorage.setItem('cv_theme', next);
          if (typeof window.toast === 'function') window.toast(`Theme set to ${next} mode`);
          close();
        }
      },
      {
        title: 'Refresh Data & Status',
        desc: 'Reload server statistics and cache',
        icon: '🔄',
        category: 'Quick Action',
        action: () => {
          close();
          window.location.reload();
        }
      },
      {
        title: 'Download Bulk Upload Template',
        desc: 'Sample Excel (.xlsx) file with pre-configured headers',
        icon: '📥',
        category: 'Quick Action',
        action: () => {
          close();
          if (typeof window.downloadBulkUploadTemplate === 'function') {
            window.downloadBulkUploadTemplate();
          } else {
            window.location.href = 'sim-upload.html';
          }
        }
      },
      {
        title: 'Log Out',
        desc: 'Securely sign out of current session',
        icon: '🔒',
        category: 'Quick Action',
        action: () => {
          close();
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = 'login.html';
        }
      }
    ];
  }

  function open() {
    if (overlayEl) {
      overlayEl.style.display = 'flex';
      const input = overlayEl.querySelector('.cv-cmd-input');
      if (input) {
        input.value = '';
        input.focus();
      }
      renderResults('');
      return;
    }

    loadCustomers();

    overlayEl = document.createElement('div');
    overlayEl.className = 'cv-cmd-overlay';
    overlayEl.innerHTML = `
      <div class="cv-cmd-palette" role="dialog" aria-modal="true" aria-label="Command Palette">
        <div class="cv-cmd-header">
          <span class="cv-cmd-icon">⚡</span>
          <input type="text" class="cv-cmd-input" placeholder="Type a customer name, IMEI, action, or page…" autocomplete="off" spellcheck="false" />
          <div class="cv-cmd-badges">
            <span class="cv-cmd-key">ESC</span>
          </div>
        </div>
        <div class="cv-cmd-body" id="cvCmdResults"></div>
        <div class="cv-cmd-footer">
          <div class="cv-cmd-footer-shortcuts">
            <span class="cv-cmd-footer-item"><span class="cv-cmd-key">↑</span><span class="cv-cmd-key">↓</span> Navigate</span>
            <span class="cv-cmd-footer-item"><span class="cv-cmd-key">↵</span> Select</span>
            <span class="cv-cmd-footer-item"><span class="cv-cmd-key">ESC</span> Close</span>
          </div>
          <span>CustomerVault Spotlight</span>
        </div>
      </div>
    `;

    document.body.appendChild(overlayEl);

    overlayEl.addEventListener('click', e => {
      if (e.target === overlayEl) close();
    });

    const input = overlayEl.querySelector('.cv-cmd-input');
    input.addEventListener('input', e => {
      renderResults(e.target.value.trim());
    });

    input.addEventListener('keydown', handleKeyNavigation);

    input.focus();
    renderResults('');
  }

  function close() {
    if (overlayEl) {
      overlayEl.style.display = 'none';
    }
  }

  function renderResults(query) {
    const listEl = overlayEl.querySelector('#cvCmdResults');
    if (!listEl) return;

    const q = (query || '').toLowerCase().trim();
    const results = [];

    // 1. Direct device/term search prompt if query looks like IMEI or serial number
    if (q.length >= 3) {
      results.push({
        title: `Search Records for "${query}"`,
        desc: `Jump to Fetch Data and query all fields for ${query}`,
        icon: '🔎',
        category: 'Quick Search',
        action: () => {
          close();
          window.location.href = `fetch-data.html?q=${encodeURIComponent(query)}`;
        }
      });
    }

    // 2. Customers
    const matchedCusts = (cachedCustomers || []).filter(c => {
      if (!q) return false;
      return (c.name && c.name.toLowerCase().includes(q)) || String(c.id) === q;
    }).slice(0, 5);

    matchedCusts.forEach(c => {
      results.push({
        title: c.name,
        desc: `Customer #${c.id} · Open dedicated inventory`,
        icon: '🏢',
        category: 'Customer Portfolios',
        action: () => {
          close();
          window.location.href = `inventory.html?customer_id=${c.id}`;
        }
      });
    });

    // 3. Navigation Pages
    PAGES.forEach(p => {
      if (!q || p.title.toLowerCase().includes(q) || p.desc.toLowerCase().includes(q)) {
        results.push({
          title: p.title,
          desc: p.desc,
          icon: p.icon,
          category: p.category,
          action: () => {
            close();
            window.location.href = p.url;
          }
        });
      }
    });

    // 4. Quick Actions
    getActions().forEach(a => {
      if (!q || a.title.toLowerCase().includes(q) || a.desc.toLowerCase().includes(q)) {
        results.push(a);
      }
    });

    currentResults = results;
    activeIndex = 0;

    if (!results.length) {
      listEl.innerHTML = `<div class="cv-cmd-empty">No matching commands, customers, or pages found for "${esc(query)}"</div>`;
      return;
    }

    // Group by category
    let html = '';
    let currCat = null;
    results.forEach((item, idx) => {
      if (item.category !== currCat) {
        currCat = item.category;
        html += `<div class="cv-cmd-section-title">${esc(currCat)}</div>`;
      }
      html += `
        <div class="cv-cmd-item ${idx === 0 ? 'active' : ''}" data-idx="${idx}">
          <div class="cv-cmd-item-left">
            <span class="cv-cmd-item-icon">${item.icon}</span>
            <div class="cv-cmd-item-info">
              <span class="cv-cmd-item-title">${esc(item.title)}</span>
              <span class="cv-cmd-item-desc">${esc(item.desc)}</span>
            </div>
          </div>
          <span class="cv-cmd-key">↵</span>
        </div>
      `;
    });

    listEl.innerHTML = html;

    listEl.querySelectorAll('.cv-cmd-item').forEach(item => {
      item.onclick = () => {
        const idx = parseInt(item.dataset.idx, 10);
        executeItem(idx);
      };
      item.onmouseenter = () => {
        const idx = parseInt(item.dataset.idx, 10);
        setActive(idx);
      };
    });
  }

  function setActive(idx) {
    activeIndex = idx;
    if (!overlayEl) return;
    const items = overlayEl.querySelectorAll('.cv-cmd-item');
    items.forEach((item, i) => {
      item.classList.toggle('active', i === activeIndex);
      if (i === activeIndex) {
        item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    });
  }

  function executeItem(idx) {
    const item = currentResults[idx];
    if (item && typeof item.action === 'function') {
      item.action();
    }
  }

  function handleKeyNavigation(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (currentResults.length > 0) {
        setActive((activeIndex + 1) % currentResults.length);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (currentResults.length > 0) {
        setActive((activeIndex - 1 + currentResults.length) % currentResults.length);
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      executeItem(activeIndex);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      close();
    }
  }

  function esc(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // Global keydown listener for Ctrl + K / Cmd + K
  window.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (overlayEl && overlayEl.style.display !== 'none') {
        close();
      } else {
        open();
      }
    }
  });

  // Wire Top Bar Search button if present (delegated click & DOM load)
  document.addEventListener('click', e => {
    const btn = e.target.closest('#bQs, .cv-search-trigger, [data-action="cmd-palette"]');
    if (btn) {
      e.preventDefault();
      open();
    }
  });

  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('bQs');
    if (btn) {
      btn.onclick = e => {
        e.preventDefault();
        open();
      };
    }
  });

  // Expose API
  window.cvCommandPalette = { open, close };
})();
