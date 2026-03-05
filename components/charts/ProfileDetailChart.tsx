"use client"

import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface ProfileDetailChartProps {
  data: Array<{
    depth: number
    temperature: number | null
    salinity: number | null
  }>
  height?: number
}

export default function ProfileDetailChart({ data, height = 400 }: ProfileDetailChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border">
        <p className="text-gray-500">No profile data available</p>
      </div>
    )
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Depth Profile</h3>
        <p className="text-sm text-gray-600">
          Temperature and Salinity vs Depth • {data.length} data points
        </p>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

          <XAxis
            type="number"
            dataKey="depth"
            domain={['dataMax - 100', 'dataMin']}
            reversed
            label={{
              value: 'Depth (m)',
              position: 'insideBottom',
              offset: -5,
              style: { textAnchor: 'middle' }
            }}
            tick={{ fontSize: 12 }}
          />

          <YAxis
            type="number"
            dataKey="temperature"
            domain={['dataMin', 'dataMax']}
            label={{
              value: 'Temperature (°C)',
              position: 'insideLeft',
              style: { textAnchor: 'middle' }
            }}
          />

          <YAxis
            type="number"
            dataKey="salinity"
            domain={['dataMin', 'dataMax']}
            label={{
              value: 'Salinity (PSU)',
              position: 'insideRight',
              style: { textAnchor: 'middle' }
            }}
          />

          <Line
            type="monotone"
            dataKey="temperature"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ fill: "#ef4444" }}
          />

          <Line
            type="monotone"
            dataKey="salinity"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: "#3b82f6" }}
          />

          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const depth = payload[0]?.value
                const temp = payload.find((p: any) => p.dataKey === 'temperature')
                const sal = payload.find((p: any) => p.dataKey === 'salinity')

                return (
                  <div className="bg-white p-2 rounded shadow">
                    <p className="font-semibold">Depth: {depth}m</p>
                    {temp && <p className="text-blue-600">Temperature: {temp.value}°C</p>}
                    {sal && <p className="text-cyan-600">Salinity: {sal.value} PSU</p>}
                  </div>
                )
              }
              return null
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
