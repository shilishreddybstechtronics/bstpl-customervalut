with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if "canAccessLoginInventory" in l or "canAccessUsersManager" in l:
        print(f"Line {i+1}:")
        print("".join(lines[max(0, i-2):min(len(lines), i+15)]))

