import re, sys

print("Applying website enhancements to scratch/build_clean_modular_app.py...")

with open("scratch/build_clean_modular_app.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update BASE_CSS with modern search & pagination styling
search_css = """
    /* =========================================================================
       MODERN SEARCH CONTAINER & CONTROLS (Requirement 2 & 5)
       ========================================================================= */
    .cv-search-container {
      position: relative;
      display: flex;
      align-items: center;
      flex: 1;
      min-width: 240px;
    }
    .cv-search-container .cv-search-icon-left {
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      pointer-events: none;
      font-size: 14px;
      color: var(--muted);
      opacity: 0.75;
      z-index: 2;
    }
    .cv-search-container input.cv-search-input {
      width: 100%;
      height: 40px;
      padding: 0 42px 0 38px;
      border-radius: 10px;
      border: 1.5px solid var(--line);
      background: var(--input-bg, var(--card));
      color: var(--text);
      font-size: 13.5px;
      font-family: inherit;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .cv-search-container input.cv-search-input:focus {
      border-color: var(--primary);
      background: var(--card);
      box-shadow: 0 0 0 3px rgba(29, 104, 225, 0.16);
      outline: none;
    }
    .cv-search-container .cv-search-clear-btn {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      background: transparent;
      border: none;
      color: var(--muted);
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      padding: 4px;
      line-height: 1;
      border-radius: 50%;
      display: none;
      z-index: 2;
    }
    .cv-search-container .cv-search-clear-btn:hover {
      color: var(--danger);
      background: rgba(239, 68, 68, 0.12);
    }
    .cv-search-container .cv-search-spinner {
      position: absolute;
      right: 36px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 13px;
      animation: cv-spin 1s linear infinite;
      display: none;
      z-index: 2;
    }
    @keyframes cv-spin {
      100% { transform: translateY(-50%) rotate(360deg); }
    }

    /* =========================================================================
       DATA HEALTH PAGINATION CONTROLS (Requirement 3)
       ========================================================================= */
    .dh-pagination-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 16px;
      background: var(--card-subtle);
      border: 1px solid var(--line);
      border-radius: 10px;
      margin: 12px 0;
    }
    .dh-pagination-controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .dh-page-btn {
      height: 32px;
      padding: 0 12px;
      border-radius: 7px;
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      border: 1px solid var(--line);
      background: var(--card);
      color: var(--text);
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .dh-page-btn:hover:not(:disabled) {
      border-color: var(--primary);
      color: var(--primary);
      background: rgba(29, 104, 225, 0.08);
    }
    .dh-page-btn:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    .dh-select-all-btn {
      height: 32px;
      padding: 0 12px;
      border-radius: 7px;
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      border: 1px solid var(--line);
      background: var(--card);
      color: var(--text);
      transition: all 0.15s ease;
    }
    .dh-select-all-btn.active {
      background: var(--primary);
      border-color: var(--primary);
      color: #fff;
    }
    .dh-page-info {
      font-size: 12.5px;
      font-weight: 700;
      color: var(--muted);
    }
"""

if ".cv-search-container" not in text:
    target_css_end = "th, td { border: 1px solid #ddd !important; padding: 6px 8px !important; }\n    }\n\"\"\""
    if target_css_end in text:
        text = text.replace(target_css_end, "th, td { border: 1px solid #ddd !important; padding: 6px 8px !important; }\n    }\n" + search_css + "\n\"\"\"")
        print("✓ Appended search & pagination CSS to BASE_CSS")
    else:
        print("! Warning: target_css_end not found")

# 2. Sidebar dynamic counts: Replace 117,783 and 154 with — in generate_sidebar
text = text.replace('<span class="cv-sb-metric-val" id="sbLiveDevCount">117,783</span>', '<span class="cv-sb-metric-val" id="sbLiveDevCount">—</span>')
text = text.replace('<span class="cv-sb-metric-val" id="sbLiveCustCount">154</span>', '<span class="cv-sb-metric-val" id="sbLiveCustCount">—</span>')
print("✓ Replaced static counts in sidebar template with dynamic placeholders (—)")

# 3. Replace static counts in home_top_elements
replacement_code = """
feature_dialogs = loc['feature_dialogs']
home_top_elements = loc['home_top_elements']
# Remove hardcoded static numbers from home_top_elements
home_top_elements = home_top_elements.replace('>154<', '>—<').replace('>117,783<', '>—<').replace('>117,781<', '>—<').replace('>90<', '>—<')
"""
text = text.replace("feature_dialogs = loc['feature_dialogs']\nhome_top_elements = loc['home_top_elements']", replacement_code)
print("✓ Added dynamic replacements for home_top_elements")

with open("scratch/build_clean_modular_app.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Builder base updated successfully!")

