with open('backend/models.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'class User(' in l:
        for j in range(i, min(len(lines), i+30)):
            print(f'{j+1}: {lines[j].rstrip()}')
        break

