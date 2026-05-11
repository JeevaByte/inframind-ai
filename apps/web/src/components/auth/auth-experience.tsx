"use client"

import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { useMemo, useState } from "react"
import { motion } from "framer-motion"
import { ArrowRight, ShieldCheck, Sparkles, Workflow } from "lucide-react"

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"

type AuthMode = "signin" | "register"

interface AuthExperienceProps {
  mode: AuthMode
}

function GitHubMark(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.866-.013-1.7-2.782.605-3.369-1.344-3.369-1.344-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.54 9.54 0 0 1 2.504.337c1.909-1.296 2.747-1.026 2.747-1.026.546 1.378.203 2.397.1 2.65.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.31.678.922.678 1.858 0 1.34-.012 2.421-.012 2.75 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.523 2 12 2Z" />
    </svg>
  )
}

const authCopy = {
  signin: {
    eyebrow: "Sign In",
    title: "Get back into the review loop.",
    description:
      "Access infralint reports, dashboards, and upload flows from one focused control surface.",
    primaryLabel: "Sign In",
    alternateHref: "/register",
    alternateLabel: "Create an account",
    alternatePrompt: "Need an account?",
    githubLabel: "Continue with GitHub",
    emailNotice:
      "Email and password sign-in is still a UI path only. Use GitHub today or wire a backend identity provider next.",
  },
  register: {
    eyebrow: "Register",
    title: "Create an account for your review workspace.",
    description:
      "Start with GitHub or reserve your account now so shared infrastructure reviews can land in one place.",
    primaryLabel: "Create Account",
    alternateHref: "/signin",
    alternateLabel: "Sign in instead",
    alternatePrompt: "Already have an account?",
    githubLabel: "Sign up with GitHub",
    emailNotice:
      "Email registration is staged as a frontend path for now. GitHub OAuth is the quickest route once client credentials are configured.",
  },
} as const

function getFeedback(
  mode: AuthMode,
  searchParams: ReturnType<typeof useSearchParams>
): { variant: "default" | "destructive"; title: string; description: string } | null {
  const error = searchParams.get("error")
  const status = searchParams.get("status")
  const login = searchParams.get("login")

  if (status === "github_connected") {
    return {
      variant: "default",
      title: login ? `GitHub connected for @${login}` : "GitHub connected",
      description:
        "The OAuth round-trip completed successfully. Persisting a signed-in session is the next backend step if you want full account state.",
    }
  }

  if (error === "github_not_configured") {
    return {
      variant: "destructive",
      title: "GitHub sign-in is not configured yet",
      description:
        "Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to apps/web/.env.local before using the GitHub auth button.",
    }
  }

  if (error === "github_state_mismatch") {
    return {
      variant: "destructive",
      title: "GitHub auth state check failed",
      description:
        "The OAuth state token did not match the stored value. Start the GitHub sign-in flow again from this page.",
    }
  }

  if (error === "github_access_denied") {
    return {
      variant: "destructive",
      title: "GitHub access was denied",
      description: "GitHub did not grant access to infralint. Try again or use the alternate registration path.",
    }
  }

  if (error === "github_token_exchange_failed" || error === "github_user_fetch_failed") {
    return {
      variant: "destructive",
      title: "GitHub sign-in did not complete",
      description:
        "The OAuth callback returned, but infralint could not finish the GitHub exchange. Verify the client credentials and callback URL.",
    }
  }

  if (error === "github_missing_code") {
    return {
      variant: "destructive",
      title: "GitHub did not return an authorization code",
      description: `The ${mode === "signin" ? "sign-in" : "registration"} flow did not receive a usable callback from GitHub.`,
    }
  }

  return null
}

export function AuthExperience({ mode }: AuthExperienceProps) {
  const searchParams = useSearchParams()
  const [localNotice, setLocalNotice] = useState<string | null>(null)
  const copy = authCopy[mode]
  const feedback = useMemo(() => getFeedback(mode, searchParams), [mode, searchParams])

  return (
    <div className="relative min-h-[calc(100vh-4rem)] overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,hsl(var(--accent)/0.28),transparent_28%),radial-gradient(circle_at_bottom_right,hsl(var(--primary)/0.18),transparent_24%)]" />
      <div className="relative mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)] lg:px-8 lg:py-16">
        <motion.section
          className="flex flex-col justify-between gap-8"
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="space-y-6">
            <Badge variant="outline" className="w-fit border-primary/20 bg-primary/5 px-4 py-1 text-primary">
              {copy.eyebrow}
            </Badge>
            <div className="space-y-4">
              <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
                {copy.title}
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-muted-foreground">{copy.description}</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="surface-panel rounded-[1.75rem] p-5">
                <Sparkles className="mb-4 h-5 w-5 text-primary" />
                <p className="text-sm font-semibold text-foreground">Premium review flow</p>
                <p className="mt-2 text-sm text-muted-foreground">Keep auth inside the same visual system as the dashboard and upload surfaces.</p>
              </div>
              <div className="surface-panel rounded-[1.75rem] p-5">
                <Workflow className="mb-4 h-5 w-5 text-primary" />
                <p className="text-sm font-semibold text-foreground">GitHub-first entry</p>
                <p className="mt-2 text-sm text-muted-foreground">Start with the provider engineering teams already trust for repo-centric workflows.</p>
              </div>
              <div className="surface-panel rounded-[1.75rem] p-5">
                <ShieldCheck className="mb-4 h-5 w-5 text-primary" />
                <p className="text-sm font-semibold text-foreground">Safer rollout path</p>
                <p className="mt-2 text-sm text-muted-foreground">OAuth state validation is included in the GitHub handoff so the entry path is not just a dead button.</p>
              </div>
            </div>
          </div>

          <Alert className="surface-panel max-w-2xl rounded-[1.75rem] border-primary/15 bg-primary/5">
            <Sparkles className="h-4 w-4" />
            <AlertTitle>Operator note</AlertTitle>
            <AlertDescription>
              The page is production-grade UI, while local email auth remains a placeholder until a persistent session backend is added.
            </AlertDescription>
          </Alert>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, x: 18 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.08 }}
        >
          <Card className="surface-panel rounded-[2rem] border-border/60 bg-card/85 shadow-[0_24px_90px_-36px_hsl(var(--foreground)/0.36)]">
            <CardHeader className="space-y-3">
              <CardTitle className="text-3xl text-foreground">{copy.eyebrow}</CardTitle>
              <CardDescription className="text-sm leading-6 text-muted-foreground">
                Use GitHub for the fastest path, or stage local auth details here while the backend identity layer is completed.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {feedback && (
                <Alert variant={feedback.variant} className="rounded-[1.5rem]">
                  <AlertTitle>{feedback.title}</AlertTitle>
                  <AlertDescription>{feedback.description}</AlertDescription>
                </Alert>
              )}

              {localNotice && (
                <Alert className="rounded-[1.5rem] border-primary/15 bg-primary/5">
                  <AlertTitle>Local auth is not wired yet</AlertTitle>
                  <AlertDescription>{localNotice}</AlertDescription>
                </Alert>
              )}

              <Button asChild size="lg" className="h-12 w-full rounded-xl gap-2">
                <Link href={`/api/auth/github?mode=${mode}`}>
                  <GitHubMark className="h-5 w-5" />
                  {copy.githubLabel}
                </Link>
              </Button>

              <div className="flex items-center gap-3 text-xs uppercase tracking-[0.25em] text-muted-foreground">
                <Separator className="bg-border/70" />
                Or continue with email
                <Separator className="bg-border/70" />
              </div>

              <form
                className="space-y-4"
                onSubmit={(event) => {
                  event.preventDefault()
                  setLocalNotice(copy.emailNotice)
                }}
              >
                {mode === "register" && (
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">First name</Label>
                      <Input id="firstName" name="firstName" placeholder="Avery" autoComplete="given-name" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Last name</Label>
                      <Input id="lastName" name="lastName" placeholder="Jordan" autoComplete="family-name" />
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="email">Work email</Label>
                  <Input id="email" name="email" type="email" placeholder="team@company.com" autoComplete="email" />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    placeholder={mode === "signin" ? "Enter your password" : "Create a password"}
                    autoComplete={mode === "signin" ? "current-password" : "new-password"}
                  />
                </div>

                {mode === "register" && (
                  <div className="space-y-2">
                    <Label htmlFor="company">Company</Label>
                    <Input id="company" name="company" placeholder="Infra Platform Team" autoComplete="organization" />
                  </div>
                )}

                <Button type="submit" size="lg" variant="outline" className="h-12 w-full rounded-xl border-border/80 bg-background/60">
                  {copy.primaryLabel}
                </Button>
              </form>

              <div className="rounded-[1.5rem] border border-border/70 bg-background/40 p-4 text-sm text-muted-foreground">
                <span className="font-medium text-foreground">{copy.alternatePrompt}</span>{" "}
                <Link href={copy.alternateHref} className="font-medium text-primary hover:underline">
                  {copy.alternateLabel}
                </Link>
                <span className="mx-2 text-border">·</span>
                <Link href="/dashboard" className="inline-flex items-center gap-1 font-medium text-foreground hover:text-primary">
                  Continue to dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </CardContent>
          </Card>
        </motion.section>
      </div>
    </div>
  )
}