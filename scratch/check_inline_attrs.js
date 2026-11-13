const fs = require('fs');
const ts = require('C:/Users/soumy/AppData/Local/Programs/Antigravity IDE/resources/app/extensions/node_modules/typescript/lib/typescript.js');

const content = fs.readFileSync('frontend/index.html', 'utf8');
const lines = content.split(/\r?\n/);

// Find inline attributes like onclick="..."
const attrRegex = /\bon\w+\s*=\s*(["'])([\s\S]*?)\1/gi;
let match;
let count = 0;
while ((match = attrRegex.exec(content)) !== null) {
  count++;
  const code = match[2];
  const prefix = content.substring(0, match.index);
  const lineNo = prefix.split('\n').length;
  
  const sf = ts.createSourceFile('attr.js', code, ts.ScriptTarget.Latest, true);
  if (sf.parseDiagnostics && sf.parseDiagnostics.length > 0) {
    console.log(`[ATTR ERROR] Line ${lineNo}:`);
    console.log(`  Code: ${code}`);
    for (const d of sf.parseDiagnostics) {
      console.log(`  -> ${d.messageText}`);
    }
  }
}
console.log(`Checked ${count} inline handlers.`);

