import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { authService, User } from '../services/auth'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import {
  Home,
  FolderOpen,
  FileText,
  MessageSquare,
  BarChart3,
  GitBranch,
  Clock,
  Settings,
  LogOut,
  Menu,
  X,
  User as UserIcon,
  ChevronDown,
  Plus
} from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation()
  const navigate = useNavigate()
  const { projectId } = useParams<{ projectId: string }>()
  const [user, setUser] = useState<User | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showProjectDropdown, setShowProjectDropdown] = useState(false)
  const [currentProjectId, setCurrentProjectId] = useState<number | null>(
    projectId ? Number(projectId) : null
  )

  // 获取项目列表
  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: api.projects.list,
  })

  const projects = projectsData?.projects || []
  const currentProject = projects.find((p: any) => p.id === currentProjectId)

  useEffect(() => {
    loadUser()
  }, [])

  // 监听 URL 变化，同步当前项目
  useEffect(() => {
    if (projectId) {
      const id = Number(projectId)
      setCurrentProjectId(id)
      localStorage.setItem('lastProjectId', String(id))
    } else {
      // 如果 URL 中没有项目 ID，尝试从 localStorage 加载
      const savedId = localStorage.getItem('lastProjectId')
      if (savedId) {
        setCurrentProjectId(Number(savedId))
      }
    }
  }, [projectId])

  const handleProjectSelect = (projectId: number) => {
    setCurrentProjectId(projectId)
    localStorage.setItem('lastProjectId', String(projectId))
    setShowProjectDropdown(false)
    navigate(`/projects/${projectId}`)
  }

  const loadUser = async () => {
    try {
      const userData = await authService.getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Failed to load user:', error)
    }
  }

  const handleLogout = () => {
    if (confirm('确定要退出登录吗？')) {
      authService.logout()
    }
  }

  // 动态生成导航链接（带项目ID）
  const getNavigation = () => {
    const baseNav = [
      { name: '首页', href: '/', icon: Home, requiresProject: false },
      { name: '项目列表', href: '/projects', icon: FolderOpen, requiresProject: false },
    ]

    if (currentProjectId) {
      return [
        ...baseNav,
        { name: '项目概览', href: `/projects/${currentProjectId}`, icon: Home, requiresProject: true },
        { name: '素材导入', href: `/projects/${currentProjectId}/documents`, icon: FileText, requiresProject: true },
        { name: '智能对话', href: `/projects/${currentProjectId}/chat`, icon: MessageSquare, requiresProject: true },
        { name: '知识图谱', href: `/projects/${currentProjectId}/knowledge-graph`, icon: GitBranch, requiresProject: true },
        { name: '时间线', href: `/projects/${currentProjectId}/timeline`, icon: Clock, requiresProject: true },
        { name: '数据分析', href: `/projects/${currentProjectId}/analysis`, icon: BarChart3, requiresProject: true },
      ]
    }

    return baseNav
  }

  const navigation = getNavigation()

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">F</span>
            </div>
            <span className="text-xl font-bold text-gray-900">FieldMind</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-gray-500 hover:text-gray-700"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* 项目选择器 */}
        <div className="px-4 py-4 border-b border-gray-200">
          <div className="relative">
            <button
              onClick={() => setShowProjectDropdown(!showProjectDropdown)}
              className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-2 flex-1 min-w-0">
                <FolderOpen className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-500 mb-0.5">当前项目</p>
                  <p className="text-sm font-semibold text-gray-900 truncate">
                    {currentProject ? currentProject.name : '选择项目'}
                  </p>
                </div>
              </div>
              <ChevronDown className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${showProjectDropdown ? 'rotate-180' : ''}`} />
            </button>

            {/* 项目下拉列表 */}
            {showProjectDropdown && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowProjectDropdown(false)}
                />
                <div className="absolute left-0 right-0 mt-2 bg-white rounded-lg shadow-lg border border-gray-200 z-20 max-h-80 overflow-y-auto">
                  <div className="p-2">
                    <button
                      onClick={() => {
                        setShowProjectDropdown(false)
                        navigate('/projects')
                      }}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors text-sm font-medium"
                    >
                      <Plus className="w-4 h-4" />
                      <span>新建项目</span>
                    </button>
                    <div className="my-2 border-t border-gray-200" />
                    {projects.length === 0 ? (
                      <div className="px-3 py-4 text-center text-sm text-gray-500">
                        暂无项目
                      </div>
                    ) : (
                      projects.map((project: any) => (
                        <button
                          key={project.id}
                          onClick={() => handleProjectSelect(project.id)}
                          className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors text-left ${
                            project.id === currentProjectId
                              ? 'bg-indigo-50 text-indigo-600'
                              : 'text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{project.name}</p>
                            <p className="text-xs text-gray-500">
                              {project.document_count || 0} 文件 · {project.chat_session_count || 0} 对话
                            </p>
                          </div>
                          {project.id === currentProjectId && (
                            <div className="w-2 h-2 bg-indigo-600 rounded-full flex-shrink-0 ml-2" />
                          )}
                        </button>
                      ))
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon
            const active = isActive(item.href)
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                  active
                    ? 'bg-indigo-50 text-indigo-600'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-sm font-medium">{item.name}</span>
              </Link>
            )
          })}
        </nav>

        {/* User Menu */}
        <div className="border-t border-gray-200 p-4">
          {user && (
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                <UserIcon className="w-5 h-5 text-indigo-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user.username}</p>
                <p className="text-xs text-gray-500 truncate">{user.role}</p>
              </div>
            </div>
          )}
          <div className="space-y-1">
            <Link
              to="/settings"
              className="flex items-center space-x-3 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg"
            >
              <Settings className="w-4 h-4" />
              <span>设置</span>
            </Link>
            <button
              onClick={handleLogout}
              className="w-full flex items-center space-x-3 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
            >
              <LogOut className="w-4 h-4" />
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Button */}
      <div className="lg:hidden fixed top-4 left-4 z-40">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 bg-white rounded-lg shadow-md text-gray-700 hover:text-gray-900"
        >
          <Menu className="w-6 h-6" />
        </button>
      </div>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'lg:pl-64' : 'lg:pl-0'}`}>
        <main className="min-h-screen">
          {children}
        </main>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  )
}

export default Layout
