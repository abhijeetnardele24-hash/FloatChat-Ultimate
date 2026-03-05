'use client'

import { useRef, useState } from 'react'
import { MapPin, Maximize2, Minimize2 } from 'lucide-react'
import type { ArgoFloat } from '@/lib/api-client'

interface FloatMapProps {
    floats: ArgoFloat[]
    selectedFloat?: string | null
    onFloatClick?: (wmoNumber: string) => void
}

export function FloatMap({ floats, selectedFloat, onFloatClick }: FloatMapProps) {
    const mapContainerRef = useRef<HTMLDivElement>(null)
    const [isFullscreen, setIsFullscreen] = useState(false)

    // Simple map visualization using CSS and DOM (no external map library needed)
    // This creates a visual representation of float locations

    const getBounds = () => {
        if (floats.length === 0) return { minLat: -40, maxLat: 30, minLon: 30, maxLon: 120 }

        const lats = floats.map(f => f.last_latitude || 0).filter(l => l !== 0)
        const lons = floats.map(f => f.last_longitude || 0).filter(l => l !== 0)

        return {
            minLat: Math.min(...lats, -40),
            maxLat: Math.max(...lats, 30),
            minLon: Math.min(...lons, 30),
            maxLon: Math.max(...lons, 120)
        }
    }

    const bounds = getBounds()
    const latRange = bounds.maxLat - bounds.minLat
    const lonRange = bounds.maxLon - bounds.minLon

    const getPosition = (lat: number, lon: number) => {
        const x = ((lon - bounds.minLon) / lonRange) * 100
        const y = ((bounds.maxLat - lat) / latRange) * 100
        return { x, y }
    }

    return (
        <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50' : 'w-full h-full'}`}>
            <div className="absolute top-4 right-4 z-10 flex gap-2">
                <button
                    onClick={() => setIsFullscreen(!isFullscreen)}
                    className="p-2 glass rounded-lg hover:bg-white/20 transition-all"
                >
                    {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                </button>
            </div>

            <div
                ref={mapContainerRef}
                className="w-full h-full rounded-xl overflow-hidden relative bg-gradient-to-br from-blue-950 via-blue-900 to-blue-950"
                style={{
                    backgroundImage: `
            radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 30%, rgba(16, 185, 129, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 80%, rgba(14, 165, 233, 0.14) 0%, transparent 50%)
          `
                }}
            >
                {/* Grid lines */}
                <div className="absolute inset-0 opacity-20">
                    {[...Array(10)].map((_, i) => (
                        <div
                            key={`h-${i}`}
                            className="absolute w-full border-t border-white/20"
                            style={{ top: `${i * 10}%` }}
                        />
                    ))}
                    {[...Array(10)].map((_, i) => (
                        <div
                            key={`v-${i}`}
                            className="absolute h-full border-l border-white/20"
                            style={{ left: `${i * 10}%` }}
                        />
                    ))}
                </div>

                {/* Ocean label */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-6xl font-bold text-white/5 pointer-events-none">
                    INDIAN OCEAN
                </div>

                {/* Float markers */}
                {floats.map((float) => {
                    if (!float.last_latitude || !float.last_longitude) return null

                    const pos = getPosition(float.last_latitude, float.last_longitude)
                    const isSelected = selectedFloat === float.wmo_number

                    return (
                        <div
                            key={float.id}
                            className="absolute group cursor-pointer"
                            style={{
                                left: `${pos.x}%`,
                                top: `${pos.y}%`,
                                transform: 'translate(-50%, -50%)'
                            }}
                            onClick={() => onFloatClick?.(float.wmo_number)}
                        >
                            {/* Pulse animation */}
                            <div className={`absolute inset-0 rounded-full ${isSelected ? 'bg-yellow-400' : 'bg-blue-400'
                                } opacity-50 animate-ping`} />

                            {/* Marker */}
                            <div className={`relative w-4 h-4 rounded-full ${isSelected
                                    ? 'bg-yellow-400 ring-4 ring-yellow-400/50'
                                    : 'bg-blue-500 ring-2 ring-blue-500/50'
                                } transition-all group-hover:scale-150 group-hover:ring-4`}>
                                <MapPin className="absolute -top-6 -left-2 w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>

                            {/* Tooltip */}
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                                <div className="glass-dark px-3 py-2 rounded-lg border border-white/20 whitespace-nowrap">
                                    <p className="text-sm font-semibold">{float.wmo_number}</p>
                                    <p className="text-xs text-gray-400">{float.platform_type}</p>
                                    <p className="text-xs text-gray-400">
                                        {float.last_latitude.toFixed(2)}°, {float.last_longitude.toFixed(2)}°
                                    </p>
                                    <p className="text-xs">
                                        <span className={`inline-block w-2 h-2 rounded-full mr-1 ${float.status === 'ACTIVE' ? 'bg-green-400' : 'bg-gray-400'
                                            }`} />
                                        {float.status}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )
                })}

                {/* Legend */}
                <div className="absolute bottom-4 left-4 glass-dark p-4 rounded-lg border border-white/20">
                    <h4 className="text-sm font-semibold mb-2">Legend</h4>
                    <div className="space-y-2 text-xs">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-blue-500" />
                            <span>ARGO Float</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-yellow-400" />
                            <span>Selected</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-green-400" />
                            <span>Active</span>
                        </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-white/20 text-xs text-gray-400">
                        <p>Indian Ocean</p>
                        <p>{floats.length} floats displayed</p>
                    </div>
                </div>

                {/* Coordinates display */}
                <div className="absolute top-4 left-4 glass-dark px-3 py-2 rounded-lg border border-white/20 text-xs">
                    <p className="text-gray-400">Bounds:</p>
                    <p>{bounds.minLat.toFixed(1)}°S to {bounds.maxLat.toFixed(1)}°N</p>
                    <p>{bounds.minLon.toFixed(1)}°E to {bounds.maxLon.toFixed(1)}°E</p>
                </div>
            </div>
        </div>
    )
}
