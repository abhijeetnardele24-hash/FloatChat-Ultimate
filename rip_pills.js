const fs = require('fs');

function rip(file) {
    let content = fs.readFileSync(file, 'utf8');

    // Dashboard
    if (file.includes('dashboard')) {
        let regex = /\{\/\*\s*──\s*Floating Glass Nav Pill\s*──\s*\*\/\}[\s\S]*?<\/div>\s*<\/div>\s*<\/div>/;
        content = content.replace(regex, '');
    }

    // Study
    if (file.includes('study')) {
        let regex = /\{\/\*\s*──\s*Floating Glass Pill Navbar\s*──\s*\*\/\}[\s\S]*?<\/div>\s*<\/div>\s*<\/div>/;
        content = content.replace(regex, '');
    }

    // Visualizations
    if (file.includes('visualizations')) {
        let regex = /\{\/\*\s*──\s*Floating nav pill\s*──\s*\*\/\}[\s\S]*?<\/div>\s*<\/motion\.div>/;
        content = content.replace(regex, '');
    }

    fs.writeFileSync(file, content);
}

rip('app/dashboard/page.tsx');
rip('app/study/page.tsx');
rip('app/visualizations/page.tsx');
console.log('Ripped old nav pills');
