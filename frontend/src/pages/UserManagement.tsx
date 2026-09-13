import { useState } from 'react'
import { userAPI, teamAPI, permissionAPI } from '@/services/fieldmind-api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/services/api'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { Table } from '@/components/ui/table'
import { Dialog } from '@/components/ui/dialog'
import { EmptyState } from '@/components/ui/empty-state'
import { Users, Plus, Edit, Trash2, Search, Shield, Mail, UserCheck } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'

export default function UserManagement() {
  const { toast } = useToast()
  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<any>(null)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'user',
    status: 'active',
  })

  const queryClient = useQueryClient()

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.get('/api/v1/users'),
  })

  const createUser = useMutation({
    mutationFn: (data: any) => apiClient.post('/api/v1/users', data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const updateUser = useMutation({
    mutationFn: ({ userId, data }: any) => apiClient.put(`/api/v1/users/${userId}`, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const deleteUser = useMutation({
    mutationFn: (userId: number) => apiClient.delete(`/api/v1/users/${userId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const filteredUsers = users?.filter((user: any) =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleCreateUser = async () => {
    try {
      await createUser.mutateAsync(formData)
      setIsCreateDialogOpen(false)
      setFormData({ username: '', email: '', password: '', role: 'user', status: 'active' })
      toast({
        title: '用户已创建',
        description: '新用户已成功添加',
      })
    } catch (error) {
      toast({
        title: '创建失败',
        description: '无法创建用户，请重试',
        variant: 'destructive',
      })
    }
  }

  const handleUpdateUser = async () => {
    try {
      await updateUser.mutateAsync({ userId: selectedUser.id, data: formData })
      setIsEditDialogOpen(false)
      setSelectedUser(null)
      toast({
        title: '用户已更新',
        description: '用户信息已成功更新',
      })
    } catch (error) {
      toast({
        title: '更新失败',
        description: '无法更新用户，请重试',
        variant: 'destructive',
      })
    }
  }

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('确定要删除此用户吗？')) return

    try {
      await deleteUser.mutateAsync(userId)
      toast({
        title: '用户已删除',
        description: '用户已成功删除',
      })
    } catch (error) {
      toast({
        title: '删除失败',
        description: '无法删除用户，请重试',
        variant: 'destructive',
      })
    }
  }

  const openEditDialog = (user: any) => {
    setSelectedUser(user)
    setFormData({
      username: user.username,
      email: user.email,
      password: '',
      role: user.role,
      status: user.status,
    })
    setIsEditDialogOpen(true)
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-100 text-purple-800'
      case 'manager':
        return 'bg-blue-100 text-blue-800'
      case 'user':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'inactive':
        return 'bg-gray-100 text-gray-800'
      case 'suspended':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="h-8 w-8 text-[#27768A]" />
            用户管理
          </h1>
          <p className="text-gray-600 mt-1">管理系统用户和权限</p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          添加用户
        </Button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">总用户数</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{users?.length || 0}</p>
            </div>
            <div className="h-12 w-12 bg-blue-50 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-[#27768A]" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">活跃用户</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {users?.filter((u: any) => u.status === 'active').length || 0}
              </p>
            </div>
            <div className="h-12 w-12 bg-green-50 rounded-lg flex items-center justify-center">
              <UserCheck className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">管理员</p>
              <p className="text-2xl font-bold text-purple-600 mt-1">
                {users?.filter((u: any) => u.role === 'admin').length || 0}
              </p>
            </div>
            <div className="h-12 w-12 bg-purple-50 rounded-lg flex items-center justify-center">
              <Shield className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">待审核</p>
              <p className="text-2xl font-bold text-yellow-600 mt-1">
                {users?.filter((u: any) => u.status === 'pending').length || 0}
              </p>
            </div>
            <div className="h-12 w-12 bg-yellow-50 rounded-lg flex items-center justify-center">
              <Mail className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Search */}
      <Card className="p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="搜索用户名或邮箱..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </Card>

      {/* Users Table */}
      {!filteredUsers || filteredUsers.length === 0 ? (
        <EmptyState
          icon={Users}
          title="没有用户"
          description="添加第一个用户开始管理"
          action={{
            label: '添加用户',
            onClick: () => setIsCreateDialogOpen(true),
          }}
        />
      ) : (
        <Card>
          <Table>
            <thead>
              <tr>
                <th>用户名</th>
                <th>邮箱</th>
                <th>角色</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>最后登录</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((user: any) => (
                <tr key={user.id}>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium">
                          {user.username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <span className="font-medium">{user.username}</span>
                    </div>
                  </td>
                  <td>{user.email}</td>
                  <td>
                    <Badge className={getRoleBadgeColor(user.role)}>
                      {user.role === 'admin' ? '管理员' : user.role === 'manager' ? '经理' : '用户'}
                    </Badge>
                  </td>
                  <td>
                    <Badge className={getStatusBadgeColor(user.status)}>
                      {user.status === 'active' ? '活跃' : user.status === 'inactive' ? '未激活' : '暂停'}
                    </Badge>
                  </td>
                  <td>{new Date(user.created_at).toLocaleDateString('zh-CN')}</td>
                  <td>
                    {user.last_login
                      ? new Date(user.last_login).toLocaleDateString('zh-CN')
                      : '从未登录'}
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openEditDialog(user)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteUser(user.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      {/* Create User Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">添加新用户</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">用户名</label>
              <Input
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                placeholder="输入用户名"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">邮箱</label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="输入邮箱"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">密码</label>
              <Input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="输入密码"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">角色</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="user">用户</option>
                <option value="manager">经理</option>
                <option value="admin">管理员</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              取消
            </Button>
            <Button
              onClick={handleCreateUser}
              disabled={!formData.username || !formData.email || !formData.password || createUser.isPending}
            >
              {createUser.isPending ? <Spinner size="sm" className="mr-2" /> : null}
              创建
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">编辑用户</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">用户名</label>
              <Input
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">邮箱</label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">新密码（留空不修改）</label>
              <Input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="留空则不修改密码"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">角色</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="user">用户</option>
                <option value="manager">经理</option>
                <option value="admin">管理员</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">状态</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="active">活跃</option>
                <option value="inactive">未激活</option>
                <option value="suspended">暂停</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              取消
            </Button>
            <Button
              onClick={handleUpdateUser}
              disabled={!formData.username || !formData.email || updateUser.isPending}
            >
              {updateUser.isPending ? <Spinner size="sm" className="mr-2" /> : null}
              保存
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
