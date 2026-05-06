import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MarketingFooter } from "@/components/layout/marketing-footer"

interface MarketingPageSection {
  title: string
  description: string
}

interface MarketingPageProps {
  eyebrow: string
  title: string
  description: string
  sections: MarketingPageSection[]
  ctaLabel?: string
  ctaHref?: string
  children?: React.ReactNode
}

export function MarketingPage({
  eyebrow,
  title,
  description,
  sections,
  ctaLabel = "Start an Analysis",
  ctaHref = "/upload",
  children,
}: MarketingPageProps) {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.12),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(168,85,247,0.12),_transparent_35%)]" />
        <div className="relative mx-auto max-w-5xl px-4 py-20 sm:px-6 lg:px-8">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
            {eyebrow}
          </p>
          <h1 className="max-w-3xl text-5xl font-bold text-slate-900 dark:text-white sm:text-6xl">
            {title}
          </h1>
          <p className="mt-6 max-w-3xl text-lg text-slate-600 dark:text-slate-300">
            {description}
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link href={ctaHref}>
              <Button size="lg" className="gap-2">
                {ctaLabel}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline">
                View Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-6 md:grid-cols-2">
          {sections.map((section) => (
            <Card key={section.title} className="h-full border-slate-200 bg-white/80 dark:border-slate-800 dark:bg-slate-950/80">
              <CardHeader>
                <CardTitle className="text-xl text-slate-900 dark:text-white">
                  {section.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-7 text-slate-600 dark:text-slate-300">
                  {section.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        {children && <div className="mt-8">{children}</div>}
      </section>

      <MarketingFooter />
    </div>
  )
}