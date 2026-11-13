with open('scratch/build_clean_modular_app.py', 'r', encoding='utf-8') as f:
    text = f.read()

helper_fns = """
    function openAddDeviceModal() {
      const dlg = $('devdlg');
      if (!dlg) return;
      $('devTitle').textContent = 'Add Device Record';
      $('devFields').innerHTML = buildDeviceFormFields();
      $('devErr').textContent = '';
      $('devSave').textContent = 'Create Record';
      $('devform').onsubmit = async e => {
        e.preventDefault();
        $('devErr').textContent = '';
        const body = {};
        document.querySelectorAll('#devdlg [data-devf]').forEach(i => {
          const k = i.dataset.devf, v = i.value.trim();
          if (v) body[k] = v;
        });
        const extra = {};
        document.querySelectorAll('#devdlg [data-devx]').forEach(i => {
          const k = i.dataset.devx, v = i.value.trim();
          if (v) extra[k] = v;
        });
        if (Object.keys(extra).length) body.extra = extra;

        try {
          await api('/api/devices', { method: 'POST', body: JSON.stringify(body) });
          dlg.close();
          toast('Device record created successfully');
          if (typeof loadInventoryContainer === 'function') loadInventoryContainer();
          else if (typeof refreshActiveContainer === 'function') refreshActiveContainer();
        } catch (err) { $('devErr').textContent = err.message; }
      };
      if (typeof dlg.showModal === 'function') dlg.showModal();
    }

    function loadCustomModels() {
      const sel = $('optModel');
      if (!sel) return;
      try {
        const saved = JSON.parse(localStorage.getItem('custom_models') || '[]');
        sel.querySelectorAll('.custom-model-opt').forEach(o => o.remove());
        const newOpt = sel.querySelector('option[value="__new__"]');
        saved.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m;
          opt.textContent = m;
          opt.className = 'custom-model-opt';
          if (newOpt) sel.insertBefore(opt, newOpt);
          else sel.appendChild(opt);
        });
      } catch(e) {}
    }

    function showEventPopup(opts) {
      opts = opts || {};
      const title = opts.title || 'Notification';
      const message = opts.message || '';
      const dlg = $('dlgEventPopup');
      if (!dlg || typeof dlg.showModal !== 'function') {
        toast((title ? title + ': ' : '') + message);
        return;
      }
      if ($('eventPopupTitle')) $('eventPopupTitle').textContent = title;
      if ($('eventPopupMessage')) $('eventPopupMessage').textContent = message;
      try {
        dlg.showModal();
        setTimeout(() => { try { dlg.close(); } catch(e){} }, opts.duration || 3500);
      } catch(e) { toast(message); }
    }
"""

anchor = "if (devCancelBtn) devCancelBtn.onclick = () => $('devdlg').close();"
assert anchor in text, "anchor not found in build_clean_modular_app.py"

if 'function openAddDeviceModal' not in text:
    text = text.replace(anchor, anchor + "\n" + helper_fns, 1)

with open('scratch/build_clean_modular_app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added openAddDeviceModal, loadCustomModels, and showEventPopup to build_clean_modular_app.py!")

