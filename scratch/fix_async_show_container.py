with open("frontend/index.html", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("function showContainer(boxId) {", "async function showContainer(boxId) {", 1)

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(text)

with open("frontend/dashboard.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated showContainer to async in index.html & dashboard.html")

