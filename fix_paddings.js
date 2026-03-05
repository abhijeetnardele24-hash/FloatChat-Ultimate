const fs = require('fs');
const glob = require('glob');

const files = glob.sync('app/**/*.tsx');

files.forEach(file => {
    let content = fs.readFileSync(file, 'utf8');
    let original = content;

    // Adjust 96px top paddings to 40px
    content = content.replace(/padding: '96px/g, "padding: '40px");

    // Adjust explorer top padding specifically as it might not be '96px ...'
    // It's padding: '96px 20px 0'
    // Actually the regex above covers it.

    // Adjust Home page 160px padding
    if (file.includes('page.tsx')) {
        content = content.replace(/paddingTop: 160/g, "paddingTop: 60");
        content = content.replace(/padding: '160px 24px 80px'/g, "padding: '60px 24px 80px'");
    }

    if (original !== content) {
        fs.writeFileSync(file, content);
        console.log(`Updated padding in ${file}`);
    }
});
