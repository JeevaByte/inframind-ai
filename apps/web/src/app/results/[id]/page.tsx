"use client"

import { Sidebar } from "@/components/layout/sidebar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { SummaryChart } from "@/components/results/summary-chart"
import { IssueCard } from "@/components/results/issue-card"
import { Download, Share2 } from "lucide-react"
import { mockData } from "@/lib/mock-data"

export default function ResultsPage() {
  const summary = mockData.summary
  const issues = mockData.issues

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 bg-slate-50 dark:bg-slate-900 min-h-screen">
        <div className="p-8">
          <div className="mb-8 flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                Analysis Results
              </h1>
              <p className="text-slate-600 dark:text-slate-400">
                Production Infrastructure • Completed 2 hours ago
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" className="gap-2">
                <Share2 className="h-4 w-4" />
                Share
              </Button>
              <Button className="gap-2">
                <Download className="h-4 w-4" />
                Export PDF
              </Button>
            </div>
          </div>

          {/* Summary Overview */}
          <div className="grid lg:grid-cols-3 gap-8 mb-8">
            <div className="lg:col-span-2">
              <Card>
                <CardHeader>
                  <CardTitle>Issue Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <SummaryChart
                    critical={summary.critical}
                    high={summary.high}
                    medium={summary.medium}
                    low={summary.low}
                  />
                </CardContent>
              </Card>
            </div>

            {/* Quick Stats */}
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Total Issues</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">
                    {summary.critical + summary.high + summary.medium + summary.low}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Critical Issues</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-red-600">
                    {summary.critical}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Est. Annual Savings</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-green-600">
                    $149,400
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Detailed Issues */}
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="security">Security</TabsTrigger>
              <TabsTrigger value="cost">Cost</TabsTrigger>
              <TabsTrigger value="performance">Performance</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  All Issues ({issues.length})
                </h3>
                {issues.map((issue) => (
                  <IssueCard key={issue.id} issue={issue} />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="security">
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Security Issues
                </h3>
                {issues
                  .filter((issue) => issue.category === "security")
                  .map((issue) => (
                    <IssueCard key={issue.id} issue={issue} />
                  ))}
              </div>
            </TabsContent>

            <TabsContent value="cost">
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Cost Optimization
                </h3>
                {issues
                  .filter((issue) => issue.category === "cost")
                  .map((issue) => (
                    <IssueCard key={issue.id} issue={issue} />
                  ))}
              </div>
            </TabsContent>

            <TabsContent value="performance">
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">
                  Performance Issues
                </h3>
                {issues
                  .filter((issue) => issue.category === "performance")
                  .map((issue) => (
                    <IssueCard key={issue.id} issue={issue} />
                  ))}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  )
}
