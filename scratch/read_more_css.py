import subprocess

master_head = subprocess.check_output(["git", "show", "HEAD:frontend/index.html"], encoding="utf-8", errors="ignore")

terms = ['cv-exp-btn', 'stat-info', 'live-badge', 'live-dot']

for t in terms:
    pos = master_head.find(f'.{t}')
    if pos != -1:
        print(f"=== {t} ===")
        print(master_head[pos:pos+400])

