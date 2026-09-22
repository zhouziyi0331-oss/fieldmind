"""
SuperSearchAgent - 搜索爬虫超级代理

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.search.advanced_crawl

整合crawl4ai、firecrawl、browser-use三大插件，提供智能网页搜索和数据提取能力。
展示1+1>2的协同效应：多插件并行执行、结果融合、自动降级。

设计理念:
1. 多插件融合 - 同时使用3个插件，结果去重合并
2. 智能策略 - 根据任务类型选择最优插件组合
3. 自动降级 - 单个插件失败不影响整体
4. 深度集成 - 与AgentBase、PluginLoader完全集成

核心能力:
- web_search: 智能网页搜索
- content_extraction: 内容提取和清洗
- site_crawling: 站点递归爬取
- dynamic_scraping: 动态页面抓取
- batch_crawling: 批量URL处理
- structured_extraction: 结构化数据提取
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, urljoin

from .base_agent import AgentBase, AgentStatus, AgentTask, AgentResult, AgentRole
from ..plugins.plugin_loader import PluginLoader, LoadStrategy
from ..plugins.plugin_registry import PluginRegistry, get_plugin_registry
from app.utils.deprecation import deprecated

logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """搜索策略枚举"""
    COMPREHENSIVE = "comprehensive"   # 综合策略：所有插件并行，融合结果
    FAST = "fast"                     # 快速策略：仅用firecrawl（最快）
    AI_POWERED = "ai_powered"         # AI策略：仅用crawl4ai（智能提取）
    DYNAMIC = "dynamic"               # 动态策略：仅用browser-use（处理JS）
    REDUNDANT = "redundant"           # 冗余策略：多插件验证一致性


class SearchQueryType(Enum):
    """搜索查询类型枚举"""
    WEB_SEARCH = "web_search"                   # 网页搜索
    CONTENT_EXTRACTION = "content_extraction"   # 内容提取
    SITE_CRAWLING = "site_crawling"            # 站点爬取
    DYNAMIC_SCRAPING = "dynamic_scraping"      # 动态抓取
    BATCH_CRAWLING = "batch_crawling"          # 批量爬取
    STRUCTURED_EXTRACTION = "structured_extraction"  # 结构化提取


@dataclass
class SearchResult:
    """
    搜索结果数据类

    统一的搜索结果格式，支持智能合并和去重。
    """
    urls: List[str] = field(default_factory=list)           # 发现的URL列表
    contents: List[Dict[str, Any]] = field(default_factory=list)  # 提取的内容
    structured_data: List[Dict[str, Any]] = field(default_factory=list)  # 结构化数据
    screenshots: List[str] = field(default_factory=list)    # 截图路径
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    source_plugins: List[str] = field(default_factory=list)  # 来源插件
    confidence_score: float = 0.0                           # 置信度分数
    processing_time: float = 0.0                            # 处理耗时

    def merge(self, other: 'SearchResult') -> 'SearchResult':
        """
        智能合并两个搜索结果

        去重逻辑:
        - URLs: 按URL去重
        - Contents: 按URL+title去重
        - Structured data: 按关键字段去重

        Args:
            other: 另一个搜索结果

        Returns:
            合并后的新SearchResult对象
        """
        merged = SearchResult()

        # URL去重
        url_set = set()
        for url in self.urls + other.urls:
            if url and url not in url_set:
                merged.urls.append(url)
                url_set.add(url)

        # Content去重（基于url+title）
        content_keys = set()
        for content in self.contents + other.contents:
            key = (content.get('url', ''), content.get('title', ''))
            if key not in content_keys:
                merged.contents.append(content)
                content_keys.add(key)

        # Structured data去重（基于所有字段的元组）
        data_keys = set()
        for data in self.structured_data + other.structured_data:
            # 创建一个稳定的key
            key = tuple(sorted((k, str(v)) for k, v in data.items()))
            if key not in data_keys:
                merged.structured_data.append(data)
                data_keys.add(key)

        # 截图合并（不去重，保留所有）
        merged.screenshots = self.screenshots + other.screenshots

        # 元数据合并
        merged.metadata = {**self.metadata, **other.metadata}

        # 来源插件合并
        merged.source_plugins = list(set(self.source_plugins + other.source_plugins))

        # 置信度：按成功插件数量比例计算
        total_plugins = len(set(self.source_plugins + other.source_plugins))
        successful_plugins = len(merged.source_plugins)
        merged.confidence_score = successful_plugins / total_plugins if total_plugins > 0 else 0.0

        # 处理时间取较大值
        merged.processing_time = max(self.processing_time, other.processing_time)

        return merged


@deprecated(
    reason="SuperAgent架构已被6-Agent v2替代",
    replacement="app.tools.search.advanced_crawl",
    version="2.0"
)
class SuperSearchAgent(AgentBase):
    """
    超级搜索代理

    整合crawl4ai、firecrawl、browser-use三大搜索爬虫插件，
    提供统一的智能搜索接口和强大的数据提取能力。

    核心特性:
    1. 多插件并行执行
    2. 智能结果融合
    3. 自动容错降级
    4. 策略动态选择

    使用示例:
        agent = SuperSearchAgent(agent_id="search_001")

        task = AgentTask(
            task_id="task_001",
            task_type="web_search",
            input_data={
                'query_type': 'content_extraction',
                'url': 'https://example.com',
                'strategy': 'comprehensive',
                'parameters': {
                    'extract_images': True,
                    'follow_links': False
                }
            }
        )

        result = agent.execute_task(task)
        print(result.output_data['contents'])
    """

    def __init__(self,
        agent_id: Optional[str] = None,
        registry: Optional[PluginRegistry] = None,
        loader: Optional[PluginLoader] = None,


        use_workflow_engine: bool = True):
        """
        初始化SuperSearchAgent

        Args:
            agent_id: 代理唯一标识符
            registry: 插件注册表（可选，默认使用全局单例）
            loader: 插件加载器（可选，默认创建新实例）
        """
        # 初始化插件系统
        self.registry = registry or get_plugin_registry()
        self.loader = loader or PluginLoader(registry=self.registry, strategy=LoadStrategy.LAZY)

        # 定义搜索能力映射
        self.search_capabilities = {
            'ai_web_crawl': 'crawl4ai',        # AI驱动的智能爬虫
            'fast_web_crawl': 'firecrawl',     # 快速API爬虫
            'browser_automation': 'browser-use'  # 浏览器自动化
        }

        # 调用父类初始化
        super().__init__(agent_id=agent_id)

        logger.info(f"SuperSearchAgent initialized: {self.agent_id}")

    @property
    def role(self) -> AgentRole:
        """代理角色：搜索"""
        return AgentRole.SEARCH

    @property
    def name(self) -> str:
        """代理名称"""
        return "超级搜索代理"

    @property
    def description(self) -> str:
        """代理描述"""
        return "整合crawl4ai、firecrawl、browser-use三大搜索爬虫插件，提供智能网页搜索和数据提取能力"

    @property
    def capabilities(self) -> List[str]:
        """代理能力列表"""
        return [
            "web_search",
            "content_extraction",
            "site_crawling",
            "dynamic_scraping",
            "batch_crawling",
            "structured_extraction",
            "multi_plugin_fusion",
            "automatic_fallback"
        ]

    def _initialize_tools(self):
        """
        初始化工具集

        SuperSearchAgent的工具通过PluginLoader动态加载，
        这里只需初始化空字典，实际工具在执行时加载。
        """
        self.tools = {}

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行任务的同步包装器

        AgentBase要求同步接口，但搜索操作是异步的。
        这个方法提供async→sync的桥接。

        Args:
            task: 代理任务对象

        Returns:
            任务执行结果字典
        """
        # 检测当前事件循环状态
        loop = asyncio.get_event_loop()

        if loop.is_running():
            # 如果循环正在运行（如在Jupyter中），使用ensure_future
            future = asyncio.ensure_future(self._execute_task_async(task))
            # 等待完成（这里用简单的轮询，生产环境可能需要更优雅的方式）
            while not future.done():
                time.sleep(0.01)
            result = future.result()
        else:
            # 如果没有运行的循环，使用run_until_complete
            result = loop.run_until_complete(self._execute_task_async(task))

        return result

    async def _execute_task_async(self, task: AgentTask) -> Dict[str, Any]:
        """
        异步执行任务

        根据query_type和strategy选择执行路径。

        Args:
            task: 代理任务对象

        Returns:
            任务执行结果字典

        Raises:
            Exception: 任务执行失败时抛出异常，由AgentBase处理
        """
        input_data = task.input_data
        query_type = SearchQueryType(input_data.get('query_type', 'web_search'))
        strategy = SearchStrategy(input_data.get('strategy', 'comprehensive'))
        parameters = input_data.get('parameters', {})

        logger.info(f"Executing search task: type={query_type.value}, strategy={strategy.value}")

        # 根据查询类型路由到不同的处理方法
        if query_type == SearchQueryType.WEB_SEARCH:
            result = await self._web_search(input_data, strategy, parameters)
        elif query_type == SearchQueryType.CONTENT_EXTRACTION:
            result = await self._content_extraction(input_data, strategy, parameters)
        elif query_type == SearchQueryType.SITE_CRAWLING:
            result = await self._site_crawling(input_data, strategy, parameters)
        elif query_type == SearchQueryType.DYNAMIC_SCRAPING:
            result = await self._dynamic_scraping(input_data, strategy, parameters)
        elif query_type == SearchQueryType.BATCH_CRAWLING:
            result = await self._batch_crawling(input_data, strategy, parameters)
        elif query_type == SearchQueryType.STRUCTURED_EXTRACTION:
            result = await self._structured_extraction(input_data, strategy, parameters)
        else:
            raise ValueError(f"Unknown query type: {query_type}")

        # 转换为输出格式
        output = self._format_output(result, query_type, strategy)

        logger.info(f"Search task completed: {len(result.urls)} URLs, {len(result.contents)} contents")

        return output

    # ==================== 查询类型处理方法 ====================

    async def _web_search(
        self,
        input_data: Dict[str, Any],
        strategy: SearchStrategy,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        网页搜索：根据关键词或URL搜索网页

        Args:
            input_data: 输入数据（包含url或query）
            strategy: 搜索策略
            parameters: 额外参数

        Returns:
            搜索结果
        """
        url = input_data.get('url')
        query = input_data.get('query')

        if not url and not query:
            raise ValueError("Either 'url' or 'query' must be provided")

        if strategy == SearchStrategy.COMPREHENSIVE:
            return await self._comprehensive_search(url or query, parameters)
        elif strategy == SearchStrategy.FAST:
            return await self._execute_firecrawl(url or query, parameters)
        elif strategy == SearchStrategy.AI_POWERED:
            return await self._execute_crawl4ai(url or query, parameters)
        elif strategy == SearchStrategy.DYNAMIC:
            return await self._execute_browser_use(url or query, parameters)
        else:
            return await self._comprehensive_search(url or query, parameters)

    async def _content_extraction(
        self,
        input_data: Dict[str, Any],
        strategy: SearchStrategy,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        内容提取：从URL提取结构化内容

        推荐策略：AI_POWERED（crawl4ai善于内容提取）
        """
        url = input_data.get('url')
        if not url:
            raise ValueError("URL is required for content extraction")

        if strategy == SearchStrategy.FAST:
            return await self._execute_firecrawl(url, {**parameters, 'extract_content': True})
        elif strategy == SearchStrategy.COMPREHENSIVE:
            return await self._comprehensive_extraction(url, parameters)
        else:
            # AI_POWERED或其他默认用crawl4ai
            return await self._execute_crawl4ai(url, {**parameters, 'extract_content': True})

    async def _site_crawling(
        self,
        input_data: Dict[str, Any],
        strategy: SearchStrategy,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        站点爬取：递归爬取整个站点

        推荐策略：FAST（firecrawl有站点爬取API）
        """
        url = input_data.get('url')
        if not url:
            raise ValueError("URL is required for site crawling")

        max_depth = parameters.get('max_depth', 3)
        max_pages = parameters.get('max_pages', 100)

        if strategy == SearchStrategy.COMPREHENSIVE:
            return await self._comprehensive_crawling(url, max_depth, max_pages, parameters)
        else:
            # 其他策略默认用firecrawl
            return await self._execute_firecrawl(
                url,
                {**parameters, 'mode': 'crawl', 'max_depth': max_depth, 'max_pages': max_pages}
            )

    async def _dynamic_scraping(
        self,
        input_data: Dict[str, Any],
        strategy: SearchStrategy,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        动态抓取：处理需要JavaScript的页面

        推荐策略：DYNAMIC（browser-use专门处理动态页面）
        """
        url = input_data.get('url')
        if not url:
            raise ValueError("URL is required for dynamic scraping")

        if strategy == SearchStrategy.COMPREHENSIVE:
            # 综合策略：browser-use主力，其他辅助
            return await self._comprehensive_dynamic(url, parameters)
        else:
            # 其他策略默认用browser-use
            return await self._execute_browser_use(url, {**parameters, 'wait_for_js': True})

    async def _batch_crawling(
        self,
        input_data: Dict[str, Any],
        strategy: SearchStrategy,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        批量爬取：并行处理多个URL

        推荐策略：COMPREHENSIVE（并行用多插件，提高成功率）
        """
        urls = input_data.get('urls', [])
        if not urls:
            raise ValueError("URLs list is required for batch crawling")

        # 批量任务：为每个URL创建并发任务
        tasks = []
        for url in urls:
            if strategy == SearchStrategy.FAST:
                tasks.append(self._execute_firecrawl(url, parameters))
            elif strategy == SearchStrategy.AI_POWERED:
                tasks.append(self._execute_crawl4ai(url, parameters))
            elif strategy == SearchStrategy.DYNAMIC:
                tasks.append(self._execute_browser_use(url, parameters))
            else:
                tasks.append(self._comprehensive_search(url, parameters))

        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并所有结果
        merged_result = SearchResult()
        for result in results:
            if isinstance(result, SearchResult):
                merged_result = merged_result.merge(result)

        return merged_result

    async def _structured_extraction(
        self,
        input_data: Dict[str, Any],
        strategy: SearchStrategy,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        结构化提取：按schema提取结构化数据

        推荐策略：AI_POWERED（crawl4ai有AI提取能力）
        """
        url = input_data.get('url')
        schema = input_data.get('schema', {})

        if not url:
            raise ValueError("URL is required for structured extraction")

        extraction_params = {
            **parameters,
            'schema': schema,
            'structured': True
        }

        if strategy == SearchStrategy.COMPREHENSIVE:
            return await self._comprehensive_extraction(url, extraction_params)
        else:
            # 默认用crawl4ai的AI提取
            return await self._execute_crawl4ai(url, extraction_params)

    # ==================== 策略执行方法 ====================

    async def _comprehensive_search(
        self,
        url: str,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        综合搜索策略：并行执行所有插件，融合结果

        这是1+1>2的核心：多个插件互相补充，提高成功率和数据质量。

        Args:
            url: 目标URL
            parameters: 参数

        Returns:
            融合后的搜索结果
        """
        start_time = time.time()

        # 并行执行三个插件
        tasks = [
            self._execute_crawl4ai(url, parameters),
            self._execute_firecrawl(url, parameters),
            self._execute_browser_use(url, parameters)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        merged_result = SearchResult()
        for result in results:
            if isinstance(result, SearchResult):
                merged_result = merged_result.merge(result)
            elif isinstance(result, Exception):
                logger.warning(f"Plugin execution failed: {result}")

        # 计算统计信息
        successful_count = sum(1 for r in results if isinstance(r, SearchResult))
        merged_result.confidence_score = successful_count / len(tasks) if tasks else 0.0
        merged_result.processing_time = time.time() - start_time

        logger.info(
            f"Comprehensive search: {successful_count}/{len(tasks)} plugins succeeded, "
            f"found {len(merged_result.urls)} URLs, {len(merged_result.contents)} contents"
        )

        return merged_result

    async def _comprehensive_extraction(
        self,
        url: str,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """综合提取策略：用多个插件提取内容，交叉验证"""
        extraction_params = {**parameters, 'extract_content': True}
        return await self._comprehensive_search(url, extraction_params)

    async def _comprehensive_crawling(
        self,
        url: str,
        max_depth: int,
        max_pages: int,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """综合爬取策略：结合firecrawl的站点爬取和crawl4ai的智能提取"""
        # 用firecrawl获取URL列表（快速）
        crawl_params = {**parameters, 'mode': 'crawl', 'max_depth': max_depth, 'max_pages': max_pages}
        site_result = await self._execute_firecrawl(url, crawl_params)

        # 用crawl4ai提取重要页面的内容（智能）
        if site_result.urls:
            # 取前N个URL进行深度提取
            important_urls = site_result.urls[:min(10, len(site_result.urls))]
            extract_tasks = [
                self._execute_crawl4ai(u, {**parameters, 'extract_content': True})
                for u in important_urls
            ]
            extract_results = await asyncio.gather(*extract_tasks, return_exceptions=True)

            # 合并内容
            for result in extract_results:
                if isinstance(result, SearchResult):
                    site_result = site_result.merge(result)

        return site_result

    async def _comprehensive_dynamic(
        self,
        url: str,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """综合动态抓取策略：browser-use主力，crawl4ai辅助"""
        # browser-use处理动态内容
        dynamic_result = await self._execute_browser_use(url, {**parameters, 'wait_for_js': True})

        # crawl4ai做内容提取
        extract_result = await self._execute_crawl4ai(url, {**parameters, 'extract_content': True})

        return dynamic_result.merge(extract_result)

    # ==================== 插件执行方法 ====================

    async def _execute_crawl4ai(
        self,
        url: str,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        执行crawl4ai插件

        特点：AI驱动，智能内容提取，支持复杂场景

        Args:
            url: 目标URL
            parameters: 参数

        Returns:
            搜索结果
        """
        try:
            start_time = time.time()

            # TODO: 实际调用crawl4ai插件
            # plugin = self.loader.load_plugin('crawl4ai')
            # result = await plugin.crawl(url, **parameters)

            # 模拟结果（实际集成时替换）
            result = SearchResult(
                urls=[url],
                contents=[{
                    'url': url,
                    'title': f'Content from {url}',
                    'text': 'AI-extracted content...',
                    'main_content': 'Main content extracted by AI',
                    'metadata': {'extractor': 'crawl4ai'}
                }],
                source_plugins=['crawl4ai'],
                confidence_score=0.9,
                processing_time=time.time() - start_time
            )

            logger.debug(f"crawl4ai executed: {url}")
            return result

        except Exception as e:
            logger.error(f"crawl4ai execution failed: {e}")
            raise

    async def _execute_firecrawl(
        self,
        url: str,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        执行firecrawl插件

        特点：快速，API调用，支持站点爬取

        Args:
            url: 目标URL
            parameters: 参数

        Returns:
            搜索结果
        """
        try:
            start_time = time.time()

            # TODO: 实际调用firecrawl插件
            # plugin = self.loader.load_plugin('firecrawl')
            # result = await plugin.scrape(url, **parameters)

            # 模拟结果（实际集成时替换）
            mode = parameters.get('mode', 'scrape')

            if mode == 'crawl':
                # 站点爬取模式
                max_pages = parameters.get('max_pages', 10)
                result = SearchResult(
                    urls=[f"{url}/page{i}" for i in range(1, min(max_pages, 5) + 1)],
                    contents=[{
                        'url': f"{url}/page{i}",
                        'title': f'Page {i}',
                        'markdown': f'Content from page {i}',
                        'metadata': {'extractor': 'firecrawl'}
                    } for i in range(1, min(max_pages, 5) + 1)],
                    source_plugins=['firecrawl'],
                    confidence_score=0.85,
                    processing_time=time.time() - start_time
                )
            else:
                # 单页抓取模式
                result = SearchResult(
                    urls=[url],
                    contents=[{
                        'url': url,
                        'title': f'Content from {url}',
                        'markdown': 'Fast scraped content...',
                        'metadata': {'extractor': 'firecrawl'}
                    }],
                    source_plugins=['firecrawl'],
                    confidence_score=0.85,
                    processing_time=time.time() - start_time
                )

            logger.debug(f"firecrawl executed: {url} (mode={mode})")
            return result

        except Exception as e:
            logger.error(f"firecrawl execution failed: {e}")
            raise

    async def _execute_browser_use(
        self,
        url: str,
        parameters: Dict[str, Any]
    ) -> SearchResult:
        """
        执行browser-use插件

        特点：浏览器自动化，处理动态内容，支持交互

        Args:
            url: 目标URL
            parameters: 参数

        Returns:
            搜索结果
        """
        try:
            start_time = time.time()

            # TODO: 实际调用browser-use插件
            # plugin = self.loader.load_plugin('browser-use')
            # result = await plugin.browse(url, **parameters)

            # 模拟结果（实际集成时替换）
            wait_for_js = parameters.get('wait_for_js', False)
            take_screenshot = parameters.get('take_screenshot', False)

            screenshots = []
            if take_screenshot:
                screenshots = [f'/tmp/screenshot_{uuid.uuid4().hex}.png']

            result = SearchResult(
                urls=[url],
                contents=[{
                    'url': url,
                    'title': f'Dynamic content from {url}',
                    'html': '<html>...</html>',
                    'text': 'Content after JS execution',
                    'metadata': {'extractor': 'browser-use', 'js_executed': wait_for_js}
                }],
                screenshots=screenshots,
                source_plugins=['browser-use'],
                confidence_score=0.88,
                processing_time=time.time() - start_time
            )

            logger.debug(f"browser-use executed: {url} (js={wait_for_js})")
            return result

        except Exception as e:
            logger.error(f"browser-use execution failed: {e}")
            raise

    # ==================== 辅助方法 ====================

    def _format_output(
        self,
        result: SearchResult,
        query_type: SearchQueryType,
        strategy: SearchStrategy
    ) -> Dict[str, Any]:
        """
        格式化输出结果

        Args:
            result: 搜索结果对象
            query_type: 查询类型
            strategy: 执行策略

        Returns:
            格式化的输出字典
        """
        return {
            'status': 'success',
            'query_type': query_type.value,
            'strategy': strategy.value,
            'urls': result.urls,
            'contents': result.contents,
            'structured_data': result.structured_data,
            'screenshots': result.screenshots,
            'metadata': result.metadata,
            'statistics': {
                'total_urls': len(result.urls),
                'total_contents': len(result.contents),
                'total_structured': len(result.structured_data),
                'source_plugins': result.source_plugins,
                'confidence_score': result.confidence_score,
                'processing_time': result.processing_time
            }
        }

    def get_supported_strategies(self, query_type: SearchQueryType) -> List[SearchStrategy]:
        """
        获取查询类型支持的策略列表

        Args:
            query_type: 查询类型

        Returns:
            支持的策略列表
        """
        # 所有查询类型都支持这些基础策略
        base_strategies = [SearchStrategy.COMPREHENSIVE, SearchStrategy.FAST]

        # 特定查询类型的推荐策略
        if query_type in [SearchQueryType.CONTENT_EXTRACTION, SearchQueryType.STRUCTURED_EXTRACTION]:
            base_strategies.append(SearchStrategy.AI_POWERED)

        if query_type in [SearchQueryType.DYNAMIC_SCRAPING]:
            base_strategies.append(SearchStrategy.DYNAMIC)

        return base_strategies

    def get_plugin_status(self) -> Dict[str, Any]:
        """
        获取插件状态信息

        Returns:
            插件状态字典
        """
        status = {}

        for capability, plugin_id in self.search_capabilities.items():
            # 检查插件是否可用
            plugins = self.registry.get_plugins_by_capability(capability)
            available = len(plugins) > 0

            status[plugin_id] = {
                'capability': capability,
                'available': available,
                'plugin_count': len(plugins)
            }

        return status




        # WorkflowEngine 集成


        self.use_workflow_engine = use_workflow_engine


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

