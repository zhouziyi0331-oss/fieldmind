"""
知识分析系统测试脚本
验证语义分析和LLM分析的完整流程
"""

import asyncio
from datetime import datetime
from typing import List
import os

from app.models.document import Document
from app.services.semantic_analyzer import SemanticAnalyzer
from app.services.llm_analyzer import LLMAnalyzer
from app.services.knowledge_analysis_service import KnowledgeAnalysisService


# 测试文档数据
TEST_DOCUMENTS = [
    Document(
        id="doc_1",
        title="人工智能在医疗领域的应用",
        content="""
        人工智能技术在医疗领域的应用正在快速发展。深度学习算法可以辅助医生进行疾病诊断，
        特别是在医学影像分析方面表现出色。通过训练大量的X光片、CT扫描和MRI图像，
        AI系统能够识别出肺癌、乳腺癌等疾病的早期征兆。

        此外，自然语言处理技术帮助医生快速处理电子病历，提取关键信息。
        机器学习模型还可以预测患者的疾病风险，为个性化治疗方案提供支持。

        然而，医疗AI的应用也面临挑战，包括数据隐私保护、模型可解释性、
        以及医疗责任归属等法律伦理问题。
        """,
        source="test",
        created_at=datetime.utcnow()
    ),
    Document(
        id="doc_2",
        title="区块链技术在金融行业的创新",
        content="""
        区块链技术为金融行业带来了革命性的变革。去中心化的分布式账本技术
        提高了交易的透明度和安全性，降低了中间成本。

        智能合约的应用使得金融协议可以自动执行，无需第三方中介。
        这在跨境支付、证券交易、供应链金融等领域展现出巨大潜力。

        加密货币作为区块链的首个应用，虽然面临监管挑战，但DeFi（去中心化金融）
        正在构建全新的金融生态系统。然而，技术的成熟度、能源消耗、
        以及监管合规仍是区块链大规模应用的主要障碍。
        """,
        source="test",
        created_at=datetime.utcnow()
    ),
    Document(
        id="doc_3",
        title="深度学习在计算机视觉中的突破",
        content="""
        深度学习技术彻底改变了计算机视觉领域。卷积神经网络（CNN）
        在图像识别任务中达到甚至超越人类水平。

        目标检测、语义分割、人脸识别等应用已经广泛部署在安防监控、
        自动驾驶、医疗诊断等场景中。生成对抗网络（GAN）能够生成逼真的图像，
        在艺术创作、游戏开发中展现创造力。

        Transformer架构的引入进一步提升了视觉模型的性能，Vision Transformer（ViT）
        在大规模数据集上表现优异。多模态学习将视觉与语言结合，
        使得AI系统能够理解图像内容并生成描述。
        """,
        source="test",
        created_at=datetime.utcnow()
    ),
    Document(
        id="doc_4",
        title="自然语言处理的最新进展",
        content="""
        大型语言模型（LLM）的出现标志着自然语言处理进入新时代。
        GPT系列、BERT、T5等预训练模型在各类NLP任务中刷新记录。

        这些模型通过在海量文本数据上训练，学习到丰富的语言知识和世界知识。
        Zero-shot和Few-shot学习能力使得模型可以快速适应新任务，
        无需大量标注数据。

        对话系统、机器翻译、文本摘要、问答系统等应用日益成熟。
        然而，模型的幻觉问题、偏见问题、以及计算资源消耗仍需要解决。
        提示工程（Prompt Engineering）和检索增强生成（RAG）成为提升模型性能的重要技术。
        """,
        source="test",
        created_at=datetime.utcnow()
    ),
    Document(
        id="doc_5",
        title="量子计算的发展现状",
        content="""
        量子计算被认为是未来计算技术的重要方向。利用量子叠加和量子纠缠原理，
        量子计算机在特定问题上具有指数级的加速潜力。

        目前，IBM、Google、微软等科技巨头都在投资量子计算研发。
        Google声称实现了"量子霸权"，其量子处理器在特定任务上超越经典计算机。

        量子计算在密码学、药物发现、优化问题、材料科学等领域有广阔应用前景。
        但当前量子计算机仍处于NISQ（噪声中等规模量子）时代，
        面临退相干、错误率高、可扩展性等技术挑战。实现容错量子计算还需要时间。
        """,
        source="test",
        created_at=datetime.utcnow()
    )
]


async def test_semantic_analyzer():
    """测试语义分析器"""
    print("=" * 60)
    print("测试1: 语义分析引擎")
    print("=" * 60)

    analyzer = SemanticAnalyzer()

    print(f"\n正在分析 {len(TEST_DOCUMENTS)} 篇文档...")

    result = await analyzer.analyze_documents(
        documents=TEST_DOCUMENTS,
        chunk_size=300,
        chunk_overlap=50
    )

    print(f"\n✅ 分析完成！")
    print(f"\n📊 结果统计:")
    print(f"  - 聚类数量: {len(result.clusters)}")
    print(f"  - 主题数量: {len(result.topics)}")
    print(f"  - 跨文档关联: {len(result.cross_relations)}")
    print(f"  - 异常文档: {len(result.outliers)}")

    print(f"\n📦 聚类详情:")
    for cluster in result.clusters:
        print(f"  聚类 {cluster.cluster_id}:")
        print(f"    - 文档数: {cluster.size}")
        print(f"    - 关键词: {', '.join(cluster.keywords[:5])}")
        print(f"    - 一致性: {cluster.coherence_score:.3f}")

    print(f"\n🏷️  主题详情:")
    for topic in result.topics[:3]:
        print(f"  主题 {topic.topic_id}:")
        keywords = [f"{w}({s:.2f})" for w, s in topic.keywords[:5]]
        print(f"    - 关键词: {', '.join(keywords)}")
        print(f"    - 文档数: {topic.document_count}")

    print(f"\n🔗 跨文档关联示例:")
    for rel in result.cross_relations[:3]:
        print(f"  {rel.doc1_id} ↔ {rel.doc2_id}")
        print(f"    - 相似度: {rel.similarity:.3f}")
        print(f"    - 共享概念: {', '.join(rel.shared_concepts[:3])}")

    return result


async def test_llm_analyzer(semantic_result):
    """测试LLM分析器"""
    print("\n" + "=" * 60)
    print("测试2: LLM分析引擎")
    print("=" * 60)

    # 检查API密钥
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  未配置LLM API密钥，跳过LLM测试")
        print("请设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 环境变量")
        return None

    provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai"
    print(f"\n使用LLM提供商: {provider}")

    analyzer = LLMAnalyzer(provider=provider, temperature=0.7)

    print(f"\n正在生成AI分析报告...")

    try:
        report = await analyzer.analyze(
            documents=TEST_DOCUMENTS,
            semantic_result=semantic_result,
            analysis_focus="识别技术趋势和创新方向"
        )

        print(f"\n✅ LLM分析完成！")
        print(f"\n📝 执行摘要:")
        print(f"{report.summary[:500]}...")

        print(f"\n💡 关键洞察 ({len(report.key_insights)} 个):")
        for i, insight in enumerate(report.key_insights[:3], 1):
            print(f"\n  {i}. {insight.title}")
            print(f"     类型: {insight.category} | 置信度: {insight.confidence:.0%}")
            print(f"     {insight.content[:200]}...")

        print(f"\n🎯 建议 ({len(report.recommendations)} 条):")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"  {i}. {rec}")

        print(f"\n💰 成本统计:")
        print(f"  - 输入Tokens: {report.generation_cost['input_tokens']:,}")
        print(f"  - 输出Tokens: {report.generation_cost['output_tokens']:,}")
        print(f"  - 总成本: ${report.generation_cost['total_cost_usd']:.4f}")

        return report

    except Exception as e:
        print(f"\n❌ LLM分析失败: {str(e)}")
        return None


async def test_knowledge_analysis_service():
    """测试完整的知识分析服务"""
    print("\n" + "=" * 60)
    print("测试3: 完整知识分析服务")
    print("=" * 60)

    # 检查API密钥
    enable_llm = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))

    if not enable_llm:
        print("\n⚠️  未配置LLM API密钥，仅执行语义分析")

    service = KnowledgeAnalysisService()

    print(f"\n执行完整分析流程...")

    result = await service.analyze_knowledge(
        documents=TEST_DOCUMENTS,
        analysis_focus="分析AI技术的发展趋势和应用场景",
        chunk_size=300,
        enable_llm=enable_llm
    )

    print(f"\n✅ 完整分析完成！")
    print(f"\n⏱️  分析耗时: {result['metadata']['duration_seconds']:.2f}秒")

    # 导出报告
    print(f"\n📄 导出Markdown报告...")
    md_report = await service._export_markdown(result, None)
    print(f"报告长度: {len(md_report)} 字符")

    # 保存到文件
    report_path = "/Users/alwan/test_analysis_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"报告已保存: {report_path}")

    return result


async def test_comparison_analysis():
    """测试对比分析"""
    print("\n" + "=" * 60)
    print("测试4: 文档集对比分析")
    print("=" * 60)

    # 分为两组：AI应用 vs 基础技术
    set1 = TEST_DOCUMENTS[:2]  # 医疗AI、区块链
    set2 = TEST_DOCUMENTS[2:4]  # 计算机视觉、NLP

    service = KnowledgeAnalysisService()

    print(f"\n对比两组文档:")
    print(f"  第一组: {len(set1)} 篇 (AI应用)")
    print(f"  第二组: {len(set2)} 篇 (AI技术)")

    comparison = await service.compare_document_sets(
        set1=set1,
        set2=set2,
        comparison_focus="对比应用场景与技术实现"
    )

    print(f"\n✅ 对比分析完成！")
    print(f"\n📊 差异统计:")
    print(f"  - 聚类数差异: {comparison['comparison']['cluster_count_diff']}")
    print(f"  - 主题数差异: {comparison['comparison']['topic_count_diff']}")
    print(f"  - 关联数差异: {comparison['comparison']['relation_count_diff']}")

    return comparison


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("知识分析系统 - 完整测试套件")
    print("=" * 60)
    print(f"测试时间: {datetime.utcnow().isoformat()}")
    print(f"测试文档数: {len(TEST_DOCUMENTS)}")

    try:
        # 测试1: 语义分析
        semantic_result = await test_semantic_analyzer()

        # 测试2: LLM分析
        llm_result = await test_llm_analyzer(semantic_result)

        # 测试3: 完整服务
        full_result = await test_knowledge_analysis_service()

        # 测试4: 对比分析
        comparison_result = await test_comparison_analysis()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)

        return {
            "semantic": semantic_result,
            "llm": llm_result,
            "full": full_result,
            "comparison": comparison_result
        }

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n🚀 启动知识分析系统测试...\n")

    # 检查环境
    print("环境检查:")
    print(f"  - ANTHROPIC_API_KEY: {'✅ 已设置' if os.getenv('ANTHROPIC_API_KEY') else '❌ 未设置'}")
    print(f"  - OPENAI_API_KEY: {'✅ 已设置' if os.getenv('OPENAI_API_KEY') else '❌ 未设置'}")

    # 运行测试
    results = asyncio.run(run_all_tests())

    if results:
        print("\n🎉 测试成功完成！系统已就绪。")
    else:
        print("\n⚠️  测试过程中出现错误，请检查日志。")
