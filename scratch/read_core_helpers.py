with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

for term in ['async function api', 'function toast', 'function esc', 'const esc', 'const toast', 'function isSuperAdminUser', 'function isMasterAdminUser']:
    p = text.find(term)
    if p != -1:
        print(f"=== {term} ===")
        print(text[p:p+400])

