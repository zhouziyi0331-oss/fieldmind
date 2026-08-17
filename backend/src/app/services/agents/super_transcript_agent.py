"""
SuperTranscriptAgent - 文档转换超级代理

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.transcript.document_convert

整合 markitdown + PDF-Guru 两大文档转换插件，提供：
1. 多格式文档转换（PDF, DOCX, PPTX, XLSX, HTML → Markdown）
2. 智能内容提取（文本、图片、表格）
3. 格式保留和优化
4. 批量处理能力

核心特性：
- 多插件融合：并行执行多个插件，智能合并结果
- 策略模式：5种执行策略（综合、快速、专业、批量、冗余）
- 查询类型路由：6种查询类型自动选择最优插件组合
- 自动降级：单插件失败不影响整体任务
- 结果去重：智能去重算法避免重复内容
- 置信度评分：基于成功插件数量计算置信度

作者: Agent Mesh Team
日期: 2026-08-14
Phase: 2 Day 4
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.services.agents.base_agent import AgentBase, AgentRole, AgentStatus, AgentTask
from app.services.plugins.plugin_loader import get_plugin_loader
from app.services.plugins.plugin_registry import get_plugin_registry
from app.utils.deprecation import deprecated

logger = logging.getLogger(__name__)


# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class TranscriptResult:
    """文档转换结果，支持智能合并"""

    # 核心内容
    markdown_content: str = ""
    plain_text: str = ""

    # 结构化提取
    images: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 质量指标
    page_count: int = 0
    word_count: int = 0
    image_count: int = 0
    table_count: int = 0

    # 来源追踪
    source_plugins: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    processing_time: float = 0.0

    # 错误信息
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def merge(self, other: 'TranscriptResult') -> 'TranscriptResult':
        """
        智能合并两个转换结果

        合并策略：
        1. markdown_content: 选择更长的
        2. plain_text: 选择更长的
        3. images: 按 image_id 或 URL 去重
        4. tables: 按 table_id 或内容哈希去重
        5. metadata: 深度合并
        6. 计数指标: 取最大值
        7. confidence_score: 平均值
        """
        merged = TranscriptResult()

        # 1. 选择更长的内容
        if len(self.markdown_content) >= len(other.markdown_content):
            merged.markdown_content = self.markdown_content
        else:
            merged.markdown_content = other.markdown_content

        if len(self.plain_text) >= len(other.plain_text):
            merged.plain_text = self.plain_text
        else:
            merged.plain_text = other.plain_text

        # 2. 图片去重（按 image_id 或 url）
        image_keys: Set[str] = set()
        for img in self.images + other.images:
            key = img.get('image_id') or img.get('url') or img.get('path', '')
            if key and key not in image_keys:
                merged.images.append(img)
                image_keys.add(key)

        # 3. 表格去重（按 table_id 或前100字符）
        table_keys: Set[str] = set()
        for table in self.tables + other.tables:
            key = table.get('table_id') or str(table.get('content', ''))[:100]
            if key and key not in table_keys:
                merged.tables.append(table)
                table_keys.add(key)

        # 4. 元数据深度合并
        merged.metadata = {**self.metadata, **other.metadata}

        # 5. 计数指标：取最大值
        merged.page_count = max(self.page_count, other.page_count)
        merged.word_count = max(self.word_count, other.word_count)
        merged.image_count = len(merged.images)
        merged.table_count = len(merged.tables)

        # 6. 来源追踪
        merged.source_plugins = list(set(self.source_plugins + other.source_plugins))

        # 7. 置信度：平均值
        if self.confidence_score > 0 and other.confidence_score > 0:
            merged.confidence_score = (self.confidence_score + other.confidence_score) / 2
        else:
            merged.confidence_score = max(self.confidence_score, other.confidence_score)

        merged.processing_time = self.processing_time + other.processing_time

        # 8. 合并警告和错误
        merged.warnings = list(set(self.warnings + other.warnings))
        merged.errors = list(set(self.errors + other.errors))

        return merged


class TranscriptStrategy(Enum):
    """文档转换执行策略"""

    COMPREHENSIVE = "comprehensive"   # 综合：所有插件并行，合并结果
    FAST = "fast"                     # 快速：仅 markitdown（轻量级）
    PROFESSIONAL = "professional"     # 专业：仅 PDF-Guru（高质量）
    BATCH = "batch"                   # 批量：优先速度，fallback 到质量
    REDUNDANT = "redundant"           # 冗余：多插件验证，确保准确性


class TranscriptQueryType(Enum):
    """文档转换查询类型"""

    FORMAT_CONVERSION = "format_conversion"           # 格式转换：PDF/DOCX → Markdown
    CONTENT_EXTRACTION = "content_extraction"         # 内容提取：文本、图片、表格
    BATCH_PROCESSING = "batch_processing"             # 批量处理：多文件转换
    QUALITY_OPTIMIZATION = "quality_optimization"     # 质量优化：高精度转换
    METADATA_EXTRACTION = "metadata_extraction"       # 元数据提取：作者、日期等
    STRUCTURE_ANALYSIS = "structure_analysis"         # 结构分析：章节、目录


# ============================================================================
# SuperTranscriptAgent 核心实现
# ============================================================================

@deprecated(
    reason="SuperAgent架构已被6-Agent v2替代",
    replacement="app.tools.transcript.document_convert",
    version="2.0"
)
class SuperTranscriptAgent(AgentBase):
    """
    文档转换超级代理

    整合 markitdown + PDF-Guru 两大文档转换插件，提供：
    1. 多格式文档转换
    2. 智能内容提取
    3. 格式保留和优化
    4. 批量处理能力

    插件集成：
    - markitdown: 轻量级通用转换（优先级 10）
    - PDF-Guru: 专业 PDF 处理（优先级 9）

    查询类型映射：
    - format_conversion → FAST: markitdown
    - content_extraction → PROFESSIONAL: PDF-Guru
    - batch_processing → BATCH: markitdown → PDF-Guru
    - quality_optimization → PROFESSIONAL: PDF-Guru
    - metadata_extraction → COMPREHENSIVE: 两者
    - structure_analysis → COMPREHENSIVE: 两者

    策略模式：
    - comprehensive: 两个插件并行，智能合并
    - fast: 仅 markitdown
    - professional: 仅 PDF-Guru
    - batch: markitdown 优先，失败则 PDF-Guru
    - redundant: 两者并行，交叉验证
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        registry: Optional[Any] = None,
        loader: Optional[Any] = None
    ):
        """
        初始化 SuperTranscriptAgent

        Args:
            agent_id: 代理唯一标识
            registry: 插件注册表实例
            loader: 插件加载器实例
        """
        # 依赖注入
        self.registry = registry or get_plugin_registry()
        self.loader = loader or get_plugin_loader()

        # 能力映射
        self.transcript_capabilities = {
            'universal_markdown': 'markitdown',
            'pdf_processing': 'PDF-Guru',
        }

        # 调用父类初始化
        super().__init__(agent_id=agent_id)

        logger.info(
            f"SuperTranscriptAgent initialized: {self.agent_id}, "
            f"capabilities: {list(self.transcript_capabilities.keys())}"
        )

    # ========================================================================
    # AgentBase 抽象方法实现
    # ========================================================================

    @property
    def role(self) -> AgentRole:
        """代理角色"""
        return AgentRole.TRANSCRIPT

    @property
    def name(self) -> str:
        """代理名称"""
        return "超级文档转换代理"

    @property
    def description(self) -> str:
        """代理描述"""
        return (
            "整合markitdown、PDF-Guru两大文档转换插件，提供多格式文档转换、"
            "智能内容提取、格式保留优化、批量处理能力。支持PDF、DOCX、PPTX、"
            "XLSX、HTML等格式转换为Markdown。"
        )

    @property
    def capabilities(self) -> List[str]:
        """代理能力列表"""
        return [
            "format_conversion",      # 格式转换
            "content_extraction",     # 内容提取
            "batch_processing",       # 批量处理
            "quality_optimization",   # 质量优化
            "metadata_extraction",    # 元数据提取
            "structure_analysis",     # 结构分析
            "multi_plugin_fusion",    # 多插件融合
            "automatic_fallback",     # 自动降级
        ]

    def _initialize_tools(self):
        """初始化工具（文档转换代理不需要额外工具）"""
        self.tools = {}

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行任务的核心实现（同步入口）

        桥接同步和异步：
        1. 获取或创建事件循环
        2. 如果循环正在运行，创建 Future 并轮询
        3. 否则直接 run_until_complete

        Args:
            task: 代理任务对象

        Returns:
            任务执行结果字典
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # 循环正在运行，创建 future 并轮询
            future = asyncio.ensure_future(self._execute_task_async(task))
            while not future.done():
                time.sleep(0.01)
            result = future.result()
        else:
            # 循环未运行，直接执行
            result = loop.run_until_complete(self._execute_task_async(task))

        return result

    # ========================================================================
    # 异步任务执行逻辑
    # ========================================================================

    async def _execute_task_async(self, task: AgentTask) -> Dict[str, Any]:
        """
        异步执行任务

        Args:
            task: 代理任务对象

        Returns:
            任务执行结果字典
        """
        start_time = time.time()

        try:
            # 1. 提取参数
            input_data = task.input_data
            query_type_str = input_data.get('query_type', 'format_conversion')
            strategy_str = input_data.get('strategy', 'comprehensive')
            file_path = input_data.get('file_path', '')
            files = input_data.get('files', [])
            parameters = input_data.get('parameters', {})

            # 2. 转换枚举
            try:
                query_type = TranscriptQueryType(query_type_str)
            except ValueError:
                query_type = TranscriptQueryType.FORMAT_CONVERSION

            try:
                strategy = TranscriptStrategy(strategy_str)
            except ValueError:
                strategy = TranscriptStrategy.COMPREHENSIVE

            logger.info(
                f"Executing task {task.task_id}: query_type={query_type.value}, "
                f"strategy={strategy.value}, file_path={file_path}, files_count={len(files)}"
            )

            # 3. 根据策略执行
            if strategy == TranscriptStrategy.COMPREHENSIVE:
                result = await self._comprehensive_transcript(
                    query_type, file_path, files, parameters
                )
            elif strategy == TranscriptStrategy.FAST:
                result = await self._fast_transcript(
                    query_type, file_path, files, parameters
                )
            elif strategy == TranscriptStrategy.PROFESSIONAL:
                result = await self._professional_transcript(
                    query_type, file_path, files, parameters
                )
            elif strategy == TranscriptStrategy.BATCH:
                result = await self._batch_transcript(
                    query_type, file_path, files, parameters
                )
            elif strategy == TranscriptStrategy.REDUNDANT:
                result = await self._redundant_transcript(
                    query_type, file_path, files, parameters
                )
            else:
                result = await self._comprehensive_transcript(
                    query_type, file_path, files, parameters
                )

            # 4. 计算总耗时
            processing_time = time.time() - start_time
            result.processing_time = processing_time

            # 5. 构造返回结果
            return {
                'markdown_content': result.markdown_content,
                'plain_text': result.plain_text,
                'images': result.images,
                'tables': result.tables,
                'metadata': result.metadata,
                'statistics': {
                    'page_count': result.page_count,
                    'word_count': result.word_count,
                    'image_count': result.image_count,
                    'table_count': result.table_count,
                },
                'source_plugins': result.source_plugins,
                'confidence_score': result.confidence_score,
                'processing_time': result.processing_time,
                'warnings': result.warnings,
                'errors': result.errors,
            }

        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            return {
                'error': str(e),
                'markdown_content': '',
                'confidence_score': 0.0,
                'processing_time': time.time() - start_time,
            }

    # ========================================================================
    # 策略实现
    # ========================================================================

    async def _comprehensive_transcript(
        self,
        query_type: TranscriptQueryType,
        file_path: str,
        files: List[str],
        parameters: Dict[str, Any]
    ) -> TranscriptResult:
        """
        综合策略：所有插件并行执行，智能合并结果

        优势：
        - 最全面的结果
        - 最高的准确性
        - 交叉验证

        适用场景：
        - 重要文档转换
        - 需要高准确性
        - 不在意处理时间
        """
        logger.info("Executing comprehensive transcript strategy")

        tasks = [
            self._execute_markitdown(query_type, file_path, files, parameters),
            self._execute_pdf_guru(query_type, file_path, files, parameters),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        merged_result = TranscriptResult()
        successful_count = 0

        for result in results:
            if isinstance(result, TranscriptResult):
                merged_result = merged_result.merge(result)
                successful_count += 1
            elif isinstance(result, Exception):
                logger.warning(f"Plugin execution failed: {result}")
                merged_result.errors.append(str(result))

        # 计算置信度
        merged_result.confidence_score = successful_count / len(tasks)

        logger.info(
            f"Comprehensive strategy completed: {successful_count}/{len(tasks)} plugins succeeded"
        )

        return merged_result

    async def _fast_transcript(
        self,
        query_type: TranscriptQueryType,
        file_path: str,
        files: List[str],
        parameters: Dict[str, Any]
    ) -> TranscriptResult:
        """
        快速策略：仅使用 markitdown（最快）

        优势：
        - 速度最快
        - 资源占用少
        - 支持多种格式

        适用场景：
        - 快速预览
        - 批量处理
        - 对质量要求不高
        """
        logger.info("Executing fast transcript strategy (markitdown only)")
        return await self._execute_markitdown(query_type, file_path, files, parameters)

    async def _professional_transcript(
        self,
        query_type: TranscriptQueryType,
        file_path: str,
        files: List[str],
        parameters: Dict[str, Any]
    ) -> TranscriptResult:
        """
        专业策略：仅使用 PDF-Guru（最高质量）

        优势：
        - 最高质量
        - PDF 专项优化
        - 精确提取

        适用场景：
        - PDF 文档
        - 需要高质量
        - 复杂格式保留
        """
        logger.info("Executing professional transcript strategy (PDF-Guru only)")
        return await self._execute_pdf_guru(query_type, file_path, files, parameters)

    async def _batch_transcript(
        self,
        query_type: TranscriptQueryType,
        file_path: str,
        files: List[str],
        parameters: Dict[str, Any]
    ) -> TranscriptResult:
        """
        批量策略：优先速度，失败则降级到质量

        执行顺序：
        1. 先尝试 markitdown（快速）
        2. 失败则 fallback 到 PDF-Guru（高质量）

        优势：
        - 平衡速度和质量
        - 自动降级
        - 批量场景优化
        """
        logger.info("Executing batch transcript strategy")

        # 先尝试快速
        result = await self._execute_markitdown(query_type, file_path, files, parameters)

        # 如果成功且有内容，直接返回
        if result.markdown_content or result.plain_text:
            logger.info("Batch strategy: markitdown succeeded")
            return result

        # 否则 fallback 到专业
        logger.info("Batch strategy: falling back to PDF-Guru")
        return await self._execute_pdf_guru(query_type, file_path, files, parameters)

    async def _redundant_transcript(
        self,
        query_type: TranscriptQueryType,
        file_path: str,
        files: List[str],
        parameters: Dict[str, Any]
    ) -> TranscriptResult:
        """
        冗余策略：多插件并行，交叉验证

        与 comprehensive 的区别：
        - comprehensive: 合并所有结果
        - redundant: 验证结果一致性，选择最可信的

        优势：
        - 最高可靠性
        - 错误检测
        - 质量保证
        """
        logger.info("Executing redundant transcript strategy")

        # 并行执行
        tasks = [
            self._execute_markitdown(query_type, file_path, files, parameters),
            self._execute_pdf_guru(query_type, file_path, files, parameters),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 提取成功的结果
        valid_results = [r for r in results if isinstance(r, TranscriptResult)]

        if not valid_results:
            logger.warning("Redundant strategy: all plugins failed")
            return TranscriptResult(
                errors=[str(r) for r in results if isinstance(r, Exception)]
            )

        # 选择内容最长的（通常意味着提取更完整）
        best_result = max(valid_results, key=lambda r: len(r.markdown_content))
        best_result.confidence_score = len(valid_results) / len(tasks)

        # 添加其他结果作为验证
        for result in valid_results:
            if result is not best_result:
                best_result.source_plugins.extend(result.source_plugins)

        logger.info(
            f"Redundant strategy completed: selected result from {best_result.source_plugins[0]}"
        )

        return best_result

    # ========================================================================
    # 插件执行方法
    # ========================================================================

    async def _execute_markitdown(
        self,
        query_type: TranscriptQueryType,
        file_path: str,
        files: List[str],
        parameters: Dict[str, Any]
    ) -> TranscriptResult:
        """
        执行 markitdown 插件

        Args:
            query_type: 查询类型
            file_path: 单个文件路径
            files: 多文件列表
            parameters: 额外参数

        Returns:
            转换结果
        """
        start_time = time.time()
        result = TranscriptResult()
        result.source_plugins.append('markitdown')

        try:
            logger.info(f"Executing markitdown: file_path={file_path}, files_count={len(files)}")

            # 模拟插件调用
            # 实际实现中会调用真实的 markitdown 插件

            if file_path:
                # 单文件处理
                result.markdown_content = f"# Converted by markitdown\n\nFile: {file_path}\n\nContent..."
                result.plain_text = "Plain text content..."
                result.page_count = 1
                result.word_count = 100
            elif files:
                # 多文件处理
                result.markdown_content = f"# Batch conversion by markitdown\n\n"
                for file in files:
                    result.markdown_content += f"## {file}\n\nContent...\n\n"
                result.page_count = len(files)
                result.word_count = 100 * len(files)

            result.metadata = {
                'converter': 'markitdown',
                'version': '1.0',
                'query_type': query_type.value,
            }

            result.confidence_score = 0.85
            result.processing_time = time.time() - start_time

            logger.info(f"markitdown execution succeeded: {len(result.markdown_content)} chars")

        except Exception as e:
            logger.error(f"markitdown execution failed: {e}", exc_info=True)
            result.errors.append(f"markitdown error: {str(e)}")
            result.confidence_score = 0.0

        return result

    async def _execute_pdf_guru(
        self,
        query_type: TranscriptQueryType,
        file_path: str,
        files: List[str],
        parameters: Dict[str, Any]
    ) -> TranscriptResult:
        """
        执行 PDF-Guru 插件

        Args:
            query_type: 查询类型
            file_path: 单个文件路径
            files: 多文件列表
            parameters: 额外参数

        Returns:
            转换结果
        """
        start_time = time.time()
        result = TranscriptResult()
        result.source_plugins.append('PDF-Guru')

        try:
            logger.info(f"Executing PDF-Guru: file_path={file_path}, files_count={len(files)}")

            # 模拟插件调用
            # 实际实现中会调用真实的 PDF-Guru 插件

            if file_path:
                # 单文件处理（专业级）
                result.markdown_content = f"# Professional PDF conversion\n\nFile: {file_path}\n\nDetailed content with formatting..."
                result.plain_text = "Plain text with high accuracy..."
                result.page_count = 5
                result.word_count = 500

                # 提取图片和表格
                result.images = [
                    {'image_id': 'img1', 'url': '/images/img1.png', 'caption': 'Figure 1'},
                    {'image_id': 'img2', 'url': '/images/img2.png', 'caption': 'Figure 2'},
                ]
                result.tables = [
                    {'table_id': 'tbl1', 'content': 'Table data...', 'rows': 5, 'cols': 3},
                ]
                result.image_count = 2
                result.table_count = 1
            elif files:
                # 多文件处理
                result.markdown_content = f"# Professional batch conversion\n\n"
                for file in files:
                    result.markdown_content += f"## {file}\n\nDetailed content...\n\n"
                result.page_count = len(files) * 5
                result.word_count = len(files) * 500
                result.image_count = len(files) * 2
                result.table_count = len(files)

            result.metadata = {
                'converter': 'PDF-Guru',
                'version': '2.0',
                'query_type': query_type.value,
                'quality': 'professional',
            }

            result.confidence_score = 0.95
            result.processing_time = time.time() - start_time

            logger.info(f"PDF-Guru execution succeeded: {len(result.markdown_content)} chars")

        except Exception as e:
            logger.error(f"PDF-Guru execution failed: {e}", exc_info=True)
            result.errors.append(f"PDF-Guru error: {str(e)}")
            result.confidence_score = 0.0

        return result

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return ['pdf', 'docx', 'pptx', 'xlsx', 'html', 'txt', 'md']

    def get_query_types(self) -> List[str]:
        """获取所有查询类型"""
        return [qt.value for qt in TranscriptQueryType]

    def get_strategies(self) -> List[str]:
        """获取所有策略"""
        return [s.value for s in TranscriptStrategy]

    def recommend_strategy(
        self,
        file_count: int,
        file_format: str,
        quality_priority: bool = False
    ) -> TranscriptStrategy:
        """
        推荐执行策略

        Args:
            file_count: 文件数量
            file_format: 文件格式
            quality_priority: 是否优先质量

        Returns:
            推荐的策略
        """
        # 批量处理
        if file_count > 10:
            return TranscriptStrategy.BATCH

        # PDF 文档且要求质量
        if file_format.lower() == 'pdf' and quality_priority:
            return TranscriptStrategy.PROFESSIONAL

        # 单文件快速处理
        if file_count == 1 and not quality_priority:
            return TranscriptStrategy.FAST

        # 默认综合策略
        return TranscriptStrategy.COMPREHENSIVE


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    'SuperTranscriptAgent',
    'TranscriptResult',
    'TranscriptStrategy',
    'TranscriptQueryType',
]
