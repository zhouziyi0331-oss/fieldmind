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

  try {
    console.log('[aggregateService] 请求 dashboard aggregate, projectId:', projectId);

    const response = await fetch(`${API_BASE}/api/aggregate/dashboard/${projectId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    console.log('[aggregateService] 响应状态:', response.status, response.statusText);
    console.log('[aggregateService] Content-Type:', response.headers.get('content-type'));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[aggregateService] 请求失败:', errorText);
      throw new Error(`获取聚合数据失败: ${response.statusText}`);
    }

    // 先获取文本，再解析JSON，以便调试
    const text = await response.text();
    console.log('[aggregateService] 响应长度:', text.length);

    let result;
    try {
      result = JSON.parse(text);
      console.log('[aggregateService] JSON解析成功');
    } catch (e) {
      console.error('[aggregateService] JSON解析失败:', e);
      console.error('[aggregateService] 原始响应:', text.substring(0, 200));
      throw new Error(`JSON解析失败: ${e instanceof Error ? e.message : String(e)}`);
    }

    // 如果后端返回标准格式 {success, data, message}，提取data字段
    if (result.success && result.data) {
      console.log('[aggregateService] 返回标准格式data');
      return result.data;
    }

    // 否则直接返回（兼容旧格式）
    console.log('[aggregateService] 返回原始结果');
    return result;

  } catch (error) {
    console.error('[aggregateService] getDashboardAggregate错误:', error);
    throw error;
  }
}

/**
 * 获取快速统计（用于顶部状态栏）
 */
export async function getQuickStats(projectId: number): Promise<QuickStats> {
  const token = localStorage.getItem('token');

  try {
    console.log('[aggregateService] 请求 quick stats, projectId:', projectId);

    const response = await fetch(`${API_BASE}/api/aggregate/quick-stats/${projectId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    console.log('[aggregateService] Quick Stats 响应状态:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[aggregateService] Quick Stats 请求失败:', errorText);
      throw new Error(`获取快速统计失败: ${response.statusText}`);
    }

    const text = await response.text();
    let result;

    try {
      result = JSON.parse(text);
    } catch (e) {
      console.error('[aggregateService] Quick Stats JSON解析失败:', e);
      throw new Error(`JSON解析失败: ${e instanceof Error ? e.message : String(e)}`);
    }

    // 如果后端返回标准格式 {success, data, message}，提取data字段
    if (result.success && result.data) {
      return result.data;
    }

    // 否则直接返回（兼容旧格式）
    return result;

  } catch (error) {
    console.error('[aggregateService] getQuickStats错误:', error);
    throw error;
  }
}
