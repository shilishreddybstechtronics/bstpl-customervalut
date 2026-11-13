with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'old_subnav_re = r\'<div class="inv-subnav" role="tablist">[\\s\\S]*?</div>\''
replacement = 'old_subnav_re = r\'<div class="inv-subnav" role="tablist"[^>]*>[\\s\\S]*?</div>\''

if target in text:
    text = text.replace(target, replacement)
    with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated old_subnav_re successfully')
else:
    print('Target not found')

