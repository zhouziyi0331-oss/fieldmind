"""
Plugin Adapter测试套件

测试插件适配器系统的核心功能:
1. 插件接口规范
2. 动态加载机制
3. 适配器实现
4. 端到端集成
"""

import pytest
import asyncio
import time
from datetime import datetime

from src.app.services.plugins.plugin_interface import (
    PluginInterface,
    BasePluginAdapter,
    MockPluginAdapter,
    PluginContext,
    PluginInput,
    PluginOutput,
    PluginExecutionStatus,
    PluginError,
    PluginValidationError,
    PluginExecutionError,
    create_plugin_context,
    create_plugin_input
)

from src.app.services.plugins.plugin_loader import (
    PluginLoader,
    LoadStrategy,
    LoadedPlugin,
    get_plugin_loader
)

from src.app.services.plugins.plugin_adapter import (
    GraphRAGAdapter,
    Crawl4AIAdapter,
    RAGFlowAdapter,
    MarkitdownAdapter,
    HanLPAdapter,
    AdapterFactory
)

from src.app.services.plugins.plugin_registry import (
    get_plugin_registry
)


# ==================== 插件接口测试 ====================

class TestPluginInterface:
    """插件接口测试"""

    def test_plugin_context_creation(self):
        """测试插件上下文创建"""
        context = create_plugin_context(
            agent_id="test_agent",
            capability_id="graph_rag",
            timeout=30.0
        )

        assert context.agent_id == "test_agent"
        assert context.capability_id == "graph_rag"
        assert context.timeout == 30.0
        assert context.request_id.startswith("req_")

    def test_plugin_input_creation(self):
        """测试插件输入创建"""
        plugin_input = create_plugin_input(
            capability_id="graph_rag",
            input_type="text",
            data="test document",
            parameters={"max_entities": 10}
        )

        assert plugin_input.capability_id == "graph_rag"
        assert plugin_input.input_type == "text"
        assert plugin_input.data == "test document"
        assert plugin_input.parameters["max_entities"] == 10

    def test_plugin_output_to_dict(self):
        """测试插件输出转字典"""
        output = PluginOutput(
            capability_id="graph_rag",
            output_type="graph",
            data={"entities": []},
            status=PluginExecutionStatus.SUCCESS,
            execution_time=1.5
        )

        output_dict = output.to_dict()

        assert output_dict["capability_id"] == "graph_rag"
        assert output_dict["status"] == "success"
        assert output_dict["execution_time"] == 1.5

    def test_mock_plugin_adapter(self):
        """测试Mock适配器"""
        adapter = MockPluginAdapter(
            plugin_id="mock_plugin",
            capability_id="test_capability",
            mock_output={"result": "test_data"},
            execution_time=0.05
        )

        plugin_input = create_plugin_input(
            capability_id="test_capability",
            input_type="text",
            data="test"
        )

        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert output.data["result"] == "test_data"
        assert output.execution_time > 0

    @pytest.mark.asyncio
    async def test_mock_plugin_adapter_async(self):
        """测试Mock适配器异步执行"""
        adapter = MockPluginAdapter(
            plugin_id="mock_plugin",
            capability_id="test_capability"
        )

        plugin_input = create_plugin_input(
            capability_id="test_capability",
            input_type="text",
            data="test"
        )

        output = await adapter.execute_async(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS

    def test_base_adapter_validation(self):
        """测试基础适配器输入验证"""
        adapter = MockPluginAdapter(
            plugin_id="test",
            capability_id="test_cap"
        )

        # 正确的输入
        valid_input = create_plugin_input(
            capability_id="test_cap",
            input_type="text",
            data="test"
        )
        assert adapter.validate_input(valid_input) is True

        # 错误的能力ID
        invalid_input = create_plugin_input(
            capability_id="wrong_cap",
            input_type="text",
            data="test"
        )
        with pytest.raises(PluginValidationError):
            adapter.validate_input(invalid_input)

        # 空数据
        null_input = create_plugin_input(
            capability_id="test_cap",
            input_type="text",
            data=None
        )
        with pytest.raises(PluginValidationError):
            adapter.validate_input(null_input)


# ==================== 插件加载器测试 ====================

class TestPluginLoader:
    """插件加载器测试"""

    @pytest.fixture
    def loader(self):
        """创建加载器实例"""
        registry = get_plugin_registry()
        if not registry.get_all_plugins():
            registry.scan_all_plugins()
        return PluginLoader(registry=registry, strategy=LoadStrategy.LAZY)

    def test_loader_initialization(self, loader):
        """测试加载器初始化"""
        assert loader.strategy == LoadStrategy.LAZY
        assert loader.registry is not None
        assert len(loader._loaded_plugins) == 0

    def test_load_plugin(self, loader):
        """测试加载插件"""
        # 加载graphrag
        loaded = loader.load_plugin("graphrag", "graph_rag")

        assert loaded is not None
        assert loaded.plugin_id == "graphrag"
        assert loaded.capability_id == "graph_rag"
        assert loaded.module is not None
        assert loaded.access_count == 0

    def test_load_plugin_caching(self, loader):
        """测试插件加载缓存"""
        # 第一次加载
        loaded1 = loader.load_plugin("graphrag", "graph_rag")

        # 第二次加载（应该从缓存获取）
        loaded2 = loader.load_plugin("graphrag", "graph_rag")

        assert loaded1 is loaded2
        assert loaded2.access_count == 1  # 第二次访问计数增加

    def test_load_by_capability(self, loader):
        """测试按能力加载插件"""
        # 加载提供graph_rag能力的插件
        loaded = loader.load_by_capability("graph_rag")

        assert loaded is not None
        assert loaded.capability_id == "graph_rag"
        # 应该加载优先级最高的graphrag
        assert loaded.plugin_id == "graphrag"

    def test_load_by_capability_with_preference(self, loader):
        """测试按能力加载插件（指定首选）"""
        # 假设graphiti也提供graph相关能力
        # 这里测试首选参数的工作原理
        loaded = loader.load_by_capability("graph_rag", prefer_plugin_id="graphrag")

        assert loaded.plugin_id == "graphrag"

    def test_unload_plugin(self, loader):
        """测试卸载插件"""
        # 先加载
        loader.load_plugin("graphrag", "graph_rag")
        assert loader.is_loaded("graphrag")

        # 卸载
        success = loader.unload_plugin("graphrag")

        assert success is True
        assert not loader.is_loaded("graphrag")

    def test_is_loaded(self, loader):
        """测试检查插件是否已加载"""
        assert not loader.is_loaded("graphrag")

        loader.load_plugin("graphrag", "graph_rag")

        assert loader.is_loaded("graphrag")

    def test_get_loaded_plugin(self, loader):
        """测试获取已加载插件"""
        loader.load_plugin("graphrag", "graph_rag")

        loaded = loader.get_loaded_plugin("graphrag")

        assert loaded is not None
        assert loaded.plugin_id == "graphrag"

    def test_get_plugin_by_capability(self, loader):
        """测试按能力获取已加载插件"""
        loader.load_plugin("graphrag", "graph_rag")

        loaded = loader.get_plugin_by_capability("graph_rag")

        assert loaded is not None
        assert loaded.capability_id == "graph_rag"

    def test_get_all_loaded(self, loader):
        """测试获取所有已加载插件"""
        loader.load_plugin("graphrag", "graph_rag")
        loader.load_plugin("crawl4ai", "ai_web_crawl")

        all_loaded = loader.get_all_loaded()

        assert len(all_loaded) >= 2
        assert "graphrag" in all_loaded
        assert "crawl4ai" in all_loaded

    def test_get_statistics(self, loader):
        """测试获取统计信息"""
        loader.load_plugin("graphrag", "graph_rag")

        stats = loader.get_statistics()

        assert "total_loaded" in stats
        assert stats["total_loaded"] >= 1
        assert stats["strategy"] == "lazy"
        assert "plugins" in stats

    def test_register_adapter_factory(self, loader):
        """测试注册适配器工厂"""
        def mock_factory(plugin_id, capability_id):
            return MockPluginAdapter(plugin_id, capability_id)

        loader.register_adapter_factory("test_plugin", mock_factory)

        adapter = loader.create_adapter("test_plugin", "test_cap")

        assert adapter is not None
        assert isinstance(adapter, MockPluginAdapter)

    def test_load_with_adapter(self, loader):
        """测试加载插件并创建适配器"""
        def mock_factory(plugin_id, capability_id):
            return MockPluginAdapter(plugin_id, capability_id)

        loaded, adapter = loader.load_with_adapter(
            "graphrag",
            "graph_rag",
            adapter_factory=mock_factory
        )

        assert loaded is not None
        assert adapter is not None
        assert loaded.adapter is adapter

    def test_unload_all(self, loader):
        """测试卸载所有插件"""
        loader.load_plugin("graphrag", "graph_rag")
        loader.load_plugin("crawl4ai", "ai_web_crawl")

        count = loader.unload_all()

        assert count >= 2
        assert len(loader.get_all_loaded()) == 0

    def test_singleton_pattern(self):
        """测试单例模式"""
        loader1 = get_plugin_loader()
        loader2 = get_plugin_loader()

        assert loader1 is loader2


# ==================== 适配器实现测试 ====================

class TestAdapterImplementations:
    """适配器实现测试"""

    def test_graphrag_adapter(self):
        """测试GraphRAG适配器"""
        adapter = GraphRAGAdapter()

        assert adapter.plugin_id == "graphrag"
        assert adapter.capability_id == "graph_rag"

        plugin_input = create_plugin_input(
            capability_id="graph_rag",
            input_type="text",
            data="test document"
        )

        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert "entities" in output.data
        assert "relationships" in output.data
        assert output.execution_time > 0

    def test_crawl4ai_adapter(self):
        """测试Crawl4AI适配器"""
        adapter = Crawl4AIAdapter()

        plugin_input = create_plugin_input(
            capability_id="ai_web_crawl",
            input_type="url",
            data="https://example.com"
        )

        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert "markdown" in output.data
        assert "url" in output.data

    def test_ragflow_adapter(self):
        """测试RAGFlow适配器"""
        adapter = RAGFlowAdapter()

        plugin_input = create_plugin_input(
            capability_id="enterprise_rag",
            input_type="query",
            data="What is RAG?"
        )

        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert "answer" in output.data
        assert "chunks" in output.data

    def test_markitdown_adapter(self):
        """测试Markitdown适配器"""
        adapter = MarkitdownAdapter()

        plugin_input = create_plugin_input(
            capability_id="universal_markdown",
            input_type="pdf",
            data="/path/to/document.pdf"
        )

        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert "markdown" in output.data

    def test_hanlp_adapter(self):
        """测试HanLP适配器"""
        adapter = HanLPAdapter()

        plugin_input = create_plugin_input(
            capability_id="chinese_nlp",
            input_type="text",
            data="我爱自然语言处理"
        )

        output = adapter.execute(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert "tokens" in output.data
        assert "pos" in output.data

    def test_adapter_factory_create(self):
        """测试适配器工厂创建"""
        adapter = AdapterFactory.create("graphrag", "graph_rag")

        assert isinstance(adapter, GraphRAGAdapter)

    def test_adapter_factory_get_supported(self):
        """测试获取支持的插件列表"""
        supported = AdapterFactory.get_supported_plugins()

        assert "graphrag" in supported
        assert "crawl4ai" in supported
        assert "ragflow" in supported
        assert "markitdown" in supported

    def test_adapter_factory_register(self):
        """测试注册新适配器"""
        class CustomAdapter(BasePluginAdapter):
            def __init__(self):
                super().__init__("custom", "custom_cap")

            def execute(self, plugin_input):
                return PluginOutput(
                    capability_id=self.capability_id,
                    output_type="custom",
                    data={"result": "custom"},
                    status=PluginExecutionStatus.SUCCESS
                )

        AdapterFactory.register("custom_plugin", CustomAdapter)

        adapter = AdapterFactory.create("custom_plugin", "custom_cap")

        assert isinstance(adapter, CustomAdapter)


# ==================== 集成测试 ====================

class TestPluginAdapterIntegration:
    """插件适配器集成测试"""

    @pytest.fixture
    def setup_system(self):
        """设置完整系统"""
        registry = get_plugin_registry()
        if not registry.get_all_plugins():
            registry.scan_all_plugins()

        loader = PluginLoader(registry=registry)

        # 注册适配器工厂
        loader.register_adapter_factory("graphrag", lambda pid, cid: GraphRAGAdapter())
        loader.register_adapter_factory("crawl4ai", lambda pid, cid: Crawl4AIAdapter())
        loader.register_adapter_factory("ragflow", lambda pid, cid: RAGFlowAdapter())

        return registry, loader

    def test_complete_workflow(self, setup_system):
        """测试完整工作流程"""
        registry, loader = setup_system

        # 1. 查询能力提供者
        providers = registry.get_plugins_by_capability("graph_rag")
        assert len(providers) > 0

        # 2. 加载插件
        loaded = loader.load_plugin("graphrag", "graph_rag")
        assert loaded is not None

        # 3. 创建适配器
        adapter = AdapterFactory.create("graphrag", "graph_rag")
        assert adapter is not None

        # 4. 执行插件
        plugin_input = create_plugin_input(
            capability_id="graph_rag",
            input_type="text",
            data="test document"
        )

        output = adapter.execute(plugin_input)
        assert output.status == PluginExecutionStatus.SUCCESS

    def test_capability_based_execution(self, setup_system):
        """测试基于能力的执行"""
        registry, loader = setup_system

        # 根据能力加载插件
        loaded = loader.load_by_capability("graph_rag")

        # 创建对应的适配器
        adapter = AdapterFactory.create(loaded.plugin_id, loaded.capability_id)

        # 执行
        plugin_input = create_plugin_input(
            capability_id=loaded.capability_id,
            input_type="text",
            data="test data"
        )

        output = adapter.execute(plugin_input)
        assert output.status == PluginExecutionStatus.SUCCESS

    def test_multiple_capabilities(self, setup_system):
        """测试多个能力的加载和执行"""
        registry, loader = setup_system

        capabilities = ["graph_rag", "ai_web_crawl", "enterprise_rag"]

        for capability_id in capabilities:
            # 加载
            loaded = loader.load_by_capability(capability_id)
            assert loaded is not None

            # 创建适配器
            try:
                adapter = AdapterFactory.create(loaded.plugin_id, capability_id)
                assert adapter is not None
            except ValueError:
                # 某些插件可能没有适配器实现
                continue

    def test_load_with_adapter_integration(self, setup_system):
        """测试加载插件+适配器的集成"""
        registry, loader = setup_system

        # 加载插件并创建适配器
        loaded, adapter = loader.load_with_adapter(
            "graphrag",
            "graph_rag",
            adapter_factory=lambda pid, cid: GraphRAGAdapter()
        )

        assert loaded is not None
        assert adapter is not None
        assert loaded.adapter is adapter

        # 使用适配器执行
        plugin_input = create_plugin_input(
            capability_id="graph_rag",
            input_type="text",
            data="integration test"
        )

        output = adapter.execute(plugin_input)
        assert output.status == PluginExecutionStatus.SUCCESS

    def test_error_handling(self, setup_system):
        """测试错误处理"""
        registry, loader = setup_system

        # 尝试加载不存在的插件
        with pytest.raises(Exception):
            loader.load_plugin("nonexistent_plugin", "nonexistent_cap")

        # 尝试创建不存在的适配器
        with pytest.raises(ValueError):
            AdapterFactory.create("nonexistent_plugin", "nonexistent_cap")

    @pytest.mark.asyncio
    async def test_async_execution(self, setup_system):
        """测试异步执行"""
        registry, loader = setup_system

        adapter = GraphRAGAdapter()

        plugin_input = create_plugin_input(
            capability_id="graph_rag",
            input_type="text",
            data="async test"
        )

        output = await adapter.execute_async(plugin_input)

        assert output.status == PluginExecutionStatus.SUCCESS
        assert output.execution_time > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
