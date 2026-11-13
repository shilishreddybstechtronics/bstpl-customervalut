with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '<!-- Sub-View 3: Bulk Upload' in l:
        start = i
        break
for i in range(start, min(start+100, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

