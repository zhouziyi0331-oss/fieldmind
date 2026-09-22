"""
向量数据库测试脚本
测试 pgvector 的功能和性能
"""

import sys
import os
import time
import numpy as np
from typing import List

# 添加 src 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.core.vector_store import VectorStore


def generate_random_vector(dim: int = 1536) -> List[float]:
    """生成随机向量"""
    vec = np.random.rand(dim).astype(np.float32)
    # 归一化
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def test_connection():
    """测试1: 数据库连接"""
    print("\n" + "="*60)
    print("测试1: 数据库连接")
    print("="*60)

    try:
        store = VectorStore()
        stats = store.get_stats()
        print(f"✅ 连接成功")
        print(f"   总向量数: {stats.get('total_vectors', 0)}")
        print(f"   总文档数: {stats.get('total_documents', 0)}")
        print(f"   表大小: {stats.get('table_size', 'N/A')}")
        store.close()
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_insert_single():
    """测试2: 单个向量插入"""
    print("\n" + "="*60)
    print("测试2: 单个向量插入")
    print("="*60)

    try:
        store = VectorStore()

        doc_id = "test_doc_001"
        chunk_id = "test_chunk_001"
        embedding = generate_random_vector()

        start = time.time()
        success = store.insert_vector(doc_id, chunk_id, embedding)
        elapsed = time.time() - start

        if success:
            print(f"✅ 插入成功")
            print(f"   耗时: {elapsed*1000:.2f}ms")

            # 验证
            exists = store.vector_exists(chunk_id)
            print(f"   验证存在: {exists}")

            store.close()
            return True
        else:
            print(f"❌ 插入失败")
            store.close()
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_batch_insert():
    """测试3: 批量插入"""
    print("\n" + "="*60)
    print("测试3: 批量插入（100个向量）")
    print("="*60)

    try:
        store = VectorStore()

        # 准备100个向量
        vectors = []
        for i in range(100):
            vectors.append({
                "document_id": f"test_doc_{i//10:03d}",
                "chunk_id": f"test_chunk_{i:03d}",
                "embedding": generate_random_vector(),
                "model_name": "text-embedding-ada-002"
            })

        start = time.time()
        success_count, fail_count = store.batch_insert_vectors(vectors)
        elapsed = time.time() - start

        print(f"✅ 批量插入完成")
        print(f"   成功: {success_count}")
        print(f"   失败: {fail_count}")
        print(f"   总耗时: {elapsed:.2f}s")
        print(f"   平均每个: {elapsed/len(vectors)*1000:.2f}ms")

        store.close()
        return success_count == len(vectors)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_search():
    """测试4: 向量检索"""
    print("\n" + "="*60)
    print("测试4: 向量检索（Top 5）")
    print("="*60)

    try:
        store = VectorStore()

        # 生成查询向量
        query_vector = generate_random_vector()

        start = time.time()
        results = store.search_similar_vectors(
            query_embedding=query_vector,
            top_k=5,
            similarity_threshold=0.0
        )
        elapsed = time.time() - start

        print(f"✅ 检索完成")
        print(f"   耗时: {elapsed*1000:.2f}ms")
        print(f"   结果数: {len(results)}")

        if results:
            print(f"\n   Top 5 结果:")
            for i, result in enumerate(results[:5], 1):
                print(f"   {i}. chunk_id={result['chunk_id']}, "
                      f"similarity={result['similarity']:.4f}")

        store.close()
        return len(results) > 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_search_performance():
    """测试5: 检索性能（100次查询）"""
    print("\n" + "="*60)
    print("测试5: 检索性能测试（100次查询）")
    print("="*60)

    try:
        store = VectorStore()

        query_times = []

        for i in range(100):
            query_vector = generate_random_vector()

            start = time.time()
            results = store.search_similar_vectors(
                query_embedding=query_vector,
                top_k=10
            )
            elapsed = time.time() - start
            query_times.append(elapsed)

        avg_time = np.mean(query_times)
        p95_time = np.percentile(query_times, 95)
        p99_time = np.percentile(query_times, 99)

        print(f"✅ 性能测试完成")
        print(f"   平均耗时: {avg_time*1000:.2f}ms")
        print(f"   P95耗时: {p95_time*1000:.2f}ms")
        print(f"   P99耗时: {p99_time*1000:.2f}ms")
        print(f"   QPS: {1/avg_time:.2f} queries/sec")

        store.close()
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_document_search():
    """测试6: 文档内检索"""
    print("\n" + "="*60)
    print("测试6: 文档内检索")
    print("="*60)

    try:
        store = VectorStore()

        # 先插入同一文档的多个向量
        doc_id = "focused_doc_001"
        vectors = []
        for i in range(10):
            vectors.append({
                "document_id": doc_id,
                "chunk_id": f"{doc_id}_chunk_{i:03d}",
                "embedding": generate_random_vector()
            })

        store.batch_insert_vectors(vectors)

        # 检索
        query_vector = generate_random_vector()

        start = time.time()
        results = store.search_similar_vectors(
            query_embedding=query_vector,
            top_k=5,
            document_id=doc_id
        )
        elapsed = time.time() - start

        print(f"✅ 文档内检索完成")
        print(f"   耗时: {elapsed*1000:.2f}ms")
        print(f"   结果数: {len(results)}")

        # 验证所有结果都属于指定文档
        all_match = all(r['document_id'] == doc_id for r in results)
        print(f"   结果验证: {'✓ 所有结果来自目标文档' if all_match else '✗ 结果包含其他文档'}")

        store.close()
        return all_match

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_delete():
    """测试7: 删除向量"""
    print("\n" + "="*60)
    print("测试7: 删除向量")
    print("="*60)

    try:
        store = VectorStore()

        # 插入测试向量
        chunk_id = "test_delete_chunk"
        store.insert_vector("test_doc", chunk_id, generate_random_vector())

        # 验证存在
        exists_before = store.vector_exists(chunk_id)
        print(f"   删除前存在: {exists_before}")

        # 删除
        success = store.delete_vector(chunk_id)

        # 验证删除
        exists_after = store.vector_exists(chunk_id)
        print(f"   删除操作: {'成功' if success else '失败'}")
        print(f"   删除后存在: {exists_after}")

        store.close()
        return success and not exists_after

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_delete_document():
    """测试8: 删除文档所有向量"""
    print("\n" + "="*60)
    print("测试8: 删除文档所有向量")
    print("="*60)

    try:
        store = VectorStore()

        # 插入测试文档的多个向量
        doc_id = "test_delete_doc"
        vectors = []
        for i in range(5):
            vectors.append({
                "document_id": doc_id,
                "chunk_id": f"{doc_id}_chunk_{i}",
                "embedding": generate_random_vector()
            })

        store.batch_insert_vectors(vectors)

        # 验证插入
        count_before = store.get_vector_count(doc_id)
        print(f"   删除前向量数: {count_before}")

        # 删除文档
        deleted_count = store.delete_document_vectors(doc_id)

        # 验证删除
        count_after = store.get_vector_count(doc_id)
        print(f"   删除数量: {deleted_count}")
        print(f"   删除后向量数: {count_after}")

        store.close()
        return deleted_count == count_before and count_after == 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_stats():
    """测试9: 统计信息"""
    print("\n" + "="*60)
    print("测试9: 统计信息")
    print("="*60)

    try:
        store = VectorStore()

        stats = store.get_stats()

        print(f"✅ 统计信息获取成功")
        print(f"   总向量数: {stats.get('total_vectors', 0)}")
        print(f"   总文档数: {stats.get('total_documents', 0)}")
        print(f"   表大小: {stats.get('table_size', 'N/A')}")
        print(f"   模型分布:")
        for model in stats.get('models', []):
            print(f"     - {model['model_name']}: {model['count']}")

        store.close()
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_large_scale():
    """测试10: 大规模性能测试（1000个向量）"""
    print("\n" + "="*60)
    print("测试10: 大规模性能测试（1000个向量）")
    print("="*60)

    try:
        store = VectorStore()

        # 批量插入1000个向量
        print("   准备数据...")
        vectors = []
        for i in range(1000):
            vectors.append({
                "document_id": f"large_doc_{i//100:03d}",
                "chunk_id": f"large_chunk_{i:04d}",
                "embedding": generate_random_vector()
            })

        print("   开始插入...")
        start = time.time()
        success_count, fail_count = store.batch_insert_vectors(vectors)
        insert_time = time.time() - start

        print(f"   插入完成: {success_count}/{len(vectors)}")
        print(f"   插入耗时: {insert_time:.2f}s")
        print(f"   插入速率: {success_count/insert_time:.2f} vectors/sec")

        # 测试检索性能
        print("   测试检索性能...")
        query_times = []
        for _ in range(50):
            query_vector = generate_random_vector()
            start = time.time()
            results = store.search_similar_vectors(query_vector, top_k=10)
            query_times.append(time.time() - start)

        avg_query_time = np.mean(query_times)
        print(f"   平均检索耗时: {avg_query_time*1000:.2f}ms")
        print(f"   检索QPS: {1/avg_query_time:.2f}")

        store.close()
        return success_count == len(vectors)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("FieldMind 向量数据库测试套件")
    print("="*60)

    tests = [
        ("数据库连接", test_connection),
        ("单个向量插入", test_insert_single),
        ("批量插入", test_batch_insert),
        ("向量检索", test_search),
        ("检索性能", test_search_performance),
        ("文档内检索", test_document_search),
        ("删除向量", test_delete),
        ("删除文档", test_delete_document),
        ("统计信息", test_stats),
        ("大规模测试", test_large_scale),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            results.append((name, False))

    # 输出总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 通过")
    print(f"通过率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
