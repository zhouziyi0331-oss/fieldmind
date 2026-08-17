import { useState } from 'react';
import { Zap, CheckCircle, Clock, XCircle, Play, Settings } from 'lucide-react';

interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  status: 'active' | 'inactive' | 'testing';
  usage: number;
  lastUsed: string;
}

const SkillEcosystem = () => {
  const [skills] = useState<Skill[]>([
    {
      id: '1',
      name: '时间线生成',
      description: '从知识图谱中提取事件，生成带有模糊时间推理的时间线',
      category: '知识整理',
      status: 'active',
      usage: 45,
      lastUsed: '2024-06-20 14:30',
    },
    {
      id: '2',
      name: '多源叙事生成',
      description: '结合图谱和向量检索，生成带引用的连贯叙事',
      category: '内容生成',
      status: 'active',
      usage: 38,
      lastUsed: '2024-06-20 10:15',
    },
    {
      id: '3',
      name: '关键词提取',
      description: '从对话和文档中自动提取关键词和主题',
      category: '知识整理',
      status: 'active',
      usage: 52,
      lastUsed: '2024-06-19 16:45',
    },
    {
      id: '4',
      name: '语义搜索',
      description: '基于向量相似度的智能搜索功能',
      category: '检索查询',
      status: 'active',
      usage: 67,
      lastUsed: '2024-06-20 15:20',
    },
    {
      id: '5',
      name: '实体识别',
      description: '识别文本中的人物、地点、组织等实体',
      category: '信息抽取',
      status: 'testing',
      usage: 12,
      lastUsed: '2024-06-18 09:30',
    },
    {
      id: '6',
      name: '关系抽取',
      description: '抽取实体之间的关系并构建知识图谱',
      category: '信息抽取',
      status: 'testing',
      usage: 8,
      lastUsed: '2024-06-17 11:00',
    },
    {
      id: '7',
      name: '情感分析',
      description: '分析访谈内容中的情感倾向和态度',
      category: '内容分析',
      status: 'inactive',
      usage: 0,
      lastUsed: '未使用',
    },
    {
      id: '8',
      name: '主题建模',
      description: '从大量文本中发现潜在主题和话题',
      category: '内容分析',
      status: 'inactive',
      usage: 0,
      lastUsed: '未使用',
    },
  ]);

  const [selectedCategory, setSelectedCategory] = useState<string>('全部');

  const categories = ['全部', '知识整理', '内容生成', '检索查询', '信息抽取', '内容分析'];

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'active':
        return {
          icon: CheckCircle,
          label: '运行中',
          color: '#27ae60',
          bg: 'rgba(39, 174, 96, 0.1)',
        };
      case 'testing':
        return {
          icon: Clock,
          label: '测试中',
          color: '#f39c12',
          bg: 'rgba(243, 156, 18, 0.1)',
        };
      case 'inactive':
        return {
          icon: XCircle,
          label: '未激活',
          color: '#95a5a6',
          bg: 'rgba(149, 165, 166, 0.1)',
        };
      default:
        return {
          icon: XCircle,
          label: '未知',
          color: '#95a5a6',
          bg: 'rgba(149, 165, 166, 0.1)',
        };
    }
  };

  const filteredSkills =
    selectedCategory === '全部'
      ? skills
      : skills.filter((skill) => skill.category === selectedCategory);

  const activeSkills = skills.filter((s) => s.status === 'active').length;
  const testingSkills = skills.filter((s) => s.status === 'testing').length;
  const inactiveSkills = skills.filter((s) => s.status === 'inactive').length;

  return (
    <div>
      {/* 统计概览 */}
      <div className="grid grid-3" style={{ marginBottom: '32px' }}>
        <div className="stat-card">
          <div className="stat-label">运行中</div>
          <div className="stat-value" style={{ color: '#27ae60' }}>
            {activeSkills}
          </div>
          <div className="stat-change" style={{ color: '#27ae60' }}>
            <CheckCircle size={14} />
            <span>Skills</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">测试中</div>
          <div className="stat-value" style={{ color: '#f39c12' }}>
            {testingSkills}
          </div>
          <div className="stat-change" style={{ color: '#f39c12' }}>
            <Clock size={14} />
            <span>Skills</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-label">未激活</div>
          <div className="stat-value" style={{ color: '#95a5a6' }}>
            {inactiveSkills}
          </div>
          <div className="stat-change" style={{ color: '#95a5a6' }}>
            <XCircle size={14} />
            <span>Skills</span>
          </div>
        </div>
      </div>

      {/* 分类筛选 */}
      <div className="card" style={{ marginBottom: '32px' }}>
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

      {/* Skill卡片 */}
      <div className="grid grid-2" style={{ gap: '24px' }}>
        {filteredSkills.map((skill) => {
          const statusConfig = getStatusConfig(skill.status);
          const StatusIcon = statusConfig.icon;

          return (
            <div key={skill.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'linear-gradient(135deg, var(--color-primary), var(--color-deep))',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <Zap size={24} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '16px', marginBottom: '4px' }}>
                      {skill.name}
                    </div>
                    <div
                      style={{
                        fontSize: '12px',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        display: 'inline-block',
                        background: 'var(--bg-light)',
                        color: 'var(--text-gray)',
                      }}
                    >
                      {skill.category}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: statusConfig.bg,
                    color: statusConfig.color,
                    fontSize: '13px',
                    fontWeight: 500,
                  }}
                >
                  <StatusIcon size={14} />
                  {statusConfig.label}
                </div>
              </div>

              <p style={{ color: 'var(--text-gray)', fontSize: '14px', lineHeight: 1.6, marginBottom: '16px' }}>
                {skill.description}
              </p>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid var(--border-light)' }}>
                <div style={{ fontSize: '13px', color: 'var(--text-gray)' }}>
                  使用次数: <span style={{ fontWeight: 600, color: 'var(--text-dark)' }}>{skill.usage}</span>
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-gray)' }}>
                  最后使用: {skill.lastUsed}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
                {skill.status === 'active' && (
                  <button className="btn-primary" style={{ flex: 1, padding: '8px' }}>
                    <Play size={16} />
                    运行
                  </button>
                )}
                {skill.status === 'testing' && (
                  <button className="btn-secondary" style={{ flex: 1, padding: '8px' }}>
                    <Play size={16} />
                    测试
                  </button>
                )}
                {skill.status === 'inactive' && (
                  <button className="btn-outline" style={{ flex: 1, padding: '8px' }}>
                    <Play size={16} />
                    激活
                  </button>
                )}
                <button className="btn-outline" style={{ padding: '8px' }}>
                  <Settings size={16} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SkillEcosystem;
