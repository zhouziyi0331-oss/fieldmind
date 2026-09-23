import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Modal, Progress, Tag, Statistic, Row, Col, Tabs, List, message } from 'antd';
import {
  PlayCircleOutlined,
  TrophyOutlined,
  LockOutlined,
  UnlockOutlined,
  CheckCircleOutlined,
  StarOutlined,
  FireOutlined
} from '@ant-design/icons';
import axios from 'axios';
import Cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';

// 注册布局算法
Cytoscape.use(dagre);

const { TabPane } = Tabs;

interface SkillNode {
  id: string;
  label: string;
  description: string;
  tier: number;
  position: { x: number; y: number };
  status: string;
  level: number;
  difficulty: string;
  category: string;
  color: string;
  size: number;
}

interface SkillEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  strength: number;
  style: string;
}

interface SkillTreeData {
  nodes: SkillNode[];
  edges: SkillEdge[];
  metadata: {
    totalNodes: number;
    totalEdges: number;
    maxTier: number;
  };
}

interface SkillDetail {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty: string;
  estimated_hours: number;
  status: string;
  level: number;
  xp: number;
  prerequisites: string[];
  rationale: string;
  interpretation: string;
  execution_steps: string[];
  boundaries: string;
}

const SkillTreeViewer: React.FC<{ packageId: number }> = ({ packageId }) => {
  const [treeData, setTreeData] = useState<SkillTreeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedSkill, setSelectedSkill] = useState<SkillDetail | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [userProgress, setUserProgress] = useState<any>(null);

  const cyRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSkillTree();
    loadUserProgress();
  }, [packageId]);

  useEffect(() => {
    if (treeData && containerRef.current) {
      renderGraph();
    }
  }, [treeData]);

  const loadSkillTree = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/skills/tree/${packageId}`);
      if (response.data.success) {
        setTreeData({
          nodes: response.data.nodes,
          edges: response.data.edges,
          metadata: response.data.metadata
        });
      } else {
        // 树还未构建，尝试构建
        message.info('正在构建技能树...');
        await buildSkillTree();
      }
    } catch (error) {
      message.error('加载技能树失败');
    } finally {
      setLoading(false);
    }
  };

  const buildSkillTree = async () => {
    try {
      const response = await axios.post('/api/skills/tree/build', {
        package_id: packageId
      });
      if (response.data.success) {
        setTreeData(response.data.tree);
        message.success('技能树构建成功！');
      }
    } catch (error) {
      message.error('构建技能树失败');
    }
  };

  const loadUserProgress = async () => {
    try {
      const userId = 1; // TODO: 从认证获取
      const response = await axios.get(`/api/skills/progress/user/${userId}`);
      setUserProgress(response.data);
    } catch (error) {
      console.error('加载用户进度失败', error);
    }
  };

  const renderGraph = () => {
    if (!treeData || !containerRef.current) return;

    // 准备Cytoscape数据
    const elements = [
      // 节点
      ...treeData.nodes.map(node => ({
        data: {
          id: node.id,
          label: node.label,
          ...node
        },
        position: node.position
      })),
      // 边
      ...treeData.edges.map(edge => ({
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type,
          style: edge.style
        }
      }))
    ];

    // 初始化Cytoscape
    const cy = Cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'background-color': 'data(color)',
            'width': 'data(size)',
            'height': 'data(size)',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            'color': '#fff',
            'text-outline-width': 2,
            'text-outline-color': 'data(color)'
          }
        },
        {
          selector: 'node[status="locked"]',
          style: {
            'background-color': '#cccccc',
            'opacity': 0.6
          }
        },
        {
          selector: 'node[status="available"]',
          style: {
            'background-color': '#4CAF50'
          }
        },
        {
          selector: 'node[status="learning"]',
          style: {
            'background-color': '#2196F3',
            'border-width': 3,
            'border-color': '#FFC107'
          }
        },
        {
          selector: 'node[status="mastered"]',
          style: {
            'background-color': '#FFD700',
            'border-width': 3,
            'border-color': '#FF5722'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#999',
            'target-arrow-color': '#999',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier'
          }
        },
        {
          selector: 'edge[type="prerequisite"]',
          style: {
            'line-color': '#F44336',
            'target-arrow-color': '#F44336',
            'line-style': 'solid'
          }
        },
        {
          selector: 'edge[type="related"]',
          style: {
            'line-color': '#2196F3',
            'target-arrow-color': '#2196F3',
            'line-style': 'dashed'
          }
        }
      ],
      layout: {
        name: 'preset'
      },
      minZoom: 0.3,
      maxZoom: 3
    });

    // 节点点击事件
    cy.on('tap', 'node', async (evt: any) => {
      const node = evt.target;
      const skillId = node.data('id');
      await loadSkillDetail(skillId);
    });

    cyRef.current = cy;
  };

  const loadSkillDetail = async (skillId: string) => {
    try {
      const response = await axios.get(`/api/skills/node/${skillId}`);
      setSelectedSkill(response.data);
      setDetailModalVisible(true);
    } catch (error) {
      message.error('加载技能详情失败');
    }
  };

  const handleStartLearning = async () => {
    if (!selectedSkill) return;

    try {
      const response = await axios.post('/api/skills/progress/start', {
        skill_id: selectedSkill.id
      });

      if (response.data.success) {
        message.success(`开始学习 ${selectedSkill.name}`);
        setDetailModalVisible(false);
        loadSkillTree(); // 刷新技能树
        loadUserProgress();
      } else {
        message.warning(response.data.message);
        if (response.data.required_skills) {
          Modal.info({
            title: '需要前置技能',
            content: (
              <div>
                <p>请先完成以下技能：</p>
                <ul>
                  {response.data.required_skills.map((skill: string) => (
                    <li key={skill}>{skill}</li>
                  ))}
                </ul>
              </div>
            )
          });
        }
      }
    } catch (error) {
      message.error('开始学习失败');
    }
  };

  const renderSkillDetail = () => {
    if (!selectedSkill) return null;

    const statusColors: any = {
      locked: 'default',
      available: 'success',
      learning: 'processing',
      mastered: 'warning'
    };

    const difficultyColors: any = {
      beginner: 'green',
      intermediate: 'blue',
      advanced: 'orange',
      expert: 'red'
    };

    return (
      <Modal
        title={selectedSkill.name}
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          selectedSkill.status === 'available' && (
            <Button
              key="start"
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleStartLearning}
            >
              开始学习
            </Button>
          )
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 技能状态 */}
          <Row gutter={16}>
            <Col span={8}>
              <Statistic
                title="状态"
                value={selectedSkill.status}
                prefix={
                  selectedSkill.status === 'locked' ? <LockOutlined /> :
                  selectedSkill.status === 'available' ? <UnlockOutlined /> :
                  selectedSkill.status === 'learning' ? <PlayCircleOutlined /> :
                  <CheckCircleOutlined />
                }
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="等级"
                value={selectedSkill.level}
                suffix="/ 100"
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="预计时长"
                value={selectedSkill.estimated_hours}
                suffix="小时"
              />
            </Col>
          </Row>

          {/* 标签 */}
          <div>
            <Tag color={difficultyColors[selectedSkill.difficulty]}>
              {selectedSkill.difficulty}
            </Tag>
            <Tag color="blue">{selectedSkill.category}</Tag>
          </div>

          {/* 描述 */}
          <Card size="small" title="描述">
            {selectedSkill.description}
          </Card>

          {/* RIA++结构 */}
          <Tabs>
            <TabPane tab="为什么需要 (R)" key="rationale">
              <p>{selectedSkill.rationale}</p>
            </TabPane>
            <TabPane tab="核心逻辑 (I)" key="interpretation">
              <p>{selectedSkill.interpretation}</p>
            </TabPane>
            <TabPane tab="执行步骤 (E)" key="execution">
              <List
                size="small"
                dataSource={selectedSkill.execution_steps || []}
                renderItem={(step, index) => (
                  <List.Item>
                    {index + 1}. {step}
                  </List.Item>
                )}
              />
            </TabPane>
            <TabPane tab="边界 (B)" key="boundaries">
              <p>{selectedSkill.boundaries}</p>
            </TabPane>
          </Tabs>

          {/* 前置技能 */}
          {selectedSkill.prerequisites && selectedSkill.prerequisites.length > 0 && (
            <Card size="small" title="前置技能">
              {selectedSkill.prerequisites.map((prereq: string) => (
                <Tag key={prereq}>{prereq}</Tag>
              ))}
            </Card>
          )}
        </Space>
      </Modal>
    );
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部工具栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space>
              <Button
                icon={<FireOutlined />}
                onClick={loadSkillTree}
                loading={loading}
              >
                刷新技能树
              </Button>
              {!treeData && (
                <Button
                  type="primary"
                  onClick={buildSkillTree}
                  loading={loading}
                >
                  构建技能树
                </Button>
              )}
            </Space>
          </Col>

          {/* 用户进度统计 */}
          {userProgress && (
            <>
              <Col>
                <Statistic
                  title="学习中"
                  value={userProgress.learning?.length || 0}
                  prefix={<PlayCircleOutlined style={{ color: '#2196F3' }} />}
                />
              </Col>
              <Col>
                <Statistic
                  title="已完成"
                  value={userProgress.completed?.length || 0}
                  prefix={<CheckCircleOutlined style={{ color: '#4CAF50' }} />}
                />
              </Col>
              <Col>
                <Statistic
                  title="已精通"
                  value={userProgress.mastered?.length || 0}
                  prefix={<StarOutlined style={{ color: '#FFD700' }} />}
                />
              </Col>
            </>
          )}
        </Row>
      </Card>

      {/* 技能树可视化 */}
      <Card
        title="技能树"
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, padding: 0 }}
      >
        <div
          ref={containerRef}
          style={{
            width: '100%',
            height: '100%',
            minHeight: '600px',
            background: '#f5f5f5'
          }}
        />
      </Card>

      {/* 技能详情Modal */}
      {renderSkillDetail()}
    </div>
  );
};

export default SkillTreeViewer;
