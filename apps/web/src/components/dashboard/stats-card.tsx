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
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">
              {label}
            </p>
            <p className="text-3xl font-bold text-slate-900 dark:text-white">
              {value}
            </p>
          </div>
          <div className="text-blue-500 dark:text-blue-400">
            {iconMap[icon] || <FileText className="h-8 w-8" />}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
