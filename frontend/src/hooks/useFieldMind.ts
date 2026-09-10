import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  projectsService,
  documentsService,
  knowledgeGraphService,
  dashboardService,
  qualityService,
  chatService,
  timelineService,
  reportsService,
  analyticsService,
  citationsService,
  memoryService,
  businessAnalysisService,
  monitoringService,
  workflowService,
  ocrService,
  visualizationService,
  authService,
} from '@/services/fieldmind'

// ============================================
// 认证 Hooks
// ============================================
export const useLogin = () => {
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
  })
}

export const useRegister = () => {
  return useMutation({
    mutationFn: ({
      email,
      username,
      password,
    }: {
      email: string
      username: string
      password: string
    }) => authService.register(email, username, password),
  })
}

export const useCurrentUser = () => {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: authService.getCurrentUser,
  })
}

// ============================================
// 项目 Hooks
// ============================================
export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],
    queryFn: projectsService.getAll,
  })
}

export const useProject = (id: number) => {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: () => projectsService.getById(id),
    enabled: !!id,
  })
}

export const useProjectStats = (id: number) => {
  return useQuery({
    queryKey: ['projects', id, 'stats'],
    queryFn: () => projectsService.getStats(id),
    enabled: !!id,
  })
}

export const useCreateProject = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: projectsService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export const useUpdateProject = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      projectsService.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['projects', variables.id] })
    },
  })
}

export const useDeleteProject = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: projectsService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

// ============================================
// 文档 Hooks
// ============================================
export const useDocuments = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'documents'],
    queryFn: () => documentsService.getAll(projectId),
    enabled: !!projectId,
  })
}

export const useDocument = (projectId: number, documentId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'documents', documentId],
    queryFn: () => documentsService.getById(projectId, documentId),
    enabled: !!projectId && !!documentId,
  })
}

export const useUploadDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, file }: { projectId: number; file: File }) =>
      documentsService.upload(projectId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'documents'],
      })
    },
  })
}

export const useDeleteDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      projectId,
      documentId,
    }: {
      projectId: number
      documentId: number
    }) => documentsService.delete(projectId, documentId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'documents'],
      })
    },
  })
}

export const useProcessDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      projectId,
      documentId,
    }: {
      projectId: number
      documentId: number
    }) => documentsService.process(projectId, documentId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'documents', variables.documentId],
      })
    },
  })
}

// ============================================
// 知识图谱 Hooks
// ============================================
export const useKnowledgeGraph = (projectId: number, limit?: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'knowledge-graph', limit],
    queryFn: () => knowledgeGraphService.getData(projectId, limit),
    enabled: !!projectId,
  })
}

export const useKnowledgeGraphNode = (projectId: number, nodeId: string) => {
  return useQuery({
    queryKey: ['projects', projectId, 'knowledge-graph', 'nodes', nodeId],
    queryFn: () => knowledgeGraphService.getNode(projectId, nodeId),
    enabled: !!projectId && !!nodeId,
  })
}

export const useSearchNodes = (projectId: number, query: string) => {
  return useQuery({
    queryKey: ['projects', projectId, 'knowledge-graph', 'search', query],
    queryFn: () => knowledgeGraphService.searchNodes(projectId, query),
    enabled: !!projectId && !!query,
  })
}

// ============================================
// Dashboard Hooks
// ============================================
export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardService.getStats,
  })
}

export const useRecentProjects = (limit?: number) => {
  return useQuery({
    queryKey: ['dashboard', 'recent-projects', limit],
    queryFn: () => dashboardService.getRecentProjects(limit),
  })
}

export const useTrends = (days?: number) => {
  return useQuery({
    queryKey: ['dashboard', 'trends', days],
    queryFn: () => dashboardService.getTrends(days),
  })
}

// ============================================
// 数据质量 Hooks
// ============================================
export const useDataQuality = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'quality'],
    queryFn: () => qualityService.getMetrics(projectId),
    enabled: !!projectId,
  })
}

export const useDimensionCoverage = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'quality', 'dimensions'],
    queryFn: () => qualityService.getDimensionCoverage(projectId),
    enabled: !!projectId,
  })
}

export const useQualityIssues = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'quality', 'issues'],
    queryFn: () => qualityService.getIssues(projectId),
    enabled: !!projectId,
  })
}

// ============================================
// Chat/RAG Hooks
// ============================================
export const useSendMessage = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      projectId,
      message,
      conversationId,
    }: {
      projectId: number
      message: string
      conversationId?: string
    }) => chatService.sendMessage(projectId, message, conversationId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'conversations'],
      })
    },
  })
}

export const useConversations = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'conversations'],
    queryFn: () => chatService.getConversations(projectId),
    enabled: !!projectId,
  })
}

export const useConversation = (projectId: number, conversationId: string) => {
  return useQuery({
    queryKey: ['projects', projectId, 'conversations', conversationId],
    queryFn: () => chatService.getConversation(projectId, conversationId),
    enabled: !!projectId && !!conversationId,
  })
}

// ============================================
// Timeline Hooks
// ============================================
export const useTimelineEvents = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'timeline'],
    queryFn: () => timelineService.getEvents(projectId),
    enabled: !!projectId,
  })
}

export const useCreateTimelineEvent = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: number; data: any }) =>
      timelineService.createEvent(projectId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'timeline'],
      })
    },
  })
}

// ============================================
// Reports Hooks
// ============================================
export const useReports = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'reports'],
    queryFn: () => reportsService.getAll(projectId),
    enabled: !!projectId,
  })
}

export const useReport = (projectId: number, reportId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'reports', reportId],
    queryFn: () => reportsService.getById(projectId, reportId),
    enabled: !!projectId && !!reportId,
  })
}

export const useGenerateReport = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      projectId,
      type,
      options,
    }: {
      projectId: number
      type: string
      options?: any
    }) => reportsService.generate(projectId, type, options),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'reports'],
      })
    },
  })
}

// ============================================
// Analytics Hooks
// ============================================
export const useAnalyticsMetrics = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'analytics'],
    queryFn: () => analyticsService.getMetrics(projectId),
    enabled: !!projectId,
  })
}

export const useChartData = (
  projectId: number,
  chartType: string,
  params?: any
) => {
  return useQuery({
    queryKey: ['projects', projectId, 'analytics', 'charts', chartType, params],
    queryFn: () => analyticsService.getChartData(projectId, chartType, params),
    enabled: !!projectId && !!chartType,
  })
}

// ============================================
// Citations Hooks
// ============================================
export const useCitations = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'citations'],
    queryFn: () => citationsService.getAll(projectId),
    enabled: !!projectId,
  })
}

// ============================================
// Memory Hooks
// ============================================
export const useMemories = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'memory'],
    queryFn: () => memoryService.getAll(projectId),
    enabled: !!projectId,
  })
}

export const useAddMemory = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: number; data: any }) =>
      memoryService.add(projectId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'memory'],
      })
    },
  })
}

// ============================================
// Business Analysis Hooks
// ============================================
export const useBusinessAnalysis = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'business-analysis'],
    queryFn: () => businessAnalysisService.getResults(projectId),
    enabled: !!projectId,
  })
}

export const useAnalyzeBusiness = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, options }: { projectId: number; options?: any }) =>
      businessAnalysisService.analyze(projectId, options),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'business-analysis'],
      })
    },
  })
}

// ============================================
// Monitoring Hooks
// ============================================
export const useMonitoringMetrics = () => {
  return useQuery({
    queryKey: ['monitoring', 'metrics'],
    queryFn: monitoringService.getMetrics,
  })
}

export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: monitoringService.getHealth,
    refetchInterval: 30000, // 每30秒检查一次
  })
}

// ============================================
// Workflow Hooks
// ============================================
export const useWorkflows = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'workflows'],
    queryFn: () => workflowService.getAll(projectId),
    enabled: !!projectId,
  })
}

export const useWorkflow = (projectId: number, workflowId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'workflows', workflowId],
    queryFn: () => workflowService.getById(projectId, workflowId),
    enabled: !!projectId && !!workflowId,
  })
}

export const useCreateWorkflow = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: number; data: any }) =>
      workflowService.create(projectId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'workflows'],
      })
    },
  })
}

export const useExecuteWorkflow = () => {
  return useMutation({
    mutationFn: ({
      projectId,
      workflowId,
      params,
    }: {
      projectId: number
      workflowId: number
      params?: any
    }) => workflowService.execute(projectId, workflowId, params),
  })
}

// ============================================
// Visualization Hooks
// ============================================
export const useVisualizations = (projectId: number) => {
  return useQuery({
    queryKey: ['projects', projectId, 'visualizations'],
    queryFn: () => visualizationService.getAll(projectId),
    enabled: !!projectId,
  })
}

export const useGenerateVisualization = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      projectId,
      type,
      options,
    }: {
      projectId: number
      type: string
      options?: any
    }) => visualizationService.generate(projectId, type, options),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'visualizations'],
      })
    },
  })
}
