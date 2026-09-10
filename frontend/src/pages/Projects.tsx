import { useState } from 'react'
import { useProjects, useCreateProject, useDeleteProject } from '@/hooks/useFieldMind'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { EmptyState } from '@/components/ui/empty-state'
import { Plus, Trash2, FolderOpen, Search, Grid3x3, List, FileText, Network } from 'lucide-react'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

type ViewMode = 'grid' | 'list'

export default function Projects() {
  const { data: projectsData, isLoading } = useProjects()
  const createProject = useCreateProject()
  const deleteProject = useDeleteProject()

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [newProject, setNewProject] = useState({ name: '', description: '' })
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [searchQuery, setSearchQuery] = useState('')

  const handleCreate = async () => {
    if (!newProject.name.trim()) return
    await createProject.mutateAsync(newProject)
    setIsCreateDialogOpen(false)
    setNewProject({ name: '', description: '' })
  }

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (confirm('确定要删除这个项目吗？此操作无法撤销。')) {
      await deleteProject.mutateAsync(id)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  const projects = projectsData?.data || []
  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (project.description && project.description.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面头部 */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">项目</h1>
          <p className="text-text-secondary mt-1">管理您的知识项目</p>
        </div>

        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              新建项目
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>创建新项目</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <Input
                label="项目名称"
                placeholder="输入项目名称"
                value={newProject.name}
                onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                autoFocus
              />
              <Textarea
                label="项目描述"
                placeholder="输入项目描述（可选）"
                value={newProject.description}
                onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                rows={4}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleCreate} disabled={!newProject.name.trim() || createProject.isPending} loading={createProject.isPending}>
                创建
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* 工具栏 */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
        {/* 搜索框 */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-text-tertiary" />
          <Input
            placeholder="搜索项目..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* 视图切换 */}
        <div className="flex gap-2">
          <Button
            variant={viewMode === 'grid' ? 'primary' : 'outline'}
            size="icon"
            onClick={() => setViewMode('grid')}
          >
            <Grid3x3 className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'primary' : 'outline'}
            size="icon"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 项目列表 */}
      {filteredProjects.length === 0 ? (
        <Card>
          <CardContent className="py-16">
            <EmptyState
              icon={<FolderOpen className="h-16 w-16" />}
              title={searchQuery ? '未找到匹配的项目' : '暂无项目'}
              description={searchQuery ? '尝试使用其他关键词搜索' : '创建您的第一个项目开始使用'}
              action={
                !searchQuery && (
                  <Button onClick={() => setIsCreateDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    新建项目
                  </Button>
                )
              }
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {viewMode === 'grid' ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredProjects.map((project, index) => (
                <Link key={project.id} to={`/projects/${project.id}`}>
                  <Card
                    hover
                    className="h-full animate-scale-in"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0">
                            <FolderOpen className="h-6 w-6 text-white" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <CardTitle className="text-lg truncate">{project.name}</CardTitle>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="flex-shrink-0"
                          onClick={(e) => handleDelete(project.id, e)}
                          disabled={deleteProject.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-text-secondary mb-4 line-clamp-2 h-10">
                        {project.description || '暂无描述'}
                      </p>
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1 text-primary">
                            <FileText className="h-4 w-4" />
                            <span>{project.documents || 0}</span>
                          </div>
                          <div className="flex items-center gap-1 text-secondary">
                            <Network className="h-4 w-4" />
                            <span>{project.contexts || 0}</span>
                          </div>
                        </div>
                        <span className="text-text-tertiary">
                          {formatDistanceToNow(new Date(project.updated_at), {
                            addSuffix: true,
                            locale: zhCN,
                          })}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="divide-y divide-border">
                  {filteredProjects.map((project, index) => (
                    <Link
                      key={project.id}
                      to={`/projects/${project.id}`}
                      className="flex items-center justify-between p-4 hover:bg-surface-hover transition-colors animate-slide-in-up"
                      style={{ animationDelay: `${index * 30}ms` }}
                    >
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0">
                          <FolderOpen className="h-5 w-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-text-primary truncate">
                            {project.name}
                          </h3>
                          <p className="text-sm text-text-secondary truncate">
                            {project.description || '暂无描述'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 ml-4">
                        <Badge variant="outline">{project.documents || 0} 文档</Badge>
                        <Badge variant="secondary">{project.contexts || 0} 上下文</Badge>
                        <span className="text-sm text-text-tertiary hidden sm:inline">
                          {formatDistanceToNow(new Date(project.updated_at), {
                            addSuffix: true,
                            locale: zhCN,
                          })}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => handleDelete(project.id, e)}
                          disabled={deleteProject.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
