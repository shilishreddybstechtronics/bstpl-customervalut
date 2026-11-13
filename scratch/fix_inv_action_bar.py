with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'old_action_bar_re = r\'<div style="display:flex;gap:12px;align-items:center;margin-top:14px;flex-wrap:wrap">[\s\S]*?</div>\''
replacement = 'old_action_bar_re = r\'<div class="row" style="margin:14px 0;gap:10px;flex-wrap:wrap;align-items:center">[\\s\\S]*?</div>\''

if target in text:
    text = text.replace(target, replacement)
    with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated old_action_bar_re in build_clean_modular_app.py')
else:
    print('Target not found')

