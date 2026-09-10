import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useDocuments, useUploadDocument, useDeleteDocument } from '@/hooks/useFieldMind'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { EmptyState } from '@/components/ui/empty-state'
import { FileUpload } from '@/components/ui/file-upload'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Trash2, FileText, Upload, Search, Grid3x3, List, Download, Eye } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

type ViewMode = 'table' | 'grid'

export default function Documents() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)

  const { data: documentsData, isLoading } = useDocuments(projectId)
  const uploadDocument = useUploadDocument()
  const deleteDocument = useDeleteDocument()

  const [viewMode, setViewMode] = useState<ViewMode>('table')
  const [searchQuery, setSearchQuery] = useState('')

  const handleUpload = async (file: File, onProgress: (progress: number) => void) => {
    return new Promise<void>((resolve, reject) => {
      // 模拟上传进度
      let progress = 0
      const interval = setInterval(() => {
        progress += Math.random() * 15
        if (progress > 100) progress = 100
        onProgress(progress)

        if (progress >= 100) {
          clearInterval(interval)
          // 实际上传
          uploadDocument
            .mutateAsync({ projectId, file })
            .then(() => resolve())
            .catch((error) => reject(error))
        }
      }, 200)
    })
  }

  const handleDelete = async (documentId: number) => {
    if (confirm('确定要删除这个文档吗？')) {
      await deleteDocument.mutateAsync({ projectId, documentId })
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const documents = documentsData?.data || []
  const filteredDocuments = documents.filter(doc =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-text-primary">文档管理</h1>
        <p className="text-text-secondary mt-1">上传和管理项目文档</p>
      </div>

      {/* 文件上传区域 */}
      <Card className="animate-slide-in-up">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            上传文档
          </CardTitle>
        </CardHeader>
        <CardContent>
          <FileUpload onUpload={handleUpload} />
        </CardContent>
      </Card>

      {/* 工具栏 */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
        {/* 搜索框 */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-text-tertiary" />
          <Input
            placeholder="搜索文档..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* 视图切换 */}
        <div className="flex gap-2">
          <Button
            variant={viewMode === 'table' ? 'primary' : 'outline'}
            size="icon"
            onClick={() => setViewMode('table')}
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'grid' ? 'primary' : 'outline'}
            size="icon"
            onClick={() => setViewMode('grid')}
          >
            <Grid3x3 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 文档列表 */}
      <Card className="animate-slide-in-up" style={{ animationDelay: '200ms' }}>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>文档列表 ({filteredDocuments.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredDocuments.length === 0 ? (
            <EmptyState
              icon={<FileText className="h-16 w-16" />}
              title={searchQuery ? '未找到匹配的文档' : '暂无文档'}
              description={
                searchQuery
                  ? '尝试使用其他关键词搜索'
                  : '上传您的第一个文档开始分析'
              }
            />
          ) : viewMode === 'table' ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>文件名</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>大小</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>上传时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDocuments.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-primary" />
                        {doc.filename}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{doc.file_type}</Badge>
                    </TableCell>
                    <TableCell>{formatFileSize(doc.file_size)}</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          doc.status === 'completed'
                            ? 'success'
                            : doc.status === 'processing'
                            ? 'warning'
                            : 'default'
                        }
                      >
                        {doc.status === 'completed'
                          ? '已完成'
                          : doc.status === 'processing'
                          ? '处理中'
                          : '待处理'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-text-secondary">
                      {formatDistanceToNow(new Date(doc.created_at), {
                        addSuffix: true,
                        locale: zhCN,
                      })}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="ghost" size="icon">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon">
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(doc.id)}
                          disabled={deleteDocument.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredDocuments.map((doc, index) => (
                <Card
                  key={doc.id}
                  hover
                  className="animate-scale-in"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <FileText className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-text-primary truncate mb-1">
                          {doc.filename}
                        </h3>
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="text-xs">
                            {doc.file_type}
                          </Badge>
                          <span className="text-xs text-text-secondary">
                            {formatFileSize(doc.file_size)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <Badge
                            variant={
                              doc.status === 'completed'
                                ? 'success'
                                : doc.status === 'processing'
                                ? 'warning'
                                : 'default'
                            }
                            className="text-xs"
                          >
                            {doc.status === 'completed'
                              ? '已完成'
                              : doc.status === 'processing'
                              ? '处理中'
                              : '待处理'}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={() => handleDelete(doc.id)}
                            disabled={deleteDocument.isPending}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
