/**
 * KnowledgeNetworkViewer - 增强版知识脉络可视化
 *
 * 功能：
 * 1. 分层展示：大脉络 → 子脉络 → 实体
 * 2. 可折叠节点：点击展开/收起子脉络
 * 3. 维度聚类：按照业务维度（文化、经济、社会、政策）分组
 * 4. 频次热力图：节点大小和颜色表示频次
 * 5. 侧边详情面板：显示节点详细信息
 * 6. 搜索和过滤：快速定位实体
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface Dimension {
  id: string;
  name: string;
  keywords: string[];
  frequency: number;
  sub_dimensions?: SubDimension[];
}

interface SubDimension {
  id: string;
  name: string;
  parent_dimension: string;
  keywords: string[];
  frequency: number;
  entities?: Entity[];
}

interface Entity {
  id: string;
  name: string;
  type: string;
  mentions: number;
  sub_dimension?: string;
}

interface Relation {
  source: string;
  target: string;
  type: string;
  weight: number;
}

interface NetworkData {
  dimensions: Dimension[];
  entities: Entity[];
  relations: Relation[];
}

interface KnowledgeNetworkViewerProps {
  projectId: number;
  width?: number;
  height?: number;
}

type NodeType = 'dimension' | 'sub_dimension' | 'entity';

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: NodeType;
  frequency?: number;
  mentions?: number;
  children?: GraphNode[];
  collapsed?: boolean;
  parent?: string;
}

const KnowledgeNetworkViewer: React.FC<KnowledgeNetworkViewerProps> = ({
  projectId,
  width = 1200,
  height = 800
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [data, setData] = useState<NetworkData | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDimension, setFilterDimension] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  // 维度颜色映射
  const dimensionColors: Record<string, string> = {
    '文化': '#9b59b6',
    '经济': '#27ae60',
    '社会': '#3498db',
    '政策': '#e74c3c',
    '其他': '#95a5a6'
  };

  // 加载数据
  useEffect(() => {
    fetchNetworkData();
  }, [projectId]);

  const fetchNetworkData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/knowledge-graph/${projectId}/network`);
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error('加载知识网络失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 构建图谱数据
  const buildGraphData = (): { nodes: GraphNode[], links: any[] } => {
    if (!data) return { nodes: [], links: [] };

    const nodes: GraphNode[] = [];
    const links: any[] = [];

    // 添加维度节点
    data.dimensions.forEach(dim => {
      const dimNode: GraphNode = {
        id: dim.id,
        name: dim.name,
        type: 'dimension',
        frequency: dim.frequency,
        collapsed: true,
        children: []
      };

      nodes.push(dimNode);

      // 添加子维度节点（初始隐藏）
      if (dim.sub_dimensions) {
        dim.sub_dimensions.forEach(subDim => {
          const subDimNode: GraphNode = {
            id: subDim.id,
            name: subDim.name,
            type: 'sub_dimension',
            frequency: subDim.frequency,
            parent: dim.id,
            collapsed: true,
            children: []
          };

          // 暂不添加到 nodes（折叠状态）
          dimNode.children!.push(subDimNode);

          // 添加实体节点（初始隐藏）
          if (subDim.entities) {
            subDim.entities.forEach(entity => {
              const entityNode: GraphNode = {
                id: entity.id,
                name: entity.name,
                type: 'entity',
                mentions: entity.mentions,
                parent: subDim.id
              };

              subDimNode.children!.push(entityNode);
            });
          }
        });
      }
    });

    // 添加关系链接
    data.relations.forEach(rel => {
      links.push({
        source: rel.source,
        target: rel.target,
        type: rel.type,
        weight: rel.weight
      });
    });

    return { nodes, links };
  };

  // 渲染图谱
  useEffect(() => {
    if (!svgRef.current || !data) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { nodes, links } = buildGraphData();

    // 创建 g 容器
    const g = svg.append('g');

    // 添加缩放
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // 创建力导向仿真
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(links)
        .id((d: any) => d.id)
        .distance(d => d.type === 'hierarchy' ? 100 : 150))
      .force('charge', d3.forceManyBody()
        .strength((d: any) => d.type === 'dimension' ? -500 : -200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide()
        .radius((d: any) => getNodeRadius(d) + 10));

    // 绘制连接线
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d: any) => Math.sqrt(d.weight || 1));

    // 绘制节点
    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('r', (d: any) => getNodeRadius(d))
      .attr('fill', (d: any) => getNodeColor(d))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any);

    // 添加节点标签
    const label = g.append('g')
      .selectAll('text')
      .data(nodes)
      .enter()
      .append('text')
      .text((d: any) => d.name)
      .attr('font-size', (d: any) => d.type === 'dimension' ? 14 : 12)
      .attr('font-weight', (d: any) => d.type === 'dimension' ? 'bold' : 'normal')
      .attr('dx', (d: any) => getNodeRadius(d) + 5)
      .attr('dy', 4)
      .style('pointer-events', 'none');

    // 节点点击事件
    node.on('click', (event, d: any) => {
      event.stopPropagation();
      handleNodeClick(d);
    });

    // 节点悬停效果
    node.on('mouseenter', function(event, d: any) {
      d3.select(this)
        .attr('stroke', '#000')
        .attr('stroke-width', 3);
    })
    .on('mouseleave', function() {
      d3.select(this)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    });

    // 更新位置
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      label
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    // 拖拽函数
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [data, filterDimension, searchTerm]);

  // 节点点击处理
  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);

    // 如果是维度或子维度，切换折叠状态
    if (node.type === 'dimension' || node.type === 'sub_dimension') {
      node.collapsed = !node.collapsed;
      // 重新渲染以展开/折叠子节点
      setData({ ...data! });
    }
  };

  // 获取节点半径
  const getNodeRadius = (node: GraphNode): number => {
    if (node.type === 'dimension') {
      return Math.sqrt((node.frequency || 0) / 10) * 20 + 30;
    } else if (node.type === 'sub_dimension') {
      return Math.sqrt((node.frequency || 0) / 10) * 15 + 20;
    } else {
      return Math.sqrt((node.mentions || 0)) * 3 + 8;
    }
  };

  // 获取节点颜色
  const getNodeColor = (node: GraphNode): string => {
    if (node.type === 'dimension') {
      return dimensionColors[node.name] || dimensionColors['其他'];
    } else if (node.type === 'sub_dimension') {
      const parentDim = data?.dimensions.find(d => d.id === node.parent);
      const baseColor = dimensionColors[parentDim?.name || '其他'];
      return d3.color(baseColor)!.brighter(0.5).toString();
    } else {
      return '#95a5a6';
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <div>加载知识网络中...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '50px', color: '#e74c3c' }}>
        加载失败
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: '20px' }}>
      {/* 主图谱区域 */}
      <div style={{ flex: 1 }}>
        {/* 控制面板 */}
        <div style={{
          padding: '15px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          marginBottom: '15px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
            {/* 搜索框 */}
            <input
              type="text"
              placeholder="搜索实体..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />

            {/* 维度过滤 */}
            <select
              value={filterDimension}
              onChange={(e) => setFilterDimension(e.target.value)}
              style={{
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            >
              <option value="all">所有维度</option>
              {Object.keys(dimensionColors).map(dim => (
                <option key={dim} value={dim}>{dim}</option>
              ))}
            </select>

            {/* 刷新按钮 */}
            <button
              onClick={fetchNetworkData}
              style={{
                padding: '8px 16px',
                backgroundColor: '#3498db',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              🔄 刷新
            </button>
          </div>
        </div>

        {/* 图谱画布 */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          overflow: 'hidden'
        }}>
          <svg ref={svgRef} width={width} height={height}></svg>
        </div>

        {/* 图例 */}
        <div style={{
          marginTop: '15px',
          padding: '15px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <strong>图例：</strong>
          <div style={{ display: 'flex', gap: '20px', marginTop: '10px', flexWrap: 'wrap' }}>
            {Object.entries(dimensionColors).map(([name, color]) => (
              <div key={name} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  backgroundColor: color
                }}></div>
                <span>{name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 侧边详情面板 */}
      {selectedNode && (
        <div style={{
          width: '350px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          padding: '20px',
          maxHeight: height,
          overflowY: 'auto'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ margin: 0 }}>节点详情</h3>
            <button
              onClick={() => setSelectedNode(null)}
              style={{
                border: 'none',
                background: 'none',
                fontSize: '20px',
                cursor: 'pointer',
                color: '#95a5a6'
              }}
            >
              ×
            </button>
          </div>

          <div>
            <div style={{ marginBottom: '15px' }}>
              <div style={{ fontSize: '12px', color: '#7f8c8d', marginBottom: '5px' }}>类型</div>
              <div style={{
                padding: '4px 8px',
                backgroundColor: '#ecf0f1',
                borderRadius: '4px',
                display: 'inline-block'
              }}>
                {selectedNode.type === 'dimension' ? '维度' :
                 selectedNode.type === 'sub_dimension' ? '子维度' : '实体'}
              </div>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <div style={{ fontSize: '12px', color: '#7f8c8d', marginBottom: '5px' }}>名称</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{selectedNode.name}</div>
            </div>

            {selectedNode.frequency !== undefined && (
              <div style={{ marginBottom: '15px' }}>
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginBottom: '5px' }}>频次</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3498db' }}>
                  {selectedNode.frequency}
                </div>
              </div>
            )}

            {selectedNode.mentions !== undefined && (
              <div style={{ marginBottom: '15px' }}>
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginBottom: '5px' }}>提及次数</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#27ae60' }}>
                  {selectedNode.mentions}
                </div>
              </div>
            )}

            {selectedNode.children && selectedNode.children.length > 0 && (
              <div style={{ marginBottom: '15px' }}>
                <div style={{ fontSize: '12px', color: '#7f8c8d', marginBottom: '5px' }}>子节点</div>
                <div>{selectedNode.children.length} 个</div>
                <button
                  onClick={() => handleNodeClick(selectedNode)}
                  style={{
                    marginTop: '10px',
                    padding: '8px 16px',
                    backgroundColor: '#3498db',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    width: '100%'
                  }}
                >
                  {selectedNode.collapsed ? '展开子节点' : '收起子节点'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeNetworkViewer;
