import { useState } from 'react';
import { Brain, ChevronDown, ChevronRight, Layers } from 'lucide-react';

interface Layer {
  id: string;
  name: string;
  level: number;
  description: string;
  concepts: string[];
  expanded: boolean;
}

const ThinkingModel = () => {
  const [layers, setLayers] = useState<Layer[]>([
    {
      id: '1',
      name: '表层观察',
      level: 1,
      description: '直接可见的现象和行为',
      concepts: ['空间布局', '人流分布', '业态类型', '建筑风貌'],
      expanded: true,
    },
    {
      id: '2',
      name: '行为模式',
      level: 2,
      description: '居民的日常活动和互动方式',
      concepts: ['生活习惯', '社交网络', '消费行为', '时间节奏'],
      expanded: true,
    },
    {
      id: '3',
      name: '社会关系',
      level: 3,
      description: '人与人之间的连接和组织形态',
      concepts: ['邻里关系', '社区组织', '权力结构', '利益关系'],
      expanded: true,
    },
    {
      id: '4',
      name: '文化意义',
      level: 4,
      description: '共享的价值观和符号系统',
      concepts: ['地方认同', '集体记忆', '文化符号', '仪式传统'],
      expanded: true,
    },
    {
      id: '5',
      name: '深层结构',
      level: 5,
      description: '隐藏的规则和权力机制',
      concepts: ['制度逻辑', '资本流动', '历史脉络', '发展模式'],
      expanded: true,
    },
  ]);

  const toggleLayer = (id: string) => {
    setLayers(
      layers.map((layer) =>
        layer.id === id ? { ...layer, expanded: !layer.expanded } : layer
      )
    );
  };

  const getLevelColor = (level: number) => {
    const colors = [
      'var(--color-primary)',
      'var(--color-secondary)',
      'var(--color-accent)',
      'var(--color-highlight)',
      'var(--color-deep)',
    ];
    return colors[level - 1] || colors[0];
  };

  return (
    <div>
      {/* 模型说明 */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div className="card-header">
          <div className="card-title">
            <Brain className="card-title-icon" />
            田野思维模型
          </div>
        </div>
        <p style={{ color: 'var(--text-gray)', lineHeight: 1.6 }}>
          从表层现象到深层结构，逐层解析社区的多维度特征。
          点击每一层可以展开查看详细概念，帮助建立系统性的分析框架。
        </p>
      </div>

      {/* 层级模型 */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div className="card-header">
          <div className="card-title">
            <Layers className="card-title-icon" />
            分析层级
          </div>
        </div>

        <div style={{ position: 'relative' }}>
          {/* 连接线 */}
          <div
            style={{
              position: 'absolute',
              left: '32px',
              top: '0',
              bottom: '0',
              width: '2px',
              background: 'linear-gradient(180deg, var(--color-primary), var(--color-deep))',
              opacity: 0.3,
            }}
          />

          {layers.map((layer, index) => (
            <div
              key={layer.id}
              style={{
                marginBottom: index < layers.length - 1 ? '16px' : '0',
                position: 'relative',
              }}
            >
              {/* 层级卡片 */}
              <div
                onClick={() => toggleLayer(layer.id)}
                style={{
                  padding: '20px',
                  background: 'var(--bg-light)',
                  borderRadius: 'var(--radius-md)',
                  borderLeft: `4px solid ${getLevelColor(layer.level)}`,
                  cursor: 'pointer',
                  transition: 'var(--transition)',
                  marginLeft: `${(layer.level - 1) * 24}px`,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'white';
                  e.currentTarget.style.boxShadow = 'var(--shadow-md)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'var(--bg-light)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {/* 层级编号 */}
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      background: getLevelColor(layer.level),
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: '18px',
                      flexShrink: 0,
                    }}
                  >
                    {layer.level}
                  </div>

                  {/* 层级信息 */}
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        fontWeight: 600,
                        fontSize: '16px',
                        marginBottom: '4px',
                        color: 'var(--text-dark)',
                      }}
                    >
                      {layer.name}
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-gray)' }}>
                      {layer.description}
                    </div>
                  </div>

                  {/* 展开图标 */}
                  {layer.expanded ? (
                    <ChevronDown size={20} color="var(--text-gray)" />
                  ) : (
                    <ChevronRight size={20} color="var(--text-gray)" />
                  )}
                </div>

                {/* 概念列表 */}
                {layer.expanded && (
                  <div
                    style={{
                      marginTop: '16px',
                      paddingTop: '16px',
                      borderTop: '1px solid var(--border-light)',
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '8px',
                    }}
                  >
                    {layer.concepts.map((concept, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '6px 12px',
                          background: 'white',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '13px',
                          fontWeight: 500,
                          color: getLevelColor(layer.level),
                          border: `1px solid ${getLevelColor(layer.level)}`,
                          transition: 'var(--transition)',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = getLevelColor(layer.level);
                          e.currentTarget.style.color = 'white';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'white';
                          e.currentTarget.style.color = getLevelColor(layer.level);
                        }}
                      >
                        {concept}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 应用示例 */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">应用示例</div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {[
            {
              case: '老街改造项目',
              analysis:
                '从表层的建筑风貌，到行为层的商业模式，再到深层的历史文化价值，形成完整的改造策略。',
              color: 'var(--color-primary)',
            },
            {
              case: '社区营造实践',
              analysis:
                '识别居民的日常活动模式，理解邻里关系网络，最终触及社区认同的深层机制。',
              color: 'var(--color-secondary)',
            },
            {
              case: '公共空间设计',
              analysis:
                '观察空间使用行为，分析社交互动规律，挖掘空间的文化意义和社会价值。',
              color: 'var(--color-deep)',
            },
          ].map((example, index) => (
            <div
              key={index}
              style={{
                padding: '16px',
                background: 'var(--bg-light)',
                borderRadius: 'var(--radius-md)',
                borderLeft: `4px solid ${example.color}`,
              }}
            >
              <div
                style={{
                  fontWeight: 600,
                  marginBottom: '8px',
                  color: 'var(--text-dark)',
                }}
              >
                {example.case}
              </div>
              <div style={{ fontSize: '14px', color: 'var(--text-gray)', lineHeight: 1.6 }}>
                {example.analysis}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ThinkingModel;
