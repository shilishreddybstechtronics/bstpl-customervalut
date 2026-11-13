import re, subprocess

master_head = subprocess.check_output(['git', 'show', 'HEAD:frontend/index.html'], encoding='utf-8', errors='ignore')
pos_errors = master_head.find('id="box-errors"')
pos_errors_end = master_head.find('</section>', pos_errors) + len('</section>')
tail = master_head[pos_errors_end:]

print(f"Total tail length: {len(tail)}")
pos_script = tail.find('<script>')
print(f"First <script> in tail at: {pos_script}")

pre_script = tail[:pos_script]
print("Pre-script content summary:")
print(f"Pre-script length: {len(pre_script)}")

# Find all dialog tags in pre_script and post_script
all_dlgs = list(re.finditer(r'<dialog\s+[^>]*id="([^"]+)"', tail))
for m in all_dlgs:
    loc = "PRE-SCRIPT" if m.start() < pos_script else "POST-SCRIPT"
    print(f"  {m.group(1)} at {m.start()} ({loc})")
