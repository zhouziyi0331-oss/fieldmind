import { useParams } from 'react-router-dom'
import { citationAPI } from '@/services/fieldmind-api';
import { useCitations } from '@/hooks/useFieldMind'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FileText, CheckCircle, AlertCircle } from 'lucide-react'

export default function Citations() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)
  const { data, isLoading } = useCitations(projectId)

  if (isLoading) return <div className="flex items-center justify-center h-96"><Spinner size="lg" /></div>

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-text-primary">引用管理</h1>
        <p className="text-text-secondary mt-1">管理文档引用和来源追溯</p>
      </div>
      <div className="space-y-3">
        {data?.data?.map((citation: any) => (
          <Card key={citation.id} hover>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <FileText className="h-5 w-5 text-primary flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <p className="font-medium text-text-primary">{citation.text}</p>
                    <p className="text-sm text-text-secondary mt-1">来源: {citation.source}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={citation.verified ? 'success' : 'warning'}>
                    {citation.verified ? <CheckCircle className="h-3 w-3 mr-1" /> : <AlertCircle className="h-3 w-3 mr-1" />}
                    {citation.verified ? '已验证' : '待验证'}
                  </Badge>
                  <Button size="sm" variant="outline">查看</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
