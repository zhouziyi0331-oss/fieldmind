import { useEffect, useState } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { useConversationStore } from '../stores/conversationStore';
import { useFileStore } from '../stores/fileStore';
import {
  TrendingUp,
  Files,
  MessageSquare,
  Database,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const Overview = () => {
  const { currentProject, currentStats, refreshStats } = useProjectStore();
  const { conversations, fetchConversations } = useConversationStore();
  const { files, fetchFiles } = useFileStore();

  useEffect(() => {
    if (currentProject) {
      refreshStats();
      fetchConversations(currentProject.id);
      fetchFiles(currentProject.id);
    }
  }, [currentProject?.id]);

  if (!currentStats) {
    return <div>加载中...</div>;
  }

  // 趋势图数据
  const trendData = {
    labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    datasets: [
      {
        label: '新增对话',
        data: [5, 8, 6, 12, 9, 15, 10],
        borderColor: 'rgb(255, 107, 107)',
        backgroundColor: 'rgba(255, 107, 107, 0.1)',
        tension: 0.4,
      },
      {
        label: '新增文件',
        data: [3, 5, 4, 8, 6, 10, 7],
        borderColor: 'rgb(78, 205, 196)',
        backgroundColor: 'rgba(78, 205, 196, 0.1)',
        tension: 0.4,
      },
    ],
  };

  // 文件类型分布
  const fileTypeData = {
    labels: Object.keys(currentStats.files.by_type),
    datasets: [
      {
        data: Object.values(currentStats.files.by_type),
        backgroundColor: [
          'rgba(255, 107, 107, 0.8)',
          'rgba(78, 205, 196, 0.8)',
          'rgba(255, 230, 109, 0.8)',
          'rgba(149, 225, 211, 0.8)',
          'rgba(108, 92, 231, 0.8)',
        ],
        borderWidth: 0,
      },
    ],
  };

  // 知识图谱节点类型分布
  const nodeTypeData = {
    labels: Object.keys(currentStats.knowledge.graph_nodes_by_type),
    datasets: [
      {
        label: '节点数量',
        data: Object.values(currentStats.knowledge.graph_nodes_by_type),
        backgroundColor: [
          'rgba(255, 107, 107, 0.7)',
          'rgba(78, 205, 196, 0.7)',
          'rgba(255, 230, 109, 0.7)',
          'rgba(149, 225, 211, 0.7)',
          'rgba(108, 92, 231, 0.7)',
        ],
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };

  return (
    <div>
      {/* 统计卡片 */}
      <div className="grid grid-4" style={{ marginBottom: '32px' }}>
        <div className="stat-card">
          <div className="stat-label">文件总数</div>
          <div className="stat-value">{currentStats.files.total}</div>
          <div className="stat-change positive">
            <ArrowUpRight size={14} />
            <span>就绪 {currentStats.files.ready_percentage}%</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">对话数量</div>
          <div className="stat-value">{currentStats.conversations.total}</div>
          <div className="stat-change positive">
            <ArrowUpRight size={14} />
            <span>活跃 {currentStats.activity.active_conversations_7d}</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">知识图谱</div>
          <div className="stat-value">{currentStats.knowledge.graph_nodes}</div>
          <div className="stat-change">
            <Database size={14} />
            <span>节点总数</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">向量文档</div>
          <div className="stat-value">{currentStats.knowledge.vector_documents}</div>
          <div className="stat-change">
            <Database size={14} />
            <span>文档总数</span>
          </div>
        </div>
      </div>

      {/* 图表区域 */}
      <div className="grid grid-2" style={{ marginBottom: '32px' }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <TrendingUp className="card-title-icon" />
              活动趋势
            </div>
          </div>
          <div style={{ height: '280px' }}>
            <Line data={trendData} options={chartOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Files className="card-title-icon" />
              文件类型分布
            </div>
          </div>
          <div style={{ height: '280px' }}>
            <Doughnut data={fileTypeData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* 知识图谱节点分布 */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div className="card-header">
          <div className="card-title">
            <Database className="card-title-icon" />
            知识图谱节点分布
          </div>
        </div>
        <div style={{ height: '300px' }}>
          <Bar data={nodeTypeData} options={chartOptions} />
        </div>
      </div>

      {/* 最近对话 */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <MessageSquare className="card-title-icon" />
            最近对话
          </div>
          <button className="card-action">查看全部</button>
        </div>
        <div>
          {currentStats.conversations.recent.map((conv) => (
            <div
              key={conv.id}
              style={{
                padding: '12px 0',
                borderBottom: '1px solid var(--border-light)',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 500, marginBottom: '4px' }}>
                {conv.title}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-gray)' }}>
                {new Date(conv.updated_at).toLocaleString('zh-CN')}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Overview;
