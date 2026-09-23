import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Lightbulb,
  MessageSquare,
  Brain,
  BookOpen,
  Zap,
  FileText,
  ArrowRight,
  Sparkles
} from 'lucide-react';

interface DistillationEntryProps {
  projectId: number;
  stats?: {
    total_units: number;
    breakdown: {
      insights: number;
      quotes: number;
      models: number;
      cases: number;
      actions: number;
      methods: number;
    };
  };
}

export default function DistillationEntry({ projectId, stats }: DistillationEntryProps) {
  const navigate = useNavigate();

  const unitTypes = [
    { key: 'insights', name: '洞察', icon: Lightbulb, color: 'yellow' },
    { key: 'quotes', name: '原话', icon: MessageSquare, color: 'blue' },
    { key: 'models', name: '模型', icon: Brain, color: 'purple' },
    { key: 'cases', name: '案例', icon: BookOpen, color: 'green' },
    { key: 'actions', name: '建议', icon: Zap, color: 'red' },
    { key: 'methods', name: '方法论', icon: FileText, color: 'indigo' }
  ];

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg border border-purple-200 p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Sparkles className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">知识蒸馏</h3>
            <p className="text-sm text-gray-600">从数据中提炼可复用知识</p>
          </div>
        </div>
        <button
          onClick={() => navigate(`/projects/${projectId}/distillation`)}
          className="flex items-center space-x-1 text-purple-600 hover:text-purple-700"
        >
          <span className="text-sm font-medium">查看全部</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {stats ? (
        <>
          <div className="grid grid-cols-3 gap-3 mb-4">
            {unitTypes.map((type) => {
              const Icon = type.icon;
              const count = stats.breakdown[type.key as keyof typeof stats.breakdown] || 0;

              return (
                <div
                  key={type.key}
                  className="bg-white rounded-lg p-3 border border-gray-200 hover:shadow-sm transition-shadow cursor-pointer"
                  onClick={() => navigate(`/projects/${projectId}/distillation`)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <Icon className={`w-5 h-5 text-${type.color}-600`} />
                    <span className="text-xl font-bold text-gray-900">{count}</span>
                  </div>
                  <p className="text-xs text-gray-600">{type.name}</p>
                </div>
              );
            })}
          </div>

          <div className="bg-white rounded-lg p-4 border border-purple-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">知识单元总数</p>
                <p className="text-2xl font-bold text-purple-600">{stats.total_units}</p>
              </div>
              <button
                onClick={() => navigate(`/projects/${projectId}/distillation`)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
              >
                进入知识库
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white rounded-lg p-6 border border-gray-200 text-center">
          <Sparkles className="w-12 h-12 text-purple-300 mx-auto mb-3" />
          <p className="text-gray-600 mb-4">还未进行知识蒸馏</p>
          <button
            onClick={() => navigate(`/projects/${projectId}/distillation`)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
          >
            开始蒸馏
          </button>
        </div>
      )}
    </div>
  );
}
