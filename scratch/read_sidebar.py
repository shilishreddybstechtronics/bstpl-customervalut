with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
m = re.search(r'(<aside class="cv-sidebar" id="cvSidebar">[\s\S]*?</aside>)', text)
if m:
    print(m.group(1))
else:
    print("Sidebar not found")

