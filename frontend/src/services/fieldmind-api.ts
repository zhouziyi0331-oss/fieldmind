/**
 * FieldMind 完整 API 服务
 * 连接所有后端 API 端点
 */

import { api } from './api'

// ==================== 认证 API ====================
export const authAPI = {
  register: (data: any) => api.post('/api/v1/auth/register', data),
  login: (data: any) => api.post('/api/v1/auth/login', data),
  logout: () => api.post('/api/v1/auth/logout'),
  getMe: () => api.get('/api/v1/auth/me'),
  refresh: () => api.post('/api/v1/auth/refresh'),
}

// ==================== 用户 API ====================
export const userAPI = {
  getProfile: () => api.get('/api/v1/users/me'),
  updateProfile: (data: any) => api.put('/api/v1/users/me', data),
  getUsers: (params?: any) => api.get('/api/v1/users', { params }),
  getUserById: (id: string) => api.get(`/api/v1/users/${id}`),
  createUser: (data: any) => api.post('/api/v1/users', data),
  updateUser: (id: string, data: any) => api.put(`/api/v1/users/${id}`, data),
  deleteUser: (id: string) => api.delete(`/api/v1/users/${id}`),
}

// ==================== 项目 API ====================
export const projectAPI = {
  getProjects: (params?: any) => api.get('/api/v1/projects', { params }),
  getProject: (id: string) => api.get(`/api/v1/projects/${id}`),
  createProject: (data: any) => api.post('/api/v1/projects', data),
  updateProject: (id: string, data: any) => api.put(`/api/v1/projects/${id}`, data),
  deleteProject: (id: string) => api.delete(`/api/v1/projects/${id}`),
  getProjectStats: (id: string) => api.get(`/api/v1/projects/${id}/stats`),
}

// ==================== 文档 API ====================
export const documentAPI = {
  getDocuments: (params?: any) => api.get('/api/v1/documents', { params }),
  getDocument: (id: string) => api.get(`/api/v1/documents/${id}`),
  createDocument: (data: any) => api.post('/api/v1/documents', data),
  updateDocument: (id: string, data: any) => api.put(`/api/v1/documents/${id}`, data),
  deleteDocument: (id: string) => api.delete(`/api/v1/documents/${id}`),
  uploadDocument: (file: File, projectId?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) formData.append('project_id', projectId)
    return api.post('/api/v1/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
}

// ==================== 知识图谱 API ====================
export const knowledgeGraphAPI = {
  // 传统知识图谱API (保留兼容性)
  getGraph: (projectId: string) => api.get(`/api/v1/knowledge-graph/${projectId}`),
  getEntities: (params?: any) => api.get('/api/v1/knowledge-graph/entities', { params }),
  getEntity: (id: string) => api.get(`/api/v1/knowledge-graph/entities/${id}`),
  createEntity: (data: any) => api.post('/api/v1/knowledge-graph/entities', data),
  updateEntity: (id: string, data: any) => api.put(`/api/v1/knowledge-graph/entities/${id}`, data),
  deleteEntity: (id: string) => api.delete(`/api/v1/knowledge-graph/entities/${id}`),
  getRelations: (params?: any) => api.get('/api/v1/knowledge-graph/relations', { params }),
  createRelation: (data: any) => api.post('/api/v1/knowledge-graph/relations', data),
  deleteRelation: (id: string) => api.delete(`/api/v1/knowledge-graph/relations/${id}`),

  // 🆕 9步骤统一知识图谱API
  // 获取文档的完整知识图谱（基于9步骤管道）
  getDocumentGraph: (dirtyDocId: number, params?: { include_steps?: string }) =>
    api.get(`/api/v1/knowledge-graph/document/${dirtyDocId}`, { params }),

  // 创建知识图谱快照（版本管理）
  createSnapshot: (dirtyDocId: number, name?: string) =>
    api.post(`/api/v1/knowledge-graph/document/${dirtyDocId}/snapshot`, { name }),

  // 获取所有快照列表
  getSnapshots: (dirtyDocId: number) =>
    api.get(`/api/v1/knowledge-graph/document/${dirtyDocId}/snapshots`),

  // 按层级获取图谱（1=核心层, 2=次要层, 3=细节层）
  getGraphByLayer: (dirtyDocId: number, layer: number) =>
    api.get(`/api/v1/knowledge-graph/document/${dirtyDocId}/layers`, { params: { layer } }),

  // 比较两个文档的知识图谱
  compareGraphs: (docId1: number, docId2: number) =>
    api.get('/api/v1/knowledge-graph/compare', { params: { doc1: docId1, doc2: docId2 } }),

  // 导出知识图谱（支持json, graphml, cypher格式）
  exportGraph: (dirtyDocId: number, format: 'json' | 'graphml' | 'cypher' = 'json') =>
    api.get(`/api/v1/knowledge-graph/document/${dirtyDocId}/export`, { params: { format } }),

  // 批量构建知识图谱
  batchBuildGraphs: (dirtyDocIds: number[]) =>
    api.post('/api/v1/knowledge-graph/batch-build', { dirty_doc_ids: dirtyDocIds }),

  // 获取图谱构建状态
  getBuildStatus: (taskId: string) =>
    api.get(`/api/v1/knowledge-graph/build-status/${taskId}`),

  // 🆕 手动添加节点和关系
  // 手动添加实体节点
  addManualEntity: (dirtyDocId: number, data: {
    entity_name: string
    entity_type: string
    importance_score?: number
    properties?: Record<string, any>
  }) => api.post(`/api/v1/knowledge-graph/document/${dirtyDocId}/manual/entity`, data),

  // 手动添加事件节点
  addManualEvent: (dirtyDocId: number, data: {
    event_title: string
    event_summary?: string
    event_5w1h?: Record<string, any>
  }) => api.post(`/api/v1/knowledge-graph/document/${dirtyDocId}/manual/event`, data),

  // 手动添加关系
  addManualRelation: (dirtyDocId: number, data: {
    source_id: number
    target_id: number
    relation_type: string
    confidence?: number
    properties?: Record<string, any>
  }) => api.post(`/api/v1/knowledge-graph/document/${dirtyDocId}/manual/relation`, data),

  // 删除节点
  deleteNode: (dirtyDocId: number, nodeId: string, nodeType: 'entity' | 'event') =>
    api.delete(`/api/v1/knowledge-graph/document/${dirtyDocId}/node/${nodeType}/${nodeId}`),

  // 更新节点
  updateNode: (dirtyDocId: number, nodeId: string, nodeType: 'entity' | 'event', data: any) =>
    api.put(`/api/v1/knowledge-graph/document/${dirtyDocId}/node/${nodeType}/${nodeId}`, data),
}

// ==================== 对话 API ====================
export const conversationAPI = {
  createConversation: (data: any) => api.post('/api/v1/conversation/conversations', data),
  getRecentConversations: () => api.get('/api/v1/conversation/conversations/recent'),
  searchConversations: (query: string) => api.post('/api/v1/conversation/conversations/search', { query }),
  getConversationByEntity: (entityName: string) => api.get(`/api/v1/conversation/conversations/entity/${entityName}`),
  getConversationById: (id: string) => api.get(`/api/v1/conversation/conversations/${id}`),
  updateConversation: (id: string, data: any) => api.put(`/api/v1/conversation/conversations/${id}`, data),
  deleteConversation: (id: string) => api.delete(`/api/v1/conversation/conversations/${id}`),
}

// ==================== 聊天 API ====================
export const chatAPI = {
  sendMessage: (conversationId: string, message: string) =>
    api.post(`/api/v1/project-chat/${conversationId}/message`, { message }),
  getMessages: (conversationId: string) =>
    api.get(`/api/v1/project-chat/${conversationId}/messages`),
  createSession: (projectId: string) =>
    api.post('/api/v1/project-chat/session', { project_id: projectId }),
}

// ==================== 工作流 API ====================
export const workflowAPI = {
  getWorkflows: (params?: any) => api.get('/api/v1/workflows', { params }),
  getWorkflow: (id: string) => api.get(`/api/v1/workflows/${id}`),
  createWorkflow: (data: any) => api.post('/api/v1/workflows', data),
  updateWorkflow: (id: string, data: any) => api.put(`/api/v1/workflows/${id}`, data),
  deleteWorkflow: (id: string) => api.delete(`/api/v1/workflows/${id}`),
  executeWorkflow: (id: string, data?: any) => api.post(`/api/v1/workflows/${id}/execute`, data),
  getWorkflowExecutions: (id: string) => api.get(`/api/v1/workflows/${id}/executions`),
}

// ==================== 仪表板 API ====================
export const dashboardAPI = {
  getStats: () => api.get('/api/v1/dashboard/stats'),
  getRecentActivity: () => api.get('/api/v1/dashboard/activity'),
  getProjectStats: (projectId: string) => api.get(`/api/v1/dashboard/projects/${projectId}/stats`),
}

// ==================== 搜索 API ====================
export const searchAPI = {
  search: (query: string, params?: any) =>
    api.post('/api/v1/search', { query, ...params }),
  advancedSearch: (filters: any) =>
    api.post('/api/v1/search/advanced', filters),
  keywordSearch: (keyword: string) =>
    api.get('/api/v1/search/keyword', { params: { q: keyword } }),
}

// ==================== 标注 API ====================
export const annotationAPI = {
  createAnnotation: (data: any) => api.post('/api/v1/annotation/annotations', data),
  getAnnotations: (params?: any) => api.get('/api/v1/annotation/annotations', { params }),
  getAnnotation: (id: string) => api.get(`/api/v1/annotation/annotations/${id}`),
  updateAnnotation: (id: string, data: any) => api.put(`/api/v1/annotation/annotations/${id}`, data),
  deleteAnnotation: (id: string) => api.delete(`/api/v1/annotation/annotations/${id}`),
  getTargetAnnotations: (targetType: string, targetId: string) =>
    api.get(`/api/v1/annotation/annotations/target/${targetType}/${targetId}`),
}

// ==================== 审计 API ====================
export const auditAPI = {
  getLogs: (params?: any) => api.get('/api/v1/audit/logs', { params }),
  getResourceLogs: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/audit/resource/${resourceType}/${resourceId}`),
  getUserActivity: (userId: string) => api.get(`/api/v1/audit/user/${userId}/activity`),
  getStatistics: () => api.get('/api/v1/audit/statistics'),
  cleanup: (days: number) => api.delete(`/api/v1/audit/cleanup?days=${days}`),
}

// ==================== 技能 API ====================
export const skillAPI = {
  getSkills: (params?: any) => api.get('/api/v1/skills', { params }),
  getSkill: (id: string) => api.get(`/api/v1/skills/${id}`),
  createSkill: (data: any) => api.post('/api/v1/skills', data),
  updateSkill: (id: string, data: any) => api.put(`/api/v1/skills/${id}`, data),
  deleteSkill: (id: string) => api.delete(`/api/v1/skills/${id}`),
  executeSkill: (id: string, data: any) => api.post(`/api/v1/skills/${id}/execute`, data),
}

// ==================== SOP API ====================
export const sopAPI = {
  getSOPs: (params?: any) => api.get('/api/v1/sop', { params }),
  getSOP: (id: string) => api.get(`/api/v1/sop/${id}`),
  createSOP: (data: any) => api.post('/api/v1/sop', data),
  updateSOP: (id: string, data: any) => api.put(`/api/v1/sop/${id}`, data),
  deleteSOP: (id: string) => api.delete(`/api/v1/sop/${id}`),
}

// ==================== 任务 API ====================
export const taskAPI = {
  getTasks: (params?: any) => api.get('/api/v1/tasks', { params }),
  getTask: (id: string) => api.get(`/api/v1/tasks/${id}`),
  createTask: (data: any) => api.post('/api/v1/tasks', data),
  updateTask: (id: string, data: any) => api.put(`/api/v1/tasks/${id}`, data),
  deleteTask: (id: string) => api.delete(`/api/v1/tasks/${id}`),
}

// ==================== 分析 API ====================
export const analyticsAPI = {
  getProjectAnalytics: (projectId: string) =>
    api.get(`/api/v1/analytics/projects/${projectId}`),
  getDocumentAnalytics: (documentId: string) =>
    api.get(`/api/v1/analytics/documents/${documentId}`),
  getUserAnalytics: (userId: string) =>
    api.get(`/api/v1/analytics/users/${userId}`),
  getSystemAnalytics: () => api.get('/api/v1/analytics/system'),
}

// ==================== 可视化 API ====================
export const visualizationAPI = {
  generateChart: (type: string, data: any) =>
    api.post('/api/v1/visualization/chart', { type, data }),
  getChartData: (chartId: string) =>
    api.get(`/api/v1/visualization/charts/${chartId}`),
}

// ==================== 业务分析 API ====================
export const businessAnalysisAPI = {
  getExistingAnalysis: (projectId: string) =>
    api.get(`/api/v1/business-analysis/projects/${projectId}/business-analysis/existing`),
  getPotentialAnalysis: (projectId: string) =>
    api.get(`/api/v1/business-analysis/projects/${projectId}/business-analysis/potential`),
  getAIEvaluation: (projectId: string, data: any) =>
    api.post(`/api/v1/business-analysis/projects/${projectId}/business-analysis/ai-evaluation`, data),
}

// ==================== 协作 API ====================
export const collaborationAPI = {
  getMembers: (projectId: string) =>
    api.get(`/api/v1/collaboration/projects/${projectId}/members`),
  addMember: (projectId: string, data: any) =>
    api.post(`/api/v1/collaboration/projects/${projectId}/members`, data),
  removeMember: (projectId: string, userId: string) =>
    api.delete(`/api/v1/collaboration/projects/${projectId}/members/${userId}`),
  updateMemberRole: (projectId: string, userId: string, role: string) =>
    api.put(`/api/v1/collaboration/projects/${projectId}/members/${userId}/role`, { role }),
  inviteMember: (projectId: string, email: string) =>
    api.post(`/api/v1/collaboration/projects/${projectId}/invites`, { email }),
  getActivityLog: (projectId: string) =>
    api.get(`/api/v1/collaboration/projects/${projectId}/activity-log`),
  checkPermission: (projectId: string, action: string) =>
    api.get(`/api/v1/collaboration/projects/${projectId}/permissions/check?action=${action}`),
}

// ==================== 音频 API ====================
export const audioAPI = {
  uploadAudio: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/v1/audio/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getStatus: (taskId: string) => api.get(`/api/v1/audio/status/${taskId}`),
  getList: () => api.get('/api/v1/audio/list'),
}

// ==================== 背景学习 API ====================
export const backgroundLearningAPI = {
  createTask: (data: any) => api.post('/api/v1/background-learning/tasks', data),
  executeTask: (taskId: string) => api.post(`/api/v1/background-learning/tasks/${taskId}/execute`),
  getTasks: (params?: any) => api.get('/api/v1/background-learning/tasks', { params }),
  createSchedule: (data: any) => api.post('/api/v1/background-learning/schedules', data),
  getInsights: (params?: any) => api.get('/api/v1/background-learning/insights', { params }),
  reviewInsight: (insightId: string, data: any) =>
    api.put(`/api/v1/background-learning/insights/${insightId}/review`, data),
}

// ==================== API 管理 ====================
export const apiManagementAPI = {
  getStats: () => api.get('/api/v1/api-management/stats'),
  getMetrics: () => api.get('/api/v1/api-management/metrics'),
  getLogs: (params?: any) => api.get('/api/v1/api-management/logs', { params }),
  resetRateLimit: (userId: string) => api.post(`/api/v1/api-management/rate-limit/reset?user_id=${userId}`),
  getConfig: () => api.get('/api/v1/api-management/config'),
  updateConfig: (data: any) => api.put('/api/v1/api-management/config', data),
  getHealth: async () => {
    const response: any = await api.get('/api/monitoring/health')
    // 后端返回的是标准 API Response 格式: { success, data, error, metadata }
    // 提取实际的健康检查数据
    return response.data || response
  },
  getEndpoints: () => api.get('/api/v1/api-management/endpoints'),
  getErrors: (params?: any) => api.get('/api/v1/api-management/errors', { params }),
  getPerformance: () => api.get('/api/v1/api-management/performance'),
}

// ==================== 分块量化 API ====================
export const chunksAPI = {
  getChunks: (params?: any) => api.get('/api/v1/chunks-quantification/chunks', { params }),
  createChunk: (data: any) => api.post('/api/v1/chunks-quantification/chunks', data),
  getChunk: (id: string) => api.get(`/api/v1/chunks-quantification/chunks/${id}`),
  updateChunk: (id: string, data: any) => api.put(`/api/v1/chunks-quantification/chunks/${id}`, data),
  quantifyChunk: (id: string) => api.post(`/api/v1/chunks-quantification/chunks/${id}/quantify`),
}

// ==================== 爬虫 API ====================
export const crawlerAPI = {
  createTask: (data: any) => api.post('/api/v1/crawler/tasks', data),
  getTasks: (params?: any) => api.get('/api/v1/crawler/tasks', { params }),
  getTask: (id: string) => api.get(`/api/v1/crawler/tasks/${id}`),
  startTask: (id: string) => api.post(`/api/v1/crawler/tasks/${id}/start`),
  stopTask: (id: string) => api.post(`/api/v1/crawler/tasks/${id}/stop`),
  getResults: (taskId: string) => api.get(`/api/v1/crawler/tasks/${taskId}/results`),
}

// ==================== 数据增强 API ====================
export const dataEnrichmentAPI = {
  enrichData: (data: any) => api.post('/api/v1/data-enrichment/enrich', data),
  getEnrichmentHistory: (params?: any) => api.get('/api/v1/data-enrichment/history', { params }),
}

// ==================== 数据质量 API ====================
export const dataQualityAPI = {
  checkQuality: (data: any) => api.post('/api/v1/data-quality/check', data),
  getReports: (params?: any) => api.get('/api/v1/data-quality/reports', { params }),
  getReport: (id: string) => api.get(`/api/v1/data-quality/reports/${id}`),
  createRule: (data: any) => api.post('/api/v1/data-quality/rules', data),
  getRules: () => api.get('/api/v1/data-quality/rules'),
}

// ==================== 增强聊天 API ====================
export const enhancedChatAPI = {
  createSession: (data: any) => api.post('/api/v1/enhanced-chat/sessions', data),
  getSessions: (params?: any) => api.get('/api/v1/enhanced-chat/sessions', { params }),
  getSession: (id: string) => api.get(`/api/v1/enhanced-chat/sessions/${id}`),
  sendMessage: (sessionId: string, data: any) => api.post(`/api/v1/enhanced-chat/sessions/${sessionId}/messages`, data),
  getMessages: (sessionId: string) => api.get(`/api/v1/enhanced-chat/sessions/${sessionId}/messages`),
  getSuggestions: (sessionId: string) => api.get(`/api/v1/enhanced-chat/sessions/${sessionId}/suggestions`),
  getContext: (sessionId: string) => api.get(`/api/v1/enhanced-chat/sessions/${sessionId}/context`),
  updateContext: (sessionId: string, data: any) => api.put(`/api/v1/enhanced-chat/sessions/${sessionId}/context`, data),
}

// ==================== 执行跟踪 API ====================
export const executionTrackingAPI = {
  createExecution: (data: any) => api.post('/api/v1/execution-tracking/executions', data),
  getExecutions: (params?: any) => api.get('/api/v1/execution-tracking/executions', { params }),
  getExecution: (id: string) => api.get(`/api/v1/execution-tracking/executions/${id}`),
  updateStatus: (id: string, status: string) => api.put(`/api/v1/execution-tracking/executions/${id}/status`, { status }),
  addLog: (id: string, log: any) => api.post(`/api/v1/execution-tracking/executions/${id}/logs`, log),
  getLogs: (id: string) => api.get(`/api/v1/execution-tracking/executions/${id}/logs`),
}

// ==================== 经验图谱 API ====================
export const experienceGraphAPI = {
  getGraph: (params?: any) => api.get('/api/v1/experience-graph', { params }),
  addExperience: (data: any) => api.post('/api/v1/experience-graph/experiences', data),
  linkExperiences: (data: any) => api.post('/api/v1/experience-graph/links', data),
}

// ==================== 反馈循环 API ====================
export const feedbackLoopsAPI = {
  createFeedback: (data: any) => api.post('/api/v1/feedback-loops/feedback', data),
  getFeedbacks: (params?: any) => api.get('/api/v1/feedback-loops/feedback', { params }),
  getFeedback: (id: string) => api.get(`/api/v1/feedback-loops/feedback/${id}`),
  processFeedback: (id: string) => api.post(`/api/v1/feedback-loops/feedback/${id}/process`),
  getLoops: () => api.get('/api/v1/feedback-loops/loops'),
  createLoop: (data: any) => api.post('/api/v1/feedback-loops/loops', data),
  getMetrics: (loopId: string) => api.get(`/api/v1/feedback-loops/loops/${loopId}/metrics`),
  getImprovements: (params?: any) => api.get('/api/v1/feedback-loops/improvements', { params }),
}

// ==================== 数据馈送 API ====================
export const feedingAPI = {
  createFeed: (data: any) => api.post('/api/v1/feeding/feeds', data),
  getFeeds: (params?: any) => api.get('/api/v1/feeding/feeds', { params }),
  getFeed: (id: string) => api.get(`/api/v1/feeding/feeds/${id}`),
  updateFeed: (id: string, data: any) => api.put(`/api/v1/feeding/feeds/${id}`, data),
  deleteFeed: (id: string) => api.delete(`/api/v1/feeding/feeds/${id}`),
  startFeed: (id: string) => api.post(`/api/v1/feeding/feeds/${id}/start`),
  stopFeed: (id: string) => api.post(`/api/v1/feeding/feeds/${id}/stop`),
  getFeedData: (feedId: string, params?: any) => api.get(`/api/v1/feeding/feeds/${feedId}/data`, { params }),
  testConnection: (data: any) => api.post('/api/v1/feeding/test-connection', data),
  getStatistics: (feedId: string) => api.get(`/api/v1/feeding/feeds/${feedId}/statistics`),
  refreshFeed: (id: string) => api.post(`/api/v1/feeding/feeds/${id}/refresh`),
}

// ==================== 治理验证 API ====================
export const governanceAPI = {
  validateData: (data: any) => api.post('/api/v1/governance-validation/validate', data),
  getRules: (params?: any) => api.get('/api/v1/governance-validation/rules', { params }),
  createRule: (data: any) => api.post('/api/v1/governance-validation/rules', data),
  updateRule: (id: string, data: any) => api.put(`/api/v1/governance-validation/rules/${id}`, data),
  deleteRule: (id: string) => api.delete(`/api/v1/governance-validation/rules/${id}`),
}

// ==================== 行业 API ====================
export const industryAPI = {
  getIndustries: () => api.get('/api/v1/industry/industries'),
  getIndustry: (id: string) => api.get(`/api/v1/industry/industries/${id}`),
  getKnowledgeBase: (industryId: string) => api.get(`/api/v1/industry/industries/${industryId}/knowledge-base`),
  searchIndustry: (query: string) => api.post('/api/v1/industry/search', { query }),
}

// ==================== 知识网络 API ====================
export const knowledgeNetworkAPI = {
  getNetwork: (params?: any) => api.get('/api/v1/knowledge-network', { params }),
  addNode: (data: any) => api.post('/api/v1/knowledge-network/nodes', data),
}

// ==================== 学习 API ====================
export const learningAPI = {
  createLearningTask: (data: any) => api.post('/api/v1/learning/tasks', data),
  getTasks: (params?: any) => api.get('/api/v1/learning/tasks', { params }),
  getTask: (id: string) => api.get(`/api/v1/learning/tasks/${id}`),
  startTask: (id: string) => api.post(`/api/v1/learning/tasks/${id}/start`),
  getModels: (params?: any) => api.get('/api/v1/learning/models', { params }),
  getModel: (id: string) => api.get(`/api/v1/learning/models/${id}`),
  trainModel: (id: string, data: any) => api.post(`/api/v1/learning/models/${id}/train`, data),
  evaluateModel: (id: string, data: any) => api.post(`/api/v1/learning/models/${id}/evaluate`, data),
  getMetrics: (modelId: string) => api.get(`/api/v1/learning/models/${modelId}/metrics`),
}

// ==================== 数据血缘 API ====================
export const lineageAPI = {
  getLineage: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/lineage/${resourceType}/${resourceId}`),
  createLineage: (data: any) => api.post('/api/v1/lineage', data),
  getUpstream: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/lineage/${resourceType}/${resourceId}/upstream`),
  getDownstream: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/lineage/${resourceType}/${resourceId}/downstream`),
  getImpactAnalysis: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/lineage/${resourceType}/${resourceId}/impact`),
  searchLineage: (query: string) => api.post('/api/v1/lineage/search', { query }),
  getGraph: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/lineage/${resourceType}/${resourceId}/graph`),
  updateLineage: (id: string, data: any) => api.put(`/api/v1/lineage/${id}`, data),
  deleteLineage: (id: string) => api.delete(`/api/v1/lineage/${id}`),
  validateLineage: (resourceType: string, resourceId: string) =>
    api.post(`/api/v1/lineage/${resourceType}/${resourceId}/validate`),
}

// ==================== 模式识别 API ====================
export const patternRecognitionAPI = {
  analyzePatterns: (data: any) => api.post('/api/v1/pattern-recognition/analyze', data),
  getPatterns: (params?: any) => api.get('/api/v1/pattern-recognition/patterns', { params }),
  getPattern: (id: string) => api.get(`/api/v1/pattern-recognition/patterns/${id}`),
  trainModel: (data: any) => api.post('/api/v1/pattern-recognition/train', data),
  predictPattern: (data: any) => api.post('/api/v1/pattern-recognition/predict', data),
}

// ==================== 权限 API ====================
export const permissionAPI = {
  getPermissions: (params?: any) => api.get('/api/v1/permissions', { params }),
  checkPermission: (resource: string, action: string) =>
    api.get(`/api/v1/permissions/check?resource=${resource}&action=${action}`),
  grantPermission: (data: any) => api.post('/api/v1/permissions/grant', data),
  revokePermission: (data: any) => api.post('/api/v1/permissions/revoke', data),
  getRoles: () => api.get('/api/v1/permissions/roles'),
  createRole: (data: any) => api.post('/api/v1/permissions/roles', data),
  updateRole: (id: string, data: any) => api.put(`/api/v1/permissions/roles/${id}`, data),
  deleteRole: (id: string) => api.delete(`/api/v1/permissions/roles/${id}`),
  assignRole: (userId: string, roleId: string) =>
    api.post('/api/v1/permissions/assign-role', { user_id: userId, role_id: roleId }),
  getUserPermissions: (userId: string) => api.get(`/api/v1/permissions/users/${userId}`),
  getResourcePermissions: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/permissions/resources/${resourceType}/${resourceId}`),
}

// ==================== RAG API ====================
export const ragAPI = {
  query: (data: any) => api.post('/api/v1/rag/query', data),
  indexDocument: (data: any) => api.post('/api/v1/rag/index', data),
  search: (query: string, params?: any) => api.post('/api/v1/rag/search', { query, ...params }),
}

// ==================== 报告 API ====================
export const reportAPI = {
  getReports: (params?: any) => api.get('/api/v1/reports', { params }),
  getReport: (id: string) => api.get(`/api/v1/reports/${id}`),
  createReport: (data: any) => api.post('/api/v1/reports', data),
  updateReport: (id: string, data: any) => api.put(`/api/v1/reports/${id}`, data),
  deleteReport: (id: string) => api.delete(`/api/v1/reports/${id}`),
  generateReport: (id: string) => api.post(`/api/v1/reports/${id}/generate`),
}

// ==================== 技能生成 API ====================
export const skillGenerationAPI = {
  generateSkill: (data: any) => api.post('/api/v1/skill-generation/generate', data),
  getGeneratedSkills: (params?: any) => api.get('/api/v1/skill-generation/skills', { params }),
  getSkill: (id: string) => api.get(`/api/v1/skill-generation/skills/${id}`),
  refineSkill: (id: string, data: any) => api.post(`/api/v1/skill-generation/skills/${id}/refine`, data),
  testSkill: (id: string, data: any) => api.post(`/api/v1/skill-generation/skills/${id}/test`, data),
  deploySkill: (id: string) => api.post(`/api/v1/skill-generation/skills/${id}/deploy`),
}

// ==================== 技能优化 API ====================
export const skillOptimizationAPI = {
  analyzeSkill: (skillId: string) => api.get(`/api/v1/skill-optimization/skills/${skillId}/analyze`),
  optimizeSkill: (skillId: string, data: any) => api.post(`/api/v1/skill-optimization/skills/${skillId}/optimize`, data),
  getOptimizations: (params?: any) => api.get('/api/v1/skill-optimization/optimizations', { params }),
  getOptimization: (id: string) => api.get(`/api/v1/skill-optimization/optimizations/${id}`),
  applyOptimization: (id: string) => api.post(`/api/v1/skill-optimization/optimizations/${id}/apply`),
  compareVersions: (skillId: string, version1: string, version2: string) =>
    api.get(`/api/v1/skill-optimization/skills/${skillId}/compare?v1=${version1}&v2=${version2}`),
  getMetrics: (skillId: string) => api.get(`/api/v1/skill-optimization/skills/${skillId}/metrics`),
  getBenchmarks: (skillId: string) => api.get(`/api/v1/skill-optimization/skills/${skillId}/benchmarks`),
}

// ==================== 超级智能体 API ====================
export const superAgentsAPI = {
  getAgents: (params?: any) => api.get('/api/v1/super-agents', { params }),
  getAgent: (id: string) => api.get(`/api/v1/super-agents/${id}`),
  createAgent: (data: any) => api.post('/api/v1/super-agents', data),
  updateAgent: (id: string, data: any) => api.put(`/api/v1/super-agents/${id}`, data),
  deleteAgent: (id: string) => api.delete(`/api/v1/super-agents/${id}`),
  executeAgent: (id: string, data: any) => api.post(`/api/v1/super-agents/${id}/execute`, data),
  getAgentLogs: (id: string) => api.get(`/api/v1/super-agents/${id}/logs`),
}

// ==================== 标签 API ====================
export const taggingAPI = {
  getTags: (params?: any) => api.get('/api/v1/tagging/tags', { params }),
  getTag: (id: string) => api.get(`/api/v1/tagging/tags/${id}`),
  createTag: (data: any) => api.post('/api/v1/tagging/tags', data),
  updateTag: (id: string, data: any) => api.put(`/api/v1/tagging/tags/${id}`, data),
  deleteTag: (id: string) => api.delete(`/api/v1/tagging/tags/${id}`),
  tagResource: (data: any) => api.post('/api/v1/tagging/tag-resource', data),
  untagResource: (data: any) => api.post('/api/v1/tagging/untag-resource', data),
  getResourceTags: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/tagging/resources/${resourceType}/${resourceId}/tags`),
  searchByTags: (tags: string[]) => api.post('/api/v1/tagging/search', { tags }),
  suggestTags: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/tagging/suggest?resource_type=${resourceType}&resource_id=${resourceId}`),
  getTagCategories: () => api.get('/api/v1/tagging/categories'),
  bulkTag: (data: any) => api.post('/api/v1/tagging/bulk-tag', data),
}

// ==================== 主题分析 API ====================
export const topicAnalysisAPI = {
  analyzeTopics: (data: any) => api.post('/api/v1/topic-analysis/analyze', data),
  getTopics: (params?: any) => api.get('/api/v1/topic-analysis/topics', { params }),
  getTopic: (id: string) => api.get(`/api/v1/topic-analysis/topics/${id}`),
  getDocumentTopics: (documentId: string) => api.get(`/api/v1/topic-analysis/documents/${documentId}/topics`),
  getTopicDocuments: (topicId: string) => api.get(`/api/v1/topic-analysis/topics/${topicId}/documents`),
  getTopicTrends: (topicId: string) => api.get(`/api/v1/topic-analysis/topics/${topicId}/trends`),
  extractKeywords: (data: any) => api.post('/api/v1/topic-analysis/extract-keywords', data),
}

// ==================== 可追溯性 API ====================
export const traceabilityAPI = {
  getTrace: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/traceability/${resourceType}/${resourceId}`),
  createTrace: (data: any) => api.post('/api/v1/traceability', data),
  getHistory: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/traceability/${resourceType}/${resourceId}/history`),
  getChanges: (resourceType: string, resourceId: string) =>
    api.get(`/api/v1/traceability/${resourceType}/${resourceId}/changes`),
  compareVersions: (resourceType: string, resourceId: string, version1: string, version2: string) =>
    api.get(`/api/v1/traceability/${resourceType}/${resourceId}/compare?v1=${version1}&v2=${version2}`),
}

// ==================== 插件 API ====================
export const pluginsAPI = {
  getPlugins: (params?: any) => api.get('/api/v1/unified-plugins/plugins', { params }),
  getPlugin: (id: string) => api.get(`/api/v1/unified-plugins/plugins/${id}`),
  installPlugin: (data: any) => api.post('/api/v1/unified-plugins/plugins/install', data),
  uninstallPlugin: (id: string) => api.delete(`/api/v1/unified-plugins/plugins/${id}`),
  enablePlugin: (id: string) => api.post(`/api/v1/unified-plugins/plugins/${id}/enable`),
  disablePlugin: (id: string) => api.post(`/api/v1/unified-plugins/plugins/${id}/disable`),
  configurePlugin: (id: string, data: any) => api.put(`/api/v1/unified-plugins/plugins/${id}/config`, data),
  executePlugin: (id: string, data: any) => api.post(`/api/v1/unified-plugins/plugins/${id}/execute`, data),
}

// ==================== 用户分析 API ====================
export const userAnalysisAPI = {
  getUserAnalytics: (userId: string) => api.get(`/api/v1/user-analysis/users/${userId}/analytics`),
  getBehaviorPatterns: (userId: string) => api.get(`/api/v1/user-analysis/users/${userId}/behavior-patterns`),
  getActivityTimeline: (userId: string) => api.get(`/api/v1/user-analysis/users/${userId}/activity-timeline`),
  getUserSegments: () => api.get('/api/v1/user-analysis/segments'),
  segmentUsers: (criteria: any) => api.post('/api/v1/user-analysis/segment', criteria),
  getUserInsights: (userId: string) => api.get(`/api/v1/user-analysis/users/${userId}/insights`),
  getEngagementMetrics: (userId: string) => api.get(`/api/v1/user-analysis/users/${userId}/engagement`),
  predictUserBehavior: (userId: string, data: any) =>
    api.post(`/api/v1/user-analysis/users/${userId}/predict`, data),
  getRecommendations: (userId: string) => api.get(`/api/v1/user-analysis/users/${userId}/recommendations`),
}

// ==================== 工作台 API ====================
export const workbenchAPI = {
  getDashboard: () => api.get('/api/v1/workbench/dashboard'),
  getWidgets: () => api.get('/api/v1/workbench/widgets'),
  addWidget: (data: any) => api.post('/api/v1/workbench/widgets', data),
  removeWidget: (id: string) => api.delete(`/api/v1/workbench/widgets/${id}`),
  updateWidget: (id: string, data: any) => api.put(`/api/v1/workbench/widgets/${id}`, data),
  getQuickActions: () => api.get('/api/v1/workbench/quick-actions'),
  executeAction: (actionId: string, data?: any) => api.post(`/api/v1/workbench/actions/${actionId}`, data),
  getNotifications: (params?: any) => api.get('/api/v1/workbench/notifications', { params }),
  markNotificationRead: (id: string) => api.put(`/api/v1/workbench/notifications/${id}/read`),
  getRecentItems: (type: string) => api.get(`/api/v1/workbench/recent/${type}`),
  getFavorites: () => api.get('/api/v1/workbench/favorites'),
  addFavorite: (data: any) => api.post('/api/v1/workbench/favorites', data),
  removeFavorite: (id: string) => api.delete(`/api/v1/workbench/favorites/${id}`),
  getWorkspaces: () => api.get('/api/v1/workbench/workspaces'),
  createWorkspace: (data: any) => api.post('/api/v1/workbench/workspaces', data),
  switchWorkspace: (id: string) => api.post(`/api/v1/workbench/workspaces/${id}/switch`),
  getSettings: () => api.get('/api/v1/workbench/settings'),
  updateSettings: (data: any) => api.put('/api/v1/workbench/settings', data),
  search: (query: string) => api.post('/api/v1/workbench/search', { query }),
  getShortcuts: () => api.get('/api/v1/workbench/shortcuts'),
}

// 导出所有 API
export default {
  auth: authAPI,
  user: userAPI,
  project: projectAPI,
  document: documentAPI,
  knowledgeGraph: knowledgeGraphAPI,
  conversation: conversationAPI,
  chat: chatAPI,
  workflow: workflowAPI,
  dashboard: dashboardAPI,
  search: searchAPI,
  annotation: annotationAPI,
  audit: auditAPI,
  skill: skillAPI,
  sop: sopAPI,
  task: taskAPI,
  analytics: analyticsAPI,
  visualization: visualizationAPI,
  businessAnalysis: businessAnalysisAPI,
  collaboration: collaborationAPI,
  audio: audioAPI,
  backgroundLearning: backgroundLearningAPI,
  apiManagement: apiManagementAPI,
  chunks: chunksAPI,
  crawler: crawlerAPI,
  dataEnrichment: dataEnrichmentAPI,
  dataQuality: dataQualityAPI,
  enhancedChat: enhancedChatAPI,
  executionTracking: executionTrackingAPI,
  experienceGraph: experienceGraphAPI,
  feedbackLoops: feedbackLoopsAPI,
  feeding: feedingAPI,
  governance: governanceAPI,
  industry: industryAPI,
  knowledgeNetwork: knowledgeNetworkAPI,
  learning: learningAPI,
  lineage: lineageAPI,
  patternRecognition: patternRecognitionAPI,
  permission: permissionAPI,
  rag: ragAPI,
  report: reportAPI,
  skillGeneration: skillGenerationAPI,
  skillOptimization: skillOptimizationAPI,
  superAgents: superAgentsAPI,
  tagging: taggingAPI,
  topicAnalysis: topicAnalysisAPI,
  traceability: traceabilityAPI,
  plugins: pluginsAPI,
  userAnalysis: userAnalysisAPI,
  workbench: workbenchAPI,
}
