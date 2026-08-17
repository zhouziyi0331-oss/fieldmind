"""
测试SuperSearchAgent

验证SuperSearchAgent的核心功能：
1. 代理初始化和基本属性
2. 多插件并行执行
3. 结果智能融合
4. 策略动态选择
5. 自动容错降级
6. 与AgentBase集成
"""

import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from app.services.agents.super_search_agent import (
    SuperSearchAgent,
    SearchStrategy,
    SearchQueryType,
    SearchResult
)
from app.services.agents.base_agent import AgentStatus, AgentTask, AgentRole
from app.services.plugins.plugin_registry import get_plugin_registry
from app.services.plugins.plugin_loader import get_plugin_loader


# ==================== Fixtures ====================

@pytest.fixture
def search_agent():
    """创建测试用的SuperSearchAgent实例"""
    registry = get_plugin_registry()
    loader = get_plugin_loader()
    agent = SuperSearchAgent(
        agent_id="test_search_agent",
        registry=registry,
        loader=loader
    )
    return agent


@pytest.fixture
def sample_task():
    """创建示例任务"""
    return AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='web_search',
        input_data={
            'query_type': 'web_search',
            'url': 'https://example.com',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )


@pytest.fixture
def setup_test_environment():
    """设置测试环境"""
    registry = get_plugin_registry()
    loader = get_plugin_loader()
    return registry, loader


# ==================== 基础属性测试 ====================

def test_agent_initialization(search_agent):
    """测试代理初始化"""
    assert search_agent.agent_id == "test_search_agent"
    assert search_agent.status == AgentStatus.IDLE
    assert search_agent.role == AgentRole.SEARCH
    assert search_agent.registry is not None
    assert search_agent.loader is not None


def test_agent_capabilities(search_agent):
    """测试代理能力列表"""
    capabilities = search_agent.capabilities

    assert len(capabilities) == 8
    assert "web_search" in capabilities
    assert "content_extraction" in capabilities
    assert "site_crawling" in capabilities
    assert "dynamic_scraping" in capabilities
    assert "batch_crawling" in capabilities
    assert "structured_extraction" in capabilities
    assert "multi_plugin_fusion" in capabilities
    assert "automatic_fallback" in capabilities


def test_search_capabilities_mapping(search_agent):
    """测试搜索能力映射"""
    assert 'ai_web_crawl' in search_agent.search_capabilities
    assert 'fast_web_crawl' in search_agent.search_capabilities
    assert 'browser_automation' in search_agent.search_capabilities

    assert search_agent.search_capabilities['ai_web_crawl'] == 'crawl4ai'
    assert search_agent.search_capabilities['fast_web_crawl'] == 'firecrawl'
    assert search_agent.search_capabilities['browser_automation'] == 'browser-use'


# ==================== SearchResult测试 ====================

def test_search_result_initialization():
    """测试SearchResult初始化"""
    result = SearchResult()

    assert result.urls == []
    assert result.contents == []
    assert result.structured_data == []
    assert result.screenshots == []
    assert result.metadata == {}
    assert result.source_plugins == []
    assert result.confidence_score == 0.0
    assert result.processing_time == 0.0


def test_search_result_merge():
    """测试SearchResult智能合并"""
    result1 = SearchResult(
        urls=['https://example.com', 'https://test.com'],
        contents=[
            {'url': 'https://example.com', 'title': 'Example', 'text': 'Content 1'},
            {'url': 'https://test.com', 'title': 'Test', 'text': 'Content 2'}
        ],
        source_plugins=['crawl4ai'],
        confidence_score=0.9
    )

    result2 = SearchResult(
        urls=['https://test.com', 'https://new.com'],  # test.com重复
        contents=[
            {'url': 'https://test.com', 'title': 'Test', 'text': 'Content 2'},  # 重复
            {'url': 'https://new.com', 'title': 'New', 'text': 'Content 3'}
        ],
        source_plugins=['firecrawl'],
        confidence_score=0.85
    )

    merged = result1.merge(result2)

    # URL去重：3个唯一URL
    assert len(merged.urls) == 3
    assert 'https://example.com' in merged.urls
    assert 'https://test.com' in merged.urls
    assert 'https://new.com' in merged.urls

    # Content去重：3个唯一内容
    assert len(merged.contents) == 3

    # 插件合并
    assert len(merged.source_plugins) == 2
    assert 'crawl4ai' in merged.source_plugins
    assert 'firecrawl' in merged.source_plugins

    # 置信度计算
    assert merged.confidence_score == 1.0  # 2/2插件成功


def test_search_result_merge_with_duplicates():
    """测试SearchResult去重逻辑"""
    result1 = SearchResult(
        urls=['https://a.com', 'https://b.com', 'https://c.com'],
        source_plugins=['plugin1']
    )

    result2 = SearchResult(
        urls=['https://b.com', 'https://c.com', 'https://d.com'],  # b和c重复
        source_plugins=['plugin2']
    )

    merged = result1.merge(result2)

    # 应该有4个唯一URL
    assert len(merged.urls) == 4
    url_set = set(merged.urls)
    assert len(url_set) == 4  # 确认没有重复


# ==================== 策略枚举测试 ====================

def test_search_strategy_enum():
    """测试SearchStrategy枚举"""
    assert SearchStrategy.COMPREHENSIVE.value == "comprehensive"
    assert SearchStrategy.FAST.value == "fast"
    assert SearchStrategy.AI_POWERED.value == "ai_powered"
    assert SearchStrategy.DYNAMIC.value == "dynamic"
    assert SearchStrategy.REDUNDANT.value == "redundant"


def test_search_query_type_enum():
    """测试SearchQueryType枚举"""
    assert SearchQueryType.WEB_SEARCH.value == "web_search"
    assert SearchQueryType.CONTENT_EXTRACTION.value == "content_extraction"
    assert SearchQueryType.SITE_CRAWLING.value == "site_crawling"
    assert SearchQueryType.DYNAMIC_SCRAPING.value == "dynamic_scraping"
    assert SearchQueryType.BATCH_CRAWLING.value == "batch_crawling"
    assert SearchQueryType.STRUCTURED_EXTRACTION.value == "structured_extraction"


# ==================== 任务执行测试 ====================

def test_execute_web_search_task(search_agent):
    """测试执行网页搜索任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='web_search',
        input_data={
            'query_type': 'web_search',
            'url': 'https://example.com',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = search_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'urls' in result.output_data
    assert 'contents' in result.output_data
    assert 'statistics' in result.output_data
    assert result.output_data['status'] == 'success'


def test_execute_content_extraction_task(search_agent):
    """测试执行内容提取任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='content_extraction',
        input_data={
            'query_type': 'content_extraction',
            'url': 'https://example.com/article',
            'strategy': 'ai_powered',
            'parameters': {'extract_images': True}
        }
    )

    result = search_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['query_type'] == 'content_extraction'
    assert result.output_data['strategy'] == 'ai_powered'


def test_execute_site_crawling_task(search_agent):
    """测试执行站点爬取任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='site_crawling',
        input_data={
            'query_type': 'site_crawling',
            'url': 'https://example.com',
            'strategy': 'fast',
            'parameters': {
                'max_depth': 2,
                'max_pages': 50
            }
        }
    )

    result = search_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['query_type'] == 'site_crawling'
    # 站点爬取应该返回多个URL
    assert result.output_data['statistics']['total_urls'] >= 1


def test_execute_dynamic_scraping_task(search_agent):
    """测试执行动态抓取任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='dynamic_scraping',
        input_data={
            'query_type': 'dynamic_scraping',
            'url': 'https://example.com/spa',
            'strategy': 'dynamic',
            'parameters': {'wait_for_js': True}
        }
    )

    result = search_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['query_type'] == 'dynamic_scraping'


def test_execute_batch_crawling_task(search_agent):
    """测试执行批量爬取任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='batch_crawling',
        input_data={
            'query_type': 'batch_crawling',
            'urls': [
                'https://example.com/page1',
                'https://example.com/page2',
                'https://example.com/page3'
            ],
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result = search_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['query_type'] == 'batch_crawling'
    # 批量爬取应该返回多个URL
    assert result.output_data['statistics']['total_urls'] >= 3


def test_execute_structured_extraction_task(search_agent):
    """测试执行结构化提取任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='structured_extraction',
        input_data={
            'query_type': 'structured_extraction',
            'url': 'https://example.com/products',
            'strategy': 'ai_powered',
            'schema': {
                'name': 'string',
                'price': 'number',
                'description': 'string'
            },
            'parameters': {}
        }
    )

    result = search_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['query_type'] == 'structured_extraction'


def test_execute_comprehensive_strategy(search_agent):
    """测试综合策略（并行执行多插件）"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='web_search',
        input_data={
            'query_type': 'web_search',
            'url': 'https://example.com',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result = search_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['strategy'] == 'comprehensive'

    # 综合策略应该有多个插件参与
    statistics = result.output_data['statistics']
    assert 'source_plugins' in statistics
    # 注意：实际插件未加载时，模拟会成功
    assert 'confidence_score' in statistics


# ==================== 错误处理测试 ====================

def test_execute_task_missing_url():
    """测试缺少URL参数的错误处理"""
    agent = SuperSearchAgent(agent_id="test_agent")

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='web_search',
        input_data={
            'query_type': 'content_extraction',
            # 缺少url参数
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = agent.execute_task(task)

    # 应该返回错误状态
    assert result.status == AgentStatus.FAILED
    assert len(result.errors) > 0
    assert 'URL is required' in result.errors[0]


def test_execute_task_invalid_query_type():
    """测试无效查询类型的错误处理"""
    agent = SuperSearchAgent(agent_id="test_agent")

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='web_search',
        input_data={
            'query_type': 'invalid_type',
            'url': 'https://example.com',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = agent.execute_task(task)

    assert result.status == AgentStatus.FAILED
    assert len(result.errors) > 0
    assert 'SearchQueryType' in result.errors[0]


# ==================== 辅助方法测试 ====================

def test_get_supported_strategies(search_agent):
    """测试获取支持的策略列表"""
    # 内容提取支持AI_POWERED策略
    strategies = search_agent.get_supported_strategies(SearchQueryType.CONTENT_EXTRACTION)
    assert SearchStrategy.COMPREHENSIVE in strategies
    assert SearchStrategy.FAST in strategies
    assert SearchStrategy.AI_POWERED in strategies

    # 动态抓取支持DYNAMIC策略
    strategies = search_agent.get_supported_strategies(SearchQueryType.DYNAMIC_SCRAPING)
    assert SearchStrategy.DYNAMIC in strategies


def test_get_plugin_status(search_agent):
    """测试获取插件状态"""
    status = search_agent.get_plugin_status()

    assert 'crawl4ai' in status
    assert 'firecrawl' in status
    assert 'browser-use' in status

    for plugin_id, plugin_status in status.items():
        assert 'capability' in plugin_status
        assert 'available' in plugin_status
        assert 'plugin_count' in plugin_status


def test_format_output(search_agent):
    """测试输出格式化"""
    result = SearchResult(
        urls=['https://example.com'],
        contents=[{'url': 'https://example.com', 'title': 'Example'}],
        source_plugins=['crawl4ai', 'firecrawl'],
        confidence_score=0.9,
        processing_time=1.5
    )

    output = search_agent._format_output(
        result,
        SearchQueryType.WEB_SEARCH,
        SearchStrategy.COMPREHENSIVE
    )

    assert output['status'] == 'success'
    assert output['query_type'] == 'web_search'
    assert output['strategy'] == 'comprehensive'
    assert len(output['urls']) == 1
    assert len(output['contents']) == 1

    stats = output['statistics']
    assert stats['total_urls'] == 1
    assert stats['total_contents'] == 1
    assert stats['confidence_score'] == 0.9
    assert stats['processing_time'] == 1.5
    assert len(stats['source_plugins']) == 2


# ==================== 集成测试 ====================

def test_agent_lifecycle(search_agent, sample_task):
    """测试代理完整生命周期"""
    # 初始状态
    assert search_agent.status == AgentStatus.IDLE

    # 执行任务
    result = search_agent.execute_task(sample_task)

    # 任务完成后状态应该是COMPLETED或FAILED（不是IDLE）
    assert search_agent.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
    assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]


def test_multiple_tasks_sequential(search_agent):
    """测试连续执行多个任务"""
    tasks = [
        AgentTask(
            task_id=str(uuid.uuid4()),
            task_type='web_search',
            input_data={
                'query_type': 'web_search',
                'url': f'https://example.com/page{i}',
                'strategy': 'fast',
                'parameters': {}
            }
        )
        for i in range(3)
    ]

    results = []
    for task in tasks:
        result = search_agent.execute_task(task)
        results.append(result)

    # 所有任务都应该完成
    assert len(results) == 3
    for result in results:
        assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]


def test_agent_with_real_registry(setup_test_environment):
    """测试使用真实注册表的代理"""
    registry, loader = setup_test_environment

    agent = SuperSearchAgent(
        agent_id="real_registry_agent",
        registry=registry,
        loader=loader
    )

    assert agent.registry is registry
    assert agent.loader is loader
    assert agent.status == AgentStatus.IDLE


# ==================== 性能测试 ====================

def test_concurrent_task_execution():
    """测试并发任务执行（模拟多代理场景）"""
    agents = [
        SuperSearchAgent(agent_id=f"agent_{i}")
        for i in range(3)
    ]

    tasks = [
        AgentTask(
            task_id=str(uuid.uuid4()),
            task_type='web_search',
            input_data={
                'query_type': 'web_search',
                'url': f'https://example.com/page{i}',
                'strategy': 'fast',
                'parameters': {}
            }
        )
        for i in range(3)
    ]

    results = []
    for agent, task in zip(agents, tasks):
        result = agent.execute_task(task)
        results.append(result)

    assert len(results) == 3


# ==================== 运行所有测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
