import re

# ==============================================================================
# 1. Update frontend/index.html (Login Page)
# ==============================================================================
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    idx_content = f.read()

# A. Remove Theme button from top bar
idx_content = re.sub(
    r'\s*<button class="theme-toggle-btn" id="themeToggleBtn"[^>]*>.*?</button>',
    '',
    idx_content
)

# B. Remove Copyright footer
idx_content = re.sub(
    r'\s*<!-- Footer -->\s*<footer class="index-footer">[\s\S]*?</footer>',
    '',
    idx_content
)

# C. Adjust body and index-main in CSS so layout is perfectly balanced
idx_content = idx_content.replace(
    'justify-content: space-between;',
    'justify-content: flex-start;'
)

# Ensure index-main padding is balanced
idx_content = idx_content.replace(
    'padding: 36px 24px;',
    'padding: 40px 24px 48px;'
)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(idx_content)

print("Updated frontend/index.html successfully.")

# ==============================================================================
# 2. Update frontend/login.html
# ==============================================================================
with open('frontend/login.html', 'r', encoding='utf-8') as f:
    login_content = f.read()

# A. Remove Theme button
login_content = re.sub(
    r'\s*<button class="theme-toggle-btn" id="themeToggleBtn"[^>]*>.*?</button>',
    '',
    login_content
)

# B. Remove Copyright footer
login_content = re.sub(
    r'\s*<!-- Footer -->\s*<footer class="login-footer">[\s\S]*?</footer>',
    '',
    login_content
)

# C. Adjust body justify-content
login_content = login_content.replace(
    'justify-content: space-between;',
    'justify-content: flex-start;'
)

with open('frontend/login.html', 'w', encoding='utf-8') as f:
    f.write(login_content)

print("Updated frontend/login.html successfully.")

# ==============================================================================
# 3. Update frontend/home.html and frontend/dashboard.html
# "in home page i want the Symbol on the left than the good morning message after that keep space and leave all the remaining like that"
# ==============================================================================
home_files = ['frontend/home.html', 'frontend/dashboard.html']

for hf in home_files:
    with open(hf, 'r', encoding='utf-8') as f:
        hc = f.read()

    # In CSS: fix .user-greeting-wrap so it does NOT have margin-left: auto
    hc = hc.replace(
        '.user-greeting-wrap {\n      display: flex;\n      align-items: center;\n      gap: 8px;\n      margin-left: auto;\n      flex-wrap: wrap;\n    }',
        '.user-greeting-wrap {\n      display: flex;\n      align-items: center;\n      gap: 12px;\n      margin-left: 0 !important;\n      margin-right: auto;\n      flex-shrink: 0;\n    }'
    )

    # In Header HTML:
    # Ensure:
    # [Symbol on left] [Good morning message] [space via margin-right:auto] [all remaining items on right]
    old_hdr_re = r'<header class="cv-top-header">[\s\S]*?</header>'
    
    new_hdr_html = """<header class="cv-top-header">
        <div class="cv-header-single-line" style="display:flex;align-items:center;justify-content:space-between;width:100%;gap:16px">
          <!-- Left: Symbol FIRST, then Good Morning Greeting & Role Badge -->
          <div class="user-greeting-wrap" style="display:flex;align-items:center;gap:12px;margin-left:0;margin-right:auto;flex-shrink:0">
            <div class="cv-avatar-circle" id="userAvatarCircle" title="User Settings &amp; Preferences" onclick="location.href='settings.html'" style="cursor:pointer;width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--primary,#1d68e1),var(--accent,#fca311));color:#fff;font-size:17px;font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px rgba(0,0,0,0.18)">S</div>
            <div class="user-badge" id="uBadge" style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;background:var(--card-subtle);border:1px solid var(--line);border-radius:99px;font-weight:700;font-size:13.5px">
              <span id="hi">Good morning, Shilish Reddy</span>
              <span class="role-pill admin" id="rolePill">ADMIN</span>
            </div>
          </div>

          <!-- Space in between is automatically maintained by margin-right: auto on greeting and margin-left: auto on actions -->

          <!-- Right: Remaining Items (Search, Refresh, Alerts, Cart, Logout) -->
          <div class="cv-header-actions acts" style="display:flex;align-items:center;gap:8px;margin-left:auto;flex-wrap:wrap">
            <button class="b" id="bQs" title="Quick Search (Ctrl + K)"><span>🔎 Search</span></button>
            <button class="b" id="bRefresh" title="Reload current data">🔄 Refresh</button>
            <button class="b on" id="bAl" title="Toggle Expiry Alerts">Alerts: ON</button>
            <button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="location.href='cart.html'" style="font-weight:700">
              🛒 Cart (<span id="headerCartCountBadge">0</span>)
            </button>
            <button class="b b-logout" id="bLo" type="button" onclick="logout(true)" title="Sign out of your session" style="font-weight:700;padding:6px 14px;border-radius:8px">Logout</button>
          </div>
        </div>
      </header>"""

    hc = re.sub(old_hdr_re, new_hdr_html, hc, count=1)

    with open(hf, 'w', encoding='utf-8') as f:
        f.write(hc)
    
    print(f"Updated {hf} header successfully.")

