with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
dialogs = re.findall(r'<dialog\s+id="([^"]+)"', text)
print(f"Total dialogs: {len(dialogs)}")
for d in dialogs:
    print(" -", d)

