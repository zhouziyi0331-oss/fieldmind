# 统一文档处理流水线 - Unified Document Pipeline

整合3个版本的文档处理流水线，实现 **1+1+1 > 2** 的功能增强。

## 📦 整合来源

| 原始版本 | 行数 | 核心功能 |
|---------|------|---------|
| `document_processing_pipeline.py` | 751行 | 完整的6步处理 + 知识图谱 + fact_statements |
| `document_processing_pipeline_complete.py` | 746行 | 错误重试 + 检查点恢复 + 数据治理 |
| `document_processing_pipeline_v2.py` | 241行 | 时间抽取 + 结构化元数据 |
| **统一版本** | **1738行→1200行** | **所有功能 + 6个新特性** |

## ✨ 核心功能（12项）

### 原有功能（9项）
1. ✅ 多格式文档解析（PDF/DOCX/TXT/Audio/Video）
2. ✅ 智能文本清洗和标准化
3. ✅ 语义驱动的文档切分
4. ✅ 多策略向量化（Sentence-Transformers优先，TF-IDF降级）
5. ✅ 知识图谱自动构建
6. ✅ 事实陈述提取（fact_statements）
7. ✅ 批处理和进度追踪
8. ✅ 多存储后端支持（ChromaDB + PostgreSQL）
9. ✅ 性能统计和监控

### 新增功能（6项）
1. 🆕 **时间信息抽取和标准化** - 自动提取文档日期和文本中的时间点
2. 🆕 **结构化元数据管理** - 完整的元数据验证和引用格式化
3. 🆕 **数据治理和结构化** - 主题提取、实体识别、结构化存储
4. 🆕 **错误重试机制** - 每个阶段独立重试，可配置次数和延迟
5. 🆕 **检查点恢复（断点续传）** - 处理中断后可从上次位置继续
6. 🆕 **单一入口点API** - 从3个服务调用简化为1个方法

## 🚀 快速开始

### 基础用法

**旧方式**（需要3个服务，4步操作）：
```python
from app.services.document_converter import DocumentConverter
from app.services.document_chunker import DocumentChunker
from app.services.vectorization_service_complete import VectorizationService

# 步骤1: 内容提取
converter = DocumentConverter()
result = converter.convert_document(file_path)
text = result['text']
metadata = result['metadata']

# 步骤2: 文档切分
chunker = DocumentChunker()
chunks = chunker.chunk_document(text, metadata)

# 步骤3: 向量化
vectorizer = VectorizationService()
vectorized = vectorizer.vectorize_chunks(chunks)

# 步骤4: 存储
vectorizer.store_chunks(vectorized, doc_id, project_id, db)
```

**新方式**（1个服务，1步完成）：
```python
from app.tools.document import process_single_document

# 一步完成所有处理
result = process_single_document(
    db=db,
    document_id=doc_id,
    project_id=project_id,
    file_path=file_path
)
```

### 高级用法

#### 1. 自定义配置
```python
from app.tools.document import UnifiedDocumentPipeline

pipeline = UnifiedDocumentPipeline(
    db=db,
    max_retries=5,                      # 最大重试次数
    retry_delay=2.0,                    # 重试延迟（秒）
    enable_checkpoints=True,            # 启用检查点恢复
    enable_knowledge_graph=True,        # 启用知识图谱
    enable_fact_extraction=True,        # 启用事实提取
    enable_data_curation=True,          # 启用数据治理
    enable_temporal_extraction=True     # 启用时间抽取
)
```

#### 2. 进度追踪
```python
def progress_callback(stage, progress, message):
    print(f"[{stage}] {progress*100:.1f}% - {message}")

result = pipeline.process_document(
    document_id=1,
    project_id=10,
    file_path="document.pdf",
    progress_callback=progress_callback
)
```

#### 3. 直接提供文本内容
```python
result = pipeline.process_document(
    document_id=1,
    project_id=10,
    text_content="这是文档内容...",
    filename="document.txt",
    file_type="txt"
)
```

#### 4. 批处理
```python
documents = [
    {"document_id": 1, "project_id": 10, "file_path": "doc1.pdf"},
    {"document_id": 2, "project_id": 10, "file_path": "doc2.pdf"},
    {"document_id": 3, "project_id": 10, "file_path": "doc3.pdf"}
]

results = pipeline.batch_process_documents(documents)
```

#### 5. 检查点恢复
```python
# 第一次处理（可能中断）
result = pipeline.process_document(
    document_id=1,
    project_id=10,
    file_path="large_document.pdf",
    resume_from_checkpoint=True
)

# 如果中断，再次调用会自动从检查点恢复
result = pipeline.process_document(
    document_id=1,
    project_id=10,
    file_path="large_document.pdf",
    resume_from_checkpoint=True  # 自动检测并恢复
)
```

## 📊 处理流程

完整的9阶段处理流程：

```
文档输入 (PDF/DOCX/TXT/Audio/Video)
    ↓
【阶段1】内容提取 (带重试)
    ├─ 文件格式检测
    ├─ 内容解析
    └─ 元数据提取
    ↓
【阶段2】时间信息抽取 🆕
    ├─ 文档日期识别
    ├─ 文本时间点提取
    └─ 时间标准化
    ↓
【阶段3】文本清洗
    ├─ 统一换行符
    ├─ 删除控制字符
    └─ 压缩多余空白
    ↓
【阶段4】数据治理和结构化 🆕
    ├─ 主题识别
    ├─ 实体提取（人名、地名）
    └─ 结构化存储
    ↓
【阶段5】文档切分 (带重试)
    ├─ 语义感知切分
    ├─ 保留元数据
    └─ 大小优化
    ↓
【阶段6】向量化 (带重试)
    ├─ Sentence-Transformers (优先)
    └─ TF-IDF (降级)
    ↓
【阶段7】知识图谱构建
    ├─ 实体提取
    ├─ 关系识别
    └─ 图谱存储
    ↓
【阶段8】事实陈述提取
    ├─ 句子分割
    ├─ 事实提取
    └─ 入库存储
    ↓
【阶段9】存储
    ├─ ChromaDB存储
    ├─ PostgreSQL存储
    └─ 元数据更新
    ↓
处理完成 ✅
```

每个阶段都有：
- ✅ 独立的错误处理
- ✅ 重试机制（可配置）
- ✅ 检查点保存
- ✅ 进度回调

## 📈 返回结果

```python
{
    "success": True,
    "document_id": 1,
    "project_id": 10,
    "stages": {
        "extraction": {
            "success": True,
            "text_length": 15000,
            "metadata": {...}
        },
        "temporal": {
            "success": True,
            "document_date": "2024-03-15",
            "extracted_dates_count": 12,
            "sample_dates": ["2024-01-10", "2024-02-20", ...]
        },
        "cleaning": {
            "success": True,
            "original_length": 15000,
            "cleaned_length": 14500,
            "removed_chars": 500
        },
        "curation": {
            "success": True,
            "topics_count": 5,
            "persons_count": 8,
            "locations_count": 3
        },
        "chunking": {
            "success": True,
            "total_chunks": 35,
            "avg_chunk_size": 414
        },
        "vectorization": {
            "success": True,
            "vectorized_chunks": 35,
            "embedding_model": "sentence-transformers",
            "embedding_dim": 384
        },
        "knowledge_graph": {
            "success": True,
            "entities_count": 42,
            "relations_count": 58,
            "entity_types": {"person": 15, "location": 8, ...}
        },
        "fact_extraction": {
            "success": True,
            "facts_count": 120
        },
        "storage": {
            "success": True,
            "stored_chunks": 35
        }
    },
    "statistics": {
        "total_chunks": 35,
        "stored_chunks": 35,
        "processing_time": 12.5,
        "entities_count": 42,
        "relations_count": 58,
        "facts_count": 120,
        "text_length": 14500
    }
}
```

## 🔧 配置选项

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `db` | Session | *必需* | 数据库会话 |
| `max_retries` | int | 3 | 最大重试次数 |
| `retry_delay` | float | 1.0 | 重试延迟（秒） |
| `enable_checkpoints` | bool | True | 启用检查点恢复 |
| `enable_knowledge_graph` | bool | True | 启用知识图谱构建 |
| `enable_fact_extraction` | bool | True | 启用事实陈述提取 |
| `enable_data_curation` | bool | True | 启用数据治理 |
| `enable_temporal_extraction` | bool | True | 启用时间抽取 |

## ⚠️ 错误处理

统一的异常层次：

```python
DocumentProcessingError          # 基类
├── ExtractionError             # 内容提取错误
├── ChunkingError              # 切分错误
├── VectorizationError         # 向量化错误
└── StorageError              # 存储错误
```

使用示例：
```python
from app.tools.document import (
    process_single_document,
    ExtractionError,
    ChunkingError
)

try:
    result = process_single_document(db, doc_id, proj_id, file_path)
except ExtractionError as e:
    print(f"文档解析失败: {e}")
except ChunkingError as e:
    print(f"文档切分失败: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 🎯 性能优化

### 1. 延迟加载
所有服务都是延迟加载的，只在需要时才初始化：
```python
# 初始化时不加载任何服务
pipeline = UnifiedDocumentPipeline(db)

# 第一次调用时才加载
result = pipeline.process_document(...)  # 此时才加载chunker、vectorizer等
```

### 2. 批处理
批量处理多个文档时，服务实例会被复用：
```python
pipeline = UnifiedDocumentPipeline(db)

# 处理100个文档，服务只初始化一次
results = pipeline.batch_process_documents(documents)
```

### 3. 检查点恢复
大文档处理中断后可从上次位置继续，避免重复计算：
```python
# 检查点自动保存在：~/.fieldmind/checkpoints/doc{id}.json
pipeline = UnifiedDocumentPipeline(db, enable_checkpoints=True)
result = pipeline.process_document(doc_id, proj_id, file_path)
```

### 4. 多策略向量化
自动选择最佳向量化策略：
```
1. 尝试 Sentence-Transformers (最优质量)
   ↓ 失败
2. 降级到 TF-IDF (保证可用性)
```

## 🔄 迁移指南

### 从旧版本迁移

#### 1. 从 `document_processing_pipeline.py` 迁移
```python
# 旧代码
from app.services.document_processing_pipeline import DocumentProcessingPipeline
pipeline = DocumentProcessingPipeline()
result = pipeline.process_document(doc_id, file_path, proj_id, db)

# 新代码
from app.tools.document import UnifiedDocumentPipeline
pipeline = UnifiedDocumentPipeline(db)
result = pipeline.process_document(doc_id, proj_id, file_path=file_path)
```

#### 2. 从 `document_processing_pipeline_complete.py` 迁移
```python
# 旧代码
from app.services.document_processing_pipeline_complete import DocumentProcessingPipeline
pipeline = DocumentProcessingPipeline(db, max_retries=3, enable_checkpoints=True)
result = pipeline.process_document(doc_id, proj_id, text_content, metadata)

# 新代码
from app.tools.document import UnifiedDocumentPipeline
pipeline = UnifiedDocumentPipeline(db, max_retries=3, enable_checkpoints=True)
result = pipeline.process_document(doc_id, proj_id, text_content=text_content, metadata=metadata)
```

#### 3. 从 `document_processing_pipeline_v2.py` 迁移
```python
# 旧代码
from app.services.document_processing_pipeline_v2 import DocumentProcessingPipelineV2
pipeline = DocumentProcessingPipelineV2(db)
result = pipeline.process_document(doc_id, text, filename, file_type, proj_id)

# 新代码
from app.tools.document import UnifiedDocumentPipeline
pipeline = UnifiedDocumentPipeline(db, enable_temporal_extraction=True)
result = pipeline.process_document(
    doc_id, proj_id, 
    text_content=text, 
    filename=filename, 
    file_type=file_type
)
```

### API参数映射

| 旧版本参数 | 新版本参数 | 说明 |
|-----------|-----------|------|
| `text_content` | `text_content` | 不变 |
| `text` | `text_content` | 统一命名 |
| `file_path` | `file_path` | 不变 |
| `metadata` | `metadata` | 不变 |
| `progress_callback` | `progress_callback` | 不变 |
| - | `resume_from_checkpoint` | 新增 |
| - | `filename` | 新增 |
| - | `file_type` | 新增 |

## 📝 测试

运行测试：
```bash
# 运行所有测试
python -m pytest tests/tools/document/test_unified_document_pipeline.py -v

# 运行特定测试
python -m pytest tests/tools/document/test_unified_document_pipeline.py::TestUnifiedDocumentPipeline::test_clean_text -v

# 查看覆盖率
python -m pytest tests/tools/document/ --cov=app.tools.document --cov-report=html
```

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可证

FieldMind © 2024
