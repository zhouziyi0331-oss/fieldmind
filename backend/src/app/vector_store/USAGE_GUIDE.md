# 向量存储系统使用指南

## 快速开始

### 1. 基础向量检索

```python
import numpy as np
from app.vector_store import Document, DistanceMetric, IndexType
from app.vector_store.backends import FaissVectorStore

# 创建向量存储
store = FaissVectorStore(
    dimension=768,
    distance_metric=DistanceMetric.COSINE,
    index_type=IndexType.HNSW
)

# 创建文档
doc1 = Document(
    id="doc1",
    content="机器学习是人工智能的一个分支",
    embedding=np.random.rand(768).astype(np.float32),
    metadata={"category": "AI", "year": 2024}
)

doc2 = Document(
    id="doc2",
    content="深度学习是机器学习的一种方法",
    embedding=np.random.rand(768).astype(np.float32),
    metadata={"category": "AI", "year": 2024}
)

# 添加文档
store.add([doc1, doc2])

# 搜索
query_embedding = np.random.rand(768).astype(np.float32)
results = store.search(query_embedding, top_k=5)

for result in results:
    print(f"ID: {result.document.id}")
    print(f"Score: {result.score:.4f}")
    print(f"Content: {result.document.content}")
    print()
```

### 2. 使用缓存加速

```python
from app.vector_store.cache import LRUCache

# 创建缓存
cache = LRUCache(
    max_size=1000,
    ttl=300,  # 5分钟过期
    enable_semantic=True,
    semantic_threshold=0.95
)

# 带缓存的搜索
def search_with_cache(query_embedding, top_k=10):
    # 尝试从缓存获取
    cached_result = cache.get(query_embedding, top_k=top_k)
    if cached_result is not None:
        print("缓存命中！")
        return cached_result
    
    # 缓存未命中，执行搜索
    results = store.search(query_embedding, top_k=top_k)
    
    # 缓存结果
    cache.set(query_embedding, results, top_k=top_k)
    
    return results

# 使用
results = search_with_cache(query_embedding)

# 查看缓存统计
stats = cache.get_stats()
print(f"命中率: {stats['hit_rate']:.2%}")
```

### 3. 混合检索（语义 + 关键词）

```python
from app.vector_store.retrieval import HybridRetriever, FusionMethod

# 创建混合检索器
retriever = HybridRetriever(
    vector_store=store,
    fusion_method=FusionMethod.RRF,
    dense_weight=0.7,
    sparse_weight=0.3
)

# 添加文档（需要包含 content 和 embedding）
retriever.add_documents([doc1, doc2])

# 混合搜索
results = retriever.search(
    query_text="机器学习算法",
    query_embedding=query_embedding,
    top_k=10
)

for result in results:
    print(f"{result.document.id}: {result.score:.4f}")
```

## 完整示例

### 示例1：构建文档问答系统

```python
import numpy as np
from app.vector_store import Document
from app.vector_store.backends import FaissVectorStore
from app.vector_store.cache import LRUCache
from app.vector_store.retrieval import HybridRetriever, FusionMethod

class DocumentQA:
    """文档问答系统"""
    
    def __init__(self, dimension=768):
        self.dimension = dimension
        
        # 向量存储
        self.store = FaissVectorStore(
            dimension=dimension,
            index_type=IndexType.HNSW,
            hnsw_m=32
        )
        
        # 混合检索
        self.retriever = HybridRetriever(
            vector_store=self.store,
            fusion_method=FusionMethod.RRF
        )
        
        # 缓存
        self.cache = LRUCache(
            max_size=1000,
            ttl=600,
            enable_semantic=True,
            semantic_threshold=0.95
        )
    
    def add_documents(self, documents):
        """添加文档"""
        self.retriever.add_documents(documents)
    
    def search(self, query_text, query_embedding, top_k=5):
        """搜索相关文档（带缓存）"""
        # 尝试缓存
        cache_key = f"{query_text}_{top_k}"
        cached = self.cache.get(query_embedding, query=query_text, top_k=top_k)
        
        if cached is not None:
            return cached
        
        # 混合检索
        results = self.retriever.search(
            query_text=query_text,
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        # 缓存结果
        self.cache.set(query_embedding, results, query=query_text, top_k=top_k)
        
        return results
    
    def get_stats(self):
        """获取统计信息"""
        return {
            "documents": self.store.count(),
            "cache": self.cache.get_stats(),
            "retriever": self.retriever.get_stats()
        }

# 使用示例
qa_system = DocumentQA(dimension=768)

# 添加文档
documents = [
    Document(
        id=f"doc{i}",
        content=f"文档{i}的内容...",
        embedding=np.random.rand(768).astype(np.float32)
    )
    for i in range(100)
]
qa_system.add_documents(documents)

# 查询
query = "什么是机器学习？"
query_vec = np.random.rand(768).astype(np.float32)
results = qa_system.search(query, query_vec, top_k=5)

# 统计
stats = qa_system.get_stats()
print(f"文档数: {stats['documents']}")
print(f"缓存命中率: {stats['cache']['hit_rate']:.2%}")
```

### 示例2：多后端对比

```python
from app.vector_store.backends import FaissVectorStore, ChromaVectorStore

def compare_backends(documents, query_embedding, top_k=10):
    """对比不同后端的性能"""
    
    backends = {
        "FAISS-Flat": FaissVectorStore(
            dimension=768,
            index_type=IndexType.FLAT
        ),
        "FAISS-HNSW": FaissVectorStore(
            dimension=768,
            index_type=IndexType.HNSW
        ),
        "Chroma": ChromaVectorStore(
            dimension=768,
            collection_name="test"
        )
    }
    
    results = {}
    
    for name, backend in backends.items():
        # 添加文档
        import time
        start = time.time()
        backend.add(documents)
        add_time = time.time() - start
        
        # 搜索
        start = time.time()
        search_results = backend.search(query_embedding, top_k=top_k)
        search_time = time.time() - start
        
        results[name] = {
            "add_time": f"{add_time:.3f}s",
            "search_time": f"{search_time*1000:.2f}ms",
            "results": len(search_results)
        }
    
    return results

# 运行对比
docs = [Document(...) for _ in range(1000)]
query = np.random.rand(768).astype(np.float32)
comparison = compare_backends(docs, query)

for name, metrics in comparison.items():
    print(f"\n{name}:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
```

### 示例3：持久化和加载

```python
# FAISS 持久化
faiss_store = FaissVectorStore(
    dimension=768,
    persist_dir="./faiss_index"
)
faiss_store.add(documents)
faiss_store.save()

# 加载
loaded_store = FaissVectorStore.load("./faiss_index")
results = loaded_store.search(query_embedding, top_k=10)

# Chroma 自动持久化
chroma_store = ChromaVectorStore(
    dimension=768,
    collection_name="my_collection",
    persist_directory="./chroma_db"
)
chroma_store.add(documents)

# 重启后自动恢复
chroma_store2 = ChromaVectorStore(
    dimension=768,
    collection_name="my_collection",
    persist_directory="./chroma_db"
)
# 数据自动加载
print(f"文档数: {chroma_store2.count()}")
```

## 性能优化建议

### 1. 选择合适的后端

- **小数据量 (< 10K)**: FAISS Flat 或 Chroma
- **中等数据量 (10K - 1M)**: FAISS HNSW
- **大数据量 (> 1M)**: FAISS IVF + GPU

### 2. 索引参数调优

```python
# HNSW 参数
store = FaissVectorStore(
    dimension=768,
    index_type=IndexType.HNSW,
    hnsw_m=32,              # 连接数，越大越精确但越慢
    hnsw_ef_construction=200,  # 构建质量
    hnsw_ef_search=128      # 搜索质量，越大越精确
)
```

### 3. 使用缓存

```python
# 对于重复查询，使用缓存
cache = LRUCache(
    max_size=1000,
    ttl=300,
    enable_semantic=True  # 相似查询也能命中
)
```

### 4. 批量操作

```python
# 批量添加更高效
store.add(documents)  # 一次添加多个

# 批量搜索
queries = [embedding1, embedding2, embedding3]
results = store.batch_search(queries, top_k=10)
```

## 常见问题

### Q1: 如何选择距离度量？

- **余弦相似度** (COSINE): 适合已归一化的向量，不关心向量长度
- **欧几里得距离** (L2): 考虑向量长度
- **点积** (DOT_PRODUCT): 用于特殊场景

### Q2: 混合检索什么时候用？

- 需要同时考虑语义和关键词匹配
- 提高召回率
- 用户查询较短或包含特定术语

### Q3: 缓存应该多大？

- 根据查询重复率：高重复 → 大缓存
- 内存限制：每个条目约 1KB
- 推荐：1000-10000

### Q4: HNSW vs Flat 如何选择？

| 维度 | Flat | HNSW |
|------|------|------|
| 精确度 | 100% | ~98% |
| 速度 | 慢 | 快 |
| 内存 | 低 | 中 |
| 适用 | < 10K | > 10K |

## 最佳实践

1. **先测试后上线**: 使用 benchmark.py 测试性能
2. **监控缓存命中率**: 低于 20% 考虑关闭
3. **定期重建索引**: 删除操作后调用 rebuild_index()
4. **设置合理的 top_k**: 通常 10-50 足够
5. **使用元数据过滤**: 减少搜索空间

## 参考文档

- [向量存储 README](README.md)
- [性能基准测试](benchmark.py)
- [实施日志](IMPLEMENTATION_LOG.md)
