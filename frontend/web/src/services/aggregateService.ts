/**
 * 数据聚合服务
 * 统一调用后端聚合API，确保所有模块看到的是同一份数据快照
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Production warning: ensure VITE_API_BASE_URL is set in .env.production
if (import.meta.env.PROD && API_BASE.includes('localhost')) {
  console.error('⚠️ Production build detected with localhost API URL. Set VITE_API_BASE_URL in .env.production');
}

export interface DashboardAggregate {
  project: {
    id: number;
    name: string;
    description: string | null;
    created_at: string;
  };

  summary: {
    total_docs: number;
    total_facts: number;
    total_vectors: number;
    total_entities: number;
    total_relations: number;
  };

  coverage: {
    timestamp_coverage: number;
    entity_coverage: number;
  };

  documents: {
    by_type: Record<string, number>;
    audio_files: Array<{
      id: number;
      filename: string;
      file_type: string;
      upload_time: string | null;
      status: string;
      audio_url: string | null;
    }>;
    recent_uploads: Array<{
      id: number;
      filename: string;
      file_type: string;
      status: string;
      upload_time: string | null;
    }>;
  };

  knowledge_graph: {
    top_entities: Array<{
      name: string;
      type: string;
      relation_count: number;
    }>;
  };

  health: {
    postgres: boolean;
    sqlite: boolean;
    chromadb: boolean;
    neo4j: boolean;
  };
}

export interface QuickStats {
  total_docs: number;
  total_facts: number;
  project_id: number;
}

/**
 * 获取完整的仪表盘数据
 * 这个接口会一次性返回所有模块需要的数据
 */
export async function getDashboardAggregate(projectId: number): Promise<DashboardAggregate> {
  const token = localStorage.getItem('token');

  const response = await fetch(`${API_BASE}/api/aggregate/dashboard/${projectId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`获取聚合数据失败: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 获取快速统计（用于顶部状态栏）
 */
export async function getQuickStats(projectId: number): Promise<QuickStats> {
  const token = localStorage.getItem('token');

  const response = await fetch(`${API_BASE}/api/aggregate/quick-stats/${projectId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`获取快速统计失败: ${response.statusText}`);
  }

  return response.json();
}
