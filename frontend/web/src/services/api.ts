/**
 * API Service for FieldMind Backend
 * Enhanced with error handling and performance tracking
 */
import axios from 'axios'
import { handleError } from '../utils/errorHandler'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - 添加认证和性能追踪
apiClient.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 记录请求开始时间（用于性能追踪）
    config.metadata = { startTime: new Date() }

    // 日志
    if (import.meta.env.DEV) {
      console.log(`📤 ${config.method?.toUpperCase()} ${config.url}`)
    }

    return config
  },
  (error) => {
    console.error('❌ Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - 增强错误处理和性能日志
apiClient.interceptors.response.use(
  (response) => {
    // 计算请求耗时
    const duration = new Date().getTime() - response.config.metadata.startTime.getTime()

    // 性能日志
    if (import.meta.env.DEV) {
      console.log(
        `📥 ${response.config.method?.toUpperCase()} ${response.config.url} ` +
        `[${response.status}] ${duration}ms`
      )
    }

    // 性能警告
    if (duration > 3000) {
      console.warn(`⚠️ Slow API: ${response.config.url} took ${duration}ms`)
    }

    return response.data
  },
  (error) => {
    // 使用统一错误处理
    const appError = handleError(error)

    // 开发模式详细日志
    if (import.meta.env.DEV) {
      console.error('❌ API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        message: appError.message,
        code: appError.code
      })
    }

    return Promise.reject(appError)
  }
)

// 为TypeScript添加metadata类型
declare module 'axios' {
  export interface AxiosRequestConfig {
    metadata?: {
      startTime: Date
    }
  }
}

export interface Project {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
}

export interface Document {
  id: string
  project_id: string
  filename: string
  file_type: string
  file_size: number
  content?: string
  status: string
  processing_progress: number
  created_at: string
}

export interface Memory {
  id: string
  project_id: string
  content: string
  memory_type: string
  importance: number
  created_at: string
}

export const api = {
  // Projects
  projects: {
    list: () => apiClient.get<Project[]>('/api/v1/projects'),
    get: (id: number) => apiClient.get<Project>(`/api/v1/projects/${id}`),
    create: (data: Partial<Project>) => apiClient.post<Project>('/api/v1/projects', data),
    update: (id: number, data: Partial<Project>) =>
      apiClient.put<Project>(`/api/v1/projects/${id}`, data),
    delete: (id: number) => apiClient.delete(`/api/v1/projects/${id}`),
    analyze: (id: number) => apiClient.post(`/api/projects/${id}/analyze`),
    getStats: (id: number) => apiClient.get(`/api/projects/${id}/stats`),
  },

  // Documents
  documents: {
    list: (projectId: number) =>
      apiClient.get<Document[]>(`/api/v1/projects/${projectId}/documents`),
    get: (documentId: number) =>
      apiClient.get<Document>(`/api/documents/${documentId}`),
    upload: (projectId: number, file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('project_id', projectId.toString())
      return apiClient.post<Document>(
        `/api/documents/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      )
    },
    delete: (documentId: number) =>
      apiClient.delete(`/api/documents/${documentId}`),
    getFactStatements: (documentId: number) =>
      apiClient.get(`/api/documents/${documentId}/fact-statements`),
  },

  // Chat
  chat: {
    createSession: (data: { project_id: number; name: string; document_ids?: number[] }) =>
      apiClient.post('/api/chat/sessions', data),
    listSessions: (projectId: number) =>
      apiClient.get(`/api/chat/projects/${projectId}/sessions`),
    getSession: (sessionId: number) =>
      apiClient.get(`/api/chat/sessions/${sessionId}`),
    deleteSession: (sessionId: number) =>
      apiClient.delete(`/api/chat/sessions/${sessionId}`),
    sendMessage: (sessionId: number, content: string) =>
      apiClient.post(`/api/chat/sessions/${sessionId}/messages`, { content }),
    getMessages: (sessionId: number) =>
      apiClient.get(`/api/chat/sessions/${sessionId}/messages`),
    evolveSkill: (sessionId: number) =>
      apiClient.post(`/api/chat/sessions/${sessionId}/evolve-skill`),
  },

  // Memories
  memories: {
    list: (projectId: string, type?: string) => {
      const params = type ? { memory_type: type } : {}
      return apiClient.get<Memory[]>(`/api/memory/project/${projectId}`, { params })
    },
    create: (projectId: string, data: Partial<Memory>) =>
      apiClient.post<Memory>(`/api/memory/create`, data),
    get: (memoryId: string) =>
      apiClient.get<Memory>(`/api/memory/${memoryId}`),
    delete: (memoryId: string) =>
      apiClient.delete(`/api/memory/${memoryId}`),
  },

  // Knowledge Graph
  knowledgeGraph: {
    getGraph: (projectId: number) =>
      apiClient.get(`/api/knowledge-graph/projects/${projectId}/graph`),
    getKeywords: (projectId: number, topK?: number) =>
      apiClient.get(`/api/knowledge-graph/projects/${projectId}/keywords`, {
        params: { top_k: topK || 50 }
      }),
    getDocumentEntities: (documentId: number) =>
      apiClient.get(`/api/knowledge-graph/documents/${documentId}/entities`),
    buildGraphForDocument: (documentId: number) =>
      apiClient.post(`/api/knowledge-graph-v2/build/${documentId}`),
    getGraphStats: () =>
      apiClient.get('/api/knowledge-graph-v2/stats'),
  },

  // Timeline
  timeline: {
    getEvents: (projectId: number) =>
      apiClient.get(`/api/timeline/projects/${projectId}/events`),
    getGroupedEvents: (projectId: number, groupBy?: string) =>
      apiClient.get(`/api/timeline/projects/${projectId}/events/grouped`, {
        params: { group_by: groupBy || 'year' }
      }),
  },
}

export default api
