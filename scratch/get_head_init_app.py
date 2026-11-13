import subprocess

out = subprocess.check_output(["git", "show", "HEAD:frontend/index.html"], encoding="utf-8", errors="ignore")
pos = out.find("function initApp()")
print(out[pos:pos+1000])

