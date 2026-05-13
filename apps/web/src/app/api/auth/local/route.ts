import { NextRequest, NextResponse } from "next/server"

const LOCAL_AUTH_COOKIE = "infralint_local_auth"

function getAppOrigin(request: NextRequest) {
  return (process.env["NEXT_PUBLIC_APP_URL"] || request.nextUrl.origin).replace(/\/$/, "")
}

function safeRedirect(request: NextRequest, mode: "signin" | "register", params?: Record<string, string>) {
  const redirectUrl = new URL(`/${mode}`, getAppOrigin(request))

  for (const [key, value] of Object.entries(params || {})) {
    redirectUrl.searchParams.set(key, value)
  }

  return redirectUrl
}

export async function POST(request: NextRequest) {
  const formData = await request.formData()
  const mode = formData.get("mode") === "register" ? "register" : "signin"
  const email = String(formData.get("email") || "").trim().toLowerCase()
  const password = String(formData.get("password") || "")
  const firstName = String(formData.get("firstName") || "").trim()
  const lastName = String(formData.get("lastName") || "").trim()
  const company = String(formData.get("company") || "").trim()

  if (!email || !password) {
    return NextResponse.redirect(safeRedirect(request, mode, { error: "local_missing_fields" }))
  }

  if (mode === "register" && password.length < 8) {
    return NextResponse.redirect(safeRedirect(request, mode, { error: "local_password_too_short" }))
  }

  const profile = {
    email,
    firstName,
    lastName,
    company,
    mode,
    signedInAt: new Date().toISOString(),
  }

  const response = NextResponse.redirect(new URL(`/dashboard?auth=local&mode=${mode}`, getAppOrigin(request)))
  response.cookies.set(LOCAL_AUTH_COOKIE, JSON.stringify(profile), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  })

  return response
}