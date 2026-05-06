import { Badge } from "@/components/ui/badge"

type Severity = "critical" | "high" | "medium" | "low"

interface SeverityBadgeProps {
  severity: Severity
}

const severityStyles: Record<Severity, { bg: string; text: string; label: string }> = {
  critical: {
    bg: "bg-red-100 dark:bg-red-950",
    text: "text-red-800 dark:text-red-200",
    label: "Critical",
  },
  high: {
    bg: "bg-orange-100 dark:bg-orange-950",
    text: "text-orange-800 dark:text-orange-200",
    label: "High",
  },
  medium: {
    bg: "bg-yellow-100 dark:bg-yellow-950",
    text: "text-yellow-800 dark:text-yellow-200",
    label: "Medium",
  },
  low: {
    bg: "bg-blue-100 dark:bg-blue-950",
    text: "text-blue-800 dark:text-blue-200",
    label: "Low",
  },
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const style = severityStyles[severity]
  return (
    <Badge
      variant="outline"
      className={`${style.bg} ${style.text} border-0 font-semibold`}
    >
      {style.label}
    </Badge>
  )
}
