"""
简化版测试 - 验证核心3函数
直接测试，不依赖复杂环境
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_basic_chunking():
    """测试基础分块功能"""
    print("\n" + "="*60)
    print("测试: 基础文本分块")
    print("="*60)

    from app.processors.text_chunker import TextChunker

    chunker = TextChunker(chunk_size=50, chunk_overlap=10)

    text = """十八洞村的山歌很有特色。
村民们经常在田间唱山歌。
这些民歌传承了苗族文化。
山歌是当地重要的文化遗产。"""

    chunks = chunker.chunk(text)

    print(f"\n原文长度: {len(text)} 字符")
    print(f"生成分块: {len(chunks)} 个")

    for i, chunk in enumerate(chunks):
        print(f"\n块 {i}:")
        print(f"  索引: {chunk.sequence}")
        print(f"  Token数: {chunk.token_count}")
        print(f"  内容: {chunk.content[:50]}...")

    # 验证
    assert len(chunks) > 0, "应该生成至少1个块"
    assert chunks[0].sequence == 0, "第一个块的索引应该是0"
    assert all(c.token_count > 0 for c in chunks), "所有块都应该有token计数"

    print("\n✅ 基础分块测试通过")


def test_mock_vectorization():
    """测试Mock向量生成"""
    print("\n" + "="*60)
    print("测试: Mock 向量生成")
    print("="*60)

    from app.processors.vector_generator import MockEmbedding

    generator = MockEmbedding(dimension=384)

    texts = [
        "十八洞村的山歌很有特色。",
        "村民们经常在田间唱山歌。",
        "这些民歌传承了苗族文化。"
    ]

    embeddings = generator.generate(texts)

    print(f"\n输入文本: {len(texts)} 条")
    print(f"生成向量: {len(embeddings)} 个")
    print(f"向量维度: {len(embeddings[0])}")

    # 验证
    assert len(embeddings) == len(texts), "向量数量应该等于文本数量"
    assert all(len(e) == 384 for e in embeddings), "所有向量维度应该是384"

    print("\n✅ Mock向量生成测试通过")


def test_data_structure():
    """测试数据结构"""
    print("\n" + "="*60)
    print("测试: 核心数据结构")
    print("="*60)

    from app.processors.text_chunker import TextChunk

    # 创建测试chunk
    chunk = TextChunk(
        content="测试内容",
        sequence=0,
        token_count=10,
        start_index=0,
        end_index=10,
        metadata={"test": "data"}
    )

    print(f"\nChunk 对象:")
    print(f"  content: {chunk.content}")
    print(f"  sequence: {chunk.sequence}")
    print(f"  token_count: {chunk.token_count}")
    print(f"  metadata: {chunk.metadata}")

    # 验证
    assert chunk.content == "测试内容"
    assert chunk.sequence == 0
    assert chunk.token_count == 10

    print("\n✅ 数据结构测试通过")


def test_file_classification():
    """测试文件分类"""
    print("\n" + "="*60)
    print("测试: 文件分类")
    print("="*60)

    from app.services.file_classifier import FileClassifier

    # 测试不同文件类型
    test_cases = [
        ("test.pdf", "application/pdf", "document"),
        ("photo.jpg", "image/jpeg", "image"),
        ("song.mp3", "audio/mpeg", "audio"),
        ("video.mp4", "video/mp4", "video"),
        ("data.csv", "text/csv", "table"),
    ]

    for filename, mime_type, expected_type in test_cases:
        result = FileClassifier.classify(filename, mime_type)
        print(f"\n{filename}:")
        print(f"  分类: {result['type'].value}")
        print(f"  置信度: {result['confidence']}")
        print(f"  方法: {result['method']}")

        assert result['type'].value == expected_type, f"{filename} 分类错误"

    print("\n✅ 文件分类测试通过")


def main():
    """运行所有基础测试"""
    print("\n" + "="*60)
    print("FieldMind 核心功能基础测试")
    print("="*60)

    try:
        # 测试1: 文本分块
        test_basic_chunking()

        # 测试2: 向量生成
        test_mock_vectorization()

        # 测试3: 数据结构
        test_data_structure()

        # 测试4: 文件分类
        test_file_classification()

        # 汇总
        print("\n" + "="*60)
        print("🎉 所有基础测试通过！")
        print("="*60)
        print("\n验证完成:")
        print("  ✅ 文本分块 - 正常工作")
        print("  ✅ 向量生成 - Mock模式正常")
        print("  ✅ 数据结构 - 定义正确")
        print("  ✅ 文件分类 - 识别准确")
        print("\n核心组件已就绪，可以进行集成测试。")

        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
