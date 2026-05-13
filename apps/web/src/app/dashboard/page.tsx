"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Sidebar } from "@/components/layout/sidebar"
import { Button } from "@/components/ui/button"
import { StatsCard } from "@/components/dashboard/stats-card"
import { RecentAnalyses } from "@/components/dashboard/recent-analyses"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Plus, Radar, Sparkles, ShieldAlert, GitBranch, Loader2, ShieldCheck, RefreshCcw } from "lucide-react"
import Link from "next/link"
import {
  listAnalysesForFile,
  listFiles,
  type BackendAnalysisResult,
  type BackendFinding,
} from "@/lib/backend-api"
import {
  disconnectGitHub,
  getGitHubConnection,
  listGitHubRepos,
  listRepoScans,
  startRepoScan,
  type GitHubConnectionResponse,
  type GitHubRepository,
  type RepoScanResult,
} from "@/lib/github-api"

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

interface GitHubPanelState {
  connection: GitHubConnectionResponse | null
  repositories: GitHubRepository[]
  scans: RepoScanResult[]
  selectedRepository: string
  manualRepository: string
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

const defaultGitHubState: GitHubPanelState = {
  connection: null,
  repositories: [],
  scans: [],
  selectedRepository: "",
  manualRepository: "octocat/Hello-World",
}

const repoScanScanners = ["checkov", "trivy", "gitleaks", "semgrep", "prowler"]

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

function repoScanSeverityClass(severity: string) {
  switch (severity) {
    case "critical":
      return "bg-rose-500/10 text-rose-700 dark:text-rose-300"
    case "high":
      return "bg-orange-500/10 text-orange-700 dark:text-orange-300"
    case "medium":
      return "bg-amber-500/10 text-amber-700 dark:text-amber-300"
    case "low":
      return "bg-sky-500/10 text-sky-700 dark:text-sky-300"
    default:
      return "bg-slate-500/10 text-slate-700 dark:text-slate-300"
  }
}

function repoScanStatusClass(status: string) {
  switch (status) {
    case "completed":
      return "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
    case "failed":
      return "bg-rose-500/10 text-rose-700 dark:text-rose-300"
    case "running":
      return "bg-amber-500/10 text-amber-700 dark:text-amber-300"
    default:
      return "bg-slate-500/10 text-slate-700 dark:text-slate-300"
  }
}

export default function DashboardPage() {
  const searchParams = useSearchParams()
  const [dashboardState, setDashboardState] = useState<DashboardState>(defaultState)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [hasMounted, setHasMounted] = useState(false)
  const [githubState, setGitHubState] = useState<GitHubPanelState>(defaultGitHubState)
  const [githubErrorMessage, setGitHubErrorMessage] = useState<string | null>(null)
  const [isGitHubLoading, setIsGitHubLoading] = useState(true)
  const [isRepoScanning, setIsRepoScanning] = useState(false)
  const authMode = searchParams.get("mode") === "register" ? "register" : "signin"
  const localAuthActive = searchParams.get("auth") === "local"

  useEffect(() => {
    setHasMounted(true)
  }, [])

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

  useEffect(() => {
    let isCancelled = false

    async function loadGitHubPanel() {
      setIsGitHubLoading(true)
      setGitHubErrorMessage(null)

      try {
        const connection = await getGitHubConnection()
        if (!connection.connected) {
          if (!isCancelled) {
            setGitHubState(defaultGitHubState)
          }
          return
        }

        const [repositories, scans] = await Promise.all([listGitHubRepos(), listRepoScans()])

        if (!isCancelled) {
          setGitHubState((current) => ({
            connection,
            repositories,
            scans,
            selectedRepository: current.selectedRepository || repositories[0]?.fullName || "",
            manualRepository: current.manualRepository,
          }))
        }
      } catch (error) {
        if (!isCancelled) {
          setGitHubErrorMessage(error instanceof Error ? error.message : "Failed to load GitHub scanning workspace.")
        }
      } finally {
        if (!isCancelled) {
          setIsGitHubLoading(false)
        }
      }
    }

    void loadGitHubPanel()

    return () => {
      isCancelled = true
    }
  }, [])

  async function handleDisconnectGitHub() {
    setGitHubErrorMessage(null)

    try {
      await disconnectGitHub()
      setGitHubState(defaultGitHubState)
    } catch (error) {
      setGitHubErrorMessage(error instanceof Error ? error.message : "Failed to disconnect GitHub.")
    }
  }

  async function handleStartRepoScan() {
    const repository = githubState.connection?.connected
      ? githubState.selectedRepository
      : githubState.manualRepository.trim()

    if (!repository) {
      setGitHubErrorMessage("Choose a repository before starting a scan.")
      return
    }

    setIsRepoScanning(true)
    setGitHubErrorMessage(null)

    try {
      const scan = await startRepoScan(repository, undefined, repoScanScanners)
      setGitHubState((current) => ({
        ...current,
        scans: [scan, ...current.scans],
      }))
    } catch (error) {
      setGitHubErrorMessage(error instanceof Error ? error.message : "Failed to start a repository scan.")
    } finally {
      setIsRepoScanning(false)
    }
  }

  const latestRepoScan = githubState.scans[0] ?? null
  const groupedRepoFindings = latestRepoScan?.findings.reduce<Record<string, typeof latestRepoScan.findings>>((groups, finding) => {
    const source = typeof latestRepoScan.scanners.find((scanner) => finding.id.startsWith(`${scanner.scanner}:`))?.scanner === "string"
      ? latestRepoScan.scanners.find((scanner) => finding.id.startsWith(`${scanner.scanner}:`))?.scanner || "unknown"
      : "unknown"
    groups[source] = [...(groups[source] || []), finding]
    return groups
  }, {}) ?? {}

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

          {hasMounted && localAuthActive && (
            <Alert className="mb-6 rounded-[1.75rem] border-primary/15 bg-primary/5">
              <Sparkles className="h-4 w-4" />
              <AlertTitle>{authMode === "register" ? "Local account created" : "Local sign-in active"}</AlertTitle>
              <AlertDescription>
                {authMode === "register"
                  ? "A lightweight local session is active for this environment. You can continue through uploads and dashboard flows while the full identity backend is completed."
                  : "A lightweight local session is active for this environment. You can continue through uploads and dashboard flows while the full identity backend is completed."}
              </AlertDescription>
              <div className="mt-4">
                <Button asChild variant="outline" className="rounded-xl border-border/80 bg-background/70">
                  <Link href="/api/auth/logout">Sign Out</Link>
                </Button>
              </div>
            </Alert>
          )}

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

          <div className="mb-8 surface-panel rounded-[1.75rem] p-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="max-w-2xl">
                <div className="flex items-center gap-3">
                  <GitBranch className="h-5 w-5 text-primary" />
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">GitHub Security Workspace</p>
                </div>
                <h2 className="mt-3 text-2xl font-semibold text-foreground">Connect a repository and run multi-scanner security checks</h2>
                <p className="mt-3 text-sm leading-7 text-muted-foreground">
                  Start with GitHub OAuth for private repositories, or enter a public repository directly and run a manual scan that fans out to Checkov, Trivy, Gitleaks, Semgrep, and the planned Prowler phase marker.
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                {githubState.connection?.connected ? (
                  <>
                    <Button
                      variant="outline"
                      className="rounded-full border-border/80 bg-background/75"
                      onClick={handleDisconnectGitHub}
                    >
                      Disconnect GitHub
                    </Button>
                    <Button
                      className="gap-2 rounded-full"
                      onClick={handleStartRepoScan}
                      disabled={isRepoScanning || !githubState.selectedRepository}
                    >
                      {isRepoScanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                      Scan Repository
                    </Button>
                  </>
                ) : (
                  <div className="flex flex-wrap gap-3">
                    <Button asChild className="gap-2 rounded-full">
                      <Link href="/api/auth/github?mode=signin">
                        <GitBranch className="h-4 w-4" />
                        Connect GitHub
                      </Link>
                    </Button>
                    <Button
                      className="gap-2 rounded-full"
                      onClick={handleStartRepoScan}
                      disabled={isRepoScanning || !githubState.manualRepository.trim()}
                    >
                      {isRepoScanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                      Scan Public Repo
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {githubErrorMessage && (
              <Alert variant="destructive" className="mt-6 rounded-[1.5rem]">
                <ShieldAlert className="h-4 w-4" />
                <AlertTitle>GitHub scanning unavailable</AlertTitle>
                <AlertDescription>{githubErrorMessage}</AlertDescription>
              </Alert>
            )}

            <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
              <div className="rounded-[1.5rem] border border-border/70 bg-card/75 p-5 shadow-sm backdrop-blur-sm">
                {isGitHubLoading ? (
                  <div className="space-y-4">
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-20 w-full" />
                  </div>
                ) : githubState.connection?.connected ? (
                  <div className="space-y-5">
                    <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                      <span className="rounded-full border border-border/70 bg-background/80 px-3 py-1 text-foreground">
                        Connected as @{githubState.connection.login}
                      </span>
                      <span>50 most recently updated repositories are available for selection.</span>
                    </div>

                    <label className="block space-y-2">
                      <span className="text-sm font-medium text-foreground">Repository</span>
                      <select
                        className="w-full rounded-2xl border border-border/70 bg-background/80 px-4 py-3 text-sm text-foreground outline-none"
                        value={githubState.selectedRepository}
                        onChange={(event) =>
                          setGitHubState((current) => ({
                            ...current,
                            selectedRepository: event.target.value,
                          }))
                        }
                      >
                        {githubState.repositories.length === 0 ? (
                          <option value="">No repositories returned from GitHub</option>
                        ) : (
                          githubState.repositories.map((repository) => (
                            <option key={repository.id} value={repository.fullName}>
                              {repository.fullName} ({repository.defaultBranch})
                            </option>
                          ))
                        )}
                      </select>
                    </label>

                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                      {repoScanScanners.map((scanner) => (
                        <div key={scanner} className="rounded-2xl border border-border/70 bg-background/70 px-4 py-3 text-sm text-foreground">
                          <p className="font-medium uppercase tracking-[0.18em] text-muted-foreground">{scanner}</p>
                          <p className="mt-2 text-sm leading-6 text-muted-foreground">
                            {scanner === "prowler"
                              ? "Phase 2 placeholder for AWS account posture checks."
                              : "Enabled for repository-content scanning in this MVP flow."}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="rounded-[1.25rem] border border-dashed border-border/70 bg-background/60 p-6 text-sm leading-7 text-muted-foreground">
                      GitHub OAuth is still the right path for private repos and repository listing. For immediate validation in this environment, you can run a public repository scan without OAuth.
                    </div>
                    <label className="block space-y-2">
                      <span className="text-sm font-medium text-foreground">Public repository</span>
                      <input
                        className="w-full rounded-2xl border border-border/70 bg-background/80 px-4 py-3 text-sm text-foreground outline-none"
                        value={githubState.manualRepository}
                        onChange={(event) =>
                          setGitHubState((current) => ({
                            ...current,
                            manualRepository: event.target.value,
                          }))
                        }
                        placeholder="owner/name"
                      />
                    </label>
                  </div>
                )}
              </div>

              <div className="rounded-[1.5rem] border border-border/70 bg-card/75 p-5 shadow-sm backdrop-blur-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Latest repository scan</p>
                    <h3 className="mt-2 text-xl font-semibold text-foreground">Scanner execution summary</h3>
                  </div>
                  <RefreshCcw className="h-4 w-4 text-primary" />
                </div>

                {latestRepoScan ? (
                  <div className="mt-5 space-y-4 text-sm">
                    <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                      <div className="flex flex-wrap items-center gap-3">
                        <p className="font-medium text-foreground">{latestRepoScan.repository}</p>
                        <span className={`rounded-full px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] ${repoScanStatusClass(latestRepoScan.status)}`}>
                          {latestRepoScan.status}
                        </span>
                        <span className="rounded-full bg-background px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                          {latestRepoScan.metadata?.used_github_token ? "OAuth token" : "Public clone"}
                        </span>
                      </div>
                      <p className="mt-3 text-muted-foreground">
                        Findings: {latestRepoScan.summary.total} total, {latestRepoScan.summary.critical} critical, {latestRepoScan.summary.high} high
                      </p>
                      {latestRepoScan.error_message && (
                        <p className="mt-3 text-rose-600 dark:text-rose-300">{latestRepoScan.error_message}</p>
                      )}
                    </div>

                    <div className="space-y-3">
                      {latestRepoScan.scanners.map((scanner) => (
                        <div key={`${latestRepoScan.scan_id}-${scanner.scanner}`} className="rounded-2xl border border-border/70 bg-background/70 p-4">
                          <div className="flex items-center justify-between gap-3">
                            <div className="flex items-center gap-3">
                              <p className="font-medium text-foreground">{scanner.scanner}</p>
                              <span className={`rounded-full px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] ${repoScanStatusClass(scanner.status)}`}>
                                {scanner.status}
                              </span>
                            </div>
                            <span className={`rounded-full px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] ${repoScanSeverityClass(scanner.summary.critical > 0 ? "critical" : scanner.summary.high > 0 ? "high" : scanner.summary.medium > 0 ? "medium" : scanner.summary.low > 0 ? "low" : "info")}`}>
                              {scanner.summary.total} findings
                            </span>
                          </div>
                          <p className="mt-2 text-muted-foreground">
                            {scanner.summary.total} findings surfaced across this scanner.
                          </p>
                          {scanner.error_message && (
                            <p className="mt-2 text-rose-600 dark:text-rose-300">{scanner.error_message}</p>
                          )}
                        </div>
                      ))}
                    </div>

                    {Object.keys(groupedRepoFindings).length > 0 && (
                      <div className="space-y-3">
                        <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Grouped findings preview</p>
                        {Object.entries(groupedRepoFindings).map(([source, findings]) => (
                          <div key={source} className="rounded-2xl border border-border/70 bg-background/70 p-4">
                            <div className="flex items-center justify-between gap-3">
                              <p className="font-medium text-foreground">{source}</p>
                              <span className="rounded-full bg-background px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
                                {findings.length} item{findings.length === 1 ? "" : "s"}
                              </span>
                            </div>
                            <div className="mt-3 space-y-2">
                              {findings.slice(0, 4).map((finding) => (
                                <div key={finding.id} className="rounded-xl border border-border/60 bg-card/70 px-3 py-3">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className={`rounded-full px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.18em] ${repoScanSeverityClass(finding.severity)}`}>
                                      {finding.severity}
                                    </span>
                                    <span className="text-sm font-medium text-foreground">{finding.title}</span>
                                  </div>
                                  {finding.resource && <p className="mt-2 text-xs text-muted-foreground">{finding.resource}</p>}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="mt-5 rounded-[1.25rem] border border-dashed border-border/70 bg-background/60 p-5 text-sm leading-7 text-muted-foreground">
                    No repository scans have been started yet. Connect GitHub, choose a repository, and run the first security pass.
                  </div>
                )}
              </div>
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
