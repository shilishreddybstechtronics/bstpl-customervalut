with open('backend/routes_customers.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('def set_customer_avatar(')
if pos != -1:
    print(text[pos:pos+400])

