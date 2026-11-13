import glob
import re

for f in sorted(glob.glob('bstpl-customervalut/frontend/*.html')):
    with open(f, 'r', encoding='utf-8') as fp:
        content = fp.read()
    if "\\" in content:
        # Check if there are backslashes inside onerror attributes
        matches = re.findall(r'onerror="[^"]*\\+[^"]*"', content)
        if matches:
            print(f"File {f} has backslash inside onerror: {matches}")
print("Check completed successfully.")

