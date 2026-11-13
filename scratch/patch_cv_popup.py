with open('frontend/cv-popup.js', 'r', encoding='utf-8') as f:
    c = f.read()

target = "b.querySelector('[data-act=go]').onclick = () => close([...b.querySelectorAll('.cvp-cols input:checked')].map(i => i.value));"
replacement = """const noBtn = b.querySelector('[data-act=no]');
        if (noBtn) noBtn.onclick = (e) => { e.stopPropagation(); close(null); };
        const goBtn = b.querySelector('[data-act=go]');
        if (goBtn) goBtn.onclick = (e) => {
          e.stopPropagation();
          const selected = [...b.querySelectorAll('.cvp-cols input:checked')].map(i => i.value);
          close(selected.length ? selected : null);
        };"""

if target in c:
    c = c.replace(target, replacement)
    with open('frontend/cv-popup.js', 'w', encoding='utf-8') as f:
        f.write(c)
    print("SUCCESS: Patched cv-popup.js!")
else:
    print("ERROR: target not found in cv-popup.js")

