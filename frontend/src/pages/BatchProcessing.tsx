import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/services/api'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { Progress } from '@/components/ui/progress'
import { EmptyState } from '@/components/ui/empty-state'
import { Dialog } from '@/components/ui/dialog'
import { Checkbox } from '@/components/ui/checkbox'
import { Layers, Plus, PlayCircle, PauseCircle, StopCircle, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

export default function BatchProcessing() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)
  const { toast } = useToast()

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [selectedOperation, setSelectedOperation] = useState('extract_entities')
  const [selectedDocuments, setSelectedDocuments] = useState<number[]>([])

  const queryClient = useQueryClient()

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['projects', projectId, 'batch-jobs'],
    queryFn: () => apiClient.get(`/api/v1/projects/${projectId}/batch/jobs`),
    enabled: !!projectId,
  })

  const createBatchJob = useMutation({
    mutationFn: (data: any) => apiClient.post(`/api/v1/projects/${projectId}/batch/jobs`, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'batch-jobs'] }),
  })

  const cancelBatchJob = useMutation({
    mutationFn: (jobId: number) => apiClient.post(`/api/v1/projects/${projectId}/batch/jobs/${jobId}/cancel`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'batch-jobs'] }),
  })

  const operations = [
    { value: 'extract_entities', label: '实体提取', description: '批量提取文档中的实体' },
    { value: 'extract_relations', label: '关系提取', description: '批量提取实体间的关系' },
    { value: 'generate_summaries', label: '生成摘要', description: '为文档生成摘要' },
    { value: 'quality_check', label: '质量检查', description: '批量检查数据质量' },
    { value: 'reprocess', label: '重新处理', description: '重新处理选定文档' },
    { value: 'export', label: '导出数据', description: '批量导出处理结果' },
  ]

  const handleCreateJob = async () => {
    if (selectedDocuments.length === 0) {
      toast({
        title: '请选择文档',
        description: '至少选择一个文档进行批处理',
        variant: 'destructive',
      })
      return
    }

    try {
      await createBatchJob.mutateAsync({
        operation: selectedOperation,
        documentIds: selectedDocuments,
      })
      setIsCreateDialogOpen(false)
      setSelectedDocuments([])
      toast({
        title: '批处理任务已创建',
        description: `已创建 ${selectedOperation} 任务，处理 ${selectedDocuments.length} 个文档`,
      })
    } catch (error) {
      toast({
        title: '创建失败',
        description: '无法创建批处理任务，请重试',
        variant: 'destructive',
      })
    }
  }

  const handleCancelJob = async (jobId: number) => {
    try {
      await cancelBatchJob.mutateAsync(jobId)
      toast({
        title: '任务已取消',
        description: '批处理任务已成功取消',
      })
    } catch (error) {
      toast({
        title: '取消失败',
        description: '无法取消任务，请重试',
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
      case 'cancelled':
        return 'bg-gray-100 text-gray-800'
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
        return <PlayCircle className="h-5 w-5 text-yellow-600" />
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-600" />
      case 'cancelled':
        return <StopCircle className="h-5 w-5 text-gray-600" />
      default:
        return null
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
      case 'cancelled':
        return '已取消'
      default:
        return status
    }
  }

  const getOperationLabel = (operation: string) => {
    const op = operations.find((o) => o.value === operation)
    return op?.label || operation
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Layers className="h-8 w-8 text-[#27768A]" />
            批量处理
          </h1>
          <p className="text-gray-600 mt-1">批量处理文档和数据</p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          创建批处理任务
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6">
          <p className="text-sm text-gray-600">总任务数</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{jobs?.length || 0}</p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-gray-600">处理中</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">
            {jobs?.filter((j: any) => j.status === 'processing').length || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-gray-600">已完成</p>
          <p className="text-2xl font-bold text-green-600 mt-1">
            {jobs?.filter((j: any) => j.status === 'completed').length || 0}
          </p>
        </Card>
        <Card className="p-6">
          <p className="text-sm text-gray-600">失败</p>
          <p className="text-2xl font-bold text-red-600 mt-1">
            {jobs?.filter((j: any) => j.status === 'failed').length || 0}
          </p>
        </Card>
      </div>

      {/* Jobs List */}
      {!jobs || jobs.length === 0 ? (
        <EmptyState
          icon={Layers}
          title="没有批处理任务"
          description="创建第一个批处理任务开始批量处理数据"
          action={{
            label: '创建任务',
            onClick: () => setIsCreateDialogOpen(true),
          }}
        />
      ) : (
        <div className="space-y-4">
          {jobs.map((job: any) => (
            <Card key={job.id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-4 flex-1">
                  {getStatusIcon(job.status)}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold">{getOperationLabel(job.operation)}</h3>
                      <Badge className={getStatusColor(job.status)}>
                        {getStatusText(job.status)}
                      </Badge>
                    </div>

                    <div className="space-y-2">
                      <p className="text-sm text-gray-600">
                        创建时间: {new Date(job.created_at).toLocaleString('zh-CN')}
                      </p>

                      <div className="flex items-center gap-6 text-sm text-gray-600">
                        <span>总文档: {job.total_documents}</span>
                        <span>已处理: {job.processed_documents}</span>
                        {job.failed_documents > 0 && (
                          <span className="text-red-600">失败: {job.failed_documents}</span>
                        )}
                      </div>

                      {(job.status === 'processing' || job.status === 'pending') && (
                        <div>
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-gray-600">处理进度</span>
                            <span className="font-medium">
                              {Math.round((job.processed_documents / job.total_documents) * 100)}%
                            </span>
                          </div>
                          <Progress
                            value={(job.processed_documents / job.total_documents) * 100}
                          />
                        </div>
                      )}

                      {job.status === 'completed' && job.duration && (
                        <p className="text-sm text-gray-600">
                          耗时: {job.duration}
                        </p>
                      )}

                      {job.status === 'failed' && job.error && (
                        <div className="mt-2 p-3 bg-red-50 rounded-lg">
                          <p className="text-sm text-red-800">{job.error}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  {(job.status === 'processing' || job.status === 'pending') && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCancelJob(job.id)}
                    >
                      <StopCircle className="h-4 w-4 mr-2" />
                      取消
                    </Button>
                  )}
                  <Button variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    重试
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Job Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">创建批处理任务</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">处理操作</label>
              <select
                value={selectedOperation}
                onChange={(e) => setSelectedOperation(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
              >
                {operations.map((op) => (
                  <option key={op.value} value={op.value}>
                    {op.label} - {op.description}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">选择文档</label>
              <div className="border rounded-md p-4 max-h-64 overflow-y-auto">
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map((docId) => (
                    <label key={docId} className="flex items-center gap-2 cursor-pointer">
                      <Checkbox
                        checked={selectedDocuments.includes(docId)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setSelectedDocuments([...selectedDocuments, docId])
                          } else {
                            setSelectedDocuments(selectedDocuments.filter((id) => id !== docId))
                          }
                        }}
                      />
                      <span className="text-sm">文档 {docId}.pdf</span>
                    </label>
                  ))}
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                已选择 {selectedDocuments.length} 个文档
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              取消
            </Button>
            <Button
              onClick={handleCreateJob}
              disabled={selectedDocuments.length === 0 || createBatchJob.isPending}
            >
              {createBatchJob.isPending ? <Spinner size="sm" className="mr-2" /> : null}
              创建任务
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
