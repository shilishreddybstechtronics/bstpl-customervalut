with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "old_opt_values_re = r'<!-- Optional Values Saved into Every Record -->[\\s\\S]*?<!-- Bulk File Upload Progress with Live Percentage -->'"
replacement = "old_opt_values_re = r'<div class=\"card\" id=\"optValuesCard\"[\\s\\S]*?</div>\\s*</div>\\s*</div>(?=\\s*<!-- Duplicate Handling -->)'"

sub_target = "box_inv_html = re.sub(old_opt_values_re, new_opt_values_html + \"\\n\\n          <!-- Bulk File Upload Progress with Live Percentage -->\", box_inv_html, count=1)"
sub_replacement = "box_inv_html = re.sub(old_opt_values_re, new_opt_values_html, box_inv_html, count=1)"

if target in text:
    text = text.replace(target, replacement).replace(sub_target, sub_replacement)
    with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated opt_values replacement in build_clean_modular_app.py')
else:
    print('Target not found')

