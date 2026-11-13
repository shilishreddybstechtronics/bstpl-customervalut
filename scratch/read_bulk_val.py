with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(10460, 10525):
    print(f'{i+1}: {lines[i].rstrip()}')

