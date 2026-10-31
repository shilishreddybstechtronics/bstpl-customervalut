with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(5150, 5700):
    if "theme" in lines[i].lower():
        print(f"Line {i+1}: {lines[i].strip()[:100]}")

