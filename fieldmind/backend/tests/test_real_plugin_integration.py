"""
Real Plugin Integration Tests - Phase 2 Days 6-7

测试真实插件的集成和执行，验证从Mock到真实插件的替换。

集成的插件:
1. ✅ MarkitdownAdapter - 文档转换
2. ✅ Crawl4AIAdapter - 网络爬虫
3. ✅ Mem0Adapter - 持久化记忆
4. ✅ LightRAGAdapter - 轻量级RAG
5. ⚠️  GraphRAGAdapter - 知识图谱（简化实现）

测试策略:
- 单元测试：单个适配器的基本功能
- 集成测试：通过SuperAgent调用真实插件
- 端到端测试：通过EnhancedCoordinatorAgent编排多插件工作流
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

from app.services.plugins.plugin_adapter import (
    MarkitdownAdapter,
    Crawl4AIAdapter,
    Mem0Adapter,
    LightRAGAdapter,
    GraphRAGAdapter,
)
from app.services.plugins.plugin_interface import (
    PluginInput,
    PluginExecutionStatus,
    create_plugin_input,
)


# ==================== MarkitdownAdapter 测试 ====================

class TestMarkitdownAdapter:
    """测试 Markitdown 真实插件集成"""

    def test_markitdown_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = MarkitdownAdapter()
        assert adapter.plugin_id == "markitdown"
        assert adapter.capability_id == "universal_markdown"
        assert "pdf" in adapter._supported_input_types
        assert "url" in adapter._supported_input_types

    def test_markitdown_convert_url(self):
        """测试 Markitdown URL 转换"""
        adapter = MarkitdownAdapter()

        # 使用一个简单的公开URL
        plugin_input = create_plugin_input(
            capability_id="universal_markdown",
            input_type="url",
            data="https://example.com",
            parameters={}
        )

        output = adapter.execute(plugin_input)

        # 验证输出
        assert output.status == PluginExecutionStatus.SUCCESS
        assert "markdown" in output.data
        assert len(output.data["markdown"]) > 0
        assert output.execution_time > 0
        print(f"✅ Markitdown URL conversion: {len(output.data['markdown'])} chars")

    def test_markitdown_convert_html_file(self):
        """测试 Markitdown HTML 文件转换"""
        adapter = MarkitdownAdapter()

        # 创建临时HTML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("""
            <html>
                <head><title>Test Page</title></head>
                <body>
                    <h1>Hello World</h1>
                    <p>This is a test paragraph.</p>
                    <ul>
                        <li>Item 1</li>
                        <li>Item 2</li>
                    </ul>
                </body>
            </html>
            """)
            temp_file = f.name

        try:
            plugin_input = create_plugin_input(
                capability_id="universal_markdown",
                input_type="html",
                data=temp_file,
                parameters={}
            )

            output = adapter.execute(plugin_input)

            assert output.status == PluginExecutionStatus.SUCCESS
            assert "markdown" in output.data
            markdown_content = output.data["markdown"]
            assert "Hello World" in markdown_content
            assert "test paragraph" in markdown_content
            print(f"✅ Markitdown HTML conversion successful")

        finally:
            os.unlink(temp_file)


# ==================== Crawl4AIAdapter 测试 ====================

class TestCrawl4AIAdapter:
    """测试 Crawl4AI 真实插件集成"""

    def test_crawl4ai_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = Crawl4AIAdapter()
        assert adapter.plugin_id == "crawl4ai"
        assert adapter.capability_id == "ai_web_crawl"

    @pytest.mark.asyncio
    async def test_crawl4ai_crawl_simple_url(self):
        """测试 Crawl4AI 爬取简单URL"""
        adapter = Crawl4AIAdapter()

        plugin_input = create_plugin_input(
            capability_id="ai_web_crawl",
            input_type="url",
            data="https://example.com",
            parameters={}
        )

        output = await adapter.execute_async(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert "url" in output.data
        assert "markdown" in output.data
        assert len(output.data["markdown"]) > 0
        assert "metadata" in output.data
        print(f"✅ Crawl4AI crawl: {len(output.data['markdown'])} chars")

    def test_crawl4ai_synchronous_wrapper(self):
        """测试 Crawl4AI 同步包装器"""
        adapter = Crawl4AIAdapter()

        plugin_input = create_plugin_input(
            capability_id="ai_web_crawl",
            input_type="url",
            data="https://example.com",
            parameters={}
        )

        # 使用同步接口
        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert "markdown" in output.data
        print(f"✅ Crawl4AI synchronous execution successful")


# ==================== Mem0Adapter 测试 ====================

class TestMem0Adapter:
    """测试 Mem0 真实插件集成"""

    def test_mem0_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = Mem0Adapter()
        assert adapter.plugin_id == "mem0"
        assert adapter.capability_id == "persistent_memory"

    def test_mem0_store_memory(self):
        """测试 Mem0 存储记忆"""
        adapter = Mem0Adapter()

        messages = [
            {"role": "user", "content": "My name is Alice"},
            {"role": "assistant", "content": "Nice to meet you, Alice!"}
        ]

        plugin_input = create_plugin_input(
            capability_id="persistent_memory",
            input_type="interactions",
            data=messages,
            parameters={"user_id": "test_user_001"}
        )

        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert output.data["operation"] == "store"
        assert output.data["stored_memories"] == len(messages)
        assert output.data["success"] is True
        print(f"✅ Mem0 stored {output.data['stored_memories']} memories")

    def test_mem0_retrieve_memory(self):
        """测试 Mem0 检索记忆"""
        adapter = Mem0Adapter()

        # 先存储
        messages = [
            {"role": "user", "content": "I love playing guitar"},
        ]
        store_input = create_plugin_input(
            capability_id="persistent_memory",
            input_type="interactions",
            data=messages,
            parameters={"user_id": "test_user_002"}
        )
        adapter.execute(store_input)

        # 然后检索
        query_input = create_plugin_input(
            capability_id="persistent_memory",
            input_type="query",
            data="What are my hobbies?",
            parameters={"user_id": "test_user_002"}
        )

        output = adapter.execute(query_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert output.data["operation"] == "retrieve"
        assert "memories" in output.data
        print(f"✅ Mem0 retrieved {output.data['memory_count']} memories")


# ==================== LightRAGAdapter 测试 ====================

class TestLightRAGAdapter:
    """测试 LightRAG 真实插件集成"""

    def test_lightrag_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = LightRAGAdapter()
        assert adapter.plugin_id == "LightRAG"
        assert adapter.capability_id == "lightweight_rag"

    def test_lightrag_insert_text(self):
        """测试 LightRAG 插入文本"""
        adapter = LightRAGAdapter()

        text = "The capital of France is Paris. Paris is known for the Eiffel Tower."

        plugin_input = create_plugin_input(
            capability_id="lightweight_rag",
            input_type="text",
            data=text,
            parameters={}
        )

        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert output.data["operation"] == "insert"
        assert output.data["success"] is True
        print(f"✅ LightRAG inserted {output.data['text_length']} chars")

    def test_lightrag_query(self):
        """测试 LightRAG 查询"""
        adapter = LightRAGAdapter()

        # 先插入一些文本
        text = "Python is a programming language. It is used for AI and web development."
        insert_input = create_plugin_input(
            capability_id="lightweight_rag",
            input_type="text",
            data=text,
            parameters={}
        )
        adapter.execute(insert_input)

        # 然后查询
        query_input = create_plugin_input(
            capability_id="lightweight_rag",
            input_type="query",
            data="What is Python used for?",
            parameters={"mode": "hybrid"}
        )

        output = adapter.execute(query_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert output.data["operation"] == "query"
        assert "answer" in output.data
        assert len(output.data["answer"]) > 0
        print(f"✅ LightRAG query answered: {len(output.data['answer'])} chars")


# ==================== GraphRAGAdapter 测试 ====================

class TestGraphRAGAdapter:
    """测试 GraphRAG 真实插件集成（简化版本）"""

    def test_graphrag_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = GraphRAGAdapter()
        assert adapter.plugin_id == "graphrag"
        assert adapter.capability_id == "graph_rag"

    def test_graphrag_extract_entities(self):
        """测试 GraphRAG 实体提取（简化版本）"""
        adapter = GraphRAGAdapter()

        text = "Microsoft was founded by Bill Gates. The company is based in Redmond."

        plugin_input = create_plugin_input(
            capability_id="graph_rag",
            input_type="text",
            data=text,
            parameters={}
        )

        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert "entities" in output.data
        assert "relationships" in output.data
        assert "communities" in output.data
        assert output.data["entity_count"] > 0
        print(f"✅ GraphRAG extracted {output.data['entity_count']} entities")


# ==================== 集成测试 ====================

class TestPluginIntegration:
    """测试插件间的集成和协作"""

    def test_multi_plugin_workflow(self):
        """测试多插件协作工作流"""
        # 工作流: Crawl4AI爬取 -> Markitdown转换 -> LightRAG索引 -> 查询

        # Step 1: 爬取网页
        crawl_adapter = Crawl4AIAdapter()
        crawl_input = create_plugin_input(
            capability_id="ai_web_crawl",
            input_type="url",
            data="https://example.com",
            parameters={}
        )
        crawl_output = crawl_adapter.execute(crawl_input)
        assert crawl_output.status == PluginExecutionStatus.SUCCESS
        markdown_content = crawl_output.data["markdown"]
        print(f"Step 1: Crawled {len(markdown_content)} chars")

        # Step 2: LightRAG 索引内容
        rag_adapter = LightRAGAdapter()
        insert_input = create_plugin_input(
            capability_id="lightweight_rag",
            input_type="text",
            data=markdown_content,
            parameters={}
        )
        insert_output = rag_adapter.execute(insert_input)
        assert insert_output.status == PluginExecutionStatus.SUCCESS
        print(f"Step 2: Indexed content")

        # Step 3: 查询
        query_input = create_plugin_input(
            capability_id="lightweight_rag",
            input_type="query",
            data="What is this page about?",
            parameters={"mode": "hybrid"}
        )
        query_output = rag_adapter.execute(query_input)
        assert query_output.status == PluginExecutionStatus.SUCCESS
        print(f"Step 3: Query answered: {query_output.data['answer'][:100]}...")

        print("✅ Multi-plugin workflow completed successfully")

    def test_performance_comparison(self):
        """测试真实插件 vs Mock 性能对比"""
        # 真实插件通常比Mock慢，但提供真实数据

        adapter = MarkitdownAdapter()
        plugin_input = create_plugin_input(
            capability_id="universal_markdown",
            input_type="url",
            data="https://example.com",
            parameters={}
        )

        output = adapter.execute(plugin_input)

        # 真实插件应该有合理的执行时间
        assert 0 < output.execution_time < 30  # 不超过30秒
        print(f"✅ Real plugin execution time: {output.execution_time:.2f}s")


# ==================== 压力测试 ====================

@pytest.mark.slow
class TestPluginStress:
    """插件压力测试（标记为slow，默认跳过）"""

    def test_concurrent_crawl(self):
        """测试并发爬取"""
        import concurrent.futures

        adapter = Crawl4AIAdapter()
        urls = [
            "https://example.com",
            "https://www.ietf.org",
            "https://www.w3.org"
        ]

        def crawl_url(url):
            plugin_input = create_plugin_input(
                capability_id="ai_web_crawl",
                input_type="url",
                data=url,
                parameters={}
            )
            return adapter.execute(plugin_input)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(crawl_url, url) for url in urls]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = sum(1 for r in results if r.status == PluginExecutionStatus.SUCCESS)
        print(f"✅ Concurrent crawl: {success_count}/{len(urls)} succeeded")
        assert success_count >= 2  # 至少2个成功


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
