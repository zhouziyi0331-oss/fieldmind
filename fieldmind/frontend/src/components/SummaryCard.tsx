/**
 * 文件缩影卡片组件
 * Summary Card Component
 *
 * 功能：
 * - 显示文档的知识缩影
 * - 一句话摘要、关键词、实体、主题
 * - 量化指标、维度标签、时空上下文
 * - 关联文档链接
 */

import React from 'react';
import { FileSummary } from '../types/summary';
import {
  FileTextOutlined,
  TagOutlined,
  UserOutlined,
  ClockCircleOutlined,
  EnvironmentOutlined,
  LinkOutlined,
  BarChartOutlined,
  FolderOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import './SummaryCard.css';

interface SummaryCardProps {
  summary: FileSummary;
  onClick?: (documentId: number) => void;
  onKeywordClick?: (keyword: string) => void;
  onRelatedClick?: (documentId: number) => void;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  summary,
  onClick,
  onKeywordClick,
  onRelatedClick
}) => {
  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // 格式化时间
  const formatDate = (dateStr?: string): string => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  // 获取状态标签样式
  const getStatusClass = (status: string): string => {
    switch (status) {
      case 'done': return 'status-done';
      case 'pending': return 'status-pending';
      case 'generating': return 'status-generating';
      case 'error': return 'status-error';
      default: return '';
    }
  };

  // 获取文件类型图标颜色
  const getFileTypeColor = (fileType: string): string => {
    if (fileType.includes('pdf')) return '#f5222d';
    if (fileType.includes('word') || fileType.includes('doc')) return '#1890ff';
    if (fileType.includes('excel') || fileType.includes('xls')) return '#52c41a';
    if (fileType.includes('audio') || fileType.includes('mp3')) return '#722ed1';
    if (fileType.includes('video') || fileType.includes('mp4')) return '#eb2f96';
    if (fileType.includes('image') || fileType.includes('jpg') || fileType.includes('png')) return '#13c2c2';
    return '#8c8c8c';
  };

  return (
    <div
      className={`summary-card ${summary.status}`}
      onClick={() => onClick?.(summary.document_id)}
    >
      {/* 卡片头部 */}
      <div className="summary-card-header">
        <div className="header-left">
          <FileTextOutlined
            style={{
              color: getFileTypeColor(summary.file_type),
              fontSize: '18px',
              marginRight: '8px'
            }}
          />
          <span className="document-title">{summary.document_title}</span>
        </div>
        <div className="header-right">
          <span className={`status-badge ${getStatusClass(summary.status)}`}>
            {summary.status === 'done' ? '缩影' :
             summary.status === 'pending' ? '待生成' :
             summary.status === 'generating' ? '生成中...' : '错误'}
          </span>
        </div>
      </div>

      {/* 一句话摘要 */}
      <div className="summary-card-body">
        <p className="one-line-summary">{summary.one_line_summary}</p>

        {/* 关键词 */}
        {summary.top_keywords && summary.top_keywords.length > 0 && (
          <div className="summary-section keywords-section">
            <TagOutlined className="section-icon" />
            <div className="keywords-container">
              {summary.top_keywords.map((kw, idx) => (
                <span
                  key={idx}
                  className="keyword-tag"
                  onClick={(e) => {
                    e.stopPropagation();
                    onKeywordClick?.(kw.word);
                  }}
                >
                  {kw.word}
                  {kw.count && <span className="keyword-count">({kw.count})</span>}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 核心主题 */}
        {summary.top_topics && summary.top_topics.length > 0 && (
          <div className="summary-section topics-section">
            <FolderOutlined className="section-icon" />
            <div className="topics-container">
              {summary.top_topics.map((topic, idx) => (
                <span key={idx} className="topic-tag">
                  {topic.topic_name}
                  <span className="topic-weight">({topic.weight})</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 核心实体 */}
        {summary.top_entities && summary.top_entities.length > 0 && (
          <div className="summary-section entities-section">
            <UserOutlined className="section-icon" />
            <div className="entities-container">
              {summary.top_entities.map((entity, idx) => (
                <span key={idx} className="entity-tag" title={`类型：${entity.type}，提及${entity.mention_count}次`}>
                  {entity.name}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 量化指标 */}
        <div className="summary-section metrics-section">
          <BarChartOutlined className="section-icon" />
          <div className="metrics-container">
            <span className="metric-item">
              📊 {summary.word_count.toLocaleString()}字
            </span>
            <span className="metric-divider">|</span>
            <span className="metric-item">
              📦 {summary.chunk_count}块
            </span>
            <span className="metric-divider">|</span>
            <span className="metric-item">
              📄 {summary.file_type}
            </span>
            <span className="metric-divider">|</span>
            <span className="metric-item">
              💾 {formatFileSize(summary.file_size)}
            </span>
          </div>
        </div>

        {/* 维度标签 */}
        <div className="summary-section dimensions-section">
          <span className="section-label">分类：</span>
          <span className="dimension-tag primary">{summary.primary_dimension}</span>
          {summary.secondary_dimensions && summary.secondary_dimensions.map((dim, idx) => (
            <span key={idx} className="dimension-tag secondary">{dim}</span>
          ))}
        </div>

        {/* 时空上下文 */}
        {(summary.time_start || summary.spatial_context) && (
          <div className="summary-section context-section">
            {summary.time_start && (
              <span className="context-item">
                <ClockCircleOutlined className="context-icon" />
                {summary.time_start}
                {summary.time_end && summary.time_end !== summary.time_start && ` - ${summary.time_end}`}
              </span>
            )}
            {summary.spatial_context && (
              <span className="context-item">
                <EnvironmentOutlined className="context-icon" />
                {summary.spatial_context}
              </span>
            )}
          </div>
        )}

        {/* 关联文档 */}
        {summary.related_documents && summary.related_documents.length > 0 && (
          <div className="summary-section related-section">
            <LinkOutlined className="section-icon" />
            <span className="section-label">关联：</span>
            {summary.related_documents.map((doc, idx) => (
              <span
                key={idx}
                className="related-tag"
                title={`相似度：${doc.similarity}，重叠关键词：${doc.overlap_keywords}个`}
                onClick={(e) => {
                  e.stopPropagation();
                  onRelatedClick?.(doc.document_id);
                }}
              >
                {doc.title}
                <span className="similarity-badge">{(doc.similarity * 100).toFixed(0)}%</span>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 卡片底部 */}
      <div className="summary-card-footer">
        <span className="footer-info">
          <CalendarOutlined className="footer-icon" />
          生成时间：{formatDate(summary.generated_at || summary.created_at)}
        </span>
      </div>
    </div>
  );
};

export default SummaryCard;
