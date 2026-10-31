with open('backend/schemas.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'class UserOut(' in l:
        for j in range(i, min(len(lines), i+30)):
            print(f'{j+1}: {lines[j].rstrip()}')
        break

