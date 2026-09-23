# FieldMind RAG深度集成架构 - Graphiti + LLM Wiki

## 🎯 集成目标

将知识图谱（Graphiti）和RAG系统（LLM Wiki）深度融入FieldMind，升级为**智能知识检索和生成系统**。

---

## 📦 Graphiti核心能力分析

**来源**: https://github.com/getzep/graphiti

**核心功能**:
- 动态知识图谱构建
- 时序知识管理
- 实体和关系提取
- 图查询和遍历
- 上下文感知检索

**关键价值**:
- 不仅存储文本，而是理解实体关系
- 时间维度的知识演化
- 图结构高效检索

---

## 📚 LLM Wiki核心能力分析

**来源**: https://github.com/nashsu/llm_wiki

**核心功能**:
- RAG（检索增强生成）
- 向量化存储和检索
- 多源知识融合
- 问答系统
- 知识更新和维护

**关键价值**:
- 语义搜索而非关键词匹配
- 结合检索和生成
- 持续学习和更新

---

## 🏗️ FieldMind RAG架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      FieldMind RAG System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Document   │───►│  Knowledge   │───►│   Vector     │     │
│  │   Ingestion  │    │    Graph     │    │   Store      │     │
│  │   (SBPACK)   │    │  (Graphiti)  │    │  (Embeddings)│     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Unified Knowledge Base                      │   │
│  │  - Entities (人、地点、概念)                             │   │
│  │  - Relations (关系图谱)                                 │   │
│  │  - Temporal (时序演化)                                  │   │
│  │  - Vectors (语义向量)                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              RAG Query Engine                            │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐       │   │
│  │  │   Graph    │  │  Vector    │  │   Hybrid   │       │   │
│  │  │   Query    │  │  Search    │  │   Rerank   │       │   │
│  │  └────────────┘  └────────────┘  └────────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LLM Generation Layer                        │   │
│  │  - Context Assembly                                      │   │
│  │  - Prompt Engineering                                    │   │
│  │  - Answer Generation                                     │   │
│  │  - Citation Tracking                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ 新增数据模型

### 1. 知识图谱核心表

```python
# backend/src/app/models/knowledge_graph.py

class Entity(Base):
    """实体节点（Graphiti风格）"""
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(String(100), unique=True)  # UUID
    
    # 实体信息
    name = Column(String(500), nullable=False, index=True)
    entity_type = Column(String(100))  # PERSON, ORGANIZATION, CONCEPT, EVENT, LOCATION
    description = Column(Text)
    
    # 属性（JSON存储灵活属性）
    attributes = Column(JSON)  # {"age": 30, "occupation": "engineer"}
    
    # 别名
    aliases = Column(JSON)  # ["别名1", "别名2"]
    
    # 时序信息（Graphiti特色）
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    observation_count = Column(Integer, default=0)
    
    # 置信度
    confidence_score = Column(Float, default=1.0)
    
    # 来源追溯
    source_documents = Column(JSON)  # [{"doc_id": 1, "chunk_id": 123}]
    
    # 向量（语义嵌入）
    embedding = Column(Vector(1536))  # pgvector扩展
    
    # 关系
    outgoing_relations = relationship("Relation", foreign_keys="Relation.source_id")
    incoming_relations = relationship("Relation", foreign_keys="Relation.target_id")


class Relation(Base):
    """关系边"""
    __tablename__ = "relations"
    
    id = Column(Integer, primary_key=True)
    relation_id = Column(String(100), unique=True)
    
    # 关系端点
    source_id = Column(Integer, ForeignKey("entities.id"))
    target_id = Column(Integer, ForeignKey("entities.id"))
    
    # 关系类型
    relation_type = Column(String(100))  # WORKS_FOR, LOCATED_IN, INVENTED, etc.
    
    # 关系描述
    description = Column(Text)
    
    # 属性
    properties = Column(JSON)  # {"since": "2020", "role": "CEO"}
    
    # 时序信息
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)  # NULL表示当前有效
    
    # 置信度
    confidence_score = Column(Float, default=1.0)
    
    # 来源
    source_documents = Column(JSON)
    
    # 权重（用于图遍历）
    weight = Column(Float, default=1.0)


class TemporalEvent(Base):
    """时序事件（Graphiti特色）"""
    __tablename__ = "temporal_events"
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String(100), unique=True)
    
    # 事件信息
    event_type = Column(String(100))
    description = Column(Text)
    
    # 时间
    timestamp = Column(DateTime, nullable=False)
    duration = Column(Interval)  # 持续时长
    
    # 涉及的实体
    entities = Column(JSON)  # [entity_id1, entity_id2, ...]
    
    # 涉及的关系
    relations = Column(JSON)  # [relation_id1, relation_id2, ...]
    
    # 事件序列
    previous_event_id = Column(String(100))
    next_event_id = Column(String(100))
```

### 2. 向量存储表

```python
class VectorChunk(Base):
    """向量化的文本块"""
    __tablename__ = "vector_chunks"
    
    id = Column(Integer, primary_key=True)
    chunk_id = Column(String(100), unique=True)
    
    # 原始内容
    content = Column(Text, nullable=False)
    content_hash = Column(String(64))
    
    # 元数据
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    
    # 向量嵌入
    embedding = Column(Vector(1536))  # OpenAI ada-002 dimension
    
    # 关联的实体
    entities = Column(JSON)  # [entity_id1, entity_id2, ...]
    
    # 语义标签
    semantic_tags = Column(JSON)
    
    # 索引
    __table_args__ = (
        Index('idx_vector_chunks_embedding', 'embedding', postgresql_using='ivfflat'),
    )


class VectorIndex(Base):
    """向量索引配置"""
    __tablename__ = "vector_indexes"
    
    id = Column(Integer, primary_key=True)
    index_name = Column(String(100), unique=True)
    
    # 索引类型
    index_type = Column(String(50))  # ivfflat, hnsw
    
    # 参数
    parameters = Column(JSON)
    
    # 统计
    total_vectors = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 3. RAG会话表

```python
class RAGSession(Base):
    """RAG对话会话"""
    __tablename__ = "rag_sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 会话上下文
    context_window = Column(JSON)  # 最近的对话历史
    
    # 检索设置
    retrieval_config = Column(JSON)
    
    # 统计
    query_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class RAGQuery(Base):
    """RAG查询记录"""
    __tablename__ = "rag_queries"
    
    id = Column(Integer, primary_key=True)
    query_id = Column(String(100), unique=True)
    
    session_id = Column(Integer, ForeignKey("rag_sessions.id"))
    
    # 查询
    query_text = Column(Text, nullable=False)
    query_embedding = Column(Vector(1536))
    
    # 检索结果
    retrieved_chunks = Column(JSON)  # [{"chunk_id": "...", "score": 0.95}, ...]
    retrieved_entities = Column(JSON)
    retrieved_relations = Column(JSON)
    
    # 生成结果
    generated_answer = Column(Text)
    answer_sources = Column(JSON)  # 引用来源
    
    # 评估
    relevance_score = Column(Float)
    user_feedback = Column(String(50))  # thumbs_up, thumbs_down
    
    # 性能
    retrieval_time_ms = Column(Integer)
    generation_time_ms = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🔧 核心服务实现

### 1. 知识图谱构建器

```python
# backend/src/app/services/knowledge_graph_builder.py

class KnowledgeGraphBuilder:
    """
    从SBPACK构建知识图谱
    
    整合：
    - 文档实体提取
    - 关系识别
    - 时序事件提取
    - 图谱构建和优化
    """
    
    def __init__(self, db: Session, llm_client):
        self.db = db
        self.llm = llm_client
        
    async def build_from_sbpack(self, package_id: int) -> Dict[str, Any]:
        """从SBPACK构建知识图谱"""
        # 1. 加载知识点和技能
        knowledge_items = load_knowledge(package_id)
        skill_items = load_skills(package_id)
        
        # 2. 提取实体
        entities = await self.extract_entities(knowledge_items)
        
        # 3. 提取关系
        relations = await self.extract_relations(entities, knowledge_items)
        
        # 4. 构建时序事件
        events = await self.extract_temporal_events(knowledge_items)
        
        # 5. 保存图谱
        self.save_graph(entities, relations, events)
        
        return {
            "entities": len(entities),
            "relations": len(relations),
            "events": len(events)
        }
    
    async def extract_entities(self, items: List) -> List[Entity]:
        """使用LLM提取实体"""
        prompt = """
        从以下文本中提取实体：
        - 人物（PERSON）
        - 组织（ORGANIZATION）
        - 概念（CONCEPT）
        - 地点（LOCATION）
        - 事件（EVENT）
        
        返回JSON格式。
        """
        # LLM调用
        pass
    
    async def extract_relations(self, entities: List[Entity], items: List) -> List[Relation]:
        """提取实体间关系"""
        pass
```

### 2. 向量存储服务

```python
# backend/src/app/services/vector_store.py

class VectorStore:
    """
    向量存储和检索
    
    使用pgvector扩展实现高效向量检索
    """
    
    def __init__(self, db: Session, embedding_model):
        self.db = db
        self.embedding_model = embedding_model
        
    async def add_documents(self, documents: List[Dict]) -> int:
        """添加文档到向量存储"""
        chunks = []
        
        for doc in documents:
            # 1. 分块
            doc_chunks = self.chunk_document(doc)
            
            # 2. 生成嵌入
            for chunk in doc_chunks:
                embedding = await self.embedding_model.embed(chunk['content'])
                
                vector_chunk = VectorChunk(
                    content=chunk['content'],
                    embedding=embedding,
                    document_id=doc['id']
                )
                chunks.append(vector_chunk)
        
        self.db.add_all(chunks)
        self.db.commit()
        
        return len(chunks)
    
    async def similarity_search(
        self, 
        query: str, 
        top_k: int = 10,
        threshold: float = 0.7
    ) -> List[Dict]:
        """语义相似度搜索"""
        # 1. 查询向量化
        query_embedding = await self.embedding_model.embed(query)
        
        # 2. 向量检索（pgvector）
        results = self.db.execute(f"""
            SELECT 
                chunk_id,
                content,
                1 - (embedding <=> :query_vec) as similarity
            FROM vector_chunks
            WHERE 1 - (embedding <=> :query_vec) > :threshold
            ORDER BY embedding <=> :query_vec
            LIMIT :top_k
        """, {
            "query_vec": query_embedding,
            "threshold": threshold,
            "top_k": top_k
        })
        
        return results.fetchall()
```

### 3. 混合检索引擎

```python
# backend/src/app/services/hybrid_retriever.py

class HybridRetriever:
    """
    混合检索引擎
    
    结合：
    - 向量语义搜索
    - 图谱遍历
    - 全文检索
    - 重排序
    """
    
    def __init__(self, db: Session, vector_store: VectorStore, graph_query: GraphQuery):
        self.db = db
        self.vector_store = vector_store
        self.graph_query = graph_query
        
    async def retrieve(
        self, 
        query: str,
        strategy: str = 'hybrid',
        top_k: int = 10
    ) -> List[Dict]:
        """混合检索"""
        
        # 1. 向量检索
        vector_results = await self.vector_store.similarity_search(query, top_k=20)
        
        # 2. 图谱检索
        # 先识别查询中的实体
        query_entities = await self.extract_query_entities(query)
        
        graph_results = []
        if query_entities:
            # 图遍历获取相关实体和关系
            graph_results = await self.graph_query.traverse(
                query_entities,
                max_depth=2
            )
        
        # 3. 全文检索（作为补充）
        fulltext_results = await self.fulltext_search(query, top_k=10)
        
        # 4. 混合和重排序
        combined = self.combine_results(vector_results, graph_results, fulltext_results)
        reranked = await self.rerank(query, combined, top_k=top_k)
        
        return reranked
    
    async def rerank(self, query: str, candidates: List, top_k: int) -> List:
        """重排序候选结果"""
        # 使用交叉编码器或LLM重排序
        pass
```

### 4. RAG生成服务

```python
# backend/src/app/services/rag_generator.py

class RAGGenerator:
    """
    RAG生成服务
    
    检索 + 生成 = 有根据的回答
    """
    
    def __init__(self, retriever: HybridRetriever, llm_client):
        self.retriever = retriever
        self.llm = llm_client
        
    async def generate_answer(
        self, 
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成答案"""
        
        # 1. 检索相关内容
        retrieved = await self.retriever.retrieve(query, top_k=10)
        
        # 2. 组装上下文
        context = self.assemble_context(retrieved)
        
        # 3. 构建提示词
        prompt = f"""
        基于以下上下文回答问题。如果上下文中没有相关信息，请说"我不知道"。
        
        上下文：
        {context}
        
        问题：{query}
        
        回答：
        """
        
        # 4. LLM生成
        answer = await self.llm.generate(prompt)
        
        # 5. 提取引用
        citations = self.extract_citations(answer, retrieved)
        
        # 6. 保存查询记录
        self.save_query_record(query, retrieved, answer, citations)
        
        return {
            "answer": answer,
            "sources": citations,
            "retrieved_count": len(retrieved)
        }
    
    def assemble_context(self, retrieved: List) -> str:
        """组装上下文"""
        # 将检索结果组织成连贯的上下文
        pass
```

---

## 📊 完整数据流

```
用户上传PDF
    ↓
SBPACK蒸馏（知识+技能）
    ↓
并行处理：
    ├─ 知识图谱构建
    │  ├─ 实体提取
    │  ├─ 关系识别
    │  └─ 时序事件
    │
    └─ 向量化存储
       ├─ 文本分块
       ├─ 嵌入生成
       └─ 向量索引
    ↓
统一知识库
    ↓
用户查询
    ↓
混合检索：
    ├─ 向量语义搜索
    ├─ 图谱遍历
    └─ 全文检索
    ↓
重排序
    ↓
上下文组装
    ↓
LLM生成答案
    ↓
引用追踪
    ↓
返回结果
```

---

## 🎯 核心特性

### 1. 三层检索
- **向量层**: 语义相似度（LLM Wiki）
- **图谱层**: 实体关系遍历（Graphiti）
- **文本层**: 关键词匹配（传统检索）

### 2. 时序感知
- 知识的时间维度
- 事件序列
- 动态更新

### 3. 引用追踪
- 每个答案都有来源
- 可追溯到原始文档
- 支持验证和审计

### 4. 持续学习
- 新文档自动更新图谱
- 增量向量化
- 知识融合和去重

---

## 🚀 API设计

```python
# RAG查询
POST /api/rag/query
{
  "query": "什么是机器学习？",
  "session_id": "optional",
  "retrieval_config": {
    "strategy": "hybrid",
    "top_k": 10
  }
}

# 知识图谱查询
GET /api/graph/entities/{entity_name}
GET /api/graph/relations?source={entity_id}&type={relation_type}
GET /api/graph/traverse?start={entity_id}&max_depth=2

# 向量搜索
POST /api/vectors/search
{
  "query": "深度学习应用",
  "top_k": 20,
  "filters": {"document_type": "paper"}
}

# 图谱可视化
GET /api/graph/visualize?entity_id={id}
```

---

## 📈 性能优化

### 1. 向量索引
- 使用pgvector的IVFFlat或HNSW索引
- 预计算常见查询的嵌入

### 2. 图谱缓存
- 热点实体和关系缓存
- 图遍历结果缓存

### 3. 批处理
- 批量嵌入生成
- 批量图谱更新

---

## 🎓 与现有系统整合

### 整合点1: SBPACK → 知识图谱
```python
# 蒸馏完成后自动构建图谱
@event.listens_for(SBPACKPackage, 'after_insert')
def build_graph(mapper, connection, target):
    graph_builder.build_from_sbpack(target.id)
```

### 整合点2: Obsidian笔记 → 向量存储
```python
# Obsidian同步时自动向量化
@event.listens_for(ObsidianNote, 'after_insert')
def vectorize_note(mapper, connection, target):
    vector_store.add_document(target)
```

### 整合点3: 技能树 → 知识图谱
```python
# 技能节点作为图谱中的特殊实体
skill_entity = Entity(
    name=skill_node.name,
    entity_type='SKILL',
    attributes={
        'difficulty': skill_node.difficulty,
        'category': skill_node.category
    }
)
```

---

这是FieldMind的**下一个重大升级**：从知识管理到**智能知识问答**！

继续实施？
