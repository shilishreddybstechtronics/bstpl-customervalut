with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "feature_blocks = loc['feature_blocks']"
hook = "feature_blocks = loc['feature_blocks']\nfeature_blocks['INV'] = feature_blocks['INV'].replace('initBulkUploadContainer();', 'if (typeof initBulkUploadContainer === \"function\") initBulkUploadContainer();')\n"

if 'if (typeof initBulkUploadContainer ===' not in text:
    text = text.replace(target, hook, 1)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated feature_blocks['INV'] safe caller in build_clean_modular_app.py!")

