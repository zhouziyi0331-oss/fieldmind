# 向量存储系统集成方案

## 当前状况分析

### 现有系统
- **位置**: `app/core/vector_store.py`
- **技术**: PostgreSQL + pgvector
- **功能**: 基础的向量插入、搜索、删除

### 新系统
- **位置**: `app/vector_store/`
- **技术**: FAISS + Chroma，带缓存和混合检索
- **优势**: 
  - 3-264倍性能提升
  - 支持多种后端
  - 智能缓存
  - 混合检索（语义+关键词）

## 集成策略

### 方案1: 完全替换（推荐）⭐

**优点**: 
- 充分利用新系统所有功能
- 性能提升最大
- 代码最简洁

**缺点**:
- 需要迁移现有数据
- API 有变化

**实施步骤**:
1. 创建适配器层，兼容旧API
2. 逐步迁移数据
3. 更新调用代码
4. 废弃旧系统

### 方案2: 并行运行

**优点**:
- 风险低
- 可以逐步切换
- 保留旧系统作为备份

**缺点**:
- 维护两套系统
- 数据可能不一致

### 方案3: 适配器模式（最快）⚡

**优点**:
- 最小改动
- 快速上线
- 向后兼容

**缺点**:
- 不能充分利用新功能
- 性能提升有限

## 推荐实施：分阶段迁移

### 第一阶段：适配器集成（1天）

创建适配器，让新系统适配旧接口：

```python
# app/core/vector_store_v2.py
from app.vector_store.backends import FaissVectorStore
from app.vector_store.cache import LRUCache
from app.vector_store import Document
import numpy as np

class VectorStoreV2:
    """新向量存储适配器"""
    
    def __init__(self):
        # 使用 FAISS + 缓存
        self.store = FaissVectorStore(
            dimension=1536,  # OpenAI embedding 维度
            index_type=IndexType.HNSW
        )
        
        self.cache = LRUCache(
            max_size=1000,
            ttl=600,
            enable_semantic=True
        )
    
    def insert_vector(self, document_id, chunk_id, embedding, model_name):
        """适配旧接口"""
        doc = Document(
            id=chunk_id,
            content="",  # 如需要，从数据库获取
            embedding=np.array(embedding, dtype=np.float32),
            metadata={
                "document_id": document_id,
                "model_name": model_name
            }
        )
        self.store.add([doc])
        return True
    
    def search_similar_vectors(self, query_embedding, top_k=5, 
                               document_id=None, similarity_threshold=0.0):
        """适配旧接口"""
        # 先查缓存
        cached = self.cache.get(
            np.array(query_embedding, dtype=np.float32),
            top_k=top_k
        )
        if cached:
            return self._convert_results(cached)
        
        # 搜索
        filters = {"document_id": document_id} if document_id else None
        results = self.store.search(
            np.array(query_embedding, dtype=np.float32),
            top_k=top_k,
            filters=filters
        )
        
        # 缓存结果
        self.cache.set(
            np.array(query_embedding, dtype=np.float32),
            results,
            top_k=top_k
        )
        
        # 转换格式
        return self._convert_results(results)
    
    def _convert_results(self, results):
        """转换为旧格式"""
        return [
            {
                "chunk_id": r.document.id,
                "document_id": r.document.metadata.get("document_id"),
                "model_name": r.document.metadata.get("model_name"),
                "similarity": r.score
            }
            for r in results
        ]
```

**使用方式**:
```python
# 配置文件中添加开关
USE_NEW_VECTOR_STORE = True

# 在需要的地方
if USE_NEW_VECTOR_STORE:
    from app.core.vector_store_v2 import VectorStoreV2
    vector_store = VectorStoreV2()
else:
    from app.core.vector_store import get_vector_store
    vector_store = get_vector_store()
```

### 第二阶段：数据迁移（1-2天）

创建迁移脚本：

```python
# scripts/migrate_vectors.py
from app.core.vector_store import get_vector_store as get_old_store
from app.vector_store.backends import FaissVectorStore
from app.vector_store import Document
import numpy as np

def migrate_vectors():
    """迁移向量数据"""
    old_store = get_old_store()
    new_store = FaissVectorStore(dimension=1536, persist_dir="./faiss_index")
    
    # 获取所有向量（分批）
    batch_size = 1000
    offset = 0
    
    while True:
        # 从 PostgreSQL 读取
        conn = old_store._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT chunk_id, document_id, embedding, model_name "
            "FROM document_vectors LIMIT %s OFFSET %s",
            (batch_size, offset)
        )
        rows = cursor.fetchall()
        
        if not rows:
            break
        
        # 转换为新格式
        docs = []
        for row in rows:
            doc = Document(
                id=row[0],  # chunk_id
                content="",
                embedding=np.array(row[2], dtype=np.float32),
                metadata={
                    "document_id": row[1],
                    "model_name": row[3]
                }
            )
            docs.append(doc)
        
        # 批量添加
        new_store.add(docs)
        
        offset += batch_size
        print(f"已迁移 {offset} 条向量")
    
    # 保存索引
    new_store.save()
    print("迁移完成！")

if __name__ == "__main__":
    migrate_vectors()
```

### 第三阶段：启用新功能（1天）

添加混合检索：

```python
# app/core/vector_store_v2.py (扩展)
from app.vector_store.retrieval import HybridRetriever, FusionMethod

class VectorStoreV2Enhanced:
    """增强版向量存储"""
    
    def __init__(self):
        self.store = FaissVectorStore(...)
        self.retriever = HybridRetriever(
            vector_store=self.store,
            fusion_method=FusionMethod.RRF
        )
        self.cache = LRUCache(...)
    
    def hybrid_search(self, query_text, query_embedding, top_k=5):
        """混合检索（新功能）"""
        return self.retriever.search(
            query_text=query_text,
            query_embedding=np.array(query_embedding, dtype=np.float32),
            top_k=top_k
        )
```

### 第四阶段：监控和优化（持续）

添加监控：

```python
def get_performance_metrics():
    """获取性能指标"""
    cache_stats = cache.get_stats()
    store_stats = store.get_stats()
    
    return {
        "cache_hit_rate": cache_stats["hit_rate"],
        "total_vectors": store_stats["count"],
        "avg_search_latency": "...",  # 从日志收集
    }
```

## 快速开始

### 立即可用（10分钟）

1. **创建适配器**
```bash
cd /Users/alwan/FieldMind/backend/src
# 创建 app/core/vector_store_v2.py
```

2. **配置切换**
```python
# app/config.py
USE_NEW_VECTOR_STORE: bool = False  # 初始关闭
```

3. **小范围测试**
```python
# 在一个 API 端点测试
@router.get("/test-new-vector")
async def test_new_vector():
    store = VectorStoreV2()
    # 测试搜索
    results = store.search_similar_vectors(...)
    return results
```

## 风险管理

### 回滚计划
1. 保留旧系统代码
2. 配置开关快速切换
3. 数据双写一段时间

### 监控指标
- 搜索延迟 P95、P99
- 缓存命中率
- 错误率
- 内存占用

### 测试清单
- [ ] 基础搜索功能
- [ ] 批量插入性能
- [ ] 缓存命中率
- [ ] 混合检索效果
- [ ] 并发压力测试

## 预期收益

### 性能提升
- 搜索延迟：**0.4ms → 0.14ms** (HNSW)
- 缓存命中：**<2μs** (264倍提升)
- QPS：**~1000 → 7000+**

### 功能增强
- ✅ 混合检索（语义+关键词）
- ✅ 智能缓存
- ✅ 多后端支持
- ✅ 更好的可观测性

### 成本
- 开发时间：3-5天
- 风险：低（有回滚方案）
- 维护：简化（统一接口）

## 下一步行动

**立即执行**:
1. 创建 `vector_store_v2.py` 适配器
2. 添加配置开关
3. 单元测试验证

**本周完成**:
1. 数据迁移脚本
2. 全面集成测试
3. 文档更新

**下周上线**:
1. 灰度发布
2. 性能监控
3. 用户反馈收集

---

**准备好开始了吗？**
