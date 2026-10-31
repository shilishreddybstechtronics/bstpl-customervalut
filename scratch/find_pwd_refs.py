with open('frontend/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if any(k in line for k in ["'pwd'", '"pwd"', "'pf'", "'p1'", "'p2'", "'p3'", "'pe'", "'pc'"]):
            print(f'{i+1}: {line.strip()[:100]}')

