with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_boot = """    // Page Boot
    document.addEventListener('DOMContentLoaded', async () => {
      """ + "{" + """p['init_js']}
    });
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      """ + "{" + """p['init_js']}
    }"""

new_boot = """    // Page Boot
    const _bootPage = async () => {
      """ + "{" + """p['init_js']}
    };
    document.addEventListener('DOMContentLoaded', _bootPage);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      _bootPage();
    }"""

assert old_boot in text, "old_boot not found!"
text = text.replace(old_boot, new_boot)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated build_clean_modular_app.py with safe async boot")

