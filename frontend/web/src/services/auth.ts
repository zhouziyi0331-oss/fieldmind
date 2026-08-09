/**
 * 认证服务
 */
export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  role?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: number
  username: string
  email: string
  role: string
  permissions: string[]
  created_at: string
}

export const authService = {
  /**
   * 用户登录
   */
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await apiClient.post<AuthResponse>('/api/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    // 保存token
    if (response.access_token) {
      localStorage.setItem('auth_token', response.access_token)
    }

    return response
  },

  /**
   * 用户注册
   */
  register: async (data: RegisterRequest): Promise<User> => {
    return apiClient.post<User>('/api/auth/register', data)
  },

  /**
   * 获取当前用户
   */
  getCurrentUser: async (): Promise<User> => {
    return apiClient.get<User>('/api/auth/me')
  },

  /**
   * 退出登录
   */
  logout: () => {
    localStorage.removeItem('auth_token')
    window.location.href = '/login'
  },

  /**
   * 检查是否已登录
   */
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('auth_token')
  },

  /**
   * 获取token
   */
  getToken: (): string | null => {
    return localStorage.getItem('auth_token')
  }
}
