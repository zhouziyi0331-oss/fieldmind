# 统一向量化引擎使用指南

## 📚 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [API参考](#api参考)
4. [使用示例](#使用示例)
5. [最佳实践](#最佳实践)
6. [迁移指南](#迁移指南)
7. [性能优化](#性能优化)
8. [故障排查](#故障排查)

---

## 🚀 快速开始

### 最简单的用法

```python
from app.tools.vectorization import create_engine, VectorEngine

# 创建引擎（零配置，自动使用TF-IDF）
engine = create_engine()

# 编码查询
query_vec = engine.encode_query("田野调查方法")

# 编码文档
doc_vecs = engine.encode_documents([
    "费孝通先生在江村进行了深入的田野调查",
    "十八洞村是精准扶贫的典型案例"
])

# 向量化并存储
chunks = [
    {"chunk_id": "c1", "text": "费孝通的江村经济", "document_id": "doc1", "chunk_index": 0},
    {"chunk_id": "c2", "text": "精准扶贫政策", "document_id": "doc2", "chunk_index": 0},
]
engine.vectorize_and_store(chunks)

# 语义检索
results = engine.search_similar("田野调查", top_k=5)
for result in results:
    print(f"[{result.score:.3f}] {result.chunk.text}")
```

---

## 🧠 核心概念

### 1. 向量化引擎 (VectorEngine)

| 引擎 | 维度 | 模型大小 | 准确率 | 速度 | 离线 | 适用场景 |
|------|------|----------|--------|------|------|----------|
| **BGE_LARGE** | 1024 | 326MB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ | 生产环境，最高精度 |
| **BGE_SMALL** | 512 | 102MB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | 平衡方案（推荐） |
| **MINILM** | 384 | 80MB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | Mac本地，快速检索 |
| **TFIDF** | 384 | 0MB | ⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | 零依赖，关键词匹配 |

### 2. 存储后端 (StorageBackend)

| 后端 | 持久化 | 语义检索 | SQL查询 | 元数据 | 适用场景 |
|------|--------|----------|---------|--------|----------|
| **MEMORY** | ❌ | ✅ | ❌ | ✅ | 测试、临时计算 |
| **SQL_ONLY** | ✅ | ❌ | ✅ | ✅ | 结构化数据管理 |
| **CHROMADB_ONLY** | ✅ | ✅ | ❌ | ✅ | 纯语义检索 |
| **DUAL** | ✅ | ✅ | ✅ | ✅ | 生产环境（推荐） |

### 3. 数据类

#### VectorizedChunk
```python
@dataclass
class VectorizedChunk:
    chunk_id: str              # 唯一标识
    text: str                  # 原始文本
    embedding: List[float]     # 向量 (维度取决于引擎)
    dimension: int             # 向量维度
    model: str                 # 模型名称
    document_id: str           # 所属文档ID
    chunk_index: int           # 在文档中的索引
    metadata: Dict[str, Any]   # 自定义元数据
    vectorized_at: datetime    # 向量化时间
```

#### SearchResult
```python
@dataclass
class SearchResult:
    chunk: VectorizedChunk     # 匹配的文本块
    score: float               # 相似度分数 [0, 1]
    rank: int                  # 排名 (1-based)
```

---

## 📖 API参考

### 主类: UnifiedVectorizationEngine

#### 初始化

```python
engine = UnifiedVectorizationEngine(
    engine: VectorEngine = VectorEngine.BGE_SMALL,
    storage: StorageBackend = StorageBackend.MEMORY,
    optimize_query: bool = True,        # BGE查询优化
    auto_fallback: bool = True,         # 自动降级
)
```

#### 编码接口

##### encode_query()
```python
def encode_query(
    self,
    query: str,
    normalize: bool = True
) -> np.ndarray:
    """
    编码查询文本
    
    参数:
        query: 查询文本
        normalize: 是否归一化向量
    
    返回:
        查询向量 (dimension,)
    
    示例:
        >>> engine.encode_query("田野调查")
        array([0.123, -0.456, ...])  # 长度=dimension
    """
```

##### encode_documents()
```python
def encode_documents(
    self,
    texts: List[str],
    batch_size: int = 32,
    normalize: bool = True,
    show_progress: bool = False
) -> np.ndarray:
    """
    批量编码文档
    
    参数:
        texts: 文档文本列表
        batch_size: 批处理大小
        normalize: 是否归一化
        show_progress: 是否显示进度条
    
    返回:
        文档向量矩阵 (n_texts, dimension)
    
    示例:
        >>> engine.encode_documents(["文本1", "文本2"])
        array([[0.1, 0.2, ...],
               [0.3, 0.4, ...]])
    """
```

#### 存储接口

##### vectorize_and_store()
```python
def vectorize_and_store(
    self,
    chunks: List[Dict[str, Any]],
    project_id: int = None,
    db: Session = None,
    collection_name: str = "fieldmind",
    output_mode: str = "dataclass"
) -> List[Union[VectorizedChunk, Dict[str, Any]]]:
    """
    向量化并存储文本块
    
    参数:
        chunks: 文本块列表，每个包含:
            - text: 文本内容 (必需)
            - document_id: 文档ID (必需)
            - chunk_index: 索引 (必需)
            - chunk_id: 唯一ID (可选)
            - metadata: 元数据 (可选)
        project_id: 项目ID (SQL存储需要)
        db: 数据库会话 (SQL存储需要)
        collection_name: ChromaDB集合名称
        output_mode: "dataclass" 或 "dict"
    
    返回:
        向量化后的文本块列表
    
    示例:
        >>> chunks = [
        ...     {"text": "内容1", "document_id": "doc1", "chunk_index": 0},
        ...     {"text": "内容2", "document_id": "doc1", "chunk_index": 1},
        ... ]
        >>> results = engine.vectorize_and_store(chunks)
    """
```

#### 检索接口

##### search_similar()
```python
def search_similar(
    self,
    query: str,
    top_k: int = 10,
    filters: Dict[str, Any] = None,
    threshold: float = 0.0,
    collection_name: str = "fieldmind",
    output_mode: str = "dataclass"
) -> List[Union[SearchResult, Dict[str, Any]]]:
    """
    语义检索
    
    参数:
        query: 查询文本
        top_k: 返回结果数量
        filters: 过滤条件 (如 {"document_id": "123"})
        threshold: 最小相似度阈值 [0, 1]
        collection_name: ChromaDB集合名称
        output_mode: "dataclass" 或 "dict"
    
    返回:
        检索结果列表 (按相似度降序)
    
    示例:
        >>> results = engine.search_similar(
        ...     query="田野调查方法",
        ...     top_k=5,
        ...     threshold=0.5
        ... )
        >>> for result in results:
        ...     print(f"[{result.score:.3f}] {result.chunk.text}")
    """
```

#### 管理接口

##### delete_by_document()
```python
def delete_by_document(
    self,
    document_id: str,
    db: Session = None,
    collection_name: str = "fieldmind"
) -> bool:
    """删除文档的所有向量"""
```

##### get_statistics()
```python
def get_statistics(
    self,
    project_id: int = None,
    db: Session = None,
    collection_name: str = "fieldmind"
) -> VectorStatistics:
    """获取统计信息"""
```

---

## 💡 使用示例

### 示例1: 基础向量化和检索

```python
from app.tools.vectorization import create_engine, VectorEngine, StorageBackend

# 创建引擎
engine = create_engine(
    engine=VectorEngine.TFIDF,
    storage=StorageBackend.MEMORY
)

# 准备数据
chunks = [
    {
        "chunk_id": "c1",
        "text": "费孝通先生在江村进行了深入的田野调查",
        "document_id": "doc1",
        "chunk_index": 0,
        "metadata": {"author": "费孝通"}
    },
    {
        "chunk_id": "c2",
        "text": "十八洞村是精准扶贫的典型案例",
        "document_id": "doc2",
        "chunk_index": 0,
        "metadata": {"location": "湖南"}
    },
]

# 向量化并存储
vectorized = engine.vectorize_and_store(chunks)
print(f"✅ 向量化完成: {len(vectorized)} 个chunks")

# 语义检索
results = engine.search_similar("田野调查", top_k=3)
print(f"\n🔍 检索结果:")
for result in results:
    print(f"  [{result.rank}] 相似度={result.score:.3f}")
    print(f"      {result.chunk.text}")
```

### 示例2: 使用BGE模型（高精度）

```python
from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend

# 生产环境推荐配置
engine = UnifiedVectorizationEngine(
    engine=VectorEngine.BGE_SMALL,      # 平衡方案
    storage=StorageBackend.DUAL,        # SQL + ChromaDB双写
    optimize_query=True,                 # 查询优化
    auto_fallback=True                   # 自动降级
)

# 使用方式同上
```

### 示例3: 批量处理大量文档

```python
from app.tools.vectorization import create_engine

engine = create_engine()

# 大批量文档
large_batch = []
for doc_id in range(100):
    for chunk_idx in range(50):
        large_batch.append({
            "chunk_id": f"doc{doc_id}_c{chunk_idx}",
            "text": f"文档{doc_id}的第{chunk_idx}段内容...",
            "document_id": f"doc{doc_id}",
            "chunk_index": chunk_idx,
        })

# 批量向量化（自动分批，显示进度）
print("开始向量化5000个chunks...")
results = engine.vectorize_and_store(large_batch)
print(f"✅ 完成: {len(results)} 个chunks")

# 统计信息
stats = engine.get_statistics()
print(f"\n📊 统计:")
print(f"  总chunks: {stats.total_chunks}")
print(f"  总文档: {stats.total_documents}")
print(f"  向量维度: {stats.dimension}")
print(f"  模型: {stats.model}")
```

### 示例4: 带过滤的检索

```python
# 存储带元数据的chunks
chunks = [
    {
        "text": "苗族银饰工艺",
        "document_id": "doc1",
        "chunk_index": 0,
        "metadata": {"ethnic": "苗族", "category": "工艺"}
    },
    {
        "text": "布依族山歌传承",
        "document_id": "doc2",
        "chunk_index": 0,
        "metadata": {"ethnic": "布依族", "category": "音乐"}
    },
    {
        "text": "苗族服饰文化",
        "document_id": "doc3",
        "chunk_index": 0,
        "metadata": {"ethnic": "苗族", "category": "服饰"}
    },
]

engine.vectorize_and_store(chunks)

# 只检索苗族相关内容
results = engine.search_similar(
    query="民族文化",
    top_k=10,
    filters={"ethnic": "苗族"}
)

for result in results:
    print(f"[{result.score:.3f}] {result.chunk.text}")
    print(f"  元数据: {result.chunk.metadata}")
```

### 示例5: 删除和管理

```python
# 删除某个文档的所有向量
success = engine.delete_by_document("doc1")
print(f"删除doc1: {'成功' if success else '失败'}")

# 查看统计
stats = engine.get_statistics()
print(f"剩余chunks: {stats.total_chunks}")
```

### 示例6: 便捷函数（快速使用）

```python
from app.tools.vectorization import (
    encode_query,
    encode_documents,
    vectorize_and_store,
    search_similar,
    VectorEngine
)

# 快速编码查询
query_vec = encode_query("田野调查", engine=VectorEngine.TFIDF)

# 快速编码文档
doc_vecs = encode_documents(["文本1", "文本2"], engine=VectorEngine.TFIDF)

# 快速向量化存储
chunks = [{"text": "内容", "document_id": "d1", "chunk_index": 0}]
results = vectorize_and_store(chunks, engine=VectorEngine.TFIDF)

# 快速检索
search_results = search_similar("查询", top_k=5, engine=VectorEngine.TFIDF)
```

---

## 🎯 最佳实践

### 1. 引擎选择策略

```python
# 开发/测试: 使用TF-IDF（零配置）
dev_engine = create_engine(
    engine=VectorEngine.TFIDF,
    storage=StorageBackend.MEMORY
)

# 生产环境: 使用BGE + 双写
prod_engine = create_engine(
    engine=VectorEngine.BGE_SMALL,
    storage=StorageBackend.DUAL
)

# 离线场景: 使用MiniLM
offline_engine = create_engine(
    engine=VectorEngine.MINILM,
    storage=StorageBackend.CHROMADB_ONLY
)
```

### 2. 单例模式使用

```python
# 推荐：使用单例减少内存
engine = UnifiedVectorizationEngine.get_instance(
    engine=VectorEngine.BGE_SMALL,
    storage=StorageBackend.MEMORY
)

# 同样配置会返回同一实例
engine2 = UnifiedVectorizationEngine.get_instance(
    engine=VectorEngine.BGE_SMALL,
    storage=StorageBackend.MEMORY
)

assert engine is engine2  # True
```

### 3. 批处理优化

```python
# ❌ 不推荐：逐个处理
for text in large_text_list:
    engine.encode_documents([text])

# ✅ 推荐：批量处理
engine.encode_documents(
    large_text_list,
    batch_size=64,           # 根据内存调整
    show_progress=True       # 大批量显示进度
)
```

### 4. 元数据设计

```python
# 推荐的元数据结构
metadata = {
    # 核心信息
    "document_type": "interview",
    "project_id": 123,
    
    # 时空信息
    "location": "十八洞村",
    "date": "2024-01-15",
    
    # 分类标签
    "category": "扶贫",
    "ethnic": "苗族",
    
    # 来源信息
    "interviewer": "张三",
    "interviewee": "村长",
    
    # 质量指标
    "confidence": 0.95,
    "verified": True,
}

chunk = {
    "text": "访谈内容...",
    "document_id": "interview_001",
    "chunk_index": 0,
    "metadata": metadata
}
```

### 5. 错误处理

```python
from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine

try:
    engine = UnifiedVectorizationEngine(
        engine=VectorEngine.BGE_LARGE,
        auto_fallback=True  # 重要：启用降级
    )
except RuntimeError as e:
    print(f"引擎初始化失败: {e}")
    # 降级到TF-IDF
    engine = UnifiedVectorizationEngine(engine=VectorEngine.TFIDF)

# 编码时的错误处理
try:
    results = engine.search_similar("", top_k=5)
except ValueError as e:
    print(f"查询错误: {e}")
```

---

## 🔄 迁移指南

### 从 vectorization_service_complete.py 迁移

**旧代码:**
```python
from app.services.vectorization_service_complete import VectorizationService

service = VectorizationService()
vectors = service.vectorize_chunks(chunks)
service.store_chunks(vectors, project_id=1, db=db_session)
results = service.query_similar(query, top_k=10)
```

**新代码:**
```python
from app.tools.vectorization import create_engine, VectorEngine, StorageBackend

engine = create_engine(
    engine=VectorEngine.BGE_LARGE,  # 对应FlagEmbedding
    storage=StorageBackend.DUAL      # 对应SQL+ChromaDB双写
)

# 一步完成向量化和存储
vectorized = engine.vectorize_and_store(chunks, project_id=1, db=db_session)

# 检索
results = engine.search_similar(query, top_k=10)
```

### 从 embedding_service_v2.py 迁移

**旧代码:**
```python
from app.services.embedding_service_v2 import FlagEmbeddingService

service = FlagEmbeddingService()
query_emb = service.encode_queries([query])[0]
doc_embs = service.encode_documents(documents)
```

**新代码:**
```python
from app.tools.vectorization import create_engine, VectorEngine

engine = create_engine(
    engine=VectorEngine.BGE_SMALL,   # 对应BGE Small
    optimize_query=True               # 对应query指令优化
)

query_emb = engine.encode_query(query)
doc_embs = engine.encode_documents(documents)
```

### 从 tfidf_vectorization.py 迁移

**旧代码:**
```python
from app.services.tfidf_vectorization import TfidfVectorizationService

service = TfidfVectorizationService(embedding_dim=384)
service.fit(texts)
vectors = service.vectorize_chunks(chunks)
```

**新代码:**
```python
from app.tools.vectorization import create_engine, VectorEngine

engine = create_engine(engine=VectorEngine.TFIDF)

# 不需要手动fit，自动训练
vectorized = engine.vectorize_and_store(chunks)
```

---

## ⚡ 性能优化

### 1. 向量维度 vs 性能

| 维度 | 编码速度 | 检索速度 | 存储大小 | 精度 |
|------|----------|----------|----------|------|
| 384 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1.5KB/chunk | ⭐⭐⭐ |
| 512 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 2KB/chunk | ⭐⭐⭐⭐ |
| 1024 | ⭐⭐⭐ | ⭐⭐⭐ | 4KB/chunk | ⭐⭐⭐⭐⭐ |

### 2. 批处理基准测试

```python
import time

# 单个编码: 慢
start = time.time()
for text in texts:
    engine.encode_documents([text])
single_time = time.time() - start

# 批量编码: 快
start = time.time()
engine.encode_documents(texts, batch_size=32)
batch_time = time.time() - start

print(f"单个: {single_time:.2f}s")
print(f"批量: {batch_time:.2f}s")
print(f"加速: {single_time/batch_time:.1f}x")
```

### 3. 存储后端性能

| 操作 | MEMORY | CHROMADB | SQL | DUAL |
|------|--------|----------|-----|------|
| 写入 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 检索 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| 持久化 | ❌ | ✅ | ✅ | ✅ |

---

## 🔧 故障排查

### 问题1: 模型加载失败

**症状:**
```
RuntimeError: All encoders failed to load
```

**解决:**
```python
# 1. 启用自动降级
engine = UnifiedVectorizationEngine(
    engine=VectorEngine.BGE_LARGE,
    auto_fallback=True  # 关键
)

# 2. 直接使用TF-IDF
engine = UnifiedVectorizationEngine(engine=VectorEngine.TFIDF)

# 3. 检查依赖
# pip install FlagEmbedding sentence-transformers
```

### 问题2: 检索结果为空

**原因:** 
- 查询为空
- 阈值设置过高
- 存储中没有数据

**解决:**
```python
# 检查存储
stats = engine.get_statistics()
print(f"总chunks: {stats.total_chunks}")

# 降低阈值
results = engine.search_similar(query, threshold=0.0)

# 检查查询
if not query.strip():
    raise ValueError("Query is empty")
```

### 问题3: 内存占用过高

**原因:** 多个引擎实例

**解决:**
```python
# ✅ 使用单例
engine = UnifiedVectorizationEngine.get_instance(
    engine=VectorEngine.BGE_SMALL
)

# ❌ 避免重复创建
for _ in range(100):
    engine = UnifiedVectorizationEngine(...)  # 内存泄漏
```

### 问题4: ChromaDB连接失败

**解决:**
```python
# 检查ChromaDB配置
import chromadb

try:
    client = chromadb.Client()
    print("ChromaDB可用")
except Exception as e:
    print(f"ChromaDB不可用: {e}")
    # 降级到内存存储
    engine = create_engine(storage=StorageBackend.MEMORY)
```

---

## 📊 技术对比

### 与原服务对比

| 特性 | 原7个服务 | 统一引擎 |
|------|-----------|----------|
| 文件数 | 7 | 1 |
| 代码行数 | 1,962 | 1,120 |
| 模型选择 | 固定 | 4种可选 |
| 存储方式 | 固定 | 4种可选 |
| Query优化 | 部分 | 全部支持 |
| 自动降级 | 无 | ✅ |
| 单例模式 | 部分 | ✅ |
| 测试覆盖 | 无 | 44个用例 |
| 输出模式 | 混乱 | 统一 |

---

## 🎓 常见问题

**Q: 应该使用哪个引擎？**

A: 
- 开发/测试: `TFIDF` (零配置)
- 生产环境: `BGE_SMALL` (平衡)
- 最高精度: `BGE_LARGE` (GPU环境)
- 离线场景: `MINILM` (轻量)

**Q: 存储后端如何选择？**

A:
- 仅测试: `MEMORY`
- 纯语义检索: `CHROMADB_ONLY`
- 需要SQL查询: `SQL_ONLY`
- 生产推荐: `DUAL`

**Q: 如何提高检索准确率？**

A:
1. 使用更高维度的模型 (BGE_LARGE)
2. 启用Query优化 (`optimize_query=True`)
3. 调整相似度阈值
4. 使用元数据过滤

**Q: 性能瓶颈在哪里？**

A:
1. 编码速度: 使用批处理
2. 检索速度: 使用ChromaDB
3. 存储速度: 避免DUAL模式的双写开销

---

## 📝 总结

统一向量化引擎提供了:

✅ **简化接口** - 7个服务整合为1个  
✅ **灵活配置** - 4种引擎 × 4种存储 = 16种组合  
✅ **自动降级** - 模型加载失败自动切换  
✅ **完整测试** - 44个测试用例覆盖  
✅ **向后兼容** - 支持dict和dataclass输出  
✅ **生产就绪** - 单例模式、错误处理、性能优化  

立即开始使用: `from app.tools.vectorization import create_engine`
