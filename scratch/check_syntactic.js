const fs = require('fs');
const ts = require('C:/Users/soumy/AppData/Local/Programs/Antigravity IDE/resources/app/extensions/node_modules/typescript/lib/typescript.js');

const content = fs.readFileSync('frontend/index.html', 'utf8');
const regex = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
let match;
while ((match = regex.exec(content)) !== null) {
  if (match[1].includes('src=')) continue;
  const scriptCode = match[2];
  const prefix = content.substring(0, match.index + match[0].indexOf('>') + 1);
  const startLine = prefix.split('\n').length;
  const padded = '\n'.repeat(startLine - 1) + scriptCode;
  
  const options = { allowJs: true, checkJs: true, target: ts.ScriptTarget.Latest };
  const host = ts.createCompilerHost(options);
  const origGetSourceFile = host.getSourceFile;
  host.getSourceFile = (fileName, languageVersion) => {
    if (fileName === 'virtual.js') {
      return ts.createSourceFile('virtual.js', padded, languageVersion, true);
    }
    return origGetSourceFile(fileName, languageVersion);
  };
  
  const program = ts.createProgram(['virtual.js'], options, host);
  const synDiag = program.getSyntacticDiagnostics();
  console.log(`Syntactic diagnostics count: ${synDiag.length}`);
  for (const d of synDiag) {
    const { line, character } = d.file.getLineAndCharacterOfPosition(d.start);
    console.log(`  Line ${line + 1}, Col ${character + 1}: ${d.messageText}`);
  }
}

