import axios, { AxiosInstance } from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加认证 token
apiClient.interceptors.request.use(
  (config) => {
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

// 响应拦截器 - 统一处理响应
apiClient.interceptors.response.use(
  (response) => {
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
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ============================================
// 认证相关 API (修复后的端点)
// ============================================
export const authService = {
  login: (email: string, password: string) =>
    apiClient.post('/api/v1/auth/login', { email, password }),

  register: (email: string, username: string, password: string) =>
    apiClient.post('/api/v1/auth/register', { email, username, password }),

  logout: () =>
    apiClient.post('/api/v1/auth/logout'),

  getCurrentUser: () =>
    apiClient.get('/api/v1/auth/me'),
}

// ============================================
// 项目相关 API (修复后的端点)
// ============================================
export const projectsService = {
  getAll: () =>
    apiClient.get('/api/v1/projects'),

  getById: (id: number) =>
    apiClient.get(`/api/v1/projects/${id}`),

  create: (data: { name: string; description?: string }) =>
    apiClient.post('/api/v1/projects', data),

  update: (id: number, data: { name?: string; description?: string }) =>
    apiClient.put(`/api/v1/projects/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/api/v1/projects/${id}`),

  getStats: (id: number) =>
    apiClient.get(`/api/v1/projects/${id}/stats`),
}

// ============================================
// 文档相关 API (修复后的端点)
// ============================================
export const documentsService = {
  getAll: (projectId: number) =>
    apiClient.get(`/api/v1/projects/${projectId}/documents`),

  getById: (projectId: number, documentId: number) =>
    apiClient.get(`/api/v1/projects/${projectId}/documents/${documentId}`),

  upload: (projectId: number, file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post(`/api/v1/projects/${projectId}/documents/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      },
    })
  },

  delete: (projectId: number, documentId: number) =>
    apiClient.delete(`/api/v1/projects/${projectId}/documents/${documentId}`),

  process: (projectId: number, documentId: number) =>
    apiClient.post(`/api/v1/projects/${projectId}/documents/${documentId}/process`),

  getProcessingStatus: (projectId: number, documentId: number) =>
    apiClient.get(`/api/v1/projects/${projectId}/documents/${documentId}/status`),
}

// ============================================
// 知识图谱 API (修复后的端点 - 使用 v3)
// ============================================
export const knowledgeGraphService = {
  getData: (projectId: number, limit?: number) =>
    apiClient.get(`/api/knowledge-graph-v3/projects/${projectId}/graph`, {
      params: { limit },
    }),

  getNode: (projectId: number, nodeId: string) =>
    apiClient.get(`/api/knowledge-graph/nodes/${nodeId}`, {
      params: { project_id: projectId },
    }),

  searchNodes: (projectId: number, query: string) =>
    apiClient.get(`/api/knowledge-graph/search`, {
      params: { project_id: projectId, query },
    }),

  getStats: (projectId: number) =>
    apiClient.get(`/api/knowledge-graph-v3/projects/${projectId}/stats`),
}

// ============================================
// Dashboard API (修复后的端点)
// ============================================
export const dashboardService = {
  getStats: () =>
    apiClient.get('/api/v1/dashboard/stats'),

  getRecentProjects: (limit?: number) =>
    apiClient.get('/api/v1/dashboard/recent-projects', {
      params: { limit },
    }),

  getTrends: (days?: number) =>
    apiClient.get('/api/v1/dashboard/trends', {
      params: { days },
    }),
}

// ============================================
// 数据质量 API (修复后的端点)
// ============================================
export const qualityService = {
  getMetrics: (projectId: number) =>
    apiClient.get(`/api/quality/projects/${projectId}/metrics`),

  getDimensionCoverage: (projectId: number) =>
    apiClient.get(`/api/quality/projects/${projectId}/dimensions`),

  getIssues: (projectId: number) =>
    apiClient.get(`/api/quality/projects/${projectId}/issues`),
}

// ============================================
// Chat/RAG API (修复后的端点)
// ============================================
export const chatService = {
  sendMessage: (projectId: number, message: string, conversationId?: string) =>
    apiClient.post(`/api/chat/send`, {
      project_id: projectId,
      message,
      conversation_id: conversationId,
    }),

  getConversations: (projectId: number) =>
    apiClient.get(`/api/chat/conversations`, {
      params: { project_id: projectId },
    }),

  getConversation: (projectId: number, conversationId: string) =>
    apiClient.get(`/api/chat/conversations/${conversationId}`, {
      params: { project_id: projectId },
    }),

  deleteConversation: (projectId: number, conversationId: string) =>
    apiClient.delete(`/api/chat/conversations/${conversationId}`, {
      params: { project_id: projectId },
    }),
}

// ============================================
// Timeline API (修复后的端点)
// ============================================
export const timelineService = {
  getEvents: (projectId: number) =>
    apiClient.get(`/api/timeline/projects/${projectId}/events`),

  getEvent: (projectId: number, eventId: number) =>
    apiClient.get(`/api/timeline/events/${eventId}`, {
      params: { project_id: projectId },
    }),

  createEvent: (projectId: number, data: any) =>
    apiClient.post(`/api/timeline/projects/${projectId}/events`, data),
}

// ============================================
// Reports API (修复后的端点)
// ============================================
export const reportsService = {
  generate: (projectId: number, type: string, options?: any) =>
    apiClient.post(`/api/reports/generate`, {
      project_id: projectId,
      type,
      options,
    }),

  getAll: (projectId: number) =>
    apiClient.get(`/api/reports/projects/${projectId}/list`),

  getById: (projectId: number, reportId: number) =>
    apiClient.get(`/api/reports/${reportId}`, {
      params: { project_id: projectId },
    }),

  delete: (projectId: number, reportId: number) =>
    apiClient.delete(`/api/reports/${reportId}`, {
      params: { project_id: projectId },
    }),
}

// ============================================
// Analytics API (修复后的端点)
// ============================================
export const analyticsService = {
  getMetrics: (projectId: number) =>
    apiClient.get(`/api/analytics/projects/${projectId}/metrics`),

  getChartData: (projectId: number, chartType: string, params?: any) =>
    apiClient.get(`/api/analytics/projects/${projectId}/charts/${chartType}`, {
      params,
    }),
}

// ============================================
// Citations API (修复后的端点)
// ============================================
export const citationsService = {
  getAll: (projectId: number) =>
    apiClient.get(`/api/citations/projects/${projectId}/list`),

  getById: (projectId: number, citationId: number) =>
    apiClient.get(`/api/citations/${citationId}`, {
      params: { project_id: projectId },
    }),

  verify: (projectId: number, citationId: number) =>
    apiClient.post(`/api/citations/${citationId}/verify`, {
      project_id: projectId,
    }),
}

// ============================================
// Memory API (修复后的端点)
// ============================================
export const memoryService = {
  getAll: (projectId: number) =>
    apiClient.get(`/api/memory/projects/${projectId}/list`),

  add: (projectId: number, data: any) =>
    apiClient.post(`/api/memory/projects/${projectId}/add`, data),

  delete: (projectId: number, memoryId: number) =>
    apiClient.delete(`/api/memory/${memoryId}`, {
      params: { project_id: projectId },
    }),
}

// ============================================
// Business Analysis API (修复后的端点)
// ============================================
export const businessAnalysisService = {
  analyze: (projectId: number, options?: any) =>
    apiClient.post(`/api/business-analysis/analyze`, {
      project_id: projectId,
      ...options,
    }),

  getResults: (projectId: number) =>
    apiClient.get(`/api/business-analysis/projects/${projectId}/results`),
}

// ============================================
// Monitoring API (修复后的端点)
// ============================================
export const monitoringService = {
  getMetrics: () =>
    apiClient.get('/api/monitoring/metrics'),

  getHealth: () =>
    apiClient.get('/api/monitoring/health'),

  getLogs: (params?: any) =>
    apiClient.get('/api/monitoring/logs', { params }),
}

// ============================================
// Workflow API (修复后的端点)
// ============================================
export const workflowService = {
  getAll: (projectId: number) =>
    apiClient.get(`/api/workflows/projects/${projectId}/list`),

  getById: (projectId: number, workflowId: number) =>
    apiClient.get(`/api/workflows/${workflowId}`, {
      params: { project_id: projectId },
    }),

  create: (projectId: number, data: any) =>
    apiClient.post(`/api/workflows/projects/${projectId}/create`, data),

  execute: (projectId: number, workflowId: number, params?: any) =>
    apiClient.post(`/api/workflows/${workflowId}/execute`, {
      project_id: projectId,
      ...params,
    }),

  getStatus: (projectId: number, workflowId: number, executionId: string) =>
    apiClient.get(`/api/workflows/${workflowId}/executions/${executionId}`, {
      params: { project_id: projectId },
    }),
}

// ============================================
// OCR API (修复后的端点)
// ============================================
export const ocrService = {
  process: (projectId: number, documentId: number) =>
    apiClient.post(`/api/ocr/process`, {
      project_id: projectId,
      document_id: documentId,
    }),

  getResult: (projectId: number, documentId: number) =>
    apiClient.get(`/api/ocr/results`, {
      params: { project_id: projectId, document_id: documentId },
    }),
}

// ============================================
// Visualization API (修复后的端点)
// ============================================
export const visualizationService = {
  generate: (projectId: number, type: string, options?: any) =>
    apiClient.post(`/api/visualize/generate`, {
      project_id: projectId,
      type,
      options,
    }),

  getAll: (projectId: number) =>
    apiClient.get(`/api/visualize/projects/${projectId}/list`),
}

// ============================================
// Batch Processing API (修复后的端点)
// ============================================
export const batchService = {
  createJob: (projectId: number, documents: number[]) =>
    apiClient.post(`/api/batch/jobs`, {
      project_id: projectId,
      document_ids: documents,
    }),

  getJob: (jobId: string) =>
    apiClient.get(`/api/batch/jobs/${jobId}`),

  getJobs: (projectId: number) =>
    apiClient.get(`/api/batch/projects/${projectId}/jobs`),
}

export default apiClient
