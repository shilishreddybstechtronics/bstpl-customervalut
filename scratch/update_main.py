with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '@app.post("/auth/logout")'
if target in text:
    text = text.replace(target, '@app.post("/auth/logout")\n@app.post("/api/auth/logout")')
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated main.py successfully")
else:
    print("Target not found in main.py")

