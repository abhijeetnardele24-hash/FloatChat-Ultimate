const fs = require('fs');

let code = fs.readFileSync('app/page.tsx', 'utf8');

const regex = /\{\/\* ── Floating Glass Nav Pill ── \*\/\}[\s\S]*?(?=\{\/\* ── Hero ── \*\/})/g;

const newNav = `            {/* ── Floating Nav Pill ── */}
            <motion.div initial={{ y: -100, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
                style={{ position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)', zIndex: 50, width: '92%', maxWidth: 1000 }}>
                <div style={{
                    ...glassCard,
                    background: 'rgba(255,255,255,0.4)',
                    borderRadius: 99,
                    padding: '12px 24px',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                    {/* Logo */}
                    <Link href="/" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}>
                        <FloatChatLogo size={18} />
                    </Link>

                    {/* Links */}
                    <div className="nav-links" style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
                        {[{ label: 'Chat', href: '/chat' }, { label: 'Explorer', href: '/explorer' }, { label: 'Charts', href: '/visualizations' }, { label: 'Tools', href: '/tools' }, { label: 'Study', href: '/study' }, { label: 'Docs', href: '#docs' }].map(item => (
                            <Link key={item.label} href={item.href} style={{ fontSize: 13, fontWeight: 700, color: '#4a4a4c', textDecoration: 'none', transition: 'color 0.2s ease' }}
                                onMouseEnter={(e) => (e.target).style.color = '#000'} onMouseLeave={(e) => (e.target).style.color = '#4a4a4c'}>
                                {item.label}
                            </Link>
                        ))}
                    </div>

                    {/* CTA */}
                    <Link href="/dashboard" style={{
                        display: 'inline-flex', alignItems: 'center', gap: 8,
                        padding: '10px 24px', borderRadius: 99,
                        background: '#1d1d1f', color: '#fff',
                        fontSize: 13, fontWeight: 700, textDecoration: 'none',
                        boxShadow: '0 4px 14px rgba(0,0,0,0.15)', letterSpacing: '-0.01em',
                        transition: 'transform 0.2s ease, background 0.2s ease',
                    }}
                    onMouseEnter={(e) => { (e.target).style.background = '#000'; (e.target).style.transform = 'scale(1.02)' }}
                    onMouseLeave={(e) => { (e.target).style.background = '#1d1d1f'; (e.target).style.transform = 'scale(1)' }}
                    >
                        Dashboard <ArrowRight style={{ width: 14, height: 14 }} />
                    </Link>
                </div>
            </motion.div>

            `;

code = code.replace(regex, newNav);
fs.writeFileSync('app/page.tsx', code);
console.log('Fixed nav pill in page.tsx');
