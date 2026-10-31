with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "function loadHomeContainer" in l:
        print(f"Line {i+1}:")
        print("".join(lines[i:i+40]))
        break

