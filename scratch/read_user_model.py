with open('backend/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('class User(')
if pos != -1:
    print(text[pos:pos+1000])

