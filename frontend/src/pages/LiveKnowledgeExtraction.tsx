import React, { useState, useEffect, useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Play, Pause, RotateCcw, Zap, Database, FileText } from 'lucide-react'
import { UnifiedKnowledgeGraph } from '@/components/ui/unified-knowledge-graph'
import { knowledgeGraphAPI } from '@/services/fieldmind-api'
import { toast } from 'sonner'

interface ExtractionEvent {
  step: number
  type: 'node' | 'edge' | 'property'
  action: 'add' | 'update' | 'infer'
  data: any
  timestamp: number
  reasoning?: string // AI提炼的原因
  source_text?: string // 来自原始文本的哪一段
}

interface ExtractionLog {
  step: number
  step_name: string
  event: string
  extracted_count: number
  timestamp: number
  details: string
}

const EXTRACTION_STEPS = [
  {
    step: 3,
    name: '实体构建',
    description: '从原始文本中识别人物、地点、组织等实体',
    icon: '🔍',
    color: 'bg-blue-500'
  },
  {
    step: 4,
    name: '事件提取',
    description: '提取历史事件，建立时间线',
    icon: '📅',
    color: 'bg-green-500'
  },
  {
    step: 5,
    name: '关系发现',
    description: '分析实体之间的关联关系',
    icon: '🔗',
    color: 'bg-purple-500'
  },
  {
    step: 6,
    name: '本体构建',
    description: '建立知识分类体系和层级结构',
    icon: '🏗️',
    color: 'bg-orange-500'
  },
  {
    step: 7,
    name: '逻辑推理',
    description: '基于已有知识推理新关系',
    icon: '🧠',
    color: 'bg-pink-500'
  },
  {
    step: 8,
    name: '知识单元化',
    description: '组织成独立的知识单元',
    icon: '📦',
    color: 'bg-indigo-500'
  },
]

export default function LiveKnowledgeExtraction() {
  // 用户输入的文档ID
  const [dirtyDocId, setDirtyDocId] = useState<number | null>(null)
  const [docIdInput, setDocIdInput] = useState<string>('')

  // 文档信息
  const [documentInfo, setDocumentInfo] = useState<any>(null)

  const [isProcessing, setIsProcessing] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [currentStep, setCurrentStep] = useState<number | null>(null)

  // 图谱数据（实时增长）
  const [graphData, setGraphData] = useState<any>({ nodes: [], edges: [] })

  // 提炼事件流
  const [extractionEvents, setExtractionEvents] = useState<ExtractionEvent[]>([])

  // 提炼日志
  const [extractionLogs, setExtractionLogs] = useState<ExtractionLog[]>([])

  // 当前正在提炼的文本片段
  const [currentTextSegment, setCurrentTextSegment] = useState<string>('')

  // 统计数据
  const [stats, setStats] = useState({
    total_entities: 0,
    total_events: 0,
    total_relations: 0,
    inferred_relations: 0,
    core_units: 0,
  })

  // EventSource 用于SSE连接
  const [eventSource, setEventSource] = useState<EventSource | null>(null)

  // 🔥 核心功能：加载文档信息
  const loadDocumentInfo = async (docId: number) => {
    try {
      const response = await fetch(`/api/v1/live-extraction/document/${docId}/text-preview`)
      const result = await response.json()

      if (result.success) {
        setDocumentInfo(result.data)
        toast.success('文档加载成功')
      } else {
        toast.error('文档不存在')
      }
    } catch (error) {
      console.error('Failed to load document:', error)
      toast.error('加载文档失败')
    }
  }

  // 🔥 核心功能：实时提炼知识（SSE连接）
  const startRealtimeExtraction = () => {
    if (!dirtyDocId) {
      toast.error('请先输入文档ID')
      return
    }

    setIsProcessing(true)
    setIsPaused(false)
    setGraphData({ nodes: [], edges: [] })
    setExtractionEvents([])
    setExtractionLogs([])
    setCurrentStep(3)

    // 建立SSE连接
    const url = `/api/v1/live-extraction/document/${dirtyDocId}/extract-realtime`
    const es = new EventSource(url)

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        // 处理不同类型的事件
        if (data.error) {
          toast.error(data.error)
          es.close()
          setIsProcessing(false)
          return
        }

        // 步骤开始
        if (data.status === 'started') {
          setCurrentStep(data.step)
          addLog(data.step, EXTRACTION_STEPS.find(s => s.step === data.step)?.name || '', data.message, 0)
        }

        // 步骤完成
        else if (data.status === 'completed') {
          addLog(data.step, EXTRACTION_STEPS.find(s => s.step === data.step)?.name || '', '完成', 0)
        }

        // 提炼完成
        else if (data.status === 'finished') {
          toast.success('知识提炼完成！')
          es.close()
          setIsProcessing(false)
          setCurrentStep(null)
        }

        // 提取出节点
        else if (data.type === 'node' && data.action === 'add') {
          addNodeToGraph(data.data, data.step)
          setCurrentTextSegment(data.source_text || '')
          addLog(data.step, '', `提炼出${data.data.type}: ${data.data.label}`, 1)

          // 更新统计
          if (data.data.type === 'EVENT') {
            setStats(prev => ({ ...prev, total_events: prev.total_events + 1 }))
          } else {
            setStats(prev => ({ ...prev, total_entities: prev.total_entities + 1 }))
          }
        }

        // 提取出边
        else if (data.type === 'edge' && data.action === 'add') {
          addEdgeToGraph(data.data, data.step)
          addLog(data.step, '', `发现关系: ${data.data.type}`, 1)

          // 更新统计
          if (data.step === 7) {
            setStats(prev => ({ ...prev, inferred_relations: prev.inferred_relations + 1 }))
          } else {
            setStats(prev => ({ ...prev, total_relations: prev.total_relations + 1 }))
          }
        }

        // 标记核心节点
        else if (data.type === 'property' && data.action === 'update') {
          updateNodeProperty(data.data.id, { is_core: true, layer: 1 })
          setStats(prev => ({ ...prev, core_units: prev.core_units + 1 }))
          addLog(data.step, '', `标记核心单元`, 1)
        }

      } catch (e) {
        console.error('Failed to parse SSE event:', e)
      }
    }

    es.onerror = (error) => {
      console.error('SSE error:', error)
      toast.error('连接中断')
      es.close()
      setIsProcessing(false)
    }

    setEventSource(es)
  }

  // 添加节点到图谱（实时生长）
  const addNodeToGraph = (node: any, step: number) => {
    setGraphData((prev: any) => {
      // 检查节点是否已存在
      if (prev.nodes.some((n: any) => n.id === node.id)) {
        return prev
      }

      return {
        ...prev,
        nodes: [...prev.nodes, { ...node, pipeline_step: step }]
      }
    })
  }

  // 添加边到图谱（实时连接）
  const addEdgeToGraph = (edge: any, step: number) => {
    setGraphData((prev: any) => {
      // 检查边是否已存在
      if (prev.edges.some((e: any) => e.id === edge.id)) {
        return prev
      }

      return {
        ...prev,
        edges: [...prev.edges, { ...edge, pipeline_step: step }]
      }
    })
  }

  // 更新节点属性
  const updateNodeProperty = (nodeId: string, properties: any) => {
    setGraphData((prev: any) => {
      return {
        ...prev,
        nodes: prev.nodes.map((n: any) =>
          n.id === nodeId ? { ...n, ...properties } : n
        )
      }
    })
  }

  // 添加日志
  const addLog = (step: number, stepName: string, event: string, count: number) => {
    setExtractionLogs(prev => [...prev, {
      step,
      step_name: stepName,
      event,
      extracted_count: count,
      timestamp: Date.now(),
      details: event
    }])
  }

  // 加载文档
  const handleLoadDocument = () => {
    const docId = parseInt(docIdInput)
    if (isNaN(docId) || docId <= 0) {
      toast.error('请输入有效的文档ID')
      return
    }
    setDirtyDocId(docId)
    loadDocumentInfo(docId)
  }

  // 暂停/继续
  const togglePause = () => {
    // SSE不支持暂停，只能关闭连接
    if (eventSource) {
      eventSource.close()
      setEventSource(null)
      setIsProcessing(false)
      toast.info('已停止提炼')
    }
  }

  // 重置
  const resetExtraction = () => {
    if (eventSource) {
      eventSource.close()
      setEventSource(null)
    }
    setIsProcessing(false)
    setIsPaused(false)
    setCurrentStep(null)
    setGraphData({ nodes: [], edges: [] })
    setExtractionEvents([])
    setExtractionLogs([])
    setCurrentTextSegment('')
    setStats({
      total_entities: 0,
      total_events: 0,
      total_relations: 0,
      inferred_relations: 0,
      core_units: 0,
    })
    toast.info('已重置')
  }

  // 组件卸载时关闭SSE连接
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close()
      }
    }
  }, [eventSource])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-[1800px] mx-auto space-y-6">

        {/* 顶部控制栏 */}
        <Card className="p-6 border-2 border-blue-200 bg-white shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Zap className="w-8 h-8 text-yellow-500" />
                实时知识提炼可视化
              </h1>
              <p className="text-gray-600 mt-2">
                观察AI如何从你的文档中一步步提炼出结构化知识图谱
              </p>
            </div>
          </div>

          {/* 文档选择区 */}
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1 flex items-center gap-3">
              <FileText className="w-5 h-5 text-gray-500" />
              <Input
                type="number"
                placeholder="输入文档ID (dirty_doc_id)"
                value={docIdInput}
                onChange={(e) => setDocIdInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLoadDocument()}
                className="max-w-xs"
                disabled={isProcessing}
              />
              <Button
                onClick={handleLoadDocument}
                disabled={isProcessing}
                variant="outline"
              >
                加载文档
              </Button>
            </div>

            <div className="flex gap-3">
              <Button
                onClick={startRealtimeExtraction}
                disabled={isProcessing || !dirtyDocId}
                size="lg"
                className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
              >
                <Play className="w-5 h-5 mr-2" />
                开始提炼
              </Button>

              <Button
                onClick={togglePause}
                disabled={!isProcessing}
                size="lg"
                variant="outline"
              >
                <Pause className="w-5 h-5 mr-2" />
                停止
              </Button>

              <Button
                onClick={resetExtraction}
                size="lg"
                variant="outline"
              >
                <RotateCcw className="w-5 h-5 mr-2" />
                重置
              </Button>
            </div>
          </div>

          {/* 文档信息显示 */}
          {documentInfo && (
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-gray-600">文档类型</div>
                  <div className="text-sm font-medium">{documentInfo.source_type}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-600">文本长度</div>
                  <div className="text-sm font-medium">{documentInfo.total_length} 字符</div>
                </div>
                <div>
                  <div className="text-xs text-gray-600">字数统计</div>
                  <div className="text-sm font-medium">{documentInfo.word_count} 字</div>
                </div>
                <div>
                  <div className="text-xs text-gray-600">文本预览</div>
                  <div className="text-xs text-gray-700 truncate">{documentInfo.text_preview}</div>
                </div>
              </div>
            </div>
          )}

          {/* 实时统计 */}
          <div className="grid grid-cols-5 gap-4 mt-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.total_entities}</div>
              <div className="text-sm text-gray-600">提炼实体</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats.total_events}</div>
              <div className="text-sm text-gray-600">提炼事件</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{stats.total_relations}</div>
              <div className="text-sm text-gray-600">发现关系</div>
            </div>
            <div className="bg-pink-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-pink-600">{stats.inferred_relations}</div>
              <div className="text-sm text-gray-600">推理关系</div>
            </div>
            <div className="bg-indigo-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-indigo-600">{stats.core_units}</div>
              <div className="text-sm text-gray-600">知识单元</div>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-3 gap-6">

          {/* 左侧：步骤进度 */}
          <Card className="p-6 col-span-1">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Database className="w-5 h-5" />
              提炼步骤
            </h2>

            <div className="space-y-3">
              {EXTRACTION_STEPS.map((step) => (
                <div
                  key={step.step}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    currentStep === step.step
                      ? 'border-blue-500 bg-blue-50 shadow-md scale-105'
                      : currentStep && currentStep > step.step
                      ? 'border-green-300 bg-green-50'
                      : 'border-gray-200 bg-white'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`text-2xl ${currentStep === step.step ? 'animate-pulse' : ''}`}>
                      {step.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">步骤{step.step}</span>
                        {currentStep === step.step && (
                          <Badge className="bg-blue-500">
                            <span className="animate-pulse">进行中</span>
                          </Badge>
                        )}
                        {currentStep && currentStep > step.step && (
                          <Badge className="bg-green-500">已完成</Badge>
                        )}
                      </div>
                      <div className="text-sm font-medium text-gray-700 mt-1">
                        {step.name}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {step.description}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* 中间：知识图谱实时可视化 */}
          <Card className="p-6 col-span-2">
            <h2 className="text-xl font-bold mb-4">知识图谱实时生长</h2>

            {graphData.nodes.length === 0 ? (
              <div className="h-[600px] flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-center text-gray-500">
                  <Zap className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg font-medium">点击"开始提炼"观看知识图谱生长</p>
                  <p className="text-sm mt-2">AI将从原始文本中逐步提炼出结构化知识</p>
                </div>
              </div>
            ) : (
              <div className="border-2 border-gray-200 rounded-lg overflow-hidden">
                <UnifiedKnowledgeGraph
                  data={graphData}
                  width={900}
                  height={600}
                />
              </div>
            )}

            {/* 当前正在处理的文本片段 */}
            {currentTextSegment && (
              <div className="mt-4 p-4 bg-yellow-50 border-2 border-yellow-200 rounded-lg">
                <div className="text-sm font-semibold text-yellow-800 mb-2">
                  🔍 正在分析文本：
                </div>
                <div className="text-sm text-gray-700 italic">
                  "{currentTextSegment}"
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* 底部：实时提炼日志 */}
        <Card className="p-6">
          <h2 className="text-xl font-bold mb-4">提炼日志</h2>

          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {extractionLogs.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                暂无日志
              </div>
            ) : (
              extractionLogs.map((log, index) => (
                <div
                  key={index}
                  className="flex items-start gap-4 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <Badge className={EXTRACTION_STEPS.find(s => s.step === log.step)?.color}>
                    步骤{log.step}
                  </Badge>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">
                      {log.event}
                    </div>
                    {log.extracted_count > 0 && (
                      <div className="text-xs text-gray-600 mt-1">
                        提炼了 {log.extracted_count} 个元素
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

      </div>
    </div>
  )
}
