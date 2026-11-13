with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Verify header action buttons block
header_acts_marker = '<div class="cv-header-actions acts"'
idx_marker = text.find(header_acts_marker)
print("Header acts found at:", idx_marker)

# Verify settings options block
settings_options_marker = '<!-- Options shifted from top bar into Settings -->'
idx_settings = text.find(settings_options_marker)
print("Settings options found at:", idx_settings)

theme_marker = '<!-- Themes & Look (7 Themes + Light/Dark Mode) -->'
idx_theme = text.find(theme_marker, idx_settings)
print("Theme marker found at:", idx_theme)

slice_to_remove = text[idx_settings:idx_theme]
print("Slice to remove from settings:\n", slice_to_remove)

