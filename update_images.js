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

files.forEach(file => {
    const fullPath = path.join(__dirname, file);
    if (fs.existsSync(fullPath)) {
        let content = fs.readFileSync(fullPath, 'utf8');

        // Remove white under-gradient if perfectly matches
        content = content.replace(/<div style=\{\{\s*position:\s*'absolute',\s*width:\s*'100vw',\s*height:\s*'100vh',\s*top:\s*0,\s*left:\s*0,\s*background:\s*'linear-gradient[^>]+ \/>/g, '');

        // Update the img tags (opacity to 1 and add slowPan)
        content = content.replace(/style=\{\{ position: 'absolute', width: '100vw', height: '100vh', objectFit: 'cover', opacity: 0\.[46]5? \}\}/g,
            "style={{ position: 'absolute', width: '100vw', height: '100vh', objectFit: 'cover', opacity: 1, animation: 'slowPan 30s ease-in-out infinite' }}");

        // Update the overlay gradients
        content = content.replace(/background: 'linear-gradient\(to bottom, rgba\(255,255,255,0\.[12]\) 0%, rgba\(245,245,247,0\.85\) 100%\)', backdropFilter: 'blur\(\d+px\)'/g,
            "background: 'linear-gradient(to bottom, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.4) 100%)', backdropFilter: 'blur(0px)'");

        // Insert slowPan keyframes
        if (!content.includes('slowPan')) {
            content = content.replace(/<style>\{`/g, "<style>{`\n                @keyframes slowPan { 0%, 100% { transform: scale(1.05) translate(0, 0); } 50% { transform: scale(1.05) translate(-1.5%, -1.5%); } }");
        }

        fs.writeFileSync(fullPath, content);
    }
});
console.log("Updated images successfully!");
