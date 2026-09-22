/**
 * TraceabilityPanel - 溯源回溯面板
 *
 * 功能：
 * 1. 输入结论文本，追溯到原始 chunk
 * 2. 显示 chunk 在原文中的上下文
 * 3. 显示音频时间戳（如果有）
 * 4. 高亮显示匹配关键词
 * 5. 支持批量溯源
 */

import React, { useState } from 'react';
import axios from 'axios';

interface ChunkSource {
  chunk_id: number;
  chunk_content: string;
  chunk_index: number;
  match_score: number;
  matched_keywords: string[];
  document: {
    document_id: number;
    file_name: string;
    file_type: string;
  };
  context: {
    before: string;
    after: string;
  };
  audio_timestamp?: {
    start_time: number;
    end_time: number;
  };
}

interface TraceResult {
  conclusion_text: string;
  project_id: number;
  total_sources: number;
  sources: ChunkSource[];
}

interface TraceabilityPanelProps {
  projectId: number;
  onAudioSeek?: (documentId: number, timestamp: number) => void;
}

const TraceabilityPanel: React.FC<TraceabilityPanelProps> = ({
  projectId,
  onAudioSeek
}) => {
  const [conclusionText, setConclusionText] = useState('');
  const [traceResult, setTraceResult] = useState<TraceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<ChunkSource | null>(null);

  // 执行溯源
  const handleTrace = async () => {
    if (!conclusionText.trim()) {
      alert('请输入要溯源的结论文本');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await axios.post(`/api/v1/traceability/trace`, {
        conclusion_text: conclusionText,
        project_id: projectId,
        top_k: 10
      });
      setTraceResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || '溯源失败');
    } finally {
      setLoading(false);
    }
  };

  // 查看完整上下文
  const viewFullContext = async (source: ChunkSource) => {
    try {
      const response = await axios.get(
        `/api/v1/traceability/chunk/${source.chunk_id}/context?context_size=500`
      );
      setSelectedSource({
        ...source,
        context: response.data.context
      });
    } catch (err: any) {
      alert(err.response?.data?.detail || '加载上下文失败');
    }
  };

  // 跳转到音频时间点
  const seekAudio = (source: ChunkSource) => {
    if (source.audio_timestamp && onAudioSeek) {
      onAudioSeek(source.document.document_id, source.audio_timestamp.start_time);
    }
  };

  // 高亮关键词
  const highlightKeywords = (text: string, keywords: string[]) => {
    if (!keywords || keywords.length === 0) return text;

    let highlightedText = text;
    keywords.forEach(keyword => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlightedText = highlightedText.replace(
        regex,
        '<mark style="background-color: #fff59d; padding: 2px 4px; border-radius: 2px;">$1</mark>'
      );
    });
    return highlightedText;
  };

  // 格式化时间戳
  const formatTimestamp = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="traceability-panel" style={{ padding: '20px' }}>
      {/* 标题 */}
      <h2 style={{ marginBottom: '20px' }}>🔍 溯源回溯</h2>

      {/* 输入区域 */}
      <div style={{
        backgroundColor: '#fff',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
          输入结论或洞察文本：
        </label>
        <textarea
          value={conclusionText}
          onChange={(e) => setConclusionText(e.target.value)}
          placeholder="例如：社区居民普遍认为需要增加公共活动空间..."
          style={{
            width: '100%',
            minHeight: '120px',
            padding: '12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px',
            fontFamily: 'inherit',
            resize: 'vertical'
          }}
        />
        <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
          <button
            onClick={handleTrace}
            disabled={loading || !conclusionText.trim()}
            style={{
              padding: '10px 24px',
              backgroundColor: loading ? '#95a5a6' : '#3498db',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 'bold'
            }}
          >
            {loading ? '溯源中...' : '开始溯源'}
          </button>
          <button
            onClick={() => {
              setConclusionText('');
              setTraceResult(null);
              setError(null);
            }}
            style={{
              padding: '10px 24px',
              backgroundColor: '#ecf0f1',
              color: '#34495e',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            清空
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#fadbd8',
          color: '#c0392b',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          ❌ {error}
        </div>
      )}

      {/* 溯源结果 */}
      {traceResult && (
        <div>
          {/* 结果统计 */}
          <div style={{
            backgroundColor: '#e8f8f5',
            padding: '15px',
            borderRadius: '4px',
            marginBottom: '20px',
            borderLeft: '4px solid #27ae60'
          }}>
            <strong>找到 {traceResult.total_sources} 个相关来源</strong>
          </div>

          {/* 来源列表 */}
          {traceResult.sources.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '50px',
              color: '#95a5a6'
            }}>
              未找到相关来源
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {traceResult.sources.map((source) => (
                <div
                  key={source.chunk_id}
                  style={{
                    backgroundColor: '#fff',
                    padding: '20px',
                    borderRadius: '8px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    border: '1px solid #ecf0f1'
                  }}
                >
                  {/* 来源头部 */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '15px'
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{
                          fontSize: '16px',
                          fontWeight: 'bold',
                          color: '#2c3e50'
                        }}>
                          📄 {source.document.file_name}
                        </span>
                        <span style={{
                          padding: '2px 8px',
                          backgroundColor: '#ecf0f1',
                          borderRadius: '4px',
                          fontSize: '12px',
                          color: '#7f8c8d'
                        }}>
                          Chunk #{source.chunk_index}
                        </span>
                      </div>
                      <div style={{ marginTop: '5px', fontSize: '12px', color: '#95a5a6' }}>
                        匹配度：
                        <span style={{
                          color: source.match_score >= 0.7 ? '#27ae60' :
                                 source.match_score >= 0.5 ? '#f39c12' : '#e74c3c',
                          fontWeight: 'bold',
                          marginLeft: '5px'
                        }}>
                          {(source.match_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* 操作按钮 */}
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => viewFullContext(source)}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#3498db',
                          color: '#fff',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        查看上下文
                      </button>
                      {source.audio_timestamp && (
                        <button
                          onClick={() => seekAudio(source)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#9b59b6',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          🎵 {formatTimestamp(source.audio_timestamp.start_time)}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* 匹配的关键词 */}
                  {source.matched_keywords.length > 0 && (
                    <div style={{ marginBottom: '15px' }}>
                      <span style={{ fontSize: '12px', color: '#7f8c8d' }}>匹配关键词：</span>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '5px' }}>
                        {source.matched_keywords.map((keyword, idx) => (
                          <span
                            key={idx}
                            style={{
                              padding: '4px 8px',
                              backgroundColor: '#fff3cd',
                              color: '#856404',
                              borderRadius: '4px',
                              fontSize: '12px'
                            }}
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Chunk 内容 */}
                  <div style={{
                    padding: '15px',
                    backgroundColor: '#f8f9fa',
                    borderRadius: '4px',
                    borderLeft: '3px solid #3498db'
                  }}>
                    <div
                      style={{ lineHeight: '1.6', color: '#2c3e50' }}
                      dangerouslySetInnerHTML={{
                        __html: highlightKeywords(source.chunk_content, source.matched_keywords)
                      }}
                    />
                  </div>

                  {/* 上下文预览 */}
                  {source.context && (source.context.before || source.context.after) && (
                    <div style={{ marginTop: '10px', fontSize: '12px', color: '#7f8c8d' }}>
                      {source.context.before && (
                        <div style={{ marginBottom: '5px' }}>
                          <span style={{ fontWeight: 'bold' }}>前文：</span>
                          <span>{source.context.before.substring(0, 100)}...</span>
                        </div>
                      )}
                      {source.context.after && (
                        <div>
                          <span style={{ fontWeight: 'bold' }}>后文：</span>
                          <span>{source.context.after.substring(0, 100)}...</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 完整上下文模态框 */}
      {selectedSource && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
          }}
          onClick={() => setSelectedSource(null)}
        >
          <div
            style={{
              backgroundColor: '#fff',
              padding: '30px',
              borderRadius: '8px',
              maxWidth: '800px',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 4px 16px rgba(0,0,0,0.2)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginBottom: '20px' }}>完整上下文</h3>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '14px', color: '#7f8c8d', marginBottom: '10px' }}>
                📄 {selectedSource.document.file_name} - Chunk #{selectedSource.chunk_index}
              </div>
            </div>

            <div style={{ lineHeight: '1.8', color: '#2c3e50' }}>
              {/* 前文 */}
              {selectedSource.context.before && (
                <div style={{ color: '#95a5a6', marginBottom: '10px' }}>
                  {selectedSource.context.before}
                </div>
              )}

              {/* 当前 chunk（高亮） */}
              <div
                style={{
                  padding: '15px',
                  backgroundColor: '#fff3cd',
                  borderRadius: '4px',
                  marginBottom: '10px'
                }}
                dangerouslySetInnerHTML={{
                  __html: highlightKeywords(selectedSource.chunk_content, selectedSource.matched_keywords)
                }}
              />

              {/* 后文 */}
              {selectedSource.context.after && (
                <div style={{ color: '#95a5a6' }}>
                  {selectedSource.context.after}
                </div>
              )}
            </div>

            <div style={{ marginTop: '20px', textAlign: 'right' }}>
              <button
                onClick={() => setSelectedSource(null)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#3498db',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TraceabilityPanel;
