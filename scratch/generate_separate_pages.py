import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    master_html = f.read()

pages = [
    {
        'filename': 'home.html',
        'title': 'Home Overview — BSTPL CustomerVault',
        'default_box': 'box-home',
        'active_hash': 'home'
    },
    {
        'filename': 'inventory.html',
        'title': 'Customer Inventory — BSTPL CustomerVault',
        'default_box': 'box-inv',
        'active_hash': 'inventory'
    },
    {
        'filename': 'sim-upload.html',
        'title': 'SIM Data Upload — BSTPL CustomerVault',
        'default_box': 'box-sim',
        'active_hash': 'sim-upload'
    },
    {
        'filename': 'fetch-data.html',
        'title': 'Fetch Data & Device Records — BSTPL CustomerVault',
        'default_box': 'box-fetch',
        'active_hash': 'fetch-data'
    },
    {
        'filename': 'edit-delete.html',
        'title': 'Edit / Delete by IMEI — BSTPL CustomerVault',
        'default_box': 'box-edit',
        'active_hash': 'edit-delete'
    },
    {
        'filename': 'alerts.html',
        'title': 'SIM Expiry Alerts — BSTPL CustomerVault',
        'default_box': 'box-exp',
        'active_hash': 'alerts'
    },
    {
        'filename': 'errors.html',
        'title': 'Errored Entries & Corrections — BSTPL CustomerVault',
        'default_box': 'box-errors',
        'active_hash': 'errors'
    }
]

for p in pages:
    content = master_html
    # Update title
    content = re.sub(r'<title>[^<]*</title>', f'<title>{p["title"]}</title>', content, count=1)
    
    # Update default container fallback in getInitialTargetBox
    old_fn = "return map[hash] || map[query] || 'box-home';"
    new_fn = f"return map[hash] || map[query] || '{p['default_box']}';"
    content = content.replace(old_fn, new_fn)
    
    # Save file
    file_path = f'frontend/{p["filename"]}'
    with open(file_path, 'w', encoding='utf-8') as out_f:
        out_f.write(content)
    print(f"Generated {file_path} (default: {p['default_box']}) successfully.")

print("\nAll 7 separate webpages created successfully!")

