with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)</script>', text)
code = scripts[2]

lines = code.splitlines()
print(f"Total lines in script #2: {len(lines)}")

# Search for lines that look like function declarations or section headers
for i, line in enumerate(lines):
    if line.strip().startswith('function ') or line.strip().startswith('async function '):
        name = line.strip().split('(')[0]
        if i % 30 == 0 or 'Container' in line or 'load' in line or 'init' in line or 'fetch' in line:
            print(f"Line {i}: {name}")
    elif line.strip().startswith('/*') and '---' in line:
        print(f"Line {i}: {line.strip()[:60]}")

