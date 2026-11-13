with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    text = f.read()

from patch_all_enhancements import new_home_block

home_start = text.find("feature_blocks['HOME'] = r\"\"\"")
marker = "feature_dialogs = loc['feature_dialogs']"
idx = text.find(marker, home_start)

if home_start != -1 and idx != -1:
    # Find the closing triple quotes right before feature_dialogs
    q_idx = text.rfind('"""', home_start, idx)
    text = text[:home_start] + new_home_block + "\n\n" + text[idx:]
    with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("✓ Successfully replaced feature_blocks['HOME']!")
else:
    print(f"Failed to find bounds: home_start={home_start}, idx={idx}")

