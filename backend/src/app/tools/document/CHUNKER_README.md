# 统一文档分块器使用指南

## 概述

`UnifiedDocumentChunker` 整合了 v1 和 v2 两个版本的文档分块器，提供统一、强大的文档切分功能。

### 核心特性

✅ **双模式输出** - 支持Dict模式（v1兼容）和强类型ChunkMetadata模式（v2兼容）  
✅ **完整时间戳支持** - 音频/视频时间戳自动映射到chunks  
✅ **智能overlap策略** - 真正实现chunk间重叠，保持上下文连贯  
✅ **分块质量评分** - 0-100分评分系统，4个质量等级  
✅ **多种分块策略** - 语义边界、固定大小、句子级、滑动窗口

---

## 快速开始

### 1. 基础使用（推荐）

```python
from app.tools.document import chunk_document

# 最简单的调用
chunks = chunk_document("这是一段很长的文本...")

# 每个chunk是一个Dict：
# {
#     "chunk_id": "chunk_0001",
#     "text": "...",
#     "chunk_index": 1,
#     "total_chunks": 5,
#     "prev_chunk_id": "chunk_0000",
#     "next_chunk_id": "chunk_0002",
#     "metadata": {
#         "start_pos": 0,
#         "end_pos": 350,
#         "paragraph_index": 0,
#         "chunk_type": "semantic",
#         "quality_score": 85.5,
#         "quality_level": "good"
#     }
# }
```

### 2. 自定义参数

```python
chunks = chunk_document(
    text="长文本...",
    metadata={"doc_id": "123", "author": "Alice"},
    strategy="semantic",  # semantic/fixed/sentence/sliding
    min_size=200,
    max_size=500,
    enable_overlap=True,
    overlap_size=50
)
```

### 3. 使用分块器对象（高级）

```python
from app.tools.document import UnifiedDocumentChunker, ChunkStrategy

# 创建分块器实例
chunker = UnifiedDocumentChunker(
    strategy=ChunkStrategy.SEMANTIC,
    min_chunk_size=200,
    max_chunk_size=500,
    target_chunk_size=350,
    overlap_size=50,
    enable_overlap=True,
    enable_quality_scoring=True
)

# 分块
chunks = chunker.chunk_document(text, output_mode="dict")
```

---

## 四种分块策略

### 1. Semantic（语义边界）- 默认推荐

按段落和句子边界智能切分，保持语义完整性。

```python
from app.tools.document import create_chunker, ChunkStrategy

chunker = create_chunker(strategy=ChunkStrategy.SEMANTIC)
chunks = chunker.chunk_document(text, output_mode="dict")
```

**适用场景**：
- 📄 普通文档（文章、报告、书籍）
- 💬 对话文本（保持对话完整）
- 📝 结构化内容（有明确段落）

**优点**：
- ✅ 保持语义完整性
- ✅ 尊重自然边界
- ✅ 质量评分最高

### 2. Fixed（固定大小）

按目标大小硬切，不考虑语义边界。

```python
chunker = create_chunker(
    strategy=ChunkStrategy.FIXED,
    target_chunk_size=300
)
chunks = chunker.chunk_document(text, output_mode="dict")
```

**适用场景**：
- 🔢 向量数据库存储（需要统一长度）
- 📊 批量处理（需要可预测的chunk数量）
- ⚡ 高性能要求（最快）

**优点**：
- ✅ 速度最快
- ✅ Chunk大小可预测
- ✅ 简单可靠

### 3. Sentence（句子级）

每个chunk是完整句子的集合。

```python
chunker = create_chunker(
    strategy=ChunkStrategy.SENTENCE,
    max_chunk_size=400
)
chunks = chunker.chunk_document(text, output_mode="dict")
```

**适用场景**：
- 📰 新闻文章
- 📖 小说、故事
- 🗣️ 演讲稿

**优点**：
- ✅ 句子完整性
- ✅ 易于阅读
- ✅ 适合引用

### 4. Sliding（滑动窗口）

固定窗口大小，固定步长滑动。

```python
chunker = create_chunker(
    strategy=ChunkStrategy.SLIDING,
    target_chunk_size=300,
    overlap_size=50  # 窗口重叠50字符
)
chunks = chunker.chunk_document(text, output_mode="dict")
```

**适用场景**：
- 🔍 信息检索（增加召回率）
- 🧠 RAG系统（减少边界信息丢失）
- 📚 密集文本分析

**优点**：
- ✅ 保证信息覆盖
- ✅ 减少边界损失
- ✅ 提高检索召回率

---

## 音频/视频时间戳映射

自动将Whisper转录的时间戳映射到chunks。

```python
# Whisper转录结果
transcript = [
    {"text": "这是第一段内容。", "start": 0.0, "end": 2.5},
    {"text": "这是第二段内容。", "start": 2.5, "end": 5.0},
    {"text": "这是第三段内容。", "start": 5.0, "end": 7.8},
]

# 分块时传入transcript
chunks = chunk_document(
    text="这是第一段内容。这是第二段内容。这是第三段内容。",
    metadata={"transcript": transcript}
)

# 结果：每个chunk自动带有时间戳
for chunk in chunks:
    print(f"Chunk {chunk['chunk_id']}: "
          f"{chunk['metadata']['start_sec']:.2f}s - "
          f"{chunk['metadata']['end_sec']:.2f}s")

# 输出：
# Chunk chunk_0000: 0.00s - 2.50s
# Chunk chunk_0001: 2.50s - 5.00s
# Chunk chunk_0002: 5.00s - 7.80s
```

**应用场景**：
- 🎵 音频内容检索
- 🎬 视频字幕对齐
- 📻 播客时间轴生成

---

## Overlap功能（智能重叠）

在chunk之间添加重叠部分，保持上下文连贯。

```python
chunker = UnifiedDocumentChunker(
    max_chunk_size=300,
    overlap_size=50,
    enable_overlap=True  # 启用overlap
)

chunks = chunker.chunk_document(text, output_mode="dict")

# 检查overlap
for chunk in chunks:
    if chunk['metadata'].get('has_overlap'):
        overlap_size = chunk['metadata']['overlap_size']
        print(f"Chunk {chunk['chunk_id']} 有 {overlap_size} 字符的overlap")
```

**效果**：
```
Chunk 0: [0-300]
Chunk 1: [250-550]  ← 前50字符与Chunk 0重叠
Chunk 2: [500-800]  ← 前50字符与Chunk 1重叠
```

**好处**：
- ✅ 避免关键信息被边界切断
- ✅ 提高RAG检索质量
- ✅ 保持上下文连贯性

---

## 质量评分系统

自动评估每个chunk的质量（0-100分）。

### 评分维度

1. **大小合理性** (30分) - 在目标范围内得高分
2. **语义完整性** (40分) - 完整段落/句子得高分
3. **边界清晰度** (20分) - 在自然边界得高分
4. **文本密度** (10分) - 非空白字符占比

### 质量等级

| 等级 | 分数 | 说明 |
|------|------|------|
| EXCELLENT | 90-100 | 完整段落，边界清晰 |
| GOOD | 70-89 | 句子完整，语义连贯 |
| FAIR | 50-69 | 有断句，但可用 |
| POOR | <50 | 强制切分，语义不完整 |

### 使用示例

```python
chunker = UnifiedDocumentChunker(enable_quality_scoring=True)
chunks = chunker.chunk_document(text, output_mode="dict")

# 查看质量
for chunk in chunks:
    score = chunk['metadata']['quality_score']
    level = chunk['metadata']['quality_level']
    print(f"Chunk {chunk['chunk_id']}: {score:.1f}分 ({level})")

# 输出：
# Chunk chunk_0000: 92.5分 (excellent)
# Chunk chunk_0001: 78.3分 (good)
# Chunk chunk_0002: 45.2分 (poor)

# 过滤低质量chunks
good_chunks = [c for c in chunks 
               if c['metadata']['quality_score'] >= 70]
```

---

## 批量处理

高效处理多个文档。

```python
from app.tools.document import batch_chunk_documents

documents = [
    {"text": "文档1的内容...", "metadata": {"doc_id": 1}},
    {"text": "文档2的内容...", "metadata": {"doc_id": 2}},
    {"text": "文档3的内容...", "metadata": {"doc_id": 3}},
]

# 批量分块
results = batch_chunk_documents(documents, strategy="semantic")

# results是一个二维列表
for i, chunks in enumerate(results):
    print(f"文档 {i+1}: {len(chunks)} 个chunks")
```

### 带进度回调

```python
chunker = UnifiedDocumentChunker()

def on_progress(current, total):
    print(f"处理进度: {current}/{total}")

results = chunker.batch_chunk_documents(
    documents,
    progress_callback=on_progress
)
```

---

## 输出模式

### 1. Dict模式（默认，v1兼容）

```python
chunks = chunker.chunk_document(text, output_mode="dict")
# 返回: List[Dict[str, Any]]

chunk = chunks[0]
print(chunk["chunk_id"])
print(chunk["text"])
print(chunk["metadata"]["quality_score"])
```

### 2. ChunkResult模式（强类型）

```python
chunks = chunker.chunk_document(text, output_mode="result")
# 返回: List[ChunkResult]

chunk = chunks[0]
print(chunk.chunk_id)
print(chunk.text)
print(chunk.quality_score)
print(chunk.quality_level)  # ChunkQuality枚举
```

### 3. ChunkMetadata模式（v2兼容）

```python
from app.schemas.document_metadata import DocumentMetadata

# 需要提供DocumentMetadata对象
doc_meta = DocumentMetadata(
    document_id="doc123",
    source_file="report.pdf",
    document_type=DocumentType.PDF,
    source_level=SourceLevel.PRIMARY,
    # ... 其他字段
)

chunks = chunker.chunk_document(
    text,
    document_metadata=doc_meta,
    output_mode="metadata"
)
# 返回: List[ChunkMetadata]

# 每个chunk继承了完整的父文档元数据
chunk = chunks[0]
print(chunk.document_id)  # "doc123"
print(chunk.source_file)  # "report.pdf"
print(chunk.chunk_index)
```

---

## 工具函数

### 1. Chunk预览

```python
chunker = UnifiedDocumentChunker()
chunks = chunker.chunk_document(long_text, output_mode="result")

# 获取前3个chunk的预览
previews = chunker.get_chunk_preview(chunks, preview_count=3, preview_length=100)

for preview in previews:
    print(f"{preview['chunk_id']}: {preview['preview']}")
    print(f"  长度: {preview['length']}, 位置: {preview['position']}")
```

### 2. 分块统计

```python
stats = chunker.get_chunking_stats(chunks)

print(f"总chunks数: {stats['total_chunks']}")
print(f"平均大小: {stats['avg_chunk_size']:.0f} 字符")
print(f"最小大小: {stats['min_chunk_size']} 字符")
print(f"最大大小: {stats['max_chunk_size']} 字符")
print(f"平均质量: {stats['avg_quality_score']:.1f} 分")
print(f"质量分布: {stats['quality_distribution']}")

# 输出示例：
# 总chunks数: 12
# 平均大小: 325 字符
# 最小大小: 180 字符
# 最大大小: 480 字符
# 平均质量: 82.3 分
# 质量分布: {'excellent': 4, 'good': 6, 'fair': 2}
```

---

## 最佳实践

### 1. 选择合适的策略

| 场景 | 推荐策略 | 原因 |
|------|---------|------|
| 通用文档处理 | Semantic | 保持语义完整 |
| 向量数据库 | Fixed | 统一长度 |
| RAG检索 | Sliding | 提高召回 |
| 内容引用 | Sentence | 保持句子完整 |

### 2. 参数调优

```python
# 短文档（博客、新闻）
chunker = UnifiedDocumentChunker(
    min_chunk_size=150,
    max_chunk_size=300,
    target_chunk_size=225
)

# 长文档（书籍、论文）
chunker = UnifiedDocumentChunker(
    min_chunk_size=300,
    max_chunk_size=600,
    target_chunk_size=450
)

# RAG系统（需要overlap）
chunker = UnifiedDocumentChunker(
    max_chunk_size=400,
    overlap_size=100,
    enable_overlap=True
)
```

### 3. 质量控制

```python
# 过滤低质量chunks
chunks = chunker.chunk_document(text, output_mode="dict")
high_quality = [c for c in chunks 
                if c['metadata']['quality_score'] >= 70]

# 或者：标记低质量chunks
for chunk in chunks:
    if chunk['metadata']['quality_score'] < 50:
        chunk['metadata']['needs_review'] = True
```

### 4. 性能优化

```python
# 对于大批量文档
chunker = UnifiedDocumentChunker(
    enable_quality_scoring=False,  # 禁用质量评分加速
    max_chunks_limit=100  # 限制最大chunk数
)

# 使用批量处理
results = chunker.batch_chunk_documents(documents)
```

---

## 迁移指南

### 从v1迁移

```python
# 旧代码 (v1)
from app.services.document_chunker import DocumentChunker

chunker = DocumentChunker(min_chunk_size=200, max_chunk_size=500)
chunks = chunker.chunk_document(text, metadata)

# 新代码 (Unified)
from app.tools.document import create_chunker

chunker = create_chunker(min_chunk_size=200, max_chunk_size=500)
chunks = chunker.chunk_document(text, metadata, output_mode="dict")
# 返回格式完全兼容v1
```

### 从v2迁移

```python
# 旧代码 (v2)
from app.services.document_chunker_v2 import DocumentChunkerV2
from app.schemas.document_metadata import DocumentMetadata

chunker = DocumentChunkerV2()
chunks = chunker.chunk_document(text, document_metadata)
# 返回: List[ChunkMetadata]

# 新代码 (Unified)
from app.tools.document import UnifiedDocumentChunker

chunker = UnifiedDocumentChunker()
chunks = chunker.chunk_document(
    text,
    document_metadata=document_metadata,
    output_mode="metadata"
)
# 返回格式完全兼容v2
```

---

## API参考

### UnifiedDocumentChunker

```python
class UnifiedDocumentChunker:
    def __init__(
        self,
        strategy: ChunkStrategy = ChunkStrategy.SEMANTIC,
        min_chunk_size: int = 200,
        max_chunk_size: int = 500,
        target_chunk_size: int = 350,
        overlap_size: int = 50,
        enable_overlap: bool = False,
        enable_quality_scoring: bool = True,
        max_chunks_limit: int = 500
    )
    
    def chunk_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_metadata: Optional[Any] = None,
        output_mode: str = "dict",
        progress_callback: Optional[Callable] = None
    ) -> Union[List[Dict], List[ChunkResult], List[ChunkMetadata]]
    
    def batch_chunk_documents(
        self,
        documents: List[Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ) -> List[List[Dict[str, Any]]]
    
    def get_chunk_preview(
        self,
        chunks: List[Union[Dict, ChunkResult]],
        preview_count: int = 3,
        preview_length: int = 100
    ) -> List[Dict[str, Any]]
    
    def get_chunking_stats(
        self,
        chunks: List[Union[Dict, ChunkResult]]
    ) -> Dict[str, Any]
```

### 便捷函数

```python
def create_chunker(
    strategy: Union[str, ChunkStrategy] = ChunkStrategy.SEMANTIC,
    **kwargs
) -> UnifiedDocumentChunker

def chunk_document(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    strategy: str = "semantic",
    min_size: int = 200,
    max_size: int = 500,
    enable_overlap: bool = False,
    overlap_size: int = 50
) -> List[Dict[str, Any]]

def batch_chunk_documents(
    documents: List[Dict[str, Any]],
    strategy: str = "semantic",
    **kwargs
) -> List[List[Dict[str, Any]]]
```

---

## 常见问题

### 1. 如何选择chunk大小？

```python
# 一般规则：
# - 向量数据库: 200-500字符
# - RAG系统: 300-600字符
# - 搜索引擎: 150-300字符
# - 摘要生成: 500-1000字符

# 考虑因素：
# 1. 模型上下文窗口（如GPT-4: 8K tokens）
# 2. 嵌入模型限制（如OpenAI: 8191 tokens）
# 3. 语义完整性需求
# 4. 检索性能要求
```

### 2. Overlap会让chunk数量翻倍吗？

不会。Overlap只是在chunk的开头添加上一个chunk的结尾部分，不会产生新的chunk。

### 3. 质量评分为什么重要？

质量评分帮助你：
- 识别强制切分的低质量chunks
- 优化chunk参数配置
- 过滤不适合处理的chunks
- 监控分块质量趋势

### 4. 如何处理超长文档？

```python
# 方法1：增加max_chunk_size
chunker = UnifiedDocumentChunker(max_chunk_size=1000)

# 方法2：使用滑动窗口
chunker = UnifiedDocumentChunker(
    strategy=ChunkStrategy.SLIDING,
    target_chunk_size=500
)

# 方法3：设置chunk数量限制
chunker = UnifiedDocumentChunker(max_chunks_limit=200)
# 超过200个chunk会自动合并
```

### 5. 时间戳映射失败怎么办？

```python
# 时间戳映射需要：
# 1. transcript格式正确
# 2. transcript的text能在原文中找到
# 3. transcript按时间顺序排列

# 检查映射结果
chunks = chunker.chunk_document(text, metadata={"transcript": transcript})
mapped = [c for c in chunks if c['metadata'].get('start_sec') is not None]
print(f"成功映射: {len(mapped)}/{len(chunks)} 个chunks")
```

---

## 更新日志

### v1.0.0 (统一版本)

**新增功能**：
- ✅ 5个新功能：双模式输出、完整时间戳、智能overlap、质量评分、多策略
- ✅ 4种分块策略：semantic、fixed、sentence、sliding
- ✅ 质量评分系统（0-100分，4等级）
- ✅ 真正的overlap实现
- ✅ 批量处理支持

**整合内容**：
- ✅ v1的音频时间戳映射
- ✅ v1的chunk预览功能
- ✅ v2的元数据完整继承
- ✅ v2的ChunkMetadata输出

**测试覆盖**：
- ✅ 31个测试用例，100%通过

---

## 联系与支持

遇到问题或有建议？
- 📧 提交Issue到项目仓库
- 📖 查看项目文档
- 💬 加入开发者讨论组
