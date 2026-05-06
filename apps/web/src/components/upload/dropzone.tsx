"use client"

import { Upload, File } from "lucide-react"
import { useState, useRef, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

export function Dropzone() {
  const [isDragActive, setIsDragActive] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragActive(false)

    const droppedFiles = Array.from(e.dataTransfer.files)
    handleFiles(droppedFiles)
  }

  const handleFiles = (newFiles: File[]) => {
    const validFiles = newFiles.filter((file) => {
      const ext = file.name.split(".").pop()?.toLowerCase()
      return ["yaml", "yml", "json", "tf"].includes(ext || "")
    })

    // Deduplicate files based on name, size, and lastModified
    const existingFileKeys = new Set(
      uploadedFiles.map((f) => `${f.name}-${f.size}-${f.lastModified}`)
    )

    const newUniqueFiles = validFiles.filter(
      (file) =>
        !existingFileKeys.has(`${file.name}-${file.size}-${file.lastModified}`)
    )

    setUploadedFiles((prev) => [...prev, ...newUniqueFiles])

    if (newUniqueFiles.length > 0) {
      simulateUpload()
    }
  }

  const simulateUpload = () => {
    let progress = 0

    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    intervalRef.current = setInterval(() => {
      progress += Math.random() * 30
      if (progress >= 100) {
        progress = 100
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
      }
      setUploadProgress(progress)
    }, 300)
  }

  return (
    <div className="space-y-6">
      <Card
        className={cn(
          "border-2 border-dashed transition-colors cursor-pointer",
          isDragActive
            ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
            : "border-slate-300 dark:border-slate-700"
        )}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            inputRef.current?.click()
          }
        }}
        role="button"
        tabIndex={0}
      >
        <CardContent className="pt-12 pb-12 text-center">
          <Upload className="h-12 w-12 mx-auto mb-4 text-slate-400" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
            Drop files here or click to browse
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Supports Terraform, CloudFormation, Kubernetes YAML, and JSON files
          </p>
          <input
            ref={inputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => handleFiles(Array.from(e.target.files || []))}
            accept=".tf,.yaml,.yml,.json"
            aria-label="Upload infrastructure configuration files"
          />
        </CardContent>
      </Card>

      {uploadedFiles.length > 0 && (
        <div className="space-y-4" role="region" aria-live="polite" aria-label="Uploaded files list">
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white mb-3">
              Uploaded Files ({uploadedFiles.length})
            </h3>
            <div className="space-y-2">
              {uploadedFiles.map((file) => (
                <div
                  key={`${file.name}-${file.size}-${file.lastModified}`}
                  className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800"
                  role="listitem"
                >
                  <File className="h-5 w-5 text-blue-500" aria-hidden="true" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                      {file.name}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {uploadProgress > 0 && uploadProgress < 100 && (
            <div className="space-y-2">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Uploading... {Math.round(uploadProgress)}%
              </p>
              <Progress value={uploadProgress} role="progressbar" aria-valuenow={uploadProgress} aria-valuemin={0} aria-valuemax={100} />
            </div>
          )}

          {uploadProgress === 100 && (
            <p className="text-sm text-green-600 dark:text-green-400" role="status">
              ✓ Upload complete! Ready to analyze.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
