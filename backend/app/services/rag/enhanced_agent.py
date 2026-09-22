"""
增强型RAG Agent集成 (Enhanced RAG Agent Integration)

将检索质量保证和Agent能力整合到统一的Agent系统
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from .core import RAGService, VectorStore, EmbeddingService, SearchResult
from .retrieval_enhancement import (
    KeywordRetriever,
    BM25Retriever,
    HybridRetriever,
    DiversityReranker,
    RetrievalQualityAnalyzer,
    RetrievalResult
)
from .agent_enhancement import (
    IntentRecognizer,
    IntentType,
    Intent,
    ConversationManager,
    ToolRegistry,
    TaskOrchestrator,
    TaskType,
    tool_calculate,
    tool_count_words,
    tool_extract_urls,
    tool_format_json
)
from .citation_tracker import CitationTracker

logger = logging.getLogger(__name__)


class EnhancedRAGAgent:
    """
    增强型RAG Agent

    集成能力:
    1. 多路召回检索 (向量+关键词+BM25)
    2. 重排序和多样性控制
    3. 意图识别
    4. 多轮对话管理
    5. 工具调用
    6. 任务编排
    7. 引用溯源
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        enable_hybrid_retrieval: bool = True,
        enable_diversity: bool = True,
        enable_citation_tracking: bool = True
    ):
        """
        初始化增强型RAG Agent

        Args:
            vector_store: 向量存储
            embedding_service: 嵌入服务
            enable_hybrid_retrieval: 是否启用混合检索
            enable_diversity: 是否启用多样性重排序
            enable_citation_tracking: 是否启用引用追踪
        """
        # 基础RAG服务
        self.rag_service = RAGService(vector_store, embedding_service)

        # 检索增强组件
        self.enable_hybrid_retrieval = enable_hybrid_retrieval
        if enable_hybrid_retrieval:
            self.keyword_retriever = KeywordRetriever()
            self.bm25_retriever = BM25Retriever()
            self.hybrid_retriever = HybridRetriever(
                vector_weight=0.5,
                keyword_weight=0.25,
                bm25_weight=0.25
            )

        self.enable_diversity = enable_diversity
        if enable_diversity:
            self.diversity_reranker = DiversityReranker(lambda_param=0.5)

        self.retrieval_analyzer = RetrievalQualityAnalyzer()

        # Agent能力组件
        self.intent_recognizer = IntentRecognizer()
        self.conversation_manager = ConversationManager(max_history=10)
        self.tool_registry = ToolRegistry()
        self.task_orchestrator = TaskOrchestrator()

        # 引用追踪
        self.enable_citation_tracking = enable_citation_tracking
        if enable_citation_tracking:
            self.citation_tracker = CitationTracker()

        # 注册内置工具
        self._register_builtin_tools()

        logger.info("Enhanced RAG Agent initialized")

    def _register_builtin_tools(self):
        """注册内置工具"""
        # 计算工具
        self.tool_registry.register(
            name="calculate",
            description="执行数学计算",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式"
                    }
                },
                "required": ["expression"]
            },
            function=tool_calculate
        )

        # 词数统计工具
        self.tool_registry.register(
            name="count_words",
            description="统计文本词数",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要统计的文本"
                    }
                },
                "required": ["text"]
            },
            function=tool_count_words
        )

        # URL提取工具
        self.tool_registry.register(
            name="extract_urls",
            description="从文本中提取URL",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "包含URL的文本"
                    }
                },
                "required": ["text"]
            },
            function=tool_extract_urls
        )

        # JSON格式化工具
        self.tool_registry.register(
            name="format_json",
            description="格式化JSON字符串",
            parameters={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "JSON字符串"
                    }
                },
                "required": ["data"]
            },
            function=tool_format_json
        )

    async def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        索引文档（同时索引到多个检索器）

        Args:
            doc_id: 文档ID
            content: 文档内容
            metadata: 元数据
        """
        # 索引到向量存储
        await self.rag_service.index_document(doc_id, content, metadata)

        # 索引到关键词和BM25检索器
        if self.enable_hybrid_retrieval:
            self.keyword_retriever.index_document(doc_id, content)
            self.bm25_retriever.index_document(doc_id, content)

        logger.info(f"Document {doc_id} indexed to all retrievers")

    async def process_query(
        self,
        query: str,
        top_k: int = 5,
        use_conversation_context: bool = True
    ) -> Dict[str, Any]:
        """
        处理用户查询（完整的Agent流程）

        Args:
            query: 用户查询
            top_k: 返回文档数
            use_conversation_context: 是否使用对话上下文

        Returns:
            处理结果
        """
        start_time = datetime.now()

        # 1. 意图识别
        intent = self.intent_recognizer.recognize(query)
        logger.info(f"Recognized intent: {intent.intent_type.value} (confidence: {intent.confidence:.2f})")

        # 2. 获取对话上下文
        context_summary = ""
        if use_conversation_context:
            context_summary = self.conversation_manager.get_context_summary()
            context_entities = self.conversation_manager.extract_context_entities()
        else:
            context_entities = {}

        # 3. 根据意图选择处理策略
        if intent.intent_type == IntentType.CALCULATE:
            # 直接调用计算工具
            result = await self._handle_calculate_intent(query, intent)
        elif intent.intent_type in [IntentType.QUERY, IntentType.SEARCH, IntentType.EXPLAIN]:
            # 执行RAG检索和生成
            result = await self._handle_rag_intent(query, top_k, context_summary)
        elif intent.intent_type == IntentType.COMPARE:
            # 执行对比分析
            result = await self._handle_compare_intent(query, top_k)
        elif intent.intent_type == IntentType.SUMMARIZE:
            # 执行摘要生成
            result = await self._handle_summarize_intent(query, top_k)
        else:
            # 默认RAG处理
            result = await self._handle_rag_intent(query, top_k, context_summary)

        # 4. 添加到对话历史
        self.conversation_manager.add_turn(
            user_message=query,
            assistant_message=result.get("answer", ""),
            intent=intent,
            context={"entities": context_entities}
        )

        # 5. 添加元信息
        result.update({
            "intent": intent.to_dict(),
            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
            "conversation_id": self.conversation_manager.conversation_id
        })

        return result

    async def _handle_rag_intent(
        self,
        query: str,
        top_k: int,
        context_summary: str
    ) -> Dict[str, Any]:
        """处理RAG类型意图"""
        # 1. 多路召回
        retrieval_results = await self._multi_path_retrieval(query, top_k)

        # 2. 多样性重排序
        if self.enable_diversity and retrieval_results:
            retrieval_results = self.diversity_reranker.rerank(retrieval_results, top_k)

        # 3. 质量分析
        quality_metrics = self.retrieval_analyzer.calculate_metrics(retrieval_results)
        low_quality = self.retrieval_analyzer.identify_low_quality_results(retrieval_results)

        # 4. 构建上下文
        context_parts = []
        if context_summary:
            context_parts.append(f"## 对话上下文\n{context_summary}\n")

        for i, result in enumerate(retrieval_results[:top_k], 1):
            context_parts.append(f"[文档 {i}]\n{result.content}")

        context = "\n\n".join(context_parts)

        # 5. 生成答案（模拟LLM）
        answer = self._generate_answer(query, context)

        # 6. 引用追踪
        citations = []
        citation_metrics = {}
        visualization = {}

        if self.enable_citation_tracking and retrieval_results:
            source_documents = [
                {
                    "doc_id": r.doc_id,
                    "content": r.content,
                    "score": r.score
                }
                for r in retrieval_results
            ]

            answer_with_citations = self.citation_tracker.track_citations(
                query=query,
                answer=answer,
                source_documents=source_documents
            )

            citations = [c.to_dict() for c in answer_with_citations.citations]
            citation_metrics = {
                "overall_confidence": answer_with_citations.overall_confidence,
                "coverage_ratio": answer_with_citations.coverage_ratio,
                "citation_count": len(answer_with_citations.citations)
            }
            visualization = self.citation_tracker.format_for_visualization(answer_with_citations)

        return {
            "query": query,
            "answer": answer,
            "retrieval_results": [r.to_dict() for r in retrieval_results],
            "retrieval_metrics": quality_metrics.to_dict(),
            "low_quality_results": low_quality,
            "citations": citations,
            "citation_metrics": citation_metrics,
            "visualization": visualization,
            "strategy": "multi_path_rag"
        }

    async def _handle_calculate_intent(
        self,
        query: str,
        intent: Intent
    ) -> Dict[str, Any]:
        """处理计算类型意图"""
        # 提取数学表达式
        import re
        expression_match = re.search(r'[\d+\-*/().]+', query)

        if expression_match:
            expression = expression_match.group()
            tool_call = self.tool_registry.call("calculate", expression=expression)

            if tool_call.success:
                answer = f"计算结果: {tool_call.result}"
            else:
                answer = f"计算失败: {tool_call.error}"
        else:
            answer = "未能识别出数学表达式"

        return {
            "query": query,
            "answer": answer,
            "tool_calls": [tool_call.to_dict()] if 'tool_call' in locals() else [],
            "strategy": "tool_call"
        }

    async def _handle_compare_intent(
        self,
        query: str,
        top_k: int
    ) -> Dict[str, Any]:
        """处理对比类型意图"""
        # 检索相关文档
        retrieval_results = await self._multi_path_retrieval(query, top_k * 2)

        # 分组比较（简化实现）
        answer = f"基于检索到的{len(retrieval_results)}个文档，进行对比分析：\n"
        answer += "（此处应该包含详细的对比内容，实际应由LLM生成）"

        return {
            "query": query,
            "answer": answer,
            "retrieval_results": [r.to_dict() for r in retrieval_results],
            "strategy": "compare"
        }

    async def _handle_summarize_intent(
        self,
        query: str,
        top_k: int
    ) -> Dict[str, Any]:
        """处理摘要类型意图"""
        # 检索相关文档
        retrieval_results = await self._multi_path_retrieval(query, top_k)

        # 生成摘要（简化实现）
        answer = "文档摘要：\n"
        for i, result in enumerate(retrieval_results[:3], 1):
            snippet = result.content[:150] + "..."
            answer += f"{i}. {snippet}\n"

        return {
            "query": query,
            "answer": answer,
            "retrieval_results": [r.to_dict() for r in retrieval_results],
            "strategy": "summarize"
        }

    async def _multi_path_retrieval(
        self,
        query: str,
        top_k: int
    ) -> List[RetrievalResult]:
        """
        多路召回检索

        Args:
            query: 查询
            top_k: 返回数量

        Returns:
            融合后的检索结果
        """
        if not self.enable_hybrid_retrieval:
            # 仅使用向量检索
            vector_results = await self.rag_service.search(query, top_k)
            return [
                RetrievalResult(
                    doc_id=r.document.doc_id,
                    content=r.document.content,
                    score=r.score,
                    retrieval_method="vector",
                    rank=r.rank
                )
                for r in vector_results
            ]

        # 1. 向量检索
        vector_search_results = await self.rag_service.search(query, top_k)
        vector_results = [
            RetrievalResult(
                doc_id=r.document.doc_id,
                content=r.document.content,
                score=r.score,
                retrieval_method="vector",
                rank=r.rank
            )
            for r in vector_search_results
        ]

        # 2. 关键词检索
        keyword_results = self.keyword_retriever.search(query, top_k)

        # 3. BM25检索
        bm25_results = self.bm25_retriever.search(query, top_k)

        # 4. 融合结果
        hybrid_results = self.hybrid_retriever.fuse_results(
            vector_results=vector_results,
            keyword_results=keyword_results,
            bm25_results=bm25_results,
            top_k=top_k
        )

        return hybrid_results

    def _generate_answer(self, query: str, context: str) -> str:
        """
        生成答案（模拟LLM）

        实际生产环境应该调用真实的LLM API
        """
        # 简单模拟：从上下文中提取相关句子
        sentences = context.split("。")
        relevant_sentences = [
            s for s in sentences
            if any(word in s for word in query.split())
        ]

        if relevant_sentences:
            answer = "。".join(relevant_sentences[:3]) + "。"
        else:
            answer = f"根据知识库内容，关于「{query}」的信息如下：系统找到了相关文档。具体内容请参考检索结果。"

        return answer

    def register_custom_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function
    ):
        """注册自定义工具"""
        self.tool_registry.register(name, description, parameters, function)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return [turn.to_dict() for turn in self.conversation_manager.turns]

    def clear_conversation(self):
        """清空对话历史"""
        self.conversation_manager.clear_history()

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        return self.tool_registry.list_tools()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        base_stats = self.rag_service.get_statistics()

        return {
            **base_stats,
            "conversation_turns": len(self.conversation_manager.turns),
            "available_tools": len(self.tool_registry.tools),
            "hybrid_retrieval_enabled": self.enable_hybrid_retrieval,
            "diversity_enabled": self.enable_diversity,
            "citation_tracking_enabled": self.enable_citation_tracking
        }


# ============================================================================
# 便捷函数
# ============================================================================

async def create_enhanced_rag_agent(
    embedding_dim: int = 768,
    model_name: str = "sentence-transformers",
    enable_all_features: bool = True
) -> EnhancedRAGAgent:
    """
    创建增强型RAG Agent实例

    Args:
        embedding_dim: 嵌入维度
        model_name: 嵌入模型名称
        enable_all_features: 是否启用所有增强特性

    Returns:
        EnhancedRAGAgent实例
    """
    vector_store = VectorStore(embedding_dim=embedding_dim)
    embedding_service = EmbeddingService(model_name=model_name)

    agent = EnhancedRAGAgent(
        vector_store=vector_store,
        embedding_service=embedding_service,
        enable_hybrid_retrieval=enable_all_features,
        enable_diversity=enable_all_features,
        enable_citation_tracking=enable_all_features
    )

    logger.info("Enhanced RAG Agent created with all features enabled")
    return agent
