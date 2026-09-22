import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { useAuthStore } from '@/store/authStore'
import { useNavigate } from 'react-router-dom'
import { User, Mail, Shield, Bell, Key, LogOut } from 'lucide-react'

export default function Settings() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-text-primary">设置</h1>
        <p className="text-text-secondary mt-1">管理您的账户和应用设置</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 账户信息 */}
        <Card className="animate-slide-in-up" style={{ animationDelay: '0ms' }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              账户信息
            </CardTitle>
            <CardDescription>您的个人信息</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <Avatar className="h-16 w-16">
                <AvatarImage src="https://github.com/shadcn.png" />
                <AvatarFallback>
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-medium text-text-primary">{user?.username || '用户'}</p>
                <Badge variant="outline">{user?.role || '用户'}</Badge>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-text-secondary">用户名</label>
                <Input value={user?.username || '-'} disabled />
              </div>
              <div>
                <label className="text-sm font-medium text-text-secondary flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  邮箱
                </label>
                <Input value={user?.email || '-'} disabled />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 账户安全 */}
        <Card className="animate-slide-in-up" style={{ animationDelay: '100ms' }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              账户安全
            </CardTitle>
            <CardDescription>保护您的账户安全</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button variant="outline" className="w-full justify-start">
              <Key className="h-4 w-4 mr-2" />
              修改密码
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Shield className="h-4 w-4 mr-2" />
              两步验证
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Mail className="h-4 w-4 mr-2" />
              修改邮箱
            </Button>
          </CardContent>
        </Card>

        {/* 通知设置 */}
        <Card className="animate-slide-in-up" style={{ animationDelay: '200ms' }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              通知设置
            </CardTitle>
            <CardDescription>管理您的通知偏好</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">邮件通知</p>
                <p className="text-xs text-text-secondary">接收邮件提醒</p>
              </div>
              <input type="checkbox" className="h-4 w-4" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">处理完成通知</p>
                <p className="text-xs text-text-secondary">文档处理完成后通知</p>
              </div>
              <input type="checkbox" className="h-4 w-4" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">系统更新</p>
                <p className="text-xs text-text-secondary">接收系统更新消息</p>
              </div>
              <input type="checkbox" className="h-4 w-4" />
            </div>
          </CardContent>
        </Card>

        {/* 退出登录 */}
        <Card className="animate-slide-in-up" style={{ animationDelay: '300ms' }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LogOut className="h-5 w-5" />
              退出登录
            </CardTitle>
            <CardDescription>退出您的账户</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="destructive" onClick={handleLogout} className="w-full">
              <LogOut className="h-4 w-4 mr-2" />
              退出登录
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* 应用信息 */}
      <Card className="animate-slide-in-up" style={{ animationDelay: '400ms' }}>
        <CardHeader>
          <CardTitle>应用信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">版本</span>
              <Badge variant="outline">v1.0.0</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">最后更新</span>
              <span className="text-text-primary">2026-09-09</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-text-secondary">环境</span>
              <Badge variant="success">生产环境</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
