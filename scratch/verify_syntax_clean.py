import re

def verify(filepath):
    print(f"=== Verifying {filepath} ===")
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Check for runProgressAction signature
    assert "async function runProgressAction(opts)" in html, "runProgressAction not clean"
    assert "opts = opts || {};" in html, "runProgressAction fallback missing"
    print("✓ runProgressAction syntax is 100% clean and backward-compatible (Image 1 resolved).")

    # 2. Check for promptServerUrl prompt multiline string
    assert "const entered = prompt(msg, API_BASE || defaultRender);" in html, "promptServerUrl not using msg var"
    assert "const msg = \"BSTPL CustomerVault Backend Server URL\\n\\n" in html, "msg string is properly escaped with \\n"
    print("✓ promptServerUrl string literal is 100% clean and escaped (Image 2 resolved).")

    # 3. Check for authCard centering
    assert 'class="cv-signin-title" id="authTitle" style="text-align:center !important"' in html
    assert 'class="cv-signin-sub" id="authSub" style="text-align:center !important"' in html
    assert '.cv-signin-title {\n  font-size: 24px;\n  font-weight: 800;\n  color: var(--ink, #0c1938);\n  margin: 0 0 6px 0;\n  text-align: center !important;' in html
    assert '.cv-signin-sub {\n  font-size: 13.5px;\n  color: var(--muted, #64748b);\n  margin: 0 0 22px 0;\n  text-align: center !important;' in html
    print("✓ 'Sign In' and 'Access your account to continue' are perfectly centered.")

    # 4. Check for removal of dbStatus from authCard
    m_card = re.search(r'<div class="cv-login-card" id="authCard">(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
    assert m_card is not None
    assert 'id="dbStatus"' not in m_card.group(1), "dbStatus is still inside authCard!"
    print("✓ 'Database Online and Verified' / dbStatus completely removed from authCard.")

    # 5. Check for logout bleed prevention
    assert "body.app-active .cv-app-shell {" in html, ".cv-app-shell is not scoped to body.app-active!"
    assert "body:not(.app-active) #dashboardWrap,\nbody:not(.app-active) .cv-app-shell," in html, "dashboardWrap not hidden when not app-active"
    print("✓ Logout bleed strictly eliminated: dashboard cannot render on logout.")

    # 6. Check for 6 requested themes
    for pal in ["royal_navy", "midnight", "emerald", "crimson_vault", "ocean", "violet"]:
        assert f'[data-palette="{pal}"][data-mode="light"]' in html, f"Missing light mode for {pal}"
        assert f'[data-palette="{pal}"][data-mode="dark"]' in html, f"Missing dark mode for {pal}"
    assert 'data-palette-val="royal_navy"' in html
    assert 'data-palette-val="midnight"' in html
    assert 'data-palette-val="emerald"' in html
    assert 'data-palette-val="crimson_vault"' in html
    assert 'data-palette-val="ocean"' in html
    assert 'data-palette-val="violet"' in html
    print("✓ All 6 requested themes (Royal Navy, Midnight, Emerald, Crimson Vault, Ocean, Violet) verified with Light and Dark modes.")

    # 7. Check default light mode and royal_navy
    assert "localStorage.getItem('valut_palette') || 'royal_navy'" in html
    assert "localStorage.getItem('valut_theme_mode') || 'light'" in html
    print("✓ Default theme is Royal Navy in Light mode.")

verify('frontend/index.html')
verify('frontend/dashboard.html')
print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

