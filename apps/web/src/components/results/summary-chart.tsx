"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"

import { cn } from "@/lib/utils"

interface SummaryChartProps {
  critical: number
  high: number
  medium: number
  low: number
  totalIssues: number
  averageScore: number | null
}

const severityRows = [
  { key: "critical", label: "Critical", textClass: "text-rose-600", bgClass: "bg-rose-500", ringClass: "bg-rose-500/12" },
  { key: "high", label: "High", textClass: "text-orange-500", bgClass: "bg-orange-500", ringClass: "bg-orange-500/12" },
  { key: "medium", label: "Medium", textClass: "text-amber-500", bgClass: "bg-amber-500", ringClass: "bg-amber-500/12" },
  { key: "low", label: "Low", textClass: "text-sky-500", bgClass: "bg-sky-500", ringClass: "bg-sky-500/12" },
] as const

export function SummaryChart({ critical, high, medium, low, totalIssues, averageScore }: SummaryChartProps) {
  const data = [
    { name: "Critical", value: critical, color: "#ef4444" },
    { name: "High", value: high, color: "#f97316" },
    { name: "Medium", value: medium, color: "#eab308" },
    { name: "Low", value: low, color: "#3b82f6" },
  ]

  const total = totalIssues || critical + high + medium + low
  const counts = { critical, high, medium, low }

  return (
    <div className="grid gap-8 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
      <div className="relative flex min-h-[280px] items-center justify-center overflow-hidden rounded-[1.75rem] border border-border/70 bg-background/70 p-4">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,hsl(var(--primary)/0.12),transparent_55%)]" />
        {total > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={68}
                  outerRadius={98}
                  paddingAngle={4}
                  stroke="none"
                  dataKey="value"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="rounded-full border border-border/70 bg-background/90 px-8 py-6 text-center shadow-sm backdrop-blur">
                <p className="text-4xl font-semibold text-foreground">{total}</p>
                <p className="mt-1 text-xs uppercase tracking-[0.24em] text-muted-foreground">Findings</p>
                <p className="mt-3 text-sm text-muted-foreground">
                  {averageScore !== null ? `${averageScore}% average score` : "Score pending"}
                </p>
              </div>
            </div>
          </>
        ) : (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <p className="text-3xl font-semibold text-foreground">0</p>
            <p className="mt-2 text-sm text-muted-foreground">No findings were returned for this report.</p>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {severityRows.map((row) => {
          const count = counts[row.key]
          const percentage = total > 0 ? Math.round((count / total) * 100) : 0

          return (
            <div
              key={row.key}
              className={cn(
                "rounded-[1.5rem] border border-border/70 p-4 shadow-sm",
                row.ringClass
              )}
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className={cn("text-sm font-semibold", row.textClass)}>{row.label}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.22em] text-muted-foreground">Severity distribution</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-semibold text-foreground">{count}</p>
                  <p className="text-xs text-muted-foreground">{percentage}% of report</p>
                </div>
              </div>
              <div className="mt-4 h-2 rounded-full bg-background/70">
                <div
                  className={cn("h-full rounded-full", row.bgClass)}
                  style={{ width: `${Math.max(percentage, count > 0 ? 8 : 0)}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
