with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.*theme-.*\{.*', text)
print("theme- rules count:", len(matches))
for m in matches[:10]:
    print(m)

matches2 = re.findall(r'.*(?:royal_navy|midnight|emerald|crimson_vault).*', text)
print("palette names count:", len(matches2))
for m in matches2[:10]:
    print(m)

