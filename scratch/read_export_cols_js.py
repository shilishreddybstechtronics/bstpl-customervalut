with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(3485, min(3620, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

