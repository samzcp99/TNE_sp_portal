import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { build } from './node_modules/esbuild/lib/main.js';
await build({entryPoints:['src/lib/password-generator.ts'], bundle:true, platform:'node', format:'esm', outfile:'/opt/pswd/generator-test-bundle.mjs', tsconfig:'tsconfig.json'});
globalThis.window = {crypto:webcrypto};
const {generateNormalPassword,generateDicewarePassword,generatePin} = await import('/opt/pswd/generator-test-bundle.mjs');
const opts={customSymbols:'',excludeSimilar:false,excludeSymbols:'',includeLower:true,includeUpper:true,includeNumbers:true,includeSymbols:true,length:20};
const generated=new Set();
for(let i=0;i<200;i++){
 const p=generateNormalPassword(opts);assert.equal(p.length,20);generated.add(p);
 const digits=generateNormalPassword({...opts,includeLower:false,includeUpper:false,includeSymbols:false,length:16});assert.match(digits,/^\d{16}$/);
 const pin=generatePin({pinLength:6});assert.match(pin,/^\d{6}$/);
 const clean=generateNormalPassword({...opts,excludeSimilar:true,excludeSymbols:'@#$%'});assert.ok(!/[Il1O0@#$%]/.test(clean));
 const phrase=generateDicewarePassword({wordlist:['alpha','beta','gamma','delta'],wordCount:6,separator:'dash',capitalize:false,randomCapitalization:true,randomNumberBeginning:false,randomNumberEnd:false});assert.equal(phrase.split('-').length,6);
}
assert.equal(generated.size,200);
console.log('PASS: 200 iterations covering password length, excluded characters, numeric-only passwords, PIN, passphrases and uniqueness. No passwords logged.');
