const fs = require('fs');
const ts = require('C:/Users/soumy/AppData/Local/Programs/Antigravity IDE/resources/app/extensions/node_modules/typescript/lib/typescript.js');

const content = fs.readFileSync('frontend/index.html', 'utf8');
const regex = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
let match;
while ((match = regex.exec(content)) !== null) {
  if (match[1].includes('src=')) continue;
  const code = match[2];
  
  // We parse with standard non-module target to catch illegal await
  const sf = ts.createSourceFile('test.js', code, ts.ScriptTarget.ES2020, true, ts.ScriptKind.JS);
  
  function checkNode(node) {
    if (ts.isAwaitExpression(node)) {
      // Find parent function
      let parent = node.parent;
      while (parent && !ts.isFunctionDeclaration(parent) && !ts.isFunctionExpression(parent) && !ts.isArrowFunction(parent) && !ts.isMethodDeclaration(parent)) {
        parent = parent.parent;
      }
      if (parent) {
        const hasAsync = parent.modifiers && parent.modifiers.some(m => m.kind === ts.SyntaxKind.AsyncKeyword);
        if (!hasAsync) {
          const { line, character } = sf.getLineAndCharacterOfPosition(node.getStart());
          const name = parent.name ? parent.name.getText() : 'anonymous';
          console.error(`SYNTAX ERROR: 'await' used in non-async function '${name}' at line ${line + 1}, col ${character + 1}`);
        }
      }
    }
    ts.forEachChild(node, checkNode);
  }
  
  checkNode(sf);
}
console.log("Check complete.");

