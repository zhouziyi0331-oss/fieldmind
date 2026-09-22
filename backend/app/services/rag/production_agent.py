"""
增强型RAG Agent - 生产版本

使用真实的嵌入模型和LLM
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os

from .core import VectorStore
from .real_embedding import get_embedding_service, RealEmbeddingService
from .real_llm import get_llm_service, RealLLMService
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
    ConversationManager,
    ToolRegistry,
    tool_calculate,
    tool_count_words,
    tool_extract_urls,
    tool_format_json
)
from .citation_tracker import CitationTracker

logger = logging.getLogger(__name__)


class ProductionRAGAgent:
    """
    生产级RAG Agent

    使用真实模型：
    - 嵌入: sentence-transformers (BAAI/bge-small-zh-v1.5)
    - LLM: OpenAI (gpt-3.5-turbo) 或 Ollama (本地模型)
    """

    def __init__(
        self,
        embedding_model: str = "BAAI/bge-small-zh-v1.5",
        llm_provider: str = "openai",
        llm_model: str = "gpt-3.5-turbo",
        enable_hybrid_retrieval: bool = True,
        enable_diversity: bool = True,
        enable_citation_tracking: bool = True
    ):
        """
        初始化生产级Agent

        Args:
            embedding_model: 嵌入模型名称
            llm_provider: LLM提供商 (openai, ollama)
            llm_model: LLM模型名称
            enable_hybrid_retrieval: 启用混合检索
            enable_diversity: 启用多样性重排序
            enable_citation_tracking: 启用引用追踪
        """
        # 初始化嵌入服务
        self.embedding_service = get_embedding_service(embedding_model)

        # 初始化LLM服务
        self.llm_service = get_llm_service(llm_provider, llm_model)

        # 初始化向量存储
        self.vector_store = VectorStore(embedding_dim=self.embedding_service.embedding_dim)

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

        # 引用追踪
        self.enable_citation_tracking = enable_citation_tracking
        if enable_citation_tracking:
            self.citation_tracker = CitationTracker()

        # 注册内置工具
        self._register_builtin_tools()

        logger.info(f"✅ 生产级RAG Agent初始化成功")
        logger.info(f"   嵌入模型: {embedding_model}")
        logger.info(f"   LLM: {llm_provider}/{llm_model}")

    def _register_builtin_tools(self):
        """注册内置工具"""
        self.tool_registry.register(
            name="calculate",
            description="执行数学计算",
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"]
            },
            function=tool_calculate
        )

        self.tool_registry.register(
            name="count_words",
            description="统计文本词数",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"]
            },
            function=tool_count_words
        )

        self.tool_registry.register(
            name="extract_urls",
            description="从文本中提取URL",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"]
            },
            function=tool_extract_urls
        )

        self.tool_registry.register(
            name="format_json",
            description="格式化JSON字符串",
            parameters={
                "type": "object",
                "properties": {"data": {"type": "string"}},
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
        """索引文档（使用真实嵌入模型）"""
        from .core import Document

        # 生成真实嵌入
        embedding = await self.embedding_service.embed_text(content)

        # 创建文档
        document = Document(
            doc_id=doc_id,
            content=content,
            metadata=metadata or {},
            embedding=embedding
        )

        # 添加到向量存储
        self.vector_store.add_document(document, embedding)

        # 索引到关键词和BM25检索器
        if self.enable_hybrid_retrieval:
            self.keyword_retriever.index_document(doc_id, content)
            self.bm25_retriever.index_document(doc_id, content)

        logger.info(f"文档 {doc_id} 已索引（使用真实嵌入模型）")

    async def process_query(
        self,
        query: str,
        top_k: int = 5,
        use_conversation_context: bool = True
    ) -> Dict[str, Any]:
        """
        处理用户查询（完整的Agent流程，使用真实LLM）
        """
        start_time = datetime.now()

        # 1. 意图识别
        intent = self.intent_recognizer.recognize(query)
        logger.info(f"识别意图: {intent.intent_type.value} (置信度: {intent.confidence:.2f})")

        # 2. 获取对话上下文
        context_summary = ""
        conversation_history = []
        if use_conversation_context:
            context_summary = self.conversation_manager.get_context_summary()
            # 构建对话历史（用于LLM）
            for turn in self.conversation_manager.get_recent_turns(3):
                conversation_history.append({
                    "role": "user",
                    "content": turn.user_message
                })
                conversation_history.append({
                    "role": "assistant",
                    "content": turn.assistant_message
                })

        # 3. 根据意图选择处理策略
        if intent.intent_type == IntentType.CALCULATE:
            result = await self._handle_calculate_intent(query, intent)
        elif intent.intent_type in [IntentType.QUERY, IntentType.SEARCH, IntentType.EXPLAIN]:
            result = await self._handle_rag_intent(query, top_k, context_summary, conversation_history)
        else:
            result = await self._handle_rag_intent(query, top_k, context_summary, conversation_history)

        # 4. 添加到对话历史
        self.conversation_manager.add_turn(
            user_message=query,
            assistant_message=result.get("answer", ""),
            intent=intent
        )

        # 5. 添加元信息
        result.update({
            "intent": intent.to_dict(),
            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
            "conversation_id": self.conversation_manager.conversation_id,
            "using_real_models": True  # 标记使用真实模型
        })

        return result

    async def _handle_rag_intent(
        self,
        query: str,
        top_k: int,
        context_summary: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """处理RAG类型意图（使用真实LLM）"""
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
            context_parts.append(f"## 对话历史\n{context_summary}\n")

        for i, result in enumerate(retrieval_results[:top_k], 1):
            context_parts.append(f"[文档 {i}]\n{result.content}")

        context = "\n\n".join(context_parts)

        # 5. 使用真实LLM生成答案
        answer = await self.llm_service.generate_with_context(
            query=query,
            context=context,
            conversation_history=conversation_history
        )

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
            "strategy": "production_rag"
        }

    async def _handle_calculate_intent(
        self,
        query: str,
        intent
    ) -> Dict[str, Any]:
        """处理计算类型意图"""
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

    async def _multi_path_retrieval(
        self,
        query: str,
        top_k: int
    ) -> List[RetrievalResult]:
        """多路召回检索（使用真实嵌入）"""
        if not self.enable_hybrid_retrieval:
            # 仅使用向量检索（真实嵌入）
            query_embedding = await self.embedding_service.embed_text(query)
            vector_search_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k
            )

            return [
                RetrievalResult(
                    doc_id=r.document.doc_id,
                    content=r.document.content,
                    score=r.score,
                    retrieval_method="vector",
                    rank=r.rank
                )
                for r in vector_search_results
            ]

        # 1. 向量检索（真实嵌入）
        query_embedding = await self.embedding_service.embed_text(query)
        vector_search_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k
        )
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

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_documents": len(self.vector_store.documents),
            "embedding_dim": self.vector_store.embedding_dim,
            "conversation_turns": len(self.conversation_manager.turns),
            "available_tools": len(self.tool_registry.tools),
            "hybrid_retrieval_enabled": self.enable_hybrid_retrieval,
            "diversity_enabled": self.enable_diversity,
            "citation_tracking_enabled": self.enable_citation_tracking,
            "embedding_model": self.embedding_service.model_name,
            "llm_provider": self.llm_service.provider,
            "llm_model": self.llm_service.model
        }

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return [turn.to_dict() for turn in self.conversation_manager.turns]

    def clear_conversation(self):
        """清空对话历史"""
        self.conversation_manager.clear_history()


# 便捷函数
async def create_production_rag_agent(
    embedding_model: str = "BAAI/bge-small-zh-v1.5",
    llm_provider: str = None,
    llm_model: str = None,
    enable_all_features: bool = True
) -> ProductionRAGAgent:
    """
    创建生产级RAG Agent实例

    Args:
        embedding_model: 嵌入模型名称
        llm_provider: LLM提供商 (openai, ollama)，None则自动检测
        llm_model: LLM模型名称
        enable_all_features: 是否启用所有增强特性

    Returns:
        ProductionRAGAgent实例
    """
    # 自动检测LLM配置
    if llm_provider is None:
        if os.getenv("OPENAI_API_KEY"):
            llm_provider = "openai"
            llm_model = llm_model or "gpt-3.5-turbo"
            logger.info("检测到 OPENAI_API_KEY，使用 OpenAI")
        else:
            llm_provider = "ollama"
            llm_model = llm_model or "qwen:7b"
            logger.info("未检测到 API Key，使用本地 Ollama")

    agent = ProductionRAGAgent(
        embedding_model=embedding_model,
        llm_provider=llm_provider,
        llm_model=llm_model,
        enable_hybrid_retrieval=enable_all_features,
        enable_diversity=enable_all_features,
        enable_citation_tracking=enable_all_features
    )

    logger.info("✅ 生产级RAG Agent创建成功")
    return agent
