import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Play,
  Pause,
  RotateCcw,
  Layers,
  Download,
  Camera,
} from 'lucide-react'

// 9步骤知识图谱数据结构
interface KGNode {
  id: string
  label: string
  type: string // PERSON, EVENT, ORGANIZATION, CONCEPT, etc.
  layer: number // 1=核心, 2=次要, 3=细节
  is_core: boolean
  size: number
  x?: number
  y?: number
  pipeline_step: number // 来自哪个管道步骤
  properties?: Record<string, any>
}

interface KGEdge {
  id: string
  source: string | KGNode
  target: string | KGNode
  type: string
  weight: number
  pipeline_step: number
}

interface UnifiedKGData {
  nodes: KGNode[]
  edges: KGEdge[]
  statistics: {
    node_count: number
    edge_count: number
    core_node_count: number
    avg_degree: number
    density: number
  }
  node_type_distribution: Record<string, number>
  edge_type_distribution: Record<string, number>
}

interface UnifiedKnowledgeGraphProps {
  data: UnifiedKGData
  width?: number
  height?: number
  onNodeClick?: (node: KGNode) => void
  onNodeDoubleClick?: (node: KGNode) => void
}

// 节点类型颜色映射
const NODE_TYPE_COLORS: Record<string, string> = {
  PERSON: '#3B82F6', // 蓝色
  EVENT: '#EF4444', // 红色
  ORGANIZATION: '#10B981', // 绿色
  LOCATION: '#F59E0B', // 橙色
  CONCEPT: '#8B5CF6', // 紫色
  PROJECT: '#EC4899', // 粉色
  DOCUMENT: '#6366F1', // 靛蓝色
  TECHNOLOGY: '#14B8A6', // 青色
  default: '#6B7280', // 灰色
}

// 边类型颜色映射
const EDGE_TYPE_COLORS: Record<string, string> = {
  IS_A: '#10B981',
  PART_OF: '#3B82F6',
  PARTICIPATES_IN: '#F59E0B',
  LOCATED_IN: '#8B5CF6',
  WORKS_FOR: '#EC4899',
  COLLABORATES_WITH: '#14B8A6',
  default: '#9CA3AF',
}

export function UnifiedKnowledgeGraph({
  data,
  width = 1200,
  height = 700,
  onNodeClick,
  onNodeDoubleClick,
}: UnifiedKnowledgeGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [zoom, setZoom] = useState(1)
  const [isSimulationRunning, setIsSimulationRunning] = useState(true)
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null)
  const [activeLayer, setActiveLayer] = useState<number | 'all'>('all')
  const simulationRef = useRef<any>(null)

  // 根据层级过滤节点和边
  const filteredData = {
    nodes: activeLayer === 'all'
      ? data.nodes
      : data.nodes.filter(n => n.layer === activeLayer),
    edges: (() => {
      const nodeIds = new Set(
        (activeLayer === 'all' ? data.nodes : data.nodes.filter(n => n.layer === activeLayer))
          .map(n => n.id)
      )
      return data.edges.filter(e =>
        nodeIds.has(typeof e.source === 'string' ? e.source : e.source.id) &&
        nodeIds.has(typeof e.target === 'string' ? e.target : e.target.id)
      )
    })()
  }

  useEffect(() => {
    if (!svgRef.current || filteredData.nodes.length === 0) return

    // 清空之前的内容
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
    const container = svg.append('g')

    // 设置缩放行为
    const zoomBehavior = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform)
        setZoom(event.transform.k)
      })

    svg.call(zoomBehavior as any)

    // 创建力导向图模拟 - 根据层级调整力的强度
    const simulation = d3
      .forceSimulation(filteredData.nodes as any)
      .force(
        'link',
        d3
          .forceLink(filteredData.edges)
          .id((d: any) => d.id)
          .distance((d: any) => {
            // 核心节点之间距离更大
            const source = d.source as KGNode
            const target = d.target as KGNode
            if (source.is_core && target.is_core) return 150
            if (source.is_core || target.is_core) return 120
            return 80
          })
          .strength(0.3)
      )
      .force('charge', d3.forceManyBody().strength((d: any) => {
        // 核心节点排斥力更大
        return d.is_core ? -500 : -300
      }))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => d.size + 10))

    simulationRef.current = simulation

    // 创建箭头标记 - 多种颜色
    const defs = svg.append('defs')
    Object.entries(EDGE_TYPE_COLORS).forEach(([type, color]) => {
      defs.append('marker')
        .attr('id', `arrowhead-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', color)
    })

    // 绘制连接线
    const link = container
      .append('g')
      .selectAll('line')
      .data(filteredData.edges)
      .enter()
      .append('line')
      .attr('stroke', (d: any) => EDGE_TYPE_COLORS[d.type] || EDGE_TYPE_COLORS.default)
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d: any) => Math.sqrt(d.weight) * 1.5)
      .attr('marker-end', (d: any) => `url(#arrowhead-${d.type in EDGE_TYPE_COLORS ? d.type : 'default'})`)

    // 绘制节点组
    const node = container
      .append('g')
      .selectAll('g')
      .data(filteredData.nodes)
      .enter()
      .append('g')
      .attr('cursor', 'pointer')
      .call(
        d3
          .drag<any, any>()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
      )

    // 绘制节点圆圈
    node
      .append('circle')
      .attr('r', (d: any) => d.size)
      .attr('fill', (d: any) => NODE_TYPE_COLORS[d.type] || NODE_TYPE_COLORS.default)
      .attr('stroke', (d: any) => d.is_core ? '#F59E0B' : '#fff')
      .attr('stroke-width', (d: any) => d.is_core ? 4 : 2)
      .on('click', function (event, d: any) {
        event.stopPropagation()
        setSelectedNode(d)
        onNodeClick?.(d)

        // 高亮选中节点
        d3.selectAll('circle')
          .attr('stroke', (n: any) => n.is_core ? '#F59E0B' : '#fff')
          .attr('stroke-width', (n: any) => n.is_core ? 4 : 2)
        d3.select(this)
          .attr('stroke', '#DC2626')
          .attr('stroke-width', 5)
      })
      .on('dblclick', function (event, d: any) {
        event.stopPropagation()
        onNodeDoubleClick?.(d)
      })

    // 添加节点标签
    node
      .append('text')
      .text((d: any) => d.label)
      .attr('x', 0)
      .attr('y', (d: any) => d.size + 18)
      .attr('text-anchor', 'middle')
      .attr('font-size', (d: any) => d.is_core ? '14px' : '12px')
      .attr('font-weight', (d: any) => d.is_core ? 'bold' : 'normal')
      .attr('fill', '#1A1A1A')
      .attr('pointer-events', 'none')

    // 添加层级标识（小圆点）
    node
      .append('circle')
      .attr('r', 4)
      .attr('cx', (d: any) => -d.size * 0.7)
      .attr('cy', (d: any) => -d.size * 0.7)
      .attr('fill', (d: any) => {
        if (d.layer === 1) return '#EF4444'
        if (d.layer === 2) return '#F59E0B'
        return '#10B981'
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)

    // 添加悬停提示
    node.append('title').text((d: any) =>
      `${d.label}\n类型: ${d.type}\n层级: ${d.layer}\n步骤: ${d.pipeline_step}${d.is_core ? '\n[核心节点]' : ''}`
    )

    // 添加边的标签
    const edgeLabels = container
      .append('g')
      .selectAll('text')
      .data(filteredData.edges)
      .enter()
      .append('text')
      .text((d: any) => d.type)
      .attr('font-size', '10px')
      .attr('fill', '#6B7280')
      .attr('text-anchor', 'middle')
      .attr('pointer-events', 'none')

    // 力模拟更新
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)

      edgeLabels
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2)
    })

    // 拖拽函数
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    function dragged(event: any) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }

    // 清理函数
    return () => {
      simulation.stop()
    }
  }, [filteredData, width, height, onNodeClick, onNodeDoubleClick])

  const handleZoomIn = () => {
    const svg = d3.select(svgRef.current)
    const currentTransform = d3.zoomTransform(svg.node()!)
    svg
      .transition()
      .duration(300)
      .call(
        d3.zoom<SVGSVGElement, unknown>().transform as any,
        currentTransform.scale(currentTransform.k * 1.3)
      )
  }

  const handleZoomOut = () => {
    const svg = d3.select(svgRef.current)
    const currentTransform = d3.zoomTransform(svg.node()!)
    svg
      .transition()
      .duration(300)
      .call(
        d3.zoom<SVGSVGElement, unknown>().transform as any,
        currentTransform.scale(currentTransform.k * 0.7)
      )
  }

  const handleResetZoom = () => {
    const svg = d3.select(svgRef.current)
    svg
      .transition()
      .duration(300)
      .call(
        d3.zoom<SVGSVGElement, unknown>().transform as any,
        d3.zoomIdentity
      )
    setZoom(1)
  }

  const handleToggleSimulation = () => {
    if (simulationRef.current) {
      if (isSimulationRunning) {
        simulationRef.current.stop()
      } else {
        simulationRef.current.restart()
      }
      setIsSimulationRunning(!isSimulationRunning)
    }
  }

  const handleRestart = () => {
    if (simulationRef.current) {
      simulationRef.current.alpha(1).restart()
      setIsSimulationRunning(true)
    }
  }

  const handleExportImage = () => {
    if (!svgRef.current) return
    const svgData = new XMLSerializer().serializeToString(svgRef.current)
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    const img = new Image()
    img.onload = () => {
      ctx?.drawImage(img, 0, 0)
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = 'knowledge-graph.png'
          a.click()
          URL.revokeObjectURL(url)
        }
      })
    }
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
  }

  return (
    <div className="space-y-4">
      {/* 统计面板 */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <div className="text-2xl font-bold text-primary">{data.statistics.node_count}</div>
          <div className="text-xs text-text-secondary">节点总数</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-secondary">{data.statistics.edge_count}</div>
          <div className="text-xs text-text-secondary">边总数</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-accent-gold">{data.statistics.core_node_count}</div>
          <div className="text-xs text-text-secondary">核心节点</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-info">{data.statistics.avg_degree.toFixed(2)}</div>
          <div className="text-xs text-text-secondary">平均度数</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-bold text-success">{(data.statistics.density * 100).toFixed(1)}%</div>
          <div className="text-xs text-text-secondary">图密度</div>
        </Card>
      </div>

      {/* 控制面板 */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={handleZoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-sm text-text-secondary min-w-[3rem] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <Button variant="outline" size="icon" onClick={handleZoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={handleResetZoom}>
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Tabs value={String(activeLayer)} onValueChange={(v) => setActiveLayer(v === 'all' ? 'all' : Number(v))}>
            <TabsList>
              <TabsTrigger value="all">全部层级</TabsTrigger>
              <TabsTrigger value="1">核心层</TabsTrigger>
              <TabsTrigger value="2">次要层</TabsTrigger>
              <TabsTrigger value="3">细节层</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleSimulation}
          >
            {isSimulationRunning ? (
              <>
                <Pause className="h-4 w-4 mr-2" />
                暂停
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                继续
              </>
            )}
          </Button>
          <Button variant="outline" size="sm" onClick={handleRestart}>
            <RotateCcw className="h-4 w-4 mr-2" />
            重置
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportImage}>
            <Camera className="h-4 w-4 mr-2" />
            导出图片
          </Button>
        </div>
      </div>

      {/* 图谱可视化区域 */}
      <div className="relative border-2 border-border rounded-lg overflow-hidden bg-gradient-to-br from-primary/5 to-secondary/5">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          className="w-full"
          style={{ minHeight: height }}
        />

        {/* 选中节点信息 */}
        {selectedNode && (
          <Card className="absolute top-4 right-4 w-72 animate-scale-in shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center justify-between">
                节点详情
                <Badge variant={selectedNode.is_core ? 'default' : 'outline'}>
                  {selectedNode.is_core ? '核心节点' : '普通节点'}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="font-medium">名称：</span>
                <span className="text-text-secondary">{selectedNode.label}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">类型：</span>
                <Badge style={{ backgroundColor: NODE_TYPE_COLORS[selectedNode.type] || NODE_TYPE_COLORS.default }}>
                  {selectedNode.type}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">层级：</span>
                <Badge variant="outline">
                  Layer {selectedNode.layer} {selectedNode.layer === 1 ? '(核心)' : selectedNode.layer === 2 ? '(次要)' : '(细节)'}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">来源步骤：</span>
                <span className="text-text-secondary">Step {selectedNode.pipeline_step}</span>
              </div>
              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <div>
                  <span className="font-medium">属性：</span>
                  <div className="mt-1 text-xs bg-gray-50 p-2 rounded max-h-32 overflow-y-auto">
                    {Object.entries(selectedNode.properties).map(([key, value]) => (
                      <div key={key} className="flex justify-between py-1 border-b last:border-b-0">
                        <span className="text-gray-600">{key}:</span>
                        <span className="text-gray-900">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* 图例 */}
      <Card className="p-4">
        <div className="space-y-3">
          <div>
            <h4 className="text-sm font-semibold mb-2">节点类型</h4>
            <div className="flex items-center gap-4 flex-wrap">
              {Object.entries(NODE_TYPE_COLORS).filter(([k]) => k !== 'default').map(([type, color]) => (
                <div key={type} className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-xs text-text-secondary">{type}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-2">边类型</h4>
            <div className="flex items-center gap-4 flex-wrap">
              {Object.entries(EDGE_TYPE_COLORS).filter(([k]) => k !== 'default').map(([type, color]) => (
                <div key={type} className="flex items-center gap-2">
                  <div className="h-0.5 w-6" style={{ backgroundColor: color }} />
                  <span className="text-xs text-text-secondary">{type}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-2">层级标识</h4>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-red-500" />
                <span className="text-xs text-text-secondary">Layer 1 (核心)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-orange-500" />
                <span className="text-xs text-text-secondary">Layer 2 (次要)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-green-500" />
                <span className="text-xs text-text-secondary">Layer 3 (细节)</span>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
