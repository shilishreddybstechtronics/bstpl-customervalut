with open('frontend/fetch-data.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(1600, min(1750, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')

