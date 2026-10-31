with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "bulk upload" in l.lower() or "valupload" in l.lower() or "valresult" in l.lower():
        print(f"Line {i+1}: {l.strip()[:100]}")

