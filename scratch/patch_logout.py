with open("backend/main.py", "rb") as f:
    content = f.read()

old = b'@app.post("/auth/logout")\r\n@app.post("/api/auth/logout")\r\ndef logout'
if old not in content:
    old = b'@app.post("/auth/logout")\n@app.post("/api/auth/logout")\ndef logout'

assert old in content, "old not found"

new = b'@app.post("/auth/logout")\r\n@app.post("/api/auth/logout")\r\n@app.get("/auth/logout")\r\n@app.get("/api/auth/logout")\r\ndef logout'
content = content.replace(old, new)
with open("backend/main.py", "wb") as f:
    f.write(content)

print("Updated logout endpoints in backend/main.py successfully.")

