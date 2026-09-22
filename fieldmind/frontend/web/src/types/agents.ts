/**
 * SuperAgent Type Definitions
 * TypeScript interfaces matching backend Pydantic models
 * Generated from: backend/src/app/schemas/agent_schemas.py
 */

// ============= Base Models =============

export interface AgentMetadata {
  plugins_used: string[]
  token_usage?: number
  execution_stages: string[]
  warnings: string[]
}

export interface AgentExecutionResult {
  agent_id: string
  status: 'success' | 'failed' | 'partial'
  execution_time: number
  timestamp: string
  metadata: AgentMetadata
}

// ============= Knowledge Agent =============

export interface KnowledgeAnalysisRequest {
  document_ids: number[]
  project_id?: number
  analysis_depth?: 'quick' | 'standard' | 'deep'
  focus_areas?: string[]
  use_plugins?: string[]
  max_entities?: number
}

export interface ExtractedEntity {
  name: string
  type: string
  description?: string
  confidence: number
  mentions: number
  document_ids: number[]
}

export interface ExtractedRelation {
  source: string
  target: string
  relation_type: string
  confidence: number
  evidence?: string
}

export interface KnowledgeAnalysisResult {
  entities: ExtractedEntity[]
  relations: ExtractedRelation[]
  themes: Array<Record<string, any>>
  key_insights: string[]
  document_summaries: Record<number, string>
  confidence_score: number
}

export interface KnowledgeAnalysisResponse extends AgentExecutionResult {
  result: KnowledgeAnalysisResult
  error?: string
}

// ============= Search Agent =============

export interface SearchQueryRequest {
  query: string
  project_id?: number
  search_scope?: 'documents' | 'knowledge_graph' | 'memory' | 'all'
  search_modes?: Array<'semantic' | 'keyword' | 'hybrid'>
  max_results?: number
  filters?: Record<string, any>
  use_plugins?: string[]
}

export interface SearchResultItem {
  id: string
  source_type: 'document' | 'entity' | 'memory' | 'relation'
  title: string
  content: string
  relevance_score: number
  metadata: Record<string, any>
  highlights?: string[]
}

export interface SearchQueryResult {
  results: SearchResultItem[]
  total_results: number
  search_time: number
  applied_filters: Record<string, any>
  suggestions: string[]
}

export interface SearchQueryResponse extends AgentExecutionResult {
  result: SearchQueryResult
  error?: string
}

// ============= Summary Agent =============

export interface SummaryRequest {
  content_ids: number[]
  content_type: 'documents' | 'chat_messages' | 'entities' | 'mixed'
  summary_style?: 'bullet_points' | 'paragraph' | 'executive' | 'technical'
  length?: 'brief' | 'medium' | 'detailed'
  focus_aspects?: string[]
  include_citations?: boolean
  use_plugins?: string[]
}

export interface SummarySection {
  title: string
  content: string
  importance: number
  citations?: string[]
}

export interface SummaryResult {
  summary_text: string
  sections: SummarySection[]
  key_points: string[]
  word_count: number
  reading_time_minutes: number
  citations: string[]
}

export interface SummaryResponse extends AgentExecutionResult {
  result: SummaryResult
  error?: string
}

// ============= Transcript Agent =============

export interface TranscriptRequest {
  audio_file_path?: string
  audio_url?: string
  video_file_path?: string
  video_url?: string
  language?: string
  enable_diarization?: boolean
  enable_timestamps?: boolean
  output_formats?: Array<'text' | 'srt' | 'vtt' | 'json'>
  use_plugins?: string[]
}

export interface TranscriptSegment {
  start_time: number
  end_time: number
  speaker?: string
  text: string
  confidence: number
}

export interface TranscriptResult {
  full_text: string
  segments: TranscriptSegment[]
  speakers_detected: string[]
  language_detected: string
  duration_seconds: number
  word_count: number
  formatted_outputs: Record<string, string>
}

export interface TranscriptResponse extends AgentExecutionResult {
  result: TranscriptResult
  error?: string
}

// ============= Orchestration =============

export interface AgentTask {
  agent_type: 'knowledge' | 'search' | 'summary' | 'transcript'
  task_id: string
  parameters: Record<string, any>
  dependencies?: string[]
  priority?: number
}

export interface OrchestrationRequest {
  tasks: AgentTask[]
  execution_mode: 'sequential' | 'parallel' | 'dag'
  project_id?: number
  timeout_seconds?: number
  failure_strategy?: 'stop_on_error' | 'continue_on_error' | 'retry_failed'
  max_retries?: number
}

export interface TaskResult {
  task_id: string
  agent_type: string
  status: 'success' | 'failed' | 'skipped'
  result?: any
  error?: string
  execution_time: number
}

export interface OrchestrationResult {
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  skipped_tasks: number
  task_results: TaskResult[]
  total_execution_time: number
  execution_graph?: Record<string, any>
}

export interface OrchestrationResponse extends AgentExecutionResult {
  result: OrchestrationResult
  error?: string
}

// ============= Execution Status =============

export interface ExecutionStatusRequest {
  execution_id: string
}

export interface ExecutionStatus {
  execution_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress_percentage: number
  current_stage?: string
  started_at: string
  completed_at?: string
  result?: any
  error?: string
}

export interface ExecutionStatusResponse {
  success: boolean
  data: ExecutionStatus
  timestamp: string
}

// ============= Health Check =============

export interface AgentHealthStatus {
  agent_type: string
  status: 'healthy' | 'degraded' | 'unavailable'
  last_check: string
  details?: Record<string, any>
}

export interface PluginHealthStatus {
  plugin_name: string
  status: 'available' | 'unavailable'
  version?: string
  last_check: string
}

export interface HealthCheckResponse {
  overall_status: 'healthy' | 'degraded' | 'unavailable'
  agents: AgentHealthStatus[]
  plugins: PluginHealthStatus[]
  timestamp: string
}

// ============= Unified API Response =============

export interface APIResponse<T = any> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details: Record<string, any>
    recovery_suggestions: string[]
  }
  timestamp: string
}

// ============= Error Types =============

export interface ErrorDetail {
  code: string
  message: string
  details: Record<string, any>
  recovery_suggestions: string[]
}

export class AgentAPIError extends Error {
  code: string
  details: Record<string, any>
  recoverySuggestions: string[]

  constructor(error: ErrorDetail) {
    super(error.message)
    this.name = 'AgentAPIError'
    this.code = error.code
    this.details = error.details
    this.recoverySuggestions = error.recovery_suggestions
  }
}
