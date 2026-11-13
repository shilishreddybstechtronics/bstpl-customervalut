with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    text = f.read()

target1 = 'enhanced_inv_js = enhanced_inv_js.replace("await loadCustomerFilesContainer();", "await loadCustomerFilesContainer();\n" + cust_files_handlers)'
target2 = 'fetch_block = fetch_block.replace("wrap.innerHTML = html;", "wrap.innerHTML = html;\n" + nf_filter_listener)'

# We replace them with valid python literals
text = text.replace('enhanced_inv_js = enhanced_inv_js.replace("await loadCustomerFilesContainer();", "await loadCustomerFilesContainer();\n" + cust_files_handlers)',
                    'enhanced_inv_js = enhanced_inv_js.replace("await loadCustomerFilesContainer();", "await loadCustomerFilesContainer();\\n" + cust_files_handlers)')

text = text.replace('fetch_block = fetch_block.replace("wrap.innerHTML = html;", "wrap.innerHTML = html;\n" + nf_filter_listener)',
                    'fetch_block = fetch_block.replace("wrap.innerHTML = html;", "wrap.innerHTML = html;\\n" + nf_filter_listener)')

with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Fixed line breaks in python literals!")

