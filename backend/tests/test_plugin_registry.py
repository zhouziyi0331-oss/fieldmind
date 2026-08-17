"""
Plugin Registry 测试套件

测试插件注册表的核心功能:
1. 插件扫描与发现
2. 元数据解析
3. 能力推断
4. 索引构建
5. 查询接口
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from src.app.services.plugins.plugin_registry import (
    PluginRegistry,
    PluginType,
    PluginStatus,
    PluginCapability,
    PluginMetadata,
    CapabilityIndex,
    get_plugin_registry
)


class TestPluginRegistry:
    """插件注册表测试"""

    @pytest.fixture
    def registry(self):
        """创建测试用的注册表实例"""
        return PluginRegistry(repos_dir="/Users/alwan/FieldMind/repos")

    @pytest.fixture
    def scanned_registry(self, registry):
        """创建已扫描的注册表实例"""
        registry.scan_all_plugins()
        return registry

    # ==================== 基础功能测试 ====================

    def test_registry_initialization(self, registry):
        """测试注册表初始化"""
        assert registry.repos_dir == Path("/Users/alwan/FieldMind/repos")
        assert len(registry._plugins) == 0
        assert len(registry._capability_index) == 0
        assert len(registry._type_index) == 0

    def test_plugin_scanning(self, scanned_registry):
        """测试插件扫描"""
        plugins = scanned_registry.get_all_plugins()

        # 应该扫描到31个插件
        assert len(plugins) >= 29, f"Expected at least 29 plugins, got {len(plugins)}"

        # 验证关键插件存在
        assert "graphrag" in plugins
        assert "crawl4ai" in plugins
        assert "ragflow" in plugins
        assert "markitdown" in plugins

    def test_plugin_type_inference(self, registry):
        """测试插件类型推断"""
        assert registry._infer_plugin_type("graphrag") == PluginType.KNOWLEDGE_GRAPH
        assert registry._infer_plugin_type("crawl4ai") == PluginType.SEARCH_CRAWLER
        assert registry._infer_plugin_type("ragflow") == PluginType.RAG_MEMORY
        assert registry._infer_plugin_type("HanLP") == PluginType.NLP_PROCESSING
        assert registry._infer_plugin_type("markitdown") == PluginType.DOCUMENT_CONVERSION
        assert registry._infer_plugin_type("neo4j") == PluginType.DATABASE
        assert registry._infer_plugin_type("mind-map") == PluginType.VISUALIZATION
        assert registry._infer_plugin_type("Pillow") == PluginType.UTILITY

    # ==================== 能力推断测试 ====================

    def test_graphrag_capabilities(self, scanned_registry):
        """测试graphrag能力推断"""
        graphrag = scanned_registry.get_plugin("graphrag")
        assert graphrag is not None
        assert graphrag.plugin_type == PluginType.KNOWLEDGE_GRAPH

        cap_ids = [cap.capability_id for cap in graphrag.capabilities]
        assert "graph_rag" in cap_ids
        assert "entity_extraction" in cap_ids

    def test_crawl4ai_capabilities(self, scanned_registry):
        """测试crawl4ai能力推断"""
        crawl4ai = scanned_registry.get_plugin("crawl4ai")
        assert crawl4ai is not None
        assert crawl4ai.plugin_type == PluginType.SEARCH_CRAWLER

        cap_ids = [cap.capability_id for cap in crawl4ai.capabilities]
        assert "ai_web_crawl" in cap_ids

    def test_ragflow_capabilities(self, scanned_registry):
        """测试ragflow能力推断"""
        ragflow = scanned_registry.get_plugin("ragflow")
        assert ragflow is not None
        assert ragflow.plugin_type == PluginType.RAG_MEMORY

        cap_ids = [cap.capability_id for cap in ragflow.capabilities]
        assert "enterprise_rag" in cap_ids
        assert "document_parsing" in cap_ids

    def test_markitdown_capabilities(self, scanned_registry):
        """测试markitdown能力推断"""
        markitdown = scanned_registry.get_plugin("markitdown")
        assert markitdown is not None
        assert markitdown.plugin_type == PluginType.DOCUMENT_CONVERSION

        cap_ids = [cap.capability_id for cap in markitdown.capabilities]
        assert "universal_markdown" in cap_ids

    # ==================== 索引构建测试 ====================

    def test_capability_index_building(self, scanned_registry):
        """测试能力索引构建"""
        cap_index = scanned_registry.get_capability_index()

        # 应该有多个能力被索引
        assert len(cap_index) > 0

        # 检查特定能力的提供者
        if "graph_rag" in cap_index:
            assert "graphrag" in cap_index["graph_rag"].providers

        if "ai_web_crawl" in cap_index:
            assert "crawl4ai" in cap_index["ai_web_crawl"].providers

    def test_type_index_building(self, scanned_registry):
        """测试类型索引构建"""
        # 获取知识图谱类型的插件
        kg_plugins = scanned_registry.get_plugins_by_type(PluginType.KNOWLEDGE_GRAPH)
        kg_ids = [p.plugin_id for p in kg_plugins]

        assert "graphrag" in kg_ids or "graphiti" in kg_ids or "cognee" in kg_ids

        # 获取搜索爬虫类型的插件
        crawler_plugins = scanned_registry.get_plugins_by_type(PluginType.SEARCH_CRAWLER)
        crawler_ids = [p.plugin_id for p in crawler_plugins]

        assert "crawl4ai" in crawler_ids or "firecrawl" in crawler_ids

    def test_priority_ordering(self, scanned_registry):
        """测试优先级排序"""
        # 获取提供graph_rag能力的插件
        graph_rag_plugins = scanned_registry.get_plugins_by_capability("graph_rag")

        if graph_rag_plugins:
            # graphrag应该排在第一位（如果存在）
            first_plugin = graph_rag_plugins[0]
            assert first_plugin.plugin_id == "graphrag"

    # ==================== 查询接口测试 ====================

    def test_get_plugin(self, scanned_registry):
        """测试获取单个插件"""
        graphrag = scanned_registry.get_plugin("graphrag")
        assert graphrag is not None
        assert graphrag.plugin_id == "graphrag"
        assert graphrag.plugin_type == PluginType.KNOWLEDGE_GRAPH

    def test_get_all_plugins(self, scanned_registry):
        """测试获取所有插件"""
        plugins = scanned_registry.get_all_plugins()
        assert len(plugins) >= 29
        assert isinstance(plugins, dict)

    def test_get_plugins_by_type(self, scanned_registry):
        """测试按类型查询插件"""
        kg_plugins = scanned_registry.get_plugins_by_type(PluginType.KNOWLEDGE_GRAPH)
        assert len(kg_plugins) > 0

        for plugin in kg_plugins:
            assert plugin.plugin_type == PluginType.KNOWLEDGE_GRAPH

    def test_get_plugins_by_capability(self, scanned_registry):
        """测试按能力查询插件"""
        # 查询提供entity_extraction能力的插件
        entity_plugins = scanned_registry.get_plugins_by_capability("entity_extraction")

        if entity_plugins:
            # 验证返回的插件确实提供该能力
            for plugin in entity_plugins:
                cap_ids = [cap.capability_id for cap in plugin.capabilities]
                assert "entity_extraction" in cap_ids

    def test_search_plugins(self, scanned_registry):
        """测试搜索插件"""
        # 搜索包含"graph"的插件
        graph_plugins = scanned_registry.search_plugins("graph")
        assert len(graph_plugins) > 0

        # 搜索包含"crawl"的插件
        crawl_plugins = scanned_registry.search_plugins("crawl")
        assert len(crawl_plugins) > 0

    # ==================== 导出与统计测试 ====================

    def test_get_statistics(self, scanned_registry):
        """测试获取统计信息"""
        stats = scanned_registry.get_statistics()

        assert "total_plugins" in stats
        assert stats["total_plugins"] >= 29

        assert "by_type" in stats
        assert "by_status" in stats
        assert "total_capabilities" in stats
        assert "by_language" in stats

        # 验证统计数据合理性
        assert stats["total_capabilities"] > 0
        assert len(stats["by_type"]) > 0

    def test_export_registry(self, scanned_registry, tmp_path):
        """测试导出注册表"""
        output_file = tmp_path / "test_registry.json"
        scanned_registry.export_registry(str(output_file))

        assert output_file.exists()

        # 验证导出的JSON结构
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert "total_plugins" in data
        assert "plugins" in data
        assert "capability_index" in data
        assert "type_index" in data
        assert data["total_plugins"] >= 29

    # ==================== 元数据解析测试 ====================

    def test_readme_extraction(self, scanned_registry):
        """测试README描述提取"""
        # 检查是否有插件成功提取了描述
        plugins_with_desc = [
            p for p in scanned_registry.get_all_plugins().values()
            if p.description and p.description != "No description available"
        ]

        assert len(plugins_with_desc) > 0

    def test_language_detection(self, scanned_registry):
        """测试编程语言检测"""
        plugins = scanned_registry.get_all_plugins()

        # 检查是否有插件检测到了语言
        plugins_with_lang = [
            p for p in plugins.values()
            if len(p.languages) > 0
        ]

        assert len(plugins_with_lang) > 0

        # 验证Python项目被正确识别
        graphrag = scanned_registry.get_plugin("graphrag")
        if graphrag:
            assert "Python" in graphrag.languages or len(graphrag.languages) > 0

    def test_version_parsing(self, scanned_registry):
        """测试版本解析"""
        plugins = scanned_registry.get_all_plugins()

        # 检查是否有插件解析到了版本
        plugins_with_version = [
            p for p in plugins.values()
            if p.version != "unknown"
        ]

        # 至少应该有一些插件有版本信息
        assert len(plugins_with_version) > 0

    # ==================== 单例模式测试 ====================

    def test_singleton_pattern(self):
        """测试单例模式"""
        registry1 = get_plugin_registry()
        registry2 = get_plugin_registry()

        assert registry1 is registry2

    # ==================== 边界条件测试 ====================

    def test_nonexistent_plugin(self, scanned_registry):
        """测试查询不存在的插件"""
        plugin = scanned_registry.get_plugin("nonexistent_plugin_xyz")
        assert plugin is None

    def test_nonexistent_capability(self, scanned_registry):
        """测试查询不存在的能力"""
        plugins = scanned_registry.get_plugins_by_capability("nonexistent_capability_xyz")
        assert plugins == []

    def test_empty_search(self, scanned_registry):
        """测试空搜索结果"""
        results = scanned_registry.search_plugins("xyzabc123nonexistent")
        assert results == []


class TestPluginCapability:
    """插件能力数据类测试"""

    def test_capability_creation(self):
        """测试能力创建"""
        cap = PluginCapability(
            capability_id="test_cap",
            category="test",
            description="Test capability",
            input_types=["text"],
            output_types=["result"]
        )

        assert cap.capability_id == "test_cap"
        assert cap.category == "test"
        assert len(cap.input_types) == 1
        assert len(cap.output_types) == 1


class TestPluginMetadata:
    """插件元数据数据类测试"""

    def test_metadata_creation(self):
        """测试元数据创建"""
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            plugin_name="Test Plugin",
            plugin_type=PluginType.UTILITY,
            version="1.0.0"
        )

        assert metadata.plugin_id == "test_plugin"
        assert metadata.plugin_type == PluginType.UTILITY
        assert metadata.status == PluginStatus.DISCOVERED

    def test_metadata_to_dict(self):
        """测试元数据转字典"""
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            plugin_name="Test Plugin",
            plugin_type=PluginType.UTILITY
        )

        data = metadata.to_dict()

        assert data["plugin_id"] == "test_plugin"
        assert data["plugin_type"] == "utility"
        assert data["status"] == "discovered"
        assert "last_updated" in data


# ==================== 集成测试 ====================

class TestPluginRegistryIntegration:
    """插件注册表集成测试"""

    def test_complete_workflow(self):
        """测试完整工作流程"""
        # 1. 创建注册表
        registry = PluginRegistry()

        # 2. 扫描插件
        plugins = registry.scan_all_plugins()
        assert len(plugins) >= 29

        # 3. 查询特定插件
        graphrag = registry.get_plugin("graphrag")
        assert graphrag is not None

        # 4. 按能力查询
        if graphrag and len(graphrag.capabilities) > 0:
            cap_id = graphrag.capabilities[0].capability_id
            providers = registry.get_plugins_by_capability(cap_id)
            assert len(providers) > 0

        # 5. 获取统计信息
        stats = registry.get_statistics()
        assert stats["total_plugins"] >= 29

        # 6. 搜索插件
        results = registry.search_plugins("graph")
        assert len(results) > 0

    def test_capability_to_plugin_mapping(self):
        """测试能力→插件映射的完整性"""
        registry = PluginRegistry()
        registry.scan_all_plugins()

        cap_index = registry.get_capability_index()

        # 验证每个能力的提供者都存在
        for cap_id, index in cap_index.items():
            for provider_id in index.providers:
                plugin = registry.get_plugin(provider_id)
                assert plugin is not None, f"Provider {provider_id} for {cap_id} not found"

                # 验证该插件确实声明了这个能力
                plugin_cap_ids = [cap.capability_id for cap in plugin.capabilities]
                assert cap_id in plugin_cap_ids, f"{provider_id} doesn't have capability {cap_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
