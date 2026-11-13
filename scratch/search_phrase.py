import os, re

pattern = 'customer file'
for root, dirs, files in os.walk('.'):
    if '.git' in root: continue
    for f in files:
        if f.endswith(('.html', '.js', '.py')):
            p = os.path.join(root, f)
            try:
                txt = open(p, encoding='utf-8', errors='ignore').read()
                if pattern in txt.lower():
                    matches = [line.strip() for line in txt.splitlines() if pattern in line.lower()]
                    print(f"File: {p} (matches: {len(matches)})")
                    for m in matches[:3]:
                        print(f"   {m[:100]}")
            except Exception: pass

