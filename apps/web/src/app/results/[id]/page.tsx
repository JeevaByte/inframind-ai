"use client"

import { useEffect, useMemo, useState } from "react"
import { useParams, useSearchParams } from "next/navigation"
import { jsPDF } from "jspdf"
import { Sidebar } from "@/components/layout/sidebar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { SummaryChart } from "@/components/results/summary-chart"
import { IssueCard } from "@/components/results/issue-card"
import { Download, Share2 } from "lucide-react"
import { getFileMetadata, type BackendAnalysisResult, type BackendFinding } from "@/lib/backend-api"

async function fetchAnalysisResult(analysisId: string): Promise<BackendAnalysisResult> {
  const res = await fetch(`/api/analysis/${analysisId}`, { cache: "no-store" })
  if (!res.ok) {
    let message = "Failed to load analysis result"
    try {
      const errPayload = (await res.json()) as { error?: string }
      if (errPayload.error) message = errPayload.error
    } catch {
      // non-JSON error body; keep default message
    }
    throw new Error(message)
  }
  return res.json() as Promise<BackendAnalysisResult>
}

interface IssueViewModel {
  id: string
  title: string
  description: string
  severity: "critical" | "high" | "medium" | "low"
  category: "security" | "reliability" | "cost" | "compliance"
  recommendation: string
  estimatedImpact: string
}

interface ResultsState {
  analyses: BackendAnalysisResult[]
  issues: IssueViewModel[]
  summary: {
    critical: number
    high: number
    medium: number
    low: number
    info: number
  }
  averageScore: number | null
  fileNames: string[]
  categorySummary: {
    security: number
    reliability: number
    cost: number
    compliance: number
  }
  scoreBreakdown: {
    security: number | null
    reliability: number | null
    cost: number | null
    compliance: number | null
  }
  deploymentReadiness: string | null
  architectureSummary: string | null
  topRecommendations: string[]
  perFileSummary: Array<{
    fileId: string
    fileName: string
    score: number | null
    totalIssues: number
    security: number
    reliability: number
    cost: number
    compliance: number
    critical: number
    high: number
    medium: number
    low: number
  }>
}

function findingToCategory(finding: BackendFinding) {
  if (finding.category) {
    return finding.category
  }
  if (finding.rule_id.startsWith("SEC")) {
    return "security"
  }
  if (finding.rule_id.startsWith("REL")) {
    return "reliability"
  }
  if (finding.rule_id.startsWith("COST")) {
    return "cost"
  }
  return "compliance"
}

export default function ResultsPage() {
  const params = useParams<{ id: string }>()
  const searchParams = useSearchParams()
  const [resultsState, setResultsState] = useState<ResultsState | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const analysisIds = useMemo(() => {
    const fromQuery = (searchParams.get("analysisIds") || "")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean)

    const ids = [params.id, ...fromQuery].filter(Boolean)
    return [...new Set(ids)]
  }, [params.id, searchParams])

  useEffect(() => {
    let isCancelled = false

    async function loadResults() {
      setIsLoading(true)
      setErrorMessage(null)

      try {
        const analyses = await Promise.all(analysisIds.map((analysisId) => fetchAnalysisResult(analysisId)))
        const uniqueFileIds = [...new Set(analyses.map((analysis) => analysis.file_id))]
        const fileMetadata = await Promise.all(uniqueFileIds.map((fileId) => getFileMetadata(fileId)))
        const fileNameById = new Map(fileMetadata.map((file) => [file.file_id, file.original_filename]))

        const summary = { critical: 0, high: 0, medium: 0, low: 0, info: 0 }
        const categorySummary = { security: 0, reliability: 0, cost: 0, compliance: 0 }
        const issues = analyses.flatMap((analysis) =>
          analysis.findings.map((finding) => {
            summary[finding.severity] += 1
            const category = findingToCategory(finding)
            categorySummary[category] += 1

            return {
              id: `${analysis.analysis_id}-${finding.id}`,
              title: finding.title,
              description: finding.line_number
                ? `${finding.description} (line ${finding.line_number})`
                : finding.description,
              severity: finding.severity === "info" ? "low" : finding.severity,
              category,
              recommendation: finding.recommendation,
              estimatedImpact: typeof finding.metadata["estimated_impact"] === "string"
                ? finding.metadata["estimated_impact"]
                : typeof finding.metadata["estimated_cost"] === "string"
                  ? finding.metadata["estimated_cost"]
                  : "Operational impact not provided",
            }
          })
        )

        const perFileSummary = analyses.map((analysis) => {
          const fileSummary = {
            fileId: analysis.file_id,
            fileName: fileNameById.get(analysis.file_id) || analysis.file_id,
            score: typeof analysis.score === "number" ? analysis.score : null,
            totalIssues: analysis.findings.length,
            security: 0,
            reliability: 0,
            cost: 0,
            compliance: 0,
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
          }

          analysis.findings.forEach((finding) => {
            const category = findingToCategory(finding)
            fileSummary[category] += 1

            if (finding.severity === "info") {
              fileSummary.low += 1
              return
            }

            fileSummary[finding.severity] += 1
          })

          return fileSummary
        })

        const scoredAnalyses = analyses.filter((analysis) => typeof analysis.score === "number")
        const averageScore = scoredAnalyses.length > 0
          ? Number(
              (
                scoredAnalyses.reduce((total, analysis) => total + (analysis.score || 0), 0) /
                scoredAnalyses.length
              ).toFixed(1)
            )
          : null

        if (!isCancelled) {
          setResultsState({
            analyses,
            issues,
            summary,
            averageScore,
            categorySummary,
            scoreBreakdown: {
              security: analyses[0]?.security_score ?? null,
              reliability: analyses[0]?.reliability_score ?? null,
              cost: analyses[0]?.cost_optimization_score ?? null,
              compliance: analyses[0]?.compliance_score ?? null,
            },
            deploymentReadiness: analyses[0]?.deployment_readiness ?? null,
            architectureSummary: analyses[0]?.architecture_summary ?? null,
            topRecommendations: analyses.flatMap((analysis) => analysis.top_recommendations || []).slice(0, 5),
            perFileSummary,
            fileNames: analyses.map((analysis) => fileNameById.get(analysis.file_id) || analysis.file_id),
          })
        }
      } catch (error) {
        if (!isCancelled) {
          setErrorMessage(error instanceof Error ? error.message : "Failed to load analysis results.")
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false)
        }
      }
    }

    void loadResults()

    return () => {
      isCancelled = true
    }
  }, [analysisIds])

  const handleShare = async () => {
    const shareUrl = window.location.href

    try {
      if (navigator.share) {
        await navigator.share({
          title: "infralint Analysis Results",
          text: "Review the infrastructure analysis results.",
          url: shareUrl,
        })
        setActionMessage("Share sheet opened.")
        return
      }

      await navigator.clipboard.writeText(shareUrl)
      setActionMessage("Results link copied to clipboard.")
    } catch (error) {
      setActionMessage(
        error instanceof Error ? error.message : "Unable to share the current results."
      )
    }
  }

  const handleExportPdf = () => {
    if (!resultsState) {
      return
    }

    const document = new jsPDF({ unit: "pt", format: "a4" })
    const pageWidth = document.internal.pageSize.getWidth()
    const pageHeight = document.internal.pageSize.getHeight()
    const margin = 40
    const lineHeight = 16
    let currentY = margin

    const lines = [
      "infralint Analysis Report",
      "",
      `Files: ${resultsState.fileNames.join(", ")}`,
      `Average score: ${resultsState.averageScore !== null ? `${resultsState.averageScore}%` : "N/A"}`,
      `Total issues: ${totalIssues}`,
      "",
      "Severity Summary",
      `- Critical: ${resultsState.summary.critical}`,
      `- High: ${resultsState.summary.high}`,
      `- Medium: ${resultsState.summary.medium}`,
      `- Low: ${resultsState.summary.low}`,
      "",
      "Category Summary",
      `- Security: ${resultsState.categorySummary.security}`,
      `- Cost: ${resultsState.categorySummary.cost}`,
      `- Compliance: ${resultsState.categorySummary.compliance}`,
      "",
      "Per-file Summary",
      ...resultsState.perFileSummary.flatMap((file) => [
        `${file.fileName}: ${file.totalIssues} issues, score ${file.score !== null ? `${file.score}%` : "N/A"}`,
        `  Security ${file.security} | Cost ${file.cost} | Compliance ${file.compliance}`,
        `  Critical ${file.critical} | High ${file.high} | Medium ${file.medium} | Low ${file.low}`,
      ]),
      "",
      "Findings",
      ...resultsState.issues.flatMap((issue, index) => [
        `${index + 1}. [${issue.severity.toUpperCase()}] ${issue.title}`,
        `   Category: ${issue.category}`,
        `   ${issue.description}`,
        `   Recommendation: ${issue.recommendation}`,
        `   Estimated impact: ${issue.estimatedImpact}`,
      ]),
    ]

    document.setFont("helvetica", "normal")
    document.setFontSize(11)

    lines.forEach((line, index) => {
      if (index === 0) {
        document.setFont("helvetica", "bold")
        document.setFontSize(16)
      } else {
        document.setFont("helvetica", "normal")
        document.setFontSize(11)
      }

      const wrapped = document.splitTextToSize(line || " ", pageWidth - margin * 2)
      wrapped.forEach((wrappedLine: string) => {
        if (currentY > pageHeight - margin) {
          document.addPage()
          currentY = margin
        }

        document.text(wrappedLine, margin, currentY)
        currentY += lineHeight
      })

      if (line === "") {
        currentY += 6
      }
    })

    document.save(`infralint-analysis-${analysisIds[0] || "report"}.pdf`)
    setActionMessage("Analysis report downloaded.")
  }

  const filteredIssues = (category: "security" | "reliability" | "cost" | "compliance") =>
    resultsState?.issues.filter((issue) => issue.category === category) || []

  const totalIssues = resultsState?.issues.length || 0
  const statusText = resultsState?.analyses.every((analysis) => analysis.status === "completed")
    ? "Completed"
    : "In progress"

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 bg-slate-50 dark:bg-slate-900 min-h-screen">
        <div className="p-8">
          {isLoading ? (
            <div className="rounded-lg border border-slate-200 bg-white p-6 text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
              AI is loading the infrastructure review...
            </div>
          ) : errorMessage ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">
              {errorMessage}
            </div>
          ) : resultsState ? (
            <>
          <div className="mb-8 flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                AI Infrastructure Review
              </h1>
              <p className="text-slate-600 dark:text-slate-400">
                {resultsState.fileNames.join(", ")} • {statusText}
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" className="gap-2" onClick={handleShare}>
                <Share2 className="h-4 w-4" />
                Share
              </Button>
              <Button className="gap-2" onClick={handleExportPdf}>
                <Download className="h-4 w-4" />
                Export PDF
              </Button>
            </div>
          </div>

          {actionMessage && (
            <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700 dark:border-blue-900 dark:bg-blue-950/30 dark:text-blue-300">
              {actionMessage}
            </div>
          )}

          {/* Summary Overview */}
          <div className="grid lg:grid-cols-3 gap-8 mb-8">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>AI Findings Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <SummaryChart
                    critical={resultsState.summary.critical}
                    high={resultsState.summary.high}
                    medium={resultsState.summary.medium}
                    low={resultsState.summary.low}
                  />
                </CardContent>
              </Card>
            </div>

            {/* Quick Stats */}
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Total Issues</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">
                    {totalIssues}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Deployment Readiness</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-blue-600">
                    {resultsState.deploymentReadiness || "Needs review"}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Average Score</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-green-600">
                    {resultsState.averageScore !== null ? `${resultsState.averageScore}%` : "N/A"}
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>

          <div className="grid gap-8 lg:grid-cols-3 mb-8">
            <Card>
              <CardHeader>
                <CardTitle>Issue Categories</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">Security</span>
                  <span className="font-semibold text-slate-900 dark:text-white">{resultsState.categorySummary.security}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">Reliability</span>
                  <span className="font-semibold text-slate-900 dark:text-white">{resultsState.categorySummary.reliability}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">Cost</span>
                  <span className="font-semibold text-slate-900 dark:text-white">{resultsState.categorySummary.cost}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">Compliance</span>
                  <span className="font-semibold text-slate-900 dark:text-white">{resultsState.categorySummary.compliance}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>AI Review Highlights</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
                  <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Architecture Summary</p>
                  <p className="mt-2 text-sm leading-7 text-slate-700 dark:text-slate-300">
                    {resultsState.architectureSummary || "Architecture summary unavailable."}
                  </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
                    <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Score Breakdown</p>
                    <div className="mt-3 space-y-2 text-sm text-slate-700 dark:text-slate-300">
                      <div className="flex items-center justify-between"><span>Security</span><span>{resultsState.scoreBreakdown.security !== null ? `${resultsState.scoreBreakdown.security}%` : "N/A"}</span></div>
                      <div className="flex items-center justify-between"><span>Reliability</span><span>{resultsState.scoreBreakdown.reliability !== null ? `${resultsState.scoreBreakdown.reliability}%` : "N/A"}</span></div>
                      <div className="flex items-center justify-between"><span>Cost</span><span>{resultsState.scoreBreakdown.cost !== null ? `${resultsState.scoreBreakdown.cost}%` : "N/A"}</span></div>
                      <div className="flex items-center justify-between"><span>Compliance</span><span>{resultsState.scoreBreakdown.compliance !== null ? `${resultsState.scoreBreakdown.compliance}%` : "N/A"}</span></div>
                    </div>
                  </div>

                  <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
                    <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Top Recommendations</p>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700 dark:text-slate-300">
                      {resultsState.topRecommendations.length > 0 ? resultsState.topRecommendations.map((recommendation) => (
                        <li key={recommendation}>• {recommendation}</li>
                      )) : <li>No AI recommendations available.</li>}
                    </ul>
                  </div>
                </div>

                <div className="space-y-4">
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">Per-file Issue Summary</p>
                  {resultsState.perFileSummary.map((file) => (
                  <div key={file.fileId} className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
                    <div className="mb-3 flex items-start justify-between gap-4">
                      <div>
                        <p className="font-semibold text-slate-900 dark:text-white">{file.fileName}</p>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          {file.totalIssues} issue{file.totalIssues === 1 ? "" : "s"} detected
                        </p>
                      </div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">
                        Score: {file.score !== null ? `${file.score}%` : "N/A"}
                      </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="rounded-md bg-slate-50 p-3 dark:bg-slate-900">
                        <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Categories</p>
                        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
                          Security {file.security} | Reliability {file.reliability} | Cost {file.cost} | Compliance {file.compliance}
                        </p>
                      </div>
                      <div className="rounded-md bg-slate-50 p-3 dark:bg-slate-900 sm:col-span-2">
                        <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Severity</p>
                        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
                          Critical {file.critical} | High {file.high} | Medium {file.medium} | Low {file.low}
                        </p>
                      </div>
                    </div>
                  </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Issues */}
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="security">Security</TabsTrigger>
              <TabsTrigger value="reliability">Reliability</TabsTrigger>
              <TabsTrigger value="cost">Cost</TabsTrigger>
              <TabsTrigger value="compliance">Compliance</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  All Issues ({totalIssues})
                </h3>
                {resultsState.issues.map((issue) => (
                  <IssueCard key={issue.id} issue={issue} />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="security">
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Security Issues
                </h3>
                {filteredIssues("security").map((issue) => (
                  <IssueCard key={issue.id} issue={issue} />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="reliability">
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Reliability Issues
                </h3>
                {filteredIssues("reliability").map((issue) => (
                  <IssueCard key={issue.id} issue={issue} />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="cost">
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Cost Optimization
                </h3>
                {filteredIssues("cost").map((issue) => (
                  <IssueCard key={issue.id} issue={issue} />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="compliance">
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Compliance Issues
                </h3>
                {filteredIssues("compliance").map((issue) => (
                  <IssueCard key={issue.id} issue={issue} />
                ))}
              </div>
            </TabsContent>
          </Tabs>
            </>
          ) : null}
        </div>
      </main>
    </div>
  )
}
