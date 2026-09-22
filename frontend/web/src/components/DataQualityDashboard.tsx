/**
 * DataQualityDashboard - 数据质量监控面板
 *
 * 功能：
 * 1. 显示项目整体质量评分（0-100分）
 * 2. 展示文档处理状态统计
 * 3. 标识数据缺口（未处理文档、失败文档）
 * 4. 提供重试功能
 * 5. 实时更新处理进度
 */

import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface QualityMetrics {
  overall_score: number;
  completeness_score: number;
  success_rate: number;
  coverage_score: number;
  quantification_score: number;
}

interface ProcessingStatus {
  total_documents: number;
  completed: number;
  processing: number;
  pending: number;
  error: number;
}

interface DataGap {
  document_id: number;
  file_name: string;
  issue_type: string;
  error_message?: string;
  uploaded_at: string;
}

interface QualityData {
  project_id: number;
  project_name: string;
  quality_score: QualityMetrics;
  processing_status: ProcessingStatus;
  data_gaps: DataGap[];
  last_updated: string;
}

interface DataQualityDashboardProps {
  projectId: number;
  autoRefresh?: boolean;
  refreshInterval?: number; // 秒
}

const DataQualityDashboard: React.FC<DataQualityDashboardProps> = ({
  projectId,
  autoRefresh = true,
  refreshInterval = 30
}) => {
  const [data, setData] = useState<QualityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryingDocs, setRetryingDocs] = useState<Set<number>>(new Set());

  // 获取数据质量数据
  const fetchQualityData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/v1/data-quality/overview/${projectId}`);
      setData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载数据质量数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 重试处理失败的文档
  const retryDocument = async (documentId: number) => {
    try {
      setRetryingDocs(prev => new Set(prev).add(documentId));
      await axios.post(`/api/v1/data-quality/retry/${projectId}/${documentId}`);
      // 重新获取数据
      await fetchQualityData();
    } catch (err: any) {
      alert(err.response?.data?.detail || '重试失败');
    } finally {
      setRetryingDocs(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
    }
  };

  // 批量重试所有失败文档
  const retryAllFailed = async () => {
    if (!data || data.data_gaps.length === 0) return;

    const failedDocs = data.data_gaps
      .filter(gap => gap.issue_type === 'processing_error')
      .map(gap => gap.document_id);

    if (failedDocs.length === 0) {
      alert('没有需要重试的文档');
      return;
    }

    if (!confirm(`确定要重试 ${failedDocs.length} 个失败的文档吗？`)) {
      return;
    }

    for (const docId of failedDocs) {
      await retryDocument(docId);
    }
  };

  useEffect(() => {
    fetchQualityData();

    if (autoRefresh) {
      const interval = setInterval(fetchQualityData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [projectId, autoRefresh, refreshInterval]);

  // 获取质量评分颜色
  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#27ae60'; // 绿色
    if (score >= 60) return '#f39c12'; // 橙色
    return '#e74c3c'; // 红色
  };

  // 获取状态徽章颜色
  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      completed: '#27ae60',
      processing: '#3498db',
      pending: '#95a5a6',
      error: '#e74c3c'
    };
    return colors[status] || '#95a5a6';
  };

  if (loading && !data) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <div className="spinner">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: '#e74c3c' }}>
        <h3>❌ 错误</h3>
        <p>{error}</p>
        <button onClick={fetchQualityData} style={{ marginTop: '10px' }}>
          重试
        </button>
      </div>
    );
  }

  if (!data) return null;

  const progressPercentage = data.processing_status.total_documents > 0
    ? (data.processing_status.completed / data.processing_status.total_documents) * 100
    : 0;

  return (
    <div className="data-quality-dashboard" style={{ padding: '20px' }}>
      {/* 标题栏 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h2>📊 数据质量监控</h2>
        <button
          onClick={fetchQualityData}
          disabled={loading}
          style={{
            padding: '8px 16px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          🔄 刷新
        </button>
      </div>

      {/* 整体质量评分卡片 */}
      <div style={{
        backgroundColor: '#fff',
        padding: '30px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        <h3 style={{ marginBottom: '20px' }}>整体质量评分</h3>
        <div style={{
          fontSize: '64px',
          fontWeight: 'bold',
          color: getScoreColor(data.quality_score.overall_score)
        }}>
          {data.quality_score.overall_score.toFixed(1)}
        </div>
        <div style={{ fontSize: '18px', color: '#666', marginTop: '10px' }}>
          / 100
        </div>

        {/* 分项评分 */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '20px',
          marginTop: '30px'
        }}>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>完整性（40%）</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '5px' }}>
              {data.quality_score.completeness_score.toFixed(1)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>成功率（30%）</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '5px' }}>
              {data.quality_score.success_rate.toFixed(1)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>覆盖度（20%）</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '5px' }}>
              {data.quality_score.coverage_score.toFixed(1)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#666' }}>量化度（10%）</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '5px' }}>
              {data.quality_score.quantification_score.toFixed(1)}
            </div>
          </div>
        </div>
      </div>

      {/* 处理状态统计 */}
      <div style={{
        backgroundColor: '#fff',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <h3 style={{ marginBottom: '20px' }}>📈 处理状态</h3>

        {/* 进度条 */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span>整体进度</span>
            <span>{progressPercentage.toFixed(1)}%</span>
          </div>
          <div style={{
            width: '100%',
            height: '24px',
            backgroundColor: '#ecf0f1',
            borderRadius: '12px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${progressPercentage}%`,
              height: '100%',
              backgroundColor: '#3498db',
              transition: 'width 0.3s ease'
            }}></div>
          </div>
        </div>

        {/* 状态统计 */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '15px'
        }}>
          <div style={{
            padding: '15px',
            borderRadius: '6px',
            backgroundColor: '#ecf0f1'
          }}>
            <div style={{ fontSize: '12px', color: '#666' }}>总文档数</div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '5px' }}>
              {data.processing_status.total_documents}
            </div>
          </div>
          <div style={{
            padding: '15px',
            borderRadius: '6px',
            backgroundColor: '#d5f4e6',
            borderLeft: `4px solid ${getStatusColor('completed')}`
          }}>
            <div style={{ fontSize: '12px', color: '#666' }}>已完成</div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '5px' }}>
              {data.processing_status.completed}
            </div>
          </div>
          <div style={{
            padding: '15px',
            borderRadius: '6px',
            backgroundColor: '#d6eaf8',
            borderLeft: `4px solid ${getStatusColor('processing')}`
          }}>
            <div style={{ fontSize: '12px', color: '#666' }}>处理中</div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '5px' }}>
              {data.processing_status.processing}
            </div>
          </div>
          <div style={{
            padding: '15px',
            borderRadius: '6px',
            backgroundColor: '#e8e8e8',
            borderLeft: `4px solid ${getStatusColor('pending')}`
          }}>
            <div style={{ fontSize: '12px', color: '#666' }}>待处理</div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '5px' }}>
              {data.processing_status.pending}
            </div>
          </div>
          <div style={{
            padding: '15px',
            borderRadius: '6px',
            backgroundColor: '#fadbd8',
            borderLeft: `4px solid ${getStatusColor('error')}`
          }}>
            <div style={{ fontSize: '12px', color: '#666' }}>失败</div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '5px' }}>
              {data.processing_status.error}
            </div>
          </div>
        </div>
      </div>

      {/* 数据缺口列表 */}
      {data.data_gaps.length > 0 && (
        <div style={{
          backgroundColor: '#fff',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3>⚠️ 数据缺口 ({data.data_gaps.length})</h3>
            <button
              onClick={retryAllFailed}
              style={{
                padding: '8px 16px',
                backgroundColor: '#3498db',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              批量重试
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #ecf0f1' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>文件名</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>问题类型</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>错误信息</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>上传时间</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {data.data_gaps.map((gap) => (
                  <tr key={gap.document_id} style={{ borderBottom: '1px solid #ecf0f1' }}>
                    <td style={{ padding: '12px' }}>{gap.file_name}</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        backgroundColor: gap.issue_type === 'processing_error' ? '#fadbd8' : '#fef5e7',
                        color: gap.issue_type === 'processing_error' ? '#c0392b' : '#d68910',
                        fontSize: '12px'
                      }}>
                        {gap.issue_type === 'processing_error' ? '处理失败' :
                         gap.issue_type === 'missing_content' ? '缺少内容' :
                         gap.issue_type === 'pending' ? '待处理' : gap.issue_type}
                      </span>
                    </td>
                    <td style={{ padding: '12px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      <span title={gap.error_message}>
                        {gap.error_message || '-'}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontSize: '12px', color: '#666' }}>
                      {new Date(gap.uploaded_at).toLocaleString('zh-CN')}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {gap.issue_type === 'processing_error' && (
                        <button
                          onClick={() => retryDocument(gap.document_id)}
                          disabled={retryingDocs.has(gap.document_id)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: retryingDocs.has(gap.document_id) ? '#95a5a6' : '#3498db',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: retryingDocs.has(gap.document_id) ? 'not-allowed' : 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          {retryingDocs.has(gap.document_id) ? '重试中...' : '重试'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 最后更新时间 */}
      <div style={{ marginTop: '20px', textAlign: 'center', color: '#95a5a6', fontSize: '12px' }}>
        最后更新：{new Date(data.last_updated).toLocaleString('zh-CN')}
      </div>
    </div>
  );
};

export default DataQualityDashboard;
