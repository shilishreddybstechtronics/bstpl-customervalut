import subprocess

out = subprocess.check_output(["git", "show", "HEAD:frontend/index.html"], encoding="utf-8", errors="ignore")
pos = out.find('id="featEdit"')
print(out[pos:pos+1500])

