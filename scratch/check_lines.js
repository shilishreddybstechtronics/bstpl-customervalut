const fs = require('fs');
const content = fs.readFileSync('frontend/index.html', 'utf8');
const lines = content.split('\n');
console.log('Total lines:', lines.length);
for (let i = 15610; i <= 15635; i++) {
  console.log(`${i}: ${JSON.stringify(lines[i - 1])}`);
}

