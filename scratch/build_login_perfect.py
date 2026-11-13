def build_index_page():
    content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate, max-age=0" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BSTPL CustomerVault — Secure Smart Connected Surface Online</title>
  <link rel="icon" href="logo.svg" type="image/svg+xml" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <script>
    function showAuthLoader(msg) {
      let loader = document.getElementById('cvGlobalLoader');
      if (!loader) {
        loader = document.createElement('div');
        loader.id = 'cvGlobalLoader';
        loader.className = 'cv-global-loader';
        loader.innerHTML = `
          <div class="cv-loader-backdrop"></div>
          <div class="cv-loader-card">
            <div class="cv-loader-logo-3d">B</div>
            <div class="cv-loader-brand-title">BSTPL <span>CustomerVault</span></div>
            <div class="cv-loader-brand-sub">SECURE SMART CONNECTED SURFACE ONLINE</div>
            <div class="cv-loader-msg" id="cvLoaderMsg">${msg}</div>
            <div class="cv-loader-progress"><div class="cv-loader-progress-bar"></div></div>
          </div>
        `;
        document.body.appendChild(loader);
      }
      const msgEl = document.getElementById('cvLoaderMsg');
      if (msgEl) msgEl.textContent = msg;
      loader.style.display = 'flex';
    }

    function hideAuthLoader() {
      const loader = document.getElementById('cvGlobalLoader');
      if (loader) loader.style.display = 'none';
    }

    (function() {
      try {
        var m = localStorage.getItem('valut_theme_mode') || 'dark';
        var p = localStorage.getItem('valut_palette') || 'royal_navy';
        document.documentElement.setAttribute('data-theme', m);
        document.documentElement.setAttribute('data-mode', m);
        document.documentElement.setAttribute('data-palette', p);
      } catch(e) {}
    })();
  </script>
  <style>
    /* Reset & Base */
    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    [data-palette="royal_navy"][data-mode="light"],
    [data-palette="royal_navy"]:not([data-mode="dark"]),
    :root:not([data-palette]) {
      --bg: #f8fafc;
      --bg-gradient: radial-gradient(circle at 15% 15%, #e0eafc 0%, #edf2f9 100%);
      --card: #ffffff;
      --card-subtle: #f1f5f9;
      --card-border: rgba(15, 43, 92, 0.15);
      --text: #0b1a30;
      --text-dim: #475569;
      --primary: #0f2b5c;
      --primary-hover: #0a1c3d;
      --primary-gradient: linear-gradient(135deg, #0f2b5c 0%, #1d4ed8 100%);
      --accent: #d4af37;
      --accent-light: rgba(212, 175, 55, 0.15);
      --ok: #16a34a;
      --danger: #dc2626;
      --danger-bg: rgba(220, 38, 38, 0.08);
      --font: 'Manrope', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --shadow: 0 10px 35px rgba(20, 33, 61, 0.1);
    }
    [data-palette="royal_navy"][data-mode="dark"],
    [data-mode="dark"]:not([data-palette]) {
      --bg: #070d19;
      --bg-gradient: radial-gradient(circle at 20% 20%, #0d1e3d 0%, #060b14 100%);
      --card: #0e1b33;
      --card-subtle: #142546;
      --card-border: rgba(56, 189, 248, 0.2);
      --text: #f8fafc;
      --text-dim: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --primary-gradient: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
      --accent: #d4af37;
      --accent-light: rgba(212, 175, 55, 0.15);
      --ok: #34d399;
      --danger: #f87171;
      --danger-bg: rgba(239, 68, 68, 0.12);
      --font: 'Manrope', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
    }

    body {
      font-family: var(--font);
      background: var(--bg);
      background-image: var(--bg-gradient);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      overflow-x: hidden;
      position: relative;
    }

    body::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background-image: linear-gradient(rgba(56, 189, 248, 0.03) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none;
      z-index: 0;
    }

    .index-top-bar {
      position: relative;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 36px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(10, 20, 40, 0.2);
      backdrop-filter: blur(12px);
    }
    [data-mode="light"] .index-top-bar {
      border-bottom: 1px solid rgba(15, 43, 92, 0.1);
      background: rgba(255, 255, 255, 0.6);
    }

    .cv-brand-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      color: inherit;
    }
    .cv-brand-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #0284c7 0%, #1e3a8a 100%);
      color: #ffffff;
      font-size: 22px;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 16px rgba(2, 132, 199, 0.4);
    }
    .cv-brand-title {
      font-size: 17.5px;
      font-weight: 800;
      letter-spacing: -0.3px;
      color: var(--text);
      line-height: 1.2;
    }
    .cv-brand-sub {
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1.2px;
      color: var(--primary);
      text-transform: uppercase;
    }

    .top-bar-right {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .tagline-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 16px;
      border-radius: 99px;
      font-size: 12px;
      font-weight: 800;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--primary);
    }
    .system-status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 14px;
      border-radius: 99px;
      font-size: 12px;
      font-weight: 700;
      background: rgba(52, 211, 153, 0.12);
      border: 1px solid rgba(52, 211, 153, 0.3);
      color: var(--ok);
    }
    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--ok);
      box-shadow: 0 0 8px var(--ok);
      animation: pulseDot 1.8s infinite;
    }
    @keyframes pulseDot {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(1.2); }
    }

    /* Main Container Split View: Form on LEFT, Hero Branding on RIGHT */
    .index-main {
      position: relative;
      z-index: 10;
      max-width: 1220px;
      width: 100%;
      margin: 0 auto;
      padding: 40px 24px 48px;
      display: grid;
      grid-template-columns: 0.85fr 1.15fr;
      align-items: center;
      gap: 52px;
      flex-grow: 1;
    }

    /* Left Auth Card */
    .auth-card-wrap {
      display: flex;
      justify-content: center;
      width: 100%;
    }
    .auth-card {
      width: 100%;
      max-width: 440px;
      background: var(--card);
      border: 1.5px solid var(--card-border);
      border-radius: 24px;
      padding: 34px 30px;
      box-shadow: var(--shadow);
      position: relative;
    }

    .auth-header {
      margin-bottom: 24px;
      text-align: center;
    }
    .card-brand-crest {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 12px;
    }
    .card-brand-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: linear-gradient(135deg, #0284c7 0%, #1e3a8a 100%);
      color: #ffffff;
      font-size: 16px;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card-brand-text {
      text-align: left;
    }
    .card-brand-title {
      font-size: 14px;
      font-weight: 800;
      color: var(--text);
      line-height: 1.1;
    }
    .card-brand-sub {
      font-size: 9px;
      font-weight: 700;
      letter-spacing: 0.8px;
      color: var(--primary);
    }

    .auth-header h2 {
      font-size: 24px;
      font-weight: 800;
      color: var(--text);
      letter-spacing: -0.4px;
      margin-bottom: 4px;
    }
    .auth-header p {
      font-size: 13px;
      color: var(--text-dim);
    }

    .form-group {
      margin-bottom: 16px;
    }
    .form-group label {
      display: block;
      font-size: 12px;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .input-wrapper {
      position: relative;
      display: flex;
      align-items: center;
    }
    .input-ico {
      position: absolute;
      left: 14px;
      font-size: 16px;
      color: var(--text-dim);
      pointer-events: none;
    }
    .auth-input {
      width: 100%;
      height: 46px;
      padding: 0 14px 0 42px;
      background: rgba(255, 255, 255, 0.04);
      border: 1.5px solid rgba(255, 255, 255, 0.15);
      border-radius: 12px;
      color: var(--text);
      font-size: 14px;
      font-weight: 600;
      font-family: inherit;
      transition: all 0.2s;
    }
    [data-mode="light"] .auth-input {
      background: #f8fafc;
      border-color: #cbd5e1;
    }
    .auth-input:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
    }
    .auth-input::placeholder {
      color: var(--text-dim);
      opacity: 0.7;
    }
    .eye-btn {
      position: absolute;
      right: 12px;
      background: none;
      border: none;
      font-size: 16px;
      cursor: pointer;
      color: var(--text-dim);
      padding: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .auth-success-box {
      display: none;
      align-items: center;
      gap: 10px;
      background: rgba(16, 185, 129, 0.12);
      border: 1.5px solid #10b981;
      color: #10b981;
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 16px;
    }
    .auth-success-box.show {
      display: flex;
    }
    .auth-error-box {
      display: none;
      align-items: center;
      gap: 10px;
      background: var(--danger-bg);
      border: 1.5px solid var(--danger);
      color: var(--danger);
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 16px;
    }
    .auth-error-box.show {
      display: flex;
    }

    .auth-submit-btn {
      width: 100%;
      height: 48px;
      border: none;
      border-radius: 12px;
      background: var(--primary-gradient);
      color: #ffffff;
      font-size: 15px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 6px 20px rgba(2, 132, 199, 0.4);
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }
    .auth-submit-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(2, 132, 199, 0.55);
    }
    .auth-submit-btn:disabled {
      opacity: 0.65;
      cursor: not-allowed;
    }

    .auth-switch-wrap {
      margin-top: 16px;
      text-align: center;
      font-size: 13px;
      color: var(--text-dim);
    }
    .auth-switch-btn {
      background: none;
      border: none;
      color: var(--primary);
      font-weight: 800;
      cursor: pointer;
      margin-left: 4px;
      text-decoration: underline;
    }

    /* Right Hero Branding Column */
    .hero-col {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .hero-tag {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 16px;
      border-radius: 99px;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      background: rgba(56, 189, 248, 0.12);
      border: 1.5px solid rgba(56, 189, 248, 0.35);
      color: var(--primary);
      width: fit-content;
    }
    .hero-headline {
      font-size: 42px;
      font-weight: 800;
      line-height: 1.15;
      letter-spacing: -0.8px;
      color: var(--text);
    }
    .hero-highlight {
      background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
      background-clip: text;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    [data-mode="light"] .hero-highlight {
      background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%);
      background-clip: text;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .hero-sub {
      font-size: 16px;
      color: var(--text-dim);
      line-height: 1.6;
      max-width: 540px;
    }

    .hero-features-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 10px;
    }
    .feature-card {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 14px 16px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }
    [data-mode="light"] .feature-card {
      background: #ffffff;
      border: 1.5px solid #e2e8f0;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
    }
    .feature-card:hover {
      transform: translateY(-2px);
      border-color: var(--primary);
      box-shadow: 0 6px 20px rgba(56, 189, 248, 0.15);
    }
    .feature-ico-box {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: rgba(56, 189, 248, 0.12);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      flex-shrink: 0;
    }
    .feature-card h4 {
      font-size: 13.5px;
      font-weight: 800;
      color: var(--text);
      margin-bottom: 2px;
    }
    .feature-card p {
      font-size: 12px;
      color: var(--text-dim);
      line-height: 1.4;
    }

    /* Branded 3D Loader */
    .cv-global-loader {
      position: fixed;
      inset: 0;
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity 0.25s ease;
    }
    .cv-loader-backdrop {
      position: absolute;
      inset: 0;
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
    }
    .cv-loader-card {
      position: relative;
      z-index: 2;
      background: var(--card, #1e293b);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 20px;
      padding: 30px 40px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.4), 0 0 0 1px rgba(56, 189, 248, 0.2);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      max-width: 360px;
      animation: cvCardPop 0.3s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    @keyframes cvCardPop {
      0% { opacity: 0; transform: scale(0.9) translateY(12px); }
      100% { opacity: 1; transform: scale(1) translateY(0); }
    }
    .cv-loader-logo-3d {
      width: 52px;
      height: 52px;
      background: linear-gradient(135deg, #0284c7 0%, #38bdf8 100%);
      color: #ffffff;
      font-size: 25px;
      font-weight: 900;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8px 24px rgba(2, 132, 199, 0.45);
      margin-bottom: 12px;
      animation: cvLogoPulse 1.8s ease-in-out infinite alternate;
    }
    @keyframes cvLogoPulse {
      0% { transform: scale(0.96) rotate(-2deg); box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3); }
      100% { transform: scale(1.06) rotate(2deg); box-shadow: 0 12px 30px rgba(56, 189, 248, 0.6); }
    }
    .cv-loader-brand-title {
      font-size: 16px;
      font-weight: 800;
      color: var(--text, #f8fafc);
      margin-bottom: 2px;
    }
    .cv-loader-brand-title span { color: #38bdf8; }
    .cv-loader-brand-sub {
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1.2px;
      color: var(--text-dim, #94a3b8);
      text-transform: uppercase;
      margin-bottom: 14px;
    }
    .cv-loader-msg {
      font-size: 13.5px;
      font-weight: 700;
      color: var(--text, #f8fafc);
      margin-bottom: 14px;
    }
    .cv-loader-progress {
      width: 200px;
      height: 5px;
      background: rgba(255,255,255,0.08);
      border-radius: 99px;
      overflow: hidden;
      position: relative;
    }
    .cv-loader-progress-bar {
      position: absolute;
      left: -40%;
      width: 40%;
      height: 100%;
      background: linear-gradient(90deg, transparent, #38bdf8, transparent);
      border-radius: 99px;
      animation: cvProgressIndeterminate 1.2s ease-in-out infinite;
    }
    @keyframes cvProgressIndeterminate {
      0% { left: -40%; width: 40%; }
      50% { width: 60%; }
      100% { left: 100%; width: 40%; }
    }

    /* Responsive */
    @media (max-width: 960px) {
      .index-main {
        grid-template-columns: 1fr;
        gap: 36px;
        padding: 24px 18px;
      }
      .hero-headline {
        font-size: 32px;
      }
      .hero-features-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>

  <!-- Top Navigation Bar -->
  <header class="index-top-bar">
    <a href="index.html" class="cv-brand-wrap" title="BSTPL CustomerVault Portal">
      <div class="cv-brand-icon">B</div>
      <div class="cv-brand-text">
        <div class="cv-brand-title">BSTPL CustomerVault</div>
        <div class="cv-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>
      </div>
    </a>
    <div class="top-bar-right">
      <div class="tagline-pill">Secure Smart Connected Surface Online</div>
      <div class="system-status-pill">
        <span class="status-dot"></span>
        <span>Services Online</span>
      </div>
    </div>
  </header>

  <!-- Split View Main Content: Form on LEFT, Branding on RIGHT -->
  <main class="index-main">
    
    <!-- Left Authentication Form Card -->
    <div class="auth-card-wrap">
      <div class="auth-card">
        
        <div class="auth-header">
          <div class="card-brand-crest">
            <div class="card-brand-icon">B</div>
            <div class="card-brand-text">
              <div class="card-brand-title">BSTPL CustomerVault</div>
              <div class="card-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>
            </div>
          </div>
          <h2 id="authTitle">Sign In</h2>
          <p id="authSub">Access your account to continue</p>
        </div>

        <form id="authForm" novalidate autocomplete="on">
          <!-- Full name input (used in register mode) -->
          <div class="form-group" id="authNameWrap" hidden>
            <label for="authName">Full Name</label>
            <div class="input-wrapper">
              <span class="input-ico">📇</span>
              <input type="text" id="authName" class="auth-input" placeholder="Your full name" autocomplete="name" />
            </div>
          </div>

          <!-- Username / Employee ID -->
          <div class="form-group">
            <label for="authId">Username</label>
            <div class="input-wrapper">
              <span class="input-ico">👤</span>
              <input type="text" id="authId" class="auth-input" placeholder="Username or Employee ID" autocomplete="username" spellcheck="false" autocapitalize="none" required />
            </div>
          </div>

          <!-- Password -->
          <div class="form-group">
            <label for="authPw">Password</label>
            <div class="input-wrapper">
              <span class="input-ico">🔒</span>
              <input type="password" id="authPw" class="auth-input" placeholder="Password" autocomplete="current-password" required />
              <button type="button" class="eye-btn" id="authPwToggle" title="Show password" aria-label="Show password">👁️</button>
            </div>
          </div>

          <!-- Success Notification Banner for Logout -->
          <div class="auth-success-box" id="authSuccessBox" role="status">
            <span>✓</span>
            <span id="authSuccessText">You have been successfully signed out of BSTPL CustomerVault.</span>
          </div>

          <!-- Error Alert Banner -->
          <div class="auth-error-box" id="authErrBox" role="alert">
            <span>⚠️</span>
            <span id="authErr">Invalid credentials</span>
          </div>

          <!-- Submit Button -->
          <button type="submit" class="auth-submit-btn" id="authSubmit">
            <span id="authSubmitLabel">Login</span>
            <span>→</span>
          </button>
        </form>

        <!-- Mode switch between login and register -->
        <div class="auth-switch-wrap" id="authSwitchWrap">
          <span id="authSwitchText">New to BSTPL CustomerVault?</span>
          <button type="button" class="auth-switch-btn" id="authSwitchBtn">Create your ID</button>
        </div>

      </div>
    </div>

    <!-- Right Branding Column: Secure Smart Connected Surface Online -->
    <div class="hero-col">
      <div class="hero-tag">🌐 Secure Smart Connected Surface Online</div>
      <h1 class="hero-headline">
        Secure Smart Connected<br>
        <span class="hero-highlight">Surface Online</span>
      </h1>
      <p class="hero-sub">
        Your Customer Data, Our Priority. Manage, fetch, edit and track your customer data and inventory &mdash; all in one place with high-speed telemetrics and enterprise security.
      </p>

      <!-- 4 Core Capabilities Grid (☁️ 👤 📝 🛢️) -->
      <div class="hero-features-grid">
        <div class="feature-card">
          <div class="feature-ico-box">☁️</div>
          <div>
            <h4>Smart Fetch &amp; SIM Upload</h4>
            <p>Multi-sheet Excel ingestion with auto E-SIM / Plastic SIM classification and validation.</p>
          </div>
        </div>

        <div class="feature-card">
          <div class="feature-ico-box">👤</div>
          <div>
            <h4>Customer Inventory</h4>
            <p>Comprehensive customer portfolios, active device accounts, and instant query debouncing.</p>
          </div>
        </div>

        <div class="feature-card">
          <div class="feature-ico-box">📝</div>
          <div>
            <h4>Edit &amp; Track by IMEI</h4>
            <p>Single &amp; bulk IMEI operations, dynamic column registration, and recycle cart protection.</p>
          </div>
        </div>

        <div class="feature-card">
          <div class="feature-ico-box">🛢️</div>
          <div>
            <h4>Inventory Vault &amp; Alerts</h4>
            <p>Automated 30-day SIM expiration diagnostics, data health audits, and live telemetry feeds.</p>
          </div>
        </div>
      </div>
    </div>

  </main>

  <script>
    const API_BASE = window.location.origin;
    let authMode = 'login';

    const $ = id => document.getElementById(id);

    // Prevent navigating back to authenticated pages after logout
    if (window.history && window.history.replaceState) {
      if (window.location.search && window.location.search.includes('logout=1')) {
        window.history.replaceState(null, '', 'index.html?logout=1');
      }
    }
    window.addEventListener('pageshow', function(e) {
      if (e.persisted || (window.performance && window.performance.navigation && window.performance.navigation.type === 2)) {
        if (window.location.search && window.location.search.includes('logout=1')) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
      }
    });

    // Check existing session
    (async function checkExistingSession() {
      const existingToken = localStorage.getItem('token');
      const hasLogoutParam = !!(window.location && window.location.search && window.location.search.includes('logout=1'));
      if (hasLogoutParam) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        if ($('authSuccessBox')) $('authSuccessBox').classList.add('show');
      }
      if (existingToken && !hasLogoutParam) {
        try {
          const res = await fetch(API_BASE + '/api/me', {
            headers: { 'Authorization': 'Bearer ' + existingToken }
          });
          if (res.ok) {
            window.location.replace('home.html');
          } else if (res.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
          }
        } catch(e) {}
      }
    })();

    // Password visibility toggle
    if ($('authPwToggle')) {
      $('authPwToggle').onclick = () => {
        const inp = $('authPw');
        const isPw = inp.type === 'password';
        inp.type = isPw ? 'text' : 'password';
        $('authPwToggle').textContent = isPw ? '🙈' : '👁️';
        $('authPwToggle').setAttribute('title', isPw ? 'Hide password' : 'Show password');
      };
    }

    // Toggle mode between Sign In and Create your ID
    if ($('authSwitchBtn')) {
      $('authSwitchBtn').onclick = () => {
        authMode = authMode === 'login' ? 'register' : 'login';
        $('authNameWrap').hidden = (authMode === 'login');
        $('authTitle').textContent = authMode === 'login' ? 'Sign In' : 'Create your ID';
        $('authSub').textContent = authMode === 'login' ? 'Access your account to continue' : 'Register a new employee profile in CustomerVault';
        $('authSubmitLabel').textContent = authMode === 'login' ? 'Login' : 'Create Account';
        $('authSwitchText').textContent = authMode === 'login' ? 'New to BSTPL CustomerVault?' : 'Already have an ID?';
        $('authSwitchBtn').textContent = authMode === 'login' ? 'Create your ID' : 'Sign In';
        clearError();
      };
    }

    function showError(msg) {
      const box = $('authErrBox');
      const text = $('authErr');
      if (box && text) {
        text.textContent = msg;
        box.classList.add('show');
      }
    }

    function clearError() {
      const box = $('authErrBox');
      if (box) box.classList.remove('show');
    }

    // Form submission
    if ($('authForm')) {
      $('authForm').onsubmit = async e => {
        e.preventDefault();
        clearError();
        const userId = ($('authId')?.value || '').trim();
        const password = $('authPw')?.value || '';
        const name = ($('authName')?.value || '').trim();

        if (!userId) {
          showError('Please enter your Username or Employee ID.');
          $('authId')?.focus();
          return;
        }
        if (!password) {
          showError('Please enter your password.');
          $('authPw')?.focus();
          return;
        }

        const btn = $('authSubmit');
        const lbl = $('authSubmitLabel');
        btn.disabled = true;
        lbl.textContent = 'Authenticating…';
        showAuthLoader('Signing in to BSTPL CustomerVault…');

        try {
          const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register';
          const payload = authMode === 'login' ? { user_id: userId, password } : { name: name || userId, user_id: userId, password };

          let res;
          try {
            res = await fetch(API_BASE + endpoint, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload)
            });
            if (res.status === 404 && authMode === 'login') {
              res = await fetch(API_BASE + '/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
              });
            }
          } catch(netErr) {
            throw new Error('Cannot reach CustomerVault backend server. Please verify the backend is running.');
          }

          const data = await res.json().catch(() => ({}));
          if (!res.ok) {
            throw new Error(data.detail || data.message || 'Authentication failed. Please verify your credentials.');
          }

          if (!data.access_token) {
            throw new Error('Server returned invalid authentication payload (missing access_token).');
          }

          localStorage.setItem('token', data.access_token);
          if (data.user) {
            localStorage.setItem('user', JSON.stringify(data.user));
          }

          lbl.textContent = 'Success! Opening Home Overview…';
          showAuthLoader('Welcome back! Opening Home Overview…');
          setTimeout(() => {
            window.location.replace('home.html');
          }, 200);
        } catch(err) {
          hideAuthLoader();
          showError(err.message || 'Login failed. Please verify your credentials.');
        } finally {
          btn.disabled = false;
          if (lbl.textContent !== 'Success! Opening Home Overview…') {
            lbl.textContent = authMode === 'login' ? 'Login' : 'Create Account';
          }
        }
      };
    }
  </script>
</body>
</html>"""
    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    with open('frontend/login.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: index.html and login.html updated perfectly!")

if __name__ == '__main__':
    build_index_page()

