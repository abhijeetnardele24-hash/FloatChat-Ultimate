'use client'

import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

type ChartValue = string | number | null

interface ChartData {
    name: string
    value: number
    [key: string]: ChartValue
}

interface ChartProps {
    data: ChartData[]
    title?: string
    dataKey?: string
    color?: string
    type?: 'line' | 'area' | 'bar'
}

interface DataChartTooltipProps {
    active?: boolean
    payload?: Array<{
        value?: ChartValue
        payload?: ChartData
    }>
    dataKey: string
}

function DataChartTooltip({ active, payload, dataKey }: DataChartTooltipProps) {
    if (active && payload && payload.length > 0) {
        const first = payload[0]
        return (
            <div className="glass-dark p-3 rounded-lg border border-white/20">
                <p className="text-sm font-semibold">{first.payload?.name ?? ''}</p>
                <p className="text-sm text-blue-400">{`${dataKey}: ${first.value ?? ''}`}</p>
            </div>
        )
    }
    return null
}

export function DataChart({ data, title, dataKey = 'value', color = '#3b82f6', type = 'line' }: ChartProps) {
    return (
        <div className="w-full h-full">
            {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
            <ResponsiveContainer width="100%" height="100%">
                {type === 'line' && (
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                        <XAxis dataKey="name" stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip content={<DataChartTooltip dataKey={dataKey} />} />
                        <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={{ fill: color }} />
                    </LineChart>
                )}
                {type === 'area' && (
                    <AreaChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                        <XAxis dataKey="name" stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip content={<DataChartTooltip dataKey={dataKey} />} />
                        <Area type="monotone" dataKey={dataKey} stroke={color} fill={color} fillOpacity={0.3} />
                    </AreaChart>
                )}
                {type === 'bar' && (
                    <BarChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                        <XAxis dataKey="name" stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip content={<DataChartTooltip dataKey={dataKey} />} />
                        <Bar dataKey={dataKey} fill={color} />
                    </BarChart>
                )}
            </ResponsiveContainer>
        </div>
    )
}

interface TemperatureProfileProps {
    data: Array<{ depth: number; temperature: number }>
}

export function TemperatureProfile({ data }: TemperatureProfileProps) {
    const chartData = data.map(d => ({
        name: `${d.depth}m`,
        depth: d.depth,
        temperature: d.temperature
    }))

    return (
        <div className="w-full h-[400px]">
            <h3 className="text-lg font-semibold mb-4">Temperature Profile</h3>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                    <XAxis dataKey="depth" stroke="#9ca3af" label={{ value: 'Depth (m)', position: 'insideBottom', offset: -5 }} />
                    <YAxis stroke="#9ca3af" label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip
                        content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                                return (
                                    <div className="glass-dark p-3 rounded-lg border border-white/20">
                                        <p className="text-sm">Depth: {payload[0].payload.depth}m</p>
                                        <p className="text-sm text-orange-400">Temp: {payload[0].value}°C</p>
                                    </div>
                                )
                            }
                            return null
                        }}
                    />
                    <Line type="monotone" dataKey="temperature" stroke="#f97316" strokeWidth={3} dot={{ fill: '#f97316', r: 4 }} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    )
}

interface SalinityProfileProps {
    data: Array<{ depth: number; salinity: number }>
}

export function SalinityProfile({ data }: SalinityProfileProps) {
    const chartData = data.map(d => ({
        name: `${d.depth}m`,
        depth: d.depth,
        salinity: d.salinity
    }))

    return (
        <div className="w-full h-[400px]">
            <h3 className="text-lg font-semibold mb-4">Salinity Profile</h3>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                    <XAxis dataKey="depth" stroke="#9ca3af" label={{ value: 'Depth (m)', position: 'insideBottom', offset: -5 }} />
                    <YAxis stroke="#9ca3af" label={{ value: 'Salinity (PSU)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip
                        content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                                return (
                                    <div className="glass-dark p-3 rounded-lg border border-white/20">
                                        <p className="text-sm">Depth: {payload[0].payload.depth}m</p>
                                        <p className="text-sm text-cyan-400">Salinity: {payload[0].value} PSU</p>
                                    </div>
                                )
                            }
                            return null
                        }}
                    />
                    <Area type="monotone" dataKey="salinity" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.3} />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    )
}

interface StatsChartProps {
    floatCount: number
    profileCount: number
    activeCount: number
}

export function StatsChart({ floatCount, profileCount, activeCount }: StatsChartProps) {
    const data = [
        { name: 'Total Floats', value: floatCount, color: '#3b82f6' },
        { name: 'Active Floats', value: activeCount, color: '#10b981' },
        { name: 'Profiles', value: profileCount, color: '#8b5cf6' }
    ]

    return (
        <div className="w-full h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                    <XAxis dataKey="name" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                        content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                                return (
                                    <div className="glass-dark p-3 rounded-lg border border-white/20">
                                        <p className="text-sm font-semibold">{payload[0].payload.name}</p>
                                        <p className="text-sm" style={{ color: payload[0].payload.color }}>
                                            Count: {payload[0].value}
                                        </p>
                                    </div>
                                )
                            }
                            return null
                        }}
                    />
                    <Bar dataKey="value" fill="#3b82f6">
                        {data.map((entry, index) => (
                            <Bar key={`bar-${index}`} fill={entry.color} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}
