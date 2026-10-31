with open("backend/routes_data.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "def get_inventory_health" in l or "/inventory/health" in l:
        print(f"Line {i+1}:")
        print("".join(lines[i:i+60]))

