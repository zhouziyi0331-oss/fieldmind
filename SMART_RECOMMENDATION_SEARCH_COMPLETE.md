# 智能推荐搜索系统 - 完整实现文档

## 📋 概述

智能推荐搜索系统整合多种推荐策略和搜索方法，为用户提供智能化的内容发现和推荐服务。支持报告推荐、关键词推荐、文档推荐和实时搜索建议。

**实现日期**: 2024
**状态**: ✅ 已完成并部署

---

## 🏗️ 系统架构

### 核心组件

1. **SmartRecommendationService** (新增)
   - 文件: `backend/src/app/services/smart_recommendation_service.py`
   - 功能: 报告推荐、关键词推荐、文档推荐、搜索建议

2. **UnifiedSearchService** (已有)
   - 文件: `backend/src/app/services/unified_search.py`
   - 功能: 统一搜索接口（关键词、语义、混合、实体）

3. **CorrelationRecommender** (已有)
   - 文件: `backend/src/app/services/correlation_recommender.py`
   - 功能: 基于对象关联的推荐

4. **Recommendations API** (新增)
   - 文件: `backend/src/app/api/v1/recommendations.py`
   - 功能: 8 个 API 端点

### 数据基础

使用现有的数据表：
- **reports** - 报告表
- **report_relations** - 报告关系网络
- **report_entities** - 报告实体
- **keywords** - 关键词表
- **keyword_relations** - 关键词关系网络
- **documents** - 文档表
- **document_keywords** - 文档-关键词关联

---

## 🎯 核心功能

### 1. 报告推荐

#### 推荐策略

**1.1 基于关系网络 (relation_based)**
- 利用报告关系网络 (`report_relations` 表)
- 推荐直接关联的报告
- 考虑关系类型和强度

**1.2 基于共享实体 (entity_based)**
- 计算报告间的实体重叠度
- 使用 Jaccard 相似度
- 公式: `similarity = |intersection| / |union|`

**1.3 基于关键词 (keyword_based)**
- 通过文档关联获取报告的关键词
- 计算关键词相似度
- Jaccard 相似度

**1.4 混合策略 (hybrid, 推荐)**
- 综合上述三种策略
- 加权: 关系 0.4 + 实体 0.35 + 关键词 0.25
- 多策略融合，提高推荐准确性

#### 推荐流程
```
1. 获取当前报告信息
   ↓
2. 根据策略计算候选报告
   - 关系网络查询
   - 实体相似度计算
   - 关键词匹配
   ↓
3. 多策略加权融合（hybrid）
   ↓
4. 过滤已排除的报告
   ↓
5. 按分数排序，返回 Top N
```

### 2. 关键词推荐

#### 推荐策略

**2.1 基于网络 (network)**
- 利用关键词共现网络 (`keyword_relations`)
- 推荐直接关联的关键词
- 按关系强度排序

**2.2 基于上下文 (context)**
- 推荐同一分类的高频关键词
- 适合探索性浏览

#### 推荐场景
- 关键词扩展
- 同义词发现
- 相关概念探索

### 3. 文档推荐

#### 推荐策略

**3.1 基于关键词 (keyword)**
- 计算文档间的关键词相似度
- Jaccard 相似度计算
- 适合内容相关推荐

**3.2 基于时间 (temporal)**
- 推荐时间相近的文档（±7天）
- 时间差越小，分数越高
- 适合时序分析场景

### 4. 搜索建议（自动补全）

#### 建议类型

**4.1 关键词建议**
- 模糊匹配关键词文本
- 按频率排序
- 返回 ID、文本、分类、频率

**4.2 实体建议**
- 模糊匹配实体名称
- 按频率排序
- 返回 ID、名称、类型、频率

**4.3 文档建议**
- 模糊匹配文档标题和文件名
- 返回文档基本信息

#### 应用场景
- 搜索框自动补全
- 智能提示
- 快速定位

### 5. 统一搜索

整合多种搜索方式：
- **关键词搜索**: 全文匹配
- **语义检索**: 向量相似度
- **混合检索**: 综合关键词和语义
- **实体查询**: 知识图谱查询

---

## 🔌 API 端点

### 1. 获取报告推荐
```http
GET /api/v1/reports/{report_id}/recommendations
```

**查询参数**:
- `project_id` (必需): 项目ID
- `strategy`: 推荐策略 (默认 "hybrid")
- `top_n`: 推荐数量 (默认 5, 最大 20)
- `exclude_ids`: 排除的报告ID，逗号分隔

**响应**:
```json
{
  "success": true,
  "data": {
    "report_id": "abc-123",
    "recommendations": [
      {
        "report_id": "def-456",
        "title": "相关报告标题",
        "score": 0.85,
        "reason": "混合推荐 (relation_based, entity_based)",
        "strategy": "hybrid",
        "strategies": ["relation_based", "entity_based"]
      }
    ],
    "strategy": "hybrid",
    "count": 5
  }
}
```

### 2. 获取关键词推荐
```http
GET /api/v1/keywords/{keyword_id}/recommendations
```

**查询参数**:
- `project_id` (必需): 项目ID
- `strategy`: 推荐策略 (默认 "network")
- `top_n`: 推荐数量 (默认 10, 最大 50)

**响应**:
```json
{
  "success": true,
  "data": {
    "keyword_id": 123,
    "recommendations": [
      {
        "keyword_id": 456,
        "text": "村民",
        "category": "人物",
        "score": 0.78,
        "reason": "共现 12 次",
        "co_occurrence": 12,
        "relation_strength": 0.78
      }
    ],
    "strategy": "network",
    "count": 10
  }
}
```

### 3. 获取文档推荐
```http
GET /api/v1/documents/{document_id}/recommendations
```

**查询参数**:
- `project_id` (必需): 项目ID
- `strategy`: 推荐策略 (默认 "keyword")
- `top_n`: 推荐数量 (默认 5, 最大 20)

**响应**:
```json
{
  "success": true,
  "data": {
    "document_id": 789,
    "recommendations": [
      {
        "document_id": 790,
        "title": "相关文档.pdf",
        "score": 0.65,
        "reason": "共享 8 个关键词",
        "shared_keywords": 8
      }
    ],
    "strategy": "keyword",
    "count": 5
  }
}
```

### 4. 搜索建议（自动补全）
```http
GET /api/v1/projects/{project_id}/search-suggestions
```

**查询参数**:
- `query` (必需): 搜索查询
- `suggestion_type`: 建议类型 (默认 "all")
  - `keywords`: 仅关键词
  - `entities`: 仅实体
  - `documents`: 仅文档
  - `all`: 全部类型
- `limit`: 每种类型的建议数量 (默认 5, 最大 20)

**响应**:
```json
{
  "success": true,
  "data": {
    "query": "村",
    "suggestions": {
      "keywords": [
        {
          "id": 123,
          "text": "村委会",
          "category": "组织",
          "frequency": 45,
          "type": "keyword"
        }
      ],
      "entities": [
        {
          "id": 456,
          "name": "村民",
          "type": "PERSON",
          "frequency": 32
        }
      ],
      "documents": [
        {
          "id": 789,
          "title": "村落调查报告",
          "file_name": "village_survey.pdf",
          "type": "document"
        }
      ]
    }
  }
}
```

### 5. 统一搜索
```http
POST /api/v1/projects/{project_id}/unified-search
```

**请求体**:
```json
{
  "query": "村委会治理",
  "search_type": "hybrid",
  "top_k": 10
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "query": "村委会治理",
    "results": [
      {
        "chunk_id": "...",
        "document_id": 123,
        "text": "...",
        "score": 0.89
      }
    ],
    "count": 10,
    "search_type": "hybrid"
  }
}
```

### 6. 推荐系统统计
```http
GET /api/v1/projects/{project_id}/recommendation-stats
```

**响应**:
```json
{
  "success": true,
  "data": {
    "reports": {
      "total": 150,
      "relations": 234,
      "avg_relations_per_report": 1.56
    },
    "keywords": {
      "total": 456,
      "relations": 1234,
      "avg_relations_per_keyword": 2.70
    },
    "documents": {
      "total": 200
    },
    "recommendation_coverage": {
      "reports_with_relations": true,
      "keywords_with_relations": true,
      "overall_ready": true
    }
  }
}
```

### 7. 批量获取报告推荐
```http
POST /api/v1/projects/{project_id}/batch-recommendations
```

**查询参数**:
- `report_ids` (必需): 报告ID列表（查询参数数组）
- `strategy`: 推荐策略 (默认 "hybrid")
- `top_n`: 每个报告推荐数量 (默认 3, 最大 10)

**响应**:
```json
{
  "success": true,
  "data": {
    "batch_results": {
      "report-1": [...],
      "report-2": [...],
      "report-3": [...]
    },
    "strategy": "hybrid",
    "processed_count": 3
  }
}
```

---

## 📊 推荐算法详解

### Jaccard 相似度

用于计算两个集合的相似度：

```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|

示例：
报告A实体: {村委会, 村民, 老王}
报告B实体: {村委会, 老王, 李书记}

交集: {村委会, 老王} = 2
并集: {村委会, 村民, 老王, 李书记} = 4
Jaccard相似度 = 2 / 4 = 0.5
```

### 混合推荐加权

```python
final_score = 0.4 * relation_score 
            + 0.35 * entity_score 
            + 0.25 * keyword_score

# 权重说明：
# - 关系网络 (0.4): 最高权重，已经过人工确认或系统推断
# - 实体相似度 (0.35): 次高权重，内容相关性强
# - 关键词相似度 (0.25): 基础权重，补充推荐
```

### 时间衰减

文档时间推荐的分数计算：

```python
time_diff = |doc1.created_at - doc2.created_at|
time_window = 7 days

score = max(0, 1 - (time_diff / time_window))

# 例如：
# 时间差 0 天 → score = 1.0
# 时间差 3.5 天 → score = 0.5
# 时间差 7 天 → score = 0.0
```

---

## 🎨 前端集成建议

### 推荐组件位置

**1. 报告详情页**
```
┌─────────────────────────────────┐
│  报告标题                        │
│  报告内容...                     │
│                                  │
│  相关报告推荐 (5个)              │
│  ┌────┬────┬────┬────┬────┐    │
│  │报告│报告│报告│报告│报告│    │
│  └────┴────┴────┴────┴────┘    │
└─────────────────────────────────┘
```

**2. 关键词详情页**
```
┌─────────────────────────────────┐
│  关键词: 村委会                  │
│  出现频率: 45次                  │
│                                  │
│  相关关键词                      │
│  [村民] [基层组织] [村长]...    │
└─────────────────────────────────┘
```

**3. 搜索框自动补全**
```
搜索: 村___
       ↓
┌─────────────────┐
│ 关键词          │
│  • 村委会 (45)  │
│  • 村民 (32)    │
│ 文档            │
│  • 村落调查.pdf │
└─────────────────┘
```

**4. 文档列表侧边栏**
```
┌──────────┬─────────────────┐
│ 文档列表 │ 推荐文档        │
│          │                 │
│ • 文档A  │ 基于当前选择    │
│ • 文档B  │ • 相关文档1     │
│ • 文档C  │ • 相关文档2     │
└──────────┴─────────────────┘
```

### 交互流程

**推荐刷新流程**:
```
用户查看报告A
  ↓
自动调用推荐API
  ↓
显示相关报告
  ↓
用户点击报告B
  ↓
刷新推荐（排除A）
```

**搜索建议流程**:
```
用户输入 "村"
  ↓
延迟 300ms (debounce)
  ↓
调用搜索建议API
  ↓
显示下拉列表
  ↓
用户选择建议项
  ↓
跳转到详情页
```

### 推荐理由展示

```jsx
// 推荐卡片示例
<RecommendationCard>
  <Title>{report.title}</Title>
  <Score>匹配度: {(score * 100).toFixed(0)}%</Score>
  <Reason>
    <Icon>🔗</Icon>
    <Text>{reason}</Text>
  </Reason>
  {strategies && (
    <Badges>
      {strategies.map(s => <Badge>{s}</Badge>)}
    </Badges>
  )}
</RecommendationCard>
```

---

## 🚀 使用场景

### 场景 1: 报告浏览

**用户流程**:
1. 打开报告详情页
2. 系统自动加载推荐报告
3. 点击推荐报告继续浏览
4. 形成浏览链路

**API 调用**:
```javascript
// 获取报告推荐
const recommendations = await fetch(
  `/api/v1/reports/${reportId}/recommendations?project_id=1&strategy=hybrid&top_n=5`
)
```

### 场景 2: 关键词探索

**用户流程**:
1. 从报告中点击关键词
2. 查看关键词详情
3. 显示相关关键词网络
4. 点击相关关键词继续探索

**API 调用**:
```javascript
// 获取关键词推荐
const recommendations = await fetch(
  `/api/v1/keywords/${keywordId}/recommendations?project_id=1&strategy=network&top_n=10`
)
```

### 场景 3: 智能搜索

**用户流程**:
1. 在搜索框输入查询
2. 实时显示搜索建议
3. 选择建议项或按回车搜索
4. 查看搜索结果

**API 调用**:
```javascript
// 搜索建议（输入时）
const suggestions = await fetch(
  `/api/v1/projects/${projectId}/search-suggestions?query=${query}&suggestion_type=all&limit=5`
)

// 统一搜索（提交时）
const results = await fetch(`/api/v1/projects/${projectId}/unified-search`, {
  method: 'POST',
  body: JSON.stringify({
    query: query,
    search_type: 'hybrid',
    top_k: 20
  })
})
```

### 场景 4: 批量推荐（列表页）

**用户流程**:
1. 查看报告列表
2. 每个报告卡片显示 3 个推荐
3. 一次性批量加载

**API 调用**:
```javascript
// 批量获取推荐
const batchRecommendations = await fetch(
  `/api/v1/projects/${projectId}/batch-recommendations?report_ids=${reportIds.join(',')}&strategy=hybrid&top_n=3`,
  { method: 'POST' }
)
```

---

## 📈 性能优化

### 缓存策略

**推荐结果缓存**:
```python
# Redis缓存键设计
cache_key = f"recommend:report:{report_id}:{strategy}:{top_n}"
ttl = 3600  # 1小时

# 缓存失效条件
- 报告内容更新
- 关系网络重建
- 新报告关联
```

**搜索建议缓存**:
```python
# 热门查询缓存
cache_key = f"suggest:{project_id}:{query}"
ttl = 1800  # 30分钟
```

### 数据库优化

**推荐查询优化**:
```sql
-- 已有索引利用
- report_relations: (source_report_id, target_report_id)
- keyword_relations: (keyword1_id, keyword2_id, project_id)
- document_keywords: (document_id, keyword_id)

-- 查询限制
- 候选报告限制在 50 个以内
- Top N 推荐限制在 20 个以内
```

### 异步处理

**批量推荐**:
```python
# 并发处理多个报告
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(service.recommend_reports, rid, project_id)
        for rid in report_ids
    ]
    results = [f.result() for f in futures]
```

---

## 🧪 测试示例

### 测试推荐功能

```bash
# 1. 测试报告推荐
curl "http://localhost:8000/api/v1/reports/abc-123/recommendations?project_id=1&strategy=hybrid&top_n=5"

# 2. 测试关键词推荐
curl "http://localhost:8000/api/v1/keywords/123/recommendations?project_id=1&strategy=network&top_n=10"

# 3. 测试文档推荐
curl "http://localhost:8000/api/v1/documents/789/recommendations?project_id=1&strategy=keyword&top_n=5"

# 4. 测试搜索建议
curl "http://localhost:8000/api/v1/projects/1/search-suggestions?query=村&suggestion_type=all&limit=5"

# 5. 测试统一搜索
curl -X POST "http://localhost:8000/api/v1/projects/1/unified-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "村委会治理", "search_type": "hybrid", "top_k": 10}'

# 6. 测试推荐统计
curl "http://localhost:8000/api/v1/projects/1/recommendation-stats"

# 7. 测试批量推荐
curl -X POST "http://localhost:8000/api/v1/projects/1/batch-recommendations?report_ids=abc-123&report_ids=def-456&strategy=hybrid&top_n=3"
```

---

## ⚠️ 注意事项

### 数据依赖

推荐系统依赖以下数据：
- 报告关系网络必须已构建
- 关键词关系网络必须已构建
- 文档必须已提取关键词

### 冷启动问题

**新项目**:
- 报告数 < 5: 推荐结果少
- 关键词数 < 50: 推荐质量低
- 解决方案: 显示"相关内容较少"提示

**新报告**:
- 无关联关系: 基于实体和关键词推荐
- 无实体提取: 仅基于关键词推荐

### 推荐质量

影响因素：
- **关系网络质量**: 影响 relation_based 推荐
- **实体提取准确性**: 影响 entity_based 推荐
- **关键词提取质量**: 影响 keyword_based 推荐

建议：
- 定期重建关系网络
- 使用 LLM 提取实体
- 人工校验关键关系

---

## 📝 后续扩展

### 计划功能

1. **协同过滤推荐**
   - 基于用户行为
   - "查看了A的用户也查看了B"

2. **个性化推荐**
   - 用户兴趣建模
   - 推荐历史记录
   - 点击率反馈

3. **语义推荐**
   - 基于词向量的语义相似度
   - BERT 句子相似度
   - 跨语言推荐

4. **实时推荐**
   - WebSocket 推送
   - 内容更新即时推荐

5. **A/B 测试**
   - 多策略对比
   - 推荐效果评估

### 集成方向

- 与可视化系统联动
- 与知识图谱整合
- 与用户行为分析联动

---

## 🎉 总结

智能推荐搜索系统已完整实现并部署，具备：

✅ **8 个 API 端点**
✅ **报告推荐** (4种策略)
✅ **关键词推荐** (2种策略)
✅ **文档推荐** (2种策略)
✅ **搜索建议** (自动补全)
✅ **统一搜索** (多种搜索方式)
✅ **批量推荐** (列表场景优化)
✅ **推荐统计** (系统监控)

系统可立即投入使用，为用户提供智能化的内容发现和推荐服务。
