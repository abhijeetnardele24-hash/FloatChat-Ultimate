'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { OceanAIBadge, FloatChatLogo } from '@/components/Brand'
import { apiClient } from '@/lib/api-client'
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { motion } from 'framer-motion'

const FONT = "var(--font-inter), -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif"

// ── Apple Design System Colors ───────────────────────────────────────────
const APPLE_BG_SIDEBAR = '#ffffff'
const APPLE_BG_HOVER = '#f5f5f7'
const APPLE_TEXT = '#1d1d1f'
const APPLE_SUBTEXT = '#86868b'
const APPLE_BLUE = '#0071e3'

function StatusDot({ status }: { status: 'checking' | 'online' | 'degraded' | 'offline' }) {
    const colors: Record<string, string> = { checking: '#ff9f0a', online: '#34c759', degraded: '#ff9f0a', offline: '#ff3b30' }
    return <span style={{ width: 8, height: 8, borderRadius: '50%', background: colors[status] ?? '#ccc', display: 'inline-block' }} />
}

export default function Sidebar() {
    const pathname = usePathname()
    const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'degraded' | 'offline'>('checking')
    const [isCollapsed, setIsCollapsed] = useState(false)

    useEffect(() => {
        let mounted = true
        async function load() {
            try {
                const health = await apiClient.healthCheck()
                if (!mounted) return
                setBackendStatus(health.status === 'healthy' ? 'online' : 'degraded')
            } catch {
                if (mounted) setBackendStatus('offline')
            }
        }
        void load()
        return () => { mounted = false }
    }, [])

    return (
        <div style={{ position: 'relative', height: '100%', zIndex: 50 }}>
            {/* The Sidebar Container */}
            <motion.div
                initial={false}
                animate={{ width: isCollapsed ? 0 : 250 }}
                transition={{ type: 'spring', damping: 28, stiffness: 220 }}
                style={{
                    height: '100%',
                    display: 'flex', flexDirection: 'column',
                    borderRight: '1px solid rgba(0,0,0,0.06)',
                    background: APPLE_BG_SIDEBAR,
                    flexShrink: 0,
                    overflow: 'hidden', position: 'relative'
                }}
            >
                <div style={{ width: 250, padding: '24px 20px', display: 'flex', flexDirection: 'column', gap: 28, height: '100%', overflowY: 'auto', flexShrink: 0 }}>
                    {/* Header Logo */}
                    <div style={{ padding: '0 8px' }}>
                        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
                            <FloatChatLogo size={18} color={APPLE_BLUE} />
                            <span style={{ fontSize: 14, fontWeight: 700, color: APPLE_TEXT, letterSpacing: '-0.02em', fontFamily: FONT }}>FloatChat</span>
                        </Link>
                    </div>

                    {/* Navigation */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {[{ label: 'Home', href: '/' }, { label: 'Chat', href: '/chat' }, { label: 'Explorer', href: '/explorer' }, { label: 'Charts', href: '/visualizations' }, { label: 'Tools', href: '/tools' }, { label: 'Study', href: '/study' }, { label: 'Docs', href: '/docs' }].map(link => {
                            const active = (link.href === '/' && pathname === '/') || (link.href !== '/' && pathname?.startsWith(link.href))
                            return (
                                <Link key={link.label} href={link.href} style={{
                                    textDecoration: 'none', padding: '10px 14px', borderRadius: 10, fontSize: 14, fontWeight: active ? 600 : 500,
                                    color: active ? APPLE_TEXT : APPLE_SUBTEXT,
                                    background: active ? APPLE_BG_HOVER : 'transparent',
                                    transition: 'all 0.15s', fontFamily: FONT
                                }}
                                    onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = APPLE_BG_HOVER; e.currentTarget.style.color = APPLE_TEXT }}
                                    onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = APPLE_SUBTEXT }}
                                >
                                    {link.label}
                                </Link>
                            )
                        })}
                    </div>

                    <div style={{ flex: 1 }} />

                    {/* Dashboard Button */}
                    <Link href="/dashboard" style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                        padding: '12px', borderRadius: 12, background: APPLE_BG_HOVER, color: APPLE_TEXT,
                        fontSize: 13, fontWeight: 600, textDecoration: 'none',
                        transition: 'background 0.2s', fontFamily: FONT
                    }}
                        onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(0,0,0,0.08)' }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = APPLE_BG_HOVER }}>
                        Dashboard
                    </Link>

                    {/* Backend Status Box */}
                    <div style={{ border: '1px solid rgba(0,0,0,0.06)', borderRadius: 14, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10, fontFamily: FONT }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, borderRadius: 8, background: APPLE_BG_HOVER }}>
                                <OceanAIBadge size={16} />
                            </div>
                            <div>
                                <p style={{ fontSize: 13, fontWeight: 600, color: APPLE_TEXT, margin: '0 0 2px', lineHeight: 1 }}>Ocean AI</p>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                                    <StatusDot status={backendStatus} />
                                    <span style={{ fontSize: 11, color: APPLE_SUBTEXT, fontWeight: 500, textTransform: 'capitalize' }}>{backendStatus}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </motion.div>

            {/* Toggle Button */}
            <motion.button
                onClick={() => setIsCollapsed(!isCollapsed)}
                initial={false}
                animate={{ left: isCollapsed ? 16 : 266 }}
                transition={{ type: 'spring', damping: 28, stiffness: 220 }}
                style={{
                    position: 'absolute',
                    top: 24,
                    zIndex: 100,
                    width: 32, height: 32,
                    borderRadius: 16,
                    background: '#ffffff',
                    border: '1px solid rgba(0,0,0,0.08)',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    cursor: 'pointer',
                    color: APPLE_SUBTEXT
                }}
                onMouseEnter={e => { e.currentTarget.style.color = APPLE_TEXT; e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = APPLE_SUBTEXT; e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)'; }}
            >
                {isCollapsed ? <PanelLeftOpen style={{ width: 14, height: 14 }} /> : <PanelLeftClose style={{ width: 14, height: 14 }} />}
            </motion.button>
        </div>
    )
}
