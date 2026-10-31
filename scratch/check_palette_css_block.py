with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Check where palettes are defined
pos_palettes_start = text.find('/* ===== 6 PREMIER THEMES (with Dark & Light Mode Support) ===== */')
pos_palettes_end = text.find('/* --- Responsive Tweaks --- */', pos_palettes_start)
if pos_palettes_end == -1:
    pos_palettes_end = text.find('[data-palette] body {', pos_palettes_start)

print(f"Palettes start: {pos_palettes_start}, end: {pos_palettes_end}")
print(text[pos_palettes_start:pos_palettes_start+300])

