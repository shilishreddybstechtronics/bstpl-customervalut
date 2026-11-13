import os
import re

html_files = [
    'frontend/alerts.html',
    'frontend/dashboard.html',
    'frontend/edit-delete.html',
    'frontend/errors.html',
    'frontend/fetch-data.html',
    'frontend/home.html',
    'frontend/inventory.html',
    'frontend/settings.html',
    'frontend/sim-upload.html'
]

# 1. Update sidebar Cart button in all HTML files
for p in html_files:
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()

    # Pattern for sidebar Cart link
    # Match <a class="cv-nav-item ..." href="..." ... id="sidebarBtnCart" ...>
    old_cart_link = re.search(r'<a\s+class="cv-nav-item\s*[^"]*"\s+href="[^"]*"\s*(?:onclick="[^"]*")?\s*id="sidebarBtnCart"[^>]*>', c)
    if old_cart_link:
        new_cart_link = '<a class="cv-nav-item " href="cart.html" id="sidebarBtnCart" title="Cart &amp; Recycle Bin" style="text-decoration:none">'
        c = c[:old_cart_link.start()] + new_cart_link + c[old_cart_link.end():]
        print(f"Updated sidebar Cart link in {p}")
    else:
        print(f"Sidebar Cart link NOT matched in {p}")

    # In header: update btnHeaderCart to go to cart.html
    c = c.replace(
        '<button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="openCartModal()" style="font-weight:700">',
        '<button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="location.href=\'cart.html\'" style="font-weight:700">'
    )

    # In inline JS: update openCartModal function to redirect to cart.html
    c = re.sub(
        r'function\s+openCartModal\s*\(\)\s*\{[\s\S]*?window\.location\.href\s*=\s*[\'"][^\'"]*[\'"];?\s*\}',
        'function openCartModal() {\n        window.location.href = \'cart.html\';\n      }',
        c
    )

    with open(p, 'w', encoding='utf-8') as f:
        f.write(c)

print("HTML files updated.")

