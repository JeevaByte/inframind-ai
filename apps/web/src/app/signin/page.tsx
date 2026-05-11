import type { Metadata } from "next"

import { AuthExperience } from "@/components/auth/auth-experience"

export const metadata: Metadata = {
  title: "Sign In | infralint",
  description: "Sign in to infralint and continue your infrastructure review workflow.",
}

export default function SignInPage() {
  return <AuthExperience mode="signin" />
}