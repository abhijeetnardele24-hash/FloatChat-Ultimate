"use client"

import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface Measurement {
  pressure: number | null
  depth: number | null
  temperature: number | null
  temperature_qc: number | null
  salinity: number | null
  salinity_qc: number | null
}

interface ProfileData {
  profile_id: number
  measurements: Measurement[]
  count: number
  wmo_number: string
  profile_date: string
  latitude: number
  longitude: number
}

interface DepthProfileChartProps {
  data: ProfileData
  variable: 'temperature' | 'salinity'
  height?: number
}

export default function DepthProfileChart({ 
  data, 
  variable, 
  height = 400 
}: DepthProfileChartProps) {
  // Process data with useMemo to avoid effect cascading
  const chartData = React.useMemo(() => {
    if (!data?.measurements) return []

    return data.measurements
      .filter(m => {
        const qcField = variable === 'temperature' ? m.temperature_qc : m.salinity_qc
        const value = variable === 'temperature' ? m.temperature : m.salinity
        return qcField === 1 && value !== null && value !== undefined
      })
      .map(m => ({
        depth: m.depth || 0,
        value: variable === 'temperature' ? m.temperature! : m.salinity!,
        pressure: m.pressure || 0,
      }))
      .filter(d => d.value !== null && d.value !== undefined)
  }, [data, variable])

  const formatYAxis = (value: number) => {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}km`
    }
    return `${value}m`
  }

  const formatTooltip = (value: number | undefined, name?: string) => {
    if (value === undefined) return ['', '']
    if (name === 'value') {
      const unit = variable === 'temperature' ? '°C' : 'PSU'
      return [`${value.toFixed(3)} ${unit}`, variable === 'temperature' ? 'Temperature' : 'Salinity']
    }
    if (name === 'depth') {
      return [formatYAxis(value), 'Depth']
    }
    return [value, name || '']
  }

  const variableConfig = {
    temperature: {
      color: '#ef4444',
      name: 'Temperature',
      unit: '°C',
      domain: [-2, 35] as [number, number],
    },
    salinity: {
      color: '#3b82f6', 
      name: 'Salinity',
      unit: 'PSU',
      domain: [30, 40] as [number, number],
    },
  }

  const config = variableConfig[variable]

  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border">
        <p className="text-gray-500">No valid {config.name.toLowerCase()} data available</p>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          {config.name} Profile
        </h3>
        <p className="text-sm text-gray-600">
          Float {data.wmo_number} • {new Date(data.profile_date).toLocaleDateString()} • 
          {data.latitude.toFixed(3)}°, {data.longitude.toFixed(3)}°
        </p>
        <p className="text-xs text-gray-500">
          {chartData.length} data points • QC Flag 1 (Good data only)
        </p>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            dataKey="value"
            domain={config.domain}
            label={{
              value: `${config.name} (${config.unit})`,
              position: 'insideBottom',
              offset: -5,
              style: { textAnchor: 'middle' }
            }}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            type="number"
            dataKey="depth"
            domain={['dataMax - 100', 'dataMin']}
            reversed
            label={{
              value: 'Depth',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle' }
            }}
            tickFormatter={formatYAxis}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={(value) => `${config.name}: ${(value || 0).toFixed(3)} ${config.unit}`}
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '6px'
            }}
          />
          <Line
            type="monotone"
            dataKey="depth"
            stroke={config.color}
            strokeWidth={2}
            dot={false}
            name="depth"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 flex justify-between text-xs text-gray-500">
        <span>Min: {Math.min(...chartData.map(d => d.value)).toFixed(3)} {config.unit}</span>
        <span>Max: {Math.max(...chartData.map(d => d.value)).toFixed(3)} {config.unit}</span>
        <span>Range: {(Math.max(...chartData.map(d => d.value)) - Math.min(...chartData.map(d => d.value))).toFixed(3)} {config.unit}</span>
      </div>
    </div>
  )
}
