import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

interface TimelineEvent {
  date: string;
  date_string: string;
  description: string;
  document_id: number;
  document_name: string;
  timestamp: number;
}

interface TimelineData {
  events: TimelineEvent[];
  events_by_year?: Record<string, TimelineEvent[]>;
  statistics: {
    total_events: number;
    date_range: {
      start: string;
      end: string;
    } | null;
  };
}

interface GroupedData {
  groups: Array<{
    key: string;
    events: TimelineEvent[];
    count: number;
  }>;
  statistics: {
    total_events: number;
    date_range: {
      start: string;
      end: string;
    } | null;
  };
}

const TimelinePage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [groupBy, setGroupBy] = useState<'year' | 'month' | 'document'>('year');
  const [viewMode, setViewMode] = useState<'timeline' | 'list'>('timeline');

  // 获取时间线数据
  const { data: timelineData, isLoading, error } = useQuery<TimelineData>({
    queryKey: ['timeline', projectId],
    queryFn: () => api.timeline.getEvents(Number(projectId)),
    enabled: !!projectId && viewMode === 'timeline',
  });

  // 获取分组数据
  const { data: groupedData, isLoading: groupedLoading } = useQuery<GroupedData>({
    queryKey: ['timelineGrouped', projectId, groupBy],
    queryFn: () => api.timeline.getGroupedEvents(Number(projectId), groupBy),
    enabled: !!projectId && viewMode === 'list',
  });

  if (isLoading || groupedLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载时间线...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">加载失败</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  const hasEvents = (viewMode === 'timeline' && timelineData?.events.length) ||
                    (viewMode === 'list' && groupedData?.groups.length);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to={`/projects/${projectId}`}
                className="text-gray-600 hover:text-gray-900"
              >
                ← 返回项目
              </Link>
              <div className="h-6 w-px bg-gray-300" />
              <h1 className="text-2xl font-bold">⏱️ 时间线</h1>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('timeline')}
                className={`px-4 py-2 rounded ${
                  viewMode === 'timeline'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                时间轴视图
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-4 py-2 rounded ${
                  viewMode === 'list'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                列表视图
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {!hasEvents ? (
          <div className="bg-white rounded-xl shadow-md p-8 text-center">
            <svg
              className="w-24 h-24 mx-auto text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h2 className="text-xl font-bold text-gray-700 mb-2">暂无时间线数据</h2>
            <p className="text-gray-600">请先上传包含日期信息的文档，系统将自动提取时间事件</p>
          </div>
        ) : (
          <>
            {viewMode === 'timeline' && timelineData && (
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="lg:col-span-3">
                  <div className="bg-white rounded-xl shadow-md p-6">
                    <div className="relative">
                      {/* 时间轴主线 */}
                      <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-blue-200"></div>

                      {/* 事件列表 */}
                      <div className="space-y-8">
                        {timelineData.events.map((event, index) => (
                          <div key={index} className="relative pl-16">
                            {/* 时间点 */}
                            <div className="absolute left-6 w-5 h-5 bg-blue-600 rounded-full border-4 border-white shadow"></div>

                            {/* 事件卡片 */}
                            <div className="bg-gray-50 rounded-lg p-4 hover:shadow-md transition-shadow">
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                                    {event.date_string}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    来自: {event.document_name}
                                  </span>
                                </div>
                              </div>
                              <p className="text-gray-700 text-sm leading-relaxed">
                                {event.description}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="bg-white rounded-xl shadow-md p-4">
                    <h3 className="font-bold mb-3">📊 统计信息</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">事件总数:</span>
                        <span className="font-semibold">{timelineData.statistics.total_events}</span>
                      </div>
                      {timelineData.statistics.date_range && (
                        <>
                          <div className="flex justify-between">
                            <span className="text-gray-600">开始日期:</span>
                            <span className="font-semibold">{timelineData.statistics.date_range.start}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">结束日期:</span>
                            <span className="font-semibold">{timelineData.statistics.date_range.end}</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {timelineData.events_by_year && (
                    <div className="bg-white rounded-xl shadow-md p-4">
                      <h3 className="font-bold mb-3">📅 按年份分布</h3>
                      <div className="space-y-2">
                        {Object.entries(timelineData.events_by_year)
                          .sort(([a], [b]) => b.localeCompare(a))
                          .map(([year, events]) => (
                            <div key={year} className="flex items-center justify-between text-sm">
                              <span className="text-gray-700">{year}年</span>
                              <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                                {events.length} 个事件
                              </span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {viewMode === 'list' && groupedData && (
              <div className="space-y-6">
                <div className="bg-white rounded-xl shadow-md p-4">
                  <div className="flex items-center gap-4 mb-4">
                    <span className="text-sm font-semibold text-gray-700">分组方式:</span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setGroupBy('year')}
                        className={`px-3 py-1 text-sm rounded ${
                          groupBy === 'year'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        按年份
                      </button>
                      <button
                        onClick={() => setGroupBy('month')}
                        className={`px-3 py-1 text-sm rounded ${
                          groupBy === 'month'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        按月份
                      </button>
                      <button
                        onClick={() => setGroupBy('document')}
                        className={`px-3 py-1 text-sm rounded ${
                          groupBy === 'document'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        按文档
                      </button>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {groupedData.groups.map((group, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="text-lg font-bold text-gray-800">{group.key}</h3>
                          <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-semibold rounded">
                            {group.count} 个事件
                          </span>
                        </div>
                        <div className="space-y-2">
                          {group.events.map((event, eventIndex) => (
                            <div key={eventIndex} className="bg-gray-50 rounded p-3">
                              <div className="flex items-start gap-3">
                                <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded whitespace-nowrap">
                                  {event.date_string}
                                </span>
                                <div className="flex-1">
                                  <p className="text-sm text-gray-700 mb-1">{event.description}</p>
                                  <p className="text-xs text-gray-500">来自: {event.document_name}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TimelinePage;
