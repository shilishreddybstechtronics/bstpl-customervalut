import re

GRID_HTML = """      <!-- 4 Stat Metric Cards (Home Overview: Total Customers, Deleted Customers, Customer Errors, Error Entries) -->
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
      </div>
"""

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # Find </header>
    pos = html.find('</header>')
    if pos == -1:
        print("Header not found in", filepath)
        return

    # Check if statsRibbon is already in file
    if 'id="statsRibbon"' in html:
        print("statsRibbon already present in", filepath)
        return

    after_header = pos + len('</header>')
    # Find next section tag
    pos_sec = html.find('<section', after_header)
    if pos_sec != -1:
        html = html[:after_header] + "\n\n" + GRID_HTML + "\n      " + html[pos_sec:]
    else:
        html = html[:after_header] + "\n\n" + GRID_HTML + "\n\n" + html[after_header:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print("SUCCESS: Inserted 4-card grid into", filepath)

if __name__ == '__main__':
    process_file('frontend/home.html')
    process_file('frontend/dashboard.html')

