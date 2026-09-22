/**
 * 文件缩影类型定义
 * File Summary Types
 */

/**
 * 关键词
 */
export interface Keyword {
  word: string;
  rank: number;
  tfidf?: number;
  count?: number;
}

/**
 * 实体
 */
export interface Entity {
  name: string;
  type: string;
  mention_count: number;
}

/**
 * 主题
 */
export interface Topic {
  topic_id: number;
  topic_name: string;
  weight: number;
}

/**
 * 事件
 */
export interface Event {
  name: string;
  date?: string;
  description?: string;
}

/**
 * 关联文档
 */
export interface RelatedDocument {
  document_id: number;
  title: string;
  similarity: number;
  overlap_keywords: number;
}

/**
 * 文件缩影
 */
export interface FileSummary {
  // 基础信息
  id: number;
  document_id: number;
  project_id: number;

  // 摘要内容
  one_line_summary: string;
  full_summary: string;

  // 核心信息
  top_keywords: Keyword[];
  top_entities: Entity[];
  top_topics: Topic[];
  top_events: Event[];

  // 量化指标
  word_count: number;
  chunk_count: number;
  avg_chunk_length: number;
  emotion_polarity?: number;
  subjectivity?: number;

  // 维度标签
  primary_dimension: string;
  secondary_dimensions: string[];

  // 时空上下文
  time_start?: string;
  time_end?: string;
  spatial_context?: string;

  // 关联文档
  related_documents: RelatedDocument[];

  // 状态
  status: 'pending' | 'generating' | 'done' | 'error';
  generated_at?: string;
  error_message?: string;

  // 时间戳
  created_at: string;
  updated_at: string;

  // 文档信息（来自 JOIN）
  document_title: string;
  file_type: string;
  file_size: number;
  document_created_at?: string;
}

/**
 * 缩影列表响应
 */
export interface SummaryListResponse {
  total: number;
  summaries: FileSummary[];
  skip: number;
  limit: number;
}

/**
 * 维度统计
 */
export interface DimensionStat {
  name: string;
  count: number;
}

/**
 * 缩影统计
 */
export interface SummaryStats {
  total_summaries: number;
  status_breakdown: {
    done?: number;
    pending?: number;
    error?: number;
  };
  avg_word_count: number;
}

/**
 * 缩影搜索参数
 */
export interface SummarySearchParams {
  project_id: number;
  skip?: number;
  limit?: number;
  q?: string;              // 关键词搜索
  dimension?: string;      // 维度筛选
  status?: string;         // 状态筛选
}
