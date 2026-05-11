import type { Metadata } from "next"

import { AuthExperience } from "@/components/auth/auth-experience"

export const metadata: Metadata = {
  title: "Register | infralint",
  description: "Create an infralint account and start with GitHub or staged local registration.",
}

export default function RegisterPage() {
  return <AuthExperience mode="register" />
}