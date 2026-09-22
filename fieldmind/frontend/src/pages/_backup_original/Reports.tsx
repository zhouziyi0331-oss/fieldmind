import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useReports, useGenerateReport, useReport } from '@/hooks/useFieldMind'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { EmptyState } from '@/components/ui/empty-state'
import { FileText, Download, Eye, Trash2, Plus, TrendingUp } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const REPORT_TYPES = [
  { value: 'summary', label: '项目摘要报告' },
  { value: 'analysis', label: '深度分析报告' },
  { value: 'quality', label: '数据质量报告' },
  { value: 'insights', label: '洞察发现报告' },
  { value: 'timeline', label: '时间线报告' },
  { value: 'citation', label: '引用分析报告' },
]

export default function Reports() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)

  const { data: reportsData, isLoading } = useReports(projectId)
  const generateReport = useGenerateReport()

  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false)
  const [selectedType, setSelectedType] = useState('summary')
  const [previewReportId, setPreviewReportId] = useState<number | null>(null)

  const reports = reportsData?.data || []

  const handleGenerate = async () => {
    try {
      await generateReport.mutateAsync({
        projectId,
        type: selectedType,
      })
      setIsGenerateDialogOpen(false)
    } catch (error) {
      console.error('Failed to generate report:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, any> = {
      completed: 'success',
      processing: 'warning',
      failed: 'error',
      pending: 'default',
    }
    const labels: Record<string, string> = {
      completed: '已完成',
      processing: '生成中',
      failed: '失败',
      pending: '等待中',
    }
    return (
      <Badge variant={variants[status] || 'default'}>
        {labels[status] || status}
      </Badge>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">报告管理</h1>
          <p className="text-text-secondary mt-1">生成和管理项目分析报告</p>
        </div>

        <Dialog open={isGenerateDialogOpen} onOpenChange={setIsGenerateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              生成报告
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>生成新报告</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium text-text-primary mb-2 block">
                  报告类型
                </label>
                <Select value={selectedType} onValueChange={setSelectedType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {REPORT_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsGenerateDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleGenerate} loading={generateReport.isPending}>
                生成
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card hover>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              报告总数
            </CardTitle>
            <FileText className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">{reports.length}</div>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              已完成
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-success">
              {reports.filter((r: any) => r.status === 'completed').length}
            </div>
          </CardContent>
        </Card>

        <Card hover>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              生成中
            </CardTitle>
            <Spinner className="h-4 w-4" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-warning">
              {reports.filter((r: any) => r.status === 'processing').length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 报告列表 */}
      <Card>
        <CardHeader>
          <CardTitle>报告列表</CardTitle>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <EmptyState
              icon={<FileText className="h-16 w-16" />}
              title="暂无报告"
              description="点击上方按钮生成您的第一份报告"
              action={
                <Button onClick={() => setIsGenerateDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  生成报告
                </Button>
              }
            />
          ) : (
            <div className="space-y-3">
              {reports.map((report: any, index: number) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between p-4 border border-border rounded-lg hover:border-primary transition-all animate-slide-in-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <FileText className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-text-primary truncate">
                        {REPORT_TYPES.find((t) => t.value === report.type)?.label ||
                          report.type}
                      </h3>
                      <p className="text-sm text-text-secondary">
                        生成于{' '}
                        {formatDistanceToNow(new Date(report.created_at), {
                          addSuffix: true,
                          locale: zhCN,
                        })}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {getStatusBadge(report.status)}
                    {report.status === 'completed' && (
                      <>
                        <Button variant="ghost" size="icon">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon">
                          <Download className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                    <Button variant="ghost" size="icon">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
