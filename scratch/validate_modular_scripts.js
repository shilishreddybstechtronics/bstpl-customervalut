const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('frontend/index.html', 'utf-8');
const scriptMatches = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)];
const mainScript = scriptMatches[2][1];

const posHome = mainScript.indexOf('async function loadHomeContainer()');
const posInv = mainScript.indexOf('async function loadInventoryContainer()');
const posSim = mainScript.indexOf('function initBulkUploadContainer()');
const posFetch = mainScript.indexOf('function initFetchContainer()');
const posEdit = mainScript.indexOf('function initEditImeiContainer()');
const posAlerts = mainScript.indexOf('async function loadExpiryContainer()');
const posHealth = mainScript.indexOf('async function loadHealthContainer()');
const posErrors = mainScript.indexOf('async function loadErrorsContainer()');
const posCart = mainScript.indexOf('async function loadCartContainer()');
const posUsers = mainScript.indexOf('async function loadAuditLogContainer()');
const posQuicksearch = mainScript.indexOf('/* ---------- Quick Search (Ctrl+K) ---------- */');

const core1 = mainScript.slice(0, posHome);
const core2 = mainScript.slice(posQuicksearch);

const featureBlocks = {
  HOME: mainScript.slice(posHome, posInv) + "\n" + mainScript.slice(posHealth, posErrors),
  INV: mainScript.slice(posInv, posSim),
  SIM: mainScript.slice(posSim, posFetch),
  FETCH: mainScript.slice(posFetch, posEdit),
  EDIT: mainScript.slice(posEdit, posAlerts) + "\n" + mainScript.slice(posCart, posUsers),
  ALERTS: mainScript.slice(posAlerts, posHealth),
  ERRORS: mainScript.slice(posErrors, posCart),
  SETTINGS: mainScript.slice(posUsers, posQuicksearch)
};

let allPassed = true;
for (const [key, block] of Object.entries(featureBlocks)) {
  const code = core1 + "\n\n" + block + "\n\n" + core2;
  try {
    new vm.Script(code);
    console.log(`[PASS] Feature ${key}: compiles with 0 syntax errors.`);
  } catch (err) {
    allPassed = false;
    console.error(`[FAIL] Feature ${key}: ${err.message}`);
  }
}

if (!allPassed) process.exit(1);
console.log("\nALL MODULAR FEATURE SCRIPTS VALIDATED SUCCESSFULLY (100%)!");

