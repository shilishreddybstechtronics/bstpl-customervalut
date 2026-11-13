with open('frontend/fetch-data.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2985, min(3085, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

