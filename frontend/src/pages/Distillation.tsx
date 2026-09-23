import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Lightbulb,
  MessageSquare,
  Brain,
  BookOpen,
  Zap,
  FileText,
  ArrowLeft,
  RefreshCw,
  Filter,
  Search,
  Eye,
  TrendingUp
} from 'lucide-react';

interface DistillationStats {
  total_units: number;
  breakdown: {
    insights: number;
    quotes: number;
    models: number;
    cases: number;
    actions: number;
    methods: number;
  };
}

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

export default function DistillationPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [stats, setStats] = useState<DistillationStats | null>(null);
  const [units, setUnits] = useState<DistilledUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [distilling, setDistilling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const unitTypes = [
    { key: 'all', name: '全部', icon: Eye, color: 'gray' },
    { key: 'insight', name: '核心洞察', icon: Lightbulb, color: 'yellow' },
    { key: 'quote', name: '经典原话', icon: MessageSquare, color: 'blue' },
    { key: 'model', name: '思维模型', icon: Brain, color: 'purple' },
    { key: 'case', name: '案例应用', icon: BookOpen, color: 'green' },
    { key: 'action', name: '行动建议', icon: Zap, color: 'red' },
    { key: 'method', name: '方法论', icon: FileText, color: 'indigo' }
  ];

  useEffect(() => {
    loadStats();
    loadUnits();
  }, [projectId]);

  const loadStats = async () => {
    try {
      const response = await fetch(`/api/projects/${projectId}/distillation/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('加载统计失败:', err);
    }
  };

  const loadUnits = async () => {
    try {
      setLoading(true);
      setError(null);

      const typeParam = selectedType === 'all' ? '' : `?unit_type=${selectedType}`;
      const response = await fetch(`/api/projects/${projectId}/distilled-units${typeParam}`);

      if (!response.ok) {
        throw new Error('加载失败');
      }

      const data = await response.json();
      setUnits(data.units || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDistill = async () => {
    try {
      setDistilling(true);
      setError(null);

      const response = await fetch(`/api/projects/${projectId}/distill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error('蒸馏失败');
      }

      const result = await response.json();

      // 刷新数据
      await loadStats();
      await loadUnits();

      alert(`蒸馏完成！提取了 ${result.total_units} 个知识单元`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setDistilling(false);
    }
  };

  const getTypeIcon = (type: string) => {
    const typeConfig = unitTypes.find(t => t.key === type);
    const Icon = typeConfig?.icon || FileText;
    return <Icon className="w-5 h-5" />;
  };

  const getTypeColor = (type: string) => {
    const typeConfig = unitTypes.find(t => t.key === type);
    return typeConfig?.color || 'gray';
  };

  const getCredibilityLabel = (score: number) => {
    if (score >= 0.8) return { label: '高', color: 'green' };
    if (score >= 0.5) return { label: '中', color: 'yellow' };
    return { label: '低', color: 'gray' };
  };

  const filteredUnits = units.filter(unit => {
    const matchesType = selectedType === 'all' || unit.unit_type === selectedType;
    const matchesSearch = !searchQuery ||
      unit.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      unit.content.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate(`/projects/${projectId}`)}
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">知识蒸馏</h1>
                <p className="text-sm text-gray-600 mt-1">
                  从结构化数据中提炼可复用、可溯源的知识单元
                </p>
              </div>
            </div>

            <button
              onClick={handleDistill}
              disabled={distilling}
              className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${distilling ? 'animate-spin' : ''}`} />
              <span>{distilling ? '蒸馏中...' : '开始蒸馏'}</span>
            </button>
          </div>

          {/* Stats Cards */}
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mt-6">
              <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
                <div className="flex items-center justify-between">
                  <Eye className="w-8 h-8 text-gray-600" />
                  <span className="text-2xl font-bold text-gray-900">{stats.total_units}</span>
                </div>
                <p className="text-sm text-gray-600 mt-2">总计</p>
              </div>

              {unitTypes.slice(1).map((type) => {
                const Icon = type.icon;
                const count = stats.breakdown[type.key as keyof typeof stats.breakdown] || 0;

                return (
                  <div
                    key={type.key}
                    className={`bg-gradient-to-br from-${type.color}-50 to-${type.color}-100 rounded-lg p-4 border border-${type.color}-200 cursor-pointer hover:shadow-md transition-shadow`}
                    onClick={() => setSelectedType(type.key)}
                  >
                    <div className="flex items-center justify-between">
                      <Icon className={`w-8 h-8 text-${type.color}-600`} />
                      <span className="text-2xl font-bold text-gray-900">{count}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-2">{type.name}</p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
            {/* Type Filter */}
            <div className="flex items-center space-x-2 overflow-x-auto">
              {unitTypes.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.key}
                    onClick={() => setSelectedType(type.key)}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${
                      selectedType === type.key
                        ? `bg-${type.color}-100 text-${type.color}-700 border-2 border-${type.color}-300`
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{type.name}</span>
                  </button>
                );
              })}
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索知识单元..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Knowledge Units List */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
            {error}
          </div>
        ) : filteredUnits.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无知识单元</h3>
            <p className="text-gray-600 mb-4">
              {selectedType === 'all'
                ? '点击"开始蒸馏"按钮从结构化数据中提取知识'
                : `暂无${unitTypes.find(t => t.key === selectedType)?.name}类型的知识单元`
              }
            </p>
            {selectedType !== 'all' && (
              <button
                onClick={() => setSelectedType('all')}
                className="text-blue-600 hover:text-blue-700"
              >
                查看全部
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredUnits.map((unit) => {
              const credibility = getCredibilityLabel(unit.credibility);
              const colorClass = getTypeColor(unit.unit_type);

              return (
                <div
                  key={unit.id}
                  className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer border-l-4"
                  style={{ borderLeftColor: `var(--color-${colorClass}-500)` }}
                  onClick={() => navigate(`/projects/${projectId}/distillation/${unit.id}`)}
                >
                  <div className="p-6">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start space-x-3 flex-1">
                        <div className={`p-2 bg-${colorClass}-100 rounded-lg`}>
                          {getTypeIcon(unit.unit_type)}
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-1">
                            {unit.title}
                          </h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span className={`px-2 py-1 bg-${colorClass}-100 text-${colorClass}-700 rounded`}>
                              {unitTypes.find(t => t.key === unit.unit_type)?.name}
                            </span>
                            <span className="flex items-center space-x-1">
                              <TrendingUp className="w-4 h-4" />
                              <span>可信度: {(unit.credibility * 100).toFixed(0)}%</span>
                            </span>
                            <span>
                              置信度: {(unit.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Credibility Badge */}
                      <span className={`px-3 py-1 bg-${credibility.color}-100 text-${credibility.color}-700 rounded-full text-sm font-medium`}>
                        {credibility.label}可信
                      </span>
                    </div>

                    {/* Content Preview */}
                    <p className="text-gray-700 leading-relaxed mb-4">
                      {unit.content.length > 200
                        ? `${unit.content.substring(0, 200)}...`
                        : unit.content
                      }
                    </p>

                    {/* Footer */}
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <span>
                        创建时间: {new Date(unit.created_at).toLocaleString('zh-CN')}
                      </span>
                      <button className="text-blue-600 hover:text-blue-700 flex items-center space-x-1">
                        <Eye className="w-4 h-4" />
                        <span>查看详情</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
