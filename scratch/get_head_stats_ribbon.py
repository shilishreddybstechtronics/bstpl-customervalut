import subprocess

out = subprocess.check_output(["git", "show", "HEAD:frontend/index.html"], encoding="utf-8", errors="ignore")
pos = 0
matches = []
while True:
    p = out.find("statsRibbon", pos)
    if p == -1: break
    matches.append(p)
    pos = p + 11

print("Matches in HEAD for statsRibbon:", matches)
for m in matches:
    print("--- MATCH AT", m, "---")
    print(out[max(0, m-200):m+500])

