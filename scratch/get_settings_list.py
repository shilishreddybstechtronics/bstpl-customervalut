import subprocess

out = subprocess.check_output(["git", "show", "f3d4383:frontend/index.html"], encoding="utf-8", errors="ignore")
pos = out.find('class="settings-action-list"')
print(out[pos:pos+2500])

