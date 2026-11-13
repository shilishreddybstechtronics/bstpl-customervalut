with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

m = re.search(r'function renderTable\b[\s\S]*?(?=\n\s*(?:function|const|let|var)\s+[a-zA-Z0-9_$]+\b)', text)
if m:
    print(m.group(0))
else:
    print("Not found")

