with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
comments = re.findall(r'/\*+\s*[-=]*\s*([A-Za-z0-9 &,/()_-]+)\s*[-=]*\s*\*+/', text)
print("Section comments in index.html:", len(comments))
for c in comments[:30]:
    print(" -", c)

