'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { ChevronLeft, ArrowRight, FileText, Code, Database, Zap, BookOpen, Key, Lock, Compass, BarChart2 } from 'lucide-react'
import { FloatChatLogo } from '@/components/Brand'

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif"

const GLASS: React.CSSProperties = {
    background: 'rgba(255,255,255,0.72)',
    backdropFilter: 'blur(72px) saturate(180%)',
    WebkitBackdropFilter: 'blur(72px) saturate(180%)',
    border: '1px solid rgba(255,255,255,0.95)',
    boxShadow: '0 2px 0 rgba(255,255,255,1) inset, 0 10px 40px rgba(0,0,0,0.07)',
}

type Section = 'Introduction' | 'Quickstart Guide' | 'Authentication' | 'Rate Limits' | 'ARGO Infrastructure' | 'Language Models' | 'Vector Search' | 'Study Workspaces';

export default function DocsPage() {
    const [activeSection, setActiveSection] = useState<Section>('Introduction');

    const renderContent = () => {
        switch (activeSection) {
            case 'Introduction':
                return (
                    <motion.div key="intro" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 14px', borderRadius: 99, background: 'rgba(0,113,227,0.1)', color: '#0071e3', fontSize: 12, fontWeight: 700, marginBottom: 20 }}>
                            <BookOpen style={{ width: 14, height: 14 }} /> Version 1.0 (Current)
                        </div>

                        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 24, lineHeight: 1.1 }}>
                            Introduction to FloatChat
                        </h2>

                        <p style={{ fontSize: 16, lineHeight: 1.6, color: '#1d1d1f', marginBottom: 24, fontWeight: 500 }}>
                            FloatChat provides a powerful natural language interface over the global ARGO ocean floats dataset. Instead of writing complex SQL or using clunky visualization tools, you can simply ask questions in plain English.
                        </p>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 40 }}>
                            <div style={{ padding: '24px', borderRadius: 20, background: 'rgba(255,255,255,0.5)', border: '1px solid rgba(0,0,0,0.05)', boxShadow: '0 4px 14px rgba(0,0,0,0.03)' }}>
                                <Database style={{ color: '#ff9f0a', marginBottom: 12 }} />
                                <h4 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8, color: '#000' }}>Direct Argo Access</h4>
                                <p style={{ fontSize: 14, color: '#6e6e73', lineHeight: 1.5 }}>Query millions of ocean profiles in real-time instantly using our distributed backend database.</p>
                            </div>
                            <div style={{ padding: '24px', borderRadius: 20, background: 'rgba(255,255,255,0.5)', border: '1px solid rgba(0,0,0,0.05)', boxShadow: '0 4px 14px rgba(0,0,0,0.03)' }}>
                                <Zap style={{ color: '#0071e3', marginBottom: 12 }} />
                                <h4 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8, color: '#000' }}>AI Powered Search</h4>
                                <p style={{ fontSize: 14, color: '#6e6e73', lineHeight: 1.5 }}>Our routing engine dynamically picks Gemini, OpenAI, or Ollama automatically for optimal cost and efficiency.</p>
                            </div>
                        </div>

                        <h3 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#000', marginBottom: 16 }}>
                            Why FloatChat?
                        </h3>
                        <p style={{ fontSize: 15, lineHeight: 1.6, color: '#4a4a4c', marginBottom: 16 }}>
                            ARGO floats collect massive amounts of data in the ocean, but accessing that data historically required parsing giant text files or interacting with slow government APIs. FloatChat indexes all this data, places an intelligent LLM layer on top of it, and delivers insights in under a second.
                        </p>
                    </motion.div>
                );
            case 'Quickstart Guide':
                return (
                    <motion.div key="quickstart" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }}>
                        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 24, lineHeight: 1.1 }}>
                            Quickstart Guide
                        </h2>

                        <p style={{ fontSize: 16, lineHeight: 1.6, color: '#1d1d1f', marginBottom: 24, fontWeight: 500 }}>
                            You can interact with FloatChat's engine directly via our REST API. Most endpoints accept plain JSON.
                        </p>

                        <h3 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#000', marginBottom: 16 }}>
                            Making your first request
                        </h3>
                        <p style={{ fontSize: 15, lineHeight: 1.6, color: '#4a4a4c', marginBottom: 16 }}>
                            To get started quickly with the API, simply send a POST request with your query directly to the LLM router over HTTP. Below is an example using `fetch` or cURL.
                        </p>

                        <div style={{ background: '#1d1d1f', borderRadius: 16, padding: '20px', overflowX: 'auto', marginBottom: 24, boxShadow: '0 8px 30px rgba(0,0,0,0.1)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                                <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff5f56' }} />
                                <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ffbd2e' }} />
                                <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#27c93f' }} />
                                <span style={{ fontSize: 12, color: '#888', marginLeft: 8, fontFamily: 'monospace' }}>terminal</span>
                            </div>
                            <pre style={{ margin: 0, color: '#f8f8f2', fontFamily: "Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace", fontSize: 14, lineHeight: 1.5, whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                                <span style={{ color: '#ff79c6' }}>const</span> res = <span style={{ color: '#ff79c6' }}>await</span> <span style={{ color: '#50fa7b' }}>fetch</span>(<span style={{ color: '#f1fa8c' }}>'https://api.floatchat.ai/v1/chat'</span>, {'{'}
                                <span style={{ color: '#8be9fd' }}>method</span>: <span style={{ color: '#f1fa8c' }}>'POST'</span>,
                                <span style={{ color: '#8be9fd' }}>headers</span>: {'{'} <span style={{ color: '#f1fa8c' }}>'Content-Type'</span>: <span style={{ color: '#f1fa8c' }}>'application/json'</span> {'}'},
                                <span style={{ color: '#8be9fd' }}>body</span>: <span style={{ color: '#50fa7b' }}>JSON</span>.<span style={{ color: '#50fa7b' }}>stringify</span>({'{'}
                                <span style={{ color: '#8be9fd' }}>message</span>: <span style={{ color: '#f1fa8c' }}>"What is the average temperature in the Pacific?"</span>
                                {'}'})
                                {'}'});

                                <span style={{ color: '#ff79c6' }}>const</span> data = <span style={{ color: '#ff79c6' }}>await</span> res.<span style={{ color: '#50fa7b' }}>json</span>();
                                <span style={{ color: '#8be9fd' }}>console</span>.<span style={{ color: '#50fa7b' }}>log</span>(data.<span style={{ color: '#8be9fd' }}>response</span>);
                            </pre>
                        </div>
                    </motion.div>
                );
            case 'Authentication':
                return (
                    <motion.div key="auth" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }}>
                        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 24, lineHeight: 1.1 }}>
                            Authentication
                        </h2>
                        <p style={{ fontSize: 16, lineHeight: 1.6, color: '#1d1d1f', marginBottom: 24, fontWeight: 500 }}>
                            FloatChat API utilizes Bearer token authentication. You must send your API key in the `Authorization` header of every request.
                        </p>

                        <div style={{ display: 'flex', gap: 16, marginBottom: 32, padding: '20px', borderRadius: 16, background: 'rgba(255,160,10,0.1)', border: '1px solid rgba(255,160,10,0.2)' }}>
                            <Lock style={{ width: 24, height: 24, color: '#f59e0b', flexShrink: 0 }} />
                            <div>
                                <h4 style={{ fontSize: 14, fontWeight: 700, color: '#92400e', marginBottom: 4 }}>Keep your keys secure</h4>
                                <p style={{ fontSize: 14, color: '#92400e', margin: 0, lineHeight: 1.5 }}>Never expose your API keys in publicly accessible client-side code such as raw frontend JavaScript or GitHub repositories. Always route requests through your own backend server.</p>
                            </div>
                        </div>

                        <h3 style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#000', marginBottom: 12 }}>Header Format</h3>
                        <div style={{ background: '#f5f5f7', padding: '16px 20px', borderRadius: 12, border: '1px solid rgba(0,0,0,0.05)', fontFamily: 'monospace', fontSize: 14, color: '#1d1d1f', marginBottom: 24 }}>
                            Authorization: Bearer fc_live_xxxxxxxxxxxxxxxxxxxx
                        </div>
                    </motion.div>
                );
            case 'Rate Limits':
                return (
                    <motion.div key="rates" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }}>
                        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 24, lineHeight: 1.1 }}>
                            Rate Limits
                        </h2>
                        <p style={{ fontSize: 16, lineHeight: 1.6, color: '#1d1d1f', marginBottom: 24, fontWeight: 500 }}>
                            To guarantee high availability and fair usage across the global API network, FloatChat enforces standard rate limits per workspace.
                        </p>

                        <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 32, fontSize: 14 }}>
                            <thead>
                                <tr style={{ borderBottom: '2px solid rgba(0,0,0,0.1)' }}>
                                    <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 700, color: '#6e6e73' }}>Tier</th>
                                    <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 700, color: '#6e6e73' }}>Requests per minute</th>
                                    <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 700, color: '#6e6e73' }}>Searches per day</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                                    <td style={{ padding: '12px 16px', fontWeight: 600, color: '#1d1d1f' }}>Free Plan</td>
                                    <td style={{ padding: '12px 16px', color: '#4a4a4c' }}>30 RPM</td>
                                    <td style={{ padding: '12px 16px', color: '#4a4a4c' }}>500 / day</td>
                                </tr>
                                <tr style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                                    <td style={{ padding: '12px 16px', fontWeight: 600, color: '#0071e3' }}>Pro Plan</td>
                                    <td style={{ padding: '12px 16px', color: '#4a4a4c' }}>500 RPM</td>
                                    <td style={{ padding: '12px 16px', color: '#4a4a4c' }}>10,000 / day</td>
                                </tr>
                                <tr>
                                    <td style={{ padding: '12px 16px', fontWeight: 600, color: '#1d1d1f' }}>Enterprise</td>
                                    <td style={{ padding: '12px 16px', color: '#4a4a4c' }}>Custom defined</td>
                                    <td style={{ padding: '12px 16px', color: '#4a4a4c' }}>Unlimited</td>
                                </tr>
                            </tbody>
                        </table>
                    </motion.div>
                );
            case 'ARGO Infrastructure':
            case 'Language Models':
            case 'Vector Search':
            case 'Study Workspaces':
                return (
                    <motion.div key={activeSection} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 14px', borderRadius: 99, background: 'rgba(0,113,227,0.1)', color: '#0071e3', fontSize: 12, fontWeight: 700, marginBottom: 20 }}>
                            <Code style={{ width: 14, height: 14 }} /> Core Concept
                        </div>
                        <h2 style={{ fontSize: '2.4rem', fontWeight: 900, letterSpacing: '-0.04em', color: '#000', marginBottom: 24, lineHeight: 1.1 }}>
                            {activeSection}
                        </h2>
                        <p style={{ fontSize: 16, lineHeight: 1.6, color: '#1d1d1f', marginBottom: 24, fontWeight: 500 }}>
                            {activeSection} is a fundamental pillar of the FloatChat architecture. We orchestrate thousands of distributed nodes internally.
                        </p>

                        <div style={{ padding: '30px', borderRadius: 24, border: '2px dashed rgba(0,0,0,0.1)', textAlign: 'center', background: 'rgba(255,255,255,0.2)' }}>
                            <Compass style={{ width: 40, height: 40, color: '#a0a0a5', margin: '0 auto 16px' }} />
                            <h3 style={{ fontSize: 16, fontWeight: 700, color: '#1d1d1f', marginBottom: 8 }}>Coming soon</h3>
                            <p style={{ fontSize: 14, color: '#6e6e73' }}>Detailed technical documentation on the {activeSection} architecture is currently being written by our engineering team.</p>
                        </div>
                    </motion.div>
                );
        }
    };

    return (
        <div style={{ backgroundColor: '#f5f5f7', minHeight: '100vh', position: 'relative', fontFamily: FONT, overflowX: 'hidden' }}>

            {/* ── Apple-like Animated 4K Liquid Ocean Background ── */}
            <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
                {/* Flowing Ocean Image (Animated) */}
                <div style={{
                    position: 'absolute', inset: 0,
                    backgroundImage: 'url(https://images.unsplash.com/photo-1518837695005-2083093ee35b?q=80&w=3840&auto=format&fit=crop)',
                    backgroundSize: '120% 120%',
                    opacity: 1,
                    animation: 'oceanFlow 35s ease-in-out infinite'
                }} />

                {/* Delicate Frosted Glass Overlay */}
                <div style={{
                    position: 'absolute', inset: 0,
                    background: 'linear-gradient(to bottom, rgba(255,255,255,0.0) 0%, rgba(255,255,255,0.2) 100%)',
                    backdropFilter: 'blur(0px)'
                }} />

                {/* Subtle light flares for depth */}
                <div style={{ position: 'absolute', width: 800, height: 800, top: -200, left: -200, borderRadius: '50%', background: 'radial-gradient(circle, rgba(230, 230, 235, 0.4) 0%, transparent 70%)', filter: 'blur(80px)' }} />
                <div style={{ position: 'absolute', width: 600, height: 600, top: '20%', right: -100, borderRadius: '50%', background: 'radial-gradient(circle, rgba(240, 240, 245, 0.5) 0%, transparent 70%)', filter: 'blur(80px)' }} />
            </div>



            {/* ── Main Layout ── */}
            <div style={{ position: 'relative', zIndex: 10, maxWidth: 1200, margin: '0 auto', padding: '40px 20px 60px' }}>

                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: 60 }}>
                    <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ type: 'spring', stiffness: 100, damping: 20 }}
                        style={{ fontSize: 'clamp(3rem, 6vw, 4.5rem)', fontWeight: 900, letterSpacing: '-0.05em', color: '#000', marginBottom: 16 }}>
                        Documentation
                    </motion.h1>
                    <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1, duration: 0.6 }}
                        style={{ fontSize: '1.2rem', color: '#111', fontWeight: 600, maxWidth: 600, margin: '0 auto' }}>
                        Everything you need to integrate, query, and build with the FloatChat APIs.
                    </motion.p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 32, alignItems: 'start' }}>

                    {/* Sidebar */}
                    <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}
                        style={{ ...GLASS, borderRadius: 24, padding: '24px 20px', position: 'sticky', top: 100, display: 'flex', flexDirection: 'column' }}>

                        <h3 style={{ fontSize: 13, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#6e6e73', marginBottom: 16, paddingLeft: 12 }}>Getting Started</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            {(['Introduction', 'Quickstart Guide', 'Authentication', 'Rate Limits'] as Section[]).map((link) => {
                                const isActive = activeSection === link;
                                return (
                                    <button
                                        key={link}
                                        onClick={() => setActiveSection(link)}
                                        style={{
                                            padding: '10px 12px', borderRadius: 12, fontSize: 14, border: 'none',
                                            fontWeight: isActive ? 700 : 500,
                                            color: isActive ? '#0071e3' : '#4a4a4c',
                                            background: isActive ? 'rgba(0,113,227,0.08)' : 'transparent',
                                            cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s', width: '100%', fontFamily: FONT
                                        }}
                                        onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = 'rgba(0,0,0,0.04)'; e.currentTarget.style.color = isActive ? '#0071e3' : '#000' }}
                                        onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = isActive ? '#0071e3' : '#4a4a4c' }}
                                    >
                                        {link}
                                    </button>
                                );
                            })}
                        </div>

                        <h3 style={{ fontSize: 13, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#6e6e73', marginBottom: 16, paddingLeft: 12, marginTop: 32 }}>Core Concepts</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            {(['ARGO Infrastructure', 'Language Models', 'Vector Search', 'Study Workspaces'] as Section[]).map((link) => {
                                const isActive = activeSection === link;
                                return (
                                    <button
                                        key={link}
                                        onClick={() => setActiveSection(link)}
                                        style={{
                                            padding: '10px 12px', borderRadius: 12, fontSize: 14, border: 'none',
                                            fontWeight: isActive ? 700 : 500,
                                            color: isActive ? '#0071e3' : '#4a4a4c',
                                            background: isActive ? 'rgba(0,113,227,0.08)' : 'transparent',
                                            cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s', width: '100%', fontFamily: FONT
                                        }}
                                        onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.background = 'rgba(0,0,0,0.04)'; e.currentTarget.style.color = isActive ? '#0071e3' : '#000' }}
                                        onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = isActive ? '#0071e3' : '#4a4a4c' }}
                                    >
                                        {link}
                                    </button>
                                );
                            })}
                        </div>
                    </motion.div>

                    {/* Content */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }}
                        style={{ ...GLASS, borderRadius: 32, padding: '48px 40px', overflow: 'hidden', minHeight: '600px' }}>

                        <AnimatePresence mode="wait">
                            {renderContent()}
                        </AnimatePresence>

                    </motion.div>

                </div>

            </div>

        </div>
    )
}
