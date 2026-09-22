# 统一知识图谱引擎

整合6个知识图谱版本的强大统一系统

## 架构设计

```
知识图谱工具层
├── unified_graph_engine.py    # 核心引擎
│   ├── MultiStrategyEntityExtractor      # 多策略实体提取
│   ├── EnhancedRelationExtractor         # 增强关系提取
│   ├── EntityAlignmentEngine             # 实体对齐 (NEW)
│   ├── EntityTimelineTracker             # 时间线追踪 (NEW)
│   ├── GraphQueryEngine                  # 图查询引擎 (NEW)
│   ├── CommunityDetector                 # 社区检测 (NEW)
│   ├── GraphStatistics                   # 图统计 (NEW)
│   └── UnifiedKnowledgeGraphEngine       # 统一入口
├── graph_persistence.py       # 持久化服务
└── __init__.py               # 公共API导出
```

## 功能特性

### 整合的原有功能
1. **多策略实体提取** (from v2 + improved)
   - jieba 词性标注 (优先)
   - 全面的正则表达式规则 (补充)
   - 完整的停用词过滤
   - 5种实体类型: 人名、地名、机构、日期、概念

2. **增强的关系提取** (from service + builder)
   - 共现关系检测
   - 关系类型推断
   - 关系强度计算 (NEW)

3. **持久化和缓存** (from builder_optimized)
   - 多种存储: JSON, Pickle, SQLite, PostgreSQL
   - 版本控制
   - 增量更新
   - 内存缓存

### 新增强大功能 (1+1+1+1+1+1 > 2)

4. **跨文档实体对齐** (NEW)
   - 实体消歧和合并
   - 变体识别 (如 "张教授" vs "张三教授")
   - 规范化实体名称

5. **实体时间线追踪** (NEW)
   - 跨文档追踪实体演变
   - 时间排序的提及记录
   - 共现实体分析

6. **高级图查询API** (NEW)
   - 子图提取 (指定中心和深度)
   - 路径查找 (实体间最短路径)
   - 共同邻居查询

7. **社区检测** (NEW)
   - Louvain 算法聚类
   - 自动发现实体群组
   - 连通分量分析

8. **图统计和质量评估** (NEW)
   - PageRank 重要性排名
   - 多种中心性指标 (度中心性、介数中心性、接近中心性)
   - 图质量评估 (密度、连通性等)

## 使用示例

### 快速开始 - 单文档图谱

```python
from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine

# 创建引擎
engine = UnifiedKnowledgeGraphEngine()

# 构建图谱
graph = engine.build_graph_from_document(
    doc_id="interview_001",
    content="张教授在北京大学进行田野调查，研究传统文化的传承..."
)

print(f"提取了 {len(graph['nodes'])} 个实体")
print(f"发现了 {len(graph['edges'])} 个关系")
```

### 跨文档统一图谱

```python
# 构建多个文档的图谱
for doc_id, content in documents.items():
    engine.build_graph_from_document(doc_id, content)

# 统一所有图谱并进行实体对齐
unified = engine.build_unified_graph(
    align_entities=True,      # 实体对齐
    detect_communities=True   # 社区检测
)

print(f"统一图谱包含 {unified['statistics']['node_count']} 个实体")
print(f"检测到 {unified['statistics']['connected_components']} 个社区")
```

### 查询子图

```python
# 以"张教授"为中心提取2层子图
subgraph = engine.query_graph(
    center_entity="张教授",
    max_depth=2,
    entity_types=["person", "organization"]  # 只关注人和机构
)
```

### 查找实体间路径

```python
# 查找两个实体之间的关系路径
path = engine.find_path("张教授", "北京大学", max_length=5)
if path:
    print(" -> ".join(path))
```

### 获取重要实体排名

```python
# 按 PageRank 获取最重要的10个实体
top_entities = engine.get_top_entities(
    top_k=10,
    metric='pagerank'
)

for entity, score in top_entities:
    print(f"{entity}: {score:.4f}")
```

### 追踪实体时间线

```python
# 追踪"传统文化"概念在不同文档中的演变
timeline = engine.get_entity_timeline(
    entity="传统文化",
    documents=documents_with_timestamps
)

for event in timeline:
    print(f"{event['timestamp']}: 提及 {event['mention_count']} 次")
    print(f"  共现实体: {', '.join(event['co_entities'][:5])}")
```

### 持久化图谱

```python
from app.tools.knowledge.graph import GraphPersistenceService

# JSON 存储
persistence = GraphPersistenceService(
    storage_type='json',
    storage_path='./graphs'
)

# 保存
persistence.save_graph('unified_graph', unified)

# 加载
loaded = persistence.load_graph('unified_graph')

# SQLite 存储 (支持版本控制)
persistence = GraphPersistenceService(
    storage_type='sqlite',
    db_connection_string='./graphs/knowledge.db'
)
```

### 便捷函数

```python
from app.tools.knowledge.graph import create_knowledge_graph

# 一行代码创建图谱
graph = create_knowledge_graph(document_text)
```

## 对比: 旧方式 vs 新方式

### 旧方式 (需要协调3个服务)

```python
# 步骤1: 提取实体
from app.services.knowledge_graph_v2 import knowledge_graph_service_v2
entities = knowledge_graph_service_v2.extract_entities(text)

# 步骤2: 提取关系
relations = knowledge_graph_service_v2.extract_relations(text, entities)

# 步骤3: 构建图谱
from app.services.knowledge_graph_builder import get_knowledge_graph_builder
builder = get_knowledge_graph_builder()
graph = builder.build_graph(entities, relations)

# 步骤4: 持久化
from app.services.knowledge_graph_service import KnowledgeGraphService
kg_service = KnowledgeGraphService()
kg_service.save_graph(graph)
```

### 新方式 (单一入口)

```python
from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine

engine = UnifiedKnowledgeGraphEngine()
graph = engine.build_graph_from_document(doc_id, text)
# 自动提取、关系分析、统计计算、缓存，一步完成
```

## 性能优化

1. **自动策略选择**
   - jieba 可用时优先使用 NLP
   - 自动降级到 regex (无依赖)

2. **智能缓存**
   - 实体提取结果缓存
   - 关系提取结果缓存
   - 图谱加载缓存

3. **批处理支持**
   - 多文档并行处理
   - 增量更新机制

4. **可选依赖**
   - jieba: 中文NLP (推荐但非必需)
   - networkx: 高级图算法 (推荐但非必需)
   - 核心功能无外部依赖

## 迁移指南

### 从旧服务迁移

```python
# 旧代码
from app.services.knowledge_graph_v2 import knowledge_graph_service_v2 as kg_service

entities = kg_service.extract_entities(text)
relations = kg_service.extract_relations(text, entities)

# 新代码 (完全兼容)
from app.tools.knowledge.graph import UnifiedKnowledgeGraphEngine

engine = UnifiedKnowledgeGraphEngine()
graph = engine.build_graph_from_document(doc_id, text)

# 提取相同格式的实体和关系
entities = {
    entity_type: [
        {'text': n['id'], 'type': n['type']}
        for n in graph['nodes']
        if n['type'] == entity_type
    ]
    for entity_type in ['person', 'location', 'organization', 'date', 'concept']
}
```

## API 导入路径

```python
# 推荐方式 - 从 tools 层导入
from app.tools.knowledge.graph import (
    UnifiedKnowledgeGraphEngine,
    GraphPersistenceService,
    create_knowledge_graph
)

# 向后兼容 - 仍可从旧路径导入 (deprecated)
from app.services.knowledge_graph_v2 import knowledge_graph_service_v2
```

## 测试

```bash
# 运行单元测试
pytest tests/tools/knowledge/graph/

# 集成测试
pytest tests/integration/test_knowledge_graph_integration.py
```

## 依赖

### 必需
- Python 3.8+
- 标准库

### 可选 (增强功能)
```bash
pip install jieba              # 中文NLP分词
pip install networkx           # 高级图算法
pip install psycopg2-binary    # PostgreSQL支持
```

## 维护者

整合自6个原版本:
- knowledge_graph.py (基础版)
- knowledge_graph_v2.py (完整规则版)
- knowledge_graph_improved.py (jieba版)
- knowledge_graph_service.py (持久化版)
- knowledge_graph_builder.py (构建器版)
- knowledge_graph_builder_optimized.py (优化版)

统一引擎实现: 2024年整合
