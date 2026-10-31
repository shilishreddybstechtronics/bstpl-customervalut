with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(6028, 6105):
    print(f'{i+1}: {lines[i].rstrip()}')

