with open('frontend/alerts.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos1 = text.find('<main class="cv-main-panel"')
pos2 = text.find('id="box-exp"')
print(text[pos1:pos2])

