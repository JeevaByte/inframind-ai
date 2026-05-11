import { NextRequest, NextResponse } from "next/server"

function getAppOrigin(request: NextRequest) {
  return (process.env["NEXT_PUBLIC_APP_URL"] || request.nextUrl.origin).replace(/\/$/, "")
}

export async function GET(request: NextRequest) {
  const clientId = process.env["GITHUB_CLIENT_ID"]
  const mode = request.nextUrl.searchParams.get("mode") === "register" ? "register" : "signin"
  const appOrigin = getAppOrigin(request)
  const fallbackUrl = new URL(`/${mode}`, appOrigin)

  if (!clientId) {
    fallbackUrl.searchParams.set("error", "github_not_configured")
    return NextResponse.redirect(fallbackUrl)
  }

  const state = crypto.randomUUID()
  const callbackUrl = new URL("/api/auth/github/callback", appOrigin)
  callbackUrl.searchParams.set("mode", mode)

  const authorizeUrl = new URL("https://github.com/login/oauth/authorize")
  authorizeUrl.searchParams.set("client_id", clientId)
  authorizeUrl.searchParams.set("redirect_uri", callbackUrl.toString())
  authorizeUrl.searchParams.set("scope", "read:user user:email")
  authorizeUrl.searchParams.set("state", state)
  authorizeUrl.searchParams.set("allow_signup", "true")

  const response = NextResponse.redirect(authorizeUrl)
  response.cookies.set("github_oauth_state", state, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 10,
  })

  return response
}