with open('backend/routes_customers.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('from datetime import datetime', 'from datetime import datetime, date, timedelta', 1)

with open('backend/routes_customers.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated imports in routes_customers.py")

