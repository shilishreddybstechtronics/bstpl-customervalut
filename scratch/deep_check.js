const fs = require('fs');
const ts = require('C:/Users/soumy/AppData/Local/Programs/Antigravity IDE/resources/app/extensions/node_modules/typescript/lib/typescript.js');

const html = fs.readFileSync('frontend/index.html', 'utf8');
const regex = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
let match;
let count = 0;
while ((match = regex.exec(html)) !== null) {
  count++;
  if (match[1].includes('src=')) continue;
  const scriptContent = match[2];
  const before = html.substring(0, match.index + match[0].indexOf('>') + 1);
  const lineOffset = before.split('\n').length;
  const paddedContent = '\n'.repeat(lineOffset - 1) + scriptContent;
  
  const sf = ts.createSourceFile('index.js', paddedContent, ts.ScriptTarget.Latest, true);
  console.log(`Script ${count} (line ${lineOffset}): parse diagnostics count = ${sf.parseDiagnostics.length}`);
  for (const d of sf.parseDiagnostics) {
    const { line, character } = sf.getLineAndCharacterOfPosition(d.start);
    console.log(`  Line ${line + 1}, Col ${character + 1}:`, d.messageText);
  }
}

