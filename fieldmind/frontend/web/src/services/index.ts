/**
 * Services Index
 * Centralized exports for all service modules
 */

// Main API client
export { default as api } from './api'

// SuperAgents - dedicated SDK with additional features
export {
  superAgents,
  superAgentClient,
  AgentAPIError,
} from './superAgents'

// Other services
export { default as aggregateService } from './aggregateService'
export * from './auth'

// Re-export commonly used types
export type {
  Project,
  Document,
  Memory,
} from './api'

export type {
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
  APIResponse,
} from '../types/agents'
