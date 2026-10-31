const { execSync } = require('child_process');
const content = execSync('git show 45bf85a:frontend/index.html', { maxBuffer: 50 * 1024 * 1024 }).toString('utf8');
const lines = content.split(/\r?\n/);
for (let i = 15610; i <= 15630; i++) {
  console.log(`${i}: ${lines[i-1]}`);
}

