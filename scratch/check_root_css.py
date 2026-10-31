with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('--- Lines 20-60 ---')
for i in range(20, 60):
    print(f'{i+1}: {lines[i]}', end='')

print('\n--- Lines 220-250 ---')
for i in range(220, 250):
    print(f'{i+1}: {lines[i]}', end='')

