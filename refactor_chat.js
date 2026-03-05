const fs = require('fs')

let content = fs.readFileSync('app/chat/page.tsx', 'utf8')

const NEW_RETURN = `return (
        <div style={{ backgroundColor: '#f5f5f7', height: '100vh', display: 'flex', flexDirection: 'row', position: 'relative', fontFamily: FONT, overflow: 'hidden' }}>

            {/* ── Apple-like Animated 4K Liquid Ocean Background ── */}
            <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
                {/* Flowing Ocean Image (Animated) */}
                <div style={{
                    position: 'absolute', inset: 0,
                    backgroundImage: 'url(https://images.unsplash.com/photo-1518182170546-076616fdcb18?q=80&w=3840&auto=format&fit=crop)',
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

            {/* ── Left Sidebar Navigation ── */}
            <div style={{ 
                width: 250, padding: '24px 20px', display: 'flex', flexDirection: 'column', gap: 32, 
                zIndex: 40, borderRight: '1px solid rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.35)', 
                backdropFilter: 'blur(32px)', WebkitBackdropFilter: 'blur(32px)', flexShrink: 0 
            }}>
                <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', padding: '0 8px' }}>
                    <FloatChatLogo size={18} />
                    <span style={{ fontSize: 13, fontWeight: 800, color: '#000', letterSpacing: '-0.02em' }}>FloatChat</span>
                </Link>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {[{ label: 'Home', href: '/' }, { label: 'Chat', href: '/chat' }, { label: 'Explorer', href: '/explorer' }, { label: 'Charts', href: '/visualizations' }, { label: 'Tools', href: '/tools' }, { label: 'Study', href: '/study' }, { label: 'Docs', href: '/docs' }].map(link => {
                        const active = link.label === 'Chat'
                        return (
                            <Link key={link.label} href={link.href} style={{ 
                                textDecoration: 'none', padding: '10px 14px', borderRadius: 12, fontSize: 13, fontWeight: active ? 700 : 600, 
                                color: active ? '#000' : '#4a4a4c', background: active ? 'rgba(255,255,255,0.8)' : 'transparent', 
                                boxShadow: active ? '0 2px 10px rgba(0,0,0,0.05)' : 'none', transition: 'all 0.2s' 
                            }}
                                onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'rgba(255,255,255,0.4)' }}
                                onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent' }}
                            >
                                {link.label}
                            </Link>
                        )
                    })}
                </div>

                <div style={{ flex: 1 }} />

                <Link href="/dashboard" style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    padding: '12px', borderRadius: 14, background: '#1d1d1f', color: '#fff',
                    fontSize: 13, fontWeight: 700, textDecoration: 'none',
                    boxShadow: '0 4px 14px rgba(0,0,0,0.15)', letterSpacing: '-0.01em',
                    transition: 'transform 0.2s ease, background 0.2s ease',
                }}
                    onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.02)' }}
                    onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)' }}>
                    Dashboard
                </Link>

                <div style={{ ...GLASS_SUBTLE, padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <OceanAIBadge size={24} />
                        <div>
                            <p style={{ fontSize: 12, fontWeight: 800, color: '#000', margin: '0 0 2px', lineHeight: 1 }}>Ocean AI</p>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <StatusDot status={backendStatus} />
                                <span style={{ fontSize: 10, color: '#6e6e73', fontWeight: 600, textTransform: 'capitalize' }}>{backendStatus}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Chat Main Area ── */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 10 }}>
                {/* Messages */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '40px 0 20px' }}>
                    <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 24px', display: 'flex', flexDirection: 'column', gap: 18 }}>

                        {/* Welcome state */}
                        {messages.length === 0 && (
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
                                style={{ textAlign: 'center', padding: '100px 20px 60px' }}>
                                <div style={{ width: 72, height: 72, borderRadius: 26, background: '#0071e3', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', boxShadow: '0 8px 32px rgba(0,113,227,0.28)' }}>
                                    <FloatMarkIcon size={32} color="#fff" />
                                </div>
                                <h2 style={{ fontSize: '1.8rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 6 }}>Ask the Ocean AI</h2>
                                <p style={{ fontSize: 14, color: '#6e6e73', marginBottom: 8 }}>Backend-linked · returns confidence, sources, reliability</p>
                            </motion.div>
                        )}

                        {/* Message list */}
                        <AnimatePresence initial={false}>
                            {messages.map((msg, i) => (
                                <motion.div key={i}
                                    initial={{ opacity: 0, y: 12, scale: 0.98 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.35, ease: 'easeOut' }}
                                    style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', gap: 12 }}>

                                    {msg.role === 'assistant' && (
                                        <OceanAIBadge size={32} />
                                    )}

                                    <div style={{
                                        maxWidth: '82%',
                                        ...(msg.role === 'user'
                                            ? { background: '#1d1d1f', color: '#fff', padding: '14px 18px', borderRadius: '22px 22px 6px 22px', boxShadow: '0 4px 16px rgba(0,0,0,0.2)' }
                                            : { ...GLASS, padding: '16px 20px', borderRadius: '6px 22px 22px 22px' }
                                        )
                                    }}>
                                        {/* Content */}
                                        {msg.role === 'assistant' ? (
                                            <div style={{ fontSize: 14, lineHeight: 1.65, color: '#1d1d1f' }}>
                                                <div className="prose prose-sm max-w-none">
                                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{String(msg.content)}</ReactMarkdown>
                                                </div>
                                            </div>
                                        ) : (
                                            <p style={{ fontSize: 14, lineHeight: 1.65, color: '#fff', margin: 0, fontWeight: 500 }}>{msg.content}</p>
                                        )}

                                        {/* ── Backend metadata (assistant only) ── */}
                                        {msg.role === 'assistant' && (
                                            <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid rgba(0,0,0,0.07)' }}>
                                                {/* Chips row */}
                                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
                                                    {msg.source && <Chip label={\`source: \${msg.source}\`} color="#0071e3" />}
                                                    {msg.query_type && <Chip label={\`type: \${msg.query_type}\`} />}
                                                    {msg.intent && <Chip label={\`intent: \${msg.intent}\`} />}
                                                    {msg.row_count != null && <Chip label={\`rows: \${msg.row_count}\`} />}
                                                    {msg.cached != null && <Chip label={msg.cached ? '⚡ cached' : 'live'} color={msg.cached ? '#5e5ce6' : '#34c759'} />}
                                                    {msg.confidence != null && <Chip label={\`confidence: \${pct(msg.confidence)}\`} color="#ff9f0a" />}
                                                    {msg.evidence_score != null && <Chip label={\`evidence: \${score(msg.evidence_score)}\`} />}
                                                    {msg.evidence_coverage_score != null && <Chip label={\`coverage: \${score(msg.evidence_coverage_score)}\`} />}
                                                </div>

                                                {/* Provider metrics */}
                                                {msg.provider_metrics && msg.provider_metrics.length > 0 && (
                                                    <div style={{ ...GLASS_SUBTLE, padding: '10px 14px', marginBottom: 10 }}>
                                                        <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#6e6e73', marginBottom: 8 }}>Provider Metrics</p>
                                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                                            {msg.provider_metrics.map((m: ChatProviderMetric, idx: number) => (
                                                                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 99, background: m.success ? 'rgba(52,199,89,0.12)' : 'rgba(255,59,48,0.1)', border: \`1px solid \${m.success ? 'rgba(52,199,89,0.3)' : 'rgba(255,59,48,0.3)'}\` }}>
                                                                    <Zap style={{ width: 10, height: 10, color: m.success ? '#34c759' : '#ff3b30' }} />
                                                                    <span style={{ fontSize: 11, fontWeight: 700, color: '#1d1d1f' }}>{m.provider}</span>
                                                                    <span style={{ fontSize: 11, color: '#6e6e73' }}>{ms(m.latency_ms)}</span>
                                                                    <span style={{ fontSize: 11, fontWeight: 600, color: m.success ? '#34c759' : '#ff3b30' }}>{m.success ? '✓' : '✗'}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Sources */}
                                                {msg.sources && msg.sources.length > 0 && (
                                                    <div style={{ ...GLASS_SUBTLE, padding: '10px 14px', marginBottom: 10 }}>
                                                        <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#6e6e73', marginBottom: 6 }}>Sources</p>
                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                                            {msg.sources.slice(0, 4).map((src, idx) => (
                                                                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                                                    <a href={src.source} target="_blank" rel="noreferrer" style={{ fontSize: 12, fontWeight: 700, color: '#0071e3', textDecoration: 'none' }}>{src.title}</a>
                                                                    <p style={{ fontSize: 12, color: '#6e6e73', margin: 0 }}>{src.snippet}</p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Reliability collapsible */}
                                                {(msg.method || (msg.reliability_warnings?.length ?? 0) > 0 || (msg.next_checks?.length ?? 0) > 0) && (
                                                    <details style={{ ...GLASS_SUBTLE as object, padding: '10px 14px', marginBottom: 10 }}>
                                                        <summary style={{ cursor: 'pointer', fontSize: 11, fontWeight: 700, color: '#6e6e73', letterSpacing: '0.05em', listStyle: 'none' }}>⚠ Reliability Details</summary>
                                                        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                                                            {msg.method && <p style={{ fontSize: 12, color: '#3a3a3c', margin: 0 }}><strong>Method:</strong> {msg.method}</p>}
                                                            {(msg.data_source?.length ?? 0) > 0 && <p style={{ fontSize: 12, color: '#3a3a3c', margin: 0 }}><strong>Data source:</strong> {msg.data_source!.join(', ')}</p>}
                                                            {(msg.limitations?.length ?? 0) > 0 && <p style={{ fontSize: 12, color: '#ff9f0a', margin: 0 }}><strong>Limitations:</strong> {msg.limitations!.join(' · ')}</p>}
                                                            {(msg.reliability_warnings?.length ?? 0) > 0 && <p style={{ fontSize: 12, color: '#ff3b30', margin: 0 }}><strong>Warnings:</strong> {msg.reliability_warnings!.join(' · ')}</p>}
                                                            {(msg.next_checks?.length ?? 0) > 0 && <p style={{ fontSize: 12, color: '#5e5ce6', margin: 0 }}><strong>Next checks:</strong> {msg.next_checks!.join(' · ')}</p>}
                                                        </div>
                                                    </details>
                                                )}

                                                {/* Feedback thumbs */}
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                                                    <span style={{ fontSize: 11, color: '#6e6e73', fontWeight: 600 }}>Helpful?</span>
                                                    {([1, -1] as const).map(r => (
                                                        <button key={r} onClick={() => void sendFeedback(msg, r)}
                                                            style={{ width: 26, height: 26, borderRadius: 8, border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.05)', transition: 'background 0.15s' }}
                                                            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(0,0,0,0.1)')}
                                                            onMouseLeave={e => (e.currentTarget.style.background = 'rgba(0,0,0,0.05)')}>
                                                            {r === 1 ? <ThumbsUp style={{ width: 12, height: 12, color: '#34c759' }} /> : <ThumbsDown style={{ width: 12, height: 12, color: '#ff3b30' }} />}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>

                        {/* Loading */}
                        {loading && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', gap: 10 }}>
                                <OceanAIBadge size={32} />
                                <div style={{ ...GLASS, padding: '14px 18px', borderRadius: '6px 20px 20px 20px', display: 'flex', gap: 6, alignItems: 'center' }}>
                                    {[0, 1, 2].map(i => (
                                        <motion.span key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: '#0071e3', display: 'block' }}
                                            animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.1, 0.8] }}
                                            transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.3 }} />
                                    ))}
                                    <span style={{ fontSize: 12, color: '#6e6e73', marginLeft: 4, fontWeight: 600 }}>Thinking with {provider}…</span>
                                </div>
                            </motion.div>
                        )}
                        <div ref={bottomRef} />
                    </div>
                </div>

                {/* ── Input bar & Compact Switcher ── */}
                <div style={{ padding: '0 24px 24px', flexShrink: 0, width: '100%', maxWidth: 860, margin: '0 auto' }}>

                    {/* Suggestions Inline */}
                    <AnimatePresence>
                        {messages.length === 0 && (
                            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10, height: 0, paddingBottom: 0 }}
                                style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 14, scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}>
                                {SUGGESTIONS.map(s => (
                                    <button key={s} onClick={() => void send(s)}
                                        style={{ ...GLASS, padding: '10px 16px', borderRadius: 99, flexShrink: 0, fontSize: 13, fontWeight: 600, color: '#3a3a3c', cursor: 'pointer', border: '1px solid rgba(255,255,255,0.7)', transition: 'background 0.2s, transform 0.1s' }}
                                        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.85)'; e.currentTarget.style.transform = 'scale(1.02)' }}
                                        onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.58)'; e.currentTarget.style.transform = 'scale(1)' }}>
                                        {s}
                                    </button>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Integrated Input & Settings container */}
                    <div style={{ ...GLASS, display: 'flex', flexDirection: 'column', borderRadius: 28, padding: '6px', boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}>
                        {/* Input row */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '6px 8px 6px 18px' }}>
                            <input
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send() } }}
                                placeholder="Ask about ARGO floats, ocean data, temperature…"
                                style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', fontSize: 15, fontWeight: 500, color: '#1d1d1f', fontFamily: FONT }}
                            />
                            <button onClick={() => void send()} disabled={!input.trim() || loading}
                                style={{ width: 44, height: 44, borderRadius: 99, background: (input.trim() && !loading) ? '#0071e3' : 'rgba(0,0,0,0.08)', border: 'none', cursor: (input.trim() && !loading) ? 'pointer' : 'default', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s', flexShrink: 0, boxShadow: (input.trim() && !loading) ? '0 4px 12px rgba(0,113,227,0.3)' : 'none' }}>
                                <Send style={{ width: 16, height: 16, color: (input.trim() && !loading) ? '#fff' : '#aaa' }} />
                            </button>
                        </div>

                        {/* Compact Provider Switcher (Footer) */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 14px 6px', borderTop: '1px solid rgba(0,0,0,0.06)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <span style={{ fontSize: 11, fontWeight: 800, color: '#8e8e93', textTransform: 'uppercase', letterSpacing: '0.05em', marginRight: 4 }}>Model</span>
                                {PROVIDERS.map(p => (
                                    <button key={p.id} onClick={() => setProvider(p.id)}
                                        style={{ padding: '4px 12px', borderRadius: 99, fontSize: 11, fontWeight: 700, background: provider === p.id ? '#1d1d1f' : 'transparent', color: provider === p.id ? '#fff' : '#6e6e73', cursor: 'pointer', border: 'none', transition: 'all 0.2s', fontFamily: FONT }}
                                        onMouseEnter={e => { if (provider !== p.id) e.currentTarget.style.color = '#1d1d1f' }}
                                        onMouseLeave={e => { if (provider !== p.id) e.currentTarget.style.color = '#6e6e73' }}>
                                        {p.label}
                                    </button>
                                ))}
                            </div>
                            <span style={{ fontSize: 11, color: '#a0a0a5', fontWeight: 600 }}>API: {process.env.NEXT_PUBLIC_API_URL || 'localhost'}</span>
                        </div>
                    </div>

                </div>
            </div>

            <style>{\`
                @keyframes orb1 { 0%,100% { transform: translate(0,0) scale(1); } 33% { transform: translate(80px,-100px) scale(1.1); } 66% { transform: translate(-60px,60px) scale(0.92); } }
                @keyframes orb2 { 0%,100% { transform: translate(0,0) scale(1); } 30% { transform: translate(-100px,80px) scale(1.12); } 70% { transform: translate(70px,-50px) scale(0.9); } }
                @keyframes orb3 { 0%,100% { transform: translate(0,0) scale(1); } 40% { transform: translate(50px,90px) scale(1.08); } 80% { transform: translate(-80px,-60px) scale(0.95); } }
                input::placeholder { color: #a0a0a5; }
                details summary::-webkit-details-marker { display: none; }
                
                /* Hide scrollbar for inline suggestions */
                ::-webkit-scrollbar {
                    display: none;
                }
            \`}</style>
        </div>
    )
}
`

const START = content.search(/return \(\s*<div style=\{\{ backgroundColor: '#f5f5f7'/);
if (START === -1) {
    console.error("Could not find return statement")
    process.exit(1)
}

content = content.substring(0, START) + NEW_RETURN

fs.writeFileSync('app/chat/page.tsx', content)
console.log('Successfully updated chat layout')
