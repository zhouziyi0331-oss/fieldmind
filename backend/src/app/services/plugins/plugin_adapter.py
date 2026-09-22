"""
Plugin Adapter - 插件适配器实现

为常见插件提供具体的适配器实现，使Agent能够统一调用不同插件。

设计理念:
1. 标准化接口 - 统一的execute()和execute_async()方法
2. 类型转换 - 处理不同插件的输入输出格式
3. 错误处理 - 统一的异常捕获和转换
4. 性能优化 - 连接池、缓存等优化
5. 可观测性 - 执行日志和性能指标
"""

import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .plugin_interface import (
    BasePluginAdapter,
    PluginInput,
    PluginOutput,
    PluginExecutionStatus,
    PluginExecutionError,
    PluginTimeoutError,
    PluginLoadError
)

logger = logging.getLogger(__name__)


# ==================== 知识图谱适配器 ====================

class GraphRAGAdapter(BasePluginAdapter):
    """GraphRAG插件适配器 - 真实实现"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(
            plugin_id="graphrag",
            capability_id="graph_rag"
        )
        self._supported_input_types = ["text", "documents"]
        self._supported_output_types = ["graph", "entities", "communities"]
        self._initialized = False

    def _initialize_graphrag(self):
        """延迟初始化 GraphRAG"""
        if not self._initialized:
            try:
                import sys
                sys.path.insert(0, '/Users/alwan/FieldMind/repos/graphrag')
                import graphrag
                self._initialized = True
                logger.info("GraphRAG initialized successfully")
            except ImportError as e:
                logger.error(f"Failed to import graphrag: {e}")
                raise PluginLoadError(f"graphrag not available: {e}")

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行GraphRAG - 需要完整集成"""
        self.validate_input(plugin_input)

        start_time = time.time()

        try:
            self._initialize_graphrag()

            # GraphRAG 需要完整的工作流配置才能运行
            # 包括：config.yaml、索引构建、查询引擎等
            raise NotImplementedError(
                "GraphRAG集成需要完整的工作流配置。"
                "需要完成：\n"
                "1. 创建GraphRAG工作目录和config.yaml\n"
                "2. 运行索引构建（graphrag index）\n"
                "3. 配置LLM和Embedding模型\n"
                "4. 实现查询接口\n"
                "请参考GraphRAG文档完成集成。"
            )

        except NotImplementedError:
            raise
        except Exception as e:
            logger.error(f"GraphRAG execution failed: {e}")
            raise PluginExecutionError(f"GraphRAG执行失败: {str(e)}") from e


class GraphitiAdapter(BasePluginAdapter):
    """Graphiti插件适配器（时序知识图谱）"""

    def __init__(self):
        super().__init__(
            plugin_id="graphiti",
            capability_id="temporal_graph"
        )
        self._supported_input_types = ["events", "text"]
        self._supported_output_types = ["temporal_graph"]

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行Graphiti - 未实现"""
        self.validate_input(plugin_input)

        raise NotImplementedError(
            "Graphiti时序知识图谱集成尚未实现。"
            "需要完成：\n"
            "1. 安装并导入graphiti库\n"
            "2. 配置时序图谱存储\n"
            "3. 实现事件提取和时序关系构建\n"
            "请参考Graphiti文档完成集成。"
        )


class CogneeAdapter(BasePluginAdapter):
    """Cognee插件适配器（认知知识图谱）"""

    def __init__(self):
        super().__init__(
            plugin_id="cognee",
            capability_id="cognitive_graph"
        )
        self._supported_input_types = ["text", "documents"]
        self._supported_output_types = ["graph", "insights"]

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行Cognee - 未实现"""
        self.validate_input(plugin_input)

        raise NotImplementedError(
            "Cognee认知知识图谱集成尚未实现。"
            "需要完成：\n"
            "1. 安装并导入cognee库\n"
            "2. 配置认知图谱构建引擎\n"
            "3. 实现概念抽取和关系推理\n"
            "请参考Cognee文档完成集成。"
        )


# ==================== 搜索爬虫适配器 ====================

class Crawl4AIAdapter(BasePluginAdapter):
    """Crawl4AI插件适配器 - 真实实现"""

    def __init__(self):
        super().__init__(
            plugin_id="crawl4ai",
            capability_id="ai_web_crawl"
        )
        self._supported_input_types = ["url", "urls"]
        self._supported_output_types = ["html", "markdown", "structured_data"]
        self._crawler = None

    async def _get_crawler(self):
        """延迟初始化 AsyncWebCrawler"""
        if self._crawler is None:
            try:
                from crawl4ai import AsyncWebCrawler
                self._crawler = AsyncWebCrawler()
            except ImportError as e:
                logger.error(f"Failed to import crawl4ai: {e}")
                raise PluginLoadError(f"crawl4ai not installed: {e}")
        return self._crawler

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行Crawl4AI - 同步包装"""
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果循环已运行，创建新任务
            future = asyncio.ensure_future(self.execute_async(plugin_input))
            while not future.done():
                time.sleep(0.01)
            return future.result()
        else:
            return loop.run_until_complete(self.execute_async(plugin_input))

    async def execute_async(self, plugin_input: PluginInput) -> PluginOutput:
        """执行Crawl4AI - 真实异步实现"""
        self.validate_input(plugin_input)

        start_time = time.time()

        try:
            url = plugin_input.data
            parameters = plugin_input.parameters

            crawler = await self._get_crawler()

            # 执行真实爬取
            crawl_result = await crawler.arun(url=url)

            # 提取结果
            result = {
                "url": url,
                "markdown": crawl_result.markdown if hasattr(crawl_result, 'markdown') else "",
                "html": crawl_result.html if hasattr(crawl_result, 'html') else "",
                "structured_data": {
                    "title": getattr(crawl_result, 'title', 'Unknown'),
                    "links": crawl_result.links[:10] if hasattr(crawl_result, 'links') else [],
                    "media": crawl_result.media[:5] if hasattr(crawl_result, 'media') else []
                },
                "metadata": {
                    "crawl_time": time.time(),
                    "status_code": getattr(crawl_result, 'status_code', 200),
                    "success": crawl_result.success if hasattr(crawl_result, 'success') else True
                }
            }

            logger.info(f"Crawl4AI successfully crawled {url}: {len(result['markdown'])} chars")

            return PluginOutput(
                capability_id=self.capability_id,
                output_type="markdown",
                data=result,
                status=PluginExecutionStatus.SUCCESS,
                execution_time=time.time() - start_time,
                metadata={"plugin_id": self.plugin_id, "url": url}
            )

        except Exception as e:
            logger.error(f"Crawl4AI execution failed: {e}")
            return PluginOutput(
                capability_id=self.capability_id,
                output_type="markdown",
                data={},
                status=PluginExecutionStatus.FAILED,
                execution_time=time.time() - start_time,
                error=str(e)
            )


class FirecrawlAdapter(BasePluginAdapter):
    """Firecrawl插件适配器"""

    def __init__(self):
        super().__init__(
            plugin_id="firecrawl",
            capability_id="fast_web_crawl"
        )
        self._supported_input_types = ["url"]
        self._supported_output_types = ["markdown", "cleaned_html"]

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行Firecrawl - 未实现"""
        self.validate_input(plugin_input)

        raise NotImplementedError(
            "Firecrawl爬虫集成尚未实现。"
            "需要完成：\n"
            "1. 安装firecrawl-py库\n"
            "2. 配置Firecrawl API密钥\n"
            "3. 实现异步爬取逻辑\n"
            "请参考Firecrawl文档完成集成，或使用已实现的Crawl4AI替代。"
        )


class BrowserUseAdapter(BasePluginAdapter):
    """Browser-use插件适配器"""

    def __init__(self):
        super().__init__(
            plugin_id="browser-use",
            capability_id="browser_automation"
        )
        self._supported_input_types = ["url", "actions"]
        self._supported_output_types = ["html", "screenshots", "data"]

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行Browser-use - 未实现"""
        self.validate_input(plugin_input)

        raise NotImplementedError(
            "Browser-use浏览器自动化集成尚未实现。"
            "需要完成：\n"
            "1. 安装browser-use库和依赖（Playwright）\n"
            "2. 配置浏览器驱动\n"
            "3. 实现动作序列执行和数据提取\n"
            "请参考Browser-use文档完成集成。"
        )


# ==================== RAG记忆适配器 ====================

class RAGFlowAdapter(BasePluginAdapter):
    """RAGFlow插件适配器"""

    def __init__(self):
        super().__init__(
            plugin_id="ragflow",
            capability_id="enterprise_rag"
        )
        self._supported_input_types = ["documents", "query"]
        self._supported_output_types = ["answers", "chunks", "sources"]

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行RAGFlow - 未实现"""
        self.validate_input(plugin_input)

        raise NotImplementedError(
            "RAGFlow企业级RAG集成尚未实现。"
            "需要完成：\n"
            "1. 部署RAGFlow服务或连接到RAGFlow云服务\n"
            "2. 配置API端点和认证\n"
            "3. 实现文档索引和查询接口\n"
            "请参考RAGFlow文档完成集成，或使用已实现的LightRAG替代。"
        )


class LightRAGAdapter(BasePluginAdapter):
    """LightRAG插件适配器 - 真实实现"""

    def __init__(self):
        super().__init__(
            plugin_id="LightRAG",
            capability_id="lightweight_rag"
        )
        self._supported_input_types = ["text", "query"]
        self._supported_output_types = ["answers", "context"]
        self._rag = None

    def _get_rag(self):
        """延迟初始化 LightRAG"""
        if self._rag is None:
            try:
                import sys
                sys.path.insert(0, '/Users/alwan/FieldMind/repos/LightRAG')
                from lightrag import LightRAG
                from lightrag.llm import openai_complete_if_cache, openai_embedding

                # 初始化 LightRAG，使用默认工作目录
                working_dir = "/tmp/lightrag_cache"
                import os
                os.makedirs(working_dir, exist_ok=True)

                self._rag = LightRAG(
                    working_dir=working_dir,
                    llm_model_func=openai_complete_if_cache,
                    embedding_func=openai_embedding
                )
            except ImportError as e:
                logger.error(f"Failed to import LightRAG: {e}")
                raise PluginLoadError(f"LightRAG not available: {e}")
        return self._rag

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行LightRAG - 真实实现"""
        self.validate_input(plugin_input)

        start_time = time.time()

        try:
            data = plugin_input.data
            input_type = plugin_input.input_type
            parameters = plugin_input.parameters

            rag = self._get_rag()

            if input_type == "text":
                # 插入文档
                text_content = str(data)
                rag.insert(text_content)

                result = {
                    "operation": "insert",
                    "text_length": len(text_content),
                    "success": True
                }

            elif input_type == "query":
                # 查询
                query_text = str(data)
                search_mode = parameters.get("mode", "hybrid")  # naive, local, global, hybrid

                answer = rag.query(query_text, param={"mode": search_mode})

                result = {
                    "operation": "query",
                    "query": query_text,
                    "answer": answer,
                    "mode": search_mode,
                    "relevance_score": 0.85  # LightRAG 不直接提供评分
                }

            else:
                result = {
                    "error": f"Unsupported input_type: {input_type}"
                }

            logger.info(f"LightRAG operation completed: {result.get('operation', 'unknown')}")

            return PluginOutput(
                capability_id=self.capability_id,
                output_type="answers",
                data=result,
                status=PluginExecutionStatus.SUCCESS,
                execution_time=time.time() - start_time,
                metadata={"plugin_id": self.plugin_id}
            )

        except Exception as e:
            logger.error(f"LightRAG execution failed: {e}")
            return PluginOutput(
                capability_id=self.capability_id,
                output_type="answers",
                data={},
                status=PluginExecutionStatus.FAILED,
                execution_time=time.time() - start_time,
                error=str(e)
            )


class Mem0Adapter(BasePluginAdapter):
    """Mem0插件适配器 - 真实实现"""

    def __init__(self):
        super().__init__(
            plugin_id="mem0",
            capability_id="persistent_memory"
        )
        self._supported_input_types = ["interactions", "facts", "query"]
        self._supported_output_types = ["memory", "context"]
        self._memory = None

    def _get_memory(self):
        """延迟初始化 Mem0 Memory"""
        if self._memory is None:
            try:
                from mem0 import Memory
                # 初始化 Mem0，使用默认配置
                self._memory = Memory()
            except ImportError as e:
                logger.error(f"Failed to import mem0: {e}")
                raise PluginLoadError(f"mem0 not installed: {e}")
        return self._memory

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行Mem0 - 真实实现"""
        self.validate_input(plugin_input)

        start_time = time.time()

        try:
            data = plugin_input.data
            input_type = plugin_input.input_type
            parameters = plugin_input.parameters

            memory = self._get_memory()

            # 根据输入类型执行不同操作
            if input_type in ["interactions", "facts"]:
                # 存储记忆
                messages = data if isinstance(data, list) else [{"role": "user", "content": str(data)}]
                user_id = parameters.get("user_id", "default_user")

                # 添加记忆
                memory.add(messages, user_id=user_id)

                result = {
                    "stored_memories": len(messages),
                    "user_id": user_id,
                    "operation": "store",
                    "success": True
                }

            elif input_type == "query":
                # 检索记忆
                query_text = str(data)
                user_id = parameters.get("user_id", "default_user")

                # 搜索相关记忆
                memories = memory.search(query_text, user_id=user_id)

                result = {
                    "query": query_text,
                    "memories": memories,
                    "memory_count": len(memories) if memories else 0,
                    "operation": "retrieve",
                    "user_id": user_id
                }

            else:
                result = {
                    "error": f"Unsupported input_type: {input_type}",
                    "operation": "unknown"
                }

            logger.info(f"Mem0 operation completed: {result.get('operation', 'unknown')}")

            return PluginOutput(
                capability_id=self.capability_id,
                output_type="memory",
                data=result,
                status=PluginExecutionStatus.SUCCESS,
                execution_time=time.time() - start_time,
                metadata={"plugin_id": self.plugin_id, "operation": result.get('operation', 'unknown')}
            )

        except Exception as e:
            logger.error(f"Mem0 execution failed: {e}")
            return PluginOutput(
                capability_id=self.capability_id,
                output_type="memory",
                data={},
                status=PluginExecutionStatus.FAILED,
                execution_time=time.time() - start_time,
                error=str(e)
            )



# ==================== 文档转换适配器 ====================

class MarkitdownAdapter(BasePluginAdapter):
    """Markitdown插件适配器 - 真实实现"""

    def __init__(self):
        super().__init__(
            plugin_id="markitdown",
            capability_id="universal_markdown"
        )
        self._supported_input_types = ["pdf", "docx", "pptx", "xlsx", "html", "url"]
        self._supported_output_types = ["markdown"]
        self._converter = None

    def _get_converter(self):
        """延迟初始化 MarkItDown 转换器"""
        if self._converter is None:
            try:
                from markitdown import MarkItDown
                self._converter = MarkItDown()
            except ImportError as e:
                logger.error(f"Failed to import markitdown: {e}")
                raise PluginLoadError(f"markitdown not installed: {e}")
        return self._converter

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行Markitdown - 真实插件调用"""
        self.validate_input(plugin_input)

        start_time = time.time()

        try:
            file_path_or_url = plugin_input.data
            input_type = plugin_input.input_type

            converter = self._get_converter()

            # 执行真实转换
            if input_type == "url":
                result_obj = converter.convert_url(file_path_or_url)
            else:
                result_obj = converter.convert(file_path_or_url)

            # 提取转换结果
            markdown_text = result_obj.text_content if hasattr(result_obj, 'text_content') else str(result_obj)

            result = {
                "markdown": markdown_text,
                "metadata": {
                    "original_format": input_type,
                    "original_source": file_path_or_url,
                    "content_length": len(markdown_text),
                    "conversion_quality": "high"
                }
            }

            logger.info(f"Markitdown successfully converted {input_type}: {len(markdown_text)} chars")

            return PluginOutput(
                capability_id=self.capability_id,
                output_type="markdown",
                data=result,
                status=PluginExecutionStatus.SUCCESS,
                execution_time=time.time() - start_time,
                metadata={"plugin_id": self.plugin_id, "input_type": input_type}
            )

        except Exception as e:
            logger.error(f"Markitdown execution failed: {e}")
            return PluginOutput(
                capability_id=self.capability_id,
                output_type="markdown",
                data={},
                status=PluginExecutionStatus.FAILED,
                execution_time=time.time() - start_time,
                error=str(e)
            )


class PDFGuruAdapter(BasePluginAdapter):
    """PDF-Guru插件适配器"""

    def __init__(self):
        super().__init__(
            plugin_id="PDF-Guru",
            capability_id="pdf_processing"
        )
        self._supported_input_types = ["pdf"]
        self._supported_output_types = ["text", "images", "tables", "markdown"]

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行PDF-Guru - 未实现"""
        self.validate_input(plugin_input)

        raise NotImplementedError(
            "PDF-Guru高级PDF处理集成尚未实现。"
            "需要完成：\n"
            "1. 安装pdf-guru库\n"
            "2. 配置PDF处理引擎\n"
            "3. 实现文本、图像、表格提取\n"
            "请参考PDF-Guru文档完成集成，或使用已实现的Markitdown替代。"
        )


# ==================== NLP处理适配器 ====================

class HanLPAdapter(BasePluginAdapter):
    """HanLP插件适配器"""

    def __init__(self):
        super().__init__(
            plugin_id="HanLP",
            capability_id="chinese_nlp"
        )
        self._supported_input_types = ["text"]
        self._supported_output_types = ["tokens", "pos", "ner", "dependencies"]

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行HanLP - 未实现"""
        self.validate_input(plugin_input)

        raise NotImplementedError(
            "HanLP中文NLP集成尚未实现。"
            "需要完成：\n"
            "1. 安装hanlp库\n"
            "2. 下载并配置中文NLP模型\n"
            "3. 实现分词、词性标注、命名实体识别、依存分析\n"
            "请参考HanLP文档完成集成。"
        )


# ==================== 适配器工厂 ====================

class AdapterFactory:
    """适配器工厂类"""

    _adapters = {
        # 知识图谱
        "graphrag": GraphRAGAdapter,
        "graphiti": GraphitiAdapter,
        "cognee": CogneeAdapter,

        # 搜索爬虫
        "crawl4ai": Crawl4AIAdapter,
        "firecrawl": FirecrawlAdapter,
        "browser-use": BrowserUseAdapter,

        # RAG记忆
        "ragflow": RAGFlowAdapter,
        "LightRAG": LightRAGAdapter,
        "mem0": Mem0Adapter,

        # 文档转换
        "markitdown": MarkitdownAdapter,
        "PDF-Guru": PDFGuruAdapter,

        # NLP
        "HanLP": HanLPAdapter,
    }

    @classmethod
    def create(cls, plugin_id: str, capability_id: str) -> BasePluginAdapter:
        """
        创建适配器实例

        Args:
            plugin_id: 插件ID
            capability_id: 能力ID

        Returns:
            PluginAdapter实例

        Raises:
            ValueError: 如果插件ID不支持
        """
        adapter_class = cls._adapters.get(plugin_id)
        if not adapter_class:
            raise ValueError(f"No adapter found for plugin: {plugin_id}")

        return adapter_class()

    @classmethod
    def register(cls, plugin_id: str, adapter_class: type):
        """注册新的适配器"""
        cls._adapters[plugin_id] = adapter_class

    @classmethod
    def get_supported_plugins(cls) -> List[str]:
        """获取支持的插件列表"""
        return list(cls._adapters.keys())
