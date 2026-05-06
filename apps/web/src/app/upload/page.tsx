"use client"

import { Sidebar } from "@/components/layout/sidebar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dropzone } from "@/components/upload/dropzone"
import { Progress } from "@/components/ui/progress"
import { CheckCircle2, FileText, Zap } from "lucide-react"

export default function UploadPage() {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 bg-slate-50 dark:bg-slate-900 min-h-screen">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              Upload Infrastructure Files
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Upload your configuration files to get started with analysis
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Upload Area */}
            <div className="lg:col-span-2">
              <Dropzone />
            </div>

            {/* Info Cards */}
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Zap className="h-5 w-5 text-blue-500" />
                    Supported Formats
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-slate-400" />
                    <span>Terraform (.tf)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-slate-400" />
                    <span>CloudFormation (.yaml, .json)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-slate-400" />
                    <span>Kubernetes (.yaml, .yml)</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    Analysis Steps
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm font-semibold mb-1">Step 1: Upload</p>
                    <Progress value={100} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold mb-1">Step 2: Analyze</p>
                    <Progress value={0} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold mb-1">Step 3: Results</p>
                    <Progress value={0} />
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
