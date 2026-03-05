const fs = require('fs');
const path = require('path');

const bgs = {
    'app/chat/page.tsx': 'https://images.unsplash.com/photo-1518182170546-076616fdcb18?q=80&w=3840&auto=format&fit=crop',
    'app/dashboard/page.tsx': 'https://images.unsplash.com/photo-1498623116890-37e912163d5d?q=80&w=3840&auto=format&fit=crop',
    'app/explorer/page.tsx': 'https://images.unsplash.com/photo-1542240578-1b60882e9643?q=80&w=3840&auto=format&fit=crop',
    'app/page.tsx': 'https://images.unsplash.com/photo-1505118380757-91f5f5632de0?q=80&w=3840&auto=format&fit=crop',
    'app/study/page.tsx': 'https://images.unsplash.com/photo-1473448912268-2022ce9509d8?q=80&w=3840&auto=format&fit=crop',
    'app/tools/page.tsx': 'https://images.unsplash.com/photo-1551244072-5d12893278ab?q=80&w=3840&auto=format&fit=crop',
    'app/visualizations/page.tsx': 'https://images.unsplash.com/photo-1518837695005-2083093ee35b?q=80&w=3840&auto=format&fit=crop'
};

for (const [file, img] of Object.entries(bgs)) {
    const fullPath = path.join(__dirname, file);
    if (!fs.existsSync(fullPath)) continue;

    let content = fs.readFileSync(fullPath, 'utf8');

    // Inject the animated background BEFORE the nav
    const backgroundMarkup = `
            {/* ── Apple-like Animated 4K Liquid Ocean Background ── */}
            <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
                {/* Flowing Ocean Image (Animated) */}
                <div style={{ 
                    position: 'absolute', inset: 0, 
                    backgroundImage: 'url(${img})',
                    backgroundSize: '120% 120%', 
                    opacity: 0.85,
                    animation: 'oceanFlow 35s ease-in-out infinite' 
                }} />
                
                {/* Delicate Frosted Glass Overlay */}
                <div style={{ 
                    position: 'absolute', inset: 0, 
                    background: 'linear-gradient(to bottom, rgba(255,255,255,0.05) 0%, rgba(245,245,247,0.85) 100%)', 
                    backdropFilter: 'blur(3px)' 
                }} />

                {/* Subtle light flares for depth */}
                <div style={{ position: 'absolute', width: 800, height: 800, top: -200, left: -200, borderRadius: '50%', background: 'radial-gradient(circle, rgba(230, 230, 235, 0.4) 0%, transparent 70%)', filter: 'blur(80px)' }} />
                <div style={{ position: 'absolute', width: 600, height: 600, top: '20%', right: -100, borderRadius: '50%', background: 'radial-gradient(circle, rgba(240, 240, 245, 0.5) 0%, transparent 70%)', filter: 'blur(80px)' }} />
            </div>
`;
    // Replace the old neutral silver wisps section entirely
    content = content.replace(/\{\/\* ── Neutral Apple-style silver wisps \(no blue tint\) ── \*\/\}\s*<div style=\{\{ position: 'fixed', inset: 0[^]+?<\/div>\s*<\/div>/, backgroundMarkup.trim());

    fs.writeFileSync(fullPath, content);
}

console.log('Background animations added!');
