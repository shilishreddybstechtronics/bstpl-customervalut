with open("frontend/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(4720, 5060):
    if i < len(lines):
        line = lines[i]
        if any(w in line for w in ['Themes', 'theme', 'valFilter', 'Ready for Insertion', 'Successfully Inserted', 'Failed New', 'Total New', 'id="val', 'class="val']):
            print(f"{i+1}: {line.strip()[:100]}")

