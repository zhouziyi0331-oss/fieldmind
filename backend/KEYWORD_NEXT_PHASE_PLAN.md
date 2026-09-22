# 关键词功能 - 下一阶段计划

## 📊 当前状态分析

### ✅ 已完成功能
1. **核心提取能力**
   - TF-IDF 提取 ✅
   - LLM 精炼（可选）✅
   - 混合方法 ✅
   - 集成到文档处理流水线（阶段7）✅

2. **数据存储**
   - `keywords` 表：641 个唯一关键词
   - `document_keywords` 表：918 条关联记录
   - 覆盖 28 个文档
   - 63% 关键词已分类（406/641）

3. **基础 API**
   - `/keywords/extract` - 单文档提取
   - `/keywords/batch-extract` - 批量提取
   - 基础搜索功能

### ❌ 缺失/不完善的功能

#### 1. 关键词关系网络 (0%)
- **现状**: `keyword_relations` 表为空（0条记录）
- **缺失**: 共现分析、关系强度计算、关系可视化

#### 2. 知识脉络生成 (0%)
- **现状**: `knowledge_node_id` 字段全为空
- **缺失**: 关键词聚类、主题演化、知识图谱连接

#### 3. 关键词搜索和过滤 (30%)
- **现状**: 基础 API 存在，但功能有限
- **缺失**: 
  - 多维度过滤（分类、时间、项目）
  - 关键词推荐
  - 相关关键词查找
  - 跨文档搜索

#### 4. 可视化和分析 (0%)
- **缺失**:
  - 关键词云
  - 时间演化图
  - 共现网络图
  - 分布统计图表

#### 5. 前端集成 (0%)
- **缺失**:
  - 关键词面板
  - 关键词标签系统
  - 关键词过滤器
  - 可视化组件

---

## 🎯 下一阶段目标：关键词关系网络

### 为什么先做关系网络？
1. **最大价值**: 关系网络是关键词功能从"标签"到"知识"的跃升
2. **技术基础完备**: 数据已经存在，只需计算关系
3. **支撑其他功能**: 知识脉络、推荐、搜索都依赖关系网络
4. **可见性强**: 网络可视化能直接展示价值

---

## 📋 实施计划

### 阶段 1: 关键词共现分析 (30分钟)

**目标**: 构建关键词共现网络

#### 任务 1.1: 共现计算服务
创建 `keyword_relation_builder.py`

```python
class KeywordRelationBuilder:
    def build_cooccurrence_relations(
        self, 
        project_id: int,
        window_size: int = 100,  # 字符窗口
        min_cooccurrence: int = 2
    ) -> List[KeywordRelation]:
        """
        计算关键词共现关系
        
        策略：
        1. 文档级共现：同一文档中出现
        2. 段落级共现：同一段落中出现（更强的关系）
        3. 窗口级共现：在 N 个字符内出现（最强的关系）
        """
        
    def calculate_relation_strength(
        self,
        keyword1_id: int,
        keyword2_id: int
    ) -> float:
        """
        计算关系强度
        
        因素：
        - 共现次数
        - 共现的接近度（窗口越小，权重越高）
        - 关键词本身的权重
        """
```

**输入**: 
- `keywords` 表：641 个关键词
- `document_keywords` 表：918 条关联 + positions 字段

**输出**:
- `keyword_relations` 表：预计 1000-3000 条关系
- 关系类型：`co_occurrence`
- 关系强度：0.0-1.0

#### 任务 1.2: 批量构建脚本
创建 `batch_build_keyword_relations.py`

```bash
# 为项目 1 构建关系网络
python batch_build_keyword_relations.py --project-id 1

# 测试模式（只处理 Top 50 关键词）
python batch_build_keyword_relations.py --project-id 1 --test --limit 50
```

**验收标准**:
- [ ] `keyword_relations` 表从 0 增长到 1000+
- [ ] 每个关系有 `co_occurrence`、`strength` 值
- [ ] Top 关键词的关系数 > 5

---

### 阶段 2: 关键词关系 API (20分钟)

**目标**: 提供关系查询接口

#### 任务 2.1: 关系查询服务
扩展 `keyword_service.py`

```python
class KeywordService:
    def get_related_keywords(
        self,
        keyword_id: int,
        relation_type: str = "co_occurrence",
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """获取相关关键词"""
        
    def get_keyword_network(
        self,
        keyword_ids: List[int],
        depth: int = 1  # 关系深度
    ) -> Dict[str, Any]:
        """
        获取关键词网络
        
        返回格式：
        {
            "nodes": [{"id": 1, "text": "村委会", "weight": 0.8}],
            "edges": [{"source": 1, "target": 2, "strength": 0.6}]
        }
        """
```

#### 任务 2.2: API 端点
添加到 `keywords.py`

```python
@router.get("/relations/{keyword_id}")
async def get_keyword_relations(keyword_id: int, top_n: int = 10):
    """获取关键词的相关词"""

@router.post("/network")
async def get_keyword_network(keyword_ids: List[int]):
    """获取关键词网络（用于可视化）"""
```

**验收标准**:
- [ ] API 返回相关关键词列表
- [ ] 网络数据格式符合前端可视化要求
- [ ] 响应时间 < 500ms

---

### 阶段 3: 关键词推荐和搜索增强 (20分钟)

**目标**: 基于关系网络提供智能推荐

#### 任务 3.1: 推荐服务
创建 `keyword_recommendation_service.py`

```python
class KeywordRecommendationService:
    def recommend_keywords(
        self,
        document_id: int,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        为文档推荐相关关键词
        
        策略：
        1. 获取文档现有关键词
        2. 找到这些关键词的相关词
        3. 过滤已存在的
        4. 按关系强度排序
        """
        
    def suggest_categories(
        self,
        keyword_id: int
    ) -> List[str]:
        """
        基于相关词的分类，建议当前关键词的分类
        """
```

#### 任务 3.2: 搜索增强
扩展 `keyword_search_service.py`

```python
def search_with_expansion(
    keywords: List[str],
    expand: bool = True,
    expansion_depth: int = 1
) -> SearchResults:
    """
    搜索时自动扩展相关关键词
    
    示例：
    输入: ["村委会"]
    扩展: ["村委会", "村民大会", "村规民约"]  # 基于共现关系
    """
```

**验收标准**:
- [ ] 推荐关键词与文档主题相关
- [ ] 分类建议基于多数投票逻辑
- [ ] 搜索召回率提升 20%+

---

### 阶段 4: 知识脉络初步集成 (30分钟)

**目标**: 连接关键词网络与知识图谱

#### 任务 4.1: 关键词聚类
创建 `keyword_clustering_service.py`

```python
class KeywordClusteringService:
    def cluster_keywords(
        self,
        project_id: int,
        method: str = "community_detection"  # 或 "kmeans"
    ) -> List[Cluster]:
        """
        基于共现关系对关键词聚类
        
        输出：
        - 社区1: 村委会、村民大会、村规民约 (主题: 基层治理)
        - 社区2: 传统技艺、非遗、手工艺 (主题: 文化传承)
        """
```

#### 任务 4.2: 知识节点映射
扩展 `keywords` 表的 `knowledge_node_id` 字段

```python
def map_keywords_to_knowledge_nodes(
    project_id: int
):
    """
    将关键词关联到知识图谱节点
    
    策略：
    1. 关键词文本与实体名称匹配
    2. 关键词簇 → 知识脉络主题
    """
```

**验收标准**:
- [ ] 识别出 5-10 个关键词簇
- [ ] 30%+ 关键词映射到知识节点
- [ ] 簇的主题标签有意义

---

## 🕐 总体时间线

| 阶段 | 任务 | 预计时间 |
|-----|------|---------|
| 1.1 | 共现计算服务 | 20分钟 |
| 1.2 | 批量构建脚本 | 10分钟 |
| 2.1 | 关系查询服务 | 10分钟 |
| 2.2 | API 端点 | 10分钟 |
| 3.1 | 推荐服务 | 15分钟 |
| 3.2 | 搜索增强 | 5分钟 |
| 4.1 | 关键词聚类 | 20分钟 |
| 4.2 | 知识节点映射 | 10分钟 |

**总计**: 100 分钟 (1小时40分钟)

---

## 📊 预期成果

### 数据层
- `keyword_relations` 表：0 → 1000+ 条关系
- `keywords.knowledge_node_id`：0% → 30% 映射率
- 5-10 个关键词主题簇

### 服务层
- `KeywordRelationBuilder` ✅
- `KeywordRecommendationService` ✅
- `KeywordClusteringService` ✅
- 3 个新 API 端点 ✅

### 功能层
- 相关关键词查询 ✅
- 关键词推荐 ✅
- 搜索扩展 ✅
- 关键词聚类 ✅

---

## 🚀 后续阶段（不在本次计划）

### 阶段 5: 可视化
- 关键词云组件
- 共现网络图（D3.js / ECharts）
- 时间演化图

### 阶段 6: 前端集成
- 关键词面板
- 标签系统
- 过滤器组件

### 阶段 7: 高级分析
- 关键词趋势分析
- 主题演化追踪
- 跨项目关键词对比

---

## 🎯 关键问题和决策点

### Q1: 共现窗口大小？
**建议**: 
- 文档级：整个文档（权重 0.3）
- 段落级：500 字符（权重 0.6）
- 句子级：100 字符（权重 1.0）

### Q2: 关系强度计算公式？
**建议**:
```python
strength = (co_occurrence_count / min_keyword_frequency) * proximity_weight
proximity_weight = 1.0 (句子级) | 0.6 (段落级) | 0.3 (文档级)
```

### Q3: 聚类算法？
**建议**: 
- 小规模（< 1000 关键词）：Louvain 社区发现
- 大规模：MiniBatch KMeans

### Q4: 是否需要 LLM 增强关系？
**建议**: 
- 第一阶段：仅统计共现（快速、稳定）
- 后续可选：LLM 识别因果、层级等语义关系

---

## ✅ 立即开始

```bash
# 1. 验证当前数据
sqlite3 backend/src/data/fieldmind.db "
SELECT 
    COUNT(DISTINCT dk1.keyword_id) as total_keywords,
    COUNT(*) as total_associations
FROM document_keywords dk1
"

# 2. 创建关系构建服务
# 实现 keyword_relation_builder.py

# 3. 运行批量构建
python batch_build_keyword_relations.py --project-id 1 --test
```

---

## 📝 备注

**与报告映射的关系**:
- 关键词关系网络 → 报告可以展示"关键主题网络"
- 关键词聚类 → 报告可以自动生成"主题分组"
- 两者**并行开发**，互不阻塞

**技术依赖**:
- 需要：`networkx`（图分析）、`scikit-learn`（聚类，已有）
- 可选：`python-louvain`（社区发现）
