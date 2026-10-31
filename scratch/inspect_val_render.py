with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(10540, 10630):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

