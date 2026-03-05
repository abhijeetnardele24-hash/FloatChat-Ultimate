const fs = require('fs');
const path = require('path');

// Fix Chat Page
let chatPath = path.join(__dirname, 'app/chat/page.tsx');
let chatCss = fs.readFileSync(chatPath, 'utf8');

chatCss = chatCss.replace(
    /(\n\s*<FloatChatLogo size=\{16\} \/>\n\s*<\/div>)\n\n\s*\{\/\* ── Messages ── \*\/\}/,
    '$1\n            </div>\n\n            {/* ── Messages ── */}'
).replace(
    /(\n\s*<\/p>\n\s*<\/div>\n\s*<\/div>)\n\n\s*<style>/,
    '$1\n            </div>\n\n            <style>'
);
fs.writeFileSync(chatPath, chatCss);

// Fix Explorer Page
let expPath = path.join(__dirname, 'app/explorer/page.tsx');
let expCss = fs.readFileSync(expPath, 'utf8');

expCss = expCss.replace(
    /(\n\s*<\/button>\n\s*<\/div>\n\s*<\/div>)\n\n\s*\{\/\* Body \*\/\}/,
    '$1\n            </div>\n\n            {/* Body */}'
).replace(
    /(\n\s*<\/div>\n\s*<\/div>\n\s*<\/div>)\n\n\s*<\/div>\n\s*\)/,
    '$1\n            </div>\n            </div>\n\n        </div>\n    )'
);
fs.writeFileSync(expPath, expCss);

// Fix Study Page
let studyPath = path.join(__dirname, 'app/study/page.tsx');
let studyCss = fs.readFileSync(studyPath, 'utf8');

studyCss = studyCss.replace(
    /(\n\s*<\/div>\n\s*<\/div>)\n\n\s*\{\/\* Main Layout \*\/\}/,
    '$1\n            </div>\n\n            {/* Main Layout */}'
).replace(
    /(\n\s*<\/div>\n\s*<\/div>\n\s*<\/div>\n\s*<\/div>)\n\n\s*<\/div>\n\s*\)/,
    '$1\n            </div>\n\n        </div>\n    )'
);
fs.writeFileSync(studyPath, studyCss);

console.log('Fixed unmatched divs!');
