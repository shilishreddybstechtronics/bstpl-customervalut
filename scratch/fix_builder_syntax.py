with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    text = f.read()

# Fix literal newline in string concatenation
text = text.replace('feature_blocks[\'SIM\'] = loc[\'feature_blocks\'][\'SIM\'] + "\n\n" + restore_all_js', 'feature_blocks[\'SIM\'] = loc[\'feature_blocks\'][\'SIM\'] + "\\n\\n" + restore_all_js')
text = text.replace('feature_blocks[\'INV\'] = enhanced_inv_js + "\n\n" + sim_block_copy', 'feature_blocks[\'INV\'] = enhanced_inv_js + "\\n\\n" + sim_block_copy')
text = text.replace('replace("wrap.innerHTML = html;", "wrap.innerHTML = html;\\n" + nf_filter_listener)', 'replace("wrap.innerHTML = html;", "wrap.innerHTML = html;\\n\\n" + nf_filter_listener)')

with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Builder syntax strings fixed!")

