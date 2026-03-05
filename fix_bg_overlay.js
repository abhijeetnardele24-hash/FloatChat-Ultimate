const fs = require('fs');
const path = require('path');

const files = [
    'app/chat/page.tsx',
    'app/dashboard/page.tsx',
    'app/explorer/page.tsx',
    'app/page.tsx',
    'app/study/page.tsx',
    'app/tools/page.tsx',
    'app/visualizations/page.tsx'
];

for (const file of files) {
    const fullPath = path.join(__dirname, file);
    if (!fs.existsSync(fullPath)) continue;

    let content = fs.readFileSync(fullPath, 'utf8');

    // Make the background fully visible and vibrant
    content = content.replace(
        /background: 'linear-gradient\(to bottom, rgba\(255,255,255,0\.[0-9]+\) 0%, rgba\(245,245,247,0\.[0-9]+\) 100%\)',[\s]*backdropFilter: 'blur\([0-9]+px\)'/,
        "background: 'linear-gradient(to bottom, rgba(255,255,255,0.0) 0%, rgba(255,255,255,0.2) 100%)', backdropFilter: 'blur(0px)'"
    );

    // Make sure the image is fully opaque
    content = content.replace(/opacity: 0\.85/g, 'opacity: 1');

    fs.writeFileSync(fullPath, content);
    console.log('Fixed overlay in', file);
}
