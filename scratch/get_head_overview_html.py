import subprocess

out = subprocess.check_output(["git", "show", "HEAD:frontend/index.html"], encoding="utf-8", errors="ignore")
pos = out.find('<div class="cv-overview-card">')
print("Found overview card at pos:", pos)
if pos != -1:
    print(out[pos:pos+3500])

