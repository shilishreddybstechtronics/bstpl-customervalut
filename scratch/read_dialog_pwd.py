with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(6845, 6865):
    print(f'{i+1}: {lines[i].rstrip()}')

