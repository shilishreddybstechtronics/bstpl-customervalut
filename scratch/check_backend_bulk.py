with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'def bulk_add' in l or 'def bulk_validate' in l:
        for j in range(i, min(len(lines), i+30)):
            print(f'{j+1}: {lines[j].rstrip()}')

