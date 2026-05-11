import { NextResponse } from "next/server"

const FASTAPI_URL = (process.env["FASTAPI_URL"] || "http://localhost:8000").replace(/\/$/, "")

export async function POST(request: Request) {
  try {
    const formData = await request.formData()

    // Step 1: Upload files to FastAPI
    const uploadRes = await fetch(`${FASTAPI_URL}/api/v1/files/upload/bulk`, {
      method: "POST",
      body: formData,
    })

    if (!uploadRes.ok) {
      const text = await uploadRes.text()
      let message = "File upload failed"
      try {
        const parsed = JSON.parse(text) as { message?: string; detail?: string; errors?: string[] }
        message = parsed.errors?.join("\n") || parsed.message || parsed.detail || message
      } catch {
        // non-JSON error body; keep default message
      }
      return NextResponse.json({ error: message }, { status: uploadRes.status })
    }

    const uploadPayload = (await uploadRes.json()) as {
      success: boolean
      data: Array<{ file_id: string }>
      message?: string
      errors?: string[]
    }

    if (!uploadPayload.success) {
      return NextResponse.json(
        { error: uploadPayload.errors?.join("\n") || uploadPayload.message || "File upload failed" },
        { status: 500 }
      )
    }

    if (!Array.isArray(uploadPayload.data) || uploadPayload.data.length === 0) {
      return NextResponse.json({ error: "No files were uploaded" }, { status: 422 })
    }

    const fileIds = uploadPayload.data.map((f) => f.file_id)

    // Step 2: Trigger bulk analysis
    const analysisRes = await fetch(`${FASTAPI_URL}/api/v1/analysis/bulk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_ids: fileIds,
        analysis_type: "full",
        options: {},
      }),
    })

    if (!analysisRes.ok) {
      const text = await analysisRes.text()
      let message = "Analysis submission failed"
      try {
        const parsed = JSON.parse(text) as { message?: string; detail?: string; errors?: string[] }
        message = parsed.errors?.join("\n") || parsed.message || parsed.detail || message
      } catch {
        // non-JSON error body; keep default message
      }
      return NextResponse.json({ error: message }, { status: analysisRes.status })
    }

    const analysisPayload = (await analysisRes.json()) as {
      success: boolean
      data: {
        submitted: Array<{ analysis_id: string; file_id: string; status: string; message: string }>
        failed: Array<{ file_id: string; error: string }>
      }
      message?: string
      errors?: string[]
    }

    if (!analysisPayload.success) {
      return NextResponse.json(
        { error: analysisPayload.errors?.join("\n") || analysisPayload.message || "Analysis submission failed" },
        { status: 500 }
      )
    }

    return NextResponse.json(analysisPayload.data)
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Internal server error" },
      { status: 500 }
    )
  }
}
