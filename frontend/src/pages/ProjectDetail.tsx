import { useParams, Link } from 'react-router-dom'
import { useProject, useProjectStats } from '@/hooks/useFieldMind'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { FileText, Network, BarChart3, Upload, Settings, TrendingUp } from 'lucide-react'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id!)

  const { data: project, isLoading: projectLoading } = useProject(projectId)
  const { data: stats, isLoading: statsLoading } = useProjectStats(projectId)

  if (projectLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center h-96 animate-fade-in">
        <h2 className="text-2xl font-bold text-text-primary mb-2">项目不存在</h2>
        <Link to="/projects">
          <Button>返回项目列表</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 项目头部 */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold text-text-primary">{project.name}</h1>
            <Badge variant="success">活跃</Badge>
          </div>
          <p className="text-text-secondary">{project.description || '暂无描述'}</p>
        </div>
        <div className="flex items-center gap-2">
          <Link to={`/projects/${projectId}/documents`}>
            <Button>
              <Upload className="h-4 w-4 mr-2" />
              上传文档
            </Button>
          </Link>
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            项目设置
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card hover className="animate-slide-in-up" style={{ animationDelay: '0ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              文档总数
            </CardTitle>
            <FileText className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">{stats?.documents.total || 0}</div>
            <p className="text-xs text-text-secondary mt-1">
              {stats?.documents.completed || 0} 已完成
            </p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '100ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              数据分块
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-secondary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-secondary">{stats?.chunks || 0}</div>
            <p className="text-xs text-text-secondary mt-1">文本块</p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '200ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              知识实体
            </CardTitle>
            <Network className="h-4 w-4 text-info" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-info">{stats?.entities || 0}</div>
            <p className="text-xs text-text-secondary mt-1">实体节点</p>
          </CardContent>
        </Card>

        <Card hover className="animate-slide-in-up" style={{ animationDelay: '300ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-text-secondary">
              洞察数量
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-accent-gold" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-accent-gold">{stats?.insights || 0}</div>
            <p className="text-xs text-text-secondary mt-1">结构化洞察</p>
          </CardContent>
        </Card>
      </div>

      {/* 功能标签页 */}
      <Tabs defaultValue="overview" className="space-y-4 animate-slide-in-up" style={{ animationDelay: '400ms' }}>
        <TabsList>
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="documents">文档</TabsTrigger>
          <TabsTrigger value="knowledge-graph">知识图谱</TabsTrigger>
          <TabsTrigger value="data-quality">数据质量</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>处理进度</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">文档处理</span>
                      <span className="text-sm text-text-secondary">
                        {stats?.documents.completed || 0} / {stats?.documents.total || 0}
                      </span>
                    </div>
                    <div className="h-2 bg-primary/20 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{
                          width: `${
                            stats?.documents.total
                              ? (stats.documents.completed / stats.documents.total) * 100
                              : 0
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>快速操作</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Link to={`/projects/${projectId}/documents`}>
                  <Button variant="outline" className="w-full justify-start">
                    <Upload className="h-4 w-4 mr-2" />
                    上传新文档
                  </Button>
                </Link>
                <Link to={`/projects/${projectId}/knowledge-graph`}>
                  <Button variant="outline" className="w-full justify-start">
                    <Network className="h-4 w-4 mr-2" />
                    查看知识图谱
                  </Button>
                </Link>
                <Link to={`/projects/${projectId}/data-quality`}>
                  <Button variant="outline" className="w-full justify-start">
                    <BarChart3 className="h-4 w-4 mr-2" />
                    数据质量分析
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="documents" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>文档管理</CardTitle>
                <Link to={`/projects/${projectId}/documents`}>
                  <Button>
                    <Upload className="h-4 w-4 mr-2" />
                    上传文档
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-text-secondary mb-4">查看和管理项目文档，上传新文档进行分析。</p>
              <Link to={`/projects/${projectId}/documents`}>
                <Button variant="link" className="px-0">
                  前往文档管理 →
                </Button>
              </Link>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="knowledge-graph" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>知识图谱</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-text-secondary mb-4">可视化知识关系网络，探索实体之间的关联。</p>
              <Link to={`/projects/${projectId}/knowledge-graph`}>
                <Button variant="link" className="px-0">
                  查看知识图谱 →
                </Button>
              </Link>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="data-quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>数据质量</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-text-secondary mb-4">查看数据质量指标和分析报告。</p>
              <Link to={`/projects/${projectId}/data-quality`}>
                <Button variant="link" className="px-0">
                  查看数据质量 →
                </Button>
              </Link>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
