import subprocess

out = subprocess.check_output(["git", "show", "HEAD:frontend/index.html"], encoding="utf-8", errors="ignore")
pos = out.find("globalExpiryAlertBanner")
print("Found globalExpiryAlertBanner in HEAD at:", pos)
if pos != -1:
    print(out[pos-100:pos+1200])

