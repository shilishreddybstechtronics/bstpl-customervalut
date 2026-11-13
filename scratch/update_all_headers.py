import re

pages = [
    'frontend/cart.html',
    'frontend/inventory.html',
    'frontend/sim-upload.html',
    'frontend/fetch-data.html',
    'frontend/edit-delete.html',
    'frontend/alerts.html',
    'frontend/errors.html',
    'frontend/settings.html'
]

for p in pages:
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()

    # Fix .user-greeting-wrap in CSS
    c = c.replace(
        '.user-greeting-wrap {\n      display: flex;\n      align-items: center;\n      gap: 8px;\n      margin-left: auto;\n      flex-wrap: wrap;\n    }',
        '.user-greeting-wrap {\n      display: flex;\n      align-items: center;\n      gap: 12px;\n      margin-left: 0 !important;\n      margin-right: auto;\n      flex-shrink: 0;\n    }'
    )

    # In header:
    c = c.replace(
        '<div class="user-greeting-wrap" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">',
        '<div class="user-greeting-wrap" style="display:flex;align-items:center;gap:12px;margin-left:0;margin-right:auto;flex-shrink:0">'
    )
    c = c.replace(
        '<div class="cv-header-single-line" style="display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap">',
        '<div class="cv-header-single-line" style="display:flex;align-items:center;justify-content:space-between;width:100%;gap:16px">'
    )

    with open(p, 'w', encoding='utf-8') as f:
        f.write(c)

print("Updated modular pages headers.")

