with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add applyTheme to LEAN_FOUNDATION_JS
target = "const canDeleteValidInventory = () => {"
replacement = """function applyTheme(pal, mode, save = true) {
      pal = pal || localStorage.getItem('valut_palette') || 'royal_navy';
      mode = mode || localStorage.getItem('valut_theme_mode') || 'light';
      document.documentElement.setAttribute('data-theme', mode);
      document.documentElement.setAttribute('data-mode', mode);
      document.documentElement.setAttribute('data-palette', pal);
      if (save) {
        try {
          localStorage.setItem('valut_palette', pal);
          localStorage.setItem('valut_theme_mode', mode);
        } catch(e) {}
      }
    }

    const canDeleteValidInventory = () => {"""

assert target in text
text = text.replace(target, replacement, 1)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added applyTheme to LEAN_FOUNDATION_JS")

