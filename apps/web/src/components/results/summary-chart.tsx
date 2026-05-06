"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"

interface SummaryChartProps {
  critical: number
  high: number
  medium: number
  low: number
}

export function SummaryChart({ critical, high, medium, low }: SummaryChartProps) {
  const data = [
    { name: "Critical", value: critical, color: "#ef4444" },
    { name: "High", value: high, color: "#f97316" },
    { name: "Medium", value: medium, color: "#eab308" },
    { name: "Low", value: low, color: "#3b82f6" },
  ]

  const total = critical + high + medium + low

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <p className="text-2xl font-bold text-red-600">{critical}</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">Critical</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-orange-600">{high}</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">High</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-yellow-600">{medium}</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">Medium</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-600">{low}</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">Low</p>
        </div>
      </div>

      {total > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name}: ${value}`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-80 flex items-center justify-center text-slate-500">
          No issues found
        </div>
      )}
    </div>
  )
}
