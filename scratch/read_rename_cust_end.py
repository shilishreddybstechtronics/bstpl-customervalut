with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('def rename_customer(')
if pos != -1:
    print(text[pos+1000:pos+2500])

