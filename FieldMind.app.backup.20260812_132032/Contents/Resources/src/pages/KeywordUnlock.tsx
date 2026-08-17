import { useState, useEffect } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { Key, Search, TrendingUp, Hash } from 'lucide-react';

interface Keyword {
  text: string;
  count: number;
  category: string;
  trend: 'up' | 'down' | 'stable';
}

const KeywordUnlock = () => {
  const { currentProject } = useProjectStore();
  const [keywords, setKeywords] = useState<Keyword[]>([
    { text: '社区营造', count: 45, category: '核心概念', trend: 'up' },
    { text: '在地文化', count: 38, category: '核心概念', trend: 'up' },
    { text: '公共空间', count: 32, category: '空间', trend: 'stable' },
    { text: '居民参与', count: 28, category: '社会', trend: 'up' },
    { text: '历史建筑', count: 25, category: '空间', trend: 'stable' },
    { text: '商业业态', count: 22, category: '经济', trend: 'down' },
    { text: '文化传承', count: 20, category: '文化', trend: 'up' },
    { text: '邻里关系', count: 18, category: '社会', trend: 'stable' },
    { text: '街道治理', count: 15, category: '管理', trend: 'up' },
    { text: '城市更新', count: 12, category: '核心概念', trend: 'stable' },
  ]);

  const [selectedCategory, setSelectedCategory] = useState<string>('全部');
  const [searchTerm, setSearchTerm] = useState('');

  const categories = ['全部', '核心概念', '空间', '社会', '经济', '文化', '管理'];

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up':
        return '#27ae60';
      case 'down':
        return '#e74c3c';
      default:
        return '#95a5a6';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return '↑';
      case 'down':
        return '↓';
      default:
        return '→';
    }
  };

  const filteredKeywords = keywords
    .filter((kw) => selectedCategory === '全部' || kw.category === selectedCategory)
    .filter((kw) => kw.text.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div>
      {/* 搜索和筛选 */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search
              size={18}
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-gray)',
              }}
            />
            <input
              type="text"
              placeholder="搜索关键词..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px 10px 40px',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '14px',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  fontWeight: 500,
                  cursor: 'pointer',
                  background:
                    selectedCategory === cat ? 'var(--color-primary)' : 'var(--bg-light)',
                  color: selectedCategory === cat ? 'white' : 'var(--text-gray)',
                  transition: 'var(--transition)',
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 关键词云 */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div className="card-header">
          <div className="card-title">
            <Key className="card-title-icon" />
            关键词云 ({filteredKeywords.length})
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '12px',
            padding: '24px',
            background: 'var(--bg-light)',
            borderRadius: 'var(--radius-md)',
            minHeight: '200px',
          }}
        >
          {filteredKeywords.map((keyword, index) => {
            const fontSize = 14 + (keyword.count / 5);
            return (
              <div
                key={index}
                style={{
                  padding: '8px 16px',
                  background: 'white',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: `${fontSize}px`,
                  fontWeight: 500,
                  color: 'var(--text-dark)',
                  cursor: 'pointer',
                  transition: 'var(--transition)',
                  boxShadow: 'var(--shadow-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
                }}
              >
                <span>{keyword.text}</span>
                <span
                  style={{
                    fontSize: '12px',
                    color: 'var(--text-gray)',
                    background: 'var(--bg-light)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                  }}
                >
                  {keyword.count}
                </span>
                <span style={{ color: getTrendColor(keyword.trend) }}>
                  {getTrendIcon(keyword.trend)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 关键词详情列表 */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Hash className="card-title-icon" />
            关键词详情
          </div>
        </div>

        <div>
          {filteredKeywords.map((keyword, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                padding: '16px',
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
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  background: 'var(--color-primary)',
                  color: 'white',
                  borderRadius: 'var(--radius-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '16px',
                }}
              >
                {index + 1}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500, marginBottom: '4px' }}>{keyword.text}</div>
                <div style={{ fontSize: '13px', color: 'var(--text-gray)' }}>
                  {keyword.category}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div
                  style={{
                    fontSize: '20px',
                    fontWeight: 700,
                    color: 'var(--color-deep)',
                    marginBottom: '4px',
                  }}
                >
                  {keyword.count}
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: getTrendColor(keyword.trend),
                    fontWeight: 500,
                  }}
                >
                  {getTrendIcon(keyword.trend)} {keyword.trend === 'up' ? '上升' : keyword.trend === 'down' ? '下降' : '稳定'}
                </div>
              </div>

              <button className="btn-outline" style={{ padding: '6px 12px' }}>
                查看详情
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default KeywordUnlock;
