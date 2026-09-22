# FieldMind 深度集成架构方案
## 文档规范化系统 × 服务生态系统全面整合

**创建时间**: 2024
**架构师**: Claude Opus 5
**目标**: 将5条规范化规则与200+服务模块深度融合，实现端到端的智能文档处理

---

## 一、系统全景分析

### 1.1 现有架构识别

#### **系统1: 文档规范化层 (Document Normalization Layer)**
```
位置: backend/src/app/services/document_normalization/
核心组件:
  - normalization_rules.py         # 5条核心规则
  - additional_rules.py            # 视频/文档规则
  - ai_service_integration.py      # AI服务集成（Whisper, OCR, BLIP-2）
  - plugin_integration.py          # 文件插件集成（已完成，但方向错误）

功能: 多模态文件 → 统一文本
  ├─ AudioToTextRule       (Whisper)
  ├─ VideoToTextRule       (PySceneDetect + BLIP-2)
  ├─ ImageToTextRule       (PaddleOCR + BLIP-2)
  ├─ TableToTextRule       (Pandas + 结构化处理)
  └─ DocumentToTextRule    (PyMuPDF, python-docx)
```

#### **系统2: FieldMind服务生态系统 (Service Ecosystem)**
```
位置: backend/src/app/services/
核心服务:

【记忆层】
  - mem0_service.py               # Mem0长记忆系统
  - cognee_service.py             # Cognee AI记忆 + Neo4j图谱

【知识图谱层】
  - knowledge_graph_service.py    # NetworkX + spaCy实体提取
  - neo4j_adapter.py              # Neo4j图数据库适配
  - graphiti_service.py           # 时序知识图谱

【RAG引擎层】
  - quivr_service.py              # Quivr第二大脑RAG
  - ragflow_service.py            # RAGFlow文档处理
  - lightrag_service.py           # 图谱增强RAG (naive/local/global/hybrid)
  - graphrag_service.py           # 微软GraphRAG (local/global双视角)
  - khoj_service.py               # 个人知识助手

【处理管线层】
  - unified_pipeline_coordinator.py  # 统一管道协调器 ⭐
  - document_processing_pipeline.py  # 文档处理管线
  - processors/document_pipeline.py  # 提取→分块→向量

【其他200+服务】
  - 实体提取、关系发现、摘要生成、分类服务...
```

### 1.2 关键发现

**🔴 当前问题:**
- 规范化层与服务生态完全隔离
- 规范化后的文本没有流入知识图谱
- 多模态内容无法进入RAG系统
- AI增强提取结果未持久化
- 缺少端到端的数据流通道

**🎯 集成目标:**
将规范化层嵌入到整个文档处理生命周期，让每一个服务都能受益于高质量的多模态文本提取。

---

## 二、深度集成架构设计

### 2.1 整体数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                     文件上传 (File Upload)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  边界0: 文件识别与路由 (File Type Detection & Routing)            │
│  - 识别文件类型: audio/video/image/table/document                 │
│  - 路由到对应的规范化规则                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【规范化层】Document Normalization Layer (新增AI增强)              │
│ ================================================================ │
│  Rule 1: AudioToTextRule                                         │
│    ├─ Whisper API                                                │
│    ├─ 去除填充词（嗯、啊）                                         │
│    └─ 添加说话人标识                                              │
│                                                                   │
│  Rule 2: VideoToTextRule                                         │
│    ├─ PySceneDetect 关键帧提取                                    │
│    ├─ BLIP-2 图像理解                                            │
│    └─ 场景时间轴构建                                              │
│                                                                   │
│  Rule 3: ImageToTextRule                                         │
│    ├─ PaddleOCR 文字识别                                         │
│    ├─ BLIP-2 视觉描述                                            │
│    └─ 多语言支持（中英）                                          │
│                                                                   │
│  Rule 4: TableToTextRule                                         │
│    ├─ Pandas结构化解析                                           │
│    ├─ 保留列语义                                                 │
│    └─ 自然语言描述生成                                            │
│                                                                   │
│  Rule 5: DocumentToTextRule                                      │
│    ├─ PyMuPDF/python-docx                                        │
│    └─ 保留文档结构                                                │
│                                                                   │
│  输出: NormalizationResult                                        │
│    ├─ text_content: 规范化文本                                    │
│    ├─ structure_info: 结构化信息                                  │
│    ├─ metadata: 元数据（置信度、处理方式）                          │
│    └─ dirty_data_handled: 脏数据处理记录                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  边界1验证: 多模态→统一文本 (Boundary 1 Validation)                │
│  - 完整性检查: 是否提取到有效文本                                   │
│  - 质量评分: 置信度、字数、结构完整性                               │
│  - 决策: 通过/标记/拒绝                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  持久化层: 规范化结果存储 (Normalized Content Storage)             │
│  ================================================================ │
│  1. ProjectDocument表更新                                         │
│     └─ text_content = result.text_content                        │
│     └─ extra_data['normalization'] = result.to_dict()            │
│                                                                   │
│  2. 新增: normalized_documents表                                  │
│     ├─ document_id                                               │
│     ├─ normalized_text                                           │
│     ├─ normalization_method (whisper/ocr/blip2...)              │
│     ├─ confidence_score                                          │
│     ├─ structure_metadata (JSON)                                 │
│     └─ created_at                                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 【统一管道协调器】Unified Pipeline Coordinator                     │
│  - 执行9步知识流水线                                              │
│  - 实体提取、关系发现、摘要生成...                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  边界2验证: 文本→可用知识 (Boundary 2 Validation)                 │
│  - 脉络清晰度检查                                                 │
│  - 知识单元可用性评估                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ 记忆层集成   │  │ 图谱层集成   │  │ RAG层集成    │
    └─────────────┘  └─────────────┘  └─────────────┘
```

### 2.2 核心集成点详细设计

#### **集成点1: 规范化层嵌入文档上传流程**

**修改位置**: `unified_pipeline_coordinator.py`

```python
# 当前流程:
上传 → 提取文本 → 验证 → 知识流水线

# 新流程:
上传 → 🆕【规范化处理】→ 验证 → 知识流水线
```

**新增方法**:
```python
def _normalize_document_content(self, doc: ProjectDocument) -> NormalizationResult:
    """
    在知识流水线前先进行规范化处理
    
    根据文件类型选择对应的规范化规则:
    - audio → AudioToTextRule (Whisper)
    - video → VideoToTextRule (场景提取)
    - image → ImageToTextRule (OCR + Vision)
    - table → TableToTextRule (结构化)
    - document → DocumentToTextRule (文档解析)
    """
    from app.services.document_normalization.normalization_service import get_normalization_service
    
    norm_service = get_normalization_service()
    result = norm_service.normalize_document(
        document_id=doc.id,
        file_type=doc.file_type,
        file_content=doc.file_content,
        metadata={
            'filename': doc.original_filename,
            'mime_type': doc.mime_type
        }
    )
    
    # 持久化规范化结果
    doc.text_content = result.text_content
    doc.extra_data = doc.extra_data or {}
    doc.extra_data['normalization'] = {
        'method': result.metadata.get('method'),
        'confidence': result.confidence,
        'word_count': result.word_count,
        'structure': result.structure_info
    }
    self.db.commit()
    
    return result
```

#### **集成点2: 知识图谱服务直接消费规范化文本**

**修改位置**: `knowledge_graph_service.py`

```python
# 在 extract_entities_and_relations() 方法中优先使用规范化后的文本

def extract_entities_and_relations(
    self, 
    text: str, 
    document_id: int = None,
    use_llm: bool = True,
    use_normalized: bool = True  # 🆕 新增参数
) -> Tuple[List[Entity], List[Relation]]:
    """
    优先使用规范化后的文本进行实体提取
    
    如果文档已经过规范化处理，使用高质量的规范化文本
    否则使用原始文本
    """
    
    if use_normalized and document_id:
        # 🆕 从数据库读取规范化文本
        from app.models.project import ProjectDocument
        doc = self.db.query(ProjectDocument).get(document_id)
        
        if doc and doc.extra_data and 'normalization' in doc.extra_data:
            normalized_text = doc.text_content
            confidence = doc.extra_data['normalization'].get('confidence', 1.0)
            
            logger.info(f"✅ 使用规范化文本进行实体提取 (置信度: {confidence:.2%})")
            text = normalized_text
    
    # 继续原有的提取逻辑...
```

#### **集成点3: RAG引擎统一使用规范化内容**

**新增**: `backend/src/app/services/rag_integration_service.py`

```python
"""
RAG集成服务 - 统一管理所有RAG引擎对规范化内容的索引
"""

class RAGIntegrationService:
    """
    将规范化后的文档自动分发到所有启用的RAG引擎
    """
    
    def __init__(self):
        self.quivr = get_quivr_service()
        self.ragflow = ragflow_service
        self.lightrag = get_lightrag_service()
        self.graphrag = get_graphrag_service()
        self.cognee = get_cognee_service()
    
    async def index_normalized_document(
        self,
        document_id: int,
        normalized_text: str,
        project_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        将规范化后的文档索引到所有RAG引擎
        
        并行执行，避免阻塞
        """
        
        results = {}
        
        # 1. Quivr索引 (第二大脑)
        try:
            quivr_result = await self.quivr.index_document(
                project_id=project_id,
                content=normalized_text,
                metadata=metadata
            )
            results['quivr'] = quivr_result
        except Exception as e:
            logger.error(f"Quivr索引失败: {e}")
            results['quivr'] = {'status': 'error', 'error': str(e)}
        
        # 2. LightRAG索引 (图谱增强)
        try:
            lightrag_result = await self.lightrag.insert_document(
                content=normalized_text,
                document_id=str(document_id),
                project_id=project_id,
                metadata=metadata
            )
            results['lightrag'] = {'status': 'success' if lightrag_result else 'failed'}
        except Exception as e:
            logger.error(f"LightRAG索引失败: {e}")
            results['lightrag'] = {'status': 'error', 'error': str(e)}
        
        # 3. Cognee记忆 (AI记忆图谱)
        try:
            cognee_result = await self.cognee.remember_document(
                content=normalized_text,
                document_id=str(document_id),
                project_id=project_id,
                metadata=metadata
            )
            results['cognee'] = {'status': 'success', 'result': cognee_result}
        except Exception as e:
            logger.error(f"Cognee索引失败: {e}")
            results['cognee'] = {'status': 'error', 'error': str(e)}
        
        # 4. GraphRAG索引 (微软多尺度)
        try:
            graphrag_result = await self.graphrag.index_document(
                content=normalized_text,
                project_id=project_id,
                document_id=document_id,
                metadata=metadata
            )
            results['graphrag'] = graphrag_result
        except Exception as e:
            logger.error(f"GraphRAG索引失败: {e}")
            results['graphrag'] = {'status': 'error', 'error': str(e)}
        
        # 5. Mem0长记忆
        try:
            from app.services.mem0_service import Mem0Service
            mem0 = Mem0Service()
            mem0_result = mem0.add_document_memory(
                project_id=int(project_id),
                document_id=document_id,
                content=normalized_text,
                metadata=metadata
            )
            results['mem0'] = mem0_result
        except Exception as e:
            logger.error(f"Mem0索引失败: {e}")
            results['mem0'] = {'status': 'error', 'error': str(e)}
        
        return results
```

#### **集成点4: 事件总线驱动的自动索引**

**修改位置**: `event_bus.py` 添加新事件类型

```python
class EventTypes:
    # ... 现有事件
    DOCUMENT_NORMALIZED = "document.normalized"  # 🆕 文档规范化完成
```

**新增事件处理器**: `backend/src/app/services/event_handlers/normalization_handler.py`

```python
"""
规范化事件处理器
监听文档规范化完成事件，自动触发下游服务
"""

async def on_document_normalized(event_data: Dict[str, Any]):
    """
    文档规范化完成后自动执行:
    1. 索引到所有RAG引擎
    2. 更新知识图谱
    3. 触发摘要生成
    """
    
    document_id = event_data['document_id']
    project_id = event_data['project_id']
    normalized_text = event_data['normalized_text']
    metadata = event_data['metadata']
    
    logger.info(f"🎯 处理文档规范化事件: doc={document_id}, project={project_id}")
    
    # 1. 索引到RAG引擎
    rag_service = RAGIntegrationService()
    rag_results = await rag_service.index_normalized_document(
        document_id=document_id,
        normalized_text=normalized_text,
        project_id=project_id,
        metadata=metadata
    )
    
    logger.info(f"✅ RAG索引完成: {rag_results}")
    
    # 2. 实体提取并更新知识图谱
    kg_service = get_knowledge_graph_service()
    entities, relations = kg_service.extract_entities_and_relations(
        text=normalized_text,
        document_id=document_id,
        use_llm=True
    )
    kg_service.add_entities_and_relations(entities, relations, document_id)
    
    logger.info(f"✅ 知识图谱更新: {len(entities)}实体, {len(relations)}关系")
    
    # 3. 发布后续事件
    publish_event(EventTypes.KNOWLEDGE_GRAPH_UPDATED, {
        'document_id': document_id,
        'entities_count': len(entities),
        'relations_count': len(relations)
    })

# 注册事件处理器
register_event_handler(EventTypes.DOCUMENT_NORMALIZED, on_document_normalized)
```

---

## 三、实现计划

### 3.1 Phase 1: 核心集成 (P0 - 最高优先级)

**任务1: 创建规范化服务统一入口**
- [x] 文件: `document_normalization/normalization_service.py`
- [ ] 功能: 提供统一的 `normalize_document()` 方法
- [ ] 集成所有5条规则 + AI服务

**任务2: 嵌入统一管道协调器**
- [ ] 修改: `unified_pipeline_coordinator.py`
- [ ] 在 `process_document()` 中添加规范化步骤
- [ ] 位置: 在边界1验证之前

**任务3: 创建RAG集成服务**
- [ ] 新建: `rag_integration_service.py`
- [ ] 实现并行索引到所有RAG引擎
- [ ] 错误处理和重试机制

**任务4: 事件驱动自动化**
- [ ] 新增事件类型: `DOCUMENT_NORMALIZED`
- [ ] 创建事件处理器: `normalization_handler.py`
- [ ] 注册到事件总线

### 3.2 Phase 2: 服务扩展 (P1)

**任务5: 知识图谱深度集成**
- [ ] 修改: `knowledge_graph_service.py`
- [ ] 优先使用规范化文本
- [ ] 添加规范化元数据跟踪

**任务6: 持久化层优化**
- [ ] 新建数据表: `normalized_documents`
- [ ] 迁移脚本: Alembic migration
- [ ] 索引优化

**任务7: 对话服务集成**
- [ ] 修改: AI对话服务
- [ ] 使用规范化文本构建上下文
- [ ] Mem0记忆增强

### 3.3 Phase 3: 监控与优化 (P2)

**任务8: 监控仪表板**
- [ ] 规范化成功率统计
- [ ] 各规则使用频率
- [ ] AI服务调用次数和成本

**任务9: 性能优化**
- [ ] 规范化结果缓存
- [ ] 批量处理优化
- [ ] 异步任务队列

**任务10: 质量反馈循环**
- [ ] 用户反馈收集
- [ ] 低质量文本重处理
- [ ] AI模型微调数据收集

---

## 四、数据模型设计

### 4.1 新增数据表

```sql
-- 规范化文档表
CREATE TABLE normalized_documents (
    id BIGSERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES project_documents(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    
    -- 规范化内容
    normalized_text TEXT NOT NULL,
    original_text TEXT,  -- 可选：保留原始文本对比
    
    -- 规范化方法
    normalization_rule VARCHAR(50) NOT NULL,  -- audio/video/image/table/document
    ai_services_used JSONB,  -- ['whisper', 'paddleocr', 'blip2']
    
    -- 质量指标
    confidence_score FLOAT DEFAULT 1.0,
    word_count INTEGER,
    completeness_score FLOAT,
    
    -- 结构化元数据
    structure_metadata JSONB,  -- 章节、时间轴、表格结构等
    dirty_data_handled JSONB,  -- 脏数据处理记录
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 索引
    CONSTRAINT uk_normalized_doc UNIQUE (document_id)
);

CREATE INDEX idx_normalized_project ON normalized_documents(project_id);
CREATE INDEX idx_normalized_rule ON normalized_documents(normalization_rule);
CREATE INDEX idx_normalized_confidence ON normalized_documents(confidence_score);
```

### 4.2 ProjectDocument表扩展

```python
# 在 extra_data 中添加规范化信息
doc.extra_data['normalization'] = {
    'method': 'whisper',
    'confidence': 0.95,
    'ai_services': ['whisper'],
    'processing_time_ms': 1250,
    'structure': {
        'speakers': ['Speaker_1', 'Speaker_2'],
        'duration_seconds': 180
    },
    'dirty_data_removed': ['filler_words', 'background_noise']
}
```

---

## 五、API接口设计

### 5.1 规范化服务API

```python
# POST /api/v1/documents/{document_id}/normalize
# 手动触发文档规范化

@router.post("/{document_id}/normalize")
async def normalize_document(
    document_id: int,
    force_reprocess: bool = False,  # 强制重新处理
    ai_enhancement: bool = True,    # 是否使用AI增强
    db: Session = Depends(get_db)
):
    """
    手动触发文档规范化处理
    
    如果文档已规范化且force_reprocess=False，直接返回缓存结果
    """
    pass
```

### 5.2 集成状态查询API

```python
# GET /api/v1/documents/{document_id}/integration-status
# 查询文档在各服务中的索引状态

@router.get("/{document_id}/integration-status")
async def get_integration_status(document_id: int, db: Session = Depends(get_db)):
    """
    返回文档在所有集成服务中的状态:
    {
        "normalized": true,
        "normalization_method": "whisper",
        "rag_engines": {
            "quivr": {"indexed": true, "brain_id": "xxx"},
            "lightrag": {"indexed": true},
            "cognee": {"indexed": true, "memories": 5},
            "graphrag": {"indexed": false, "reason": "pending"}
        },
        "knowledge_graph": {
            "entities": 25,
            "relations": 18
        },
        "mem0": {
            "memories": 3
        }
    }
    """
    pass
```

---

## 六、测试策略

### 6.1 单元测试

```python
# tests/services/test_normalization_integration.py

def test_audio_normalization_to_rag():
    """测试音频规范化后自动索引到RAG"""
    # 1. 上传音频文件
    # 2. 触发规范化
    # 3. 验证Quivr/LightRAG是否索引成功
    pass

def test_image_normalization_to_knowledge_graph():
    """测试图片OCR后实体自动提取"""
    # 1. 上传包含文字的图片
    # 2. 触发规范化 (OCR)
    # 3. 验证知识图谱是否提取到实体
    pass
```

### 6.2 集成测试

```python
# tests/integration/test_end_to_end_flow.py

async def test_full_document_lifecycle():
    """
    测试完整的文档生命周期:
    上传 → 规范化 → 知识流水线 → RAG索引 → 对话检索
    """
    # 1. 上传多模态文件
    # 2. 等待规范化完成
    # 3. 验证统一管道协调器执行成功
    # 4. 验证所有RAG引擎索引成功
    # 5. 执行对话查询，验证能检索到规范化内容
    pass
```

---

## 七、监控指标

### 7.1 规范化层指标

```python
metrics = {
    "normalization": {
        "total_documents": 1000,
        "by_rule": {
            "audio": 250,
            "video": 100,
            "image": 300,
            "table": 150,
            "document": 200
        },
        "success_rate": 0.98,
        "avg_confidence": 0.92,
        "ai_service_calls": {
            "whisper": 250,
            "paddleocr": 300,
            "blip2": 400
        },
        "avg_processing_time_ms": {
            "audio": 1200,
            "video": 5000,
            "image": 800
        }
    }
}
```

### 7.2 集成层指标

```python
integration_metrics = {
    "rag_indexing": {
        "quivr_success_rate": 0.99,
        "lightrag_success_rate": 0.97,
        "cognee_success_rate": 0.95,
        "avg_indexing_time_ms": 450
    },
    "knowledge_graph": {
        "entities_extracted": 5000,
        "relations_discovered": 3500,
        "avg_entities_per_doc": 5
    }
}
```

---

## 八、成功标准

### 8.1 功能完整性
- [ ] 所有5条规范化规则集成到统一管道
- [ ] 所有RAG引擎自动索引规范化内容
- [ ] 知识图谱优先使用规范化文本
- [ ] 事件驱动自动化流程正常工作

### 8.2 性能指标
- [ ] 规范化成功率 > 95%
- [ ] 端到端处理时间 < 30秒 (普通文档)
- [ ] RAG索引成功率 > 98%
- [ ] 知识图谱实体提取准确率 > 90%

### 8.3 用户体验
- [ ] 用户上传文件后无需手动触发规范化
- [ ] 对话查询能检索到多模态文件内容
- [ ] 知识图谱包含音频/视频/图片中的实体
- [ ] 系统响应速度无明显下降

---

## 九、风险与缓解

### 9.1 性能风险

**风险**: AI服务调用延迟高，阻塞整个流水线

**缓解**:
- 异步任务队列处理规范化
- 设置超时和重试机制
- 优先级队列：重要文档优先处理

### 9.2 成本风险

**风险**: Whisper/BLIP-2 API调用成本高

**缓解**:
- 缓存规范化结果，避免重复处理
- 提供"快速模式"（跳过AI增强）
- 批量处理优化

### 9.3 质量风险

**风险**: 规范化质量不稳定

**缓解**:
- 置信度阈值过滤
- 边界1/边界2验证
- 人工审核低置信度结果

---

## 十、下一步行动

### 立即执行 (今天)
1. ✅ 创建此架构文档
2. 🔲 创建 `normalization_service.py` 统一入口
3. 🔲 实现 `RAGIntegrationService`
4. 🔲 修改 `unified_pipeline_coordinator.py` 嵌入规范化层

### 本周内完成
5. 🔲 创建事件处理器 `normalization_handler.py`
6. 🔲 修改 `knowledge_graph_service.py` 集成
7. 🔲 数据库迁移：新建 `normalized_documents` 表
8. 🔲 编写端到端测试

### 下周完成
9. 🔲 API接口开发
10. 🔲 监控仪表板
11. 🔲 性能优化
12. 🔲 文档和培训

---

**架构负责人**: Claude Opus 5
**最后更新**: 2024
**状态**: 设计完成，待实施
