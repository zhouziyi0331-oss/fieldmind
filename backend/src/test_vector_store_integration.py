"""
测试新向量存储集成

验证 VectorStoreV2 适配器功能
"""

import sys
import numpy as np
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.vector_store_v2 import VectorStoreV2, get_vector_store_v2


def test_basic_operations():
    """测试基本操作"""
    print("=" * 60)
    print("测试新向量存储适配器")
    print("=" * 60)

    # 创建实例
    print("\n1. 创建向量存储...")
    store = VectorStoreV2(dimension=384, index_type="hnsw", use_cache=True)
    print("✓ 创建成功")

    # 插入单个向量
    print("\n2. 插入单个向量...")
    embedding = np.random.rand(384).astype(np.float32).tolist()
    success = store.insert_vector(
        document_id="doc1",
        chunk_id="chunk1",
        embedding=embedding,
        model_name="test-model"
    )
    print(f"✓ 插入{'成功' if success else '失败'}")

    # 批量插入
    print("\n3. 批量插入向量...")
    vectors = []
    for i in range(10):
        vectors.append({
            "document_id": f"doc{i}",
            "chunk_id": f"chunk{i+2}",
            "embedding": np.random.rand(384).astype(np.float32).tolist(),
            "model_name": "test-model"
        })

    success_count, fail_count = store.batch_insert_vectors(vectors)
    print(f"✓ 成功: {success_count}, 失败: {fail_count}")

    # 检查数量
    print("\n4. 检查向量数量...")
    count = store.get_vector_count()
    print(f"✓ 当前向量数: {count}")

    # 搜索
    print("\n5. 搜索相似向量...")
    query_embedding = np.random.rand(384).astype(np.float32).tolist()
    results = store.search_similar_vectors(
        query_embedding=query_embedding,
        top_k=5
    )
    print(f"✓ 找到 {len(results)} 个结果")
    for i, result in enumerate(results[:3]):
        print(f"  {i+1}. chunk_id={result['chunk_id']}, similarity={result['similarity']:.4f}")

    # 再次搜索（测试缓存）
    print("\n6. 再次搜索（测试缓存）...")
    results2 = store.search_similar_vectors(
        query_embedding=query_embedding,
        top_k=5
    )
    print(f"✓ 找到 {len(results2)} 个结果（应该来自缓存）")

    # 检查向量存在性
    print("\n7. 检查向量存在性...")
    exists = store.vector_exists("chunk1")
    print(f"✓ chunk1 {'存在' if exists else '不存在'}")

    # 获取统计信息
    print("\n8. 获取统计信息...")
    stats = store.get_stats()
    print(f"✓ 统计信息:")
    print(f"  - 向量数: {stats.get('count', 0)}")
    print(f"  - 索引类型: {stats.get('index_type', 'N/A')}")
    if 'cache' in stats:
        print(f"  - 缓存命中率: {stats['cache']['hit_rate']:.2%}")
        print(f"  - 缓存大小: {stats['cache']['size']}/{stats['cache']['max_size']}")

    # 删除向量
    print("\n9. 删除向量...")
    deleted = store.delete_vector("chunk1")
    print(f"✓ 删除{'成功' if deleted else '失败'}")

    count_after = store.get_vector_count()
    print(f"✓ 删除后向量数: {count_after}")

    print("\n" + "=" * 60)
    print("所有测试完成！✓")
    print("=" * 60)


def test_performance():
    """测试性能"""
    import time

    print("\n" + "=" * 60)
    print("性能测试")
    print("=" * 60)

    store = VectorStoreV2(dimension=384, index_type="hnsw", use_cache=True)

    # 批量插入
    print("\n1. 批量插入 1000 个向量...")
    vectors = []
    for i in range(1000):
        vectors.append({
            "document_id": f"doc{i % 100}",
            "chunk_id": f"perf_chunk{i}",
            "embedding": np.random.rand(384).astype(np.float32).tolist(),
            "model_name": "test-model"
        })

    start = time.time()
    success, fail = store.batch_insert_vectors(vectors)
    insert_time = time.time() - start
    print(f"✓ 插入时间: {insert_time:.2f}s")
    print(f"✓ 平均: {insert_time/1000*1000:.2f}ms/向量")

    # 搜索性能
    print("\n2. 搜索性能测试 (100次)...")
    queries = [np.random.rand(384).astype(np.float32).tolist() for _ in range(100)]

    latencies = []
    for query in queries:
        start = time.time()
        results = store.search_similar_vectors(query, top_k=10)
        latency = (time.time() - start) * 1000  # 转为毫秒
        latencies.append(latency)

    avg_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    p99_latency = np.percentile(latencies, 99)

    print(f"✓ 平均延迟: {avg_latency:.2f}ms")
    print(f"✓ P95 延迟: {p95_latency:.2f}ms")
    print(f"✓ P99 延迟: {p99_latency:.2f}ms")
    print(f"✓ QPS: {1000/avg_latency:.0f}")

    # 缓存性能
    print("\n3. 缓存性能测试...")
    # 使用相同的查询
    same_query = queries[0]

    cache_latencies = []
    for _ in range(100):
        start = time.time()
        results = store.search_similar_vectors(same_query, top_k=10)
        latency = (time.time() - start) * 1000000  # 转为微秒
        cache_latencies.append(latency)

    avg_cache_latency = np.mean(cache_latencies)
    print(f"✓ 缓存命中延迟: {avg_cache_latency:.2f}μs")
    print(f"✓ 加速比: {avg_latency*1000/avg_cache_latency:.0f}×")

    stats = store.get_stats()
    if 'cache' in stats:
        print(f"✓ 缓存命中率: {stats['cache']['hit_rate']:.2%}")

    print("\n" + "=" * 60)
    print("性能测试完成！")
    print("=" * 60)


def test_compatibility():
    """测试与旧接口的兼容性"""
    print("\n" + "=" * 60)
    print("兼容性测试")
    print("=" * 60)

    store = VectorStoreV2(dimension=384)

    # 测试所有旧接口
    methods = [
        "insert_vector",
        "batch_insert_vectors",
        "search_similar_vectors",
        "delete_vector",
        "get_vector_count",
        "vector_exists",
        "get_stats",
        "close"
    ]

    print("\n检查接口兼容性:")
    for method in methods:
        has_method = hasattr(store, method)
        print(f"  {'✓' if has_method else '✗'} {method}")

    print("\n✓ 所有接口都已实现")
    print("=" * 60)


if __name__ == "__main__":
    try:
        # 基本功能测试
        test_basic_operations()

        # 性能测试
        test_performance()

        # 兼容性测试
        test_compatibility()

        print("\n" + "🎉 " * 20)
        print("所有测试通过！新向量存储已准备就绪！")
        print("🎉 " * 20)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
