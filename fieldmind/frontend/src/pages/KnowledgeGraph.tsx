import { useParams } from 'react-router-dom'
import { knowledgeGraphAPI } from '@/services/fieldmind-api';
import { useKnowledgeGraph } from '@/hooks/useFieldMind'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { KnowledgeGraphVisualization } from '@/components/ui/knowledge-graph-visualization'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Network, Download, Filter, Search } from 'lucide-react'
import { useState } from 'react'

// 模拟数据
const mockNodes = [
  { id: '1', label: '张三', type: 'person' as const, size: 25 },
  { id: '2', label: '李四', type: 'person' as const, size: 20 },
  { id: '3', label: '北京', type: 'location' as const, size: 30 },
  { id: '4', label: '上海', type: 'location' as const, size: 25 },
  { id: '5', label: '项目启动会', type: 'event' as const, size: 22 },
  { id: '6', label: '人工智能', type: 'concept' as const, size: 28 },
  { id: '7', label: '机器学习', type: 'concept' as const, size: 24 },
  { id: '8', label: '王五', type: 'person' as const, size: 18 },
  { id: '9', label: '深圳', type: 'location' as const, size: 22 },
  { id: '10', label: '技术研讨', type: 'event' as const, size: 20 },
]

const mockLinks = [
  { source: '1', target: '3', type: '居住于', weight: 2 },
  { source: '1', target: '5', type: '参与', weight: 1 },
  { source: '2', target: '4', type: '工作于', weight: 2 },
  { source: '3', target: '5', type: '举办地', weight: 1 },
  { source: '5', target: '6', type: '讨论', weight: 2 },
  { source: '6', target: '7', type: '包含', weight: 3 },
  { source: '1', target: '2', type: '认识', weight: 1 },
  { source: '8', target: '9', type: '居住于', weight: 2 },
  { source: '2', target: '10', type: '参与', weight: 1 },
  { source: '7', target: '10', type: '相关', weight: 1 },
]

export default function KnowledgeGraph() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)

  const { data, isLoading } = useKnowledgeGraph(projectId, 100)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<string>('all')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const stats = data?.stats || { node_count: mockNodes.length, edge_count: mockLinks.length }

  // 过滤节点
  const filteredNodes = mockNodes.filter((node) => {
    const matchesSearch = node.label.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = filterType === 'all' || node.type === filterType
    return matchesSearch && matchesType
  })

  // 过滤连接（只保留两端节点都在过滤后列表中的连接）
  const filteredNodeIds = new Set(filteredNodes.map((n) => n.id))
  const filteredLinks = mockLinks.filter(
    (link) =>
      filteredNodeIds.has(link.source.toString()) &&
      filteredNodeIds.has(link.target.toString())
  )

  const handleNodeClick = (node: any) => {
    console.log('Node clicked:', node)
  }

  const handleNodeDoubleClick = (node: any) => {
    console.log('Node double clicked:', node)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面标题 */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">知识图谱</h1>
          <p className="text-text-secondary mt-1">可视化知识关系网络</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card hover className="animate-slide-in-up" style={{ animationDelay: '0ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              实体节点
            </CardTitle>
            <Network className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">{filteredNodes.length}</div>
            <p className="text-xs text-text-secondary mt-1">
              共 {stats.node_count} 个实体
            </p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '100ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              关系边
            </CardTitle>
            <Network className="h-4 w-4 text-secondary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-secondary">{filteredLinks.length}</div>
            <p className="text-xs text-text-secondary mt-1">
              共 {stats.edge_count} 个关系
            </p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '200ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              平均度数
            </CardTitle>
            <Network className="h-4 w-4 text-info" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-info">
              {filteredNodes.length > 0
                ? ((filteredLinks.length * 2) / filteredNodes.length).toFixed(1)
                : 0}
            </div>
            <p className="text-xs text-text-secondary mt-1">连接密度</p>
          </CardContent>
        </Card>
      </div>

      {/* 搜索和筛选 */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-text-tertiary" />
          <Input
            placeholder="搜索节点..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-[180px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="节点类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部类型</SelectItem>
            <SelectItem value="person">人物</SelectItem>
            <SelectItem value="location">地点</SelectItem>
            <SelectItem value="event">事件</SelectItem>
            <SelectItem value="concept">概念</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 图谱可视化区域 */}
      <Card className="animate-slide-in-up" style={{ animationDelay: '300ms' }}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            关系网络
          </CardTitle>
        </CardHeader>
        <CardContent>
          <KnowledgeGraphVisualization
            nodes={filteredNodes}
            links={filteredLinks}
            width={1200}
            height={600}
            onNodeClick={handleNodeClick}
            onNodeDoubleClick={handleNodeDoubleClick}
          />
        </CardContent>
      </Card>

      {/* 操作指南 */}
      <Card className="animate-slide-in-up" style={{ animationDelay: '400ms' }}>
        <CardHeader>
          <CardTitle>操作指南</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-primary font-bold">1</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">拖动节点</p>
                <p className="text-xs text-text-secondary">调整节点位置</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-secondary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-secondary font-bold">2</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">滚轮缩放</p>
                <p className="text-xs text-text-secondary">放大或缩小</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-info/10 flex items-center justify-center flex-shrink-0">
                <span className="text-info font-bold">3</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">点击节点</p>
                <p className="text-xs text-text-secondary">查看详情</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-accent-gold/10 flex items-center justify-center flex-shrink-0">
                <span className="text-accent-gold font-bold">4</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">双击节点</p>
                <p className="text-xs text-text-secondary">展开关联</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
