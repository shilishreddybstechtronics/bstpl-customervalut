with open('backend/routes_customers.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(48, 65):
    print(f"{i+1}: {lines[i]}", end="")

