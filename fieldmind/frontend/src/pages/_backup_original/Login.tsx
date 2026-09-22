import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '@/services/fieldmind'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Network } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

export default function Login() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const { toast } = useToast()

  const [isLoading, setIsLoading] = useState(false)
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      let response
      if (isRegister) {
        response = await authService.register(
          formData.email,
          formData.username,
          formData.password
        )
      } else {
        response = await authService.login(formData.email, formData.password)
      }

      setAuth(response.user, response.token)
      toast({
        title: '成功',
        description: isRegister ? '注册成功！' : '登录成功！',
        variant: 'success',
      })
      navigate('/dashboard')
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || (isRegister ? '注册失败' : '登录失败')
      setError(errorMsg)
      toast({
        title: '错误',
        description: errorMsg,
        variant: 'error',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-background to-secondary/10 p-4">
      <Card className="w-full max-w-md animate-scale-in">
        <CardHeader className="space-y-1 text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg">
              <Network className="h-8 w-8 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">
            {isRegister ? '注册 FieldMind' : '登录 FieldMind'}
          </CardTitle>
          <CardDescription>
            {isRegister ? '创建账号开始使用' : '输入您的账号信息'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="error">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Input
              label="邮箱"
              type="email"
              placeholder="your@email.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              autoFocus
            />

            {isRegister && (
              <Input
                label="用户名"
                type="text"
                placeholder="username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
              />
            )}

            <Input
              label="密码"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />

            <Button type="submit" className="w-full" loading={isLoading}>
              {isRegister ? '注册' : '登录'}
            </Button>

            <div className="text-center">
              <Button
                type="button"
                variant="link"
                onClick={() => {
                  setIsRegister(!isRegister)
                  setError('')
                }}
                className="text-sm"
              >
                {isRegister ? '已有账号？立即登录' : '没有账号？立即注册'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
