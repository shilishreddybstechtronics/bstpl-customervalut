with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('.cv-brand-icon')
print(text[pos:pos+1000])

