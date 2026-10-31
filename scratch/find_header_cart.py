with open('frontend/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'btnHeaderCart' in line:
            print(f'{i+1}: {line.strip()}')

