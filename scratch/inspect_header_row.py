import subprocess

out = subprocess.check_output(['git', 'show', 'HEAD~3:frontend/index.html'], text=True)
lines = out.split('\n')
for i, l in enumerate(lines):
    if 'cv-header-row-1' in l or ('class="cv-top-header"' in l):
        print(f"Line {i+1}:")
        print("\n".join(lines[i:i+40]))
        break

