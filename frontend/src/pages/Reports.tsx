import React, { useState, useEffect } from 'react';
import { reportAPI, analyticsAPI } from '@/services/fieldmind-api';

interface Report {
  id: number;
  name: string;
  description: string;
  report_type: string;
  status: string;
  created_at: string;
  file_path?: string;
}

interface ReportStats {
  total: number;
  level1: number;
  level2: number;
  level3: number;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState<ReportStats>({ total: 0, level1: 0, level2: 0, level3: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      setError(null);

      // 获取报告列表（假设API端点存在）
      const response = await reportAPI.getReports();
      const reportsData = response.data || [];

      setReports(reportsData);

      // 计算统计数据
      const statsData = {
        total: reportsData.length,
        level1: reportsData.filter((r: Report) => r.report_type === 'level1').length,
        level2: reportsData.filter((r: Report) => r.report_type === 'level2').length,
        level3: reportsData.filter((r: Report) => r.report_type === 'level3').length,
      };
      setStats(statsData);

    } catch (err: any) {
      console.error('加载报告列表失败:', err);
      setError(err.message || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const getReportTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'level1': 'Level 1 - 田野调查',
      'level2': 'Level 2 - 理论分析',
      'level3': 'Level 3 - 商业分析'
    };
    return labels[type] || type;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  const downloadReport = async (reportId: number) => {
    try {
      // 下载报告
      const response = await reportAPI.downloadReport(reportId);
      // 处理文件下载
      const blob = new Blob([response.data], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${reportId}.md`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('下载报告失败:', err);
    }
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

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">加载失败: {error}</p>
          <button
            onClick={loadReports}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="page-title">智能报告</h1>
          <p className="page-subtitle">三层报告体系：田野调查 → 理论分析 → 商业评估</p>
        </div>
        <button
          onClick={() => window.location.href = '/chat'}
          className="px-4 py-2 bg-[#27768A] text-white rounded-lg hover:bg-[#1F5E6E]"
        >
          生成新报告
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">总报告数</div>
          <div className="text-2xl font-bold">{stats.total}</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Level 1 田野调查</div>
          <div className="text-2xl font-bold text-[#27768A]">{stats.level1}</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Level 2 理论分析</div>
          <div className="text-2xl font-bold text-[#748D44]">{stats.level2}</div>
        </div>
        <div className="stat-card">
          <div className="text-sm text-gray-600 mb-1">Level 3 商业分析</div>
          <div className="text-2xl font-bold text-[#F8B042]">{stats.level3}</div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-lg font-semibold mb-6">所有报告</h3>

        {reports.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>暂无报告</p>
            <p className="text-sm mt-2">在聊天中使用指令生成报告</p>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow">
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-12 h-12 bg-[#27768A]/10 rounded-lg flex items-center justify-center">
                    <svg className="w-6 h-6 text-[#27768A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{report.name}</div>
                    <div className="text-sm text-gray-600">{report.description || getReportTypeLabel(report.report_type)}</div>
                  </div>
                  <div className="text-sm text-gray-500">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      report.status === 'completed' ? 'bg-green-100 text-green-800' :
                      report.status === 'generating' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {report.status === 'completed' ? '已完成' : report.status === 'generating' ? '生成中' : report.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">{formatDate(report.created_at)}</div>
                </div>
                <div className="flex gap-2">
                  {report.status === 'completed' && (
                    <button
                      onClick={() => downloadReport(report.id)}
                      className="p-2 hover:bg-gray-100 rounded-lg"
                      title="下载报告"
                    >
                      <svg className="w-5 h-5 text-[#27768A]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
