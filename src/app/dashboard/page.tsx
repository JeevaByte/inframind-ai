"use client"

import { Sidebar } from "@/components/layout/sidebar"
import { Button } from "@/components/ui/button"
import { StatsCard } from "@/components/dashboard/stats-card"
import { RecentAnalyses } from "@/components/dashboard/recent-analyses"
import { Plus } from "lucide-react"
import Link from "next/link"
import { mockData } from "@/lib/mock-data"

export default function DashboardPage() {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 bg-slate-50 dark:bg-slate-900 min-h-screen">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              Dashboard
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Overview of your infrastructure analyses
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid md:grid-cols-4 gap-6 mb-8">
            {mockData.stats.map((stat) => (
              <StatsCard
                key={stat.label}
                label={stat.label}
                value={stat.value}
                icon={stat.icon}
              />
            ))}
          </div>

          {/* Quick Actions */}
          <div className="mb-8">
            <Link href="/upload">
              <Button size="lg" className="gap-2">
                <Plus className="h-5 w-5" />
                New Analysis
              </Button>
            </Link>
          </div>

          {/* Recent Analyses */}
          <RecentAnalyses analyses={mockData.recentAnalyses} />
        </div>
      </main>
    </div>
  )
}
