import React, { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import * as d3 from 'd3';
import { useAppContext } from '../contexts/AppContext';

interface Node {
  id: string;
  label: string;
  type: string;
  group: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface Edge {
  id: string;
  source: string | Node;
  target: string | Node;
  label: string;
  type: string;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
  statistics: {
    total_nodes: number;
    total_edges: number;
    node_types: Record<string, number>;
  };
}

interface Keyword {
  text: string;
  value: number;
  frequency: number;
}

const KnowledgeGraphPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [viewMode, setViewMode] = useState<'graph' | 'keywords'>('graph');
  const { navigateToChat, selectEntity } = useAppContext();

  // 获取知识图谱数据
  const { data: graphData, isLoading: graphLoading, error: graphError } = useQuery<GraphData>({
    queryKey: ['knowledgeGraph', projectId],
    queryFn: () => api.knowledgeGraph.getGraph(Number(projectId)),
    enabled: !!projectId && viewMode === 'graph',
  });

  // 获取关键词数据
  const { data: keywordsData, isLoading: keywordsLoading } = useQuery<Keyword[]>({
    queryKey: ['keywords', projectId],
    queryFn: () => api.knowledgeGraph.getKeywords(Number(projectId), 50),
    enabled: !!projectId && viewMode === 'keywords',
  });

  // 处理节点点击 - 选中实体并提供跳转选项
  const handleNodeClick = (node: Node) => {
    setSelectedNode(node);
    selectEntity(node.label, node.type);
    console.log('[KnowledgeGraphPage] 节点被点击:', node.label);
  };

  // 跳转到聊天页并自动提问
  const handleAskAboutEntity = () => {
    if (!selectedNode) return;
    const question = `请详细介绍一下"${selectedNode.label}"`;
    navigateToChat(question);
  };

  // D3.js 可视化
  useEffect(() => {
    if (!graphData || !svgRef.current || viewMode !== 'graph') return;
    if (graphData.nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // 创建力导向图
    const simulation = d3.forceSimulation<Node>(graphData.nodes)
      .force('link', d3.forceLink<Node, Edge>(graphData.edges)
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // 创建容器
    const g = svg.append('g');

    // 添加缩放
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // 颜色映射
    const colorScale = d3.scaleOrdinal<string>()
      .domain(['person', 'location', 'organization', 'date', 'concept'])
      .range(['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']);

    // 绘制边
    const link = g.append('g')
      .selectAll('line')
      .data(graphData.edges)
      .join('line')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.6);

    // 绘制节点
    const node = g.append('g')
      .selectAll('circle')
      .data(graphData.nodes)
      .join('circle')
      .attr('r', 8)
      .attr('fill', d => colorScale(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(d3.drag<SVGCircleElement, Node>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))
      .on('click', (event, d) => {
        handleNodeClick(d);
        event.stopPropagation();
      })
      .on('mouseover', function() {
        d3.select(this).attr('r', 12);
      })
      .on('mouseout', function() {
        d3.select(this).attr('r', 8);
      });

    // 添加标签
    const label = g.append('g')
      .selectAll('text')
      .data(graphData.nodes)
      .join('text')
      .text(d => d.label)
      .attr('font-size', 10)
      .attr('dx', 12)
      .attr('dy', 4)
      .attr('fill', '#334155')
      .style('pointer-events', 'none')
      .style('user-select', 'none');

    // 更新位置
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as Node).x!)
        .attr('y1', d => (d.source as Node).y!)
        .attr('x2', d => (d.target as Node).x!)
        .attr('y2', d => (d.target as Node).y!);

      node
        .attr('cx', d => d.x!)
        .attr('cy', d => d.y!);

      label
        .attr('x', d => d.x!)
        .attr('y', d => d.y!);
    });

    function dragstarted(event: d3.D3DragEvent<SVGCircleElement, Node, Node>) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGCircleElement, Node, Node>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGCircleElement, Node, Node>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [graphData, viewMode]);

  if (graphLoading || keywordsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载知识图谱...</p>
        </div>
      </div>
    );
  }

  if (graphError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">加载失败</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to={`/projects/${projectId}`}
                className="text-gray-600 hover:text-gray-900"
              >
                ← 返回项目
              </Link>
              <div className="h-6 w-px bg-gray-300" />
              <h1 className="text-2xl font-bold">🌳 知识脉络</h1>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('graph')}
                className={`px-4 py-2 rounded ${
                  viewMode === 'graph'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                图谱视图
              </button>
              <button
                onClick={() => setViewMode('keywords')}
                className={`px-4 py-2 rounded ${
                  viewMode === 'keywords'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                关键词云
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {viewMode === 'graph' && graphData && (
          <>
            {graphData.nodes.length === 0 ? (
              <div className="bg-white rounded-xl shadow-md p-8 text-center">
                <svg
                  className="w-24 h-24 mx-auto text-gray-400 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <h2 className="text-xl font-bold text-gray-700 mb-2">暂无知识图谱</h2>
                <p className="text-gray-600">请先上传文档，系统将自动提取实体和关系</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="lg:col-span-3">
                  <div className="bg-white rounded-xl shadow-md p-4">
                    <svg
                      ref={svgRef}
                      className="w-full"
                      style={{ height: '600px' }}
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="bg-white rounded-xl shadow-md p-4">
                    <h3 className="font-bold mb-3">📊 统计信息</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">节点总数:</span>
                        <span className="font-semibold">{graphData.statistics.total_nodes}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">关系总数:</span>
                        <span className="font-semibold">{graphData.statistics.total_edges}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-xl shadow-md p-4">
                    <h3 className="font-bold mb-3">🏷️ 实体类型</h3>
                    <div className="space-y-2">
                      {Object.entries(graphData.statistics.node_types).map(([type, count]) => (
                        <div key={type} className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{
                                backgroundColor:
                                  type === 'person' ? '#3b82f6' :
                                  type === 'location' ? '#10b981' :
                                  type === 'organization' ? '#f59e0b' :
                                  type === 'date' ? '#8b5cf6' :
                                  '#ef4444'
                              }}
                            />
                            <span className="text-gray-700 capitalize">{type}</span>
                          </div>
                          <span className="font-semibold">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {selectedNode && (
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                      <h3 className="font-bold mb-2">🔍 节点详情</h3>
                      <div className="space-y-1 text-sm mb-3">
                        <div><span className="text-gray-600">名称:</span> {selectedNode.label}</div>
                        <div><span className="text-gray-600">类型:</span> {selectedNode.type}</div>
                        <div><span className="text-gray-600">ID:</span> {selectedNode.id}</div>
                      </div>
                      <button
                        onClick={handleAskAboutEntity}
                        className="w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm font-medium"
                      >
                        💬 询问AI关于"{selectedNode.label}"
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {viewMode === 'keywords' && keywordsData && (
          <div className="bg-white rounded-xl shadow-md p-8">
            {keywordsData.length === 0 ? (
              <div className="text-center">
                <p className="text-gray-600">暂无关键词数据</p>
              </div>
            ) : (
              <div className="flex flex-wrap gap-3 justify-center">
                {keywordsData.map((keyword, index) => {
                  const fontSize = Math.max(12, Math.min(32, keyword.frequency * 2));
                  const opacity = Math.max(0.4, Math.min(1, keyword.frequency / 10));

                  return (
                    <span
                      key={index}
                      className="inline-block px-3 py-1 rounded hover:bg-blue-50 cursor-pointer transition-colors"
                      style={{
                        fontSize: `${fontSize}px`,
                        opacity: opacity,
                        color: '#3b82f6'
                      }}
                      title={`出现 ${keyword.frequency} 次 - 点击询问AI`}
                      onClick={() => {
                        const question = `请详细介绍一下"${keyword.text}"`;
                        navigateToChat(question);
                      }}
                    >
                      {keyword.text}
                    </span>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeGraphPage;
