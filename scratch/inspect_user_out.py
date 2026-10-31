with open("backend/routes_users.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(25, 75):
    if i < len(lines):
        print(f"{i+1}: {lines[i]}", end="")

