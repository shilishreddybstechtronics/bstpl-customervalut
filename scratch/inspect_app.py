with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if ("('pf')" in l or "('pc')" in l or "('pwd')" in l):
        print(f"{i+1}: {l.strip()}")

