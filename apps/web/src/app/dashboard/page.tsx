"use client"

import { useEffect, useState } from "react"
import { Sidebar } from "@/components/layout/sidebar"
import { Button } from "@/components/ui/button"
import { StatsCard } from "@/components/dashboard/stats-card"
import { RecentAnalyses } from "@/components/dashboard/recent-analyses"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Plus, Radar, Sparkles, ShieldAlert } from "lucide-react"
import Link from "next/link"
import {
  listAnalysesForFile,
  listFiles,
  type BackendAnalysisResult,
  type BackendFinding,
} from "@/lib/backend-api"

interface DashboardStat {
  label: string
  value: string | number
  icon: string
}

interface DashboardAnalysis {
  id: string
  name: string
  date: string
  status: string
  issuesFound: number
  severity: string
}

interface DashboardState {
  stats: DashboardStat[]
  recentAnalyses: DashboardAnalysis[]
}

const defaultState: DashboardState = {
  stats: [
    { label: "Files Uploaded", value: 0, icon: "FileText" },
    { label: "Analyses Run", value: 0, icon: "AlertCircle" },
    { label: "Estimated Savings", value: "$0", icon: "DollarSign" },
    { label: "Avg Security Score", value: "N/A", icon: "Shield" },
  ],
  recentAnalyses: [],
}

function getAnalysisDate(analysis: BackendAnalysisResult, fallback: string) {
  return analysis.completed_at || analysis.started_at || fallback
}

function getSeverity(finding: BackendFinding) {
  if (finding.severity === "info") {
    return "low"
  }
  return finding.severity
}

function highestSeverity(findings: BackendFinding[]) {
  const order = ["critical", "high", "medium", "low", "info"] as const
  for (const severity of order) {
    if (findings.some((finding) => finding.severity === severity)) {
      return severity === "info" ? "low" : severity
    }
  }
  return "low"
}

function parseSavings(findings: BackendFinding[]) {
  let total = 0
  for (const finding of findings) {
    const candidates = [finding.metadata["estimated_cost"], finding.metadata["estimated_impact"]]
    for (const candidate of candidates) {
      if (typeof candidate !== "string") {
        continue
      }
      const match = candidate.match(/\$\s*([\d,]+(?:\.\d+)?)/)
      if (!match) {
        continue
      }
      const amount = match[1]
      if (!amount) {
        continue
      }
      total += Number(amount.replace(/,/g, ""))
      break
    }
  }
  return total
}

export default function DashboardPage() {
  const [dashboardState, setDashboardState] = useState<DashboardState>(defaultState)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isCancelled = false

    async function loadDashboard() {
      setIsLoading(true)
      setErrorMessage(null)

      try {
        const filesResponse = await listFiles()
        const analysesByFile = await Promise.all(
          filesResponse.files.map(async (file) => ({
            file,
            analyses: await listAnalysesForFile(file.file_id),
          }))
        )

        const allAnalyses = analysesByFile
          .flatMap(({ file, analyses }) =>
            analyses.map((analysis) => ({
              analysis,
              fileName: file.original_filename || file.filename,
              fileDate: file.uploaded_at,
            }))
          )
          .sort(
            (left, right) =>
              new Date(getAnalysisDate(right.analysis, right.fileDate)).getTime() -
              new Date(getAnalysisDate(left.analysis, left.fileDate)).getTime()
          )

        const completedAnalyses = allAnalyses.filter(({ analysis }) => analysis.status === "completed")
        const totalSavings = completedAnalyses.reduce(
          (sum, { analysis }) => sum + parseSavings(analysis.findings),
          0
        )
        const securityScores = completedAnalyses
          .map(({ analysis }) => analysis.security_score)
          .filter((score): score is number => typeof score === "number")
        const averageSecurityScore = securityScores.length > 0
          ? `${Math.round(securityScores.reduce((sum, score) => sum + score, 0) / securityScores.length)}%`
          : "N/A"

        const stats: DashboardStat[] = [
          { label: "Files Uploaded", value: filesResponse.total, icon: "FileText" },
          { label: "Analyses Run", value: allAnalyses.length, icon: "AlertCircle" },
          { label: "Estimated Savings", value: `$${totalSavings.toLocaleString()}`, icon: "DollarSign" },
          { label: "Avg Security Score", value: averageSecurityScore, icon: "Shield" },
        ]

        const recentAnalyses: DashboardAnalysis[] = allAnalyses.slice(0, 6).map(({ analysis, fileName, fileDate }) => ({
          id: analysis.analysis_id,
          name: fileName,
          date: getAnalysisDate(analysis, fileDate),
          status: analysis.status,
          issuesFound: analysis.findings.length,
          severity: highestSeverity(analysis.findings.map((finding) => ({ ...finding, severity: getSeverity(finding) } as BackendFinding))),
        }))

        if (!isCancelled) {
          setDashboardState({ stats, recentAnalyses })
        }
      } catch (error) {
        if (!isCancelled) {
          setErrorMessage(error instanceof Error ? error.message : "Failed to load dashboard data.")
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false)
        }
      }
    }

    void loadDashboard()

    return () => {
      isCancelled = true
    }
  }, [])

  return (
    <div className="flex">
      <Sidebar />
      <main className="min-h-screen flex-1 bg-background">
        <div className="p-8">
          <div className="mb-8 flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
            <div>
            <h1 className="mb-2 text-3xl font-bold text-foreground">
              Dashboard
            </h1>
            <p className="text-muted-foreground">
              Overview of your uploaded files and recent analysis activity
            </p>
            </div>

            <Alert className="surface-panel max-w-xl rounded-[1.75rem] border-primary/15 bg-primary/5">
              <Sparkles className="h-4 w-4" />
              <AlertTitle>Operator view enabled</AlertTitle>
              <AlertDescription>
                The dashboard now uses live backend data and richer shadcn-style status panels instead of mock placeholders.
              </AlertDescription>
            </Alert>
          </div>

          {errorMessage && (
            <Alert variant="destructive" className="mb-6 rounded-[1.75rem]">
              <ShieldAlert className="h-4 w-4" />
              <AlertTitle>Backend data unavailable</AlertTitle>
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          )}

          {/* Stats Cards */}
          <div className="mb-8 grid gap-6 md:grid-cols-4">
            {isLoading
              ? Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="surface-panel rounded-[1.75rem] p-6">
                    <div className="flex items-start justify-between">
                      <div className="space-y-3">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-9 w-20" />
                      </div>
                      <Skeleton className="h-10 w-10 rounded-2xl" />
                    </div>
                  </div>
                ))
              : dashboardState.stats.map((stat) => (
                  <StatsCard
                    key={stat.label}
                    label={stat.label}
                    value={stat.value}
                    icon={stat.icon}
                  />
                ))}
          </div>

          <div className="mb-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
            <div className="surface-panel rounded-[1.75rem] p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Review Cadence</p>
                  <h2 className="mt-2 text-xl font-semibold text-foreground">Current activity window</h2>
                </div>
                <Radar className="h-5 w-5 text-primary" />
              </div>
              <p className="mt-3 max-w-2xl text-sm text-muted-foreground">
                Use the live dashboard as a quick operator surface: upload files, monitor analysis volume, and move directly into results without bouncing between mock summaries and raw backend output.
              </p>
            </div>

            <div className="flex items-center justify-between rounded-[1.75rem] border border-border/70 bg-card/75 p-6 shadow-sm backdrop-blur-sm">
              <div>
                <p className="text-sm font-medium text-foreground">Need a fresh report?</p>
                <p className="mt-1 text-sm text-muted-foreground">Upload a new infrastructure file and generate another run.</p>
              </div>
              <Link href="/upload">
                <Button size="lg" className="gap-2 rounded-full">
                  <Plus className="h-5 w-5" />
                  New Analysis
                </Button>
              </Link>
            </div>
          </div>

          {/* Quick Actions */}
          {/* Recent Analyses */}
          <RecentAnalyses analyses={dashboardState.recentAnalyses} />
        </div>
      </main>
    </div>
  )
}
