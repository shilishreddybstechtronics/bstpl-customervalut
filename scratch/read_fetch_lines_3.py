with open('frontend/fetch-data.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2950, min(3150, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')

