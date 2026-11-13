with open('backend/routes_users.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(166, 216):
    print(f'{i+1}: {lines[i].rstrip()}')

