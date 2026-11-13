with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(3950, 4030):
    print(f"{i+1}: {lines[i]}", end="")

