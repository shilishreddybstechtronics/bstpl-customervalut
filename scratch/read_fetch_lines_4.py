with open('frontend/fetch-data.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(3150, min(3300, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')

