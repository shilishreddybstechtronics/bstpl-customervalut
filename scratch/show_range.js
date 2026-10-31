const fs = require('fs');
const content = fs.readFileSync('frontend/index.html', 'utf8');
const lines = content.split(/\r?\n/);
for (let i = 15590; i < 15640; i++) {
  console.log(`${i + 1}: ${lines[i]}`);
}

