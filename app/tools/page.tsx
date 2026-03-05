'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Waves, ChevronLeft, Calculator, BookOpen, GitCompare, ArrowRight, Lightbulb, BarChart2, Loader2, Globe, Cloud, Anchor, Fish, Thermometer, Ship } from 'lucide-react'
import Link from 'next/link'
import { apiClient, type GlossaryItem, type PressureDepthResponse, type LearningInsight, type ToolsQuickStats, type CompareRunResponse } from '@/lib/api-client'

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif"
const GLASS: React.CSSProperties = {
    background: 'rgba(255,255,255,0.75)', backdropFilter: 'blur(72px) saturate(180%)',
    WebkitBackdropFilter: 'blur(72px) saturate(180%)', border: '1px solid rgba(255,255,255,0.95)',
    borderRadius: 24, boxShadow: '0 2px 0 rgba(255,255,255,1) inset, 0 8px 36px rgba(0,0,0,0.07)',
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fadeUp: any = { hidden: { opacity: 0, y: 16 }, visible: (i: number = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.4, delay: i * 0.06 } }) }

type Mode = 'calc' | 'glossary' | 'compare' | 'learn' | 'datasources'
const MODES: { id: Mode; icon: typeof Calculator; label: string }[] = [
    { id: 'calc', icon: Calculator, label: 'Calculator' },
    { id: 'glossary', icon: BookOpen, label: 'Glossary' },
    { id: 'compare', icon: GitCompare, label: 'Compare' },
    { id: 'learn', icon: Lightbulb, label: 'Insights' },
    { id: 'datasources', icon: Globe, label: 'Data Sources' },
]

function InputField({ label, value, onChange, placeholder, type = 'number' }: { label: string; value: string; onChange: (v: string) => void; placeholder: string; type?: string }) {
    return (
        <div>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: '#6e6e73', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>{label}</label>
            <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
                style={{ width: '100%', padding: '12px 16px', border: '1.5px solid rgba(0,0,0,0.08)', borderRadius: 14, fontSize: 14, fontWeight: 600, color: '#000', fontFamily: FONT, outline: 'none', background: 'rgba(255,255,255,0.65)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', boxSizing: 'border-box' }} />
        </div>
    )
}

export default function ToolsPage() {
    const [mode, setMode] = useState<Mode>('calc')
    // Calc
    const [depth, setDepth] = useState('')
    const [lat, setLat] = useState('')
    const [calcResult, setCalcResult] = useState<PressureDepthResponse | null>(null)
    const [calcLoading, setCalcLoading] = useState(false)
    // Glossary
    const [glossary, setGlossary] = useState<GlossaryItem[]>([])
    const [glossaryQ, setGlossaryQ] = useState('')
    // Compare
    const [regionA, setRegionA] = useState('')
    const [regionB, setRegionB] = useState('')
    const [compareResult, setCompareResult] = useState<CompareRunResponse | null>(null)
    const [compareLoading, setCompareLoading] = useState(false)
    // Insights + quick stats
    const [insights, setInsights] = useState<LearningInsight[]>([])
    const [quickStats, setQuickStats] = useState<ToolsQuickStats | null>(null)
    const [insightsLoading, setInsightsLoading] = useState(false)
    // Data Sources
    const [apiStatuses, setApiStatuses] = useState<Record<string, { ok: boolean; loading: boolean }>>({})
    const [marineLat, setMarineLat] = useState('40.7')
    const [marineLon, setMarineLon] = useState('-74.0')
    const [marineData, setMarineData] = useState<any>(null)
    const [marineLoading, setMarineLoading] = useState(false)
    const [selectedApi, setSelectedApi] = useState<string>('open-meteo-marine')

    useEffect(() => {
        if (mode === 'glossary') {
            apiClient.getToolsGlossary(glossaryQ || undefined).then(setGlossary).catch(() => { })
        }
    }, [mode, glossaryQ])

    useEffect(() => {
        if (mode !== 'learn') return
        setInsightsLoading(true)
        Promise.all([apiClient.getLearningInsights(), apiClient.getToolsQuickStats()])
            .then(([ins, qs]) => { setInsights(ins); setQuickStats(qs) })
            .catch(() => { setInsights([]); setQuickStats(null) })
            .finally(() => setInsightsLoading(false))
    }, [mode])

    useEffect(() => {
        if (mode !== 'datasources') return
        const apis = [
            'open-meteo-marine', 'erddap', 'gebco', 'wod', 'ooi', 'icoads', 'ioos', 'onc', 'argovis', 'obis', 'gfw'
        ]
        setApiStatuses(Object.fromEntries(apis.map(a => [a, { ok: false, loading: true }])))
        Promise.allSettled([
            apiClient.openMeteoMarinePing(),
            apiClient.erddapPing(),
            apiClient.gebcoPing(),
            apiClient.wodPing(),
            apiClient.ooiPing(),
            apiClient.icoadsPing(),
            apiClient.ioosPing(),
            apiClient.oncPing(),
            apiClient.argovisPing(),
            apiClient.obisPing(),
            apiClient.gfwPing(),
        ]).then(results => {
            const statuses: Record<string, { ok: boolean; loading: boolean }> = {}
            const keys = ['open-meteo-marine', 'erddap', 'gebco', 'wod', 'ooi', 'icoads', 'ioos', 'onc', 'argovis', 'obis', 'gfw']
            results.forEach((r, i) => { statuses[keys[i]] = { ok: r.status === 'fulfilled' && !!r.value?.ok, loading: false } })
            setApiStatuses(statuses)
        })
    }, [mode])

    async function fetchMarineData() {
        setMarineLoading(true)
        try {
            const data = await apiClient.getSeaTemperature(parseFloat(marineLat), parseFloat(marineLon), 3)
            setMarineData(data)
        } catch { setMarineData(null) }
        setMarineLoading(false)
    }

    async function runCalc() {
        if (!depth) return
        setCalcLoading(true)
        try { setCalcResult(await apiClient.calculatePressureDepth({ depth_m: parseFloat(depth), latitude: lat ? parseFloat(lat) : undefined })) }
        catch { /* noop */ } finally { setCalcLoading(false) }
    }

    async function runCompare() {
        if (!regionA || !regionB) return
        setCompareLoading(true)
        try { setCompareResult(await apiClient.runStudyCompare({ region_a: regionA, region_b: regionB })) }
        catch { /* noop */ } finally { setCompareLoading(false) }
    }

    return (
        <div style={{ backgroundColor: '#f5f5f7', minHeight: '100vh', position: 'relative', fontFamily: FONT, overflow: 'hidden' }}>
            {/* ── Apple-like Animated 4K Liquid Ocean Background ── */}
            <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
                {/* Flowing Ocean Image (Animated) */}
                <div style={{
                    position: 'absolute', inset: 0,
                    backgroundImage: 'url(https://images.unsplash.com/photo-1551244072-5d12893278ab?q=80&w=3840&auto=format&fit=crop)',
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

            {/* Floating Pill Nav */}
            <div style={{ position: 'fixed', top: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 50, width: '90%', maxWidth: 960 }}>
                <div style={{ ...GLASS, borderRadius: 99, padding: '10px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 2px 0 rgba(255,255,255,0.9) inset, 0 12px 36px rgba(0,0,0,0.1)' }}>
                    <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none', fontSize: 13, fontWeight: 600, color: '#6e6e73' }}>
                        <ChevronLeft style={{ width: 14, height: 14 }} /> Home
                    </Link>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Waves style={{ width: 16, height: 16, color: '#0071e3' }} />
                        <span style={{ fontSize: 14, fontWeight: 800, color: '#000' }}>Research Tools</span>
                    </div>
                    <Link href="/dashboard" style={{ padding: '8px 18px', borderRadius: 99, background: '#000', color: '#fff', fontSize: 12, fontWeight: 700, textDecoration: 'none' }}>Dashboard</Link>
                </div>
            </div>

            {/* Content */}
            <div style={{ position: 'relative', zIndex: 10, maxWidth: 820, margin: '0 auto', padding: '100px 24px 60px' }}>

                {/* Quick stats bar — always visible */}
                {quickStats && mode === 'learn' && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
                        style={{ ...GLASS, padding: '14px 20px', marginBottom: 24, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
                        {[
                            { label: 'Min Temp', value: quickStats.min_temperature != null ? `${quickStats.min_temperature.toFixed(1)}°C` : '—', color: '#0071e3' },
                            { label: 'Max Temp', value: quickStats.max_temperature != null ? `${quickStats.max_temperature.toFixed(1)}°C` : '—', color: '#ff3b30' },
                            { label: 'Min Salinity', value: quickStats.min_salinity != null ? `${quickStats.min_salinity.toFixed(2)} PSU` : '—', color: '#5e5ce6' },
                            { label: 'Max Salinity', value: quickStats.max_salinity != null ? `${quickStats.max_salinity.toFixed(2)} PSU` : '—', color: '#34c759' },
                            { label: 'Median Depth', value: quickStats.median_depth != null ? `${quickStats.median_depth.toFixed(0)} m` : '—', color: '#ff9f0a' },
                            { label: 'Latest Profile', value: quickStats.latest_profile_date ? new Date(quickStats.latest_profile_date).toLocaleDateString() : '—', color: '#000' },
                        ].map(k => (
                            <div key={k.label}>
                                <p style={{ fontSize: '1rem', fontWeight: 900, letterSpacing: '-0.03em', color: k.color }}>{k.value}</p>
                                <p style={{ fontSize: 9, fontWeight: 700, color: '#a0a0a5', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{k.label}</p>
                            </div>
                        ))}
                    </motion.div>
                )}

                {/* Mode tabs */}
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 32 }}>
                    <div style={{ ...GLASS, display: 'flex', padding: 5, gap: 4, borderRadius: 99 }}>
                        {MODES.map(m => (
                            <button key={m.id} onClick={() => setMode(m.id)}
                                style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '9px 20px', borderRadius: 99, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 700, fontFamily: FONT, transition: 'all 0.18s', background: mode === m.id ? '#fff' : 'transparent', color: mode === m.id ? '#000' : '#6e6e73', boxShadow: mode === m.id ? '0 2px 10px rgba(0,0,0,0.12)' : 'none' }}>
                                <m.icon style={{ width: 14, height: 14 }} />{m.label}
                            </button>
                        ))}
                    </div>
                </div>

                <AnimatePresence mode="wait">
                    {/* Calculator */}
                    {mode === 'calc' && (
                        <motion.div key="calc" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
                            <div style={{ ...GLASS, padding: '32px' }}>
                                <h2 style={{ fontSize: '1.5rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 6 }}>Pressure ↔ Depth</h2>
                                <p style={{ fontSize: 13, color: '#6e6e73', marginBottom: 24 }}>Convert between ocean depth (m) and pressure (dbar)</p>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                                    <InputField label="Depth (m)" value={depth} onChange={setDepth} placeholder="e.g. 1000" />
                                    <InputField label="Latitude (optional)" value={lat} onChange={setLat} placeholder="e.g. 45.0" />
                                </div>
                                <button onClick={() => void runCalc()} disabled={!depth || calcLoading}
                                    style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '13px 28px', borderRadius: 99, background: '#000', color: '#fff', border: 'none', cursor: depth ? 'pointer' : 'not-allowed', fontSize: 14, fontWeight: 800, fontFamily: FONT, opacity: depth ? 1 : 0.4, boxShadow: '0 4px 16px rgba(0,0,0,0.2)', transition: 'all 0.15s' }}>
                                    {calcLoading ? <Loader2 style={{ width: 14, height: 14, animation: 'spin 1s linear infinite' }} /> : null}
                                    {calcLoading ? 'Calculating…' : 'Calculate'} <ArrowRight style={{ width: 14, height: 14 }} />
                                </button>
                                {calcResult && (
                                    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                                        style={{ marginTop: 20, padding: '20px 24px', borderRadius: 18, background: 'rgba(0,113,227,0.08)', border: '1px solid rgba(0,113,227,0.2)' }}>
                                        <p style={{ fontSize: 11, fontWeight: 700, color: '#0071e3', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 10 }}>Result</p>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                                            {[{ label: 'Depth', value: `${calcResult.depth_m.toFixed(1)} m` }, { label: 'Pressure', value: `${calcResult.pressure_dbar.toFixed(1)} dbar` }, { label: 'Latitude', value: `${calcResult.latitude.toFixed(2)}°` }].map(r => (
                                                <div key={r.label}>
                                                    <p style={{ fontSize: 11, color: '#6e6e73', fontWeight: 600, marginBottom: 2 }}>{r.label}</p>
                                                    <p style={{ fontSize: '1.2rem', fontWeight: 900, color: '#000', letterSpacing: '-0.03em' }}>{r.value}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}
                            </div>
                        </motion.div>
                    )}

                    {/* Glossary */}
                    {mode === 'glossary' && (
                        <motion.div key="glossary" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
                            <div style={{ ...GLASS, padding: '24px', marginBottom: 16 }}>
                                <InputField label="Search glossary" value={glossaryQ} onChange={setGlossaryQ} placeholder="e.g. salinity, oxygen, CTD" type="text" />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                {glossary.slice(0, 15).map((item, i) => (
                                    <motion.div key={item.term} variants={fadeUp} initial="hidden" animate="visible" custom={i} style={{ ...GLASS, padding: '18px 22px' }}>
                                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                                            <div>
                                                <p style={{ fontSize: 14, fontWeight: 800, color: '#000', marginBottom: 4 }}>{item.term}</p>
                                                <p style={{ fontSize: 13, color: '#3a3a3c', lineHeight: 1.55 }}>{item.short_definition}</p>
                                                {item.units && <p style={{ fontSize: 11, color: '#6e6e73', fontWeight: 600, marginTop: 4 }}>Units: {item.units}</p>}
                                            </div>
                                            <span style={{ fontSize: 10, fontWeight: 700, padding: '4px 10px', borderRadius: 99, background: 'rgba(0,113,227,0.1)', color: '#0071e3', whiteSpace: 'nowrap', textTransform: 'uppercase', flexShrink: 0 }}>{item.category}</span>
                                        </div>
                                    </motion.div>
                                ))}
                                {glossary.length === 0 && <p style={{ textAlign: 'center', color: '#6e6e73', fontSize: 13, padding: '40px 0' }}>No glossary terms found — connect backend</p>}
                            </div>
                        </motion.div>
                    )}

                    {/* Compare */}
                    {mode === 'compare' && (
                        <motion.div key="compare" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
                            <div style={{ ...GLASS, padding: '32px' }}>
                                <h2 style={{ fontSize: '1.5rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 6 }}>Compare Ocean Regions</h2>
                                <p style={{ fontSize: 13, color: '#6e6e73', marginBottom: 24 }}>Compare float and profile density between two regions</p>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                                    <InputField label="Region A" value={regionA} onChange={setRegionA} placeholder="e.g. North Atlantic" type="text" />
                                    <InputField label="Region B" value={regionB} onChange={setRegionB} placeholder="e.g. Pacific" type="text" />
                                </div>
                                <button onClick={() => void runCompare()} disabled={!regionA || !regionB || compareLoading}
                                    style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '13px 28px', borderRadius: 99, background: '#000', color: '#fff', border: 'none', cursor: (regionA && regionB) ? 'pointer' : 'not-allowed', fontSize: 14, fontWeight: 800, fontFamily: FONT, opacity: (regionA && regionB) ? 1 : 0.4, boxShadow: '0 4px 16px rgba(0,0,0,0.2)', transition: 'all 0.15s' }}>
                                    {compareLoading ? <Loader2 style={{ width: 14, height: 14, animation: 'spin 1s linear infinite' }} /> : <GitCompare style={{ width: 14, height: 14 }} />}
                                    {compareLoading ? 'Comparing…' : 'Compare Regions'}
                                </button>
                                {compareResult && (
                                    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                                        style={{ marginTop: 20, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                                        {[
                                            { label: regionA + ' Floats', value: compareResult.floats_a, sub: `${compareResult.profiles_a.toLocaleString()} profiles`, color: '#0071e3' },
                                            { label: regionB + ' Floats', value: compareResult.floats_b, sub: `${compareResult.profiles_b.toLocaleString()} profiles`, color: '#34c759' },
                                            { label: 'Δ Difference', value: Math.abs(compareResult.delta_floats), sub: compareResult.delta_floats > 0 ? `${regionA} leads` : `${regionB} leads`, color: compareResult.delta_floats > 0 ? '#0071e3' : '#ff3b30' },
                                        ].map(r => (
                                            <div key={r.label} style={{ padding: '18px', borderRadius: 18, background: `${r.color}0f`, border: `1px solid ${r.color}25`, textAlign: 'center' }}>
                                                <p style={{ fontSize: '1.8rem', fontWeight: 900, color: r.color, letterSpacing: '-0.04em' }}>{r.value}</p>
                                                <p style={{ fontSize: 11, color: '#6e6e73', fontWeight: 600, marginTop: 4 }}>{r.label}</p>
                                                <p style={{ fontSize: 10, color: '#a0a0a5', marginTop: 2 }}>{r.sub}</p>
                                            </div>
                                        ))}
                                    </motion.div>
                                )}
                                {compareResult?.statistics?.temperature && (
                                    <div style={{ marginTop: 14, borderRadius: 16, border: '1px solid rgba(0,0,0,0.08)', background: 'rgba(0,0,0,0.03)', padding: '12px 14px' }}>
                                        <p style={{ fontSize: 11, fontWeight: 700, color: '#6e6e73', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4 }}>
                                            Advanced statistics
                                        </p>
                                        <p style={{ fontSize: 12, color: '#374151' }}>
                                            Temperature p-value: {compareResult.statistics.temperature.p_value_approx ?? 'n/a'} | effect size (d): {compareResult.statistics.temperature.effect_size_cohen_d ?? 'n/a'} | anomaly score: {compareResult.statistics.temperature.anomaly_score ?? 'n/a'}
                                        </p>
                                        <p style={{ fontSize: 12, color: '#4b5563', marginTop: 3 }}>
                                            {compareResult.statistics.temperature.interpretation || 'No interpretation available'}
                                        </p>
                                        {(compareResult.insights || []).length > 0 && (
                                            <div style={{ marginTop: 6 }}>
                                                {(compareResult.insights || []).slice(0, 3).map((insight, index) => (
                                                    <p key={`compare-insight-${index}`} style={{ fontSize: 11, color: '#4b5563' }}>
                                                        - {insight}
                                                    </p>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )}

                    {/* Insights */}
                    {mode === 'learn' && (
                        <motion.div key="learn" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
                            {insightsLoading ? (
                                <div style={{ textAlign: 'center', padding: '60px 0', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
                                    <Loader2 style={{ width: 28, height: 28, color: '#0071e3', animation: 'spin 1s linear infinite' }} />
                                    <p style={{ fontSize: 13, color: '#6e6e73', fontWeight: 600 }}>Loading insights from backend…</p>
                                </div>
                            ) : (
                                <>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 14 }}>
                                        {insights.map((ins, i) => (
                                            <motion.div key={ins.title} variants={fadeUp} initial="hidden" animate="visible" custom={i}
                                                style={{ ...GLASS, padding: '22px 24px' }}>
                                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                                                    <div style={{ width: 36, height: 36, borderRadius: 12, background: 'rgba(0,113,227,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                                        <BarChart2 style={{ width: 16, height: 16, color: '#0071e3' }} />
                                                    </div>
                                                    <div>
                                                        <p style={{ fontSize: 14, fontWeight: 800, color: '#000', marginBottom: 6 }}>{ins.title}</p>
                                                        <p style={{ fontSize: 13, color: '#3a3a3c', lineHeight: 1.6 }}>{ins.detail}</p>
                                                        {ins.metric && (
                                                            <div style={{ marginTop: 10, display: 'inline-block', padding: '4px 12px', borderRadius: 99, background: 'rgba(52,199,89,0.12)', border: '1px solid rgba(52,199,89,0.3)' }}>
                                                                <span style={{ fontSize: 12, fontWeight: 700, color: '#34c759' }}>{ins.metric}</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </motion.div>
                                        ))}
                                        {insights.length === 0 && (
                                            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '60px 0' }}>
                                                <Lightbulb style={{ width: 32, height: 32, color: '#b0b0b5', margin: '0 auto 12px' }} />
                                                <p style={{ fontSize: 14, fontWeight: 700, color: '#6e6e73' }}>No insights available — start your backend to load live data</p>
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
                        </motion.div>
                    )}

                    {/* Data Sources */}
                    {mode === 'datasources' && (
                        <motion.div key="datasources" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
                            <div style={{ ...GLASS, padding: '24px', marginBottom: 16 }}>
                                <h2 style={{ fontSize: '1.3rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 6 }}>External Data Sources</h2>
                                <p style={{ fontSize: 13, color: '#6e6e73', marginBottom: 20 }}>Free APIs for ocean data collection</p>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
                                    {[
                                        { id: 'open-meteo-marine', name: 'Open-Meteo Marine', icon: Cloud, free: true, desc: 'Waves, wind, SST' },
                                        { id: 'erddap', name: 'ERDDAP', icon: Globe, free: true, desc: '1000+ datasets' },
                                        { id: 'gebco', name: 'GEBCO', icon: Anchor, free: true, desc: 'Bathymetry' },
                                        { id: 'wod', name: 'World Ocean DB', icon: Thermometer, free: true, desc: 'Historical profiles' },
                                        { id: 'ooi', name: 'OOI', icon: Waves, free: true, desc: 'Real-time sensors' },
                                        { id: 'icoads', name: 'ICOADS', icon: Cloud, free: true, desc: 'Surface observations' },
                                        { id: 'ioos', name: 'IOOS', icon: Ship, free: true, desc: 'US coastal data' },
                                        { id: 'onc', name: 'Ocean Networks CA', icon: Anchor, free: true, desc: 'Canada observatories' },
                                        { id: 'argovis', name: 'ArgoVis', icon: Waves, free: false, desc: 'Argo float data' },
                                        { id: 'obis', name: 'OBIS', icon: Fish, free: true, desc: 'Marine biodiversity' },
                                        { id: 'gfw', name: 'Global Fishing Watch', icon: Fish, free: false, desc: 'Vessel tracking' },
                                    ].map(api => (
                                        <div key={api.id} onClick={() => setSelectedApi(api.id)}
                                            style={{ padding: '14px 16px', borderRadius: 14, border: selectedApi === api.id ? '2px solid #0071e3' : '1.5px solid rgba(0,0,0,0.08)', cursor: 'pointer', background: selectedApi === api.id ? 'rgba(0,113,227,0.05)' : 'rgba(255,255,255,0.6)', transition: 'all 0.15s' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                                <api.icon style={{ width: 14, height: 14, color: '#0071e3' }} />
                                                <span style={{ fontSize: 13, fontWeight: 700, color: '#000' }}>{api.name}</span>
                                                {api.free && <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 99, background: '#34c759', color: '#fff' }}>FREE</span>}
                                            </div>
                                            <p style={{ fontSize: 11, color: '#6e6e73' }}>{api.desc}</p>
                                            {apiStatuses[api.id] && (
                                                <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                                                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: apiStatuses[api.id].loading ? '#ffa500' : apiStatuses[api.id].ok ? '#34c759' : '#ff3b30' }} />
                                                    <span style={{ fontSize: 10, color: '#6e6e73' }}>{apiStatuses[api.id].loading ? 'Checking...' : apiStatuses[api.id].ok ? 'Connected' : 'Unavailable'}</span>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Demo: Fetch marine data */}
                            {selectedApi === 'open-meteo-marine' && (
                                <div style={{ ...GLASS, padding: '24px' }}>
                                    <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#000', marginBottom: 6 }}>Demo: Sea Surface Temperature</h3>
                                    <p style={{ fontSize: 12, color: '#6e6e73', marginBottom: 16 }}>Fetch SST forecast from Open-Meteo Marine API</p>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 12, alignItems: 'end' }}>
                                        <InputField label="Latitude" value={marineLat} onChange={setMarineLat} placeholder="e.g. 40.7" type="text" />
                                        <InputField label="Longitude" value={marineLon} onChange={setMarineLon} placeholder="e.g. -74.0" type="text" />
                                        <button onClick={() => void fetchMarineData()} disabled={marineLoading}
                                            style={{ padding: '12px 20px', borderRadius: 14, background: '#000', color: '#fff', border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 700 }}>
                                            {marineLoading ? 'Loading...' : 'Fetch Data'}
                                        </button>
                                    </div>
                                    {marineData && (
                                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ marginTop: 16, padding: 14, borderRadius: 12, background: 'rgba(0,113,227,0.08)' }}>
                                            <p style={{ fontSize: 11, color: '#0071e3', fontWeight: 700, marginBottom: 8 }}>Response Data (JSON)</p>
                                            <pre style={{ fontSize: 10, color: '#3a3a3c', overflow: 'auto', maxHeight: 200 }}>{JSON.stringify(marineData, null, 2)}</pre>
                                        </motion.div>
                                    )}
                                </div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <style>{`
                @keyframes orb1 { 0%,100% { transform:translate(0,0) scale(1); } 33% { transform:translate(80px,-100px) scale(1.1); } 66% { transform:translate(-60px,60px) scale(0.92); } }
                @keyframes orb2 { 0%,100% { transform:translate(0,0) scale(1); } 30% { transform:translate(-100px,80px) scale(1.12); } 70% { transform:translate(70px,-50px) scale(0.9); } }
                @keyframes orb3 { 0%,100% { transform:translate(0,0) scale(1); } 40% { transform:translate(50px,90px) scale(1.08); } 80% { transform:translate(-80px,-60px) scale(0.95); } }
                @keyframes spin { to { transform:rotate(360deg); } }
                input::placeholder { color: #b0b0b5; }
            `}</style>
        </div>
    )
}
