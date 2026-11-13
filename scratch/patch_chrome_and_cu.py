with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

core_helpers = """
    const myRole = () => {
      const u = getUser();
      return u.role || (u.is_admin ? 'admin' : 'standard');
    };

    async function loadCU() {
      try {
        const res = await api('/api/customers');
        if (Array.isArray(res)) CU = res;
      } catch(e) {}
      return CU;
    }

    async function updateChrome() {
      try {
        const u = getUser();
        const h = new Date().getHours();
        let greet = 'Good morning';
        if (h >= 12 && h < 17) greet = 'Good afternoon';
        else if (h >= 17) greet = 'Good evening';
        if ($('hi')) $('hi').textContent = `${greet}, ${u.name || u.user_id || 'Shilish Reddy'}`;
        const uInitial = ((u.name || u.user_id || 'U')[0] || 'U').toUpperCase();
        if ($('userAvatarCircle')) $('userAvatarCircle').textContent = uInitial;
        const r = (u.role || (u.is_admin ? 'admin' : 'standard')).toUpperCase();
        if ($('rolePill')) {
          $('rolePill').textContent = r;
          $('rolePill').className = `role-pill ${r.toLowerCase().includes('admin') ? 'admin' : 'standard'}`;
        }
      } catch(e) {}
    }

    const showBstplLoader = (msg, pct) => {};
    const hideBstplLoader = () => {};
"""

anchor = "function openBulkEditImeiModal() {"
assert anchor in text, "anchor not found in build_clean_modular_app.py"

if 'async function loadCU()' not in text:
    text = text.replace(anchor, core_helpers + "\n    " + anchor, 1)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added loadCU, updateChrome, myRole, and loader helpers to build_clean_modular_app.py!")

