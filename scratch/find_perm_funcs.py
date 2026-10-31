with open('frontend/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'canAccessUsersManager' in line or 'canAccessLoginInventory' in line or 'canAccessAudit' in line:
            print(f'{i+1}: {line.strip()}')

