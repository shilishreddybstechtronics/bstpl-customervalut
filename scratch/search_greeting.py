import re

with open("frontend/index.html", "r", encoding="utf-8") as f:
    html = f.read()

matches = [(m.start(), m.group(0)) for m in re.finditer(r'(Good\s+\w+|good\s+\w+)', html, re.IGNORECASE)]
print("Matches in index.html:", matches)

# Check git log for where 'Good morning' or 'SIM Expiry Alert' was

