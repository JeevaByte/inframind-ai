import { cookies } from "next/headers"

export const GITHUB_SESSION_COOKIE = "github_session"

export interface GitHubSession {
  accessToken: string
  login: string
  connectedAt: string
}

function decodeSession(rawValue: string): GitHubSession | null {
  try {
    const payload = JSON.parse(Buffer.from(rawValue, "base64url").toString("utf-8")) as GitHubSession
    if (!payload.accessToken || !payload.login) {
      return null
    }
    return payload
  } catch {
    return null
  }
}

function encodeSession(session: GitHubSession) {
  return Buffer.from(JSON.stringify(session), "utf-8").toString("base64url")
}

export async function getGitHubSession() {
  const cookieStore = await cookies()
  const rawValue = cookieStore.get(GITHUB_SESSION_COOKIE)?.value
  if (!rawValue) {
    return null
  }
  return decodeSession(rawValue)
}

export async function setGitHubSession(session: GitHubSession) {
  const cookieStore = await cookies()
  cookieStore.set(GITHUB_SESSION_COOKIE, encodeSession(session), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env["NODE_ENV"] === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  })
}

export async function clearGitHubSession() {
  const cookieStore = await cookies()
  cookieStore.delete(GITHUB_SESSION_COOKIE)
}
