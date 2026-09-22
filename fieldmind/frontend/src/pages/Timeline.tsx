import { useParams } from 'react-router-dom'
import { versionAPI, auditAPI } from '@/services/fieldmind-api';
import { useTimelineEvents, useCreateTimelineEvent } from '@/hooks/useFieldMind'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Badge } from '@/components/ui/badge'
import { Calendar, Clock, MapPin, User } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

export default function Timeline() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)

  const { data: eventsData, isLoading } = useTimelineEvents(projectId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const events = eventsData?.data || []

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-text-primary">时间线</h1>
        <p className="text-text-secondary mt-1">项目事件时间轴</p>
      </div>

      <div className="relative">
        {/* 时间线主轴 */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-border" />

        {/* 事件列表 */}
        <div className="space-y-6">
          {events.map((event: any, index: number) => (
            <div
              key={event.id}
              className="relative pl-20 animate-slide-in-up"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* 时间点 */}
              <div className="absolute left-6 top-0 h-5 w-5 rounded-full bg-primary border-4 border-background" />

              <Card hover>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-base">{event.title}</CardTitle>
                      <div className="flex items-center gap-4 mt-2 text-sm text-text-secondary">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {new Date(event.date).toLocaleDateString('zh-CN')}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {formatDistanceToNow(new Date(event.date), {
                            addSuffix: true,
                            locale: zhCN,
                          })}
                        </div>
                      </div>
                    </div>
                    <Badge>{event.type}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-text-secondary">{event.description}</p>
                  {event.location && (
                    <div className="flex items-center gap-1 mt-2 text-sm text-text-tertiary">
                      <MapPin className="h-4 w-4" />
                      {event.location}
                    </div>
                  )}
                  {event.participants && (
                    <div className="flex items-center gap-1 mt-2 text-sm text-text-tertiary">
                      <User className="h-4 w-4" />
                      {event.participants.join(', ')}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
