with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l.lower() for k in ['fetch data', 'fetch', 'columns', 'column', 'unique']):
        if 'fetch' in l.lower() or 'unique' in l.lower():
            print(f"{i+1}: {l.strip()[:100]}")

