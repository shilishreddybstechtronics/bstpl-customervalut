import re
import shutil
import hashlib

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update getInitialApiBase
old_api_base = """      function getInitialApiBase() {
        if (window.API_URL) return window.API_URL.replace(/\/+$/, '');
        const stored = localStorage.getItem('API_URL');
        if (stored) return stored.replace(/\/+$/, '');
        if (window.location.protocol.startsWith('http')) {
          if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            if (window.location.port === '8000') return window.location.origin;
            return 'http://127.0.0.1:8000';
          }
          return window.location.origin;
        }
        return 'http://127.0.0.1:8000';
      }"""

new_api_base = """      function getInitialApiBase() {
        if (window.API_URL) return window.API_URL.replace(/\/+$/, '');
        const isLocalHost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || !window.location.hostname;
        
        // When running on localhost / 127.0.0.1 / file://, ALWAYS prefer local backend port 8000
        if (isLocalHost || window.location.protocol === 'file:') {
          if (window.location.port === '8000') return window.location.origin;
          const stored = localStorage.getItem('API_URL');
          if (stored && (stored.includes('localhost') || stored.includes('127.0.0.1'))) {
            return stored.replace(/\/+$/, '');
          }
          return 'http://127.0.0.1:8000';
        }

        const stored = localStorage.getItem('API_URL');
        if (stored) return stored.replace(/\/+$/, '');
        return window.location.origin;
      }"""

assert old_api_base in code, "old_api_base not found"
code = code.replace(old_api_base, new_api_base, 1)

# 2. Update checkBackendHealth candidates
old_candidates = """        const candidates = [];
        if (API_BASE) candidates.push(API_BASE);
        if (!candidates.includes('https://bstpl-customervalut-2-jm3t.onrender.com')) {
          candidates.push('https://bstpl-customervalut-2-jm3t.onrender.com');
        }
        if (!candidates.includes('http://127.0.0.1:8000')) {
          candidates.push('http://127.0.0.1:8000');
        }"""

new_candidates = """        const candidates = [];
        const isLocalHost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || !window.location.hostname;
        
        if (isLocalHost || window.location.protocol === 'file:') {
          if (window.location.port === '8000' && !candidates.includes(window.location.origin)) {
            candidates.push(window.location.origin);
          }
          if (!candidates.includes('http://127.0.0.1:8000')) candidates.push('http://127.0.0.1:8000');
          if (!candidates.includes('http://localhost:8000')) candidates.push('http://localhost:8000');
          if (API_BASE && !candidates.includes(API_BASE)) candidates.push(API_BASE);
        } else {
          if (API_BASE && !candidates.includes(API_BASE)) candidates.push(API_BASE);
          if (window.location.origin && !candidates.includes(window.location.origin)) candidates.push(window.location.origin);
        }
        if (!candidates.includes('https://bstpl-customervalut-2-jm3t.onrender.com')) {
          candidates.push('https://bstpl-customervalut-2-jm3t.onrender.com');
        }"""

assert old_candidates in code, "old_candidates not found"
code = code.replace(old_candidates, new_candidates, 1)

# 3. Update status label in checkBackendHealth
old_status_label = """              if (el) {
                el.innerHTML = `Database Online and Verified <span title="Configure backend server URL" style="cursor:pointer;opacity:0.65;margin-left:6px" onclick="promptServerUrl()">⚙️</span>`;
                el.className = 'db-status ok';
              }"""

new_status_label = """              if (el) {
                const label = API_BASE.includes('127.0.0.1') || API_BASE.includes('localhost') ? 'Local Database Verified' : 'Database Online and Verified';
                el.innerHTML = `${label} <span title="Connected: ${API_BASE} (click to change)" style="cursor:pointer;opacity:0.75;margin-left:6px" onclick="promptServerUrl()">⚙️</span>`;
                el.className = 'db-status ok';
              }"""

assert old_status_label in code, "old_status_label not found"
code = code.replace(old_status_label, new_status_label, 1)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(code)

shutil.copyfile('frontend/index.html', 'frontend/dashboard.html')

h1 = hashlib.sha256(open('frontend/index.html', 'rb').read()).hexdigest()
h2 = hashlib.sha256(open('frontend/dashboard.html', 'rb').read()).hexdigest()
print(f"Applied candidates & local priority fix! Parity: {h1 == h2} ({h1})")

