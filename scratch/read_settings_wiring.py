with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(16064, 16135):
    print(f'{i+1}: {lines[i].rstrip()}')

