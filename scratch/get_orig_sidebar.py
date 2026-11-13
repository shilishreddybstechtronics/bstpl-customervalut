import subprocess, re

master_head = subprocess.check_output(["git", "show", "HEAD:frontend/index.html"], encoding="utf-8", errors="ignore")
m = re.search(r'<aside class="cv-sidebar"[\s\S]*?</aside>', master_head)
assert m, "cv-sidebar not found in HEAD"
print("Original cv-sidebar from HEAD:")
print(m.group(0))

