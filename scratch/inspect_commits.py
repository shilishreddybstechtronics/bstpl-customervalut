import subprocess

commits = ['HEAD', 'HEAD~1', 'HEAD~2', 'HEAD~3', 'HEAD~4']
for c in commits:
    try:
        out = subprocess.check_output(['git', 'show', f'{c}:frontend/index.html'], text=True)
        lines = out.split('\n')
        print(f"=== Commit {c} top header ===")
        for i in range(4280, 4340):
            if i < len(lines):
                if 'header' in lines[i].lower() or 'greeting' in lines[i].lower() or 'cart' in lines[i].lower() or 'ubadge' in lines[i].lower() or 'hi' in lines[i].lower():
                    print(f"  {i+1}: {lines[i].strip()[:90]}")
    except Exception as e:
        print(f"Err {c}: {e}")

