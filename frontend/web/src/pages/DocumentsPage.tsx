import React, { useState, useRef, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import FactStatementsViewer from '../components/FactStatementsViewer';
import BatchProcessPanel from '../components/BatchProcessPanel';
import { useAppContext } from '../contexts/AppContext';

const DocumentsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [uploading, setUploading] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [showBatchPanel, setShowBatchPanel] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const { triggerRefresh, setLastUploadedFileId } = useAppContext();

  const { data: documentsData, isLoading } = useQuery({
    queryKey: ['documents', projectId],
    queryFn: () => api.documents.list(Number(projectId)),
  });

  // 自动轮询：检查是否有处理中的文档，如果有则每3秒刷新一次
  useEffect(() => {
    const documents = documentsData?.documents || [];
    const hasProcessing = documents.some((doc: any) => doc.status === 'processing');

    if (hasProcessing) {
      const interval = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [documentsData, projectId, queryClient]);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      return api.documents.upload(Number(projectId), file);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });

      // 🎯 触发全局刷新 - 通知看板页、图谱页更新
      triggerRefresh();

      // 记录最后上传的文件ID
      if (data?.id) {
        setLastUploadedFileId(data.id);
      }

      setUploading(false);
      console.log('[DocumentsPage] 文档上传成功，已触发全局刷新');
    },
    onError: () => {
      setUploading(false);
      alert('上传失败，请重试');
    },
  });

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    for (let i = 0; i < files.length; i++) {
      await uploadMutation.mutateAsync(files[i]);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    for (let i = 0; i < files.length; i++) {
      await uploadMutation.mutateAsync(files[i]);
    }
  };

  const documents = documentsData?.documents || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部 */}
      <div className="bg-white shadow">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to={`/projects/${projectId}`}
                className="text-gray-600 hover:text-gray-900"
              >
                ← 返回项目
              </Link>
              <div className="h-6 w-px bg-gray-300" />
              <h1 className="text-2xl font-bold">📚 材料库</h1>
            </div>
            {/* 批量处理按钮 */}
            {documents.length > 0 && (
              <button
                onClick={() => setShowBatchPanel(!showBatchPanel)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                {showBatchPanel ? '隐藏批量处理' : '📦 批量处理'}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* 批量处理面板 */}
        {showBatchPanel && (
          <div className="mb-8">
            <BatchProcessPanel
              projectId={Number(projectId)}
              onComplete={() => {
                queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
                triggerRefresh();
              }}
            />
          </div>
        )}
        {/* 上传区域 */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="bg-white rounded-xl shadow-md p-8 mb-8 border-2 border-dashed border-gray-300 hover:border-indigo-500 transition-colors cursor-pointer"
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="text-center">
            <svg
              className="w-16 h-16 mx-auto text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <h3 className="text-xl font-semibold mb-2">
              {uploading ? '上传中...' : '点击或拖拽上传文档'}
            </h3>
            <p className="text-gray-600">
              支持 PDF, DOCX, PPTX, XLSX, TXT, MD, HTML, CSV, JSON, XML 等14种格式
            </p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            accept=".pdf,.docx,.doc,.pptx,.xlsx,.txt,.md,.html,.csv,.json,.xml"
          />
        </div>

        {/* 文档列表 */}
        {isLoading ? (
          <div className="text-center py-8">
            <div className="text-gray-600">加载中...</div>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-16">
            <svg
              className="w-24 h-24 mx-auto text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="text-xl text-gray-600 mb-4">还没有文档</h3>
            <p className="text-gray-500">上传您的研究资料开始使用</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    文档名称
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    类型
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    大小
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    字数
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    上传时间
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc: any) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {doc.filename}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        {doc.file_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          doc.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : doc.status === 'processing'
                            ? 'bg-yellow-100 text-yellow-800'
                            : doc.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {doc.status === 'completed'
                          ? '已完成'
                          : doc.status === 'processing'
                          ? '处理中'
                          : doc.status === 'failed'
                          ? '失败'
                          : '待处理'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {doc.word_count?.toLocaleString() || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedDocumentId(doc.id)}
                        className="text-indigo-600 hover:text-indigo-900 font-medium"
                      >
                        查看详情
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 详情模态框 */}
      {selectedDocumentId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-2xl font-bold">文档详情</h2>
              <button
                onClick={() => setSelectedDocumentId(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <FactStatementsViewer documentId={selectedDocumentId} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentsPage;
