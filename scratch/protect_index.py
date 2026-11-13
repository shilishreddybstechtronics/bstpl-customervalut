with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """,
    {
        'file': 'frontend/index.html',
        'title': 'Navigation Portal — BSTPL CustomerVault',
        'active_key': 'HOME',
        'has_auth_wrap': True,
        'has_home_header': False,
        'container_html': INDEX_PORTAL_CONTAINER,
        'dialog_keys': ['dlgEventPopup', 'dlgActionProgress'],
        'feature_js': INDEX_JS,
        'init_js': ''
    }"""

if target in text:
    text = text.replace(target, "", 1)
    with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("SUCCESS: Removed index.html from build loop in build_clean_modular_app.py")
else:
    print("WARNING: target not found!")

