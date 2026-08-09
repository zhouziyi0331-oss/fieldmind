# 深度处理链与文档网络修复方案

## 📋 问题定义

### 问题1：二次分析处理链不完整
**现状**：文档处理完成后就停止，没有触发基于处理结果的二次分析
**需求**：
- 处理完A → 用A的结果分析B
- 处理完B → 用A+B的结果重新分析整体
- 持续累积式分析，不是一次性处理

### 问题2：文件间没有形成网络联系
**现状**：每个文档独立处理，互不关联
**需求**：
- 跨文档实体消歧（同一实体在多个文档中）
- 跨文档关系发现（文档间的引用、补充、矛盾）
- 文档相似度网络
- 时间线关联（访谈的先后顺序）

---

## 🔧 解决方案架构

### 方案1：构建深度处理链
```python
# 单文档处理流程
文档上传 → 格式转换 → 内容提取 → 基础分析 → [触发点1]

[触发点1] → 跨文档实体对齐
         → 文档关系发现  
         → 知识图谱更新
         → [触发点2]

[触发点2] → 整体重新分析
         → 产业链重构
         → 时间线重排
         → Dashboard刷新
```

### 方案2：构建文档网络
```python
# 文档网络层级
1. 实体网络层：Person/Organization/Location跨文档消歧
2. 关系网络层：实体间关系的跨文档整合
3. 主题网络层：相似主题的文档聚类
4. 时间网络层：时间顺序的事件链
5. 引用网络层：文档间的引用和补充关系
```

---

## 📝 实现计划

### 阶段1：增强多格式处理能力（30分钟）

#### 1.1 表格处理增强
**文件**: `app/services/table_processor.py`
```python
class TableProcessor:
    def extract_tables_from_pdf(pdf_path) -> List[DataFrame]
    def extract_tables_from_excel(excel_path) -> List[DataFrame]
    def extract_tables_from_image(image_path) -> List[DataFrame]
    def parse_formula(formula_text) -> Dict
```

#### 1.2 多模态内容统一
**文件**: `app/services/multimodal_processor.py`
```python
class MultiModalProcessor:
    def process_any_format(file_path, file_type) -> UnifiedContent
    # 统一输出格式：
    # - text: 主文本
    # - tables: 表格数据
    # - formulas: 公式列表
    # - images: 图片描述
    # - audio_segments: 音频片段（带时间戳）
    # - metadata: 元数据
```

### 阶段2：构建文档间关联网络（45分钟）

#### 2.1 跨文档实体消歧服务
**文件**: `app/services/cross_document_entity_resolver.py`
```python
class CrossDocumentEntityResolver:
    def resolve_entities(project_id: int) -> Dict
    # 功能：
    # - 找出所有文档中的同名实体
    # - 基于上下文判断是否为同一实体
    # - 合并实体属性
    # - 更新entities表的canonical_id
```

#### 2.2 文档关系发现服务
**文件**: `app/services/document_relation_discovery.py`
```python
class DocumentRelationDiscovery:
    def discover_relations(project_id: int) -> List[DocumentRelation]
    # 关系类型：
    # - REFERENCES: 文档A引用文档B
    # - SUPPLEMENTS: 文档A补充文档B
    # - CONTRADICTS: 文档A与文档B矛盾
    # - SIMILAR_TOPIC: 相似主题
    # - TEMPORAL_SEQUENCE: 时间顺序
```

#### 2.3 文档网络构建器
**文件**: `app/services/document_network_builder.py`
```python
class DocumentNetworkBuilder:
    def build_entity_network(project_id: int) -> nx.Graph
    def build_document_similarity_network(project_id: int) -> nx.Graph
    def build_temporal_network(project_id: int) -> nx.Graph
    def build_citation_network(project_id: int) -> nx.Graph
    
    def get_unified_network(project_id: int) -> Dict:
        # 返回多层网络的JSON表示
        return {
            'entities': [...],
            'documents': [...],
            'entity_links': [...],
            'document_links': [...],
            'temporal_chain': [...]
        }
```

### 阶段3：实现二次分析处理链（60分钟）

#### 3.1 增强workflow_chain.py
**修改**: `app/services/workflow_chain.py`
```python
class WorkflowChain:
    def trigger_next_workflows(self, document, db):
        # 阶段1: 基础处理（已有）
        self._update_project_stats(project_id, db)
        self._sync_entities(document, db)
        
        # 🆕 阶段2: 跨文档关联分析
        self._trigger_cross_document_analysis(project_id, db)
        
        # 🆕 阶段3: 文档网络构建
        self._trigger_document_network_build(project_id, db)
        
        # 🆕 阶段4: 基于网络的深度分析
        self._trigger_network_based_analysis(project_id, db)
        
        # 阶段5: 知识图谱构建（已有，但需增强）
        self._trigger_knowledge_graph_build(project_id, db)
        
        # 阶段6: 产业分析（已有）
        self._trigger_industry_analysis(project_id, db)
        
        # 阶段7: Dashboard刷新（已有）
        self._refresh_dashboard_cache(project_id, db)
    
    def _trigger_cross_document_analysis(self, project_id: int, db: Session):
        """跨文档关联分析"""
        self._notify_module_start(project_id, "cross_document_analysis", "开始跨文档关联分析")
        
        # 1. 实体消歧
        from app.services.cross_document_entity_resolver import resolver
        resolved = resolver.resolve_entities(project_id)
        
        # 2. 文档关系发现
        from app.services.document_relation_discovery import discovery
        relations = discovery.discover_relations(project_id)
        
        # 3. 保存到数据库
        # ... 存储逻辑
        
        self._notify_module_complete(project_id, "cross_document_analysis", 
            f"发现{len(resolved)}个跨文档实体，{len(relations)}个文档关系")
    
    def _trigger_document_network_build(self, project_id: int, db: Session):
        """构建文档网络"""
        self._notify_module_start(project_id, "document_network", "构建文档网络")
        
        from app.services.document_network_builder import network_builder
        network = network_builder.get_unified_network(project_id)
        
        # 缓存网络结构
        from app.core.redis_client import redis_client
        redis_client.setex(
            f"document_network:{project_id}",
            3600,
            json.dumps(network)
        )
        
        self._notify_module_complete(project_id, "document_network",
            f"网络包含{len(network['documents'])}个文档，{len(network['document_links'])}条关系")
    
    def _trigger_network_based_analysis(self, project_id: int, db: Session):
        """基于网络的深度分析"""
        self._notify_module_start(project_id, "network_analysis", "基于文档网络进行深度分析")
        
        # 1. 识别核心文档（PageRank）
        # 2. 识别文档社区（Louvain）
        # 3. 识别关键路径（最短路径）
        # 4. 时间线重构
        
        from app.services.network_analyzer import analyzer
        insights = analyzer.analyze_network(project_id)
        
        self._notify_module_complete(project_id, "network_analysis",
            f"发现{len(insights['communities'])}个文档簇，识别{len(insights['key_documents'])}个核心文档")
```

#### 3.2 创建跨文档分析触发器
**文件**: `app/services/cross_document_trigger.py`
```python
class CrossDocumentTrigger:
    """跨文档分析触发器"""
    
    def should_trigger(self, project_id: int, db: Session) -> bool:
        """判断是否需要触发跨文档分析"""
        # 触发条件：
        # 1. 项目中有2+个已完成的文档
        # 2. 距离上次跨文档分析已过5分钟
        # 3. 有新的实体被提取
        pass
    
    def trigger_analysis(self, project_id: int):
        """触发跨文档分析"""
        # 在后台线程中执行
        executor.submit(self._run_cross_document_analysis, project_id)
    
    def _run_cross_document_analysis(self, project_id: int):
        """执行跨文档分析"""
        db = SessionLocal()
        try:
            # 1. 实体消歧
            # 2. 关系发现
            # 3. 网络构建
            # 4. 深度分析
            # 5. 更新知识图谱
            # 6. 推送前端
            pass
        finally:
            db.close()
```

### 阶段4：增强知识图谱（30分钟）

#### 4.1 修改knowledge_graph_service.py
**增加功能**：
```python
class KnowledgeGraphService:
    def build_cross_document_graph(self, project_id: int) -> nx.Graph:
        """构建跨文档知识图谱"""
        # 1. 加载所有文档的实体和关系
        # 2. 实体消歧和合并
        # 3. 关系去重和强化
        # 4. 添加文档间的关系
        # 5. 计算图统计指标
        pass
    
    def enrich_graph_with_document_context(self, graph: nx.Graph, project_id: int):
        """用文档上下文丰富图谱"""
        # 为每个实体添加：
        # - 出现的文档列表
        # - 每个文档中的上下文
        # - 时间戳信息
        # - 来源可信度
        pass
```

### 阶段5：数据库模型扩展（20分钟）

#### 5.1 添加文档关系表
**文件**: `app/models/document_relation.py`
```python
class DocumentRelation(Base):
    __tablename__ = "document_relations"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    source_document_id = Column(Integer, ForeignKey("project_documents.id"))
    target_document_id = Column(Integer, ForeignKey("project_documents.id"))
    relation_type = Column(String)  # REFERENCES, SUPPLEMENTS, CONTRADICTS, etc.
    confidence = Column(Float)
    evidence = Column(JSON)  # 支持证据
    created_at = Column(DateTime)
```

#### 5.2 添加实体对齐表
**文件**: `app/models/entity_alignment.py`
```python
class EntityAlignment(Base):
    __tablename__ = "entity_alignments"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    canonical_entity_id = Column(Integer)  # 标准实体ID
    mention_entity_ids = Column(JSON)  # 所有提及该实体的ID列表
    confidence = Column(Float)
    merge_reason = Column(Text)
```

---

## 🎬 实施步骤

### Step 1: 创建基础服务（先做独立的，不影响现有系统）
1. ✅ table_processor.py
2. ✅ multimodal_processor.py
3. ✅ cross_document_entity_resolver.py
4. ✅ document_relation_discovery.py
5. ✅ document_network_builder.py

### Step 2: 增强现有服务
1. 修改 workflow_chain.py - 添加新阶段
2. 修改 knowledge_graph_service.py - 跨文档支持
3. 修改 background_tasks.py - 添加触发点

### Step 3: 数据库迁移
1. 创建 document_relations 表
2. 创建 entity_alignments 表

### Step 4: 测试与验证
1. 上传2个相关文档 → 观察跨文档分析
2. 上传3个文档 → 观察网络构建
3. 上传5个文档 → 观察深度分析触发

---

## 📊 预期效果

### 效果1：完整的处理链
```
文档1上传 → 基础处理 → 完成
文档2上传 → 基础处理 → 跨文档分析(1+2) → 网络更新 → 知识图谱重构
文档3上传 → 基础处理 → 跨文档分析(1+2+3) → 网络更新 → 深度洞察
```

### 效果2：文档网络可视化
```
前端显示：
- 文档关系图（哪些文档互相引用）
- 实体网络图（跨文档的人物/组织关系）
- 时间线视图（按时间顺序排列的事件）
- 主题聚类（相似内容的文档分组）
```

### 效果3：智能推荐
```
当查看文档A时，系统推荐：
- "相关文档：B、C、D"
- "相同主题：访谈系列"
- "时间线：这是第3次访谈"
- "矛盾发现：文档B中的说法不一致"
```

---

## ⏱️ 时间估算
- 阶段1：30分钟
- 阶段2：45分钟
- 阶段3：60分钟
- 阶段4：30分钟
- 阶段5：20分钟
- **总计：约3小时**

---

## 🚀 开始实施？
确认后我将按顺序实施，每完成一个阶段推送一次通知。
