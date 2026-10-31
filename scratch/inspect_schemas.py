with open("backend/schemas.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "class Bulk" in l or "class Device" in l:
        print(f"Line {i+1}: {l.strip()}")

