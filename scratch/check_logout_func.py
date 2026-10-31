with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(7840, 7905):
    print(f'{i+1}: {lines[i].rstrip()}')

