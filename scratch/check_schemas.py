with open('backend/schemas.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'UserNameUpdate' in l or 'PasswordIn' in l:
        for j in range(max(0, i-2), min(len(lines), i+15)):
            print(f'{j+1}: {lines[j].rstrip()}')
        print('---')

