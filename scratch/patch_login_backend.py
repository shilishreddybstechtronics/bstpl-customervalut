with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '    log_activity(db, "login", "Signed in", user=user, request=request, commit=True)'
replacement = '''    # Re-authorize all accesses and roles strictly according to user ID upon login
    expected_role = role_for_id(user.user_id)
    expected_is_admin = (expected_role == "admin")
    if user.role != expected_role or user.is_admin != expected_is_admin:
        user.role = expected_role
        user.is_admin = expected_is_admin
        db.commit()
        db.refresh(user)

    log_activity(db, "login", "Signed in", user=user, request=request, commit=True)'''

assert target in content, "Target not found in backend/main.py"
content = content.replace(target, replacement, 1)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully patched login re-authorization in backend/main.py!")

