const fs = require('fs');
const vm = require('vm');

const file = process.argv[2] || 'scratch/test_inv_bundle.js';
const code = fs.readFileSync(file, 'utf-8');
new vm.Script(code);
console.log(`[SUCCESS] ${file} parsed with 0 syntax errors!`);

