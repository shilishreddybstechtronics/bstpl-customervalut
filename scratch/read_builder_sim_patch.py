with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(1480, 1570):
    if i < len(lines):
        print(f"{i+1}: {repr(lines[i][:100])}")

