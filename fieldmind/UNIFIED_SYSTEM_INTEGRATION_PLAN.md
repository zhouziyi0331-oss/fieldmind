# FieldMind 统一系统整合方案
## 解决"两个系统"问题的完整设计

---

## 🔴 问题诊断

### 当前存在的"两个系统"

#### 系统A：原有的9步骤知识流水线
```
文档上传 
  ↓
Step 1: 文本校刊 (脏数据清洗)
  ↓
Step 2: 结构分析
  ↓
Step 3: 实体构建 → entities 表
  ↓
Step 4: 事件提取 → timeline_events 表
  ↓
Step 5: 关系发现 → entity_relations 表
  ↓
Step 6: 本体构建 (缺失)
  ↓
Step 7: 逻辑推理 (缺失)
  ↓
Step 8: 知识单元化 (缺失)
  ↓
Step 9: 阅读器生成 (缺失)
```

**数据通道**：
- 🔴 **脏数据通道**：原始文档 → document_chunks (raw text)
- 🟢 **干净数据通道**：cleaned_text → 结构化知识 (entities, events, relations)

#### 系统B：新增的文档规范化层
```
文档上传
  ↓
检测文件类型
  ↓
规范化处理 (5条规则)
  ├─ 音频 → Whisper → 文本
  ├─ 视频 → PySceneDetect + BLIP-2 → 文本
  ├─ 图片 → PaddleOCR + BLIP-2 → 文本
  ├─ 表格 → 结构化提取 → 文本
  └─ 文档 → AI增强 → 文本
  ↓
并行索引到6个RAG引擎
  ├─ Quivr
  ├─ LightRAG
  ├─ GraphRAG
  ├─ Cognee
  ├─ Mem0
  └─ RAGFlow
```

**核心问题**：
1. ❌ **两条平行轨道**：9步骤流水线 和 规范化+RAG索引 各自独立
2. ❌ **数据不互通**：规范化后的文本没有进入9步骤流水线
3. ❌ **重复劳动**：RAG引擎索引了文本，但知识图谱不知道
4. ❌ **缺少统一入口**：用户不知道文档是走哪条路径处理的

---

## 🎯 统一整合方案

### 核心设计原则

1. **单一流水线**：所有文档都走同一条完整流水线
2. **规范化前置**：多模态文档先规范化为文本，再进入9步骤
3. **并行处理**：RAG索引和知识构建并行进行，互不阻塞
4. **数据互通**：所有处理结果都记录在统一的数据模型中

### 统一流水线架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        文档上传 (单一入口)                            │
│                    project_documents 表                               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│              阶段0: 文件类型检测与路由 (新增)                         │
│                                                                       │
│  file_type = detect_file_type(document)                              │
│                                                                       │
│  if file_type in ['audio', 'video', 'image', 'table']:              │
│      route = 'multimodal_normalization'                              │
│  elif file_type in ['pdf', 'docx', 'txt', 'md']:                    │
│      route = 'text_extraction'                                       │
│  else:                                                               │
│      route = 'unknown'                                               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────┴──────────┐
                    ↓                    ↓
    ┌───────────────────────┐   ┌───────────────────────┐
    │  多模态规范化分支      │   │   文本提取分支        │
    │  (音频/视频/图片/表格) │   │   (PDF/Word/TXT/MD)  │
    └───────────────────────┘   └───────────────────────┘
                    ↓                    ↓
            [AI增强处理]           [直接提取]
                    ↓                    ↓
            Whisper/OCR/BLIP-2      DocumentExtractor
                    ↓                    ↓
                    └─────────┬──────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│              统一文本内容 (汇合点)                                    │
│                                                                       │
│  normalized_text = {                                                 │
│      'content': str,              # 统一的文本内容                   │
│      'source_type': str,          # 'audio', 'video', 'document'    │
│      'confidence': float,         # AI处理置信度                     │
│      'metadata': dict,            # 扩展元数据                       │
│      'ai_enhanced': bool          # 是否AI增强                       │
│  }                                                                   │
│                                                                       │
│  存储位置: document_chunks.normalized_content (新增字段)              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│            Step 1: 文本校刊 (脏数据 → 干净数据)                      │
│                                                                       │
│  • 去除噪声字符                                                       │
│  • 修正OCR错误 (如果是图片/视频来源)                                 │
│  • 统一编码格式                                                       │
│  • 段落重组                                                           │
│                                                                       │
│  存储: document_chunks.cleaned_text                                  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│            Step 2: 结构分析                                           │
│                                                                       │
│  • 文档结构树 (章节/段落层次)                                         │
│  • 逻辑块识别                                                         │
│  • 引用关系                                                           │
│                                                                       │
│  存储: document_structure 表 (新增)                                  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────┴──────────┐
                    ↓                    ↓
        ┌──────────────────┐   ┌──────────────────────┐
        │   知识构建分支    │   │   RAG索引分支         │
        │   (Step 3-9)     │   │   (6个引擎)           │
        └──────────────────┘   └──────────────────────┘
                    ↓                    ↓
        ┌──────────────────┐   ┌──────────────────────┐
        │ Step 3: 实体构建 │   │ Quivr 索引            │
        │ → entities       │   │ LightRAG 索引         │
        └──────────────────┘   │ GraphRAG 索引         │
                    ↓           │ Cognee 索引           │
        ┌──────────────────┐   │ Mem0 索引             │
        │ Step 4: 事件提取 │   │ RAGFlow 索引          │
        │ → events         │   └──────────────────────┘
        └──────────────────┘            ↓
                    ↓           (并行执行，不阻塞)
        ┌──────────────────┐            ↓
        │ Step 5: 关系发现 │   ┌──────────────────────┐
        │ → relationships  │   │ rag_index_status     │
        └──────────────────┘   │ (新增表，记录状态)    │
                    ↓           └──────────────────────┘
        ┌──────────────────┐
        │ Step 6: 本体构建 │
        │ → ontology       │
        └──────────────────┘
                    ↓
        ┌──────────────────┐
        │ Step 7: 逻辑推理 │
        │ → inferences     │
        └──────────────────┘
                    ↓
        ┌──────────────────┐
        │ Step 8: 知识单元 │
        │ → knowledge_units│
        └──────────────────┘
                    ↓
        ┌──────────────────┐
        │ Step 9: 阅读器   │
        │ → wiki_pages     │
        └──────────────────┘
                    ↓
                    └─────────┬──────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   统一知识图谱 (最终汇合)                             │
│                                                                       │
│  • 所有实体/事件/关系 → 知识图谱                                      │
│  • 所有RAG索引状态 → 可查询                                           │
│  • 所有处理日志 → 可追溯                                              │
│                                                                       │
│  查询接口:                                                            │
│  - get_document_knowledge(doc_id) → 完整知识                         │
│  - get_document_rag_status(doc_id) → RAG索引状态                     │
│  - get_processing_pipeline(doc_id) → 处理路径                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 统一数据模型

### 1. 扩展 project_documents 表

```sql
ALTER TABLE project_documents ADD COLUMN processing_route TEXT;
-- 值: 'multimodal_normalization' | 'text_extraction' | 'unknown'

ALTER TABLE project_documents ADD COLUMN normalization_result JSON;
-- 存储规范化处理的元数据:
-- {
--   "method": "whisper" | "paddleocr" | "blip2" | "direct",
--   "confidence": 0.95,
--   "processing_time": 12.5,
--   "ai_service_calls": ["whisper", "paddleocr"]
-- }

ALTER TABLE project_documents ADD COLUMN pipeline_status JSON;
-- 记录9步骤的完成状态:
-- {
--   "step_1_text_cleaning": "completed",
--   "step_2_structure": "completed",
--   "step_3_entities": "completed",
--   "step_4_events": "in_progress",
--   ...
-- }

ALTER TABLE project_documents ADD COLUMN rag_index_status JSON;
-- 记录RAG索引状态:
-- {
--   "quivr": {"status": "success", "indexed_at": "2024-01-15T10:30:00Z"},
--   "lightrag": {"status": "success", "indexed_at": "2024-01-15T10:30:05Z"},
--   "graphrag": {"status": "failed", "error": "timeout"},
--   ...
-- }
```

### 2. 扩展 document_chunks 表

```sql
ALTER TABLE document_chunks ADD COLUMN normalized_content TEXT;
-- 规范化后的原始内容 (来自AI服务或直接提取)

ALTER TABLE document_chunks ADD COLUMN cleaned_text TEXT;
-- Step 1 清洗后的干净文本

ALTER TABLE document_chunks ADD COLUMN structure_metadata JSON;
-- Step 2 结构分析结果
-- {
--   "type": "paragraph" | "title" | "list_item",
--   "level": 1,
--   "parent_chunk_id": 123
-- }
```

### 3. 新增 document_structure 表 (Step 2)

```sql
CREATE TABLE document_structure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,
    
    -- 结构信息
    node_type TEXT NOT NULL,         -- 'chapter', 'section', 'paragraph', 'table', 'figure'
    node_level INTEGER,              -- 层级深度 (1, 2, 3...)
    title TEXT,
    
    -- 树形结构
    parent_id INTEGER,               -- 父节点ID
    sequence_order INTEGER,          -- 同级顺序
    
    -- 元数据
    metadata JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES project_documents(id),
    FOREIGN KEY (chunk_id) REFERENCES document_chunks(id),
    FOREIGN KEY (parent_id) REFERENCES document_structure(id)
);

CREATE INDEX idx_doc_structure_doc ON document_structure(document_id);
CREATE INDEX idx_doc_structure_parent ON document_structure(parent_id);
```

### 4. 统一 entities 表 (Step 3)

```sql
-- 重新设计，统一所有实体来源
CREATE TABLE entities_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT UNIQUE NOT NULL,      -- 全局唯一标识符
    
    -- 来源追溯
    document_id INTEGER NOT NULL,
    chunk_ids JSON,                       -- 提及该实体的所有chunk
    source_type TEXT,                     -- 'audio', 'video', 'image', 'document'
    
    -- 实体信息
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,            -- 'person', 'location', 'organization', 'concept'
    entity_category TEXT,
    
    -- 属性
    properties JSON,
    confidence REAL,
    mention_count INTEGER DEFAULT 0,
    
    -- 链接
    canonical_entity_id TEXT,             -- 消歧后的标准ID
    external_ids JSON,                    -- {"wikidata": "Q123", "dbpedia": "..."}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES project_documents(id)
);

CREATE INDEX idx_entities_doc ON entities_unified(document_id);
CREATE INDEX idx_entities_name ON entities_unified(entity_name);
CREATE INDEX idx_entities_type ON entities_unified(entity_type);
```

### 5. 统一 events 表 (Step 4)

```sql
CREATE TABLE events_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    
    -- 来源
    document_id INTEGER NOT NULL,
    chunk_ids JSON,
    source_type TEXT,
    
    -- 事件信息
    event_type TEXT NOT NULL,
    event_name TEXT,
    description TEXT,
    
    -- 时间
    temporal_expression TEXT,             -- 原始表达 "2024年1月"
    normalized_time_start TEXT,           -- ISO格式 "2024-01-01T00:00:00Z"
    normalized_time_end TEXT,
    time_confidence REAL,
    
    -- 空间
    spatial_expression TEXT,
    normalized_location TEXT,
    location_confidence REAL,
    
    -- 参与者
    participants JSON,                    -- [{"entity_id": "e_123", "role": "agent"}]
    
    -- 因果
    causes JSON,
    effects JSON,
    
    -- 元数据
    properties JSON,
    confidence REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES project_documents(id)
);

CREATE INDEX idx_events_doc ON events_unified(document_id);
CREATE INDEX idx_events_time ON events_unified(normalized_time_start);
```

### 6. 统一 relationships 表 (Step 5)

```sql
CREATE TABLE relationships_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relationship_id TEXT UNIQUE NOT NULL,
    
    -- 来源
    document_id INTEGER NOT NULL,
    chunk_ids JSON,
    source_type TEXT,
    
    -- 三元组
    subject_id TEXT NOT NULL,             -- 主体实体ID
    predicate TEXT NOT NULL,              -- 关系类型
    object_id TEXT NOT NULL,              -- 客体实体ID
    
    -- 属性
    properties JSON,
    confidence REAL,
    
    -- 上下文
    context_text TEXT,
    temporal_context TEXT,
    spatial_context TEXT,
    
    -- 元数据
    evidence JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES project_documents(id),
    FOREIGN KEY (subject_id) REFERENCES entities_unified(entity_id),
    FOREIGN KEY (object_id) REFERENCES entities_unified(entity_id)
);

CREATE INDEX idx_relationships_doc ON relationships_unified(document_id);
CREATE INDEX idx_relationships_subject ON relationships_unified(subject_id);
CREATE INDEX idx_relationships_object ON relationships_unified(object_id);
```

### 7. 新增 rag_index_status 表

```sql
CREATE TABLE rag_index_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    
    -- RAG引擎
    engine_name TEXT NOT NULL,            -- 'quivr', 'lightrag', 'graphrag', etc.
    
    -- 状态
    status TEXT NOT NULL,                 -- 'pending', 'indexing', 'success', 'failed'
    error_message TEXT,
    
    -- 索引信息
    indexed_at TIMESTAMP,
    index_id TEXT,                        -- 引擎内部的索引ID
    chunk_count INTEGER,
    
    -- 元数据
    metadata JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES project_documents(id),
    UNIQUE(document_id, engine_name)
);

CREATE INDEX idx_rag_status_doc ON rag_index_status(document_id);
CREATE INDEX idx_rag_status_engine ON rag_index_status(engine_name);
```

---

## 🔧 统一流水线协调器实现

### 完全重写 unified_pipeline_coordinator.py

```python
"""
统一流水线协调器 - 真正的单一入口
整合: 多模态规范化 + 9步骤知识构建 + RAG索引
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.logging import logger
from app.core.database import get_db_session
from app.models.project_document import ProjectDocument
from app.services.document_normalization.normalization_service import NormalizationService
from app.services.rag_integration_service import RAGIntegrationService
from app.services.knowledge_pipeline.text_cleaning_service import TextCleaningService
from app.services.knowledge_pipeline.structure_analysis_service import StructureAnalysisService
from app.services.knowledge_pipeline.entity_extraction_service import EntityExtractionService
from app.services.knowledge_pipeline.event_extraction_service import EventExtractionService
from app.services.knowledge_pipeline.relation_extraction_service import RelationExtractionService


class UnifiedPipelineCoordinator:
    """
    统一流水线协调器
    
    处理流程:
    1. 文件类型检测与路由
    2. 多模态规范化 (如需要)
    3. 文本清洗 (Step 1)
    4. 结构分析 (Step 2)
    5. 知识构建 (Step 3-9) + RAG索引 (并行)
    6. 状态更新与通知
    """
    
    def __init__(self):
        self.normalization_service = NormalizationService()
        self.rag_service = RAGIntegrationService()
        self.text_cleaning_service = TextCleaningService()
        self.structure_service = StructureAnalysisService()
        self.entity_service = EntityExtractionService()
        self.event_service = EventExtractionService()
        self.relation_service = RelationExtractionService()
    
    async def process_document(
        self,
        document_id: int,
        db_session
    ) -> Dict[str, Any]:
        """
        处理文档 - 单一入口
        
        Returns:
            {
                'document_id': int,
                'processing_route': str,
                'normalization': dict,
                'pipeline_steps': dict,
                'rag_indexing': dict,
                'duration': float
            }
        """
        start_time = datetime.utcnow()
        
        logger.info(f"📥 开始处理文档: {document_id}")
        
        # 获取文档
        doc = db_session.query(ProjectDocument).filter_by(id=document_id).first()
        if not doc:
            raise ValueError(f"Document not found: {document_id}")
        
        # ========== 阶段0: 文件类型检测与路由 ==========
        processing_route = self._detect_processing_route(doc)
        doc.processing_route = processing_route
        db_session.commit()
        
        logger.info(f"🔀 文档路由: {processing_route}")
        
        # ========== 阶段1: 内容获取 (规范化或直接提取) ==========
        normalized_content = await self._get_normalized_content(doc, processing_route, db_session)
        
        if not normalized_content:
            raise ValueError("无法获取文档内容")
        
        # 存储规范化结果
        doc.normalization_result = {
            'method': normalized_content.get('method'),
            'confidence': normalized_content.get('confidence'),
            'ai_enhanced': normalized_content.get('ai_enhanced', False),
            'processed_at': datetime.utcnow().isoformat()
        }
        db_session.commit()
        
        # ========== 阶段2: 9步骤知识流水线 ==========
        pipeline_results = await self._run_knowledge_pipeline(
            doc,
            normalized_content['content'],
            db_session
        )
        
        # ========== 阶段3: RAG索引 (并行) ==========
        # 不阻塞主流程，异步执行
        asyncio.create_task(
            self._index_to_rag_engines(doc, normalized_content['content'], db_session)
        )
        
        # ========== 阶段4: 最终状态更新 ==========
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ 文档处理完成: {document_id}, 耗时: {duration:.2f}s")
        
        return {
            'document_id': document_id,
            'processing_route': processing_route,
            'normalization': doc.normalization_result,
            'pipeline_steps': pipeline_results,
            'duration': duration
        }
    
    def _detect_processing_route(self, doc: ProjectDocument) -> str:
        """
        检测文档应该走哪条处理路径
        
        Returns:
            'multimodal_normalization' | 'text_extraction' | 'unknown'
        """
        file_type = doc.file_type.lower() if doc.file_type else ''
        mime_type = doc.mime_type.lower() if doc.mime_type else ''
        
        # 多模态文件 - 需要AI规范化
        multimodal_types = [
            'audio', 'video', 'image', 'table',
            'mp3', 'wav', 'mp4', 'avi', 'mov',
            'jpg', 'jpeg', 'png', 'gif', 'bmp',
            'csv', 'xlsx', 'xls'
        ]
        
        if any(t in file_type or t in mime_type for t in multimodal_types):
            return 'multimodal_normalization'
        
        # 文本文件 - 直接提取
        text_types = ['pdf', 'docx', 'doc', 'txt', 'md', 'html']
        
        if any(t in file_type or t in mime_type for t in text_types):
            return 'text_extraction'
        
        return 'unknown'
    
    async def _get_normalized_content(
        self,
        doc: ProjectDocument,
        route: str,
        db_session
    ) -> Dict[str, Any]:
        """
        获取规范化内容
        
        Returns:
            {
                'content': str,
                'method': str,
                'confidence': float,
                'ai_enhanced': bool,
                'metadata': dict
            }
        """
        if route == 'multimodal_normalization':
            logger.info(f"🤖 使用AI规范化处理: {doc.file_type}")
            
            # 调用规范化服务
            norm_result = self.normalization_service.normalize_document(
                document_id=doc.id,
                file_type=doc.file_type,
                file_content=self._get_file_content(doc),
                metadata=doc.metadata or {},
                use_cache=True,
                db_session=db_session
            )
            
            return {
                'content': norm_result.text_content,
                'method': norm_result.normalization_method,
                'confidence': norm_result.confidence,
                'ai_enhanced': True,
                'metadata': norm_result.metadata
            }
        
        elif route == 'text_extraction':
            logger.info(f"📄 直接文本提取: {doc.file_type}")
            
            # 从现有的 content 字段获取
            content = doc.content or ''
            
            if not content and doc.file_content:
                # 如果没有提取过，调用提取器
                from app.processors.document_extractor import DocumentExtractor
                extraction_result = DocumentExtractor.extract(
                    file_path=None,  # 从内存读取
                    file_content=doc.file_content,
                    mime_type=doc.mime_type
                )
                content = extraction_result['text']
            
            return {
                'content': content,
                'method': 'direct_extraction',
                'confidence': 1.0,
                'ai_enhanced': False,
                'metadata': {}
            }
        
        else:
            raise ValueError(f"未知的处理路径: {route}")
    
    def _get_file_content(self, doc: ProjectDocument) -> Optional[bytes]:
        """获取文件二进制内容"""
        if doc.file_content:
            return doc.file_content
        
        if doc.storage_path:
            # 从对象存储读取
            from app.core.storage import ObjectStorage
            storage = ObjectStorage()
            return storage.download_file_content(doc.storage_path)
        
        return None
    
    async def _run_knowledge_pipeline(
        self,
        doc: ProjectDocument,
        content: str,
        db_session
    ) -> Dict[str, Any]:
        """
        运行9步骤知识流水线
        
        Returns:
            {
                'step_1_cleaning': {'status': 'success', ...},
                'step_2_structure': {'status': 'success', ...},
                'step_3_entities': {'status': 'success', 'count': 10},
                ...
            }
        """
        results = {}
        
        # Step 1: 文本校刊 (脏数据清洗)
        logger.info("🧹 Step 1: 文本校刊")
        cleaned_text = self.text_cleaning_service.clean_text(
            text=content,
            source_type=doc.processing_route
        )
        results['step_1_cleaning'] = {
            'status': 'success',
            'original_length': len(content),
            'cleaned_length': len(cleaned_text)
        }
        
        # 保存清洗后的文本到 document_chunks
        await self._save_cleaned_chunks(doc.id, cleaned_text, db_session)
        
        # Step 2: 结构分析
        logger.info("🏗️ Step 2: 结构分析")
        structure_tree = self.structure_service.analyze_structure(
            document_id=doc.id,
            text=cleaned_text,
            db_session=db_session
        )
        results['step_2_structure'] = {
            'status': 'success',
            'node_count': len(structure_tree)
        }
        
        # Step 3: 实体构建
        logger.info("👤 Step 3: 实体构建")
        entities = self.entity_service.extract_entities(
            document_id=doc.id,
            text=cleaned_text,
            source_type=doc.processing_route,
            db_session=db_session
        )
        results['step_3_entities'] = {
            'status': 'success',
            'entity_count': len(entities)
        }
        
        # Step 4: 事件提取
        logger.info("⏰ Step 4: 事件提取")
        events = self.event_service.extract_events(
            document_id=doc.id,
            text=cleaned_text,
            entities=entities,
            db_session=db_session
        )
        results['step_4_events'] = {
            'status': 'success',
            'event_count': len(events)
        }
        
        # Step 5: 关系发现
        logger.info("🔗 Step 5: 关系发现")
        relations = self.relation_service.extract_relations(
            document_id=doc.id,
            text=cleaned_text,
            entities=entities,
            events=events,
            db_session=db_session
        )
        results['step_5_relations'] = {
            'status': 'success',
            'relation_count': len(relations)
        }
        
        # Step 6-9: TODO - 后续实现
        results['step_6_ontology'] = {'status': 'pending'}
        results['step_7_inference'] = {'status': 'pending'}
        results['step_8_knowledge_units'] = {'status': 'pending'}
        results['step_9_reader'] = {'status': 'pending'}
        
        # 更新文档的流水线状态
        doc.pipeline_status = results
        db_session.commit()
        
        return results
    
    async def _save_cleaned_chunks(
        self,
        document_id: int,
        cleaned_text: str,
        db_session
    ):
        """保存清洗后的文本块"""
        from app.models.document_chunk import DocumentChunk
        from app.processors.text_chunker import TextChunker
        
        chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        chunks = chunker.chunk(text=cleaned_text, metadata={})
        
        for chunk in chunks:
            db_chunk = DocumentChunk(
                document_id=document_id,
                content=chunk.content,
                cleaned_text=chunk.content,  # 已经是清洗后的
                sequence=chunk.sequence,
                token_count=chunk.token_count,
                metadata=chunk.metadata
            )
            db_session.add(db_chunk)
        
        db_session.commit()
        logger.info(f"💾 保存了 {len(chunks)} 个文本块")
    
    async def _index_to_rag_engines(
        self,
        doc: ProjectDocument,
        content: str,
        db_session
    ):
        """
        索引到所有RAG引擎 (并行，不阻塞主流程)
        """
        try:
            logger.info("🚀 开始RAG索引 (异步)")
            
            result = await self.rag_service.index_normalized_document(
                document_id=doc.id,
                normalized_text=content,
                project_id=doc.project_id,
                metadata={
                    'file_type': doc.file_type,
                    'processing_route': doc.processing_route,
                    'normalization_method': doc.normalization_result.get('method')
                },
                engines=['quivr', 'lightrag', 'graphrag', 'cognee', 'mem0', 'ragflow']
            )
            
            # 保存索引状态到数据库
            from app.models.rag_index_status import RAGIndexStatus
            
            for engine_name, engine_result in result.items():
                status_record = RAGIndexStatus(
                    document_id=doc.id,
                    engine_name=engine_name,
                    status=engine_result['status'],
                    error_message=engine_result.get('error'),
                    indexed_at=datetime.utcnow() if engine_result['status'] == 'success' else None,
                    metadata=engine_result
                )
                db_session.merge(status_record)
            
            db_session.commit()
            logger.info(f"✅ RAG索引完成: {result}")
            
        except Exception as e:
            logger.error(f"❌ RAG索引失败: {e}")
            # 不抛出异常，因为RAG索引失败不应该阻塞主流程


# ========== 工厂函数 ==========

def get_unified_coordinator() -> UnifiedPipelineCoordinator:
    """获取统一协调器实例"""
    return UnifiedPipelineCoordinator()
```

---

## 🎯 关键集成点

### 1. 规范化层与Step 1的关系

```
多模态文件 (音频/视频/图片)
    ↓
[规范化层] AI增强处理
    ↓
normalized_content (可能包含AI识别错误)
    ↓
[Step 1] 文本校刊 (清洗AI输出)
    ↓
cleaned_text (干净数据)
```

**关键点**：
- 规范化层输出的是"AI增强的原始文本"，可能包含OCR错误、转录错误
- Step 1 负责清洗这些错误，产生真正干净的数据
- 两者是**串联关系**，不是平行关系

### 2. RAG索引与知识构建的关系

```
cleaned_text
    ↓
    ├──→ [知识构建] Step 3-9 (串行)
    │         ↓
    │    entities → events → relations → ontology
    │
    └──→ [RAG索引] 6个引擎 (并行)
              ↓
         Quivr / LightRAG / GraphRAG / ...
```

**关键点**：
- 两个分支**并行执行**，互不阻塞
- RAG索引使用异步任务，不影响主流程
- 知识构建的结果可以反哺RAG引擎（例如实体链接）

### 3. 数据通道的统一

```
【脏数据通道】
project_documents (raw)
    ↓
normalized_content (AI处理后，可能有错误)
    ↓
cleaned_text (Step 1清洗后的干净数据)

【干净数据通道】
cleaned_text
    ↓
structure → entities → events → relations → ...
    ↓
unified_knowledge_graph
```

**关键点**：
- 只有一条主干道，所有数据都沿着这条路走
- 脏→干 的转换发生在 Step 1
- 后续所有步骤都基于干净数据

---

## 📝 下一步行动计划

### P1: 核心实现 (本周)

1. **重写 unified_pipeline_coordinator.py**
   - ✅ 架构设计已完成
   - ⏳ 实现完整的协调逻辑
   - ⏳ 集成现有的规范化服务

2. **数据库迁移**
   - 创建迁移脚本添加新字段:
     - `project_documents.processing_route`
     - `project_documents.normalization_result`
     - `project_documents.pipeline_status`
     - `project_documents.rag_index_status`
   - 创建新表:
     - `document_structure`
     - `entities_unified`
     - `events_unified`
     - `relationships_unified`
     - `rag_index_status`

3. **实现缺失的服务**
   - `TextCleaningService` (Step 1)
   - `StructureAnalysisService` (Step 2)
   - 统一 `EntityExtractionService` (Step 3)
   - 统一 `EventExtractionService` (Step 4)
   - 统一 `RelationExtractionService` (Step 5)

4. **API接口**
   - POST `/api/v1/documents/{id}/process` - 触发完整流水线
   - GET `/api/v1/documents/{id}/pipeline-status` - 查询处理状态
   - GET `/api/v1/documents/{id}/knowledge-graph` - 获取知识图谱

### P2: 测试与优化 (下周)

1. **端到端测试**
   - 测试音频文件 → Whisper → 清洗 → 知识图谱
   - 测试视频文件 → 场景提取 → 清洗 → 实体识别
   - 测试PDF文档 → 直接提取 → 结构分析 → 关系发现

2. **性能优化**
   - RAG索引真正异步化
   - 知识构建步骤的并行化
   - 缓存策略优化

3. **监控与可观测性**
   - 每个步骤的耗时统计
   - 失败率监控
   - 数据质量指标

---

## ✅ 总结

### 核心改变

1. **从两个系统 → 一个系统**
   - 规范化层不再是独立系统，而是流水线的前置步骤
   - RAG索引不再是独立系统，而是知识构建的并行分支

2. **从平行轨道 → 单一主干道**
   - 所有文档都走同一条流水线
   - 根据文件类型自动路由到正确的处理分支

3. **从数据孤岛 → 统一数据模型**
   - 所有实体/事件/关系都存储在统一的表中
   - 所有处理状态都记录在 `project_documents` 中
   - 所有RAG索引状态都可查询

### 架构优势

- ✅ **单一入口**: `UnifiedPipelineCoordinator.process_document()`
- ✅ **清晰路径**: 文件类型 → 路由 → 规范化/提取 → 清洗 → 知识构建
- ✅ **并行处理**: 知识构建和RAG索引互不阻塞
- ✅ **完整追溯**: 从原始文件到最终知识图谱的全链路可追踪
- ✅ **错误隔离**: RAG索引失败不影响知识构建
- ✅ **易于扩展**: 新增处理步骤或RAG引擎不影响主流程

### 下一个行动

需要你确认是否接受这个统一架构设计，然后我们开始实现：

1. 创建数据库迁移
2. 实现统一协调器
3. 实现Step 1-5的服务
4. 编写测试用例

你觉得这个方案如何？
