const fs = require('fs');
const glob = require('glob');

const files = glob.sync('app/**/page.tsx');
for (const file of files) {
    let content = fs.readFileSync(file, 'utf8');

    // specifically update the generic dashboard map
    if (file.includes('dashboard') || file.includes('study')) {
        if (!content.includes("{ label: 'Docs', href: '/docs' }")) {
            content = content.replace(
                /\{ label: 'Study', href: '\/study' \} \]/g,
                "{ label: 'Study', href: '/study' }, { label: 'Docs', href: '/docs' } ]"
            );
            content = content.replace(
                /\{ label: 'Tools', href: '\/tools' \} \]/g,
                "{ label: 'Tools', href: '/tools' }, { label: 'Docs', href: '/docs' } ]"
            );
            fs.writeFileSync(file, content);
        }
    }
}
console.log('Done linking docs');
