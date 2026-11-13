with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'async function downloadSingleCustomerExcel' in l:
        start = i
        break

for i in range(start, min(start+50, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

