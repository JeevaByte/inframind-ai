"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"

interface Analysis {
  id: string
  name: string
  date: string
  status: string
  issuesFound: number
  severity: string
}

interface RecentAnalysesProps {
  analyses: Analysis[]
}

export function RecentAnalyses({ analyses }: RecentAnalysesProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Analyses</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {analyses.map((analysis) => (
            <Link
              key={analysis.id}
              href={`/results/${analysis.id}`}
              className="flex items-start justify-between p-4 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <div className="flex-1">
                <h4 className="font-medium text-slate-900 dark:text-white">
                  {analysis.name}
                </h4>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  {new Date(analysis.date).toLocaleDateString()} •{" "}
                  <span className="capitalize">{analysis.status}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Badge
                  variant={
                    analysis.severity === "high"
                      ? "destructive"
                      : "secondary"
                  }
                >
                  {analysis.issuesFound} issues
                </Badge>
              </div>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
