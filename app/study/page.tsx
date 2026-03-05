'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, Download, History, RefreshCw, Save, Shield, Sparkles, ChevronLeft, Users, X, Eye, RotateCcw } from 'lucide-react'
import { FloatChatLogo } from '@/components/Brand'
import {
    apiClient,
    type StudyBackgroundJob,
    type WorkspaceMember,
    type Workspace,
    type WorkspaceSnapshotResponse,
    type WorkspaceVersionDetail,
    type WorkspaceVersionSummary,
} from '@/lib/api-client'

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif"

const GLASS: React.CSSProperties = {
    background: 'rgba(255,255,255,0.55)',
    backdropFilter: 'blur(48px) saturate(200%)',
    WebkitBackdropFilter: 'blur(48px) saturate(200%)',
    border: '1.5px solid rgba(255,255,255,0.85)',
    borderRadius: 24,
    boxShadow: '0 2px 0 rgba(255,255,255,0.9) inset, 0 10px 36px rgba(0,0,0,0.09)',
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fadeUp: any = {
    hidden: { opacity: 0, y: 16 },
    visible: (i: number = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.4, delay: i * 0.06 } })
}

function parseError(error: unknown): string {
    if (error instanceof Error) return error.message
    return 'Unknown error'
}

function downloadJson(filename: string, payload: unknown) {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    anchor.click()
    URL.revokeObjectURL(url)
}

function downloadTextFile(filename: string, content: string, mimeType: string) {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    anchor.click()
    URL.revokeObjectURL(url)
}

// ── Small reusable components ─────────────────────────────────────────────────

function GlassInput({ value, onChange, placeholder, type = 'text' }: { value: string; onChange: (v: string) => void; placeholder: string; type?: string }) {
    return (
        <input
            type={type}
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
            style={{
                width: '100%', padding: '11px 16px', border: '1.5px solid rgba(0,0,0,0.08)',
                borderRadius: 14, fontSize: 13, fontWeight: 500, color: '#000', fontFamily: FONT,
                outline: 'none', background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)', boxSizing: 'border-box',
            }}
        />
    )
}

function PrimaryBtn({ onClick, disabled, children }: { onClick: () => void; disabled?: boolean; children: React.ReactNode }) {
    return (
        <button onClick={onClick} disabled={disabled} style={{
            display: 'inline-flex', alignItems: 'center', gap: 7, padding: '10px 22px',
            borderRadius: 99, background: '#000', color: '#fff', border: 'none',
            cursor: disabled ? 'not-allowed' : 'pointer', fontSize: 13, fontWeight: 700,
            fontFamily: FONT, opacity: disabled ? 0.4 : 1,
            boxShadow: '0 4px 16px rgba(0,0,0,0.2)', transition: 'all 0.15s',
        }}>
            {children}
        </button>
    )
}

function GhostBtn({ onClick, disabled, children }: { onClick: () => void; disabled?: boolean; children: React.ReactNode }) {
    return (
        <button onClick={onClick} disabled={disabled} style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, padding: '9px 18px',
            borderRadius: 99, background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)', border: '1.5px solid rgba(0,0,0,0.1)',
            cursor: disabled ? 'not-allowed' : 'pointer', fontSize: 12, fontWeight: 700,
            fontFamily: FONT, color: '#1d1d1f', opacity: disabled ? 0.4 : 1, transition: 'all 0.15s',
        }}>
            {children}
        </button>
    )
}

function MetricCard({ label, value }: { label: string; value: string }) {
    return (
        <div style={{ ...GLASS, padding: '16px 18px', borderRadius: 18 }}>
            <p style={{ fontSize: 10, fontWeight: 700, color: '#6e6e73', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>{label}</p>
            <p style={{ fontSize: '1.4rem', fontWeight: 900, color: '#000', letterSpacing: '-0.04em' }}>{value}</p>
        </div>
    )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function StudyPage() {
    const [tokenInput, setTokenInput] = useState('')
    const [tokenReady, setTokenReady] = useState(false)
    const [workspaces, setWorkspaces] = useState<Workspace[]>([])
    const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string>('')
    const [snapshot, setSnapshot] = useState<WorkspaceSnapshotResponse | null>(null)
    const [versions, setVersions] = useState<WorkspaceVersionSummary[]>([])
    const [selectedVersion, setSelectedVersion] = useState<WorkspaceVersionDetail | null>(null)
    const [jobs, setJobs] = useState<StudyBackgroundJob[]>([])
    const [members, setMembers] = useState<WorkspaceMember[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const [newWorkspaceName, setNewWorkspaceName] = useState('')
    const [newWorkspaceDescription, setNewWorkspaceDescription] = useState('')
    const [versionLabel, setVersionLabel] = useState('')
    const [memberIdentifier, setMemberIdentifier] = useState('')
    const [memberRole, setMemberRole] = useState<'viewer' | 'editor'>('viewer')

    useEffect(() => {
        const existing = window.localStorage.getItem('floatchat_auth_token') || ''
        if (existing) {
            setTokenInput(existing)
            apiClient.setAuthToken(existing)
            setTokenReady(true)
        }
    }, [])

    const selectedWorkspace = useMemo(
        () => workspaces.find((workspace) => workspace.id === selectedWorkspaceId) || null,
        [selectedWorkspaceId, workspaces],
    )

    const loadWorkspaces = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const data = await apiClient.listWorkspaces()
            setWorkspaces(data)
            if (!selectedWorkspaceId && data.length > 0) {
                setSelectedWorkspaceId(data[0].id)
            } else if (selectedWorkspaceId && !data.some((ws) => ws.id === selectedWorkspaceId)) {
                setSelectedWorkspaceId(data.length > 0 ? data[0].id : '')
            }
        } catch (loadError) {
            setError(parseError(loadError))
        } finally {
            setIsLoading(false)
        }
    }, [selectedWorkspaceId])

    async function loadWorkspaceDetails(workspaceId: string) {
        setIsLoading(true)
        setError(null)
        try {
            const [snapshotData, versionsData, jobsData, membersData] = await Promise.all([
                apiClient.getWorkspaceSnapshot(workspaceId, { history_limit: 50 }),
                apiClient.listWorkspaceVersions(workspaceId, 50),
                apiClient.listWorkspaceJobs(workspaceId, 20),
                apiClient.listWorkspaceMembers(workspaceId),
            ])
            setSnapshot(snapshotData)
            setVersions(versionsData)
            setJobs(jobsData)
            setMembers(membersData)
            setSelectedVersion(null)
        } catch (loadError) {
            setError(parseError(loadError))
        } finally {
            setIsLoading(false)
        }
    }

    async function applyToken() {
        apiClient.setAuthToken(tokenInput.trim() || null)
        if (tokenInput.trim()) {
            window.localStorage.setItem('floatchat_auth_token', tokenInput.trim())
            setTokenReady(true)
            await loadWorkspaces()
        } else {
            window.localStorage.removeItem('floatchat_auth_token')
            setTokenReady(false)
            setWorkspaces([])
            setSelectedWorkspaceId('')
            setSnapshot(null)
            setVersions([])
            setSelectedVersion(null)
            setMembers([])
        }
    }

    async function createWorkspace() {
        if (!newWorkspaceName.trim()) return
        setIsLoading(true)
        setError(null)
        try {
            await apiClient.createWorkspace({
                name: newWorkspaceName.trim(),
                description: newWorkspaceDescription.trim() || undefined,
            })
            setNewWorkspaceName('')
            setNewWorkspaceDescription('')
            await loadWorkspaces()
        } catch (createError) {
            setError(parseError(createError))
        } finally {
            setIsLoading(false)
        }
    }

    async function createVersion() {
        if (!selectedWorkspaceId) return
        setIsLoading(true)
        setError(null)
        try {
            await apiClient.createWorkspaceVersion(selectedWorkspaceId, {
                label: versionLabel.trim() || undefined,
                include_notes: true,
                include_queries: true,
                include_compare_history: true,
                include_timeline_history: true,
                history_limit: 100,
            })
            setVersionLabel('')
            await loadWorkspaceDetails(selectedWorkspaceId)
        } catch (createError) {
            setError(parseError(createError))
        } finally {
            setIsLoading(false)
        }
    }

    async function viewVersion(versionId: string) {
        if (!selectedWorkspaceId) return
        setIsLoading(true)
        setError(null)
        try {
            const detail = await apiClient.getWorkspaceVersion(selectedWorkspaceId, versionId)
            setSelectedVersion(detail)
        } catch (viewError) {
            setError(parseError(viewError))
        } finally {
            setIsLoading(false)
        }
    }

    async function dryRunRestore(versionId: string) {
        if (!selectedWorkspaceId) return
        setIsLoading(true)
        setError(null)
        try {
            const result = await apiClient.restoreWorkspaceVersion(selectedWorkspaceId, versionId, { dry_run: true })
            window.alert(`Dry-run restore planned:\n${JSON.stringify(result.planned_restore || {}, null, 2)}`)
        } catch (restoreError) {
            setError(parseError(restoreError))
        } finally {
            setIsLoading(false)
        }
    }

    async function downloadReproPackage(versionId?: string) {
        if (!selectedWorkspaceId) return
        setIsLoading(true)
        setError(null)
        try {
            const data = await apiClient.getWorkspaceReproPackage(selectedWorkspaceId, { version_id: versionId })
            const suffix = versionId ? `version-${versionId}` : 'live'
            downloadJson(`floatchat-repro-${selectedWorkspaceId}-${suffix}.json`, data)
        } catch (downloadError) {
            setError(parseError(downloadError))
        } finally {
            setIsLoading(false)
        }
    }

    async function downloadNotebookTemplate(language: 'python' | 'r', versionId?: string) {
        if (!selectedWorkspaceId) return
        setIsLoading(true)
        setError(null)
        try {
            const data = await apiClient.getWorkspaceNotebookTemplate(selectedWorkspaceId, {
                language,
                version_id: versionId,
            })
            const mimeType = data.format === 'ipynb' ? 'application/json' : 'text/x-rsrc'
            downloadTextFile(data.filename, data.content, mimeType)
        } catch (downloadError) {
            setError(parseError(downloadError))
        } finally {
            setIsLoading(false)
        }
    }

    async function queueAsyncReproPackage(versionId?: string) {
        if (!selectedWorkspaceId) return
        setIsLoading(true)
        setError(null)
        try {
            const job = await apiClient.queueWorkspaceReproPackageJob(selectedWorkspaceId, {
                version_id: versionId,
            })
            setJobs((prev) => [job, ...prev].slice(0, 20))
        } catch (queueError) {
            setError(parseError(queueError))
        } finally {
            setIsLoading(false)
        }
    }

    async function refreshJobs() {
        if (!selectedWorkspaceId) return
        setIsLoading(true)
        setError(null)
        try {
            const data = await apiClient.listWorkspaceJobs(selectedWorkspaceId, 20)
            setJobs(data)
        } catch (jobError) {
            setError(parseError(jobError))
        } finally {
            setIsLoading(false)
        }
    }

    async function addMember() {
        if (!selectedWorkspaceId || !memberIdentifier.trim()) return
        setIsLoading(true)
        setError(null)
        try {
            await apiClient.addWorkspaceMember(selectedWorkspaceId, {
                user_identifier: memberIdentifier.trim(),
                role: memberRole,
            })
            setMemberIdentifier('')
            const updated = await apiClient.listWorkspaceMembers(selectedWorkspaceId)
            setMembers(updated)
        } catch (memberError) {
            setError(parseError(memberError))
        } finally {
            setIsLoading(false)
        }
    }

    async function removeMember(memberUserId: string) {
        if (!selectedWorkspaceId) return
        setIsLoading(true)
        setError(null)
        try {
            await apiClient.removeWorkspaceMember(selectedWorkspaceId, memberUserId)
            const updated = await apiClient.listWorkspaceMembers(selectedWorkspaceId)
            setMembers(updated)
        } catch (memberError) {
            setError(parseError(memberError))
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        if (!tokenReady) return
        void loadWorkspaces()
    }, [tokenReady, loadWorkspaces])

    useEffect(() => {
        if (!tokenReady || !selectedWorkspaceId) return
        void loadWorkspaceDetails(selectedWorkspaceId)
    }, [selectedWorkspaceId, tokenReady])

    return (
        <div style={{ backgroundColor: '#f5f5f7', minHeight: '100vh', position: 'relative', fontFamily: FONT, overflowX: 'hidden' }}>


            {/* ── Apple-like Animated 4K Liquid Ocean Background ── */}
            <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none', zIndex: 0 }}>
                {/* Flowing Ocean Image (Animated) */}
                <div style={{ 
                    position: 'absolute', inset: 0, 
                    backgroundImage: 'url(https://images.unsplash.com/photo-1473448912268-2022ce9509d8?q=80&w=3840&auto=format&fit=crop)',
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

            

            {/* ── Page Content ── */}
            <div style={{ position: 'relative', zIndex: 10, maxWidth: 1200, margin: '0 auto', padding: '40px 24px 60px' }}>

                {/* ── Page Hero ── */}
                <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0}
                    style={{ textAlign: 'center', marginBottom: 40 }}>
                    <div style={{
                        display: 'inline-flex', alignItems: 'center', gap: 8, padding: '7px 16px',
                        borderRadius: 99, marginBottom: 20, ...GLASS,
                        boxShadow: '0 4px 20px rgba(0,0,0,0.09)',
                    }}>
                        <History style={{ width: 13, height: 13, color: '#0ea5e9' }} />
                        <span style={{ fontSize: 12, fontWeight: 700, color: '#3a3a3c' }}>Versioned Research Workspaces</span>
                    </div>
                    <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)', fontWeight: 900, letterSpacing: '-0.05em', color: '#000', marginBottom: 12, lineHeight: 1.05 }}>
                        Study &amp; <span style={{ color: '#0071e3' }}>Reproducibility</span>
                    </h1>
                    <p style={{ fontSize: '1rem', color: '#6e6e73', fontWeight: 500, maxWidth: 480, margin: '0 auto' }}>
                        Create workspace versions, inspect snapshots, run restore dry-runs, and export reproducibility packages.
                    </p>
                </motion.div>

                {/* ── Error banner ── */}
                <AnimatePresence>
                    {error && (
                        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                            style={{ marginBottom: 20, padding: '14px 20px', borderRadius: 16, background: 'rgba(255,59,48,0.08)', border: '1px solid rgba(255,59,48,0.25)', color: '#c0392b', fontSize: 13, fontWeight: 600 }}>
                            {error}
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* ── Main Grid ── */}
                <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 20, alignItems: 'start' }}>

                    {/* ── LEFT SIDEBAR ── */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

                        {/* Auth Token Card */}
                        <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={1} style={{ ...GLASS, padding: '24px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                                <div style={{ width: 32, height: 32, borderRadius: 10, background: 'rgba(0,113,227,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <Shield style={{ width: 14, height: 14, color: '#0071e3' }} />
                                </div>
                                <p style={{ fontSize: 11, fontWeight: 800, color: '#000', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Auth Token</p>
                            </div>
                            <textarea
                                value={tokenInput}
                                onChange={(e) => setTokenInput(e.target.value)}
                                rows={3}
                                placeholder="Paste JWT from /api/v1/auth/login"
                                style={{
                                    width: '100%', padding: '11px 14px', border: '1.5px solid rgba(0,0,0,0.08)',
                                    borderRadius: 14, fontSize: 12, fontWeight: 500, color: '#000', fontFamily: FONT,
                                    outline: 'none', background: 'rgba(255,255,255,0.7)', resize: 'vertical',
                                    boxSizing: 'border-box', marginBottom: 12,
                                }}
                            />
                            <PrimaryBtn onClick={() => void applyToken()} disabled={isLoading}>
                                <Shield style={{ width: 13, height: 13 }} />
                                Apply token
                            </PrimaryBtn>
                        </motion.div>

                        {/* Create Workspace Card */}
                        <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={2} style={{ ...GLASS, padding: '24px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                                <div style={{ width: 32, height: 32, borderRadius: 10, background: 'rgba(52,199,89,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <Save style={{ width: 14, height: 14, color: '#34c759' }} />
                                </div>
                                <p style={{ fontSize: 11, fontWeight: 800, color: '#000', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Create Workspace</p>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                <GlassInput value={newWorkspaceName} onChange={setNewWorkspaceName} placeholder="Workspace name" />
                                <GlassInput value={newWorkspaceDescription} onChange={setNewWorkspaceDescription} placeholder="Description (optional)" />
                                <GhostBtn onClick={() => void createWorkspace()} disabled={isLoading || !tokenReady || !newWorkspaceName.trim()}>
                                    <Save style={{ width: 13, height: 13 }} />
                                    Save workspace
                                </GhostBtn>
                            </div>
                        </motion.div>

                        {/* Workspaces List */}
                        <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={3} style={{ ...GLASS, padding: '24px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                                <p style={{ fontSize: 11, fontWeight: 800, color: '#000', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Workspaces</p>
                                <button onClick={() => void loadWorkspaces()} disabled={isLoading || !tokenReady}
                                    style={{ width: 30, height: 30, borderRadius: 10, border: '1px solid rgba(0,0,0,0.1)', background: 'rgba(255,255,255,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', opacity: (isLoading || !tokenReady) ? 0.4 : 1 }}>
                                    <RefreshCw style={{ width: 13, height: 13, color: '#6e6e73' }} />
                                </button>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {workspaces.map((workspace, i) => (
                                    <motion.button
                                        key={workspace.id}
                                        variants={fadeUp} initial="hidden" animate="visible" custom={i}
                                        onClick={() => setSelectedWorkspaceId(workspace.id)}
                                        style={{
                                            width: '100%', textAlign: 'left', padding: '12px 16px', borderRadius: 16,
                                            border: selectedWorkspaceId === workspace.id ? '1.5px solid rgba(0,113,227,0.4)' : '1.5px solid rgba(0,0,0,0.06)',
                                            background: selectedWorkspaceId === workspace.id ? 'rgba(0,113,227,0.07)' : 'rgba(255,255,255,0.6)',
                                            cursor: 'pointer', transition: 'all 0.15s',
                                        }}>
                                        <p style={{ fontSize: 13, fontWeight: 700, color: selectedWorkspaceId === workspace.id ? '#0071e3' : '#000', marginBottom: 2 }}>{workspace.name}</p>
                                        <p style={{ fontSize: 11, color: '#6e6e73' }}>{workspace.description || 'No description'}</p>
                                    </motion.button>
                                ))}
                                {workspaces.length === 0 && (
                                    <p style={{ fontSize: 13, color: '#6e6e73', textAlign: 'center', padding: '20px 0' }}>
                                        {tokenReady ? 'No workspaces yet.' : 'Apply token to load.'}
                                    </p>
                                )}
                            </div>
                        </motion.div>
                    </div>

                    {/* ── RIGHT MAIN PANEL ── */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

                        {/* Workspace header */}
                        <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={1}
                            style={{ ...GLASS, padding: '20px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                            <div>
                                <p style={{ fontSize: '1.1rem', fontWeight: 900, color: '#000', letterSpacing: '-0.03em' }}>
                                    {selectedWorkspace?.name || 'Select a workspace'}
                                </p>
                                <p style={{ fontSize: 13, color: '#6e6e73', marginTop: 2 }}>
                                    {selectedWorkspace?.description || 'Pick a workspace on the left to manage versions and reproducibility.'}
                                </p>
                            </div>
                            {selectedWorkspaceId && (
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                    <GhostBtn onClick={() => void loadWorkspaceDetails(selectedWorkspaceId)} disabled={isLoading}>
                                        <Database style={{ width: 13, height: 13 }} /> Refresh
                                    </GhostBtn>
                                    <GhostBtn onClick={() => void downloadReproPackage()} disabled={isLoading}>
                                        <Download style={{ width: 13, height: 13 }} /> Repro JSON
                                    </GhostBtn>
                                    <GhostBtn onClick={() => void downloadNotebookTemplate('python')} disabled={isLoading}>
                                        <Download style={{ width: 13, height: 13 }} /> Python
                                    </GhostBtn>
                                    <GhostBtn onClick={() => void downloadNotebookTemplate('r')} disabled={isLoading}>
                                        <Download style={{ width: 13, height: 13 }} /> R template
                                    </GhostBtn>
                                    <GhostBtn onClick={() => void queueAsyncReproPackage()} disabled={isLoading}>
                                        <History style={{ width: 13, height: 13 }} /> Queue job
                                    </GhostBtn>
                                </div>
                            )}
                        </motion.div>

                        {/* ── Empty state ── */}
                        {!selectedWorkspaceId && (
                            <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={2}
                                style={{ ...GLASS, padding: '60px 40px', textAlign: 'center' }}>
                                <History style={{ width: 40, height: 40, color: '#b0b0b5', margin: '0 auto 16px' }} />
                                <p style={{ fontSize: '1.1rem', fontWeight: 800, color: '#000', marginBottom: 8 }}>No workspace selected</p>
                                <p style={{ fontSize: 13, color: '#6e6e73' }}>Apply your auth token and select a workspace on the left.</p>
                            </motion.div>
                        )}

                        {selectedWorkspaceId && (
                            <AnimatePresence>
                                {/* ── Snapshot Metric Cards ── */}
                                <motion.div key="snapshot" variants={fadeUp} initial="hidden" animate="visible" custom={2}>
                                    <p style={{ fontSize: 11, fontWeight: 800, color: '#6e6e73', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>Current Snapshot</p>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                                        <MetricCard label="Notes" value={String(snapshot?.notes.length ?? 0)} />
                                        <MetricCard label="Saved Queries" value={String(snapshot?.saved_queries.length ?? 0)} />
                                        <MetricCard label="Compare Runs" value={String(snapshot?.compare_history.length ?? 0)} />
                                        <MetricCard label="Timeline Runs" value={String(snapshot?.timeline_history.length ?? 0)} />
                                    </div>
                                </motion.div>

                                {/* ── Create Version ── */}
                                <motion.div key="createver" variants={fadeUp} initial="hidden" animate="visible" custom={3}
                                    style={{ ...GLASS, padding: '24px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                                        <div style={{ width: 32, height: 32, borderRadius: 10, background: 'rgba(94,92,230,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <Sparkles style={{ width: 14, height: 14, color: '#5e5ce6' }} />
                                        </div>
                                        <p style={{ fontSize: 11, fontWeight: 800, color: '#000', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Save New Version</p>
                                    </div>
                                    <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                                        <div style={{ flex: 1, minWidth: 200 }}>
                                            <GlassInput value={versionLabel} onChange={setVersionLabel} placeholder="Version label (optional)" />
                                        </div>
                                        <PrimaryBtn onClick={() => void createVersion()} disabled={isLoading}>
                                            <Sparkles style={{ width: 13, height: 13 }} />
                                            Save version
                                        </PrimaryBtn>
                                    </div>
                                </motion.div>

                                {/* ── Version History ── */}
                                <motion.div key="versions" variants={fadeUp} initial="hidden" animate="visible" custom={4}
                                    style={{ ...GLASS, padding: '24px' }}>
                                    <p style={{ fontSize: 11, fontWeight: 800, color: '#000', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 16 }}>Version History</p>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                        {versions.map((version, i) => (
                                            <motion.div key={version.id} variants={fadeUp} initial="hidden" animate="visible" custom={i}
                                                style={{ padding: '14px 16px', borderRadius: 18, background: 'rgba(255,255,255,0.7)', border: '1.5px solid rgba(0,0,0,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                                                <div>
                                                    <p style={{ fontSize: 13, fontWeight: 800, color: '#000' }}>{version.label || 'Unnamed version'}</p>
                                                    <p style={{ fontSize: 11, color: '#6e6e73', marginTop: 2 }}>
                                                        {version.created_at ? new Date(version.created_at).toLocaleString() : 'Unknown date'}
                                                    </p>
                                                    <p style={{ fontSize: 11, color: '#6e6e73' }}>
                                                        notes: {version.counts.notes} · queries: {version.counts.saved_queries} · compare: {version.counts.compare_history}
                                                    </p>
                                                </div>
                                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                                    <button onClick={() => void viewVersion(version.id)} disabled={isLoading}
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '7px 14px', borderRadius: 99, border: '1px solid rgba(0,0,0,0.1)', background: 'rgba(255,255,255,0.8)', fontSize: 11, fontWeight: 700, color: '#1d1d1f', cursor: 'pointer', fontFamily: FONT }}>
                                                        <Eye style={{ width: 11, height: 11 }} /> View
                                                    </button>
                                                    <button onClick={() => void dryRunRestore(version.id)} disabled={isLoading}
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '7px 14px', borderRadius: 99, border: '1px solid rgba(0,0,0,0.1)', background: 'rgba(255,255,255,0.8)', fontSize: 11, fontWeight: 700, color: '#1d1d1f', cursor: 'pointer', fontFamily: FONT }}>
                                                        <RotateCcw style={{ width: 11, height: 11 }} /> Dry-run
                                                    </button>
                                                    <button onClick={() => void downloadReproPackage(version.id)} disabled={isLoading}
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '7px 14px', borderRadius: 99, background: '#000', color: '#fff', border: 'none', fontSize: 11, fontWeight: 700, cursor: 'pointer', fontFamily: FONT }}>
                                                        <Download style={{ width: 11, height: 11 }} /> Repro JSON
                                                    </button>
                                                    <button onClick={() => void downloadNotebookTemplate('python', version.id)} disabled={isLoading}
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '7px 14px', borderRadius: 99, border: '1px solid rgba(0,0,0,0.1)', background: 'rgba(255,255,255,0.8)', fontSize: 11, fontWeight: 700, color: '#1d1d1f', cursor: 'pointer', fontFamily: FONT }}>
                                                        <Download style={{ width: 11, height: 11 }} /> Notebook
                                                    </button>
                                                    <button onClick={() => void queueAsyncReproPackage(version.id)} disabled={isLoading}
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '7px 14px', borderRadius: 99, border: '1px solid rgba(0,0,0,0.1)', background: 'rgba(255,255,255,0.8)', fontSize: 11, fontWeight: 700, color: '#1d1d1f', cursor: 'pointer', fontFamily: FONT }}>
                                                        <History style={{ width: 11, height: 11 }} /> Async job
                                                    </button>
                                                </div>
                                            </motion.div>
                                        ))}
                                        {versions.length === 0 && (
                                            <p style={{ fontSize: 13, color: '#6e6e73', textAlign: 'center', padding: '24px 0' }}>No versions saved yet. Create your first version above.</p>
                                        )}
                                    </div>
                                </motion.div>

                                {/* ── Selected Version Detail ── */}
                                {selectedVersion && (
                                    <motion.div key="verdetail" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                                        style={{ ...GLASS, padding: '24px', border: '1.5px solid rgba(0,113,227,0.25)', background: 'rgba(0,113,227,0.04)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                                            <p style={{ fontSize: 11, fontWeight: 800, color: '#0071e3', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                                                Selected Version Detail
                                            </p>
                                            <button onClick={() => setSelectedVersion(null)} style={{ width: 26, height: 26, borderRadius: 8, border: 'none', background: 'rgba(0,0,0,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
                                                <X style={{ width: 12, height: 12, color: '#6e6e73' }} />
                                            </button>
                                        </div>
                                        <p style={{ fontSize: 13, fontWeight: 700, color: '#000', marginBottom: 12 }}>
                                            {selectedVersion.label || 'Unnamed version'} <span style={{ color: '#6e6e73', fontWeight: 500, fontSize: 11 }}>({selectedVersion.id})</span>
                                        </p>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                                            <MetricCard label="Notes" value={String(selectedVersion.counts.notes)} />
                                            <MetricCard label="Saved Queries" value={String(selectedVersion.counts.saved_queries)} />
                                            <MetricCard label="Compare Runs" value={String(selectedVersion.counts.compare_history)} />
                                            <MetricCard label="Timeline Runs" value={String(selectedVersion.counts.timeline_history)} />
                                        </div>
                                    </motion.div>
                                )}

                                {/* ── Background Jobs ── */}
                                <motion.div key="jobs" variants={fadeUp} initial="hidden" animate="visible" custom={5}
                                    style={{ ...GLASS, padding: '24px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                                        <p style={{ fontSize: 11, fontWeight: 800, color: '#000', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Background Jobs</p>
                                        <GhostBtn onClick={() => void refreshJobs()} disabled={isLoading}>
                                            <RefreshCw style={{ width: 12, height: 12 }} /> Refresh
                                        </GhostBtn>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {jobs.map(job => (
                                            <div key={job.id} style={{ padding: '12px 16px', borderRadius: 16, background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(0,0,0,0.06)' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                                                    <span style={{ fontSize: 13, fontWeight: 700, color: '#000' }}>{job.job_type}</span>
                                                    <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 99, background: job.status === 'completed' ? 'rgba(52,199,89,0.12)' : 'rgba(255,159,10,0.12)', color: job.status === 'completed' ? '#34c759' : '#ff9f0a' }}>{job.status}</span>
                                                </div>
                                                <p style={{ fontSize: 11, color: '#6e6e73' }}>progress: {job.progress}% | {job.message || '-'}</p>
                                                <p style={{ fontSize: 10, color: '#b0b0b5', marginTop: 2 }}>{job.created_at || '-'}</p>
                                            </div>
                                        ))}
                                        {jobs.length === 0 && <p style={{ fontSize: 13, color: '#6e6e73', textAlign: 'center', padding: '20px 0' }}>No background jobs yet.</p>}
                                    </div>
                                </motion.div>

                                {/* ── Members ── */}
                                <motion.div key="members" variants={fadeUp} initial="hidden" animate="visible" custom={6}
                                    style={{ ...GLASS, padding: '24px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                                        <div style={{ width: 32, height: 32, borderRadius: 10, background: 'rgba(255,159,10,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <Users style={{ width: 14, height: 14, color: '#ff9f0a' }} />
                                        </div>
                                        <p style={{ fontSize: 11, fontWeight: 800, color: '#000', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Workspace Members</p>
                                    </div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 16, alignItems: 'center' }}>
                                        <div style={{ flex: 1, minWidth: 180 }}>
                                            <GlassInput value={memberIdentifier} onChange={setMemberIdentifier} placeholder="username or email" />
                                        </div>
                                        <select value={memberRole} onChange={e => setMemberRole(e.target.value as 'viewer' | 'editor')}
                                            style={{ padding: '11px 14px', border: '1.5px solid rgba(0,0,0,0.08)', borderRadius: 14, fontSize: 13, fontFamily: FONT, background: 'rgba(255,255,255,0.7)', outline: 'none', cursor: 'pointer' }}>
                                            <option value="viewer">viewer</option>
                                            <option value="editor">editor</option>
                                        </select>
                                        <GhostBtn onClick={() => void addMember()} disabled={isLoading || !memberIdentifier.trim()}>
                                            <Users style={{ width: 12, height: 12 }} /> Add
                                        </GhostBtn>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {members.map(member => (
                                            <div key={member.user_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderRadius: 16, background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(0,0,0,0.06)' }}>
                                                <div>
                                                    <p style={{ fontSize: 13, fontWeight: 700, color: '#000' }}>{member.user_id}</p>
                                                    <p style={{ fontSize: 11, color: '#6e6e73' }}>role: {member.role} · status: {member.status}</p>
                                                </div>
                                                {!member.is_owner && (
                                                    <button onClick={() => void removeMember(member.user_id)} disabled={isLoading}
                                                        style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '7px 14px', borderRadius: 99, border: '1px solid rgba(255,59,48,0.2)', background: 'rgba(255,59,48,0.06)', fontSize: 11, fontWeight: 700, color: '#ff3b30', cursor: 'pointer', fontFamily: FONT }}>
                                                        <X style={{ width: 11, height: 11 }} /> Remove
                                                    </button>
                                                )}
                                            </div>
                                        ))}
                                        {members.length === 0 && <p style={{ fontSize: 13, color: '#6e6e73', textAlign: 'center', padding: '20px 0' }}>No members loaded.</p>}
                                    </div>
                                </motion.div>
                            </AnimatePresence>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Keyframe Animations ── */}
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
                textarea::placeholder, input::placeholder { color: #b0b0b5; }
            `}</style>
        </div>
    )
}
