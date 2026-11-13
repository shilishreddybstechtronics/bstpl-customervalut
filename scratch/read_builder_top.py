with open('scratch/build_clean_modular_webpages.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("build_clean_modular_webpages.py length:", len(text))
for line in text.splitlines()[:50]:
    print(line)

