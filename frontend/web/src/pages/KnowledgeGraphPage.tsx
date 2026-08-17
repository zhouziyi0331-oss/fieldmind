import React, { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import * as d3 from 'd3';
import { useAppContext } from '../contexts/AppContext';
import {
  AgentOrchestrationPanel,
  AgentExecutionMonitor,
  AgentResultsViewer
} from '../components';
import {
  Sparkles,
  X,
  Lightbulb,
  Network,
  TrendingUp,
  ChevronRight
} from 'lucide-react';

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

// Agent任务建议类型
interface TaskSuggestion {
  id: string;
  title: string;
  description: string;
  targetEntity: string;
  agentType: 'knowledge' | 'search' | 'summary';
  icon: React.ReactNode;
  priority: 'high' | 'medium' | 'low';
}

const KnowledgeGraphPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [viewMode, setViewMode] = useState<'graph' | 'keywords'>('graph');
  const { navigateToChat, selectEntity } = useAppContext();

  // Agent panel state
  const [showAgentPanel, setShowAgentPanel] = useState(false);
  const [agentExecutionId, setAgentExecutionId] = useState<string | null>(null);
  const [agentResult, setAgentResult] = useState<any>(null);
  const [agentResultType, setAgentResultType] = useState<'knowledge' | 'search' | 'summary' | 'transcript' | null>(null);
  const [taskSuggestions, setTaskSuggestions] = useState<TaskSuggestion[]>([]);

  // 获取知识图谱数据
  const { data: graphData, isLoading: graphLoading, error: graphError } = useQuery({
    queryKey: ['knowledgeGraph', projectId],
    queryFn: () => api.knowledgeGraph.getGraph(Number(projectId)),
    enabled: !!projectId && viewMode === 'graph',
  }) as { data: GraphData | undefined; isLoading: boolean; error: Error | null };

  // 获取关键词数据
  const { data: keywordsData, isLoading: keywordsLoading } = useQuery({
    queryKey: ['keywords', projectId],
    queryFn: () => api.knowledgeGraph.getKeywords(Number(projectId), 50),
    enabled: !!projectId && viewMode === 'keywords',
  }) as { data: Keyword[] | undefined; isLoading: boolean };

  // 处理节点点击 - 选中实体并生成Agent任务建议
  const handleNodeClick = (node: Node) => {
    setSelectedNode(node);
    selectEntity(node.label, node.type);

    // 打开Agent面板
    setShowAgentPanel(true);

    // 生成智能任务建议
    generateTaskSuggestions(node);
  };

  // 生成基于实体的Agent任务建议
  const generateTaskSuggestions = (node: Node) => {
    const suggestions: TaskSuggestion[] = [];

    // 建议1: 深度知识提取
    suggestions.push({
      id: `knowledge-${node.id}`,
      title: `深度分析"${node.label}"`,
      description: `使用Knowledge Agent深度提取关于"${node.label}"的所有相关知识，包括定义、特征、关系等`,
      targetEntity: node.label,
      agentType: 'knowledge',
      icon: <Sparkles className="w-4 h-4" />,
      priority: 'high'
    });

    // 建议2: 关联实体搜索
    if (graphData) {
      const connectedNodes = graphData.edges
        .filter(e =>
          (typeof e.source === 'string' ? e.source : e.source.id) === node.id ||
          (typeof e.target === 'string' ? e.target : e.target.id) === node.id
        )
        .map(e => {
          const sourceId = typeof e.source === 'string' ? e.source : e.source.id;
          const targetId = typeof e.target === 'string' ? e.target : e.target.id;
          return sourceId === node.id ? targetId : sourceId;
        });

      if (connectedNodes.length > 0) {
        suggestions.push({
          id: `search-${node.id}`,
          title: `探索"${node.label}"的关联网络`,
          description: `搜索并分析"${node.label}"与其${connectedNodes.length}个关联实体之间的深层关系`,
          targetEntity: node.label,
          agentType: 'search',
          icon: <Network className="w-4 h-4" />,
          priority: 'medium'
        });
      }
    }

    // 建议3: 实体重要性分析
    suggestions.push({
      id: `summary-${node.id}`,
      title: `评估"${node.label}"的重要性`,
      description: `生成关于"${node.label}"在整个知识体系中的地位和影响力的综合报告`,
      targetEntity: node.label,
      agentType: 'summary',
      icon: <TrendingUp className="w-4 h-4" />,
      priority: 'low'
    });

    setTaskSuggestions(suggestions);
  };

  // 执行建议的Agent任务
  const executeTaskSuggestion = (suggestion: TaskSuggestion) => {
    // 重置Agent面板状态
    setAgentResult(null);
    setAgentResultType(null);

    // TODO: 触发AgentOrchestrationPanel任务的programmatic API
    // 当前需要用户手动在面板中配置，未来可添加自动化接口
  };

  // Agent execution handlers
  const handleAgentExecutionStart = (executionId: string) => {
    setAgentExecutionId(executionId);
    setAgentResult(null);
    setAgentResultType(null);
  };

  const handleAgentComplete = (result: any) => {
    setAgentExecutionId(null);

    if (result?.result?.task_results && result.result.task_results.length > 0) {
      const firstTask = result.result.task_results[0];
      setAgentResult(firstTask.result);
      setAgentResultType(firstTask.agent_type as any);

      // TODO: 动态更新图谱功能 - 需要后端API支持
      // 如果是knowledge agent结果，可以将新发现的实体添加到现有图谱中
    }
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
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
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

            <div className="flex items-center gap-3">
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

              {/* Agent Panel Toggle */}
              <button
                onClick={() => setShowAgentPanel(!showAgentPanel)}
                className={`flex items-center gap-2 px-4 py-2 rounded transition-all ${
                  showAgentPanel
                    ? 'bg-purple-600 text-white'
                    : 'bg-white border-2 border-purple-600 text-purple-600 hover:bg-purple-50'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                <span>Agent分析</span>
                {agentExecutionId && (
                  <span className="ml-1 w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph Area */}
        <div className="flex-1 overflow-auto">
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
                          <div className="space-y-2">
                            <button
                              onClick={() => setShowAgentPanel(true)}
                              className="w-full px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors text-sm font-medium flex items-center justify-center gap-2"
                            >
                              <Sparkles className="w-4 h-4" />
                              <span>Agent深度分析</span>
                            </button>
                            <button
                              onClick={handleAskAboutEntity}
                              className="w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm font-medium"
                            >
                              💬 询问AI关于"{selectedNode.label}"
                            </button>
                          </div>
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

        {/* Agent Panel Sidebar */}
        {showAgentPanel && (
          <div className="w-[500px] bg-white border-l border-gray-200 flex flex-col overflow-hidden">
            {/* Panel Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <h3 className="font-bold text-gray-900">Agent智能分析</h3>
                {agentExecutionId && (
                  <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                    执行中
                  </span>
                )}
              </div>
              <button
                onClick={() => setShowAgentPanel(false)}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>

            {/* Panel Content */}
            <div className="flex-1 overflow-y-auto">
              {/* Task Suggestions (when entity selected) */}
              {selectedNode && taskSuggestions.length > 0 && !agentExecutionId && !agentResult && (
                <div className="p-4 border-b border-gray-200 bg-amber-50">
                  <div className="flex items-start gap-2 mb-3">
                    <Lightbulb className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-gray-900 text-sm">智能建议</h4>
                      <p className="text-xs text-gray-600 mt-0.5">
                        基于实体 "<span className="font-medium text-gray-900">{selectedNode.label}</span>" 的推荐任务
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    {taskSuggestions.map((suggestion) => (
                      <div
                        key={suggestion.id}
                        className="bg-white rounded-lg p-3 border border-amber-200 hover:border-amber-400 transition-colors cursor-pointer"
                        onClick={() => executeTaskSuggestion(suggestion)}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-start gap-2 flex-1">
                            <div className={`p-1.5 rounded ${
                              suggestion.priority === 'high' ? 'bg-red-100 text-red-600' :
                              suggestion.priority === 'medium' ? 'bg-blue-100 text-blue-600' :
                              'bg-gray-100 text-gray-600'
                            }`}>
                              {suggestion.icon}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-sm text-gray-900">{suggestion.title}</div>
                              <div className="text-xs text-gray-600 mt-1">{suggestion.description}</div>
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0 mt-1" />
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-3 text-xs text-gray-500 text-center">
                    💡 点击建议卡片在下方面板中查看预填配置
                  </div>
                </div>
              )}

              {/* Execution Monitor */}
              {agentExecutionId && (
                <AgentExecutionMonitor
                  executionId={agentExecutionId}
                  projectId={projectId ? Number(projectId) : undefined}
                  autoRefresh={true}
                  refreshInterval={2000}
                  onComplete={handleAgentComplete}
                  onError={(error) => {
                    console.error('Agent execution error:', error);
                    setAgentExecutionId(null);
                  }}
                />
              )}

              {/* Results Viewer */}
              {agentResult && agentResultType && !agentExecutionId && (
                <div>
                  <AgentResultsViewer
                    result={agentResult}
                    resultType={agentResultType}
                  />
                  <div className="p-4 border-t border-gray-200 bg-gray-50">
                    <button
                      onClick={() => {
                        setAgentResult(null);
                        setAgentResultType(null);
                      }}
                      className="w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors text-sm font-medium"
                    >
                      返回任务编排
                    </button>
                  </div>
                </div>
              )}

              {/* Orchestration Panel */}
              {!agentExecutionId && !agentResult && (
                <AgentOrchestrationPanel
                  projectId={projectId ? Number(projectId) : undefined}
                  documentIds={[]}
                  onExecutionStart={handleAgentExecutionStart}
                  onComplete={handleAgentComplete}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeGraphPage;
