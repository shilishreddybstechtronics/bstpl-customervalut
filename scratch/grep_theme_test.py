with open('scratch/test_settings_theme_and_user_data.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.*theme.*', text, re.IGNORECASE)
for l in matches[:20]:
    print(l)

