/**
 * 文档列表页 - 缩影卡片视图
 * Documents Page with Summary Card View
 *
 * 功能：
 * - 显示文档缩影卡片列表
 * - 搜索缩影（FTS5 全文搜索）
 * - 维度筛选
 * - 状态筛选
 * - 点击跳转到文档详情
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Input,
  Select,
  Spin,
  Empty,
  Button,
  message,
  Space,
  Statistic,
  Row,
  Col,
  Card as AntCard
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  FileTextOutlined,
  FolderOutlined
} from '@ant-design/icons';
import SummaryCard from '../components/SummaryCard';
import { FileSummary, DimensionStat, SummaryStats } from '../types/summary';
import axios from 'axios';
import './DocumentsSummary.css';

const { Search } = Input;
const { Option } = Select;

export const DocumentsSummary: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  // 状态
  const [summaries, setSummaries] = useState<FileSummary[]>([]);
  const [dimensions, setDimensions] = useState<DimensionStat[]>([]);
  const [stats, setStats] = useState<SummaryStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDimension, setSelectedDimension] = useState<string | undefined>(undefined);
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>(undefined);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(50);

  // API 基础 URL
  const API_BASE_URL = 'http://localhost:8000';

  // 加载缩影列表
  const loadSummaries = async () => {
    if (!projectId) return;

    setLoading(true);
    try {
      const params: any = {
        skip,
        limit
      };

      if (searchQuery) params.q = searchQuery;
      if (selectedDimension) params.dimension = selectedDimension;
      if (selectedStatus) params.status = selectedStatus;

      const response = await axios.get(
        `${API_BASE_URL}/api/v1/file-summaries/projects/${projectId}/summaries`,
        { params }
      );

      if (response.data.success) {
        setSummaries(response.data.data.summaries);
        setTotal(response.data.data.total);
      } else {
        message.error('加载缩影失败');
      }
    } catch (error: any) {
      console.error('加载缩影失败:', error);
      message.error('加载缩影失败：' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 加载维度列表
  const loadDimensions = async () => {
    if (!projectId) return;

    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/file-summaries/projects/${projectId}/dimensions`
      );

      if (response.data.success) {
        setDimensions(response.data.data.dimensions);
      }
    } catch (error) {
      console.error('加载维度列表失败:', error);
    }
  };

  // 加载统计信息
  const loadStats = async () => {
    if (!projectId) return;

    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/file-summaries/projects/${projectId}/stats`
      );

      if (response.data.success) {
        setStats(response.data.data);
      }
    } catch (error) {
      console.error('加载统计信息失败:', error);
    }
  };

  // 初始化加载
  useEffect(() => {
    loadDimensions();
    loadStats();
  }, [projectId]);

  // 搜索和筛选变化时重新加载
  useEffect(() => {
    loadSummaries();
  }, [projectId, searchQuery, selectedDimension, selectedStatus, skip]);

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setSkip(0); // 重置分页
  };

  // 处理维度筛选
  const handleDimensionChange = (value: string | undefined) => {
    setSelectedDimension(value);
    setSkip(0);
  };

  // 处理状态筛选
  const handleStatusChange = (value: string | undefined) => {
    setSelectedStatus(value);
    setSkip(0);
  };

  // 点击卡片跳转到文档详情
  const handleCardClick = (documentId: number) => {
    navigate(`/documents/${documentId}`);
  };

  // 点击关键词搜索
  const handleKeywordClick = (keyword: string) => {
    setSearchQuery(keyword);
    setSkip(0);
  };

  // 点击关联文档跳转
  const handleRelatedClick = (documentId: number) => {
    navigate(`/documents/${documentId}`);
  };

  // 刷新
  const handleRefresh = () => {
    loadSummaries();
    loadDimensions();
    loadStats();
    message.success('已刷新');
  };

  // 重置筛选
  const handleReset = () => {
    setSearchQuery('');
    setSelectedDimension(undefined);
    setSelectedStatus(undefined);
    setSkip(0);
  };

  return (
    <div className="documents-summary-page">
      {/* 页面标题 */}
      <div className="page-header">
        <div className="header-left">
          <h1 className="page-title">
            <FileTextOutlined style={{ marginRight: '12px' }} />
            文档缩影
          </h1>
          <p className="page-description">
            查看项目中所有文档的知识缩影，快速了解文档内容
          </p>
        </div>
        <div className="header-right">
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={8}>
            <AntCard>
              <Statistic
                title="总缩影数"
                value={stats.total_summaries}
                prefix={<FileTextOutlined />}
              />
            </AntCard>
          </Col>
          <Col xs={24} sm={8}>
            <AntCard>
              <Statistic
                title="已完成"
                value={stats.status_breakdown.done || 0}
                valueStyle={{ color: '#3f8600' }}
              />
            </AntCard>
          </Col>
          <Col xs={24} sm={8}>
            <AntCard>
              <Statistic
                title="平均字数"
                value={stats.avg_word_count}
                suffix="字"
              />
            </AntCard>
          </Col>
        </Row>
      )}

      {/* 搜索和筛选栏 */}
      <div className="search-filter-bar">
        <div className="search-section">
          <Search
            placeholder="搜索关键词、主题、实体..."
            allowClear
            enterButton={<SearchOutlined />}
            size="large"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onSearch={handleSearch}
            style={{ width: '100%', maxWidth: '600px' }}
          />
        </div>

        <div className="filter-section">
          <Space size="middle" wrap>
            <Select
              placeholder="全部维度"
              allowClear
              style={{ width: 160 }}
              value={selectedDimension}
              onChange={handleDimensionChange}
            >
              {dimensions.map(dim => (
                <Option key={dim.name} value={dim.name}>
                  <FolderOutlined style={{ marginRight: '6px' }} />
                  {dim.name} ({dim.count})
                </Option>
              ))}
            </Select>

            <Select
              placeholder="全部状态"
              allowClear
              style={{ width: 140 }}
              value={selectedStatus}
              onChange={handleStatusChange}
            >
              <Option value="done">已完成</Option>
              <Option value="pending">待生成</Option>
              <Option value="generating">生成中</Option>
              <Option value="error">错误</Option>
            </Select>

            {(searchQuery || selectedDimension || selectedStatus) && (
              <Button onClick={handleReset}>重置筛选</Button>
            )}
          </Space>
        </div>

        <div className="result-count">
          找到 <strong>{total}</strong> 个缩影
        </div>
      </div>

      {/* 缩影卡片列表 */}
      <div className="summaries-container">
        {loading ? (
          <div className="loading-container">
            <Spin size="large" tip="加载中..." />
          </div>
        ) : summaries.length === 0 ? (
          <Empty
            description={
              searchQuery || selectedDimension || selectedStatus
                ? '没有找到符合条件的缩影'
                : '暂无文档缩影'
            }
            style={{ marginTop: '60px' }}
          >
            {!searchQuery && !selectedDimension && !selectedStatus && (
              <Button type="primary" onClick={() => navigate(`/projects/${projectId}/upload`)}>
                上传文档
              </Button>
            )}
          </Empty>
        ) : (
          <div className="summary-cards-list">
            {summaries.map(summary => (
              <SummaryCard
                key={summary.id}
                summary={summary}
                onClick={handleCardClick}
                onKeywordClick={handleKeywordClick}
                onRelatedClick={handleRelatedClick}
              />
            ))}
          </div>
        )}
      </div>

      {/* 分页（如果需要） */}
      {total > limit && (
        <div className="pagination-container">
          <Button
            disabled={skip === 0}
            onClick={() => setSkip(Math.max(0, skip - limit))}
          >
            上一页
          </Button>
          <span style={{ margin: '0 16px' }}>
            {skip + 1} - {Math.min(skip + limit, total)} / {total}
          </span>
          <Button
            disabled={skip + limit >= total}
            onClick={() => setSkip(skip + limit)}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  );
};

export default DocumentsSummary;
