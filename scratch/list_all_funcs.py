with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
funcs = re.findall(r'(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(', text)
print(f"Total functions in index.html: {len(funcs)}")
print("Sample functions:", funcs[:40])

