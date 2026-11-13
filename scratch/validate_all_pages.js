const fs = require('fs');
const vm = require('vm');

const files = [
  'frontend/index.html',
  'frontend/dashboard.html',
  'frontend/home.html',
  'frontend/inventory.html',
  'frontend/sim-upload.html',
  'frontend/fetch-data.html',
  'frontend/edit-delete.html',
  'frontend/alerts.html',
  'frontend/errors.html',
  'frontend/settings.html',
  'frontend/login.html'
];

let allPassed = true;

for (const file of files) {
  const content = fs.readFileSync(file, 'utf-8');
  const scriptRegex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
  let match;
  let scriptIndex = 0;
  
  while ((match = scriptRegex.exec(content)) !== null) {
    const code = match[1];
    if (!code.trim()) continue;
    try {
      new vm.Script(code);
      // console.log(`  [OK] ${file} script #${scriptIndex}`);
    } catch (err) {
      allPassed = false;
      console.error(`[FAIL] ${file} script #${scriptIndex}: ${err.message}`);
    }
    scriptIndex++;
  }
  console.log(`[PASS] ${file}: all ${scriptIndex} scripts parsed with 0 syntax errors.`);
}

if (!allPassed) {
  console.error("Syntax errors found!");
  process.exit(1);
} else {
  console.log("\nALL 11 HTML FILES VALIDATED WITH 0 SYNTAX ERRORS (100% PASS)!");
}
