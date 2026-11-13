import re

def patch_index_html():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update CSS grid to Form Left, Hero Right
    html = re.sub(
        r'grid-template-columns:\s*1\.18fr\s*0\.82fr;',
        'grid-template-columns: 0.82fr 1.18fr;',
        html
    )

    # 2. Update tagline pill in top bar
    html = re.sub(
        r'<div class="tagline-pill">[^<]*</div>',
        '<div class="tagline-pill">Secure Smart Connected Surface Online</div>',
        html
    )

    # 3. Swap DOM columns inside <main class="index-main">
    # Extract hero-col and auth-card-wrap
    hero_match = re.search(r'(<div class="hero-col">[\s\S]*?</div>\s*</div>\s*</div>)', html)
    # Let's find exact bounds of hero-col and auth-card-wrap
    m_main = re.search(r'<main class="index-main">([\s\S]*?)</main>', html)
    if m_main:
        main_content = m_main.group(1)
        m_hero = re.search(r'(<!-- Left Hero Column[\s\S]*?</div>\s*</div>\s*</div>)', main_content)
        m_auth = re.search(r'(<!-- Right Authentication Form Card[\s\S]*?</div>\s*</div>)', main_content)
        if m_hero and m_auth:
            hero_block = m_hero.group(1)
            auth_block = m_auth.group(1)
            
            # Update hero_block branding
            new_hero_block = hero_block.replace(
                '⚡ Enterprise Telemetrics &amp; Inventory Vault',
                '🌐 Secure Smart Connected Surface Online'
            ).replace(
                'Your Customer Data,<br>\n        <span class="hero-highlight">Our Priority</span>',
                'Secure Smart Connected<br>\n        <span class="hero-highlight">Surface Online</span>'
            ).replace(
                'Your Customer Data,<br>\r\n        <span class="hero-highlight">Our Priority</span>',
                'Secure Smart Connected<br>\r\n        <span class="hero-highlight">Surface Online</span>'
            )
            new_hero_block = new_hero_block.replace(
                '<!-- Left Hero Column: Brand, Headline, Subtitle, and 4 Feature Cards -->',
                '<!-- Right Branding Column: Secure Smart Connected Surface Online -->'
            )
            new_auth_block = auth_block.replace(
                '<!-- Right Authentication Form Card -->',
                '<!-- Left Authentication Form Card -->'
            )

            new_main_content = f"\n    \n    {new_auth_block}\n\n    {new_hero_block}\n\n  "
            html = html[:m_main.start(1)] + new_main_content + html[m_main.end(1):]

    # 4. Add back-button protection script
    back_guard = """
    // Prevent navigating back to authenticated pages after logout
    if (window.history && window.history.replaceState) {
      if (window.location.search && window.location.search.includes('logout=1')) {
        window.history.replaceState(null, '', 'index.html?logout=1');
      }
    }
    window.addEventListener('pageshow', function(e) {
      if (e.persisted || (window.performance && window.performance.navigation && window.performance.navigation.type === 2)) {
        if (window.location.search && window.location.search.includes('logout=1')) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
      }
    });
"""
    if 'Prevent navigating back to authenticated pages' not in html:
        html = html.replace("const API_BASE = window.location.origin;", "const API_BASE = window.location.origin;\n" + back_guard)

    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("SUCCESS: frontend/index.html updated!")

def patch_login_html():
    with open('frontend/login.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update CSS grid
    html = re.sub(
        r'grid-template-columns:\s*1\.15fr\s*0\.85fr;',
        'grid-template-columns: 0.85fr 1.15fr;',
        html
    )

    # 2. Swap DOM columns inside <main class="login-main">
    m_main = re.search(r'<main class="login-main">([\s\S]*?)</main>', html)
    if m_main:
        main_content = m_main.group(1)
        m_hero = re.search(r'(<!-- Left Hero Column[\s\S]*?</div>\s*</div>)', main_content)
        m_auth = re.search(r'(<!-- Right Auth Card[\s\S]*?</div>\s*</div>)', main_content)
        if m_hero and m_auth:
            hero_block = m_hero.group(1)
            auth_block = m_auth.group(1)

            new_hero_block = hero_block.replace(
                '<!-- Left Hero Column -->',
                '<!-- Right Branding Column: Secure Smart Connected Surface Online -->'
            ).replace(
                'Automated SIM &amp; Customer Inventory',
                'Secure Smart Connected Surface Online'
            )
            # update headline if present
            new_hero_block = re.sub(r'<h1 class="hero-headline">[\s\S]*?</h1>',
                '<h1 class="hero-headline">Secure Smart Connected<br><span class="hero-highlight">Surface Online</span></h1>',
                new_hero_block
            )
            new_auth_block = auth_block.replace(
                '<!-- Right Auth Card -->',
                '<!-- Left Auth Card -->'
            )
            new_main_content = f"\n    \n    {new_auth_block}\n\n    {new_hero_block}\n\n  "
            html = html[:m_main.start(1)] + new_main_content + html[m_main.end(1):]

    # Add back-guard
    back_guard = """
    if (window.history && window.history.replaceState) {
      if (window.location.search && window.location.search.includes('logout=1')) {
        window.history.replaceState(null, '', 'login.html?logout=1');
      }
    }
"""
    if 'history.replaceState' not in html:
        html = html.replace("<script>", "<script>\n" + back_guard)

    with open('frontend/login.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("SUCCESS: frontend/login.html updated!")

if __name__ == '__main__':
    patch_index_html()
    patch_login_html()

