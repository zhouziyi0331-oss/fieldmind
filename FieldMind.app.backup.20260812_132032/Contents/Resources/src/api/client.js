import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8765'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

// Ingest API
export const ingestAPI = {
  uploadFile: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/api/ingest/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  uploadBatch: (files) => {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })
    return apiClient.post('/api/ingest/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getTaskStatus: (taskId) => {
    return apiClient.get(`/api/ingest/task/${taskId}`)
  },

  listTasks: () => {
    return apiClient.get('/api/ingest/tasks')
  },
}

// Search API
export const searchAPI = {
  search: (query, mode = 'hybrid', mediaType = null, limit = 20) => {
    return apiClient.post('/api/search/', {
      query,
      mode,
      media_type: mediaType,
      limit,
    })
  },

  getStats: () => {
    return apiClient.get('/api/search/stats')
  },
}

// Graph API
export const graphAPI = {
  getTimeline: (theme = null, person = null) => {
    const params = {}
    if (theme) params.theme = theme
    if (person) params.person = person
    return apiClient.get('/api/graph/timeline', { params })
  },

  getGraphData: (mode = 'full', centerNode = null) => {
    const params = { mode }
    if (centerNode) params.center_node = centerNode
    return apiClient.get('/api/graph/nodes', { params })
  },

  executeCypher: (cypher) => {
    return apiClient.post('/api/graph/query', { cypher })
  },

  getStats: () => {
    return apiClient.get('/api/graph/stats')
  },
}

// Agent API
export const agentAPI = {
  chat: (message, history = [], useWeb = false) => {
    return apiClient.post('/api/agent/chat', {
      message,
      history,
      use_web: useWeb,
    })
  },

  healthCheck: () => {
    return apiClient.get('/api/agent/health')
  },
}

// System API
export const systemAPI = {
  getHealth: () => {
    return apiClient.get('/health')
  },

  getInfo: () => {
    return apiClient.get('/')
  },
}

export default apiClient
