import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { GitBranch, Search } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { knowledgeGraphAPI } from '@/services/fieldmind-api'

interface AddRelationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  dirtyDocId: number
  nodes: Array<{ id: string; label: string; type: string }>
  onSuccess: () => void
}

const RELATION_TYPES = [
  { value: 'IS_A', label: '是一个 (IS_A)' },
  { value: 'PART_OF', label: '部分 (PART_OF)' },
  { value: 'PARTICIPATES_IN', label: '参与 (PARTICIPATES_IN)' },
  { value: 'LOCATED_IN', label: '位于 (LOCATED_IN)' },
  { value: 'WORKS_FOR', label: '工作于 (WORKS_FOR)' },
  { value: 'COLLABORATES_WITH', label: '合作 (COLLABORATES_WITH)' },
  { value: 'BELONGS_TO', label: '属于 (BELONGS_TO)' },
  { value: 'CREATES', label: '创建 (CREATES)' },
  { value: 'MANAGES', label: '管理 (MANAGES)' },
  { value: 'RELATED_TO', label: '相关 (RELATED_TO)' },
]

export function AddRelationDialog({
  open,
  onOpenChange,
  dirtyDocId,
  nodes,
  onSuccess,
}: AddRelationDialogProps) {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [sourceSearch, setSourceSearch] = useState('')
  const [targetSearch, setTargetSearch] = useState('')

  const [form, setForm] = useState({
    source_id: '',
    target_id: '',
    relation_type: 'RELATED_TO',
    confidence: 0.9,
    properties: '',
  })

  // 过滤节点
  const filteredSourceNodes = nodes.filter((node) =>
    node.label.toLowerCase().includes(sourceSearch.toLowerCase())
  )

  const filteredTargetNodes = nodes.filter((node) =>
    node.label.toLowerCase().includes(targetSearch.toLowerCase()) &&
    node.id !== form.source_id
  )

  const handleAdd = async () => {
    if (!form.source_id || !form.target_id) {
      toast({
        title: '提示',
        description: '请选择源节点和目标节点',
        variant: 'destructive',
      })
      return
    }

    if (form.source_id === form.target_id) {
      toast({
        title: '提示',
        description: '源节点和目标节点不能相同',
        variant: 'destructive',
      })
      return
    }

    try {
      setLoading(true)
      const properties = form.properties ? JSON.parse(form.properties) : {}

      await knowledgeGraphAPI.addManualRelation(dirtyDocId, {
        source_id: parseInt(form.source_id),
        target_id: parseInt(form.target_id),
        relation_type: form.relation_type,
        confidence: form.confidence,
        properties,
      })

      toast({
        title: '成功',
        description: '关系已添加',
      })

      // 重置表单
      setForm({
        source_id: '',
        target_id: '',
        relation_type: 'RELATED_TO',
        confidence: 0.9,
        properties: '',
      })
      setSourceSearch('')
      setTargetSearch('')

      onSuccess()
      onOpenChange(false)
    } catch (error: any) {
      toast({
        title: '添加失败',
        description: error.message || '无法添加关系',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const getNodeLabel = (nodeId: string) => {
    const node = nodes.find((n) => n.id === nodeId)
    return node ? `${node.label} (${node.type})` : ''
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            手动添加关系
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 源节点选择 */}
          <div className="space-y-2">
            <Label htmlFor="source">源节点 *</Label>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索源节点..."
                value={sourceSearch}
                onChange={(e) => setSourceSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select
              value={form.source_id}
              onValueChange={(value) => setForm({ ...form, source_id: value })}
            >
              <SelectTrigger id="source">
                <SelectValue placeholder="选择源节点">
                  {form.source_id && getNodeLabel(form.source_id)}
                </SelectValue>
              </SelectTrigger>
              <SelectContent className="max-h-60">
                {filteredSourceNodes.length === 0 ? (
                  <div className="p-4 text-center text-sm text-gray-500">
                    未找到匹配的节点
                  </div>
                ) : (
                  filteredSourceNodes.map((node) => (
                    <SelectItem key={node.id} value={node.id}>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{node.label}</span>
                        <span className="text-xs text-gray-500">
                          ({node.type})
                        </span>
                      </div>
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>

          {/* 关系类型 */}
          <div className="space-y-2">
            <Label htmlFor="relation-type">关系类型 *</Label>
            <Select
              value={form.relation_type}
              onValueChange={(value) =>
                setForm({ ...form, relation_type: value })
              }
            >
              <SelectTrigger id="relation-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {RELATION_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* 目标节点选择 */}
          <div className="space-y-2">
            <Label htmlFor="target">目标节点 *</Label>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索目标节点..."
                value={targetSearch}
                onChange={(e) => setTargetSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select
              value={form.target_id}
              onValueChange={(value) => setForm({ ...form, target_id: value })}
            >
              <SelectTrigger id="target">
                <SelectValue placeholder="选择目标节点">
                  {form.target_id && getNodeLabel(form.target_id)}
                </SelectValue>
              </SelectTrigger>
              <SelectContent className="max-h-60">
                {filteredTargetNodes.length === 0 ? (
                  <div className="p-4 text-center text-sm text-gray-500">
                    未找到匹配的节点
                  </div>
                ) : (
                  filteredTargetNodes.map((node) => (
                    <SelectItem key={node.id} value={node.id}>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{node.label}</span>
                        <span className="text-xs text-gray-500">
                          ({node.type})
                        </span>
                      </div>
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>

          {/* 置信度 */}
          <div className="space-y-2">
            <Label htmlFor="confidence">置信度 (0-1)</Label>
            <div className="flex items-center gap-4">
              <Input
                id="confidence"
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={form.confidence}
                onChange={(e) =>
                  setForm({
                    ...form,
                    confidence: parseFloat(e.target.value),
                  })
                }
                className="flex-1"
              />
              <span className="text-sm font-medium w-12 text-center">
                {form.confidence.toFixed(1)}
              </span>
            </div>
          </div>

          {/* 属性 */}
          <div className="space-y-2">
            <Label htmlFor="relation-properties">属性 (JSON格式，可选)</Label>
            <Textarea
              id="relation-properties"
              placeholder='例如：{"权重": 1.0, "描述": "密切合作"}'
              value={form.properties}
              onChange={(e) => setForm({ ...form, properties: e.target.value })}
              rows={3}
            />
            <p className="text-xs text-gray-500">
              请输入合法的JSON格式，如 {`{"key": "value"}`}
            </p>
          </div>

          {/* 关系预览 */}
          {form.source_id && form.target_id && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-sm font-medium text-blue-900 mb-2">
                关系预览：
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="font-semibold text-blue-700">
                  {getNodeLabel(form.source_id)}
                </span>
                <span className="text-blue-600">→</span>
                <span className="px-2 py-1 bg-blue-100 rounded text-blue-800">
                  {form.relation_type}
                </span>
                <span className="text-blue-600">→</span>
                <span className="font-semibold text-blue-700">
                  {getNodeLabel(form.target_id)}
                </span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleAdd} disabled={loading}>
            {loading ? '添加中...' : '添加关系'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
