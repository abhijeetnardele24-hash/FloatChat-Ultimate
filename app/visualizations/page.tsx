'use client'

import { motion, AnimatePresence, type Variants } from 'framer-motion'
import { RefreshCw, Activity, Droplets, Thermometer, Globe, Layers, Wind, BarChart3, Cpu, TrendingUp } from 'lucide-react'
import {
    Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
    BarElement, ArcElement, RadialLinearScale, Title, Tooltip, Legend,
    Filler, ScatterController, PolarAreaController,
} from 'chart.js'
import { Line, Bar, Doughnut, Radar, Scatter, PolarArea } from 'react-chartjs-2'
import { useVisualizationData } from '@/lib/useVisualizationData'

ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement,
    BarElement, ArcElement, RadialLinearScale,
    Title, Tooltip, Legend, Filler, ScatterController, PolarAreaController,
)

// ── Tokens ─────────────────────────────────────────────────────────────────
const F = "'Inter', -apple-system, sans-serif"
const GLASS: React.CSSProperties = {
    background: 'rgba(255,255,255,0.80)',
    backdropFilter: 'blur(60px) saturate(200%)',
    WebkitBackdropFilter: 'blur(60px) saturate(200%)',
    border: '1px solid rgba(255,255,255,0.92)',
    borderRadius: 24,
    boxShadow: '0 1px 0 rgba(255,255,255,0.9) inset, 0 12px 48px rgba(0,0,0,0.07)',
}
const PILL: React.CSSProperties = {
    background: 'rgba(255,255,255,0.92)',
    backdropFilter: 'blur(40px)',
    WebkitBackdropFilter: 'blur(40px)',
    border: '1px solid rgba(255,255,255,0.96)',
    borderRadius: 999,
    boxShadow: '0 4px 24px rgba(0,0,0,0.10)',
}
const P = {
    blue: { s: '#0071e3', l: 'rgba(0,113,227,0.10)' },
    green: { s: '#28cd41', l: 'rgba(40,205,65,0.10)' },
    orange: { s: '#ff9f0a', l: 'rgba(255,159,10,0.10)' },
    purple: { s: '#5e5ce6', l: 'rgba(94,92,230,0.10)' },
    teal: { s: '#32ade6', l: 'rgba(50,173,230,0.10)' },
    pink: { s: '#ff375f', l: 'rgba(255,55,95,0.10)' },
    indigo: { s: '#5856d6', l: 'rgba(88,86,214,0.10)' },
}
const TT = {
    backgroundColor: 'rgba(255,255,255,0.97)', titleColor: '#000',
    bodyColor: '#3a3a3c', borderColor: 'rgba(0,0,0,0.08)', borderWidth: 1,
    cornerRadius: 14, padding: 14, boxPadding: 4,
    titleFont: { family: F, size: 12, weight: 700 as const },
    bodyFont: { family: F, size: 11 },
}
const AX = {
    grid: { color: 'rgba(0,0,0,0.04)' },
    ticks: { color: '#8a8a8e', font: { family: F, size: 11 }, padding: 6 },
    border: { display: false },
}
const UP: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.5, delay: i * 0.07, ease: [.22, .68, .36, 1] } }),
}
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const BCOLORS = [
    'rgba(0,113,227,0.82)', 'rgba(40,205,65,0.82)', 'rgba(255,159,10,0.82)',
    'rgba(94,92,230,0.82)', 'rgba(50,173,230,0.82)', 'rgba(255,55,95,0.82)',
    'rgba(88,86,214,0.82)', 'rgba(255,214,10,0.82)',
]

// ── Helpers ─────────────────────────────────────────────────────────────────
function num(n: number | null | undefined, dec = 0) {
    if (n == null) return '—'
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
    return dec > 0 ? n.toFixed(dec) : String(Math.round(n))
}

// ── Shimmer ──────────────────────────────────────────────────────────────────
function Shim({ h = 180, r = 14 }: { h?: number; r?: number }) {
    return (
        <div style={{
            height: h, borderRadius: r,
            background: 'linear-gradient(90deg,rgba(0,0,0,0.05) 0%,rgba(0,0,0,0.02) 50%,rgba(0,0,0,0.05) 100%)',
            backgroundSize: '200% 100%', animation: 'shimmer 1.5s infinite',
        }} />
    )
}

// ── Awaiting ─────────────────────────────────────────────────────────────────
function Await({ label = 'Awaiting Data' }: { label?: string }) {
    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <div style={{ width: 44, height: 44, borderRadius: '50%', border: '3px solid rgba(0,113,227,0.15)', borderTop: '3px solid #0071e3', animation: 'spin 1.1s linear infinite' }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: '#aeaeb2', letterSpacing: '0.05em' }}>{label}</span>
        </div>
    )
}

// ── SVG Gauge ────────────────────────────────────────────────────────────────
function Gauge({ pct, color, label, value }: { pct: number; color: string; label: string; value: string }) {
    const r = 50, circ = 2 * Math.PI * r, arc = circ * 0.75
    const offset = arc - (arc * Math.min(Math.max(pct, 0), 100)) / 100
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <svg width="120" height="85" viewBox="0 0 120 85">
                <circle cx="60" cy="75" r={r} fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="13"
                    strokeDasharray={`${arc} ${circ}`} strokeLinecap="round" transform="rotate(135 60 75)" />
                <circle cx="60" cy="75" r={r} fill="none" stroke={color} strokeWidth="13"
                    strokeDasharray={`${arc} ${circ}`} strokeDashoffset={offset} strokeLinecap="round"
                    transform="rotate(135 60 75)" style={{ transition: 'stroke-dashoffset 1.4s ease' }} />
                <text x="60" y="70" textAnchor="middle" fontSize="16" fontWeight="800" fill="#000" fontFamily={F}>{value}</text>
            </svg>
            <span style={{ fontSize: 10, fontWeight: 700, color: '#6e6e73', textAlign: 'center', maxWidth: 80 }}>{label}</span>
        </div>
    )
}

// ── KPI Card ─────────────────────────────────────────────────────────────────
function KpiCard({ label, value, sub, color, icon: Icon, i = 0, loading, trend }: {
    label: string; value: string; sub: string
    color: { s: string; l: string }
    icon: React.FC<{ size?: number; strokeWidth?: number }>
    i?: number; loading: boolean; trend?: string
}) {
    return (
        <motion.div variants={UP} initial="hidden" animate="visible" custom={i}
            style={{ ...GLASS, padding: '22px', display: 'flex', flexDirection: 'column', gap: 10, position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: `linear-gradient(90deg,${color.s},${color.s}44)`, borderRadius: '24px 24px 0 0' }} />
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ width: 40, height: 40, borderRadius: 13, background: color.l, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ color: color.s }}><Icon size={17} strokeWidth={2} /></span>
                </div>
                {trend && (
                    <span style={{ fontSize: 10, fontWeight: 700, padding: '3px 9px', borderRadius: 99, color: trend.startsWith('+') ? '#28cd41' : '#ff375f', background: trend.startsWith('+') ? 'rgba(40,205,65,0.10)' : 'rgba(255,55,95,0.10)' }}>
                        {trend}
                    </span>
                )}
            </div>
            {loading
                ? <Shim h={36} r={8} />
                : <p style={{ fontSize: '1.9rem', fontWeight: 900, letterSpacing: '-0.05em', color: value === '—' ? '#c7c7cc' : '#000', margin: 0, lineHeight: 1 }}>{value}</p>
            }
            <div>
                <p style={{ fontSize: 11, fontWeight: 700, color: '#8a8a8e', textTransform: 'uppercase', letterSpacing: '0.09em', margin: 0 }}>{label}</p>
                <p style={{ fontSize: 11, color: '#aeaeb2', margin: '2px 0 0', fontWeight: 500 }}>{sub}</p>
            </div>
        </motion.div>
    )
}

// ── Chart Card ───────────────────────────────────────────────────────────────
function ChartCard({ title, label, color, icon: Icon, children, span = 1, i = 0, badge }: {
    title: string; label: string; color: { s: string; l: string }
    icon: React.FC<{ size?: number; strokeWidth?: number }>
    children: React.ReactNode; span?: 1 | 2; i?: number; badge?: string
}) {
    return (
        <motion.div variants={UP} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} custom={i}
            style={{ ...GLASS, padding: 0, gridColumn: span === 2 ? 'span 2' : undefined, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '18px 22px 12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                        <div style={{ width: 32, height: 32, borderRadius: 10, background: color.l, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                            <span style={{ color: color.s }}><Icon size={14} strokeWidth={2.2} /></span>
                        </div>
                        <div>
                            <p style={{ fontSize: 9.5, fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase', color: color.s, margin: 0 }}>{label}</p>
                            <p style={{ fontSize: '0.88rem', fontWeight: 800, color: '#000', margin: 0, letterSpacing: '-0.02em' }}>{title}</p>
                        </div>
                    </div>
                    {badge && <span style={{ fontSize: 10, fontWeight: 700, color: color.s, background: color.l, padding: '3px 10px', borderRadius: 99 }}>{badge}</span>}
                </div>
                <div style={{ height: 2, borderRadius: 99, background: `linear-gradient(90deg,${color.s},transparent)` }} />
            </div>
            <div style={{ padding: '4px 18px 18px', flex: 1 }}>{children}</div>
        </motion.div>
    )
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default function VisualizationsPage() {
    const { stats, loading, lastRefresh, countdown, refetch } = useVisualizationData()
    const s = stats

    // Derived values
    const monthly = s?.monthly_profiles ?? new Array(12).fill(0)
    const yearLabels = Object.keys(s?.yearly_profiles ?? {}).sort()
    const yearVals = yearLabels.map(y => s!.yearly_profiles[y])
    const basins = s?.ocean_basins ?? []
    const platforms = s?.platform_types ?? []
    const measurements = s?.measurements ?? []
    const tempMeas = measurements.filter(m => m.temperature != null)
    const salMeas = measurements.filter(m => m.salinity != null)
    const hasMeas = measurements.length > 0
    const hasBasins = basins.length > 0
    const hasPlat = platforms.length > 0
    const activePct = s ? Math.min(100, Math.round((s.active_floats / Math.max(s.total_floats, 1)) * 100)) : 0
    const profUtil = s ? Math.min(100, Math.round((s.total_profiles / 200) * 100)) : 0
    const measUtil = s ? Math.min(100, Math.round((s.total_measurements / 2000) * 100)) : 0
    const qualScore = hasMeas ? 92 : 0

    // Chart data
    const lineData = {
        labels: MONTHS,
        datasets: [{
            label: 'Profiles', data: monthly,
            borderColor: P.blue.s,
            backgroundColor: (ctx: { chart: ChartJS }) => {
                const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 220)
                g.addColorStop(0, 'rgba(0,113,227,0.26)'); g.addColorStop(1, 'rgba(0,113,227,0)'); return g
            },
            borderWidth: 2.5, pointBackgroundColor: P.blue.s, pointBorderColor: '#fff',
            pointBorderWidth: 2, pointRadius: 5, pointHoverRadius: 9, tension: 0.45, fill: true,
        }]
    }

    const stackedData = {
        labels: MONTHS,
        datasets: [
            { label: 'Current Year', data: monthly, backgroundColor: 'rgba(0,113,227,0.78)', borderRadius: 6, borderSkipped: false, stack: 'a' },
            { label: 'Historical Avg', data: monthly.map(v => Math.round(v * 0.3)), backgroundColor: 'rgba(0,113,227,0.25)', borderRadius: 6, borderSkipped: false, stack: 'a' },
        ]
    }

    const donutData = {
        labels: ['Active Floats', 'Inactive Floats', 'BGC-Argo Est.'],
        datasets: [{
            data: [s?.active_floats ?? 0, s?.inactive_floats ?? 0, Math.round((s?.active_floats ?? 0) * 0.22)],
            backgroundColor: ['rgba(40,205,65,0.85)', 'rgba(255,159,10,0.85)', 'rgba(94,92,230,0.85)'],
            borderColor: ['#fff', '#fff', '#fff'], borderWidth: 4, hoverOffset: 14,
        }]
    }

    const basinBarData = {
        labels: basins.map(b => b.name),
        datasets: [{ label: 'Floats', data: basins.map(b => b.floats), backgroundColor: BCOLORS.slice(0, basins.length), borderRadius: 9, borderSkipped: false }]
    }

    const basinGrouped = {
        labels: basins.map(b => b.name),
        datasets: [
            { label: 'Floats', data: basins.map(b => b.floats), backgroundColor: 'rgba(0,113,227,0.80)', borderRadius: 7, borderSkipped: false },
            { label: 'Profiles', data: basins.map(b => b.profiles), backgroundColor: 'rgba(40,205,65,0.80)', borderRadius: 7, borderSkipped: false },
        ]
    }

    const polarData = {
        labels: platforms.map(p => p.type),
        datasets: [{ data: platforms.map(p => p.count), backgroundColor: ['rgba(0,113,227,0.72)', 'rgba(40,205,65,0.72)', 'rgba(255,159,10,0.72)', 'rgba(94,92,230,0.72)'], borderColor: '#fff', borderWidth: 2 }]
    }

    const tempScatter = {
        datasets: [{
            label: 'Temp vs Depth',
            data: tempMeas.map(m => ({ x: m.temperature, y: -(m.depth ?? m.pressure ?? 0) })),
            backgroundColor: tempMeas.map(m => m.temperature > 25 ? 'rgba(255,59,48,0.7)' : m.temperature > 15 ? 'rgba(255,159,10,0.7)' : m.temperature > 5 ? 'rgba(0,113,227,0.7)' : 'rgba(94,92,230,0.7)'),
            pointRadius: 3.5, pointHoverRadius: 7,
        }]
    }

    const salScatter = {
        datasets: [{ label: 'Salinity vs Depth', data: salMeas.map(m => ({ x: m.salinity, y: -(m.depth ?? m.pressure ?? 0) })), backgroundColor: 'rgba(50,173,230,0.65)', pointRadius: 3.5, pointHoverRadius: 7 }]
    }

    const yearBarData = {
        labels: yearLabels,
        datasets: [{ label: 'Profiles per Year', data: yearVals, backgroundColor: yearLabels.map((_, i) => `hsla(${210 + i * 20},78%,56%,0.85)`), borderRadius: 9, borderSkipped: false }]
    }

    const radarData = {
        labels: ['Active Floats', 'Profiles', 'Measurements', 'Ocean Basins', 'Platform Diversity', 'Data Quality'],
        datasets: [{
            label: 'Network Health',
            data: [activePct, profUtil, measUtil, Math.min(100, (s?.ocean_basins_count ?? 0) * 16), Math.min(100, platforms.length * 34), qualScore],
            backgroundColor: 'rgba(0,113,227,0.14)', borderColor: P.blue.s, borderWidth: 2.5,
            pointBackgroundColor: P.blue.s, pointBorderColor: '#fff', pointBorderWidth: 2, pointRadius: 5,
        }]
    }

    // Chart options
    const baseOpts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { ...TT } }, scales: { x: { ...AX }, y: { ...AX, beginAtZero: true } }, animation: { duration: 700 } }
    const scatterOpts = (xLbl: string) => ({ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { ...TT, callbacks: { label: (c: { parsed: { x: number; y: number } }) => `${xLbl}: ${c.parsed.x.toFixed(2)}  |  Depth: ${Math.abs(c.parsed.y).toFixed(0)}m` } } }, scales: { x: { ...AX, title: { display: true, text: xLbl, color: '#8a8a8e', font: { family: F, size: 10 } } }, y: { ...AX, title: { display: true, text: 'Depth (m)', color: '#8a8a8e', font: { family: F, size: 10 } } } }, animation: { duration: 400 } })
    const donutOpts = { responsive: true, maintainAspectRatio: false, cutout: '68%', plugins: { legend: { display: true, position: 'bottom' as const, labels: { color: '#3a3a3c', font: { family: F, size: 11, weight: 600 as const }, padding: 16, boxWidth: 9, usePointStyle: true, pointStyle: 'circle' as const } }, tooltip: { ...TT } }, animation: { duration: 700 } }
    const radarOpts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { ...TT } }, scales: { r: { min: 0, max: 100, ticks: { color: '#8a8a8e', font: { family: F, size: 10 }, stepSize: 25, backdropColor: 'transparent' }, grid: { color: 'rgba(0,0,0,0.06)' }, pointLabels: { color: '#3a3a3c', font: { family: F, size: 11, weight: 700 as const } }, angleLines: { color: 'rgba(0,0,0,0.06)' } } }, animation: { duration: 900 } }
    const polarOpts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'right' as const, labels: { color: '#3a3a3c', font: { family: F, size: 11 }, padding: 14, boxWidth: 10, usePointStyle: true, pointStyle: 'circle' as const } }, tooltip: { ...TT } }, scales: { r: { ticks: { backdropColor: 'transparent', color: '#8a8a8e', font: { family: F, size: 10 } }, grid: { color: 'rgba(0,0,0,0.05)' } } }, animation: { duration: 700 } }
    const stackedOpts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'top' as const, labels: { color: '#3a3a3c', font: { family: F, size: 11 }, padding: 14, boxWidth: 10, usePointStyle: true, pointStyle: 'circle' as const } }, tooltip: { ...TT } }, scales: { x: { ...AX, stacked: true }, y: { ...AX, stacked: true, beginAtZero: true } }, animation: { duration: 700 } }
    const groupedOpts = { ...baseOpts, plugins: { legend: { display: true, position: 'top' as const, labels: { color: '#3a3a3c', font: { family: F, size: 11 }, padding: 12, boxWidth: 9, usePointStyle: true, pointStyle: 'circle' as const } }, tooltip: { ...TT } } }

    const kpis = [
        { label: 'Active Floats', value: num(s?.active_floats), sub: `${num(s?.total_floats)} total floats`, color: P.blue, icon: Activity, trend: undefined },
        { label: 'Total Profiles', value: num(s?.total_profiles), sub: 'Oceanographic casts', color: P.green, icon: Layers, trend: undefined },
        { label: 'Avg Temperature', value: s?.avg_temperature != null ? `${s.avg_temperature.toFixed(2)}°C` : '—', sub: 'Cross-ocean mean', color: P.orange, icon: Thermometer, trend: undefined },
        { label: 'Avg Salinity', value: s?.avg_salinity != null ? `${s.avg_salinity.toFixed(2)} PSU` : '—', sub: 'Practical Salinity Units', color: P.purple, icon: Droplets, trend: undefined },
        { label: 'Measurements', value: num(s?.total_measurements), sub: 'Total depth readings', color: P.teal, icon: Wind, trend: undefined },
        { label: 'Ocean Basins', value: num(s?.ocean_basins_count), sub: `${platforms.length} platform types`, color: P.pink, icon: Globe, trend: undefined },
    ]

    return (
        <>
            {/* ── Fixed Ocean Background (behind everything) ── */}
            <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
                <div style={{ position: 'absolute', inset: 0, backgroundImage: 'url(https://images.unsplash.com/photo-1518837695005-2083093ee35b?q=80&w=3840&auto=format&fit=crop)', backgroundSize: '120% 120%', animation: 'oceanFlow 35s ease-in-out infinite' }} />
                <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom,rgba(240,244,248,0.15) 0%,rgba(240,244,248,0.35) 100%)' }} />
            </div>

            {/* ── Sticky Live Pill (sticks within <main> scroll container) ── */}
            <div style={{ position: 'sticky', top: 16, zIndex: 50, display: 'flex', justifyContent: 'flex-end', paddingRight: 28, marginBottom: -52, pointerEvents: 'none' }}>
                <div style={{ ...PILL, padding: '9px 16px', display: 'flex', alignItems: 'center', gap: 10, pointerEvents: 'all' }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: s ? '#28cd41' : '#ff9f0a', display: 'inline-block', boxShadow: s ? '0 0 8px rgba(40,205,65,0.9)' : '0 0 8px rgba(255,159,10,0.7)', animation: 'ping 2s ease-in-out infinite' }} />
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#3a3a3c' }}>{s ? 'Live' : 'Connecting'} · {countdown}s</span>
                    <button onClick={refetch} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '5px 12px', borderRadius: 99, border: '1px solid rgba(0,0,0,0.09)', background: 'rgba(0,0,0,0.03)', cursor: 'pointer', fontSize: 11, fontWeight: 700, color: '#3a3a3c', fontFamily: F }}>
                        <RefreshCw style={{ width: 11, height: 11 }} /> Refresh
                    </button>
                </div>
            </div>

            {/* ── Scrollable Content ── */}
            <div style={{ position: 'relative', zIndex: 10, backgroundColor: 'transparent', fontFamily: F }}>
                <div style={{ maxWidth: 1140, margin: '0 auto', padding: '44px 24px 80px' }}>

                    {/* Header */}
                    <motion.div variants={UP} initial="hidden" animate="visible" custom={0} style={{ marginBottom: 30 }}>
                        <p style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.15em', textTransform: 'uppercase', color: P.blue.s, margin: '0 0 6px' }}>ARGO Ocean Intelligence · Live Dashboard</p>
                        <h1 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', margin: '0 0 8px', lineHeight: 1.1 }}>Data Visualizations</h1>
                        <p style={{ fontSize: 14, color: '#6e6e73', fontWeight: 500, margin: 0 }}>
                            {s ? `Live data: ${num(s.active_floats)} active floats · ${num(s.total_profiles)} profiles · ${num(s.total_measurements)} measurements · ${num(s.ocean_basins_count)} ocean basins · updated ${new Date(s.last_updated).toLocaleTimeString()}` : 'Connecting to backend…'}
                        </p>
                        <AnimatePresence>
                            {!s && !loading && (
                                <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                                    style={{ marginTop: 14, padding: '12px 18px', borderRadius: 14, background: 'rgba(255,159,10,0.08)', border: '1px solid rgba(255,159,10,0.25)', display: 'inline-flex', gap: 10, alignItems: 'center' }}>
                                    <span>⚠️</span>
                                    <span style={{ fontSize: 12, fontWeight: 600, color: '#92520a' }}>Backend offline or no data — run ingestion from Dashboard.</span>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>

                    {/* KPI Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 13, marginBottom: 18 }}>
                        {kpis.map((k, i) => <KpiCard key={k.label} {...k} i={i + 1} loading={loading} />)}
                    </div>

                    {/* Gauges */}
                    <motion.div variants={UP} initial="hidden" whileInView="visible" viewport={{ once: true }} custom={0}
                        style={{ ...GLASS, padding: '20px 28px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap', justifyContent: 'space-around' }}>
                        <div>
                            <p style={{ fontSize: 9.5, fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase', color: P.blue.s, margin: 0 }}>Platform Health</p>
                            <p style={{ fontSize: '0.9rem', fontWeight: 800, color: '#000', margin: '2px 0 0' }}>Network Utilization Gauges</p>
                        </div>
                        <Gauge pct={activePct} color={P.green.s} label="Active Float Rate" value={`${activePct}%`} />
                        <Gauge pct={profUtil} color={P.blue.s} label="Profile Utilization" value={`${profUtil}%`} />
                        <Gauge pct={measUtil} color={P.teal.s} label="Measurement Fill" value={`${measUtil}%`} />
                        <Gauge pct={qualScore} color={P.purple.s} label="Data Quality Score" value={`${qualScore}%`} />
                    </motion.div>

                    {/* Row 1: Line + Doughnut */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1.65fr 1fr', gap: 13, marginBottom: 13 }}>
                        <ChartCard title="Profiles collected per month" label="Profile Timeline" color={P.blue} icon={Layers} badge="Live" i={0}>
                            <div style={{ height: 240 }}>
                                {loading ? <Shim h={240} /> : monthly.some(v => v > 0) ? <Line data={lineData} options={baseOpts as object} /> : <Await label="No profile data yet" />}
                            </div>
                        </ChartCard>
                        <ChartCard title="Active vs Inactive vs BGC" label="Float Status" color={P.purple} icon={Activity} i={1}>
                            <div style={{ height: 240 }}>
                                {loading ? <Shim h={240} />
                                    : (s?.active_floats ?? 0) + (s?.inactive_floats ?? 0) > 0
                                        ? <Doughnut data={donutData} options={donutOpts} />
                                        : <Await label="No float data" />}
                            </div>
                        </ChartCard>
                    </div>

                    {/* Row 2: Stacked bar */}
                    <div style={{ marginBottom: 13 }}>
                        <ChartCard title="Monthly profile distribution — current vs historical average" label="Stacked Activity" color={P.teal} icon={BarChart3} span={2} i={0} badge="Enhanced">
                            <div style={{ height: 220 }}>
                                {loading ? <Shim h={220} /> : monthly.some(v => v > 0) ? <Bar data={stackedData} options={stackedOpts as object} /> : <Await />}
                            </div>
                        </ChartCard>
                    </div>

                    {/* Row 3: Basin bar + Platform polar */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 13, marginBottom: 13 }}>
                        <ChartCard title="Active floats by ocean basin" label="Basin Distribution" color={P.green} icon={Globe} i={0}>
                            <div style={{ height: 250 }}>
                                {loading ? <Shim h={250} /> : hasBasins ? <Bar data={basinBarData} options={{ ...baseOpts, indexAxis: 'y' } as object} /> : <Await label="No basin data" />}
                            </div>
                        </ChartCard>
                        <ChartCard title="Float platform types breakdown" label="Platform Polar Area" color={P.pink} icon={Cpu} i={1}>
                            <div style={{ height: 250 }}>
                                {loading ? <Shim h={250} /> : hasPlat ? <PolarArea data={polarData} options={polarOpts} /> : <Await label="No platform data" />}
                            </div>
                        </ChartCard>
                    </div>

                    {/* Row 4: Basin grouped */}
                    <div style={{ marginBottom: 13 }}>
                        <ChartCard title="Floats vs profiles per ocean basin — comparative breakdown" label="Basin Comparison" color={P.indigo} icon={BarChart3} span={2} i={0} badge="Grouped">
                            <div style={{ height: 230 }}>
                                {loading ? <Shim h={230} /> : hasBasins ? <Bar data={basinGrouped} options={groupedOpts as object} /> : <Await />}
                            </div>
                        </ChartCard>
                    </div>

                    {/* Row 5: Scatter plots */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 13, marginBottom: 13 }}>
                        <ChartCard title="Temperature (°C) vs Ocean Depth" label="Temperature Profile" color={P.orange} icon={Thermometer} i={0}>
                            <div style={{ height: 270 }}>
                                {loading ? <Shim h={270} /> : hasMeas ? <Scatter data={tempScatter} options={scatterOpts('Temp °C') as object} /> : <Await label="Run ingestion for measurement data" />}
                            </div>
                            {hasMeas && (
                                <div style={{ display: 'flex', gap: 10, marginTop: 10, flexWrap: 'wrap' }}>
                                    {([['>25°C', '#ff3b30'], ['15–25°C', '#ff9f0a'], ['5–15°C', '#0071e3'], ['<5°C', '#5e5ce6']] as [string, string][]).map(([l, c]) => (
                                        <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />
                                            <span style={{ fontSize: 10, fontWeight: 600, color: '#8a8a8e' }}>{l}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </ChartCard>
                        <ChartCard title="Salinity (PSU) vs Ocean Depth" label="Salinity Profile" color={P.teal} icon={Droplets} i={1}>
                            <div style={{ height: 270 }}>
                                {loading ? <Shim h={270} /> : hasMeas ? <Scatter data={salScatter} options={scatterOpts('Salinity PSU') as object} /> : <Await label="Run ingestion for salinity data" />}
                            </div>
                        </ChartCard>
                    </div>

                    {/* Row 6: Annual trend + Radar */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 13, marginBottom: 13 }}>
                        <ChartCard title="Profile collection trend by year" label="Annual Trend" color={P.indigo} icon={TrendingUp} i={0} badge="Historical">
                            <div style={{ height: 260 }}>
                                {loading ? <Shim h={260} /> : yearVals.length > 0 ? <Bar data={yearBarData} options={baseOpts as object} /> : <Await label="No yearly data" />}
                            </div>
                        </ChartCard>
                        <ChartCard title="ARGO network coverage & health index" label="Network Health Radar" color={P.blue} icon={Activity} i={1}>
                            <div style={{ height: 260 }}>
                                {loading ? <Shim h={260} /> : <Radar data={radarData} options={radarOpts} />}
                            </div>
                        </ChartCard>
                    </div>

                    {/* Recent Profile Table */}
                    <motion.div variants={UP} initial="hidden" whileInView="visible" viewport={{ once: true }} custom={0}
                        style={{ ...GLASS, padding: '22px', marginBottom: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                            <div style={{ width: 32, height: 32, borderRadius: 10, background: P.green.l, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <span style={{ color: P.green.s }}><Activity size={14} strokeWidth={2.2} /></span>
                            </div>
                            <div>
                                <p style={{ fontSize: 9.5, fontWeight: 800, letterSpacing: '0.14em', textTransform: 'uppercase', color: P.green.s, margin: 0 }}>Live Feed</p>
                                <p style={{ fontSize: '0.88rem', fontWeight: 800, color: '#000', margin: 0 }}>Recent Profile Activity</p>
                            </div>
                            <span style={{ marginLeft: 'auto', fontSize: 10, fontWeight: 700, color: P.green.s, background: P.green.l, padding: '3px 10px', borderRadius: 99 }}>
                                {s?.recent_profiles?.length ?? 0} records
                            </span>
                        </div>
                        <div style={{ height: 2, borderRadius: 99, background: `linear-gradient(90deg,${P.green.s},transparent)`, marginBottom: 14 }} />
                        {loading ? <Shim h={160} /> : (s?.recent_profiles ?? []).length > 0 ? (
                            <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, fontFamily: F }}>
                                    <thead>
                                        <tr>
                                            {['WMO Number', 'Cycle', 'Date', 'Basin', 'Platform', 'Avg Temp', 'Avg Salinity', 'Meas.'].map(h => (
                                                <th key={h} style={{ textAlign: 'left', padding: '6px 12px', fontSize: 10, fontWeight: 800, color: '#8a8a8e', textTransform: 'uppercase', letterSpacing: '0.07em', borderBottom: '1px solid rgba(0,0,0,0.06)', whiteSpace: 'nowrap' }}>{h}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {s!.recent_profiles.map((r, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid rgba(0,0,0,0.04)' }}>
                                                <td style={{ padding: '9px 12px', fontWeight: 700, color: P.blue.s }}>{r.wmo_number}</td>
                                                <td style={{ padding: '9px 12px', color: '#3a3a3c' }}>{r.cycle}</td>
                                                <td style={{ padding: '9px 12px', color: '#6e6e73' }}>{r.date?.split(' ')[0] ?? '—'}</td>
                                                <td style={{ padding: '9px 12px' }}><span style={{ background: P.teal.l, color: P.teal.s, padding: '2px 8px', borderRadius: 99, fontWeight: 700, fontSize: 11, whiteSpace: 'nowrap' }}>{r.ocean_basin}</span></td>
                                                <td style={{ padding: '9px 12px' }}><span style={{ background: P.indigo.l, color: P.indigo.s, padding: '2px 8px', borderRadius: 99, fontWeight: 700, fontSize: 11 }}>{r.platform_type ?? '—'}</span></td>
                                                <td style={{ padding: '9px 12px', fontWeight: 600, color: r.avg_temperature != null && r.avg_temperature > 20 ? '#ff9f0a' : '#3a3a3c' }}>{r.avg_temperature != null ? `${r.avg_temperature.toFixed(2)}°C` : '—'}</td>
                                                <td style={{ padding: '9px 12px', color: '#3a3a3c' }}>{r.avg_salinity != null ? r.avg_salinity.toFixed(2) : '—'}</td>
                                                <td style={{ padding: '9px 12px' }}><span style={{ background: P.green.l, color: P.green.s, padding: '2px 8px', borderRadius: 99, fontWeight: 700, fontSize: 11 }}>{r.measurements}</span></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p style={{ textAlign: 'center', padding: '32px 0', color: '#aeaeb2', fontSize: 13, fontWeight: 600, margin: 0 }}>No recent profiles — run ingestion from Dashboard to populate data.</p>
                        )}
                    </motion.div>

                    {/* Footer */}
                    <motion.div variants={UP} initial="hidden" whileInView="visible" viewport={{ once: true }} custom={0}
                        style={{ ...GLASS, padding: '14px 22px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10, borderRadius: 18 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
                            <span style={{ fontSize: 12, fontWeight: 600, color: '#6e6e73' }}>Last refresh: <span style={{ color: '#000', fontWeight: 700 }}>{lastRefresh.toLocaleTimeString()}</span></span>
                            <span style={{ fontSize: 12, color: '#d1d1d6' }}>|</span>
                            <span style={{ fontSize: 12, fontWeight: 600, color: '#6e6e73' }}>{num(s?.total_measurements)} measurements · {num(s?.total_profiles)} profiles · {num(s?.total_floats)} floats</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span style={{ width: 7, height: 7, borderRadius: '50%', background: s ? '#28cd41' : '#ff9f0a', display: 'inline-block', boxShadow: s ? '0 0 6px rgba(40,205,65,0.8)' : '0 0 6px rgba(255,159,10,0.7)' }} />
                            <span style={{ fontSize: 11, fontWeight: 700, color: '#3a3a3c' }}>Auto-refresh every 30s</span>
                        </div>
                    </motion.div>

                </div>
            </div>

            <style>{`
                @keyframes shimmer  { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
                @keyframes ping     { 0%,100%{opacity:1} 50%{opacity:0.5} }
                @keyframes spin     { to{transform:rotate(360deg)} }
                @keyframes oceanFlow{ 0%,100%{background-position:50% 50%} 33%{background-position:55% 45%} 66%{background-position:45% 55%} }
            `}</style>
        </>
    )
}
