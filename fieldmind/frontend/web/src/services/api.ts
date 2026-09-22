/**
 * API Service for FieldMind Backend
 * Enhanced with error handling and performance tracking
 */
import axios from 'axios'
import { handleError } from '../utils/errorHandler'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Production warning: ensure VITE_API_BASE_URL is set in .env.production
if (import.meta.env.PROD && API_BASE_URL.includes('localhost')) {
  console.error('⚠️ Production build detected with localhost API URL. Set VITE_API_BASE_URL in .env.production');
}

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
    // 🔥 修复 307 重定向：自动添加尾部斜杠（彻底修复版）
    if (config.url) {
      // 先移除所有尾部斜杠（避免重复）
      config.url = config.url.replace(/\/+$/, '')

      // 分离路径和查询参数
      const urlParts = config.url.split('?')
      const path = urlParts[0]
      const query = urlParts[1]

      // 始终在路径末尾添加单个斜杠
      const normalizedPath = path + '/'

      // 重新组装完整 URL
      config.url = query ? `${normalizedPath}?${query}` : normalizedPath
    }

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

    // 🔥 自动解包 success_response 格式
    const responseData = response.data

    // 如果响应包含 success 和 data 字段，说明是新的统一响应格式
    if (responseData && typeof responseData === 'object' && 'success' in responseData && 'data' in responseData) {
      // 如果请求成功，直接返回 data 字段
      if (responseData.success === true) {
        return responseData.data
      }
      // 如果请求失败，抛出错误
      if (responseData.success === false && responseData.error) {
        const errorMsg = responseData.error.message || 'API request failed'
        throw new Error(errorMsg)
      }
    }

    // 兼容旧格式：直接返回 response.data
    return responseData
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
        `/api/v1/projects/${projectId}/documents/upload`,
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

  // Workflows - 工作流编排（支持legacy和v2架构）
  workflows: {
    // Legacy workflow执行
    execute: (data: {
      workflow_type: string
      project_id: number
      document_ids?: number[]
      params?: Record<string, any>
      use_v2_architecture?: boolean
    }) =>
      apiClient.post('/api/workflows/execute', data),

    // V2 workflow执行（完整6-Agent编排）
    executeV2: (data: {
      project_id: number
      document_ids?: number[]
      enable_chunking?: boolean
      enable_vectorization?: boolean
      enable_knowledge_graph?: boolean
      enable_skills_analysis?: boolean
      enable_synthesis?: boolean
      enable_report?: boolean
      report_type?: string
      report_level?: string
      async_mode?: boolean
    }) =>
      apiClient.post('/api/v2/workflows/execute', data),

    // 执行单个v2 Agent（用于测试）
    executeSingleAgent: (data: {
      agent_type: string
      project_id: number
      input_data?: Record<string, any>
      metadata?: Record<string, any>
    }) =>
      apiClient.post('/api/v2/workflows/execute_agent', data),

    // 获取workflow状态
    getStatus: (workflowId: string) =>
      apiClient.get(`/api/workflows/${workflowId}`),

    // 获取v2 workflow状态
    getV2Status: (workflowId: string) =>
      apiClient.get(`/api/v2/workflows/status/${workflowId}`),

    // 列出所有workflow
    list: (status?: string, limit?: number) =>
      apiClient.get('/api/workflows', {
        params: { status, limit }
      }),

    // 列出可用的v2 Agents
    listV2Agents: () =>
      apiClient.get('/api/v2/workflows/agents'),

    // 取消workflow
    cancel: (workflowId: string) =>
      apiClient.post(`/api/workflows/${workflowId}/cancel`),
  },

  // Batch Processing - 批量处理（支持v2架构）
  batch: {
    // 批量处理文档
    processDocuments: (data: {
      document_ids: number[]
      force_reprocess?: boolean
      use_v2_architecture?: boolean  // 新增：支持v2架构
    }) =>
      apiClient.post('/api/batch/process', data),

    // 处理整个项目
    processProject: (data: {
      project_id: number
      force_reprocess?: boolean
      use_v2_architecture?: boolean  // 新增：支持v2架构
    }) =>
      apiClient.post('/api/batch/process-project', data),

    // 获取批处理状态
    getStatus: (batchId: string) =>
      apiClient.get(`/api/batch/status/${batchId}`),
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

  // SuperAgents - AI-powered intelligent agents
  agents: {
    analyzeKnowledge: (request: import('../types/agents').KnowledgeAnalysisRequest) =>
      apiClient.post('/api/v1/agents/knowledge/analyze', request),
    search: (request: import('../types/agents').SearchQueryRequest) =>
      apiClient.post('/api/v1/agents/search/query', request),
    summarize: (request: import('../types/agents').SummaryRequest) =>
      apiClient.post('/api/v1/agents/summary/generate', request),
    transcribe: (request: import('../types/agents').TranscriptRequest) =>
      apiClient.post('/api/v1/agents/transcript/process', request),
    orchestrate: (request: import('../types/agents').OrchestrationRequest) =>
      apiClient.post('/api/v1/agents/orchestrate', request),
    getStatus: (executionId: string) =>
      apiClient.get(`/api/v1/agents/status/${executionId}`),
    checkHealth: () =>
      apiClient.get('/api/v1/agents/health'),
  },

  // Analytics - 数据分析（基于SQL聚合的真实统计）
  analytics: {
    getTopicDistribution: (projectId: number) =>
      apiClient.get(`/api/analytics/projects/${projectId}/topic-distribution`),
    getTopEntities: (projectId: number, entityType: string, topK: number = 10) =>
      apiClient.get(`/api/analytics/projects/${projectId}/top-entities`, {
        params: { entity_type: entityType, top_k: topK }
      }),
    getWordCountStats: (projectId: number) =>
      apiClient.get(`/api/analytics/projects/${projectId}/word-count-stats`),
    getTimelineDistribution: (projectId: number) =>
      apiClient.get(`/api/analytics/projects/${projectId}/timeline-distribution`),
    generateReport: (projectId: number, reportType: string = 'overview') =>
      apiClient.post(`/api/analytics/projects/${projectId}/generate-report`, null, {
        params: { report_type: reportType }
      }),
  },
}

export default api
