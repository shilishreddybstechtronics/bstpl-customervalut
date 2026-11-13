with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

avatar_fns = """
    function avatarHtml(c) {
      const a = (c && c.avatar) || '';
      return a.startsWith('data:image/') ? `<img class="av" alt="" src="${esc(a)}">` : `<span class="av">${esc(a || '🏢')}</span>`;
    }

    function alertSummary(list) {
      if (!Array.isArray(list)) return '';
      const t = new Date(); t.setHours(0, 0, 0, 0);
      let x = 0, w = 0, m = 0;
      list.forEach(d => {
        if (!d.expiry_date) return;
        const n = Math.round((new Date(d.expiry_date) - t) / 864e5);
        if (n < 0) x++; else if (n <= 7) w++; else m++;
      });
      return `🔴 ${x} expired · 🟠 ${w} within 7 days · 🟡 ${m} within 30 days`;
    }
"""

anchor = "async function loadCU() {"
assert anchor in text, "anchor not found in build_clean_modular_app.py"

if 'function avatarHtml(c)' not in text:
    text = text.replace(anchor, avatar_fns + "\n    " + anchor, 1)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added avatarHtml and alertSummary to build_clean_modular_app.py successfully!")

