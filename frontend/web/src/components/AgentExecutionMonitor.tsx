/**
 * AgentExecutionMonitor - Agent执行监控器 (WebSocket版本)
 *
 * 功能：
 * 1. 实时显示Agent执行进度（WebSocket推送）
 * 2. 多任务状态追踪
 * 3. 执行日志展示
 * 4. 错误处理和重试
 * 5. 支持轮询降级（WebSocket不可用时）
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Clock,
  CheckCircle,
  XCircle,
  Loader,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  StopCircle,
  Eye,
  EyeOff,
  Wifi,
  WifiOff
} from 'lucide-react'
import { useExecutionStatus } from '../hooks/useAgents'
import { useAgentExecution } from '../hooks/useWebSocket'
import { WebSocketMessage } from '../services/websocket'

type AgentExecutionStatus = 'pending' | 'running' | 'completed' | 'failed'

interface AgentExecutionMonitorProps {
  executionId: string
  projectId?: number
  autoRefresh?: boolean
  refreshInterval?: number
  onComplete?: (result: any) => void
  onError?: (error: any) => void
  showLogs?: boolean
  useWebSocket?: boolean // 是否使用WebSocket，默认true
}

export const AgentExecutionMonitor: React.FC<AgentExecutionMonitorProps> = ({
  executionId,
  projectId,
  autoRefresh = true,
  refreshInterval = 2000,
  onComplete,
  onError,
  showLogs = true,
  useWebSocket: enableWebSocket = true
}) => {
  const { status, loading, error, getStatus } = useExecutionStatus()
  const [expanded, setExpanded] = useState(true)
  const [logsExpanded, setLogsExpanded] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false)
  const [usePolling, setUsePolling] = useState(!enableWebSocket)

  // WebSocket监听
  const ws = useAgentExecution({
    executionId: enableWebSocket ? executionId : null,
    projectId,
    onStart: (message: WebSocketMessage) => {
      console.log('[WebSocket] Agent execution started:', message);
      // 刷新一次状态
      getStatus(executionId);
    },
    onProgress: (message: WebSocketMessage) => {
      console.log('[WebSocket] Agent execution progress:', message);
      // 刷新状态获取最新数据
      getStatus(executionId);
    },
    onComplete: (message: WebSocketMessage) => {
      console.log('[WebSocket] Agent execution completed:', message);
      // 刷新最终状态
      getStatus(executionId).then(result => {
        if (message.status === 'completed' && onComplete) {
          onComplete(result);
        } else if (message.status === 'failed' && onError) {
          onError(message.error || result.error);
        }
      });
    },
    onTaskUpdate: (message: WebSocketMessage) => {
      console.log('[WebSocket] Agent task update:', message);
      // 刷新状态
      getStatus(executionId);
    }
  });

  // 监听WebSocket连接状态
  useEffect(() => {
    if (!enableWebSocket) return;

    const checkConnection = setInterval(() => {
      const connected = ws.isConnected();
      setIsWebSocketConnected(connected);

      // 如果WebSocket断开，降级到轮询
      if (!connected && !usePolling) {
        console.warn('[AgentExecutionMonitor] WebSocket disconnected, fallback to polling');
        setUsePolling(true);
      }
    }, 1000);

    return () => clearInterval(checkConnection);
  }, [enableWebSocket, ws, usePolling]);

  // 轮询机制（降级方案）
  useEffect(() => {
    if (!usePolling || !executionId || isPaused) return;

    let isActive = true;
    let timeoutId: ReturnType<typeof setTimeout>;

    const pollStatus = async () => {
      if (!isActive || isPaused) return;

      try {
        const result = await getStatus(executionId);

        // 检查是否已完成
        if (result?.status === 'completed') {
          if (onComplete) onComplete(result);
          return; // 停止轮询
        }

        if (result?.status === 'failed') {
          if (onError) onError(result.error);
          return; // 停止轮询
        }

        // 继续轮询
        if (autoRefresh && isActive && !isPaused) {
          timeoutId = setTimeout(pollStatus, refreshInterval);
        }
      } catch (err) {
        console.error('Poll error:', err);
        if (onError) onError(err);
      }
    };

    // 初始加载
    pollStatus();

    return () => {
      isActive = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [executionId, autoRefresh, refreshInterval, isPaused, usePolling, getStatus, onComplete, onError]);

  // 手动刷新
  const handleRefresh = useCallback(async () => {
    if (executionId) {
      await getStatus(executionId);
    }
  }, [executionId, getStatus]);

  // 暂停/恢复
  const togglePause = useCallback(() => {
    setIsPaused(!isPaused);
  }, [isPaused]);

  // 获取状态标签
  const getStatusBadge = (agentStatus: AgentExecutionStatus) => {
    switch (agentStatus) {
      case 'pending':
        return {
          label: '等待中',
          icon: Clock,
          className: 'bg-gray-100 text-gray-700 border-gray-300'
        }
      case 'running':
        return {
          label: '执行中',
          icon: Loader,
          className: 'bg-blue-100 text-blue-700 border-blue-300 animate-pulse'
        }
      case 'completed':
        return {
          label: '已完成',
          icon: CheckCircle,
          className: 'bg-green-100 text-green-700 border-green-300'
        }
      case 'failed':
        return {
          label: '失败',
          icon: XCircle,
          className: 'bg-red-100 text-red-700 border-red-300'
        }
      default:
        return {
          label: agentStatus,
          icon: AlertCircle,
          className: 'bg-gray-100 text-gray-700 border-gray-300'
        }
    }
  }

  // 计算进度百分比
  const calculateProgress = () => {
    if (!status?.result) return 0
    const result = status.result as any
    if (!result.task_results || !Array.isArray(result.task_results)) return 0
    const total = result.task_results.length
    const completed = result.task_results.filter((r: any) => r.status === 'success').length
    return total > 0 ? Math.round((completed / total) * 100) : 0
  }

  // 格式化时间
  const formatDuration = (seconds?: number) => {
    if (!seconds) return '0秒'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`
  }

  if (!status) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center space-x-3">
          <Loader className="w-5 h-5 text-indigo-600 animate-spin" />
          <span className="text-sm text-gray-600">加载执行状态...</span>
        </div>
      </div>
    )
  }

  const progress = calculateProgress()
  const mainStatus = getStatusBadge(status.status)
  const MainIcon = mainStatus.icon

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${mainStatus.className}`}>
              <MainIcon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-gray-900">执行监控</h3>
                {/* WebSocket连接指示器 */}
                {enableWebSocket && (
                  <div className="flex items-center gap-1" title={isWebSocketConnected ? 'WebSocket已连接' : usePolling ? '降级到轮询模式' : 'WebSocket连接中'}>
                    {isWebSocketConnected ? (
                      <Wifi className="w-4 h-4 text-green-600" />
                    ) : (
                      <WifiOff className="w-4 h-4 text-orange-600" />
                    )}
                    <span className="text-xs text-gray-500">
                      {isWebSocketConnected ? '实时' : '轮询'}
                    </span>
                  </div>
                )}
              </div>
              <p className="text-sm text-gray-500">
                执行ID: <span className="font-mono text-xs">{executionId}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* 状态徽章 */}
            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${mainStatus.className}`}>
              {mainStatus.label}
            </span>

            {/* 暂停/恢复按钮（仅轮询模式） */}
            {usePolling && (
              <button
                onClick={togglePause}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title={isPaused ? '恢复轮询' : '暂停轮询'}
              >
                {isPaused ? (
                  <StopCircle className="w-4 h-4 text-gray-600" />
                ) : (
                  <RefreshCw className="w-4 h-4 text-gray-600" />
                )}
              </button>
            )}

            {/* 刷新按钮 */}
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
              title="手动刷新"
            >
              <RefreshCw className={`w-4 h-4 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
            </button>

            {/* 展开/收起 */}
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {expanded ? (
                <ChevronUp className="w-4 h-4 text-gray-600" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-600" />
              )}
            </button>
          </div>
        </div>

        {/* 进度条 */}
        {status.status === 'running' && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
              <span>总体进度</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      {expanded && (
        <div className="p-6 space-y-4">
          {/* 执行统计 */}
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-900">
                {(() => {
                  const result = status.result as any
                  return result?.task_results?.length || 0
                })()}
              </p>
              <p className="text-xs text-gray-600 mt-1">总任务数</p>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">
                {status.status === 'running' ? 1 : 0}
              </p>
              <p className="text-xs text-blue-600 mt-1">执行中</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">
                {(() => {
                  const result = status.result as any
                  return result?.task_results?.filter((r: any) => r.status === 'success').length || 0
                })()}
              </p>
              <p className="text-xs text-green-600 mt-1">已完成</p>
            </div>
            <div className="text-center p-3 bg-red-50 rounded-lg">
              <p className="text-2xl font-bold text-red-600">
                {(() => {
                  const result = status.result as any
                  return result?.task_results?.filter((r: any) => r.status === 'failed').length || 0
                })()}
              </p>
              <p className="text-xs text-red-600 mt-1">失败</p>
            </div>
          </div>

          {/* Agent任务列表 */}
          {(() => {
            const result = status.result as any
            const taskResults = result?.task_results
            return taskResults && Array.isArray(taskResults) && taskResults.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">任务列表</h4>
                {taskResults.map((taskResult: any, index: number) => {
                  const agentStatus: AgentExecutionStatus =
                    taskResult.status === 'success' ? 'completed' :
                    taskResult.status === 'failed' ? 'failed' :
                    status.status === 'running' ? 'running' : 'pending'

                  const statusBadge = getStatusBadge(agentStatus)
                  const StatusIcon = statusBadge.icon

                  return (
                    <div
                      key={`${taskResult.task_id}-${index}`}
                      className={`p-4 border rounded-lg ${
                        agentStatus === 'running' ? 'border-blue-300 bg-blue-50' :
                        agentStatus === 'completed' ? 'border-green-300 bg-green-50' :
                        agentStatus === 'failed' ? 'border-red-300 bg-red-50' :
                        'border-gray-300 bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <StatusIcon className={`w-5 h-5 ${
                            agentStatus === 'running' ? 'text-blue-600 animate-spin' :
                            agentStatus === 'completed' ? 'text-green-600' :
                            agentStatus === 'failed' ? 'text-red-600' :
                            'text-gray-600'
                          }`} />
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {taskResult.agent_type}
                            </p>
                            {taskResult.execution_time && (
                              <p className="text-xs text-gray-500">
                                执行时间: {formatDuration(taskResult.execution_time)}
                              </p>
                            )}
                          </div>
                        </div>

                        <span className={`px-2 py-1 rounded text-xs font-medium ${statusBadge.className}`}>
                          {statusBadge.label}
                        </span>
                      </div>

                      {/* 错误信息 */}
                      {taskResult.error && (
                        <div className="mt-3 p-3 bg-red-100 border border-red-200 rounded text-xs text-red-800">
                          <p className="font-medium">错误信息:</p>
                          <p className="mt-1">{taskResult.error}</p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )
          })()}

          {/* 执行日志 */}
          {showLogs && status.result && (
            <div className="border-t border-gray-200 pt-4">
              <button
                onClick={() => setLogsExpanded(!logsExpanded)}
                className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900"
              >
                {logsExpanded ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                <span>执行日志</span>
              </button>

              {logsExpanded && (
                <div className="mt-3 p-4 bg-gray-900 rounded-lg text-xs font-mono text-gray-100 overflow-x-auto max-h-64 overflow-y-auto">
                  <pre>{JSON.stringify(status.result, null, 2)}</pre>
                </div>
              )}
            </div>
          )}

          {/* 错误提示 */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800 font-medium">监控错误</p>
              <p className="text-xs text-red-600 mt-1">{error.message}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AgentExecutionMonitor
