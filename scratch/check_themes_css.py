with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = list(re.finditer(r'(\[data-(?:theme|mode|palette)[^\]]*\])', text))
print('Total matches:', len(matches))
for m in matches[:30]:
    l = text[:m.start()].count('\n') + 1
    print(f'Line {l}: {m.group(1)}')

