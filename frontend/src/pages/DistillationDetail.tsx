import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ExternalLink,
  FileText,
  User,
  Clock,
  MapPin,
  Link as LinkIcon,
  TrendingUp,
  Check,
  AlertCircle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface DistilledUnit {
  id: number;
  project_id: number;
  unit_type: string;
  title: string;
  content: string;
  credibility: number;
  confidence: number;
  source_chunks: string;
  extra_data: string;
  created_at: string;
}

interface Source {
  chunk_id: number;
  chunk_index: number;
  content: string;
  full_content: string;
  document_id: number;
  document_name: string;
  page_number?: number;
  speaker?: string;
  timestamp_start?: number;
  timestamp_end?: number;
  created_at: string;
}

export default function DistillationDetailPage() {
  const { projectId, unitId } = useParams<{ projectId: string; unitId: string }>();
  const navigate = useNavigate();

  const [unit, setUnit] = useState<DistilledUnit | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const [showAllSources, setShowAllSources] = useState(false);

  useEffect(() => {
    loadUnit();
    loadSources();
  }, [unitId]);

  const loadUnit = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/distilled-units/${unitId}`);
      if (!response.ok) {
        throw new Error('加载失败');
      }

      const data = await response.json();
      setUnit(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadSources = async () => {
    try {
      setSourcesLoading(true);

      const response = await fetch(`/api/distilled-units/${unitId}/sources`);
      if (response.ok) {
        const data = await response.json();
        setSources(data.sources || []);
      }
    } catch (err) {
      console.error('加载来源失败:', err);
    } finally {
      setSourcesLoading(false);
    }
  };

  const toggleSourceExpand = (chunkId: number) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(chunkId)) {
      newExpanded.delete(chunkId);
    } else {
      newExpanded.add(chunkId);
    }
    setExpandedSources(newExpanded);
  };

  const formatTime = (seconds?: number) => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTypeConfig = (type: string) => {
    const configs: Record<string, { name: string; color: string; icon: string }> = {
      insight: { name: '核心洞察', color: 'yellow', icon: '🔍' },
      quote: { name: '经典原话', color: 'blue', icon: '💬' },
      model: { name: '思维模型', color: 'purple', icon: '🧠' },
      case: { name: '案例应用', color: 'green', icon: '📚' },
      action: { name: '行动建议', color: 'red', icon: '⚡' },
      method: { name: '方法论', color: 'indigo', icon: '📖' }
    };
    return configs[type] || { name: '未知', color: 'gray', icon: '📄' };
  };

  const getCredibilityInfo = (score: number) => {
    if (score >= 0.8) {
      return { label: '高可信', color: 'green', icon: Check, description: '来源充分，证据确凿' };
    }
    if (score >= 0.5) {
      return { label: '中可信', color: 'yellow', icon: AlertCircle, description: '来源适中，需要验证' };
    }
    return { label: '低可信', color: 'gray', icon: AlertCircle, description: '来源较少，谨慎使用' };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error || !unit) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">加载失败</h2>
          <p className="text-gray-600 mb-4">{error || '未找到知识单元'}</p>
          <button
            onClick={() => navigate(`/projects/${projectId}/distillation`)}
            className="text-blue-600 hover:text-blue-700"
          >
            返回列表
          </button>
        </div>
      </div>
    );
  }

  const typeConfig = getTypeConfig(unit.unit_type);
  const credibilityInfo = getCredibilityInfo(unit.credibility);
  const CredibilityIcon = credibilityInfo.icon;

  let extraData: any = {};
  try {
    extraData = JSON.parse(unit.extra_data || '{}');
  } catch (e) {
    console.error('解析extra_data失败:', e);
  }

  const displayedSources = showAllSources ? sources : sources.slice(0, 3);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <button
            onClick={() => navigate(`/projects/${projectId}/distillation`)}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            返回知识库
          </button>

          <div className="flex items-start space-x-4">
            <div className={`text-4xl p-3 bg-${typeConfig.color}-100 rounded-lg`}>
              {typeConfig.icon}
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <span className={`px-3 py-1 bg-${typeConfig.color}-100 text-${typeConfig.color}-700 rounded-full text-sm font-medium`}>
                  {typeConfig.name}
                </span>
                <span className={`px-3 py-1 bg-${credibilityInfo.color}-100 text-${credibilityInfo.color}-700 rounded-full text-sm font-medium flex items-center space-x-1`}>
                  <CredibilityIcon className="w-4 h-4" />
                  <span>{credibilityInfo.label}</span>
                </span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">{unit.title}</h1>
              <p className="text-sm text-gray-500">
                创建于 {new Date(unit.created_at).toLocaleString('zh-CN')}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Content Card */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">内容</h2>
              <div className="prose max-w-none">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {unit.content}
                </p>
              </div>
            </div>

            {/* Sources Card */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                  <LinkIcon className="w-5 h-5" />
                  <span>来源追溯 ({sources.length})</span>
                </h2>
                {sourcesLoading && (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                )}
              </div>

              {sources.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>暂无来源信息</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {displayedSources.map((source, index) => {
                    const isExpanded = expandedSources.has(source.chunk_id);

                    return (
                      <div
                        key={source.chunk_id}
                        className="border border-gray-200 rounded-lg overflow-hidden hover:border-blue-300 transition-colors"
                      >
                        <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                          <div className="flex items-center space-x-3 flex-1">
                            <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                              {index + 1}
                            </span>
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 text-sm">
                                <FileText className="w-4 h-4 text-gray-500" />
                                <span className="font-medium text-gray-900">
                                  {source.document_name}
                                </span>
                              </div>
                              <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                                {source.page_number && (
                                  <span className="flex items-center space-x-1">
                                    <MapPin className="w-3 h-3" />
                                    <span>第 {source.page_number} 页</span>
                                  </span>
                                )}
                                {source.speaker && (
                                  <span className="flex items-center space-x-1">
                                    <User className="w-3 h-3" />
                                    <span>{source.speaker}</span>
                                  </span>
                                )}
                                {source.timestamp_start !== undefined && (
                                  <span className="flex items-center space-x-1">
                                    <Clock className="w-3 h-3" />
                                    <span>
                                      {formatTime(source.timestamp_start)} - {formatTime(source.timestamp_end)}
                                    </span>
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>

                          <button
                            onClick={() => toggleSourceExpand(source.chunk_id)}
                            className="text-gray-500 hover:text-gray-700"
                          >
                            {isExpanded ? (
                              <ChevronUp className="w-5 h-5" />
                            ) : (
                              <ChevronDown className="w-5 h-5" />
                            )}
                          </button>
                        </div>

                        <div className="px-4 py-3 bg-white">
                          <p className="text-gray-700 text-sm leading-relaxed">
                            {isExpanded ? source.full_content : source.content}
                          </p>
                          {!isExpanded && source.full_content.length > source.content.length && (
                            <button
                              onClick={() => toggleSourceExpand(source.chunk_id)}
                              className="text-blue-600 hover:text-blue-700 text-sm mt-2"
                            >
                              展开全文
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}

                  {sources.length > 3 && !showAllSources && (
                    <button
                      onClick={() => setShowAllSources(true)}
                      className="w-full py-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      显示全部 {sources.length} 个来源
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Metrics Card */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">评分指标</h3>

              <div className="space-y-4">
                {/* Credibility */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">可信度</span>
                    <span className="text-sm font-medium text-gray-900">
                      {(unit.credibility * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`bg-${credibilityInfo.color}-500 h-2 rounded-full transition-all`}
                      style={{ width: `${unit.credibility * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {credibilityInfo.description}
                  </p>
                </div>

                {/* Confidence */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">置信度</span>
                    <span className="text-sm font-medium text-gray-900">
                      {(unit.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${unit.confidence * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    基于提取质量和信号强度
                  </p>
                </div>

                {/* Sources Count */}
                <div className="pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">来源数量</span>
                    <span className="text-sm font-medium text-gray-900">
                      {sources.length} 个
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Metadata Card */}
            {Object.keys(extraData).length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">提取信息</h3>

                <div className="space-y-3 text-sm">
                  {extraData.extraction_method && (
                    <div>
                      <span className="text-gray-600">提取方法:</span>
                      <span className="ml-2 text-gray-900 font-medium">
                        {extraData.extraction_method}
                      </span>
                    </div>
                  )}

                  {extraData.top_entities && (
                    <div>
                      <span className="text-gray-600">核心实体:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {extraData.top_entities.map((entity: string, i: number) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                          >
                            {entity}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {extraData.top_keywords && (
                    <div>
                      <span className="text-gray-600">关键词:</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {extraData.top_keywords.map((keyword: string, i: number) => (
                          <span
                            key={i}
                            className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {extraData.urgency !== undefined && (
                    <div>
                      <span className="text-gray-600">紧急度:</span>
                      <span className="ml-2 text-gray-900 font-medium">
                        {extraData.urgency >= 0.8 ? '高' : extraData.urgency >= 0.6 ? '中' : '低'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
