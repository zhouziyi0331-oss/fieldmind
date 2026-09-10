import { useParams } from 'react-router-dom'
import { useWorkflows, useCreateWorkflow, useExecuteWorkflow } from '@/hooks/useFieldMind'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Badge } from '@/components/ui/badge'
import { Play, Plus, Settings, Pause } from 'lucide-react'

export default function Workflows() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)
  const { data, isLoading } = useWorkflows(projectId)
  const executeWorkflow = useExecuteWorkflow()

  if (isLoading) {
    return <div className="flex items-center justify-center h-96"><Spinner size="lg" /></div>
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">工作流</h1>
          <p className="text-text-secondary mt-1">管理和执行自动化工作流</p>
        </div>
        <Button><Plus className="h-4 w-4 mr-2" />创建工作流</Button>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data?.data?.map((workflow: any) => (
          <Card key={workflow.id} hover>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                {workflow.name}
                <Badge>{workflow.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-text-secondary mb-4">{workflow.description}</p>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => executeWorkflow.mutate({ projectId, workflowId: workflow.id })}>
                  <Play className="h-4 w-4 mr-1" />执行
                </Button>
                <Button size="sm" variant="outline"><Settings className="h-4 w-4" /></Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
