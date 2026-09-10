import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { memoryService } from '@/services/fieldmind'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { EmptyState } from '@/components/ui/empty-state'
import { Dialog } from '@/components/ui/dialog'
import { Plus, Trash2, Search, Brain, Calendar, Tag } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

export default function Memory() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)
  const { toast } = useToast()

  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [newMemory, setNewMemory] = useState({
    content: '',
    type: 'fact',
    tags: '',
  })

  const queryClient = useQueryClient()

  const { data: memories, isLoading } = useQuery({
    queryKey: ['projects', projectId, 'memories'],
    queryFn: () => memoryService.getAll(projectId),
    enabled: !!projectId,
  })

  const createMemory = useMutation({
    mutationFn: (data: any) => memoryService.add(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'memories'] }),
  })

  const deleteMemory = useMutation({
    mutationFn: (memoryId: number) => memoryService.delete(projectId, memoryId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'memories'] }),
  })

  const filteredMemories = memories?.filter((memory: any) =>
    memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    memory.tags?.some((tag: string) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const handleCreateMemory = async () => {
    try {
      await createMemory.mutateAsync({
        ...newMemory,
        tags: newMemory.tags.split(',').map(t => t.trim()).filter(Boolean),
      })
      setIsCreateDialogOpen(false)
      setNewMemory({ content: '', type: 'fact', tags: '' })
      toast({
        title: '记忆已创建',
        description: '新记忆已成功保存',
      })
    } catch (error) {
      toast({
        title: '创建失败',
        description: '无法创建记忆，请重试',
        variant: 'destructive',
      })
    }
  }

  const handleDeleteMemory = async (memoryId: number) => {
    try {
      await deleteMemory.mutateAsync(memoryId)
      toast({
        title: '记忆已删除',
        description: '记忆已成功删除',
      })
    } catch (error) {
      toast({
        title: '删除失败',
        description: '无法删除记忆，请重试',
        variant: 'destructive',
      })
    }
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      fact: 'bg-blue-100 text-blue-800',
      insight: 'bg-purple-100 text-purple-800',
      hypothesis: 'bg-yellow-100 text-yellow-800',
      conclusion: 'bg-green-100 text-green-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Brain className="h-8 w-8 text-[#27768A]" />
            记忆系统
          </h1>
          <p className="text-gray-600 mt-1">管理项目的长期记忆和知识</p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          创建记忆
        </Button>
      </div>

      {/* Search */}
      <Card className="p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="搜索记忆内容或标签..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </Card>

      {/* Memories List */}
      {!filteredMemories || filteredMemories.length === 0 ? (
        <EmptyState
          icon={Brain}
          title="没有记忆"
          description="创建第一个记忆来开始积累项目知识"
          action={{
            label: '创建记忆',
            onClick: () => setIsCreateDialogOpen(true),
          }}
        />
      ) : (
        <div className="grid gap-4">
          {filteredMemories.map((memory: any) => (
            <Card key={memory.id} className="p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={getTypeColor(memory.type)}>
                      {memory.type}
                    </Badge>
                    <div className="flex items-center gap-1 text-sm text-gray-500">
                      <Calendar className="h-3 w-3" />
                      {new Date(memory.created_at).toLocaleDateString('zh-CN')}
                    </div>
                  </div>

                  <p className="text-gray-900 mb-3">{memory.content}</p>

                  {memory.tags && memory.tags.length > 0 && (
                    <div className="flex items-center gap-2 flex-wrap">
                      <Tag className="h-3 w-3 text-gray-400" />
                      {memory.tags.map((tag: string, index: number) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteMemory(memory.id)}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Memory Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">创建新记忆</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">类型</label>
              <select
                value={newMemory.type}
                onChange={(e) => setNewMemory({ ...newMemory, type: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="fact">事实</option>
                <option value="insight">洞察</option>
                <option value="hypothesis">假设</option>
                <option value="conclusion">结论</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">内容</label>
              <Textarea
                value={newMemory.content}
                onChange={(e) => setNewMemory({ ...newMemory, content: e.target.value })}
                placeholder="输入记忆内容..."
                rows={4}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">标签（用逗号分隔）</label>
              <Input
                value={newMemory.tags}
                onChange={(e) => setNewMemory({ ...newMemory, tags: e.target.value })}
                placeholder="标签1, 标签2, 标签3"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              取消
            </Button>
            <Button
              onClick={handleCreateMemory}
              disabled={!newMemory.content.trim() || createMemory.isPending}
            >
              {createMemory.isPending ? <Spinner size="sm" className="mr-2" /> : null}
              创建
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
