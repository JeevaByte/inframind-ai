import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { SeverityBadge } from "./severity-badge"
import { Lightbulb } from "lucide-react"

interface IssueCardProps {
  issue: {
    id: string
    title: string
    description: string
    severity: "critical" | "high" | "medium" | "low"
    category: "security" | "reliability" | "cost" | "compliance"
    recommendation: string
    estimatedImpact: string
    fileName?: string
    ruleId?: string
    resource?: string | null
    references?: string[]
  }
}

const categoryStyles = {
  security: "border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-200",
  reliability: "border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-200",
  cost: "border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
  compliance: "border-sky-500/20 bg-sky-500/10 text-sky-700 dark:text-sky-200",
} as const

function formatCategoryLabel(category: IssueCardProps["issue"]["category"]) {
  return category.charAt(0).toUpperCase() + category.slice(1)
}

export function IssueCard({ issue }: IssueCardProps) {
  return (
    <Card className="report-card report-avoid-break overflow-hidden rounded-[1.75rem] border-border/70 bg-card/90 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-xl">
      <CardHeader className="pb-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex-1 space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className={cn("border font-medium", categoryStyles[issue.category])}>
                {formatCategoryLabel(issue.category)}
              </Badge>
              {issue.fileName && (
                <Badge variant="outline" className="border-border/80 bg-background/70 text-muted-foreground">
                  {issue.fileName}
                </Badge>
              )}
              {issue.ruleId && (
                <Badge variant="outline" className="border-border/80 bg-background/70 text-muted-foreground">
                  {issue.ruleId}
                </Badge>
              )}
            </div>
            <div className="space-y-2">
              <CardTitle className="text-xl leading-7 text-foreground">{issue.title}</CardTitle>
              {issue.resource && (
                <p className="text-sm text-muted-foreground">
                  Resource: <span className="font-medium text-foreground">{issue.resource}</span>
                </p>
              )}
            </div>
          </div>
          <SeverityBadge severity={issue.severity} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-7 text-muted-foreground">{issue.description}</p>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(240px,0.8fr)]">
          <div className="rounded-[1.5rem] border border-primary/15 bg-primary/5 p-4">
            <div className="flex gap-3">
              <Lightbulb className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-primary/80">Recommendation</p>
                <p className="mt-2 text-sm leading-7 text-foreground">{issue.recommendation}</p>
              </div>
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-border/70 bg-background/60 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">Estimated impact</p>
            <p className="mt-2 text-sm font-medium leading-6 text-foreground">{issue.estimatedImpact}</p>

            {issue.references && issue.references.length > 0 && (
              <div className="mt-4 border-t border-border/70 pt-4">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">References</p>
                <div className="mt-2 space-y-2">
                  {issue.references.slice(0, 2).map((reference) => (
                    <p key={reference} className="text-sm leading-6 text-muted-foreground">
                      {reference}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
