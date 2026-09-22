import { useState } from 'react'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Plus } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { knowledgeGraphAPI } from '@/services/fieldmind-api'

interface AddNodeDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  dirtyDocId: number
  onSuccess: () => void
}

const ENTITY_TYPES = [
  { value: 'PERSON', label: '人物' },
  { value: 'ORGANIZATION', label: '组织' },
  { value: 'LOCATION', label: '地点' },
  { value: 'CONCEPT', label: '概念' },
  { value: 'PROJECT', label: '项目' },
  { value: 'TECHNOLOGY', label: '技术' },
  { value: 'DOCUMENT', label: '文档' },
]

export function AddNodeDialog({
  open,
  onOpenChange,
  dirtyDocId,
  onSuccess,
}: AddNodeDialogProps) {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [nodeType, setNodeType] = useState<'entity' | 'event'>('entity')

  // 实体表单状态
  const [entityForm, setEntityForm] = useState({
    entity_name: '',
    entity_type: 'PERSON',
    importance_score: 0.8,
    properties: '',
  })

  // 事件表单状态
  const [eventForm, setEventForm] = useState({
    event_title: '',
    event_summary: '',
    what: '',
    when: '',
    where: '',
    who: '',
    why: '',
    how: '',
  })

  const handleAddEntity = async () => {
    if (!entityForm.entity_name.trim()) {
      toast({
        title: '提示',
        description: '请输入实体名称',
        variant: 'destructive',
      })
      return
    }

    try {
      setLoading(true)
      const properties = entityForm.properties
        ? JSON.parse(entityForm.properties)
        : {}

      await knowledgeGraphAPI.addManualEntity(dirtyDocId, {
        entity_name: entityForm.entity_name,
        entity_type: entityForm.entity_type,
        importance_score: entityForm.importance_score,
        properties,
      })

      toast({
        title: '成功',
        description: '实体节点已添加',
      })

      // 重置表单
      setEntityForm({
        entity_name: '',
        entity_type: 'PERSON',
        importance_score: 0.8,
        properties: '',
      })

      onSuccess()
      onOpenChange(false)
    } catch (error: any) {
      toast({
        title: '添加失败',
        description: error.message || '无法添加实体节点',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleAddEvent = async () => {
    if (!eventForm.event_title.trim()) {
      toast({
        title: '提示',
        description: '请输入事件标题',
        variant: 'destructive',
      })
      return
    }

    try {
      setLoading(true)
      const event_5w1h = {
        what: eventForm.what,
        when: eventForm.when,
        where: eventForm.where,
        who: eventForm.who,
        why: eventForm.why,
        how: eventForm.how,
      }

      await knowledgeGraphAPI.addManualEvent(dirtyDocId, {
        event_title: eventForm.event_title,
        event_summary: eventForm.event_summary,
        event_5w1h,
      })

      toast({
        title: '成功',
        description: '事件节点已添加',
      })

      // 重置表单
      setEventForm({
        event_title: '',
        event_summary: '',
        what: '',
        when: '',
        where: '',
        who: '',
        why: '',
        how: '',
      })

      onSuccess()
      onOpenChange(false)
    } catch (error: any) {
      toast({
        title: '添加失败',
        description: error.message || '无法添加事件节点',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            手动添加节点
          </DialogTitle>
        </DialogHeader>

        <Tabs value={nodeType} onValueChange={(v) => setNodeType(v as any)}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="entity">实体节点</TabsTrigger>
            <TabsTrigger value="event">事件节点</TabsTrigger>
          </TabsList>

          {/* 实体表单 */}
          <TabsContent value="entity" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="entity-name">实体名称 *</Label>
              <Input
                id="entity-name"
                placeholder="例如：张三、北京大学、人工智能"
                value={entityForm.entity_name}
                onChange={(e) =>
                  setEntityForm({ ...entityForm, entity_name: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="entity-type">实体类型 *</Label>
              <Select
                value={entityForm.entity_type}
                onValueChange={(value) =>
                  setEntityForm({ ...entityForm, entity_type: value })
                }
              >
                <SelectTrigger id="entity-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ENTITY_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="importance">重要性评分 (0-1)</Label>
              <div className="flex items-center gap-4">
                <Input
                  id="importance"
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={entityForm.importance_score}
                  onChange={(e) =>
                    setEntityForm({
                      ...entityForm,
                      importance_score: parseFloat(e.target.value),
                    })
                  }
                  className="flex-1"
                />
                <span className="text-sm font-medium w-12 text-center">
                  {entityForm.importance_score.toFixed(1)}
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="properties">属性 (JSON格式，可选)</Label>
              <Textarea
                id="properties"
                placeholder='例如：{"年龄": 30, "职位": "教授"}'
                value={entityForm.properties}
                onChange={(e) =>
                  setEntityForm({ ...entityForm, properties: e.target.value })
                }
                rows={3}
              />
              <p className="text-xs text-gray-500">
                请输入合法的JSON格式，如 {`{"key": "value"}`}
              </p>
            </div>
          </TabsContent>

          {/* 事件表单 */}
          <TabsContent value="event" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="event-title">事件标题 *</Label>
              <Input
                id="event-title"
                placeholder="例如：项目启动会议、论文发表"
                value={eventForm.event_title}
                onChange={(e) =>
                  setEventForm({ ...eventForm, event_title: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="event-summary">事件摘要</Label>
              <Textarea
                id="event-summary"
                placeholder="简要描述事件内容"
                value={eventForm.event_summary}
                onChange={(e) =>
                  setEventForm({ ...eventForm, event_summary: e.target.value })
                }
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="what">What (什么事件)</Label>
                <Input
                  id="what"
                  placeholder="事件内容"
                  value={eventForm.what}
                  onChange={(e) =>
                    setEventForm({ ...eventForm, what: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="when">When (何时发生)</Label>
                <Input
                  id="when"
                  placeholder="时间"
                  value={eventForm.when}
                  onChange={(e) =>
                    setEventForm({ ...eventForm, when: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="where">Where (何地发生)</Label>
                <Input
                  id="where"
                  placeholder="地点"
                  value={eventForm.where}
                  onChange={(e) =>
                    setEventForm({ ...eventForm, where: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="who">Who (参与者)</Label>
                <Input
                  id="who"
                  placeholder="人物"
                  value={eventForm.who}
                  onChange={(e) =>
                    setEventForm({ ...eventForm, who: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="why">Why (为何发生)</Label>
                <Input
                  id="why"
                  placeholder="原因"
                  value={eventForm.why}
                  onChange={(e) =>
                    setEventForm({ ...eventForm, why: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="how">How (如何发生)</Label>
                <Input
                  id="how"
                  placeholder="方式"
                  value={eventForm.how}
                  onChange={(e) =>
                    setEventForm({ ...eventForm, how: e.target.value })
                  }
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={nodeType === 'entity' ? handleAddEntity : handleAddEvent}
            disabled={loading}
          >
            {loading ? '添加中...' : '添加节点'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
