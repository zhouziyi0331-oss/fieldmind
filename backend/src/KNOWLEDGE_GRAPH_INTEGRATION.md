# 知识图谱系统融合设计

## 两个知识图谱系统

### 1. 现有知识图谱（knowledge_graph.py）
- **用途**：田野调查、人物关系、文化遗产
- **节点类型**：人物、组织、地点、文化遗产、民俗等
- **支持数据库**：Neo4j、ArangoDB、NetworkX

### 2. 经验知识图谱（自学习系统）
- **用途**：AI自学习、经验沉淀、模式识别
- **节点类型**：概念、模式、技能、经验、洞察、教训
- **数据来源**：执行记录、反馈闭环、后台学习

## 融合策略

### 底层共享基础设施

#### 1. 统一的图数据库接口
```python
class GraphDatabaseAdapter:
    """统一图数据库适配器"""
    
    def __init__(self, db_type: str):
        # 支持 Neo4j / ArangoDB / NetworkX
        self.db = self._init_database(db_type)
    
    def add_node(self, node_data: Dict) -> str:
        """添加节点（两个图谱都可用）"""
    
    def add_relation(self, source_id: str, target_id: str, relation_type: str):
        """添加关系（两个图谱都可用）"""
    
    def query_by_path(self, start_id: str, end_id: str):
        """路径查询（两个图谱都可用）"""
```

#### 2. 共享的图分析算法
- 社区发现
- 中心性分析
- 路径查找
- 相似度计算

#### 3. 统一的可视化服务
```python
class GraphVisualizationService:
    """图谱可视化服务"""
    
    def generate_visualization(self, graph_type: str, project_id: int):
        """生成图谱可视化（支持两种图谱）"""
```

### 前端展示层分离

#### 1. 田野调查知识图谱（现有）
- 路由：`/knowledge-graph`
- 组件：`KnowledgeGraphViewer`
- 侧重：人物关系、地理位置、文化传承

#### 2. 经验知识图谱（新增）
- 路由：`/experience-graph`
- 组件：`ExperienceGraphViewer`
- 侧重：AI学习轨迹、技能演化、经验沉淀

### 数据层融合

#### 方案：扩展现有模型，添加类型标识

```python
# 在 knowledge_nodes 表中添加 graph_type 字段
class KnowledgeNode(Base):
    graph_type = Column(String(50), index=True)  # "field_research" 或 "experience_learning"
    
    # 原有字段保持不变
    node_type = Column(Enum(NodeType))  # 支持两套节点类型
```

#### 优势
1. **单一数据存储** - 减少维护成本
2. **跨图谱查询** - 可以关联田野调查和AI学习
3. **统一接口** - 一套API服务两个前端

### API设计

#### 统一的知识图谱API
```python
# GET /api/v1/knowledge/nodes?graph_type=field_research
# GET /api/v1/knowledge/nodes?graph_type=experience_learning

# 共享的查询接口
GET /api/v1/knowledge/query
POST /api/v1/knowledge/nodes
POST /api/v1/knowledge/relations

# 特定图谱的分析
GET /api/v1/knowledge/analyze?graph_type=...
```

### 实现优先级

#### P0 - 立即实现
1. 扩展现有 knowledge_nodes 表，添加 graph_type
2. 创建经验知识节点的适配器
3. 实现基础的查询API

#### P1 - 后续优化
1. 跨图谱关联查询
2. 统一可视化服务
3. 智能推荐（结合两个图谱）

#### P2 - 未来增强
1. 图谱融合分析
2. 知识迁移学习
3. 混合推理引擎

## 具体实现

### 扩展NodeType枚举
```python
class NodeType(str, Enum):
    # === 田野调查类 ===
    PERSON = "人物"
    ORGANIZATION = "组织"
    LOCATION = "地点"
    # ... 现有类型
    
    # === 经验学习类 ===
    CONCEPT = "概念"
    PATTERN = "模式"
    SKILL = "技能"
    EXPERIENCE = "经验"
    INSIGHT = "洞察"
    LESSON = "教训"
```

### 适配服务
```python
class ExperienceGraphService:
    """经验图谱服务（使用现有基础设施）"""
    
    def __init__(self, db: Session):
        self.db = db
        self.graph_type = "experience_learning"
    
    def add_experience_node(self, experience_data: Dict):
        """添加经验节点（使用KnowledgeNode表）"""
        node = KnowledgeNode(
            graph_type=self.graph_type,
            node_type=NodeType.EXPERIENCE,
            ...
        )
        return node
```

## 总结

- ✅ **底层融合** - 共享数据库、算法、基础设施
- ✅ **前端分离** - 两个独立的可视化界面
- ✅ **灵活扩展** - 支持未来跨图谱分析
- ✅ **代码复用** - 减少重复开发

