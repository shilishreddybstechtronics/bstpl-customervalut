
    function closeModal(id) {
      const d = typeof id === 'string' ? document.getElementById(id) : id;
      if (d && typeof d.close === 'function') d.close();
    }

    function extendAlertExpiry(days) {
      const inp = document.getElementById('devFieldExpiryDate');
      if (!inp) return;
      const base = inp.value ? new Date(inp.value) : new Date();
      const startDate = (isNaN(base.getTime()) || base < new Date()) ? new Date() : base;
      startDate.setDate(startDate.getDate() + days);
      const yyyy = startDate.getFullYear();
      const mm = String(startDate.getMonth() + 1).padStart(2, '0');
      const dd = String(startDate.getDate()).padStart(2, '0');
      inp.value = `${yyyy}-${mm}-${dd}`;
      toast(`Set expiry date to ${inp.value}`);
    }

    (function() {
      try {
        var m = localStorage.getItem('valut_theme_mode') || localStorage.getItem('theme') || 'light';
        var p = localStorage.getItem('valut_palette') || 'royal_navy';
        document.documentElement.setAttribute('data-theme', m);
        document.documentElement.setAttribute('data-mode', m);
        document.documentElement.setAttribute('data-palette', p);
      } catch(e) {}
    })();
  