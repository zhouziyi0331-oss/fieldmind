# 关键词网络系统 - 完整实现文档

## 📋 概述

关键词网络系统基于现有的 `KeywordRelationBuilder` 服务，增强了主关键词识别、社区检测和网络可视化功能。使用 NetworkX 图算法和 Louvain 社区检测算法。

**实现日期**: 2024
**状态**: ✅ 已完成并部署

---

## 🏗️ 系统架构

### 核心组件

1. **KeywordRelationBuilder** (已有)
   - 文件: `backend/src/app/services/keyword_relation_builder.py`
   - 功能: 构建关键词共现关系、计算关系强度

2. **KeywordNetworkBuilder** (新增)
   - 文件: `backend/src/app/services/keyword_network_builder.py`
   - 功能: 主关键词识别、社区检测、网络可视化

3. **Keyword Network API** (新增)
   - 文件: `backend/src/app/api/v1/keyword_network.py`
   - 功能: 7 个 API 端点

### 数据模型 (已有)

使用现有的关键词表：
- **keywords** - 关键词主表
- **keyword_relations** - 关键词共现关系
- **document_keywords** - 文档-关键词关联

---

## 🎯 核心功能

### 1. 关键词共现关系构建

**服务方法**: `KeywordRelationBuilder.build_cooccurrence_relations()`

**策略**:
- 文档级共现 (权重 0.3)
- 段落级共现 (权重 0.6, 窗口 500 字符)
- 句子级共现 (权重 1.0, 窗口 100 字符)

**关系强度计算**:
```
strength = (co_occurrence / geometric_mean_frequency) * avg_proximity_weight
归一化: normalized_strength = tanh(strength / 2)
```

### 2. 主关键词识别

**服务方法**: `KeywordNetworkBuilder.identify_main_keywords()`

**算法**: 综合评分法
```python
score = 0.5 * pagerank + 0.3 * degree_centrality + 0.2 * normalized_frequency
```

**支持的排序方法**:
- `comprehensive`: 综合评分 (默认)
- `pagerank`: PageRank 算法 (推荐)
- `frequency`: 出现频率
- `degree`: 度中心性

**中心性指标**:
- **Degree Centrality**: 连接数 (局部重要性)
- **Betweenness Centrality**: 桥接能力 (信息流控制)
- **Closeness Centrality**: 接近中心 (信息传播效率)
- **PageRank**: 网络影响力 (Google 算法)

### 3. 社区检测

**服务方法**: `KeywordNetworkBuilder.detect_communities()`

**算法**: Louvain 算法
- 依赖: `python-louvain` 库
- 优化目标: 最大化模块度 (Modularity)
- 自动确定社区数量

**社区数据结构**:
```json
{
  "id": 0,
  "keywords": [1, 2, 3, ...],
  "size": 10,
  "main_keyword": 1,
  "label": "村委会"
}
```

### 4. 关键词邻域网络

**服务方法**: `KeywordNetworkBuilder.get_keyword_neighborhood()`

**功能**: 递归扩展邻域
- `depth=1`: 直接邻居
- `depth=2`: 二度邻居
- `depth=3`: 三度邻居

**用途**: 局部网络探索、关键词关联分析

### 5. 网络可视化数据

**节点数据**:
```json
{
  "id": 123,
  "text": "村委会",
  "category": "组织",
  "frequency": 45,
  "degree_centrality": 0.234,
  "betweenness_centrality": 0.156,
  "closeness_centrality": 0.789,
  "pagerank": 0.045,
  "is_main_keyword": true,
  "community_id": 0
}
```

**边数据**:
```json
{
  "source": 123,
  "target": 456,
  "strength": 0.78,
  "co_occurrence": 12,
  "correlation": 0.85,
  "relation_type": "co_occurrence"
}
```

---

## 🔌 API 端点

### 1. 构建关键词关系
```http
POST /api/v1/projects/{project_id}/keyword-relations/build
```

**请求体**:
```json
{
  "min_cooccurrence": 2,
  "recalculate": false
}
```

**响应**:
```json
{
  "success": true,
  "message": "关键词关系构建完成",
  "data": {
    "documents_processed": 150,
    "keyword_pairs_found": 3456,
    "relations_created": 1234
  }
}
```

### 2. 构建关键词网络
```http
POST /api/v1/projects/{project_id}/keyword-network/build
```

**请求体**:
```json
{
  "min_strength": 0.1,
  "include_communities": true
}
```

**响应**: 完整网络数据 (nodes, edges, communities, statistics)

### 3. 获取关键词网络
```http
GET /api/v1/projects/{project_id}/keyword-network?min_strength=0.1&include_communities=true
```

**响应**: 同上

### 4. 获取主关键词
```http
GET /api/v1/projects/{project_id}/main-keywords?top_n=20&method=comprehensive
```

**响应**:
```json
{
  "success": true,
  "data": {
    "main_keywords": [
      {
        "id": 123,
        "text": "村委会",
        "pagerank": 0.045,
        "degree_centrality": 0.234,
        "comprehensive_score": 0.678
      }
    ],
    "method": "comprehensive",
    "total": 20
  }
}
```

### 5. 获取关键词邻域
```http
GET /api/v1/keywords/{keyword_id}/neighborhood?project_id=1&depth=2&min_strength=0.1
```

**响应**:
```json
{
  "success": true,
  "data": {
    "center_keyword": "村委会",
    "nodes": [...],
    "edges": [...],
    "statistics": {
      "total_nodes": 25,
      "total_edges": 48,
      "depth": 2
    }
  }
}
```

### 6. 获取关系统计
```http
GET /api/v1/projects/{project_id}/keyword-relations/statistics
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total_relations": 1234,
    "average_strength": 0.456,
    "max_cooccurrence": 45,
    "top_connected_keywords": [
      {"keyword": "村委会", "connections": 89},
      {"keyword": "村民", "connections": 67}
    ]
  }
}
```

### 7. 完整网络分析 (一键执行)
```http
POST /api/v1/projects/{project_id}/keyword-network/full-analysis
```

**查询参数**:
- `min_cooccurrence`: 最小共现次数 (默认 2)
- `min_strength`: 最小关系强度 (默认 0.1)
- `recalculate_relations`: 是否重新计算关系 (默认 false)
- `include_communities`: 是否社区检测 (默认 true)

**响应**:
```json
{
  "success": true,
  "message": "关键词网络完整分析完成",
  "data": {
    "relation_stats": {...},
    "network": {...},
    "main_keywords": [...]
  }
}
```

---

## 📊 网络统计指标

构建网络后返回的统计信息：

```json
{
  "total_keywords": 456,
  "total_relations": 1234,
  "network_density": 0.012,
  "connected_components": 3,
  "average_degree": 5.4,
  "main_keywords_count": 20,
  "communities_count": 8
}
```

**指标说明**:
- **network_density**: 网络密度 (实际边数 / 可能边数)
- **connected_components**: 连通分量数 (独立子图数量)
- **average_degree**: 平均度数 (平均连接数)

---

## 🔧 技术栈

### Python 依赖
- **NetworkX**: 图算法库 (中心性计算)
- **python-louvain**: Louvain 社区检测
- **SQLAlchemy**: ORM
- **FastAPI**: API 框架

### 算法
- **PageRank**: 主关键词识别
- **Louvain**: 社区检测
- **TF-IDF 变体**: 关系强度计算

---

## 🚀 使用流程

### 典型工作流

```
1. 提取关键词 (已有功能)
   → 填充 keywords 和 document_keywords 表

2. 构建共现关系
   POST /api/v1/projects/1/keyword-relations/build
   → 生成 keyword_relations 表数据

3. 完整网络分析 (推荐)
   POST /api/v1/projects/1/keyword-network/full-analysis
   → 一键生成网络、识别主关键词、检测社区

4. 查询主关键词
   GET /api/v1/projects/1/main-keywords?method=pagerank&top_n=20

5. 探索关键词邻域
   GET /api/v1/keywords/123/neighborhood?depth=2
```

### 增量更新流程

```
1. 有新文档添加关键词后
   → 调用 build-relations (recalculate=false)

2. 需要刷新网络视图
   → 调用 keyword-network/build
```

---

## 🎨 前端可视化建议

### 推荐库
- **D3.js**: Force-directed graph
- **ECharts**: Graph visualization
- **Cytoscape.js**: 网络图专用库
- **Vis.js**: 交互式网络

### 可视化方案

1. **力导向图** (Force-Directed Graph)
   - 节点: 关键词 (大小 = pagerank)
   - 边: 共现关系 (粗细 = strength)
   - 颜色: 社区归属

2. **社区视图**
   - 按社区分组显示
   - 高亮主关键词

3. **邻域探索**
   - 点击节点展开邻居
   - 支持 1-3 度扩展

### 交互功能
- 节点拖拽
- 点击查看详情
- 过滤器 (强度、社区、分类)
- 搜索定位
- 导出图片/数据

---

## 📈 性能优化

### 数据库索引 (已有)
```sql
-- keywords 表
INDEX idx_keyword_project_text (project_id, text)
INDEX idx_keyword_category (category, project_id)

-- keyword_relations 表
INDEX idx_keyword_relation (keyword1_id, keyword2_id, project_id)
```

### 缓存策略
- 网络数据可缓存 (Redis)
- 主关键词列表可缓存
- 增量更新时清除缓存

### 性能建议
- 小项目 (< 500 关键词): 实时计算
- 中项目 (500-2000): 缓存网络数据
- 大项目 (> 2000): 后台任务 + 缓存

---

## 🧪 测试示例

### 测试数据要求
- 至少 50 个关键词
- 至少 20 个文档
- 关键词有位置信息 (positions 字段)

### 测试步骤

```bash
# 1. 构建关系
curl -X POST "http://localhost:8000/api/v1/projects/1/keyword-relations/build" \
  -H "Content-Type: application/json" \
  -d '{"min_cooccurrence": 2, "recalculate": true}'

# 2. 完整分析
curl -X POST "http://localhost:8000/api/v1/projects/1/keyword-network/full-analysis?min_cooccurrence=2&include_communities=true"

# 3. 获取主关键词
curl "http://localhost:8000/api/v1/projects/1/main-keywords?top_n=10&method=pagerank"

# 4. 获取统计信息
curl "http://localhost:8000/api/v1/projects/1/keyword-relations/statistics"
```

---

## ⚠️ 注意事项

### 依赖安装
需要安装 `python-louvain` 才能使用社区检测：
```bash
pip install python-louvain
```

如果未安装，社区检测会跳过，但其他功能正常。

### 数据质量
- 确保关键词提取质量高
- 建议先用 LLM 提取关键词
- 位置信息 (positions) 影响关系强度计算

### 性能考虑
- 大规模网络 (> 5000 关键词) 建议后台任务
- NetworkX 算法复杂度 O(n²) ~ O(n³)
- 可考虑采样或分批处理

---

## 📝 后续扩展

### 计划功能
1. **时间序列分析**: 关键词演化趋势
2. **跨项目网络**: 多项目关键词关联
3. **语义增强**: 结合词向量计算语义相似度
4. **主题模型**: LDA 主题识别
5. **推荐系统**: 基于网络的关键词推荐

### 集成方向
- 与报告关系网络联动
- 与知识图谱整合
- 与推荐搜索系统联动

---

## 🎉 总结

关键词网络系统已完整实现并部署，具备：

✅ **7 个 API 端点**
✅ **主关键词识别** (PageRank)
✅ **社区检测** (Louvain)
✅ **4 种中心性指标**
✅ **邻域网络探索**
✅ **完整的网络可视化数据**
✅ **一键完整分析**

系统可立即投入使用，为关键词管理和知识发现提供强大支持。
