'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft, Map, List, Filter, X, ChevronRight, Globe, Download, Loader2, Leaf, RefreshCw } from 'lucide-react'
import { FloatChatLogo } from '@/components/Brand'
import Link from 'next/link'
import { apiClient, type ArgoFloat, type ArgoVisProfile, type BGCProfile, type BGCSummary } from '@/lib/api-client'
import ProfileDetailChart from '@/components/charts/ProfileDetailChart'

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif"
const GLASS: React.CSSProperties = {
    background: 'rgba(255,255,255,0.55)', backdropFilter: 'blur(48px) saturate(200%)',
    WebkitBackdropFilter: 'blur(48px) saturate(200%)', border: '1.5px solid rgba(255,255,255,0.85)',
    borderRadius: 24, boxShadow: '0 2px 0 rgba(255,255,255,0.9) inset, 0 10px 36px rgba(0,0,0,0.09)',
}
const GLASS_SM: React.CSSProperties = {
    background: 'rgba(255,255,255,0.42)', backdropFilter: 'blur(20px) saturate(150%)',
    WebkitBackdropFilter: 'blur(20px) saturate(150%)', border: '1px solid rgba(255,255,255,0.75)', borderRadius: 14,
}

const STATUS_OPTS = ['All', 'active', 'inactive']
const BASIN_OPTS = ['All', 'Atlantic', 'Pacific', 'Indian', 'Southern', 'Arctic']
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fadeUp: any = { hidden: { opacity: 0, y: 14 }, visible: (i: number = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.35, delay: i * 0.05 } }) }
type Tab = 'floats' | 'bgc'
type DataSource = 'local' | 'argovis'

export default function ExplorerPage() {
    const [tab, setTab] = useState<Tab>('floats')
    const [dataSource, setDataSource] = useState<DataSource>('local')
    const [view, setView] = useState<'list' | 'map'>('list')
    const [filterOpen, setFilterOpen] = useState(true)
    const [status, setStatus] = useState('All')
    const [basin, setBasin] = useState('All')
    const [limit, setLimit] = useState(50)
    const [selected, setSelected] = useState<ArgoFloat | null>(null)
    const [floats, setFloats] = useState<ArgoFloat[]>([])
    const [total, setTotal] = useState(0)
    const [loading, setLoading] = useState(false)
    const [exporting, setExporting] = useState(false)
    const [bgcProfiles, setBgcProfiles] = useState<BGCProfile[]>([])
    const [bgcSummary, setBgcSummary] = useState<BGCSummary | null>(null)
    const [bgcLoading, setBgcLoading] = useState(false)

    const mapArgoVisProfileToFloat = useCallback((profile: ArgoVisProfile, index: number): ArgoFloat => {
        return {
            id: -(index + 1),
            wmo_number: profile.platform_number || profile._id || `argovis-${index + 1}`,
            platform_type: 'ArgoVis',
            last_latitude: profile.geolocation_lat,
            last_longitude: profile.geolocation_lon,
            status: 'active',
            ocean_basin: profile.basin != null ? `Basin ${profile.basin}` : 'Unknown',
        }
    }, [])

    const fetchFloats = useCallback(async () => {
        setLoading(true); setSelected(null)
        try {
            if (dataSource === 'argovis') {
                const res = await apiClient.getLatestArgoVisProfiles(limit)
                const mapped = res.data.map((profile, index) => mapArgoVisProfileToFloat(profile, index))
                setFloats(mapped)
                setTotal(res.total ?? mapped.length)
                return
            }
            const res = await apiClient.filterArgoFloats({ status: status !== 'All' ? status : undefined, ocean_basin: basin !== 'All' ? basin : undefined, limit, offset: 0 })
            setFloats(res.data); setTotal(res.total)
        } catch {
            setFloats([])
            setTotal(0)
        } finally { setLoading(false) }
    }, [dataSource, status, basin, limit, mapArgoVisProfileToFloat])

    useEffect(() => { void fetchFloats() }, [fetchFloats])

    useEffect(() => {
        if (tab !== 'bgc') return
        setBgcLoading(true)
        Promise.all([apiClient.filterBGCProfiles({ limit: 40 }), apiClient.getBGCSummary()])
            .then(([p, s]) => { setBgcProfiles(p.data); setBgcSummary(s) })
            .catch(() => { setBgcProfiles([]); setBgcSummary(null) })
            .finally(() => setBgcLoading(false))
    }, [tab])

    async function exportCSV() {
        setExporting(true)
        try {
            const f = await apiClient.exportFloatsCsv({ status: status !== 'All' ? status : undefined, ocean_basin: basin !== 'All' ? basin : undefined })
            const url = URL.createObjectURL(f.blob)
            const a = document.createElement('a'); a.href = url; a.download = f.filename ?? 'floats.csv'; a.click(); URL.revokeObjectURL(url)
        } catch { /* noop */ } finally { setExporting(false) }
    }

    const Chip = ({ label, active, color = '#000', onClick }: { label: string; active: boolean; color?: string; onClick: () => void }) => (
        <button onClick={onClick} style={{ padding: '6px 14px', borderRadius: 99, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 700, fontFamily: FONT, transition: 'all 0.15s', background: active ? color : 'rgba(0,0,0,0.06)', color: active ? '#fff' : '#3a3a3c' }}>{label}</button>
    )

    return (
        <div style={{ backgroundColor: '#f5f5f7', height: '100vh', display: 'flex', flexDirection: 'column', position: 'relative', fontFamily: FONT, overflow: 'hidden' }}>

            {/* ── Apple-like Animated 4K Liquid Ocean Background ── */}
            <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
                {/* Flowing Ocean Image (Animated) */}
                <div style={{
                    position: 'absolute', inset: 0,
                    backgroundImage: 'url(https://images.unsplash.com/photo-1542240578-1b60882e9643?q=80&w=3840&auto=format&fit=crop)',
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

            {/* Header */}
            <div style={{ padding: '40px 20px 0', display: 'flex', justifyContent: 'center', flexShrink: 0, zIndex: 40, position: 'relative' }}>
                <div style={{ ...GLASS, borderRadius: 99, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 24px', gap: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, fontWeight: 600, color: '#6e6e73', textDecoration: 'none' }}>
                            <ChevronLeft style={{ width: 14, height: 14 }} /> Home
                        </Link>
                        <div style={{ width: 1, height: 14, background: 'rgba(0,0,0,0.1)' }} />
                        <FloatChatLogo size={15} />
                        {/* Tab */}
                        <div style={{ display: 'flex', padding: 3, gap: 2, borderRadius: 12, background: 'rgba(0,0,0,0.06)', marginLeft: 6 }}>
                            {(['floats', 'bgc'] as Tab[]).map(t => (
                                <button key={t} onClick={() => setTab(t)} style={{ padding: '5px 14px', borderRadius: 10, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 700, fontFamily: FONT, background: tab === t ? '#fff' : 'transparent', color: tab === t ? '#000' : '#6e6e73', boxShadow: tab === t ? '0 1px 4px rgba(0,0,0,0.12)' : 'none', transition: 'all 0.15s', textTransform: 'uppercase' }}>
                                    {t}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {tab === 'floats' && <div style={{ ...GLASS_SM, padding: '5px 12px', fontSize: 11, fontWeight: 700, color: '#3a3a3c' }}>{loading ? '…' : `${floats.length} / ${total.toLocaleString()}`}</div>}
                        {tab === 'floats' && <div style={{ ...GLASS_SM, padding: '5px 10px', fontSize: 11, fontWeight: 700, color: '#3a3a3c' }}>{dataSource === 'local' ? 'Local DB' : 'Argovis API'}</div>}
                        {tab === 'floats' && dataSource === 'local' && (
                            <button onClick={() => void exportCSV()} disabled={exporting}
                                style={{ ...GLASS_SM, display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 99, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 700, color: '#0071e3', fontFamily: FONT }}>
                                {exporting ? <Loader2 style={{ width: 12, height: 12, animation: 'spin 1s linear infinite' }} /> : <Download style={{ width: 12, height: 12 }} />}
                                {exporting ? 'Exporting…' : 'Export CSV'}
                            </button>
                        )}
                        <div style={{ display: 'flex', padding: 4, gap: 3, borderRadius: 14, background: 'rgba(0,0,0,0.06)' }}>
                            {[{ id: 'list' as const, icon: List }, { id: 'map' as const, icon: Map }].map(v => (
                                <button key={v.id} onClick={() => setView(v.id)}
                                    style={{ width: 30, height: 28, borderRadius: 10, border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', background: view === v.id ? '#fff' : 'transparent', boxShadow: view === v.id ? '0 1px 4px rgba(0,0,0,0.1)' : 'none', transition: 'all 0.15s' }}>
                                    <v.icon style={{ width: 13, height: 13, color: view === v.id ? '#000' : '#6e6e73' }} />
                                </button>
                            ))}
                        </div>
                        <button onClick={() => setFilterOpen(b => !b)}
                            style={{ ...GLASS_SM, display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 99, border: '1px solid rgba(0,0,0,0.08)', cursor: 'pointer', fontSize: 12, fontWeight: 700, color: '#3a3a3c', fontFamily: FONT }}>
                            <Filter style={{ width: 12, height: 12 }} /> Filters
                        </button>
                    </div>
                </div>
            </div>

            {/* Body */}
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative', zIndex: 10 }}>
                {/* Filter sidebar */}
                <AnimatePresence initial={false}>
                    {filterOpen && tab === 'floats' && (
                        <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: 240, opacity: 1 }} exit={{ width: 0, opacity: 0 }}
                            transition={{ type: 'spring', stiffness: 320, damping: 36 }}
                            style={{ ...GLASS, flexShrink: 0, margin: '12px 0 12px 12px', borderRadius: 24, overflow: 'hidden', zIndex: 20 }}>
                            <div style={{ padding: '18px 14px', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>
                                <div>
                                    <p style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#6e6e73', marginBottom: 8 }}>Data Source</p>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                        <Chip label="Local DB" active={dataSource === 'local'} onClick={() => setDataSource('local')} />
                                        <Chip label="Argovis API" active={dataSource === 'argovis'} color="#0071e3" onClick={() => setDataSource('argovis')} />
                                    </div>
                                    {dataSource === 'argovis' && <p style={{ fontSize: 11, color: '#6e6e73', marginTop: 8 }}>Using latest global profiles from Argovis.</p>}
                                </div>
                                {dataSource === 'local' && (
                                    <>
                                        <div>
                                            <p style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#6e6e73', marginBottom: 8 }}>Status</p>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                                {STATUS_OPTS.map(s => <Chip key={s} label={s === 'All' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)} active={status === s} onClick={() => setStatus(s)} />)}
                                            </div>
                                        </div>
                                        <div>
                                            <p style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#6e6e73', marginBottom: 8 }}>Ocean Basin</p>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                                {BASIN_OPTS.map(d => <Chip key={d} label={d} active={basin === d} color="#0071e3" onClick={() => setBasin(d)} />)}
                                            </div>
                                        </div>
                                        <div>
                                            <p style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#6e6e73', marginBottom: 8 }}>Limit</p>
                                            <div style={{ display: 'flex', gap: 6 }}>
                                                {[20, 50, 100].map(n => <Chip key={n} label={String(n)} active={limit === n} color="#5e5ce6" onClick={() => setLimit(n)} />)}
                                            </div>
                                        </div>
                                    </>
                                )}
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
                                    <button onClick={() => void fetchFloats()} style={{ padding: '10px', borderRadius: 14, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 700, fontFamily: FONT, background: '#000', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                                        <RefreshCw style={{ width: 12, height: 12 }} /> Apply
                                    </button>
                                    <button onClick={() => { setStatus('All'); setBasin('All'); setLimit(50); setDataSource('local') }} style={{ padding: '10px', borderRadius: 14, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 700, fontFamily: FONT, background: 'rgba(0,0,0,0.05)', color: '#6e6e73' }}>Reset</button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Float grid */}
                {tab === 'floats' && (
                    <div style={{ flex: 1, overflowY: 'auto', padding: '12px', position: 'relative' }}>
                        {loading ? (
                            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14 }}>
                                <Loader2 style={{ width: 28, height: 28, color: '#0071e3', animation: 'spin 1s linear infinite' }} />
                                <p style={{ fontSize: 13, color: '#6e6e73', fontWeight: 600 }}>Loading floats from ARGO database…</p>
                            </div>
                        ) : floats.length === 0 ? (
                            <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                <Globe style={{ width: 38, height: 38, color: '#b0b0b5', marginBottom: 14 }} />
                                <p style={{ fontSize: '1.1rem', fontWeight: 800, color: '#000', marginBottom: 6 }}>No floats found</p>
                                <p style={{ fontSize: 13, color: '#6e6e73' }}>Try different filters or connect your backend</p>
                            </div>
                        ) : (
                            <motion.div initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.04 } } }}
                                style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
                                {floats.map((f, i) => (
                                    <motion.button key={f.wmo_number} variants={fadeUp} custom={i} onClick={() => setSelected(f)}
                                        style={{ ...GLASS, padding: '18px 20px', textAlign: 'left', cursor: 'pointer', display: 'flex', flexDirection: 'column', border: 'none', fontFamily: FONT, transition: 'transform 0.15s', background: selected?.wmo_number === f.wmo_number ? 'rgba(0,113,227,0.08)' : undefined }}
                                        onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-2px)')}
                                        onMouseLeave={e => (e.currentTarget.style.transform = 'translateY(0)')}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                                                <span style={{ width: 8, height: 8, borderRadius: '50%', background: f.status === 'active' ? '#34c759' : '#ff9f0a', display: 'inline-block' }} />
                                                <span style={{ fontSize: 13, fontWeight: 800, color: '#000' }}>{f.wmo_number}</span>
                                            </div>
                                            <ChevronRight style={{ width: 13, height: 13, color: '#a0a0a5' }} />
                                        </div>
                                        <p style={{ fontSize: 12, color: '#6e6e73', fontWeight: 500 }}>{f.ocean_basin ?? '—'} · {f.platform_type ?? '—'}</p>
                                        {f.last_latitude != null && <p style={{ fontSize: 11, color: '#a0a0a5', marginTop: 4 }}>{f.last_latitude.toFixed(2)}°, {f.last_longitude?.toFixed(2) ?? '?'}°</p>}
                                    </motion.button>
                                ))}
                            </motion.div>
                        )}

                        <AnimatePresence>
                            {selected && (
                                <motion.div initial={{ x: 300, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 300, opacity: 0 }}
                                    transition={{ type: 'spring', stiffness: 320, damping: 36 }}
                                    style={{ ...GLASS, position: 'absolute', top: 12, right: 12, bottom: 12, width: 280, borderRadius: 24, overflow: 'hidden', zIndex: 20, display: 'flex', flexDirection: 'column' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid rgba(0,0,0,0.07)' }}>
                                        <p style={{ fontSize: 14, fontWeight: 800, color: '#000' }}>Float {selected.wmo_number}</p>
                                        <button onClick={() => setSelected(null)} style={{ width: 28, height: 28, borderRadius: 99, background: 'rgba(0,0,0,0.07)', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <X style={{ width: 13, height: 13 }} />
                                        </button>
                                    </div>
                                    <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {[
                                            { label: 'WMO Number', value: selected.wmo_number },
                                            { label: 'Status', value: selected.status ?? '—' },
                                            { label: 'Platform', value: selected.platform_type ?? '—' },
                                            { label: 'Ocean Basin', value: selected.ocean_basin ?? '—' },
                                            { label: 'Last Latitude', value: selected.last_latitude != null ? `${selected.last_latitude.toFixed(4)}°` : '—' },
                                            { label: 'Last Longitude', value: selected.last_longitude != null ? `${selected.last_longitude.toFixed(4)}°` : '—' },
                                        ].map(row => (
                                            <div key={row.label} style={{ ...GLASS_SM, padding: '12px 14px' }}>
                                                <p style={{ fontSize: 9, fontWeight: 700, color: '#a0a0a5', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 2 }}>{row.label}</p>
                                                <p style={{ fontSize: 14, fontWeight: 800, color: '#000' }}>{row.value}</p>
                                            </div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}

                {/* BGC tab */}
                {tab === 'bgc' && (
                    <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
                        {bgcLoading ? (
                            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
                                <Loader2 style={{ width: 28, height: 28, color: '#34c759', animation: 'spin 1s linear infinite' }} />
                                <p style={{ fontSize: 13, color: '#6e6e73', fontWeight: 600 }}>Loading BGC data…</p>
                            </div>
                        ) : (
                            <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
                                {bgcSummary && (
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(155px, 1fr))', gap: 12, marginBottom: 20 }}>
                                        {[
                                            { label: 'BGC Profiles', value: bgcSummary.total_profiles.toLocaleString(), color: '#34c759' },
                                            { label: 'BGC Floats', value: bgcSummary.total_floats.toLocaleString(), color: '#0071e3' },
                                            { label: 'Avg Chl-a', value: bgcSummary.avg_chlorophyll != null ? `${bgcSummary.avg_chlorophyll.toFixed(3)}` : '—', color: '#34c759' },
                                            { label: 'Avg Nitrate', value: bgcSummary.avg_nitrate != null ? `${bgcSummary.avg_nitrate.toFixed(2)}` : '—', color: '#ff9f0a' },
                                            { label: 'Avg O₂', value: bgcSummary.avg_oxygen != null ? `${bgcSummary.avg_oxygen.toFixed(1)}` : '—', color: '#5e5ce6' },
                                            { label: 'Avg pH', value: bgcSummary.avg_ph != null ? bgcSummary.avg_ph.toFixed(3) : '—', color: '#ff3b30' },
                                        ].map(k => (
                                            <div key={k.label} style={{ ...GLASS, padding: '18px 20px' }}>
                                                <p style={{ fontSize: '1.4rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 2 }}>{k.value}</p>
                                                <p style={{ fontSize: 10, fontWeight: 700, color: '#6e6e73', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{k.label}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
                                    {bgcProfiles.map((p, i) => (
                                        <motion.div key={p.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                                            style={{ ...GLASS, padding: '18px 20px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                                                <Leaf style={{ width: 14, height: 14, color: '#34c759' }} />
                                                <span style={{ fontSize: 13, fontWeight: 800, color: '#000' }}>{p.wmo_number}</span>
                                                <span style={{ fontSize: 11, color: '#6e6e73' }}>Cycle {p.cycle_number ?? '—'}</span>
                                            </div>
                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                                                {[
                                                    { label: 'Date', value: p.profile_date ? new Date(p.profile_date).toLocaleDateString() : '—' },
                                                    { label: 'Lat/Lon', value: p.latitude != null ? `${p.latitude.toFixed(2)}°` : '—' },
                                                    { label: 'Chl-a', value: p.chlorophyll != null ? p.chlorophyll.toFixed(3) : '—' },
                                                    { label: 'O₂', value: p.oxygen != null ? p.oxygen.toFixed(1) : '—' },
                                                    { label: 'NO₃', value: p.nitrate != null ? p.nitrate.toFixed(2) : '—' },
                                                    { label: 'pH', value: p.ph != null ? p.ph.toFixed(3) : '—' },
                                                ].map(r => (
                                                    <div key={r.label} style={{ background: 'rgba(0,0,0,0.03)', borderRadius: 10, padding: '8px 10px' }}>
                                                        <p style={{ fontSize: 9, fontWeight: 700, color: '#a0a0a5', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>{r.label}</p>
                                                        <p style={{ fontSize: 12, fontWeight: 800, color: '#000' }}>{r.value}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </motion.div>
                                    ))}
                                    {bgcProfiles.length === 0 && (
                                        <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '60px 0' }}>
                                            <Leaf style={{ width: 32, height: 32, color: '#b0b0b5', margin: '0 auto 12px' }} />
                                            <p style={{ fontSize: 14, fontWeight: 700, color: '#6e6e73' }}>No BGC profiles — connect backend to load data</p>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </div>
                )}
            </div>

            <style>{`
                @keyframes orb1 { 0%,100% { transform:translate(0,0) scale(1); } 33% { transform:translate(80px,-100px) scale(1.1); } 66% { transform:translate(-60px,60px) scale(0.92); } }
                @keyframes orb2 { 0%,100% { transform:translate(0,0) scale(1); } 30% { transform:translate(-100px,80px) scale(1.12); } 70% { transform:translate(70px,-50px) scale(0.9); } }
                @keyframes orb3 { 0%,100% { transform:translate(0,0) scale(1); } 40% { transform:translate(50px,90px) scale(1.08); } 80% { transform:translate(-80px,-60px) scale(0.95); } }
                @keyframes spin { to { transform:rotate(360deg); } }
            `}</style>
        </div>
    )
}
