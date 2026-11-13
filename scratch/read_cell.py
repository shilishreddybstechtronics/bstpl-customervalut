with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('function cell(')
print(text[pos:pos+1500])

