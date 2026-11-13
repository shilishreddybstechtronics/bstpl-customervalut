const fs = require('fs');

const html = fs.readFileSync('frontend/index.html', 'utf8');

const regex = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
let match;
let scriptIdx = 0;

while ((match = regex.exec(html)) !== null) {
  scriptIdx++;
  const attrs = match[1];
  if (attrs.includes('src=')) continue;
  
  const scriptContent = match[2];
  // Calculate line offset
  const before = html.substring(0, match.index + match[0].indexOf('>') + 1);
  const lineOffset = before.split('\n').length;
  
  console.log(`Checking inline script #${scriptIdx} starting at line ${lineOffset}...`);
  
  // Try to parse using Function or vm.Script
  const vm = require('vm');
  try {
    new vm.Script(scriptContent, {
      filename: `frontend/index.html`,
      lineOffset: lineOffset - 1
    });
    console.log(`Script #${scriptIdx} passed validation!`);
  } catch (err) {
    console.error(`ERROR in script #${scriptIdx}:`, err.stack);
  }
}

