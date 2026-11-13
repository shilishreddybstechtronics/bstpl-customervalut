with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'@app\.(?:get|post)\(["\']([^"\']+)["\']', text)
print("Routes in main.py:", matches)

