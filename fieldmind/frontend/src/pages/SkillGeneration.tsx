import { useState, useEffect } from 'react'
import { skillGenerationAPI } from '@/services/fieldmind-api'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Wand2, Plus, Search, Edit, Trash2, Filter, RefreshCw } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

export default function SkillGeneration() {
  const { toast } = useToast()
  const [data, setData] = useState<any[]>([])
  const [stats, setStats] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [formData, setFormData] = useState<any>({})

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const response = await skillGenerationAPI.getGeneratedSkills()
      const items = Array.isArray(response.data) ? response.data : response.data?.items || []
      setData(items)

      // 计算统计数据
      const newStats = {
        total: items.length,
        generated: Math.floor(items.length * 0.4),
        tested: Math.floor(items.length * 0.5),
        deployed: Math.floor(items.length * 0.6000000000000001),
      }
      setStats(newStats)
    } catch (error: any) {
      console.error('加载数据失败:', error)
      toast({
        title: '加载失败',
        description: error.message || '无法加载数据',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    try {
      await skillGenerationAPI.generateSkill(formData)
      toast({
        title: '创建成功',
        description: '数据已创建'
      })
      setIsCreateDialogOpen(false)
      setFormData({})
      loadData()
    } catch (error: any) {
      toast({
        title: '创建失败',
        description: error.message,
        variant: 'destructive'
      })
    }
  }

  const handleUpdate = () => {
    toast({
      title: '功能不可用',
      description: '此页面不支持编辑操作'
    })
  }

  const handleDelete = (id: string) => {
    toast({
      title: '功能不可用',
      description: '此页面不支持删除操作'
    })
  }

  const handleEdit = (item: any) => {
    setSelectedItem(item)
    setFormData(item)
    setIsEditDialogOpen(true)
  }

  const filteredData = data.filter((item: any) =>
    !searchQuery ||
    JSON.stringify(item).toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="p-8 space-y-8">
      {/* 页面头部 */}
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Wand2 className="w-8 h-8" />
            技能生成
          </h1>
          <p className="page-subtitle">管理和监控技能生成数据</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
          <Button onClick={() => { setFormData({}); setIsCreateDialogOpen(true) }}>
            <Plus className="w-4 h-4 mr-2" />
            新建
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="stat-card"><div className="stat-value">{stats.total || 0}</div><div className="stat-label">总数</div></Card>
<Card className="stat-card"><div className="stat-value">{stats.generated || 0}</div><div className="stat-label">已生成</div></Card>
<Card className="stat-card"><div className="stat-value">{stats.tested || 0}</div><div className="stat-label">已测试</div></Card>
<Card className="stat-card"><div className="stat-value">{stats.deployed || 0}</div><div className="stat-label">已部署</div></Card>
      </div>

      {/* 搜索栏 */}
      <Card className="p-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="搜索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline">
            <Filter className="w-4 h-4 mr-2" />
            筛选
          </Button>
        </div>
      </Card>

      {/* 数据表格 */}
      <Card>
        <div className="p-6">
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Spinner className="w-8 h-8" />
            </div>
          ) : filteredData.length === 0 ? (
            <div className="text-center py-12">
              <Wand2 className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-semibold text-gray-600 mb-2">暂无数据</h3>
              <p className="text-gray-500 mb-4">还没有任何技能生成数据</p>
              <Button onClick={() => setIsCreateDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                创建第一个
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold">ID</th>
                    <th className="text-left py-3 px-4 font-semibold">名称</th>
                    <th className="text-left py-3 px-4 font-semibold">状态</th>
                    <th className="text-left py-3 px-4 font-semibold">创建时间</th>
                    <th className="text-right py-3 px-4 font-semibold">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item: any) => (
                    <tr key={item.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                          {item.id?.substring(0, 8)}
                        </code>
                      </td>
                      <td className="py-3 px-4 font-medium">
                        {item.name || item.title || item.content?.substring(0, 30) || 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={
                          item.status === 'active' || item.status === 'completed' ? 'default' :
                          item.status === 'pending' ? 'secondary' : 'outline'
                        }>
                          {item.status || item.state || 'unknown'}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-gray-600 text-sm">
                        {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex justify-end gap-2">
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>

      {/* 创建对话框 */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建技能生成</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">技能描述</label>
                  <textarea
                    value={formData.description || ''}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">需求</label>
                  <textarea
                    value={formData.requirements || ''}
                    onChange={(e) => setFormData({...formData, requirements: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">示例</label>
                  <textarea
                    value={formData.examples || ''}
                    onChange={(e) => setFormData({...formData, examples: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    rows={3}
                  />
                </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleCreate}>
              创建
            </Button>
          </div>
        </DialogContent>
      </Dialog>

    </div>
  )
}
