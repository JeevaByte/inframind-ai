import { NextResponse } from "next/server"

import type { BackendAnalysisResult, BackendFileMetadata } from "@/lib/backend-api"

const FASTAPI_URL = (process.env["FASTAPI_URL"] || "http://localhost:8000").replace(/\/$/, "")
const REQUEST_TIMEOUT_MS = 15000
const CONCURRENCY_LIMIT = 4

interface FastApiEnvelope<T> {
  success?: boolean
  data?: T
  detail?: string
  message?: string
  errors?: string[]
}

interface AggregatedResultsRequest {
  analysisIds?: string[]
}

async function fetchFastApi<T>(path: string): Promise<T> {
  const controller = new AbortController()
  const timeoutHandle = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    const response = await fetch(`${FASTAPI_URL}${path}`, {
      cache: "no-store",
      signal: controller.signal,
    })

    const payload = (await response.json()) as FastApiEnvelope<T>

    if (!response.ok) {
      throw new Error(payload.detail || payload.message || payload.errors?.join("\n") || "Request failed")
    }

    if (payload.success === false || payload.data === undefined) {
      throw new Error(payload.errors?.join("\n") || payload.detail || payload.message || "Unexpected API response")
    }

    return payload.data
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Request timed out while loading analysis results.")
    }

    throw error
  } finally {
    clearTimeout(timeoutHandle)
  }
}

async function mapWithConcurrency<TInput, TOutput>(
  items: TInput[],
  worker: (item: TInput) => Promise<TOutput>
) {
  const results: TOutput[] = new Array(items.length)
  let currentIndex = 0

  async function runWorker() {
    while (currentIndex < items.length) {
      const index = currentIndex
      currentIndex += 1
      const item = items[index]

      if (item === undefined) {
        continue
      }

      results[index] = await worker(item)
    }
  }

  const workerCount = Math.min(CONCURRENCY_LIMIT, items.length)
  await Promise.all(Array.from({ length: workerCount }, () => runWorker()))

  return results
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as AggregatedResultsRequest
    const requestedIds = Array.isArray(body.analysisIds) ? body.analysisIds : []
    const analysisIds = [...new Set(requestedIds.map((value) => value.trim()).filter(Boolean))]

    if (analysisIds.length === 0) {
      return NextResponse.json({ error: "At least one analysis ID is required." }, { status: 400 })
    }

    const analysesSettled = await mapWithConcurrency(analysisIds, async (analysisId) => {
      try {
        const analysis = await fetchFastApi<BackendAnalysisResult>(`/api/v1/analysis/${analysisId}`)
        return { analysisId, analysis, error: null }
      } catch (error) {
        return {
          analysisId,
          analysis: null,
          error: error instanceof Error ? error.message : "Failed to load analysis result.",
        }
      }
    })

    const analyses = analysesSettled
      .filter((entry): entry is { analysisId: string; analysis: BackendAnalysisResult; error: null } => entry.analysis !== null)
      .map((entry) => entry.analysis)

    const failedAnalyses = analysesSettled
      .filter((entry) => entry.analysis === null)
      .map((entry) => ({ analysisId: entry.analysisId, error: entry.error || "Failed to load analysis result." }))

    if (analyses.length === 0) {
      return NextResponse.json(
        { error: failedAnalyses[0]?.error || "Unable to load any analysis results.", failedAnalyses },
        { status: 502 }
      )
    }

    const uniqueFileIds = [...new Set(analyses.map((analysis) => analysis.file_id))]
    const metadataSettled = await mapWithConcurrency(uniqueFileIds, async (fileId) => {
      try {
        const metadata = await fetchFastApi<BackendFileMetadata>(`/api/v1/files/${fileId}`)
        return { fileId, metadata, error: null }
      } catch (error) {
        return {
          fileId,
          metadata: null,
          error: error instanceof Error ? error.message : "Failed to load file metadata.",
        }
      }
    })

    const fileMetadata = Object.fromEntries(
      metadataSettled
        .filter((entry): entry is { fileId: string; metadata: BackendFileMetadata; error: null } => entry.metadata !== null)
        .map((entry) => [entry.fileId, entry.metadata])
    )

    const failedMetadata = metadataSettled
      .filter((entry) => entry.metadata === null)
      .map((entry) => ({ fileId: entry.fileId, error: entry.error || "Failed to load file metadata." }))

    return NextResponse.json({
      analyses,
      fileMetadata,
      failedAnalyses,
      failedMetadata,
    })
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    )
  }
}