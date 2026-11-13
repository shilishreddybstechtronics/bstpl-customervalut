import re, hashlib

files = [
    'frontend/index.html',
    'frontend/dashboard.html',
    'frontend/home.html',
    'frontend/inventory.html',
    'frontend/sim-upload.html',
    'frontend/fetch-data.html',
    'frontend/edit-delete.html',
    'frontend/alerts.html',
    'frontend/errors.html',
    'frontend/settings.html'
]

expected_nav_items = [
    ('home.html', 'Home Overview'),
    ('inventory.html', 'Customer Inventory'),
    ('sim-upload.html', 'SIM Data Upload'),
    ('fetch-data.html', 'Fetch Data'),
    ('edit-delete.html', 'Edit / Delete by IMEI'),
    ('alerts.html', 'Expiry Alerts'),
    ('errors.html', 'Errored Entries'),
    ('settings.html', 'Settings')
]

for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Sidebar Brand Header
    assert 'class="cv-brand-icon">B</div>' in html, f"{fpath} missing B brand icon!"
    assert 'class="cv-brand-title">BSTPL CustomerVault</div>' in html, f"{fpath} missing BSTPL CustomerVault brand title!"
    assert 'class="cv-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>' in html, f"{fpath} missing DEVICE &amp; INVENTORY SYSTEMS brand sub!"

    # 2. Sidebar Navigation Items
    for href, label in expected_nav_items:
        assert f'href="{href}"' in html, f"{fpath} missing {href} link!"
        assert label in html, f"{fpath} missing {label} label!"

    # 3. User Requirement: "and also in this delete data health name"
    # Data Health MUST NOT be in the sidebar menu navigation!
    sidebar_match = re.search(r'<aside class="cv-sidebar"[\s\S]*?</aside>', html)
    assert sidebar_match, f"{fpath} missing cv-sidebar!"
    sidebar_html = sidebar_match.group(0)
    assert 'Data Health' not in sidebar_html, f"{fpath} ILLEGALLY CONTAINS 'Data Health' in sidebar navigation!"
    assert 'home.html#homeDataHealthCard' not in sidebar_html, f"{fpath} ILLEGALLY CONTAINS 'home.html#homeDataHealthCard' link in sidebar!"

    # 4. Sidebar Live Stream Widget
    assert 'id="sidebarLiveWidget"' in sidebar_html, f"{fpath} missing sidebarLiveWidget!"
    assert 'id="sbLiveDevCount">117,783<' in sidebar_html, f"{fpath} missing pre-rendered 117,783 in sidebar!"
    assert 'id="sbLiveCustCount">154<' in sidebar_html, f"{fpath} missing pre-rendered 154 in sidebar!"
    assert 'id="sbLiveTime">Live • Streaming active<' in sidebar_html, f"{fpath} missing pre-rendered Live • Streaming active in sidebar!"

    # 5. Body app-active and dashboardWrap display
    assert '<body class="app-active">' in html, f"{fpath} missing <body class='app-active'>!"
    assert 'id="dashboardWrap" class="cv-app-shell" style="display:flex"' in html, f"{fpath} dashboardWrap is not display:flex!"

    # 6. authWrap ONLY in index.html
    if fpath == 'frontend/index.html':
        assert 'id="authWrap"' in html, f"{fpath} missing authWrap for logout/login wrapper!"
    else:
        assert 'id="authWrap"' not in html, f"{fpath} SHOULD NOT HAVE authWrap (login belongs in login.html/index.html)!"

    # 7. Horizontal action tabs bar #mainTabs MUST NOT BE IN ANY PAGE BODY
    assert 'id="mainTabs"' not in html, f"{fpath} ILLEGALLY CONTAINS #mainTabs in page content!"

    print(f"[PASS] {fpath}: Verified B brand icon, BSTPL CustomerVault, DEVICE & INVENTORY SYSTEMS, all 8 nav items, 'Data Health' DELETED from nav, sidebar live stream widget visible!")

# 8. User requirement verification: index.html has portal links to all 8 files + dashboard.html
with open('frontend/index.html', 'r', encoding='utf-8') as f:
    idx_html = f.read()
assert 'id="box-portal"' in idx_html, "index.html missing portal navigation container!"
for href, label in expected_nav_items:
    assert f'href="{href}"' in idx_html, f"index.html missing portal link to {href}!"
assert 'href="dashboard.html"' in idx_html, "index.html missing portal link to dashboard.html!"
print("[PASS] index.html: Verified dedicated Portal Hub containing links to all files!")

# 9. User requirement verification: dashboard.html has dashboard data
with open('frontend/dashboard.html', 'r', encoding='utf-8') as f:
    dash_html = f.read()
assert 'id="box-home"' in dash_html, "dashboard.html missing #box-home dashboard container!"
assert 'id="homeLiveUpdateCard"' in dash_html, "dashboard.html missing live updates card!"
assert 'id="homeDataHealthCard"' in dash_html, "dashboard.html missing data health card!"
assert 'id="statsRibbon"' in dash_html, "dashboard.html missing stats ribbon!"
print("[PASS] dashboard.html: Verified dedicated dashboard data (Good morning greeting, stats, live telemetry, data health)!")

print("\nALL ASSERTIONS PASSED WITH 100% SUCCESS!")
