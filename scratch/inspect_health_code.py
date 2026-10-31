with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(1880, 1945):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

