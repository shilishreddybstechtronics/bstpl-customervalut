import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update sidebar menu
old_sb_menu = '''      <nav class="cv-sidebar-menu">
        <button class="cv-nav-item on" data-target="box-home" title="Home Overview">
          <span class="cv-nav-ico">🏠</span>
          <span class="cv-nav-label">Home</span>
        </button>
        <button class="cv-nav-item" data-target="box-inv" title="Customer Inventory">
          <span class="cv-nav-ico">👥</span>
          <span class="cv-nav-label">Customers</span>
        </button>
        <button class="cv-nav-item" data-target="box-fetch" title="Device Records &amp; Fetch">
          <span class="cv-nav-ico">📱</span>
          <span class="cv-nav-label">Device Records</span>
        </button>
        <button class="cv-nav-item" data-target="box-inv" title="Customer Inventory">
          <span class="cv-nav-ico">📦</span>
          <span class="cv-nav-label">Inventory</span>
        </button>
        <button class="cv-nav-item" data-target="box-errors" id="sidebarBtnErrors" title="Errored Entries &amp; Corrections">
          <span class="cv-nav-ico">🚨</span>
          <span class="cv-nav-label">Errored Entries</span>
          <span class="badge danger" id="sidebarErrorsBadge" style="margin-left:auto;background:#ef4444;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;font-weight:800">2055</span>
        </button>
        <button class="cv-nav-item" data-target="box-sim" title="SIM Data Upload &amp; Management">
          <span class="cv-nav-ico">🗂️</span>
          <span class="cv-nav-label">Data Management</span>
        </button>
        <button class="cv-nav-item" data-target="box-exp" id="sidebarBtnAlerts" title="SIM Expiry Alerts">
          <div style="display:flex;align-items:center;gap:12px">
            <span class="cv-nav-ico">⚠️</span>
            <span class="cv-nav-label">Expiry Alerts</span>
          </div>
          <span class="cv-live-badge" style="margin-left:auto;background:rgba(245,158,11,0.2);color:#f59e0b;border:1px solid rgba(245,158,11,0.4)">ALERTS</span>
        </button>
        <button class="cv-nav-item" data-target="box-settings" id="sidebarBtnSettings" title="User Settings &amp; Theme Options">
          <span class="cv-nav-ico">⚙️</span>
          <span class="cv-nav-label">Settings</span>
        </button>
      </nav>'''

new_sb_menu = '''      <nav class="cv-sidebar-menu">
        <button class="cv-nav-item on" data-target="box-home" title="Home Overview">
          <span class="cv-nav-ico">🏠</span>
          <span class="cv-nav-label">Home</span>
        </button>
        <button class="cv-nav-item" data-target="box-edit" title="Edit / Delete by IMEI">
          <span class="cv-nav-ico">✏️</span>
          <span class="cv-nav-label">Edit / Delete by IMEI</span>
        </button>
        <button class="cv-nav-item" data-target="box-fetch" title="Device Records &amp; Fetch">
          <span class="cv-nav-ico">📱</span>
          <span class="cv-nav-label">Device Records</span>
        </button>
        <button class="cv-nav-item" data-target="box-inv" title="Customer Inventory">
          <span class="cv-nav-ico">📦</span>
          <span class="cv-nav-label">Customer Inventory</span>
        </button>
        <button class="cv-nav-item" data-target="box-errors" id="sidebarBtnErrors" title="Errored Entries &amp; Corrections">
          <span class="cv-nav-ico">🚨</span>
          <span class="cv-nav-label">Errored Entries</span>
          <span class="badge danger" id="sidebarErrorsBadge" style="margin-left:auto;background:#ef4444;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;font-weight:800">2055</span>
        </button>
        <button class="cv-nav-item" data-target="box-sim" title="SIM Data Upload &amp; Management">
          <span class="cv-nav-ico">🗂️</span>
          <span class="cv-nav-label">Data Management</span>
        </button>
        <button class="cv-nav-item" data-target="box-exp" id="sidebarBtnAlerts" title="SIM Expiry Alerts">
          <div style="display:flex;align-items:center;gap:12px">
            <span class="cv-nav-ico">⚠️</span>
            <span class="cv-nav-label">Expiry Alerts</span>
          </div>
          <span class="cv-live-badge" style="margin-left:auto;background:rgba(245,158,11,0.2);color:#f59e0b;border:1px solid rgba(245,158,11,0.4)">ALERTS</span>
        </button>
        <button class="cv-nav-item" data-target="box-settings" id="sidebarBtnSettings" title="User Settings &amp; Theme Options">
          <span class="cv-nav-ico">⚙️</span>
          <span class="cv-nav-label">Settings</span>
        </button>
      </nav>'''

assert old_sb_menu in text, "old_sb_menu not found"
text = text.replace(old_sb_menu, new_sb_menu, 1)

# 2. Update box-home to keep ONLY the SIM Expiry Alert container
home_start = text.find('<section class="container-box active" id="box-home">')
home_end = text.find('</section>', home_start) + 10
assert home_start != -1 and home_end != -1, "box-home range not found"

new_box_home = '''      <!-- =========================================================================
         CONTAINER 0: HOME OVERVIEW (Good Morning Container + SIM Expiry Alert Container Only)
         ========================================================================= -->
      <section class="container-box active" id="box-home" style="padding:0;background:transparent;border:none;box-shadow:none">
        <!-- SIM Expiry Alert Container -->
        <div class="cv-expiry-global-banner" id="globalExpiryAlertBanner" style="margin-top:0">
          <div class="cv-exp-banner-left">
            <span class="cv-exp-clock">⏰</span>
            <div>
              <span class="cv-exp-label">SIM Expiry Alert:</span>
              <span class="cv-exp-msg" id="globalExpiryAlertText">40,928 SIM(s) have already expired, and 2,936 are expiring within 30 days.</span>
            </div>
          </div>
          <div class="cv-exp-banner-actions">
            <button type="button" class="cv-exp-btn expired" id="btnViewExpiredGlobal" onclick="showContainer('box-exp')">
              <span>⚠️</span> <span>View Expired (<b id="cntExpiredGlobalBadge">40,928</b>)</span>
            </button>
            <button type="button" class="cv-exp-btn expiring" id="btnViewExpiringSoonGlobal" onclick="showContainer('box-exp')">
              <span>⏳</span> <span>View Expiring Soon (<b id="cntExpiringSoonGlobalBadge">2,936</b>)</span>
            </button>
          </div>
        </div>
      </section>'''

text = text[:home_start] + new_box_home + text[home_end:]

# 3. Guard mainTabs listener in JS
text = text.replace("$('mainTabs').onclick = e => {", "if ($('mainTabs')) $('mainTabs').onclick = e => {")

# 4. Save to frontend/index.html & frontend/dashboard.html
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('frontend/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied sidebar changes and cleaned Home Overview to index.html and dashboard.html successfully!")

