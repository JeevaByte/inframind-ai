"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import { Sidebar } from "@/components/layout/sidebar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dropzone } from "@/components/upload/dropzone"
import { Progress } from "@/components/ui/progress"
import { CheckCircle2, FileText, Zap } from "lucide-react"

export default function UploadPage() {
  const router = useRouter()
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [step1Progress, setStep1Progress] = useState(0)
  const [step2Progress, setStep2Progress] = useState(0)
  const [step3Progress, setStep3Progress] = useState(0)
  const [progressLabel, setProgressLabel] = useState<string | null>(null)
  const [completionMessage, setCompletionMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (selectedFiles.length === 0 || isSubmitting) {
      return
    }

    setIsSubmitting(true)
    setErrorMessage(null)
    setCompletionMessage(null)

    try {
      setProgressLabel("Uploading infrastructure context...")
      setStep1Progress(35)

      const formData = new FormData()
      selectedFiles.forEach((file) => formData.append("files", file))

      const res = await fetch("/api/analysis", {
        method: "POST",
        body: formData,
      })

      setStep1Progress(100)
      setProgressLabel("AI analyzing infrastructure...")
      setStep2Progress(45)

      if (!res.ok) {
        let message = "Failed to analyze uploaded files."
        try {
          const errPayload = (await res.json()) as { error?: string }
          if (errPayload.error) message = errPayload.error
        } catch {
          // non-JSON error body; keep default message
        }
        throw new Error(message)
      }

      const payload = (await res.json()) as {
        submitted: Array<{ analysis_id: string; file_id: string; status: string; message: string }>
        failed: Array<{ file_id: string; error: string }>
      }

      if (!payload.submitted?.length) {
        throw new Error("Analysis did not return any results.")
      }

      setStep2Progress(100)
      setStep3Progress(100)
      setCompletionMessage("✓ AI analysis complete! Opening results...")

      const analysisIds = payload.submitted.map((item) => item.analysis_id)
      router.push(
        `/results/${analysisIds[0]}?analysisIds=${encodeURIComponent(analysisIds.join(","))}`
      )
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to analyze uploaded files."
      )
      setStep2Progress(0)
      setStep3Progress(0)
      setCompletionMessage(null)
    } finally {
      setProgressLabel(null)
      setIsSubmitting(false)
    }
  }

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
              Upload infrastructure files and let the AI reviewer score risks, readiness, and architecture quality.
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Upload Area */}
            <div className="lg:col-span-2">
              <div className="space-y-6">
                <Dropzone
                  disabled={isSubmitting}
                  onFilesChange={setSelectedFiles}
                  progressValue={progressLabel ? (step2Progress > 0 ? step2Progress : step1Progress) : 0}
                  progressLabel={progressLabel}
                  completionMessage={completionMessage}
                  errorMessage={errorMessage}
                />

                <div className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">
                      Ready to analyze
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {selectedFiles.length > 0
                        ? `${selectedFiles.length} file${selectedFiles.length === 1 ? "" : "s"} selected for AI-powered review.`
                        : "Upload one or more supported files to start AI analysis."}
                    </p>
                  </div>
                  <Button onClick={handleAnalyze} disabled={selectedFiles.length === 0 || isSubmitting}>
                    {isSubmitting ? "AI Analyzing..." : "Analyze with AI"}
                  </Button>
                </div>
              </div>
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
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-slate-400" />
                    <span>Dockerfile</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-slate-400" />
                    <span>GitHub Actions (.yaml, .yml)</span>
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
                    <Progress value={step1Progress || (selectedFiles.length > 0 ? 100 : 0)} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold mb-1">Step 2: Analyze</p>
                    <Progress value={step2Progress} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold mb-1">Step 3: Results</p>
                    <Progress value={step3Progress} />
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
