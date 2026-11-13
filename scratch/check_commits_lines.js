const { execSync } = require('child_process');
const commits = execSync('git rev-list HEAD', { encoding: 'utf8' }).trim().split('\n');

for (const c of commits) {
  try {
    const content = execSync(`git show ${c}:frontend/index.html`, { maxBuffer: 50 * 1024 * 1024 }).toString('utf8');
    const lines = content.split(/\r?\n/);
    if (lines.length >= 15625) {
      console.log(`Commit ${c.substring(0, 7)}:`);
      console.log(`  Line 15617: ${JSON.stringify(lines[15616])}`);
      console.log(`  Line 15618: ${JSON.stringify(lines[15617])}`);
      console.log(`  Line 15619: ${JSON.stringify(lines[15618])}`);
      console.log(`  Line 15620: ${JSON.stringify(lines[15619])}`);
      console.log(`  Line 15621: ${JSON.stringify(lines[15620])}`);
      console.log(`  Line 15622: ${JSON.stringify(lines[15621])}`);
      console.log(`  Line 15623: ${JSON.stringify(lines[15622])}`);
      console.log(`  Line 15624: ${JSON.stringify(lines[15623])}`);
      console.log(`  Line 15625: ${JSON.stringify(lines[15624])}`);
      console.log(`  Line 15626: ${JSON.stringify(lines[15625])}`);
    }
  } catch (e) {}
}

