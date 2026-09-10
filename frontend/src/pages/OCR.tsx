import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ocrService } from '@/services/fieldmind'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileUpload } from '@/components/ui/file-upload'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { Progress } from '@/components/ui/progress'
import { EmptyState } from '@/components/ui/empty-state'
import { Tabs } from '@/components/ui/tabs'
import { ScanText, Upload, FileText, CheckCircle, XCircle, Clock, Download, Eye } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

export default function OCR() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)
  const { toast } = useToast()

  const [activeTab, setActiveTab] = useState('upload')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [ocrLanguage, setOcrLanguage] = useState('zh-CN')

  const queryClient = useQueryClient()

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['projects', projectId, 'ocr-tasks'],
    queryFn: () => ocrService.getTasks(projectId),
    enabled: !!projectId,
  })

  const createOCRTask = useMutation({
    mutationFn: (data: any) => ocrService.process(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'ocr-tasks'] }),
  })

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast({
        title: '请选择文件',
        description: '请至少选择一个文件进行 OCR',
        variant: 'destructive',
      })
      return
    }

    try {
      const formData = new FormData()
      selectedFiles.forEach((file) => {
        formData.append('files', file)
      })
      formData.append('language', ocrLanguage)

      await createOCRTask.mutateAsync(formData)
      setSelectedFiles([])
      setActiveTab('tasks')
      toast({
        title: 'OCR 任务已创建',
        description: `已提交 ${selectedFiles.length} 个文件进行识别`,
      })
    } catch (error) {
      toast({
        title: '上传失败',
        description: '无法创建 OCR 任务，请重试',
        variant: 'destructive',
      })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'processing':
        return 'bg-blue-100 text-blue-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'processing':
        return <Spinner size="sm" />
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-600" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />
      default:
        return <FileText className="h-5 w-5 text-gray-600" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '已完成'
      case 'processing':
        return '处理中'
      case 'pending':
        return '等待中'
      case 'failed':
        return '失败'
      default:
        return status
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <ScanText className="h-8 w-8 text-[#27768A]" />
            OCR 文字识别
          </h1>
          <p className="text-gray-600 mt-1">智能图像文字识别和提取</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="border-b border-gray-200">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('upload')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'upload'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              上传文件
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'tasks'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              识别任务
            </button>
          </div>
        </div>

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="mt-6">
            <Card className="p-8">
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-4">上传图像文件</h3>
                  <FileUpload
                    accept="image/*,.pdf"
                    multiple
                    onChange={setSelectedFiles}
                    maxSize={50 * 1024 * 1024} // 50MB
                  />
                  <p className="text-sm text-gray-500 mt-2">
                    支持 JPG, PNG, PDF 格式，单个文件最大 50MB
                  </p>
                </div>

                {selectedFiles.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">已选择文件 ({selectedFiles.length})</h4>
                    <div className="space-y-2">
                      {selectedFiles.map((file, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <FileText className="h-5 w-5 text-gray-400" />
                            <div>
                              <p className="text-sm font-medium">{file.name}</p>
                              <p className="text-xs text-gray-500">
                                {(file.size / 1024 / 1024).toFixed(2)} MB
                              </p>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setSelectedFiles(selectedFiles.filter((_, i) => i !== index))
                            }
                          >
                            移除
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium mb-2">识别语言</label>
                  <select
                    value={ocrLanguage}
                    onChange={(e) => setOcrLanguage(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="zh-CN">简体中文</option>
                    <option value="zh-TW">繁体中文</option>
                    <option value="en">英文</option>
                    <option value="ja">日文</option>
                    <option value="ko">韩文</option>
                    <option value="auto">自动检测</option>
                  </select>
                </div>

                <Button
                  onClick={handleUpload}
                  disabled={selectedFiles.length === 0 || createOCRTask.isPending}
                  className="w-full"
                  size="lg"
                >
                  {createOCRTask.isPending ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      上传中...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      开始 OCR 识别
                    </>
                  )}
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Tasks Tab */}
        {activeTab === 'tasks' && (
          <div className="mt-6">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <Spinner size="lg" />
              </div>
            ) : !tasks || tasks.length === 0 ? (
              <EmptyState
                icon={ScanText}
                title="没有 OCR 任务"
                description="上传图像文件开始进行文字识别"
                action={{
                  label: '上传文件',
                  onClick: () => setActiveTab('upload'),
                }}
              />
            ) : (
              <div className="space-y-4">
                {tasks.map((task: any) => (
                  <Card key={task.id} className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-4 flex-1">
                        {getStatusIcon(task.status)}
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-semibold">{task.filename}</h3>
                            <Badge className={getStatusColor(task.status)}>
                              {getStatusText(task.status)}
                            </Badge>
                          </div>

                          <div className="space-y-2">
                            <p className="text-sm text-gray-600">
                              创建时间: {new Date(task.created_at).toLocaleString('zh-CN')}
                            </p>

                            {task.status === 'processing' && task.progress !== undefined && (
                              <div>
                                <div className="flex items-center justify-between text-sm mb-1">
                                  <span className="text-gray-600">识别进度</span>
                                  <span className="font-medium">{task.progress}%</span>
                                </div>
                                <Progress value={task.progress} />
                              </div>
                            )}

                            {task.status === 'completed' && (
                              <div className="grid grid-cols-3 gap-4 mt-3">
                                <div>
                                  <p className="text-xs text-gray-500">识别字符</p>
                                  <p className="text-sm font-semibold">
                                    {task.characters_count?.toLocaleString() || 0}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-xs text-gray-500">置信度</p>
                                  <p className="text-sm font-semibold">
                                    {task.confidence ? `${task.confidence.toFixed(1)}%` : 'N/A'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-xs text-gray-500">耗时</p>
                                  <p className="text-sm font-semibold">
                                    {task.processing_time || 'N/A'}
                                  </p>
                                </div>
                              </div>
                            )}

                            {task.status === 'failed' && task.error && (
                              <div className="mt-2 p-3 bg-red-50 rounded-lg">
                                <p className="text-sm text-red-800">{task.error}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {task.status === 'completed' && (
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4 mr-2" />
                            查看
                          </Button>
                          <Button variant="outline" size="sm">
                            <Download className="h-4 w-4 mr-2" />
                            下载
                          </Button>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </Tabs>
    </div>
  )
}
