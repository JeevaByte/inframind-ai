import { NextResponse } from "next/server"

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export async function POST(request: Request) {
  const body = (await request.json()) as {
    name?: string
    email?: string
    company?: string
    message?: string
  }

  const name = body.name?.trim() || ""
  const email = body.email?.trim() || ""
  const company = body.company?.trim() || ""
  const message = body.message?.trim() || ""

  if (!name || !email || !message) {
    return NextResponse.json(
      { error: "Name, email, and message are required." },
      { status: 400 }
    )
  }

  if (!isValidEmail(email)) {
    return NextResponse.json(
      { error: "Please enter a valid email address." },
      { status: 400 }
    )
  }

  if (message.length < 20) {
    return NextResponse.json(
      { error: "Please provide a bit more detail in your message." },
      { status: 400 }
    )
  }

  console.info("[contact] New inquiry", {
    name,
    email,
    company,
    messageLength: message.length,
  })

  return NextResponse.json({
    message: "Thanks. Your message has been sent and we will follow up shortly.",
  })
}