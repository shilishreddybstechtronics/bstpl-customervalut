with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("sbLiveDevCount count:", text.count("sbLiveDevCount"))
print("loadHealthContainer count:", text.count("loadHealthContainer"))
print("feature_blocks['INV'] count:", text.count("feature_blocks['INV']"))
print("containers['box-home'] count:", text.count("containers['box-home']"))
print("generate_sidebar count:", text.count("def generate_sidebar"))
print("BASE_CSS count:", text.count("BASE_CSS ="))

