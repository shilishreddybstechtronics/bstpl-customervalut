with open('backend/routes_users.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if '@router.put("/users/{user_id}")' in l:
        for j in range(i, min(len(lines), i+45)):
            print(f'{j+1}: {lines[j].rstrip()}')
        break

