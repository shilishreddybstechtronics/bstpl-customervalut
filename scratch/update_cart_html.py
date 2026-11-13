import os

html_path = r'c:\Users\soumy\OneDrive\Documents\bstpl-view\frontend\cart.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove <header class="cv-top-header">...</header>
header_start = '<header class="cv-top-header">'
header_end = '</header>'

h_start_idx = content.find(header_start)
assert h_start_idx != -1, "Could not find <header class=\"cv-top-header\">"

h_end_idx = content.find(header_end, h_start_idx)
assert h_end_idx != -1, "Could not find </header>"
h_end_idx += len(header_end)

# Remove the header
content = content[:h_start_idx] + content[h_end_idx:]
print("1. Successfully removed cv-top-header block.")

# 2. Update the 4 KPI metric cards to a clean single line grid format
old_stats_strip = """        <!-- 4 High-Impact KPI Metrics Strip -->
        <div class="stats" style="grid-template-columns:repeat(auto-fit, minmax(210px, 1fr));gap:14px;margin-top:0;margin-bottom:20px">
          
          <!-- Card 1: Total Deleted Items -->
          <div class="card stat" style="padding:16px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--primary);box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Total in Cart</span>
              <span style="font-size:20px">📦</span>
            </div>
            <b id="statTotalItems" style="font-size:24px;font-weight:800;color:var(--text);display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Recoverable records</span>
          </div>

          <!-- Card 2: Deleted Customers -->
          <div class="card stat" style="padding:16px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid #0284c7;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Deleted Customers</span>
              <span style="font-size:20px">🏢</span>
            </div>
            <b id="statTotalCusts" style="font-size:24px;font-weight:800;color:#0284c7;display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Whole account portfolios</span>
          </div>

          <!-- Card 3: Deleted Customer Entries -->
          <div class="card stat" style="padding:16px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid #2563eb;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Customer Entries</span>
              <span style="font-size:20px">📱</span>
            </div>
            <b id="statTotalDevs" style="font-size:24px;font-weight:800;color:#2563eb;display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Inventory &amp; SIM rows</span>
          </div>

          <!-- Card 4: Errored Records -->
          <div class="card stat" style="padding:16px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid #ef4444;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Errored Entries</span>
              <span style="font-size:20px">⚠️</span>
            </div>
            <b id="statTotalErrs" style="font-size:24px;font-weight:800;color:#ef4444;display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Flagged for review</span>
          </div>

        </div>"""

new_stats_strip = """        <!-- 4 High-Impact KPI Metrics Strip in One-Line Grid Format -->
        <div class="stats" id="cartKpiStrip" style="display:grid;grid-template-columns:repeat(4, 1fr);gap:16px;width:100%;margin-top:0;margin-bottom:20px">
          
          <!-- Card 1: Total Deleted Items -->
          <div class="card stat" style="min-width:0;padding:18px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--primary);box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Total in Cart</span>
              <span style="font-size:20px">📦</span>
            </div>
            <b id="statTotalItems" style="font-size:26px;font-weight:800;color:var(--text);display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Recoverable records</span>
          </div>

          <!-- Card 2: Deleted Customers -->
          <div class="card stat" style="min-width:0;padding:18px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid #0284c7;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Deleted Customers</span>
              <span style="font-size:20px">🏢</span>
            </div>
            <b id="statTotalCusts" style="font-size:26px;font-weight:800;color:#0284c7;display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Whole account portfolios</span>
          </div>

          <!-- Card 3: Deleted Customer Entries -->
          <div class="card stat" style="min-width:0;padding:18px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid #2563eb;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Customer Entries</span>
              <span style="font-size:20px">📱</span>
            </div>
            <b id="statTotalDevs" style="font-size:26px;font-weight:800;color:#2563eb;display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Inventory &amp; SIM rows</span>
          </div>

          <!-- Card 4: Errored Records -->
          <div class="card stat" style="min-width:0;padding:18px 20px;border-radius:14px;background:var(--card);border:1px solid var(--line);border-left:4px solid #ef4444;box-shadow:0 3px 12px rgba(0,0,0,0.02)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--muted)">Errored Entries</span>
              <span style="font-size:20px">⚠️</span>
            </div>
            <b id="statTotalErrs" style="font-size:26px;font-weight:800;color:#ef4444;display:block;line-height:1">0</b>
            <span style="font-size:12px;color:var(--muted);margin-top:6px;display:block">Flagged for review</span>
          </div>

        </div>"""

assert old_stats_strip in content, "Could not find exact old_stats_strip"
content = content.replace(old_stats_strip, new_stats_strip, 1)
print("2. Successfully updated 4 KPI cards to single-line grid format.")

# 3. Add responsive CSS rule for #cartKpiStrip
css_rule = """
    /* Ensure 4 Cart KPI Cards render strictly in one line on desktop */
    #cartKpiStrip {
      display: grid !important;
      grid-template-columns: repeat(4, 1fr) !important;
      gap: 16px !important;
      width: 100% !important;
    }
    @media (max-width: 900px) {
      #cartKpiStrip {
        grid-template-columns: repeat(2, 1fr) !important;
      }
    }
    @media (max-width: 480px) {
      #cartKpiStrip {
        grid-template-columns: 1fr !important;
      }
    }
"""

if '#cartKpiStrip' not in content:
    content = content.replace('</style>', css_rule + '\n  </style>', 1)
    print("3. Injected responsive CSS for #cartKpiStrip.")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("cart.html successfully updated!")

