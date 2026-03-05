'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, BarChart2, Map, MessageSquare, Wrench, Zap, Globe, Star, History } from 'lucide-react'
import { FloatChatLogo } from '@/components/Brand'
import Link from 'next/link'
import { apiClient, type ArgoSummaryStats } from '@/lib/api-client'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fadeUp: any = {
    hidden: { opacity: 0, y: 32 },
    visible: (i: number = 0) => ({
        opacity: 1, y: 0,
        transition: { duration: 0.65, delay: i * 0.08, ease: 'easeOut' }
    })
}

const FEATURES = [
    { icon: MessageSquare, label: 'AI Chat', title: 'Natural language ocean intelligence.', desc: 'Ask anything about ARGO data in plain English. AI retrieves and explains ocean measurements instantly.', href: '/chat', color: '#0071e3' },
    { icon: Map, label: 'Explorer', title: 'Explore every float on the planet.', desc: 'Interactive global map with real-time ARGO float positions, temperature, and salinity readings.', href: '/explorer', color: '#34c759' },
    { icon: BarChart2, label: 'Charts', title: 'Data that tells a beautiful story.', desc: 'Beautiful charts for temperature, salinity, and ocean layer analysis — built for researchers.', href: '/visualizations', color: '#ff9f0a' },
    { icon: Wrench, label: 'Tools', title: 'Professional oceanographic tools.', desc: 'Density calculators, glossary, timeline, and comparison utilities purpose-built for ocean science.', href: '/tools', color: '#5e5ce6' },
    { icon: History, label: 'Study', title: 'Versioned research workspaces.', desc: 'Create workspace versions, inspect snapshots, run restore dry-runs, and export reproducibility packages.', href: '/study', color: '#0ea5e9' },
]

// ── Shared liquid glass style ─────────────────────────────────────────────────
const glassCard: React.CSSProperties = {
    background: 'rgba(255,255,255,0.75)',
    backdropFilter: 'blur(72px) saturate(180%)',
    WebkitBackdropFilter: 'blur(72px) saturate(180%)',
    border: '1px solid rgba(255,255,255,0.95)',
    borderRadius: 28,
    boxShadow: '0 2px 0 rgba(255,255,255,1) inset, 0 10px 40px rgba(0,0,0,0.07)',
}

export default function Home() {
    const [stats, setStats] = useState<ArgoSummaryStats | null>(null)

    useEffect(() => {
        apiClient.getArgoSummaryStats().then(setStats).catch(() => { })
    }, [])

    return (
        <div style={{ backgroundColor: '#f5f5f7', minHeight: '100vh', overflowX: 'hidden', position: 'relative', fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif" }}>


            {/* ── Apple-like Animated 4K Liquid Ocean Background ── */}
            <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
                {/* Flowing Ocean Image (Animated) */}
                <div style={{
                    position: 'absolute', inset: 0,
                    backgroundImage: 'url(https://images.unsplash.com/photo-1505118380757-91f5f5632de0?q=80&w=3840&auto=format&fit=crop)',
                    backgroundSize: '120% 120%',
                    opacity: 1,
                    animation: 'oceanFlow 35s ease-in-out infinite'
                }} />

                {/* Delicate Frosted Glass Overlay */}
                <div style={{
                    position: 'absolute', inset: 0,
                    background: 'linear-gradient(to bottom, rgba(255,255,255,0.0) 0%, rgba(255,255,255,0.2) 100%)', backdropFilter: 'blur(0px)'
                }} />

                {/* Subtle light flares for depth */}
                <div style={{ position: 'absolute', width: 800, height: 800, top: -200, left: -200, borderRadius: '50%', background: 'radial-gradient(circle, rgba(230, 230, 235, 0.4) 0%, transparent 70%)', filter: 'blur(80px)' }} />
                <div style={{ position: 'absolute', width: 600, height: 600, top: '20%', right: -100, borderRadius: '50%', background: 'radial-gradient(circle, rgba(240, 240, 245, 0.5) 0%, transparent 70%)', filter: 'blur(80px)' }} />
            </div>



            {/* ── Hero ── */}
            <section style={{ position: 'relative', zIndex: 10, paddingTop: 60, paddingBottom: 80, textAlign: 'center', maxWidth: 900, margin: '0 auto', padding: '60px 24px 80px' }}>

                {/* Live badge */}
                <motion.div variants={{ hidden: { opacity: 0, y: -20 }, visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 200, damping: 20 } } }} initial="hidden" animate="visible"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '7px 16px', borderRadius: 99, marginBottom: 36, ...glassCard, boxShadow: '0 4px 20px rgba(0,0,0,0.07)' }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#34c759', display: 'inline-block', boxShadow: '0 0 10px rgba(52,199,89,0.7)' }} />
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#000' }}>
                        {stats?.active_floats?.toLocaleString() ?? '3,942'} ARGO floats live worldwide
                    </span>
                </motion.div>

                {/* Hero heading */}
                <motion.h1 variants={{ hidden: { opacity: 0, scale: 0.9, y: 40 }, visible: { opacity: 1, scale: 1, y: 0, transition: { type: 'spring', stiffness: 120, damping: 15, delay: 0.1 } } }} initial="hidden" animate="visible"
                    style={{ fontSize: 'clamp(3.5rem, 11vw, 7.5rem)', fontWeight: 900, letterSpacing: '-0.06em', lineHeight: 1.05, marginBottom: 28, color: '#000000', textShadow: '0 12px 40px rgba(0,0,0,0.1)' }}>
                    Ocean data,{' '}
                    <span style={{ color: '#0071e3' }}>reimagined.</span>
                </motion.h1>

                <motion.p variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6, delay: 0.2 } } }} initial="hidden" animate="visible"
                    style={{ fontSize: '1.3rem', lineHeight: 1.6, color: '#111', maxWidth: 650, margin: '0 auto 48px', fontWeight: 800, textShadow: '0 2px 10px rgba(255,255,255,0.9)' }}>
                    The most advanced AI-powered ocean intelligence platform.
                    ARGO float data — as accessible as a Google search.
                </motion.p>

                <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { duration: 0.6, delay: 0.3 } } }} initial="hidden" animate="visible"
                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, flexWrap: 'wrap' }}>
                    <Link href="/chat" style={{
                        display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 36px', borderRadius: 99,
                        background: '#000', color: '#fff', fontSize: 16, fontWeight: 800, textDecoration: 'none',
                        boxShadow: '0 12px 34px rgba(0,0,0,0.22)', letterSpacing: '-0.01em', transition: 'transform 0.2s',
                    }} onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.03)')} onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}>Ask AI Now <ArrowRight style={{ width: 16, height: 16 }} /></Link>
                    <Link href="/explorer" style={{
                        display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 36px', borderRadius: 99,
                        ...glassCard, color: '#000', fontSize: 16, fontWeight: 800, textDecoration: 'none', letterSpacing: '-0.01em', transition: 'transform 0.2s'
                    }} onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.03)')} onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}>Explore Map <Globe style={{ width: 16, height: 16 }} /></Link>
                </motion.div>

                {/* Stats */}
                <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={4}
                    style={{ display: 'flex', alignItems: 'stretch', justifyContent: 'center', gap: 16, flexWrap: 'wrap', marginTop: 56 }}>
                    {[
                        { label: 'Active Floats', value: stats?.active_floats?.toLocaleString() ?? '3,942' },
                        { label: 'Ocean Profiles', value: (stats?.total_profiles ?? 142000).toLocaleString() },
                        { label: 'Ocean Basins', value: '7' },
                    ].map(stat => (
                        <div key={stat.label} style={{ ...glassCard, padding: '20px 32px', textAlign: 'center', minWidth: 160 }}>
                            <div style={{ fontSize: '2rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000' }}>{stat.value}</div>
                            <div style={{ fontSize: 12, color: '#6e6e73', marginTop: 4, fontWeight: 600 }}>{stat.label}</div>
                        </div>
                    ))}
                </motion.div>
            </section>

            {/* ── Feature Cards ── */}
            <section style={{ position: 'relative', zIndex: 10, padding: '0 24px 60px', maxWidth: 1060, margin: '0 auto' }}>
                <motion.h2 variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }} custom={0}
                    style={{ fontSize: 'clamp(1.8rem, 4vw, 2.8rem)', fontWeight: 800, letterSpacing: '-0.04em', color: '#000', marginBottom: 24, textAlign: 'center' }}>
                    Everything you need.<br />
                    <span style={{ color: '#6e6e73', fontWeight: 400 }}>Nothing you don&apos;t.</span>
                </motion.h2>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 16 }}>
                    {FEATURES.map((f, i) => (
                        <motion.div key={f.label} variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }} custom={i}>
                            <Link href={f.href} style={{ textDecoration: 'none' }}>
                                <div style={{
                                    ...glassCard,
                                    padding: '28px 24px 24px',
                                    minHeight: 260,
                                    display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                                    cursor: 'pointer',
                                    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                                }}
                                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.transform = 'translateY(-4px)'; (e.currentTarget as HTMLElement).style.boxShadow = '0 2px 0 rgba(255,255,255,1) inset, 0 20px 60px rgba(0,0,0,0.10)'; }}
                                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.transform = 'translateY(0)'; (e.currentTarget as HTMLElement).style.boxShadow = glassCard.boxShadow as string; }}
                                >
                                    <div>
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
                                            <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: '#6e6e73' }}>{f.label}</span>
                                            <div style={{ width: 38, height: 38, borderRadius: 14, background: `${f.color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', border: `1px solid ${f.color}30` }}>
                                                <f.icon style={{ width: 16, height: 16, color: f.color }} />
                                            </div>
                                        </div>
                                        <h3 style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1.25, color: '#000', marginBottom: 10 }}>{f.title}</h3>
                                        <p style={{ fontSize: 13, lineHeight: 1.65, color: '#6e6e73' }}>{f.desc}</p>
                                    </div>
                                    <div style={{ marginTop: 20, display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 700, color: f.color }}>
                                        Open {f.label} <ArrowRight style={{ width: 13, height: 13 }} />
                                    </div>
                                </div>
                            </Link>
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* ── Tech banner ── */}
            <section style={{ position: 'relative', zIndex: 10, padding: '0 24px 80px', maxWidth: 1060, margin: '0 auto' }}>
                <div style={{ ...glassCard, padding: '48px 40px', textAlign: 'center', background: 'rgba(255,255,255,0.65)' }}>
                    <motion.h2 variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }} custom={0}
                        style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.04em', color: '#000', marginBottom: 28 }}>
                        The most advanced ocean AI stack ever assembled.
                    </motion.h2>
                    <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 10 }}>
                        {[
                            { icon: Zap, label: 'Ollama LLM' },
                            { icon: Star, label: 'Gemini Pro' },
                            { icon: Globe, label: 'ARGO API' },
                            { icon: BarChart2, label: 'ChromaDB' },
                            { icon: Map, label: 'BGC Floats' },
                        ].map((tech, i) => (
                            <motion.div key={tech.label} variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }} custom={i}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 99,
                                    background: 'rgba(255,255,255,0.8)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
                                    border: '1px solid rgba(255,255,255,0.95)',
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                                    fontSize: 13, fontWeight: 700, color: '#1d1d1f'
                                }}>
                                <tech.icon style={{ width: 14, height: 14, color: '#0071e3' }} />
                                {tech.label}
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── CTA ── */}
            <section style={{ position: 'relative', zIndex: 10, padding: '0 24px 100px', textAlign: 'center' }}>
                <motion.h2 variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }} custom={0}
                    style={{ fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 900, letterSpacing: '-0.05em', color: '#000', marginBottom: 20 }}>
                    The ocean has answers.<br />FloatChat has the key.
                </motion.h2>
                <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={{ once: true }} custom={1}>
                    <Link href="/dashboard" style={{
                        display: 'inline-flex', alignItems: 'center', gap: 8, padding: '16px 36px', borderRadius: 99,
                        background: '#000', color: '#fff', fontSize: 16, fontWeight: 800, textDecoration: 'none',
                        boxShadow: '0 10px 40px rgba(0,0,0,0.22)', letterSpacing: '-0.02em',
                    }}>
                        Get Started Free <ArrowRight style={{ width: 17, height: 17 }} />
                    </Link>
                </motion.div>
            </section>

            {/* Footer */}
            <footer style={{ position: 'relative', zIndex: 10, textAlign: 'center', padding: '24px', borderTop: '1px solid rgba(0,0,0,0.06)' }}>
                <p style={{ fontSize: 12, color: '#6e6e73', fontWeight: 500 }}>© 2025 FloatChat — AI Ocean Intelligence Platform</p>
            </footer>

            {/* Keyframes */}
            <style>{`
                @keyframes orb-drift-1 {
                    0%, 100% { transform: translate(0, 0) scale(1); }
                    33% { transform: translate(80px, -100px) scale(1.1); }
                    66% { transform: translate(-60px, 60px) scale(0.92); }
                }
                @keyframes orb-drift-2 {
                    0%, 100% { transform: translate(0, 0) scale(1); }
                    30% { transform: translate(-100px, 80px) scale(1.12); }
                    70% { transform: translate(70px, -50px) scale(0.9); }
                }
                @keyframes orb-drift-3 {
                    0%, 100% { transform: translate(0, 0) scale(1); }
                    40% { transform: translate(50px, 90px) scale(1.08); }
                    80% { transform: translate(-80px, -60px) scale(0.95); }
                }
            `}</style>
        </div >
    )
}
