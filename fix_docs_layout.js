const fs = require('fs');

const file = 'app/docs/page.tsx';
let content = fs.readFileSync(file, 'utf8');

// fix main layout max width
content = content.replace(
    /<div style={{ position: 'relative', zIndex: 10, maxWidth: 1000, margin: '0 auto', padding: '120px 20px 60px' }}>/g,
    "<div style={{ position: 'relative', zIndex: 10, maxWidth: 1200, margin: '0 auto', padding: '120px 20px 60px' }}>"
);

// fix grid layout
content = content.replace(
    /<div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 32 }}>/g,
    "<div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 32, alignItems: 'start' }}>"
);

// fix sidebar position and padding
content = content.replace(
    /style={{ \.\.\.GLASS, borderRadius: 24, padding: '24px 20px', height: 'fit-content' }}>/g,
    "style={{ ...GLASS, borderRadius: 24, padding: '24px 20px', position: 'sticky', top: 100 }}>"
);

// fix getting started buttons
content = content.replace(
    /\{key\} style=\{\{ padding: '10px 12px', borderRadius: 12, fontSize: 14, fontWeight: i === 0 \? 700 : 500, color: i === 0 \? '#0071e3' : '#4a4a4c', background: i === 0 \? 'rgba\(0,113,227,0\.08\)' : 'transparent', cursor: 'pointer' \}\}>\s*\{link\}\s*<\/div>/g,
    `{key} style={{ padding: '10px 12px', borderRadius: 12, fontSize: 14, fontWeight: i === 0 ? 700 : 500, border: 'none', color: i === 0 ? '#0071e3' : '#4a4a4c', background: i === 0 ? 'rgba(0,113,227,0.08)' : 'transparent', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s', width: '100%', fontFamily: FONT }} onMouseEnter={(e) => { if(i !== 0) e.currentTarget.style.background = 'rgba(0,0,0,0.04)'; e.currentTarget.style.color = i === 0 ? '#0071e3' : '#000' }} onMouseLeave={(e) => { if(i !== 0) e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = i === 0 ? '#0071e3' : '#4a4a4c' }}>
                                    {link}
                                </button>`
).replace(/<div key=\{i\} style=\{\{ padding: '10px 12px', borderRadius: 12, fontSize: 14, fontWeight: i === 0 \? 700 : 500, color: i === 0 \? '#0071e3' : '#4a4a4c', background: i === 0 \? 'rgba\(0,113,227,0\.08\)' : 'transparent', cursor: 'pointer' \}\}>/g,
    `<button key={i} style={{ padding: '10px 12px', borderRadius: 12, fontSize: 14, fontWeight: i === 0 ? 700 : 500, border: 'none', color: i === 0 ? '#0071e3' : '#4a4a4c', background: i === 0 ? 'rgba(0,113,227,0.08)' : 'transparent', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s', width: '100%', fontFamily: FONT }} onMouseEnter={(e) => { if(i !== 0) e.currentTarget.style.background = 'rgba(0,0,0,0.04)'; e.currentTarget.style.color = i === 0 ? '#0071e3' : '#000' }} onMouseLeave={(e) => { if(i !== 0) e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = i === 0 ? '#0071e3' : '#4a4a4c' }}>`
).replace(/<\/div>\s*\}\)\}\s*<\/div>\s*<h3/g, `</button>
                            ))}
                        </div>

                        <h3`);

// fix core concepts buttons
content = content.replace(
    /<div key=\{i\} style=\{\{ padding: '10px 12px', borderRadius: 12, fontSize: 14, fontWeight: 500, color: '#4a4a4c', cursor: 'pointer' \}\}>/g,
    `<button key={i} style={{ padding: '10px 12px', borderRadius: 12, fontSize: 14, fontWeight: 500, border: 'none', color: '#4a4a4c', background: 'transparent', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s', width: '100%', fontFamily: FONT }} onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(0,0,0,0.04)'; e.currentTarget.style.color = '#000' }} onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#4a4a4c' }}>`
);

// fix button closing
content = content.replace(/<\/button>\s*<\/div>\s*\}\)\}\s*<\/div>\s*<\/motion.div>/g,
    `</button>
                            ))}
                        </div>
                    </motion.div>`);
content = content.replace(/\{link\}\s*<\/div>\s*\}\)\}\s*<\/div>\s*<\/motion.div>/g,
    `{link}
                                </button>
                            ))}
                        </div>
                    </motion.div>`);

// fix overflow on content
content = content.replace(
    /style={{ \.\.\.GLASS, borderRadius: 32, padding: '48px 40px' }}>/g,
    "style={{ ...GLASS, borderRadius: 32, padding: '48px 40px', overflow: 'hidden' }}>"
);

// fix wrap pre
content = content.replace(
    /fontSize: 14, lineHeight: 1\.5 }}>/g,
    "fontSize: 14, lineHeight: 1.5, whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>"
);

fs.writeFileSync(file, content);
console.log('Fixed docs layout!');
