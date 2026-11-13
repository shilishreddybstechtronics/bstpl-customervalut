with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'added_by_you = count(ACTIVE, Device.added_by == user.id) or 0',
    'added_by_you = (count(ACTIVE, Device.added_by == user.id) or 0) if (user and hasattr(user, "id")) else 0'
)

with open('backend/routes_data.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated backend/routes_data.py successfully!")

