with open("frontend/index.html", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update CSS
css_old = """body.app-active #authWrap,
#authWrap[hidden] {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  max-height: 0 !important;
  overflow: hidden !important;
  pointer-events: none !important;
}"""

css_new = """body.app-active #authWrap,
#authWrap[hidden] {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  max-height: 0 !important;
  overflow: hidden !important;
  pointer-events: none !important;
}

body.app-active #dashboardWrap,
body.app-active .cv-app-shell {
  display: flex !important;
  visibility: visible !important;
  position: static !important;
  left: auto !important;
  height: auto !important;
  max-height: none !important;
  overflow: visible !important;
  pointer-events: auto !important;
}"""

assert css_old in text, "css_old not found"
text = text.replace(css_old, css_new, 1)

# 2. Update switchView
switch_old = """      function switchView(signedIn) {
        initTheme();
        if (signedIn) {
          document.body.classList.add('app-active');
          if ($('authWrap')) {
            $('authWrap').hidden = true;
            $('authWrap').style.setProperty('display', 'none', 'important');
          }
          if ($('dashboardWrap')) {
            $('dashboardWrap').hidden = false;
            $('dashboardWrap').style.setProperty('display', 'flex', 'important');
          }
          window.scrollTo(0, 0);
          initApp();
        } else {
          document.body.classList.remove('app-active');
          hideBstplLoader();
          if ($('dashboardWrap')) {
            $('dashboardWrap').hidden = true;
            $('dashboardWrap').style.setProperty('display', 'none', 'important');
            $('dashboardWrap').style.setProperty('visibility', 'hidden', 'important');
          }
          if ($('authWrap')) {
            $('authWrap').hidden = false;
            $('authWrap').style.setProperty('display', 'flex', 'important');
            $('authWrap').style.setProperty('visibility', 'visible', 'important');
          }
          window.scrollTo(0, 0);
          if ($('authPw')) $('authPw').value = '';
          if ($('authId')) $('authId').focus();
        }
      }"""

switch_new = """      function switchView(signedIn) {
        initTheme();
        if (signedIn) {
          document.body.classList.add('app-active');
          if ($('authWrap')) {
            $('authWrap').hidden = true;
            $('authWrap').setAttribute('hidden', '');
            $('authWrap').style.setProperty('display', 'none', 'important');
            $('authWrap').style.setProperty('visibility', 'hidden', 'important');
          }
          if ($('dashboardWrap')) {
            $('dashboardWrap').hidden = false;
            $('dashboardWrap').removeAttribute('hidden');
            $('dashboardWrap').style.setProperty('display', 'flex', 'important');
            $('dashboardWrap').style.setProperty('visibility', 'visible', 'important');
            $('dashboardWrap').style.removeProperty('position');
            $('dashboardWrap').style.removeProperty('left');
            $('dashboardWrap').style.removeProperty('height');
            $('dashboardWrap').style.removeProperty('max-height');
            $('dashboardWrap').style.removeProperty('overflow');
            $('dashboardWrap').style.removeProperty('pointer-events');
          }
          window.scrollTo(0, 0);
          showContainer('box-home');
          initApp();
        } else {
          document.body.classList.remove('app-active');
          hideBstplLoader();
          if ($('dashboardWrap')) {
            $('dashboardWrap').hidden = true;
            $('dashboardWrap').setAttribute('hidden', '');
            $('dashboardWrap').style.setProperty('display', 'none', 'important');
            $('dashboardWrap').style.setProperty('visibility', 'hidden', 'important');
          }
          if ($('authWrap')) {
            $('authWrap').hidden = false;
            $('authWrap').removeAttribute('hidden');
            $('authWrap').style.setProperty('display', 'flex', 'important');
            $('authWrap').style.setProperty('visibility', 'visible', 'important');
          }
          window.scrollTo(0, 0);
          if ($('authPw')) $('authPw').value = '';
          if ($('authId')) $('authId').focus();
        }
      }"""

assert switch_old in text, "switch_old not found"
text = text.replace(switch_old, switch_new, 1)

# 3. Update initApp
init_old = """      async function initApp() {
        try {
          initThemeDock();
          await loadCU().catch(e => console.warn('loadCU notice:', e));
          await updateChrome().catch(e => console.warn('updateChrome notice:', e));
          await showContainer('box-home').catch(e => console.warn('showContainer notice:', e));
          runLiveCycleBackground();
        } catch (err) {"""

init_new = """      async function initApp() {
        try {
          initThemeDock();
          showContainer('box-home');
          const u = getUser(), h = new Date().getHours();
          if ($('hi') && (u.name || u.user_id)) {
            $('hi').textContent = `Good ${h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening'}, ${u.name || u.user_id}`;
          }
          if ($('userAvatarCircle')) {
            const uInitial = ((u.name || u.user_id || 'U')[0] || 'U').toUpperCase();
            $('userAvatarCircle').textContent = uInitial;
          }
          await loadCU().catch(e => console.warn('loadCU notice:', e));
          await updateChrome().catch(e => console.warn('updateChrome notice:', e));
          runLiveCycleBackground();
        } catch (err) {"""

assert init_old in text, "init_old not found"
text = text.replace(init_old, init_new, 1)

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(text)

with open("frontend/dashboard.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Applied login blank screen fix cleanly to index.html and dashboard.html.")

