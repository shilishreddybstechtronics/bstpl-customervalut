with open('frontend/home.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('<header class="cv-top-header">')
idx2 = text.find('</header>', idx1)
print(text[idx1:idx2+9])

