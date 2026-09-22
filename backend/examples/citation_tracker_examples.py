"""
引用溯源系统使用示例

演示如何使用 CitationTracker 进行精确引用追踪
"""
import asyncio
import json
from app.services.rag.citation_integration import (
    create_rag_service_with_citations,
    CitationAnalyzer
)


async def example_basic_usage():
    """示例1：基本使用"""
    print("=" * 80)
    print("示例1：基本引用追踪")
    print("=" * 80)

    # 创建服务
    service = await create_rag_service_with_citations()

    # 索引文档
    documents = [
        {
            "doc_id": "doc_system_overview",
            "content": """FieldMind是一个智能知识管理系统，采用RAG(检索增强生成)技术。
系统支持文档上传、智能检索、AI问答等核心功能。
用户可以上传PDF、Word、Markdown等多种格式的文档。
系统会自动进行文本提取、分块、向量化处理。""",
            "metadata": {"category": "overview", "version": "1.0"}
        },
        {
            "doc_id": "doc_upload_feature",
            "content": """文档上传功能说明：
1. 支持的格式：PDF(.pdf)、Word(.doc/.docx)、文本(.txt)、Markdown(.md)
2. 单个文件大小限制：50MB
3. 上传后会自动进行OCR识别（针对扫描版PDF）
4. 支持批量上传，最多同时上传10个文件
5. 上传成功后会返回文档ID，用于后续检索""",
            "metadata": {"category": "features", "version": "1.0"}
        },
        {
            "doc_id": "doc_search_feature",
            "content": """智能检索功能：
系统使用向量数据库存储文档嵌入。
检索时会将用户问题转换为向量，然后进行相似度搜索。
默认返回Top-5最相关的文档片段。
支持元数据过滤，可以按文档类型、日期等维度筛选。""",
            "metadata": {"category": "features", "version": "1.0"}
        }
    ]

    print("\n📚 索引文档中...")
    await service.index_documents(documents)
    print(f"✅ 成功索引 {len(documents)} 个文档")

    # 提问并生成答案
    query = "FieldMind支持哪些文档格式？有大小限制吗？"
    print(f"\n❓ 用户提问: {query}")

    print("\n🔍 检索相关文档并生成答案...")
    result = await service.generate_with_citations(
        query=query,
        top_k=3,
        enable_citation_tracking=True
    )

    # 打印答案
    print(f"\n💬 答案:\n{result['answer']}")

    # 打印引用信息
    print(f"\n📖 引用溯源 ({len(result['citations'])} 条):")
    for i, citation in enumerate(result['citations'], 1):
        print(f"\n  [{i}] 答案句子: {citation['answer_sentence']}")
        print(f"      来源文档: {citation['source_fragment']['doc_id']}")
        print(f"      置信度: {citation['confidence_score']:.2%}")
        print(f"      匹配类型: {citation['match_type']}")
        print(f"      位置: {citation['source_fragment']['start_char']}-{citation['source_fragment']['end_char']}")
        print(f"      证据: {citation['evidence_text'][:80]}...")

    # 打印整体指标
    metrics = result['metrics']
    print(f"\n📊 整体指标:")
    print(f"   - 整体置信度: {metrics['overall_confidence']:.2%}")
    print(f"   - 覆盖率: {metrics['coverage_ratio']:.2%}")
    print(f"   - 引用总数: {metrics['citation_count']}")
    print(f"   - 高置信度引用: {metrics['high_confidence_count']}")


async def example_visualization_data():
    """示例2：生成可视化数据"""
    print("\n\n" + "=" * 80)
    print("示例2：生成前端可视化数据")
    print("=" * 80)

    service = await create_rag_service_with_citations()

    # 索引文档
    await service.index_document(
        doc_id="doc_api",
        content="FieldMind提供RESTful API接口。主要端点包括：/api/v1/documents用于文档管理，/api/v1/search用于检索，/api/v1/chat用于问答。所有API都需要Bearer Token认证。"
    )

    query = "如何使用API进行文档检索？"
    result = await service.generate_with_citations(
        query=query,
        enable_citation_tracking=True
    )

    # 获取可视化数据
    viz_data = result['visualization']

    print(f"\n📊 可视化数据结构:")
    print(json.dumps(viz_data, indent=2, ensure_ascii=False))

    # 展示如何使用可视化数据
    print(f"\n🎨 前端展示示例:")
    print(f"答案: {viz_data['answer']['text']}")
    print(f"\n句子高亮信息:")
    for sentence_info in viz_data['answer']['sentences']:
        if sentence_info['has_citation']:
            print(f"  - \"{sentence_info['text']}\"")
            print(f"    → 高亮颜色: {sentence_info['color']}")
            print(f"    → 来源: {sentence_info['source_doc_id']}")


async def example_quality_validation():
    """示例3：引用质量验证"""
    print("\n\n" + "=" * 80)
    print("示例3：引用质量验证")
    print("=" * 80)

    service = await create_rag_service_with_citations()

    # 索引测试文档
    await service.index_documents([
        {
            "doc_id": "doc1",
            "content": "FieldMind系统架构采用前后端分离设计。后端使用FastAPI框架，数据库使用PostgreSQL。",
            "metadata": {}
        },
        {
            "doc_id": "doc2",
            "content": "前端使用React开发，支持响应式布局。UI组件库使用Ant Design。",
            "metadata": {}
        }
    ])

    # 生成答案
    result = await service.generate_with_citations(
        query="FieldMind的技术栈是什么？",
        enable_citation_tracking=True
    )

    # 质量验证
    from app.services.rag.citation_tracker import AnswerWithCitations, Citation
    from datetime import datetime

    # 构建验证对象
    citations_list = []
    for c_dict in result['citations']:
        from app.services.rag.citation_tracker import DocumentFragment

        fragment = DocumentFragment(
            doc_id=c_dict['source_fragment']['doc_id'],
            content=c_dict['source_fragment']['content'],
            start_char=c_dict['source_fragment']['start_char'],
            end_char=c_dict['source_fragment']['end_char']
        )

        citation = Citation(
            answer_sentence=c_dict['answer_sentence'],
            source_fragment=fragment,
            confidence_score=c_dict['confidence_score'],
            similarity_score=c_dict['similarity_score'],
            match_type=c_dict['match_type'],
            evidence_text=c_dict['evidence_text']
        )
        citations_list.append(citation)

    answer_with_citations = AnswerWithCitations(
        query=result['query'],
        answer=result['answer'],
        citations=citations_list,
        overall_confidence=result['metrics']['overall_confidence'],
        coverage_ratio=result['metrics']['coverage_ratio'],
        timestamp=datetime.now()
    )

    validation = await service.validate_citation_quality(
        answer_with_citations,
        quality_threshold=0.7
    )

    print(f"\n✅ 质量验证结果:")
    print(f"   是否通过: {'✅ 是' if validation['is_valid'] else '❌ 否'}")
    print(f"   质量评分: {validation['quality_score']:.2%}")
    print(f"   整体置信度: {validation['overall_confidence']:.2%}")
    print(f"   覆盖率: {validation['coverage_ratio']:.2%}")

    print(f"\n📊 引用分布:")
    breakdown = validation['citation_breakdown']
    print(f"   - 总数: {breakdown['total']}")
    print(f"   - 高置信度 (≥0.8): {breakdown['high_confidence']}")
    print(f"   - 中等置信度 (0.6-0.8): {breakdown['medium_confidence']}")
    print(f"   - 低置信度 (<0.6): {breakdown['low_confidence']}")

    print(f"\n💡 建议: {validation['recommendation']}")


async def example_problematic_citations():
    """示例4：识别问题引用"""
    print("\n\n" + "=" * 80)
    print("示例4：识别和分析问题引用")
    print("=" * 80)

    service = await create_rag_service_with_citations()

    # 索引一些相关性不强的文档
    await service.index_documents([
        {
            "doc_id": "relevant_doc",
            "content": "FieldMind的部署方式包括Docker容器部署和Kubernetes集群部署。",
            "metadata": {}
        },
        {
            "doc_id": "irrelevant_doc",
            "content": "今天天气很好，适合户外活动。",
            "metadata": {}
        }
    ])

    result = await service.generate_with_citations(
        query="如何部署FieldMind？",
        top_k=2,
        enable_citation_tracking=True
    )

    # 构建 AnswerWithCitations
    from app.services.rag.citation_tracker import AnswerWithCitations, Citation, DocumentFragment
    from datetime import datetime

    citations_list = []
    for c_dict in result['citations']:
        fragment = DocumentFragment(
            doc_id=c_dict['source_fragment']['doc_id'],
            content=c_dict['source_fragment']['content'],
            start_char=c_dict['source_fragment']['start_char'],
            end_char=c_dict['source_fragment']['end_char']
        )

        citation = Citation(
            answer_sentence=c_dict['answer_sentence'],
            source_fragment=fragment,
            confidence_score=c_dict['confidence_score'],
            similarity_score=c_dict['similarity_score'],
            match_type=c_dict['match_type'],
            evidence_text=c_dict['evidence_text']
        )
        citations_list.append(citation)

    answer_with_citations = AnswerWithCitations(
        query=result['query'],
        answer=result['answer'],
        citations=citations_list,
        overall_confidence=result['metrics']['overall_confidence'],
        coverage_ratio=result['metrics']['coverage_ratio'],
        timestamp=datetime.now()
    )

    # 识别问题引用
    problematic = CitationAnalyzer.identify_problematic_citations(
        answer_with_citations,
        confidence_threshold=0.6
    )

    print(f"\n⚠️  发现 {len(problematic)} 个问题引用:\n")
    for issue in problematic:
        print(f"[{issue['index'] + 1}] {issue['answer_sentence']}")
        print(f"    来源: {issue['source_doc_id']}")
        print(f"    置信度: {issue['confidence']:.2%}")
        print(f"    匹配类型: {issue['match_type']}")
        print(f"    问题: {', '.join(issue['issues'])}")
        print(f"    建议: {issue['recommendation']}\n")


async def example_batch_analysis():
    """示例5：批量分析历史引用"""
    print("\n\n" + "=" * 80)
    print("示例5：批量分析历史引用数据")
    print("=" * 80)

    service = await create_rag_service_with_citations()

    # 索引文档
    await service.index_documents([
        {
            "doc_id": "doc1",
            "content": "FieldMind支持多种部署方式：Docker、Kubernetes、裸机部署。",
            "metadata": {}
        },
        {
            "doc_id": "doc2",
            "content": "系统性能优化建议：使用Redis缓存、配置数据库索引、启用CDN加速。",
            "metadata": {}
        }
    ])

    # 模拟多次查询
    queries = [
        "如何部署FieldMind？",
        "怎样优化系统性能？",
        "FieldMind有哪些特性？"
    ]

    history = []
    print("\n📝 执行批量查询...")

    for query in queries:
        result = await service.generate_with_citations(
            query=query,
            enable_citation_tracking=True
        )

        # 构建 AnswerWithCitations
        from app.services.rag.citation_tracker import AnswerWithCitations, Citation, DocumentFragment
        from datetime import datetime

        citations_list = []
        for c_dict in result['citations']:
            fragment = DocumentFragment(
                doc_id=c_dict['source_fragment']['doc_id'],
                content=c_dict['source_fragment']['content'],
                start_char=c_dict['source_fragment']['start_char'],
                end_char=c_dict['source_fragment']['end_char']
            )

            citation = Citation(
                answer_sentence=c_dict['answer_sentence'],
                source_fragment=fragment,
                confidence_score=c_dict['confidence_score'],
                similarity_score=c_dict['similarity_score'],
                match_type=c_dict['match_type'],
                evidence_text=c_dict['evidence_text']
            )
            citations_list.append(citation)

        answer_with_citations = AnswerWithCitations(
            query=result['query'],
            answer=result['answer'],
            citations=citations_list,
            overall_confidence=result['metrics']['overall_confidence'],
            coverage_ratio=result['metrics']['coverage_ratio'],
            timestamp=datetime.now()
        )

        history.append(answer_with_citations)

    # 分析历史数据
    analysis = CitationAnalyzer.analyze_citation_distribution(history)

    print(f"\n📊 历史引用分析报告:")
    print(f"\n基础统计:")
    print(f"   - 总查询数: {analysis['total_queries']}")
    print(f"   - 总引用数: {analysis['total_citations']}")
    print(f"   - 平均每次引用数: {analysis['avg_citations_per_query']:.1f}")

    print(f"\n置信度统计:")
    conf_stats = analysis['confidence_stats']
    print(f"   - 平均置信度: {conf_stats['mean']:.2%}")
    print(f"   - 最低置信度: {conf_stats['min']:.2%}")
    print(f"   - 最高置信度: {conf_stats['max']:.2%}")
    print(f"   - 高置信度比例: {conf_stats['high_confidence_ratio']:.2%}")

    print(f"\n匹配类型分布:")
    for match_type, count in analysis['match_type_distribution'].items():
        print(f"   - {match_type}: {count}")

    print(f"\n覆盖率统计:")
    cov_stats = analysis['coverage_stats']
    print(f"   - 平均覆盖率: {cov_stats['mean']:.2%}")
    print(f"   - 最低覆盖率: {cov_stats['min']:.2%}")
    print(f"   - 最高覆盖率: {cov_stats['max']:.2%}")


async def main():
    """运行所有示例"""
    print("\n🚀 FieldMind 引用溯源系统 - 完整示例\n")

    try:
        await example_basic_usage()
        await example_visualization_data()
        await example_quality_validation()
        await example_problematic_citations()
        await example_batch_analysis()

        print("\n\n" + "=" * 80)
        print("✅ 所有示例运行完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
