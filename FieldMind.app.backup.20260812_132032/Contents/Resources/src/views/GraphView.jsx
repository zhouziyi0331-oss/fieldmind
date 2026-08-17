import React, { useState, useEffect, useRef } from 'react'
import { graphAPI } from '../api/client'
import * as d3 from 'd3'
import './GraphView.css'

function GraphView() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState('full')
  const svgRef = useRef(null)

  useEffect(() => {
    loadGraphData()
  }, [mode])

  useEffect(() => {
    if (graphData.nodes.length > 0) {
      renderGraph()
    }
  }, [graphData])

  const loadGraphData = async () => {
    setLoading(true)
    try {
      const data = await graphAPI.getGraphData(mode)
      setGraphData(data)
    } catch (error) {
      console.error('Load graph failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const renderGraph = () => {
    if (!svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // 创建力导向图
    const simulation = d3.forceSimulation(graphData.nodes)
      .force('link', d3.forceLink(graphData.edges)
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30))

    // 添加缩放功能
    const g = svg.append('g')
    svg.call(d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      }))

    // 绘制边
    const link = g.append('g')
      .selectAll('line')
      .data(graphData.edges)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2)

    // 绘制节点
    const node = g.append('g')
      .selectAll('circle')
      .data(graphData.nodes)
      .join('circle')
      .attr('r', 10)
      .attr('fill', d => getNodeColor(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .call(drag(simulation))

    // 添加节点标签
    const label = g.append('g')
      .selectAll('text')
      .data(graphData.nodes)
      .join('text')
      .text(d => d.label)
      .attr('font-size', 12)
      .attr('dx', 15)
      .attr('dy', 4)
      .style('pointer-events', 'none')

    // 添加提示信息
    node.append('title')
      .text(d => `${d.label} (${d.type})`)

    // 更新位置
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y)

      label
        .attr('x', d => d.x)
        .attr('y', d => d.y)
    })

    // 拖拽功能
    function drag(simulation) {
      function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        event.subject.fx = event.subject.x
        event.subject.fy = event.subject.y
      }

      function dragged(event) {
        event.subject.fx = event.x
        event.subject.fy = event.y
      }

      function dragended(event) {
        if (!event.active) simulation.alphaTarget(0)
        event.subject.fx = null
        event.subject.fy = null
      }

      return d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
    }
  }

  const getNodeColor = (type) => {
    const colors = {
      person: '#8b5cf6',
      event: '#10b981',
      place: '#f59e0b',
      theme: '#ec4899',
      media: '#3b82f6',
      time: '#6366f1',
    }
    return colors[type] || '#64748b'
  }

  if (loading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="spinner"></div>
          <p>加载图谱数据...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page graph-page">
      <div className="page-header">
        <h1 className="page-title">🕸️ 知识图谱</h1>
        <p className="page-description">可视化人物关系、事件联系和主题网络</p>
      </div>

      <div className="card graph-controls">
        <div className="control-group">
          <label>图谱模式:</label>
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="full">完整图谱</option>
            <option value="person">人物关系</option>
            <option value="event">事件网络</option>
            <option value="theme">主题聚类</option>
          </select>
        </div>

        <div className="legend">
          <div className="legend-item">
            <span className="legend-color" style={{ background: '#8b5cf6' }}></span>
            <span>人物</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ background: '#10b981' }}></span>
            <span>事件</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ background: '#f59e0b' }}></span>
            <span>地点</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ background: '#ec4899' }}></span>
            <span>主题</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ background: '#3b82f6' }}></span>
            <span>媒体</span>
          </div>
        </div>
      </div>

      {graphData.nodes.length > 0 ? (
        <div className="card graph-container">
          <svg ref={svgRef} className="graph-svg"></svg>
          <div className="graph-hint">
            💡 拖拽节点可以调整布局，滚轮缩放，拖动背景平移
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">🕸️</div>
          <h3 className="empty-state-title">暂无图谱数据</h3>
          <p className="empty-state-description">
            上传并处理田野调查材料后，系统会自动构建知识图谱
          </p>
        </div>
      )}
    </div>
  )
}

export default GraphView
