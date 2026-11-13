import re

NEW_STATS_RIBBON = """      <!-- 4 Stat Metric Cards (Home Overview: Total Customers, Deleted Customers, Customer Errors, Error Entries) -->
      <div class="stats" id="statsRibbon" style="display:grid;grid-template-columns:repeat(4, 1fr);gap:16px;margin:18px 0 24px">
        <div class="stat-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 4px 16px rgba(0,0,0,0.03)">
          <div class="stat-icon-wrap" style="width:48px;height:48px;border-radius:12px;background:rgba(59, 130, 246, 0.12);color:#3b82f6;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">
            <span class="stat-icon">👥</span>
          </div>
          <div class="stat-info">
            <span class="stat-num" id="statCustomers" style="font-size:24px;font-weight:800;color:var(--text);display:block;line-height:1.2">—</span>
            <span class="stat-label" style="font-size:12.5px;font-weight:700;color:var(--muted)">Total Customers</span>
          </div>
        </div>
        <div class="stat-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 4px 16px rgba(0,0,0,0.03);cursor:pointer" onclick="location.href='cart.html'" title="View Deleted Customers in Cart">
          <div class="stat-icon-wrap" style="width:48px;height:48px;border-radius:12px;background:rgba(245, 158, 11, 0.12);color:#f59e0b;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">
            <span class="stat-icon">🗑️</span>
          </div>
          <div class="stat-info">
            <span class="stat-num" id="statDeletedCustomers" style="font-size:24px;font-weight:800;color:var(--text);display:block;line-height:1.2">—</span>
            <span class="stat-label" style="font-size:12.5px;font-weight:700;color:var(--muted)">Deleted Customers</span>
          </div>
        </div>
        <div class="stat-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 4px 16px rgba(0,0,0,0.03);cursor:pointer" onclick="location.href='errors.html'" title="View Customer Errors">
          <div class="stat-icon-wrap" style="width:48px;height:48px;border-radius:12px;background:rgba(239, 68, 68, 0.12);color:#ef4444;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">
            <span class="stat-icon">⚠️</span>
          </div>
          <div class="stat-info">
            <span class="stat-num" id="statCustomerErrors" style="font-size:24px;font-weight:800;color:var(--text);display:block;line-height:1.2">—</span>
            <span class="stat-label" style="font-size:12.5px;font-weight:700;color:var(--muted)">Customer Errors</span>
          </div>
        </div>
        <div class="stat-card" style="display:flex;align-items:center;gap:16px;padding:18px 20px;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 4px 16px rgba(0,0,0,0.03);cursor:pointer" onclick="location.href='errors.html'" title="View Error Entries">
          <div class="stat-icon-wrap" style="width:48px;height:48px;border-radius:12px;background:rgba(185, 28, 28, 0.12);color:#b91c1c;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">
            <span class="stat-icon">🚨</span>
          </div>
          <div class="stat-info">
            <span class="stat-num" id="statErrorEntries" style="font-size:24px;font-weight:800;color:var(--text);display:block;line-height:1.2">—</span>
            <span class="stat-label" style="font-size:12.5px;font-weight:700;color:var(--muted)">Error Entries</span>
          </div>
        </div>
      </div>"""

def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Remove globalExpiryAlertBanner completely
    html = re.sub(
        r'<!-- Global SIM Expiry Alert Banner[\s\S]*?</div>\s*</div>\s*</div>',
        '',
        html
    )

    # 2. Replace stats ribbon
    m_stats = re.search(r'(<!-- 4 Stat Metric Cards[\s\S]*?</div>\s*</div>)', html)
    if m_stats:
        html = html[:m_stats.start(1)] + NEW_STATS_RIBBON + html[m_stats.end(1):]

    # 3. Add responsive CSS for stats ribbon if not present
    responsive_css = """
    #statsRibbon {
      display: grid !important;
      grid-template-columns: repeat(4, 1fr) !important;
      gap: 16px !important;
      margin: 18px 0 24px !important;
    }
    @media (max-width: 1024px) {
      #statsRibbon {
        grid-template-columns: repeat(2, 1fr) !important;
      }
    }
    @media (max-width: 600px) {
      #statsRibbon {
        grid-template-columns: 1fr !important;
      }
    }
    """
    if '#statsRibbon {' not in html:
        html = html.replace('</style>', responsive_css + '\n  </style>', 1)

    # 4. Update JS stat population in updateChrome
    old_js = """if ($('statCustomers')) $('statCustomers').textContent = Number(custCount).toLocaleString('en-US');
            if ($('statDevices')) $('statDevices').textContent = Number(devCount).toLocaleString('en-US');
            if ($('statAddedByYou')) $('statAddedByYou').textContent = Number(uCount).toLocaleString('en-US');
            if ($('statColumns')) $('statColumns').textContent = String(COLS.length + extraCount);"""

    new_js = """const delCustCount = s.deleted_customers != null ? s.deleted_customers : 0;
            const custErrCount = s.customer_errors != null ? s.customer_errors : 0;
            const errEntriesCount = s.error_entries != null ? s.error_entries : (s.errored_records != null ? s.errored_records : 0);

            if ($('statCustomers')) $('statCustomers').textContent = Number(custCount).toLocaleString('en-US');
            if ($('statDeletedCustomers')) $('statDeletedCustomers').textContent = Number(delCustCount).toLocaleString('en-US');
            if ($('statCustomerErrors')) $('statCustomerErrors').textContent = Number(custErrCount).toLocaleString('en-US');
            if ($('statErrorEntries')) $('statErrorEntries').textContent = Number(errEntriesCount).toLocaleString('en-US');
            if ($('statDevices')) $('statDevices').textContent = Number(devCount).toLocaleString('en-US');
            if ($('statAddedByYou')) $('statAddedByYou').textContent = Number(uCount).toLocaleString('en-US');
            if ($('statColumns')) $('statColumns').textContent = String(s.unique_columns || (COLS.length + extraCount));"""

    if old_js in html:
        html = html.replace(old_js, new_js)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"SUCCESS: Patched {filepath}!")

if __name__ == '__main__':
    patch_file('frontend/home.html')
    patch_file('frontend/dashboard.html')

