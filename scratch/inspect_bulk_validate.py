with open("backend/routes_data.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "def bulk_validate" in l or "@router.post(\"/devices/bulk/validate\"" in l:
        print(f"Line {i+1}:")
        print("".join(lines[i:i+80]))
        break

