with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

m = re.search(r'/\* ==+ SIDEBAR ==+ \*/[\s\S]*?(?=/\* ==+|\Z)', text)
if m:
    print(m.group(0)[:2000])
else:
    pos = text.find('.cv-sidebar {')
    print(text[pos:pos+2500])

