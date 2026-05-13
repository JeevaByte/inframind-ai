"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useParams, useSearchParams } from "next/navigation"
import { jsPDF } from "jspdf"
import { Download, FileText, Share2, ShieldAlert, Sparkles } from "lucide-react"

import { Sidebar } from "@/components/layout/sidebar"
import { SummaryChart } from "@/components/results/summary-chart"
import { IssueCard } from "@/components/results/issue-card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { BackendAnalysisResult, BackendFileMetadata, BackendFinding } from "@/lib/backend-api"
import { cn } from "@/lib/utils"

type SeverityLevel = "critical" | "high" | "medium" | "low"
type CategoryKey = "security" | "reliability" | "cost" | "compliance"

const severityRank: Record<SeverityLevel, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
}

const severityMeta: Record<SeverityLevel, { label: string; className: string; pdf: [number, number, number] }> = {
  critical: {
    label: "Critical",
    className: "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-200",
    pdf: [225, 29, 72],
  },
  high: {
    label: "High",
    className: "border-orange-500/20 bg-orange-500/10 text-orange-700 dark:text-orange-200",
    pdf: [249, 115, 22],
  },
  medium: {
    label: "Medium",
    className: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-200",
    pdf: [245, 158, 11],
  },
  low: {
    label: "Low",
    className: "border-sky-500/20 bg-sky-500/10 text-sky-700 dark:text-sky-200",
    pdf: [14, 165, 233],
  },
}

const categoryMeta: Record<CategoryKey, { label: string; barClass: string; badgeClass: string; pdf: [number, number, number] }> = {
  security: {
    label: "Security",
    barClass: "bg-rose-500",
    badgeClass: "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-200",
    pdf: [225, 29, 72],
  },
  reliability: {
    label: "Reliability",
    barClass: "bg-amber-500",
    badgeClass: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-200",
    pdf: [245, 158, 11],
  },
  cost: {
    label: "Cost",
    barClass: "bg-emerald-500",
    badgeClass: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
    pdf: [16, 185, 129],
  },
  compliance: {
    label: "Compliance",
    barClass: "bg-sky-500",
    badgeClass: "border-sky-500/20 bg-sky-500/10 text-sky-700 dark:text-sky-200",
    pdf: [14, 165, 233],
  },
}

interface AggregatedResultsPayload {
  analyses: BackendAnalysisResult[]
  fileMetadata: Record<string, BackendFileMetadata>
  failedAnalyses: Array<{ analysisId: string; error: string }>
  failedMetadata: Array<{ fileId: string; error: string }>
}

async function fetchAggregatedResults(analysisIds: string[], signal: AbortSignal): Promise<AggregatedResultsPayload> {
  const response = await fetch("/api/analysis/results", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
    signal,
    body: JSON.stringify({ analysisIds }),
  })

  const payload = (await response.json()) as AggregatedResultsPayload & { error?: string }

  if (!response.ok) {
    throw new Error(payload.error || "Failed to load aggregated analysis results.")
  }

  return payload
}

interface IssueViewModel {
  id: string
  title: string
  description: string
  severity: SeverityLevel
  category: CategoryKey
  recommendation: string
  estimatedImpact: string
  fileName: string
  ruleId: string
  resource?: string | null
  references: string[]
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
  generatedAt: string | null
  failedAnalyses: Array<{
    analysisId: string
    fileId: string
    fileName: string
    errorMessage: string
  }>
  perFileSummary: Array<{
    fileId: string
    fileName: string
    status: BackendAnalysisResult["status"]
    errorMessage: string | null
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

function averageMetric(
  analyses: BackendAnalysisResult[],
  metric: "security_score" | "reliability_score" | "cost_optimization_score" | "compliance_score"
) {
  const values = analyses
    .map((analysis) => analysis[metric])
    .filter((value): value is number => typeof value === "number")

  if (values.length === 0) {
    return null
  }

  return Number((values.reduce((total, value) => total + value, 0) / values.length).toFixed(1))
}

function formatTimestamp(value: string | null | undefined) {
  if (!value) {
    return "Pending"
  }

  try {
    return new Intl.DateTimeFormat("en", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value))
  } catch {
    return value
  }
}

function getRiskProfile(averageScore: number | null, summary?: ResultsState["summary"]) {
  const critical = summary?.critical || 0
  const high = summary?.high || 0

  if (critical > 0 || (averageScore !== null && averageScore < 55)) {
    return {
      label: "High Risk Exposure",
      description: "Critical weaknesses or low scoring controls are present. This report should be treated as an active remediation queue.",
      badgeClass: "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-200",
      pdf: [225, 29, 72] as [number, number, number],
    }
  }

  if (high > 0 || (averageScore !== null && averageScore < 72)) {
    return {
      label: "Elevated Risk",
      description: "The stack is deployable only with targeted follow-up. Prioritize the highest-severity findings before broad rollout.",
      badgeClass: "border-orange-500/20 bg-orange-500/10 text-orange-700 dark:text-orange-200",
      pdf: [249, 115, 22] as [number, number, number],
    }
  }

  if ((summary?.medium || 0) > 0 || (averageScore !== null && averageScore < 85)) {
    return {
      label: "Moderate Risk",
      description: "Core controls are in place, but the scorecard still shows meaningful clean-up opportunities before production hardening.",
      badgeClass: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-200",
      pdf: [245, 158, 11] as [number, number, number],
    }
  }

  return {
    label: "Strong Posture",
    description: "No major blockers surfaced in this report. The remaining findings are maintenance-level refinements.",
    badgeClass: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
    pdf: [16, 185, 129] as [number, number, number],
  }
}

function getReadinessProfile(readiness: string | null) {
  const normalized = (readiness || "needs review").toLowerCase()

  if (normalized.includes("ready")) {
    return {
      label: readiness || "Ready",
      className: "text-emerald-600 dark:text-emerald-300",
    }
  }

  if (normalized.includes("review") || normalized.includes("conditional")) {
    return {
      label: readiness || "Needs review",
      className: "text-amber-600 dark:text-amber-300",
    }
  }

  return {
    label: readiness || "Attention required",
    className: "text-rose-600 dark:text-rose-300",
  }
}

function getReportStatus(analyses: BackendAnalysisResult[]) {
  const hasInProgress = analyses.some((analysis) => analysis.status === "pending" || analysis.status === "running")
  if (hasInProgress) {
    return {
      label: "In progress",
      className: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-200",
      pdf: [245, 158, 11] as [number, number, number],
    }
  }

  const hasFailures = analyses.some((analysis) => analysis.status === "failed")
  if (hasFailures) {
    return {
      label: "Completed with failures",
      className: "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-200",
      pdf: [225, 29, 72] as [number, number, number],
    }
  }

  return {
    label: "Completed",
    className: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
    pdf: [16, 185, 129] as [number, number, number],
  }
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
  const [loadNotice, setLoadNotice] = useState<string | null>(null)
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
    const controller = new AbortController()

    async function loadResults() {
      setIsLoading(true)
      setErrorMessage(null)
      setLoadNotice(null)

      try {
        const payload = await fetchAggregatedResults(analysisIds, controller.signal)
        const analyses = payload.analyses
        const fileNameById = new Map(
          Object.entries(payload.fileMetadata).map(([fileId, file]) => [fileId, file.original_filename])
        )

        if (analyses.length === 0) {
          throw new Error("No analysis results were returned for this request.")
        }

        const summary = { critical: 0, high: 0, medium: 0, low: 0, info: 0 }
        const categorySummary = { security: 0, reliability: 0, cost: 0, compliance: 0 }
        const issues = analyses.flatMap((analysis) =>
          analysis.findings.map((finding) => {
            summary[finding.severity] += 1
            const category = findingToCategory(finding)
            categorySummary[category] += 1
            const fileName = fileNameById.get(analysis.file_id) || analysis.file_id

            return {
              id: `${analysis.analysis_id}-${finding.id}`,
              title: finding.title,
              description: finding.line_number
                ? `${finding.description} (line ${finding.line_number})`
                : finding.description,
              severity: finding.severity === "info" ? "low" : finding.severity,
              category,
              recommendation: finding.recommendation,
              fileName,
              ruleId: finding.rule_id,
              resource: finding.resource ?? null,
              references: finding.references || [],
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
            status: analysis.status,
            errorMessage: analysis.error_message ?? null,
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

        const failedAnalyses = analyses
          .filter((analysis) => analysis.status === "failed")
          .map((analysis) => ({
            analysisId: analysis.analysis_id,
            fileId: analysis.file_id,
            fileName: fileNameById.get(analysis.file_id) || analysis.file_id,
            errorMessage: analysis.error_message || "Analysis failed before findings could be produced.",
          }))

        setResultsState({
          analyses,
          issues,
          summary,
          averageScore,
          categorySummary,
          scoreBreakdown: {
            security: averageMetric(analyses, "security_score"),
            reliability: averageMetric(analyses, "reliability_score"),
            cost: averageMetric(analyses, "cost_optimization_score"),
            compliance: averageMetric(analyses, "compliance_score"),
          },
          deploymentReadiness: analyses.find((analysis) => analysis.deployment_readiness)?.deployment_readiness ?? null,
          architectureSummary: analyses.find((analysis) => analysis.architecture_summary)?.architecture_summary ?? null,
          topRecommendations: [...new Set(analyses.flatMap((analysis) => analysis.top_recommendations || []).filter(Boolean))].slice(0, 5),
          generatedAt:
            analyses
              .map((analysis) => analysis.completed_at || analysis.started_at)
              .filter((value): value is string => Boolean(value))
              .sort()
              .at(-1) ?? null,
                failedAnalyses,
          perFileSummary,
          fileNames: [...new Set(analyses.map((analysis) => fileNameById.get(analysis.file_id) || analysis.file_id))],
        })

        if (payload.failedAnalyses.length > 0 || payload.failedMetadata.length > 0) {
          const fragments: string[] = []

          if (payload.failedAnalyses.length > 0) {
            fragments.push(`${payload.failedAnalyses.length} analysis result${payload.failedAnalyses.length === 1 ? "" : "s"} could not be loaded`)
          }

          if (payload.failedMetadata.length > 0) {
            fragments.push(`${payload.failedMetadata.length} file name${payload.failedMetadata.length === 1 ? "" : "s"} could not be resolved`)
          }

          setLoadNotice(`${fragments.join(" and ")}. The scorecard below is based on the results that were returned successfully.`)
        }
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          return
        }

        setErrorMessage(error instanceof Error ? error.message : "Failed to load analysis results.")
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    void loadResults()

    return () => {
      controller.abort()
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
    let currentY = margin
    const reportDate = formatTimestamp(resultsState.generatedAt)
    const totalIssues = resultsState.issues.length
    const riskProfile = getRiskProfile(resultsState.averageScore, resultsState.summary)
    const severitySummary = [
      { label: "Critical", value: resultsState.summary.critical, color: severityMeta.critical.pdf },
      { label: "High", value: resultsState.summary.high, color: severityMeta.high.pdf },
      { label: "Medium", value: resultsState.summary.medium, color: severityMeta.medium.pdf },
      { label: "Low", value: resultsState.summary.low, color: severityMeta.low.pdf },
    ]
    const completedAnalyses = resultsState.analyses.filter((analysis) => analysis.status === "completed").length
    const failedAnalysesCount = resultsState.failedAnalyses.length
    const scoreCards = [
      { label: "Average score", value: resultsState.averageScore !== null ? `${resultsState.averageScore}%` : "N/A", detail: riskProfile.label, color: [37, 99, 235] as [number, number, number] },
      { label: "Deployment readiness", value: resultsState.deploymentReadiness || "Needs review", detail: "Release decision signal", color: [16, 185, 129] as [number, number, number] },
      { label: "Analysis coverage", value: `${completedAnalyses}/${resultsState.analyses.length}`, detail: failedAnalysesCount > 0 ? `${failedAnalysesCount} analysis failure${failedAnalysesCount === 1 ? "" : "s"}` : "All analyses completed successfully", color: [124, 58, 237] as [number, number, number] },
      { label: "Total findings", value: `${totalIssues}`, detail: `${resultsState.summary.critical + resultsState.summary.high} urgent items`, color: [225, 29, 72] as [number, number, number] },
    ]
    const scoreBreakdown = [
      { label: "Security", value: resultsState.scoreBreakdown.security },
      { label: "Reliability", value: resultsState.scoreBreakdown.reliability },
      { label: "Cost", value: resultsState.scoreBreakdown.cost },
      { label: "Compliance", value: resultsState.scoreBreakdown.compliance },
    ]
    const categoryBreakdown = [
      { label: "Security", value: resultsState.categorySummary.security, color: categoryMeta.security.pdf },
      { label: "Reliability", value: resultsState.categorySummary.reliability, color: categoryMeta.reliability.pdf },
      { label: "Cost", value: resultsState.categorySummary.cost, color: categoryMeta.cost.pdf },
      { label: "Compliance", value: resultsState.categorySummary.compliance, color: categoryMeta.compliance.pdf },
    ]
    const priorityFindings = [...resultsState.issues]
      .sort((left, right) => severityRank[right.severity] - severityRank[left.severity])
      .slice(0, 8)

    const ensureSpace = (height: number) => {
      if (currentY + height <= pageHeight - margin) {
        return
      }

      document.addPage()
      currentY = margin
    }

    const drawWrappedText = (
      text: string,
      x: number,
      y: number,
      maxWidth: number,
      options?: { fontSize?: number; color?: [number, number, number]; lineHeight?: number; fontStyle?: "normal" | "bold" }
    ) => {
      const fontSize = options?.fontSize ?? 11
      const lineHeight = options?.lineHeight ?? 16

      document.setFont("helvetica", options?.fontStyle || "normal")
      document.setFontSize(fontSize)
      if (options?.color) {
        document.setTextColor(...options.color)
      } else {
        document.setTextColor(30, 41, 59)
      }

      const lines = document.splitTextToSize(text || " ", maxWidth) as string[]
      ensureSpace(lines.length * lineHeight + 6)
      document.text(lines, x, y)
      currentY = y + lines.length * lineHeight
    }

    const drawSection = (title: string, description?: string) => {
      ensureSpace(48)
      document.setDrawColor(226, 232, 240)
      document.line(margin, currentY, pageWidth - margin, currentY)
      currentY += 18
      document.setFont("helvetica", "bold")
      document.setFontSize(15)
      document.setTextColor(15, 23, 42)
      document.text(title, margin, currentY)
      currentY += 14

      if (description) {
        drawWrappedText(description, margin, currentY, pageWidth - margin * 2, {
          fontSize: 10,
          color: [100, 116, 139],
          lineHeight: 14,
        })
        currentY += 6
      }
    }

    const drawMetricCard = (
      x: number,
      y: number,
      width: number,
      height: number,
      label: string,
      value: string,
      detail: string,
      color: [number, number, number]
    ) => {
      document.setFillColor(248, 250, 252)
      document.setDrawColor(226, 232, 240)
      document.rect(x, y, width, height, "FD")
      document.setFillColor(...color)
      document.rect(x, y, 5, height, "F")
      document.setFont("helvetica", "bold")
      document.setFontSize(10)
      document.setTextColor(100, 116, 139)
      document.text(label.toUpperCase(), x + 16, y + 20)
      document.setFontSize(18)
      document.setTextColor(15, 23, 42)
      document.text(value, x + 16, y + 44)
      document.setFont("helvetica", "normal")
      document.setFontSize(9)
      document.setTextColor(71, 85, 105)
      const detailLines = document.splitTextToSize(detail, width - 28) as string[]
      document.text(detailLines, x + 16, y + 62)
    }

    const drawMiniMetric = (
      x: number,
      y: number,
      width: number,
      label: string,
      value: number,
      color: [number, number, number]
    ) => {
      document.setFillColor(255, 255, 255)
      document.setDrawColor(226, 232, 240)
      document.roundedRect(x, y, width, 54, 10, 10, "FD")
      document.setFillColor(...color)
      document.circle(x + 16, y + 18, 4, "F")
      document.setFont("helvetica", "bold")
      document.setFontSize(10)
      document.setTextColor(100, 116, 139)
      document.text(label.toUpperCase(), x + 28, y + 21)
      document.setFontSize(18)
      document.setTextColor(15, 23, 42)
      document.text(`${value}`, x + 14, y + 42)
    }

    const drawCategoryBar = (
      x: number,
      y: number,
      width: number,
      label: string,
      value: number,
      maxValue: number,
      color: [number, number, number]
    ) => {
      document.setFont("helvetica", "normal")
      document.setFontSize(10)
      document.setTextColor(51, 65, 85)
      document.text(label, x, y)
      document.text(`${value}`, x + width - 18, y)
      document.setFillColor(241, 245, 249)
      document.roundedRect(x, y + 8, width, 8, 4, 4, "F")
      document.setFillColor(...color)
      const barWidth = maxValue > 0 ? Math.max((value / maxValue) * width, value > 0 ? 14 : 0) : 0
      if (barWidth > 0) {
        document.roundedRect(x, y + 8, barWidth, 8, 4, 4, "F")
      }
    }

    document.setFillColor(15, 23, 42)
    document.rect(0, 0, pageWidth, 134, "F")
    document.setFont("helvetica", "bold")
    document.setFontSize(24)
    document.setTextColor(255, 255, 255)
    document.text("infralint Infrastructure Scorecard", margin, 48)
    document.setFont("helvetica", "normal")
    document.setFontSize(11)
    document.text(`Generated ${reportDate}`, margin, 70)
    document.text(`Files: ${resultsState.fileNames.join(", ")}`, margin, 88, { maxWidth: pageWidth - margin * 2 })
    document.setFillColor(...riskProfile.pdf)
    document.rect(pageWidth - 180, 36, 140, 28, "F")
    document.setFont("helvetica", "bold")
    document.setFontSize(10)
    document.setTextColor(255, 255, 255)
    document.text(riskProfile.label.toUpperCase(), pageWidth - 170, 54)

    currentY = 156
    const cardGap = 14
    const cardWidth = (pageWidth - margin * 2 - cardGap) / 2
    const cardHeight = 84

    scoreCards.forEach((card, index) => {
      const column = index % 2
      const row = Math.floor(index / 2)
      const x = margin + column * (cardWidth + cardGap)
      const y = currentY + row * (cardHeight + cardGap)
      drawMetricCard(x, y, cardWidth, cardHeight, card.label, card.value, card.detail, card.color)
    })
    currentY += cardHeight * 2 + cardGap + 28

    ensureSpace(82)
    const miniGap = 10
    const miniWidth = (pageWidth - margin * 2 - miniGap * 3) / 4
    severitySummary.forEach((item, index) => {
      drawMiniMetric(margin + index * (miniWidth + miniGap), currentY, miniWidth, item.label, item.value, item.color)
    })
    currentY += 74

    drawSection("Executive summary", "A client-ready summary of the current posture, deployment signal, and the most important remediation themes.")
    drawWrappedText(riskProfile.description, margin, currentY, pageWidth - margin * 2, {
      fontSize: 11,
      color: [30, 41, 59],
      lineHeight: 16,
    })
    currentY += 8
    drawWrappedText(
      resultsState.architectureSummary || "Architecture summary unavailable. Use the detailed findings below to validate controls, deployment defaults, and operational guardrails.",
      margin,
      currentY,
      pageWidth - margin * 2,
      { fontSize: 11, color: [51, 65, 85], lineHeight: 16 }
    )
    currentY += 10

    drawSection("Score breakdown")
    scoreBreakdown.forEach((item) => {
      const value = item.value !== null ? `${item.value}%` : "N/A"
      drawWrappedText(`${item.label}: ${value}`, margin, currentY, pageWidth - margin * 2, {
        fontSize: 11,
        color: [30, 41, 59],
        lineHeight: 16,
        fontStyle: "bold",
      })
    })
    currentY += 2
    Object.entries(resultsState.categorySummary).forEach(([category, count]) => {
      const meta = categoryMeta[category as CategoryKey]
      drawWrappedText(`${meta.label} findings: ${count}`, margin, currentY, pageWidth - margin * 2, {
        fontSize: 10,
        color: [71, 85, 105],
        lineHeight: 14,
      })
    })
    currentY += 12

    ensureSpace(88)
    const maxCategoryValue = Math.max(...categoryBreakdown.map((item) => item.value), 1)
    categoryBreakdown.forEach((item, index) => {
      drawCategoryBar(margin, currentY + index * 24, pageWidth - margin * 2, item.label, item.value, maxCategoryValue, item.color)
    })
    currentY += categoryBreakdown.length * 24 + 10

    drawSection("Top recommendations")
    if (resultsState.topRecommendations.length > 0) {
      resultsState.topRecommendations.forEach((recommendation) => {
        drawWrappedText(`• ${recommendation}`, margin, currentY, pageWidth - margin * 2, {
          fontSize: 11,
          color: [30, 41, 59],
          lineHeight: 16,
        })
      })
    } else {
      drawWrappedText("No top recommendations were returned by the analysis service.", margin, currentY, pageWidth - margin * 2, {
        fontSize: 11,
        color: [71, 85, 105],
        lineHeight: 16,
      })
    }
    currentY += 10

    drawSection("Per-file scorecard")
    resultsState.perFileSummary.forEach((file) => {
      ensureSpace(74)
      document.setFillColor(248, 250, 252)
      document.setDrawColor(226, 232, 240)
      document.rect(margin, currentY, pageWidth - margin * 2, 64, "FD")
      document.setFont("helvetica", "bold")
      document.setFontSize(11)
      document.setTextColor(15, 23, 42)
      document.text(file.fileName, margin + 14, currentY + 20)
      document.setFont("helvetica", "normal")
      document.setFontSize(10)
      document.setTextColor(71, 85, 105)
      document.text(`Score: ${file.score !== null ? `${file.score}%` : "N/A"}  •  Findings: ${file.totalIssues}`, margin + 14, currentY + 38)
      document.text(
        `Security ${file.security}  |  Reliability ${file.reliability}  |  Cost ${file.cost}  |  Compliance ${file.compliance}`,
        margin + 14,
        currentY + 54
      )
      currentY += 76
    })

    drawSection("Priority findings", "The export focuses on the highest-severity issues first so the report reads like a remediation plan, not a raw data dump.")
    priorityFindings.forEach((issue, index) => {
      ensureSpace(96)
      const accent = severityMeta[issue.severity].pdf
      document.setFillColor(255, 255, 255)
      document.setDrawColor(226, 232, 240)
      document.rect(margin, currentY, pageWidth - margin * 2, 82, "FD")
      document.setFillColor(...accent)
      document.rect(margin, currentY, 6, 82, "F")
      document.setFont("helvetica", "bold")
      document.setFontSize(11)
      document.setTextColor(15, 23, 42)
      document.text(`${index + 1}. ${issue.title}`, margin + 16, currentY + 18)
      document.setFont("helvetica", "normal")
      document.setFontSize(9)
      document.setTextColor(71, 85, 105)
      document.text(`${severityMeta[issue.severity].label} • ${categoryMeta[issue.category].label} • ${issue.fileName}`, margin + 16, currentY + 34)
      const descriptionLines = document.splitTextToSize(issue.description, pageWidth - margin * 2 - 32) as string[]
      document.text(descriptionLines.slice(0, 2), margin + 16, currentY + 50)
      const recommendationLines = document.splitTextToSize(`Recommendation: ${issue.recommendation}`, pageWidth - margin * 2 - 32) as string[]
      document.text(recommendationLines.slice(0, 2), margin + 16, currentY + 70)
      currentY += 94
    })

    const pageCount = document.getNumberOfPages()
    if (resultsState.failedAnalyses.length > 0) {
      drawSection("Analysis failures", "These files did not produce a usable result and should not be interpreted as clean passes.")
      resultsState.failedAnalyses.forEach((analysis, index) => {
        ensureSpace(84)
        document.setFillColor(255, 245, 245)
        document.setDrawColor(254, 205, 211)
        document.rect(margin, currentY, pageWidth - margin * 2, 70, "FD")
        document.setFillColor(225, 29, 72)
        document.rect(margin, currentY, 6, 70, "F")
        document.setFont("helvetica", "bold")
        document.setFontSize(11)
        document.setTextColor(15, 23, 42)
        document.text(`${index + 1}. ${analysis.fileName}`, margin + 16, currentY + 18)
        document.setFont("helvetica", "normal")
        document.setFontSize(9)
        document.setTextColor(71, 85, 105)
        const errorLines = document.splitTextToSize(`Failure: ${analysis.errorMessage}`, pageWidth - margin * 2 - 30) as string[]
        document.text(errorLines.slice(0, 3), margin + 16, currentY + 36)
        currentY += 82
      })
    }

    for (let index = 1; index <= pageCount; index += 1) {
      document.setPage(index)
      document.setFont("helvetica", "normal")
      document.setFontSize(9)
      document.setTextColor(148, 163, 184)
      document.text(`Page ${index} of ${pageCount}`, pageWidth - margin - 46, pageHeight - 18)
      document.text("infralint report", margin, pageHeight - 18)
    }

    document.save(`infralint-analysis-${analysisIds[0] || "report"}.pdf`)
    setActionMessage("Analysis report downloaded.")
  }

  const totalIssues = resultsState?.issues.length || 0
  const riskProfile = resultsState ? getRiskProfile(resultsState.averageScore, resultsState.summary) : null
  const reportStatus = resultsState ? getReportStatus(resultsState.analyses) : null
  const readinessProfile = resultsState ? getReadinessProfile(resultsState.deploymentReadiness) : null
  const sortedIssues = useMemo(
    () => (resultsState ? [...resultsState.issues].sort((left, right) => severityRank[right.severity] - severityRank[left.severity]) : []),
    [resultsState]
  )
  const scoreBreakdownCards = resultsState
    ? [
        { key: "security", label: "Security", value: resultsState.scoreBreakdown.security },
        { key: "reliability", label: "Reliability", value: resultsState.scoreBreakdown.reliability },
        { key: "cost", label: "Cost", value: resultsState.scoreBreakdown.cost },
        { key: "compliance", label: "Compliance", value: resultsState.scoreBreakdown.compliance },
      ]
    : []
  const maxCategoryCount = resultsState ? Math.max(...Object.values(resultsState.categorySummary), 1) : 1

  const filteredIssues = (category: CategoryKey) => sortedIssues.filter((issue) => issue.category === category)

  const renderIssueCollection = (issues: IssueViewModel[], emptyLabel: string) => {
    if (issues.length === 0) {
      return (
        <Card className="rounded-[1.75rem] border-dashed border-border/70 bg-background/70">
          <CardContent className="p-10 text-center text-sm text-muted-foreground">{emptyLabel}</CardContent>
        </Card>
      )
    }

    return (
      <div className="space-y-5">
        {issues.map((issue) => (
          <IssueCard key={issue.id} issue={issue} />
        ))}
      </div>
    )
  }

  return (
    <div className="report-page flex min-h-screen bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.10),transparent_28%),radial-gradient(circle_at_bottom_right,hsl(var(--accent)/0.18),transparent_26%)] print:bg-none">
      <Sidebar />
      <main className="report-main min-h-screen flex-1 bg-transparent">
        <div className="report-shell mx-auto max-w-7xl px-6 py-8 lg:px-8">
          {isLoading ? (
            <div className="surface-panel rounded-[1.75rem] p-6 text-muted-foreground report-card report-avoid-break">
              AI is loading the infrastructure review...
            </div>
          ) : errorMessage ? (
            <Card className="rounded-[1.75rem] border-rose-500/20 bg-rose-500/5 report-card report-avoid-break">
              <CardContent className="flex items-start gap-3 p-6 text-rose-700 dark:text-rose-200">
                <ShieldAlert className="mt-0.5 h-5 w-5 flex-shrink-0" />
                <div>
                  <p className="font-semibold">Unable to load report</p>
                  <p className="mt-1 text-sm text-rose-700/90 dark:text-rose-200/90">{errorMessage}</p>
                </div>
              </CardContent>
            </Card>
          ) : resultsState ? (
            <>
              <section className="report-hero report-card report-avoid-break relative overflow-hidden rounded-[2rem] border border-border/70 bg-[linear-gradient(140deg,hsl(var(--background))_5%,hsl(var(--primary)/0.08)_45%,hsl(var(--accent)/0.10)_100%)] p-8 shadow-[0_30px_100px_-42px_hsl(var(--foreground)/0.45)]">
                <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.14),transparent_32%),radial-gradient(circle_at_bottom_right,hsl(var(--accent)/0.15),transparent_28%)]" />
                <div className="relative flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
                  <div className="max-w-4xl space-y-5">
                    <Badge variant="outline" className="w-fit border-primary/20 bg-primary/5 px-4 py-1 text-primary">
                      Modern security scorecard
                    </Badge>
                    <div className="space-y-4">
                      <h1 className="text-4xl font-semibold tracking-tight text-foreground lg:text-5xl">
                        Client-ready infrastructure review
                      </h1>
                      <p className="max-w-3xl text-base leading-8 text-muted-foreground lg:text-lg">
                        A polished executive summary of deployment posture, risk concentration, and remediation priorities across {resultsState.fileNames.length} reviewed file{resultsState.fileNames.length === 1 ? "" : "s"}.
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-3 text-sm">
                      <Badge variant="outline" className={cn("border px-3 py-1", riskProfile?.badgeClass)}>
                        {riskProfile?.label}
                      </Badge>
                      <Badge variant="outline" className={cn("border px-3 py-1", reportStatus?.className)}>
                        {reportStatus?.label}
                      </Badge>
                      <Badge variant="outline" className="border-border/70 bg-background/60 px-3 py-1 text-muted-foreground">
                        Generated {formatTimestamp(resultsState.generatedAt)}
                      </Badge>
                    </div>
                  </div>

                  <div className="report-actions flex flex-wrap gap-3 print:hidden">
                    <Button variant="outline" className="gap-2 rounded-full border-border/80 bg-background/75" onClick={handleShare}>
                      <Share2 className="h-4 w-4" />
                      Share
                    </Button>
                    <Button className="gap-2 rounded-full" onClick={handleExportPdf}>
                      <Download className="h-4 w-4" />
                      Export PDF
                    </Button>
                  </div>
                </div>

                {actionMessage && (
                  <div className="relative mt-6 rounded-[1.25rem] border border-primary/15 bg-background/80 px-4 py-3 text-sm text-foreground">
                    {actionMessage}
                  </div>
                )}

                {loadNotice && (
                  <div className="relative mt-4 rounded-[1.25rem] border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-800 dark:text-amber-200 print:border-border print:bg-background print:text-foreground">
                    {loadNotice}
                  </div>
                )}

                {resultsState.failedAnalyses.length > 0 && (
                  <Alert className="relative mt-4 border-rose-500/20 bg-rose-500/10 text-rose-800 dark:text-rose-200 print:border-border print:bg-background print:text-foreground">
                    <ShieldAlert className="h-4 w-4" />
                    <AlertTitle>{resultsState.failedAnalyses.length} analysis failure{resultsState.failedAnalyses.length === 1 ? "" : "s"} detected</AlertTitle>
                    <AlertDescription>
                      <p>
                        This report is {reportStatus?.label.toLowerCase()}. Failed analyses are shown explicitly below and should not be interpreted as clean results.
                      </p>
                      <div className="mt-3 space-y-2">
                        {resultsState.failedAnalyses.slice(0, 3).map((analysis) => (
                          <p key={analysis.analysisId} className="text-sm leading-6 text-current/90">
                            <span className="font-medium">{analysis.fileName}:</span> {analysis.errorMessage}
                          </p>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                <div className="relative mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                  {[
                    {
                      label: "Average score",
                      value: resultsState.averageScore !== null ? `${resultsState.averageScore}%` : "N/A",
                      detail: riskProfile?.description || "Score unavailable",
                    },
                    {
                      label: "Deployment readiness",
                      value: readinessProfile?.label || "Needs review",
                      detail: "Release recommendation based on returned readiness signal.",
                    },
                    {
                      label: "Failed analyses",
                      value: `${resultsState.failedAnalyses.length}`,
                      detail:
                        resultsState.failedAnalyses.length > 0
                          ? `${resultsState.failedAnalyses.slice(0, 2).map((analysis) => analysis.fileName).join(", ")}${resultsState.failedAnalyses.length > 2 ? `, +${resultsState.failedAnalyses.length - 2} more` : ""}`
                          : "All requested analyses completed without execution failures.",
                    },
                    {
                      label: "Total findings",
                      value: `${totalIssues}`,
                      detail: `${resultsState.summary.critical + resultsState.summary.high} urgent items require priority attention.`,
                    },
                    {
                      label: "Files reviewed",
                      value: `${resultsState.fileNames.length}`,
                      detail: resultsState.fileNames.join(", "),
                    },
                  ].map((stat) => (
                    <div key={stat.label} className="rounded-[1.5rem] border border-border/70 bg-background/75 p-5 shadow-sm backdrop-blur">
                      <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{stat.label}</p>
                      <p className={cn("mt-3 text-3xl font-semibold text-foreground", stat.label === "Deployment readiness" && readinessProfile?.className)}>
                        {stat.value}
                      </p>
                      <p className="mt-3 line-clamp-3 text-sm leading-6 text-muted-foreground">{stat.detail}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)] report-grid">
                <Card className="surface-panel rounded-[1.75rem] border-border/70 bg-card/85 shadow-[0_24px_90px_-38px_hsl(var(--foreground)/0.36)] report-card report-avoid-break">
                  <CardHeader>
                    <CardTitle>Executive posture</CardTitle>
                    <CardDescription>
                      A scorecard-style overview of severity concentration and the current operating signal for this report.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-8 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
                      <div className="space-y-6">
                        <div className="rounded-[1.5rem] border border-border/70 bg-background/70 p-5">
                          <div className="flex items-center justify-between gap-4">
                            <div>
                              <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Risk posture</p>
                              <p className="mt-2 text-2xl font-semibold text-foreground">{riskProfile?.label}</p>
                            </div>
                            <Sparkles className="h-5 w-5 text-primary" />
                          </div>
                          <p className="mt-4 text-sm leading-7 text-muted-foreground">{riskProfile?.description}</p>
                        </div>

                        <div className="rounded-[1.5rem] border border-border/70 bg-background/70 p-5">
                          <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Architecture summary</p>
                          <p className="mt-4 text-sm leading-7 text-foreground/90">
                            {resultsState.architectureSummary || "Architecture summary unavailable. Use the findings below to evaluate exposed surfaces and remediation depth."}
                          </p>
                        </div>

                        <div className="rounded-[1.5rem] border border-border/70 bg-background/70 p-5">
                          <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">Top recommendations</p>
                          <div className="mt-4 space-y-3">
                            {resultsState.topRecommendations.length > 0 ? (
                              resultsState.topRecommendations.map((recommendation) => (
                                <div key={recommendation} className="flex gap-3 rounded-[1rem] border border-border/60 bg-background/70 p-3">
                                  <div className="mt-1 h-2.5 w-2.5 rounded-full bg-primary" />
                                  <p className="text-sm leading-6 text-foreground/90">{recommendation}</p>
                                </div>
                              ))
                            ) : (
                              <p className="text-sm text-muted-foreground">No recommendations were returned by the analysis service.</p>
                            )}
                          </div>
                        </div>
                      </div>

                      <SummaryChart
                        critical={resultsState.summary.critical}
                        high={resultsState.summary.high}
                        medium={resultsState.summary.medium}
                        low={resultsState.summary.low}
                        totalIssues={totalIssues}
                        averageScore={resultsState.averageScore}
                      />
                    </div>
                  </CardContent>
                </Card>

                <div className="space-y-6">
                  <Card className="surface-panel rounded-[1.75rem] border-border/70 bg-card/85 report-card report-avoid-break">
                    <CardHeader>
                      <CardTitle>Category concentration</CardTitle>
                      <CardDescription>Where the report is clustering most of its risk.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-5">
                      {(Object.entries(resultsState.categorySummary) as Array<[CategoryKey, number]>).map(([category, count]) => (
                        <div key={category} className="space-y-2">
                          <div className="flex items-center justify-between gap-4 text-sm">
                            <span className="font-medium text-foreground">{categoryMeta[category].label}</span>
                            <span className="text-muted-foreground">{count}</span>
                          </div>
                          <div className="h-2 rounded-full bg-background/70">
                            <div
                              className={cn("h-full rounded-full", categoryMeta[category].barClass)}
                              style={{ width: `${Math.max((count / maxCategoryCount) * 100, count > 0 ? 10 : 0)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  <Card className="surface-panel rounded-[1.75rem] border-border/70 bg-card/85 report-card report-avoid-break">
                    <CardHeader>
                      <CardTitle>Control breakdown</CardTitle>
                      <CardDescription>Averaged score signal across the review dimensions.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {scoreBreakdownCards.map((item) => {
                        const category = item.key as CategoryKey
                        const value = item.value ?? 0
                        return (
                          <div key={item.key} className="rounded-[1.25rem] border border-border/70 bg-background/70 p-4">
                            <div className="flex items-center justify-between gap-4">
                              <Badge variant="outline" className={cn("border", categoryMeta[category].badgeClass)}>
                                {item.label}
                              </Badge>
                              <span className="text-sm font-semibold text-foreground">{item.value !== null ? `${item.value}%` : "N/A"}</span>
                            </div>
                            <div className="mt-4 h-2 rounded-full bg-background/70">
                              <div
                                className={cn("h-full rounded-full", categoryMeta[category].barClass)}
                                style={{ width: `${Math.max(value, item.value !== null ? 10 : 0)}%` }}
                              />
                            </div>
                          </div>
                        )
                      })}
                    </CardContent>
                  </Card>
                </div>
              </section>

              <section className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1.12fr)_minmax(0,0.88fr)] report-grid">
                <Card className="surface-panel rounded-[1.75rem] border-border/70 bg-card/85 report-card report-avoid-break">
                  <CardHeader>
                    <CardTitle>Per-file scorecards</CardTitle>
                    <CardDescription>Each reviewed file summarized as a compact audit block.</CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-4 lg:grid-cols-2">
                    {resultsState.perFileSummary.map((file) => (
                      <div key={file.fileId} className="rounded-[1.5rem] border border-border/70 bg-background/70 p-5 shadow-sm">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-lg font-semibold text-foreground">{file.fileName}</p>
                            <p className="mt-1 text-sm text-muted-foreground">
                              {file.status === "failed"
                                ? "Analysis failed before findings could be produced"
                                : `${file.totalIssues} finding${file.totalIssues === 1 ? "" : "s"} surfaced`}
                            </p>
                          </div>
                          <Badge
                            variant="outline"
                            className={cn(
                              "border px-3 py-1",
                              file.status === "failed"
                                ? "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-200"
                                : file.status === "completed"
                                  ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200"
                                  : "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-200"
                            )}
                          >
                            {file.status === "failed" ? "Failed" : file.score !== null ? `${file.score}%` : file.status}
                          </Badge>
                        </div>

                        {file.status === "failed" ? (
                          <div className="mt-5 rounded-[1rem] border border-rose-500/20 bg-rose-500/10 p-4 text-sm leading-7 text-rose-800 dark:text-rose-200">
                            {file.errorMessage || "The backend did not return a detailed failure reason for this analysis."}
                          </div>
                        ) : (
                          <div className="mt-5 grid gap-3 sm:grid-cols-2">
                            <div className="rounded-[1rem] border border-border/60 bg-background/70 p-3">
                              <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Categories</p>
                              <p className="mt-2 text-sm leading-6 text-foreground/90">
                                Security {file.security} · Reliability {file.reliability} · Cost {file.cost} · Compliance {file.compliance}
                              </p>
                            </div>
                            <div className="rounded-[1rem] border border-border/60 bg-background/70 p-3">
                              <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Severity mix</p>
                              <p className="mt-2 text-sm leading-6 text-foreground/90">
                                Critical {file.critical} · High {file.high} · Medium {file.medium} · Low {file.low}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card className="surface-panel rounded-[1.75rem] border-border/70 bg-card/85 report-card report-avoid-break">
                  <CardHeader>
                    <CardTitle>Report scope</CardTitle>
                    <CardDescription>Context that helps the PDF read like a handoff-ready review artifact.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-5">
                    <div className="rounded-[1.5rem] border border-border/70 bg-background/70 p-5">
                      <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Files included</p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {resultsState.fileNames.map((fileName) => (
                          <Badge key={fileName} variant="outline" className="border-border/70 bg-background/70 text-muted-foreground">
                            {fileName}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-[1.5rem] border border-border/70 bg-background/70 p-5">
                      <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Priority actions</p>
                      <div className="mt-4 space-y-3">
                        {sortedIssues.slice(0, 3).map((issue) => (
                          <div key={issue.id} className="flex items-start gap-3 rounded-[1rem] border border-border/60 bg-background/70 p-3">
                            <FileText className="mt-0.5 h-4 w-4 text-primary" />
                            <div>
                              <p className="text-sm font-medium text-foreground">{issue.title}</p>
                              <p className="mt-1 text-sm leading-6 text-muted-foreground">{issue.recommendation}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-[1.5rem] border border-primary/15 bg-primary/5 p-5">
                      <p className="text-xs uppercase tracking-[0.22em] text-primary/80">Presentation note</p>
                      <p className="mt-3 text-sm leading-7 text-foreground/90">
                        The export now mirrors the on-screen scorecard structure: executive summary first, scored dimensions second, and findings sorted by urgency instead of raw payload order.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </section>

              <section className="mt-8">
                <Tabs defaultValue="overview" className="space-y-6 report-tabs">
                  <TabsList className="report-actions flex h-auto flex-wrap gap-2 rounded-[1.25rem] border border-border/70 bg-background/80 p-2 print:hidden">
                    <TabsTrigger value="overview">Overview ({totalIssues})</TabsTrigger>
                    <TabsTrigger value="security">Security ({filteredIssues("security").length})</TabsTrigger>
                    <TabsTrigger value="reliability">Reliability ({filteredIssues("reliability").length})</TabsTrigger>
                    <TabsTrigger value="cost">Cost ({filteredIssues("cost").length})</TabsTrigger>
                    <TabsTrigger value="compliance">Compliance ({filteredIssues("compliance").length})</TabsTrigger>
                  </TabsList>

                  <TabsContent value="overview" className="space-y-4">
                    <div>
                      <h3 className="text-xl font-semibold text-foreground">All findings</h3>
                      <p className="mt-2 text-sm text-muted-foreground">Sorted by severity so the page reads like a remediation queue.</p>
                    </div>
                    {renderIssueCollection(sortedIssues, "No findings are available for this report.")}
                  </TabsContent>

                  <TabsContent value="security" className="space-y-4">
                    <div>
                      <h3 className="text-xl font-semibold text-foreground">Security findings</h3>
                      <p className="mt-2 text-sm text-muted-foreground">Issues related to secrets, exposure, policy, and attack surface reduction.</p>
                    </div>
                    {renderIssueCollection(filteredIssues("security"), "No security findings were returned for this report.")}
                  </TabsContent>

                  <TabsContent value="reliability" className="space-y-4">
                    <div>
                      <h3 className="text-xl font-semibold text-foreground">Reliability findings</h3>
                      <p className="mt-2 text-sm text-muted-foreground">Signals that affect resilience, availability, and operational safety.</p>
                    </div>
                    {renderIssueCollection(filteredIssues("reliability"), "No reliability findings were returned for this report.")}
                  </TabsContent>

                  <TabsContent value="cost" className="space-y-4">
                    <div>
                      <h3 className="text-xl font-semibold text-foreground">Cost findings</h3>
                      <p className="mt-2 text-sm text-muted-foreground">Optimization opportunities that affect spending efficiency and resource waste.</p>
                    </div>
                    {renderIssueCollection(filteredIssues("cost"), "No cost findings were returned for this report.")}
                  </TabsContent>

                  <TabsContent value="compliance" className="space-y-4">
                    <div>
                      <h3 className="text-xl font-semibold text-foreground">Compliance findings</h3>
                      <p className="mt-2 text-sm text-muted-foreground">Controls tied to standards, governance, and policy alignment.</p>
                    </div>
                    {renderIssueCollection(filteredIssues("compliance"), "No compliance findings were returned for this report.")}
                  </TabsContent>
                </Tabs>
              </section>

              <div className="report-actions mt-6 flex justify-end print:hidden">
                <Button asChild variant="outline" className="rounded-full border-border/80 bg-background/70">
                  <Link href="/dashboard">Back to dashboard</Link>
                </Button>
              </div>
            </>
          ) : null}
        </div>
      </main>
    </div>
  )
}
