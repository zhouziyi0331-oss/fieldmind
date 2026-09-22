"""
向量存储性能基准测试

测试不同后端的性能指标：
- 搜索延迟
- 吞吐量
- 内存占用
- 准确率
"""

import time
import numpy as np
from typing import List, Dict, Any
import psutil
import os

from app.vector_store import Document, DistanceMetric, IndexType
from app.vector_store.backends import FaissVectorStore, ChromaVectorStore
from app.vector_store.cache import LRUCache
from app.vector_store.retrieval import HybridRetriever, FusionMethod


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self, dimension: int = 768):
        """初始化基准测试

        Args:
            dimension: 向量维度
        """
        self.dimension = dimension
        self.results: Dict[str, Any] = {}

    def generate_documents(self, num_docs: int) -> List[Document]:
        """生成测试文档

        Args:
            num_docs: 文档数量

        Returns:
            文档列表
        """
        docs = []
        for i in range(num_docs):
            embedding = np.random.rand(self.dimension).astype(np.float32)
            doc = Document(
                id=f"doc{i}",
                content=f"这是第{i}个测试文档的内容",
                embedding=embedding,
                metadata={"index": i, "category": f"cat{i % 10}"}
            )
            docs.append(doc)
        return docs

    def benchmark_faiss_flat(self, num_docs: int = 10000, num_queries: int = 100):
        """测试 FAISS Flat 索引

        Args:
            num_docs: 文档数量
            num_queries: 查询数量

        Returns:
            性能指标字典
        """
        print(f"\n=== FAISS Flat Benchmark ({num_docs} docs) ===")

        # 创建存储
        store = FaissVectorStore(
            dimension=self.dimension,
            index_type=IndexType.FLAT,
            distance_metric=DistanceMetric.COSINE
        )

        # 生成文档
        print("生成文档...")
        docs = self.generate_documents(num_docs)

        # 测试添加性能
        print("测试添加性能...")
        start_time = time.time()
        store.add(docs)
        add_time = time.time() - start_time

        # 生成查询
        queries = [np.random.rand(self.dimension).astype(np.float32) for _ in range(num_queries)]

        # 测试搜索性能
        print("测试搜索性能...")
        latencies = []
        for query in queries:
            start = time.time()
            results = store.search(query, top_k=10)
            latency = (time.time() - start) * 1000  # 转换为毫秒
            latencies.append(latency)

        # 计算统计
        avg_latency = np.mean(latencies)
        p50_latency = np.percentile(latencies, 50)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        qps = 1000 / avg_latency if avg_latency > 0 else 0

        # 内存占用
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        results = {
            "backend": "FAISS Flat",
            "num_docs": num_docs,
            "dimension": self.dimension,
            "add_time": f"{add_time:.2f}s",
            "avg_latency": f"{avg_latency:.2f}ms",
            "p50_latency": f"{p50_latency:.2f}ms",
            "p95_latency": f"{p95_latency:.2f}ms",
            "p99_latency": f"{p99_latency:.2f}ms",
            "qps": f"{qps:.0f}",
            "memory_mb": f"{memory_mb:.0f}MB"
        }

        self._print_results(results)
        return results

    def benchmark_faiss_hnsw(self, num_docs: int = 10000, num_queries: int = 100):
        """测试 FAISS HNSW 索引

        Args:
            num_docs: 文档数量
            num_queries: 查询数量

        Returns:
            性能指标字典
        """
        print(f"\n=== FAISS HNSW Benchmark ({num_docs} docs) ===")

        store = FaissVectorStore(
            dimension=self.dimension,
            index_type=IndexType.HNSW,
            distance_metric=DistanceMetric.COSINE,
            hnsw_m=32,
            hnsw_ef_construction=200,
            hnsw_ef_search=128
        )

        print("生成文档...")
        docs = self.generate_documents(num_docs)

        print("测试添加性能...")
        start_time = time.time()
        store.add(docs)
        add_time = time.time() - start_time

        queries = [np.random.rand(self.dimension).astype(np.float32) for _ in range(num_queries)]

        print("测试搜索性能...")
        latencies = []
        for query in queries:
            start = time.time()
            results = store.search(query, top_k=10)
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        qps = 1000 / avg_latency if avg_latency > 0 else 0

        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024

        results = {
            "backend": "FAISS HNSW",
            "num_docs": num_docs,
            "dimension": self.dimension,
            "add_time": f"{add_time:.2f}s",
            "avg_latency": f"{avg_latency:.2f}ms",
            "p95_latency": f"{p95_latency:.2f}ms",
            "qps": f"{qps:.0f}",
            "memory_mb": f"{memory_mb:.0f}MB"
        }

        self._print_results(results)
        return results

    def benchmark_cache(self, num_queries: int = 1000):
        """测试缓存性能

        Args:
            num_queries: 查询数量

        Returns:
            性能指标字典
        """
        print(f"\n=== Cache Benchmark ({num_queries} queries) ===")

        cache = LRUCache(max_size=1000, enable_semantic=False)

        # 预填充缓存
        print("预填充缓存...")
        for i in range(500):
            query = np.random.rand(self.dimension).astype(np.float32)
            cache.set(query, f"result_{i}")

        # 测试命中性能
        print("测试缓存命中...")
        queries = [np.random.rand(self.dimension).astype(np.float32) for _ in range(num_queries)]

        # 先缓存一半查询
        for i in range(0, num_queries, 2):
            cache.set(queries[i], f"result_{i}")

        # 测试查询
        hit_latencies = []
        miss_latencies = []

        for i, query in enumerate(queries):
            start = time.time()
            result = cache.get(query)
            latency = (time.time() - start) * 1000000  # 微秒

            if result is not None:
                hit_latencies.append(latency)
            else:
                miss_latencies.append(latency)

        stats = cache.get_stats()

        results = {
            "cache_type": "LRU",
            "max_size": 1000,
            "hit_rate": f"{stats['hit_rate']:.2%}",
            "avg_hit_latency": f"{np.mean(hit_latencies):.2f}μs",
            "avg_miss_latency": f"{np.mean(miss_latencies):.2f}μs",
            "hits": stats['hits'],
            "misses": stats['misses']
        }

        self._print_results(results)
        return results

    def benchmark_hybrid(self, num_docs: int = 1000, num_queries: int = 50):
        """测试混合检索性能

        Args:
            num_docs: 文档数量
            num_queries: 查询数量

        Returns:
            性能指标字典
        """
        print(f"\n=== Hybrid Retrieval Benchmark ({num_docs} docs) ===")

        # 创建混合检索器
        store = FaissVectorStore(dimension=self.dimension)
        retriever = HybridRetriever(
            vector_store=store,
            fusion_method=FusionMethod.RRF
        )

        print("生成文档...")
        docs = self.generate_documents(num_docs)

        print("添加文档...")
        start_time = time.time()
        retriever.add_documents(docs)
        add_time = time.time() - start_time

        print("测试混合检索...")
        latencies = []
        for i in range(num_queries):
            query_vec = np.random.rand(self.dimension).astype(np.float32)
            query_text = f"测试查询{i}"

            start = time.time()
            results = retriever.search(
                query_text=query_text,
                query_embedding=query_vec,
                top_k=10
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        avg_latency = np.mean(latencies)
        qps = 1000 / avg_latency if avg_latency > 0 else 0

        results = {
            "retriever": "Hybrid (RRF)",
            "num_docs": num_docs,
            "add_time": f"{add_time:.2f}s",
            "avg_latency": f"{avg_latency:.2f}ms",
            "qps": f"{qps:.0f}"
        }

        self._print_results(results)
        return results

    def _print_results(self, results: Dict[str, Any]):
        """打印结果

        Args:
            results: 结果字典
        """
        print("\n结果:")
        for key, value in results.items():
            print(f"  {key}: {value}")

    def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("=" * 60)
        print("向量存储性能基准测试")
        print("=" * 60)

        # 小规模测试
        self.benchmark_faiss_flat(num_docs=1000, num_queries=100)
        self.benchmark_faiss_hnsw(num_docs=1000, num_queries=100)

        # 缓存测试
        self.benchmark_cache(num_queries=1000)

        # 混合检索测试
        self.benchmark_hybrid(num_docs=500, num_queries=50)

        print("\n" + "=" * 60)
        print("基准测试完成")
        print("=" * 60)


if __name__ == "__main__":
    benchmark = PerformanceBenchmark(dimension=768)
    benchmark.run_all_benchmarks()
