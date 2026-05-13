import { NextRequest, NextResponse } from "next/server"

const LOCAL_AUTH_COOKIE = "infralint_local_auth"

function getAppOrigin(request: NextRequest) {
  return (process.env["NEXT_PUBLIC_APP_URL"] || request.nextUrl.origin).replace(/\/$/, "")
}

export async function GET(request: NextRequest) {
  const redirectUrl = new URL("/signin", getAppOrigin(request))
  redirectUrl.searchParams.set("status", "logged_out")

  const response = NextResponse.redirect(redirectUrl)
  response.cookies.delete(LOCAL_AUTH_COOKIE)
  response.cookies.delete("github_oauth_state")

  return response
}