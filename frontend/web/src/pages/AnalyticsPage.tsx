/**
 * 数据分析页面 - 基于SQL聚合的真实统计
 * 不是向量检索，而是结构化查询
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../services/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface TopicStat {
  topic: string;
  count: number;
  percentage: number;
}

interface EntityStat {
  name: string;
  count: number;
}

const AnalyticsPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [loading, setLoading] = useState(true);
  const [topicStats, setTopicStats] = useState<TopicStat[]>([]);
  const [personStats, setPersonStats] = useState<EntityStat[]>([]);
  const [locationStats, setLocationStats] = useState<EntityStat[]>([]);
  const [wordStats, setWordStats] = useState<any>(null);

  useEffect(() => {
    loadAnalytics();
  }, [projectId]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);

      // 并行加载所有统计数据
      const [topics, persons, locations, words] = await Promise.all([
        fetch(`${API_BASE_URL}/api/analytics/projects/${projectId}/topic-distribution`).then(r => r.json()),
        fetch(`${API_BASE_URL}/api/analytics/projects/${projectId}/top-entities?entity_type=person&top_k=10`).then(r => r.json()),
        fetch(`${API_BASE_URL}/api/analytics/projects/${projectId}/top-entities?entity_type=location&top_k=10`).then(r => r.json()),
        fetch(`${API_BASE_URL}/api/analytics/projects/${projectId}/word-count-stats`).then(r => r.json()),
      ]);

      setTopicStats(topics.topics || []);
      setPersonStats(persons.entities || []);
      setLocationStats(locations.entities || []);
      setWordStats(words);

    } catch (error) {
      console.error('加载分析数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/analytics/projects/${projectId}/generate-report`,
        { method: 'POST' }
      );
      const data = await response.json();

      if (data.success) {
        alert('报告生成成功！');
        console.log('报告:', data.report);
      } else {
        alert(data.message || '报告生成失败');
      }
    } catch (error) {
      console.error('生成报告失败:', error);
      alert('生成报告失败');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">加载数据分析...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* 页头 */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800">数据分析</h1>
        <p className="text-gray-600 mt-2">基于SQL聚合的真实统计数据</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-500 mb-2">总字数</div>
          <div className="text-3xl font-bold text-indigo-600">
            {wordStats?.total_words?.toLocaleString() || 0}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-500 mb-2">文本片段数</div>
          <div className="text-3xl font-bold text-green-600">
            {wordStats?.total_chunks || 0}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-500 mb-2">平均字数/片段</div>
          <div className="text-3xl font-bold text-purple-600">
            {wordStats?.avg_words_per_chunk?.toFixed(1) || 0}
          </div>
        </div>
      </div>

      {/* 主题分布 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">主题分布（SQL聚合）</h2>

        {topicStats.length > 0 ? (
          <div className="space-y-3">
            {topicStats.map((stat) => (
              <div key={stat.topic} className="flex items-center">
                <div className="w-20 text-sm font-medium text-gray-700">
                  {stat.topic}
                </div>
                <div className="flex-1 mx-4">
                  <div className="bg-gray-200 rounded-full h-6 relative">
                    <div
                      className="bg-indigo-600 rounded-full h-6 flex items-center justify-end pr-2"
                      style={{ width: `${stat.percentage}%` }}
                    >
                      <span className="text-white text-xs font-medium">
                        {stat.percentage}%
                      </span>
                    </div>
                  </div>
                </div>
                <div className="w-20 text-right text-sm text-gray-600">
                  {stat.count}次
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-500 text-center py-8">
            暂无数据，请先上传并处理文档
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Top人物 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">主要人物（提及次数）</h2>

          {personStats.length > 0 ? (
            <div className="space-y-2">
              {personStats.map((stat, index) => (
                <div key={stat.name} className="flex items-center justify-between py-2 border-b border-gray-100">
                  <div className="flex items-center">
                    <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs flex items-center justify-center mr-3">
                      {index + 1}
                    </span>
                    <span className="font-medium">{stat.name}</span>
                  </div>
                  <span className="text-gray-600">{stat.count}次</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              暂无人物数据
            </div>
          )}
        </div>

        {/* Top地点 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">主要地点（提及次数）</h2>

          {locationStats.length > 0 ? (
            <div className="space-y-2">
              {locationStats.map((stat, index) => (
                <div key={stat.name} className="flex items-center justify-between py-2 border-b border-gray-100">
                  <div className="flex items-center">
                    <span className="w-6 h-6 rounded-full bg-green-100 text-green-600 text-xs flex items-center justify-center mr-3">
                      {index + 1}
                    </span>
                    <span className="font-medium">{stat.name}</span>
                  </div>
                  <span className="text-gray-600">{stat.count}次</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              暂无地点数据
            </div>
          )}
        </div>
      </div>

      {/* 生成报告按钮 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">生成分析报告</h2>
            <p className="text-sm text-gray-600 mt-1">
              基于上述统计数据生成报告（所有数字来自SQL查询）
            </p>
          </div>
          <button
            onClick={generateReport}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
          >
            生成报告
          </button>
        </div>
      </div>

      {/* 数据说明 */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="text-sm text-blue-800">
            <strong>数据来源说明：</strong>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>所有统计数字来自SQL聚合查询（COUNT、SUM、AVG）</li>
              <li>主题分类基于关键词规则自动打标</li>
              <li>人名和地名通过jieba分词自动提取</li>
              <li>数据每次上传文档时自动更新</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
