with open('backend/routes_users.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '@router' in line:
            print(f'{i+1}: {line.strip()}')

