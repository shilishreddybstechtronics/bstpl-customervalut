const fs = require('fs');

function testHtml(filePath) {
  console.log(`Checking frontend flow in ${filePath}...`);
  const html = fs.readFileSync(filePath, 'utf8');

  // Check Settings dialog
  if (!html.includes('id="dlgSettings"')) throw new Error("Missing #dlgSettings");

  // Check all options
  const checks = [
    'id="closeDlgSettings"',
    'id="settingsBtnEditName"',
    'id="settingsCurrentNameVal"',
    'id="settingsAccountName"',
    'id="settingsUserAvatarCircle"',
    'id="settingsBtnPassword"',
    'id="settingsBtnManageUsers"',
    'id="settingsBtnLoginInv"',
    'id="settingsModeLight"',
    'id="settingsModeDark"',
    'data-palette-val="royal_navy"',
    'data-palette-val="midnight"',
    'data-palette-val="emerald"',
    'data-palette-val="crimson_vault"',
    'data-palette-val="ocean"',
    'data-palette-val="violet"',
    'data-palette-val="sunset"',
    'id="settingsBtnLogout"'
  ];

  for (const c of checks) {
    if (!html.includes(c)) throw new Error(`Missing ${c} in ${filePath}`);
  }
  console.log("✓ All Settings buttons, user display, and 7 themes present in markup.");

  // Check Edit Name dialog with 3 exact user options: Current Name, Updated Name, Confirm Name + Save
  const nameChecks = [
    'id="dlgEditName"',
    'id="closeDlgEditName"',
    'id="editNameCurrent"',
    'id="editNameUpdated"',
    'id="editNameConfirm"',
    'id="btnConfirmEditName"'
  ];
  for (const c of nameChecks) {
    if (!html.includes(c)) throw new Error(`Missing ${c} in ${filePath}`);
  }
  console.log("✓ Edit Name modal with 3 fields (Current Name, Updated Name, Confirm Name) & Save button present.");

  // Check Change Password dialog
  const pwChecks = [
    'id="pwd"',
    'id="closeDlgChangePassword"',
    'id="p1"',
    'id="p2"',
    'id="p3"',
    'id="btnConfirmChangePw"',
    "togglePasswordInputVisibility('p1')",
    "togglePasswordInputVisibility('p2')",
    "togglePasswordInputVisibility('p3')"
  ];
  for (const c of pwChecks) {
    if (!html.includes(c)) throw new Error(`Missing ${c} in ${filePath}`);
  }
  console.log("✓ Change Password modal with 3 eye toggles & confirmation button present.");

  // Check JS wiring
  if (!html.includes("openEditNameModal()")) throw new Error("openEditNameModal missing");
  if (!html.includes("submitEditNameModal()")) throw new Error("submitEditNameModal missing");
  if (!html.includes("openChangePasswordModal()")) throw new Error("openChangePasswordModal missing");
  if (!html.includes("applyTheme(pal, currentMode, true)")) throw new Error("applyTheme persistence missing");
  if (!html.includes("window.addEventListener('pageshow'")) throw new Error("pageshow guard missing");
  if (!html.includes("window.addEventListener('popstate'")) throw new Error("popstate guard missing");

  console.log(`✓ ${filePath} flow verification PASSED completely!\n`);
}

testHtml('frontend/index.html');
testHtml('frontend/dashboard.html');
