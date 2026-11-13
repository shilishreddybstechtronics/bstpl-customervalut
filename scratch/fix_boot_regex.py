with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """    // Page Boot
    document.addEventListener('DOMContentLoaded', async () => {
      {p['init_js']}
    });
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      {p['init_js']}
    }"""

# In the actual file it has double curlies {{ and }}
import re
text = re.sub(
    r"// Page Boot\s*document\.addEventListener\('DOMContentLoaded', async \(\) => \{\{\s*\{p\['init_js'\]\}\s*\}\}\);\s*if \(document\.readyState === 'complete' \|\| document\.readyState === 'interactive'\) \{\{\s*\{p\['init_js'\]\}\s*\}\}",
    r"""// Page Boot
    const _bootPage = async () => {{
      {p['init_js']}
    }};
    document.addEventListener('DOMContentLoaded', _bootPage);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {{
      _bootPage();
    }}""",
    text
)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated successfully!")

