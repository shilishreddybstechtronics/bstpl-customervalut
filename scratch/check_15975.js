const fs = require('fs');
const content = fs.readFileSync('frontend/index.html', 'utf8');
const lines = content.split(/\r?\n/);
for (let i = 15965; i <= 15985; i++) {
  console.log(`${i}: ${lines[i - 1]}`);
}

