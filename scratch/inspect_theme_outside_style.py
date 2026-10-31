with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

in_style = False
for i, l in enumerate(lines):
    if "<style" in l: in_style = True
    if "</style>" in l: in_style = False; continue
    if in_style: continue
    if "theme" in l.lower():
        print(f"Line {i+1}: {l.strip()[:100]}")

