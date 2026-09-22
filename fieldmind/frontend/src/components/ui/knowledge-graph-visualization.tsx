import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Play,
  Pause,
  RotateCcw,
} from 'lucide-react'

interface Node {
  id: string
  label: string
  type: 'person' | 'location' | 'event' | 'concept'
  size?: number
}

interface Link {
  source: string | Node
  target: string | Node
  type: string
  weight?: number
}

interface KnowledgeGraphVisualizationProps {
  nodes: Node[]
  links: Link[]
  width?: number
  height?: number
  onNodeClick?: (node: Node) => void
  onNodeDoubleClick?: (node: Node) => void
}

const NODE_COLORS = {
  person: '#27768A', // 深青蓝
  location: '#748D44', // 橄榄绿
  event: '#589DA4', // 中青蓝
  concept: '#F8B042', // 金黄色
}

const NODE_LABELS = {
  person: '人物',
  location: '地点',
  event: '事件',
  concept: '概念',
}

export function KnowledgeGraphVisualization({
  nodes,
  links,
  width = 1200,
  height = 600,
  onNodeClick,
  onNodeDoubleClick,
}: KnowledgeGraphVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [zoom, setZoom] = useState(1)
  const [isSimulationRunning, setIsSimulationRunning] = useState(true)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const simulationRef = useRef<any>(null)

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return

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

    // 创建力导向图模拟
    const simulation = d3
      .forceSimulation(nodes as any)
      .force(
        'link',
        d3
          .forceLink(links)
          .id((d: any) => d.id)
          .distance(100)
          .strength(0.5)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40))

    simulationRef.current = simulation

    // 创建箭头标记
    svg
      .append('defs')
      .selectAll('marker')
      .data(['end'])
      .enter()
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999')

    // 绘制连接线
    const link = container
      .append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d: any) => Math.sqrt(d.weight || 1))
      .attr('marker-end', 'url(#arrowhead)')

    // 绘制节点组
    const node = container
      .append('g')
      .selectAll('g')
      .data(nodes)
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
      .attr('r', (d: any) => d.size || 20)
      .attr('fill', (d: any) => NODE_COLORS[d.type] || '#999')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', function (event, d: any) {
        event.stopPropagation()
        setSelectedNode(d)
        onNodeClick?.(d)

        // 高亮选中节点
        d3.selectAll('circle').attr('stroke-width', 2).attr('stroke', '#fff')
        d3.select(this).attr('stroke-width', 3).attr('stroke', '#F8B042')
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
      .attr('y', (d: any) => (d.size || 20) + 15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#1A1A1A')
      .attr('pointer-events', 'none')

    // 添加悬停提示
    node.append('title').text((d: any) => `${d.label} (${NODE_LABELS[d.type]})`)

    // 力模拟更新
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
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
  }, [nodes, links, width, height, onNodeClick, onNodeDoubleClick])

  const handleZoomIn = () => {
    const svg = d3.select(svgRef.current)
    const currentTransform = d3.zoomTransform(svg.node()!)
    svg
      .transition()
      .duration(300)
      .call(
        d3.zoom<SVGSVGElement, unknown>().transform as any,
        currentTransform.scale(currentTransform.k * 1.2)
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
        currentTransform.scale(currentTransform.k * 0.8)
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

  return (
    <div className="space-y-4">
      {/* 控制面板 */}
      <div className="flex items-center justify-between">
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
        </div>
      </div>

      {/* 图谱容器 */}
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
          <Card className="absolute top-4 right-4 w-64 animate-scale-in">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">节点信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <span className="text-sm font-medium">名称：</span>
                <span className="text-sm text-text-secondary ml-2">
                  {selectedNode.label}
                </span>
              </div>
              <div>
                <span className="text-sm font-medium">类型：</span>
                <Badge variant="outline" className="ml-2">
                  {NODE_LABELS[selectedNode.type]}
                </Badge>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 图例 */}
      <div className="flex items-center justify-center gap-6 flex-wrap">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <div
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-xs text-text-secondary">
              {NODE_LABELS[type as keyof typeof NODE_LABELS]}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
