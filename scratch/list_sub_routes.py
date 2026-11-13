for f in ['backend/routes_data.py', 'backend/routes_activity.py', 'backend/routes_customers.py']:
    with open(f, 'r', encoding='utf-8') as fp:
        c = fp.read()
    import re
    routes = re.findall(r'@router\.(?:get|post|put|delete)\(["\']([^"\']+)["\']', c)
    print(f"{f}: {routes}")

