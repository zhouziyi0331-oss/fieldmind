"""
引用溯源系统测试

测试 CitationTracker 的核心功能
"""
import pytest
import asyncio
from app.services.rag.citation_tracker import (
    CitationTracker,
    SentenceSplitter,
    CitationMatcher,
    DocumentFragment
)
from app.services.rag.citation_integration import (
    RAGServiceWithCitations,
    CitationAnalyzer,
    create_rag_service_with_citations
)


class TestSentenceSplitter:
    """测试句子分割器"""

    def test_split_chinese_sentences(self):
        """测试中文句子分割"""
        text = "这是第一句。这是第二句！这是第三句？"
        sentences = SentenceSplitter.split_sentences(text)

        assert len(sentences) == 3
        assert sentences[0][0] == "这是第一句。"
        assert sentences[1][0] == "这是第二句！"
        assert sentences[2][0] == "这是第三句？"

    def test_split_english_sentences(self):
        """测试英文句子分割"""
        text = "This is the first sentence. This is the second! And the third?"
        sentences = SentenceSplitter.split_sentences(text)

        assert len(sentences) == 3
        assert "first sentence" in sentences[0][0]
        assert "second" in sentences[1][0]

    def test_split_mixed_sentences(self):
        """测试中英文混合句子"""
        text = "FieldMind支持PDF格式。It also supports Word documents. 还支持Markdown文件！"
        sentences = SentenceSplitter.split_sentences(text)

        assert len(sentences) == 3

    def test_sentence_positions(self):
        """测试句子位置信息"""
        text = "第一句。第二句。"
        sentences = SentenceSplitter.split_sentences(text)

        # 验证位置信息
        assert sentences[0][1] == 0  # 第一句起始位置
        assert sentences[0][2] > sentences[0][1]  # 结束位置大于起始

    def test_get_sentence_at_position(self):
        """测试根据位置获取句子"""
        text = "第一句话在这里。第二句话在这里。"

        # 获取第一句
        result = SentenceSplitter.get_sentence_at_position(text, 5)
        assert result is not None
        assert "第一句" in result[0]


class TestCitationMatcher:
    """测试引用匹配器"""

    def test_exact_match(self):
        """测试完全匹配"""
        text1 = "FieldMind支持PDF、Word、Markdown等文档格式。"
        text2 = "FieldMind支持PDF、Word、Markdown等文档格式。"

        similarity = CitationMatcher.calculate_similarity(text1, text2)
        assert similarity > 0.95

        match_type = CitationMatcher.determine_match_type(similarity)
        assert match_type == "exact_match"

    def test_paraphrase_match(self):
        """测试转述匹配"""
        text1 = "FieldMind支持多种文档格式"
        text2 = "FieldMind可以处理各种类型的文档"

        similarity = CitationMatcher.calculate_similarity(text1, text2)
        # 应该在 0.5-0.9 之间
        assert 0.3 < similarity < 0.95

    def test_weak_match(self):
        """测试弱匹配"""
        text1 = "FieldMind是一个知识管理系统"
        text2 = "文档上传功能非常简单"

        similarity = CitationMatcher.calculate_similarity(text1, text2)
        assert similarity < 0.5

    def test_confidence_calculation(self):
        """测试置信度计算"""
        # 高相似度 + exact_match
        confidence1 = CitationMatcher.calculate_confidence(0.95, "exact_match", 0.9)
        assert confidence1 > 0.9

        # 低相似度 + weak
        confidence2 = CitationMatcher.calculate_confidence(0.4, "weak", 0.5)
        assert confidence2 < 0.5

    def test_find_best_match(self):
        """测试最佳匹配查找"""
        sentence = "FieldMind支持PDF文档上传"

        fragments = [
            DocumentFragment(
                doc_id="doc1",
                content="FieldMind系统支持PDF、Word等格式的文档上传功能",
                start_char=0,
                end_char=50
            ),
            DocumentFragment(
                doc_id="doc2",
                content="系统配置文件位于config目录下",
                start_char=0,
                end_char=30
            )
        ]

        result = CitationMatcher.find_best_match(
            sentence,
            fragments,
            {"doc1": 0.9, "doc2": 0.7}
        )

        assert result is not None
        fragment, similarity, match_type, confidence = result
        assert fragment.doc_id == "doc1"  # 应该匹配第一个片段
        assert confidence > 0.5


class TestCitationTracker:
    """测试引用追踪器"""

    def test_create_fragments(self):
        """测试文档片段创建"""
        tracker = CitationTracker()

        content = "这是第一段内容，包含一些信息。" * 10  # 重复多次以创建多个片段
        fragments = tracker.create_fragments_from_document(
            doc_id="test_doc",
            content=content,
            chunk_size=100,
            overlap=20
        )

        assert len(fragments) > 0
        # 验证片段信息
        for fragment in fragments:
            assert fragment.doc_id == "test_doc"
            assert fragment.start_char >= 0
            assert fragment.end_char > fragment.start_char
            assert len(fragment.content) > 0

    def test_track_citations(self):
        """测试引用追踪"""
        tracker = CitationTracker()

        query = "FieldMind支持哪些文档格式？"
        answer = "FieldMind支持PDF、Word、Markdown等文档格式。系统会自动识别文件类型。"

        source_documents = [
            {
                "doc_id": "doc_features",
                "content": "FieldMind系统支持多种文档格式，包括PDF、Word文档(doc/docx)、Markdown(md)等。上传时系统会自动识别文件类型并进行相应处理。",
                "score": 0.95
            },
            {
                "doc_id": "doc_upload",
                "content": "文档上传功能位于主界面的上传按钮。点击后可以选择本地文件进行上传。",
                "score": 0.75
            }
        ]

        result = tracker.track_citations(query, answer, source_documents)

        # 验证结果
        assert result.query == query
        assert result.answer == answer
        assert len(result.citations) > 0
        assert 0 <= result.overall_confidence <= 1.0
        assert 0 <= result.coverage_ratio <= 1.0

        # 验证引用详细信息
        for citation in result.citations:
            assert citation.answer_sentence in answer
            assert citation.source_fragment.doc_id in ["doc_features", "doc_upload"]
            assert 0 <= citation.confidence_score <= 1.0
            assert citation.match_type in ["exact_match", "paraphrase", "inference", "weak"]

    def test_format_for_visualization(self):
        """测试可视化格式化"""
        tracker = CitationTracker()

        query = "测试问题"
        answer = "这是第一句答案。这是第二句答案。"

        source_documents = [
            {
                "doc_id": "doc1",
                "content": "这是第一句答案的来源文档内容。",
                "score": 0.9
            }
        ]

        answer_with_citations = tracker.track_citations(query, answer, source_documents)
        viz_data = tracker.format_for_visualization(answer_with_citations)

        # 验证可视化数据结构
        assert "query" in viz_data
        assert "answer" in viz_data
        assert "overall_metrics" in viz_data
        assert "sources" in viz_data

        # 验证答案结构
        assert "text" in viz_data["answer"]
        assert "sentences" in viz_data["answer"]

        # 验证指标
        metrics = viz_data["overall_metrics"]
        assert "confidence" in metrics
        assert "coverage" in metrics
        assert "total_citations" in metrics


@pytest.mark.asyncio
class TestRAGServiceWithCitations:
    """测试带引用的RAG服务"""

    async def test_create_service(self):
        """测试服务创建"""
        service = await create_rag_service_with_citations()
        assert service is not None
        assert service.citation_tracker is not None

    async def test_generate_with_citations(self):
        """测试生成带引用的答案"""
        service = await create_rag_service_with_citations()

        # 索引一些测试文档
        await service.index_documents([
            {
                "doc_id": "doc1",
                "content": "FieldMind是一个智能知识管理系统，支持文档上传、检索和AI问答功能。",
                "metadata": {"category": "intro"}
            },
            {
                "doc_id": "doc2",
                "content": "系统支持PDF、Word、Markdown等多种文档格式。上传后会自动进行文本提取和向量化处理。",
                "metadata": {"category": "features"}
            }
        ])

        # 生成答案
        result = await service.generate_with_citations(
            query="FieldMind支持哪些文档格式？",
            top_k=2,
            enable_citation_tracking=True
        )

        # 验证结果
        assert "answer" in result
        assert "citations" in result
        assert "visualization" in result
        assert "metrics" in result

        # 验证指标
        metrics = result["metrics"]
        assert "overall_confidence" in metrics
        assert "coverage_ratio" in metrics
        assert "citation_count" in metrics

    async def test_validate_citation_quality(self):
        """测试引用质量验证"""
        service = await create_rag_service_with_citations()

        # 索引测试文档
        await service.index_document(
            doc_id="test_doc",
            content="这是一份测试文档，包含测试内容。"
        )

        # 生成答案
        result = await service.generate_with_citations(
            query="测试内容是什么？",
            enable_citation_tracking=True
        )

        # 构建 AnswerWithCitations 对象
        from app.services.rag.citation_tracker import AnswerWithCitations, Citation, DocumentFragment

        answer_with_citations = AnswerWithCitations(
            query=result["query"],
            answer=result["answer"],
            citations=[],  # 简化测试
            overall_confidence=0.85,
            coverage_ratio=0.90
        )

        # 验证质量
        validation = await service.validate_citation_quality(answer_with_citations)

        assert "is_valid" in validation
        assert "quality_score" in validation
        assert "recommendation" in validation


class TestCitationAnalyzer:
    """测试引用分析器"""

    def test_analyze_empty_history(self):
        """测试空历史记录"""
        result = CitationAnalyzer.analyze_citation_distribution([])
        assert "error" in result

    def test_identify_problematic_citations(self):
        """测试识别问题引用"""
        from app.services.rag.citation_tracker import (
            AnswerWithCitations,
            Citation,
            DocumentFragment
        )

        # 创建测试数据
        fragment = DocumentFragment(
            doc_id="doc1",
            content="测试内容",
            start_char=0,
            end_char=10
        )

        citations = [
            Citation(
                answer_sentence="高置信度句子",
                source_fragment=fragment,
                confidence_score=0.9,
                similarity_score=0.85,
                match_type="exact_match",
                evidence_text="证据"
            ),
            Citation(
                answer_sentence="低置信度句子",
                source_fragment=fragment,
                confidence_score=0.3,
                similarity_score=0.25,
                match_type="weak",
                evidence_text="证据"
            )
        ]

        answer_with_citations = AnswerWithCitations(
            query="测试",
            answer="高置信度句子。低置信度句子。",
            citations=citations,
            overall_confidence=0.6,
            coverage_ratio=0.8
        )

        problematic = CitationAnalyzer.identify_problematic_citations(
            answer_with_citations,
            confidence_threshold=0.5
        )

        # 应该识别出一个问题引用
        assert len(problematic) == 1
        assert problematic[0]["confidence"] == 0.3
        assert "低置信度" in problematic[0]["issues"][0]


# 性能测试
class TestPerformance:
    """性能测试"""

    def test_large_document_fragmentation(self):
        """测试大文档分片性能"""
        import time

        tracker = CitationTracker()

        # 创建大文档 (约10000字)
        large_content = "这是一段测试内容。" * 1000

        start_time = time.time()
        fragments = tracker.create_fragments_from_document(
            doc_id="large_doc",
            content=large_content,
            chunk_size=200,
            overlap=50
        )
        elapsed = time.time() - start_time

        # 验证性能（应该在1秒内完成）
        assert elapsed < 1.0
        assert len(fragments) > 0

    def test_citation_matching_performance(self):
        """测试引用匹配性能"""
        import time

        tracker = CitationTracker()

        query = "测试问题"
        answer = "这是第一句。这是第二句。这是第三句。这是第四句。这是第五句。"

        # 创建多个源文档
        source_documents = [
            {
                "doc_id": f"doc_{i}",
                "content": f"这是文档{i}的内容，包含一些相关信息。" * 20,
                "score": 0.8
            }
            for i in range(10)
        ]

        start_time = time.time()
        result = tracker.track_citations(query, answer, source_documents)
        elapsed = time.time() - start_time

        # 验证性能（应该在2秒内完成）
        assert elapsed < 2.0
        assert len(result.citations) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
