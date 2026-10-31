with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = list(re.finditer(r'\.cv-signin-title|\.cv-signin-sub', text))
for m in matches:
    l = text[:m.start()].count('\n') + 1
    print(f'Line {l}: {text[m.start():m.start()+150]}')

