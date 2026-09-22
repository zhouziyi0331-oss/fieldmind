"""
VectorizationAgent 测试

验证VectorizationAgent真实可用：
1. 服务加载测试
2. 向量化测试
3. 多策略测试
4. 输出格式兼容性测试
5. 语义检索测试
6. 统计功能测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.agents.vectorization_agent import (
    VectorizationAgent,
    VectorizationStrategy,
    VectorizedChunk,
    VectorizationResult
)


def test_service_loading():
    """测试1: 验证真实服务加载"""
    print("\n" + "=" * 70)
    print("测试1: 服务加载")
    print("=" * 70)

    agent = VectorizationAgent()

    # 测试加载主服务
    try:
        service = agent._load_vectorization_service()
        assert service is not None
        print("✅ VectorizationService加载成功")
        print(f"   模型: {service.model_name}")
        print(f"   维度: {service.embedding_dim}")
    except Exception as e:
        print(f"❌ VectorizationService加载失败: {e}")

    # 测试加载TF-IDF服务
    try:
        service = agent._load_tfidf_service()
        assert service is not None
        print("✅ TfidfVectorizationService加载成功")
        print(f"   模型: {service.model_name}")
        print(f"   维度: {service.embedding_dim}")
    except Exception as e:
        print(f"❌ TfidfVectorizationService加载失败: {e}")


def test_vectorization_chinese():
    """测试2: 中文文本向量化"""
    print("\n" + "=" * 70)
    print("测试2: 中文文本向量化")
    print("=" * 70)

    agent = VectorizationAgent(default_strategy=VectorizationStrategy.FLAG_EMBEDDING)

    test_chunks = [
        {
            "chunk_id": "chunk_0001",
            "text": "布依族是中国西南地区的少数民族，主要分布在贵州省。",
            "metadata": {
                "source_file": "buyi_culture.txt",
                "file_type": "text",
                "chunk_index": 0
            }
        },
        {
            "chunk_id": "chunk_0002",
            "text": "布依族的传统服饰色彩鲜艳，工艺精湛，展现了独特的民族文化。",
            "metadata": {
                "source_file": "buyi_culture.txt",
                "file_type": "text",
                "chunk_index": 1
            }
        },
        {
            "chunk_id": "chunk_0003",
            "text": "布依族的山歌是重要的文化遗产，传承着民族的历史和智慧。",
            "metadata": {
                "source_file": "buyi_culture.txt",
                "file_type": "text",
                "chunk_index": 2
            }
        }
    ]

    result = agent.vectorize_chunks(test_chunks)

    assert result is not None
    assert result.success_count == len(test_chunks)
    assert result.strategy == VectorizationStrategy.FLAG_EMBEDDING.value
    assert result.embedding_dim > 0
    assert len(result.chunks) == len(test_chunks)

    print(f"✅ 向量化成功")
    print(f"   策略: {result.strategy}")
    print(f"   模型: {result.embedding_model}")
    print(f"   维度: {result.embedding_dim}")
    print(f"   成功: {result.success_count}/{result.total_chunks}")
    print(f"   耗时: {result.duration_seconds:.3f}s")

    # 验证每个chunk
    for i, chunk in enumerate(result.chunks):
        assert chunk.chunk_id == test_chunks[i]["chunk_id"]
        assert chunk.text == test_chunks[i]["text"]
        assert len(chunk.embedding) == result.embedding_dim
        assert chunk.embedding_model == result.embedding_model
        print(f"   Chunk {i+1}: {chunk.chunk_id} - 向量维度={len(chunk.embedding)}")


def test_strategy_selection():
    """测试3: 策略自动选择"""
    print("\n" + "=" * 70)
    print("测试3: 策略自动选择")
    print("=" * 70)

    agent = VectorizationAgent(default_strategy=VectorizationStrategy.AUTO)

    # 中文文本 - 应该选择FLAG_EMBEDDING
    chinese_chunks = [
        {
            "chunk_id": "cn_001",
            "text": "这是中文文本，应该使用FlagEmbedding进行向量化。",
            "metadata": {}
        }
    ]

    selected = agent._select_strategy(chinese_chunks, VectorizationStrategy.AUTO)
    assert selected == VectorizationStrategy.FLAG_EMBEDDING
    print(f"✅ 中文文本 -> {selected.value}")

    # 英文文本 - 应该选择SENTENCE_TRANSFORMER
    english_chunks = [
        {
            "chunk_id": "en_001",
            "text": "This is an English text that should use SentenceTransformer.",
            "metadata": {}
        }
    ]

    selected = agent._select_strategy(english_chunks, VectorizationStrategy.AUTO)
    assert selected == VectorizationStrategy.SENTENCE_TRANSFORMER
    print(f"✅ 英文文本 -> {selected.value}")


def test_tfidf_strategy():
    """测试4: TF-IDF策略（无需网络）"""
    print("\n" + "=" * 70)
    print("测试4: TF-IDF策略")
    print("=" * 70)

    agent = VectorizationAgent(
        default_strategy=VectorizationStrategy.TFIDF,
        embedding_dim=384
    )

    test_chunks = [
        {
            "chunk_id": "tfidf_001",
            "text": "乡村振兴战略是中国农村发展的重要方针。",
            "metadata": {}
        },
        {
            "chunk_id": "tfidf_002",
            "text": "传统文化保护需要社区的共同努力。",
            "metadata": {}
        }
    ]

    result = agent.vectorize_chunks(test_chunks, strategy=VectorizationStrategy.TFIDF)

    assert result is not None
    assert result.success_count == len(test_chunks)
    assert result.strategy == VectorizationStrategy.TFIDF.value
    assert result.embedding_dim == 384

    print(f"✅ TF-IDF向量化成功")
    print(f"   策略: {result.strategy}")
    print(f"   模型: {result.embedding_model}")
    print(f"   维度: {result.embedding_dim}")
    print(f"   成功: {result.success_count}/{result.total_chunks}")


def test_output_format():
    """测试5: 输出格式兼容性"""
    print("\n" + "=" * 70)
    print("测试5: 输出格式兼容性")
    print("=" * 70)

    agent = VectorizationAgent()

    test_chunks = [
        {
            "chunk_id": "format_001",
            "text": "测试输出格式是否符合预期。",
            "metadata": {
                "source_file": "test.txt",
                "chunk_index": 0,
                "start_pos": 0,
                "end_pos": 50
            }
        }
    ]

    result = agent.vectorize_chunks(test_chunks)

    # 验证VectorizationResult格式
    assert hasattr(result, 'chunks')
    assert hasattr(result, 'strategy')
    assert hasattr(result, 'embedding_model')
    assert hasattr(result, 'embedding_dim')
    assert hasattr(result, 'total_chunks')
    assert hasattr(result, 'success_count')
    assert hasattr(result, 'failed_count')
    assert hasattr(result, 'duration_seconds')

    # 验证VectorizedChunk格式
    chunk = result.chunks[0]
    assert hasattr(chunk, 'chunk_id')
    assert hasattr(chunk, 'text')
    assert hasattr(chunk, 'embedding')
    assert hasattr(chunk, 'embedding_model')
    assert hasattr(chunk, 'embedding_dim')
    assert hasattr(chunk, 'metadata')
    assert hasattr(chunk, 'vectorized_at')

    # 验证embedding是列表且包含浮点数
    assert isinstance(chunk.embedding, list)
    assert len(chunk.embedding) > 0
    assert all(isinstance(x, (int, float)) for x in chunk.embedding)

    print("✅ 输出格式验证通过")
    print(f"   VectorizationResult: ✓")
    print(f"   VectorizedChunk: ✓")
    print(f"   embedding类型: list[float]")
    print(f"   metadata保留: {chunk.metadata}")


def test_batch_processing():
    """测试6: 批量处理"""
    print("\n" + "=" * 70)
    print("测试6: 批量处理")
    print("=" * 70)

    agent = VectorizationAgent(batch_size=5)

    # 创建20个chunks进行批量测试
    test_chunks = [
        {
            "chunk_id": f"batch_{i:03d}",
            "text": f"这是第{i+1}个测试文本块，用于验证批量处理功能。",
            "metadata": {"batch_index": i}
        }
        for i in range(20)
    ]

    result = agent.vectorize_chunks(test_chunks)

    assert result.success_count == 20
    assert len(result.chunks) == 20

    print(f"✅ 批量处理成功")
    print(f"   总数: {result.total_chunks}")
    print(f"   成功: {result.success_count}")
    print(f"   失败: {result.failed_count}")
    print(f"   耗时: {result.duration_seconds:.3f}s")
    print(f"   平均速度: {result.total_chunks/result.duration_seconds:.1f} chunks/s")


def test_stats():
    """测试7: 统计功能"""
    print("\n" + "=" * 70)
    print("测试7: 统计功能")
    print("=" * 70)

    agent = VectorizationAgent()

    # 执行多次向量化
    for i in range(3):
        chunks = [
            {
                "chunk_id": f"stats_{i}_{j}",
                "text": f"统计测试文本 {i}-{j}",
                "metadata": {}
            }
            for j in range(5)
        ]
        agent.vectorize_chunks(chunks)

    stats = agent.get_stats()

    assert stats["total_vectorized"] == 15  # 3次 × 5个
    assert "service_usage" in stats
    assert "errors" in stats

    print("✅ 统计功能正常")
    print(f"   总向量化数: {stats['total_vectorized']}")
    print(f"   服务使用统计: {stats['service_usage']}")
    print(f"   默认策略: {stats['default_strategy']}")
    print(f"   向量维度: {stats['embedding_dim']}")
    print(f"   批大小: {stats['batch_size']}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 VectorizationAgent 完整测试套件")
    print("=" * 70)

    tests = [
        ("服务加载", test_service_loading),
        ("中文向量化", test_vectorization_chinese),
        ("策略选择", test_strategy_selection),
        ("TF-IDF策略", test_tfidf_strategy),
        ("输出格式", test_output_format),
        ("批量处理", test_batch_processing),
        ("统计功能", test_stats),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {name} 测试通过")
        except AssertionError as e:
            failed += 1
            print(f"❌ {name} 测试失败: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"测试总结: {passed} 通过, {failed} 失败")
    print("=" * 70)

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_all_tests()
    sys.exit(0 if failed == 0 else 1)
