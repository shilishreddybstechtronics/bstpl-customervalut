import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Rename "Device Records" to "Fetch Data" in sidebar
old_device_records = '''        <button class="cv-nav-item" data-target="box-fetch" title="Device Records &amp; Fetch">
          <span class="cv-nav-ico">📱</span>
          <span class="cv-nav-label">Device Records</span>
        </button>'''

new_fetch_data = '''        <button class="cv-nav-item" data-target="box-fetch" title="Fetch Data">
          <span class="cv-nav-ico">🔍</span>
          <span class="cv-nav-label">Fetch Data</span>
        </button>'''

assert old_device_records in text, "old_device_records not found"
text = text.replace(old_device_records, new_fetch_data, 1)

# 2. In box-home: Keep ONLY the Live Updates option
home_start = text.find('<section class="container-box active" id="box-home"')
home_end = text.find('</section>', home_start) + 10
assert home_start != -1 and home_end != -1, "box-home range not found"

new_box_home = '''      <!-- =========================================================================
         CONTAINER 0: HOME OVERVIEW (Live Update Option Only -> Opens Live Telemetry Popup)
         ========================================================================= -->
      <section class="container-box active" id="box-home" style="padding:0;background:transparent;border:none;box-shadow:none">
        <!-- Live Updates Centerpiece Option Card -->
        <div class="card" id="homeLiveUpdatesCard" style="margin:0;padding:28px 32px;border:1.5px solid #38bdf8;border-radius:20px;background:linear-gradient(135deg, #0b1120 0%, #0f172a 50%, #1e293b 100%);color:#fff;box-shadow:0 12px 35px rgba(14,165,233,0.2);cursor:pointer;transition:transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.25s ease" onclick="openLiveUpdatesModal()">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:20px">
            <div style="display:flex;align-items:center;gap:18px">
              <div style="width:58px;height:58px;border-radius:16px;background:rgba(56,189,248,0.2);color:#38bdf8;display:flex;align-items:center;justify-content:center;font-size:30px;box-shadow:0 0 25px rgba(56,189,248,0.35);flex-shrink:0">
                ⚡
              </div>
              <div>
                <div style="display:flex;align-items:center;gap:10px">
                  <h3 style="margin:0;font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.2px">Live Updates &amp; Telemetry Stream</h3>
                  <span class="live-badge" style="background:#10b981;color:#fff;font-size:11px;padding:3px 10px;border-radius:99px;font-weight:800;letter-spacing:0.5px">
                    <span class="cv-live-dot-pulse"></span> LIVE
                  </span>
                </div>
                <p style="margin:6px 0 0;font-size:13.5px;color:#94a3b8;line-height:1.4">
                  Real-time device tracking, telemetry stream, inventory health diagnostics &amp; live customer database synchronization.
                </p>
                <div style="margin-top:10px;font-size:12.5px;color:#38bdf8;font-weight:700;display:flex;align-items:center;gap:6px">
                  <span>👉 Click to open live stream, metrics &amp; telemetry popup</span>
                </div>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:12px">
              <button class="b" type="button" style="background:linear-gradient(135deg, #0284c7, #2563eb);color:#fff;font-weight:800;font-size:14px;border:none;border-radius:10px;padding:12px 24px;box-shadow:0 4px 18px rgba(37,99,235,0.4);cursor:pointer;display:inline-flex;align-items:center;gap:8px" onclick="event.stopPropagation(); openLiveUpdatesModal();">
                <span>⚡ Open Live Telemetry Stream</span>
              </button>
            </div>
          </div>
        </div>
      </section>'''

text = text[:home_start] + new_box_home + text[home_end:]

# 3. Ensure showContainer guarantees ONLY the selected container is displayed and all others hidden
old_container_loop = '''        document.querySelectorAll('.container-box').forEach(box => {
          const isActive = box.id === boxId;
          box.classList.toggle('active', isActive);
          if (isActive) {
            box.style.display = 'block';
          }
        });'''

new_container_loop = '''        document.querySelectorAll('.container-box').forEach(box => {
          const isActive = box.id === boxId;
          box.classList.toggle('active', isActive);
          box.style.display = isActive ? 'block' : 'none';
        });'''

assert old_container_loop in text, "old_container_loop not found"
text = text.replace(old_container_loop, new_container_loop, 1)

# Save to frontend/index.html & frontend/dashboard.html
with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('frontend/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied Fetch Data rename, Home live update option, and strict container isolation successfully!")

