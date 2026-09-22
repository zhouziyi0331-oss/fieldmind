/**
 * SuperAgent Service Layer
 * Type-safe TypeScript SDK for Agent API calls
 */

import axios, { AxiosInstance } from 'axios'
import type {
  KnowledgeAnalysisRequest,
  KnowledgeAnalysisResponse,
  SearchQueryRequest,
  SearchQueryResponse,
  SummaryRequest,
  SummaryResponse,
  TranscriptRequest,
  TranscriptResponse,
  OrchestrationRequest,
  OrchestrationResponse,
  ExecutionStatusResponse,
  HealthCheckResponse,
  APIResponse,
  AgentAPIError as AgentAPIErrorType,
} from '../types/agents'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Production warning: ensure VITE_API_BASE_URL is set in .env.production
if (import.meta.env.PROD && API_BASE_URL.includes('localhost')) {
  console.error('⚠️ Production build detected with localhost API URL. Set VITE_API_BASE_URL in .env.production');
}

/**
 * SuperAgent API Client
 */
class SuperAgentClient {
  private client: AxiosInstance

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL: `${baseURL}/api/v1/agents`,
      timeout: 120000, // 2 minutes for agent operations
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Log request
        if (import.meta.env.DEV) {
          console.log(`🤖 Agent API: ${config.method?.toUpperCase()} ${config.url}`)
        }

        return config
      },
      (error) => {
        console.error('❌ Agent request error:', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Log response
        if (import.meta.env.DEV) {
          console.log(`✅ Agent API: ${response.config.url} completed`)
        }
        return response.data
      },
      (error) => {
        // Handle API errors
        if (error.response?.data?.error) {
          const apiError = new AgentAPIError(error.response.data.error)
          console.error('❌ Agent API error:', apiError)
          return Promise.reject(apiError)
        }
        return Promise.reject(error)
      }
    )
  }

  /**
   * Knowledge Agent: Deep document analysis
   */
  async analyzeKnowledge(
    request: KnowledgeAnalysisRequest
  ): Promise<APIResponse<KnowledgeAnalysisResponse>> {
    return this.client.post('/knowledge/analyze', request)
  }

  /**
   * Search Agent: Multi-source intelligent search
   */
  async searchQuery(
    request: SearchQueryRequest
  ): Promise<APIResponse<SearchQueryResponse>> {
    return this.client.post('/search/query', request)
  }

  /**
   * Summary Agent: Structured summarization
   */
  async generateSummary(
    request: SummaryRequest
  ): Promise<APIResponse<SummaryResponse>> {
    return this.client.post('/summary/generate', request)
  }

  /**
   * Transcript Agent: Audio/video transcription
   */
  async processTranscript(
    request: TranscriptRequest
  ): Promise<APIResponse<TranscriptResponse>> {
    return this.client.post('/transcript/process', request)
  }

  /**
   * Orchestration: Multi-agent coordination
   */
  async orchestrateAgents(
    request: OrchestrationRequest
  ): Promise<APIResponse<OrchestrationResponse>> {
    return this.client.post('/orchestrate', request)
  }

  /**
   * Get execution status
   */
  async getExecutionStatus(executionId: string): Promise<ExecutionStatusResponse> {
    return this.client.get(`/status/${executionId}`)
  }

  /**
   * Health check
   */
  async checkHealth(): Promise<HealthCheckResponse> {
    return this.client.get('/health')
  }

  /**
   * Poll execution status until completion
   * @param executionId - Execution ID to poll
   * @param intervalMs - Polling interval in milliseconds (default: 2000)
   * @param timeoutMs - Timeout in milliseconds (default: 300000 = 5 minutes)
   */
  async pollExecutionStatus(
    executionId: string,
    intervalMs: number = 2000,
    timeoutMs: number = 300000
  ): Promise<ExecutionStatusResponse> {
    const startTime = Date.now()

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const response = await this.getExecutionStatus(executionId)

          if (response.data.status === 'completed') {
            resolve(response)
            return
          }

          if (response.data.status === 'failed') {
            reject(new Error(response.data.error || 'Execution failed'))
            return
          }

          // Check timeout
          if (Date.now() - startTime > timeoutMs) {
            reject(new Error('Execution status polling timeout'))
            return
          }

          // Continue polling
          setTimeout(poll, intervalMs)
        } catch (error) {
          reject(error)
        }
      }

      poll()
    })
  }
}

/**
 * Custom error class for Agent API errors
 */
export class AgentAPIError extends Error implements AgentAPIErrorType {
  code: string
  details: Record<string, any>
  recoverySuggestions: string[]

  constructor(error: AgentAPIErrorType) {
    super(error.message)
    this.name = 'AgentAPIError'
    this.code = error.code
    this.details = error.details
    this.recoverySuggestions = error.recovery_suggestions || error.recoverySuggestions || []

    // Maintain proper prototype chain
    Object.setPrototypeOf(this, AgentAPIError.prototype)
  }

  /**
   * Get user-friendly error message with recovery suggestions
   */
  getUserMessage(): string {
    let message = this.message

    if (this.recoverySuggestions.length > 0) {
      message += '\n\n建议：\n'
      message += this.recoverySuggestions.map((s, i) => `${i + 1}. ${s}`).join('\n')
    }

    return message
  }
}

/**
 * Singleton instance
 */
export const superAgentClient = new SuperAgentClient()

/**
 * Convenience functions for direct use
 */
export const superAgents = {
  /**
   * Analyze documents with Knowledge Agent
   */
  analyzeKnowledge: (request: KnowledgeAnalysisRequest) =>
    superAgentClient.analyzeKnowledge(request),

  /**
   * Search with Search Agent
   */
  search: (request: SearchQueryRequest) =>
    superAgentClient.searchQuery(request),

  /**
   * Generate summary with Summary Agent
   */
  summarize: (request: SummaryRequest) =>
    superAgentClient.generateSummary(request),

  /**
   * Process audio/video with Transcript Agent
   */
  transcribe: (request: TranscriptRequest) =>
    superAgentClient.processTranscript(request),

  /**
   * Orchestrate multiple agents
   */
  orchestrate: (request: OrchestrationRequest) =>
    superAgentClient.orchestrateAgents(request),

  /**
   * Get execution status
   */
  getStatus: (executionId: string) =>
    superAgentClient.getExecutionStatus(executionId),

  /**
   * Poll execution status until completion
   */
  pollStatus: (executionId: string, intervalMs?: number, timeoutMs?: number) =>
    superAgentClient.pollExecutionStatus(executionId, intervalMs, timeoutMs),

  /**
   * Check agent health
   */
  checkHealth: () =>
    superAgentClient.checkHealth(),
}

export default superAgents
