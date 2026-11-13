
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
          