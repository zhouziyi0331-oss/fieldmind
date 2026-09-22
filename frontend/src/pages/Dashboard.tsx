import React, { useState, useEffect } from 'react';
import { dashboardAPI, analyticsAPI } from '@/services/fieldmind-api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DashboardStats {
  total_projects: number;
  total_documents: number;
  total_reports: number;
  total_keywords: number;
  projects_trend?: number;
  documents_trend?: number;
}

interface ActivityData {
  name: string;
  value: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    total_projects: 0,
    total_documents: 0,
    total_reports: 0,
    total_keywords: 0,
  });
  const [activityData, setActivityData] = useState<ActivityData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 获取仪表盘统计数据
      const response = await dashboardAPI.getStats();
      const statsData = response.data || {};

      setStats({
        total_projects: statsData.total_projects || 0,
        total_documents: statsData.total_documents || 0,
        total_reports: statsData.total_reports || 0,
        total_keywords: statsData.total_keywords || 0,
        projects_trend: statsData.projects_trend,
        documents_trend: statsData.documents_trend,
      });

      // 获取活动数据（最近7天）
      if (statsData.activity_data && Array.isArray(statsData.activity_data)) {
        setActivityData(statsData.activity_data);
      } else {
        // 如果没有活动数据，使用空数组
        setActivityData([]);
      }

    } catch (err: any) {
      console.error('加载仪表盘数据失败:', err);
      setError(err.message || '加载失败');

      // 设置默认值避免显示错误
      setStats({
        total_projects: 0,
        total_documents: 0,
        total_reports: 0,
        total_keywords: 0,
      });
      setActivityData([]);
    } finally {
      setLoading(false);
    }
  };

  const formatTrend = (trend?: number) => {
    if (trend === undefined || trend === null) return null;
    const isPositive = trend >= 0;
    return (
      <div className={`mt-2 text-sm flex items-center ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
          {isPositive ? (
            <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
          ) : (
            <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
          )}
        </svg>
        {Math.abs(trend)}% 较上月
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <div className="page-header">
        <h1 className="page-title">仪表盘</h1>
        <p className="page-subtitle">欢迎回来！这是您的数据概览</p>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-yellow-800">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>部分数据加载失败</span>
          </div>
          <button
            onClick={loadDashboardData}
            className="px-3 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm"
          >
            重试
          </button>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-gray-600">项目总数</span>
            <div className="w-10 h-10 rounded-lg bg-[#27768A]/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-[#27768A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.total_projects}</div>
          {formatTrend(stats.projects_trend)}
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-gray-600">文档总数</span>
            <div className="w-10 h-10 rounded-lg bg-[#748D44]/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-[#748D44]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.total_documents.toLocaleString()}</div>
          {formatTrend(stats.documents_trend)}
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-gray-600">生成报告</span>
            <div className="w-10 h-10 rounded-lg bg-[#F8B042]/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-[#F8B042]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.total_reports}</div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-gray-600">关键词数</span>
            <div className="w-10 h-10 rounded-lg bg-[#EC6A52]/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-[#EC6A52]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats.total_keywords.toLocaleString()}</div>
        </div>
      </div>

      {/* Chart */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-4">活动概览</h3>
        {activityData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="name" stroke="#6B7280" />
              <YAxis stroke="#6B7280" />
              <Tooltip />
              <Bar dataKey="value" fill="#27768A" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[300px] text-gray-400">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p>暂无活动数据</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
