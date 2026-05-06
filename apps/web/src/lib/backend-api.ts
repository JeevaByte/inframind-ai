const DEFAULT_ANALYSIS_API_URL = "http://localhost:8000"

function getApiBaseUrl() {
  return (process.env["NEXT_PUBLIC_ANALYSIS_API_URL"] || DEFAULT_ANALYSIS_API_URL).replace(/\/$/, "")
}

interface ApiEnvelope<T> {
  success: boolean
  data: T
  message?: string
  errors?: string[]
}

export interface UploadedBackendFile {
  file_id: string
  filename: string
  file_type: string
  size_bytes: number
  message: string
}

export interface BackendFileMetadata {
  file_id: string
  filename: string
  original_filename: string
  file_type: string
  size_bytes: number
  content_type: string
  uploaded_at: string
  checksum: string
}

export interface AnalysisSubmission {
  analysis_id: string
  file_id: string
  status: "pending" | "running" | "completed" | "failed"
  analysis_type: "security" | "cost" | "compliance" | "full"
  message: string
}

export interface BulkAnalysisSubmission {
  submitted: AnalysisSubmission[]
  failed: Array<{ file_id: string; error: string }>
}

export interface BackendFinding {
  id: string
  rule_id: string
  title: string
  description: string
  severity: "critical" | "high" | "medium" | "low" | "info"
  resource?: string | null
  line_number?: number | null
  recommendation: string
  references: string[]
  metadata: Record<string, string | number | boolean | null>
}

export interface BackendAnalysisResult {
  analysis_id: string
  file_id: string
  analysis_type: "security" | "cost" | "compliance" | "full"
  status: "pending" | "running" | "completed" | "failed"
  findings: BackendFinding[]
  summary?: string | null
  score?: number | null
  started_at?: string | null
  completed_at?: string | null
  error_message?: string | null
  metadata: Record<string, string | number | boolean | null>
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    cache: "no-store",
    ...init,
  })

  const payload = (await response.json()) as ApiEnvelope<T> | { detail?: string }

  if (!response.ok) {
    const detail = "detail" in payload && payload.detail ? payload.detail : "Request failed"
    throw new Error(detail)
  }

  if (!("success" in payload) || !payload.success || payload.data === undefined) {
    const message = "success" in payload
      ? payload.errors?.length
        ? payload.errors.join("\n")
        : payload.message || "Unexpected API response"
      : payload.detail || "Unexpected API response"
    throw new Error(message)
  }

  return payload.data
}

export async function uploadFiles(files: File[]) {
  const formData = new FormData()
  files.forEach((file) => formData.append("files", file))

  return apiRequest<UploadedBackendFile[]>("/api/v1/files/upload/bulk", {
    method: "POST",
    body: formData,
  })
}

export async function startBulkAnalysis(fileIds: string[]) {
  return apiRequest<BulkAnalysisSubmission>("/api/v1/analysis/bulk", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      file_ids: fileIds,
      analysis_type: "full",
      options: {},
    }),
  })
}

export async function getAnalysisResult(analysisId: string) {
  return apiRequest<BackendAnalysisResult>(`/api/v1/analysis/${analysisId}`)
}

export async function getFileMetadata(fileId: string) {
  return apiRequest<BackendFileMetadata>(`/api/v1/files/${fileId}`)
}