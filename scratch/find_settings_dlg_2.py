with open('frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()
import re
m = re.search(r'<dialog[^>]*id=["\']dlgSettings["\'][\s\S]*?</dialog>', html)
if m:
    print(m.group(0)[1500:])

