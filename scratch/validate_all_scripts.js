const fs = require('fs');
const ts = require('C:/Users/soumy/AppData/Local/Programs/Antigravity IDE/resources/app/extensions/node_modules/typescript/lib/typescript.js');

function deepValidateHtml(file) {
  console.log(`=== Deep Validating ${file} ===`);
  const content = fs.readFileSync(file, 'utf8');
  
  // 1. Check for basic HTML tag balancing for script/style
  const scriptOpenCount = (content.match(/<script\b/gi) || []).length;
  const scriptCloseCount = (content.match(/<\/script>/gi) || []).length;
  console.log(`Script tags: ${scriptOpenCount} open, ${scriptCloseCount} close`);
  if (scriptOpenCount !== scriptCloseCount) {
    console.error(`ERROR: Mismatched script tags!`);
  }
  
  // 2. Validate all JavaScript in <script> blocks
  const regex = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let match;
  let blockIdx = 0;
  let totalErrors = 0;
  
  while ((match = regex.exec(content)) !== null) {
    blockIdx++;
    if (match[1].includes('src=')) continue;
    const code = match[2];
    const prefix = content.substring(0, match.index + match[0].indexOf('>') + 1);
    const startLine = prefix.split('\n').length;
    
    // Create source file
    const padded = '\n'.repeat(startLine - 1) + code;
    const sf = ts.createSourceFile('test.js', padded, ts.ScriptTarget.Latest, true);
    
    if (sf.parseDiagnostics && sf.parseDiagnostics.length > 0) {
      for (const d of sf.parseDiagnostics) {
        totalErrors++;
        const { line, character } = sf.getLineAndCharacterOfPosition(d.start);
        console.error(`Parse Error in ${file} at Ln ${line + 1}, Col ${character + 1}: ${d.messageText}`);
      }
    }
    
    // Run VM script check
    const vm = require('vm');
    try {
      new vm.Script(code, { filename: `${file}#script${blockIdx}`, lineOffset: startLine - 1 });
      console.log(`✓ Script block #${blockIdx} (starts line ${startLine}) syntax valid via vm.Script`);
    } catch (err) {
      totalErrors++;
      console.error(`VM Syntax Error in ${file} around line ${startLine}:`, err.message);
    }
  }
  
  console.log(`Validation finished for ${file}: ${totalErrors} errors found.\n`);
  return totalErrors;
}

const e1 = deepValidateHtml('frontend/index.html');
const e2 = deepValidateHtml('frontend/dashboard.html');
process.exit(e1 + e2 === 0 ? 0 : 1);

