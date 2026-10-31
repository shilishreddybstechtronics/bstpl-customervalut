with open('frontend/index.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'bLogInv' in line or 'dlgLoginInventory' in line or 'login-inventory' in line or 'loadAuditLog' in line:
            print(f'{i+1}: {line.strip()}')

