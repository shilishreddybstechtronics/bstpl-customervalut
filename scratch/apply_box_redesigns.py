import re, sys

print("=== Applying Redesigned Search Term, Search Value(s), IMEI & Optional Values ===")

with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# -----------------------------------------------------------------------------
# 1. Customization for containers['box-inv']: Redesign Search Term Box
# -----------------------------------------------------------------------------
new_inv_search_html = """          <div class="grow" style="min-width:300px">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
              <label for="invQuery" style="font-size:12.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px">
                <span style="font-size:14px">🔎</span> <span>Search Term</span>
              </label>
              <span style="font-size:11px;color:var(--muted);font-weight:600">Type or press Enter to filter</span>
            </div>
            <div style="position:relative;display:flex;align-items:center">
              <span style="position:absolute;left:13px;color:var(--primary);font-size:15px;pointer-events:none;opacity:0.85">🔍</span>
              <input id="invQuery" placeholder="Type value to search…" autocomplete="off"
                style="width:100%;height:42px;padding:0 38px 0 38px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;font-weight:600;box-shadow:0 1px 3px rgba(0,0,0,0.04);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)" />
              <button class="b" id="invClear" type="button" title="Clear search"
                style="position:absolute;right:8px;height:26px;width:26px;border-radius:50%;padding:0;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;background:var(--line);color:var(--muted);border:none;cursor:pointer;transition:all 0.15s">✕</button>
            </div>
          </div>"""

old_inv_search_re = r'<div class="grow">\s*<label for="invQuery">Search Term</label>\s*<input id="invQuery"[^>]*>\s*</div>\s*<button class="b" id="invClear"[^>]*>Clear</button>'

# -----------------------------------------------------------------------------
# 2. Customization for containers['box-inv']: Redesign Optional Values Card
# -----------------------------------------------------------------------------
new_opt_values_html = """          <!-- Optional Values Saved into Every Record (Redesigned Enterprise Card) -->
          <div class="card" id="optValuesCard"
            style="padding:22px 24px;border:1.5px solid var(--line);border-radius:16px;margin:18px 0;background:var(--card);box-shadow:0 4px 20px rgba(0,0,0,0.03);transition:all 0.2s ease">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:10px;border-bottom:1px solid var(--line);padding-bottom:14px">
              <div style="display:flex;align-items:center;gap:12px">
                <div style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg, rgba(56,189,248,0.18), rgba(99,102,241,0.18));color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800">
                  ⚙️
                </div>
                <div>
                  <h4 style="margin:0;font-size:15.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:8px">
                    Optional Values (Saved into every record if blank in file)
                  </h4>
                  <p class="sub" style="margin:3px 0 0;font-size:12px;color:var(--muted)">
                    If the Excel row already has a value for any of these, the row's value wins.
                  </p>
                </div>
              </div>
              <span class="badge" style="background:var(--card-subtle);border:1px solid var(--line);color:var(--text);font-size:11.5px;font-weight:700;padding:4px 12px;border-radius:99px;display:inline-flex;align-items:center;gap:6px">
                <span>💡</span> <span>Auto-Fill Fallback</span>
              </span>
            </div>

            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:14px">
              <!-- Field 1: Model -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">
                <label for="optModel" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">
                  <span>📟</span> <span>Model</span>
                </label>
                <select id="optModel" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)">
                  <option value="">-- None / Keep from file --</option>
                  <option value="17IS">17IS</option>
                  <option value="17L">17L</option>
                  <option value="17IS-CAN">17IS-CAN</option>
                  <option value="17A">17A</option>
                  <option value="17S">17S</option>
                  <option value="13L">13L</option>
                  <option value="13S">13S</option>
                  <option value="55L">55L</option>
                  <option value="__new__">+ New model…</option>
                </select>
                <input id="optNewModel" placeholder="Enter new model name…" style="margin-top:6px;width:100%;height:36px;padding:0 10px;font-size:12px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" hidden />
              </div>

              <!-- Field 2: Dispatched Date -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">
                <label for="optDispatchedDate" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">
                  <span>📦</span> <span>Dispatched Date</span>
                </label>
                <input type="date" id="optDispatchedDate" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />
              </div>

              <!-- Field 3: Activation Date -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">
                <label for="optActDate" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">
                  <span>⚡</span> <span>Activation Date</span>
                </label>
                <input type="date" id="optActDate" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />
              </div>

              <!-- Field 4: Expiry Date -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">
                <label for="optExpiryDate" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">
                  <span>⏳</span> <span>Expiry Date</span>
                </label>
                <input type="date" id="optExpiryDate" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />
              </div>

              <!-- Field 5: Flash -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">
                <label for="optFlash" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">
                  <span>💾</span> <span>Flash</span>
                </label>
                <select id="optFlash" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)">
                  <option value="">-- None / Keep from file --</option>
                  <option value="Winbond">Winbond</option>
                  <option value="Adesto">Adesto</option>
                </select>
              </div>

              <!-- Field 6: Firmware -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">
                <label for="optFirmware" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">
                  <span>🏷️</span> <span>Firmware</span>
                </label>
                <input id="optFirmware" placeholder="e.g. v2.4.1" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />
              </div>

              <!-- Field 7: SIM Provider -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">
                <label for="optSimProvider" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">
                  <span>📶</span> <span>SIM Provider</span>
                </label>
                <select id="optSimProvider" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)">
                  <option value="">-- None / Keep from file --</option>
                  <option value="Airtel">Airtel</option>
                  <option value="Vodafone">Vodafone</option>
                  <option value="Jio">Jio</option>
                  <option value="BSNL">BSNL</option>
                </select>
              </div>
            </div>
          </div>"""

old_opt_values_re = r'<!-- Optional Values Saved into Every Record -->[\s\S]*?<!-- Bulk File Upload Progress with Live Percentage -->'

# -----------------------------------------------------------------------------
# 3. Customization for containers['box-fetch']: Redesign Search Value(s) Box
# -----------------------------------------------------------------------------
new_fetch_query_html = """            <div style="flex:2;min-width:320px">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
                <label for="fq" style="font-size:12.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px">
                  <span style="font-size:14px">🎯</span> <span>Search Value(s)</span>
                </label>
                <span class="sub" style="font-size:11px;color:var(--muted);font-weight:600">Comma / newline separated values supported</span>
              </div>
              <div style="position:relative;display:flex;align-items:center">
                <span style="position:absolute;left:14px;color:var(--primary);font-size:15px;pointer-events:none;opacity:0.85">🔎</span>
                <input id="fq" placeholder="Enter term or paste comma/newline separated values (leave empty to list all)…"
                  style="width:100%;height:44px;padding:0 36px 0 40px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13px;font-weight:600;box-shadow:0 1px 3px rgba(0,0,0,0.04);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)" />
                <button type="button" id="fqClearBtn" title="Clear query" onclick="const q = document.getElementById('fq'); if(q){q.value=''; q.focus();}"
                  style="position:absolute;right:9px;height:26px;width:26px;border-radius:50%;border:none;background:var(--line);color:var(--muted);font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.15s">✕</button>
              </div>
            </div>"""

old_fetch_query_re = r'<div>\s*<label for="fq"[^>]*>Search Value\(s\)</label>\s*<input id="fq"[^>]*>\s*</div>'

# -----------------------------------------------------------------------------
# 4. Customization for containers['box-edit']: Redesign IMEI Box
# -----------------------------------------------------------------------------
new_edit_imei_html = """      <!-- Single IMEI Record Editor (Redesigned Modern Card) -->
      <div class="card" style="padding:22px 24px;border:1.5px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:18px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px">
          <div>
            <h3 style="margin:0 0 4px 0; font-size:16px; font-weight:800; color:var(--text);display:flex;align-items:center;gap:8px">
              <span style="font-size:18px">📱</span> <span>Edit / Delete Individual Record</span>
            </h3>
            <p class="sub" style="margin:0; font-size:12.5px;color:var(--muted)">Find an individual device record by its unique 15-digit IMEI to update metadata or delete.</p>
          </div>
          <span class="badge" style="background:var(--card-subtle);border:1px solid var(--line);color:var(--text);font-size:11.5px;font-weight:700;padding:4px 10px;border-radius:99px">
            🔢 Standard 15 Digits
          </span>
        </div>

        <div style="display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap">
          <div style="flex:1;min-width:280px">
            <label for="ei" style="font-size:12.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">
              <span>IMEI</span> <span style="font-size:11px;font-weight:600;color:var(--muted)">(15-Digit Device Identifier)</span>
            </label>
            <div style="position:relative;display:flex;align-items:center">
              <span style="position:absolute;left:14px;color:var(--primary);font-size:16px;pointer-events:none;opacity:0.85">📱</span>
              <input id="ei" placeholder="Enter 15-digit IMEI…" maxlength="20" autocomplete="off"
                style="width:100%;height:44px;padding:0 36px 0 42px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-family:monospace;font-size:14.5px;font-weight:700;letter-spacing:0.8px;box-shadow:inset 0 1px 3px rgba(0,0,0,0.04);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)" />
              <button type="button" id="eiClearBtn" title="Clear IMEI" onclick="const i = document.getElementById('ei'); if(i){i.value=''; i.focus();}"
                style="position:absolute;right:10px;height:24px;width:24px;border-radius:50%;border:none;background:var(--line);color:var(--muted);font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;cursor:pointer">✕</button>
            </div>
          </div>
          <button class="b p" id="eg" type="button"
            style="height:44px;padding:0 24px;font-size:13.5px;font-weight:800;border-radius:10px;background:linear-gradient(135deg, var(--primary), var(--primary-hover, #0a1c3d));color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 4px 14px rgba(15,43,92,0.25);cursor:pointer;transition:all 0.2s ease">
            <span>🔍</span> <span>Find Record</span>
          </button>
        </div>
        <div id="er" style="margin-top:14px"></div>
      </div>"""

old_edit_imei_re = r'<!-- Single IMEI Record Editor -->[\s\S]*?<div id="er"></div>\s*</div>'

# -----------------------------------------------------------------------------
# Insert customizations into scratch/build_clean_modular_app.py
# -----------------------------------------------------------------------------
custom_block = f"""
# --- Redesigned Boxes (Requirement: Search Term, Search Value(s), IMEI & Optional Values) ---
# 1. Redesign Search Term in box_inv_html
box_inv_html = re.sub({repr(old_inv_search_re)}, {repr(new_inv_search_html)}, box_inv_html, count=1)

# 2. Redesign Optional Values Card in box_inv_html
box_inv_html = re.sub({repr(old_opt_values_re)}, {repr(new_opt_values_html)} + "\\n\\n          <!-- Bulk File Upload Progress with Live Percentage -->", box_inv_html, count=1)

containers['box-inv'] = box_inv_html

# 3. Redesign Search Value(s) in containers['box-fetch']
containers['box-fetch'] = re.sub({repr(old_fetch_query_re)}, {repr(new_fetch_query_html)}, containers['box-fetch'], count=1)

# 4. Redesign IMEI in containers['box-edit']
containers['box-edit'] = re.sub({repr(old_edit_imei_re)}, {repr(new_edit_imei_html)}, containers['box-edit'], count=1)
"""

anchor = "containers['box-inv'] = box_inv_html"
if anchor in text and "Redesign Search Term in box_inv_html" not in text:
    text = text.replace(anchor, anchor + "\n" + custom_block, 1)
    print("✓ Successfully injected redesigned boxes into build_clean_modular_app.py")
else:
    print("Target anchor not found or already injected")

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("=== build_clean_modular_app.py updated successfully ===")

