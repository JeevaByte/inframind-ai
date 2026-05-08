import { NextResponse } from "next/server"

const FASTAPI_URL = (process.env.FASTAPI_URL || "http://localhost:8000").replace(/\/$/, "")

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  try {
    const res = await fetch(`${FASTAPI_URL}/api/v1/analysis/${id}`, {
      cache: "no-store",
    })

    if (!res.ok) {
      const text = await res.text()
      let message = "Analysis not found"
      try {
        const parsed = JSON.parse(text) as { detail?: string; message?: string }
        message = parsed.detail || parsed.message || message
      } catch {
        // non-JSON error body; keep default message
      }
      return NextResponse.json({ error: message }, { status: res.status })
    }

    const payload = (await res.json()) as {
      success?: boolean
      data?: unknown
    }

    // Unwrap the FastAPI envelope and return just the data
    if (payload.success && payload.data !== undefined) {
      return NextResponse.json(payload.data)
    }

    return NextResponse.json(payload)
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    )
  }
}
