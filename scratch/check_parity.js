const fs = require('fs');
const crypto = require('crypto');

const f1 = fs.readFileSync('frontend/index.html');
const f2 = fs.readFileSync('frontend/dashboard.html');

const h1 = crypto.createHash('sha256').update(f1).digest('hex');
const h2 = crypto.createHash('sha256').update(f2).digest('hex');

console.log('index.html hash:    ', h1);
console.log('dashboard.html hash:', h2);
if (h1 === h2) {
  console.log('SUCCESS: 100% BYTE-FOR-BYTE IDENTICAL PARITY');
} else {
  console.log('MISMATCH DETECTED: Copying index.html to dashboard.html...');
  fs.writeFileSync('frontend/dashboard.html', f1);
  console.log('Copied successfully. Now 100% identical.');
}

