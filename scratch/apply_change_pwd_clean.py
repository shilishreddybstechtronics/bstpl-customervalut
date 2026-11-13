with open("frontend/index.html", "r", encoding="utf-8") as f:
    text = f.read()

target = """      if ($('btnConfirmChangePw')) $('btnConfirmChangePw').onclick = e => {
        if ($('pf')) {
          if (typeof $('pf').requestSubmit === 'function') {
            $('pf').requestSubmit();
          } else {
            $('pf').dispatchEvent(new Event('submit', { cancelable: true }));
          }
        }
      };

      if ($('pf')) $('pf').onsubmit = async e => {
        e.preventDefault();
        const pe = $('pe');
        if (pe) { pe.textContent = ''; pe.hidden = true; }
        const curPw = $('p1')?.value || '';
        const newPw = $('p2')?.value || '';
        const repPw = $('p3')?.value || '';

        if (!curPw) {
          if (pe) { pe.textContent = 'Please enter your current password.'; pe.hidden = false; }
          return;
        }
        if (!newPw || newPw.length < 8) {
          if (pe) { pe.textContent = 'New password must be at least 8 characters long.'; pe.hidden = false; }
          return;
        }
        if (newPw !== repPw) {
          if (pe) { pe.textContent = 'New password and confirm new password do not match.'; pe.hidden = false; }
          return;
        }

        const btn = $('btnConfirmChangePw');
        if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; }

        try {
          const r = await api('/api/me/password', { method: 'POST', body: JSON.stringify({ current_password: curPw, new_password: newPw }) });
          if (r.access_token) { tok = r.access_token; localStorage.setItem('token', tok); }
          closeChangePasswordModal();
          toast('Password updated successfully in website & database');
        } catch (err) {
          if (pe) { pe.textContent = err.message || 'Failed to update password.'; pe.hidden = false; }
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = 'Confirm & Change Password'; }
        }
      };"""

replacement = """      async function submitChangePasswordModal() {
        const pe = $('pe');
        if (pe) { pe.textContent = ''; pe.hidden = true; }
        const curPw = $('p1')?.value || '';
        const newPw = $('p2')?.value || '';
        const repPw = $('p3')?.value || '';

        if (!curPw) {
          if (pe) { pe.textContent = 'Please enter your current password.'; pe.hidden = false; }
          return;
        }
        if (!newPw || newPw.length < 8) {
          if (pe) { pe.textContent = 'New password must be at least 8 characters long.'; pe.hidden = false; }
          return;
        }
        if (newPw !== repPw) {
          if (pe) { pe.textContent = 'New password and confirm new password do not match.'; pe.hidden = false; }
          return;
        }

        const btn = $('btnConfirmChangePw');
        if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; }

        try {
          const r = await api('/api/me/password', { method: 'POST', body: JSON.stringify({ current_password: curPw, new_password: newPw }) });
          if (r.access_token) { tok = r.access_token; localStorage.setItem('token', tok); }
          closeChangePasswordModal();
          toast('Password updated successfully in website & database');
          if ($('dlgSettings') && typeof $('dlgSettings').showModal === 'function') {
            openSettingsModal();
          }
        } catch (err) {
          if (pe) { pe.textContent = err.message || 'Failed to update password.'; pe.hidden = false; }
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = 'Confirm & Change Password'; }
        }
      }
      window.submitChangePasswordModal = submitChangePasswordModal;

      if ($('btnConfirmChangePw')) $('btnConfirmChangePw').onclick = e => { e.preventDefault(); submitChangePasswordModal(); };
      if ($('pf')) $('pf').onsubmit = e => { e.preventDefault(); submitChangePasswordModal(); };"""

assert target in text, "Target not found in frontend/index.html"
text = text.replace(target, replacement)

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(text)

with open("frontend/dashboard.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Applied submitChangePasswordModal cleanly to index.html and dashboard.html with 100% parity.")

