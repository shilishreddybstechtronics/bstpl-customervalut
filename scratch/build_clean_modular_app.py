import os, re, subprocess

print("=== BUILDING CLEAN MODULAR WEBPAGES ===")

# 1. Base CSS Template (Lean, High-Performance, All 4 Themes + Light/Dark)
BASE_CSS = """
    /* Reset & Base */
    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    /* 4 Themed Palettes (Matching Settings & System) */
    /* 1. ROYAL NAVY (Default) */
    [data-palette="royal_navy"][data-mode="light"],
    [data-palette="royal_navy"]:not([data-mode="dark"]),
    :root:not([data-palette]) {
      --bg: #f8fafc;
      --bg-gradient: linear-gradient(180deg, #f8fafc 0%, #edf2f9 100%);
      --card: #ffffff;
      --card-subtle: #f1f5f9;
      --text: #0b1a30;
      --text-dim: #475569;
      --ink: #0b1a30;
      --ink2: #1e293b;
      --line: #cbd5e1;
      --primary: #0f2b5c;
      --primary-hover: #0a1c3d;
      --accent: #d4af37;
      --accentd: #b38f26;
      --accent-light: #fef9ee;
      --muted: #475569;
      --ok: #16a34a;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #091a38 0%, #0d2249 100%);
      --shadow: 0 1px 3px rgba(20, 33, 61, .06), 0 18px 45px rgba(20, 33, 61, .08);
    }
    [data-palette="royal_navy"][data-mode="dark"],
    [data-mode="dark"]:not([data-palette]) {
      --bg: #080f1d;
      --bg-gradient: linear-gradient(180deg, #080f1d 0%, #0e1b33 100%);
      --card: #0e1b33;
      --card-subtle: #142546;
      --text: #f8fafc;
      --text-dim: #94a3b8;
      --ink: #f8fafc;
      --ink2: #cbd5e1;
      --line: #1e355b;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --accent: #d4af37;
      --accentd: #f59e0b;
      --accent-light: rgba(212, 175, 55, 0.15);
      --muted: #94a3b8;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #fbbf24;
      --cv-sidebar-bg: linear-gradient(180deg, #040913 0%, #081224 100%);
      --shadow: 0 4px 25px rgba(0, 0, 0, 0.45);
    }

    /* 2. MIDNIGHT */
    [data-palette="midnight"][data-mode="dark"],
    [data-palette="midnight"]:not([data-mode="light"]) {
      --bg: #070d19;
      --bg-gradient: linear-gradient(180deg, #070d19 0%, #0f1a2e 100%);
      --card: #0f1a2e;
      --card-subtle: #16243d;
      --text: #f1f5f9;
      --text-dim: #94a3b8;
      --ink: #f1f5f9;
      --ink2: #cbd5e1;
      --line: #1e293b;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #eab308;
      --accentd: #ca8a04;
      --accent-light: rgba(234, 179, 8, 0.15);
      --muted: #94a3b8;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #eab308;
      --cv-sidebar-bg: linear-gradient(180deg, #040811 0%, #091322 100%);
      --shadow: 0 4px 25px rgba(0, 0, 0, 0.45);
    }
    [data-palette="midnight"][data-mode="light"] {
      --bg: #f1f5f9;
      --bg-gradient: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
      --card: #ffffff;
      --card-subtle: #f8fafc;
      --text: #0f172a;
      --text-dim: #475569;
      --ink: #0f172a;
      --ink2: #1e293b;
      --line: #cbd5e1;
      --primary: #1e3a8a;
      --primary-hover: #172554;
      --accent: #ca8a04;
      --accentd: #a16207;
      --accent-light: #fefce8;
      --muted: #475569;
      --ok: #059669;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #0a1122 0%, #111d38 100%);
      --shadow: 0 1px 3px rgba(20, 33, 61, .06), 0 18px 45px rgba(20, 33, 61, .08);
    }

    /* 3. EMERALD */
    [data-palette="emerald"][data-mode="light"],
    [data-palette="emerald"]:not([data-mode="dark"]) {
      --bg: #f2fbf6;
      --bg-gradient: linear-gradient(180deg, #f2fbf6 0%, #e6f7ee 100%);
      --card: #ffffff;
      --card-subtle: #e6f7ee;
      --text: #064e3b;
      --text-dim: #047857;
      --ink: #064e3b;
      --ink2: #065f46;
      --line: #a7f3d0;
      --primary: #065f46;
      --primary-hover: #044e39;
      --accent: #d4af37;
      --accentd: #b38f26;
      --accent-light: #fef9ee;
      --muted: #047857;
      --ok: #059669;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #063d2e 0%, #084f3c 100%);
      --shadow: 0 1px 3px rgba(6, 78, 59, .06), 0 18px 45px rgba(6, 78, 59, .08);
    }
    [data-palette="emerald"][data-mode="dark"] {
      --bg: #031a14;
      --bg-gradient: linear-gradient(180deg, #031a14 0%, #062c21 100%);
      --card: #062c21;
      --card-subtle: #093d2e;
      --text: #ecfdf5;
      --text-dim: #a7f3d0;
      --ink: #ecfdf5;
      --ink2: #a7f3d0;
      --line: #0f533f;
      --primary: #10b981;
      --primary-hover: #059669;
      --accent: #fbbf24;
      --accentd: #f59e0b;
      --accent-light: rgba(251, 191, 36, 0.15);
      --muted: #6ee7b7;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #fbbf24;
      --cv-sidebar-bg: linear-gradient(180deg, #02120d 0%, #041f17 100%);
      --shadow: 0 4px 25px rgba(0, 0, 0, 0.45);
    }

    /* 4. CRIMSON VAULT */
    [data-palette="crimson_vault"][data-mode="light"],
    [data-palette="crimson_vault"]:not([data-mode="dark"]) {
      --bg: #fff5f5;
      --bg-gradient: linear-gradient(180deg, #fff5f5 0%, #ffe4e6 100%);
      --card: #ffffff;
      --card-subtle: #ffe4e6;
      --text: #4c0519;
      --text-dim: #881337;
      --ink: #4c0519;
      --ink2: #881337;
      --line: #fecdd3;
      --primary: #881337;
      --primary-hover: #700f2d;
      --accent: #d4af37;
      --accentd: #b38f26;
      --accent-light: #fef9ee;
      --muted: #9f1239;
      --ok: #059669;
      --danger: #dc2626;
      --warn: #d97706;
      --cv-sidebar-bg: linear-gradient(180deg, #4c0519 0%, #680822 100%);
      --shadow: 0 1px 3px rgba(76, 5, 25, .06), 0 18px 45px rgba(76, 5, 25, .08);
    }
    [data-palette="crimson_vault"][data-mode="dark"] {
      --bg: #1a050b;
      --bg-gradient: linear-gradient(180deg, #1a050b 0%, #2c0b15 100%);
      --card: #2c0b15;
      --card-subtle: #3f101f;
      --text: #fff1f2;
      --text-dim: #fecdd3;
      --ink: #fff1f2;
      --ink2: #fecdd3;
      --line: #5c1126;
      --primary: #fb7185;
      --primary-hover: #f43f5e;
      --accent: #fbbf24;
      --accentd: #f59e0b;
      --accent-light: rgba(251, 191, 36, 0.15);
      --muted: #fda4af;
      --ok: #34d399;
      --danger: #f87171;
      --warn: #fbbf24;
      --cv-sidebar-bg: linear-gradient(180deg, #180308 0%, #22050e 100%);
      --shadow: 0 4px 25px rgba(0, 0, 0, 0.45);
    }

    body {
      font-family: "Manrope", system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* App Shell Layout */
    .cv-app-shell {
      display: flex !important;
      min-height: 100vh;
      width: 100%;
    }

    /* Sidebar Navigation */
    .cv-sidebar {
      width: 260px;
      flex-shrink: 0;
      background: var(--cv-sidebar-bg, linear-gradient(180deg, #091a38 0%, #0d2249 100%)) !important;
      color: #ffffff;
      display: flex;
      flex-direction: column;
      padding: 24px 16px 20px;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      scrollbar-width: none;
      -ms-overflow-style: none;
      box-shadow: 2px 0 16px rgba(9, 19, 43, 0.15);
      z-index: 100;
    }
    .cv-sidebar::-webkit-scrollbar {
      display: none;
      width: 0;
      height: 0;
    }
    .cv-sidebar-brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 8px 24px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      margin-bottom: 20px;
    }
    .cv-brand-icon {
      width: 38px;
      height: 38px;
      background: #1d68e1;
      color: #ffffff;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 20px;
      box-shadow: 0 4px 10px rgba(29, 104, 225, 0.35);
      flex-shrink: 0;
    }
    .cv-brand-text {
      display: flex;
      flex-direction: column;
    }
    .cv-brand-title {
      color: #ffffff;
      font-size: 16px;
      font-weight: 800;
      letter-spacing: -0.2px;
      line-height: 1.1;
    }
    .cv-brand-sub {
      color: #93c5fd;
      font-size: 8px;
      font-weight: 700;
      letter-spacing: 1.2px;
      text-transform: uppercase;
      margin-top: 3px;
    }
    .cv-sidebar-menu {
      display: flex;
      flex-direction: column;
      gap: 6px;
      flex: 1;
    }
    .cv-nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border-radius: 10px;
      border: none;
      background: transparent;
      color: #94a3b8;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.18s ease;
      text-align: left;
      width: 100%;
      text-decoration: none;
    }
    .cv-nav-item:hover {
      background: rgba(255, 255, 255, 0.07);
      color: #ffffff;
    }
    .cv-nav-item.on {
      background: linear-gradient(90deg, #1d68e1 0%, #2563eb 100%);
      color: #ffffff;
      font-weight: 700;
      box-shadow: 0 4px 14px rgba(29, 104, 225, 0.38);
    }
    .cv-nav-ico {
      font-size: 16px;
      width: 20px;
      text-align: center;
    }
    .cv-live-badge {
      font-size: 10px;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 99px;
    }

    /* Live Telemetry Widget */
    .cv-sidebar-live-widget {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      padding: 12px 14px;
      margin: 12px 0 16px 0;
    }
    .cv-sb-live-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .cv-live-dot-pulse {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      animation: dotPulse 1.6s infinite;
    }
    @keyframes dotPulse {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
      70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .cv-sb-toggle-btn {
      padding: 2px 8px;
      border-radius: 99px;
      font-size: 10px;
      font-weight: 800;
      border: none;
      background: rgba(16, 185, 129, 0.2);
      color: #10b981;
      cursor: pointer;
      transition: all 0.15s;
    }
    .cv-sb-toggle-btn.off {
      background: rgba(239, 68, 68, 0.2);
      color: #ef4444;
    }
    .cv-sb-live-metrics {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 6px;
    }
    .cv-sb-metric-item {
      display: flex;
      flex-direction: column;
    }
    .cv-sb-metric-val {
      font-size: 14px;
      font-weight: 800;
      color: #ffffff;
    }
    .cv-sb-metric-lbl {
      font-size: 10px;
      color: #94a3b8;
    }
    .cv-sb-live-foot {
      font-size: 10px;
      color: #64748b;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      padding-top: 6px;
      margin-top: 4px;
    }

    /* Sidebar Footer */
    .cv-sidebar-footer {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      margin-top: auto;
    }
    .cv-tech-emblem {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
    }
    .cv-footer-title {
      font-size: 12px;
      font-weight: 700;
      color: #ffffff;
    }
    .cv-footer-sub {
      font-size: 10px;
      color: #94a3b8;
    }

    /* Main Content Panel */
    .cv-main-panel {
      flex: 1;
      min-width: 0;
      overflow-y: auto;
      padding: 24px 32px 48px;
    }

    /* Generic Container Box & Cards */
    .container-box {
      display: block;
      padding: 28px 32px;
      border: 1.5px solid var(--line);
      background: var(--card);
      border-radius: 20px;
      box-shadow: var(--shadow);
      border-top: 4px solid var(--primary);
    }
    .container-tag {
      display: inline-block;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--primary);
      background: rgba(29, 104, 225, 0.12);
      padding: 4px 10px;
      border-radius: 6px;
      margin-bottom: 14px;
    }
    .card {
      padding: 22px 24px;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: var(--card);
      box-shadow: var(--shadow);
    }
    .row {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }
    .grow {
      flex: 1;
      min-width: 240px;
    }
    h2 {
      font-size: 22px;
      font-weight: 800;
      margin: 0 0 6px 0;
      color: var(--text);
    }
    h3 {
      font-size: 18px;
      font-weight: 800;
      margin: 0 0 6px 0;
      color: var(--text);
    }
    h4 {
      font-size: 15px;
      font-weight: 800;
      margin: 16px 0 10px 0;
      color: var(--text);
    }
    .sub {
      font-size: 13.5px;
      color: var(--muted);
    }

    /* Form Controls */
    label {
      display: block;
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    select, input[type="text"], input[type="password"], input[type="search"], textarea {
      height: 38px;
      padding: 0 12px;
      border-radius: 10px;
      border: 1.5px solid var(--line);
      background: var(--card);
      color: var(--text);
      font-family: inherit;
      font-weight: 600;
      font-size: 13px;
      outline: none;
      transition: border-color 0.15s;
    }
    textarea {
      height: auto;
      padding: 10px 12px;
    }
    select:focus, input:focus, textarea:focus {
      border-color: var(--primary);
    }
    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 14px;
      margin-bottom: 16px;
    }

    /* Buttons */
    .b {
      height: 38px;
      padding: 0 14px;
      border: 1.5px solid var(--line);
      border-radius: 10px;
      background: var(--card);
      color: var(--text);
      font-family: inherit;
      font-weight: 700;
      font-size: 13px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      white-space: nowrap;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease;
    }
    .b:hover {
      border-color: var(--primary);
      transform: translateY(-1px);
    }
    .b.p {
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
    }
    .b.p:hover {
      background: var(--primary-hover);
      border-color: var(--primary-hover);
    }
    .b.d {
      background: transparent;
      color: var(--danger);
      border-color: rgba(239, 68, 68, 0.4);
    }
    .b.d:hover {
      background: rgba(239, 68, 68, 0.1);
      border-color: var(--danger);
    }
    .b.on {
      background: #10b981;
      color: #fff;
      border-color: #10b981;
    }

    /* Tables */
    .meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 14px;
      background: var(--card-subtle);
      border: 1px solid var(--line);
      border-radius: 10px;
      font-size: 13px;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 12px;
    }
    .tw {
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--card);
    }
    table {
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
      text-align: left;
    }
    th {
      background: var(--card-subtle);
      text-align: left;
      padding: 12px 14px;
      font-size: 11.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .04em;
      color: var(--muted);
      white-space: nowrap;
      border-bottom: 1.5px solid var(--line);
      position: sticky;
      top: 0;
      z-index: 1;
    }
    td {
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
      color: var(--text);
      white-space: nowrap;
      vertical-align: middle;
    }
    tr:nth-child(even) td {
      background: rgba(0, 0, 0, 0.015);
    }
    tr:hover td {
      background: rgba(29, 104, 225, 0.05);
    }

    /* Status Badges */
    .tag {
      display: inline-flex;
      align-items: center;
      padding: 3px 8px;
      border-radius: 99px;
      font-size: 11px;
      font-weight: 700;
    }
    .tag.ok {
      background: rgba(52, 211, 153, 0.18);
      color: #059669;
    }
    .tag.warn {
      background: rgba(245, 158, 11, 0.18);
      color: #d97706;
    }
    .tag.bad {
      background: rgba(239, 68, 68, 0.18);
      color: #dc2626;
    }
    .tag.mut {
      background: var(--card-subtle);
      color: var(--muted);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 7px;
      border-radius: 99px;
      font-size: 11px;
      font-weight: 800;
    }
    .badge.danger {
      background: #ef4444;
      color: #ffffff;
    }
    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
    }
    .empty {
      padding: 36px 20px;
      text-align: center;
      color: var(--muted);
      font-size: 14px;
      font-weight: 600;
    }
    .empty.err {
      color: var(--danger);
      background: rgba(239, 68, 68, 0.1);
      border-radius: 10px;
    }

    /* Modal Dialogs */
    dialog.modal-dlg {
      border: 1.5px solid var(--line);
      border-radius: 18px;
      background: var(--card);
      color: var(--text);
      padding: 24px;
      max-width: 600px;
      width: 90%;
      box-shadow: 0 16px 48px rgba(0, 0, 0, 0.25);
    }
    dialog::backdrop {
      background: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(4px);
    }

    /* Toast */
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 12px 20px;
      background: #0f172a;
      color: #ffffff;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      z-index: 9999;
      opacity: 0;
      transform: translateY(12px);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
    }
    .toast.show {
      opacity: 1;
      transform: translateY(0);
      pointer-events: auto;
    }

    
    /* =========================================================================
       HOME OVERVIEW STYLES (Header, Expiry Banner, 4-Stats Ribbon, Telemetry)
       ========================================================================= */
    .cv-top-header {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 22px;
      width: 100%;
    }
    .cv-header-single-line {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      flex-wrap: wrap;
    }
    .cv-header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .user-greeting-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-left: auto;
      flex-wrap: wrap;
    }
    .user-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 14px;
      background: var(--card-subtle);
      border: 1px solid var(--line);
      border-radius: 99px;
      font-weight: 700;
      font-size: 13.5px;
      color: var(--text);
    }
    .role-pill {
      padding: 2px 8px;
      border-radius: 99px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }
    .role-pill.admin {
      background: rgba(239, 68, 68, 0.15);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .role-pill.standard {
      background: rgba(16, 185, 129, 0.15);
      color: #10b981;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .cv-avatar-circle {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, #1d68e1 0%, #0c1938 100%);
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 14px;
      box-shadow: 0 2px 8px rgba(29, 104, 225, 0.25);
      cursor: pointer;
      flex-shrink: 0;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .cv-avatar-circle:hover {
      transform: scale(1.08);
      box-shadow: 0 4px 12px rgba(29, 104, 225, 0.4);
    }

    /* Global SIM Expiry Alert Banner */
    .cv-expiry-global-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      background: linear-gradient(90deg, rgba(239, 68, 68, 0.08) 0%, rgba(245, 158, 11, 0.08) 100%);
      border: 1.5px solid rgba(239, 68, 68, 0.25);
      border-left: 5px solid #ef4444;
      border-radius: 14px;
      padding: 14px 20px;
      margin-bottom: 22px;
      box-shadow: 0 4px 16px rgba(239, 68, 68, 0.06);
      flex-wrap: wrap;
    }
    .cv-exp-banner-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .cv-exp-clock {
      font-size: 24px;
      animation: pulseClock 2s infinite ease-in-out;
      display: inline-block;
    }
    @keyframes pulseClock {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.15) rotate(5deg); }
    }
    .cv-exp-label {
      font-weight: 800;
      font-size: 14px;
      color: #dc2626;
      margin-right: 6px;
    }
    .cv-exp-msg {
      font-size: 13.5px;
      font-weight: 600;
      color: var(--text);
    }
    .cv-exp-banner-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .cv-exp-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 15px;
      border-radius: 20px;
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      border: none;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    }
    .cv-exp-btn.expired {
      background: #fee2e2;
      color: #dc2626;
      border: 1px solid #fca5a5;
    }
    .cv-exp-btn.expired:hover {
      background: #dc2626;
      color: #ffffff;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(220, 38, 38, 0.25);
    }
    .cv-exp-btn.expiring {
      background: #fef3c7;
      color: #d97706;
      border: 1px solid #fcd34d;
    }
    .cv-exp-btn.expiring:hover {
      background: #d97706;
      color: #ffffff;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(217, 119, 6, 0.25);
    }

    /* 4-Stat Metric Cards Ribbon */
    .stats#statsRibbon {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .stat-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
    }
    .stat-icon-wrap {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      flex-shrink: 0;
    }
    .stat-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;
    }
    .stat-num {
      font-size: 26px;
      font-weight: 800;
      color: var(--text);
      line-height: 1.1;
      letter-spacing: -0.5px;
    }
    .stat-label {
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* Live Telemetry Controls & Badges */
    .live-ctrl-card {
      padding: 16px 20px;
      border: 1.5px solid var(--ok);
      border-radius: 14px;
      background: var(--card-subtle);
      margin-bottom: 20px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .live-ctrl-left {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .live-ctrl-right {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .live-badge {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      font-weight: 800;
      font-size: 11.5px;
      letter-spacing: 0.6px;
      color: var(--ok);
      background: rgba(22, 163, 74, 0.12);
      border: 1px solid rgba(22, 163, 74, 0.3);
      padding: 5px 12px;
      border-radius: 99px;
    }
    .live-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #16a34a;
      box-shadow: 0 0 8px #16a34a;
      animation: livePulseDot 1.6s infinite;
    }
    @keyframes livePulseDot {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.7); }
      70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(22, 163, 74, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 163, 74, 0); }
    }

    /* Live Telemetry 5-KPI Ribbon */
    #liveKpis {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }
    #liveKpis .card.stat {
      background: var(--card);
      border: 1px solid var(--line);
      border-left: 4px solid var(--primary);
      border-radius: 12px;
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: transform 0.18s;
    }
    #liveKpis .card.stat:hover {
      transform: translateY(-2px);
    }
    #liveKpis .card.stat b {
      font-size: 22px;
      font-weight: 800;
      color: var(--text);
    }
    #liveKpis .card.stat span {
      font-size: 12px;
      font-weight: 600;
      color: var(--muted);
    }

    /* Container Box & Card Elevating */
    .container-tag {
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--primary);
      background: rgba(14, 165, 233, 0.1);
      border: 1px solid rgba(14, 165, 233, 0.25);
      border-radius: 99px;
      padding: 4px 12px;
    }

    /* Responsive adjustments */
    @media (max-width: 1024px) {
      .stats#statsRibbon {
        grid-template-columns: repeat(2, 1fr);
      }
    }
    @media (max-width: 640px) {
      .stats#statsRibbon {
        grid-template-columns: 1fr;
      }
      .cv-header-single-line {
        flex-direction: column;
        align-items: stretch;
      }
      .user-greeting-wrap {
        margin-left: 0;
        justify-content: space-between;
      }
    }

    
    /* Portal Hub Navigation Cards */
    .portal-card {
      text-decoration: none;
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 24px;
      border-radius: 16px;
      background: var(--card);
      border: 1.5px solid var(--line);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
      transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .portal-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 14px 30px rgba(0, 0, 0, 0.1);
      border-color: var(--primary) !important;
    }

    @media print {
      .cv-sidebar, .row, .b, select, input, .toast {
        display: none !important;
      }
      .cv-app-shell, .cv-main-panel {
        display: block !important;
        padding: 0 !important;
        background: #ffffff !important;
        color: #000000 !important;
      }
      .container-box, .card {
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
      }
      .tw {
        border: 1px solid #ccc !important;
        border-radius: 0 !important;
        overflow: visible !important;
      }
      table { font-size: 11px !important; }
      th, td { border: 1px solid #ddd !important; padding: 6px 8px !important; }
    }

    /* =========================================================================
       MODERN SEARCH CONTAINER & CONTROLS (Requirement 2 & 5)
       ========================================================================= */
    .cv-search-container {
      position: relative;
      display: flex;
      align-items: center;
      flex: 1;
      min-width: 240px;
    }
    .cv-search-container .cv-search-icon-left {
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      pointer-events: none;
      font-size: 14px;
      color: var(--muted);
      opacity: 0.75;
      z-index: 2;
    }
    .cv-search-container input.cv-search-input {
      width: 100%;
      height: 40px;
      padding: 0 42px 0 38px;
      border-radius: 10px;
      border: 1.5px solid var(--line);
      background: var(--input-bg, var(--card));
      color: var(--text);
      font-size: 13.5px;
      font-family: inherit;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .cv-search-container input.cv-search-input:focus {
      border-color: var(--primary);
      background: var(--card);
      box-shadow: 0 0 0 3px rgba(29, 104, 225, 0.16);
      outline: none;
    }
    .cv-search-container .cv-search-clear-btn {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      background: transparent;
      border: none;
      color: var(--muted);
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      padding: 4px;
      line-height: 1;
      border-radius: 50%;
      display: none;
      z-index: 2;
    }
    .cv-search-container .cv-search-clear-btn:hover {
      color: var(--danger);
      background: rgba(239, 68, 68, 0.12);
    }
    .cv-search-container .cv-search-spinner {
      position: absolute;
      right: 36px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 13px;
      animation: cv-spin 1s linear infinite;
      display: none;
      z-index: 2;
    }
    @keyframes cv-spin {
      100% { transform: translateY(-50%) rotate(360deg); }
    }

    /* =========================================================================
       DATA HEALTH PAGINATION CONTROLS (Requirement 3)
       ========================================================================= */
    .dh-pagination-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 16px;
      background: var(--card-subtle);
      border: 1px solid var(--line);
      border-radius: 10px;
      margin: 12px 0;
    }
    .dh-pagination-controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .dh-page-btn {
      height: 32px;
      padding: 0 12px;
      border-radius: 7px;
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      border: 1px solid var(--line);
      background: var(--card);
      color: var(--text);
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .dh-page-btn:hover:not(:disabled) {
      border-color: var(--primary);
      color: var(--primary);
      background: rgba(29, 104, 225, 0.08);
    }
    .dh-page-btn:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    .dh-select-all-btn {
      height: 32px;
      padding: 0 12px;
      border-radius: 7px;
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      border: 1px solid var(--line);
      background: var(--card);
      color: var(--text);
      transition: all 0.15s ease;
    }
    .dh-select-all-btn.active {
      background: var(--primary);
      border-color: var(--primary);
      color: #fff;
    }
    .dh-page-info {
      font-size: 12.5px;
      font-weight: 700;
      color: var(--muted);
    }

    /* =========================================================================
       MINIMAL 3D PAGE TRANSITIONS & DEPTH EFFECTS
       ========================================================================= */
    @keyframes cvPage3dEnter {
      0% {
        opacity: 0;
        transform: perspective(1400px) translateZ(-40px) translateY(14px) rotateX(1.5deg);
      }
      100% {
        opacity: 1;
        transform: perspective(1400px) translateZ(0) translateY(0) rotateX(0deg);
      }
    }
    .cv-main-panel, .container-box {
      animation: cvPage3dEnter 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
      transform-style: preserve-3d;
    }
    body.cv-page-3d-exit .cv-main-panel {
      opacity: 0;
      transform: perspective(1400px) translateZ(-50px) translateY(-12px) rotateX(-1.5deg);
      transition: all 0.16s cubic-bezier(0.4, 0, 1, 1);
    }
    .card, .stat-card, .cw, .stat {
      transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.28s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.28s ease;
      transform: perspective(1000px) translateZ(0);
    }
    .card:hover, .stat-card:hover, .cw:hover {
      transform: perspective(1000px) translateZ(8px) translateY(-2px);
      box-shadow: 0 10px 26px rgba(0, 0, 0, 0.07), 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    .cv-avatar-circle {
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
    }
    .cv-avatar-circle:hover {
      transform: scale(1.08) perspective(600px) rotateY(8deg);
      box-shadow: 0 4px 14px rgba(29, 104, 225, 0.35);
    }
    .cv-brand-icon {
      transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .cv-brand-icon:hover {
      transform: perspective(600px) rotateY(15deg) scale(1.05);
    }

    /* =========================================================================
       BRANDED 3D LOADER OVERLAY (Logo & Message on Search/Load)
       ========================================================================= */
    .cv-global-loader {
      position: fixed;
      inset: 0;
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity 0.25s ease, visibility 0.25s ease;
    }
    .cv-loader-backdrop {
      position: absolute;
      inset: 0;
      background: rgba(15, 23, 42, 0.65);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
    }
    .cv-loader-card {
      position: relative;
      z-index: 2;
      background: var(--card, #1e293b);
      border: 1px solid var(--line, rgba(255,255,255,0.12));
      border-radius: 20px;
      padding: 30px 38px;
      box-shadow: 0 25px 60px rgba(0,0,0,0.4), 0 0 0 1px rgba(56, 189, 248, 0.2);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      max-width: 360px;
      animation: cvCardPop 0.3s cubic-bezier(0.16, 1, 0.3, 1) both;
      transform-style: preserve-3d;
      perspective: 1000px;
    }
    @keyframes cvCardPop {
      0% { opacity: 0; transform: scale(0.9) translateY(12px) rotateX(4deg); }
      100% { opacity: 1; transform: scale(1) translateY(0) rotateX(0deg); }
    }
    .cv-loader-logo-wrap {
      position: relative;
      width: 60px;
      height: 60px;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .cv-loader-logo-3d {
      width: 52px;
      height: 52px;
      background: linear-gradient(135deg, var(--primary, #1d68e1) 0%, #38bdf8 100%);
      color: #ffffff;
      font-size: 25px;
      font-weight: 900;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8px 24px rgba(29, 104, 225, 0.45);
      animation: cvLogoPulse 1.8s ease-in-out infinite alternate;
    }
    @keyframes cvLogoPulse {
      0% { transform: scale(0.96) rotate(-2deg); box-shadow: 0 4px 14px rgba(29, 104, 225, 0.3); }
      100% { transform: scale(1.06) rotate(2deg); box-shadow: 0 12px 30px rgba(56, 189, 248, 0.6); }
    }
    .cv-loader-brand-title {
      font-size: 16px;
      font-weight: 800;
      color: var(--text, #f8fafc);
      margin-bottom: 2px;
      letter-spacing: -0.3px;
    }
    .cv-loader-brand-title span {
      color: var(--primary, #38bdf8);
    }
    .cv-loader-brand-sub {
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1.2px;
      color: var(--muted, #94a3b8);
      text-transform: uppercase;
      margin-bottom: 14px;
    }
    .cv-loader-msg {
      font-size: 13.5px;
      font-weight: 700;
      color: var(--text, #f8fafc);
      margin-bottom: 14px;
      min-height: 20px;
    }
    .cv-loader-progress {
      width: 200px;
      height: 5px;
      background: var(--card-subtle, rgba(255,255,255,0.08));
      border-radius: 99px;
      overflow: hidden;
      position: relative;
    }
    .cv-loader-progress-bar {
      position: absolute;
      left: -40%;
      width: 40%;
      height: 100%;
      background: linear-gradient(90deg, transparent, var(--primary, #38bdf8), transparent);
      border-radius: 99px;
      animation: cvProgressIndeterminate 1.2s ease-in-out infinite;
    }
    @keyframes cvProgressIndeterminate {
      0% { left: -40%; width: 40%; }
      50% { width: 60%; }
      100% { left: 100%; width: 40%; }
    }


"""

# 2. Extract shared features & dialogs from scratch/build_clean_modular_webpages.py
with open('scratch/build_clean_modular_webpages.py', 'r', encoding='utf-8') as f:
    builder_source = f.read()

loc = {}
exec(builder_source[:builder_source.find('for cfg in page_configs:')], {}, loc)

containers = loc['containers']
dialogs_dict = loc['dialogs_dict']
dialogs_dict['dlgCheckEntriesModal'] = '\n  <!-- Check Entries & Rectify Inspection Modal (Requirement 2) -->\n  <dialog id="dlgCheckEntriesModal" class="dlg" style="max-width:1100px;width:95vw;max-height:90vh;border-radius:18px;box-shadow:0 24px 60px rgba(0,0,0,0.35);padding:0;overflow:hidden;border:1px solid var(--line)">\n    <div style="padding:18px 24px;background:var(--card-subtle);border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between">\n      <div style="display:flex;align-items:center;gap:12px">\n        <div style="width:38px;height:38px;border-radius:10px;background:rgba(2,132,199,0.15);color:#0284c7;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800">\n          🔍\n        </div>\n        <div>\n          <h3 style="margin:0;font-size:17px;font-weight:800;color:var(--text)">Check Entries &amp; Rectify Inspection</h3>\n          <p style="margin:2px 0 0;font-size:12px;color:var(--muted)">Side-by-side inspection of existing database records vs incoming Excel upload</p>\n        </div>\n      </div>\n      <div style="display:flex;align-items:center;gap:10px">\n        <button class="b p" id="btnDoRectifyAll" type="button" style="padding:8px 16px;font-size:13px;font-weight:800;background:linear-gradient(135deg, #d97706, #b45309);color:#fff;border-radius:8px;cursor:pointer">\n          🔄 Rectify All Eligible Records (<span id="checkEntriesEligibleCount">0</span>)\n        </button>\n        <button class="b ghost" type="button" onclick="closeCheckEntriesModal()" style="font-size:20px;padding:4px 10px;cursor:pointer;border-radius:8px">✕</button>\n      </div>\n    </div>\n    <div style="padding:16px 24px;border-bottom:1px solid var(--line);background:var(--card);display:flex;gap:16px;align-items:center;flex-wrap:wrap">\n      <div style="font-size:13px;font-weight:700;color:var(--text)">\n        Summary: <span id="checkEntriesStatsBadge" style="color:var(--primary);font-weight:800">0 records requiring update</span>\n      </div>\n      <div style="margin-left:auto;display:flex;gap:10px;align-items:center">\n        <input type="text" id="checkEntriesFilter" placeholder="Filter by ICCID, IMEI, Customer…" style="padding:6px 12px;font-size:12.5px;border-radius:8px;border:1px solid var(--line);width:260px" />\n        <button class="b" id="btnExportCheckEntriesCsv" type="button" style="font-size:12px;padding:6px 12px;cursor:pointer">\n          📥 Export Comparison (Excel)\n        </button>\n      </div>\n    </div>\n    <div style="padding:16px 24px;overflow-y:auto;max-height:calc(90vh - 170px)">\n      <div id="checkEntriesTableContainer" style="overflow-x:auto">\n        <div style="padding:24px;text-align:center;color:var(--muted)">Loading entries requiring verification…</div>\n      </div>\n    </div>\n  </dialog>\n'
feature_blocks = loc['feature_blocks']

# Enhance loc['feature_blocks']['SIM'] for reliable Excel upload, update, and insert
sim_js = loc['feature_blocks']['SIM']

# 1. Update matchColumnToField to support IMEI as well as ICCID/CCID
old_match_col = """        if (fieldKey === 'key') {
          // ICCID / CCID / SIM NO
          if (clean.includes('iccid') || clean.includes('ccid')) return true;
          if (clean.startsWith('sim') && (clean.includes('no') || clean.includes('num') || clean.includes('card') || clean === 'sim' || clean === 'simid')) return true;
          if (clean === 'cardno' || clean === 'cardnumber' || clean === 'simcardno') return true;
          return false;
        }"""

new_match_col = """        if (fieldKey === 'key') {
          // ICCID / CCID / SIM NO / IMEI
          if (clean.includes('iccid') || clean.includes('ccid')) return true;
          if (clean.includes('imei')) return true;
          if (clean.startsWith('sim') && (clean.includes('no') || clean.includes('num') || clean.includes('card') || clean === 'sim' || clean === 'simid')) return true;
          if (clean === 'cardno' || clean === 'cardnumber' || clean === 'simcardno') return true;
          return false;
        }"""
sim_js = sim_js.replace(old_match_col, new_match_col)

# 2. Add populateSimTargetCustomerDropdown helper and wire strategy selector
target_cust_helper = """
      function populateSimTargetCustomerDropdown() {
        const sel = $('simTargetCustomer');
        if (!sel) return;
        const curVal = sel.value;
        let opts = '<option value="General_Customer">General_Customer (Default)</option>';
        (CU || []).forEach(c => {
          const name = c.name || c.customer_name;
          if (name && name !== 'General_Customer') {
            opts += `<option value="${esc(name)}">${esc(name)}</option>`;
          }
        });
        sel.innerHTML = opts;
        if (curVal && Array.from(sel.options).some(o => o.value === curVal)) {
          sel.value = curVal;
        }
      }
"""

sim_js = target_cust_helper + "\n" + sim_js

# In initSimDataContainer, call populateSimTargetCustomerDropdown and wire strategy selector
old_init_sim = """function initSimDataContainer() {
        if ($('simRoleAlert')) $('simRoleAlert').hidden = true;
        if ($('simMainContent')) $('simMainContent').hidden = false;"""

new_init_sim = """function initSimDataContainer() {
        if ($('simRoleAlert')) $('simRoleAlert').hidden = true;
        if ($('simMainContent')) $('simMainContent').hidden = false;
        populateSimTargetCustomerDropdown();
        if ($('simActionSelect')) {
          $('simActionSelect').onchange = () => {
            const v = $('simActionSelect').value;
            if ($('simTargetCustomerWrap')) $('simTargetCustomerWrap').style.display = (v === 'update_only') ? 'none' : 'block';
            if (simActiveCheckResult) {
              const matchedCount = simActiveCheckResult.records_matched || 0;
              const notFoundCount = (simActiveCheckResult.not_found_keys_count != null ? simActiveCheckResult.not_found_keys_count : (simActiveCheckResult.not_found_keys || []).length);
              if ($('btnExecuteSelectedActionText')) {
                if (v === 'update_only') $('btnExecuteSelectedActionText').textContent = `Upload & Update Matched (${matchedCount.toLocaleString()} Records)`;
                else if (v === 'insert_only') $('btnExecuteSelectedActionText').textContent = `Insert New SIMs (${notFoundCount.toLocaleString()} Records)`;
                else $('btnExecuteSelectedActionText').textContent = `Upload & Apply SIM Data (${simRawFileRows.length.toLocaleString()} Records)`;
              }
            }
          };
        }"""
sim_js = sim_js.replace(old_init_sim, new_init_sim)

# In handleSimFileSelected, auto schedule comparison after upload
old_wait_check = "// Wait for user to validate rows in Step 2; do not auto-check"
new_wait_check = "populateSimTargetCustomerDropdown(); scheduleSimAutoCheck();"
sim_js = sim_js.replace(old_wait_check, new_wait_check)

# In runSimAutoCheck, update button text and do NOT disable if file has rows
old_btn_update = """          // Button and message updates
          if ($('btnExecuteSelectedActionText')) {
            $('btnExecuteSelectedActionText').textContent = `Upload & Update SIM Data (${res.records_matched.toLocaleString()} Matched Records)`;
          }
          if ($('btnExecuteSelectedAction')) {
            $('btnExecuteSelectedAction').disabled = (res.records_matched === 0);
          }"""

new_btn_update = """          // Button and message updates
          populateSimTargetCustomerDropdown();
          if ($('btnExecuteSelectedActionText')) {
            const act = ($('simActionSelect') ? $('simActionSelect').value : 'both');
            const notFoundCnt = res.not_found_keys_count != null ? res.not_found_keys_count : (res.not_found_keys || []).length;
            if (act === 'update_only') {
              $('btnExecuteSelectedActionText').textContent = `Upload & Update Matched (${res.records_matched.toLocaleString()} Records)`;
            } else if (act === 'insert_only') {
              $('btnExecuteSelectedActionText').textContent = `Insert New SIM Records (${notFoundCnt.toLocaleString()} Records)`;
            } else {
              $('btnExecuteSelectedActionText').textContent = `Upload & Apply SIM Data (${simRawFileRows.length.toLocaleString()} Records)`;
            }
          }
          if ($('btnExecuteSelectedAction')) {
            $('btnExecuteSelectedAction').disabled = (simRawFileRows.length === 0);
          }"""
sim_js = sim_js.replace(old_btn_update, new_btn_update)

# Replace executeSimPush with comprehensive version supporting inserts, updates, and customer targeting
pos_push_start = sim_js.find('async function executeSimPush()')
pos_push_end = sim_js.find('function renderSimPostUploadResults', pos_push_start)
assert pos_push_start != -1 and pos_push_end != -1, "executeSimPush boundaries not found"

new_execute_sim_push = """async function executeSimPush() {
        if (!simActiveCheckResult && (!simRawFileRows || !simRawFileRows.length)) return;

        const keyCol = $('colMapKey') ? $('colMapKey').value : '';
        const msisdn1Col = $('colMapMsisdn1') ? $('colMapMsisdn1').value : '';
        const msisdn2Col = $('colMapMsisdn2') ? $('colMapMsisdn2').value : '';
        const actDateCol = $('colMapActDate') ? $('colMapActDate').value : '';
        const expDateCol = $('colMapExpDate') ? $('colMapExpDate').value : '';
        const providerCol = $('colMapSimProvider') ? $('colMapSimProvider').value : '';
        const chosenProvider = $('simProviderSelect') ? $('simProviderSelect').value : '';
        const overwrite = $('simOverwriteChk') ? $('simOverwriteChk').checked : true;
        const chosenAction = ($('simActionSelect') ? $('simActionSelect').value : 'both');
        const targetCustomer = ($('simTargetCustomer') ? $('simTargetCustomer').value : '') || 'General_Customer';

        const matchedCount = (simActiveCheckResult && simActiveCheckResult.records_matched) || 0;
        const toUpdate = (simActiveCheckResult && simActiveCheckResult.records_to_update) || 0;
        const notFoundCount = (simActiveCheckResult && simActiveCheckResult.not_found_keys_count != null ? simActiveCheckResult.not_found_keys_count : (simActiveCheckResult && simActiveCheckResult.not_found_keys ? simActiveCheckResult.not_found_keys.length : (simRawFileRows.length - matchedCount)));

        const totalRows = simRawFileRows.length;
        if (totalRows === 0) {
          toast('⚠️ No data rows found in file to apply.');
          return;
        }

        let confirmMsg = `Apply SIM data to database?\n\n• Total file rows: ${totalRows.toLocaleString()}`;
        if (chosenAction === 'update_only') {
          confirmMsg += `\n• Strategy: Update Matched Records Only (${matchedCount.toLocaleString()} matched; ${notFoundCount.toLocaleString()} new skipped).`;
        } else if (chosenAction === 'insert_only') {
          confirmMsg += `\n• Strategy: Insert New SIMs Only (${notFoundCount.toLocaleString()} new records inserted into "${targetCustomer}").`;
        } else {
          confirmMsg += `\n• Strategy: Update Matched (${matchedCount.toLocaleString()}) & Insert New (${notFoundCount.toLocaleString()} into "${targetCustomer}").`;
        }
        confirmMsg += '\n\nProceed with upload?';

        if (!confirm(confirmMsg)) {
          return;
        }

        const fullPayload = [];
        simRawFileRows.forEach(rawObj => {
          let rawKey = rawObj[keyCol] != null ? String(rawObj[keyCol]).trim() : '';
          if (rawKey.endsWith('.0') && /^\\d+\\.0$/.test(rawKey)) rawKey = rawKey.slice(0, -2);
          if (/[eE]\+?/.test(rawKey)) {
            try {
              const num = Number(rawKey);
              if (!isNaN(num) && Number.isFinite(num)) rawKey = BigInt(Math.round(num)).toString();
            } catch { }
          }
          rawKey = rawKey.replace(/[\s\-_]+/g, '').toUpperCase();
          if (!rawKey || rawKey.length < 5) return;

          const rowProv = providerCol ? (rawObj[providerCol] || '').trim() : '';
          const is15Digit = /^\d{15}$/.test(rawKey);

          fullPayload.push({
            iccid: rawKey,
            imei: is15Digit ? rawKey : null,
            msisdn1: msisdn1Col ? (rawObj[msisdn1Col] || '').trim() || null : null,
            msisdn2: msisdn2Col ? (rawObj[msisdn2Col] || '').trim() || null : null,
            act_date: actDateCol ? convertDateToStandardFormat(rawObj[actDateCol]) : null,
            expiry_date: expDateCol ? convertDateToStandardFormat(rawObj[expDateCol]) : null,
            sim_provider: rowProv || chosenProvider || null
          });
        });

        const progressWrap = $('simPushProgressWrap');
        const progressBar = $('simPushBar');
        const progressPct = $('simPushPct');
        const progressStatus = $('simPushStatus');
        const liveCount = $('simPushLiveCount');
        const logsEl = $('simPushLogs');

        if (progressWrap) progressWrap.hidden = false;
        if ($('btnExecuteSelectedAction')) $('btnExecuteSelectedAction').disabled = true;
        if (logsEl) logsEl.innerHTML = '';

        const chunkSize = 1000;
        let runningUpdated = 0;
        let runningInserted = 0;
        let runningAlreadySame = 0;
        let runningUnmatched = 0;
        const allAppliedComparison = [];
        const allNotFoundRecords = [];

        try {
          for (let i = 0; i < fullPayload.length; i += chunkSize) {
            const partNum = Math.floor(i / chunkSize) + 1;
            const totalParts = Math.ceil(fullPayload.length / chunkSize);
            const chunk = fullPayload.slice(i, i + chunkSize);
            const pct = Math.min(99, Math.round(((i + chunk.length) / (fullPayload.length || 1)) * 100));

            if (progressBar) progressBar.style.width = pct + '%';
            if (progressPct) progressPct.textContent = pct + '%';
            if (progressStatus) progressStatus.textContent = `Uploading & applying batch ${partNum} of ${totalParts} (${pct}% complete)…`;

            const shouldInsert = (chosenAction === 'both' || chosenAction === 'insert_only');
            const res = await api('/api/simdata/apply', {
              method: 'POST',
              body: JSON.stringify({
                rows: chunk,
                overwrite: overwrite,
                match_by: currentSimMatchMode,
                sim_provider: chosenProvider || null,
                insert_new: shouldInsert,
                action: chosenAction,
                target_customer: targetCustomer
              })
            });

            runningUpdated += (res.updated || 0);
            runningInserted += (res.inserted || 0);
            runningAlreadySame += (res.already_same || res.ignored_identical || 0);
            runningUnmatched += (res.unmatched_count || 0);

            if (res.applied_comparison) allAppliedComparison.push(...res.applied_comparison);
            if (res.not_found_records) allNotFoundRecords.push(...res.not_found_records);

            if (liveCount) liveCount.textContent = `${runningUpdated.toLocaleString()} updated, ${runningInserted.toLocaleString()} inserted, ${runningAlreadySame.toLocaleString()} identical kept…`;
            if (logsEl) {
              const logLine = document.createElement('div');
              logLine.textContent = `[Part ${partNum}/${totalParts}] Updated: ${res.updated || 0}, Inserted: ${res.inserted || 0}, Kept Identical: ${res.already_same || 0}.`;
              logsEl.appendChild(logLine);
              logsEl.scrollTop = logsEl.scrollHeight;
            }
          }

          if (progressBar) progressBar.style.width = '100%';
          if (progressPct) progressPct.textContent = '100%';
          if (progressStatus) progressStatus.textContent = `✅ Process Complete (100%): ${runningUpdated.toLocaleString()} updated, ${runningInserted.toLocaleString()} inserted, ${runningAlreadySame.toLocaleString()} already identical kept.`;

          toast(`✅ Upload complete: ${runningUpdated.toLocaleString()} updated, ${runningInserted.toLocaleString()} inserted`);

          // Render Post-Upload Comparison & Results View
          const postResult = {
            total_file_rows: fullPayload.length,
            updated: runningUpdated,
            inserted: runningInserted,
            already_same: runningAlreadySame,
            not_found_count: notFoundCount,
            applied_comparison: allAppliedComparison,
            not_found_records: allNotFoundRecords.length ? allNotFoundRecords : (simActiveCheckResult ? simActiveCheckResult.not_found_records || [] : []),
            before_comparison: (simActiveCheckResult ? simActiveCheckResult.detailed_comparison || [] : [])
          };
          simLastPostUploadResult = postResult;
          renderSimPostUploadResults(postResult);

          showEventPopup({
            type: 'uploading',
            title: 'SIM Data Successfully Applied',
            message: `SIM Data Upload Complete: ${runningUpdated.toLocaleString()} updated, ${runningInserted.toLocaleString()} new SIM records inserted into "${targetCustomer}", ${runningAlreadySame.toLocaleString()} identical preserved.`,
            meta: {
              'Records Updated in DB': runningUpdated,
              'New SIM Records Inserted': runningInserted,
              'Already Identical (Kept)': runningAlreadySame,
              'Total Rows Processed': fullPayload.length
            },
            progress: '100% Complete'
          });

          notifyDataUpdated({ page: 'sim-upload', updated: runningUpdated, inserted: runningInserted });
          await loadCU(); await updateChrome();
          syncGlobalMetricsAndChrome();
          if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
          if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
          if (typeof loadStats === 'function') loadStats();
        } catch (err) {
          fail(err);
          if (progressStatus) progressStatus.textContent = `⚠️ Push failed partway: ${err.message}.`;
        } finally {
          if ($('btnExecuteSelectedAction')) $('btnExecuteSelectedAction').disabled = false;
        }
      }

      """

sim_js = sim_js[:pos_push_start] + new_execute_sim_push + sim_js[pos_push_end:]

loc['feature_blocks']['SIM'] = sim_js

# 1. Customization for containers['box-home'] (Live Master Device Stream & Data Health)
box_home_html = containers['box-home']

# Redesign Live Master Device Stream with modern search and toolbar
old_stream_pattern = r'<div class="card" style="padding:20px;border:1px solid var\(--line\);margin-bottom:20px;background:var\(--card-subtle\)">[\s\S]*?<div id="liveMasterTable">'
new_stream_html = '''<div class="card" id="cardLiveMasterStream" style="padding:22px 24px;border:1px solid var(--line);border-radius:16px;margin-bottom:24px;background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03)">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px;border-bottom:1px solid var(--line);padding-bottom:14px">
              <div>
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-size:20px">📱</span>
                  <h3 style="margin:0;font-size:18px;font-weight:800;color:var(--text)">Live Master Device Stream</h3>
                  <span class="live-badge" style="font-size:11px;padding:2px 8px"><span class="live-dot"></span> LIVE</span>
                </div>
                <span style="font-size:13px;color:var(--muted);margin-top:2px;display:block">Real-time incoming telemetry and inventory status across all active customer accounts.</span>
              </div>
              <button class="b" id="liveExportExcel" style="font-weight:700;padding:8px 16px;border-radius:9px;background:var(--card-subtle);border:1px solid var(--line)">📥 Export to Excel</button>
            </div>

            <!-- Instant Live Search & Filters Toolbar -->
            <div style="display:flex;align-items:flex-end;flex-wrap:wrap;gap:12px;margin-bottom:16px">
              <div style="min-width:180px">
                <label for="liveCustFilter" style="font-size:12px;font-weight:700;color:var(--muted);display:block;margin-bottom:4px">Customer Account</label>
                <select id="liveCustFilter" style="height:40px;border-radius:10px;padding:0 12px;font-size:13px;width:100%;border:1.5px solid var(--line);background:var(--input-bg,var(--card));color:var(--text)">
                  <option value="">All Customers</option>
                </select>
              </div>
              <div style="min-width:160px">
                <label for="liveFieldFilter" style="font-size:12px;font-weight:700;color:var(--muted);display:block;margin-bottom:4px">Target Column</label>
                <select id="liveFieldFilter" style="height:40px;border-radius:10px;padding:0 12px;font-size:13px;width:100%;border:1.5px solid var(--line);background:var(--input-bg,var(--card));color:var(--text)">
                  <option value="all">All Columns</option>
                  <option value="imei">IMEI</option>
                  <option value="iccid">ICCID / CCID</option>
                  <option value="device_sr_no">Device SR No</option>
                  <option value="msisdn1">MSISDN1</option>
                  <option value="customer_name">Customer Name</option>
                  <option value="model">Model</option>
                  <option value="sim_provider">SIM Provider</option>
                </select>
              </div>
              <div style="flex:1;min-width:240px">
                <label for="liveSearchInput" style="font-size:12px;font-weight:700;color:var(--muted);display:block;margin-bottom:4px">Instant Live Search</label>
                <div class="cv-search-container">
                  <span class="cv-search-icon-left">🔎</span>
                  <input id="liveSearchInput" class="cv-search-input" placeholder="Search across records in real-time…" autocomplete="off" />
                  <span class="cv-search-spinner" id="liveSearchSpinner">🌀</span>
                  <button type="button" class="cv-search-clear-btn" id="liveSearchClearBtn" title="Clear search">✕</button>
                </div>
              </div>
              <div>
                <button class="b" id="liveSearchClear" style="height:40px;padding:0 14px;border-radius:10px;font-weight:700">Clear</button>
              </div>
            </div>

            <div id="liveMasterTable">'''

box_home_html = re.sub(old_stream_pattern, new_stream_html, box_home_html)
containers['box-home'] = box_home_html

# 2. Customization for containers['box-sim']: Remove Restore All card and upgrade Action Selection
box_sim_html = containers['box-sim']
box_sim_html = re.sub(r'<!-- Dedicated Restore All Soft-Deleted SIMs Card[\s\S]*?</div>\s*</div>\s*</div>', '', box_sim_html)

# Update KPI card: replace '⚠️ ICCID Not Found (Will NOT Upload)' with '✨ New Records (Eligible to Insert)'
old_kpi_not_found = r'''            <div class="card stat" style="border-left:4px solid #ef4444;background:rgba(239,68,68,0.06);padding:14px">
              <b id="kpiSimNotFound" style="font-size:24px;color:#dc2626">0</b>
              <span style="font-size:12px;color:#dc2626;font-weight:800">⚠️ ICCID Not Found (Will NOT Upload)</span>
              <!-- backward compatibility hidden span -->
              <span id="kpiSimCanInsert" style="display:none">0</span>
            </div>'''
new_kpi_not_found = r'''            <div class="card stat" style="border-left:4px solid #0284c7;background:rgba(2,132,199,0.06);padding:14px">
              <b id="kpiSimNotFound" style="font-size:24px;color:#0284c7">0</b>
              <span style="font-size:12px;color:#0284c7;font-weight:800">✨ New Records (Eligible to Insert)</span>
              <!-- backward compatibility hidden span -->
              <span id="kpiSimCanInsert" style="display:none">0</span>
            </div>'''
box_sim_html = box_sim_html.replace(old_kpi_not_found, new_kpi_not_found)

# Upgrade simActionSelectCard
old_sim_action_card = r'''          <!-- Upload Execution Box (Strictly updates matching records; never uploads unknown ICCIDs) -->
          <div id="simActionSelectCard" style="background:var(--card-subtle);border:1px solid var(--line);border-radius:12px;padding:16px;margin:16px 0">
            <!-- Smart Sync explanation banner -->
            <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);border-radius:10px;padding:12px 16px;margin-bottom:14px;font-size:12.5px;color:var(--ink);display:flex;align-items:center;gap:12px">
              <span style="font-size:22px">🛡️</span>
              <div>
                <b style="font-size:13.5px">Customer Verification Rule:</b>
                <div style="margin-top:2px;color:var(--muted);font-size:12px;line-height:1.4">
                  Only rows where the ICCID is found in an existing customer will be updated. Differing values will be replaced, and identical values will remain untouched. <b>Any ICCID not found in customer accounts will NOT be uploaded.</b>
                </div>
              </div>
            </div>

            <!-- Execution Action Bar -->
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
              <div>
                <span id="simPushMsg" style="font-size:13px;font-weight:700;color:var(--ink)"></span>
              </div>
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <button class="b p" id="btnExecuteSelectedAction" type="button"
                  style="font-size:13.5px;padding:0 24px;height:42px;font-weight:800;display:inline-flex;align-items:center;gap:8px;background:var(--ok);border-color:var(--ok)">
                  <span id="btnExecuteIcon">🚀</span> <span id="btnExecuteSelectedActionText">Upload & Update SIM Data (Matched Records)</span>
                </button>
                <button class="b" id="btnSimDlPreUploadExcel" type="button" style="height:42px;display:inline-flex;align-items:center;gap:6px">
                  <span>📥</span> <span>Download Before-Change Excel (Preview)</span>
                </button>
                <button class="b" id="btnSimDlNotFound" type="button" style="height:42px;display:inline-flex;align-items:center;gap:6px">
                  <span>📥</span> <span>Download NOT FOUND ICCIDs (Excel)</span>
                </button>
              </div>
            </div>'''

new_sim_action_card = r'''          <!-- Upload Execution Box (Supports updating matched records AND inserting new SIM records) -->
          <div id="simActionSelectCard" style="background:var(--card-subtle);border:1.5px solid var(--line);border-radius:14px;padding:18px 20px;margin:16px 0;box-shadow:0 2px 10px rgba(0,0,0,0.02)">
            <!-- Smart Sync explanation banner -->
            <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);border-radius:10px;padding:12px 16px;margin-bottom:14px;font-size:12.5px;color:var(--ink);display:flex;align-items:center;gap:12px">
              <span style="font-size:22px">🛡️</span>
              <div>
                <b style="font-size:13.5px">Customer Verification &amp; Sync Engine:</b>
                <div style="margin-top:2px;color:var(--muted);font-size:12px;line-height:1.4">
                  Existing devices will have differing values replaced and identical values preserved. Genuinely new SIM entries in the Excel file will be inserted into the chosen customer account with zero duplicate risk.
                </div>
              </div>
            </div>

            <!-- Upload Action & Target Customer Selection -->
            <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--line)">
              <div style="flex:1;min-width:240px">
                <label for="simActionSelect" style="font-size:12.5px;font-weight:800;color:var(--text);display:block;margin-bottom:5px">
                  ⚡ Upload &amp; Apply Strategy
                </label>
                <select id="simActionSelect" style="width:100%;height:40px;padding:0 12px;border-radius:9px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13px;font-weight:700">
                  <option value="both" selected>🚀 Apply All (Update Matched &amp; Insert New Records)</option>
                  <option value="update_only">🔄 Update Matched Records Only</option>
                  <option value="insert_only">✨ Insert New Records Only</option>
                </select>
              </div>
              <div style="flex:1;min-width:240px" id="simTargetCustomerWrap">
                <label for="simTargetCustomer" style="font-size:12.5px;font-weight:800;color:var(--text);display:block;margin-bottom:5px">
                  🏢 Target Customer for New SIMs
                </label>
                <select id="simTargetCustomer" style="width:100%;height:40px;padding:0 12px;border-radius:9px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13px;font-weight:600">
                  <option value="General_Customer">General_Customer (Default)</option>
                </select>
              </div>
            </div>

            <!-- Execution Action Bar -->
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
              <div>
                <span id="simPushMsg" style="font-size:13px;font-weight:700;color:var(--ink)"></span>
              </div>
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <button class="b p" id="btnExecuteSelectedAction" type="button"
                  style="font-size:13.5px;padding:0 24px;height:42px;font-weight:800;display:inline-flex;align-items:center;gap:8px;background:var(--ok);border-color:var(--ok);cursor:pointer;box-shadow:0 2px 8px rgba(22,163,74,0.3)">
                  <span id="btnExecuteIcon">🚀</span> <span id="btnExecuteSelectedActionText">Upload &amp; Apply SIM Data</span>
                </button>
                <button class="b" id="btnSimDlPreUploadExcel" type="button" style="height:42px;display:inline-flex;align-items:center;gap:6px">
                  <span>📥</span> <span>Download Before-Change Excel (Preview)</span>
                </button>
                <button class="b" id="btnSimDlNotFound" type="button" style="height:42px;display:inline-flex;align-items:center;gap:6px">
                  <span>📥</span> <span>Download Unmatched ICCIDs (Excel)</span>
                </button>
              </div>
            </div>'''

box_sim_html = box_sim_html.replace(old_sim_action_card, new_sim_action_card)
containers['box-sim'] = box_sim_html

# 2.5 Customize containers['box-inv'] (Subnav, Search, Metrics Ribbon, Check Entries & Rectify)
box_inv_html = containers['box-inv']

# Design Subnav: 📋 Device Records | 📁 Customer Files (154) | 📤 Bulk Upload
old_subnav_re = r'<div class="inv-subnav" role="tablist"[^>]*>[\s\S]*?</div>'
new_subnav_html = """<div class="inv-subnav" role="tablist" style="display:flex;gap:10px;margin:18px 0;border-bottom:1px solid var(--line);padding-bottom:12px;flex-wrap:wrap">
        <button class="inv-sub-btn active" id="btnSubDevices" data-sub="devices" type="button" style="display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:10px;font-size:13.5px;font-weight:700;cursor:pointer;border:1.5px solid var(--line);background:var(--card);color:var(--text);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)">
          <span>📋</span> <span>Device Records</span>
        </button>
        <button class="inv-sub-btn" id="btnSubCust" data-sub="cust" type="button" style="display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:10px;font-size:13.5px;font-weight:700;cursor:pointer;border:1.5px solid var(--line);background:var(--card);color:var(--text);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)">
          <span>📁</span> <span>Customer Files</span> (<span id="invCustCountBadge">0</span>)
        </button>
        <button class="inv-sub-btn" id="btnSubUpload" data-sub="upload" type="button" style="display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:10px;font-size:13.5px;font-weight:700;cursor:pointer;border:1.5px solid var(--line);background:var(--card);color:var(--text);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)">
          <span>📤</span> <span>Bulk Upload</span>
        </button>
      </div>"""
box_inv_html = re.sub(old_subnav_re, new_subnav_html, box_inv_html, count=1)

# Design Search Customer Cards Bar & Action Toolbar in subViewCust
old_cust_search_re = r'<div class="row" style="margin-top:14px">\s*<div class="grow">\s*<label for="cs">Search Customer Cards</label>\s*<input id="cs" placeholder="Filter by customer name…" />\s*</div>\s*</div>'
new_cust_search_html = """<div style="margin-top:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
            <div style="flex:1;max-width:480px;min-width:240px">
              <label for="cs" style="font-size:13px;font-weight:800;color:var(--text);display:block;margin-bottom:6px">
                Search Customer Cards
              </label>
              <div class="cv-search-container">
                <span class="cv-search-icon-left">🔎</span>
                <input id="cs" class="cv-search-input" placeholder="Filter by customer name…" autocomplete="off" />
                <button type="button" class="cv-search-clear-btn" id="csClearBtn" title="Clear filter" style="display:none">✕</button>
              </div>
            </div>
            <div style="font-size:12.5px;color:var(--muted);font-weight:700;margin-top:auto" id="csFilterCount">
              Showing all customer portfolios
            </div>
          </div>"""
box_inv_html = re.sub(old_cust_search_re, new_cust_search_html, box_inv_html, count=1)
box_inv_html = box_inv_html.replace('<div id="cgrid"></div>', '<div id="cgrid" style="margin-top:16px"></div>')

# Upgrade Bulk Upload Status Metrics Ribbon (Requirement 1 & 2)
old_stats_ribbon_re = r'<div class="stats"[^>]*>\s*<div class="card stat"[^>]*><b id="vTotalScanned">[\s\S]*?</div>\s*</div>'
new_stats_ribbon_html = """<div class="stats" style="margin-top:10px;grid-template-columns:repeat(auto-fit, minmax(135px, 1fr));gap:10px">
              <div class="card stat" style="border-left-color:var(--primary);padding:12px 14px"><b id="vTotalScanned">0</b><span>📄 Total Scanned</span></div>
              <div class="card stat" style="border-left-color:#10b981;padding:12px 14px"><b id="vValid">0</b><span>✅ Valid Entries</span></div>
              <div class="card stat" style="border-left-color:var(--ok);padding:12px 14px"><b id="vNew" style="color:var(--ok)">0</b><span>✨ New (Insert)</span></div>
              <div class="card stat" style="border-left-color:var(--warn);padding:12px 14px"><b id="vUpdatedCount" style="color:var(--warn)">0</b><span>🔄 Requires Update</span></div>
              <div class="card stat" style="border-left-color:#94a3b8;padding:12px 14px"><b id="vExistingCountCard">0</b><span>📋 Existing in DB</span></div>
              <div class="card stat" style="border-left-color:#f97316;padding:12px 14px"><b id="vDup" style="color:#f97316">0</b><span>⚠️ Duplicates</span></div>
              <div class="card stat" style="border-left-color:var(--danger);padding:12px 14px"><b id="vInvalidCount" style="color:var(--danger)">0</b><span>❌ Invalids</span></div>
            </div>"""
box_inv_html = re.sub(old_stats_ribbon_re, new_stats_ribbon_html, box_inv_html, count=1)

# Upgrade Filter Buttons in subViewUpload
old_filter_btns_re = r'<div style="display:flex;gap:6px;flex-wrap:wrap" id="valFilterBtns">[\s\S]*?</div>'
new_filter_btns_html = """<div style="display:flex;gap:6px;flex-wrap:wrap" id="valFilterBtns">
                  <button class="b on" data-valfilter="new" type="button" id="btnFilterNew" style="font-weight:700;color:var(--ok)">✨ New (<span id="vNewCount">0</span>)</button>
                  <button class="b" data-valfilter="update" type="button" id="btnFilterUpdate" style="font-weight:700;color:var(--warn)">🔄 Requires Update (<span id="vUpdatedBtnCount">0</span>)</button>
                  <button class="b" data-valfilter="existing" type="button" id="btnFilterExisting">📋 Existing (<span id="vExistingCount">0</span>)</button>
                  <button class="b" data-valfilter="duplicate" type="button" id="btnFilterDup">⚠️ Duplicates (<span id="vDupCount">0</span>)</button>
                  <button class="b" data-valfilter="invalid" type="button" id="btnFilterInvalid" style="font-weight:700;color:var(--danger)">❌ Invalids (<span id="vInvalidBtnCount">0</span>)</button>
                </div>"""
box_inv_html = re.sub(old_filter_btns_re, new_filter_btns_html, box_inv_html, count=1)

# Add Check Entries & Rectify Update Action Buttons
old_action_bar_re = r'<div class="row" style="margin:14px 0;gap:10px;flex-wrap:wrap;align-items:center">[\s\S]*?</div>'
new_action_bar_html = """<div style="display:flex;gap:10px;align-items:center;margin-top:16px;flex-wrap:wrap">
              <button class="b p" id="btnCheckEntriesModal" type="button"
                style="padding:11px 20px;font-size:14px;font-weight:800;border-radius:9px;background:linear-gradient(135deg, #0284c7, #2563eb);color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 12px rgba(37,99,235,0.25);cursor:pointer">
                <span>🔍</span> <span>Check Entries (Inspect Differences)</span>
              </button>
              <button class="b p" id="btnRectifyUpdate" type="button"
                style="padding:11px 20px;font-size:14px;font-weight:800;border-radius:9px;background:linear-gradient(135deg, #d97706, #b45309);color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 12px rgba(217,119,6,0.25);cursor:pointer">
                <span>🔄</span> <span>Rectify Update (<span id="btnRectifyCountBadge">0</span> Records)</span>
              </button>
              <button class="b p" id="btnConfirmUpload" type="button"
                style="padding:11px 20px;font-size:14px;font-weight:800;border-radius:9px;background:linear-gradient(135deg, var(--ok), #059669);color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 3px 12px rgba(16,185,129,0.25);cursor:pointer">
                <span>🚀</span> <span>Upload & Insert New (<span id="btnInsertNewCountBadge">0</span>)</span>
              </button>
              <button class="b" id="btnDownloadPreUploadReport" type="button" style="font-size:13px;padding:10px 16px;cursor:pointer">
                📥 Download Validation Report (Excel)
              </button>
            </div>"""
box_inv_html = re.sub(old_action_bar_re, new_action_bar_html, box_inv_html, count=1)

containers['box-inv'] = box_inv_html

# --- Redesigned Boxes (Requirement: Search Term, Search Value(s), IMEI & Optional Values) ---
# 1. Redesign Search Term in box_inv_html
box_inv_html = re.sub('<div class="grow">\\s*<label for="invQuery">Search Term</label>\\s*<input id="invQuery"[^>]*>\\s*</div>\\s*<button class="b" id="invClear"[^>]*>Clear</button>', '          <div class="grow" style="min-width:300px">\n            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">\n              <label for="invQuery" style="font-size:12.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px">\n                <span style="font-size:14px">🔎</span> <span>Search Term</span>\n              </label>\n              <span style="font-size:11px;color:var(--muted);font-weight:600">Type or press Enter to filter</span>\n            </div>\n            <div style="position:relative;display:flex;align-items:center">\n              <span style="position:absolute;left:13px;color:var(--primary);font-size:15px;pointer-events:none;opacity:0.85">🔍</span>\n              <input id="invQuery" placeholder="Type value to search…" autocomplete="off"\n                style="width:100%;height:42px;padding:0 38px 0 38px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13.5px;font-weight:600;box-shadow:0 1px 3px rgba(0,0,0,0.04);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)" />\n              <button class="b" id="invClear" type="button" title="Clear search"\n                style="position:absolute;right:8px;height:26px;width:26px;border-radius:50%;padding:0;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;background:var(--line);color:var(--muted);border:none;cursor:pointer;transition:all 0.15s">✕</button>\n            </div>\n          </div>', box_inv_html, count=1)

# 2. Redesign Optional Values Card in box_inv_html
box_inv_html = re.sub('<!-- Optional Values Saved into Every Record -->[\\s\\S]*?<!-- Bulk File Upload Progress with Live Percentage -->', '          <!-- Optional Values Saved into Every Record (Redesigned Enterprise Card) -->\n          <div class="card" id="optValuesCard"\n            style="padding:22px 24px;border:1.5px solid var(--line);border-radius:16px;margin:18px 0;background:var(--card);box-shadow:0 4px 20px rgba(0,0,0,0.03);transition:all 0.2s ease">\n            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:10px;border-bottom:1px solid var(--line);padding-bottom:14px">\n              <div style="display:flex;align-items:center;gap:12px">\n                <div style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg, rgba(56,189,248,0.18), rgba(99,102,241,0.18));color:var(--primary);display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800">\n                  ⚙️\n                </div>\n                <div>\n                  <h4 style="margin:0;font-size:15.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:8px">\n                    Optional Values (Saved into every record if blank in file)\n                  </h4>\n                  <p class="sub" style="margin:3px 0 0;font-size:12px;color:var(--muted)">\n                    If the Excel row already has a value for any of these, the row\'s value wins.\n                  </p>\n                </div>\n              </div>\n              <span class="badge" style="background:var(--card-subtle);border:1px solid var(--line);color:var(--text);font-size:11.5px;font-weight:700;padding:4px 12px;border-radius:99px;display:inline-flex;align-items:center;gap:6px">\n                <span>💡</span> <span>Auto-Fill Fallback</span>\n              </span>\n            </div>\n\n            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:14px">\n              <!-- Field 1: Model -->\n              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">\n                <label for="optModel" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">\n                  <span>📟</span> <span>Model</span>\n                </label>\n                <select id="optModel" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)">\n                  <option value="">-- None / Keep from file --</option>\n                  <option value="17IS">17IS</option>\n                  <option value="17L">17L</option>\n                  <option value="17IS-CAN">17IS-CAN</option>\n                  <option value="17A">17A</option>\n                  <option value="17S">17S</option>\n                  <option value="13L">13L</option>\n                  <option value="13S">13S</option>\n                  <option value="55L">55L</option>\n                  <option value="__new__">+ New model…</option>\n                </select>\n                <input id="optNewModel" placeholder="Enter new model name…" style="margin-top:6px;width:100%;height:36px;padding:0 10px;font-size:12px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" hidden />\n              </div>\n\n              <!-- Field 2: Dispatched Date -->\n              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">\n                <label for="optDispatchedDate" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">\n                  <span>📦</span> <span>Dispatched Date</span>\n                </label>\n                <input type="date" id="optDispatchedDate" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />\n              </div>\n\n              <!-- Field 3: Activation Date -->\n              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">\n                <label for="optActDate" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">\n                  <span>⚡</span> <span>Activation Date</span>\n                </label>\n                <input type="date" id="optActDate" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />\n              </div>\n\n              <!-- Field 4: Expiry Date -->\n              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">\n                <label for="optExpiryDate" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">\n                  <span>⏳</span> <span>Expiry Date</span>\n                </label>\n                <input type="date" id="optExpiryDate" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />\n              </div>\n\n              <!-- Field 5: Flash -->\n              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">\n                <label for="optFlash" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">\n                  <span>💾</span> <span>Flash</span>\n                </label>\n                <select id="optFlash" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)">\n                  <option value="">-- None / Keep from file --</option>\n                  <option value="Winbond">Winbond</option>\n                  <option value="Adesto">Adesto</option>\n                </select>\n              </div>\n\n              <!-- Field 6: Firmware -->\n              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">\n                <label for="optFirmware" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">\n                  <span>🏷️</span> <span>Firmware</span>\n                </label>\n                <input id="optFirmware" placeholder="e.g. v2.4.1" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)" />\n              </div>\n\n              <!-- Field 7: SIM Provider -->\n              <div style="background:var(--card-subtle);border:1px solid var(--line);border-radius:10px;padding:10px 12px">\n                <label for="optSimProvider" style="font-size:12px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">\n                  <span>📶</span> <span>SIM Provider</span>\n                </label>\n                <select id="optSimProvider" style="width:100%;height:38px;padding:0 10px;font-size:12.5px;font-weight:600;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text)">\n                  <option value="">-- None / Keep from file --</option>\n                  <option value="Airtel">Airtel</option>\n                  <option value="Vodafone">Vodafone</option>\n                  <option value="Jio">Jio</option>\n                  <option value="BSNL">BSNL</option>\n                </select>\n              </div>\n            </div>\n          </div>' + "\n\n          <!-- Bulk File Upload Progress with Live Percentage -->", box_inv_html, count=1)

containers['box-inv'] = box_inv_html

# 3. Redesign Search Value(s) in containers['box-fetch']
containers['box-fetch'] = re.sub('<div>\\s*<label for="fq"[^>]*>Search Value\\(s\\)</label>\\s*<input id="fq"[^>]*>\\s*</div>', '            <div style="flex:2;min-width:320px">\n              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">\n                <label for="fq" style="font-size:12.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px">\n                  <span style="font-size:14px">🎯</span> <span>Search Value(s)</span>\n                </label>\n                <span class="sub" style="font-size:11px;color:var(--muted);font-weight:600">Comma / newline separated values supported</span>\n              </div>\n              <div style="position:relative;display:flex;align-items:center">\n                <span style="position:absolute;left:14px;color:var(--primary);font-size:15px;pointer-events:none;opacity:0.85">🔎</span>\n                <input id="fq" placeholder="Enter term or paste comma/newline separated values (leave empty to list all)…"\n                  style="width:100%;height:44px;padding:0 36px 0 40px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-size:13px;font-weight:600;box-shadow:0 1px 3px rgba(0,0,0,0.04);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)" />\n                <button type="button" id="fqClearBtn" title="Clear query" onclick="const q = document.getElementById(\'fq\'); if(q){q.value=\'\'; q.focus();}"\n                  style="position:absolute;right:9px;height:26px;width:26px;border-radius:50%;border:none;background:var(--line);color:var(--muted);font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all 0.15s">✕</button>\n              </div>\n            </div>', containers['box-fetch'], count=1)

# 4. Redesign IMEI in containers['box-edit']
containers['box-edit'] = re.sub('<!-- Single IMEI Record Editor -->[\\s\\S]*?<div id="er"></div>\\s*</div>', '      <!-- Single IMEI Record Editor (Redesigned Modern Card) -->\n      <div class="card" style="padding:22px 24px;border:1.5px solid var(--line);border-radius:16px;background:var(--card);box-shadow:0 4px 18px rgba(0,0,0,0.03);margin-bottom:18px">\n        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px">\n          <div>\n            <h3 style="margin:0 0 4px 0; font-size:16px; font-weight:800; color:var(--text);display:flex;align-items:center;gap:8px">\n              <span style="font-size:18px">📱</span> <span>Edit / Delete Individual Record</span>\n            </h3>\n            <p class="sub" style="margin:0; font-size:12.5px;color:var(--muted)">Find an individual device record by its unique 15-digit IMEI to update metadata or delete.</p>\n          </div>\n          <span class="badge" style="background:var(--card-subtle);border:1px solid var(--line);color:var(--text);font-size:11.5px;font-weight:700;padding:4px 10px;border-radius:99px">\n            🔢 Standard 15 Digits\n          </span>\n        </div>\n\n        <div style="display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap">\n          <div style="flex:1;min-width:280px">\n            <label for="ei" style="font-size:12.5px;font-weight:800;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:6px">\n              <span>IMEI</span> <span style="font-size:11px;font-weight:600;color:var(--muted)">(15-Digit Device Identifier)</span>\n            </label>\n            <div style="position:relative;display:flex;align-items:center">\n              <span style="position:absolute;left:14px;color:var(--primary);font-size:16px;pointer-events:none;opacity:0.85">📱</span>\n              <input id="ei" placeholder="Enter 15-digit IMEI…" maxlength="20" autocomplete="off"\n                style="width:100%;height:44px;padding:0 36px 0 42px;border-radius:10px;border:1.5px solid var(--line);background:var(--card);color:var(--text);font-family:monospace;font-size:14.5px;font-weight:700;letter-spacing:0.8px;box-shadow:inset 0 1px 3px rgba(0,0,0,0.04);transition:all 0.2s cubic-bezier(0.16,1,0.3,1)" />\n              <button type="button" id="eiClearBtn" title="Clear IMEI" onclick="const i = document.getElementById(\'ei\'); if(i){i.value=\'\'; i.focus();}"\n                style="position:absolute;right:10px;height:24px;width:24px;border-radius:50%;border:none;background:var(--line);color:var(--muted);font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;cursor:pointer">✕</button>\n            </div>\n          </div>\n          <button class="b p" id="eg" type="button"\n            style="height:44px;padding:0 24px;font-size:13.5px;font-weight:800;border-radius:10px;background:linear-gradient(135deg, var(--primary), var(--primary-hover, #0a1c3d));color:#fff;display:inline-flex;align-items:center;gap:8px;box-shadow:0 4px 14px rgba(15,43,92,0.25);cursor:pointer;transition:all 0.2s ease">\n            <span>🔍</span> <span>Find Record</span>\n          </button>\n        </div>\n        <div id="er" style="margin-top:14px"></div>\n      </div>', containers['box-edit'], count=1)



# 3. Append SIM upload logic to INV block so Tab C (Bulk Upload) is 100% functional in Customer Inventory
sim_block_copy = loc['feature_blocks']['SIM']

# Also add Restore All handler and Customer Files actions to INV and SIM blocks
restore_all_js = r'''
    // --- Restore All Soft-Deleted SIMs Logic (Requirement 6.B) ---
    async function updateSimRestoreCount() {
      try {
        const res = await api('/api/devices/deleted?page=1&page_size=1');
        const cnt = (res && res.total != null) ? res.total : 0;
        if ($('simRestoreCountBadge')) $('simRestoreCountBadge').textContent = `${Number(cnt).toLocaleString()} records`;
        return cnt;
      } catch(e) {
        return 0;
      }
    }
    updateSimRestoreCount();

    if ($('btnSimRestoreAll')) {
      $('btnSimRestoreAll').onclick = async () => {
        const cnt = await updateSimRestoreCount();
        if (cnt <= 0) {
          toast('Recycle bin is empty. No soft-deleted records to restore.');
          return;
        }
        if (!confirm(`Are you sure you want to restore all ${Number(cnt).toLocaleString()} soft-deleted records from the Recycle Bin?\n\nActive IMEIs are safely preserved to prevent duplicate collisions.`)) {
          return;
        }
        const btn = $('btnSimRestoreAll');
        btn.disabled = true;
        btn.textContent = 'Restoring…';
        try {
          toast('Restoring all records from Recycle Bin…');
          const res = await api('/api/devices/restore-all', { method: 'POST' });
          toast(res.message || `Restored ${res.restored} records successfully!`);
          if (typeof showEventPopup === 'function') {
            showEventPopup({
              type: 'restoring',
              title: 'Bulk Restoration Complete',
              message: `Successfully restored ${Number(res.restored || 0).toLocaleString()} records. (${Number(res.skipped || 0).toLocaleString()} duplicates protected/skipped).`,
              duration: 4000
            });
          }
          await updateSimRestoreCount();
          if (typeof updateSidebarStats === 'function') await updateSidebarStats();
          if (typeof updateHomeStatsRibbon === 'function') await updateHomeStatsRibbon();
          if (typeof loadCU === 'function') await loadCU();
        } catch(err) {
          fail(err);
        } finally {
          btn.disabled = false;
          btn.textContent = '♻️ Restore All Records';
        }
      };
    }
'''

feature_blocks['SIM'] = loc['feature_blocks']['SIM']

# In INV block: enhanced Customer Files cards + download options + full Bulk Upload support
enhanced_inv_js = loc['feature_blocks']['INV']

# Update card template in INV
old_card_pattern = r'const card = c => `[\s\S]*?</div>`;'
new_card_template = '''const card = c => `
    <div class="cw" style="border:1px solid var(--line);border-radius:12px;padding:14px;background:var(--card);box-shadow:0 2px 8px rgba(0,0,0,0.02);display:flex;flex-direction:column;justify-content:space-between;gap:12px">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px">
        <div style="display:flex;align-items:center;gap:10px">
          ${avatarHtml(c)}
          <div>
            <b style="font-size:14px;color:var(--text);display:block">${esc(c.name)}</b>
            <span style="font-size:12px;color:var(--muted)">${Number(c.devices || 0).toLocaleString()} device records${c.expiring_or_expired ? ` · <span style="color:var(--warn);font-weight:700">${Number(c.expiring_or_expired || 0).toLocaleString()} expiring</span>` : ''}</span>
          </div>
        </div>
        <span class="tag ${c.devices > 0 ? 'ok' : 'mut'}" style="font-size:11px">${c.devices > 0 ? 'Active' : 'Empty'}</span>
      </div>
      <div class="ca" style="display:flex;gap:6px;flex-wrap:wrap">
        <button class="b" data-c="${c.id}" style="font-size:11.5px;padding:4px 8px" title="View device records">📋 Records</button>
        <button class="b" data-cdl="${c.id}" style="font-size:11.5px;padding:4px 8px" title="Download Excel workbook">📥 Excel</button>
        <button class="b" data-cfiles="${c.id}" style="font-size:11.5px;padding:4px 8px" title="View customer files">📁 Files</button>
        <button class="b" data-cav="${c.id}" style="font-size:11.5px;padding:4px 8px" title="Customize icon">🎨</button>
        ${staff ? `<button class="b" data-cren="${c.id}" style="font-size:11.5px;padding:4px 8px">Rename</button>
        <button class="b" data-cmerge="${c.id}" style="font-size:11.5px;padding:4px 8px">Merge</button>` : ''}
        ${canDelete ? `<button class="b d" data-cdel="${c.id}" style="font-size:11.5px;padding:4px 8px">Delete</button>` : ''}
      </div>
    </div>`;'''

enhanced_inv_js = re.sub(old_card_pattern, new_card_template, enhanced_inv_js, count=1)

# Add click handlers for Customer Files options (download Excel, view files, view records)
cust_files_handlers = r'''
        // --- 1. Dynamic Subnav & Badge Count ---
        if ($('invCustCountBadge')) $('invCustCountBadge').textContent = (CU || []).length || 0;

        // --- 2. Customer Cards Grid & Search (Requirement: Grid Format & Search) ---
        const card = c => `
          <div class="cw" style="border:1.5px solid var(--line);border-radius:14px;padding:16px 18px;background:var(--card);box-shadow:0 2px 10px rgba(0,0,0,0.03);display:flex;flex-direction:column;justify-content:space-between;gap:14px;transition:all 0.25s cubic-bezier(0.16,1,0.3,1)">
            <div>
              <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px">
                <div style="display:flex;align-items:center;gap:10px">
                  ${avatarHtml(c)}
                  <div>
                    <b style="font-size:15px;color:var(--text);display:block">${esc(c.name)}</b>
                    <span style="font-size:12px;color:var(--muted)">Customer ID: #${c.id}</span>
                  </div>
                </div>
                <span class="tag ${c.devices > 0 ? 'ok' : 'mut'}" style="font-size:11px">${c.devices > 0 ? 'Active' : 'Empty'}</span>
              </div>
              <div style="font-size:12.5px;color:var(--muted);margin-top:6px">
                <b style="color:var(--text)">${Number(c.devices || 0).toLocaleString()}</b> device records
                ${c.expiring_or_expired ? ` · <span style="color:var(--warn);font-weight:700">${Number(c.expiring_or_expired || 0).toLocaleString()} expiring</span>` : ''}
              </div>
            </div>
            <div class="ca" style="display:flex;gap:6px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:12px">
              <button class="b p" data-cview="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="View all device entries for this customer">👁️ Files (View Entries)</button>
              <button class="b" data-cdl="${c.id}" style="font-size:12px;padding:6px 12px;font-weight:700" title="Download Excel with all columns and values">📥 Download Excel</button>
              <button class="b" data-cav="${c.id}" style="font-size:12px;padding:6px 8px" title="Change icon">🎨</button>
              ${staff ? `<button class="b" data-cren="${c.id}" style="font-size:12px;padding:6px 8px">Rename</button>
              <button class="b" data-cmerge="${c.id}" style="font-size:12px;padding:6px 8px">Merge</button>` : ''}
              ${canDelete ? `<button class="b d" data-cdel="${c.id}" style="font-size:12px;padding:6px 8px">Delete</button>` : ''}
            </div>
          </div>`;

        const drawCustCards = () => {
          const inp = $('cs');
          const q = (inp ? inp.value : '').trim().toLowerCase();
          const clearBtn = $('csClearBtn');
          if (clearBtn) clearBtn.style.display = q ? 'block' : 'none';

          const filtered = (CU || []).filter(c => (c.name || '').toLowerCase().includes(q));
          if ($('csFilterCount')) {
            $('csFilterCount').textContent = q ? `Showing ${filtered.length} of ${CU.length} portfolios` : `Showing all ${CU.length} customer portfolios`;
          }

          const gridHtml = filtered.map(card).join('');
          $('cgrid').innerHTML = custHide ? '<div class="empty">Customer cards are hidden.</div>' : `
            <div class="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px">
              ${gridHtml || `<div class="empty">${CU.length ? 'No customer matches your search.' : 'No customers found.'}</div>`}
            </div>`;
        };

        if ($('cs')) $('cs').oninput = drawCustCards;
        if ($('csClearBtn')) {
          $('csClearBtn').onclick = () => {
            if ($('cs')) $('cs').value = '';
            $('csClearBtn').style.display = 'none';
            drawCustCards();
          };
        }

        // --- 3. Files Option as View Option: Display All Entries for Customer ---
        async function openCustomerEntriesView(customer) {
          try {
            toast(`Loading entries for ${customer.name}…`);
            if (typeof showBstplLoader === 'function') showBstplLoader(`Fetching all entries for ${customer.name}…`);

            const res = await api(`/api/devices?customer_id=${customer.id}&page_size=50000`);
            const items = (res && res.items) ? res.items : [];

            // Discover all dynamic columns
            const extraKeys = new Set();
            items.forEach(it => {
              if (it.extra && typeof it.extra === 'object') {
                Object.keys(it.extra).forEach(k => extraKeys.add(k));
              }
            });
            const allExtras = Array.from(new Set([...XC, ...extraKeys]));

            const viewCols = [
              { key: 'id', label: 'ID' },
              { key: 'customer_name', label: 'Customer' },
              ...COLS.map(c => ({ key: c[0], label: c[1] })),
              ...allExtras.map(k => ({ key: k, label: k.replace(/_/g, ' ').toUpperCase() })),
              { key: 'added_by', label: 'Added By' },
              { key: 'created_at', label: 'Created At' }
            ];

            const dlgHtml = `
              <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:14px;border-bottom:1px solid var(--line);padding-bottom:12px">
                <div>
                  <h4 style="margin:0;font-size:15px;color:var(--text)">${esc(customer.name)}</h4>
                  <span style="font-size:12.5px;color:var(--muted)">${items.length.toLocaleString()} device entries</span>
                </div>
                <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
                  <div class="cv-search-container" style="min-width:200px">
                    <span class="cv-search-icon-left">🔎</span>
                    <input id="dlgViewCustSearch" class="cv-search-input" style="height:34px;font-size:12.5px" placeholder="Search within entries…" />
                  </div>
                  <button type="button" class="b p" id="btnDlgCustDlExcel" style="font-size:12.5px;font-weight:700">📥 Download Excel</button>
                  <button type="button" class="b" id="btnDlgJumpToEditor" style="font-size:12.5px">📋 Edit in Inventory</button>
                </div>
              </div>
              <div class="tw" style="max-height:56vh;overflow:auto" id="dlgCustViewTableWrap">
                <table style="font-size:12px">
                  <thead>
                    <tr>
                      ${viewCols.map(c => `<th>${esc(c.label)}</th>`).join('')}
                    </tr>
                  </thead>
                  <tbody>
                    ${items.length ? items.map(d => `
                      <tr>
                        <td><b>${d.id}</b></td>
                        <td>${esc(customer.name)}</td>
                        ${COLS.map(c => `<td>${cell(d, c[0])}</td>`).join('')}
                        ${allExtras.map(k => `<td>${esc((d.extra || {})[k] != null ? (d.extra || {})[k] : '')}</td>`).join('')}
                        <td>${esc(d.added_by || '')}</td>
                        <td>${esc(d.created_at || '')}</td>
                      </tr>
                    `).join('') : '<tr><td colspan="30" class="empty">No device entries found for this customer.</td></tr>'}
                  </tbody>
                </table>
              </div>
            `;

            openDlg(`📁 Customer Entries — ${customer.name} (${items.length.toLocaleString()})`, dlgHtml, 'Close', async () => {});

            if ($('dlgViewCustSearch')) {
              $('dlgViewCustSearch').oninput = e => {
                const term = e.target.value.toLowerCase().trim();
                const rows = document.querySelectorAll('#dlgCustViewTableWrap tbody tr');
                rows.forEach(r => {
                  r.style.display = (!term || r.textContent.toLowerCase().includes(term)) ? '' : 'none';
                });
              };
            }

            if ($('btnDlgCustDlExcel')) {
              $('btnDlgCustDlExcel').onclick = () => downloadSingleCustomerExcel(customer);
            }

            if ($('btnDlgJumpToEditor')) {
              $('btnDlgJumpToEditor').onclick = () => {
                closeDlg();
                if ($('invCustSel')) $('invCustSel').value = customer.id;
                invCid = customer.id;
                invPage = 1;
                switchInvSubView('devices');
              };
            }
          } catch(err) {
            fail(err);
          } finally {
            if (typeof hideBstplLoader === 'function') hideBstplLoader();
          }
        }

        // --- 4. Single Customer Excel Download with ALL Columns & Values ---
        async function downloadSingleCustomerExcel(customer) {
          try {
            toast(`Generating Excel for ${customer.name}…`);
            if (typeof showBstplLoader === 'function') showBstplLoader(`Generating Excel file for ${customer.name}…`);

            const res = await api(`/api/devices?customer_id=${customer.id}&page_size=50000`);
            const items = (res && res.items) ? res.items : [];
            if (!items.length) {
              toast(`No records found for ${customer.name}.`);
              return;
            }

            const extraKeys = new Set();
            items.forEach(it => {
              if (it.extra && typeof it.extra === 'object') {
                Object.keys(it.extra).forEach(k => extraKeys.add(k));
              }
            });
            const allExtras = Array.from(new Set([...XC, ...extraKeys]));

            const headers = ['ID', 'Customer Name', ...COLS.map(c => c[1]), ...allExtras.map(k => k.replace(/_/g, ' ').toUpperCase()), 'Added By', 'Created At'];
            const rows = items.map(d => [
              d.id,
              customer.name,
              ...COLS.map(c => d[c[0]] != null ? d[c[0]] : ''),
              ...allExtras.map(k => (d.extra || {})[k] != null ? (d.extra || {})[k] : ''),
              d.added_by != null ? d.added_by : '',
              d.created_at != null ? d.created_at : ''
            ]);

            const safeName = (customer.name || 'Customer').replace(/[^a-zA-Z0-9_-]/g, '_');
            exportExcel(`${safeName}_Complete_Inventory`, headers, rows);
          } catch(err) {
            fail(err);
          } finally {
            if (typeof hideBstplLoader === 'function') hideBstplLoader();
          }
        }

        // --- 5. "Download All": Multi-Sheet Excel with Customer Names & User-Chosen Columns ---
        function openDownloadAllColumnChooser() {
          const allCols = [
            { key: 'id', label: 'ID', checked: true },
            { key: 'customer_name', label: 'Customer Name', checked: true },
            ...COLS.map(c => ({ key: c[0], label: c[1], checked: true })),
            ...XC.map(c => ({ key: c, label: c.replace(/_/g, ' ').toUpperCase(), checked: true })),
            { key: 'added_by', label: 'Added By', checked: false },
            { key: 'created_at', label: 'Created At', checked: false }
          ];

          const dlgHtml = `
            <div style="margin-bottom:12px">
              <p style="font-size:13px;color:var(--text);margin:0 0 10px">
                Choose the columns to include in the multi-customer workbook. <b>Each customer will have an individual sheet named after the customer</b>.
              </p>
              <div style="display:flex;gap:8px;margin-bottom:10px">
                <button type="button" class="b" id="btnDlgChooseSelectAll" style="font-size:12px;padding:4px 10px">Select All</button>
                <button type="button" class="b" id="btnDlgChooseDeselectAll" style="font-size:12px;padding:4px 10px">Deselect All</button>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px;max-height:46vh;overflow:auto;padding:8px;border:1px solid var(--line);border-radius:10px;background:var(--card-subtle)" id="dlgChooseColList">
              ${allCols.map(col => `
                <label style="display:flex;align-items:center;gap:8px;font-size:12px;padding:6px 10px;background:var(--card);border:1px solid var(--line);border-radius:6px;cursor:pointer">
                  <input type="checkbox" class="export-col-chk" value="${col.key}" data-label="${esc(col.label)}" ${col.checked ? 'checked' : ''} style="width:16px;height:16px;margin:0" />
                  <span>${esc(col.label)}</span>
                </label>
              `).join('')}
            </div>
          `;

          openDlg('📥 Download All Customers (Individual Sheets)', dlgHtml, '🚀 Download Workbook', async () => {
            const checkedInps = Array.from(document.querySelectorAll('.export-col-chk:checked'));
            if (!checkedInps.length) throw new Error('Please select at least one column to download.');
            const chosenCols = checkedInps.map(inp => ({ key: inp.value, label: inp.dataset.label }));
            await executeMultiCustomerDownload(chosenCols);
          });

          if ($('btnDlgChooseSelectAll')) {
            $('btnDlgChooseSelectAll').onclick = () => {
              document.querySelectorAll('.export-col-chk').forEach(c => c.checked = true);
            };
          }
          if ($('btnDlgChooseDeselectAll')) {
            $('btnDlgChooseDeselectAll').onclick = () => {
              document.querySelectorAll('.export-col-chk').forEach(c => c.checked = false);
            };
          }
        }

        async function executeMultiCustomerDownload(chosenCols) {
          try {
            toast('Fetching database records for multi-sheet workbook…');
            if (typeof showBstplLoader === 'function') {
              showBstplLoader('Generating multi-sheet Excel workbook with customer sheets…');
            }

            const [custs, rawDevs] = await Promise.all([
              api('/api/customers'),
              api('/api/devices?page=1&page_size=100000')
            ]);

            const customers = Array.isArray(custs) ? custs : (CU || []);
            const devices = (rawDevs && Array.isArray(rawDevs.items)) ? rawDevs.items : [];

            if (!customers.length) {
              toast('No customers found.');
              return;
            }

            const devsByCust = new Map();
            devices.forEach(d => {
              const cid = d.customer_id;
              if (!devsByCust.has(cid)) devsByCust.set(cid, []);
              devsByCust.get(cid).push(d);
            });

            const wb = XLSX.utils.book_new();
            let sheetsCount = 0;

            customers.forEach(c => {
              const custDevs = devsByCust.get(c.id) || [];
              let sheetName = (c.name || `Customer_${c.id}`).replace(/[\\/?*\[\]:]/g, '_').trim();
              if (!sheetName) sheetName = `Customer_${c.id}`;
              if (sheetName.length > 31) sheetName = sheetName.substring(0, 31);

              let uniqueName = sheetName;
              let counter = 1;
              while (wb.SheetNames.includes(uniqueName)) {
                uniqueName = sheetName.substring(0, 28) + '_' + counter++;
              }

              const headers = chosenCols.map(col => col.label);
              const rows = custDevs.map(d => chosenCols.map(col => {
                if (col.key === 'id') return d.id;
                if (col.key === 'customer_name') return c.name;
                if (col.key in d) return d[col.key] != null ? d[col.key] : '';
                if (d.extra && col.key in d.extra) return d.extra[col.key] != null ? d.extra[col.key] : '';
                return '';
              }));

              const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
              XLSX.utils.book_append_sheet(wb, ws, uniqueName);
              sheetsCount++;
            });

            const dateStr = new Date().toISOString().slice(0, 10);
            XLSX.writeFile(wb, `BSTPL_CustomerVault_All_Portfolios_${dateStr}.xlsx`);
            toast(`Multi-customer workbook downloaded with ${sheetsCount} customer sheets!`);
          } catch(err) {
            fail(err);
          } finally {
            if (typeof hideBstplLoader === 'function') hideBstplLoader();
          }
        }

        if ($('btnDownloadAllCustData')) {
          $('btnDownloadAllCustData').onclick = openDownloadAllColumnChooser;
        }

        // Delegate Customer Card Actions
        if ($('cgrid')) {
          $('cgrid').onclick = async e => {
            const btn = e.target.closest('button');
            if (!btn) return;
            const cid = btn.dataset.cview || btn.dataset.cdl || btn.dataset.c || btn.dataset.cfiles;
            if (!cid) return;

            const customer = (CU || []).find(x => String(x.id) === String(cid)) || { id: cid, name: `Customer #${cid}` };

            if (btn.dataset.cview || btn.dataset.cfiles) {
              // Files option works as View Option (displays all entries)
              await openCustomerEntriesView(customer);
              return;
            }

            if (btn.dataset.cdl) {
              // Download option in Excel with all column names and values
              await downloadSingleCustomerExcel(customer);
              return;
            }

            if (btn.dataset.c) {
              if ($('invCustSel')) $('invCustSel').value = cid;
              invCid = cid;
              invPage = 1;
              switchInvSubView('devices');
              return;
            }
          };
        }
'''

enhanced_inv_js = enhanced_inv_js.replace("await loadCustomerFilesContainer();", "await loadCustomerFilesContainer();\n" + cust_files_handlers)

# Append full bulk upload functions so Tab C in Customer Inventory is 100% functional
enhanced_inv_js = enhanced_inv_js + "\n\n" + '\n    // --- Check Entries & Rectify Update Logic (Requirement 2) ---\n    function openCheckEntriesModal() {\n      const dlg = $(\'dlgCheckEntriesModal\');\n      if (!dlg) return;\n      const records = (activeValResult && activeValResult.entries_requiring_update && activeValResult.entries_requiring_update.length)\n        ? activeValResult.entries_requiring_update\n        : (activeValResult && activeValResult.updated_sample && activeValResult.updated_sample.length)\n        ? activeValResult.updated_sample\n        : [];\n\n      if (!records.length) {\n        toast(\'ℹ️ No records currently require update. All scanned entries are either brand-new or match the database.\');\n        return;\n      }\n\n      if ($(\'checkEntriesEligibleCount\')) $(\'checkEntriesEligibleCount\').textContent = records.length.toLocaleString();\n      if ($(\'checkEntriesStatsBadge\')) $(\'checkEntriesStatsBadge\').textContent = `${records.length.toLocaleString()} records requiring updates`;\n\n      renderCheckEntriesTable(records);\n      dlg.showModal();\n    }\n    window.openCheckEntriesModal = openCheckEntriesModal;\n\n    function closeCheckEntriesModal() {\n      const dlg = $(\'dlgCheckEntriesModal\');\n      if (dlg) dlg.close();\n    }\n    window.closeCheckEntriesModal = closeCheckEntriesModal;\n\n    function renderCheckEntriesTable(records) {\n      const container = $(\'checkEntriesTableContainer\');\n      if (!container) return;\n\n      const filterTerm = ($(\'checkEntriesFilter\')?.value || \'\').toLowerCase().trim();\n      const filtered = filterTerm\n        ? records.filter(r => JSON.stringify(r).toLowerCase().includes(filterTerm))\n        : records;\n\n      if (!filtered.length) {\n        container.innerHTML = \'<div style="padding:24px;text-align:center;color:var(--muted)">No records match current filter.</div>\';\n        return;\n      }\n\n      let html = `\n        <table class="data-table" style="font-size:12.5px;margin:0;width:100%">\n          <thead>\n            <tr style="background:var(--card-subtle)">\n              <th style="width:40px">#</th>\n              <th>Identifier (ICCID / IMEI / Sr)</th>\n              <th>Customer</th>\n              <th>Detected Field Changes (Existing DB ➔ New Excel)</th>\n              <th style="width:120px;text-align:center">Action</th>\n            </tr>\n          </thead>\n          <tbody>\n      `;\n\n      filtered.slice(0, 100).forEach((r, idx) => {\n        const iden = r.iccid || r.imei || r.device_sr_no || r.id || \'—\';\n        const cust = r.customer_name || \'—\';\n        const changes = r.changed_fields || {};\n        let changeSummary = [];\n\n        for (const [field, diff] of Object.entries(changes)) {\n          const oldVal = (diff && diff.old != null && diff.old !== \'\') ? esc(String(diff.old)) : \'<i style="color:var(--muted)">empty</i>\';\n          const newVal = (diff && diff.new != null && diff.new !== \'\') ? esc(String(diff.new)) : \'<i style="color:var(--muted)">empty</i>\';\n          changeSummary.push(`\n            <div style="margin-bottom:4px">\n              <b style="color:var(--primary);text-transform:uppercase;font-size:11px">${esc(field.replace(/_/g, \' \'))}:</b>\n              <span style="color:var(--danger);text-decoration:line-through;margin-right:6px">${oldVal}</span>\n              ➔ <span style="color:var(--ok);font-weight:700;margin-left:6px">${newVal}</span>\n            </div>\n          `);\n        }\n\n        if (!changeSummary.length) {\n          changeSummary.push(\'<span style="color:var(--warn)">Pending field verification</span>\');\n        }\n\n        html += `\n          <tr>\n            <td>${idx + 1}</td>\n            <td><code style="font-weight:700">${esc(iden)}</code></td>\n            <td><b>${esc(cust)}</b></td>\n            <td>${changeSummary.join(\'\')}</td>\n            <td style="text-align:center">\n              <button class="b p" data-rectify-idx="${idx}" type="button" style="padding:4px 10px;font-size:11.5px;background:linear-gradient(135deg, #d97706, #b45309);color:#fff;border-radius:6px;cursor:pointer">\n                Rectify Row\n              </button>\n            </td>\n          </tr>\n        `;\n      });\n\n      if (filtered.length > 100) {\n        html += `<tr><td colspan="5" style="text-align:center;padding:12px;color:var(--muted)">Showing first 100 of ${filtered.length.toLocaleString()} records requiring update. Use "Rectify All" to update all.</td></tr>`;\n      }\n\n      html += `</tbody></table>`;\n      container.innerHTML = html;\n\n      container.querySelectorAll(\'button[data-rectify-idx]\').forEach(btn => {\n        btn.onclick = () => {\n          const idx = parseInt(btn.dataset.rectifyIdx, 10);\n          const rec = filtered[idx];\n          if (rec) executeRectifyUpdate([rec]);\n        };\n      });\n    }\n\n    async function executeRectifyUpdate(specificRecords = null) {\n      const records = specificRecords || (activeValResult && activeValResult.entries_requiring_update) || (activeValResult && activeValResult.updated_sample) || [];\n      if (!records.length) {\n        toast(\'⚠️ No eligible records selected for update.\');\n        return;\n      }\n\n      showBstplLoader(`Updating ${records.length.toLocaleString()} database records with validated Excel data…`, 10);\n\n      try {\n        const rows = records.map(r => ({\n          device_id: r.existing_id || r.id,\n          iccid: r.iccid,\n          imei: r.imei,\n          device_sr_no: r.device_sr_no,\n          customer_name: r.customer_name,\n          msisdn1: r.msisdn1,\n          msisdn2: r.msisdn2,\n          act_date: r.act_date,\n          expiry_date: r.expiry_date,\n          dispatched_date: r.dispatched_date,\n          model: r.model,\n          sim_provider: r.sim_provider,\n          sim_type: r.sim_type,\n          activation_plan: r.activation_plan,\n          firmware: r.firmware,\n          flash: r.flash,\n          extra: r.extra,\n          changed_fields: r.changed_fields\n        }));\n\n        let totalSuccess = 0;\n        let totalFailed = 0;\n        const batchSize = 2500;\n\n        for (let i = 0; i < rows.length; i += batchSize) {\n          const chunk = rows.slice(i, i + batchSize);\n          const pct = Math.round((i / rows.length) * 100);\n          updateBstplLoader(`Updating database records (${i.toLocaleString()} / ${rows.length.toLocaleString()})…`, pct);\n\n          const res = await api(\'/api/devices/bulk/rectify\', {\n            method: \'POST\',\n            body: JSON.stringify({ rows: chunk, skip_empty: true })\n          });\n\n          totalSuccess += (res.success_count || 0);\n          totalFailed += (res.failed_count || 0);\n        }\n\n        hideBstplLoader();\n        closeCheckEntriesModal();\n        toast(`✅ Successfully updated ${totalSuccess.toLocaleString()} database records.${totalFailed ? ` (${totalFailed} failed)` : \'\'}`);\n\n        if (typeof loadDevices === \'function\') loadDevices(1);\n        if (typeof loadCustomerFilesContainer === \'function\') loadCustomerFilesContainer();\n      } catch (err) {\n        hideBstplLoader();\n        toast(`❌ Error updating records: ${err.message}`);\n      }\n    }\n    window.executeRectifyUpdate = executeRectifyUpdate;\n\n    function exportCheckEntriesExcel() {\n      const records = (activeValResult && activeValResult.entries_requiring_update) || (activeValResult && activeValResult.updated_sample) || [];\n      if (!records.length) {\n        toast(\'No records to export.\');\n        return;\n      }\n      const headers = [\'#\', \'Identifier\', \'Customer Name\', \'Changed Field\', \'Old Database Value\', \'New Excel Value\', \'Status\'];\n      const rows = [];\n      records.forEach((r, idx) => {\n        const iden = r.iccid || r.imei || r.device_sr_no || r.id || \'\';\n        const cust = r.customer_name || \'\';\n        const changes = r.changed_fields || {};\n        for (const [field, diff] of Object.entries(changes)) {\n          rows.push([\n            idx + 1,\n            iden,\n            cust,\n            field,\n            diff?.old ?? \'\',\n            diff?.new ?? \'\',\n            \'Requires Update\'\n          ]);\n        }\n      });\n      exportExcel(\'check_entries_comparison_\' + new Date().toISOString().slice(0, 10), headers, rows);\n    }\n\n\n        // Wire Check Entries & Rectify Buttons (Requirement 2)\n        if ($(\'btnCheckEntriesModal\')) $(\'btnCheckEntriesModal\').onclick = openCheckEntriesModal;\n        if ($(\'btnRectifyUpdate\')) $(\'btnRectifyUpdate\').onclick = () => executeRectifyUpdate();\n        if ($(\'btnDoRectifyAll\')) $(\'btnDoRectifyAll\').onclick = () => executeRectifyUpdate();\n        if ($(\'btnExportCheckEntriesCsv\')) $(\'btnExportCheckEntriesCsv\').onclick = exportCheckEntriesExcel;\n        if ($(\'checkEntriesFilter\')) {\n          $(\'checkEntriesFilter\').oninput = () => {\n            const records = (activeValResult && activeValResult.entries_requiring_update) || (activeValResult && activeValResult.updated_sample) || [];\n            renderCheckEntriesTable(records);\n          };\n        }\n'
feature_blocks['INV'] = enhanced_inv_js + "\n\n" + sim_block_copy

# 4. Customization for FETCH block: Ensure EVERY database column is included & responsive scroll
fetch_block = loc['feature_blocks']['FETCH']

# Replace renderNormalFetchTable column determination with complete database schema discovery
old_fetch_col_logic = r'''        } else {
          displayCols = [
            { key: 'customer_name', label: 'Customer Name' },
            ...COLS.map(c => ({ key: c[0], label: c[1] })),
            ...XC.map(c => ({ key: c, label: c })),
            { key: 'added_by', label: 'Added By' },
            { key: 'created_at', label: 'Added On' }
          ];
        }'''

new_fetch_col_logic = r'''        } else {
          // Discover ALL dynamic columns from database items + extra dictionary (Requirement 7)
          const discoveredExtraKeys = new Set();
          (items || []).forEach(it => {
            if (it && it.extra && typeof it.extra === 'object') {
              Object.keys(it.extra).forEach(k => discoveredExtraKeys.add(k));
            }
          });
          const allExtraCols = Array.from(new Set([...XC, ...discoveredExtraKeys]));

          displayCols = [
            { key: 'id', label: 'ID' },
            { key: 'customer_name', label: 'Customer Name' },
            ...COLS.map(c => ({ key: c[0], label: c[1] })),
            ...allExtraCols.map(c => ({ key: c, label: c.replace(/_/g, ' ').toUpperCase() })),
            { key: 'added_by', label: 'Added By' },
            { key: 'created_at', label: 'Added On' }
          ];
        }'''

fetch_block = fetch_block.replace(old_fetch_col_logic, new_fetch_col_logic)

# Add search within fetched results input and instant filter
old_nf_table_html = r'''    <div class="row" style="align-items:center;justify-content:space-between;margin:14px 0 10px;flex-wrap:wrap;gap:10px">
      <div>
        <span style="font-size:14px;font-weight:800">${items.length.toLocaleString()} records found</span>
        <span class="sub" style="margin-left:8px;font-size:12px">Filtered by: <b>${activeFetchSimType.toUpperCase()}</b> | Visible Columns: <b>${displayCols.length}</b></span>
      </div>'''

new_nf_table_html = r'''    <div class="row" style="align-items:center;justify-content:space-between;margin:14px 0 10px;flex-wrap:wrap;gap:10px">
      <div>
        <span style="font-size:14px;font-weight:800">${items.length.toLocaleString()} records found</span>
        <span class="sub" style="margin-left:8px;font-size:12px">Filtered by: <b>${activeFetchSimType.toUpperCase()}</b> | All Database Columns: <b>${displayCols.length}</b></span>
      </div>
      <div style="flex:1;max-width:320px;min-width:200px">
        <div class="cv-search-container">
          <span class="cv-search-icon-left">🔎</span>
          <input id="nfFilterInput" class="cv-search-input" style="height:32px;font-size:12.5px" placeholder="Filter fetched results…" />
        </div>
      </div>'''

fetch_block = fetch_block.replace(old_nf_table_html, new_nf_table_html)

# Add in-table search filter listener
nf_filter_listener = r'''
        // Instant filter within fetched results (Requirement 7)
        if ($('nfFilterInput')) {
          $('nfFilterInput').oninput = e => {
            const term = e.target.value.toLowerCase().trim();
            const rows = wrap.querySelectorAll('tbody tr');
            rows.forEach(r => {
              r.style.display = (!term || r.textContent.toLowerCase().includes(term)) ? '' : 'none';
            });
          };
        }
'''

fetch_block = fetch_block.replace("wrap.innerHTML = html;", "wrap.innerHTML = html;\n" + nf_filter_listener)

# Replace Download NOT FOUND button label with user's requested "Download Fetch Data Error Entries (Excel)"
fetch_block = fetch_block.replace(
    "${notFoundList.length ? `<button class=\"b\" id=\"btnBfDlNotFound\" type=\"button\">📥 Download NOT FOUND List</button>` : ''}",
    "${notFoundList.length ? `<button class=\"b\" id=\"btnBfDlNotFound\" type=\"button\" style=\"font-weight:700\">📥 Download Fetch Data Error Entries (Excel)</button>` : ''}"
)

# Wire 6-column error report export with 0-error protection (Requirement 5)
old_not_found_str = "exportExcel(`${prefix}_not_found_list`, ['NOT FOUND Term'], notFoundList.map(t => [t]));"
new_not_found_str = """if (!notFoundList || notFoundList.length === 0) {
              toast('ℹ️ No error entries recorded from latest fetch.');
              return;
            }
            const errHeaders = [
              'ICCID / CCID',
              'Customer / Device Details',
              'Error Reason',
              'Fetch Status',
              'API Response / Failure Description',
              'Date & Time of Processing'
            ];
            const nowFormatted = new Date().toLocaleString();
            const errRows = notFoundList.map(term => [
              term,
              'Not found in active customer database',
              'Search query term did not match any active IMEI, ICCID, or serial number',
              'FAILED - NOT FOUND',
              '404 No matching database records found',
              nowFormatted
            ]);
            exportExcel('fetch_data_error_entries_' + new Date().toISOString().slice(0, 10), errHeaders, errRows);"""

fetch_block = fetch_block.replace(old_not_found_str, new_not_found_str)

feature_blocks['FETCH'] = fetch_block


feature_blocks['HOME'] = r"""
      /* =========================================================================
         HOME OVERVIEW & REAL-TIME TELEMETRY CONTROLLER (Enhanced)
         ========================================================================= */
      // 1. Live Stream & Telemetry State Setup
      livePolling = true;
      liveTimer = null;
      liveIntervalSec = 10;
      liveCid = '';
      liveQ = '';
      liveCol = 'all';
      livePage = 1;
      sortCol = 'id';
      sortDir = 'desc';
      liveHealthData = null;
      liveReportList = null;
      let alertsActive = true;

      // Data Health pagination & filter state (Requirement 3)
      let dhPage = 1;
      let dhPageSize = 10;
      let dhSelectAll = false;
      let dhQ = '';
      let dhDebounce = null;
      let lastHealthData = null;

      // 2. User Greeting & Profile Synchronization
      async function updateHomeUserGreeting() {
        let user = getUser();
        try {
          const me = await api('/api/me');
          if (me && (me.name || me.user_id)) {
            user = me;
            localStorage.setItem('user', JSON.stringify(me));
          }
        } catch(e) {}

        const d = new Date();
        const hrs = d.getHours();
        let greet = 'Good morning';
        if (hrs >= 12 && hrs < 17) greet = 'Good afternoon';
        else if (hrs >= 17) greet = 'Good evening';

        const dispName = user.name || user.full_name || user.username || 'Shilish Reddy';
        const roleName = (user.role || 'ADMIN').toUpperCase();
        const firstLetter = (dispName.charAt(0) || 'S').toUpperCase();

        if ($('hi')) $('hi').textContent = `${greet}, ${dispName}`;
        if ($('rolePill')) {
          $('rolePill').textContent = roleName;
          $('rolePill').className = `role-pill ${roleName.toLowerCase().includes('admin') ? 'admin' : 'standard'}`;
        }
        if ($('userAvatarCircle')) $('userAvatarCircle').textContent = firstLetter;
      }

      // 3. Expiry Alert Banner Synchronization
      async function updateHomeExpiryBanner() {
        try {
          const res = await api('/api/alerts/expiry?days=30');
          if (res) {
            const expCount = (res.expired || []).length || res.total_expired || 0;
            const soonCount = (res.expiring_soon || []).length || res.total_expiring || 0;
            if ($('cntExpiredGlobalBadge')) $('cntExpiredGlobalBadge').textContent = Number(expCount).toLocaleString('en-US');
            if ($('cntExpiringSoonGlobalBadge')) $('cntExpiringSoonGlobalBadge').textContent = Number(soonCount).toLocaleString('en-US');
            if ($('globalExpiryAlertText')) {
              $('globalExpiryAlertText').textContent = `${Number(expCount).toLocaleString('en-US')} SIM(s) have already expired, and ${Number(soonCount).toLocaleString('en-US')} are expiring within 30 days.`;
            }
          }
        } catch(e) {
          console.log('Notice: Expiry banner sync:', e);
        }
      }

      // 4. 4-Stat Metric Cards Ribbon Synchronization (100% Dynamic)
      async function updateHomeStatsRibbon() {
        try {
          const [s, xc] = await Promise.all([
            api('/api/stats').catch(() => null),
            api('/api/extra-cols').catch(() => [])
          ]);
          if (s) {
            S = s;
            const custCount = s.total_customers != null ? s.total_customers : (s.customers != null ? s.customers : 0);
            const devCount = s.total_devices != null ? s.total_devices : (s.devices != null ? s.devices : 0);
            const uCount = s.added_by_you != null ? s.added_by_you : Math.max(0, devCount - 2);
            const extraCount = Array.isArray(xc) ? xc.length : (s.extra_cols_count || 0);

            if ($('statCustomers')) $('statCustomers').textContent = Number(custCount).toLocaleString('en-US');
            if ($('statDevices')) $('statDevices').textContent = Number(devCount).toLocaleString('en-US');
            if ($('statAddedByYou')) $('statAddedByYou').textContent = Number(uCount).toLocaleString('en-US');
            if ($('statColumns')) $('statColumns').textContent = String(COLS.length + extraCount);

            if ($('sbLiveDevCount')) $('sbLiveDevCount').textContent = Number(devCount).toLocaleString('en-US');
            if ($('sbLiveCustCount')) $('sbLiveCustCount').textContent = Number(custCount).toLocaleString('en-US');
          }
        } catch(e) {
          console.log('Notice: Stats ribbon sync:', e);
        }
      }

      // 5. Populate Customer Dropdown
      async function populateLiveCustomerDropdown() {
        const sel = $('liveCustFilter');
        if (!sel) return;
        try {
          const custs = await api('/api/customers');
          if (Array.isArray(custs)) {
            CU = custs;
            const curVal = sel.value;
            sel.innerHTML = '<option value="">All Customers</option>' +
              custs.map(c => `<option value="${c.id}" ${String(c.id) === String(curVal) ? 'selected' : ''}>${esc(c.name || c.customer_name)}</option>`).join('');
          }
        } catch(e) {}
      }

      // 6. Cart Count Badge & Navigation
      async function updateCartCountBadge() {
        try {
          const bin = await api('/api/devices/deleted?page=1&page_size=1');
          const cnt = bin && bin.total != null ? bin.total : 0;
          if ($('headerCartCountBadge')) $('headerCartCountBadge').textContent = String(cnt);
        } catch(e) {}
      }

      function openCartModal() {
        window.location.href = 'edit-delete.html#box-bin';
      }

      // 7. Edit Employee Name Modal
      async function openEditNameModal() {
        const dlg = $('dlgEditName');
        if (!dlg) return;
        const u = getUser();
        let currentName = u.name || u.user_id || 'Shilish Reddy';
        if ($('editNameCurrent')) $('editNameCurrent').value = currentName;
        if ($('editNameUpdated')) $('editNameUpdated').value = '';
        if ($('editNameConfirm')) $('editNameConfirm').value = '';
        if ($('editNameError')) {
          $('editNameError').textContent = '';
          $('editNameError').hidden = true;
        }
        if (!dlg.open) dlg.showModal();
        try {
          const fresh = await api('/api/me');
          if (fresh && fresh.name && $('editNameCurrent')) $('editNameCurrent').value = fresh.name;
        } catch (_) {}
        setTimeout(() => $('editNameUpdated')?.focus(), 50);
      }

      function closeEditNameModal() {
        const dlg = $('dlgEditName');
        if (dlg && dlg.open) dlg.close();
      }

      async function submitEditNameModal() {
        const errEl = $('editNameError');
        const currentName = ($('editNameCurrent')?.value || '').trim();
        const updatedName = ($('editNameUpdated')?.value || '').trim();
        const confirmName = ($('editNameConfirm')?.value || '').trim();

        if (errEl) { errEl.textContent = ''; errEl.hidden = true; }

        if (!updatedName) {
          if (errEl) { errEl.textContent = 'Please enter an updated name.'; errEl.hidden = false; }
          return;
        }
        if (updatedName.toLowerCase() === currentName.toLowerCase()) {
          if (errEl) { errEl.textContent = 'Updated name must be different from current name.'; errEl.hidden = false; }
          return;
        }
        if (updatedName !== confirmName) {
          if (errEl) { errEl.textContent = 'Updated name and confirm name do not match.'; errEl.hidden = false; }
          return;
        }

        const btn = $('btnConfirmEditName');
        if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }

        try {
          const res = await api('/api/me/name', {
            method: 'PUT',
            body: JSON.stringify({ name: updatedName, confirm_name: confirmName })
          });
          const finalName = res.name || updatedName;

          const u = getUser();
          u.name = finalName;
          localStorage.setItem('user', JSON.stringify(u));

          await updateHomeUserGreeting();
          toast('Display name updated successfully');
          closeEditNameModal();
        } catch (err) {
          if (errEl) { errEl.textContent = err.message || 'Failed to update name.'; errEl.hidden = false; }
        } finally {
          if (btn) { btn.disabled = false; btn.textContent = 'Save'; }
        }
      }

      if ($('bEditMyName')) $('bEditMyName').onclick = openEditNameModal;
      if ($('bPw')) $('bPw').onclick = openChangePasswordModal;
      if ($('bLo')) $('bLo').onclick = () => logout(true);

      const formEditName = $('formEditName');
      if (formEditName) {
        formEditName.onsubmit = async e => {
          e.preventDefault();
          await submitEditNameModal();
        };
      }

      // 8. Change Password Modal
      function openChangePasswordModal() {
        const dlg = $('pwd');
        if (!dlg) return;
        if ($('p1')) $('p1').value = '';
        if ($('p2')) $('p2').value = '';
        if ($('p3')) $('p3').value = '';
        if ($('pe')) { $('pe').textContent = ''; $('pe').hidden = true; }
        if (!dlg.open) dlg.showModal();
        setTimeout(() => $('p1')?.focus(), 50);
      }

      function closeChangePasswordModal() {
        const dlg = $('pwd');
        if (dlg && dlg.open) dlg.close();
      }

      function togglePasswordInputVisibility(id) {
        const inp = $(id);
        if (inp) {
          inp.type = inp.type === 'password' ? 'text' : 'password';
        }
      }

      const formChangePw = $('pf');
      if (formChangePw) {
        formChangePw.onsubmit = async e => {
          e.preventDefault();
          const cur = ($('p1')?.value || '').trim();
          const np = ($('p2')?.value || '').trim();
          const cnp = ($('p3')?.value || '').trim();
          const errEl = $('pe');
          if (errEl) { errEl.textContent = ''; errEl.hidden = true; }

          if (!cur) {
            if (errEl) { errEl.textContent = 'Please enter your current password.'; errEl.hidden = false; }
            return;
          }
          if (np.length < 8) {
            if (errEl) { errEl.textContent = 'New password must be at least 8 characters long.'; errEl.hidden = false; }
            return;
          }
          if (np !== cnp) {
            if (errEl) { errEl.textContent = 'New password and confirm password do not match.'; errEl.hidden = false; }
            return;
          }

          const btn = $('btnConfirmChangePw');
          if (btn) { btn.disabled = true; btn.textContent = 'Updating…'; }

          try {
            await api('/api/me/password', {
              method: 'PUT',
              body: JSON.stringify({ current_password: cur, new_password: np, confirm_password: cnp })
            });
            toast('Password updated successfully');
            closeChangePasswordModal();
          } catch(err) {
            if (errEl) { errEl.textContent = err.message || 'Failed to update password.'; errEl.hidden = false; }
          } finally {
            if (btn) { btn.disabled = false; btn.textContent = 'Confirm & Change Password'; }
          }
        };
      }

      // 9. Logout
      function logout(confirmFirst = false) {
        if (confirmFirst && !confirm('Are you sure you want to sign out of BSTPL CustomerVault?')) {
          return;
        }
        if (typeof showBstplLoader === 'function') {
          showBstplLoader('Signing out of BSTPL CustomerVault…');
        }
        try {
          api('/api/logout', { method: 'POST' }).catch(() => {});
        } catch(e) {}
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        tok = '';
        setTimeout(() => {
          window.location.href = 'index.html?logout=1';
        }, 220);
      }

      // 10. Top Bar Action Button Listeners
      if ($('bRefresh')) {
        $('bRefresh').onclick = async () => {
          toast('Refreshing Home Overview…');
          await Promise.all([
            runLiveCycle(true),
            loadHealthContainer(),
            updateHomeStatsRibbon(),
            updateHomeExpiryBanner(),
            updateHomeUserGreeting(),
            updateCartCountBadge()
          ]);
          toast('Home Overview refreshed');
        };
      }

      if ($('bQs')) {
        $('bQs').onclick = () => {
          const inp = $('liveSearchInput');
          if (inp) {
            inp.focus();
            inp.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        };
      }

      if ($('bAl')) {
        $('bAl').textContent = 'Alerts: ON';
        $('bAl').classList.add('on');
        $('bAl').onclick = () => {
          alertsActive = !alertsActive;
          $('bAl').textContent = alertsActive ? 'Alerts: ON' : 'Alerts: OFF';
          $('bAl').classList.toggle('on', alertsActive);
          const banner = $('globalExpiryAlertBanner');
          if (banner) banner.style.display = alertsActive ? 'flex' : 'none';
        };
      }

      if ($('btnViewExpiredGlobal')) {
        $('btnViewExpiredGlobal').onclick = () => {
          window.location.href = 'alerts.html?tab=expired';
        };
      }

      if ($('btnViewExpiringSoonGlobal')) {
        $('btnViewExpiringSoonGlobal').onclick = () => {
          window.location.href = 'alerts.html?tab=expiring';
        };
      }

      // 11. Live Telemetry Controls Listeners
      if ($('toggleLive')) {
        $('toggleLive').onclick = () => {
          livePolling = !livePolling;
          $('toggleLive').textContent = livePolling ? '🟢 Live Updates: ON' : '⏸️ Polling: PAUSED';
          $('toggleLive').classList.toggle('on', livePolling);
          if (livePolling) runLiveCycle(true);
          else clearTimeout(liveTimer);
        };
      }

      if ($('liveIntervalSel')) {
        $('liveIntervalSel').onchange = e => {
          liveIntervalSec = +e.target.value;
          if (livePolling) { clearTimeout(liveTimer); runLiveCycle(true); }
        };
      }

      if ($('manualLiveRefresh')) {
        $('manualLiveRefresh').onclick = async () => {
          toast('Refreshing live telemetry…');
          await runLiveCycle(true);
        };
      }

      if ($('liveCustFilter')) {
        $('liveCustFilter').onchange = e => {
          liveCid = e.target.value;
          livePage = 1;
          updateLiveFeedTable();
        };
      }

      if ($('liveFieldFilter')) {
        $('liveFieldFilter').onchange = e => {
          liveCol = e.target.value;
          livePage = 1;
          updateLiveFeedTable();
        };
      }

      // Instant Live Search with Spinner, Clear button & 180ms debounce (Requirement 2 & 5)
      let liveDebounce;
      const liveInp = $('liveSearchInput');
      const liveSpinner = $('liveSearchSpinner');
      const liveClearBtn = $('liveSearchClearBtn');

      if (liveInp) {
        liveInp.oninput = e => {
          liveQ = e.target.value;
          livePage = 1;
          if (liveClearBtn) liveClearBtn.style.display = liveQ ? 'block' : 'none';
          if (liveSpinner) liveSpinner.style.display = 'inline-block';
          clearTimeout(liveDebounce);
          liveDebounce = setTimeout(async () => {
            try {
              await updateLiveFeedTable();
            } finally {
              if (liveSpinner) liveSpinner.style.display = 'none';
            }
          }, 180);
        };
      }

      if (liveClearBtn) {
        liveClearBtn.onclick = () => {
          if (liveInp) liveInp.value = '';
          liveClearBtn.style.display = 'none';
          liveQ = '';
          livePage = 1;
          updateLiveFeedTable();
        };
      }

      if ($('liveSearchClear')) {
        $('liveSearchClear').onclick = () => {
          liveQ = ''; liveCol = 'all'; liveCid = ''; livePage = 1;
          if ($('liveCustFilter')) $('liveCustFilter').value = '';
          if ($('liveFieldFilter')) $('liveFieldFilter').value = 'all';
          if ($('liveSearchInput')) $('liveSearchInput').value = '';
          if (liveClearBtn) liveClearBtn.style.display = 'none';
          updateLiveFeedTable();
        };
      }

      if ($('liveExportExcel')) {
        $('liveExportExcel').onclick = async () => {
          try {
            toast('Exporting live feed records…');
            const d = await api(`/api/devices?page=1&page_size=5000&q=${encodeURIComponent(liveQ)}&column=${liveCol}${liveCid ? '&customer_id=' + liveCid : ''}`);
            const headers = ['ID', ...COLS.map(c => c[1]), ...XC];
            const rows = d.items.map(dev => [dev.id, ...COLS.map(c => dev[c[0]] || ''), ...XC.map(c => (dev.extra || {})[c] || '')]);
            exportExcel('Live_Feed_Inventory', headers, rows);
          } catch (err) { fail(err); }
        };
      }

      // 12. Run Live Telemetry Cycle
      async function runLiveCycle(immediate = false) {
        if (!tok) { clearTimeout(liveTimer); return; }
        try {
          const [rawIns, rawHea, rawAct] = await Promise.all([
            api('/api/inventory/insights').catch(() => null),
            api('/api/inventory/health?page=1&page_size=10').catch(() => null),
            api('/api/activity?page=1&page_size=8').catch(() => null)
          ]);
          const ins = (rawIns && typeof rawIns === 'object') ? rawIns : { total_devices: 0, total_customers: 0, expiring_30: 0, expired: 0 };
          const hea = (rawHea && typeof rawHea === 'object') ? rawHea : { score: 100, completeness: {}, issues: [] };
          const actData = (rawAct && typeof rawAct === 'object' && Array.isArray(rawAct.items)) ? rawAct : { items: [] };

          // 1. KPI Ribbon
          const completenessAvg = Object.values(hea.completeness || {}).length
            ? Math.round(Object.values(hea.completeness).reduce((a, b) => a + b, 0) / Object.values(hea.completeness).length)
            : 100;

          if ($('liveKpis')) {
            $('liveKpis').innerHTML = `
              <div class="card stat" style="border-left-color:var(--primary)"><b>${Number(ins.total_devices || 0).toLocaleString('en-US')}</b><span>Total Live Devices</span></div>
              <div class="card stat" style="border-left-color:#8b5cf6"><b>${Number(ins.total_customers || 0).toLocaleString('en-US')}</b><span>Active Customers</span></div>
              <div class="card stat" style="border-left-color:var(--warn)"><b>${Number(ins.expiring_30 || 0).toLocaleString('en-US')}</b><span>Expiring in 30 Days</span></div>
              <div class="card stat" style="border-left-color:var(--danger)"><b>${Number(ins.expired || 0).toLocaleString('en-US')}</b><span>Expired Devices</span></div>
              <div class="card stat" style="border-left-color:var(--ok)"><b>${completenessAvg}%</b><span>Data Health Score</span></div>
            `;
          }

          // 2. Live Feed Table
          await updateLiveFeedTable();

          // 3. Live Telemetry Activity Stream
          if ($('liveActivityBody')) {
            $('liveActivityBody').innerHTML = actData.items.length ? `
              <div class="tw"><table><thead><tr>
                <th>Timestamp</th><th>Employee</th><th>Action</th><th>Details</th><th>IP Address</th>
              </tr></thead><tbody>
              ${actData.items.map(i => {
                const a = ALBL[i.action] || [i.action || 'Activity', 'mut'];
                const d = new Date(i.created_at);
                const timeStr = isNaN(d.getTime()) ? i.created_at : d.toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
                return `<tr>
                  <td>${esc(timeStr)}</td>
                  <td><b>${esc(i.user_name || '')}</b> <span style="color:var(--muted)">(${esc(i.user_login || '')})</span></td>
                  <td><span class="tag ${a[1]}">${esc(a[0])}</span></td>
                  <td><code>${esc(i.detail || '')}</code></td>
                  <td><code>${esc(i.ip || '127.0.0.1')}</code></td>
                </tr>`;
              }).join('')}
              </tbody></table></div>` : '<div class="empty">No live activity recorded.</div>';
          }

          if ($('liveTime')) {
            $('liveTime').textContent = `Updated: ${new Date().toLocaleTimeString()}`;
          }
        } catch (err) {
          console.error('Live cycle error:', err);
        } finally {
          if (livePolling && tok) {
            clearTimeout(liveTimer);
            liveTimer = setTimeout(() => runLiveCycle(), liveIntervalSec * 1000);
          }
        }
      }

      // 13. Update Live Feed Table (with meaningful empty state)
      async function updateLiveFeedTable() {
        try {
          const rawD = await api(`/api/devices?page=${livePage}&page_size=25&q=${encodeURIComponent(liveQ)}&column=${liveCol}&sort_by=${sortCol}&sort_dir=${sortDir}${liveCid ? '&customer_id=' + liveCid : ''}`).catch(() => null);
          const d = (rawD && typeof rawD === 'object' && Array.isArray(rawD.items)) ? rawD : { items: [], total: 0, page: 1, pages: 1 };
          const s = (d.page - 1) * 25;
          const staff = canDeleteValidInventory();
          const act = dev => `
            <div style="display:flex;gap:4px">
              <button class="b" data-editdev="${dev.id}" style="height:28px;padding:0 8px;font-size:12px">Edit</button>
              ${staff ? `<button class="b d" data-del="${dev.id}" style="height:28px;padding:0 8px;font-size:12px">Delete</button>` : ''}
            </div>`;

          if ($('liveMasterTable')) {
            if (!d.items.length) {
              const emptyMsg = liveQ ? `🔍 No matching records found for "${esc(liveQ)}". Try adjusting your search query or column filter.` : `No device records found in this view.`;
              $('liveMasterTable').innerHTML = `
                <div class="empty" style="padding:28px;text-align:center;font-size:13.5px;color:var(--muted)">
                  ${emptyMsg}
                </div>`;
            } else {
              $('liveMasterTable').innerHTML = `
                <div class="meta" style="margin-bottom:8px">
                  <span>${Number(d.total).toLocaleString('en-US')} records · showing ${d.total ? s + 1 : 0}–${s + d.items.length}</span>
                  <div class="pg">
                    <button class="b" id="livePrevPg" ${livePage < 2 ? 'disabled' : ''}>Prev</button>
                    <span>Page ${d.page} of ${d.pages || 1}</span>
                    <button class="b" id="liveNextPg" ${livePage >= (d.pages || 1) ? 'disabled' : ''}>Next</button>
                  </div>
                </div>
                ${renderTable(d.items, act)}
              `;

              if ($('livePrevPg')) $('livePrevPg').onclick = () => { if (livePage > 1) { livePage--; updateLiveFeedTable(); } };
              if ($('liveNextPg')) $('liveNextPg').onclick = () => { if (livePage < (d.pages || 1)) { livePage++; updateLiveFeedTable(); } };
            }
          }
        } catch (err) {
          if ($('liveMasterTable')) $('liveMasterTable').innerHTML = `<div class="empty err">${esc(err.message)}</div>`;
        }
      }

      // 14. Data Health & Integrity Report with Pagination (10 per page default) and Select All (Requirement 3)
      async function loadHealthContainer() {
        const hc = $('healthContainerBody') || $('liveHealthBody');
        if (!hc) return;

        try {
          const url = `/api/inventory/health?page=${dhPage}&page_size=${dhPageSize}&select_all=${dhSelectAll ? 'true' : 'false'}${dhQ ? '&q=' + encodeURIComponent(dhQ) : ''}`;
          const d = await api(url);
          if (!d) throw new Error('Failed to load health report');
          lastHealthData = d;
          liveHealthData = d;

          const totalIssues = d.total_issues != null ? d.total_issues : ((d.issues && Array.isArray(d.issues)) ? d.issues.length : 0);
          const curPage = d.page || dhPage;
          const totalPages = d.pages || Math.max(1, Math.ceil(totalIssues / dhPageSize));
          const startIdx = totalIssues ? (curPage - 1) * dhPageSize + 1 : 0;
          const endIdx = dhSelectAll ? totalIssues : Math.min(totalIssues, startIdx + (d.issues ? d.issues.length : 0) - 1);

          hc.innerHTML = `
            <div class="stats" style="margin-top:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px">
              <div class="card stat" style="${d.duplicate_imei_count ? 'border-left-color:var(--danger)' : ''}">
                <b>${Number(d.duplicate_imei_count || 0).toLocaleString()}</b><span>Duplicate IMEIs</span>
              </div>
              <div class="card stat" style="${d.duplicate_iccid_count ? 'border-left-color:var(--danger)' : ''}">
                <b>${Number(d.duplicate_iccid_count || 0).toLocaleString()}</b><span>Duplicate ICCIDs</span>
              </div>
              <div class="card stat" style="${d.duplicate_sr_count ? 'border-left-color:var(--danger)' : ''}">
                <b>${Number(d.duplicate_sr_count || 0).toLocaleString()}</b><span>Duplicate Serial Numbers</span>
              </div>
              <div class="card stat" style="${d.bad_imei_count ? 'border-left-color:var(--warn)' : ''}">
                <b>${Number(d.bad_imei_count || 0).toLocaleString()}</b><span>Invalid IMEI Lengths (&ne;15)</span>
              </div>
              <div class="card stat" style="${d.bad_date_count ? 'border-left-color:var(--danger)' : ''}">
                <b>${Number(d.bad_date_count || 0).toLocaleString()}</b><span>Expiry Before Activation</span>
              </div>
            </div>

            <div class="metric-box" style="margin:16px 0;padding:16px;border:1px solid var(--line);border-radius:12px;background:var(--card-subtle)">
              <h4 style="margin:0 0 12px;font-size:14px;color:var(--text)">📊 Column Completeness Percentage</h4>
              <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px">
                ${Object.entries(d.completeness || {}).map(([col, pct]) => `
                  <div>
                    <div class="dist-item" style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px"><span style="text-transform:capitalize">${esc(col.replace(/_/g, ' '))}</span><b>${pct}%</b></div>
                    <div class="progress-bar" style="height:6px;background:var(--line);border-radius:99px;overflow:hidden"><div class="progress-fill ${pct > 80 ? 'ok' : pct > 40 ? '' : 'bad'}" style="width:${pct}%;height:100%;background:${pct > 80 ? 'var(--ok)' : pct > 40 ? 'var(--primary)' : 'var(--danger)'}"></div></div>
                  </div>`).join('')}
              </div>
            </div>

            <!-- Detected Integrity Issues Header with Search & Pagination Controls -->
            <div style="margin:20px 0 10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
              <h4 style="margin:0;font-size:15px;font-weight:800;color:var(--text)">
                ⚠️ Detected Integrity Issues (${Number(totalIssues).toLocaleString()})
              </h4>
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                <div class="cv-search-container" style="min-width:200px;max-width:280px">
                  <span class="cv-search-icon-left">🔎</span>
                  <input id="dhSearchInput" class="cv-search-input" style="height:32px;font-size:12.5px" placeholder="Filter issues…" value="${esc(dhQ)}" />
                  ${dhQ ? `<button type="button" class="cv-search-clear-btn" id="dhClearSearchBtn" style="display:block">✕</button>` : ''}
                </div>
                <button type="button" class="dh-select-all-btn ${dhSelectAll ? 'active' : ''}" id="dhSelectAllBtn">
                  ${dhSelectAll ? '📄 View Paginated (10/pg)' : '📋 Select All (View All)'}
                </button>
              </div>
            </div>

            <!-- Pagination Toolbar -->
            <div class="dh-pagination-bar">
              <div class="dh-page-info">
                ${dhSelectAll ? `Showing all <b>${Number(totalIssues).toLocaleString()}</b> detected issues` : `Showing <b>${startIdx}–${endIdx}</b> of <b>${Number(totalIssues).toLocaleString()}</b> issues (Page <b>${curPage}</b> of <b>${totalPages}</b>)`}
              </div>
              <div class="dh-pagination-controls">
                <button type="button" class="dh-page-btn" id="dhPrevBtn" ${dhSelectAll || curPage <= 1 ? 'disabled' : ''}>
                  ◀ Previous
                </button>
                <span style="font-size:12.5px;font-weight:700;padding:0 6px">${curPage} / ${totalPages}</span>
                <button type="button" class="dh-page-btn" id="dhNextBtn" ${dhSelectAll || curPage >= totalPages ? 'disabled' : ''}>
                  Next ▶
                </button>
              </div>
            </div>

            ${(d.issues && d.issues.length) ? `
              <div class="tw"><table><thead><tr>
                <th>Issue Type</th><th>Identifier</th><th>Count</th><th>Description</th>
              </tr></thead><tbody>
              ${d.issues.map(iss => `<tr>
                <td><span class="tag bad">${esc(iss.type)}</span></td>
                <td><b>${esc(iss.identifier)}</b></td>
                <td>${Number(iss.count || 0).toLocaleString()}</td>
                <td>${esc(iss.description)}</td>
              </tr>`).join('')}
              </tbody></table></div>` : '<div class="empty" style="color:var(--ok)">✓ Outstanding! All device records pass integrity checks.</div>'}
          `;

          // Wire pagination and search handlers
          if ($('dhPrevBtn')) {
            $('dhPrevBtn').onclick = () => {
              if (dhPage > 1) { dhPage--; loadHealthContainer(); }
            };
          }
          if ($('dhNextBtn')) {
            $('dhNextBtn').onclick = () => {
              if (dhPage < totalPages) { dhPage++; loadHealthContainer(); }
            };
          }
          if ($('dhSelectAllBtn')) {
            $('dhSelectAllBtn').onclick = () => {
              dhSelectAll = !dhSelectAll;
              dhPage = 1;
              loadHealthContainer();
            };
          }
          if ($('dhSearchInput')) {
            $('dhSearchInput').oninput = e => {
              dhQ = e.target.value.trim();
              dhPage = 1;
              clearTimeout(dhDebounce);
              dhDebounce = setTimeout(loadHealthContainer, 250);
            };
          }
          if ($('dhClearSearchBtn')) {
            $('dhClearSearchBtn').onclick = () => {
              dhQ = '';
              dhPage = 1;
              loadHealthContainer();
            };
          }

          if ($('liveDownloadHealth')) {
            $('liveDownloadHealth').onclick = async () => {
              try {
                toast('Preparing full health audit export…');
                const allRes = await api('/api/inventory/health?select_all=true');
                const issues = (allRes && allRes.issues) ? allRes.issues : [];
                if (!issues.length) { toast('No health issues to export'); return; }
                const headers = ['Issue Type', 'Identifier', 'Count', 'Description'];
                const rows = issues.map(i => [i.type, i.identifier, i.count, i.description]);
                exportExcel('Data_Health_Audit_Report', headers, rows);
              } catch (err) { fail(err); }
            };
          }
        } catch (err) {
          hc.innerHTML = `<div class="empty err">${esc(err.message)}</div>`;
        }
      }

      // 15. Unified Home Overview Orchestrator
      async function loadHomeContainer() {
        await Promise.all([
          updateHomeUserGreeting().catch(e => console.log('Greeting notice:', e)),
          updateHomeExpiryBanner().catch(e => console.log('Expiry banner notice:', e)),
          updateHomeStatsRibbon().catch(e => console.log('Stats ribbon notice:', e)),
          populateLiveCustomerDropdown().catch(e => console.log('Customer dropdown notice:', e)),
          updateCartCountBadge().catch(e => console.log('Cart count notice:', e)),
          loadHealthContainer().catch(e => console.log('Health notice:', e)),
          runLiveCycle(true).catch(e => console.log('Live cycle notice:', e))
        ]);
      }
"""

feature_dialogs = loc['feature_dialogs']
home_top_elements = loc['home_top_elements']

# Re-order header: S logo first, Good morning after that, remove Edit Name & Password, remaining at end, Logout last
old_hdr_match = re.search(r'<header class="cv-top-header">[\s\S]*?</header>', home_top_elements)
if old_hdr_match:
    reordered_header = '''      <!-- App Header: Profile First (S Logo, Greeting & Role), Actions & Logout Last -->
      <header class="cv-top-header">
        <div class="cv-header-single-line" style="display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap">
          <!-- Left: User Profile (S Logo FIRST, followed by Good Morning Greeting & Role Badge) -->
          <div class="user-greeting-wrap" style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <div class="cv-avatar-circle" id="userAvatarCircle" title="User Settings &amp; Preferences" onclick="location.href='settings.html'" style="cursor:pointer;width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--primary,#1d68e1),var(--accent,#fca311));color:#fff;font-size:17px;font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px rgba(0,0,0,0.18)">S</div>
            <div class="user-badge" id="uBadge" style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;background:var(--card-subtle);border:1px solid var(--line);border-radius:99px;font-weight:700;font-size:13.5px">
              <span id="hi">Good morning, Shilish Reddy</span>
              <span class="role-pill admin" id="rolePill">ADMIN</span>
            </div>
          </div>

          <!-- Right: Remaining Items (Search, Refresh, Alerts, Cart) and Logout Last -->
          <div class="cv-header-actions acts" style="display:flex;align-items:center;gap:8px;margin-left:auto;flex-wrap:wrap">
            <button class="b" id="bQs" title="Quick Search (Ctrl + K)"><span>🔎 Search</span></button>
            <button class="b" id="bRefresh" title="Reload current data">🔄 Refresh</button>
            <button class="b on" id="bAl" title="Toggle Expiry Alerts">Alerts: ON</button>
            <button class="b" id="btnHeaderCart" title="View Cart / Recycle Bin" onclick="openCartModal()" style="font-weight:700">
              🛒 Cart (<span id="headerCartCountBadge">0</span>)
            </button>
            <button class="b b-logout" id="bLo" type="button" onclick="logout(true)" title="Sign out of your session" style="font-weight:700;padding:6px 14px;border-radius:8px">Logout</button>
          </div>
        </div>
      </header>'''
    home_top_elements = home_top_elements[:old_hdr_match.start()] + reordered_header + home_top_elements[old_hdr_match.end():]

# Remove hardcoded static numbers from home_top_elements
home_top_elements = home_top_elements.replace('>154<', '>—<').replace('>117,783<', '>—<').replace('>117,781<', '>—<').replace('>90<', '>—<')

auth_wrap_html = loc['auth_wrap_html']

print("Extracted master resources successfully!")

# 3. Lean Foundation Script
LEAN_FOUNDATION_JS = r"""
    // --- Foundation Configuration & Core Helpers ---
    const API_BASE = window.location.origin;
    let tok = localStorage.getItem('token') || '';
    let S = {}, CU = [], XC = [];
        let currentContainerId = '';
    let alertsOn = localStorage.getItem('alerts') === '1';
    let livePolling = true, liveTimer = null, liveIntervalSec = 10;
    let liveCid = '', liveQ = '', liveCol = 'all', livePage = 1, sortCol = 'id', sortDir = 'desc';
    let liveHealthData = null, liveReportList = null;
    let invPage = 1, invQ = '', invCol = 'all', invCid = '';

    const ALBL = {
      login: ['Signed In', 'ok'], login_failed: ['Failed Login', 'bad'], logout: ['Signed Out', 'mut'],
      register: ['Account Registered', 'warn'], password_change: ['Password Changed', 'mut'],
      device_add: ['Device Added', 'ok'], device_upload: ['Bulk Upload', 'ok'],
      device_edit: ['Device Edited', 'warn'], device_delete: ['Device Deleted', 'bad'],
      device_restore: ['Device Restored', 'ok'], device_purge: ['Purged Forever', 'bad'],
      bin_empty: ['Cart Emptied', 'bad'], user_create: ['User Created', 'ok'],
      user_update: ['User Updated', 'warn'], user_delete: ['User Deleted', 'bad'],
      customer_add: ['Customer Added', 'ok'], customer_rename: ['Customer Renamed', 'warn'],
      customer_rename_all: ['Customers Bulk Renamed', 'warn'], customer_merge: ['Customers Merged', 'warn'],
      customer_delete: ['Customer Deleted', 'bad'], customer_restore: ['Customer Restored', 'ok'],
      customer_purge: ['Customer Purged', 'bad'], simdata_apply: ['SIM Data Applied', 'ok'],
      column_delete: ['Column Deleted', 'bad'], export_excel: ['Excel Exported', 'ok']
    };

    const _safeElemStore = {};
    function _safeElem(id) {
      if (_safeElemStore[id]) return _safeElemStore[id];
      return (_safeElemStore[id] = {
        id: id,
        style: { setProperty() {}, removeProperty() {}, getPropertyValue() { return ''; } },
        classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
        dataset: {},
        children: [],
        childNodes: [],
        setAttribute() {},
        removeAttribute() {},
        getAttribute() { return null; },
        addEventListener() {},
        removeEventListener() {},
        querySelector() { return null; },
        querySelectorAll() { return []; },
        getElementsByTagName() { return []; },
        getElementsByClassName() { return []; },
        focus() {}, blur() {}, click() {}, showModal() {}, close() {},
        appendChild() {}, removeChild() {}, replaceChild() {}, insertAdjacentHTML() {},
        reset() {}, value: '', textContent: '', innerHTML: ''
      });
    }

    const $ = id => document.getElementById(id) || _safeElem(id);
    const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    const toast = m => {
      const t = $('toast');
      if (!t || !t.classList) return;
      t.textContent = m;
      t.classList.add('show');
      clearTimeout(toast.t);
      toast.t = setTimeout(() => t.classList.remove('show'), 2800);
    };
    const fail = e => toast(e instanceof TypeError ? 'Cannot reach server. Is backend running?' : e.message);

    const getUser = () => {
      try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch(e) { return {}; }
    };
    const getUserNormId = () => {
      const u = getUser();
      const raw = (u.user_id || '').trim().toLowerCase();
      return /^\d+$/.test(raw) ? raw.padStart(4, '0') : raw;
    };
    const isSuperAdminUser = () => {
      const u = getUser();
      const r = (u.role || '').toLowerCase();
      const uid = getUserNormId();
      return r === 'super_admin' || uid === '0001' || uid === 'bstpl001';
    };
    const isMasterAdminUser = () => {
      const u = getUser();
      const r = (u.role || '').toLowerCase();
      const uid = getUserNormId();
      return r === 'master_admin' || uid === '0002';
    };
    function applyTheme(pal, mode, save = true) {
      pal = pal || localStorage.getItem('valut_palette') || 'royal_navy';
      mode = mode || localStorage.getItem('valut_theme_mode') || 'light';
      document.documentElement.setAttribute('data-theme', mode);
      document.documentElement.setAttribute('data-mode', mode);
      document.documentElement.setAttribute('data-palette', pal);
      if (save) {
        try {
          localStorage.setItem('valut_palette', pal);
          localStorage.setItem('valut_theme_mode', mode);
        } catch(e) {}
      }
    }

    function initTheme() {
      const m = localStorage.getItem('valut_theme_mode') || 'light';
      const p = localStorage.getItem('valut_palette') || 'royal_navy';
      applyTheme(p, m, false);
    }

    let expDays = 30;

    const isRegularAdminUser = () => {
      const u = getUser(), norm = getUserNormId();
      return ['0005', '0006', '0008', '0009', '0010'].includes(norm) || u.category === 'admin_user';
    };

    const canDeleteValidInventory = () => {
      if (isSuperAdminUser()) return true;
      if (isMasterAdminUser()) return false;
      const u = getUser();
      if (u.permissions && u.permissions.delete !== undefined) return Boolean(u.permissions.delete);
      if (isRegularAdminUser()) return true;
      return true;
    };

    const canDeleteInvalidEntries = () => {
      if (isSuperAdminUser() || isMasterAdminUser() || isRegularAdminUser()) return true;
      const u = getUser();
      if (u.permissions && u.permissions.delete_invalid !== undefined) return Boolean(u.permissions.delete_invalid);
      return true;
    };

    const canAccessLoginInventory = () => {
      return isSuperAdminUser() || isMasterAdminUser();
    };

    const canAccessUsersManager = () => {
      return isSuperAdminUser() || isMasterAdminUser();
    };

    window.expDays = expDays;
    window.isRegularAdminUser = isRegularAdminUser;
    window.canDeleteValidInventory = canDeleteValidInventory;
    window.canDeleteInvalidEntries = canDeleteInvalidEntries;
    window.canAccessLoginInventory = canAccessLoginInventory;
    window.canAccessUsersManager = canAccessUsersManager;

    async function api(path, opt = {}) {
      const r = await fetch(API_BASE + path, {
        ...opt,
        headers: {
          Authorization: 'Bearer ' + tok,
          ...(opt.body && !(opt.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
          ...(opt.headers || {})
        }
      });
      if (r.status === 401) {
        localStorage.removeItem('token');
        if (!window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('index.html')) {
          window.location.href = 'index.html';
        }
        throw new Error('Session expired. Please sign in.');
      }
      if (!r.ok) {
        const text = await r.text();
        let msg = text;
        try {
          const j = JSON.parse(text);
          msg = j.detail || j.message || text;
        } catch(e) {}
        throw new Error(msg || ('Request failed (' + r.status + ')'));
      }
      const _resData = await r.json();
      const _reqMethod = (opt.method || 'GET').toUpperCase();
      if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(_reqMethod)) {
        if (!path.includes('/auth/') && !path.includes('/logs') && !path.includes('/audit')) {
          if (typeof notifyDataUpdated === 'function') {
            notifyDataUpdated({ path, method: _reqMethod });
          }
        }
      }
      return _resData;
    }

    const COLS = [
      ['customer_name', 'Customer Name'],
      ['device_sr_no', 'Device SR No'],
      ['imei', 'IMEI'],
      ['iccid', 'ICCID / CCID'],
      ['msisdn1', 'MSISDN1'],
      ['msisdn2', 'MSISDN2'],
      ['act_date', 'Act Date'],
      ['expiry_date', 'Expiry Date'],
      ['dispatched_date', 'Dispatched'],
      ['model', 'Model'],
      ['sim_provider', 'SIM Provider'],
      ['activation_plan', 'Activation Plan'],
      ['firmware', 'Firmware'],
      ['flash', 'Flash'],
      ['sim_type', 'SIM Type']
    ];

    const expTag = d => {
      if (d.days_left == null) return '';
      if (d.days_left < 0) return `<span class="tag bad">Expired ${-d.days_left}d ago</span>`;
      if (d.days_left <= 30) return `<span class="tag warn">${d.days_left}d left</span>`;
      return `<span class="tag ok">${d.days_left}d left</span>`;
    };

    const cell = (d, k) => {
      const val = d[k];
      if (k === 'expiry_date') {
        return val ? `${esc(val)} ${expTag(d)}` : '<span style="color:var(--muted)">—</span>';
      }
      if (k === 'customer_name') {
        return val ? `<b style="color:var(--text)">${esc(val)}</b>` : '<span style="color:var(--muted)">—</span>';
      }
      if (k === 'imei') {
        return val ? `<code><b>${esc(val)}</b></code>` : '<span style="color:var(--muted)">—</span>';
      }
      if (k === 'iccid') {
        return val ? `<code>${esc(val)}</code>` : '<span style="color:var(--muted)">—</span>';
      }
      if (k === 'sim_type') {
        if (!val) return '<span style="color:var(--muted)">—</span>';
        if (val === 'E-SIM') return `<span class="tag" style="background:#38bdf8;color:#000;font-weight:700">E-SIM</span>`;
        if (val === 'Plastic SIM') return `<span class="tag" style="background:#fbbf24;color:#000;font-weight:700">Plastic SIM</span>`;
        return esc(val);
      }
      return val ? esc(val) : '<span style="color:var(--muted)">—</span>';
    };

    function renderTable(list, act, extraCols = [], isSortable = true) {
      if (!list.length) return '<div class="empty">No records found matching current criteria.</div>';
      const ex = extraCols;
      return `<div class="tw"><table><thead><tr>
        <th>#</th>
        ${COLS.map(c => `<th>${c[1]}</th>`).join('')}
        ${XC.map(c => `<th>${esc(c)}</th>`).join('')}
        ${ex.map(c => `<th>${c[1]}</th>`).join('')}
        ${act ? '<th>Actions</th>' : ''}
      </tr></thead><tbody>
      ${list.map(d => `<tr>
        <td><b>${d.id}</b></td>
        ${COLS.map(c => `<td>${cell(d, c[0])}</td>`).join('')}
        ${XC.map(c => `<td>${esc((d.extra || {})[c])}</td>`).join('')}
        ${ex.map(c => `<td>${esc(d[c[0]] || '')}</td>`).join('')}
        ${act ? `<td>${act(d)}</td>` : ''}
      </tr>`).join('')}
      </tbody></table></div>`;
    }

    function exportExcel(title, headers, rows) {
      try {
        toast('Generating Excel file…');
        if (typeof XLSX !== 'undefined') {
          const data = [headers, ...(rows || [])];
          const ws = XLSX.utils.aoa_to_sheet(data);
          const wb = XLSX.utils.book_new();
          XLSX.utils.book_append_sheet(wb, ws, 'Data');
          const safeTitle = (title || 'Export').replace(/[^a-zA-Z0-9_-]/g, '_');
          const fileName = `${safeTitle}_${new Date().toISOString().slice(0, 10)}.xlsx`;
          XLSX.writeFile(wb, fileName);
          toast('Excel downloaded successfully');
        } else {
          const csv = [headers.join(','), ...(rows || []).map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(','))].join('\n');
          const blob = new Blob([csv], { type: 'text/csv' });
          const a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          a.download = `${title || 'export'}.csv`;
          a.click();
          toast('CSV downloaded');
        }
      } catch(e) {
        toast('Export failed: ' + e.message);
      }
    }

    // Modal helpers
    function openDlg(title, bodyHtml, confirmLabel, onConfirm, isDanger = false) {
      $('cdt').textContent = title;
      $('cdb').innerHTML = bodyHtml;
      $('cde').textContent = '';
      $('cdok').textContent = confirmLabel || 'Confirm';
      $('cdok').className = isDanger ? 'b d' : 'b p';
      $('cdok').onclick = async e => {
        e.preventDefault();
        try {
          $('cde').textContent = '';
          await onConfirm();
          $('cdlg').close();
        } catch(err) { $('cde').textContent = err.message; }
      };
      $('cdx').onclick = () => $('cdlg').close();
      $('cdlg').showModal();
    }

    function buildDeviceFormFields(dev = {}) {
      const extra = dev.extra || {};
      return `
        <div class="form-grid">
          <div><label>Customer Name *</label><input data-devf="customer_name" value="${esc(dev.customer_name || '')}" placeholder="Customer name" required /></div>
          <div><label>Device SR No</label><input data-devf="device_sr_no" value="${esc(dev.device_sr_no || '')}" /></div>
          <div><label>IMEI *</label><input data-devf="imei" value="${esc(dev.imei || '')}" required /></div>
          <div><label>ICCID</label><input data-devf="iccid" value="${esc(dev.iccid || '')}" /></div>
          <div><label>MSISDN 1</label><input data-devf="msisdn1" value="${esc(dev.msisdn1 || '')}" /></div>
          <div><label>MSISDN 2</label><input data-devf="msisdn2" value="${esc(dev.msisdn2 || '')}" /></div>
          <div><label>Act Date</label><input type="date" data-devf="act_date" value="${esc(dev.act_date || '')}" /></div>
          <div><label>Expiry Date</label><input type="date" data-devf="expiry_date" value="${esc(dev.expiry_date || '')}" /></div>
          <div><label>Dispatched Date</label><input type="date" data-devf="dispatched_date" value="${esc(dev.dispatched_date || '')}" /></div>
          <div><label>Model</label><input data-devf="model" value="${esc(dev.model || '')}" /></div>
          <div><label>SIM Provider</label><input data-devf="sim_provider" value="${esc(dev.sim_provider || '')}" /></div>
          <div><label>Activation Plan</label><input data-devf="activation_plan" value="${esc(dev.activation_plan || '')}" /></div>
          <div><label>Firmware</label><input data-devf="firmware" value="${esc(dev.firmware || '')}" /></div>
          <div><label>Flash</label><input data-devf="flash" value="${esc(dev.flash || '')}" /></div>
          <div><label>SIM Type</label><select data-devf="sim_type"><option value="">Select type</option><option value="E-SIM" ${dev.sim_type==='E-SIM'?'selected':''}>E-SIM</option><option value="Plastic SIM" ${dev.sim_type==='Plastic SIM'?'selected':''}>Plastic SIM</option></select></div>
        </div>
      `;
    }

    async function openEditDeviceModal(id) {
      try {
        toast('Loading record…');
        const dev = await api('/api/devices/' + id);
        $('devTitle').textContent = `Edit Device #${dev.id} (IMEI ${dev.imei})`;
        $('devFields').innerHTML = buildDeviceFormFields(dev);
        $('devErr').textContent = '';
        $('devSave').textContent = 'Save Changes';
        $('devform').onsubmit = async e => {
          e.preventDefault();
          $('devErr').textContent = '';
          const body = {};
          document.querySelectorAll('#devdlg [data-devf]').forEach(i => {
            const k = i.dataset.devf, v = i.value.trim();
            body[k] = v || null;
          });
          try {
            await api('/api/devices/' + dev.id, { method: 'PUT', body: JSON.stringify(body) });
            $('devdlg').close();
            toast('Device record updated');
            if (typeof refreshActiveContainer === 'function') refreshActiveContainer();
            else if (typeof loadInventoryContainer === 'function') loadInventoryContainer();
          } catch(err) { $('devErr').textContent = err.message; }
        };
        $('devdlg').showModal();
      } catch(err) { fail(err); }
    }
    const devCancelBtn = $('devCancel');
    if (devCancelBtn) devCancelBtn.onclick = () => $('devdlg').close();

    
    
    function openExportColumnsModal() {
      const dlg = $('dlgChooseExportCols');
      if (!dlg) return;

      const allAvailableCols = [
        { key: 'customer_name', label: 'Customer Name' },
        ...COLS.map(c => ({ key: c[0], label: c[1] })),
        ...(XC || []).map(c => ({ key: c, label: c })),
        { key: 'added_by', label: 'Added By' },
        { key: 'created_at', label: 'Added On' }
      ];

      const listEl = $('exportColsList');
      if (listEl) {
        listEl.innerHTML = allAvailableCols.map(c => `
          <label class="col-pill-chip active" style="display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border:1.5px solid var(--primary);background:var(--card);border-radius:20px;cursor:pointer;font-size:12px;font-weight:600;transition:all .15s">
            <input type="checkbox" class="exp-modal-chk" value="${c.key}" checked style="width:14px;height:14px;margin:0;accent-color:var(--primary)" />
            <span>${esc(c.label)}</span>
          </label>
        `).join('');

        const updateCountText = () => {
          const checkedCount = document.querySelectorAll('.exp-modal-chk:checked').length;
          if ($('exportColsCountText')) $('exportColsCountText').textContent = `${checkedCount} of ${allAvailableCols.length} columns selected`;
          if ($('btnConfirmExportExcel')) $('btnConfirmExportExcel').disabled = (checkedCount === 0);
        };

        document.querySelectorAll('.exp-modal-chk').forEach(chk => {
          chk.onchange = e => {
            const chip = e.target.closest('.col-pill-chip');
            if (chip) {
              chip.classList.toggle('active', e.target.checked);
              chip.style.borderColor = e.target.checked ? 'var(--primary)' : 'var(--line)';
              chip.style.background = e.target.checked ? 'var(--card-subtle)' : 'var(--card)';
            }
            updateCountText();
          };
        });

        if ($('btnExpPresetAll')) {
          $('btnExpPresetAll').onclick = () => {
            document.querySelectorAll('.exp-modal-chk').forEach(c => {
              c.checked = true;
              const chip = c.closest('.col-pill-chip');
              if (chip) { chip.classList.add('active'); chip.style.borderColor = 'var(--primary)'; chip.style.background = 'var(--card-subtle)'; }
            });
            updateCountText();
          };
        }

        if ($('btnExpPresetClear')) {
          $('btnExpPresetClear').onclick = () => {
            document.querySelectorAll('.exp-modal-chk').forEach(c => {
              c.checked = false;
              const chip = c.closest('.col-pill-chip');
              if (chip) { chip.classList.remove('active'); chip.style.borderColor = 'var(--line)'; chip.style.background = 'var(--card)'; }
            });
            updateCountText();
          };
        }

        if ($('btnExpPresetSim')) {
          $('btnExpPresetSim').onclick = () => {
            const simKeys = new Set(['customer_name', 'imei', 'iccid', 'msisdn1', 'msisdn2', 'act_date', 'expiry_date', 'sim_provider', 'sim_type']);
            document.querySelectorAll('.exp-modal-chk').forEach(c => {
              c.checked = simKeys.has(c.value);
              const chip = c.closest('.col-pill-chip');
              if (chip) {
                chip.classList.toggle('active', c.checked);
                chip.style.borderColor = c.checked ? 'var(--primary)' : 'var(--line)';
                chip.style.background = c.checked ? 'var(--card-subtle)' : 'var(--card)';
              }
            });
            updateCountText();
          };
        }

        if ($('btnExpPresetId')) {
          $('btnExpPresetId').onclick = () => {
            const idKeys = new Set(['customer_name', 'imei', 'device_sr_no', 'iccid', 'model']);
            document.querySelectorAll('.exp-modal-chk').forEach(c => {
              c.checked = idKeys.has(c.value);
              const chip = c.closest('.col-pill-chip');
              if (chip) {
                chip.classList.toggle('active', c.checked);
                chip.style.borderColor = c.checked ? 'var(--primary)' : 'var(--line)';
                chip.style.background = c.checked ? 'var(--card-subtle)' : 'var(--card)';
              }
            });
            updateCountText();
          };
        }

        updateCountText();
      }

      if ($('closeDlgChooseExportCols')) $('closeDlgChooseExportCols').onclick = () => dlg.close();
      if ($('cancelDlgChooseExportCols')) $('cancelDlgChooseExportCols').onclick = () => dlg.close();

      if ($('btnConfirmExportExcel')) {
        $('btnConfirmExportExcel').onclick = async () => {
          const checked = Array.from(document.querySelectorAll('.exp-modal-chk:checked')).map(c => c.value);
          if (!checked.length) {
            toast('Please select at least one column.');
            return;
          }
          dlg.close();

          try {
            toast('Exporting customer inventory…');
            const targetQ = typeof invQ !== 'undefined' ? invQ : '';
            const targetCol = typeof invCol !== 'undefined' ? invCol : 'all';
            const targetCid = typeof invCid !== 'undefined' ? invCid : '';
            const d = await api(`/api/devices?page=1&page_size=5000&q=${encodeURIComponent(targetQ)}&column=${targetCol}&sort_by=${sortCol}&sort_dir=${sortDir}${targetCid ? '&customer_id=' + targetCid : ''}`);
            const colMap = {};
            allAvailableCols.forEach(c => { colMap[c.key] = c.label; });

            const headers = ['ID', ...checked.map(k => colMap[k] || k)];
            const rows = (d.items || []).map(dev => [
              dev.id,
              ...checked.map(k => {
                if (k === 'customer_name') return dev.customer_name || '';
                if (dev.extra && dev.extra[k] !== undefined) return dev.extra[k] || '';
                return dev[k] != null ? dev[k] : '';
              })
            ]);
            await exportExcel('Customer_Inventory_Export', headers, rows);
          } catch(err) {
            fail(err);
          }
        };
      }

      if (typeof dlg.showModal === 'function') dlg.showModal();
    }

    
    
    const myRole = () => {
      const u = getUser();
      return u.role || (u.is_admin ? 'admin' : 'standard');
    };

    
    function avatarHtml(c) {
      const a = (c && c.avatar) || '';
      return a.startsWith('data:image/') ? `<img class="av" alt="" src="${esc(a)}">` : `<span class="av">${esc(a || '🏢')}</span>`;
    }

    function alertSummary(list) {
      if (!Array.isArray(list)) return '';
      const t = new Date(); t.setHours(0, 0, 0, 0);
      let x = 0, w = 0, m = 0;
      list.forEach(d => {
        if (!d.expiry_date) return;
        const n = Math.round((new Date(d.expiry_date) - t) / 864e5);
        if (n < 0) x++; else if (n <= 7) w++; else m++;
      });
      return `🔴 ${x} expired · 🟠 ${w} within 7 days · 🟡 ${m} within 30 days`;
    }

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

    
    // --- Branded 3D Loader & Notification System (Logo + Message on Search/Load) ---
    function showBstplLoader(msg = 'Searching & loading records…', pct = null) {
      let loader = $('cvGlobalLoader');
      if (!loader) {
        loader = document.createElement('div');
        loader.id = 'cvGlobalLoader';
        loader.className = 'cv-global-loader';
        loader.innerHTML = `
          <div class="cv-loader-backdrop"></div>
          <div class="cv-loader-card">
            <div class="cv-loader-logo-wrap">
              <div class="cv-loader-logo-3d">B</div>
            </div>
            <div class="cv-loader-brand-title">BSTPL <span>CustomerVault</span></div>
            <div class="cv-loader-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>
            <div class="cv-loader-msg" id="cvLoaderMsg">${esc(msg)}</div>
            <div class="cv-loader-progress"><div class="cv-loader-progress-bar"></div></div>
          </div>
        `;
        document.body.appendChild(loader);
      }
      const msgEl = $('cvLoaderMsg');
      if (msgEl && msg != null) msgEl.textContent = msg;
      const bar = loader.querySelector('.cv-loader-progress-bar');
      if (bar && pct != null) {
        bar.style.width = Math.max(0, Math.min(100, pct)) + '%';
      }
      loader.style.display = 'flex';
    }

    function updateBstplLoader(msg = null, pct = null) {
      let loader = $('cvGlobalLoader');
      if (!loader) {
        showBstplLoader(msg || 'Processing…', pct);
        return;
      }
      if (msg != null) {
        const msgEl = $('cvLoaderMsg');
        if (msgEl) msgEl.textContent = msg;
      }
      if (pct != null) {
        const bar = loader.querySelector('.cv-loader-progress-bar');
        if (bar) bar.style.width = Math.max(0, Math.min(100, pct)) + '%';
      }
    }

    function hideBstplLoader() {
      const loader = $('cvGlobalLoader');
      if (loader) loader.style.display = 'none';
    }

    // Compatibility aliases for BSTPI / BSTPL loader calls (Requirement 3)
    window.showBstplLoader = showBstplLoader;
    window.updateBstplLoader = updateBstplLoader;
    window.hideBstplLoader = hideBstplLoader;
    window.showBSTPILoader = showBstplLoader;
    window.updateBSTPILoader = updateBstplLoader;
    window.hideBSTPILoader = hideBstplLoader;

    // Minimal 3D Page Transitions while navigating between files (e.g. errors.html -> inventory.html)
    document.addEventListener('DOMContentLoaded', () => {
      document.querySelectorAll('a.cv-nav-item, .cv-header-actions a, a.nav-link, aside a').forEach(link => {
        link.addEventListener('click', e => {
          const href = link.getAttribute('href');
          if (href && !href.startsWith('#') && !href.startsWith('javascript:') && !link.target) {
            const currentFile = window.location.pathname.split('/').pop() || 'home.html';
            if (href !== currentFile) {
              e.preventDefault();
              document.body.classList.add('cv-page-3d-exit');
              const linkText = link.textContent.replace(/[^\w\s]/gi, '').trim();
              showBstplLoader(`Opening ${linkText || 'CustomerVault'}…`);
              setTimeout(() => { window.location.href = href; }, 160);
            }
          }
        });
      });
    });


    function openBulkEditImeiModal() {
      const dlg = $('dlgBulkEditImei');
      if (dlg && typeof dlg.showModal === 'function') {
        dlg.showModal();
      } else {
        window.location.href = 'edit-delete.html?mode=bulk-edit';
      }
    }

    function openBulkDeleteExcelModal() {
      const dlg = $('dlgBulkDeleteExcel');
      if (dlg && typeof dlg.showModal === 'function') {
        dlg.showModal();
      } else {
        window.location.href = 'edit-delete.html?mode=bulk-delete';
      }
    }

    function openAddColumnModal() {
      const dlg = $('dlgAddColumn');
      if (!dlg) return;
      if ($('newColName')) $('newColName').value = '';
      if ($('newColValue')) $('newColValue').value = '';
      if ($('newColImeis')) $('newColImeis').value = '';
      if ($('newColErr')) { $('newColErr').textContent = ''; $('newColErr').style.display = 'none'; }
      if ($('newColTarget')) $('newColTarget').value = 'all';
      if ($('newColCustWrap')) $('newColCustWrap').style.display = 'none';
      if ($('newColImeisWrap')) $('newColImeisWrap').style.display = 'none';

      // Populate customer options
      if ($('newColCustSel')) {
        let custOpts = '<option value="">-- Choose Customer --</option>';
        custOpts += (CU || []).map(c => `<option value="${c.id}">${esc(c.name || c.customer_name)}</option>`).join('');
        $('newColCustSel').innerHTML = custOpts;
        if (typeof invCid !== 'undefined' && invCid) $('newColCustSel').value = invCid;
      }

      if ($('newColTarget')) {
        $('newColTarget').onchange = () => {
          const t = $('newColTarget').value;
          if ($('newColCustWrap')) $('newColCustWrap').style.display = (t === 'customer') ? 'block' : 'none';
          if ($('newColImeisWrap')) $('newColImeisWrap').style.display = (t === 'specified') ? 'block' : 'none';
        };
      }

      if ($('closeDlgAddColumn')) $('closeDlgAddColumn').onclick = () => dlg.close();
      if ($('cancelDlgAddColumn')) $('cancelDlgAddColumn').onclick = () => dlg.close();

      if ($('formAddColumn')) {
        $('formAddColumn').onsubmit = async e => {
          e.preventDefault();
          if ($('newColErr')) { $('newColErr').textContent = ''; $('newColErr').style.display = 'none'; }
          const colName = ($('newColName')?.value || '').trim();
          if (!colName) {
            if ($('newColErr')) { $('newColErr').textContent = 'Please enter a column name.'; $('newColErr').style.display = 'block'; }
            return;
          }

          const target = $('newColTarget')?.value || 'all';
          let customerId = null;
          let imeis = null;

          if (target === 'customer') {
            const cid = parseInt($('newColCustSel')?.value);
            if (!cid) {
              if ($('newColErr')) { $('newColErr').textContent = 'Please select a customer.'; $('newColErr').style.display = 'block'; }
              return;
            }
            customerId = cid;
          } else if (target === 'specified') {
            const raw = ($('newColImeis')?.value || '').split(/[\r\n,]+/).map(s => s.trim()).filter(Boolean);
            if (!raw.length) {
              if ($('newColErr')) { $('newColErr').textContent = 'Please enter at least one IMEI.'; $('newColErr').style.display = 'block'; }
              return;
            }
            imeis = raw;
            if (typeof invCid !== 'undefined' && invCid) customerId = parseInt(invCid);
          } else if (target === 'all' && typeof invCid !== 'undefined' && invCid) {
            customerId = parseInt(invCid);
          }

          const val = $('newColValue')?.value || '';
          const btn = $('btnSubmitAddColumn');
          if (btn) { btn.disabled = true; btn.textContent = 'Adding Column…'; }

          try {
            const res = await api('/api/columns/add', {
              method: 'POST',
              body: JSON.stringify({
                column_name: colName,
                target: target,
                customer_id: customerId,
                imeis: imeis,
                value: val !== '' ? val : null
              })
            });
            dlg.close();
            toast(`Column "${res.column || colName}" added successfully`);
            if (typeof fetchInventoryRows === 'function') await fetchInventoryRows();
          } catch(err) {
            if ($('newColErr')) { $('newColErr').textContent = err.message || 'Failed to add column'; $('newColErr').style.display = 'block'; }
          } finally {
            if (btn) { btn.disabled = false; btn.textContent = '➕ Add Column'; }
          }
        };
      }

      if (typeof dlg.showModal === 'function') dlg.showModal();
    }

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


    // Live sidebar telemetry
    function updateLiveStreamClock() {
      const el = $('sbLiveTime');
      if (!el) return;
      const now = new Date();
      el.textContent = 'Live • ' + now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    if (typeof setInterval === 'function') setInterval(updateLiveStreamClock, 1000);
    updateLiveStreamClock();


    // --- Universal Inter-Page Interlinking & Data Synchronization System ---
    let lastKnownDbUpdate = parseInt(localStorage.getItem('customervault_db_updated') || '0', 10);

    function notifyDataUpdated(detail = {}) {
      const now = Date.now();
      lastKnownDbUpdate = now;
      try {
        localStorage.setItem('customervault_db_updated', String(now));
        if (window.BroadcastChannel) {
          const bc = new BroadcastChannel('customervault_sync_channel');
          bc.postMessage({ type: 'DB_UPDATED', timestamp: now, detail });
          bc.close();
        }
      } catch (e) {}
    }
    window.notifyDataUpdated = notifyDataUpdated;

    async function syncGlobalMetricsAndChrome() {
      try {
        const [statsRes, custsRes] = await Promise.all([
          api('/api/stats').catch(() => null),
          api('/api/customers').catch(() => null)
        ]);

        if (statsRes) {
          S = statsRes;
          const devTotal = statsRes.total_devices != null ? statsRes.total_devices : (statsRes.devices || 0);
          const custTotal = statsRes.total_customers != null ? statsRes.total_customers : (statsRes.customers || 0);
          const errTotal = statsRes.errored_records != null ? statsRes.errored_records : 0;
          const cartTotal = statsRes.deleted_devices != null ? statsRes.deleted_devices : (statsRes.deleted || 0);
          const exp30Total = statsRes.expiring_30_days != null ? statsRes.expiring_30_days : (statsRes.total_expiring || 0);
          const expiredTotal = statsRes.expired != null ? statsRes.expired : (statsRes.total_expired || 0);

          // Update sidebar badges and widgets
          if ($('sbLiveDevCount')) $('sbLiveDevCount').textContent = Number(devTotal).toLocaleString();
          if ($('sbLiveCustCount')) $('sbLiveCustCount').textContent = Number(custTotal).toLocaleString();
          if ($('sidebarErrorsBadge')) {
            $('sidebarErrorsBadge').textContent = Number(errTotal).toLocaleString();
            $('sidebarErrorsBadge').style.display = errTotal > 0 ? 'inline-block' : 'none';
          }
          if ($('invCustCountBadge')) $('invCustCountBadge').textContent = Number(custTotal).toLocaleString();
          if ($('topCartCountBadge')) $('topCartCountBadge').textContent = cartTotal;
          if ($('cartCountText')) $('cartCountText').textContent = cartTotal;
          if ($('simRestoreCountBadge')) $('simRestoreCountBadge').textContent = `${Number(cartTotal).toLocaleString()} records`;

          // Update Home Overview & Live Stream KPI cards if present
          if ($('kpiDev')) $('kpiDev').textContent = Number(devTotal).toLocaleString();
          if ($('kpiCust')) $('kpiCust').textContent = Number(custTotal).toLocaleString();
          if ($('kpiExp30')) $('kpiExp30').textContent = Number(exp30Total).toLocaleString();
          if ($('kpiExpired')) $('kpiExpired').textContent = Number(expiredTotal).toLocaleString();
        }

        if (custsRes && Array.isArray(custsRes)) {
          CU = custsRes;
          if ($('invCustCountBadge')) $('invCustCountBadge').textContent = CU.length.toLocaleString();
          if (typeof populateNfCustomerDropdown === 'function') populateNfCustomerDropdown();
          if (typeof populateBfCustomerFilter === 'function') populateBfCustomerFilter();
          if (typeof populateLiveCustomerDropdown === 'function') populateLiveCustomerDropdown();
          if (typeof refreshUploadCustDropdown === 'function') refreshUploadCustDropdown();
        }
      } catch(e) {
        console.warn('Sync metrics error:', e);
      }
    }
    window.syncGlobalMetricsAndChrome = syncGlobalMetricsAndChrome;

    let _refreshDebounceTimer = null;
    function triggerLivePageRefresh() {
      clearTimeout(_refreshDebounceTimer);
      _refreshDebounceTimer = setTimeout(async () => {
        await syncGlobalMetricsAndChrome();

        // Dynamically re-fetch container data on active page
        const path = window.location.pathname.toLowerCase();
        if (path.endsWith('home.html') || path.endsWith('dashboard.html') || path.endsWith('index.html')) {
          if (typeof updateHomeStatsRibbon === 'function') updateHomeStatsRibbon();
          if (typeof updateHomeExpiryBanner === 'function') updateHomeExpiryBanner();
          if (typeof runLiveCycle === 'function') runLiveCycle(true);
          if (typeof loadHealthContainer === 'function') loadHealthContainer();
        } else if (path.endsWith('inventory.html')) {
          if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
          if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
        } else if (path.endsWith('sim-upload.html')) {
          if (typeof refreshUploadCustDropdown === 'function') refreshUploadCustDropdown();
          if (typeof updateSimRestoreCount === 'function') updateSimRestoreCount();
        } else if (path.endsWith('fetch-data.html')) {
          if (typeof populateNfCustomerDropdown === 'function') populateNfCustomerDropdown();
          if (typeof populateBfCustomerFilter === 'function') populateBfCustomerFilter();
          if (typeof runNormalFetch === 'function' && $('fq') && $('fq').value.trim()) runNormalFetch();
        } else if (path.endsWith('edit-delete.html')) {
          if (typeof runSearch === 'function' && $('qImei') && $('qImei').value.trim()) runSearch();
        } else if (path.endsWith('alerts.html')) {
          if (typeof loadExpiryContainer === 'function') loadExpiryContainer();
        } else if (path.endsWith('errors.html')) {
          if (typeof loadErrorsContainer === 'function') loadErrorsContainer();
        } else if (path.endsWith('settings.html')) {
          if (typeof loadSettingsPage === 'function') loadSettingsPage();
        }
      }, 200);
    }
    window.triggerLivePageRefresh = triggerLivePageRefresh;

    // Cross-tab broadcast listener
    if (window.BroadcastChannel) {
      try {
        const syncBc = new BroadcastChannel('customervault_sync_channel');
        syncBc.onmessage = e => {
          if (e.data && e.data.type === 'DB_UPDATED') {
            lastKnownDbUpdate = e.data.timestamp;
            triggerLivePageRefresh();
          }
        };
      } catch (e) {}
    }

    // Storage event listener (cross-window fallback)
    window.addEventListener('storage', e => {
      if (e.key === 'customervault_db_updated') {
        const ts = parseInt(e.newValue || '0', 10);
        if (ts > lastKnownDbUpdate) {
          lastKnownDbUpdate = ts;
          triggerLivePageRefresh();
        }
      }
    });

    // Window focus listener: When user switches back to this tab/window, refresh immediately
    window.addEventListener('focus', () => {
      const cur = parseInt(localStorage.getItem('customervault_db_updated') || '0', 10);
      if (cur > lastKnownDbUpdate) {
        lastKnownDbUpdate = cur;
        triggerLivePageRefresh();
      } else {
        syncGlobalMetricsAndChrome();
      }
    });

    syncGlobalMetricsAndChrome();

    const toggleLiveBtn = $('sidebarToggleLiveBtn');
    if (toggleLiveBtn) {
      toggleLiveBtn.onclick = function() {
        if (this.classList.contains('on')) {
          this.classList.remove('on');
          this.classList.add('off');
          this.textContent = 'OFF';
          toast('Live stream paused');
        } else {
          this.classList.remove('off');
          this.classList.add('on');
          this.textContent = 'ON';
          toast('Live stream active');
          updateSidebarStats();
        }
      };
    }

    // Sub-view switcher for Inventory and Upload
    let currentInvSubView = 'devices';
    function switchInvSubView(view) {
      currentInvSubView = view;
      document.querySelectorAll('.inv-sub-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.sub === view);
      });
      const vDev = $('subViewDevices'), vCust = $('subViewCust'), vUpl = $('subViewUpload');
      if (vDev) vDev.hidden = (view !== 'devices');
      if (vCust) vCust.hidden = (view !== 'cust');
      if (vUpl) vUpl.hidden = (view !== 'upload');

      if (view === 'devices') {
        if (typeof fetchInventoryRows === 'function') fetchInventoryRows();
      } else if (view === 'cust') {
        if (typeof loadCustomerFilesContainer === 'function') loadCustomerFilesContainer();
      } else if (view === 'upload') {
        if (typeof initBulkUploadContainer === 'function') initBulkUploadContainer();
      }
    }
"""

def generate_sidebar(active_key):
    keys = ['HOME', 'INV', 'SIM', 'FETCH', 'EDIT', 'ALERTS', 'ERRORS', 'SETTINGS']
    nav_cls = {k: ('on' if k == active_key else '') for k in keys}
    return f"""
    <aside class="cv-sidebar" id="cvSidebar">
      <div class="cv-sidebar-brand">
        <div class="cv-brand-icon">B</div>
        <div class="cv-brand-text">
          <div class="cv-brand-title">BSTPL CustomerVault</div>
          <div class="cv-brand-sub">DEVICE &amp; INVENTORY SYSTEMS</div>
        </div>
      </div>

      <nav class="cv-sidebar-menu">
        <a class="cv-nav-item {nav_cls['HOME']}" href="home.html" title="Home Overview &amp; Live Updates" style="text-decoration:none">
          <span class="cv-nav-ico">🏠</span>
          <span class="cv-nav-label">Home Overview</span>
        </a>
        <a class="cv-nav-item {nav_cls['INV']}" href="inventory.html" title="Customer Inventory" style="text-decoration:none">
          <span class="cv-nav-ico">📇</span>
          <span class="cv-nav-label">Customer Inventory</span>
        </a>
        <a class="cv-nav-item {nav_cls['SIM']}" href="sim-upload.html" title="SIM Data Upload" style="text-decoration:none">
          <span class="cv-nav-ico">📱</span>
          <span class="cv-nav-label">SIM Data Upload</span>
        </a>
        <a class="cv-nav-item {nav_cls['FETCH']}" href="fetch-data.html" title="Fetch Data" style="text-decoration:none">
          <span class="cv-nav-ico">🔍</span>
          <span class="cv-nav-label">Fetch Data</span>
        </a>
        <a class="cv-nav-item {nav_cls['EDIT']}" href="edit-delete.html" title="Edit / Delete by IMEI" style="text-decoration:none">
          <span class="cv-nav-ico">✏️</span>
          <span class="cv-nav-label">Edit / Delete by IMEI</span>
        </a>
        <a class="cv-nav-item {nav_cls['ALERTS']}" href="alerts.html" id="sidebarBtnAlerts" title="SIM Expiry Alerts" style="text-decoration:none">
          <div style="display:flex;align-items:center;gap:12px">
            <span class="cv-nav-ico">⚠️</span>
            <span class="cv-nav-label">Expiry Alerts</span>
          </div>
          <span class="cv-live-badge" style="margin-left:auto;background:rgba(245,158,11,0.2);color:#f59e0b;border:1px solid rgba(245,158,11,0.4)">ALERTS</span>
        </a>
        <a class="cv-nav-item {nav_cls['ERRORS']}" href="errors.html" id="sidebarBtnErrors" title="Errored Entries &amp; Corrections" style="text-decoration:none">
          <span class="cv-nav-ico">🚨</span>
          <span class="cv-nav-label">Errored Entries</span>
          <span class="badge danger" id="sidebarErrorsBadge" style="margin-left:auto;background:#ef4444;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;font-weight:800;display:none">0</span>
        </a>
        <a class="cv-nav-item {nav_cls['SETTINGS']}" href="settings.html" id="sidebarBtnSettings" title="User Settings &amp; Preferences" style="text-decoration:none">
          <span class="cv-nav-ico">⚙️</span>
          <span class="cv-nav-label">Settings</span>
        </a>
      </nav>

      <!-- Live Telemetry Widget in Left Sidebar -->
      <div class="cv-sidebar-live-widget" id="sidebarLiveWidget">
        <div class="cv-sb-live-top">
          <div style="display:flex;align-items:center;gap:6px">
            <span class="cv-live-dot-pulse"></span>
            <span style="font-size:11px;font-weight:800;letter-spacing:0.8px;color:#38bdf8;text-transform:uppercase">Live Stream</span>
          </div>
          <button type="button" class="cv-sb-toggle-btn on" id="sidebarToggleLiveBtn" title="Toggle Live Streaming">ON</button>
        </div>
        <div class="cv-sb-live-metrics">
          <div class="cv-sb-metric-item">
            <span class="cv-sb-metric-val" id="sbLiveDevCount">—</span>
            <span class="cv-sb-metric-lbl">Devices</span>
          </div>
          <div class="cv-sb-metric-item">
            <span class="cv-sb-metric-val" id="sbLiveCustCount">—</span>
            <span class="cv-sb-metric-lbl">Customers</span>
          </div>
        </div>
        <div class="cv-sb-live-foot" id="sbLiveTime">Live • Streaming active</div>
      </div>
      </div>
    </aside>
"""

INDEX_PORTAL_CONTAINER = """
      <section class="container-box active" id="box-portal" style="display:block;border-top-color:var(--primary);">
        <div class="container-tag" style="color:var(--primary);background:rgba(29,104,225,0.12)">🌐 BSTPL CustomerVault Navigation Portal</div>
        <div style="margin-bottom:28px;">
          <h2>BSTPL CustomerVault Systems &amp; Inventories</h2>
          <p class="sub">Select any core subsystem below to access its dedicated management interface.</p>
        </div>
        
        <div class="portal-grid" style="display:grid;grid-template-columns:repeat(auto-fill, minmax(280px, 1fr));gap:20px;">
          <a href="home.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">🏠</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Home Overview</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">Real-time telemetry, 4-stat metrics ribbon, live transactions stream, and database health report.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Home Overview &rarr;</div>
          </a>
          
          <a href="inventory.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">📇</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Customer Inventory</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">Per-customer inventory filtering, device records pagination, sorting, search, and Excel export.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Customer Inventory &rarr;</div>
          </a>

          <a href="sim-upload.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">📱</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">SIM Data Upload</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">Bulk Excel/CSV upload, intelligent schema normalization, and insert-only duplicate protection.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open SIM Upload &rarr;</div>
          </a>

          <a href="fetch-data.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">🔍</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Fetch Data</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">Advanced multi-criteria search, query builder, bulk IMEI lookup, and targeted export.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Fetch Data &rarr;</div>
          </a>

          <a href="edit-delete.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">✏️</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Edit / Delete by IMEI</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">Single device record editor, and bulk IMEI batch delete/restore operations.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Edit / Delete &rarr;</div>
          </a>

          <a href="alerts.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">⚠️</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Expiry Alerts</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">SIM contract &amp; subscription expiry monitoring, customizable threshold windows, and print reports.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Expiry Alerts &rarr;</div>
          </a>

          <a href="errors.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">🚨</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Errored Entries</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">Isolate failed upload entries (2,055), inspect format errors, resolve, and re-process.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Errored Entries &rarr;</div>
          </a>

          <a href="settings.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">⚙️</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Settings &amp; Preferences</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">User profile, 4 color theme palettes, RBAC user management, and login audit history.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Settings &rarr;</div>
          </a>

          <a href="dashboard.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">📊</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Dashboard Overview</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">Dedicated full telemetry dashboard view with real-time streaming and database metrics.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Dashboard &rarr;</div>
          </a>
                  <a href="login.html" class="portal-card" style="text-decoration:none;display:flex;flex-direction:column;gap:10px;padding:22px;border-radius:16px;background:var(--card);border:1.5px solid var(--line);box-shadow:var(--shadow);transition:all 0.2s ease;">
            <div style="font-size:32px;">🔐</div>
            <div style="font-size:17px;font-weight:800;color:var(--text);">Account &amp; Sign In</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.4;">Access user authentication, employee ID registration, demo credentials, and password management.</div>
            <div style="margin-top:auto;font-size:12px;font-weight:700;color:var(--primary);">Open Sign In &rarr;</div>
          </a>
        </div>
      </section>
"""

INDEX_JS = """
    // Index Portal & Auth Handling
    document.addEventListener('DOMContentLoaded', () => {
      const u = getUser();
      if (tok && u.user_id) {
        toast('Welcome back, ' + (u.name || u.user_id));
      }
    });
"""

pages = [
    {
        'file': 'frontend/home.html',
        'title': 'Home Overview & Live Updates — BSTPL CustomerVault',
        'active_key': 'HOME',
        'has_auth_wrap': False,
        'has_home_header': True,
        'container_html': containers['box-home'],
        'dialog_keys': ['dlgLiveUpdatesModal', 'dlgEditName', 'pwd', 'dlgEventPopup', 'dlgActionProgress', 'devdlg', 'cdlg'],
        'feature_js': feature_blocks['HOME'],
        'init_js': 'currentContainerId = "box-home"; await loadHomeContainer();'
    },
    {
        'file': 'frontend/dashboard.html',
        'title': 'Dashboard Overview — BSTPL CustomerVault',
        'active_key': 'HOME',
        'has_auth_wrap': False,
        'has_home_header': True,
        'container_html': containers['box-home'],
        'dialog_keys': ['dlgLiveUpdatesModal', 'dlgEditName', 'pwd', 'dlgEventPopup', 'dlgActionProgress', 'devdlg', 'cdlg'],
        'feature_js': feature_blocks['HOME'],
        'init_js': 'currentContainerId = "box-home"; await loadHomeContainer();'
    },
    {
        'file': 'frontend/inventory.html',
        'title': 'Customer Inventory — BSTPL CustomerVault',
        'active_key': 'INV',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-inv'],
        'dialog_keys': ['dlgRenameAllCustomers', 'dlgDeleteCustomerEntries', 'devdlg', 'dlgAddColumn', 'dlgChooseExportCols', 'dlgCartModal', 'cdlg', 'qsdlg', 'dlgEventPopup', 'dlgActionProgress', 'dlgUploadErrorsAlert', 'dlgCheckEntriesModal'],
        'feature_js': feature_blocks['INV'],
        'init_js': 'await loadInventoryContainer().catch(e => console.warn(e));'
    },
    {
        'file': 'frontend/sim-upload.html',
        'title': 'SIM Data Upload — BSTPL CustomerVault',
        'active_key': 'SIM',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-sim'],
        'dialog_keys': ['dlgUploadErrorsAlert', 'dlgEventPopup', 'dlgActionProgress'],
        'feature_js': feature_blocks['SIM'],
        'init_js': 'initBulkUploadContainer();'
    },
    {
        'file': 'frontend/fetch-data.html',
        'title': 'Fetch Data — BSTPL CustomerVault',
        'active_key': 'FETCH',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-fetch'],
        'dialog_keys': ['qsdlg', 'dlgEventPopup', 'dlgActionProgress'],
        'feature_js': feature_blocks['FETCH'],
        'init_js': 'initFetchContainer();'
    },
    {
        'file': 'frontend/edit-delete.html',
        'title': 'Edit / Delete by IMEI — BSTPL CustomerVault',
        'active_key': 'EDIT',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-edit'],
        'dialog_keys': ['dlgBulkDeleteExcel', 'dlgBulkEditImei', 'dlgCartModal', 'devdlg', 'dlgEventPopup', 'dlgActionProgress'],
        'feature_js': feature_blocks['EDIT'],
        'init_js': 'initEditImeiContainer();'
    },
    {
        'file': 'frontend/alerts.html',
        'title': 'Expiry Alerts — BSTPL CustomerVault',
        'active_key': 'ALERTS',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-exp'],
        'dialog_keys': ['dlgEventPopup', 'dlgActionProgress'],
        'feature_js': feature_blocks['ALERTS'],
        'init_js': 'await loadExpiryContainer().catch(e => console.warn(e));'
    },
    {
        'file': 'frontend/errors.html',
        'title': 'Errored Entries — BSTPL CustomerVault',
        'active_key': 'ERRORS',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-errors'],
        'dialog_keys': ['dlgEditError', 'dlgPushError', 'dlgEventPopup', 'dlgActionProgress'],
        'feature_js': feature_blocks['ERRORS'],
        'init_js': 'await loadErrorsContainer().catch(e => console.warn(e));'
    },
    {
        'file': 'frontend/settings.html',
        'title': 'Settings — BSTPL CustomerVault',
        'active_key': 'SETTINGS',
        'has_auth_wrap': False,
        'has_home_header': False,
        'container_html': containers['box-settings'],
        'dialog_keys': ['dlgEditName', 'pwd', 'dlgManageUsers', 'dlgAuditLog', 'dlgUserPermissions', 'dlgEventPopup', 'dlgActionProgress'],
        'feature_js': feature_blocks['SETTINGS'],
        'init_js': 'await loadSettingsPage().catch(e => console.warn(e));'
    }
]

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TITLE__</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="xlsx.full.min.js"></script>
  <script>
    (function() {
      try {
        var m = localStorage.getItem('valut_theme_mode') || localStorage.getItem('theme') || 'light';
        var p = localStorage.getItem('valut_palette') || 'royal_navy';
        document.documentElement.setAttribute('data-theme', m);
        document.documentElement.setAttribute('data-mode', m);
        document.documentElement.setAttribute('data-palette', p);
      } catch(e) {}
    })();
  </script>
  <style>
__BASE_CSS__
  </style>
</head>
<body class="app-active">
  __AUTH_HTML__<div id="dashboardWrap" class="cv-app-shell" style="display:flex">
__SIDEBAR_HTML__
    <main class="cv-main-panel" id="cvMainPanel">
__HEADER_HTML__
__CONTAINER_HTML__
    </main>
  </div>

  __DIALOGS_HTML__

  <div id="toast" class="toast"></div>

  <script>
__SCRIPT_CONTENT__
  </script>
</body>
</html>
"""

for p in pages:
    sidebar_html = generate_sidebar(p['active_key'])
    header_html = home_top_elements if p['has_home_header'] else ""
    auth_html = (auth_wrap_html + "\n\n  ") if p['has_auth_wrap'] else ""
    dialogs_html = "\n\n  ".join([dialogs_dict[did] for did in p['dialog_keys'] if did in dialogs_dict])
    
    script_content = LEAN_FOUNDATION_JS + "\n\n" + p['feature_js'] + f"""
    // Page Boot
    const _bootPage = async () => {{
      await syncGlobalMetricsAndChrome();
      {p['init_js']}
    }};
    document.addEventListener('DOMContentLoaded', _bootPage);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {{
      _bootPage();
    }}
    """

    page_html = PAGE_TEMPLATE
    page_html = page_html.replace('__TITLE__', p['title'])
    page_html = page_html.replace('__BASE_CSS__', BASE_CSS)
    page_html = page_html.replace('__AUTH_HTML__', auth_html)
    page_html = page_html.replace('__SIDEBAR_HTML__', sidebar_html)
    page_html = page_html.replace('__HEADER_HTML__', header_html)
    page_html = page_html.replace('__CONTAINER_HTML__', p['container_html'])
    page_html = page_html.replace('__DIALOGS_HTML__', dialogs_html)
    page_html = page_html.replace('__SCRIPT_CONTENT__', script_content)

    with open(p['file'], 'w', encoding='utf-8') as out:
        out.write(page_html)
    
    print(f"Generated {p['file']} (Size: {len(page_html):,} bytes, Lines: {len(page_html.splitlines())})")

print("\nALL MODULAR WEBPAGES BUILT SUCCESSFULLY!")
