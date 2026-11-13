import re

print("=== APPLYING GLOBAL POLISH & STATE RESILIENCE TO BUILDER ===")

with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add portal-card CSS to BASE_CSS if not present
portal_css = """
    /* Portal Hub Navigation Cards */
    .portal-card {
      text-decoration: none;
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 24px;
      border-radius: 16px;
      background: var(--card);
      border: 1.5px solid var(--line);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
      transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .portal-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 14px 30px rgba(0, 0, 0, 0.1);
      border-color: var(--primary) !important;
    }
"""
if '.portal-card:hover' not in text:
    text = text.replace('@media print {', portal_css + '\n    @media print {')

# 2. Add global state declarations to LEAN_FOUNDATION_JS if not present
state_decls = """    let currentContainerId = '';
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
    };"""

if 'let invPage = 1' not in text:
    text = text.replace("let currentContainerId = '';", state_decls)

# 3. Add login card to INDEX_PORTAL_CONTAINER if not present
login_card_html = """          <a href="login.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">🔐</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Account &amp; Sign In</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">Access user authentication, employee ID registration, demo credentials, and password management.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Sign In &rarr;</div>
          </a>"""

if 'href="login.html"' not in text:
    text = text.replace('</div>\n      </section>\n"""', login_card_html + '\n        </div>\n      </section>\n"""')

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("build_clean_modular_app.py updated with global state and styling polish!")

