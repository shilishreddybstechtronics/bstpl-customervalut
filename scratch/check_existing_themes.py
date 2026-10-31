with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(1830, 2055, 15):
    print(f'{i+1}: {lines[i].rstrip()[:80]}')

