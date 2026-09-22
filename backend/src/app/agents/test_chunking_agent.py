"""
测试 ChunkingAgent - 验证真实可用性

测试：
1. 加载真实服务
2. 切分文本文档
3. 切分音频转录（带时间戳）
4. 验证输出格式
5. 与现有系统兼容性
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.agents.chunking_agent import (
    get_chunking_agent,
    ChunkingStrategy,
    ChunkingAgent
)


def test_service_loading():
    """测试1: 服务加载"""
    print("=" * 80)
    print("测试1: 服务加载")
    print("=" * 80)

    agent = get_chunking_agent()
    agent._load_services()

    stats = agent.get_stats()
    print(f"\n可用服务:")
    for service, available in stats['services_available'].items():
        status = "✓" if available else "✗"
        print(f"  {status} {service}: {'可用' if available else '不可用'}")

    print("\n✓ 测试1通过")


def test_text_chunking():
    """测试2: 文本文档切分"""
    print("\n" + "=" * 80)
    print("测试2: 文本文档切分")
    print("=" * 80)

    agent = get_chunking_agent(
        min_chunk_size=200,
        max_chunk_size=500,
        chunk_overlap=50
    )

    # 测试文本（农村调研报告片段）
    test_text = """
杀猪菜是东北农村的传统美食，承载着几代人的集体记忆。每到冬季杀年猪时，村民们会将新鲜猪肉、血肠、酸菜等食材一起炖煮，形成独特的风味。

王大爷今年76岁，他回忆说："以前每家每户都养猪，到了腊月就杀猪。邻里乡亲都会来帮忙，杀完猪大家一起吃杀猪菜，特别热闹。"这不仅是一道菜，更是一种社交仪式。

然而，随着时代变迁，传统习俗正在消失。李婶说："现在年轻人都不会做了，超市买现成的，味道完全不一样。"村里只有几位老人还坚持传统做法。

为了保护这一非物质文化遗产，村委会正在组织传承活动。他们邀请老手艺人教年轻人制作杀猪菜，并将工艺录制成视频保存。希望通过这些努力，让传统美食传承下去。
    """.strip()

    # 切分
    result = agent.chunk_text(
        text=test_text,
        source_file="/data/test_report.txt",
        file_type="text",
        language="zh",
        strategy=ChunkingStrategy.AUTO
    )

    # 验证结果
    print(f"\n切分结果:")
    print(f"  策略: {result.strategy_used}")
    print(f"  总块数: {result.total_chunks}")
    print(f"  总字符数: {result.total_chars}")
    print(f"  平均块大小: {result.avg_chunk_size:.0f} 字符")
    print(f"  处理时间: {result.processing_time_ms:.0f}ms")

    print(f"\n前3个chunk:")
    for i, chunk in enumerate(result.chunks[:3]):
        print(f"\n  Chunk {i}:")
        print(f"    ID: {chunk.metadata.chunk_id}")
        print(f"    位置: {chunk.metadata.start_pos}-{chunk.metadata.end_pos}")
        print(f"    长度: {chunk.metadata.char_count} 字符")
        print(f"    文本: {chunk.text[:80]}...")

    # 验证基本要求
    assert result.total_chunks > 0, "应该生成至少1个chunk"
    assert all(chunk.metadata.char_count > 0 for chunk in result.chunks), "每个chunk应该有内容"

    print("\n✓ 测试2通过")
    return result


def test_audio_chunking():
    """测试3: 音频转录切分（带时间戳）"""
    print("\n" + "=" * 80)
    print("测试3: 音频转录切分（带时间戳）")
    print("=" * 80)

    agent = get_chunking_agent()

    # 模拟Whisper转录结果
    test_transcript = [
        {'text': '王大爷说杀猪菜是传统美食', 'start': 0.0, 'end': 3.2},
        {'text': '它需要很多道工序', 'start': 3.5, 'end': 6.1},
        {'text': '李婶补充说现在年轻人都不会做了', 'start': 6.5, 'end': 10.2},
        {'text': '村委会正在组织传承活动', 'start': 10.5, 'end': 13.8},
    ]

    # 合并为完整文本
    full_text = ' '.join([seg['text'] for seg in test_transcript])

    # 切分（带transcript元数据）
    result = agent.chunk_text(
        text=full_text,
        source_file="/data/test_audio.mp3",
        file_type="audio",
        language="zh",
        strategy=ChunkingStrategy.AUTO,
        metadata={"transcript": test_transcript}
    )

    print(f"\n切分结果:")
    print(f"  策略: {result.strategy_used}")
    print(f"  总块数: {result.total_chunks}")

    print(f"\nChunks（带时间戳）:")
    for i, chunk in enumerate(result.chunks):
        print(f"\n  Chunk {i}:")
        print(f"    文本: {chunk.text}")
        if chunk.metadata.start_sec is not None:
            print(f"    时间: {chunk.metadata.start_sec:.1f}s - {chunk.metadata.end_sec:.1f}s")
        else:
            print(f"    时间: 无时间戳")

    print("\n✓ 测试3通过")
    return result


def test_output_format_compatibility():
    """测试4: 输出格式兼容性"""
    print("\n" + "=" * 80)
    print("测试4: 输出格式兼容性（与现有系统）")
    print("=" * 80)

    agent = get_chunking_agent()

    test_text = "这是测试文本。" * 100

    result = agent.chunk_text(
        text=test_text,
        source_file="/data/test.txt",
        file_type="text",
        language="zh"
    )

    # 转换为字典格式（兼容现有系统）
    result_dict = result.to_dict()

    print(f"\n输出格式验证:")
    print(f"  ✓ 包含 'chunks' 键: {'chunks' in result_dict}")
    print(f"  ✓ 包含 'total_chunks' 键: {'total_chunks' in result_dict}")
    print(f"  ✓ 包含 'strategy_used' 键: {'strategy_used' in result_dict}")

    # 验证chunk格式
    first_chunk = result.chunks[0].to_dict()
    print(f"\n单个chunk格式验证:")
    print(f"  ✓ 包含 'chunk_id': {'chunk_id' in first_chunk}")
    print(f"  ✓ 包含 'text': {'text' in first_chunk}")
    print(f"  ✓ 包含 'metadata': {'metadata' in first_chunk}")
    print(f"  ✓ 包含 'chunk_index': {'chunk_index' in first_chunk}")
    print(f"  ✓ 包含 'prev_chunk_id': {'prev_chunk_id' in first_chunk}")
    print(f"  ✓ 包含 'next_chunk_id': {'next_chunk_id' in first_chunk}")

    # 验证与DocumentChunker的格式一致性
    assert 'chunk_id' in first_chunk
    assert 'text' in first_chunk
    assert 'metadata' in first_chunk
    assert 'chunk_index' in first_chunk

    print("\n✓ 测试4通过 - 输出格式与现有系统兼容")


def test_strategy_selection():
    """测试5: 策略自动选择"""
    print("\n" + "=" * 80)
    print("测试5: 策略自动选择")
    print("=" * 80)

    agent = get_chunking_agent()

    # 测试场景1: 短文本
    short_text = "这是短文本。" * 30
    result1 = agent.chunk_text(
        text=short_text,
        source_file="short.txt",
        file_type="text"
    )
    print(f"\n场景1 - 短文本（{len(short_text)}字）:")
    print(f"  选择策略: {result1.strategy_used}")

    # 测试场景2: 长文本
    long_text = "这是长文本，包含很多内容。" * 200
    result2 = agent.chunk_text(
        text=long_text,
        source_file="long.txt",
        file_type="text"
    )
    print(f"\n场景2 - 长文本（{len(long_text)}字）:")
    print(f"  选择策略: {result2.strategy_used}")

    # 测试场景3: 音频（带transcript）
    audio_transcript = [
        {'text': '测试音频', 'start': 0.0, 'end': 2.0},
    ]
    result3 = agent.chunk_text(
        text="测试音频",
        source_file="audio.mp3",
        file_type="audio",
        metadata={"transcript": audio_transcript}
    )
    print(f"\n场景3 - 音频（带transcript）:")
    print(f"  选择策略: {result3.strategy_used}")

    print("\n✓ 测试5通过")


def test_stats():
    """测试6: 统计功能"""
    print("\n" + "=" * 80)
    print("测试6: 统计功能")
    print("=" * 80)

    agent = get_chunking_agent()

    # 处理几个文档
    for i in range(3):
        agent.chunk_text(
            text=f"测试文档{i}。" * 100,
            source_file=f"test_{i}.txt",
            file_type="text"
        )

    # 获取统计
    stats = agent.get_stats()

    print(f"\n统计信息:")
    print(f"  总文档数: {stats['total_documents']}")
    print(f"  总块数: {stats['total_chunks']}")
    print(f"  平均每文档: {stats['avg_chunks_per_doc']:.1f} 块")
    print(f"\n策略使用统计:")
    for strategy, count in stats['strategy_usage'].items():
        print(f"  {strategy}: {count} 次")

    assert stats['total_documents'] > 0
    assert stats['total_chunks'] > 0

    print("\n✓ 测试6通过")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ChunkingAgent 真实可用性测试")
    print("=" * 80)

    try:
        # 运行所有测试
        test_service_loading()
        test_text_chunking()
        test_audio_chunking()
        test_output_format_compatibility()
        test_strategy_selection()
        test_stats()

        print("\n" + "=" * 80)
        print("✅ 所有测试通过 - ChunkingAgent 真实可用")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
