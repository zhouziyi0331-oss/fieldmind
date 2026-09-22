import { useProjects, useProjectStats } from '@/hooks/useFieldMind'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/ui/empty-state'
import { FolderOpen, FileText, Network, TrendingUp, Plus, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

// 模拟趋势数据
const trendData = [
  { name: '周一', documents: 12, entities: 45 },
  { name: '周二', documents: 19, entities: 58 },
  { name: '周三', documents: 15, entities: 52 },
  { name: '周四', documents: 25, entities: 78 },
  { name: '周五', documents: 22, entities: 65 },
  { name: '周六', documents: 18, entities: 48 },
  { name: '周日', documents: 16, entities: 42 },
]

export default function Dashboard() {
  const { data: projectsData, isLoading } = useProjects()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const projects = projectsData?.data || []
  const totalProjects = projects.length
  const totalDocuments = projects.reduce((sum, p) => sum + (p.documents || 0), 0)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">Dashboard</h1>
          <p className="text-text-secondary mt-1">欢迎使用 FieldMind 知识管理系统</p>
        </div>
        <Link to="/projects">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            新建项目
          </Button>
        </Link>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card hover className="animate-slide-in-up" style={{ animationDelay: '0ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              项目总数
            </CardTitle>
            <FolderOpen className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">{totalProjects}</div>
            <p className="text-xs text-text-secondary mt-1">
              活跃项目
            </p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '100ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              文档总数
            </CardTitle>
            <FileText className="h-4 w-4 text-secondary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-secondary">{totalDocuments}</div>
            <p className="text-xs text-text-secondary mt-1">
              已处理文档
            </p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '200ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              知识节点
            </CardTitle>
            <Network className="h-4 w-4 text-info" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-info">342</div>
            <p className="text-xs text-text-secondary mt-1">
              知识图谱
            </p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '300ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              数据质量
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-accent-gold" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-accent-gold">94%</div>
            <p className="text-xs text-text-secondary mt-1">
              平均置信度
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 数据趋势图表 */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="animate-slide-in-up" style={{ animationDelay: '400ms' }}>
          <CardHeader>
            <CardTitle>文档增长趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorDocuments" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#27768A" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#27768A" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" stroke="#666666" fontSize={12} />
                <YAxis stroke="#666666" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="documents"
                  stroke="#27768A"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorDocuments)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="animate-slide-in-up" style={{ animationDelay: '500ms' }}>
          <CardHeader>
            <CardTitle>知识实体增长</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" stroke="#666666" fontSize={12} />
                <YAxis stroke="#666666" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="entities" fill="#748D44" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 最近项目 */}
      <Card className="animate-slide-in-up" style={{ animationDelay: '600ms' }}>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>最近项目</CardTitle>
          <Link to="/projects">
            <Button variant="ghost" size="sm">
              查看全部
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {projects.length === 0 ? (
            <EmptyState
              icon={<FolderOpen className="h-16 w-16" />}
              title="暂无项目"
              description="创建您的第一个项目开始使用 FieldMind"
              action={
                <Link to="/projects">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    创建项目
                  </Button>
                </Link>
              }
            />
          ) : (
            <div className="space-y-3">
              {projects.slice(0, 5).map((project, index) => (
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="block group"
                  style={{ animationDelay: `${700 + index * 50}ms` }}
                >
                  <div className="flex items-center justify-between p-4 border border-border rounded-lg hover:border-primary hover:shadow-md transition-all">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0">
                        <FolderOpen className="h-5 w-5 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-text-primary group-hover:text-primary transition-colors truncate">
                          {project.name}
                        </h3>
                        <p className="text-sm text-text-secondary truncate">
                          {project.description || '暂无描述'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 ml-4 flex-shrink-0">
                      <div className="text-right">
                        <Badge variant="outline">{project.documents || 0} 文档</Badge>
                        <p className="text-xs text-text-tertiary mt-1">
                          {formatDistanceToNow(new Date(project.updated_at), {
                            addSuffix: true,
                            locale: zhCN,
                          })}
                        </p>
                      </div>
                      <ArrowRight className="h-5 w-5 text-text-tertiary group-hover:text-primary transition-colors" />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
