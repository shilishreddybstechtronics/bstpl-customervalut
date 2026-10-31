with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(10390, 10450):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

