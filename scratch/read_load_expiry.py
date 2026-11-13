with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re

# Find loadExpiryContainer implementation
idx = html.find('function loadExpiryContainer')
if idx != -1:
    print(html[idx:idx+4500])
else:
    print("Not found")

