const { execSync } = require('child_process');
const commits = execSync('git log -g --format="%h"', { encoding: 'utf8' }).trim().split('\n');

for (const c of commits) {
  try {
    const content = execSync(`git show ${c}:frontend/index.html`, { maxBuffer: 50 * 1024 * 1024 }).toString('utf8');
    const lines = content.split(/\r?\n/);
    if (lines.length >= 15625) {
      const l15617 = lines[15616] || '';
      const l15625 = lines[15624] || '';
      if (l15617.length >= 45) {
        console.log(`Commit ${c}:`);
        console.log(`  15617: ${l15617}`);
        console.log(`  15625: ${l15625}`);
      }
    }
  } catch (e) {}
}

