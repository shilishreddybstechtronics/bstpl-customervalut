with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "'<!-- Optional Values Saved into Every Record -->[\\\\s\\\\S]*?<!-- Bulk File Upload Progress with Live Percentage -->'"
replacement = "'<!-- Optional Values Saved into Every Record -->[\\\\s\\\\S]*?<!-- Duplicate Handling -->'"

target_sub = 'box_inv_html, count=1)'
# Check if target is present
if target in text:
    text = text.replace(target, replacement)
    text = text.replace(
        '<!-- Bulk File Upload Progress with Live Percentage -->", box_inv_html, count=1)',
        '<!-- Duplicate Handling -->", box_inv_html, count=1)'
    )
    with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated opt_values regex in build_clean_modular_app.py")
else:
    print("Target string not found in build_clean_modular_app.py")

