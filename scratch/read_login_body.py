with open('frontend/login.html', 'r', encoding='utf-8') as f:
    text = f.read()

body_start = text.find('<body>')
print(text[body_start:body_start+2500])

