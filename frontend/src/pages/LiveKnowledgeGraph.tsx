import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { knowledgeGraphAPI } from '@/services/fieldmind-api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Badge } from '@/components/ui/badge'
import { UnifiedKnowledgeGraph } from '@/components/ui/unified-knowledge-graph'
import { Progress } from '@/components/ui/progress'
import {
  Network,
  CheckCircle2,
  Circle,
  Loader2,
  RefreshCw,
  Play,
} from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

// 9步骤管道的步骤定义
const PIPELINE_STEPS = [
  { step: 1, name: '数据清洗', description: '清洗原始文本数据', graphImpact: false },
  { step: 2, name: '质量验证', description: '验证数据完整性', graphImpact: false },
  { step: 3, name: '实体构建', description: '抽取人物、地点等核心实体', graphImpact: true },
  { step: 4, name: '事件提取', description: '识别并结构化历史事件', graphImpact: true },
  { step: 5, name: '关系发现', description: '发现实体之间的关联', graphImpact: true },
  { step: 6, name: '本体构建', description: '定义知识分类体系和规则', graphImpact: true },
  { step: 7, name: '逻辑推理', description: '推理潜在的知识关联', graphImpact: true },
  { step: 8, name: '知识单元化', description: '组织成可独立使用的知识单元', graphImpact: true },
  { step: 9, name: '阅读器生成', description: '生成人类可读的输出', graphImpact: false },
]

interface StepStatus {
  step: number
  status: 'pending' | 'running' | 'completed' | 'error'
  startTime?: Date
  endTime?: Date
  result?: any
}

export default function LiveKnowledgeGraphPage() {
  const { id } = useParams<{ id: string }>()
  const { toast } = useToast()
  const dirtyDocId = parseInt(id!)

  const [graphData, setGraphData] = useState<any>(null)
  const [pipelineStatus, setPipelineStatus] = useState<StepStatus[]>(
    PIPELINE_STEPS.map(s => ({ step: s.step, status: 'pending' }))
  )
  const [currentStep, setCurrentStep] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // 模拟步骤进度（实际应该从后端WebSocket或轮询获取）
  const simulateStepProgress = async () => {
    setIsProcessing(true)

    for (let i = 0; i < PIPELINE_STEPS.length; i++) {
      const step = PIPELINE_STEPS[i]
      setCurrentStep(step.step)

      // 更新当前步骤为"运行中"
      setPipelineStatus(prev =>
        prev.map(s =>
          s.step === step.step
            ? { ...s, status: 'running', startTime: new Date() }
            : s
        )
      )

      // 模拟步骤执行时间
      await new Promise(resolve => setTimeout(resolve, 2000))

      // 更新当前步骤为"完成"
      setPipelineStatus(prev =>
        prev.map(s =>
          s.step === step.step
            ? { ...s, status: 'completed', endTime: new Date() }
            : s
        )
      )

      // 如果是影响图谱的步骤（3-8），刷新图谱显示
      if (step.graphImpact) {
        await loadGraphByStep(step.step)
      }
    }

    setIsProcessing(false)
    toast({
      title: '管道处理完成',
      description: '知识图谱已构建完毕',
    })
  }

  // 按步骤加载图谱
  const loadGraphByStep = async (upToStep: number) => {
    try {
      // 只包含步骤3到当前步骤
      const steps = Array.from({ length: upToStep - 2 }, (_, i) => i + 3)
        .filter(s => s <= 8)
        .join(',')

      const response = await knowledgeGraphAPI.getDocumentGraph(dirtyDocId, {
        include_steps: steps
      })

      setGraphData(response.data)
    } catch (error: any) {
      console.error('加载图谱失败:', error)
    }
  }

  // 自动刷新图谱
  useEffect(() => {
    if (autoRefresh && isProcessing) {
      intervalRef.current = setInterval(() => {
        if (currentStep >= 3 && currentStep <= 8) {
          loadGraphByStep(currentStep)
        }
      }, 3000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [autoRefresh, isProcessing, currentStep])

  // 初始加载完整图谱
  useEffect(() => {
    if (dirtyDocId && !isProcessing) {
      loadGraphByStep(8) // 加载所有步骤
    }
  }, [dirtyDocId])

  const handleStartPipeline = () => {
    simulateStepProgress()
  }

  const handleReset = () => {
    setPipelineStatus(
      PIPELINE_STEPS.map(s => ({ step: s.step, status: 'pending' }))
    )
    setCurrentStep(0)
    setGraphData(null)
  }

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
      case 'error':
        return <Circle className="w-5 h-5 text-red-500" />
      default:
        return <Circle className="w-5 h-5 text-gray-300" />
    }
  }

  const completedSteps = pipelineStatus.filter(s => s.status === 'completed').length
  const progress = (completedSteps / PIPELINE_STEPS.length) * 100

  return (
    <div className="space-y-6 animate-fade-in p-6">
      {/* 页面标题 */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-2">
            <Network className="w-8 h-8" />
            实时知识图谱构建
          </h1>
          <p className="text-text-secondary mt-1">步骤3-8实时显示图谱演化过程</p>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="outline">文档 ID: {dirtyDocId}</Badge>
            {graphData && (
              <Badge>
                {graphData.statistics.node_count} 节点 · {graphData.statistics.edge_count} 边
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleStartPipeline}
            disabled={isProcessing}
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                处理中...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                开始处理
              </>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={isProcessing}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            重置
          </Button>
        </div>
      </div>

      {/* 总体进度 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">管道处理进度</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>已完成 {completedSteps} / {PIPELINE_STEPS.length} 步骤</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* 步骤列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {PIPELINE_STEPS.map((step) => {
          const status = pipelineStatus.find(s => s.step === step.step)
          const isActive = currentStep === step.step

          return (
            <Card
              key={step.step}
              className={`transition-all ${
                isActive
                  ? 'ring-2 ring-primary shadow-lg'
                  : status?.status === 'completed'
                  ? 'bg-green-50'
                  : ''
              }`}
            >
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    {getStepIcon(status?.status || 'pending')}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-sm">
                        步骤 {step.step}: {step.name}
                      </h3>
                      {step.graphImpact && (
                        <Badge variant="outline" className="text-xs">
                          影响图谱
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      {step.description}
                    </p>
                    {status?.status === 'running' && (
                      <div className="mt-2">
                        <Spinner size="sm" />
                      </div>
                    )}
                    {status?.status === 'completed' && status.endTime && (
                      <p className="text-xs text-green-600 mt-2">
                        ✓ 已完成于 {status.endTime.toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 当前步骤说明 */}
      {isProcessing && currentStep > 0 && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Loader2 className="w-6 h-6 text-primary animate-spin" />
              <div>
                <h3 className="font-semibold">
                  正在执行: {PIPELINE_STEPS[currentStep - 1]?.name}
                </h3>
                <p className="text-sm text-gray-600">
                  {PIPELINE_STEPS[currentStep - 1]?.description}
                </p>
                {currentStep >= 3 && currentStep <= 8 && (
                  <p className="text-sm text-primary mt-1">
                    📊 图谱正在更新中...
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 实时图谱可视化 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              知识图谱 - 实时演化
            </span>
            {currentStep >= 3 && currentStep <= 8 && isProcessing && (
              <Badge variant="outline" className="animate-pulse">
                步骤 {currentStep} 更新中
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {graphData ? (
            <div className="space-y-4">
              {/* 当前图谱统计 */}
              <div className="grid grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">
                    {graphData.statistics.node_count}
                  </div>
                  <div className="text-xs text-gray-600">节点数</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-secondary">
                    {graphData.statistics.edge_count}
                  </div>
                  <div className="text-xs text-gray-600">边数</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-accent-gold">
                    {graphData.statistics.core_node_count}
                  </div>
                  <div className="text-xs text-gray-600">核心节点</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-info">
                    {graphData.statistics.avg_degree.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-600">平均度数</div>
                </div>
              </div>

              {/* 步骤贡献统计 */}
              {currentStep >= 3 && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-sm mb-2">各步骤图谱贡献</h4>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">步骤3-4</Badge>
                      <span>→ 节点（实体+事件）</span>
                    </div>
                    {currentStep >= 5 && (
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">步骤5</Badge>
                        <span>→ 关系边</span>
                      </div>
                    )}
                    {currentStep >= 6 && (
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">步骤6</Badge>
                        <span>→ 本体层级</span>
                      </div>
                    )}
                    {currentStep >= 7 && (
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">步骤7</Badge>
                        <span>→ 推理边</span>
                      </div>
                    )}
                    {currentStep >= 8 && (
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">步骤8</Badge>
                        <span>→ 知识单元</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 图谱可视化 */}
              <UnifiedKnowledgeGraph
                data={graphData}
                width={1200}
                height={600}
                onNodeClick={(node) => {
                  console.log('Node clicked:', node)
                  toast({
                    title: `节点: ${node.label}`,
                    description: `类型: ${node.type} | 来自步骤: ${node.pipeline_step}`,
                  })
                }}
              />
            </div>
          ) : (
            <div className="text-center py-12">
              <Network className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-semibold text-gray-600 mb-2">
                等待图谱构建
              </h3>
              <p className="text-gray-500">
                点击"开始处理"按钮，观察知识图谱的实时构建过程
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 操作提示 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">使用说明</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-primary font-bold">1</span>
              </div>
              <div>
                <p className="text-sm font-medium">实时观察</p>
                <p className="text-xs text-text-secondary">
                  步骤3-8执行时，图谱会实时更新显示
                </p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-secondary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-secondary font-bold">2</span>
              </div>
              <div>
                <p className="text-sm font-medium">步骤追踪</p>
                <p className="text-xs text-text-secondary">
                  每个节点和边都标记了来源步骤
                </p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-info/10 flex items-center justify-center flex-shrink-0">
                <span className="text-info font-bold">3</span>
              </div>
              <div>
                <p className="text-sm font-medium">演化过程</p>
                <p className="text-xs text-text-secondary">
                  观察图谱从简单到复杂的构建过程
                </p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-accent-gold/10 flex items-center justify-center flex-shrink-0">
                <span className="text-accent-gold font-bold">4</span>
              </div>
              <div>
                <p className="text-sm font-medium">知识单元</p>
                <p className="text-xs text-text-secondary">
                  步骤8将图谱组织成可独立使用的单元
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
