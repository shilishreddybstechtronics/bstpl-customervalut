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

# Pattern matching the cv-sidebar-footer block
footer_pattern = re.compile(
    r'\n?\s*<div class="cv-sidebar-footer">[\s\S]*?Smart Data[\s\S]*?Better Decisions[\s\S]*?</div>\s*</div>',
    re.IGNORECASE
)

for p in html_files:
    if not os.path.exists(p):
        print(f"Skipping {p}: file not found")
        continue
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
    
    matches = footer_pattern.findall(content)
    print(f"{p}: matches found = {len(matches)}")
    if matches:
        new_content = footer_pattern.sub('', content)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  Successfully removed from {p}")

print("Done checking html files.")

for root, dirs, files in os.walk('scratch'):
    for f in files:
        if f.endswith('.py') and f != 'clean_smart_data.py':
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fl:
                c = fl.read()
            if 'Smart Data' in c:
                c = footer_pattern.sub('', c)
                c = c.replace('<div class="cv-footer-title">Smart Data</div>', '')
                c = c.replace('<div class="cv-footer-sub">Better Decisions</div>', '')
                c = re.sub(r'\s*<div class="cv-sidebar-footer">[\s\S]*?</div>\s*</div>', '', c)
                with open(p, 'w', encoding='utf-8') as fl:
                    fl.write(c)
                print(f"Cleaned scratch file: {p}")
