with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
queries = ['Smart Data', 'Better Decisions', 'Live Stream', 'Alerts: ON']
for q in queries:
    pos = text.find(q)
    print(f"'{q}' in index.html? {pos != -1}")
    if pos != -1:
        print(text[pos-100:pos+200])
        print('---')

