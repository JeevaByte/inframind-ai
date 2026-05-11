"use client"

import { Card, CardContent } from "@/components/ui/card"
import { AlertCircle, DollarSign, Shield, FileText } from "lucide-react"

interface StatsCardProps {
  label: string
  value: string | number
  icon: string
}

const iconMap: Record<string, React.ReactNode> = {
  AlertCircle: <AlertCircle className="h-8 w-8" />,
  DollarSign: <DollarSign className="h-8 w-8" />,
  Shield: <Shield className="h-8 w-8" />,
  FileText: <FileText className="h-8 w-8" />,
}

export function StatsCard({ label, value, icon }: StatsCardProps) {
  return (
    <Card className="surface-panel rounded-[1.75rem] transition-shadow hover:shadow-2xl">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="mb-2 text-sm text-muted-foreground">
              {label}
            </p>
            <p className="text-3xl font-bold text-foreground">
              {value}
            </p>
          </div>
          <div className="rounded-2xl bg-primary/10 p-3 text-primary">
            {iconMap[icon] || <FileText className="h-8 w-8" />}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
