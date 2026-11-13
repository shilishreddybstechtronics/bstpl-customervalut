import subprocess

out = subprocess.check_output(["git", "show", "HEAD:frontend/index.html"], encoding="utf-8", errors="ignore")
pos = 0
matches = []
while True:
    p = out.find("cntExpiredGlobalBadge", pos)
    if p == -1: break
    matches.append(p)
    pos = p + 15

print("Matches in HEAD for cntExpiredGlobalBadge:", matches)
for m in matches:
    print(out[m-100:m+200])

