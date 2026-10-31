with open('backend/main.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '/auth/me' in line or '/api/auth/me' in line or 'def me(' in line:
            print(f'{i+1}: {line.strip()[:100]}')

