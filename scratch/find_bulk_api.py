with open('frontend/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '/api/bulk' in line or 'bulk_add' in line or 'bulk_validate' in line:
            print(f'{i+1}: {line.strip()[:100]}')

