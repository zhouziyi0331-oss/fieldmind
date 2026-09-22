/**
 * 批量处理面板 - 支持v2架构选择
 * 让用户可以选择使用legacy或v2的6-Agent架构处理文档
 */
import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

interface BatchProcessPanelProps {
  projectId: number;
  documentIds?: number[];
  onComplete?: () => void;
}

const BatchProcessPanel: React.FC<BatchProcessPanelProps> = ({
  projectId,
  documentIds,
  onComplete
}) => {
  const [useV2Architecture, setUseV2Architecture] = useState(true); // 默认使用v2
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const queryClient = useQueryClient();

  const processMutation = useMutation({
    mutationFn: async () => {
      if (documentIds && documentIds.length > 0) {
        // 批量处理指定文档
        return api.batch.processDocuments({
          document_ids: documentIds,
          force_reprocess: false,
          use_v2_architecture: useV2Architecture
        });
      } else {
        // 处理整个项目
        return api.batch.processProject({
          project_id: projectId,
          force_reprocess: false,
          use_v2_architecture: useV2Architecture
        });
      }
    },
    onSuccess: (data) => {
      setResult(data);
      setProcessing(false);

      // 刷新相关数据
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });

      if (onComplete) {
        onComplete();
      }
    },
    onError: (error: any) => {
      console.error('批量处理失败:', error);
      setResult({ error: error.message });
      setProcessing(false);
    }
  });

  const handleProcess = async () => {
    setProcessing(true);
    setResult(null);
    processMutation.mutate();
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">📦 批量处理</h3>

      {/* 架构选择 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          处理架构
        </label>
        <div className="space-y-3">
          {/* V2 架构选项 */}
          <label className="flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all hover:bg-blue-50 hover:border-blue-300"
            style={{ borderColor: useV2Architecture ? '#3b82f6' : '#e5e7eb' }}>
            <input
              type="radio"
              checked={useV2Architecture}
              onChange={() => setUseV2Architecture(true)}
              className="mt-1 mr-3"
            />
            <div className="flex-1">
              <div className="font-semibold text-gray-900 flex items-center gap-2">
                🚀 V2架构（6-Agent）
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">推荐</span>
              </div>
              <div className="text-sm text-gray-600 mt-1">
                完整流程：分块 → 向量化 → 知识图谱 → Skills自动分析
              </div>
              <div className="text-xs text-gray-500 mt-2">
                ✓ 真实数据流通 &nbsp; ✓ 自动Skills分析 &nbsp; ✓ 完整知识图谱
              </div>
            </div>
          </label>

          {/* Legacy 架构选项 */}
          <label className="flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all hover:bg-gray-50"
            style={{ borderColor: !useV2Architecture ? '#3b82f6' : '#e5e7eb' }}>
            <input
              type="radio"
              checked={!useV2Architecture}
              onChange={() => setUseV2Architecture(false)}
              className="mt-1 mr-3"
            />
            <div className="flex-1">
              <div className="font-semibold text-gray-900">
                📁 Legacy架构
              </div>
              <div className="text-sm text-gray-600 mt-1">
                传统流程：异步后台处理，向量化存储
              </div>
              <div className="text-xs text-gray-500 mt-2">
                ✓ 稳定可靠 &nbsp; ✓ 向后兼容
              </div>
            </div>
          </label>
        </div>
      </div>

      {/* 处理信息 */}
      <div className="mb-4 p-3 bg-gray-50 rounded text-sm text-gray-700">
        {documentIds && documentIds.length > 0 ? (
          <div>
            📄 将处理 <strong>{documentIds.length}</strong> 个文档
          </div>
        ) : (
          <div>
            📚 将处理项目中的所有文档
          </div>
        )}
        {useV2Architecture && (
          <div className="mt-2 text-blue-600">
            ⚡ 使用v2架构将自动执行：分块、向量化、知识图谱、Skills分析
          </div>
        )}
      </div>

      {/* 执行按钮 */}
      <button
        onClick={handleProcess}
        disabled={processing}
        className={`w-full py-3 px-4 rounded-lg font-semibold transition-all ${
          processing
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {processing ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            处理中...
          </span>
        ) : (
          '开始处理'
        )}
      </button>

      {/* 结果显示 */}
      {result && (
        <div className={`mt-4 p-4 rounded-lg ${
          result.error ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'
        }`}>
          {result.error ? (
            <>
              <div className="font-semibold text-red-700 mb-2">❌ 处理失败</div>
              <div className="text-sm text-red-600">{result.error}</div>
            </>
          ) : (
            <>
              <div className="font-semibold text-green-700 mb-2">✅ 处理完成</div>

              {/* V2架构结果 */}
              {useV2Architecture && result.results && (
                <div className="text-sm text-gray-700 space-y-2">
                  <div className="flex justify-between">
                    <span>成功:</span>
                    <span className="font-semibold text-green-600">{result.results.success}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>失败:</span>
                    <span className="font-semibold text-red-600">{result.results.failed}</span>
                  </div>
                  {result.results.total_processing_time && (
                    <div className="flex justify-between">
                      <span>总耗时:</span>
                      <span className="font-semibold">{result.results.total_processing_time.toFixed(2)}秒</span>
                    </div>
                  )}
                </div>
              )}

              {/* Legacy架构结果 */}
              {!useV2Architecture && (
                <div className="text-sm text-gray-700">
                  后台任务已提交，请等待处理完成
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default BatchProcessPanel;
