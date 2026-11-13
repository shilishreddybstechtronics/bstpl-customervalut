with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

assert '2025-2026' not in text, "2025-2026 found in index.html!"
assert 'Confidential & Proprietary' not in text, "Confidential & Proprietary found in index.html!"
assert 'themeToggleBtn' not in text, "themeToggleBtn found in index.html!"
assert '<footer' not in text, "footer tag found in index.html!"

print("index.html verification: Copyright and theme toggle completely removed and verified!")

with open('frontend/login.html', 'r', encoding='utf-8') as f:
    text_l = f.read()

assert '2025-2026' not in text_l, "2025-2026 found in login.html!"
assert 'Confidential & Proprietary' not in text_l, "Confidential & Proprietary found in login.html!"
assert 'themeToggleBtn' not in text_l, "themeToggleBtn found in login.html!"
assert '<footer' not in text_l, "footer tag found in login.html!"

print("login.html verification: Copyright and theme toggle completely removed and verified!")

