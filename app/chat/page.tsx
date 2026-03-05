'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Send, Mic, MicOff, Copy, Check, Trash2, Download,
    ChevronDown, ChevronRight, Zap, Terminal, RefreshCw,
    Clock, MessageSquare, Database, Globe,
} from 'lucide-react'
import { OceanAIBadge, FloatMarkIcon } from '@/components/Brand'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
    apiClient,
    type ChatMessage,
    type ChatProvider,
    type ChatProviderMetric,
} from '@/lib/api-client'

interface EnrichedMessage extends ChatMessage {
    id: string
    timestamp: Date
}

// ── Apple Design System ────────────────────────────────────────────────────────
const F = "var(--font-inter), -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', sans-serif"

const APPLE_BG = '#f5f5f7'
const APPLE_TEXT = '#1d1d1f'
const APPLE_SUBTEXT = '#86868b'
const APPLE_BLUE = '#0071e3'
const APPLE_BLUE_HOVER = '#0077ED'
const APPLE_GREEN = '#34c759'
const APPLE_RED = '#ff3b30'

const GLASS: React.CSSProperties = {
    background: 'rgba(255, 255, 255, 0.72)',
    backdropFilter: 'saturate(180%) blur(20px)',
    WebkitBackdropFilter: 'saturate(180%) blur(20px)',
    border: '1px solid rgba(255,255,255,0.6)',
    boxShadow: '0 4px 24px rgba(0,0,0,0.04)',
    borderRadius: 20,
}

const CARD: React.CSSProperties = {
    background: '#ffffff',
    border: '1px solid rgba(0,0,0,0.05)',
    boxShadow: '0 2px 12px rgba(0,0,0,0.03)',
    borderRadius: 18,
}

const PROVIDERS: Array<{ id: ChatProvider; label: string }> = [
    { id: 'auto', label: 'Auto' },
    { id: 'groq', label: 'Groq 70B' },
    { id: 'gemini', label: 'Gemini' },
    { id: 'openai', label: 'OpenAI' },
    { id: 'ollama', label: 'Ollama' },
]

const STARTERS = [
    { icon: '🌡', label: 'Temperature', q: 'What is the average ocean temperature across all floats?' },
    { icon: '🌊', label: 'Fleet Status', q: 'How many ARGO floats are currently active worldwide?' },
    { icon: '🧂', label: 'Salinity', q: 'Show me salinity trends across different ocean basins' },
    { icon: '🌍', label: 'Basins', q: 'Which ocean basin has the most active floats right now?' },
    { icon: '📍', label: 'Profiles', q: 'Show me the most recent float profiles with measurements' },
    { icon: '🔬', label: 'BGC Data', q: 'What BGC-Argo float biogeochemical data is available?' },
]

// ── Helpers ───────────────────────────────────────────────────────────────────
function uid() { return Math.random().toString(36).slice(2, 10) }
function timeStr(d: Date) { return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) }
function fmt(n?: number) { return typeof n === 'number' ? `${(n * 100).toFixed(0)}%` : '—' }
function ms(n?: number) { return typeof n === 'number' ? `${Math.round(n)}ms` : '—' }

function makeFollowUps(content: string, hasData: boolean): string[] {
    const t = content.toLowerCase(), pool: string[] = []
    if (t.includes('temperatur')) pool.push('What is the temperature trend over time?')
    if (t.includes('salinity')) pool.push('How does salinity vary by depth?')
    if (t.includes('basin')) pool.push('Which ocean basin has the most active floats?')
    if (t.includes('float') || t.includes('wmo')) pool.push('Show more details about these floats')
    if (t.includes('pacific')) pool.push('Compare Pacific vs Atlantic float data')
    if (t.includes('atlantic')) pool.push('What is the Atlantic temperature range?')
    if (t.includes('depth')) pool.push('Show measurements at deeper pressure levels')
    if (hasData) pool.push('Can you summarize this data in a table?')
    const generic = ['Show the latest ocean measurements', 'Which region has the most floats?', 'Compare temperature and salinity trends']
    for (const g of generic) { if (!pool.includes(g)) pool.push(g) }
    return pool.slice(0, 3)
}

function exportMarkdown(messages: EnrichedMessage[]) {
    const lines = ['# FloatChat Conversation\n', `_${new Date().toLocaleString()}_\n`]
    for (const m of messages) {
        lines.push(`\n## ${m.role === 'user' ? '🙋 You' : '🤖 Ocean AI'} · ${timeStr(m.timestamp)}\n`)
        lines.push(m.content)
        if (m.sql_query) lines.push('\n```sql\n' + m.sql_query + '\n```')
    }
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/markdown' }))
    a.download = `floatchat-${Date.now()}.md`; a.click()
}

// ── Copy button ───────────────────────────────────────────────────────────────
function CopyBtn({ text }: { text: string }) {
    const [done, setDone] = useState(false)
    return (
        <button onClick={() => navigator.clipboard.writeText(text).then(() => { setDone(true); setTimeout(() => setDone(false), 2000) })}
            style={{ width: 26, height: 26, borderRadius: 8, border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.2s', background: done ? 'rgba(52,199,89,0.1)' : 'transparent' }}
            onMouseEnter={e => { if (!done) e.currentTarget.style.background = 'rgba(0,0,0,0.05)' }}
            onMouseLeave={e => { if (!done) e.currentTarget.style.background = 'transparent' }}>
            {done ? <Check style={{ width: 12, height: 12, color: APPLE_GREEN }} /> : <Copy style={{ width: 12, height: 12, color: APPLE_SUBTEXT }} />}
        </button>
    )
}

// ── SQL block ─────────────────────────────────────────────────────────────────
function SqlBlock({ sql }: { sql: string }) {
    const [open, setOpen] = useState(false)
    const KEYWORDS = /\b(SELECT|FROM|WHERE|JOIN|LEFT|INNER|GROUP BY|ORDER BY|LIMIT|AND|OR|ON|AS|COUNT|AVG|SUM|MAX|MIN|DISTINCT|HAVING|WITH|INSERT|UPDATE|DELETE|CREATE|DROP)\b/g
    return (
        <div style={{ background: '#f5f5f7', border: '1px solid rgba(0,0,0,0.05)', borderRadius: 12, overflow: 'hidden', marginTop: 12 }}>
            <button onClick={() => setOpen(o => !o)} style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '10px 14px', background: 'none', border: 'none', cursor: 'pointer', width: '100%', fontFamily: F }}>
                <Terminal style={{ width: 14, height: 14, color: APPLE_BLUE }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: APPLE_TEXT, letterSpacing: '-0.01em' }}>SQL Query</span>
                {open ? <ChevronDown style={{ width: 14, height: 14, color: APPLE_SUBTEXT, marginLeft: 'auto' }} /> : <ChevronRight style={{ width: 14, height: 14, color: APPLE_SUBTEXT, marginLeft: 'auto' }} />}
            </button>
            <AnimatePresence>
                {open && (
                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} style={{ overflow: 'hidden' }}>
                        <div style={{ position: 'relative', padding: '0 14px 14px' }}>
                            <div style={{ background: '#ffffff', borderRadius: 8, padding: 12, border: '1px solid rgba(0,0,0,0.04)' }}>
                                <pre style={{ margin: 0, fontSize: 12, lineHeight: 1.6, fontFamily: "'SF Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace", whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: APPLE_TEXT }}>
                                    {sql.split('\n').map((line, i) => (
                                        <span key={i}>
                                            {line.split(KEYWORDS).map((part, j) =>
                                                KEYWORDS.test(part)
                                                    ? <span key={j} style={{ color: APPLE_BLUE, fontWeight: 600 }}>{part}</span>
                                                    : <span key={j}>{part}</span>
                                            )}
                                            {'\n'}
                                        </span>
                                    ))}
                                </pre>
                            </div>
                            <div style={{ position: 'absolute', top: 4, right: 20 }}><CopyBtn text={sql} /></div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

// ── Data table ────────────────────────────────────────────────────────────────
function DataTable({ data, rowCount }: { data: unknown[]; rowCount?: number }) {
    const [open, setOpen] = useState(true)
    if (!Array.isArray(data) || !data.length) return null
    const keys = Object.keys(data[0] as object)
    return (
        <div style={{ background: '#f5f5f7', border: '1px solid rgba(0,0,0,0.05)', borderRadius: 12, overflow: 'hidden', marginTop: 12 }}>
            <button onClick={() => setOpen(o => !o)} style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '10px 14px', background: 'none', border: 'none', cursor: 'pointer', width: '100%', fontFamily: F }}>
                <Database style={{ width: 14, height: 14, color: APPLE_GREEN }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: APPLE_TEXT, letterSpacing: '-0.01em' }}>Data</span>
                <span style={{ fontSize: 11, color: APPLE_TEXT, marginLeft: 6, background: 'rgba(0,0,0,0.05)', padding: '2px 8px', borderRadius: 99, fontWeight: 500 }}>{rowCount ?? data.length} rows</span>
                {open ? <ChevronDown style={{ width: 14, height: 14, color: APPLE_SUBTEXT, marginLeft: 'auto' }} /> : <ChevronRight style={{ width: 14, height: 14, color: APPLE_SUBTEXT, marginLeft: 'auto' }} />}
            </button>
            <AnimatePresence>
                {open && (
                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} style={{ overflow: 'hidden' }}>
                        <div style={{ overflowX: 'auto', padding: '0 14px 14px' }}>
                            <div style={{ background: '#ffffff', borderRadius: 8, border: '1px solid rgba(0,0,0,0.04)', overflow: 'hidden' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, fontFamily: F }}>
                                    <thead style={{ background: '#f9f9fb' }}>
                                        <tr>{keys.map(k => <th key={k} style={{ textAlign: 'left', padding: '8px 12px', fontSize: 11, fontWeight: 600, color: APPLE_SUBTEXT, borderBottom: '1px solid rgba(0,0,0,0.05)', whiteSpace: 'nowrap' }}>{k}</th>)}</tr>
                                    </thead>
                                    <tbody>
                                        {data.slice(0, 6).map((row, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                                                {keys.map(k => <td key={k} style={{ padding: '8px 12px', color: APPLE_TEXT, whiteSpace: 'nowrap', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>{String((row as Record<string, unknown>)[k] ?? '—')}</td>)}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            {data.length > 6 && <p style={{ fontSize: 11, color: APPLE_SUBTEXT, margin: '8px 0 0 4px', fontWeight: 500 }}>Showing 6 of {rowCount ?? data.length} rows</p>}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

// ── Streaming hook ────────────────────────────────────────────────────────────
function useStream(text: string, active: boolean, onDone: () => void) {
    const [out, setOut] = useState('')
    useEffect(() => {
        if (!active) { setOut(text); return }
        setOut(''); let i = 0
        const words = text.split(' ')
        const iv = setInterval(() => {
            i += 3; setOut(words.slice(0, i).join(' '))
            if (i >= words.length) { clearInterval(iv); setOut(text); onDone() }
        }, 16)
        return () => clearInterval(iv)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [active, text])
    return out
}

// ── Message bubble ────────────────────────────────────────────────────────────
function Bubble({ msg, isNew, onFollowUp }: { msg: EnrichedMessage; isNew: boolean; onFollowUp: (q: string) => void }) {
    const [done, setDone] = useState(!isNew || msg.role === 'user')
    const text = useStream(msg.content, isNew && msg.role === 'assistant', () => setDone(true))
    const chips = msg.role === 'assistant' && done ? makeFollowUps(msg.content, (msg.data?.length ?? 0) > 0) : []

    if (msg.role === 'user') return (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
            style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '4px 0' }}>
            <div style={{ maxWidth: '80%' }}>
                <div style={{ background: APPLE_BLUE, padding: '12px 18px', borderRadius: '20px 20px 4px 20px', boxShadow: '0 4px 14px rgba(0,113,227,0.2)' }}>
                    <p style={{ fontSize: 16, lineHeight: 1.5, color: '#fff', margin: 0, fontWeight: 400, letterSpacing: '-0.01em' }}>{msg.content}</p>
                </div>
            </div>
        </motion.div>
    )

    return (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
            style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '4px 0' }}>
            <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                <div style={{ flexShrink: 0, width: 32, height: 32, borderRadius: '50%', background: '#fff', border: '1px solid rgba(0,0,0,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                    <OceanAIBadge size={20} />
                </div>
                <div style={{ flex: 1, minWidth: 0, paddingBottom: 12 }}>
                    {/* Content */}
                    <div className="prose prose-sm max-w-none apple-prose" style={{ fontSize: 16, lineHeight: 1.6, color: APPLE_TEXT, fontWeight: 400, letterSpacing: '-0.01em' }}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
                        {!done && <span style={{ display: 'inline-block', width: 2, height: 16, background: APPLE_BLUE, marginLeft: 2, borderRadius: 1, animation: 'blink 0.8s ease-in-out infinite', verticalAlign: 'middle' }} />}
                    </div>

                    {/* Metadata */}
                    {done && msg.role === 'assistant' && (
                        <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>

                            {/* Tags */}
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                {msg.source && <Pill text={`Source: ${msg.source}`} color={APPLE_BLUE} />}
                                {msg.cached && <Pill text="Cached" color={APPLE_SUBTEXT} />}
                            </div>

                            {/* SQL & Data */}
                            {msg.sql_query && <SqlBlock sql={msg.sql_query} />}
                            {(msg.data?.length ?? 0) > 0 && <DataTable data={msg.data as unknown[]} rowCount={msg.row_count} />}

                            {/* Footer */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
                                <CopyBtn text={msg.content} />
                                <span style={{ fontSize: 12, color: APPLE_SUBTEXT, fontWeight: 500 }}>{timeStr(msg.timestamp)}</span>
                                {(msg.provider_metrics?.length ?? 0) > 0 && msg.provider_metrics!.map((m: ChatProviderMetric, i: number) => (
                                    <span key={i} style={{ fontSize: 12, color: APPLE_SUBTEXT, display: 'flex', alignItems: 'center', gap: 4 }}>
                                        <Zap style={{ width: 10, height: 10, color: m.success ? APPLE_GREEN : APPLE_RED }} />
                                        {m.provider} {ms(m.latency_ms)}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Follow-ups */}
            <AnimatePresence>
                {chips.length > 0 && (
                    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                        style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginLeft: 46 }}>
                        {chips.map(q => (
                            <button key={q} onClick={() => onFollowUp(q)}
                                style={{ padding: '8px 14px', fontSize: 13, fontWeight: 500, color: APPLE_TEXT, cursor: 'pointer', border: '1px solid rgba(0,0,0,0.08)', borderRadius: 99, fontFamily: F, transition: 'all 0.2s', background: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}
                                onMouseEnter={e => { e.currentTarget.style.background = '#f9f9fb'; e.currentTarget.style.borderColor = 'rgba(0,0,0,0.15)' }}
                                onMouseLeave={e => { e.currentTarget.style.background = '#fff'; e.currentTarget.style.borderColor = 'rgba(0,0,0,0.08)' }}>
                                {q}
                            </button>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    )
}

function Pill({ text, color = APPLE_SUBTEXT }: { text: string; color?: string }) {
    return <span style={{ padding: '3px 10px', fontSize: 11, fontWeight: 500, color, background: 'rgba(0,0,0,0.03)', border: '1px solid rgba(0,0,0,0.05)', borderRadius: 99, fontFamily: F }}>{text}</span>
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ChatPage() {
    const [messages, setMessages] = useState<EnrichedMessage[]>([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [provider, setProvider] = useState<ChatProvider>('auto')
    const [status, setStatus] = useState<'checking' | 'online' | 'degraded' | 'offline'>('checking')
    const [listening, setListening] = useState(false)
    const [newId, setNewId] = useState<string | null>(null)
    const bottomRef = useRef<HTMLDivElement>(null)
    const textRef = useRef<HTMLTextAreaElement>(null)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recRef = useRef<any>(null)

    useEffect(() => {
        if (!loading) bottomRef.current?.scrollIntoView({ behavior: 'auto' })
    }, [messages, loading])

    const resize = useCallback(() => {
        const el = textRef.current; if (!el) return
        el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 120) + 'px'
    }, [])

    useEffect(() => {
        apiClient.healthCheck()
            .then(h => setStatus(h.status === 'healthy' ? 'online' : 'degraded'))
            .catch(() => setStatus('offline'))
    }, [])

    async function send(text?: string) {
        const msg = (text ?? input).trim()
        if (!msg || loading) return
        setInput(''); if (textRef.current) textRef.current.style.height = 'auto'
        const uid_val = uid()
        setMessages(p => [...p, { id: uid_val, role: 'user', content: msg, timestamp: new Date() }])
        setLoading(true)
        try {
            const res = await apiClient.sendChatMessage(msg, provider)
            const aid = uid(); setNewId(aid)
            setMessages(p => [...p, {
                id: aid, role: 'assistant', timestamp: new Date(),
                content: res.response || 'No response generated.',
                sql_query: res.sql_query, data: res.data as unknown[],
                row_count: res.row_count, source: res.source, query_type: res.query_type,
                provider_metrics: res.provider_metrics, cached: res.cached, sources: res.sources,
            }])
        } catch (err) {
            const aid = uid(); setNewId(aid)
            setMessages(p => [...p, { id: aid, role: 'assistant', timestamp: new Date(), content: `❌ ${err instanceof Error ? err.message : 'Request failed.'}` }])
        } finally { setLoading(false) }
    }

    function toggleVoice() {
        if (listening) { recRef.current?.stop(); setListening(false); return }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const SR = (window as any).webkitSpeechRecognition ?? (window as any).SpeechRecognition
        if (!SR) { alert('Speech recognition not supported'); return }
        const rec = new SR(); rec.continuous = false; rec.interimResults = true; rec.lang = 'en-US'
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        rec.onresult = (e: any) => { setInput(Array.from(e.results).map((r: any) => r[0].transcript).join('')); setTimeout(resize, 0) }
        rec.onend = () => setListening(false); rec.onerror = () => setListening(false)
        recRef.current = rec; rec.start(); setListening(true)
    }

    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: APPLE_BG, fontFamily: F, color: APPLE_TEXT }}>

            {/* Top Bar Glass */}
            <div style={{ position: 'sticky', top: 0, zIndex: 50, ...GLASS, borderRadius: 0, borderTop: 'none', borderLeft: 'none', borderRight: 'none', borderBottom: '1px solid rgba(0,0,0,0.06)', padding: '12px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <FloatMarkIcon size={22} color={APPLE_BLUE} />
                    <span style={{ fontSize: 17, fontWeight: 600, letterSpacing: '-0.02em', color: APPLE_TEXT }}>Ocean AI</span>
                    <span style={{ width: 1, height: 16, background: 'rgba(0,0,0,0.1)' }} />
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: status === 'online' ? APPLE_GREEN : '#ff9f0a' }} />
                        <span style={{ fontSize: 12, fontWeight: 500, color: APPLE_SUBTEXT, textTransform: 'capitalize' }}>{status}</span>
                    </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    {messages.length > 0 && (
                        <>
                            <button onClick={() => exportMarkdown(messages)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: 99, background: 'rgba(0,0,0,0.04)', border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 500, color: APPLE_TEXT, transition: 'background 0.2s' }} onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,0,0,0.08)'} onMouseLeave={e => e.currentTarget.style.background = 'rgba(0,0,0,0.04)'}>
                                <Download style={{ width: 14, height: 14 }} /> Export
                            </button>
                            <button onClick={() => { setMessages([]); setNewId(null) }} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: 99, background: 'rgba(0,0,0,0.04)', border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 500, color: APPLE_RED, transition: 'background 0.2s' }} onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,59,48,0.1)'} onMouseLeave={e => e.currentTarget.style.background = 'rgba(0,0,0,0.04)'}>
                                <Trash2 style={{ width: 14, height: 14 }} /> Clear
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Messages Area */}
            <div style={{ flex: 1, padding: '0 24px' }}>
                <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24, padding: '40px 0' }}>

                    {/* Welcome */}
                    {messages.length === 0 && (
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
                            style={{ textAlign: 'center', paddingTop: '10vh', paddingBottom: 40 }}>
                            <div style={{ width: 80, height: 80, margin: '0 auto 24px', borderRadius: 22, background: '#fff', border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 12px 32px rgba(0,0,0,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <FloatMarkIcon size={44} color={APPLE_BLUE} />
                            </div>
                            <h1 style={{ fontSize: '2.5rem', fontWeight: 700, letterSpacing: '-0.04em', color: APPLE_TEXT, margin: '0 0 12px' }}>
                                How can I help you today?
                            </h1>
                            <p style={{ fontSize: 18, color: APPLE_SUBTEXT, margin: '0 0 40px', fontWeight: 400, letterSpacing: '-0.01em' }}>
                                Ask about ARGO floats, live ocean data, or analytical insights.
                            </p>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, maxWidth: 640, margin: '0 auto', textAlign: 'left' }}>
                                {STARTERS.map((s, i) => (
                                    <motion.button key={i} onClick={() => void send(s.q)} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }}
                                        style={{ ...CARD, padding: '16px 20px', cursor: 'pointer', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: 8, transition: 'box-shadow 0.2s' }}
                                        onMouseEnter={e => e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.08)'} onMouseLeave={e => e.currentTarget.style.boxShadow = CARD.boxShadow as string}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <span style={{ fontSize: 18 }}>{s.icon}</span>
                                            <span style={{ fontSize: 14, fontWeight: 600, color: APPLE_TEXT }}>{s.label}</span>
                                        </div>
                                        <span style={{ fontSize: 13, color: APPLE_SUBTEXT, lineHeight: 1.4 }}>{s.q}</span>
                                    </motion.button>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Chat Feed */}
                    <AnimatePresence initial={false}>
                        {messages.map(m => <Bubble key={m.id} msg={m} isNew={m.id === newId} onFollowUp={q => void send(q)} />)}
                    </AnimatePresence>

                    {/* Loading indicator */}
                    {loading && (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                            style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                            <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#fff', border: '1px solid rgba(0,0,0,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                                <RefreshCw style={{ width: 14, height: 14, color: APPLE_SUBTEXT, animation: 'spin 1.5s linear infinite' }} />
                            </div>
                            <div style={{ display: 'flex', gap: 6, background: '#fff', padding: '14px 20px', borderRadius: 20, border: '1px solid rgba(0,0,0,0.04)', boxShadow: '0 2px 10px rgba(0,0,0,0.02)' }}>
                                {[0, 1, 2].map(i => (
                                    <motion.div key={i} style={{ width: 8, height: 8, borderRadius: '50%', background: 'rgba(0,0,0,0.2)' }}
                                        animate={{ opacity: [0.3, 1, 0.3], y: [0, -4, 0] }}
                                        transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }} />
                                ))}
                            </div>
                        </motion.div>
                    )}

                    <div ref={bottomRef} style={{ height: 1 }} />
                </div>
            </div>

            {/* Input Floating Area */}
            <div style={{ position: 'sticky', bottom: 0, zIndex: 50, padding: '20px 24px 32px', background: 'linear-gradient(to top, #f5f5f7 70%, rgba(245,245,247,0))' }}>
                <div style={{ maxWidth: 760, margin: '0 auto' }}>

                    {/* Model selector pill */}
                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                        <div style={{ ...GLASS, borderRadius: 99, padding: '2px', display: 'flex', gap: 2 }}>
                            {PROVIDERS.map(p => (
                                <button key={p.id} onClick={() => setProvider(p.id)}
                                    style={{ padding: '6px 14px', borderRadius: 99, border: 'none', background: provider === p.id ? '#fff' : 'transparent', color: provider === p.id ? APPLE_TEXT : APPLE_SUBTEXT, fontSize: 13, fontWeight: provider === p.id ? 600 : 500, cursor: 'pointer', fontFamily: F, boxShadow: provider === p.id ? '0 2px 8px rgba(0,0,0,0.06)' : 'none', transition: 'all 0.2s' }}>
                                    {p.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Chat Input */}
                    <div style={{ ...CARD, borderRadius: 24, padding: '6px' }}>
                        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, padding: '6px 6px 6px 16px' }}>
                            <textarea ref={textRef} value={input} rows={1}
                                onChange={e => { setInput(e.target.value); resize() }}
                                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send() } }}
                                placeholder="Message Ocean AI..."
                                style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', fontSize: 16, fontWeight: 400, color: APPLE_TEXT, fontFamily: F, resize: 'none', overflow: 'hidden', lineHeight: 1.5, padding: '6px 0', minHeight: 24 }} />

                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0, paddingBottom: 2 }}>
                                {/* Voice */}
                                <button onClick={toggleVoice}
                                    style={{ width: 34, height: 34, borderRadius: 17, border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.2s', background: listening ? 'rgba(255,59,48,0.1)' : 'transparent' }}>
                                    {listening ? <MicOff style={{ width: 18, height: 18, color: APPLE_RED }} /> : <Mic style={{ width: 18, height: 18, color: APPLE_SUBTEXT }} />}
                                </button>
                                {/* Send */}
                                <button onClick={() => void send()} disabled={!input.trim() || loading}
                                    style={{
                                        width: 34, height: 34, borderRadius: 17, border: 'none', cursor: input.trim() && !loading ? 'pointer' : 'default', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.2s',
                                        background: input.trim() && !loading ? APPLE_BLUE : 'rgba(0,0,0,0.04)',
                                        transform: input.trim() && !loading ? 'scale(1)' : 'scale(0.95)'
                                    }}>
                                    <Send style={{ width: 16, height: 16, color: input.trim() && !loading ? '#fff' : 'rgba(0,0,0,0.2)', marginLeft: input.trim() && !loading ? 0 : 0 }} />
                                </button>
                            </div>
                        </div>
                    </div>
                    <div style={{ textAlign: 'center', marginTop: 10 }}>
                        <span style={{ fontSize: 11, color: APPLE_SUBTEXT, fontWeight: 400 }}>Ocean AI can make mistakes. Verify important oceanographic data.</span>
                    </div>
                </div>
            </div>

            <style>{`
                @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
                @keyframes spin { to { transform: rotate(360deg) } }
                textarea::placeholder { color: #86868b; }
                .apple-prose p { margin-top: 0; margin-bottom: 1em; }
                .apple-prose p:last-child { margin-bottom: 0; }
                .apple-prose code { background: rgba(0,0,0,0.05); padding: 2px 6px; border-radius: 6px; font-family: 'SF Mono', monospace; font-size: 0.9em; color: #1d1d1f; }
                .apple-prose pre { background: transparent; padding: 0; margin: 0; }
                .apple-prose a { color: #0071e3; text-decoration: none; }
                .apple-prose a:hover { text-decoration: underline; }
                ::-webkit-scrollbar { width: 6px; }
                ::-webkit-scrollbar-track { background: transparent; }
                ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.15); border-radius: 99px; }
                ::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.25); }
            `}</style>
        </div>
    )
}
