# FieldMind 完整系统架构设计

## 第一部分：系统概览

### 核心使命
将多源、多模态的非结构化数据（文档、音频、视频、图片、表格）转化为结构化的知识资产，支持智能检索、分析和决策。

### 架构原则
1. **统一入口**：所有文件通过单一网关进入系统
2. **管道处理**：标准化的处理流程，插件化的处理器
3. **数据治理**：严格的元数据管理和质量控制
4. **知识构建**：自动提取实体、关系，构建知识图谱
5. **智能查询**：支持自然语言、标签、关系等多维查询

---

## 第二部分：数据流架构

### 1. 完整数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户上传文件                              │
│              (PDF, DOCX, MP3, MP4, JPG, XLSX, etc.)             │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    统一上传网关 (Upload Gateway)                 │
│  - 文件验证（大小、类型、安全）                                   │
│  - 生成唯一ID                                                    │
│  - 计算哈希（去重）                                               │
│  - 存储到对象存储（S3/MinIO）                                     │
│  - 创建初始Document记录                                           │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                文件分类器 (File Classifier)                       │
│  - 基于MIME类型和扩展名                                           │
│  - 识别文件类型：Document/Image/Audio/Video/Table/Other          │
│  - 路由到对应的处理管道                                           │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
                    ┌────────┴────────┐
                    │                 │
        ┌───────────▼──────┐  ┌──────▼───────────┐
        │  文档处理管道     │  │  图片处理管道     │
        └───────────┬──────┘  └──────┬───────────┘
                    │                 │
        ┌───────────▼──────┐  ┌──────▼───────────┐
        │  音频处理管道     │  │  视频处理管道     │
        └───────────┬──────┘  └──────┬───────────┘
                    │                 │
        ┌───────────▼──────┐          │
        │  表格处理管道     │          │
        └───────────┬──────┘          │
                    │                 │
                    └────────┬────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              元数据聚合器 (Metadata Aggregator)                   │
│  - 合并所有处理器的输出                                           │
│  - 标准化元数据格式                                               │
│  - 质量检查和验证                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                结构化存储层 (Structured Storage)                  │
│  ├─ Document表：基础文件信息                                      │
│  ├─ Metadata表：提取的元数据                                      │
│  ├─ Entity表：实体（人、地点、组织、概念）                         │
│  ├─ Relation表：实体间关系                                        │
│  ├─ Tag表：标签和分类                                             │
│  ├─ Chunk表：文本分块（用于RAG）                                   │
│  └─ Embedding表：向量嵌入                                         │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              知识图谱构建器 (Knowledge Graph Builder)             │
│  - 实体识别与消歧                                                 │
│  - 关系提取与验证                                                 │
│  - 跨文档关联                                                     │
│  - 时间线构建                                                     │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  统一查询引擎 (Query Engine)                      │
│  - 全文搜索（Elasticsearch）                                      │
│  - 向量检索（向量数据库）                                          │
│  - 图查询（Neo4j/NetworkX）                                       │
│  - SQL查询（结构化数据）                                           │
│  - 自然语言查询（LLM驱动）                                         │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                     前端展示层 (Frontend)                         │
│  ├─ 文件浏览器：树形/列表/网格视图                                 │
│  ├─ 标签过滤器：按类型、标签、时间过滤                             │
│  ├─ 知识图谱可视化：实体关系图                                     │
│  ├─ 时间线视图：按时间展示文件                                     │
│  └─ AI对话：自然语言查询和分析                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 第三部分：处理管道详细设计

### 3.1 文档处理管道 (Document Pipeline)

**输入**: PDF, DOCX, TXT, MD, HTML  
**目标**: 提取文本、结构、实体、关键词

```python
# backend/src/app/services/pipelines/document_pipeline.py

class DocumentPipeline:
    """文档处理管道"""
    
    async def process(self, file_path: str, document_id: str) -> DocumentMetadata:
        """
        处理流程：
        1. 文本提取
        2. 结构识别（标题、段落、列表）
        3. 实体识别（NER）
        4. 关键词提取
        5. 摘要生成
        6. 语义分块
        7. 向量嵌入
        """
        
        # 1. 文本提取
        text = await self.extract_text(file_path)
        
        # 2. 结构识别
        structure = await self.parse_structure(text)
        
        # 3. 实体识别
        entities = await self.extract_entities(text)
        
        # 4. 关键词提取
        keywords = await self.extract_keywords(text)
        
        # 5. 摘要生成
        summary = await self.generate_summary(text)
        
        # 6. 语义分块
        chunks = await self.chunk_text(text, max_tokens=512)
        
        # 7. 向量嵌入
        embeddings = await self.generate_embeddings(chunks)
        
        return DocumentMetadata(
            document_id=document_id,
            text=text,
            structure=structure,
            entities=entities,
            keywords=keywords,
            summary=summary,
            chunks=chunks,
            embeddings=embeddings,
            metadata={
                "page_count": len(structure.pages),
                "word_count": len(text.split()),
                "language": self.detect_language(text)
            }
        )
```

**输出结构**:
```json
{
  "document_id": "doc_123",
  "type": "document",
  "text": "完整文本内容...",
  "structure": {
    "pages": 10,
    "sections": [
      {"title": "第一章", "level": 1, "start": 0, "end": 1000}
    ]
  },
  "entities": [
    {"text": "张三", "type": "PERSON", "confidence": 0.95},
    {"text": "北京", "type": "LOCATION", "confidence": 0.92}
  ],
  "keywords": ["关键词1", "关键词2"],
  "summary": "文档摘要...",
  "chunks": [
    {"id": "chunk_1", "text": "...", "embedding": [0.1, 0.2, ...]}
  ],
  "metadata": {
    "page_count": 10,
    "word_count": 5000,
    "language": "zh"
  }
}
```

### 3.2 图片处理管道 (Image Pipeline)

**输入**: JPG, PNG, HEIC, RAW  
**目标**: 提取EXIF、识别内容、OCR

```python
# backend/src/app/services/pipelines/image_pipeline.py

class ImagePipeline:
    """图片处理管道"""
    
    async def process(self, file_path: str, document_id: str) -> ImageMetadata:
        """
        处理流程：
        1. EXIF元数据提取
        2. 图像识别（场景、物体）
        3. 人脸检测
        4. OCR文字识别
        5. 颜色分析
        6. 图像向量化
        """
        
        # 1. EXIF提取
        exif = await self.extract_exif(file_path)
        
        # 2. 图像识别
        labels = await self.recognize_image(file_path)
        
        # 3. 人脸检测
        faces = await self.detect_faces(file_path)
        
        # 4. OCR
        ocr_text = await self.extract_text_from_image(file_path)
        
        # 5. 颜色分析
        colors = await self.analyze_colors(file_path)
        
        # 6. 向量化
        embedding = await self.generate_image_embedding(file_path)
        
        return ImageMetadata(
            document_id=document_id,
            exif=exif,
            labels=labels,
            faces=faces,
            ocr_text=ocr_text,
            colors=colors,
            embedding=embedding
        )
```

**输出结构**:
```json
{
  "document_id": "img_456",
  "type": "image",
  "exif": {
    "camera": "iPhone 14 Pro",
    "taken_at": "2024-01-15T10:30:00Z",
    "location": {"lat": 39.9, "lon": 116.4, "place": "北京"},
    "settings": {"iso": 100, "aperture": "f/1.8", "shutter": "1/125"}
  },
  "labels": [
    {"label": "建筑", "confidence": 0.95},
    {"label": "天空", "confidence": 0.88}
  ],
  "faces": [
    {"bbox": [100, 100, 200, 200], "confidence": 0.99}
  ],
  "ocr_text": "图片中的文字内容...",
  "colors": {
    "dominant": ["#3A5F8A", "#E8D4B8"],
    "palette": [...]
  },
  "embedding": [0.1, 0.2, ...]
}
```

### 3.3 音频处理管道 (Audio Pipeline)

**输入**: MP3, WAV, M4A  
**目标**: 转录、说话人识别、情感分析

```python
# backend/src/app/services/pipelines/audio_pipeline.py

class AudioPipeline:
    """音频处理管道"""
    
    async def process(self, file_path: str, document_id: str) -> AudioMetadata:
        """
        处理流程：
        1. 音频转录（Whisper）
        2. 说话人分离
        3. 情感分析
        4. 关键时刻检测
        5. 实体识别
        6. 摘要生成
        """
        
        # 1. 转录
        transcript = await self.transcribe(file_path)
        
        # 2. 说话人分离
        speakers = await self.diarize_speakers(file_path, transcript)
        
        # 3. 情感分析
        emotions = await self.analyze_emotion(transcript)
        
        # 4. 关键时刻
        highlights = await self.detect_highlights(transcript, emotions)
        
        # 5. 实体识别
        entities = await self.extract_entities(transcript.text)
        
        # 6. 摘要
        summary = await self.generate_summary(transcript.text)
        
        return AudioMetadata(
            document_id=document_id,
            transcript=transcript,
            speakers=speakers,
            emotions=emotions,
            highlights=highlights,
            entities=entities,
            summary=summary
        )
```

**输出结构**:
```json
{
  "document_id": "audio_789",
  "type": "audio",
  "duration": 3600,
  "transcript": {
    "text": "完整转录文本...",
    "segments": [
      {
        "start": 0.0,
        "end": 5.2,
        "text": "大家好",
        "confidence": 0.95
      }
    ]
  },
  "speakers": [
    {"id": "speaker_1", "segments": [[0, 10], [20, 30]]},
    {"id": "speaker_2", "segments": [[10, 20], [30, 40]]}
  ],
  "emotions": [
    {"timestamp": 0, "emotion": "neutral", "confidence": 0.8}
  ],
  "highlights": [
    {"timestamp": 120, "text": "重要结论", "importance": 0.9}
  ],
  "entities": [...],
  "summary": "音频摘要..."
}
```

### 3.4 视频处理管道 (Video Pipeline)

**输入**: MP4, MOV, AVI  
**目标**: 帧提取、转录、场景识别

```python
# backend/src/app/services/pipelines/video_pipeline.py

class VideoPipeline:
    """视频处理管道"""
    
    async def process(self, file_path: str, document_id: str) -> VideoMetadata:
        """
        处理流程：
        1. 关键帧提取
        2. 音频转录
        3. 场景分割
        4. 物体识别
        5. 字幕识别（OCR）
        6. 时间线构建
        """
        
        # 1. 关键帧提取
        keyframes = await self.extract_keyframes(file_path)
        
        # 2. 音频转录（复用AudioPipeline）
        audio_path = await self.extract_audio(file_path)
        audio_metadata = await self.audio_pipeline.process(audio_path, document_id)
        
        # 3. 场景分割
        scenes = await self.detect_scenes(file_path)
        
        # 4. 物体识别（每个关键帧）
        objects = await self.detect_objects(keyframes)
        
        # 5. 字幕OCR
        subtitles = await self.extract_subtitles(file_path)
        
        # 6. 构建时间线
        timeline = await self.build_timeline(scenes, audio_metadata, objects)
        
        return VideoMetadata(
            document_id=document_id,
            keyframes=keyframes,
            audio=audio_metadata,
            scenes=scenes,
            objects=objects,
            subtitles=subtitles,
            timeline=timeline
        )
```

**输出结构**:
```json
{
  "document_id": "video_101",
  "type": "video",
  "duration": 600,
  "resolution": "1920x1080",
  "fps": 30,
  "keyframes": [
    {"timestamp": 0, "path": "frame_0001.jpg"},
    {"timestamp": 5, "path": "frame_0150.jpg"}
  ],
  "audio": { /* AudioMetadata结构 */ },
  "scenes": [
    {"start": 0, "end": 30, "description": "开场"},
    {"start": 30, "end": 120, "description": "主要内容"}
  ],
  "objects": [
    {"timestamp": 0, "label": "人物", "confidence": 0.95}
  ],
  "subtitles": [
    {"start": 0, "end": 5, "text": "欢迎观看"}
  ],
  "timeline": [
    {"time": 0, "events": ["开场", "speaker_1开始说话", "出现人物"]}
  ]
}
```

### 3.5 表格处理管道 (Table Pipeline)

**输入**: XLSX, CSV, XLS  
**目标**: 结构解析、数据验证、关系识别

```python
# backend/src/app/services/pipelines/table_pipeline.py

class TablePipeline:
    """表格处理管道"""
    
    async def process(self, file_path: str, document_id: str) -> TableMetadata:
        """
        处理流程：
        1. 结构解析
        2. 字段识别
        3. 数据类型推断
        4. 数据验证
        5. 关系识别
        6. 统计分析
        """
        
        # 1. 解析结构
        sheets = await self.parse_sheets(file_path)
        
        # 2. 字段识别
        schema = await self.infer_schema(sheets)
        
        # 3. 数据验证
        validation = await self.validate_data(sheets, schema)
        
        # 4. 关系识别
        relations = await self.detect_relations(sheets)
        
        # 5. 统计分析
        stats = await self.compute_statistics(sheets)
        
        return TableMetadata(
            document_id=document_id,
            sheets=sheets,
            schema=schema,
            validation=validation,
            relations=relations,
            stats=stats
        )
```

**输出结构**:
```json
{
  "document_id": "table_202",
  "type": "table",
  "sheets": [
    {
      "name": "Sheet1",
      "rows": 100,
      "columns": 10,
      "data": [...]
    }
  ],
  "schema": [
    {"column": "姓名", "type": "string", "nullable": false},
    {"column": "年龄", "type": "integer", "nullable": false},
    {"column": "邮箱", "type": "email", "nullable": true}
  ],
  "validation": {
    "valid_rows": 95,
    "invalid_rows": 5,
    "errors": [...]
  },
  "relations": [
    {"from": "员工表.部门ID", "to": "部门表.ID"}
  ],
  "stats": {
    "年龄": {"mean": 35.5, "min": 22, "max": 58}
  }
}
```

---

## 第四部分：数据治理架构

### 4.1 元数据管理

**核心表结构**:

```sql
-- 1. 文档主表
CREATE TABLE documents (
    id VARCHAR(50) PRIMARY KEY,
    project_id INTEGER NOT NULL,
    name VARCHAR(500) NOT NULL,
    type ENUM('document', 'image', 'audio', 'video', 'table') NOT NULL,
    mime_type VARCHAR(100),
    file_size BIGINT,
    file_path VARCHAR(1000),
    hash VARCHAR(64) UNIQUE,  -- SHA256哈希，用于去重
    status ENUM('uploaded', 'processing', 'completed', 'failed') DEFAULT 'uploaded',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_type (type),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
);

-- 2. 元数据表（JSON存储）
CREATE TABLE document_metadata (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL,
    metadata_type VARCHAR(50) NOT NULL,  -- 'exif', 'transcript', 'ocr', etc.
    metadata JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    INDEX idx_type (metadata_type)
);

-- 3. 实体表
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    text VARCHAR(500) NOT NULL,
    type ENUM('PERSON', 'ORG', 'LOCATION', 'DATE', 'CONCEPT') NOT NULL,
    canonical_form VARCHAR(500),  -- 标准化形式，用于消歧
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_text_type (text, type),
    INDEX idx_type (type),
    INDEX idx_canonical (canonical_form)
);

-- 4. 文档-实体关系表
CREATE TABLE document_entities (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    mentions INTEGER DEFAULT 1,  -- 出现次数
    confidence FLOAT,
    context TEXT,  -- 出现的上下文
    
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    INDEX idx_entity (entity_id)
);

-- 5. 实体关系表
CREATE TABLE entity_relations (
    id SERIAL PRIMARY KEY,
    source_entity_id INTEGER NOT NULL,
    target_entity_id INTEGER NOT NULL,
    relation_type VARCHAR(100) NOT NULL,  -- 'works_for', 'located_in', etc.
    confidence FLOAT,
    source_documents JSON,  -- 支持该关系的文档ID列表
    
    FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    INDEX idx_source (source_entity_id),
    INDEX idx_target (target_entity_id),
    INDEX idx_type (relation_type)
);

-- 6. 标签表
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),  -- 'manual', 'auto', 'ai'
    color VARCHAR(7),  -- HEX颜色
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 文档-标签关系表
CREATE TABLE document_tags (
    document_id VARCHAR(50) NOT NULL,
    tag_id INTEGER NOT NULL,
    confidence FLOAT,  -- AI标签的置信度
    created_by VARCHAR(50),  -- 'system' 或用户ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (document_id, tag_id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 8. 文本分块表（用于RAG）
CREATE TABLE document_chunks (
    id VARCHAR(50) PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER,
    start_pos INTEGER,
    end_pos INTEGER,
    metadata JSON,
    
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    INDEX idx_chunk (document_id, chunk_index)
);

-- 9. 向量嵌入表
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    entity_type ENUM('document', 'chunk', 'image') NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,  -- 'text-embedding-3-large', etc.
    vector VECTOR(1536),  -- pgvector扩展
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_vector USING ivfflat (vector vector_cosine_ops)
);

-- 10. 时间线表
CREATE TABLE timeline_events (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL,
    event_time TIMESTAMP NOT NULL,
    event_type VARCHAR(50),
    description TEXT,
    metadata JSON,
    
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    INDEX idx_time (event_time)
);
```

### 4.2 数据质量管理

```python
# backend/src/app/services/data_quality/quality_checker.py

class DataQualityChecker:
    """数据质量检查器"""
    
    async def validate_metadata(self, metadata: Dict) -> QualityReport:
        """
        质量检查项：
        1. 完整性：必填字段是否存在
        2. 一致性：数据类型是否正确
        3. 准确性：置信度是否达标
        4. 唯一性：是否有重复
        5. 时效性：时间戳是否合理
        """
        
        report = QualityReport()
        
        # 1. 完整性检查
        required_fields = ['document_id', 'type', 'created_at']
        for field in required_fields:
            if field not in metadata:
                report.add_error(f"缺少必填字段: {field}")
        
        # 2. 一致性检查
        if 'confidence' in metadata:
            if not 0 <= metadata['confidence'] <= 1:
                report.add_error("置信度必须在0-1之间")
        
        # 3. 准确性检查
        if metadata.get('confidence', 1.0) < 0.7:
            report.add_warning("置信度较低，建议人工审核")
        
        # 4. 唯一性检查
        if await self.is_duplicate(metadata):
            report.add_warning("检测到重复数据")
        
        # 5. 时效性检查
        if 'created_at' in metadata:
            if metadata['created_at'] > datetime.now():
                report.add_error("创建时间不能在未来")
        
        return report
```

### 4.3 数据去重策略

```python
# backend/src/app/services/data_quality/deduplication.py

class DeduplicationService:
    """数据去重服务"""
    
    async def check_duplicate(self, file_path: str) -> Optional[str]:
        """
        去重策略：
        1. 文件哈希去重（SHA256）
        2. 内容相似度去重（向量相似度）
        3. 元数据去重（EXIF、时间戳）
        """
        
        # 1. 计算文件哈希
        file_hash = await self.compute_hash(file_path)
        existing = await self.db.find_by_hash(file_hash)
        if existing:
            return existing.id  # 完全相同的文件
        
        # 2. 内容相似度检查
        embedding = await self.generate_embedding(file_path)
        similar = await self.vector_db.find_similar(embedding, threshold=0.95)
        if similar:
            return similar[0].id  # 内容高度相似
        
        # 3. 元数据去重
        metadata = await self.extract_metadata(file_path)
        if metadata.get('exif'):
            duplicate = await self.db.find_by_exif(metadata['exif'])
            if duplicate:
                return duplicate.id
        
        return None  # 不是重复文件
```

---

## 第五部分：知识图谱构建

### 5.1 实体识别与消歧

```python
# backend/src/app/services/knowledge_graph/entity_resolver.py

class EntityResolver:
    """实体识别与消歧"""
    
    async def resolve_entity(self, text: str, entity_type: str, context: str) -> Entity:
        """
        消歧策略：
        1. 上下文匹配
        2. 共现实体匹配
        3. 知识库匹配
        4. 用户确认
        """
        
        # 1. 查找候选实体
        candidates = await self.find_candidates(text, entity_type)
        
        if len(candidates) == 0:
            # 新实体
            return await self.create_entity(text, entity_type)
        
        if len(candidates) == 1:
            # 唯一匹配
            return candidates[0]
        
        # 2. 上下文消歧
        best_match = await self.disambiguate_by_context(candidates, context)
        if best_match.confidence > 0.8:
            return best_match.entity
        
        # 3. 共现实体消歧
        co_entities = await self.extract_co_entities(context)
        best_match = await self.disambiguate_by_co_occurrence(candidates, co_entities)
        if best_match.confidence > 0.8:
            return best_match.entity
        
        # 4. 标记需要人工确认
        return await self.mark_for_review(text, entity_type, candidates, context)
```

### 5.2 关系提取

```python
# backend/src/app/services/knowledge_graph/relation_extractor.py

class RelationExtractor:
    """关系提取器"""
    
    async def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        """
        关系提取方法：
        1. 规则匹配（正则表达式）
        2. 依存句法分析
        3. LLM提取
        """
        
        relations = []
        
        # 1. 规则匹配
        rule_relations = await self.extract_by_rules(text, entities)
        relations.extend(rule_relations)
        
        # 2. 句法分析
        syntax_relations = await self.extract_by_syntax(text, entities)
        relations.extend(syntax_relations)
        
        # 3. LLM提取（处理复杂关系）
        if len(entities) >= 2:
            llm_relations = await self.extract_by_llm(text, entities)
            relations.extend(llm_relations)
        
        # 去重和验证
        relations = await self.deduplicate_and_validate(relations)
        
        return relations
```

### 5.3 图谱存储与查询

```python
# backend/src/app/services/knowledge_graph/graph_store.py

class GraphStore:
    """图谱存储（支持Neo4j或NetworkX）"""
    
    async def add_entity(self, entity: Entity):
        """添加实体节点"""
        query = """
        MERGE (e:Entity {id: $id})
        SET e.text = $text,
            e.type = $type,
            e.canonical_form = $canonical_form
        """
        await self.neo4j.run(query, entity.dict())
    
    async def add_relation(self, relation: Relation):
        """添加关系边"""
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})
        MERGE (source)-[r:RELATION {type: $relation_type}]->(target)
        SET r.confidence = $confidence,
            r.source_documents = $source_documents
        """
        await self.neo4j.run(query, relation.dict())
    
    async def query_neighbors(self, entity_id: str, max_depth: int = 2) -> Graph:
        """查询邻居节点"""
        query = """
        MATCH path = (start:Entity {id: $entity_id})-[*1..$max_depth]-(end:Entity)
        RETURN path
        """
        result = await self.neo4j.run(query, entity_id=entity_id, max_depth=max_depth)
        return self.build_graph(result)
    
    async def query_path(self, source_id: str, target_id: str) -> List[Path]:
        """查询两个实体间的路径"""
        query = """
        MATCH path = shortestPath(
            (source:Entity {id: $source_id})-[*]-(target:Entity {id: $target_id})
        )
        RETURN path
        """
        result = await self.neo4j.run(query, source_id=source_id, target_id=target_id)
        return self.extract_paths(result)
```

---

## 第六部分：统一查询引擎

### 6.1 查询接口设计

```python
# backend/src/app/services/query_engine/unified_query.py

class UnifiedQueryEngine:
    """统一查询引擎"""
    
    async def query(self, request: QueryRequest) -> QueryResult:
        """
        支持的查询类型：
        1. 全文搜索
        2. 向量检索
        3. 图查询
        4. SQL查询
        5. 自然语言查询
        """
        
        if request.query_type == QueryType.FULLTEXT:
            return await self.fulltext_search(request)
        
        elif request.query_type == QueryType.VECTOR:
            return await self.vector_search(request)
        
        elif request.query_type == QueryType.GRAPH:
            return await self.graph_query(request)
        
        elif request.query_type == QueryType.SQL:
            return await self.sql_query(request)
        
        elif request.query_type == QueryType.NATURAL_LANGUAGE:
            return await self.natural_language_query(request)
        
        else:
            raise ValueError(f"不支持的查询类型: {request.query_type}")
    
    async def natural_language_query(self, request: QueryRequest) -> QueryResult:
        """
        自然语言查询流程：
        1. 意图识别
        2. 实体提取
        3. 生成查询计划
        4. 执行多种查询
        5. 聚合结果
        """
        
        # 1. 意图识别
        intent = await self.classify_intent(request.query)
        
        # 2. 实体提取
        entities = await self.extract_query_entities(request.query)
        
        # 3. 生成查询计划
        plan = await self.generate_query_plan(intent, entities, request)
        
        # 4. 执行查询
        results = []
        for sub_query in plan.sub_queries:
            sub_result = await self.execute_sub_query(sub_query)
            results.append(sub_result)
        
        # 5. 聚合结果
        final_result = await self.aggregate_results(results, plan.aggregation_strategy)
        
        return final_result
```

### 6.2 查询优化

```python
# backend/src/app/services/query_engine/query_optimizer.py

class QueryOptimizer:
    """查询优化器"""
    
    async def optimize(self, query_plan: QueryPlan) -> QueryPlan:
        """
        优化策略：
        1. 谓词下推
        2. 查询重写
        3. 并行执行
        4. 缓存利用
        """
        
        # 1. 谓词下推（过滤条件提前）
        plan = await self.push_down_predicates(query_plan)
        
        # 2. 查询重写（使用更高效的查询）
        plan = await self.rewrite_query(plan)
        
        # 3. 识别可并行的子查询
        plan = await self.identify_parallel_queries(plan)
        
        # 4. 检查缓存
        plan = await self.check_cache(plan)
        
        return plan
```

---

## 第七部分：前端统一架构

### 7.1 数据层统一

```swift
// Sources/Services/UnifiedFileService.swift

/// 统一的文件项协议
protocol FileItem: Identifiable, Codable {
    var id: String { get }
    var name: String { get }
    var type: FileType { get }
    var size: Int64 { get }
    var createdAt: Date { get }
    var metadata: [String: AnyCodable] { get }
    var tags: [String] { get }
}

/// 统一的文件服务
class UnifiedFileService {
    static let shared = UnifiedFileService()
    
    /// 查询文件
    func query(request: FileQueryRequest) async throws -> FileQueryResult {
        // 统一的查询接口
        let endpoint = "/api/files/query"
        let response = try await apiClient.post(endpoint, body: request)
        return try response.decode(FileQueryResult.self)
    }
    
    /// 获取文件详情
    func getDetails(fileId: String) async throws -> FileDetails {
        let endpoint = "/api/files/\(fileId)"
        let response = try await apiClient.get(endpoint)
        return try response.decode(FileDetails.self)
    }
    
    /// 更新标签
    func updateTags(fileId: String, tags: [String]) async throws {
        let endpoint = "/api/files/\(fileId)/tags"
        try await apiClient.put(endpoint, body: ["tags": tags])
    }
}

/// 查询请求
struct FileQueryRequest: Codable {
    let projectId: Int
    let filters: [FileFilter]
    let sortBy: SortOption
    let page: Int
    let pageSize: Int
}

enum FileFilter: Codable {
    case type(FileType)
    case tags([String])
    case dateRange(Date, Date)
    case search(String)
}
```

### 7.2 ViewModel统一

```swift
// Sources/ViewModels/UnifiedFileViewModel.swift

@MainActor
class UnifiedFileViewModel: ObservableObject {
    @Published var items: [FileItem] = []
    @Published var selectedFilters: [FileFilter] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let service = UnifiedFileService.shared
    
    /// 加载文件
    func loadFiles(projectId: Int) async {
        isLoading = true
        errorMessage = nil
        
        do {
            let request = FileQueryRequest(
                projectId: projectId,
                filters: selectedFilters,
                sortBy: .createdAt,
                page: 1,
                pageSize: 50
            )
            
            let result = try await service.query(request: request)
            items = result.items
        } catch {
            errorMessage = "加载失败: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    /// 添加过滤器
    func addFilter(_ filter: FileFilter) async {
        selectedFilters.append(filter)
        await loadFiles(projectId: currentProjectId)
    }
}
```

---

## 第八部分：实施路线图

### 阶段1：数据流统一（第1-2周）

**目标**: 建立统一的文件处理管道

**任务**:
1. ✅ 创建统一上传网关 (`/api/upload`)
2. ✅ 实现文件分类器
3. ✅ 创建5个处理管道（文档/图片/音频/视频/表格）
4. ✅ 统一API响应格式
5. ✅ 创建元数据数据库表

**验收标准**:
- 所有文件类型通过统一入口上传
- 每种文件类型都能提取基础元数据
- API响应格式一致

### 阶段2：数据治理（第3-4周）

**目标**: 实现数据质量管理和去重

**任务**:
1. ✅ 实现数据质量检查器
2. ✅ 实现去重服务
3. ✅ 创建实体识别服务
4. ✅ 创建标签管理系统
5. ✅ 实现文本分块和向量化

**验收标准**:
- 自动检测和阻止重复文件
- 所有元数据通过质量检查
- 实体识别准确率 > 80%

### 阶段3：知识图谱（第5-6周）

**目标**: 构建知识图谱基础设施

**任务**:
1. ✅ 部署Neo4j或配置NetworkX
2. ✅ 实现实体消歧服务
3. ✅ 实现关系提取服务
4. ✅ 构建跨文档关联
5. ✅ 实现图查询API

**验收标准**:
- 能够查询实体间的关系
- 能够发现跨文档关联
- 图查询响应时间 < 1秒

### 阶段4：统一查询（第7-8周）

**目标**: 实现统一查询引擎

**任务**:
1. ✅ 集成Elasticsearch（全文搜索）
2. ✅ 集成向量数据库（语义搜索）
3. ✅ 实现自然语言查询
4. ✅ 实现查询优化器
5. ✅ 实现结果聚合

**验收标准**:
- 支持5种查询类型
- 自然语言查询准确率 > 70%
- 复杂查询响应时间 < 3秒

### 阶段5：前端统一（第9-10周）

**目标**: 重构前端数据层

**任务**:
1. ✅ 创建UnifiedFileService
2. ✅ 重构所有ViewModel
3. ✅ 实现统一的文件浏览器
4. ✅ 实现标签过滤器
5. ✅ 实现知识图谱可视化

**验收标准**:
- 所有页面使用统一Service
- 没有重复的API调用逻辑
- UI响应流畅

---

## 第九部分：技术栈选型

### 后端技术栈

**核心框架**:
- FastAPI: Web框架
- SQLAlchemy: ORM
- Pydantic: 数据验证

**数据存储**:
- PostgreSQL + pgvector: 主数据库 + 向量存储
- Neo4j: 知识图谱（可选，也可用NetworkX）
- Redis: 缓存
- MinIO/S3: 对象存储

**数据处理**:
- Whisper: 音频转录
- PyTesseract: OCR
- spaCy: NLP
- OpenCV: 图像处理
- FFmpeg: 视频处理

**搜索引擎**:
- Elasticsearch: 全文搜索
- pgvector: 向量检索

### 前端技术栈

**框架**:
- SwiftUI: UI框架
- Combine: 响应式编程

**网络**:
- URLSession: HTTP客户端
- WebSocket: 实时通信

**数据可视化**:
- Charts: 图表
- Custom View: 知识图谱可视化

---

## 第十部分：关键指标

### 性能指标

- 文件上传速度: > 10 MB/s
- 处理延迟: < 30秒（中等大小文件）
- 查询响应时间: < 1秒（简单查询）
- 并发处理能力: > 100个文件/分钟

### 质量指标

- 元数据提取准确率: > 95%
- 实体识别准确率: > 80%
- 关系提取准确率: > 70%
- 去重准确率: > 99%

### 用户体验指标

- UI响应时间: < 100ms
- 搜索结果相关性: > 80%
- 系统可用性: > 99.5%

---

## 第十一部分：下一步行动

现在你需要做出决定：

### 选项A：从头开始实施
- 按照阶段1-5的顺序执行
- 预计10周完成
- 需要暂停现有功能开发

### 选项B：增量重构
- 保留现有功能
- 逐步替换为新架构
- 预计15周完成

### 选项C：混合方案
- 阶段1-2快速实施（2周）
- 现有功能迁移到新架构（2周）
- 阶段3-5逐步推进（6周）
- 总计10周

---

**请告诉我你的选择，我会立即开始执行。**

同时，我建议：
1. 先审查这份架构设计
2. 讨论和调整细节
3. 确定优先级
4. 开始实施

你认为这个架构设计是否解决了你提出的问题？还有哪些需要补充或修改的地方？
