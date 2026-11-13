
    (function() {
      try {
        var m = localStorage.getItem('valut_theme_mode') || localStorage.getItem('theme') || 'light';
        var p = localStorage.getItem('valut_palette') || 'royal_navy';
        document.documentElement.setAttribute('data-theme', m);
        document.documentElement.setAttribute('data-mode', m);
        document.documentElement.setAttribute('data-palette', p);
      } catch(e) {}
    })();
  