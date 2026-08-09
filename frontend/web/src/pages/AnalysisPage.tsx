import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

const AnalysisPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  const { data: stats } = useQuery({
    queryKey: ['project-stats', projectId],
    queryFn: () => api.projects.getStats(Number(projectId)),
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link
              to={`/projects/${projectId}`}
              className="text-gray-600 hover:text-gray-900"
            >
              ← 返回项目
            </Link>
            <div className="h-6 w-px bg-gray-300" />
            <h1 className="text-2xl font-bold">📊 调查报告</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* 统计概览 */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="text-3xl font-bold text-blue-600">
              {stats?.document_count || 0}
            </div>
            <div className="text-gray-600 mt-2">文档总数</div>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="text-3xl font-bold text-green-600">
              {stats?.total_words?.toLocaleString() || 0}
            </div>
            <div className="text-gray-600 mt-2">总字数</div>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="text-3xl font-bold text-purple-600">
              {stats?.chat_session_count || 0}
            </div>
            <div className="text-gray-600 mt-2">对话会话</div>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="text-3xl font-bold text-orange-600">
              {stats?.memory_stats?.total_memories || 0}
            </div>
            <div className="text-gray-600 mt-2">长期记忆</div>
          </div>
        </div>

        {/* 技能框架状态 */}
        {stats?.has_skill_framework && stats.skill_framework && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-xl font-bold mb-4">🧠 AI技能框架</h2>
            <div className="space-y-4">
              <div>
                <div className="font-semibold text-gray-700">技能名称</div>
                <div className="text-gray-900">{stats.skill_framework.name}</div>
              </div>
              <div>
                <div className="font-semibold text-gray-700">描述</div>
                <div className="text-gray-900">{stats.skill_framework.description}</div>
              </div>
              {stats.skill_framework.capabilities && (
                <div>
                  <div className="font-semibold text-gray-700 mb-2">核心能力</div>
                  <div className="flex flex-wrap gap-2">
                    {stats.skill_framework.capabilities.map((cap: string, i: number) => (
                      <span
                        key={i}
                        className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm"
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 记忆统计 */}
        {stats?.memory_stats && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-xl font-bold mb-4">💾 记忆统计</h2>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.memory_stats.document_memories || 0}
                </div>
                <div className="text-sm text-gray-600 mt-1">文档记忆</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-600">
                  {stats.memory_stats.conversation_memories || 0}
                </div>
                <div className="text-sm text-gray-600 mt-1">对话记忆</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="text-2xl font-bold text-purple-600">
                  {stats.memory_stats.total_memories || 0}
                </div>
                <div className="text-sm text-gray-600 mt-1">总记忆数</div>
              </div>
            </div>
          </div>
        )}

        {/* 提示信息 */}
        {!stats?.has_skill_framework && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
            <div className="flex items-start gap-4">
              <svg
                className="w-6 h-6 text-yellow-600 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <h3 className="font-semibold text-yellow-800 mb-2">
                  还未构建AI技能框架
                </h3>
                <p className="text-yellow-700 mb-4">
                  运行项目分析以构建专属的AI技能框架，让AI更好地理解您的项目内容。
                </p>
                <button
                  onClick={async () => {
                    try {
                      await api.projects.analyze(Number(projectId));
                      alert('分析完成！');
                      window.location.reload();
                    } catch (error) {
                      alert('分析失败: ' + error);
                    }
                  }}
                  className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors font-semibold"
                >
                  立即分析
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisPage;
