# 网络可视化系统 - 完整实现文档

## 📋 概述

网络可视化系统为报告关系网络和关键词网络提供多格式的可视化数据输出，支持 D3.js、ECharts、Cytoscape.js、Vis.js 四种主流前端可视化库。

**实现日期**: 2024
**状态**: ✅ 已完成并部署

---

## 🏗️ 系统架构

### 核心组件

1. **NetworkVisualizationService** (新增)
   - 文件: `backend/src/app/services/network_visualization_service.py`
   - 功能: 多格式网络数据转换、统计图表生成

2. **Network Visualization API** (新增)
   - 文件: `backend/src/app/api/v1/network_visualization.py`
   - 功能: 8 个可视化 API 端点

### 支持的可视化库

| 库 | 特点 | 适用场景 |
|---|---|---|
| **D3.js** | 强大灵活，高度定制 | 复杂交互、自定义布局 |
| **ECharts** | 配置简单，效果优美 | 快速开发、中文友好 |
| **Cytoscape.js** | 专业网络分析 | 复杂拓扑、生物信息 |
| **Vis.js** | 开箱即用，交互流畅 | 简单快速、默认美观 |

---

## 🎯 核心功能

### 1. 报告关系网络可视化

**支持的数据格式**:

#### D3.js 格式
```json
{
  "format": "d3",
  "nodes": [
    {
      "id": "report-123",
      "name": "调查报告标题",
      "group": "field_research",
      "value": 4.5,
      "degree": 0.234,
      "betweenness": 0.156,
      "pagerank": 0.045
    }
  ],
  "links": [
    {
      "source": "report-123",
      "target": "report-456",
      "value": 0.78,
      "type": "REFERENCES"
    }
  ]
}
```

#### ECharts 格式
```json
{
  "format": "echarts",
  "data": [
    {
      "id": "report-123",
      "name": "调查报告标题",
      "category": "field_research",
      "symbolSize": 45,
      "value": 0.045,
      "label": {
        "show": true
      }
    }
  ],
  "links": [
    {
      "source": "report-123",
      "target": "report-456",
      "value": 0.78,
      "lineStyle": {
        "width": 3.9
      }
    }
  ],
  "categories": [
    {"name": "field_research"},
    {"name": "interview"}
  ]
}
```

#### Cytoscape.js 格式
```json
{
  "format": "cytoscape",
  "elements": [
    {
      "data": {
        "id": "report-123",
        "label": "调查报告标题",
        "type": "field_research",
        "pagerank": 0.045
      },
      "classes": "report-field_research"
    },
    {
      "data": {
        "id": "report-123-report-456",
        "source": "report-123",
        "target": "report-456",
        "strength": 0.78
      }
    }
  ]
}
```

#### Vis.js 格式
```json
{
  "format": "vis",
  "nodes": [
    {
      "id": "report-123",
      "label": "调查报告标题",
      "title": "PageRank: 0.0450",
      "value": 4.5,
      "group": "field_research"
    }
  ],
  "edges": [
    {
      "from": "report-123",
      "to": "report-456",
      "value": 0.78,
      "title": "强度: 0.78"
    }
  ]
}
```

### 2. 关键词网络可视化

**特点**:
- 节点大小 = 关键词频率
- 边粗细 = 共现强度
- 颜色 = 关键词分类
- 支持 top_n 过滤（避免网络过大）
- 支持分类过滤

**数据格式**: 与报告网络类似，字段略有不同

### 3. 社区可视化

**关键词社区检测后的可视化**:
- 自动识别关键词聚类
- 按社区着色
- 显示社区标签
- 支持 ECharts Graph

### 4. 局部网络（子图）

**报告子图**:
- 从指定报告出发
- 提取 1-3 度邻域
- 聚焦查看局部关系

**关键词子图**:
- 从指定关键词出发
- 提取关联关键词
- 探索语义关联

### 5. 统计图表

**报告网络统计**:
- 度分布（柱状图）
- PageRank 分布（饼图）

**关键词网络统计**:
- 分类分布（饼图）
- 频率分布（柱状图）

---

## 🔌 API 端点

### 1. 报告网络可视化
```http
GET /api/v1/projects/{project_id}/report-network/visualization
```

**查询参数**:
- `format_type`: 格式类型 (默认 "d3")
- `min_strength`: 最小关系强度 (默认 0.1)
- `include_isolated`: 是否包含孤立节点 (默认 false)

**响应**:
```json
{
  "success": true,
  "data": {
    "format": "d3",
    "nodes": [...],
    "links": [...],
    "metadata": {
      "project_id": 1,
      "node_count": 50,
      "edge_count": 120
    }
  }
}
```

### 2. 关键词网络可视化
```http
GET /api/v1/projects/{project_id}/keyword-network/visualization
```

**查询参数**:
- `format_type`: 格式类型 (默认 "d3")
- `min_strength`: 最小关系强度 (默认 0.1)
- `top_n`: 只显示前N个关键词 (可选)
- `category_filter`: 分类过滤 (可选)

**用例**:
```bash
# 只显示前100个高频关键词
GET /api/v1/projects/1/keyword-network/visualization?top_n=100

# 只显示"人物"分类的关键词
GET /api/v1/projects/1/keyword-network/visualization?category_filter=人物
```

### 3. 关键词社区可视化
```http
GET /api/v1/projects/{project_id}/keyword-communities/visualization
```

**功能**:
- 自动进行社区检测
- 返回按社区分组的可视化数据

### 4. 网络统计图表
```http
GET /api/v1/projects/{project_id}/network-statistics/charts
```

**查询参数**:
- `network_type`: 网络类型 (report | keyword)

**响应**:
```json
{
  "success": true,
  "data": {
    "charts": [
      {
        "type": "bar",
        "title": "度分布",
        "data": {
          "x": [1, 2, 3, 4, 5],
          "y": [10, 15, 8, 5, 2]
        }
      },
      {
        "type": "pie",
        "title": "PageRank分布",
        "data": [
          {"name": "0-0.01", "value": 20},
          {"name": "0.01-0.05", "value": 15}
        ]
      }
    ]
  }
}
```

### 5. 报告子图
```http
GET /api/v1/projects/{project_id}/report-network/subgraph
```

**查询参数**:
- `report_id` (必需): 中心报告ID
- `depth`: 邻域深度 (默认 1, 范围 1-3)
- `format_type`: 格式类型 (默认 "d3")

**用例**:
```bash
# 获取报告的二度邻居网络
GET /api/v1/projects/1/report-network/subgraph?report_id=abc-123&depth=2&format_type=echarts
```

### 6. 关键词子图
```http
GET /api/v1/projects/{project_id}/keyword-network/subgraph
```

**查询参数**:
- `keyword_id` (必需): 中心关键词ID
- `depth`: 邻域深度 (默认 1, 范围 1-3)
- `format_type`: 格式类型 (默认 "d3")

### 7. 支持的格式列表
```http
GET /api/v1/visualization/formats
```

**响应**:
```json
{
  "success": true,
  "data": {
    "formats": [
      {
        "type": "d3",
        "name": "D3.js",
        "description": "强大的数据驱动文档库",
        "recommended_for": ["高度定制", "复杂交互"],
        "library_url": "https://d3js.org/"
      }
    ]
  }
}
```

---

## 🎨 前端集成示例

### D3.js 力导向图

```javascript
// 获取数据
const response = await fetch('/api/v1/projects/1/report-network/visualization?format_type=d3');
const { data } = await response.json();

// 创建力导向图
const width = 800, height = 600;

const svg = d3.select("#network")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.links).id(d => d.id))
  .force("charge", d3.forceManyBody().strength(-100))
  .force("center", d3.forceCenter(width / 2, height / 2));

// 绘制边
const link = svg.append("g")
  .selectAll("line")
  .data(data.links)
  .enter().append("line")
  .attr("stroke-width", d => d.value * 3);

// 绘制节点
const node = svg.append("g")
  .selectAll("circle")
  .data(data.nodes)
  .enter().append("circle")
  .attr("r", d => d.value)
  .attr("fill", d => color(d.group))
  .call(d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended));

// 添加标签
const label = svg.append("g")
  .selectAll("text")
  .data(data.nodes)
  .enter().append("text")
  .text(d => d.name)
  .attr("font-size", 10);

// 更新位置
simulation.on("tick", () => {
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  node
    .attr("cx", d => d.x)
    .attr("cy", d => d.y);

  label
    .attr("x", d => d.x + 10)
    .attr("y", d => d.y);
});
```

### ECharts 关系图

```javascript
// 获取数据
const response = await fetch('/api/v1/projects/1/keyword-network/visualization?format_type=echarts&top_n=100');
const { data } = await response.json();

// 创建图表
const chart = echarts.init(document.getElementById('network'));

const option = {
  title: {
    text: '关键词网络'
  },
  tooltip: {},
  legend: {
    data: data.categories.map(c => c.name)
  },
  series: [{
    type: 'graph',
    layout: 'force',
    data: data.data,
    links: data.links,
    categories: data.categories,
    roam: true,
    label: {
      show: true,
      position: 'right'
    },
    force: {
      repulsion: 100,
      edgeLength: 50
    },
    emphasis: {
      focus: 'adjacency',
      lineStyle: {
        width: 10
      }
    }
  }]
};

chart.setOption(option);
```

### Cytoscape.js 网络图

```javascript
// 获取数据
const response = await fetch('/api/v1/projects/1/report-network/visualization?format_type=cytoscape');
const { data } = await response.json();

// 创建网络
const cy = cytoscape({
  container: document.getElementById('network'),
  elements: data.elements,
  style: [
    {
      selector: 'node',
      style: {
        'background-color': '#666',
        'label': 'data(label)',
        'width': 'data(pagerank)',
        'height': 'data(pagerank)'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 'data(strength)',
        'line-color': '#ccc',
        'curve-style': 'bezier'
      }
    }
  ],
  layout: {
    name: 'cose',
    animate: true
  }
});

// 添加交互
cy.on('tap', 'node', function(evt){
  const node = evt.target;
  console.log('点击节点:', node.data());
});
```

### Vis.js 网络

```javascript
// 获取数据
const response = await fetch('/api/v1/projects/1/keyword-network/visualization?format_type=vis&top_n=50');
const { data } = await response.json();

// 创建网络
const container = document.getElementById('network');
const network = new vis.Network(container, data, {
  nodes: {
    shape: 'dot',
    scaling: {
      min: 10,
      max: 30
    },
    font: {
      size: 12,
      face: 'Tahoma'
    }
  },
  edges: {
    width: 0.15,
    color: {inherit: 'from'},
    smooth: {
      type: 'continuous'
    }
  },
  physics: {
    stabilization: false,
    barnesHut: {
      gravitationalConstant: -80000,
      springConstant: 0.001,
      springLength: 200
    }
  },
  interaction: {
    tooltipDelay: 200,
    hideEdgesOnDrag: true
  }
});

// 事件监听
network.on('click', function(params) {
  if (params.nodes.length > 0) {
    const nodeId = params.nodes[0];
    console.log('点击节点:', nodeId);
  }
});
```

---

## 🚀 使用场景

### 场景 1: 报告关系探索

**用户流程**:
1. 打开项目的报告网络视图
2. 查看完整网络拓扑
3. 点击某个报告节点
4. 加载该报告的局部网络（子图）
5. 深入探索关联报告

**API 调用顺序**:
```javascript
// 1. 加载完整网络
const fullNetwork = await fetch('/api/v1/projects/1/report-network/visualization?format_type=echarts');

// 2. 用户点击节点后，加载子图
const subgraph = await fetch('/api/v1/projects/1/report-network/subgraph?report_id=abc-123&depth=2');
```

### 场景 2: 关键词语义探索

**用户流程**:
1. 查看关键词网络（只显示前100个）
2. 识别关键词聚类（社区）
3. 点击某个关键词
4. 查看其关联关键词
5. 发现语义关系

**API 调用**:
```javascript
// 1. 加载关键词网络
const network = await fetch('/api/v1/projects/1/keyword-network/visualization?format_type=echarts&top_n=100');

// 2. 加载社区可视化
const communities = await fetch('/api/v1/projects/1/keyword-communities/visualization');

// 3. 点击节点后，加载子图
const subgraph = await fetch('/api/v1/projects/1/keyword-network/subgraph?keyword_id=123&depth=2');
```

### 场景 3: 网络统计分析

**用户流程**:
1. 查看报告网络统计图表
2. 了解网络拓扑特征
3. 识别关键报告（高 PageRank）
4. 查看网络连通性

**API 调用**:
```javascript
// 获取统计图表
const stats = await fetch('/api/v1/projects/1/network-statistics/charts?network_type=report');

// 使用 ECharts 绘制
stats.data.charts.forEach(chart => {
  if (chart.type === 'bar') {
    // 绘制柱状图
  } else if (chart.type === 'pie') {
    // 绘制饼图
  }
});
```

### 场景 4: 多视图对比

**用户流程**:
1. 同时查看报告网络和关键词网络
2. 对比网络结构
3. 发现内容主题和报告关系的对应

**布局**:
```
┌────────────────────────────────────────┐
│  报告关系网络    │  关键词网络          │
│  (左侧)          │  (右侧)              │
│                  │                      │
│  [网络图]        │  [网络图]            │
│                  │                      │
├────────────────────────────────────────┤
│  统计图表                               │
│  [度分布] [PageRank分布] [分类分布]    │
└────────────────────────────────────────┘
```

---

## 📈 性能优化

### 大规模网络优化

**问题**: 关键词网络可能有数千个节点

**解决方案**:
1. **Top N 过滤**: 只显示高频关键词
   ```javascript
   // 只显示前100个
   ?top_n=100
   ```

2. **分类过滤**: 按分类查看
   ```javascript
   // 只显示"人物"类
   ?category_filter=人物
   ```

3. **强度阈值**: 过滤弱关系
   ```javascript
   // 只显示强关系
   ?min_strength=0.3
   ```

4. **子图模式**: 聚焦局部网络
   ```javascript
   // 只看某个关键词的邻居
   /keyword-network/subgraph?keyword_id=123
   ```

### 前端渲染优化

**Canvas vs SVG**:
- 节点数 < 100: 使用 SVG（交互性好）
- 节点数 > 100: 使用 Canvas（性能好）

**示例**:
```javascript
// D3.js 切换到 Canvas
const canvas = d3.select("#network").append("canvas");
const context = canvas.node().getContext("2d");

// ECharts 自动优化
const chart = echarts.init(dom, null, {
  renderer: nodes.length > 100 ? 'canvas' : 'svg'
});
```

### 数据缓存

**后端缓存**:
```python
# Redis 缓存可视化数据
cache_key = f"viz:report_network:{project_id}:{format_type}"
ttl = 1800  # 30分钟
```

**前端缓存**:
```javascript
// 使用 React Query 缓存
const { data } = useQuery(
  ['network', projectId, formatType],
  () => fetchNetwork(projectId, formatType),
  { staleTime: 1000 * 60 * 30 }  // 30分钟
);
```

---

## 🎨 可视化最佳实践

### 颜色方案

**报告网络**:
- 按报告类型着色
- 田野调查 → 蓝色
- 访谈记录 → 绿色
- 分析报告 → 橙色

**关键词网络**:
- 按分类着色
- 人物 → 红色
- 地点 → 绿色
- 事件 → 蓝色
- 组织 → 紫色

### 节点大小

**基于重要性**:
- 报告: PageRank * 100
- 关键词: 频率 * 2 (限制最大 80)

### 边的样式

**基于强度**:
- 粗细: strength * 3-5
- 透明度: strength (0.1-1.0)
- 弱关系可设为虚线

### 标签显示

**分级显示**:
- 重要节点: 始终显示
- 普通节点: 悬浮显示
- 次要节点: 点击显示

**示例**:
```javascript
// D3.js
label.style("display", d => d.pagerank > 0.01 ? "block" : "none");

// ECharts
label: {
  show: node.pagerank > 0.01
}
```

### 布局算法

**推荐配置**:
```javascript
// D3.js Force
d3.forceSimulation()
  .force("charge", d3.forceManyBody().strength(-100))
  .force("link", d3.forceLink().distance(50))
  .force("center", d3.forceCenter());

// Cytoscape.js
layout: {
  name: 'cose',  // 复杂网络
  // name: 'circle',  // 简单展示
  animate: true,
  animationDuration: 500
}
```

---

## 🧪 测试示例

```bash
# 1. 测试报告网络可视化
curl "http://localhost:8000/api/v1/projects/1/report-network/visualization?format_type=d3"

# 2. 测试关键词网络（前50个）
curl "http://localhost:8000/api/v1/projects/1/keyword-network/visualization?format_type=echarts&top_n=50"

# 3. 测试社区可视化
curl "http://localhost:8000/api/v1/projects/1/keyword-communities/visualization?format_type=echarts"

# 4. 测试报告子图
curl "http://localhost:8000/api/v1/projects/1/report-network/subgraph?report_id=abc-123&depth=2&format_type=vis"

# 5. 测试关键词子图
curl "http://localhost:8000/api/v1/projects/1/keyword-network/subgraph?keyword_id=123&depth=2&format_type=cytoscape"

# 6. 测试统计图表
curl "http://localhost:8000/api/v1/projects/1/network-statistics/charts?network_type=keyword"

# 7. 测试支持的格式
curl "http://localhost:8000/api/v1/visualization/formats"
```

---

## ⚠️ 注意事项

### 数据依赖

- 报告网络需先构建（调用报告关系网络 API）
- 关键词网络需先构建（调用关键词网络 API）
- 社区检测需安装 `python-louvain`

### 格式选择

**推荐场景**:
- 快速开发 → ECharts
- 高度定制 → D3.js
- 网络分析 → Cytoscape.js
- 简单易用 → Vis.js

### 性能考虑

- 节点数 > 500: 使用 Canvas 渲染
- 节点数 > 1000: 启用虚拟化或分页
- 使用 top_n 参数控制规模

---

## 📝 后续扩展

### 计划功能

1. **3D 网络可视化**
   - 使用 Three.js / 3D Force Graph
   - 适合超大规模网络

2. **时间序列网络**
   - 动态展示网络演化
   - 时间轴控制

3. **网络对比**
   - 多项目网络对比
   - 差异高亮显示

4. **交互式布局**
   - 手动调整节点位置
   - 保存自定义布局

5. **导出功能**
   - 导出 SVG/PNG
   - 导出网络数据（GraphML, GEXF）

---

## 🎉 总结

网络可视化系统已完整实现并部署，具备：

✅ **8 个 API 端点**
✅ **4 种可视化格式** (D3.js, ECharts, Cytoscape.js, Vis.js)
✅ **报告网络可视化**
✅ **关键词网络可视化**
✅ **社区可视化**
✅ **子图提取**
✅ **统计图表**
✅ **多种过滤选项**

系统为前端提供开箱即用的可视化数据，支持主流可视化库，可立即投入使用。
