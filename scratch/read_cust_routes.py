with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('@router.get("/customers"')
if pos != -1:
    print(text[pos:pos+2000])

