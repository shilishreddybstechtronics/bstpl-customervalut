const fs = require('fs');
const ts = require('C:/Users/soumy/AppData/Local/Programs/Antigravity IDE/resources/app/extensions/node_modules/typescript/lib/typescript.js');

const html = fs.readFileSync('frontend/index.html', 'utf8');
const regex = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
let match;
while ((match = regex.exec(html)) !== null) {
  if (match[1].includes('src=')) continue;
  const scriptContent = match[2];
  const before = html.substring(0, match.index + match[0].indexOf('>') + 1);
  const lineOffset = before.split('\n').length;
  
  // Create virtual source file with padding lines so line numbers match index.html
  const paddedContent = '\n'.repeat(lineOffset - 1) + scriptContent;
  const sf = ts.createSourceFile('frontend/index.html', paddedContent, ts.ScriptTarget.Latest, true);
  
  const diagnostics = [...sf.parseDiagnostics];
  console.log('TypeScript parse diagnostics count:', diagnostics.length);
  for (const d of diagnostics) {
    const { line, character } = sf.getLineAndCharacterOfPosition(d.start);
    console.log(`Line ${line + 1}, Col ${character + 1}: ${ts.flattenDiagnosticMessageText(d.messageText, '\n')}`);
  }
}

