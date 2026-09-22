# 向量存储抽象层

## 概述

这是 FieldMind 向量检索系统的统一抽象接口，支持多种向量数据库后端（FAISS、Chroma等）。

## 设计原则

1. **开闭原则**：对扩展开放，对修改关闭
2. **依赖倒置**：上层依赖抽象，不依赖具体实现
3. **里氏替换**：所有后端实现可以互换使用
4. **接口隔离**：提供清晰、最小化的接口

## 核心组件

### 1. 数据类

#### Document
```python
@dataclass
class Document:
    id: str                      # 唯一标识符
    content: str                 # 文本内容
    embedding: np.ndarray        # 向量表示（1维数组）
    metadata: Dict[str, Any]     # 元数据
```

#### SearchResult
```python
@dataclass
class SearchResult:
    document: Document           # 匹配的文档
    score: float                 # 相似度分数 [0, 1]
    distance: float              # 距离值
    rank: int                    # 排名位置
```

### 2. 枚举类型

#### DistanceMetric（距离度量）
- `COSINE`: 余弦相似度
- `EUCLIDEAN`: 欧几里得距离
- `DOT_PRODUCT`: 点积
- `L2`: L2范数

#### IndexType（索引类型）
- `FLAT`: 暴力搜索（精确但慢）
- `IVF`: 倒排文件索引
- `HNSW`: 层次化可导航小世界图
- `LSH`: 局部敏感哈希

### 3. 抽象基类 VectorStore

#### 核心方法

```python
# CRUD 操作
add(documents: List[Document]) -> List[str]
search(query_embedding, top_k, filters) -> List[SearchResult]
delete(doc_ids: List[str]) -> int
update(documents: List[Document]) -> int
get(doc_ids: List[str]) -> List[Optional[Document]]

# 辅助方法
count() -> int
clear() -> None
exists(doc_id: str) -> bool
validate_embedding(embedding: np.ndarray) -> None
get_stats() -> Dict[str, Any]
batch_search(query_embeddings, top_k, filters) -> List[List[SearchResult]]
```

## 使用示例

### 基本使用

```python
from app.vector_store import VectorStore, Document, DistanceMetric, IndexType
import numpy as np

# 创建文档
doc = Document(
    id="doc1",
    content="这是测试文档",
    embedding=np.random.rand(768),  # 假设使用768维向量
    metadata={"source": "pdf", "page": 1}
)

# 添加到向量存储（具体后端实现）
store = SomeVectorStore(dimension=768, distance_metric=DistanceMetric.COSINE)
store.add([doc])

# 搜索
query_embedding = np.random.rand(768)
results = store.search(query_embedding, top_k=5)

for result in results:
    print(f"文档: {result.document.id}, 分数: {result.score:.4f}")
```

### 带过滤的搜索

```python
# 只搜索特定来源的文档
results = store.search(
    query_embedding,
    top_k=10,
    filters={"source": "pdf", "year": 2024}
)
```

### 批量操作

```python
# 批量添加
documents = [doc1, doc2, doc3, ...]
ids = store.add(documents)

# 批量搜索
queries = [embedding1, embedding2, embedding3]
batch_results = store.batch_search(queries, top_k=5)
```

## 实现后端

### 如何实现新的后端

继承 `VectorStore` 并实现所有抽象方法：

```python
class MyVectorStore(VectorStore):
    def __init__(self, dimension: int, **kwargs):
        super().__init__(dimension, **kwargs)
        # 初始化后端特定的资源
        
    def add(self, documents):
        # 实现添加逻辑
        pass
        
    def search(self, query_embedding, top_k=10, filters=None):
        # 实现搜索逻辑
        pass
        
    # ... 实现其他方法
```

### 计划支持的后端

1. **FAISS** (Facebook AI Similarity Search)
   - 高性能向量搜索
   - 支持 GPU 加速
   - 适合大规模数据

2. **Chroma** 
   - 内置持久化
   - 丰富的元数据过滤
   - 简单易用

3. **内存存储**
   - 用于测试和小数据量
   - 无外部依赖

## 测试

运行测试：
```bash
cd /Users/alwan/FieldMind/backend/src
python3 -m pytest app/vector_store/test_base.py -v --override-ini='addopts='
```

当前测试覆盖：
- ✅ Document 数据类验证
- ✅ SearchResult 数据类
- ✅ 枚举类型
- ✅ VectorStore 接口完整性
- ✅ CRUD 操作
- ✅ 批量操作
- ✅ 异常处理

**测试结果**: 20/20 通过 ✅

## 性能目标

| 指标 | 目标值 |
|------|--------|
| 搜索延迟 (1M向量) | < 100ms |
| 吞吐量 | > 1000 QPS |
| 内存效率 | < 2GB (1M × 768维) |
| 准确率 (top-10) | > 95% |

## 下一步

- [ ] 实现 FAISS 后端 (Step 2-3)
- [ ] 实现 Chroma 后端 (Step 4-5)
- [ ] 添加缓存层 (Step 6)
- [ ] 实现混合检索 (Step 7)
- [ ] 性能基准测试 (Step 8)
- [ ] 集成到现有系统 (Step 9)

## 文件结构

```
app/vector_store/
├── __init__.py          # 模块导出
├── base.py              # 抽象接口定义 ✅
├── test_base.py         # 接口测试 ✅
├── backends/            # 后端实现（待创建）
│   ├── faiss_store.py
│   ├── chroma_store.py
│   └── memory_store.py
├── cache/               # 缓存层（待创建）
│   └── semantic_cache.py
└── retrieval/           # 检索策略（待创建）
    └── hybrid_retrieval.py
```

## 版本

当前版本: **v0.1.0** (基础抽象层)

## 贡献者

- 初始设计: 2026-08-29
- 测试覆盖: 100%
