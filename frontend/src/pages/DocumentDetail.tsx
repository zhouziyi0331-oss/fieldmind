import { useState } from 'react'
import { documentAPI } from '@/services/fieldmind-api';
import { useParams, useNavigate } from 'react-router-dom'
import { useDocument } from '@/hooks/useFieldMind'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { Tabs } from '@/components/ui/tabs'
import { FileText, Download, Share2, Edit, Trash2, ChevronLeft, FileType, Calendar, User } from 'lucide-react'

export default function DocumentDetail() {
  const { id, docId } = useParams<{ id: string; docId: string }>()
  const navigate = useNavigate()
  const projectId = Number(id)
  const documentId = Number(docId)

  const [activeTab, setActiveTab] = useState('content')

  const { data: document, isLoading } = useDocument(projectId, documentId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!document) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">文档不存在</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate(`/projects/${projectId}/documents`)}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{document.filename}</h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <FileType className="h-4 w-4" />
                <span>{document.file_type}</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>{new Date(document.created_at).toLocaleDateString('zh-CN')}</span>
              </div>
              <div className="flex items-center gap-1">
                <User className="h-4 w-4" />
                <span>{document.uploaded_by || '未知'}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline">
            <Share2 className="h-4 w-4 mr-2" />
            分享
          </Button>
          <Button variant="outline">
            <Edit className="h-4 w-4 mr-2" />
            编辑
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            下载
          </Button>
          <Button variant="outline" className="text-red-600 hover:text-red-700">
            <Trash2 className="h-4 w-4 mr-2" />
            删除
          </Button>
        </div>
      </div>

      {/* Status and Metadata */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-gray-600">状态</p>
          <Badge className="mt-2 bg-green-100 text-green-800">
            {document.status === 'completed' ? '已完成' : '处理中'}
          </Badge>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">文件大小</p>
          <p className="text-lg font-semibold mt-1">
            {((document.file_size || 0) / 1024 / 1024).toFixed(2)} MB
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">页数</p>
          <p className="text-lg font-semibold mt-1">{document.page_count || 'N/A'}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">提取实体</p>
          <p className="text-lg font-semibold mt-1">{document.entities_count || 0}</p>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="border-b border-gray-200">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('content')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'content'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              内容
            </button>
            <button
              onClick={() => setActiveTab('entities')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'entities'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              实体
            </button>
            <button
              onClick={() => setActiveTab('metadata')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'metadata'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              元数据
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'history'
                  ? 'border-[#27768A] text-[#27768A]'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              历史记录
            </button>
          </div>
        </div>

        {/* Content Tab */}
        {activeTab === 'content' && (
          <div className="mt-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">文档内容</h3>
              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {document.content || '文档内容暂不可用'}
                </p>
              </div>
            </Card>
          </div>
        )}

        {/* Entities Tab */}
        {activeTab === 'entities' && (
          <div className="mt-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">提取的实体</h3>
              <div className="space-y-4">
                {document.entities && document.entities.length > 0 ? (
                  document.entities.map((entity: any, index: number) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium">{entity.text}</p>
                        <p className="text-sm text-gray-500">{entity.type}</p>
                      </div>
                      <Badge>{entity.confidence ? `${(entity.confidence * 100).toFixed(0)}%` : 'N/A'}</Badge>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-8">暂无实体数据</p>
                )}
              </div>
            </Card>
          </div>
        )}

        {/* Metadata Tab */}
        {activeTab === 'metadata' && (
          <div className="mt-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">文档元数据</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">文件名</p>
                  <p className="font-medium mt-1">{document.filename}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">文件类型</p>
                  <p className="font-medium mt-1">{document.file_type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">上传时间</p>
                  <p className="font-medium mt-1">
                    {new Date(document.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">最后更新</p>
                  <p className="font-medium mt-1">
                    {new Date(document.updated_at || document.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">文件路径</p>
                  <p className="font-medium mt-1 text-xs break-all">{document.file_path || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">处理状态</p>
                  <p className="font-medium mt-1">{document.status}</p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="mt-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">操作历史</h3>
              <div className="space-y-4">
                <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="h-2 w-2 bg-blue-600 rounded-full mt-2"></div>
                  <div className="flex-1">
                    <p className="font-medium">文档上传</p>
                    <p className="text-sm text-gray-600">
                      {new Date(document.created_at).toLocaleString('zh-CN')}
                    </p>
                  </div>
                </div>
                {document.processed_at && (
                  <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                    <div className="h-2 w-2 bg-green-600 rounded-full mt-2"></div>
                    <div className="flex-1">
                      <p className="font-medium">处理完成</p>
                      <p className="text-sm text-gray-600">
                        {new Date(document.processed_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        )}
      </Tabs>
    </div>
  )
}
