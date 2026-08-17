/**
 * React Hooks for SuperAgents
 * Simplify agent calls in React components
 */

import { useState, useCallback } from 'react'
import { superAgents, AgentAPIError } from '../services/superAgents'
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
  APIResponse,
} from '../types/agents'

interface AgentState<T> {
  data: T | null
  loading: boolean
  error: AgentAPIError | Error | null
  executionId?: string
}

/**
 * Generic hook for agent operations
 */
function useAgentOperation<TRequest, TResponse>() {
  const [state, setState] = useState<AgentState<TResponse>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(
    async (
      operation: (request: TRequest) => Promise<APIResponse<TResponse>>,
      request: TRequest
    ) => {
      setState({ data: null, loading: true, error: null })

      try {
        const response = await operation(request)

        if (!response.success) {
          throw new Error(response.error?.message || 'Operation failed')
        }

        setState({
          data: response.data || null,
          loading: false,
          error: null,
        })

        return response.data
      } catch (error) {
        const agentError = error instanceof AgentAPIError
          ? error
          : new Error(error instanceof Error ? error.message : 'Unknown error')

        setState({
          data: null,
          loading: false,
          error: agentError,
        })

        throw agentError
      }
    },
    []
  )

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return {
    ...state,
    execute,
    reset,
  }
}

/**
 * Hook for Knowledge Agent
 */
export function useKnowledgeAgent() {
  const { data, loading, error, execute, reset } =
    useAgentOperation<KnowledgeAnalysisRequest, KnowledgeAnalysisResponse>()

  const analyze = useCallback(
    async (request: KnowledgeAnalysisRequest) => {
      return execute(superAgents.analyzeKnowledge, request)
    },
    [execute]
  )

  return {
    result: data,
    loading,
    error,
    analyze,
    reset,
  }
}

/**
 * Hook for Search Agent
 */
export function useSearchAgent() {
  const { data, loading, error, execute, reset } =
    useAgentOperation<SearchQueryRequest, SearchQueryResponse>()

  const search = useCallback(
    async (request: SearchQueryRequest) => {
      return execute(superAgents.search, request)
    },
    [execute]
  )

  return {
    result: data,
    loading,
    error,
    search,
    reset,
  }
}

/**
 * Hook for Summary Agent
 */
export function useSummaryAgent() {
  const { data, loading, error, execute, reset } =
    useAgentOperation<SummaryRequest, SummaryResponse>()

  const summarize = useCallback(
    async (request: SummaryRequest) => {
      return execute(superAgents.summarize, request)
    },
    [execute]
  )

  return {
    result: data,
    loading,
    error,
    summarize,
    reset,
  }
}

/**
 * Hook for Transcript Agent
 */
export function useTranscriptAgent() {
  const { data, loading, error, execute, reset } =
    useAgentOperation<TranscriptRequest, TranscriptResponse>()

  const transcribe = useCallback(
    async (request: TranscriptRequest) => {
      return execute(superAgents.transcribe, request)
    },
    [execute]
  )

  return {
    result: data,
    loading,
    error,
    transcribe,
    reset,
  }
}

/**
 * Hook for Agent Orchestration
 */
export function useAgentOrchestration() {
  const { data, loading, error, execute, reset } =
    useAgentOperation<OrchestrationRequest, OrchestrationResponse>()

  const orchestrate = useCallback(
    async (request: OrchestrationRequest) => {
      return execute(superAgents.orchestrate, request)
    },
    [execute]
  )

  return {
    result: data,
    loading,
    error,
    orchestrate,
    reset,
  }
}

/**
 * Hook for execution status polling
 */
export function useExecutionStatus() {
  const [state, setState] = useState<AgentState<ExecutionStatusResponse['data']>>({
    data: null,
    loading: false,
    error: null,
  })

  const poll = useCallback(
    async (executionId: string, intervalMs?: number, timeoutMs?: number) => {
      setState({ data: null, loading: true, error: null, executionId })

      try {
        const response = await superAgents.pollStatus(executionId, intervalMs, timeoutMs)

        setState({
          data: response.data,
          loading: false,
          error: null,
          executionId,
        })

        return response.data
      } catch (error) {
        const agentError = error instanceof AgentAPIError
          ? error
          : new Error(error instanceof Error ? error.message : 'Unknown error')

        setState({
          data: null,
          loading: false,
          error: agentError,
          executionId,
        })

        throw agentError
      }
    },
    []
  )

  const getStatus = useCallback(
    async (executionId: string) => {
      try {
        const response = await superAgents.getStatus(executionId)

        setState((prev) => ({
          ...prev,
          data: response.data,
          executionId,
        }))

        return response.data
      } catch (error) {
        const agentError = error instanceof AgentAPIError
          ? error
          : new Error(error instanceof Error ? error.message : 'Unknown error')

        setState((prev) => ({
          ...prev,
          error: agentError,
        }))

        throw agentError
      }
    },
    []
  )

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return {
    status: state.data,
    loading: state.loading,
    error: state.error,
    executionId: state.executionId,
    poll,
    getStatus,
    reset,
  }
}

/**
 * Hook for agent health monitoring
 */
export function useAgentHealth() {
  const [state, setState] = useState<{
    health: any | null
    loading: boolean
    error: Error | null
    lastCheck: Date | null
  }>({
    health: null,
    loading: false,
    error: null,
    lastCheck: null,
  })

  const checkHealth = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const health = await superAgents.checkHealth()

      setState({
        health,
        loading: false,
        error: null,
        lastCheck: new Date(),
      })

      return health
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Health check failed')

      setState((prev) => ({
        ...prev,
        loading: false,
        error: err,
        lastCheck: new Date(),
      }))

      throw err
    }
  }, [])

  return {
    health: state.health,
    loading: state.loading,
    error: state.error,
    lastCheck: state.lastCheck,
    checkHealth,
  }
}
