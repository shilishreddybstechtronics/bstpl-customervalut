import re

with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Locate the start of Optional Values and end of Upload Policy script
start_target = '<!-- Optional Values Saved into Every Record -->'
end_target = "document.getElementById('polGrid').addEventListener('change',function(e){var m=document.getElementById('dupMode');m.value=e.target.value;m.dispatchEvent(new Event('change'))});</script>"

start_idx = content.find(start_target)
end_idx = content.find(end_target)

assert start_idx != -1, "start_target not found"
assert end_idx != -1, "end_target not found"
end_idx += len(end_target)

print("Found section between", start_idx, "and", end_idx)
print("Original section length:", end_idx - start_idx)

new_section_html = """<!-- Optional Values Saved into Every Record (Redesigned Enterprise Card) -->
          <div class="card" id="optValuesCard" style="padding:22px 24px;border:1px solid var(--line);border-radius:16px;margin:18px 0;background:var(--card);box-shadow:0 3px 14px rgba(0,0,0,0.03)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;flex-wrap:wrap;gap:12px;border-bottom:1px solid var(--line);padding-bottom:14px">
              <div style="display:flex;align-items:center;gap:12px">
                <div style="width:40px;height:40px;border-radius:10px;background:var(--card-subtle);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0">
                  ⚙️
                </div>
                <div>
                  <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                    <h4 style="margin:0;font-size:15px;font-weight:800;color:var(--text)">Optional Values</h4>
                    <span class="badge" style="background:var(--card-subtle);border:1px solid var(--line);color:var(--muted);font-size:11px;font-weight:700;padding:2px 8px;border-radius:99px">
                      Saved into every record if blank in file
                    </span>
                  </div>
                  <p class="sub" style="margin:3px 0 0;font-size:12.5px;color:var(--muted)">
                    If the Excel row already has a value for any of these, the row's value wins.
                  </p>
                </div>
              </div>
              <span class="badge ok" style="font-size:11.5px;font-weight:700;padding:4px 10px;border-radius:99px;display:inline-flex;align-items:center;gap:5px">
                <span>💡</span> <span>Auto-Fill Fallback</span>
              </span>
            </div>

            <!-- 3 Group Columns: Device, Dates, SIM -->
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px">
              
              <!-- Group 1: Device Specs -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:14px;padding:16px">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;padding-bottom:8px;border-bottom:1px dashed var(--line)">
                  <span style="font-size:16px">📱</span>
                  <span style="font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:var(--text)">Device Attributes</span>
                </div>
                
                <!-- Model -->
                <div style="margin-bottom:12px">
                  <label for="optModel" style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:5px">
                    <span>📟</span> <span>Model</span>
                  </label>
                  <select id="optModel" style="width:100%;height:38px;padding:0 12px;font-size:13px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text);outline:none;transition:border-color 0.15s">
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
                  <input id="optNewModel" placeholder="Enter new model name…" style="margin-top:6px;width:100%;height:36px;padding:0 12px;font-size:12.5px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" hidden />
                </div>

                <!-- Firmware -->
                <div style="margin-bottom:12px">
                  <label for="optFirmware" style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:5px">
                    <span>🏷️</span> <span>Firmware</span>
                  </label>
                  <input id="optFirmware" placeholder="e.g. v2.4.1" style="width:100%;height:38px;padding:0 12px;font-size:13px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />
                </div>

                <!-- Flash -->
                <div>
                  <label for="optFlash" style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:5px">
                    <span>💾</span> <span>Flash</span>
                  </label>
                  <select id="optFlash" style="width:100%;height:38px;padding:0 12px;font-size:13px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text);outline:none">
                    <option value="">-- None / Keep from file --</option>
                    <option value="Winbond">Winbond</option>
                    <option value="Adesto">Adesto</option>
                  </select>
                </div>
              </div>

              <!-- Group 2: Important Dates -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:14px;padding:16px">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;padding-bottom:8px;border-bottom:1px dashed var(--line)">
                  <span style="font-size:16px">📅</span>
                  <span style="font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:var(--text)">Important Dates</span>
                </div>

                <!-- Dispatched Date -->
                <div style="margin-bottom:12px">
                  <label for="optDispatchedDate" style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:5px">
                    <span>📦</span> <span>Dispatched Date</span>
                  </label>
                  <input type="date" id="optDispatchedDate" style="width:100%;height:38px;padding:0 12px;font-size:13px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />
                </div>

                <!-- Activation Date -->
                <div style="margin-bottom:12px">
                  <label for="optActDate" style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:5px">
                    <span>⚡</span> <span>Activation Date</span>
                  </label>
                  <input type="date" id="optActDate" style="width:100%;height:38px;padding:0 12px;font-size:13px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />
                </div>

                <!-- Expiry Date -->
                <div>
                  <label for="optExpiryDate" style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:5px">
                    <span>⏳</span> <span>Expiry Date</span>
                  </label>
                  <input type="date" id="optExpiryDate" style="width:100%;height:38px;padding:0 12px;font-size:13px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />
                </div>
              </div>

              <!-- Group 3: SIM Configuration -->
              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:14px;padding:16px">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;padding-bottom:8px;border-bottom:1px dashed var(--line)">
                  <span style="font-size:16px">📶</span>
                  <span style="font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:0.5px;color:var(--text)">SIM &amp; Network Provider</span>
                </div>

                <!-- SIM Provider -->
                <div>
                  <label for="optSimProvider" style="font-size:12px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:5px">
                    <span>🏢</span> <span>SIM Provider</span>
                  </label>
                  <select id="optSimProvider" style="width:100%;height:38px;padding:0 12px;font-size:13px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text);outline:none">
                    <option value="">-- None / Keep from file --</option>
                    <optgroup label="TAISYS">
                      <option value="TAISYS (Airtel + BSNL)">TAISYS (Airtel + BSNL)</option>
                      <option value="TAISYS (VI + BSNL)">TAISYS (VI + BSNL)</option>
                      <option value="TAISYS (Airtel + VI)">TAISYS (Airtel + VI)</option>
                    </optgroup>
                    <optgroup label="SENSORISE">
                      <option value="SENSORISE (Airtel + BSNL)">SENSORISE (Airtel + BSNL)</option>
                      <option value="SENSORISE (VI + BSNL)">SENSORISE (VI + BSNL)</option>
                      <option value="SENSORISE (Airtel + VI)">SENSORISE (Airtel + VI)</option>
                    </optgroup>
                    <optgroup label="GROWSPACE">
                      <option value="GROWSPACE (Airtel + BSNL)">GROWSPACE (Airtel + BSNL)</option>
                      <option value="GROWSPACE (VI + BSNL)">GROWSPACE (VI + BSNL)</option>
                      <option value="GROWSPACE (Airtel + VI)">GROWSPACE (Airtel + VI)</option>
                    </optgroup>
                    <optgroup label="IOTIVITY">
                      <option value="IOTIVITY (Airtel + BSNL)">IOTIVITY (Airtel + BSNL)</option>
                      <option value="IOTIVITY (VI + BSNL)">IOTIVITY (VI + BSNL)</option>
                      <option value="IOTIVITY (Airtel + VI)">IOTIVITY (Airtel + VI)</option>
                    </optgroup>
                    <optgroup label="VI">
                      <option value="VI">VI</option>
                    </optgroup>
                  </select>
                  <p class="sub" style="margin:8px 0 0;font-size:11.5px;color:var(--muted);line-height:1.4">
                    Assigned to uploaded rows where the SIM provider column is empty.
                  </p>
                </div>
              </div>

            </div>
          </div>

          <!-- Upload Policy & Duplicate Handling (Redesigned Interactive Tile Cards) -->
          <div class="card" id="uploadPolicyCard" style="padding:22px 24px;border:1px solid var(--line);border-radius:16px;margin:18px 0;background:var(--card);box-shadow:0 3px 14px rgba(0,0,0,0.03)">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:10px;border-bottom:1px solid var(--line);padding-bottom:12px">
              <div style="display:flex;align-items:center;gap:12px">
                <div style="width:38px;height:38px;border-radius:10px;background:var(--card-subtle);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0">
                  🛡️
                </div>
                <div>
                  <h4 style="margin:0;font-size:15px;font-weight:800;color:var(--text)">Upload Policy</h4>
                  <p class="sub" style="margin:2px 0 0;font-size:12.5px;color:var(--muted)">Decides what happens to records that already exist in the database.</p>
                </div>
              </div>
              <span class="badge" style="background:var(--card-subtle);border:1px solid var(--line);font-size:11px;font-weight:700;padding:3px 10px;border-radius:99px">Select 1 Policy</span>
            </div>

            <!-- Hidden select kept for JS compatibility -->
            <select id="dupMode" hidden aria-hidden="true">
              <option value="both" selected>New entries + update changed values</option>
              <option value="skip">Skip duplicate entries</option>
              <option value="update">Update values only</option>
            </select>

            <div class="pol-grid" id="polGrid" role="radiogroup" aria-label="Upload policy" style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:14px">
              
              <!-- Option 1: Both (Default) -->
              <label class="pol-card active" data-val="both" style="position:relative;display:block;padding:16px 18px;border-radius:12px;border:2px solid var(--primary);background:rgba(29, 104, 225, 0.08);cursor:pointer;transition:all 0.2s ease">
                <div style="display:flex;align-items:flex-start;gap:12px">
                  <input type="radio" name="polPick" value="both" checked style="margin-top:3px;accent-color:var(--primary);width:16px;height:16px;cursor:pointer" />
                  <div style="flex:1">
                    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:4px">
                      <b style="font-size:13.5px;color:var(--text);font-weight:800">New entries + update</b>
                      <span class="badge ok" style="font-size:10px;padding:1px 6px;border-radius:99px;font-weight:800">Recommended</span>
                    </div>
                    <span style="display:block;font-size:12px;color:var(--muted);line-height:1.45">Add records that are not in the database and replace changed values on existing ones.</span>
                  </div>
                </div>
              </label>

              <!-- Option 2: Skip -->
              <label class="pol-card" data-val="skip" style="position:relative;display:block;padding:16px 18px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);cursor:pointer;transition:all 0.2s ease">
                <div style="display:flex;align-items:flex-start;gap:12px">
                  <input type="radio" name="polPick" value="skip" style="margin-top:3px;accent-color:var(--primary);width:16px;height:16px;cursor:pointer" />
                  <div style="flex:1">
                    <div style="margin-bottom:4px">
                      <b style="font-size:13.5px;color:var(--text);font-weight:800">Skip duplicate entries</b>
                    </div>
                    <span style="display:block;font-size:12px;color:var(--muted);line-height:1.45">Add new records only. Existing records are left untouched and listed as skipped.</span>
                  </div>
                </div>
              </label>

              <!-- Option 3: Update only -->
              <label class="pol-card" data-val="update" style="position:relative;display:block;padding:16px 18px;border-radius:12px;border:1.5px solid var(--line);background:var(--card);cursor:pointer;transition:all 0.2s ease">
                <div style="display:flex;align-items:flex-start;gap:12px">
                  <input type="radio" name="polPick" value="update" style="margin-top:3px;accent-color:var(--primary);width:16px;height:16px;cursor:pointer" />
                  <div style="flex:1">
                    <div style="margin-bottom:4px">
                      <b style="font-size:13.5px;color:var(--text);font-weight:800">Update values only</b>
                    </div>
                    <span style="display:block;font-size:12px;color:var(--muted);line-height:1.45">Never add records. Only replace changed values on records that already exist.</span>
                  </div>
                </div>
              </label>

            </div>
          </div>
          <script>
            (function() {
              const grid = document.getElementById('polGrid');
              const dupSel = document.getElementById('dupMode');
              if (!grid || !dupSel) return;
              
              function syncPolCards(selectedVal) {
                grid.querySelectorAll('.pol-card').forEach(card => {
                  const isMatch = card.dataset.val === selectedVal;
                  if (isMatch) {
                    card.style.borderColor = 'var(--primary)';
                    card.style.background = 'rgba(29, 104, 225, 0.08)';
                    card.classList.add('active');
                  } else {
                    card.style.borderColor = 'var(--line)';
                    card.style.background = 'var(--card)';
                    card.classList.remove('active');
                  }
                });
              }

              grid.addEventListener('change', function(e) {
                if (e.target && e.target.name === 'polPick') {
                  dupSel.value = e.target.value;
                  syncPolCards(e.target.value);
                  dupSel.dispatchEvent(new Event('change'));
                }
              });
            })();
          </script>"""

updated_content = content[:start_idx] + new_section_html + content[end_idx:]

with open('frontend/inventory.html', 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("Updated frontend/inventory.html successfully!")

