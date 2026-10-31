with open('frontend/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'function loadCartContainer' in line or 'function loadBin' in line:
            print(f'{i+1}: {line.strip()}')

