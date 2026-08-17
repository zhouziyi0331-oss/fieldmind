import { useState } from 'react';
import { BarChart3, PieChart, TrendingUp, Users, Calendar } from 'lucide-react';
import { Line, Bar, Doughnut, PolarArea } from 'react-chartjs-2';

const Visualization = () => {
  // 时间趋势数据
  const timelineData = {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
    datasets: [
      {
        label: '访谈人数',
        data: [12, 19, 15, 25, 22, 30],
        borderColor: 'rgb(255, 107, 107)',
        backgroundColor: 'rgba(255, 107, 107, 0.1)',
        tension: 0.4,
      },
      {
        label: '活动次数',
        data: [8, 12, 10, 18, 15, 22],
        borderColor: 'rgb(78, 205, 196)',
        backgroundColor: 'rgba(78, 205, 196, 0.1)',
        tension: 0.4,
      },
    ],
  };

  // 人群分布
  const demographicData = {
    labels: ['18-30岁', '31-45岁', '46-60岁', '60岁以上'],
    datasets: [
      {
        data: [25, 35, 28, 12],
        backgroundColor: [
          'rgba(255, 107, 107, 0.8)',
          'rgba(78, 205, 196, 0.8)',
          'rgba(255, 230, 109, 0.8)',
          'rgba(149, 225, 211, 0.8)',
        ],
      },
    ],
  };

  // 空间使用频率
  const spaceUsageData = {
    labels: ['社区广场', '文化中心', '运动场', '公园', '商业街', '图书馆'],
    datasets: [
      {
        label: '使用频率',
        data: [85, 72, 68, 90, 78, 65],
        backgroundColor: [
          'rgba(255, 107, 107, 0.7)',
          'rgba(78, 205, 196, 0.7)',
          'rgba(255, 230, 109, 0.7)',
          'rgba(149, 225, 211, 0.7)',
          'rgba(108, 92, 231, 0.7)',
          'rgba(255, 107, 107, 0.5)',
        ],
      },
    ],
  };

  // 满意度分析
  const satisfactionData = {
    labels: ['环境卫生', '公共设施', '交通便利', '社区活动', '邻里关系', '安全性'],
    datasets: [
      {
        label: '满意度',
        data: [85, 78, 72, 88, 92, 80],
        backgroundColor: 'rgba(255, 107, 107, 0.2)',
        borderColor: 'rgba(255, 107, 107, 1)',
        borderWidth: 2,
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
      {/* 顶部统计卡片 */}
      <div className="grid grid-4" style={{ marginBottom: '32px' }}>
        <div className="stat-card">
          <div className="stat-label">总访谈人数</div>
          <div className="stat-value">123</div>
          <div className="stat-change positive">
            <span>较上月 +15%</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">记录事件</div>
          <div className="stat-value">456</div>
          <div className="stat-change positive">
            <span>较上月 +23%</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">知识节点</div>
          <div className="stat-value">789</div>
          <div className="stat-change positive">
            <span>较上月 +18%</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">平均满意度</div>
          <div className="stat-value">82%</div>
          <div className="stat-change positive">
            <span>较上月 +5%</span>
          </div>
        </div>
      </div>

      {/* 第一行图表 */}
      <div className="grid grid-2" style={{ marginBottom: '32px' }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <TrendingUp className="card-title-icon" />
              调研趋势
            </div>
          </div>
          <div style={{ height: '320px' }}>
            <Line data={timelineData} options={chartOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Users className="card-title-icon" />
              人群分布
            </div>
          </div>
          <div style={{ height: '320px' }}>
            <Doughnut data={demographicData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* 第二行图表 */}
      <div className="grid grid-2" style={{ marginBottom: '32px' }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <BarChart3 className="card-title-icon" />
              空间使用频率
            </div>
          </div>
          <div style={{ height: '320px' }}>
            <Bar data={spaceUsageData} options={chartOptions} />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <PieChart className="card-title-icon" />
              满意度雷达
            </div>
          </div>
          <div style={{ height: '320px' }}>
            <PolarArea data={satisfactionData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* 数据表格 */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Calendar className="card-title-icon" />
            近期调研活动
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-light)' }}>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: 600 }}>
                  日期
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: 600 }}>
                  活动类型
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: 600 }}>
                  地点
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: 600 }}>
                  参与人数
                </th>
                <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: 600 }}>
                  状态
                </th>
              </tr>
            </thead>
            <tbody>
              {[
                { date: '2024-06-20', type: '居民访谈', location: '社区广场', people: 15, status: '已完成' },
                { date: '2024-06-18', type: '观察记录', location: '商业街', people: 8, status: '已完成' },
                { date: '2024-06-15', type: '焦点小组', location: '文化中心', people: 12, status: '已完成' },
                { date: '2024-06-12', type: '问卷调查', location: '公园', people: 50, status: '已完成' },
                { date: '2024-06-10', type: '深度访谈', location: '老街', people: 6, status: '已完成' },
              ].map((activity, index) => (
                <tr
                  key={index}
                  style={{
                    borderBottom: '1px solid var(--border-light)',
                    transition: 'var(--transition)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'var(--bg-light)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <td style={{ padding: '12px', fontSize: '14px' }}>{activity.date}</td>
                  <td style={{ padding: '12px', fontSize: '14px' }}>{activity.type}</td>
                  <td style={{ padding: '12px', fontSize: '14px' }}>{activity.location}</td>
                  <td style={{ padding: '12px', fontSize: '14px' }}>{activity.people}</td>
                  <td style={{ padding: '12px' }}>
                    <span
                      style={{
                        padding: '4px 12px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '12px',
                        background: 'rgba(39, 174, 96, 0.1)',
                        color: '#27ae60',
                        fontWeight: 500,
                      }}
                    >
                      {activity.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Visualization;
