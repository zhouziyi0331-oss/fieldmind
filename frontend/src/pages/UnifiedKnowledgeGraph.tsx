import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { knowledgeGraphAPI } from '@/services/fieldmind-api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { UnifiedKnowledgeGraph } from '@/components/ui/unified-knowledge-graph'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Network, Download, Filter, Search, Save, GitCompare, Layers, RefreshCw, FileJson, Database, Plus, GitBranch } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { AddNodeDialog } from '@/components/ui/add-node-dialog'
import { AddRelationDialog } from '@/components/ui/add-relation-dialog'

export default function UnifiedKnowledgeGraphPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const dirtyDocId = parseInt(id!)

  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [snapshotName, setSnapshotName] = useState('')
  const [selectedSteps, setSelectedSteps] = useState<string>('all')
  const [compareDocId, setCompareDocId] = useState<string>('')
  const [showAddNodeDialog, setShowAddNodeDialog] = useState(false)
  const [showAddRelationDialog, setShowAddRelationDialog] = useState(false)

  useEffect(() => {
    if (dirtyDocId) {
      loadGraph()
    }
  }, [dirtyDocId, selectedSteps])

  const loadGraph = async () => {
    try {
      setLoading(true)
      const params = selectedSteps !== 'all' ? { include_steps: selectedSteps } : undefined
      const response = await knowledgeGraphAPI.getDocumentGraph(dirtyDocId, params)
      setData(response.data)
    } catch (error: any) {
      console.error('加载知识图谱失败:', error)
      toast({
        title: '加载失败',
        description: error.message || '无法加载知识图谱数据',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSnapshot = async () => {
    if (!snapshotName.trim()) {
      toast({
        title: '提示',
        description: '请输入快照名称',
        variant: 'destructive'
      })
      return
    }

    try {
      await knowledgeGraphAPI.createSnapshot(dirtyDocId, snapshotName)
      toast({
        title: '成功',
        description: '知识图谱快照已创建'
      })
      setSnapshotName('')
    } catch (error: any) {
      toast({
        title: '创建失败',
        description: error.message,
        variant: 'destructive'
      })
    }
  }

  const handleExport = async (format: 'json' | 'graphml' | 'cypher') => {
    try {
      const response = await knowledgeGraphAPI.exportGraph(dirtyDocId, format)
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `knowledge-graph-${dirtyDocId}.${format}`
      a.click()
      URL.revokeObjectURL(url)
      toast({
        title: '导出成功',
        description: `知识图谱已导出为 ${format} 格式`
      })
    } catch (error: any) {
      toast({
        title: '导出失败',
        description: error.message,
        variant: 'destructive'
      })
    }
  }

  const handleCompare = () => {
    if (!compareDocId) {
      toast({
        title: '提示',
        description: '请输入要比较的文档ID',
        variant: 'destructive'
      })
      return
    }
    navigate(`/knowledge-graph/compare?doc1=${dirtyDocId}&doc2=${compareDocId}`)
  }

  const handleNodeClick = (node: any) => {
    console.log('Node clicked:', node)
  }

  const handleNodeDoubleClick = (node: any) => {
    console.log('Node double clicked:', node)
    // 可以展开显示节点的更多关联信息
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <Network className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h3 className="text-lg font-semibold text-gray-600 mb-2">暂无数据</h3>
        <p className="text-gray-500">文档的知识图谱尚未生成</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in p-6">
      {/* 页面标题 */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-2">
            <Network className="w-8 h-8" />
            统一知识图谱
          </h1>
          <p className="text-text-secondary mt-1">基于9步骤管道的可视化知识网络</p>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="outline">文档 ID: {dirtyDocId}</Badge>
            <Badge>
              {data.statistics.node_count} 个节点 · {data.statistics.edge_count} 条边
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button onClick={() => setShowAddNodeDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            添加节点
          </Button>
          <Button onClick={() => setShowAddRelationDialog(true)} variant="secondary">
            <GitBranch className="h-4 w-4 mr-2" />
            添加关系
          </Button>
          <Button variant="outline" onClick={loadGraph}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button variant="outline" onClick={() => handleExport('json')}>
            <FileJson className="h-4 w-4 mr-2" />
            JSON
          </Button>
          <Button variant="outline" onClick={() => handleExport('graphml')}>
            <Database className="h-4 w-4 mr-2" />
            GraphML
          </Button>
        </div>
      </div>

      {/* 操作面板 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">图谱操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 步骤过滤 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Layers className="inline w-4 h-4 mr-1" />
                过滤管道步骤
              </label>
              <Select value={selectedSteps} onValueChange={setSelectedSteps}>
                <SelectTrigger>
                  <SelectValue placeholder="选择步骤" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部步骤</SelectItem>
                  <SelectItem value="3,4">步骤3-4 (实体+事件)</SelectItem>
                  <SelectItem value="5">步骤5 (关系发现)</SelectItem>
                  <SelectItem value="6">步骤6 (本体构建)</SelectItem>
                  <SelectItem value="7">步骤7 (逻辑推理)</SelectItem>
                  <SelectItem value="8">步骤8 (知识单元化)</SelectItem>
                  <SelectItem value="3,4,5">步骤3-5 (基础图谱)</SelectItem>
                  <SelectItem value="3,4,5,6,7,8">步骤3-8 (完整图谱)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 创建快照 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Save className="inline w-4 h-4 mr-1" />
                创建快照
              </label>
              <div className="flex gap-2">
                <Input
                  placeholder="快照名称"
                  value={snapshotName}
                  onChange={(e) => setSnapshotName(e.target.value)}
                />
                <Button onClick={handleCreateSnapshot}>
                  保存
                </Button>
              </div>
            </div>

            {/* 比较图谱 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <GitCompare className="inline w-4 h-4 mr-1" />
                比较图谱
              </label>
              <div className="flex gap-2">
                <Input
                  placeholder="文档ID"
                  value={compareDocId}
                  onChange={(e) => setCompareDocId(e.target.value)}
                  type="number"
                />
                <Button onClick={handleCompare}>
                  对比
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 节点类型分布 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {data.node_type_distribution.PERSON || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">人物节点</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {data.node_type_distribution.EVENT || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">事件节点</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {data.node_type_distribution.ORGANIZATION || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">组织节点</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {data.node_type_distribution.CONCEPT || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">概念节点</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 图谱可视化 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            知识网络可视化
          </CardTitle>
        </CardHeader>
        <CardContent>
          <UnifiedKnowledgeGraph
            data={data}
            width={1200}
            height={700}
            onNodeClick={handleNodeClick}
            onNodeDoubleClick={handleNodeDoubleClick}
          />
        </CardContent>
      </Card>

      {/* 关系类型分布 */}
      <Card>
        <CardHeader>
          <CardTitle>关系类型分布</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(data.edge_type_distribution).map(([type, count]: [string, any]) => (
              <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="text-sm font-medium">{type}</span>
                <Badge variant="outline">{count}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 操作指南 */}
      <Card>
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
                <p className="text-xs text-text-secondary">调整图谱布局</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-secondary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-secondary font-bold">2</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">层级切换</p>
                <p className="text-xs text-text-secondary">查看不同层级</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-info/10 flex items-center justify-center flex-shrink-0">
                <span className="text-info font-bold">3</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">点击节点</p>
                <p className="text-xs text-text-secondary">查看节点详情</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="h-8 w-8 rounded-lg bg-accent-gold/10 flex items-center justify-center flex-shrink-0">
                <span className="text-accent-gold font-bold">4</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">导出数据</p>
                <p className="text-xs text-text-secondary">多种格式支持</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 手动添加节点对话框 */}
      <AddNodeDialog
        open={showAddNodeDialog}
        onOpenChange={setShowAddNodeDialog}
        dirtyDocId={dirtyDocId}
        onSuccess={loadGraph}
      />

      {/* 手动添加关系对话框 */}
      <AddRelationDialog
        open={showAddRelationDialog}
        onOpenChange={setShowAddRelationDialog}
        dirtyDocId={dirtyDocId}
        nodes={data?.nodes || []}
        onSuccess={loadGraph}
      />
    </div>
  )
}
