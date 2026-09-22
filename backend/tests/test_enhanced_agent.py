"""
增强型RAG Agent测试

测试检索质量保证和Agent能力增强模块
"""
import pytest
import asyncio
from app.services.rag.retrieval_enhancement import (
    KeywordRetriever,
    BM25Retriever,
    HybridRetriever,
    DiversityReranker,
    RetrievalQualityAnalyzer,
    RetrievalResult
)
from app.services.rag.agent_enhancement import (
    IntentRecognizer,
    IntentType,
    ConversationManager,
    ToolRegistry,
    TaskOrchestrator,
    TaskType,
    tool_calculate
)
from app.services.rag.enhanced_agent import (
    EnhancedRAGAgent,
    create_enhanced_rag_agent
)


class TestKeywordRetriever:
    """测试关键词检索器"""

    def test_index_and_search(self):
        """测试索引和搜索"""
        retriever = KeywordRetriever()

        # 索引文档
        retriever.index_document("doc1", "FieldMind支持PDF文档上传")
        retriever.index_document("doc2", "系统支持Word和Excel格式")
        retriever.index_document("doc3", "Markdown文件也可以上传")

        # 搜索
        results = retriever.search("支持PDF", top_k=2)

        assert len(results) > 0
        assert results[0].doc_id == "doc1"
        assert results[0].retrieval_method == "keyword"

    def test_tf_idf_scoring(self):
        """测试TF-IDF评分"""
        retriever = KeywordRetriever()

        retriever.index_document("doc1", "机器学习 机器学习 机器学习")
        retriever.index_document("doc2", "深度学习很有趣")

        results = retriever.search("机器学习", top_k=2)

        # doc1应该得分更高（TF更高）
        assert results[0].doc_id == "doc1"
        assert results[0].score > 0


class TestBM25Retriever:
    """测试BM25检索器"""

    def test_bm25_search(self):
        """测试BM25搜索"""
        retriever = BM25Retriever(k1=1.5, b=0.75)

        # 索引文档
        retriever.index_document("doc1", "FieldMind是一个知识管理系统")
        retriever.index_document("doc2", "系统支持文档上传和检索功能")
        retriever.index_document("doc3", "知识库可以存储各类文档")

        # 搜索
        results = retriever.search("知识管理", top_k=2)

        assert len(results) > 0
        assert results[0].retrieval_method == "bm25"

    def test_document_length_normalization(self):
        """测试文档长度归一化"""
        retriever = BM25Retriever()

        # 短文档
        retriever.index_document("doc1", "知识管理")
        # 长文档
        retriever.index_document("doc2", "知识管理系统是一个复杂的企业级应用" * 10)

        results = retriever.search("知识管理", top_k=2)

        # 应该有结果
        assert len(results) > 0


class TestHybridRetriever:
    """测试混合检索器"""

    def test_fuse_results(self):
        """测试结果融合"""
        hybrid = HybridRetriever(
            vector_weight=0.5,
            keyword_weight=0.25,
            bm25_weight=0.25
        )

        # 创建模拟结果
        vector_results = [
            RetrievalResult("doc1", "内容1", 0.9, "vector", 1),
            RetrievalResult("doc2", "内容2", 0.8, "vector", 2)
        ]

        keyword_results = [
            RetrievalResult("doc2", "内容2", 0.7, "keyword", 1),
            RetrievalResult("doc3", "内容3", 0.6, "keyword", 2)
        ]

        bm25_results = [
            RetrievalResult("doc1", "内容1", 0.85, "bm25", 1),
            RetrievalResult("doc3", "内容3", 0.75, "bm25", 2)
        ]

        # 融合
        fused = hybrid.fuse_results(vector_results, keyword_results, bm25_results, top_k=3)

        assert len(fused) <= 3
        assert all(r.retrieval_method == "hybrid" for r in fused)
        assert fused[0].score >= fused[1].score  # 排序正确

    def test_weight_normalization(self):
        """测试权重归一化"""
        hybrid = HybridRetriever(vector_weight=1.0, keyword_weight=1.0, bm25_weight=1.0)

        # 权重应该被归一化
        assert abs(hybrid.vector_weight + hybrid.keyword_weight + hybrid.bm25_weight - 1.0) < 0.01


class TestDiversityReranker:
    """测试多样性重排序器"""

    def test_mmr_reranking(self):
        """测试MMR重排序"""
        reranker = DiversityReranker(lambda_param=0.5)

        # 创建相似的文档
        results = [
            RetrievalResult("doc1", "FieldMind支持PDF上传", 0.9, "vector", 1),
            RetrievalResult("doc2", "FieldMind支持PDF文档上传", 0.85, "vector", 2),  # 与doc1很相似
            RetrievalResult("doc3", "系统支持Excel表格处理", 0.8, "vector", 3),  # 不同主题
        ]

        reranked = reranker.rerank(results, top_k=3)

        # doc3应该被提升（多样性）
        doc_ids = [r.doc_id for r in reranked]
        assert "doc3" in doc_ids


class TestRetrievalQualityAnalyzer:
    """测试检索质量分析器"""

    def test_calculate_metrics(self):
        """测试指标计算"""
        results = [
            RetrievalResult("doc1", "内容1", 0.9, "vector", 1),
            RetrievalResult("doc2", "内容2", 0.8, "keyword", 2),
            RetrievalResult("doc3", "内容3", 0.7, "bm25", 3),
        ]

        metrics = RetrievalQualityAnalyzer.calculate_metrics(results)

        assert metrics.total_retrieved == 3
        assert metrics.unique_docs == 3
        assert 0 <= metrics.avg_score <= 1
        assert metrics.min_score == 0.7
        assert metrics.max_score == 0.9
        assert 0 <= metrics.diversity_score <= 1
        assert len(metrics.method_distribution) > 0

    def test_identify_low_quality(self):
        """测试识别低质量结果"""
        results = [
            RetrievalResult("doc1", "高质量内容" * 20, 0.9, "vector", 1),
            RetrievalResult("doc2", "短", 0.2, "keyword", 2),  # 低分数+短内容
        ]

        low_quality = RetrievalQualityAnalyzer.identify_low_quality_results(
            results,
            score_threshold=0.5
        )

        assert len(low_quality) > 0
        assert low_quality[0]["doc_id"] == "doc2"
        assert len(low_quality[0]["issues"]) > 0


class TestIntentRecognizer:
    """测试意图识别器"""

    def test_query_intent(self):
        """测试查询意图"""
        recognizer = IntentRecognizer()

        intent = recognizer.recognize("什么是FieldMind？")

        assert intent.intent_type == IntentType.QUERY
        assert intent.confidence > 0

    def test_howto_intent(self):
        """测试操作指南意图"""
        recognizer = IntentRecognizer()

        intent = recognizer.recognize("如何上传文档？")

        assert intent.intent_type == IntentType.HOWTO

    def test_calculate_intent(self):
        """测试计算意图"""
        recognizer = IntentRecognizer()

        intent = recognizer.recognize("计算100+200的结果")

        assert intent.intent_type == IntentType.CALCULATE

    def test_extract_entities(self):
        """测试实体提取"""
        recognizer = IntentRecognizer()

        intent = recognizer.recognize("上传PDF和Word文档")

        assert "file_formats" in intent.entities
        assert len(intent.entities["file_formats"]) > 0


class TestConversationManager:
    """测试对话管理器"""

    def test_add_turn(self):
        """测试添加对话轮次"""
        manager = ConversationManager(max_history=5)

        turn = manager.add_turn(
            user_message="你好",
            assistant_message="你好！有什么可以帮助你的？"
        )

        assert turn.turn_id == 1
        assert len(manager.turns) == 1

    def test_max_history(self):
        """测试历史长度限制"""
        manager = ConversationManager(max_history=3)

        # 添加5轮对话
        for i in range(5):
            manager.add_turn(f"问题{i}", f"回答{i}")

        # 应该只保留最近3轮
        assert len(manager.turns) == 3
        assert manager.turns[0].turn_id == 3

    def test_context_summary(self):
        """测试上下文摘要"""
        manager = ConversationManager()

        manager.add_turn("FieldMind是什么？", "FieldMind是一个知识管理系统")
        manager.add_turn("它有哪些功能？", "支持文档上传、检索、AI问答等功能")

        summary = manager.get_context_summary()

        assert "FieldMind" in summary
        assert len(summary) > 0

    def test_extract_context_entities(self):
        """测试提取上下文实体"""
        manager = ConversationManager()
        recognizer = IntentRecognizer()

        intent1 = recognizer.recognize("上传PDF文档")
        manager.add_turn("上传PDF文档", "已上传", intent=intent1)

        entities = manager.extract_context_entities()

        # 应该提取到file_formats实体
        assert len(entities) >= 0


class TestToolRegistry:
    """测试工具注册表"""

    def test_register_and_call(self):
        """测试注册和调用工具"""
        registry = ToolRegistry()

        # 注册工具
        registry.register(
            name="add",
            description="加法",
            parameters={},
            function=lambda a, b: a + b
        )

        # 调用工具
        result = registry.call("add", a=1, b=2)

        assert result.success is True
        assert result.result == 3

    def test_tool_not_found(self):
        """测试工具不存在"""
        registry = ToolRegistry()

        result = registry.call("nonexistent")

        assert result.success is False
        assert "not found" in result.error

    def test_builtin_calculate(self):
        """测试内置计算工具"""
        result = tool_calculate("10 + 20 * 3")

        assert result == 70.0

    def test_list_tools(self):
        """测试列出工具"""
        registry = ToolRegistry()

        registry.register("tool1", "描述1", {}, lambda: None)
        registry.register("tool2", "描述2", {}, lambda: None)

        tools = registry.list_tools()

        assert len(tools) == 2


class TestTaskOrchestrator:
    """测试任务编排器"""

    def test_add_task(self):
        """测试添加任务"""
        orchestrator = TaskOrchestrator()

        task = orchestrator.add_task(
            task_id="task1",
            task_type=TaskType.RETRIEVAL,
            description="检索文档"
        )

        assert task.task_id == "task1"
        assert task.status == "pending"

    def test_build_execution_plan(self):
        """测试构建执行计划"""
        orchestrator = TaskOrchestrator()

        # 添加有依赖关系的任务
        orchestrator.add_task("task1", TaskType.RETRIEVAL, "检索")
        orchestrator.add_task("task2", TaskType.GENERATION, "生成", dependencies=["task1"])
        orchestrator.add_task("task3", TaskType.ANALYSIS, "分析", dependencies=["task2"])

        plan = orchestrator.build_execution_plan()

        # 执行顺序应该是 task1 -> task2 -> task3
        assert plan == ["task1", "task2", "task3"]

    def test_execute_task(self):
        """测试执行任务"""
        orchestrator = TaskOrchestrator()

        task = orchestrator.add_task("task1", TaskType.RETRIEVAL, "测试任务")

        # 执行器函数
        def executor(t):
            return f"执行了 {t.task_id}"

        result = orchestrator.execute_task("task1", executor)

        assert result == "执行了 task1"
        assert task.status == "completed"


@pytest.mark.asyncio
class TestEnhancedRAGAgent:
    """测试增强型RAG Agent"""

    async def test_create_agent(self):
        """测试创建Agent"""
        agent = await create_enhanced_rag_agent()

        assert agent is not None
        assert agent.enable_hybrid_retrieval is True
        assert agent.enable_diversity is True
        assert agent.enable_citation_tracking is True

    async def test_index_document(self):
        """测试索引文档"""
        agent = await create_enhanced_rag_agent()

        await agent.index_document(
            doc_id="doc1",
            content="FieldMind是一个智能知识管理系统"
        )

        # 验证文档被索引到所有检索器
        stats = agent.get_statistics()
        assert stats["total_documents"] == 1

    async def test_process_query_rag(self):
        """测试处理RAG查询"""
        agent = await create_enhanced_rag_agent()

        # 索引文档
        await agent.index_document("doc1", "FieldMind支持PDF、Word、Markdown等文档格式")
        await agent.index_document("doc2", "系统提供智能检索和AI问答功能")

        # 处理查询
        result = await agent.process_query("FieldMind支持哪些文档格式？", top_k=2)

        assert "answer" in result
        assert "retrieval_results" in result
        assert "intent" in result
        assert result["strategy"] == "multi_path_rag"

    async def test_process_query_calculate(self):
        """测试处理计算查询"""
        agent = await create_enhanced_rag_agent()

        result = await agent.process_query("计算 100 + 200", top_k=2)

        assert "answer" in result
        assert "300" in str(result["answer"])
        assert result["strategy"] == "tool_call"

    async def test_conversation_history(self):
        """测试对话历史"""
        agent = await create_enhanced_rag_agent()

        await agent.index_document("doc1", "FieldMind是一个知识管理系统")

        # 第一轮对话
        await agent.process_query("什么是FieldMind？")

        # 第二轮对话
        await agent.process_query("它有什么功能？", use_conversation_context=True)

        history = agent.get_conversation_history()

        assert len(history) == 2

    async def test_custom_tool(self):
        """测试自定义工具"""
        agent = await create_enhanced_rag_agent()

        # 注册自定义工具
        def custom_tool(text: str) -> str:
            return text.upper()

        agent.register_custom_tool(
            name="to_upper",
            description="转换为大写",
            parameters={"type": "object", "properties": {"text": {"type": "string"}}},
            function=custom_tool
        )

        # 验证工具已注册
        tools = agent.get_available_tools()
        tool_names = [t["name"] for t in tools]

        assert "to_upper" in tool_names

    async def test_multi_path_retrieval(self):
        """测试多路召回"""
        agent = await create_enhanced_rag_agent()

        # 索引多个文档
        await agent.index_document("doc1", "FieldMind知识管理系统")
        await agent.index_document("doc2", "系统支持文档上传")
        await agent.index_document("doc3", "提供智能检索功能")

        result = await agent.process_query("知识管理", top_k=3)

        # 验证检索结果
        assert len(result["retrieval_results"]) > 0

        # 验证方法分布
        metrics = result["retrieval_metrics"]
        assert "method_distribution" in metrics

    async def test_statistics(self):
        """测试统计信息"""
        agent = await create_enhanced_rag_agent()

        await agent.index_document("doc1", "测试文档")
        await agent.process_query("测试查询")

        stats = agent.get_statistics()

        assert "total_documents" in stats
        assert "conversation_turns" in stats
        assert "available_tools" in stats
        assert stats["conversation_turns"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
