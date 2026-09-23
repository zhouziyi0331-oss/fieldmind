import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Table,
  Tag,
  Space,
  Modal,
  message,
  Progress,
  Descriptions,
  Tabs,
  Statistic,
  Row,
  Col,
  Alert,
  Spin
} from 'antd';
import {
  FileTextOutlined,
  BulbOutlined,
  BookOutlined,
  ExperimentOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LockOutlined,
  UnlockOutlined,
  DownloadOutlined,
  ExportOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { TabPane } = Tabs;

interface SBPACKPackage {
  id: number;
  project_id: number;
  package_name: string;
  version: string;
  protocol_version: string;
  source_title: string;
  source_author: string;
  knowledge_count: number;
  skill_count: number;
  relation_count: number;
  knowledge_frozen: boolean;
  skill_frozen: boolean;
  is_built: boolean;
  is_verified: boolean;
  verification_status: string;
  created_at: string;
  updated_at: string;
}

interface KnowledgeItem {
  id: number;
  knowledge_id: string;
  title: string;
  knowledge_type: string;
  statement: string;
  explanation: string;
  why_matters: string;
  scope: string;
  is_frozen: boolean;
}

interface SkillItem {
  id: number;
  skill_id: string;
  name: string;
  display_name: string;
  description: string;
  is_frozen: boolean;
  v1_passed: boolean;
  v2_passed: boolean;
  v3_passed: boolean;
}

const SBPACKManager: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [packages, setPackages] = useState<SBPACKPackage[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<SBPACKPackage | null>(null);
  const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
  const [skillItems, setSkillItems] = useState<SkillItem[]>([]);
  const [buildModalVisible, setBuildModalVisible] = useState(false);
  const [buildProgress, setBuildProgress] = useState(0);

  useEffect(() => {
    loadPackages();
  }, [projectId]);

  const loadPackages = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/sbpack/packages?project_id=${projectId}`);
      setPackages(response.data);
      if (response.data.length > 0) {
        selectPackage(response.data[0]);
      }
    } catch (error) {
      message.error('加载SBPACK包失败');
    } finally {
      setLoading(false);
    }
  };

  const selectPackage = async (pkg: SBPACKPackage) => {
    setSelectedPackage(pkg);

    // 加载知识点
    try {
      const knowledgeResponse = await axios.get(`/api/sbpack/packages/${pkg.id}/knowledge`);
      setKnowledgeItems(knowledgeResponse.data);
    } catch (error) {
      message.error('加载知识点失败');
    }

    // 加载技能
    try {
      const skillResponse = await axios.get(`/api/sbpack/packages/${pkg.id}/skills`);
      setSkillItems(skillResponse.data);
    } catch (error) {
      message.error('加载技能失败');
    }
  };

  const handleFreeze = async (trackType: 'knowledge' | 'skill') => {
    if (!selectedPackage) return;

    Modal.confirm({
      title: `确认冻结${trackType === 'knowledge' ? '知识轨' : '技能轨'}？`,
      content: '冻结后将无法修改，只能通过解冻后重新生产。',
      okText: '确认冻结',
      cancelText: '取消',
      onOk: async () => {
        try {
          await axios.post('/api/sbpack/freeze', {
            package_id: selectedPackage.id,
            track_type: trackType
          });
          message.success(`${trackType === 'knowledge' ? '知识轨' : '技能轨'}已冻结`);
          loadPackages();
        } catch (error: any) {
          message.error(error.response?.data?.detail || '冻结失败');
        }
      }
    });
  };

  const handleBuild = async () => {
    if (!selectedPackage) return;

    // 检查双轨是否已冻结
    if (!selectedPackage.knowledge_frozen || !selectedPackage.skill_frozen) {
      message.warning('请先冻结知识轨和技能轨');
      return;
    }

    setBuildModalVisible(true);
    setBuildProgress(0);

    try {
      // 模拟构建进度
      const progressInterval = setInterval(() => {
        setBuildProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 500);

      const response = await axios.post('/api/sbpack/build', {
        package_id: selectedPackage.id
      });

      clearInterval(progressInterval);
      setBuildProgress(100);

      setTimeout(() => {
        message.success('SBPACK构建成功！');
        setBuildModalVisible(false);
        loadPackages();
      }, 1000);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '构建失败');
      setBuildModalVisible(false);
    }
  };

  const handleExportObsidian = async () => {
    if (!selectedPackage) return;

    if (!selectedPackage.is_built) {
      message.warning('请先构建SBPACK');
      return;
    }

    try {
      message.info('正在导出到Obsidian格式...');
      // TODO: 调用Obsidian导出API
      await axios.post(`/api/obsidian/export/${selectedPackage.id}`);
      message.success('导出成功！');
    } catch (error) {
      message.error('导出失败');
    }
  };

  const knowledgeColumns = [
    {
      title: 'ID',
      dataIndex: 'knowledge_id',
      key: 'knowledge_id',
      width: 150,
      ellipsis: true
    },
    {
      title: '类型',
      dataIndex: 'knowledge_type',
      key: 'knowledge_type',
      width: 120,
      render: (type: string) => {
        const colorMap: any = {
          concept: 'blue',
          claim: 'green',
          principle: 'purple',
          mechanism: 'orange',
          reportedFact: 'cyan',
          argument: 'magenta',
          boundary: 'red',
          counterexample: 'volcano'
        };
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>;
      }
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'is_frozen',
      key: 'is_frozen',
      width: 100,
      render: (frozen: boolean) => (
        frozen ? <Tag icon={<LockOutlined />} color="warning">已冻结</Tag>
               : <Tag icon={<UnlockOutlined />} color="default">未冻结</Tag>
      )
    }
  ];

  const skillColumns = [
    {
      title: 'ID',
      dataIndex: 'skill_id',
      key: 'skill_id',
      width: 150,
      ellipsis: true
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '验证状态',
      key: 'validation',
      width: 150,
      render: (record: SkillItem) => (
        <Space>
          <Tag color={record.v1_passed ? 'success' : 'error'}>V1</Tag>
          <Tag color={record.v2_passed ? 'success' : 'error'}>V2</Tag>
          <Tag color={record.v3_passed ? 'success' : 'error'}>V3</Tag>
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_frozen',
      key: 'is_frozen',
      width: 100,
      render: (frozen: boolean) => (
        frozen ? <Tag icon={<LockOutlined />} color="warning">已冻结</Tag>
               : <Tag icon={<UnlockOutlined />} color="default">未冻结</Tag>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card title="SBPACK 2.0 管理" extra={
        <Button type="primary" onClick={() => navigate(`/projects/${projectId}/sbpack/create`)}>
          创建新包
        </Button>
      }>
        {loading ? (
          <Spin tip="加载中..." />
        ) : selectedPackage ? (
          <>
            {/* 包概览 */}
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="知识点"
                    value={selectedPackage.knowledge_count}
                    prefix={<BookOutlined />}
                    suffix={selectedPackage.knowledge_frozen && <LockOutlined style={{ fontSize: 14 }} />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="技能"
                    value={selectedPackage.skill_count}
                    prefix={<BulbOutlined />}
                    suffix={selectedPackage.skill_frozen && <LockOutlined style={{ fontSize: 14 }} />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="关系"
                    value={selectedPackage.relation_count}
                    prefix={<ExperimentOutlined />}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card>
                  <Statistic
                    title="构建状态"
                    value={selectedPackage.is_built ? '已构建' : '未构建'}
                    prefix={selectedPackage.is_built ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                    valueStyle={{ color: selectedPackage.is_built ? '#3f8600' : '#cf1322' }}
                  />
                </Card>
              </Col>
            </Row>

            {/* 包信息 */}
            <Descriptions title="包信息" bordered style={{ marginBottom: 24 }}>
              <Descriptions.Item label="包名称">{selectedPackage.package_name}</Descriptions.Item>
              <Descriptions.Item label="协议版本">{selectedPackage.protocol_version}</Descriptions.Item>
              <Descriptions.Item label="包版本">{selectedPackage.version}</Descriptions.Item>
              <Descriptions.Item label="来源标题">{selectedPackage.source_title}</Descriptions.Item>
              <Descriptions.Item label="来源作者">{selectedPackage.source_author}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{new Date(selectedPackage.created_at).toLocaleString()}</Descriptions.Item>
            </Descriptions>

            {/* 操作按钮 */}
            <Space style={{ marginBottom: 24 }}>
              <Button
                type="primary"
                icon={<LockOutlined />}
                disabled={selectedPackage.knowledge_frozen}
                onClick={() => handleFreeze('knowledge')}
              >
                冻结知识轨
              </Button>
              <Button
                type="primary"
                icon={<LockOutlined />}
                disabled={selectedPackage.skill_frozen}
                onClick={() => handleFreeze('skill')}
              >
                冻结技能轨
              </Button>
              <Button
                type="primary"
                icon={<FileTextOutlined />}
                disabled={!selectedPackage.knowledge_frozen || !selectedPackage.skill_frozen || selectedPackage.is_built}
                onClick={handleBuild}
              >
                构建SBPACK
              </Button>
              <Button
                icon={<DownloadOutlined />}
                disabled={!selectedPackage.is_built}
              >
                下载.sbpack
              </Button>
              <Button
                icon={<ExportOutlined />}
                disabled={!selectedPackage.is_built}
                onClick={handleExportObsidian}
              >
                导出到Obsidian
              </Button>
            </Space>

            {/* 双轨内容 */}
            <Tabs defaultActiveKey="knowledge">
              <TabPane tab={`知识轨 (${knowledgeItems.length})`} key="knowledge">
                <Table
                  dataSource={knowledgeItems}
                  columns={knowledgeColumns}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                />
              </TabPane>
              <TabPane tab={`技能轨 (${skillItems.length})`} key="skill">
                <Table
                  dataSource={skillItems}
                  columns={skillColumns}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                />
              </TabPane>
            </Tabs>
          </>
        ) : (
          <Alert
            message="没有SBPACK包"
            description="请创建一个新的SBPACK包开始蒸馏"
            type="info"
            showIcon
          />
        )}
      </Card>

      {/* 构建进度Modal */}
      <Modal
        title="构建SBPACK"
        visible={buildModalVisible}
        footer={null}
        closable={false}
      >
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Progress type="circle" percent={buildProgress} />
          <div style={{ marginTop: 16 }}>
            {buildProgress < 100 ? '正在构建...' : '构建完成！'}
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default SBPACKManager;
