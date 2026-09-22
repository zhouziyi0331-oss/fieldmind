"""
引用溯源系统集成模块

将 CitationTracker 集成到现有 RAG 流程中
"""
from typing import List, Dict, Any, Optional
import logging

from .core import RAGService, SearchResult
from .citation_tracker import CitationTracker, AnswerWithCitations

logger = logging.getLogger(__name__)


class RAGServiceWithCitations(RAGService):
    """
    带引用溯源的 RAG 服务

    扩展原有 RAGService，增加精确引用追踪能力
    """

    def __init__(self, *args, **kwargs):
        """初始化服务"""
        super().__init__(*args, **kwargs)
        self.citation_tracker = CitationTracker()

    async def generate_with_citations(
        self,
        query: str,
        top_k: int = 5,
        llm_provider: str = "openai",
        model: str = "gpt-3.5-turbo",
        enable_citation_tracking: bool = True
    ) -> Dict[str, Any]:
        """
        检索增强生成（带引用溯源）

        Args:
            query: 用户查询
            top_k: 检索文档数
            llm_provider: LLM 提供商
            model: 模型名称
            enable_citation_tracking: 是否启用引用追踪

        Returns:
            生成结果（包含引用信息）
        """
        # 1. 检索相关文档
        search_results = await self.search(query, top_k=top_k)

        if not search_results:
            return {
                "query": query,
                "answer": "未找到相关文档。",
                "sources": [],
                "citations": [],
                "context_used": False
            }

        # 2. 构建上下文
        context_parts = []
        source_documents = []

        for result in search_results:
            context_parts.append(f"[文档 {result.rank}]\n{result.document.content}")
            source_documents.append({
                "doc_id": result.document.doc_id,
                "content": result.document.content,
                "score": result.score,
                "rank": result.rank
            })

        context = "\n\n".join(context_parts)

        # 3. 构建 prompt
        prompt = f"""基于以下上下文，请回答问题。

上下文：
{context}

问题：{query}

请提供准确、简洁的答案："""

        # 4. 调用 LLM 生成答案（这里是模拟）
        # 实际应该调用真实的 LLM 服务
        answer = self._simulate_llm_response(query, context)

        # 5. 引用溯源追踪
        if enable_citation_tracking:
            answer_with_citations = self.citation_tracker.track_citations(
                query=query,
                answer=answer,
                source_documents=source_documents
            )

            # 格式化为可视化数据
            visualization_data = self.citation_tracker.format_for_visualization(
                answer_with_citations
            )

            return {
                "query": query,
                "answer": answer,
                "sources": source_documents,
                "citations": [c.to_dict() for c in answer_with_citations.citations],
                "visualization": visualization_data,
                "metrics": {
                    "overall_confidence": answer_with_citations.overall_confidence,
                    "coverage_ratio": answer_with_citations.coverage_ratio,
                    "citation_count": len(answer_with_citations.citations),
                    "high_confidence_count": sum(
                        1 for c in answer_with_citations.citations
                        if c.confidence_score >= 0.8
                    )
                },
                "context_used": True
            }
        else:
            # 不启用引用追踪，返回简化版本
            return {
                "query": query,
                "answer": answer,
                "sources": source_documents,
                "context_used": True
            }

    def _simulate_llm_response(self, query: str, context: str) -> str:
        """
        模拟 LLM 响应

        实际生产环境应该调用真实的 LLM API
        """
        # 简单的模拟：从上下文中提取相关句子
        sentences = context.split("。")
        relevant_sentences = [s for s in sentences if any(word in s for word in query.split())]

        if relevant_sentences:
            # 取前3个相关句子
            answer = "。".join(relevant_sentences[:3]) + "。"
        else:
            # 默认回答
            answer = f"根据提供的上下文，关于「{query}」的信息如下：这是系统的核心功能之一。具体实现依赖于文档内容和配置。建议查看相关文档获取更详细的信息。"

        return answer

    async def validate_citation_quality(
        self,
        answer_with_citations: AnswerWithCitations,
        quality_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        验证引用质量

        Args:
            answer_with_citations: 带引用的答案
            quality_threshold: 质量阈值

        Returns:
            验证结果
        """
        citations = answer_with_citations.citations

        if not citations:
            return {
                "is_valid": False,
                "reason": "没有找到任何引用",
                "quality_score": 0.0
            }

        # 计算质量指标
        high_confidence_count = sum(1 for c in citations if c.confidence_score >= 0.8)
        medium_confidence_count = sum(
            1 for c in citations
            if 0.6 <= c.confidence_score < 0.8
        )
        low_confidence_count = sum(1 for c in citations if c.confidence_score < 0.6)

        # 质量评分
        quality_score = (
            (high_confidence_count * 1.0 +
             medium_confidence_count * 0.7 +
             low_confidence_count * 0.3) / len(citations)
        )

        is_valid = quality_score >= quality_threshold

        return {
            "is_valid": is_valid,
            "quality_score": quality_score,
            "overall_confidence": answer_with_citations.overall_confidence,
            "coverage_ratio": answer_with_citations.coverage_ratio,
            "citation_breakdown": {
                "total": len(citations),
                "high_confidence": high_confidence_count,
                "medium_confidence": medium_confidence_count,
                "low_confidence": low_confidence_count
            },
            "recommendation": self._get_quality_recommendation(quality_score)
        }

    @staticmethod
    def _get_quality_recommendation(quality_score: float) -> str:
        """根据质量分数给出建议"""
        if quality_score >= 0.8:
            return "引用质量优秀，可以直接使用"
        elif quality_score >= 0.6:
            return "引用质量良好，建议人工审核低置信度引用"
        elif quality_score >= 0.4:
            return "引用质量一般，建议增加更多高质量源文档"
        else:
            return "引用质量较差，建议重新检索或扩充知识库"


class CitationAnalyzer:
    """引用分析器 - 用于分析和统计引用数据"""

    @staticmethod
    def analyze_citation_distribution(
        citations_history: List[AnswerWithCitations]
    ) -> Dict[str, Any]:
        """
        分析历史引用分布

        Args:
            citations_history: 历史引用记录列表

        Returns:
            分析报告
        """
        if not citations_history:
            return {"error": "没有历史数据"}

        total_queries = len(citations_history)
        total_citations = sum(len(awc.citations) for awc in citations_history)

        # 置信度分布
        all_confidences = [
            c.confidence_score
            for awc in citations_history
            for c in awc.citations
        ]

        # 匹配类型分布
        match_type_counts = {}
        for awc in citations_history:
            for citation in awc.citations:
                match_type = citation.match_type
                match_type_counts[match_type] = match_type_counts.get(match_type, 0) + 1

        # 覆盖率统计
        coverage_ratios = [awc.coverage_ratio for awc in citations_history]

        return {
            "total_queries": total_queries,
            "total_citations": total_citations,
            "avg_citations_per_query": total_citations / total_queries if total_queries > 0 else 0,
            "confidence_stats": {
                "mean": sum(all_confidences) / len(all_confidences) if all_confidences else 0,
                "min": min(all_confidences) if all_confidences else 0,
                "max": max(all_confidences) if all_confidences else 0,
                "high_confidence_ratio": sum(1 for c in all_confidences if c >= 0.8) / len(all_confidences) if all_confidences else 0
            },
            "match_type_distribution": match_type_counts,
            "coverage_stats": {
                "mean": sum(coverage_ratios) / len(coverage_ratios) if coverage_ratios else 0,
                "min": min(coverage_ratios) if coverage_ratios else 0,
                "max": max(coverage_ratios) if coverage_ratios else 0
            }
        }

    @staticmethod
    def identify_problematic_citations(
        answer_with_citations: AnswerWithCitations,
        confidence_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        识别问题引用（低置信度、弱匹配等）

        Args:
            answer_with_citations: 带引用的答案
            confidence_threshold: 置信度阈值

        Returns:
            问题引用列表
        """
        problematic = []

        for idx, citation in enumerate(answer_with_citations.citations):
            issues = []

            # 检查置信度
            if citation.confidence_score < confidence_threshold:
                issues.append(f"低置信度: {citation.confidence_score:.2f}")

            # 检查匹配类型
            if citation.match_type == "weak":
                issues.append("弱匹配")
            elif citation.match_type == "inference":
                issues.append("推理性匹配，需要验证")

            # 检查相似度
            if citation.similarity_score < 0.4:
                issues.append(f"低相似度: {citation.similarity_score:.2f}")

            if issues:
                problematic.append({
                    "index": idx,
                    "answer_sentence": citation.answer_sentence,
                    "source_doc_id": citation.source_fragment.doc_id,
                    "confidence": citation.confidence_score,
                    "match_type": citation.match_type,
                    "issues": issues,
                    "recommendation": "建议人工审核或寻找更好的源文档"
                })

        return problematic


# 便捷函数
async def create_rag_service_with_citations(
    embedding_dim: int = 768,
    model_name: str = "sentence-transformers"
) -> RAGServiceWithCitations:
    """
    创建带引用溯源的 RAG 服务实例

    Args:
        embedding_dim: 嵌入维度
        model_name: 嵌入模型名称

    Returns:
        RAG 服务实例
    """
    from .core import VectorStore, EmbeddingService

    vector_store = VectorStore(embedding_dim=embedding_dim)
    embedding_service = EmbeddingService(model_name=model_name)

    service = RAGServiceWithCitations(
        vector_store=vector_store,
        embedding_service=embedding_service
    )

    logger.info("Created RAG service with citation tracking")
    return service
