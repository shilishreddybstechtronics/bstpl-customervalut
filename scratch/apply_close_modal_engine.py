import os, re

# =========================================================================
# 1. APPLY UNIVERSAL CLOSEMODAL & CLOSE/CANCEL ENGINE TO ALL HTML FILES
# =========================================================================
close_modal_js_snippet = '''
    // --- Universal Modal Dialog Close & Cancel Engine ---
    window.closeModal = function(id) {
      try {
        const dlg = typeof id === 'string' ? document.getElementById(id) : id;
        if (dlg) {
          if (typeof dlg.close === 'function') {
            dlg.close();
          } else {
            dlg.removeAttribute('open');
            dlg.style.display = 'none';
          }
        }
      } catch(e) {
        console.warn('Error closing modal:', id, e);
      }
    };

    document.addEventListener('DOMContentLoaded', () => {
      // Wire up all dialog backdrop clicks & close buttons
      document.querySelectorAll('dialog').forEach(dlg => {
        dlg.addEventListener('click', (e) => {
          const rect = dlg.getBoundingClientRect();
          const isInDialog = (rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
            rect.left <= e.clientX && e.clientX <= rect.left + rect.width);
          if (!isInDialog) {
            if (typeof dlg.close === 'function') dlg.close();
          }
        });

        // Wire up all cancel and close buttons inside dialogs
        dlg.querySelectorAll('button[data-close], .btn-close, .modal-close, [aria-label="Close"]').forEach(btn => {
          btn.addEventListener('click', () => {
            if (typeof dlg.close === 'function') dlg.close();
          });
        });
      });
    });
'''

html_files = [
    'frontend/inventory.html',
    'frontend/fetch-data.html',
    'frontend/edit-delete.html',
    'frontend/cart.html',
    'frontend/errors.html',
    'frontend/dashboard.html',
    'frontend/home.html',
    'frontend/sim-upload.html'
]

for fpath in html_files:
    if os.path.isfile(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'window.closeModal = function' not in content:
            # Insert right before </script> at the bottom of the file
            last_script_idx = content.rfind('</script>')
            if last_script_idx != -1:
                content = content[:last_script_idx] + '\n' + close_modal_js_snippet + '\n' + content[last_script_idx:]
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Added universal closeModal engine to {fpath}")
            else:
                print(f"WARNING: No </script> tag in {fpath}")
        else:
            print(f"closeModal already defined in {fpath}")

print("Universal closeModal engine setup complete!")

