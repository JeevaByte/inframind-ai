"use client"

import { Upload, File } from "lucide-react"
import { useState, useRef } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

interface DropzoneProps {
  onFilesChange?: (files: File[]) => void
  progressValue?: number
  progressLabel?: string | null
  completionMessage?: string | null
  errorMessage?: string | null
  disabled?: boolean
}

export function Dropzone({
  onFilesChange,
  progressValue = 0,
  progressLabel,
  completionMessage,
  errorMessage,
  disabled = false,
}: DropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDragEnter = (e: React.DragEvent) => {
    if (disabled) {
      return
    }
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
    if (disabled) {
      return
    }
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

    if (newUniqueFiles.length === 0) {
      return
    }

    const nextFiles = [...uploadedFiles, ...newUniqueFiles]
    setUploadedFiles(nextFiles)
    onFilesChange?.(nextFiles)
  }

  return (
    <div className="space-y-6">
      <Card
        className={cn(
          "border-2 border-dashed transition-colors cursor-pointer",
          disabled && "cursor-not-allowed opacity-70",
          isDragActive
            ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
            : "border-slate-300 dark:border-slate-700"
        )}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (disabled) {
            return
          }
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
            disabled={disabled}
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

          {progressValue > 0 && progressValue < 100 && progressLabel && (
            <div className="space-y-2">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {progressLabel} {Math.round(progressValue)}%
              </p>
              <Progress value={progressValue} role="progressbar" aria-valuenow={progressValue} aria-valuemin={0} aria-valuemax={100} />
            </div>
          )}

          {completionMessage && (
            <p className="text-sm text-green-600 dark:text-green-400" role="status">
              {completionMessage}
            </p>
          )}

          {errorMessage && (
            <p className="text-sm text-red-600 dark:text-red-400" role="alert">
              {errorMessage}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
