import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useAppContext, useRefreshListener } from '../contexts/AppContext';
import { getDashboardAggregate } from '../services/aggregateService';

const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const queryClient = useQueryClient();
  const { setCurrentProjectId } = useAppContext();

  // 设置当前项目ID到全局状态
  React.useEffect(() => {
    if (projectId) {
      setCurrentProjectId(Number(projectId));
    }
  }, [projectId, setCurrentProjectId]);

  // 使用聚合API获取数据
  const { data: aggregateData, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard-aggregate', projectId],
    queryFn: () => getDashboardAggregate(Number(projectId)),
    staleTime: 0, // 总是获取最新数据
  });

  // 监听全局刷新信号 - 当其他页面上传文档时自动刷新
  useRefreshListener(() => {
    console.log('[ProjectDetailPage] 收到刷新信号，重新加载聚合数据');
    refetch();
  });

  const project = aggregateData?.project;
  const summary = aggregateData?.summary;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl text-gray-600">加载中...</div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl text-red-600">加载失败</div>
      </div>
    );
  }

  const modules = [
    {
      name: '材料库',
      icon: '📚',
      description: `${summary?.total_docs || 0} 个文档`,
      path: `/projects/${projectId}/documents`,
      color: 'bg-blue-500',
    },
    {
      name: 'AI对话',
      icon: '💬',
      description: `${project?.chat_session_count || 0} 个会话`,
      path: `/projects/${projectId}/chat`,
      color: 'bg-green-500',
    },
    {
      name: '知识脉络',
      icon: '🌳',
      description: `${summary?.total_entities || 0} 个实体`,
      path: `/projects/${projectId}/knowledge-graph`,
      color: 'bg-purple-500',
    },
    {
      name: '编年知识图谱',
      icon: '⏰',
      description: '时间轴事件关联',
      path: `/projects/${projectId}/timeline`,
      color: 'bg-orange-500',
    },
    {
      name: '调查报告',
      icon: '📊',
      description: '数据分析和洞察',
      path: `/projects/${projectId}/analysis`,
      color: 'bg-red-500',
    },
    {
      name: '项目看板',
      icon: '📈',
      description: '统计和可视化',
      path: `/projects/${projectId}/dashboard`,
      color: 'bg-indigo-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部导航 */}
      <div className="bg-white shadow">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link to="/projects" className="text-gray-600 hover:text-gray-900">
              ← 返回项目列表
            </Link>
            <div className="h-6 w-px bg-gray-300" />
            <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* 项目概览 */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-xl font-semibold mb-2">项目概览</h2>
              {project.description && (
                <p className="text-gray-600">{project.description}</p>
              )}
            </div>
            <span
              className={`px-3 py-1 rounded-full text-sm font-semibold ${
                project.status === 'active'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {project.status}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-blue-600">
                {summary?.total_docs || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">文档数量</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-green-600">
                {summary?.total_facts || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">事实陈述</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-purple-600">
                {summary?.total_entities || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">知识实体</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="text-3xl font-bold text-orange-600">
                {summary?.total_vectors || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">向量数据</div>
            </div>
          </div>
        </div>

        {/* 🔪 破茧三刀：动态发现面板 */}
        {aggregateData?.dynamic_insights && aggregateData.dynamic_insights.top_entities.length > 0 && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              🔪 动态发现
              <span className="text-sm font-normal text-gray-500">（无预设词表、无固定分类、无模板框架）</span>
            </h2>

            <div className="grid md:grid-cols-3 gap-6">
              {/* BERTopic发现的主题（无监督聚类） */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">📊 发现的主题（BERTopic）</h3>
                <div className="flex flex-wrap gap-2">
                  {aggregateData.dynamic_insights.top_topics.slice(0, 10).map((topic: any) => (
                    <span
                      key={topic.name}
                      className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm hover:bg-blue-200 transition-colors cursor-pointer"
                      title={`关键词: ${topic.keywords?.join(', ')}`}
                    >
                      {topic.name} <span className="text-blue-600 font-semibold">{topic.frequency}</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* 指称消歧后的实体 */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">👤 核心实体（已消歧）</h3>
                <div className="flex flex-wrap gap-2">
                  {aggregateData.dynamic_insights.top_entities.slice(0, 12).map((entity: any) => (
                    <span
                      key={entity.canonical_name}
                      className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm hover:bg-purple-200 transition-colors cursor-pointer"
                      title={entity.aliases?.length > 0 ? `别名: ${entity.aliases.join(', ')}` : entity.entity_type}
                    >
                      {entity.canonical_name} <span className="text-purple-600 font-semibold">{entity.total_mentions}</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* 数据画像发现的维度 */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">🎯 发现的维度</h3>
                <div className="flex flex-wrap gap-2">
                  {aggregateData.dynamic_insights.discovered_dimensions?.slice(0, 8).map((dim: any) => (
                    <span
                      key={dim.name}
                      className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm hover:bg-green-200 transition-colors cursor-pointer"
                      title={`关键词: ${dim.keywords?.join(', ')}`}
                    >
                      {dim.name} <span className="text-green-600 font-semibold">{dim.total_mentions}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* 统计摘要 */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {aggregateData.dynamic_insights.total_topics_discovered}
                  </div>
                  <div className="text-sm text-gray-500">主题（聚类）</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-purple-600">
                    {aggregateData.dynamic_insights.total_entities_discovered}
                  </div>
                  <div className="text-sm text-gray-500">实体（消歧）</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {aggregateData.dynamic_insights.total_dimensions}
                  </div>
                  <div className="text-sm text-gray-500">维度（画像）</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 功能模块 */}
        <div>
          <h2 className="text-2xl font-bold mb-6">功能模块</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {modules.map((module) => (
              <Link
                key={module.name}
                to={module.path}
                className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all p-6 group"
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`w-12 h-12 ${module.color} rounded-xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform`}
                  >
                    {module.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors">
                      {module.name}
                    </h3>
                    <p className="text-sm text-gray-600">{module.description}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* 快速操作 */}
        <div className="mt-8 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl shadow-lg p-8 text-white">
          <h2 className="text-2xl font-bold mb-4">快速开始</h2>
          <div className="grid md:grid-cols-3 gap-4">
            <Link
              to={`/projects/${projectId}/documents`}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg p-4 transition-all"
            >
              <div className="font-semibold mb-2">📤 上传文档</div>
              <div className="text-sm opacity-90">添加研究资料</div>
            </Link>
            <Link
              to={`/projects/${projectId}/chat`}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg p-4 transition-all"
            >
              <div className="font-semibold mb-2">💡 开始对话</div>
              <div className="text-sm opacity-90">与AI助手交流</div>
            </Link>
            <button
              onClick={async () => {
                if (window.confirm('确定要分析项目吗？这将基于所有文档和对话构建专属AI技能。')) {
                  try {
                    await api.projects.analyze(Number(projectId));
                    alert('分析完成！AI技能已更新。');
                  } catch (error) {
                    alert('分析失败: ' + error);
                  }
                }
              }}
              className="bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg p-4 transition-all text-left"
            >
              <div className="font-semibold mb-2">🧠 智能分析</div>
              <div className="text-sm opacity-90">构建专属技能</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetailPage;
