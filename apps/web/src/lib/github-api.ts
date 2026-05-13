export interface GitHubConnectionResponse {
  connected: boolean
  login: string | null
  connectedAt: string | null
}

export interface GitHubRepository {
  id: number
  fullName: string
  isPrivate: boolean
  defaultBranch: string
  htmlUrl: string
  updatedAt: string
  language: string | null
}

export interface RepoScanFindingSummary {
  critical: number
  high: number
  medium: number
  low: number
  info: number
  total: number
}

export interface RepoScannerResult {
  scanner: string
  status: "pending" | "running" | "completed" | "failed"
  error_message?: string | null
  findings: Array<{ id: string; severity: string; title: string; resource?: string | null }>
  summary: RepoScanFindingSummary
}

export interface RepoScanResult {
  scan_id: string
  repository: string
  ref?: string | null
  status: "pending" | "running" | "completed" | "failed"
  error_message?: string | null
  findings: Array<{ id: string; severity: string; title: string; resource?: string | null }>
  summary: RepoScanFindingSummary
  scanners: RepoScannerResult[]
  started_at: string
  completed_at?: string | null
  metadata?: Record<string, string | boolean | Record<string, string> | null>
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    cache: "no-store",
    ...init,
  })

  const payload = (await response.json().catch(() => ({ error: "Unexpected response" }))) as T & {
    error?: string
    message?: string
    data?: T
  }

  if (!response.ok) {
    throw new Error(payload.error || payload.message || "Request failed")
  }

  if (payload && typeof payload === "object" && "data" in payload && payload.data) {
    return payload.data
  }

  return payload as T
}

export function getGitHubConnection() {
  return requestJson<GitHubConnectionResponse>("/api/github/connection")
}

export function disconnectGitHub() {
  return requestJson<{ success: boolean }>("/api/github/connection", { method: "DELETE" })
}

export async function listGitHubRepos() {
  const payload = await requestJson<{ repositories: GitHubRepository[] }>("/api/github/repos")
  return payload.repositories
}

export async function startRepoScan(repository: string, ref?: string, scanners?: string[]) {
  const payload = await requestJson<{ data?: RepoScanResult } | RepoScanResult>("/api/repo-scans", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ repository, ref, scanners }),
  })

  return (payload as { data?: RepoScanResult }).data ?? (payload as RepoScanResult)
}

export async function listRepoScans() {
  const payload = await requestJson<{ data?: { scans: RepoScanResult[] } } | { scans: RepoScanResult[] }>("/api/repo-scans")
  const normalized = (payload as { data?: { scans: RepoScanResult[] } }).data ?? (payload as { scans: RepoScanResult[] })
  return normalized.scans
}
