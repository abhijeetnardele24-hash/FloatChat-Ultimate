'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import { FloatChatLogo } from '@/components/Brand'

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif"

const GLASS: React.CSSProperties = {
    background: 'rgba(255,255,255,0.72)',
    backdropFilter: 'blur(72px) saturate(180%)',
    WebkitBackdropFilter: 'blur(72px) saturate(180%)',
    border: '1px solid rgba(255,255,255,0.95)',
    boxShadow: '0 2px 0 rgba(255,255,255,1) inset, 0 10px 40px rgba(0,0,0,0.07)',
}

const LINKS = [
    { label: 'Chat', href: '/chat' },
    { label: 'Explorer', href: '/explorer' },
    { label: 'Charts', href: '/visualizations' },
    { label: 'Tools', href: '/tools' },
    { label: 'Study', href: '/study' },
    { label: 'Docs', href: '/docs' }
];

export default function GlobalNav() {
    const pathname = usePathname();

    if (pathname === '/chat') return null;

    return (
        <div style={{ position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)', zIndex: 9999, width: '92%', maxWidth: 1000, fontFamily: FONT }}>
            <motion.div initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                style={{
                    ...GLASS,
                    background: 'rgba(255,255,255,0.5)',
                    borderRadius: 99,
                    padding: '12px 24px',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>

                {/* Logo & Brand in Corner */}
                <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', padding: '4px 8px', borderRadius: 12, transition: 'background 0.2s' }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.04)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                    <FloatChatLogo size={18} />
                    <span style={{ fontSize: 13, fontWeight: 800, color: '#000', letterSpacing: '-0.02em' }}>FloatChat</span>
                </Link>

                {/* Tabs */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(0,0,0,0.02)', padding: '4px', borderRadius: 99 }}>
                    {LINKS.map(item => {
                        const isActive = pathname === item.href;
                        return (
                            <Link key={item.label} href={item.href} style={{ position: 'relative', textDecoration: 'none' }}>
                                {isActive && (
                                    <motion.div layoutId="nav-pill" transition={{ type: 'spring', bounce: 0.15, duration: 0.5 }}
                                        style={{ position: 'absolute', inset: 0, background: '#fff', borderRadius: 99, boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }} />
                                )}
                                <div style={{
                                    position: 'relative', zIndex: 1, padding: '8px 18px', fontSize: 13,
                                    fontWeight: isActive ? 700 : 600,
                                    color: isActive ? '#000' : '#6e6e73',
                                    transition: 'color 0.2s ease', fontFamily: FONT
                                }}>
                                    {item.label}
                                </div>
                            </Link>
                        );
                    })}
                </div>

                {/* CTA */}
                <Link href="/dashboard" style={{
                    display: 'inline-flex', alignItems: 'center', gap: 8,
                    padding: '10px 24px', borderRadius: 99,
                    background: pathname === '/dashboard' ? '#0071e3' : '#1d1d1f', color: '#fff',
                    fontSize: 13, fontWeight: 700, textDecoration: 'none',
                    boxShadow: '0 4px 14px rgba(0,0,0,0.15)', letterSpacing: '-0.01em',
                    transition: 'transform 0.2s ease, background 0.2s ease',
                }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = pathname === '/dashboard' ? '#0077ed' : '#000'; (e.currentTarget as HTMLElement).style.transform = 'scale(1.02)' }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = pathname === '/dashboard' ? '#0071e3' : '#1d1d1f'; (e.currentTarget as HTMLElement).style.transform = 'scale(1)' }}>
                    Dashboard <ArrowRight style={{ width: 14, height: 14 }} />
                </Link>

            </motion.div>
        </div>
    )
} 
