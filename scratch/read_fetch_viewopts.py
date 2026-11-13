with open('frontend/fetch-data.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(1659, min(1720, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

