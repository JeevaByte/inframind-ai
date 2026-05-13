import type { Metadata } from "next"

import { AuthExperience } from "@/components/auth/auth-experience"

export const metadata: Metadata = {
  title: "Register | infralint",
  description: "Create an infralint account and start with GitHub or staged local registration.",
}

export default function RegisterPage() {
  const githubEnabled = Boolean(process.env["GITHUB_CLIENT_ID"] && process.env["GITHUB_CLIENT_SECRET"])

  return <AuthExperience mode="register" githubEnabled={githubEnabled} />
}