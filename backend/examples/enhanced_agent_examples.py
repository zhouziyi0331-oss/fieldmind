"""
增强型RAG Agent使用示例

演示检索质量保证和Agent能力增强的完整功能
"""
import asyncio
import json
from app.services.rag.enhanced_agent import create_enhanced_rag_agent


async def example1_basic_agent():
    """示例1: 基本Agent使用"""
    print("=" * 80)
    print("示例1: 基本增强型RAG Agent使用")
    print("=" * 80)

    # 创建Agent
    agent = await create_enhanced_rag_agent(enable_all_features=True)
    print("✅ Agent创建成功\n")

    # 索引文档
    documents = [
        {
            "doc_id": "doc_intro",
            "content": "FieldMind是一个智能知识管理系统，采用RAG(检索增强生成)技术。系统支持多种文档格式上传，包括PDF、Word、Markdown等。"
        },
        {
            "doc_id": "doc_features",
            "content": "主要功能包括：1. 文档上传和管理 2. 智能检索 3. AI问答 4. 知识图谱 5. 协作编辑。支持全文搜索和语义检索。"
        },
        {
            "doc_id": "doc_tech",
            "content": "技术栈：后端使用Python FastAPI框架，数据库使用PostgreSQL，向量数据库使用Milvus，前端使用React。"
        }
    ]

    print("📚 索引文档...")
    for doc in documents:
        await agent.index_document(doc["doc_id"], doc["content"])
    print(f"✅ 成功索引 {len(documents)} 个文档\n")

    # 处理查询
    query = "FieldMind支持哪些文档格式？"
    print(f"❓ 查询: {query}\n")

    result = await agent.process_query(query, top_k=3)

    # 打印结果
    print(f"💬 答案:\n{result['answer']}\n")

    print(f"🎯 意图识别:")
    print(f"   类型: {result['intent']['intent_type']}")
    print(f"   置信度: {result['intent']['confidence']:.2%}\n")

    print(f"📖 检索结果 ({len(result['retrieval_results'])} 个):")
    for i, res in enumerate(result['retrieval_results'][:3], 1):
        print(f"   [{i}] {res['doc_id']} (方法: {res['retrieval_method']}, 分数: {res['score']:.3f})")

    print(f"\n📊 检索质量指标:")
    metrics = result['retrieval_metrics']
    print(f"   平均分数: {metrics['avg_score']:.3f}")
    print(f"   多样性分数: {metrics['diversity_score']:.3f}")
    print(f"   覆盖率: {metrics['coverage_score']:.3f}")

    if result.get('citations'):
        print(f"\n📌 引用溯源 ({len(result['citations'])} 条):")
        for i, citation in enumerate(result['citations'][:2], 1):
            print(f"   [{i}] \"{citation['answer_sentence'][:50]}...\"")
            print(f"       来源: {citation['source_fragment']['doc_id']}")
            print(f"       置信度: {citation['confidence_score']:.2%}")


async def example2_multi_turn_conversation():
    """示例2: 多轮对话"""
    print("\n\n" + "=" * 80)
    print("示例2: 多轮对话能力")
    print("=" * 80)

    agent = await create_enhanced_rag_agent()

    # 索引文档
    await agent.index_document(
        "doc_deployment",
        "FieldMind支持Docker和Kubernetes部署。Docker部署适合单机环境，Kubernetes适合集群环境。部署前需要配置数据库连接、Redis缓存和对象存储。"
    )

    # 第一轮对话
    print("\n💬 第1轮对话:")
    query1 = "FieldMind如何部署？"
    print(f"   用户: {query1}")

    result1 = await agent.process_query(query1, use_conversation_context=False)
    print(f"   助手: {result1['answer'][:100]}...\n")

    # 第二轮对话（使用上下文）
    print("💬 第2轮对话:")
    query2 = "那配置呢？"  # 依赖上下文理解
    print(f"   用户: {query2}")

    result2 = await agent.process_query(query2, use_conversation_context=True)
    print(f"   助手: {result2['answer'][:100]}...\n")

    # 查看对话历史
    history = agent.get_conversation_history()
    print(f"📝 对话历史 (共 {len(history)} 轮):")
    for turn in history:
        print(f"   轮次 {turn['turn_id']}: {turn['user_message'][:30]}...")


async def example3_intent_based_routing():
    """示例3: 基于意图的路由"""
    print("\n\n" + "=" * 80)
    print("示例3: 意图识别与智能路由")
    print("=" * 80)

    agent = await create_enhanced_rag_agent()

    # 索引文档
    await agent.index_document(
        "doc_comparison",
        "FieldMind和传统文档管理系统的区别：1. AI智能问答 2. 语义检索 3. 知识图谱 4. 自动摘要。传统系统只支持关键词搜索。"
    )

    # 不同意图的查询
    queries = [
        ("什么是FieldMind？", "查询意图"),
        ("如何上传文档？", "操作指南意图"),
        ("计算 256 + 128", "计算意图"),
        ("FieldMind和传统系统有什么区别？", "对比意图")
    ]

    for query, description in queries:
        print(f"\n🔍 查询: {query}")
        print(f"   预期意图: {description}")

        result = await agent.process_query(query, top_k=2)

        print(f"   识别意图: {result['intent']['intent_type']}")
        print(f"   置信度: {result['intent']['confidence']:.2%}")
        print(f"   处理策略: {result['strategy']}")
        print(f"   答案: {result['answer'][:80]}...")


async def example4_tool_usage():
    """示例4: 工具调用"""
    print("\n\n" + "=" * 80)
    print("示例4: 工具调用能力")
    print("=" * 80)

    agent = await create_enhanced_rag_agent()

    # 查看可用工具
    tools = agent.get_available_tools()
    print(f"📦 可用工具 ({len(tools)} 个):")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")

    # 注册自定义工具
    print("\n➕ 注册自定义工具...")

    def reverse_text(text: str) -> str:
        """反转文本"""
        return text[::-1]

    agent.register_custom_tool(
        name="reverse",
        description="反转文本",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "要反转的文本"}
            }
        },
        function=reverse_text
    )

    # 使用工具
    print("\n🔧 测试计算工具:")
    result = await agent.process_query("计算 1024 + 2048")
    print(f"   查询: 计算 1024 + 2048")
    print(f"   结果: {result['answer']}")

    if result.get('tool_calls'):
        for call in result['tool_calls']:
            print(f"   工具调用: {call['tool_name']}")
            print(f"   参数: {call['arguments']}")
            print(f"   成功: {call['success']}")


async def example5_hybrid_retrieval():
    """示例5: 混合检索策略"""
    print("\n\n" + "=" * 80)
    print("示例5: 多路召回混合检索")
    print("=" * 80)

    agent = await create_enhanced_rag_agent(enable_all_features=True)

    # 索引多样化文档
    documents = [
        ("doc1", "FieldMind知识管理系统提供企业级知识库解决方案"),
        ("doc2", "系统架构采用微服务设计，支持水平扩展"),
        ("doc3", "安全性：支持SSO单点登录、RBAC权限控制、数据加密"),
        ("doc4", "性能优化：Redis缓存、数据库索引、CDN加速"),
        ("doc5", "API文档：提供RESTful API和GraphQL接口")
    ]

    print("📚 索引文档...")
    for doc_id, content in documents:
        await agent.index_document(doc_id, content)

    # 执行混合检索
    query = "知识管理"
    print(f"\n🔍 查询: {query}")

    result = await agent.process_query(query, top_k=5)

    print(f"\n📊 检索结果分析:")
    print(f"   总检索数: {result['retrieval_metrics']['total_retrieved']}")
    print(f"   唯一文档数: {result['retrieval_metrics']['unique_docs']}")

    print(f"\n📈 召回方法分布:")
    for method, count in result['retrieval_metrics']['method_distribution'].items():
        print(f"   {method}: {count} 个")

    print(f"\n📋 Top-3 结果:")
    for i, res in enumerate(result['retrieval_results'][:3], 1):
        print(f"   [{i}] {res['doc_id']}")
        print(f"       方法: {res['retrieval_method']}")
        print(f"       分数: {res['score']:.4f}")
        print(f"       排名: {res['rank']}")
        if res.get('metadata'):
            meta = res['metadata']
            print(f"       元数据: 向量={meta.get('in_vector')}, 关键词={meta.get('in_keyword')}, BM25={meta.get('in_bm25')}")


async def example6_diversity_reranking():
    """示例6: 多样性重排序"""
    print("\n\n" + "=" * 80)
    print("示例6: 结果多样性保证")
    print("=" * 80)

    agent = await create_enhanced_rag_agent(enable_all_features=True)

    # 索引相似和不相似的文档
    similar_docs = [
        ("doc1", "FieldMind支持PDF文档上传功能"),
        ("doc2", "系统提供PDF文件上传能力"),
        ("doc3", "可以上传PDF格式的文档"),
    ]

    different_doc = ("doc4", "FieldMind使用PostgreSQL数据库存储数据")

    print("📚 索引文档...")
    for doc_id, content in similar_docs + [different_doc]:
        await agent.index_document(doc_id, content)

    query = "PDF上传"
    print(f"\n🔍 查询: {query}")

    result = await agent.process_query(query, top_k=4)

    print(f"\n📊 多样性指标:")
    print(f"   多样性分数: {result['retrieval_metrics']['diversity_score']:.3f}")
    print(f"   (越高表示结果越多样)")

    print(f"\n📋 检索结果:")
    for i, res in enumerate(result['retrieval_results'], 1):
        print(f"   [{i}] {res['doc_id']}: {res['content'][:50]}...")
        print(f"       分数: {res['score']:.4f}")


async def example7_quality_analysis():
    """示例7: 检索质量分析"""
    print("\n\n" + "=" * 80)
    print("示例7: 检索质量分析与优化建议")
    print("=" * 80)

    agent = await create_enhanced_rag_agent()

    # 索引高质量和低质量文档
    await agent.index_document("doc_good", "FieldMind是一个功能强大的企业级知识管理系统，提供智能检索、AI问答、知识图谱等核心能力")
    await agent.index_document("doc_short", "系统")  # 低质量：太短
    await agent.index_document("doc_irrelevant", "今天天气很好，适合户外活动")  # 低质量：不相关

    query = "FieldMind的功能"
    print(f"🔍 查询: {query}\n")

    result = await agent.process_query(query, top_k=3)

    print("📊 质量指标:")
    metrics = result['retrieval_metrics']
    print(f"   平均分数: {metrics['avg_score']:.3f}")
    print(f"   最高分数: {metrics['max_score']:.3f}")
    print(f"   最低分数: {metrics['min_score']:.3f}")
    print(f"   多样性: {metrics['diversity_score']:.3f}")
    print(f"   覆盖率: {metrics['coverage_score']:.3f}")

    if result.get('low_quality_results'):
        print(f"\n⚠️  检测到 {len(result['low_quality_results'])} 个低质量结果:")
        for lq in result['low_quality_results']:
            print(f"   - {lq['doc_id']} (分数: {lq['score']:.3f})")
            print(f"     问题: {', '.join(lq['issues'])}")


async def example8_end_to_end_scenario():
    """示例8: 端到端场景"""
    print("\n\n" + "=" * 80)
    print("示例8: 完整应用场景 - 企业知识问答")
    print("=" * 80)

    agent = await create_enhanced_rag_agent(enable_all_features=True)

    # 构建企业知识库
    knowledge_base = [
        ("kb_onboarding", "新员工入职流程：1. HR报到 2. 领取设备 3. 账号开通 4. 培训课程 5. 导师对接。入职当天需要携带身份证、学历证明等材料。"),
        ("kb_leave", "请假流程：1. 系统提交申请 2. 直属主管审批 3. HR备案。病假需提供医院证明，年假需提前3天申请。"),
        ("kb_expense", "报销流程：1. 填写报销单 2. 上传发票 3. 主管审批 4. 财务审核 5. 打款。差旅费需在出差结束后30天内提交。"),
        ("kb_it_support", "IT支持：工作日9:00-18:00提供技术支持。紧急问题拨打热线400-xxx-xxxx，一般问题提交工单系统。"),
        ("kb_benefits", "员工福利：五险一金、商业保险、年度体检、节日礼品、团建活动、培训补贴。入职满一年享受带薪年假。")
    ]

    print("📚 构建企业知识库...")
    for doc_id, content in knowledge_base:
        await agent.index_document(doc_id, content)
    print(f"✅ 已索引 {len(knowledge_base)} 个知识条目\n")

    # 模拟员工咨询场景
    queries = [
        "新员工入职需要准备什么材料？",
        "我想请病假，怎么操作？",
        "报销差旅费有时间限制吗？"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"场景 {i}: 员工咨询")
        print(f"{'='*60}")
        print(f"👤 员工: {query}")

        result = await agent.process_query(query, top_k=3)

        print(f"🤖 AI助手: {result['answer']}\n")

        print(f"📚 参考知识:")
        for res in result['retrieval_results'][:2]:
            print(f"   - {res['doc_id']} (相关度: {res['score']:.2%})")

        if result.get('citations'):
            print(f"\n✅ 引用质量:")
            cite_metrics = result['citation_metrics']
            print(f"   整体置信度: {cite_metrics['overall_confidence']:.2%}")
            print(f"   覆盖率: {cite_metrics['coverage_ratio']:.2%}")

        print(f"\n⏱️  处理时间: {result['processing_time_ms']:.1f}ms")

    # 统计信息
    print(f"\n\n{'='*60}")
    print("📊 系统统计")
    print(f"{'='*60}")

    stats = agent.get_statistics()
    print(f"知识库文档数: {stats['total_documents']}")
    print(f"对话轮次: {stats['conversation_turns']}")
    print(f"可用工具数: {stats['available_tools']}")
    print(f"混合检索: {'✅ 已启用' if stats['hybrid_retrieval_enabled'] else '❌ 未启用'}")
    print(f"多样性优化: {'✅ 已启用' if stats['diversity_enabled'] else '❌ 未启用'}")
    print(f"引用追踪: {'✅ 已启用' if stats['citation_tracking_enabled'] else '❌ 未启用'}")


async def main():
    """运行所有示例"""
    print("\n🚀 增强型RAG Agent - 完整功能演示\n")

    examples = [
        example1_basic_agent,
        example2_multi_turn_conversation,
        example3_intent_based_routing,
        example4_tool_usage,
        example5_hybrid_retrieval,
        example6_diversity_reranking,
        example7_quality_analysis,
        example8_end_to_end_scenario
    ]

    for example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ 示例执行出错: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n\n" + "=" * 80)
    print("✅ 所有示例演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
