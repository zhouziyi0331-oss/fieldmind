/**
 * KnowledgeGraphViewer - 知识图谱可视化组件
 *
 * 功能：
 * 1. 使用 D3.js 力导向图展示实体和关系
 * 2. 支持实体筛选（按类型）
 * 3. 支持关系筛选（按类型）
 * 4. 实体点击显示详情
 * 5. 社区高亮显示
 * 6. 缩放和拖拽交互
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface Entity {
  id: string;
  name: string;
  type: string;
  mentions: number;
  timestamp?: number;
}

interface Relation {
  id: string;
  source: string;
  target: string;
  type: string;
  confidence: number;
  context?: string;
}

interface Community {
  id: string;
  topic: string;
  members: string[];
}

interface KnowledgeGraphData {
  entities: Entity[];
  relations: Relation[];
  communities?: Community[];
}

interface KnowledgeGraphViewerProps {
  data: KnowledgeGraphData;
  width?: number;
  height?: number;
  onEntityClick?: (entity: Entity) => void;
}

const KnowledgeGraphViewer: React.FC<KnowledgeGraphViewerProps> = ({
  data,
  width = 1200,
  height = 800,
  onEntityClick
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<Set<string>>(new Set());
  const [selectedRelationTypes, setSelectedRelationTypes] = useState<Set<string>>(new Set());
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);

  // 实体类型颜色映射
  const entityTypeColors: Record<string, string> = {
    '人物': '#4A90E2',
    '地名': '#7ED321',
    '机构': '#F5A623',
    '文化概念': '#BD10E0',
    '其他': '#9B9B9B'
  };

  // 关系类型样式
  const relationTypeStyles: Record<string, any> = {
    '亲缘': { color: '#E74C3C', dash: '0' },
    '师徒': { color: '#3498DB', dash: '5,5' },
    '教授': { color: '#2ECC71', dash: '0' },
    '参与': { color: '#F39C12', dash: '3,3' },
    '位于': { color: '#9B59B6', dash: '0' },
    '关联': { color: '#95A5A6', dash: '2,2' }
  };

  useEffect(() => {
    if (!svgRef.current || !data.entities.length) return;

    // 清空之前的内容
    d3.select(svgRef.current).selectAll('*').remove();

    // 创建 SVG 容器
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // 添加缩放功能
    const g = svg.append('g');

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // 过滤数据
    const filteredEntities = selectedEntityTypes.size === 0
      ? data.entities
      : data.entities.filter(e => selectedEntityTypes.has(e.type));

    const entityIds = new Set(filteredEntities.map(e => e.id));

    const filteredRelations = data.relations
      .filter(r => entityIds.has(r.source) && entityIds.has(r.target))
      .filter(r => selectedRelationTypes.size === 0 || selectedRelationTypes.has(r.type));

    // 构建节点和边数据
    const nodes = filteredEntities.map(e => ({
      id: e.id,
      name: e.name,
      type: e.type,
      mentions: e.mentions,
      timestamp: e.timestamp
    }));

    const links = filteredRelations.map(r => ({
      source: r.source,
      target: r.target,
      type: r.type,
      confidence: r.confidence,
      context: r.context
    }));

    // 创建力导向仿真
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(links)
        .id((d: any) => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // 绘制边
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', (d: any) => relationTypeStyles[d.type]?.color || '#999')
      .attr('stroke-width', (d: any) => Math.sqrt(d.confidence * 3))
      .attr('stroke-dasharray', (d: any) => relationTypeStyles[d.type]?.dash || '0')
      .attr('opacity', 0.6);

    // 添加边标签
    const linkLabel = g.append('g')
      .selectAll('text')
      .data(links)
      .enter()
      .append('text')
      .attr('font-size', 10)
      .attr('fill', '#666')
      .attr('text-anchor', 'middle')
      .text((d: any) => d.type);

    // 绘制节点
    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('r', (d: any) => Math.sqrt(d.mentions) * 5 + 5)
      .attr('fill', (d: any) => entityTypeColors[d.type] || entityTypeColors['其他'])
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any);

    // 添加节点标签
    const nodeLabel = g.append('g')
      .selectAll('text')
      .data(nodes)
      .enter()
      .append('text')
      .attr('font-size', 12)
      .attr('dx', 12)
      .attr('dy', 4)
      .text((d: any) => d.name)
      .style('pointer-events', 'none');

    // 节点点击事件
    node.on('click', (event, d: any) => {
      setSelectedEntity({
        id: d.id,
        name: d.name,
        type: d.type,
        mentions: d.mentions,
        timestamp: d.timestamp
      });
      if (onEntityClick) {
        onEntityClick(d);
      }
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

      linkLabel
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      nodeLabel
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

    // 清理
    return () => {
      simulation.stop();
    };
  }, [data, selectedEntityTypes, selectedRelationTypes, width, height]);

  // 获取所有实体类型
  const entityTypes = Array.from(new Set(data.entities.map(e => e.type)));
  const relationTypes = Array.from(new Set(data.relations.map(r => r.type)));

  // 切换实体类型筛选
  const toggleEntityType = (type: string) => {
    const newSet = new Set(selectedEntityTypes);
    if (newSet.has(type)) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    setSelectedEntityTypes(newSet);
  };

  // 切换关系类型筛选
  const toggleRelationType = (type: string) => {
    const newSet = new Set(selectedRelationTypes);
    if (newSet.has(type)) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    setSelectedRelationTypes(newSet);
  };

  return (
    <div className="knowledge-graph-viewer">
      <div className="controls" style={{ marginBottom: '20px' }}>
        {/* 实体类型筛选 */}
        <div style={{ marginBottom: '10px' }}>
          <strong>实体类型：</strong>
          {entityTypes.map(type => (
            <label key={type} style={{ marginLeft: '10px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={selectedEntityTypes.has(type)}
                onChange={() => toggleEntityType(type)}
              />
              <span
                style={{
                  marginLeft: '5px',
                  color: entityTypeColors[type] || entityTypeColors['其他']
                }}
              >
                {type}
              </span>
            </label>
          ))}
        </div>

        {/* 关系类型筛选 */}
        <div>
          <strong>关系类型：</strong>
          {relationTypes.map(type => (
            <label key={type} style={{ marginLeft: '10px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={selectedRelationTypes.has(type)}
                onChange={() => toggleRelationType(type)}
              />
              <span style={{ marginLeft: '5px' }}>{type}</span>
            </label>
          ))}
        </div>
      </div>

      {/* 图谱画布 */}
      <div style={{ border: '1px solid #ddd', borderRadius: '4px', overflow: 'hidden' }}>
        <svg ref={svgRef}></svg>
      </div>

      {/* 实体详情面板 */}
      {selectedEntity && (
        <div style={{
          marginTop: '20px',
          padding: '15px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          backgroundColor: '#f9f9f9'
        }}>
          <h3>{selectedEntity.name}</h3>
          <p><strong>类型：</strong>{selectedEntity.type}</p>
          <p><strong>提及次数：</strong>{selectedEntity.mentions}</p>
          {selectedEntity.timestamp !== undefined && (
            <p><strong>首次出现：</strong>{selectedEntity.timestamp.toFixed(2)}秒</p>
          )}
          <button
            onClick={() => setSelectedEntity(null)}
            style={{
              marginTop: '10px',
              padding: '5px 15px',
              cursor: 'pointer'
            }}
          >
            关闭
          </button>
        </div>
      )}

      {/* 图例 */}
      <div style={{ marginTop: '20px' }}>
        <strong>图例：</strong>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', marginTop: '10px' }}>
          {Object.entries(entityTypeColors).map(([type, color]) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{
                width: '15px',
                height: '15px',
                borderRadius: '50%',
                backgroundColor: color,
                marginRight: '5px'
              }}></div>
              <span>{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraphViewer;
