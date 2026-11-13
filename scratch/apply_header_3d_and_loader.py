import re, sys

print("Applying header re-ordering, 3D effects, and branded loading/logout system...")

# 1. Update scratch/build_clean_modular_app.py
with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    text = f.read()

# A. Add 3D effects and Branded Loader CSS to BASE_CSS
css_3d_and_loader = """
    /* =========================================================================
       MINIMAL 3D PAGE TRANSITIONS & DEPTH EFFECTS
       ========================================================================= */
    @keyframes cvPage3dEnter {
      0% {
        opacity: 0;
        transform: perspective(1400px) translateZ(-40px) translateY(14px) rotateX(1.5deg);
      }
      100% {
        opacity: 1;
        transform: perspective(1400px) translateZ(0) translateY(0) rotateX(0deg);
      }
    }
    .cv-main-panel, .container-box {
      animation: cvPage3dEnter 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
      transform-style: preserve-3d;
    }
    body.cv-page-3d-exit .cv-main-panel {
      opacity: 0;
      transform: perspective(1400px) translateZ(-50px) translateY(-12px) rotateX(-1.5deg);
      transition: all 0.16s cubic-bezier(0.4, 0, 1, 1);
    }
    .card, .stat-card, .cw, .stat {
      transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.28s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.28s ease;
      transform: perspective(1000px) translateZ(0);
    }
    .card:hover, .stat-card:hover, .cw:hover {
      transform: perspective(1000px) translateZ(8px) translateY(-2px);
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.07), 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    .cv-avatar-circle {
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
    }
    .cv-avatar-circle:hover {
      transform: scale(1.08) perspective(600px) rotateY(8deg);
      box-shadow: 0 4px 14px rgba(29, 104, 225, 0.35);
    }
    .cv-brand-icon {
      transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .cv-brand-icon:hover {
      transform: perspective(600px) rotateY(15deg) scale(1.05);
    }

    /* =========================================================================
       BRANDED 3D LOADER OVERLAY (Logo & Message on Search/Load)
       ========================================================================= */
    .cv-global-loader {
      position: fixed;
      inset: 0;
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity 0.25s ease, visibility 0.25s ease;
    }
    .cv-loader-backdrop {
      position: absolute;
      inset: 0;
      background: rgba(15, 23, 42, 0.65);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
    }
    .cv-loader-card {
      position: relative;
      z-index: 2;
      background: var(--card, #1e293b);
      border: 1px solid var(--line, rgba(255,255,255,0.12));
      border-radius: 20px;
      padding: 30px 38px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.4), 0 0 0 1px rgba(56, 189, 248, 0.2);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      max-width: 360px;
      animation: cvCardPop 0.3s cubic-bezier(0.16, 1, 0.3, 1) both;
      transform-style: preserve-3d;
      perspective: 1000px;
    }
    @keyframes cvCardPop {
      0% { opacity: 0; transform: scale(0.9) translateY(12px) rotateX(4deg); }
      100% { opacity: 1; transform: scale(1) translateY(0) rotateX(0deg); }
    }
    .cv-loader-logo-wrap {
      position: relative;
      width: 60px;
      height: 60px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .cv-loader-logo-3d {
      width: 52px;
      height: 52px;
      background: linear-gradient(135deg, var(--primary, #1d68e1) 0%, #38bdf8 100%);
      color: #ffffff;
      font-size: 25px;
      font-weight: 900;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8px 24px rgba(29, 104, 225, 0.45);
      animation: cvLogoPulse 1.8s ease-in-out infinite alternate;
    }
    @keyframes cvLogoPulse {
      0% { transform: scale(0.96) rotate(-2deg); box-shadow: 0 4px 14px rgba(29, 104, 225, 0.3); }
      100% { transform: scale(1.06) rotate(2deg); box-shadow: 0 12px 30px rgba(56, 189, 248, 0.6); }
    }
    .cv-loader-brand-title {
      font-size: 16px;
      font-weight: 800;
      color: var(--text, #f8fafc);
      margin-bottom: 2px;
      letter-spacing: -0.3px;
    }
    .cv-loader-brand-title span {
      color: var(--primary, #38bdf8);
    }
    .cv-loader-brand-sub {
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1.2px;
      color: var(--muted, #94a3b8);
      text-transform: uppercase;
      margin-bottom: 14px;
    }
    .cv-loader-msg {
      font-size: 13.5px;
      font-weight: 700;
      color: var(--text, #f8fafc);
      margin-bottom: 14px;
      min-height: 20px;
    }
    .cv-loader-progress {
      width: 200px;
      height: 5px;
      background: var(--card-subtle, rgba(255,255,255,0.08));
      border-radius: 99px;
      overflow: hidden;
      position: relative;
    }
    .cv-loader-progress-bar {
      position: absolute;
      left: -40%;
      width: 40%;
      height: 100%;
      background: linear-gradient(90deg, transparent, var(--primary, #38bdf8), transparent);
      border-radius: 99px;
      animation: cvProgressIndeterminate 1.2s ease-in-out infinite;
    }
    @keyframes cvProgressIndeterminate {
      0% { left: -40%; width: 40%; }
      50% { width: 60%; }
      100% { left: 100%; width: 40%; }
    }
"""

if "cvPage3dEnter" not in text:
    css_anchor = ".dh-page-info {"
    idx_css = text.find(css_anchor)
    if idx_css != -1:
        end_brace = text.find("}", idx_css) + 1
        text = text[:end_brace] + "\n" + css_3d_and_loader + text[end_brace:]
        print("✓ Added 3D transitions and Branded Loader styles to BASE_CSS")

# B. Re-order Top Header in home_top_elements:
# S Logo FIRST, then Greeting, remove Edit Name & Password, Search/Refresh/Alerts/Cart, Logout LAST
reordered_header = """      <!-- App Header: Profile First (S Logo, Greeting & Role), Actions & Logout Last -->
      <header class="cv-top-header">
        <div class="cv-header-single-line" style="display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap">
          <!-- Left: User Profile (S Logo FIRST, followed by Good Morning Greeting & Role Badge) -->
          <div class="user-greeting-wrap" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <div class="cv-avatar-circle" id="userAvatarCircle" title="User Settings &amp; Preferences" onclick="location.href='settings.html'" style="cursor:pointer;width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--primary,#1d68e1),var(--accent,#fca311));color:#fff;font-size:17px;font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px rgba(0,0,0,0.18)">S</div>
            <div class="user-badge" id="uBadge" style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;background:var(--card-subtle);border:1px solid var(--line);border-radius:99px;font-weight:700;font-size:13.5px">
              <span id="hi">Good morning, Shilish Reddy</span>
              <span class="role-pill admin" id="rolePill">ADMIN</span>
            </div>
          </div>

          <!-- Right: Remaining Items (Search, Refresh, Alerts, Cart) and Logout Last -->
          <div class="cv-header-actions acts" style="display:flex;align-items:center;gap:8px;margin-left:auto;flex-wrap:wrap">
            <button class="b" id="bQs" title="Quick Search (Ctrl + K)"><span>🔎 Search</span></button>
            <button class="b" id="bRefresh" title="Reload current data">🔄 Refresh</button>
            <button class="b on" id="bAl" title="Toggle Expiry Alerts">Alerts: ON</button>
            <button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="openCartModal()" style="font-weight:700">
              🛒 Cart (<span id="headerCartCountBadge">0</span>)
            </button>
            <button class="b b-logout" id="bLo" type="button" onclick="logout(true)" title="Sign out of your session" style="font-weight:700;padding:6px 14px;border-radius:8px">Logout</button>
          </div>
        </div>
      </header>"""

# Replace the existing header in home_top_elements logic
old_ht_code = """feature_dialogs = loc['feature_dialogs']
home_top_elements = loc['home_top_elements']
# Remove hardcoded static numbers from home_top_elements
home_top_elements = home_top_elements.replace('>154<', '>—<').replace('>117,783<', '>—<').replace('>117,781<', '>—<').replace('>90<', '>—<')"""

new_ht_code = """feature_dialogs = loc['feature_dialogs']
home_top_elements = loc['home_top_elements']

# Re-order header: S logo first, Good morning after that, remove Edit Name & Password, remaining at end, Logout last
old_hdr_match = re.search(r'<header class="cv-top-header">[\\s\\S]*?</header>', home_top_elements)
if old_hdr_match:
    reordered_header = '''""" + reordered_header + """'''
    home_top_elements = home_top_elements[:old_hdr_match.start()] + reordered_header + home_top_elements[old_hdr_match.end():]

# Remove hardcoded static numbers from home_top_elements
home_top_elements = home_top_elements.replace('>154<', '>—<').replace('>117,783<', '>—<').replace('>117,781<', '>—<').replace('>90<', '>—<')"""

if old_ht_code in text:
    text = text.replace(old_ht_code, new_ht_code, 1)
    print("✓ Reordered header markup in builder: S logo first, greeting second, actions and logout last")
else:
    print("! Notice: old_ht_code not found directly, checking regex replacement")

# C. Add showBstplLoader, hideBstplLoader, and 3D navigation transition to LEAN_FOUNDATION_JS
loader_and_nav_js = r'''
    // --- Branded 3D Loader & Notification System (Logo + Message on Search/Load) ---
    function showBstplLoader(msg = 'Searching & loading records…') {
      let loader = $('cvGlobalLoader');
      if (!loader) {
        loader = document.createElement('div');
        loader.id = 'cvGlobalLoader';
        loader.className = 'cv-global-loader';
        loader.innerHTML = `
          <div class="cv-loader-backdrop"></div>
          <div class="cv-loader-card">
            <div class="cv-loader-logo-wrap">
              <div class="cv-loader-logo-3d">B</div>
            </div>
            <div class="cv-loader-brand-title">BSTPL <span>CustomerVault</span></div>
            <div class="cv-loader-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>
            <div class="cv-loader-msg" id="cvLoaderMsg">${esc(msg)}</div>
            <div class="cv-loader-progress"><div class="cv-loader-progress-bar"></div></div>
          </div>
        `;
        document.body.appendChild(loader);
      }
      const msgEl = $('cvLoaderMsg');
      if (msgEl) msgEl.textContent = msg;
      loader.style.display = 'flex';
    }

    function hideBstplLoader() {
      const loader = $('cvGlobalLoader');
      if (loader) loader.style.display = 'none';
    }

    // Minimal 3D Page Transitions while navigating between files (e.g. errors.html -> inventory.html)
    document.addEventListener('DOMContentLoaded', () => {
      document.querySelectorAll('a.cv-nav-item, .cv-header-actions a, a.nav-link, aside a').forEach(link => {
        link.addEventListener('click', e => {
          const href = link.getAttribute('href');
          if (href && !href.startsWith('#') && !href.startsWith('javascript:') && !link.target) {
            const currentFile = window.location.pathname.split('/').pop() || 'home.html';
            if (href !== currentFile) {
              e.preventDefault();
              document.body.classList.add('cv-page-3d-exit');
              const linkText = link.textContent.replace(/[^\w\s]/gi, '').trim();
              showBstplLoader(`Opening ${linkText || 'CustomerVault'}…`);
              setTimeout(() => { window.location.href = href; }, 160);
            }
          }
        });
      });
    });
'''

# Update showBstplLoader stub in LEAN_FOUNDATION_JS
if "const showBstplLoader = (msg, pct) => {};" in text:
    text = text.replace("const showBstplLoader = (msg, pct) => {};", loader_and_nav_js)
    print("✓ Replaced showBstplLoader stub with full 3D branded loader and page navigation listeners")
elif "function showBstplLoader" not in text:
    anchor_pos = text.find("const ALBL = {")
    if anchor_pos != -1:
        text = text[:anchor_pos] + loader_and_nav_js + "\n" + text[anchor_pos:]
        print("✓ Injected 3D branded loader and page navigation listeners into LEAN_FOUNDATION_JS")

# D. Update logout to show branded signout message and navigate with ?logout=1
old_logout_pattern = r'function logout\(confirmFirst = false\) \{[\s\S]*?window\.location\.href = \'index\.html\';\s*\}'
new_logout_code = '''function logout(confirmFirst = false) {
        if (confirmFirst && !confirm('Are you sure you want to sign out of BSTPL CustomerVault?')) {
          return;
        }
        if (typeof showBstplLoader === 'function') {
          showBstplLoader('Signing out of BSTPL CustomerVault…');
        }
        try {
          api('/api/logout', { method: 'POST' }).catch(() => {});
        } catch(e) {}
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        tok = '';
        setTimeout(() => {
          window.location.href = 'index.html?logout=1';
        }, 220);
      }'''

text = re.sub(old_logout_pattern, new_logout_code, text)
print("✓ Updated logout() with branded signout message and clean redirect")

with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Builder successfully enhanced with header re-ordering, 3D effects, and branded loader!")

