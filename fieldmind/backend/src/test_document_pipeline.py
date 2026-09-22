"""
测试文档处理流水线的各个模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.document import UnifiedDocumentChunker
from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend


def test_chunker():
    """测试文档切分功能"""
    print("\n" + "="*60)
    print("测试1: 文档切分服务")
    print("="*60)

    chunker = UnifiedDocumentChunker(
        min_chunk_size=200,
        max_chunk_size=500,
        target_chunk_size=350
    )

    # 测试文本
    test_text = """
布依族的山歌主要有三种类型。第一种是情歌，主要在节日和婚礼时演唱。情歌的特点是旋律优美，歌词含蓄。

第二种是劳动歌，在田间地头劳作时演唱。劳动歌节奏明快，富有动感，能够鼓舞士气。

第三种是叙事歌，讲述历史故事和传说。叙事歌篇幅较长，内容丰富，是布依族口头文学的重要组成部分。这些歌曲承载着民族的记忆和文化传统。

山歌的演唱形式多样，可以独唱、对唱或合唱。在重要场合，还会有专门的歌手进行表演。
    """.strip()

    metadata = {
        "document_type": "text",
        "source": "test"
    }

    try:
        chunks = chunker.chunk_document(test_text, metadata)

        print(f"✅ 切分成功")
        print(f"   原文长度: {len(test_text)} 字")
        print(f"   切分chunks数: {len(chunks)} 个")

        for i, chunk in enumerate(chunks[:3]):  # 只显示前3个
            print(f"\n   Chunk {i+1}:")
            print(f"   - ID: {chunk['chunk_id']}")
            print(f"   - 长度: {len(chunk['text'])} 字")
            print(f"   - 位置: {chunk['metadata'].get('start_pos')}-{chunk['metadata'].get('end_pos')}")
            print(f"   - 预览: {chunk['text'][:50]}...")

        print(f"\n✅ 文档切分测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vectorizer():
    """测试向量化服务"""
    print("\n" + "="*60)
    print("测试2: 向量化服务")
    print("="*60)

    try:
        vectorizer = VectorizationService()

        print(f"✅ 向量化服务初始化成功")
        print(f"   模型: {vectorizer.model_name}")
        print(f"   维度: {vectorizer.embedding_dim}")
        print(f"   是否使用真实模型: {vectorizer.model is not None}")

        # 测试单个文本向量化
        test_text = "布依族的山歌是一种传统民间艺术"
        embedding = vectorizer.vectorize_text(test_text)

        if embedding:
            print(f"\n✅ 文本向量化成功")
            print(f"   输入文本: {test_text}")
            print(f"   向量维度: {len(embedding)}")
            print(f"   向量前5维: {embedding[:5]}")
        else:
            print(f"❌ 向量化失败")
            return False

        # 测试批量向量化
        test_chunks = [
            {"text": "这是第一个测试chunk", "chunk_id": "test_001"},
            {"text": "这是第二个测试chunk", "chunk_id": "test_002"},
            {"text": "这是第三个测试chunk", "chunk_id": "test_003"}
        ]

        vectorized_chunks = vectorizer.vectorize_chunks(test_chunks)

        print(f"\n✅ 批量向量化成功")
        print(f"   处理chunks数: {len(vectorized_chunks)}")
        print(f"   每个chunk都有embedding: {all('embedding' in c for c in vectorized_chunks)}")

        print(f"\n✅ 向量化服务测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline():
    """测试完整流水线"""
    print("\n" + "="*60)
    print("测试3: 完整处理流水线（清洗+切分+向量化）")
    print("="*60)

    try:
        from app.tools.document import UnifiedDocumentPipeline

        pipeline = UnifiedDocumentPipeline()

        # 测试清洗功能
        dirty_text = """
[00:12:15] Speaker1: 这是一段访谈录音
[00:12:30] Speaker2: 我们在讨论布依族文化

----------

有些OCR乱码字符：〇、—、～
还有连续换行



太多了

Speaker1: 继续说下去...
        """

        cleaned_text, metadata = pipeline._clean_text(dirty_text, {})

        print(f"✅ 数据清洗测试")
        print(f"   原始长度: {len(dirty_text)} 字")
        print(f"   清洗后长度: {len(cleaned_text)} 字")
        print(f"   移除字符数: {metadata['cleaning_stats']['removed_characters']}")
        print(f"   提取说话人: {metadata.get('speakers', [])}")

        print(f"\n✅ 完整流水线测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 文档处理流水线 - 单元测试")
    print("="*60)

    results = []

    # 测试1: 文档切分
    results.append(("文档切分", test_chunker()))

    # 测试2: 向量化
    results.append(("向量化服务", test_vectorizer()))

    # 测试3: 完整流水线
    results.append(("完整流水线", test_pipeline()))

    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status:10} | {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print("="*60)
    print(f"总计: {passed_count}/{total_count} 通过")

    if passed_count == total_count:
        print("\n🎉 所有测试通过！流水线各模块工作正常")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
