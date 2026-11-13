with open("frontend/index.html", "r", encoding="utf-8") as f:
    text = f.read()

dup1 = "/* ---------- Change Account Password Modal Controller ---------- *//* ---------- Change Account Password Modal Controller ---------- *//* ---------- Change Account Password Modal Controller ---------- */"
clean1 = "/* ---------- Change Account Password Modal Controller ---------- */"
text = text.replace(dup1, clean1)

dup2 = """/* =========================================================================
         CONTAINER SWITCHER:/* =========================================================================
         CONTAINER SWITCHER: Separates each container cleanly on the same webpage"""
clean2 = """/* =========================================================================
         CONTAINER SWITCHER: Separates each container cleanly on the same webpage"""
text = text.replace(dup2, clean2)

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(text)

with open("frontend/dashboard.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Cleaned up comments in index.html and dashboard.html.")

