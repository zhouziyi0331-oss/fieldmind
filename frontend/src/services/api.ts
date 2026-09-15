import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 后端统一响应格式: { success: true, data: {...}, error: null, metadata: {...} }
    if (response.data && typeof response.data === 'object') {
      // 标准格式: { success, data, error, metadata }
      if ('success' in response.data) {
        // success = false 表示业务错误
        if (!response.data.success) {
          return Promise.reject({
            message: response.data.error?.message || '请求失败',
            code: response.data.error?.code,
            details: response.data.error?.details
          })
        }
        // success = true，返回 data 字段
        return response.data.data
      }
    }
    // 没有特殊格式，直接返回
    return response.data
  },
  (error) => {
    // 处理错误
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 未授权，跳转到登录页
          localStorage.removeItem('token')
          window.location.href = '/login'
          break
        case 403:
          console.error('权限不足')
          break
        case 404:
          console.error('资源不存在')
          break
        case 500:
          console.error('服务器错误')
          break
        default:
          console.error('请求失败:', error.response.data)
      }
    } else if (error.request) {
      console.error('网络错误，请检查网络连接')
    } else {
      console.error('请求配置错误:', error.message)
    }
    return Promise.reject(error)
  }
)

// API 服务类
class ApiService {
  // 通用 GET 请求
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.get(url, config)
  }

  // 通用 POST 请求
  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.post(url, data, config)
  }

  // 通用 PUT 请求
  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.put(url, data, config)
  }

  // 通用 DELETE 请求
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.delete(url, config)
  }

  // 文件上传
  async upload<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    return apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
  }
}

export const api = new ApiService()
export default apiClient
export { apiClient }
