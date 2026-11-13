const fs = require('fs');
const ts = require('C:/Users/soumy/AppData/Local/Programs/Antigravity IDE/resources/app/extensions/node_modules/typescript/lib/typescript.js');

function checkFile(filePath) {
  console.log(`Checking ${filePath}...`);
  const content = fs.readFileSync(filePath, 'utf8');
  
  // Method 1: Check script tags
  const regex = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let match;
  let idx = 0;
  let hasErrors = false;
  while ((match = regex.exec(content)) !== null) {
    idx++;
    if (match[1].includes('src=')) continue;
    const scriptCode = match[2];
    const prefix = content.substring(0, match.index + match[0].indexOf('>') + 1);
    const startLine = prefix.split('\n').length;
    
    // Pad lines so error line numbers match the file exactly
    const padded = '\n'.repeat(startLine - 1) + scriptCode;
    
    const sf = ts.createSourceFile('file.js', padded, ts.ScriptTarget.Latest, true);
    
    // Check syntactic diagnostics
    const synDiag = sf.parseDiagnostics || [];
    if (synDiag.length > 0) {
      hasErrors = true;
      console.log(`[SYNTAX ERROR] Script #${idx} starting at line ${startLine}:`);
      for (const d of synDiag) {
        const { line, character } = sf.getLineAndCharacterOfPosition(d.start);
        const msg = typeof d.messageText === 'string' ? d.messageText : d.messageText.messageText;
        console.log(`  Line ${line + 1}, Col ${character + 1}: ${msg}`);
      }
    }
  }
  
  if (!hasErrors) {
    console.log(`✓ No parse/syntax errors found in ${filePath} script blocks.`);
  }
}

checkFile('frontend/index.html');
checkFile('frontend/dashboard.html');

