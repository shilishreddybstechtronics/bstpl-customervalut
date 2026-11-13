with open('frontend/fetch-data.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['btnRunNormalFetch', 'activateAllFieldsPreset', 'Normal Fetch', 'Bulk Fetch', 'col-pill-chip']):
        print(f"{i+1}: {l.strip()[:100]}")

