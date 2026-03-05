"use client"

import React from 'react'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface TooltipData {
  temperature: number
  salinity: number
  depth: number
  pressure: number
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as TooltipData
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="text-sm font-medium text-gray-900">
          T: {data.temperature.toFixed(3)}°C, S: {data.salinity.toFixed(3)} PSU
        </p>
        <p className="text-xs text-gray-600">
          Depth: {data.depth.toFixed(1)}m ({data.pressure.toFixed(1)} dbar)
        </p>
      </div>
    )
  }
  return null
}

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

interface TSDiagramProps {
  data: ProfileData
  height?: number
}

export default function TSDiagram({ data, height = 400 }: TSDiagramProps) {
  // Process data for T-S diagram
  const chartData = React.useMemo(() => {
    if (!data?.measurements) return []

    return data.measurements
      .filter(m => {
        // Only include good quality data (QC flag 1)
        return m.temperature_qc === 1 && 
               m.salinity_qc === 1 && 
               m.temperature !== null && 
               m.salinity !== null &&
               m.temperature !== undefined &&
               m.salinity !== undefined
      })
      .map(m => ({
        salinity: m.salinity!,
        temperature: m.temperature!,
        depth: m.depth || 0,
        pressure: m.pressure || 0,
      }))
      .filter(d => d.temperature !== null && d.salinity !== null)
  }, [data])

  // Color function for depth
  const getDepthColor = (depth: number): string => {
    // Color scale: surface (blue) -> deep (red)
    const maxDepth = Math.max(...chartData.map(d => d.depth))
    const normalizedDepth = Math.min(depth / maxDepth, 1)
    
    if (normalizedDepth < 0.25) {
      return '#3b82f6' // Blue - surface
    } else if (normalizedDepth < 0.5) {
      return '#10b981' // Green - shallow
    } else if (normalizedDepth < 0.75) {
      return '#f59e0b' // Orange - mid
    } else {
      return '#ef4444' // Red - deep
    }
  }


  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border">
        <p className="text-gray-500">No valid T-S data available</p>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Temperature-Salinity Diagram
        </h3>
        <p className="text-sm text-gray-600">
          Float {data.wmo_number} • {new Date(data.profile_date).toLocaleDateString()} • 
          {data.latitude.toFixed(3)}°, {data.longitude.toFixed(3)}°
        </p>
        <p className="text-xs text-gray-500">
          {chartData.length} data points • Color indicates depth (blue=surface, red=deep)
        </p>
      </div>

      <div className="mb-4 flex items-center space-x-4 text-xs">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-blue-500 rounded"></div>
          <span>Surface</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded"></div>
          <span>Shallow</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-amber-500 rounded"></div>
          <span>Mid-depth</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded"></div>
          <span>Deep</span>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <ScatterChart
          margin={{ top: 20, right: 20, bottom: 60, left: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            dataKey="salinity"
            domain={['dataMin - 0.1', 'dataMax + 0.1']}
            label={{
              value: 'Salinity (PSU)',
              position: 'insideBottom',
              offset: -10,
              style: { textAnchor: 'middle' }
            }}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            type="number"
            dataKey="temperature"
            domain={['dataMin - 0.5', 'dataMax + 0.5']}
            label={{
              value: 'Temperature (°C)',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle' }
            }}
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Scatter
            data={chartData}
            fill="#8884d8"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getDepthColor(entry.depth)} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-gray-500">
        <div>
          <span>Temperature Range: </span>
          <span>
            {Math.min(...chartData.map(d => d.temperature)).toFixed(3)}°C - 
            {Math.max(...chartData.map(d => d.temperature)).toFixed(3)}°C
          </span>
        </div>
        <div>
          <span>Salinity Range: </span>
          <span>
            {Math.min(...chartData.map(d => d.salinity)).toFixed(3)} - 
            {Math.max(...chartData.map(d => d.salinity)).toFixed(3)} PSU
          </span>
        </div>
        <div>
          <span>Depth Range: </span>
          <span>
            {Math.min(...chartData.map(d => d.depth)).toFixed(1)}m - 
            {Math.max(...chartData.map(d => d.depth)).toFixed(1)}m
          </span>
        </div>
        <div>
          <span>Data Points: </span>
          <span>{chartData.length}</span>
        </div>
      </div>
    </div>
  )
}
