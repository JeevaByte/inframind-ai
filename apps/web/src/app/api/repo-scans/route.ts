import { NextResponse } from "next/server"

import { getGitHubSession } from "@/lib/github-session"

const FASTAPI_URL = (process.env["FASTAPI_URL"] || process.env["NEXT_PUBLIC_ANALYSIS_API_URL"] || "http://localhost:8000").replace(/\/$/, "")

interface RepoScanRequestBody {
  repository?: string
  ref?: string
  scanners?: string[]
}

export async function POST(request: Request) {
  const session = await getGitHubSession()

  const body = (await request.json()) as RepoScanRequestBody
  if (!body.repository?.trim()) {
    return NextResponse.json({ error: "Repository is required." }, { status: 400 })
  }

  const response = await fetch(`${FASTAPI_URL}/api/v1/repo-scans/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      repository: body.repository.trim(),
      ref: body.ref?.trim() || undefined,
      scanners: body.scanners,
      github_token: session?.accessToken,
    }),
    cache: "no-store",
  })

  const payload = await response.json().catch(() => ({ error: "Unexpected server response" }))
  if (!response.ok) {
    return NextResponse.json(payload, { status: response.status })
  }

  return NextResponse.json(payload)
}

export async function GET() {
  const response = await fetch(`${FASTAPI_URL}/api/v1/repo-scans/`, {
    cache: "no-store",
  })

  const payload = await response.json().catch(() => ({ error: "Unexpected server response" }))
  if (!response.ok) {
    return NextResponse.json(payload, { status: response.status })
  }

  return NextResponse.json(payload)
}
