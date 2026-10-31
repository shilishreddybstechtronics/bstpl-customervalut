with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "u.password" in l or "user.password" in l or "pwd" in l:
        print(f"Line {i+1}: {l.strip()[:100]}")

