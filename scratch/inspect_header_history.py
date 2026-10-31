import subprocess

for c in ['HEAD', 'HEAD~1', 'HEAD~3', 'HEAD~4']:
    try:
        out = subprocess.check_output(['git', 'show', f'{c}:frontend/index.html'], text=True)
        lines = out.split('\n')
        for i, l in enumerate(lines):
            if 'cv-top-header' in l:
                print(f"=== {c} at line {i+1} ===")
                print("\n".join(lines[i:i+30]))
                break
    except Exception as e:
        print(f"Err {c}: {e}")

