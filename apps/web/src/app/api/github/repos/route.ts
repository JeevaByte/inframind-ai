import { NextResponse } from "next/server"

import { getGitHubSession } from "@/lib/github-session"

export async function GET() {
  const session = await getGitHubSession()

  if (!session) {
    return NextResponse.json({ error: "GitHub account is not connected." }, { status: 401 })
  }

  const response = await fetch("https://api.github.com/user/repos?sort=updated&per_page=50", {
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${session.accessToken}`,
      "X-GitHub-Api-Version": "2022-11-28",
    },
    cache: "no-store",
  })

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { message?: string } | null
    return NextResponse.json(
      { error: payload?.message || "Failed to load GitHub repositories." },
      { status: response.status }
    )
  }

  const payload = (await response.json()) as Array<{
    id: number
    full_name: string
    private: boolean
    default_branch: string
    html_url: string
    updated_at: string
    language: string | null
  }>

  return NextResponse.json({
    repositories: payload.map((repository) => ({
      id: repository.id,
      fullName: repository.full_name,
      isPrivate: repository.private,
      defaultBranch: repository.default_branch,
      htmlUrl: repository.html_url,
      updatedAt: repository.updated_at,
      language: repository.language,
    })),
  })
}
