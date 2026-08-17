export interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectStats {
  project_id: string;
  files: {
    total: number;
    by_type: Record<string, number>;
    by_status: Record<string, number>;
    ready_percentage: number;
  };
  conversations: {
    total: number;
    recent: Array<{
      id: string;
      title: string;
      updated_at: string;
    }>;
  };
  messages: {
    total: number;
    user: number;
    assistant: number;
    avg_per_conversation: number;
  };
  knowledge: {
    graph_nodes: number;
    graph_nodes_by_type: Record<string, number>;
    vector_documents: number;
  };
  activity: {
    last_activity: string | null;
    active_conversations_7d: number;
    is_active: boolean;
  };
}

export interface FileItem {
  id: string;
  project_id: string;
  filename: string;
  file_path: string;
  media_type: 'audio' | 'video' | 'image' | 'text';
  status: 'pending' | 'processing' | 'ready' | 'error';
  created_at: string;
  metadata?: any;
}

export interface Conversation {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: string;
  metadata?: {
    citations?: Array<{
      id: number;
      text: string;
      source: string;
      timestamp?: number;
      type: string;
    }>;
    tool_calls?: any[];
  };
}

export interface SearchResult {
  query: string;
  conversations: Array<{
    project_id: string;
    conversation_id: string;
    title: string;
    updated_at: string;
    match_type: string;
  }>;
  files: Array<{
    project_id: string;
    file_id: string;
    filename: string;
    media_type: string;
    status: string;
    match_type: string;
  }>;
  messages: Array<{
    project_id: string;
    conversation_id: string;
    conversation_title: string;
    message_id: string;
    role: string;
    context: string;
    timestamp: string;
    match_type: string;
  }>;
  total_results: number;
}

export interface GlobalStats {
  total_projects: number;
  total_conversations: number;
  total_files: number;
  total_messages: number;
  avg_conversations_per_project: number;
  avg_messages_per_conversation: number;
}
