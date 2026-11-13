import glob
import re

count = 0
files_changed = 0

for p in sorted(glob.glob('bstpl-customervalut/frontend/*.html')):
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define window.handleImgFallback early if not already present
    fallback_def = """  <script>
    function handleImgFallback(img) {
      if (img && !img.dataset.fb) {
        img.dataset.fb = '1';
        img.src = 'logo.png';
      }
    }
  </script>
</head>"""

    # Check if onerror="this.src='logo.png'" exists
    if "onerror=\"this.src='logo.png'\"" in content or 'onerror="this.src=\'logo.png\'"' in content:
        orig = content
        content = content.replace("onerror=\"this.src='logo.png'\"", "onerror=\"handleImgFallback(this)\"")
        content = content.replace('onerror="this.src=\'logo.png\'"', 'onerror="handleImgFallback(this)"')
        
        # Also ensure handleImgFallback is defined in <head>
        if "function handleImgFallback" not in content:
            if "</head>" in content:
                content = content.replace("</head>", fallback_def, 1)

        if content != orig:
            files_changed += 1
            with open(p, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {p}")

print(f"Total files updated: {files_changed}")

