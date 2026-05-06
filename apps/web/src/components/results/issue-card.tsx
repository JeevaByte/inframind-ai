import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SeverityBadge } from "./severity-badge"
import { Lightbulb } from "lucide-react"

interface IssueCardProps {
  issue: {
    id: string
    title: string
    description: string
    severity: "critical" | "high" | "medium" | "low"
    category: string
    recommendation: string
    estimatedCost: string
  }
}

export function IssueCard({ issue }: IssueCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{issue.title}</CardTitle>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {issue.category}
            </p>
          </div>
          <SeverityBadge severity={issue.severity} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          {issue.description}
        </p>

        <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
          <div className="flex gap-3">
            <Lightbulb className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">
                RECOMMENDATION
              </p>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                {issue.recommendation}
              </p>
            </div>
          </div>
        </div>

        <div className="text-sm text-slate-600 dark:text-slate-400">
          Estimated savings: <span className="font-semibold">{issue.estimatedCost}</span>
        </div>
      </CardContent>
    </Card>
  )
}
