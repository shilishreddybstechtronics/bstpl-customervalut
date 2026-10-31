with open('frontend/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'scan' in line.lower() and ('excel' in line.lower() or 'upload' in line.lower()):
            if 8500 <= i <= 10500:
                print(f'{i+1}: {line.strip()[:100]}')

