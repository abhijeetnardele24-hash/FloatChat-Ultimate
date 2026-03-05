'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { Activity, Database, Gauge, Layers, MessageSquare } from 'lucide-react'
import { FloatChatLogo } from '@/components/Brand'
import { apiClient, type AdminMetricsSummaryResponse, type AdminSloResponse, type ArgoSummaryStats } from '@/lib/api-client'

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif"

const GLASS: React.CSSProperties = {
    background: 'rgba(255,255,255,0.72)',
    backdropFilter: 'blur(72px) saturate(180%)',
    WebkitBackdropFilter: 'blur(72px) saturate(180%)',
    border: '1px solid rgba(255,255,255,0.95)',
    borderRadius: 24,
    boxShadow: '0 2px 0 rgba(255,255,255,1) inset, 0 10px 40px rgba(0,0,0,0.07)',
}

const ROW: React.CSSProperties = {
    background: 'rgba(255,255,255,0.55)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    border: '1px solid rgba(255,255,255,0.8)',
    borderRadius: 14,
    padding: '10px 14px',
}

function providerStatusLabel(health: Record<string, unknown> | null, key: string): string {
    if (!health) return 'unknown'
    const value = health[key]
    if (!value || typeof value !== 'object') return 'unknown'
    const typed = value as { available?: unknown; status?: unknown }
    const status = typeof typed.status === 'string' ? typed.status : 'unknown'
    const available = typeof typed.available === 'boolean' ? typed.available : null
    if (available === null) return status
    return `${available ? 'online' : 'offline'} (${status})`
}

function safePercent(value?: number | null): string {
    if (typeof value !== 'number' || Number.isNaN(value)) return 'n/a'
    return `${value.toFixed(2)}%`
}

function safeMs(value?: number | null): string {
    if (typeof value !== 'number' || Number.isNaN(value)) return 'n/a'
    return `${value.toFixed(0)} ms`
}

export default function DashboardPage() {
    const [stats, setStats] = useState<ArgoSummaryStats | null>(null)
    const [providers, setProviders] = useState<Record<string, unknown> | null>(null)
    const [adminMetrics, setAdminMetrics] = useState<AdminMetricsSummaryResponse | null>(null)
    const [slo, setSlo] = useState<AdminSloResponse | null>(null)
    const [adminError, setAdminError] = useState<string | null>(null)

    useEffect(() => {
        apiClient.getArgoSummaryStats().then(setStats).catch(() => setStats(null))
        apiClient.getChatProviders().then((response) => {
            setProviders((response.health ?? null) as Record<string, unknown> | null)
        }).catch(() => setProviders(null))
        apiClient.getAdminMetricsSummary({ windowMinutes: 180, includeRecentEvents: 10 }).then((response) => {
            setAdminMetrics(response)
            setAdminError(null)
        }).catch((error) => {
            setAdminMetrics(null)
            setAdminError(error instanceof Error ? error.message : 'Unavailable')
        })
        apiClient.getAdminSloStatus({ windowMinutes: 180 }).then((response) => {
            setSlo(response)
        }).catch(() => setSlo(null))
    }, [])

    const cards = useMemo(() => ([
        { title: 'Total Floats', value: stats?.total_floats?.toLocaleString() ?? 'n/a', subtitle: 'ARGO fleet indexed', icon: Layers, color: '#0071e3' },
        { title: 'Active Floats', value: stats?.active_floats?.toLocaleString() ?? 'n/a', subtitle: 'Live status', icon: Activity, color: '#34c759' },
        { title: 'Total Profiles', value: stats?.total_profiles?.toLocaleString() ?? 'n/a', subtitle: `Chat p95 ${safeMs(adminMetrics?.chat.latency_ms.p95)}`, icon: Database, color: '#ff9f0a' },
        { title: 'Total Measurements', value: stats?.total_measurements?.toLocaleString() ?? 'n/a', subtitle: `Success ${safePercent(adminMetrics?.chat.success_rate)}`, icon: Gauge, color: '#5e5ce6' },
    ]), [adminMetrics?.chat.latency_ms.p95, adminMetrics?.chat.success_rate, stats?.active_floats, stats?.total_floats, stats?.total_measurements, stats?.total_profiles])

    return (
        <div style={{ backgroundColor: '#f5f5f7', minHeight: '100vh', fontFamily: FONT, position: 'relative', overflowX: 'hidden' }}>


            {/* ── Apple-like Animated 4K Liquid Ocean Background ── */}
            <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
                {/* Flowing Ocean Image (Animated) */}
                <div style={{ 
                    position: 'absolute', inset: 0, 
                    backgroundImage: 'url(https://images.unsplash.com/photo-1498623116890-37e912163d5d?q=80&w=3840&auto=format&fit=crop)',
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

            

            {/* ── Main ── */}
            <main style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px 60px', position: 'relative', zIndex: 10, display: 'flex', flexDirection: 'column', gap: 20 }}>

                {/* Page title */}
                <div style={{ marginBottom: 4 }}>
                    <h1 style={{ fontSize: 'clamp(1.6rem, 3vw, 2.2rem)', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 4 }}>Dashboard</h1>
                    <p style={{ fontSize: 14, color: '#6e6e73', fontWeight: 500 }}>Live ARGO float metrics & backend health</p>
                </div>

                {/* ── KPI Cards ── */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
                    {cards.map(card => (
                        <div key={card.title} style={{ ...GLASS, padding: '22px 22px 18px' }}>
                            <div style={{ width: 36, height: 36, borderRadius: 12, background: `${card.color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14, border: `1px solid ${card.color}28` }}>
                                <card.icon style={{ width: 16, height: 16, color: card.color }} />
                            </div>
                            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#6e6e73', marginBottom: 6 }}>{card.title}</p>
                            <p style={{ fontSize: '1.9rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', lineHeight: 1, marginBottom: 6 }}>{card.value}</p>
                            <p style={{ fontSize: 12, color: '#6e6e73', fontWeight: 500 }}>{card.subtitle}</p>
                        </div>
                    ))}
                </div>

                {/* ── Runtime + Provider ── */}
                <div style={{ display: 'grid', gridTemplateColumns: '1.35fr 1fr', gap: 16 }}>
                    {/* Backend Runtime */}
                    <div style={{ ...GLASS, padding: '22px' }}>
                        <h2 style={{ fontSize: 13, fontWeight: 800, letterSpacing: '-0.01em', color: '#000', marginBottom: 16 }}>Backend Runtime</h2>
                        {adminError && (
                            <p style={{ marginBottom: 12, padding: '10px 14px', borderRadius: 12, background: 'rgba(255,59,48,0.06)', border: '1px solid rgba(255,59,48,0.2)', fontSize: 12, color: '#c0392b' }}>
                                Admin metrics unavailable: {adminError}
                            </p>
                        )}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                            {[
                                { label: 'Chat requests', value: adminMetrics?.chat.total_requests?.toLocaleString() ?? 'n/a' },
                                { label: 'Success rate', value: safePercent(adminMetrics?.chat.success_rate) },
                                { label: 'Cache hit rate', value: safePercent(adminMetrics?.chat.cache_hit_rate) },
                                { label: 'Latency p50', value: safeMs(adminMetrics?.chat.latency_ms.p50) },
                                { label: 'Latency p95', value: safeMs(adminMetrics?.chat.latency_ms.p95) },
                                { label: 'Latency avg', value: safeMs(adminMetrics?.chat.latency_ms.avg) },
                                { label: 'DB probe latency', value: safeMs(adminMetrics?.database.probe_latency_ms) },
                                { label: 'Ingestion jobs', value: String(adminMetrics?.ingestion.total_jobs ?? 'n/a') },
                                { label: 'Ingestion available', value: String(adminMetrics?.ingestion.available ?? false) },
                                { label: 'Service uptime', value: typeof adminMetrics?.service?.uptime_seconds === 'number' ? `${adminMetrics.service.uptime_seconds}s` : 'n/a' },
                            ].map(row => (
                                <div key={row.label} style={ROW}>
                                    <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#6e6e73', marginBottom: 4 }}>{row.label}</p>
                                    <p style={{ fontSize: 15, fontWeight: 800, color: '#000', letterSpacing: '-0.02em' }}>{row.value}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Provider Health */}
                    <div style={{ ...GLASS, padding: '22px' }}>
                        <h2 style={{ fontSize: 13, fontWeight: 800, letterSpacing: '-0.01em', color: '#000', marginBottom: 16 }}>Provider Health</h2>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {(['ollama', 'openai', 'gemini', 'rag'] as const).map(key => {
                                const raw = providers?.[key] as { available?: boolean } | undefined
                                const avail = typeof raw?.available === 'boolean' ? raw.available : null
                                const label = providerStatusLabel(providers, key)
                                return (
                                    <div key={key} style={{ ...ROW, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <span style={{ fontSize: 13, fontWeight: 700, color: '#000', textTransform: 'capitalize' }}>{key}</span>
                                        <span style={{ fontSize: 12, fontWeight: 600, color: avail === true ? '#1d7d3a' : avail === false ? '#c0392b' : '#6e6e73' }}>{label}</span>
                                    </div>
                                )
                            })}
                        </div>
                        <div style={{ marginTop: 12, padding: '12px 14px', borderRadius: 14, background: 'rgba(0,0,0,0.03)', border: '1px solid rgba(0,0,0,0.05)' }}>
                            <p style={{ fontSize: 12, fontWeight: 700, color: '#000', marginBottom: 8 }}>What is linked</p>
                            {['Chat provider routing & health', 'Admin metrics (latency/cache/success)', 'Ingestion status counters', 'ARGO dataset summary stats'].map(item => (
                                <p key={item} style={{ fontSize: 12, color: '#6e6e73', marginBottom: 4 }}>· {item}</p>
                            ))}
                        </div>
                    </div>
                </div>

                {/* ── Recent Events ── */}
                <div style={{ ...GLASS, padding: '22px' }}>
                    <h2 style={{ fontSize: 13, fontWeight: 800, letterSpacing: '-0.01em', color: '#000', marginBottom: 4 }}>Recent Backend Events</h2>
                    <p style={{ fontSize: 12, color: '#6e6e73', marginBottom: 14 }}>Latest calls captured by in-memory backend metrics.</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {(adminMetrics?.chat.recent_events ?? []).slice(0, 8).map((event, idx) => (
                            <div key={`${event.timestamp}-${idx}`} style={{ ...ROW, display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1.5fr 1fr 1fr', gap: 8, alignItems: 'center' }}>
                                <span style={{ fontSize: 11, color: '#6e6e73' }}>{new Date(event.timestamp).toLocaleString()}</span>
                                <span style={{ fontSize: 11, fontWeight: 700, color: '#0071e3', textTransform: 'capitalize' }}>{event.requested_provider}</span>
                                <span style={{ fontSize: 11, color: '#3a3a3c' }}>{event.source}</span>
                                <span style={{ fontSize: 11, color: '#3a3a3c' }}>{event.intent}</span>
                                <span style={{ fontSize: 11, color: '#6e6e73' }}>{event.latency_ms} ms</span>
                                <span style={{ fontSize: 11, fontWeight: 700, color: event.success ? '#1d7d3a' : '#c0392b' }}>{event.success ? '✓ ok' : '✗ fail'}</span>
                            </div>
                        ))}
                        {(adminMetrics?.chat.recent_events ?? []).length === 0 && (
                            <p style={{ fontSize: 13, color: '#6e6e73', padding: '12px 0', textAlign: 'center' }}>No recent events yet.</p>
                        )}
                    </div>
                </div>

                {/* ── SLO Status ── */}
                <div style={{ ...GLASS, padding: '22px' }}>
                    <h2 style={{ fontSize: 13, fontWeight: 800, letterSpacing: '-0.01em', color: '#000', marginBottom: 4 }}>SLO Status</h2>
                    <p style={{ fontSize: 12, color: '#6e6e73', marginBottom: 14 }}>Backend SLO checks from /api/admin/metrics/slo</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <div style={{ padding: '10px 14px', borderRadius: 12, background: slo?.overall_ok ? 'rgba(52,199,89,0.08)' : 'rgba(255,159,10,0.08)', border: `1px solid ${slo?.overall_ok ? 'rgba(52,199,89,0.25)' : 'rgba(255,159,10,0.25)'}`, fontSize: 13, fontWeight: 700, color: slo?.overall_ok ? '#1d7d3a' : '#b36a00' }}>
                            overall_ok: {String(Boolean(slo?.overall_ok))}
                        </div>
                        {(slo?.checks ?? []).map(check => (
                            <div key={check.name} style={ROW}>
                                <p style={{ fontSize: 13, fontWeight: 700, color: '#000', marginBottom: 2 }}>{check.name}</p>
                                <p style={{ fontSize: 12, color: '#6e6e73' }}>target: {check.target} · ok: {String(check.ok)}</p>
                            </div>
                        ))}
                        {(slo?.checks ?? []).length === 0 && <p style={{ fontSize: 13, color: '#6e6e73' }}>SLO checks unavailable.</p>}
                    </div>
                </div>

                {/* ── CTA ── */}
                <div style={{ ...GLASS, padding: '22px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                        <h2 style={{ fontSize: 13, fontWeight: 800, color: '#000', marginBottom: 4 }}>Next frontier</h2>
                        <p style={{ fontSize: 12, color: '#6e6e73' }}>Study workspace versions & reproducibility endpoints are live in the backend.</p>
                    </div>
                    <Link href="/chat" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 22px', borderRadius: 99, background: '#000', color: '#fff', fontSize: 13, fontWeight: 700, textDecoration: 'none', letterSpacing: '-0.01em', boxShadow: '0 4px 14px rgba(0,0,0,0.2)', flexShrink: 0 }}>
                        <MessageSquare style={{ width: 14, height: 14 }} />
                        Open Chat
                    </Link>
                </div>
            </main>

            <style>{`
                @keyframes drift1 { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(70px,-90px) scale(1.08)} 66%{transform:translate(-50px,50px) scale(0.94)} }
                @keyframes drift2 { 0%,100%{transform:translate(0,0) scale(1)} 30%{transform:translate(-90px,70px) scale(1.1)} 70%{transform:translate(60px,-40px) scale(0.92)} }
                @keyframes drift3 { 0%,100%{transform:translate(0,0) scale(1)} 40%{transform:translate(40px,80px) scale(1.06)} 80%{transform:translate(-70px,-50px) scale(0.96)} }
            `}</style>
        </div>
    )
}
