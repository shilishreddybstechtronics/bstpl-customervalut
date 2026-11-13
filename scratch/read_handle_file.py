with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(4235, 4300):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end='')

