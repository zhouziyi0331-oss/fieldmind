#!/usr/bin/env python3
"""
深度RAG对话系统使用示例
Deep RAG Chat Service Usage Examples

演示如何使用深度RAG服务进行：
1. 单轮对话
2. 多轮对话
3. 多源检索
4. 引用溯源
"""

import asyncio
import json
from app.services.deep_rag_service import get_deep_rag_service


async def example_01_basic_chat():
    """示例1: 基础单轮对话"""
    print("\n" + "="*70)
    print("示例1: 基础单轮对话")
    print("="*70)

    service = get_deep_rag_service()

    result = await service.deep_chat(
        query="傈僳族的传统节日有哪些？",
        session_id="example_session_01",
        project_id=1,
        use_context=False,
        top_k=5,
        llm_provider='anthropic'  # 或 'openai', 'ollama'
    )

    print(f"\n📝 问题: 傈僳族的传统节日有哪些？")
    print(f"\n💬 AI回答:")
    print(result['answer'])
    print(f"\n📊 元数据:")
    print(f"  - 置信度: {result['confidence']:.2f}")
    print(f"  - 使用的检索源: {', '.join(result['sources_used'])}")
    print(f"  - 引用数量: {len(result['citations'])}")

    if result['citations']:
        print(f"\n📚 引用来源:")
        for idx, citation in enumerate(result['citations'][:3], 1):
            print(f"  [{idx}] {citation['source']}: {citation['text'][:100]}...")


async def example_02_multi_turn_chat():
    """示例2: 多轮对话上下文"""
    print("\n" + "="*70)
    print("示例2: 多轮对话上下文")
    print("="*70)

    service = get_deep_rag_service()
    session_id = "example_session_02"

    # 第一轮
    print("\n🔵 第一轮对话")
    result1 = await service.deep_chat(
        query="傈僳族主要分布在哪里？",
        session_id=session_id,
        project_id=1,
        use_context=True
    )
    print(f"问题: 傈僳族主要分布在哪里？")
    print(f"回答: {result1['answer'][:200]}...")

    # 第二轮（依赖上下文）
    print("\n🔵 第二轮对话（依赖上下文）")
    result2 = await service.deep_chat(
        query="那里的气候怎么样？",  # "那里"指代第一轮的地点
        session_id=session_id,
        project_id=1,
        use_context=True
    )
    print(f"问题: 那里的气候怎么样？")
    print(f"回答: {result2['answer'][:200]}...")

    # 第三轮
    print("\n🔵 第三轮对话")
    result3 = await service.deep_chat(
        query="这种气候对当地农业有什么影响？",
        session_id=session_id,
        project_id=1,
        use_context=True
    )
    print(f"问题: 这种气候对当地农业有什么影响？")
    print(f"回答: {result3['answer'][:200]}...")

    # 查看对话历史
    history = service.get_conversation_history(session_id)
    print(f"\n📝 对话历史: 共 {len(history)} 条消息（{len(history)//2} 轮对话）")


async def example_03_multi_source_retrieve():
    """示例3: 多源并行检索"""
    print("\n" + "="*70)
    print("示例3: 多源并行检索（不生成回答）")
    print("="*70)

    service = get_deep_rag_service()

    result = await service.multi_source_retrieve(
        query="傈僳族的弩弓制作技艺",
        project_id=1,
        top_k=3,
        enabled_sources=['vector', 'lightrag', 'neo4j']  # 只使用这3个源
    )

    print(f"\n🔍 检索统计:")
    print(f"  - 启用的检索源: 3")
    print(f"  - 成功检索源: {result['metadata']['successful_sources']}")
    print(f"  - 总结果数: {result['metadata']['total_results']}")
    print(f"  - 引用数量: {result['metadata']['total_citations']}")

    print(f"\n📊 各源检索结果:")
    for source_name, source_data in result['results'].items():
        if 'error' in source_data:
            print(f"  ❌ {source_name}: {source_data['error']}")
        else:
            results = source_data.get('results', [])
            print(f"  ✅ {source_name}: {len(results)} 条结果")
            if results:
                print(f"     示例: {str(results[0])[:100]}...")


async def example_04_citation_tracing():
    """示例4: 引用溯源"""
    print("\n" + "="*70)
    print("示例4: 引用溯源 - 追踪信息来源")
    print("="*70)

    service = get_deep_rag_service()

    result = await service.deep_chat(
        query="傈僳族的四声部合唱有什么特点？",
        session_id="example_session_04",
        project_id=1,
        top_k=5
    )

    print(f"\n💬 AI回答:")
    print(result['answer'])

    print(f"\n📚 引用溯源详情:")
    for idx, citation in enumerate(result['citations'], 1):
        print(f"\n引用 {idx}:")
        print(f"  来源: {citation['source']}")
        print(f"  置信度: {citation['confidence']:.3f}")
        print(f"  文本: {citation['text'][:150]}...")

        # 文档追踪信息
        if 'document_id' in citation:
            print(f"  📄 文档ID: {citation['document_id']}")
        if 'document_name' in citation:
            print(f"  📄 文档名: {citation['document_name']}")
        if 'page' in citation:
            print(f"  📄 页码: {citation['page']}")
        if 'chunk_id' in citation:
            print(f"  📄 块ID: {citation['chunk_id']}")


async def example_05_selective_sources():
    """示例5: 选择性检索源"""
    print("\n" + "="*70)
    print("示例5: 选择性启用检索源")
    print("="*70)

    service = get_deep_rag_service()

    # 场景1: 只用向量检索（最快）
    print("\n🎯 场景1: 只使用向量检索")
    result1 = await service.multi_source_retrieve(
        query="傈僳族的民歌",
        project_id=1,
        top_k=3,
        enabled_sources=['vector']
    )
    print(f"  耗时最短，结果数: {result1['metadata']['total_results']}")

    # 场景2: 向量+图谱（平衡）
    print("\n🎯 场景2: 向量+知识图谱")
    result2 = await service.multi_source_retrieve(
        query="傈僳族的民歌",
        project_id=1,
        top_k=3,
        enabled_sources=['vector', 'lightrag', 'neo4j']
    )
    print(f"  结构化信息，结果数: {result2['metadata']['total_results']}")

    # 场景3: 全部源（最全面）
    print("\n🎯 场景3: 启用所有检索源")
    result3 = await service.multi_source_retrieve(
        query="傈僳族的民歌",
        project_id=1,
        top_k=3,
        enabled_sources=None  # None表示全部
    )
    print(f"  最全面，结果数: {result3['metadata']['total_results']}")


async def example_06_fusion_ranking():
    """示例6: RRF融合排序"""
    print("\n" + "="*70)
    print("示例6: RRF融合排序算法")
    print("="*70)

    service = get_deep_rag_service()

    # 先检索
    retrieval_result = await service.multi_source_retrieve(
        query="傈僳族的阔时节",
        project_id=1,
        top_k=5
    )

    print(f"\n📥 检索结果: {retrieval_result['metadata']['total_results']} 条")

    # 使用RRF融合
    fused_results = service.rank_and_fuse(
        multi_source_results=retrieval_result,
        fusion_method='rrf',
        top_k=10
    )

    print(f"\n📊 RRF融合排序 Top 10:")
    for idx, result in enumerate(fused_results, 1):
        source = result.get('source', 'unknown')
        score = result.get('fusion_score', 0.0)
        text_preview = result.get('text', '')[:80]
        print(f"{idx:2d}. [{source:10s}] 分数={score:.4f} | {text_preview}...")


async def example_07_batch_queries():
    """示例7: 批量查询（模拟）"""
    print("\n" + "="*70)
    print("示例7: 批量查询处理")
    print("="*70)

    service = get_deep_rag_service()

    queries = [
        "傈僳族的传统节日有哪些？",
        "傈僳族的民歌特点是什么？",
        "傈僳族的弩弓制作技艺如何传承？"
    ]

    print(f"\n处理 {len(queries)} 个批量查询...\n")

    results = []
    for idx, query in enumerate(queries, 1):
        print(f"[{idx}/{len(queries)}] 处理中: {query}")

        result = await service.deep_chat(
            query=query,
            session_id=f"batch_{idx}",  # 独立会话
            project_id=1,
            use_context=False  # 批量不使用上下文
        )

        results.append({
            'query': query,
            'answer': result['answer'][:100] + '...',
            'confidence': result['confidence'],
            'sources_count': len(result['sources_used'])
        })

        print(f"  ✅ 完成，置信度: {result['confidence']:.2f}")

    print(f"\n📊 批量结果汇总:")
    for idx, result in enumerate(results, 1):
        print(f"\n{idx}. {result['query']}")
        print(f"   置信度: {result['confidence']:.2f}, 检索源: {result['sources_count']}")
        print(f"   回答: {result['answer']}")


async def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("🎯 深度RAG对话系统使用示例")
    print("="*70)

    # 检查服务健康
    service = get_deep_rag_service()
    health = service.health_check()

    print(f"\n✅ 服务状态: {health['status']}")
    print(f"  - 可用检索源: {len(health['available_sources'])}")
    print(f"  - 检索源列表: {', '.join(health['available_sources'][:5])}...")

    # 运行示例（需要配置LLM API Key）
    try:
        # 示例1-2需要LLM API Key
        # await example_01_basic_chat()
        # await example_02_multi_turn_chat()

        # 示例3-7不需要LLM
        await example_03_multi_source_retrieve()
        # await example_04_citation_tracing()
        await example_05_selective_sources()
        await example_06_fusion_ranking()
        # await example_07_batch_queries()

        print("\n" + "="*70)
        print("✅ 所有示例执行完成")
        print("="*70)

    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
