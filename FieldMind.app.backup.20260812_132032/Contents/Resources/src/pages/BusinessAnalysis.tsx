import { useState } from 'react';
import { Store, TrendingUp, MapPin, DollarSign, Users } from 'lucide-react';
import { Bar, Radar } from 'react-chartjs-2';

interface Business {
  id: string;
  name: string;
  category: string;
  location: string;
  score: number;
  metrics: {
    popularity: number;
    profitability: number;
    sustainability: number;
    community: number;
    innovation: number;
  };
}

const BusinessAnalysis = () => {
  const [businesses] = useState<Business[]>([
    {
      id: '1',
      name: '老李茶馆',
      category: '餐饮',
      location: '老街口',
      score: 85,
      metrics: {
        popularity: 90,
        profitability: 75,
        sustainability: 85,
        community: 95,
        innovation: 70,
      },
    },
    {
      id: '2',
      name: '手工艺品店',
      category: '零售',
      location: '文化街',
      score: 78,
      metrics: {
        popularity: 70,
        profitability: 65,
        sustainability: 90,
        community: 85,
        innovation: 80,
      },
    },
    {
      id: '3',
      name: '社区图书馆',
      category: '文化',
      location: '中心广场',
      score: 92,
      metrics: {
        popularity: 95,
        profitability: 60,
        sustainability: 100,
        community: 100,
        innovation: 85,
      },
    },
    {
      id: '4',
      name: '创意工作室',
      category: '服务',
      location: '创意园区',
      score: 88,
      metrics: {
        popularity: 85,
        profitability: 80,
        sustainability: 85,
        community: 90,
        innovation: 100,
      },
    },
  ]);

  const [selectedBusiness, setSelectedBusiness] = useState<Business | null>(
    businesses[0]
  );

  // 业态分布
  const categoryData = {
    labels: ['餐饮', '零售', '文化', '服务', '其他'],
    datasets: [
      {
        label: '业态数量',
        data: [15, 12, 8, 10, 5],
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

  // 雷达图数据
  const radarData = selectedBusiness
    ? {
        labels: ['人气度', '盈利性', '可持续性', '社区价值', '创新性'],
        datasets: [
          {
            label: selectedBusiness.name,
            data: [
              selectedBusiness.metrics.popularity,
              selectedBusiness.metrics.profitability,
              selectedBusiness.metrics.sustainability,
              selectedBusiness.metrics.community,
              selectedBusiness.metrics.innovation,
            ],
            backgroundColor: 'rgba(255, 107, 107, 0.2)',
            borderColor: 'rgba(255, 107, 107, 1)',
            borderWidth: 2,
          },
        ],
      }
    : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'var(--color-primary)';
    if (score >= 70) return 'var(--color-secondary)';
    return 'var(--text-gray)';
  };

  return (
    <div>
      {/* 业态分布 */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div className="card-header">
          <div className="card-title">
            <Store className="card-title-icon" />
            业态分布
          </div>
        </div>
        <div style={{ height: '300px' }}>
          <Bar
            data={categoryData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { position: 'bottom' } },
            }}
          />
        </div>
      </div>

      {/* 业态列表和详情 */}
      <div className="grid grid-2" style={{ gap: '32px' }}>
        {/* 业态列表 */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <MapPin className="card-title-icon" />
              在地业态
            </div>
          </div>

          <div>
            {businesses.map((business) => (
              <div
                key={business.id}
                onClick={() => setSelectedBusiness(business)}
                style={{
                  padding: '16px',
                  borderBottom: '1px solid var(--border-light)',
                  cursor: 'pointer',
                  background:
                    selectedBusiness?.id === business.id
                      ? 'rgba(255, 107, 107, 0.05)'
                      : 'transparent',
                  transition: 'var(--transition)',
                }}
                onMouseEnter={(e) => {
                  if (selectedBusiness?.id !== business.id) {
                    e.currentTarget.style.background = 'var(--bg-light)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedBusiness?.id !== business.id) {
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px',
                  }}
                >
                  <div style={{ fontWeight: 500, fontSize: '15px' }}>
                    {business.name}
                  </div>
                  <div
                    style={{
                      fontSize: '18px',
                      fontWeight: 700,
                      color: getScoreColor(business.score),
                    }}
                  >
                    {business.score}
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    gap: '12px',
                    fontSize: '13px',
                    color: 'var(--text-gray)',
                  }}
                >
                  <span>
                    <Store size={14} style={{ display: 'inline', marginRight: '4px' }} />
                    {business.category}
                  </span>
                  <span>
                    <MapPin size={14} style={{ display: 'inline', marginRight: '4px' }} />
                    {business.location}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 业态详情 */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <TrendingUp className="card-title-icon" />
              {selectedBusiness?.name || '业态详情'}
            </div>
          </div>

          {selectedBusiness && (
            <div>
              {/* 综合评分 */}
              <div
                style={{
                  textAlign: 'center',
                  padding: '24px',
                  background: 'var(--bg-light)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '24px',
                }}
              >
                <div
                  style={{
                    fontSize: '48px',
                    fontWeight: 700,
                    color: getScoreColor(selectedBusiness.score),
                    marginBottom: '8px',
                  }}
                >
                  {selectedBusiness.score}
                </div>
                <div style={{ fontSize: '14px', color: 'var(--text-gray)' }}>
                  综合评分
                </div>
              </div>

              {/* 雷达图 */}
              {radarData && (
                <div style={{ height: '300px', marginBottom: '24px' }}>
                  <Radar data={radarData} options={chartOptions} />
                </div>
              )}

              {/* 指标详情 */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {Object.entries(selectedBusiness.metrics).map(([key, value]) => {
                  const labels: Record<string, string> = {
                    popularity: '人气度',
                    profitability: '盈利性',
                    sustainability: '可持续性',
                    community: '社区价值',
                    innovation: '创新性',
                  };

                  return (
                    <div key={key}>
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginBottom: '4px',
                          fontSize: '13px',
                        }}
                      >
                        <span>{labels[key]}</span>
                        <span style={{ fontWeight: 600 }}>{value}</span>
                      </div>
                      <div
                        style={{
                          height: '6px',
                          background: 'var(--bg-light)',
                          borderRadius: '3px',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          style={{
                            height: '100%',
                            width: `${value}%`,
                            background: `linear-gradient(90deg, var(--color-primary), var(--color-secondary))`,
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BusinessAnalysis;
