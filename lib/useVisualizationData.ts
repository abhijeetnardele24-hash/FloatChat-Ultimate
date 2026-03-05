'use client'
import { useCallback, useEffect, useRef, useState } from 'react'

// ── Types matching the enhanced /api/direct/argo/stats response ──────────────
export interface OceanBasin {
    name: string
    floats: number
    profiles: number
}

export interface PlatformType {
    type: string
    count: number
}

export interface Measurement {
    pressure: number | null
    depth: number | null
    temperature: number
    salinity: number
}

export interface RecentProfile {
    wmo_number: string
    cycle: number
    date: string | null
    ocean_basin: string
    platform_type: string
    status: string
    latitude: number | null
    longitude: number | null
    avg_temperature: number | null
    avg_salinity: number | null
    measurements: number
}

export interface VizStats {
    total_floats: number
    total_profiles: number
    total_measurements: number
    ocean_basins_count: number
    avg_temperature: number | null
    avg_salinity: number | null
    active_floats: number
    inactive_floats: number
    status_breakdown: Record<string, number>
    platform_types: PlatformType[]
    ocean_basins: OceanBasin[]
    monthly_profiles: number[]   // 12-element array Jan-Dec
    yearly_profiles: Record<string, number>
    recent_profiles: RecentProfile[]
    measurements: Measurement[]  // up to 500 samples for scatter charts
    last_updated: string
}

export interface VizData {
    stats: VizStats | null
    loading: boolean
    lastRefresh: Date
    countdown: number
    refetch: () => void
}

const REFRESH_MS = 30_000

export function useVisualizationData(): VizData {
    const [stats, setStats] = useState<VizStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [lastRefresh, setLast] = useState(new Date())
    const [countdown, setCountdown] = useState(REFRESH_MS / 1000)
    const mounted = useRef(false)

    const fetchAll = useCallback(async () => {
        try {
            const res = await fetch('/api/direct/argo/stats')
            if (res.ok) {
                const data: VizStats = await res.json()
                if (!data.error) {
                    setStats(data)
                }
            }
            setLast(new Date())
        } catch { /* silent */ }
        finally { setLoading(false) }
    }, [])

    useEffect(() => {
        if (mounted.current) return
        mounted.current = true
        fetchAll()
        const iv = setInterval(() => {
            fetchAll()
            setCountdown(REFRESH_MS / 1000)
        }, REFRESH_MS)
        return () => clearInterval(iv)
    }, [fetchAll])

    useEffect(() => {
        const t = setInterval(() =>
            setCountdown(c => c <= 1 ? REFRESH_MS / 1000 : c - 1), 1000)
        return () => clearInterval(t)
    }, [])

    return { stats, loading, lastRefresh, countdown, refetch: fetchAll }
}
