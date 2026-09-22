import * as React from "react"
import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, X, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Progress } from "./progress"
import { Button } from "./button"
import { motion, AnimatePresence } from "framer-motion"

export interface UploadFile {
  id: string
  file: File
  status: "waiting" | "uploading" | "processing" | "success" | "error"
  progress: number
  speed?: string
  remaining?: string
  error?: string
  stage?: string
}

interface FileUploadProps {
  onUpload: (file: File, onProgress: (progress: number) => void) => Promise<void>
  accept?: Record<string, string[]>
  maxSize?: number
  maxFiles?: number
  disabled?: boolean
  className?: string
}

export function FileUpload({
  onUpload,
  accept = {
    "application/pdf": [".pdf"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "text/plain": [".txt"],
    "text/markdown": [".md"],
  },
  maxSize = 500 * 1024 * 1024, // 500MB
  maxFiles = 10,
  disabled = false,
  className,
}: FileUploadProps) {
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles: UploadFile[] = acceptedFiles.map((file) => ({
        id: `${file.name}-${Date.now()}-${Math.random()}`,
        file,
        status: "waiting",
        progress: 0,
      }))

      setUploadFiles((prev) => [...prev, ...newFiles])

      // 开始上传每个文件
      newFiles.forEach((uploadFile) => {
        handleUpload(uploadFile)
      })
    },
    [onUpload]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxSize,
    maxFiles,
    disabled,
  })

  const handleUpload = async (uploadFile: UploadFile) => {
    const startTime = Date.now()

    setUploadFiles((prev) =>
      prev.map((f) =>
        f.id === uploadFile.id ? { ...f, status: "uploading", progress: 0 } : f
      )
    )

    try {
      await onUpload(uploadFile.file, (progress) => {
        const elapsed = (Date.now() - startTime) / 1000 // 秒
        const uploadedBytes = (uploadFile.file.size * progress) / 100
        const speed = uploadedBytes / elapsed // bytes/s
        const remaining = ((uploadFile.file.size - uploadedBytes) / speed) || 0

        setUploadFiles((prev) =>
          prev.map((f) =>
            f.id === uploadFile.id
              ? {
                  ...f,
                  progress,
                  speed: formatSpeed(speed),
                  remaining: formatTime(remaining),
                }
              : f
          )
        )
      })

      // 上传完成，进入处理阶段
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: "processing", progress: 100, stage: "文件解析中..." }
            : f
        )
      )

      // 模拟处理阶段
      await simulateProcessing(uploadFile.id)

      // 完成
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id ? { ...f, status: "success" } : f
        )
      )
    } catch (error) {
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: "error", error: error instanceof Error ? error.message : "上传失败" }
            : f
        )
      )
    }
  }

  const simulateProcessing = async (fileId: string) => {
    const stages = ["文件解析中...", "内容提取中...", "索引构建中..."]
    for (const stage of stages) {
      setUploadFiles((prev) =>
        prev.map((f) => (f.id === fileId ? { ...f, stage } : f))
      )
      await new Promise((resolve) => setTimeout(resolve, 1000))
    }
  }

  const removeFile = (fileId: string) => {
    setUploadFiles((prev) => prev.filter((f) => f.id !== fileId))
  }

  const retryUpload = (uploadFile: UploadFile) => {
    handleUpload(uploadFile)
  }

  return (
    <div className={cn("w-full space-y-4", className)}>
      {/* 上传区域 */}
      <div
        {...getRootProps()}
        className={cn(
          "relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary hover:bg-surface-hover",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-primary mb-4" />
        <p className="text-lg font-medium text-text-primary mb-2">
          {isDragActive ? "放开以上传文件" : "拖拽文件到这里"}
        </p>
        <p className="text-sm text-text-secondary mb-4">或点击选择文件</p>
        <p className="text-xs text-text-tertiary">
          支持: PDF, Word, TXT, Markdown | 最大: {Math.round(maxSize / (1024 * 1024))}MB
        </p>
      </div>

      {/* 上传队列 */}
      {uploadFiles.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-text-primary">
              上传队列 ({uploadFiles.length})
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setUploadFiles([])}
              disabled={uploadFiles.some((f) => f.status === "uploading")}
            >
              清空列表
            </Button>
          </div>

          <AnimatePresence mode="popLayout">
            {uploadFiles.map((uploadFile) => (
              <motion.div
                key={uploadFile.id}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -100 }}
                className="border border-border rounded-lg p-4 bg-surface"
              >
                <div className="flex items-start gap-3">
                  {/* 图标 */}
                  <div className="flex-shrink-0">
                    {uploadFile.status === "waiting" && (
                      <FileText className="h-5 w-5 text-text-secondary" />
                    )}
                    {uploadFile.status === "uploading" && (
                      <Loader2 className="h-5 w-5 text-primary animate-spin" />
                    )}
                    {uploadFile.status === "processing" && (
                      <Loader2 className="h-5 w-5 text-info animate-spin" />
                    )}
                    {uploadFile.status === "success" && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 200, damping: 10 }}
                      >
                        <CheckCircle className="h-5 w-5 text-success" />
                      </motion.div>
                    )}
                    {uploadFile.status === "error" && (
                      <AlertCircle className="h-5 w-5 text-error" />
                    )}
                  </div>

                  {/* 内容 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium text-text-primary truncate">
                        {uploadFile.file.name}
                      </p>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 flex-shrink-0"
                        onClick={() => removeFile(uploadFile.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>

                    <p className="text-xs text-text-secondary mb-2">
                      {formatFileSize(uploadFile.file.size)}
                    </p>

                    {/* 上传中 */}
                    {uploadFile.status === "uploading" && (
                      <>
                        <Progress
                          value={uploadFile.progress}
                          className="mb-2"
                          indicatorClassName="bg-gradient-to-r from-primary to-info"
                        />
                        <div className="flex items-center justify-between text-xs text-text-secondary">
                          <span>上传中... {uploadFile.progress}%</span>
                          <span>
                            {uploadFile.speed} · 剩余 {uploadFile.remaining}
                          </span>
                        </div>
                      </>
                    )}

                    {/* 处理中 */}
                    {uploadFile.status === "processing" && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <div className="h-1 flex-1 bg-info/20 rounded-full overflow-hidden">
                            <motion.div
                              className="h-full bg-info"
                              animate={{ x: ["0%", "100%"] }}
                              transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                              style={{ width: "50%" }}
                            />
                          </div>
                        </div>
                        <p className="text-xs text-info animate-pulse-subtle">
                          {uploadFile.stage}
                        </p>
                      </div>
                    )}

                    {/* 成功 */}
                    {uploadFile.status === "success" && (
                      <p className="text-xs text-success">上传成功！</p>
                    )}

                    {/* 错误 */}
                    {uploadFile.status === "error" && (
                      <div className="space-y-2">
                        <p className="text-xs text-error">{uploadFile.error}</p>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => retryUpload(uploadFile)}
                        >
                          重试
                        </Button>
                      </div>
                    )}

                    {/* 等待中 */}
                    {uploadFile.status === "waiting" && (
                      <p className="text-xs text-text-secondary">等待上传...</p>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}

// 辅助函数
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + " B"
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB"
  return (bytes / (1024 * 1024)).toFixed(2) + " MB"
}

function formatSpeed(bytesPerSecond: number): string {
  if (bytesPerSecond < 1024) return bytesPerSecond.toFixed(0) + " B/s"
  if (bytesPerSecond < 1024 * 1024)
    return (bytesPerSecond / 1024).toFixed(2) + " KB/s"
  return (bytesPerSecond / (1024 * 1024)).toFixed(2) + " MB/s"
}

function formatTime(seconds: number): string {
  if (seconds < 60) return Math.round(seconds) + " 秒"
  if (seconds < 3600) return Math.round(seconds / 60) + " 分钟"
  return Math.round(seconds / 3600) + " 小时"
}
