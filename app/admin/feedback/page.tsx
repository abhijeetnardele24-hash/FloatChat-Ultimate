'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { RefreshCcw } from 'lucide-react'
import { apiClient, type ChatFeedbackStatsResponse } from '@/lib/api-client'

export default function FeedbackAdminPage() {
    const [stats, setStats] = useState<ChatFeedbackStatsResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const loadStats = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const response = await apiClient.getChatFeedbackStats(30)
            setStats(response)
        } catch (err) {
            console.error('Failed to fetch feedback stats:', err)
            setError('Unable to load feedback analytics.')
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        void loadStats()
    }, [loadStats])

    return (
        <div className="min-h-screen bg-black text-white">
            <header className="border-b border-white/10">
                <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
                    <div>
                        <h1 className="text-lg font-semibold">Chat Feedback Analytics</h1>
                        <p className="text-xs text-gray-400">Recent sentiment and usage distribution</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <Link href="/chat" className="text-sm text-gray-400 hover:text-white transition-colors">
                            Chat
                        </Link>
                        <button
                            onClick={() => void loadStats()}
                            className="inline-flex items-center gap-2 rounded-lg border border-white/15 px-3 py-1.5 text-sm text-gray-200 hover:bg-white/10 transition-colors"
                            disabled={isLoading}
                        >
                            <RefreshCcw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                            Refresh
                        </button>
                    </div>
                </div>
            </header>

            <main className="mx-auto max-w-6xl space-y-5 px-4 py-6">
                {error && (
                    <div className="rounded-lg border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                        {error}
                    </div>
                )}

                <div className="grid gap-4 md:grid-cols-4">
                    <StatCard label="Total" value={stats?.total_feedback ?? 0} />
                    <StatCard label="Helpful" value={stats?.helpful_count ?? 0} />
                    <StatCard label="Not Helpful" value={stats?.not_helpful_count ?? 0} />
                    <StatCard label="Helpful %" value={stats?.helpful_ratio !== null && stats?.helpful_ratio !== undefined ? `${stats.helpful_ratio}%` : '-'} />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                    <section className="rounded-xl border border-white/10 bg-white/5 p-4">
                        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-300">By Source</h2>
                        <div className="space-y-2">
                            {(stats?.by_source ?? []).length === 0 && !isLoading && (
                                <p className="text-sm text-gray-500">No feedback yet.</p>
                            )}
                            {(stats?.by_source ?? []).map((item) => (
                                <div key={`source-${item.label}`} className="flex items-center justify-between rounded-md bg-black/30 px-3 py-2">
                                    <span className="text-sm text-gray-200">{item.label}</span>
                                    <span className="text-sm text-gray-400">{item.count}</span>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section className="rounded-xl border border-white/10 bg-white/5 p-4">
                        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-300">By Query Type</h2>
                        <div className="space-y-2">
                            {(stats?.by_query_type ?? []).length === 0 && !isLoading && (
                                <p className="text-sm text-gray-500">No feedback yet.</p>
                            )}
                            {(stats?.by_query_type ?? []).map((item) => (
                                <div key={`query-${item.label}`} className="flex items-center justify-between rounded-md bg-black/30 px-3 py-2">
                                    <span className="text-sm text-gray-200">{item.label}</span>
                                    <span className="text-sm text-gray-400">{item.count}</span>
                                </div>
                            ))}
                        </div>
                    </section>
                </div>

                <section className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-300">Recent Feedback</h2>
                    {(stats?.recent ?? []).length === 0 && !isLoading && (
                        <p className="text-sm text-gray-500">No records available.</p>
                    )}
                    <div className="space-y-2">
                        {(stats?.recent ?? []).map((entry, index) => (
                            <div key={`recent-${index}`} className="grid gap-2 rounded-md border border-white/10 bg-black/30 px-3 py-2 text-xs md:grid-cols-4">
                                <span className="text-gray-400">{entry.created_at ? new Date(entry.created_at).toLocaleString() : '-'}</span>
                                <span className={entry.rating === 1 ? 'text-emerald-300' : 'text-rose-300'}>
                                    {entry.rating === 1 ? 'Helpful' : 'Not helpful'}
                                </span>
                                <span className="text-gray-300">{entry.source || 'unknown'}</span>
                                <span className="text-gray-400">{entry.query_type || 'unknown'}</span>
                            </div>
                        ))}
                    </div>
                </section>
            </main>
        </div>
    )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
            <p className="text-xs uppercase tracking-wide text-gray-400">{label}</p>
            <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
        </div>
    )
}
