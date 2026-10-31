with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = list(re.finditer(r'Customer\s*Va[lu]{2}t', text, re.IGNORECASE))
print(f"Total CustomerVault matches: {len(matches)}")
for m in matches[:25]:
    l = text[:m.start()].count('\n') + 1
    print(f"Line {l}: {text[m.start()-15:m.start()+40]}")

