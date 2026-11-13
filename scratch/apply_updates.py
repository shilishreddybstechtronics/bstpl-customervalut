import os
import re

def update_file(filepath):
    print(f"Updating {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update Themes in CSS (between /* ===== 6 PREMIER THEMES and [data-palette] body)
    old_theme_css_pattern = r'/\* ===== 6 PREMIER THEMES.*?(?=\[data-palette\] body)'
    new_theme_css = """/* ===== 6 THEMES (with Light & Dark Mode Support) ===== */

    /* 1. ROYAL NAVY (Default: Navy & Gold, Light Page) */
    [data-palette="royal_navy"][data-mode="light"],
    [data-palette="royal_navy"]:not([data-mode="dark"]),
    :root:not([data-palette]) {
      --bg: #f8fafc;
      --bg-gradient: linear-gradient(180deg, #f8fafc 0%, #edf2f9 100%);
      --card: #ffffff;
      --card-subtle: #f1f5f9;
      --text: #0b1a30;
      --text-dim: #475569;
      --ink: #0b1a30;
      --ink2: #1e293b;
      --line: #cbd5e1;
      --primary: #0f2b5c;
      --primary-hover: #0a1c3d;
      --accent: #d4af37;
      --accentd: #b38f26;
      --accent-light: #fef9ee;
      --muted: #475569;
      --ok: #16a34a;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #091a38 0%, #0d2249 100%);
    }
    [data-palette="royal_navy"][data-mode="dark"] {
      --bg: #080f1d;
      --bg-gradient: linear-gradient(180deg, #080f1d 0%, #0e1b33 100%);
      --card: #0e1b33;
      --card-subtle: #142546;
      --text: #f8fafc;
      --text-dim: #94a3b8;
      --ink: #f8fafc;
      --ink2: #cbd5e1;
      --line: #1e355b;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --accent: #d4af37;
      --accentd: #f59e0b;
      --accent-light: rgba(212, 175, 55, 0.15);
      --muted: #94a3b8;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #fbbf24;
      --cv-sidebar-bg: linear-gradient(180deg, #040913 0%, #081224 100%);
    }

    /* 2. MIDNIGHT (Dark Navy with Soft Gold) */
    [data-palette="midnight"][data-mode="dark"],
    [data-palette="midnight"]:not([data-mode="light"]) {
      --bg: #070d19;
      --bg-gradient: linear-gradient(180deg, #070d19 0%, #0f1a2e 100%);
      --card: #0f1a2e;
      --card-subtle: #16243d;
      --text: #f1f5f9;
      --text-dim: #94a3b8;
      --ink: #f1f5f9;
      --ink2: #cbd5e1;
      --line: #1e293b;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #eab308;
      --accentd: #ca8a04;
      --accent-light: rgba(234, 179, 8, 0.15);
      --muted: #94a3b8;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #eab308;
      --cv-sidebar-bg: linear-gradient(180deg, #040811 0%, #091322 100%);
    }
    [data-palette="midnight"][data-mode="light"] {
      --bg: #f1f5f9;
      --bg-gradient: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
      --card: #ffffff;
      --card-subtle: #f8fafc;
      --text: #0f172a;
      --text-dim: #475569;
      --ink: #0f172a;
      --ink2: #1e293b;
      --line: #cbd5e1;
      --primary: #1e3a8a;
      --primary-hover: #172554;
      --accent: #ca8a04;
      --accentd: #a16207;
      --accent-light: #fefce8;
      --muted: #475569;
      --ok: #059669;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #0a1122 0%, #111d38 100%);
    }

    /* 3. EMERALD (Deep Green with Gold) */
    [data-palette="emerald"][data-mode="light"],
    [data-palette="emerald"]:not([data-mode="dark"]) {
      --bg: #f2fbf6;
      --bg-gradient: linear-gradient(180deg, #f2fbf6 0%, #e6f7ee 100%);
      --card: #ffffff;
      --card-subtle: #e6f7ee;
      --text: #064e3b;
      --text-dim: #047857;
      --ink: #064e3b;
      --ink2: #065f46;
      --line: #a7f3d0;
      --primary: #065f46;
      --primary-hover: #044e39;
      --accent: #d4af37;
      --accentd: #b38f26;
      --accent-light: #fef9ee;
      --muted: #047857;
      --ok: #059669;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #063d2e 0%, #084f3c 100%);
    }
    [data-palette="emerald"][data-mode="dark"] {
      --bg: #031a14;
      --bg-gradient: linear-gradient(180deg, #031a14 0%, #062c21 100%);
      --card: #062c21;
      --card-subtle: #093d2e;
      --text: #ecfdf5;
      --text-dim: #a7f3d0;
      --ink: #ecfdf5;
      --ink2: #a7f3d0;
      --line: #0f533f;
      --primary: #10b981;
      --primary-hover: #059669;
      --accent: #fbbf24;
      --accentd: #f59e0b;
      --accent-light: rgba(251, 191, 36, 0.15);
      --muted: #6ee7b7;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #fbbf24;
      --cv-sidebar-bg: linear-gradient(180deg, #02120d 0%, #041f17 100%);
    }

    /* 4. CRIMSON VAULT (Wine Red, Close to Your Current Brand) */
    [data-palette="crimson_vault"][data-mode="light"],
    [data-palette="crimson_vault"]:not([data-mode="dark"]) {
      --bg: #fff5f5;
      --bg-gradient: linear-gradient(180deg, #fff5f5 0%, #ffe4e6 100%);
      --card: #ffffff;
      --card-subtle: #ffe4e6;
      --text: #4c0519;
      --text-dim: #881337;
      --ink: #4c0519;
      --ink2: #881337;
      --line: #fecdd3;
      --primary: #881337;
      --primary-hover: #700f2d;
      --accent: #d4af37;
      --accentd: #b38f26;
      --accent-light: #fef9ee;
      --muted: #9f1239;
      --ok: #059669;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #4c0519 0%, #680822 100%);
    }
    [data-palette="crimson_vault"][data-mode="dark"] {
      --bg: #1a050b;
      --bg-gradient: linear-gradient(180deg, #1a050b 0%, #2c0b15 100%);
      --card: #2c0b15;
      --card-subtle: #3f101f;
      --text: #fff1f2;
      --text-dim: #fecdd3;
      --ink: #fff1f2;
      --ink2: #fecdd3;
      --line: #5c1126;
      --primary: #fb7185;
      --primary-hover: #f43f5e;
      --accent: #fbbf24;
      --accentd: #f59e0b;
      --accent-light: rgba(251, 191, 36, 0.15);
      --muted: #fda4af;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #fbbf24;
      --cv-sidebar-bg: linear-gradient(180deg, #120206 0%, #1e050d 100%);
    }

    /* 5. OCEAN (Teal-Blue with Amber) */
    [data-palette="ocean"][data-mode="light"],
    [data-palette="ocean"]:not([data-mode="dark"]) {
      --bg: #f0fdfa;
      --bg-gradient: linear-gradient(180deg, #f0fdfa 0%, #e0f2fe 100%);
      --card: #ffffff;
      --card-subtle: #e0f2fe;
      --text: #134e4a;
      --text-dim: #0f766e;
      --ink: #134e4a;
      --ink2: #0e7490;
      --line: #99f6e4;
      --primary: #0f766e;
      --primary-hover: #115e59;
      --accent: #f59e0b;
      --accentd: #d97706;
      --accent-light: #fffbeb;
      --muted: #0d9488;
      --ok: #059669;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #092e35 0%, #0d3d47 100%);
    }
    [data-palette="ocean"][data-mode="dark"] {
      --bg: #041c20;
      --bg-gradient: linear-gradient(180deg, #041c20 0%, #082f37 100%);
      --card: #082f37;
      --card-subtle: #0e424d;
      --text: #ccfbf1;
      --text-dim: #5eead4;
      --ink: #ccfbf1;
      --ink2: #5eead4;
      --line: #115e59;
      --primary: #2dd4bf;
      --primary-hover: #14b8a6;
      --accent: #fbbf24;
      --accentd: #f59e0b;
      --accent-light: rgba(251, 191, 36, 0.15);
      --muted: #5eead4;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #fbbf24;
      --cv-sidebar-bg: linear-gradient(180deg, #021215 0%, #051e23 100%);
    }

    /* 6. VIOLET (Rich Purple with Gold) */
    [data-palette="violet"][data-mode="light"],
    [data-palette="violet"]:not([data-mode="dark"]) {
      --bg: #faf5ff;
      --bg-gradient: linear-gradient(180deg, #faf5ff 0%, #f3e8ff 100%);
      --card: #ffffff;
      --card-subtle: #f3e8ff;
      --text: #3b0764;
      --text-dim: #581c87;
      --ink: #3b0764;
      --ink2: #6b21a8;
      --line: #e9d5ff;
      --primary: #581c87;
      --primary-hover: #491470;
      --accent: #d4af37;
      --accentd: #b38f26;
      --accent-light: #fef9ee;
      --muted: #6b21a8;
      --ok: #059669;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #2e0854 0%, #3d0e6e 100%);
    }
    [data-palette="violet"][data-mode="dark"] {
      --bg: #150426;
      --bg-gradient: linear-gradient(180deg, #150426 0%, #240742 100%);
      --card: #240742;
      --card-subtle: #340d5c;
      --text: #faf5ff;
      --text-dim: #e9d5ff;
      --ink: #faf5ff;
      --ink2: #e9d5ff;
      --line: #4a127a;
      --primary: #c084fc;
      --primary-hover: #a855f7;
      --accent: #fbbf24;
      --accentd: #f59e0b;
      --accent-light: rgba(251, 191, 36, 0.15);
      --muted: #d8b4fe;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #fbbf24;
      --cv-sidebar-bg: linear-gradient(180deg, #10021e 0%, #1a052e 100%);
    }

    """
    content = re.sub(old_theme_css_pattern, new_theme_css, content, count=1, flags=re.DOTALL)

    # 2. Hook sidebar background to CSS variable
    content = content.replace(
        'background: linear-gradient(180deg, #09132b 0%, #0c1a3c 100%);',
        'background: var(--cv-sidebar-bg, linear-gradient(180deg, #091a38 0%, #0d2249 100%)) !important;'
    )

    # 3. Center .cv-signin-title and .cv-signin-sub
    content = content.replace(
        '''.cv-signin-title {
  font-size: 24px;
  font-weight: 800;
  color: #0c1938;
  margin: 0 0 6px 0;
  text-align: left;
}''',
        '''.cv-signin-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--ink, #0c1938);
  margin: 0 0 6px 0;
  text-align: center !important;
}'''
    )

    content = content.replace(
        '''.cv-signin-sub {
  font-size: 13.5px;
  color: #64748b;
  margin: 0 0 22px 0;
  text-align: left;
}''',
        '''.cv-signin-sub {
  font-size: 13.5px;
  color: var(--muted, #64748b);
  margin: 0 0 22px 0;
  text-align: center !important;
}'''
    )

    # 4. Make .cv-app-shell display flex ONLY when body.app-active
    content = content.replace(
        '''/* --- 2. DASHBOARD SHELL (RIGHT HALF OF DESIGN) --- */
.cv-app-shell {
  display: flex !important;''',
        '''/* --- 2. DASHBOARD SHELL (RIGHT HALF OF DESIGN) --- */
body.app-active .cv-app-shell {
  display: flex !important;'''
    )

    content = content.replace(
        '''body.app-active {
  height: 100vh !important;
  max-height: 100vh !important;
  overflow: hidden !important;
}

.cv-app-shell {
  display: flex !important;''',
        '''body.app-active {
  height: 100vh !important;
  max-height: 100vh !important;
  overflow: hidden !important;
}

body.app-active .cv-app-shell {
  display: flex !important;'''
    )

    # 5. Strengthen logout isolation in CSS
    old_iso = '''/* STRICT DISPLAY ISOLATION: NEVER DISPLAY DASHBOARD ON LOGOUT */
body:not(.app-active) #dashboardWrap,
#dashboardWrap[hidden] {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  max-height: 0 !important;
  overflow: hidden !important;
  pointer-events: none !important;
}'''

    new_iso = '''/* STRICT DISPLAY ISOLATION: NEVER DISPLAY DASHBOARD ON LOGOUT */
body:not(.app-active) #dashboardWrap,
body:not(.app-active) .cv-app-shell,
#dashboardWrap[hidden] {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  max-height: 0 !important;
  position: absolute !important;
  left: -99999px !important;
  overflow: hidden !important;
  pointer-events: none !important;
}'''
    content = content.replace(old_iso, new_iso)

    # 6. HTML in #authCard: Center title/sub and remove #dbStatus
    old_auth_card_header = '''<h2 class="cv-signin-title" id="authTitle">Sign In</h2>
          <p class="cv-signin-sub" id="authSub">Access your account to continue</p>'''

    new_auth_card_header = '''<h2 class="cv-signin-title" id="authTitle" style="text-align:center !important">Sign In</h2>
          <p class="cv-signin-sub" id="authSub" style="text-align:center !important">Access your account to continue</p>'''
    content = content.replace(old_auth_card_header, new_auth_card_header)

    # Remove dbStatus from authCard
    content = content.replace('<p class="db-status" id="dbStatus">Checking server…</p>', '')

    # 7. Update dock panel HTML with the 6 requested theme styles
    old_dock_body = '''        <!-- Pure Light & Dark Mode (All other palettes removed) -->
        <p style="margin:10px 0 0;font-size:12px;color:var(--muted);text-align:center">
          Clean high-contrast theme system optimized for readability.
        </p>'''

    new_dock_body = '''        <!-- 6 Requested Themes Selector -->
        <div>
          <label style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--muted);letter-spacing:0.5px;display:block;margin-bottom:8px">Theme Style</label>
          <div style="display:flex;flex-direction:column;gap:6px">
            <button type="button" class="theme-palette-opt" data-palette-val="royal_navy">
              <div class="theme-swatch-group">
                <span style="background:#0f2b5c"></span>
                <span style="background:#d4af37"></span>
                <span style="background:#f8fafc"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Royal Navy</div>
                <div class="theme-desc">Navy and gold (Default, Light Page)</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="midnight">
              <div class="theme-swatch-group">
                <span style="background:#070d19"></span>
                <span style="background:#1e3a8a"></span>
                <span style="background:#eab308"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Midnight</div>
                <div class="theme-desc">Dark navy with soft gold</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="emerald">
              <div class="theme-swatch-group">
                <span style="background:#065f46"></span>
                <span style="background:#10b981"></span>
                <span style="background:#d4af37"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Emerald</div>
                <div class="theme-desc">Deep green with gold</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="crimson_vault">
              <div class="theme-swatch-group">
                <span style="background:#881337"></span>
                <span style="background:#e11d48"></span>
                <span style="background:#d4af37"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Crimson Vault</div>
                <div class="theme-desc">Wine red, close to your brand</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="ocean">
              <div class="theme-swatch-group">
                <span style="background:#0f766e"></span>
                <span style="background:#0284c7"></span>
                <span style="background:#f59e0b"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Ocean</div>
                <div class="theme-desc">Teal-blue with amber</div>
              </div>
            </button>
            <button type="button" class="theme-palette-opt" data-palette-val="violet">
              <div class="theme-swatch-group">
                <span style="background:#581c87"></span>
                <span style="background:#7e22ce"></span>
                <span style="background:#d4af37"></span>
              </div>
              <div class="theme-palette-info">
                <div class="theme-name">Violet</div>
                <div class="theme-desc">Rich purple with gold</div>
              </div>
            </button>
          </div>
        </div>'''
    content = content.replace(old_dock_body, new_dock_body)

    # 8. Defaults in JavaScript: change enterprise_clean -> royal_navy, dark -> light
    content = content.replace(
        "const pal = localStorage.getItem('valut_palette') || 'enterprise_clean';\n        const m = localStorage.getItem('valut_theme_mode') || 'dark';",
        "const pal = localStorage.getItem('valut_palette') || 'royal_navy';\n        const m = localStorage.getItem('valut_theme_mode') || 'light';"
    )

    content = content.replace(
        "const pal = palette || localStorage.getItem('valut_palette') || 'enterprise_clean';\n        const m = mode || localStorage.getItem('valut_theme_mode') || 'dark';",
        "const pal = palette || localStorage.getItem('valut_palette') || 'royal_navy';\n        const m = mode || localStorage.getItem('valut_theme_mode') || 'light';"
    )

    content = content.replace(
        "localStorage.getItem('valut_palette') || 'enterprise_clean'",
        "localStorage.getItem('valut_palette') || 'royal_navy'"
    )

    content = content.replace(
        "localStorage.getItem('valut_theme_mode') || 'dark'",
        "localStorage.getItem('valut_theme_mode') || 'light'"
    )

    # 9. In switchView(false):
    old_switch_false = '''          if ($('dashboardWrap')) {
            $('dashboardWrap').hidden = true;
            $('dashboardWrap').style.setProperty('display', 'none', 'important');
          }
          if ($('authWrap')) {
            $('authWrap').hidden = false;
            $('authWrap').style.setProperty('display', 'flex', 'important');
          }'''

    new_switch_false = '''          if ($('dashboardWrap')) {
            $('dashboardWrap').hidden = true;
            $('dashboardWrap').style.setProperty('display', 'none', 'important');
            $('dashboardWrap').style.setProperty('visibility', 'hidden', 'important');
          }
          if ($('authWrap')) {
            $('authWrap').hidden = false;
            $('authWrap').style.setProperty('display', 'flex', 'important');
            $('authWrap').style.setProperty('visibility', 'visible', 'important');
          }'''
    content = content.replace(old_switch_false, new_switch_false)

    # 10. Update branding: 'Sign in to CustomerVault' -> 'Sign in to BSTPL CustomerVault'
    content = content.replace("'Sign in to CustomerVault'", "'Sign in to BSTPL CustomerVault'")
    content = content.replace('"Sign in to CustomerVault"', '"Sign in to BSTPL CustomerVault"')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {filepath} successfully.")

update_file('frontend/index.html')
update_file('frontend/dashboard.html')

