with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(4300, 4325):
    print(f'{i+1}: {repr(lines[i])}')

