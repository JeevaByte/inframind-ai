import { NextRequest, NextResponse } from "next/server"

import { setGitHubSession } from "@/lib/github-session"

function getAppOrigin(request: NextRequest) {
  return (process.env["NEXT_PUBLIC_APP_URL"] || request.nextUrl.origin).replace(/\/$/, "")
}

export async function GET(request: NextRequest) {
  const clientId = process.env["GITHUB_CLIENT_ID"]
  const clientSecret = process.env["GITHUB_CLIENT_SECRET"]
  const appOrigin = getAppOrigin(request)
  const mode = request.nextUrl.searchParams.get("mode") === "register" ? "register" : "signin"
  const redirectUrl = new URL(`/${mode}`, appOrigin)

  const error = request.nextUrl.searchParams.get("error")
  if (error) {
    redirectUrl.searchParams.set("error", "github_access_denied")
    return NextResponse.redirect(redirectUrl)
  }

  const incomingState = request.nextUrl.searchParams.get("state")
  const storedState = request.cookies.get("github_oauth_state")?.value
  if (!incomingState || !storedState || incomingState !== storedState) {
    redirectUrl.searchParams.set("error", "github_state_mismatch")
    const response = NextResponse.redirect(redirectUrl)
    response.cookies.delete("github_oauth_state")
    return response
  }

  const code = request.nextUrl.searchParams.get("code")
  if (!code || !clientId || !clientSecret) {
    redirectUrl.searchParams.set("error", code ? "github_not_configured" : "github_missing_code")
    const response = NextResponse.redirect(redirectUrl)
    response.cookies.delete("github_oauth_state")
    return response
  }

  const callbackUrl = new URL("/api/auth/github/callback", appOrigin)
  callbackUrl.searchParams.set("mode", mode)

  const tokenResponse = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      client_id: clientId,
      client_secret: clientSecret,
      code,
      redirect_uri: callbackUrl.toString(),
    }),
  })

  if (!tokenResponse.ok) {
    redirectUrl.searchParams.set("error", "github_token_exchange_failed")
    const response = NextResponse.redirect(redirectUrl)
    response.cookies.delete("github_oauth_state")
    return response
  }

  const tokenPayload = (await tokenResponse.json()) as {
    access_token?: string
    error?: string
  }

  if (!tokenPayload.access_token || tokenPayload.error) {
    redirectUrl.searchParams.set("error", "github_token_exchange_failed")
    const response = NextResponse.redirect(redirectUrl)
    response.cookies.delete("github_oauth_state")
    return response
  }

  const userResponse = await fetch("https://api.github.com/user", {
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${tokenPayload.access_token}`,
      "X-GitHub-Api-Version": "2022-11-28",
    },
    cache: "no-store",
  })

  if (!userResponse.ok) {
    redirectUrl.searchParams.set("error", "github_user_fetch_failed")
    const response = NextResponse.redirect(redirectUrl)
    response.cookies.delete("github_oauth_state")
    return response
  }

  const userPayload = (await userResponse.json()) as {
    login?: string
  }

  redirectUrl.searchParams.set("status", "github_connected")
  if (userPayload.login) {
    redirectUrl.searchParams.set("login", userPayload.login)
    await setGitHubSession({
      accessToken: tokenPayload.access_token,
      login: userPayload.login,
      connectedAt: new Date().toISOString(),
    })
  }

  const response = NextResponse.redirect(redirectUrl)
  response.cookies.delete("github_oauth_state")
  return response
}