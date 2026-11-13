with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "const canDeleteValidInventory = () => {"
replacement = """function initTheme() {
      const m = localStorage.getItem('valut_theme_mode') || 'light';
      const p = localStorage.getItem('valut_palette') || 'royal_navy';
      applyTheme(p, m, false);
    }

    const canDeleteValidInventory = () => {"""

assert target in text
text = text.replace(target, replacement, 1)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added initTheme to LEAN_FOUNDATION_JS")

