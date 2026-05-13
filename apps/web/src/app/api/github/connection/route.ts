import { NextResponse } from "next/server"

import { clearGitHubSession, getGitHubSession } from "@/lib/github-session"

export async function GET() {
  const session = await getGitHubSession()

  return NextResponse.json({
    connected: Boolean(session),
    login: session?.login ?? null,
    connectedAt: session?.connectedAt ?? null,
  })
}

export async function DELETE() {
  await clearGitHubSession()
  return NextResponse.json({ success: true })
}
