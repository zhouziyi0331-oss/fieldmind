/**
 * AgentOrchestrationPanel - Agent任务编排面板
 *
 * 功能：
 * 1. 拖拽式任务配置
 * 2. 多Agent编排（顺序/并行/DAG）
 * 3. 参数表单配置
 * 4. 可视化任务流程
 * 5. 一键执行编排任务
 */

import React, { useState, useCallback } from 'react'
import {
  Brain,
  Search,
  FileText,
  Mic,
  GitBranch,
  Plus,
  Trash2,
  Play,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Settings
} from 'lucide-react'
import { useAgentOrchestration } from '../hooks/useAgents'
import type {
  OrchestrationRequest,
  AgentTask
} from '../types/agents'

type OrchestrationMode = 'sequential' | 'parallel' | 'dag'

interface AgentTemplate {
  type: string
  name: string
  icon: React.ComponentType<any>
  description: string
  defaultParams: Record<string, any>
}

const AGENT_TEMPLATES: AgentTemplate[] = [
  {
    type: 'knowledge',
    name: '知识分析',
    icon: Brain,
    description: '深度分析文档，提取实体和关系',
    defaultParams: { analysis_depth: 'standard', max_entities: 100 }
  },
  {
    type: 'search',
    name: '智能搜索',
    icon: Search,
    description: '跨文档语义搜索',
    defaultParams: { max_results: 20, use_rerank: true }
  },
  {
    type: 'summary',
    name: '摘要生成',
    icon: FileText,
    description: '生成结构化摘要',
    defaultParams: { style: 'professional', max_length: 500 }
  },
  {
    type: 'transcript',
    name: '音频转录',
    icon: Mic,
    description: '音频转文字+说话人识别',
    defaultParams: { language: 'zh', enable_diarization: true }
  }
]

interface AgentOrchestrationPanelProps {
  projectId?: number
  documentIds?: number[]
  onExecutionStart?: (executionId: string) => void
  onComplete?: (result: any) => void
}

export const AgentOrchestrationPanel: React.FC<AgentOrchestrationPanelProps> = ({
  projectId,
  documentIds = [],
  onExecutionStart,
  onComplete
}) => {
  const [tasks, setTasks] = useState<AgentTask[]>([])
  const [mode, setMode] = useState<OrchestrationMode>('sequential')
  const [expandedTask, setExpandedTask] = useState<string | null>(null)

  const { result, loading, error, orchestrate } = useAgentOrchestration()

  // 添加任务
  const addTask = useCallback((template: AgentTemplate) => {
    const newTask: AgentTask = {
      agent_type: template.type as 'knowledge' | 'search' | 'summary' | 'transcript',
      task_id: `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      parameters: {
        ...template.defaultParams,
        document_ids: documentIds,
        project_id: projectId
      },
      dependencies: mode === 'sequential' && tasks.length > 0 ? [tasks[tasks.length - 1].task_id] : []
    }
    setTasks([...tasks, newTask])
  }, [tasks, mode, documentIds, projectId])

  // 删除任务
  const removeTask = useCallback((index: number) => {
    setTasks(tasks.filter((_, i) => i !== index))
  }, [tasks])

  // 切换编排模式
  const toggleMode = useCallback(() => {
    const modes: OrchestrationMode[] = ['sequential', 'parallel', 'dag']
    const currentIndex = modes.indexOf(mode)
    const nextMode = modes[(currentIndex + 1) % modes.length]
    setMode(nextMode)

    // 重置依赖关系
    if (nextMode === 'parallel') {
      setTasks(tasks.map(t => ({ ...t, dependencies: [] })))
    } else if (nextMode === 'sequential') {
      setTasks(tasks.map((t, i) => ({
        ...t,
        dependencies: i > 0 ? [tasks[i - 1].task_id] : []
      })))
    }
  }, [mode, tasks])

  // 执行编排
  const handleExecute = useCallback(async () => {
    if (tasks.length === 0) {
      alert('请至少添加一个任务')
      return
    }

    const request: OrchestrationRequest = {
      tasks,
      execution_mode: mode,
      project_id: projectId,
      timeout_seconds: 300
    }

    try {
      const response = await orchestrate(request)
      if (response && onExecutionStart) {
        onExecutionStart(response.agent_id)
      }
      if (response && onComplete) {
        onComplete(response)
      }
    } catch (err) {
      console.error('Orchestration failed:', err)
    }
  }, [tasks, mode, projectId, orchestrate, onExecutionStart, onComplete])

  // 获取模式标签
  const getModeLabel = () => {
    switch (mode) {
      case 'sequential': return '顺序执行'
      case 'parallel': return '并行执行'
      case 'dag': return 'DAG流程'
      default: return mode
    }
  }

  // 获取模式描述
  const getModeDescription = () => {
    switch (mode) {
      case 'sequential': return '任务按顺序依次执行，前一个完成后才开始下一个'
      case 'parallel': return '所有任务同时并行执行，互不依赖'
      case 'dag': return '根据依赖关系构建有向无环图，自动优化执行顺序'
      default: return ''
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
              <GitBranch className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Agent任务编排</h3>
              <p className="text-sm text-gray-500">配置多Agent协同任务流程</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* 模式切换 */}
            <button
              onClick={toggleMode}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium text-gray-700 transition-colors"
              title={getModeDescription()}
            >
              <Settings className="w-4 h-4" />
              <span>{getModeLabel()}</span>
            </button>

            {/* 执行按钮 */}
            <button
              onClick={handleExecute}
              disabled={loading || tasks.length === 0}
              className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
            >
              <Play className="w-4 h-4" />
              <span>{loading ? '执行中...' : '执行编排'}</span>
            </button>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Agent模板选择 */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">选择Agent类型</h4>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {AGENT_TEMPLATES.map((template) => {
              const Icon = template.icon
              return (
                <button
                  key={template.type}
                  onClick={() => addTask(template)}
                  className="flex flex-col items-center p-4 border-2 border-dashed border-gray-300 hover:border-indigo-500 hover:bg-indigo-50 rounded-lg transition-all group"
                >
                  <div className="w-12 h-12 bg-gray-100 group-hover:bg-indigo-100 rounded-lg flex items-center justify-center mb-2 transition-colors">
                    <Icon className="w-6 h-6 text-gray-600 group-hover:text-indigo-600" />
                  </div>
                  <span className="text-sm font-medium text-gray-900">{template.name}</span>
                  <span className="text-xs text-gray-500 text-center mt-1">{template.description}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* 任务列表 */}
        {tasks.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-700">
                任务流程 ({tasks.length} 个任务)
              </h4>
              <span className="text-xs text-gray-500">{getModeDescription()}</span>
            </div>

            <div className="space-y-2">
              {tasks.map((task, index) => {
                const template = AGENT_TEMPLATES.find(t => t.type === task.agent_type)
                if (!template) return null

                const Icon = template.icon
                const isExpanded = expandedTask === `${index}`

                return (
                  <div
                    key={`${task.agent_type}-${index}`}
                    className="border border-gray-200 rounded-lg overflow-hidden"
                  >
                    {/* Task Header */}
                    <div className="flex items-center justify-between p-4 bg-gray-50">
                      <div className="flex items-center space-x-3">
                        <span className="flex items-center justify-center w-6 h-6 bg-indigo-600 text-white text-xs font-bold rounded-full">
                          {index + 1}
                        </span>
                        <Icon className="w-5 h-5 text-gray-600" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{template.name}</p>
                          <p className="text-xs text-gray-500">{template.description}</p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setExpandedTask(isExpanded ? null : `${index}`)}
                          className="p-1 hover:bg-gray-200 rounded transition-colors"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-gray-600" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-gray-600" />
                          )}
                        </button>
                        <button
                          onClick={() => removeTask(index)}
                          className="p-1 hover:bg-red-100 rounded transition-colors"
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </button>
                      </div>
                    </div>

                    {/* Task Parameters (Expandable) */}
                    {isExpanded && (
                      <div className="p-4 bg-white border-t border-gray-200">
                        <div className="space-y-3">
                          <h5 className="text-xs font-medium text-gray-700 uppercase">参数配置</h5>
                          <pre className="text-xs bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto">
                            {JSON.stringify(task.parameters, null, 2)}
                          </pre>
                          {task.dependencies && task.dependencies.length > 0 && (
                            <div className="text-xs text-gray-600">
                              <span className="font-medium">依赖任务:</span> {task.dependencies.join(', ')}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Arrow for sequential mode */}
                    {mode === 'sequential' && index < tasks.length - 1 && (
                      <div className="flex justify-center py-2 bg-gray-50">
                        <ArrowRight className="w-4 h-4 text-gray-400" />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Empty State */}
        {tasks.length === 0 && (
          <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
            <Plus className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-600">点击上方Agent类型添加任务</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800 font-medium">执行失败</p>
            <p className="text-xs text-red-600 mt-1">{error.message}</p>
          </div>
        )}

        {/* Result Preview */}
        {result && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800 font-medium">编排任务已启动</p>
            <p className="text-xs text-green-600 mt-1">执行ID: {result.agent_id}</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default AgentOrchestrationPanel
