import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { AgentOrchestrationPanel, AgentExecutionMonitor, AgentResultsViewer } from '../components';
import {
  BarChart3,
  FileText,
  Sparkles,
  Download,
  Trash2,
  Play
} from 'lucide-react';

interface ExecutionHistory {
  id: string;
  timestamp: number;
  status: 'completed' | 'failed';
  result?: any;
  resultType?: 'knowledge' | 'search' | 'summary' | 'transcript';
  taskCount: number;
  duration?: number;
}

const AnalysisPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  // 统计数据查询
  const { data: stats } = useQuery({
    queryKey: ['project-stats', projectId],
    queryFn: () => api.projects.getStats(Number(projectId)),
  }) as { data: any };

  // 文档列表查询
  const { data: documentsData } = useQuery({
    queryKey: ['documents', projectId],
    queryFn: () => api.documents.list(Number(projectId)),
  }) as { data: { documents: any[] } | undefined };

  // Agent工作区状态
  const [activeTab, setActiveTab] = useState<'orchestration' | 'monitor' | 'results' | 'history'>('orchestration');
  const [agentExecutionId, setAgentExecutionId] = useState<string | null>(null);
  const [agentResult, setAgentResult] = useState<any>(null);
  const [agentResultType, setAgentResultType] = useState<'knowledge' | 'search' | 'summary' | 'transcript' | null>(null);
  const [executionHistory, setExecutionHistory] = useState<ExecutionHistory[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
  const [showStatsPanel, setShowStatsPanel] = useState(true);

  // Agent执行开始处理
  const handleAgentExecutionStart = (executionId: string) => {
    setAgentExecutionId(executionId);
    setAgentResult(null);
    setAgentResultType(null);
    setActiveTab('monitor');
  };

  // Agent执行完成处理
  const handleAgentComplete = (result: any) => {
    const startTime = Date.now();

    // 提取结果
    let finalResult = null;
    let finalResultType = null;
    let taskCount = 0;

    if (result?.result?.task_results && result.result.task_results.length > 0) {
      const firstTask = result.result.task_results[0];
      finalResult = firstTask.result;
      finalResultType = firstTask.agent_type as any;
      taskCount = result.result.task_results.length;
    }

    // 保存到历史
    const historyEntry: ExecutionHistory = {
      id: agentExecutionId || `exec-${Date.now()}`,
      timestamp: startTime,
      status: 'completed',
      result: finalResult,
      resultType: finalResultType,
      taskCount,
      duration: result?.duration_seconds
    };

    setExecutionHistory([historyEntry, ...executionHistory]);
    setAgentResult(finalResult);
    setAgentResultType(finalResultType);
    setAgentExecutionId(null);
    setActiveTab('results');
  };

  // Agent执行失败处理
  const handleAgentError = (error: any) => {
    console.error('Agent execution error:', error);

    if (agentExecutionId) {
      const historyEntry: ExecutionHistory = {
        id: agentExecutionId,
        timestamp: Date.now(),
        status: 'failed',
        taskCount: 0
      };
      setExecutionHistory([historyEntry, ...executionHistory]);
    }

    setAgentExecutionId(null);
    setActiveTab('orchestration');
  };

  // 从历史加载结果
  const loadHistoryResult = (entry: ExecutionHistory) => {
    if (entry.result && entry.resultType) {
      setAgentResult(entry.result);
      setAgentResultType(entry.resultType);
      setActiveTab('results');
    }
  };

  // 删除历史记录
  const deleteHistoryEntry = (id: string) => {
    setExecutionHistory(executionHistory.filter(e => e.id !== id));
  };

  // 清空历史
  const clearHistory = () => {
    if (confirm('确定要清空所有执行历史吗？')) {
      setExecutionHistory([]);
    }
  };

  // 导出历史记录
  const exportHistory = () => {
    const dataStr = JSON.stringify(executionHistory, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `agent-history-${projectId}-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // 切换文档选择
  const toggleDocumentSelection = (docId: number) => {
    if (selectedDocuments.includes(docId)) {
      setSelectedDocuments(selectedDocuments.filter(id => id !== docId));
    } else {
      setSelectedDocuments([...selectedDocuments, docId]);
    }
  };

  const documents = documentsData?.documents || [];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 头部 */}
      <div className="bg-white shadow z-10">
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
              <h1 className="text-2xl font-bold">📊 智能分析工作台</h1>
            </div>
            <button
              onClick={() => setShowStatsPanel(!showStatsPanel)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              <BarChart3 className="w-4 h-4" />
              {showStatsPanel ? '隐藏统计' : '显示统计'}
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* 左侧：统计和文档选择 */}
        {showStatsPanel && (
          <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
            <div className="p-4">
              {/* 统计概览 */}
              <div className="mb-6">
                <h2 className="text-lg font-bold mb-3 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  项目统计
                </h2>
                <div className="space-y-3">
                  <div className="bg-blue-50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-blue-600">
                      {stats?.document_count || 0}
                    </div>
                    <div className="text-sm text-gray-600">文档总数</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-green-600">
                      {stats?.total_words?.toLocaleString() || 0}
                    </div>
                    <div className="text-sm text-gray-600">总字数</div>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-3">
                    <div className="text-2xl font-bold text-purple-600">
                      {stats?.memory_stats?.total_memories || 0}
                    </div>
                    <div className="text-sm text-gray-600">长期记忆</div>
                  </div>
                </div>
              </div>

              {/* 文档选择器 */}
              <div>
                <h2 className="text-lg font-bold mb-3 flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    选择文档
                  </span>
                  <span className="text-sm font-normal text-gray-500">
                    {selectedDocuments.length}/{documents.length}
                  </span>
                </h2>

                {documents.length === 0 ? (
                  <div className="text-sm text-gray-500 text-center py-8">
                    还没有文档
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documents.map((doc: any) => (
                      <label
                        key={doc.id}
                        className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={selectedDocuments.includes(doc.id)}
                          onChange={() => toggleDocumentSelection(doc.id)}
                          className="mt-1 w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate">
                            {doc.title}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {doc.type} • {doc.word_count?.toLocaleString() || 0} 字
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 右侧：Agent工作区 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab导航 */}
          <div className="bg-white border-b border-gray-200">
            <div className="flex items-center px-4">
              <button
                onClick={() => setActiveTab('orchestration')}
                className={`px-4 py-3 font-semibold border-b-2 transition-colors ${
                  activeTab === 'orchestration'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                <span className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  任务编排
                </span>
              </button>
              <button
                onClick={() => setActiveTab('monitor')}
                disabled={!agentExecutionId}
                className={`px-4 py-3 font-semibold border-b-2 transition-colors ${
                  activeTab === 'monitor'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed'
                }`}
              >
                <span className="flex items-center gap-2">
                  <Play className="w-4 h-4" />
                  执行监控
                  {agentExecutionId && (
                    <span className="bg-green-500 w-2 h-2 rounded-full animate-pulse"></span>
                  )}
                </span>
              </button>
              <button
                onClick={() => setActiveTab('results')}
                disabled={!agentResult}
                className={`px-4 py-3 font-semibold border-b-2 transition-colors ${
                  activeTab === 'results'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed'
                }`}
              >
                查看结果
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`px-4 py-3 font-semibold border-b-2 transition-colors ${
                  activeTab === 'history'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                <span className="flex items-center gap-2">
                  执行历史
                  {executionHistory.length > 0 && (
                    <span className="bg-gray-200 text-gray-700 text-xs px-2 py-0.5 rounded-full">
                      {executionHistory.length}
                    </span>
                  )}
                </span>
              </button>
            </div>
          </div>

          {/* Tab内容 */}
          <div className="flex-1 overflow-y-auto bg-gray-50">
            {/* 任务编排 */}
            {activeTab === 'orchestration' && (
              <div className="p-6">
                <div className="max-w-5xl mx-auto">
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 mb-6">
                    <h3 className="font-semibold text-indigo-900 mb-2">💡 工作台说明</h3>
                    <ul className="text-sm text-indigo-700 space-y-1">
                      <li>• 左侧选择要分析的文档，支持多选</li>
                      <li>• 配置多个Agent任务，支持顺序、并行或DAG执行</li>
                      <li>• 任务开始后自动切换到"执行监控"查看进度</li>
                      <li>• 完成后在"查看结果"查看分析结果</li>
                      <li>• 所有执行记录保存在"执行历史"，支持导出</li>
                    </ul>
                  </div>

                  {selectedDocuments.length > 0 && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <FileText className="w-5 h-5 text-blue-600" />
                          <span className="font-semibold text-blue-900">
                            已选择 {selectedDocuments.length} 个文档
                          </span>
                        </div>
                        <button
                          onClick={() => setSelectedDocuments([])}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          清空选择
                        </button>
                      </div>
                    </div>
                  )}

                  <AgentOrchestrationPanel
                    projectId={projectId ? Number(projectId) : undefined}
                    documentIds={selectedDocuments}
                    onExecutionStart={handleAgentExecutionStart}
                    onComplete={handleAgentComplete}
                  />
                </div>
              </div>
            )}

            {/* 执行监控 */}
            {activeTab === 'monitor' && (
              <div className="p-6">
                <div className="max-w-5xl mx-auto">
                  {agentExecutionId ? (
                    <AgentExecutionMonitor
                      executionId={agentExecutionId}
                      projectId={projectId ? Number(projectId) : undefined}
                      autoRefresh={true}
                      refreshInterval={2000}
                      onComplete={handleAgentComplete}
                      onError={handleAgentError}
                    />
                  ) : (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                      <Play className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        没有正在执行的任务
                      </h3>
                      <p className="text-gray-600 mb-6">
                        前往"任务编排"配置并执行Agent任务
                      </p>
                      <button
                        onClick={() => setActiveTab('orchestration')}
                        className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                      >
                        去编排任务
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 查看结果 */}
            {activeTab === 'results' && (
              <div className="p-6">
                <div className="max-w-5xl mx-auto">
                  {agentResult && agentResultType ? (
                    <AgentResultsViewer
                      result={agentResult}
                      resultType={agentResultType}
                    />
                  ) : (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                      <FileText className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        还没有结果
                      </h3>
                      <p className="text-gray-600 mb-6">
                        执行Agent任务后，结果将在这里显示
                      </p>
                      <button
                        onClick={() => setActiveTab('orchestration')}
                        className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                      >
                        去编排任务
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 执行历史 */}
            {activeTab === 'history' && (
              <div className="p-6">
                <div className="max-w-5xl mx-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold">执行历史</h2>
                    <div className="flex items-center gap-3">
                      {executionHistory.length > 0 && (
                        <>
                          <button
                            onClick={exportHistory}
                            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                          >
                            <Download className="w-4 h-4" />
                            导出历史
                          </button>
                          <button
                            onClick={clearHistory}
                            className="flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                            清空历史
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {executionHistory.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                      <FileText className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        没有执行历史
                      </h3>
                      <p className="text-gray-600">
                        执行的Agent任务记录将保存在这里
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {executionHistory.map((entry) => (
                        <div
                          key={entry.id}
                          className="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <span
                                  className={`px-2 py-1 rounded text-xs font-semibold ${
                                    entry.status === 'completed'
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-red-100 text-red-800'
                                  }`}
                                >
                                  {entry.status === 'completed' ? '✓ 完成' : '✗ 失败'}
                                </span>
                                <span className="text-sm text-gray-600">
                                  {entry.taskCount} 个任务
                                </span>
                                {entry.duration && (
                                  <span className="text-sm text-gray-600">
                                    耗时 {entry.duration.toFixed(1)}s
                                  </span>
                                )}
                              </div>
                              <div className="text-sm text-gray-500">
                                {new Date(entry.timestamp).toLocaleString('zh-CN')}
                              </div>
                              {entry.resultType && (
                                <div className="mt-2">
                                  <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded">
                                    {entry.resultType}
                                  </span>
                                </div>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              {entry.result && entry.resultType && (
                                <button
                                  onClick={() => loadHistoryResult(entry)}
                                  className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
                                >
                                  查看结果
                                </button>
                              )}
                              <button
                                onClick={() => deleteHistoryEntry(entry.id)}
                                className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisPage;
