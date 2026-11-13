with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('function renderTable(')
print(text[pos:pos+2500])

