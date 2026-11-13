const { execSync } = require('child_process');
const content = execSync('git show HEAD:frontend/index.html', { maxBuffer: 50 * 1024 * 1024 }).toString('utf8');
const lines = content.split(/\r?\n/);
for (let i = 15610; i <= 15630; i++) {
  console.log(`${i}: ${JSON.stringify(lines[i-1])}`);
}

