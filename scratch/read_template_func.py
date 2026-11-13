with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(5635, min(5685, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

