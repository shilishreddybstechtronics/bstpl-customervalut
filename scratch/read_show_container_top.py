with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(8095, 8145):
    print(f'{i+1}: {lines[i].rstrip()}')

