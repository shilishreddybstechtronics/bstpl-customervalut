import os

files = [
    'index.html', 'dashboard.html', 'home.html', 'inventory.html',
    'sim-upload.html', 'fetch-data.html', 'edit-delete.html', 'alerts.html',
    'errors.html', 'settings.html'
]

print(f"{'Filename':18s} | {'Size (bytes)':12s} | {'Lines':6s}")
print("-" * 42)
for f in files:
    p = os.path.join('frontend', f)
    size = os.path.getsize(p)
    lines = len(open(p, 'r', encoding='utf-8').readlines())
    print(f"{f:18s} | {size:10,d} B | {lines:5d}")

