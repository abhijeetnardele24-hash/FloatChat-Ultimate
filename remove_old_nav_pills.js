const fs = require('fs');
const glob = require('glob');

const pages = glob.sync('app/**/page.tsx');

for (const file of pages) {
    let content = fs.readFileSync(file, 'utf8');

    // Try to remove "Floating nav pill" sections (handling motion.div or div Wrappers)
    const originalContent = content;

    // Pattern for app/page.tsx style
    let r1 = /\{\/\*\s*──\s*Floating [Nn]av [Pp]ill\s*──\s*\*\/\}\s*<motion\.div[\s\S]*?(?=<\/motion\.div>)\s*<\/motion\.div>/;
    if (r1.test(content)) {
        content = content.replace(r1, '');
    }

    // Pattern for app/docs/page.tsx style 
    // Wait, docs uses a regular <div style={{ position: 'fixed', top: 20
    let r2 = /\{\/\*\s*──\s*Floating [Nn]av [Pp]ill\s*──\s*\*\/\}\s*<div style=\{\{ position: 'fixed', top: 20[\s\S]*?(?=<\/div>\s*<\/div>\s*<\/div>)\s*<\/div>\s*<\/div>\s*<\/div>/;
    if (r2.test(content)) {
        content = content.replace(r2, '');
    }

    // A more generic pattern that looks for the comment and everything down to its matching CTA ArrowRight closing
    let r3 = /\{\/\*\s*──\s*Floating [Nn]av [Pp]ill\s*──\s*\*\/\}(?:[\s\S]*?(?=Dashboard <ArrowRight))[\s\S]*?<\/Link>\s*<\/div>\s*<(?:\/motion\.div|\/div)>/;
    if (r3.test(originalContent)) {
        content = originalContent.replace(r3, '');
    }

    // Pattern for dashboard/study pages
    let r4 = /\{\/\*\s*──\s*Floating Header ──\s*\*\/\}(?:[\s\S]*?(?=Dashboard <ArrowRight\|Home <ArrowRight|<ArrowRight))[\s\S]*?<\/Link>\s*<\/div>\s*<\/div>/;
    if (r4.test(originalContent)) {
        // wait I will do it with precise regex for remaining ones if r3 missed
    }

    if (content !== originalContent) {
        fs.writeFileSync(file, content);
        console.log(`Removed local nav pill from: ${file}`);
    }
}
