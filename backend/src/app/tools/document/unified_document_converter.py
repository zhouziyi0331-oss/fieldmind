"""
统一文档转换器 (Unified Document Converter)

整合2个版本的文档转换器：
- DocumentConverter (MarkItDown) - 基础转换，87行
- UnstructuredConverter - 强大转换，284行，支持表格、OCR、结构识别

新增功能：
1. 多策略转换（Unstructured优先，MarkItDown降级，纯文本兜底）
2. 自动格式检测
3. 表格提取和保留
4. 结构识别（标题、段落、列表）
5. 错误重试机制
6. 批处理支持
7. 转换质量评分
8. 元数据增强

使用示例：
    converter = UnifiedDocumentConverter()

    # 基础转换
    result = converter.convert(file_path)
    print(result['text'])

    # 结构化转换
    result = converter.convert(file_path, preserve_structure=True)
    for element in result['elements']:
        print(f"[{element['type']}] {element['text']}")

    # 提取表格
    tables = converter.extract_tables(file_path)

    # 批处理
    results = converter.batch_convert([file1, file2, file3])
"""

import logging
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
from collections import Counter
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ConversionStrategy(Enum):
    """转换策略"""
    UNSTRUCTURED = "unstructured"  # Unstructured库（最强）
    MARKITDOWN = "markitdown"      # MarkItDown（中等）
    PLAINTEXT = "plaintext"        # 纯文本读取（兜底）


class ConversionQuality(Enum):
    """转换质量等级"""
    EXCELLENT = "excellent"  # 90-100分
    GOOD = "good"           # 70-89分
    FAIR = "fair"           # 50-69分
    POOR = "poor"           # <50分


@dataclass
class ConversionResult:
    """转换结果"""
    text: str                              # 提取的文本
    strategy_used: ConversionStrategy      # 使用的策略
    quality_score: float                   # 质量分数(0-100)
    quality_level: ConversionQuality       # 质量等级
    elements: Optional[List[Dict]] = None  # 结构化元素
    tables: Optional[List[str]] = None     # 提取的表格
    metadata: Optional[Dict] = None        # 元数据
    warnings: Optional[List[str]] = None   # 警告信息
    processing_time: float = 0.0           # 处理时间(秒)


class ConversionError(Exception):
    """转换错误"""
    pass


class UnifiedDocumentConverter:
    """
    统一文档转换器

    特性：
    - 多策略自动降级（Unstructured → MarkItDown → 纯文本）
    - 表格提取和保留
    - 结构识别（标题、段落、列表、表格）
    - 错误重试机制
    - 批处理支持
    - 质量评分
    """

    def __init__(
        self,
        preferred_strategy: ConversionStrategy = ConversionStrategy.UNSTRUCTURED,
        max_retries: int = 2,
        retry_delay: float = 0.5,
        enable_structure_detection: bool = True,
        enable_table_extraction: bool = True,
        min_text_length: int = 10
    ):
        """
        初始化转换器

        Args:
            preferred_strategy: 首选策略
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            enable_structure_detection: 是否启用结构检测
            enable_table_extraction: 是否启用表格提取
            min_text_length: 最小文本长度（用于质量评分）
        """
        self.preferred_strategy = preferred_strategy
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_structure_detection = enable_structure_detection
        self.enable_table_extraction = enable_table_extraction
        self.min_text_length = min_text_length

        # 检查可用的转换器
        self._available_strategies = self._detect_available_strategies()

        if not self._available_strategies:
            logger.warning("没有可用的转换器！将只能读取纯文本文件")

    def _detect_available_strategies(self) -> List[ConversionStrategy]:
        """检测可用的转换策略"""
        available = []

        # 检查 Unstructured
        try:
            import unstructured
            available.append(ConversionStrategy.UNSTRUCTURED)
            logger.info("✓ Unstructured 可用")
        except ImportError:
            logger.debug("Unstructured 未安装")

        # 检查 MarkItDown
        try:
            import markitdown
            available.append(ConversionStrategy.MARKITDOWN)
            logger.info("✓ MarkItDown 可用")
        except ImportError:
            logger.debug("MarkItDown 未安装")

        # 纯文本总是可用
        available.append(ConversionStrategy.PLAINTEXT)

        return available

    def convert(
        self,
        file_path: str,
        preserve_structure: bool = False,
        extract_tables: bool = None,
        strategy: Optional[ConversionStrategy] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> ConversionResult:
        """
        转换文档

        Args:
            file_path: 文件路径
            preserve_structure: 是否保留结构（返回结构化元素）
            extract_tables: 是否提取表格（None=自动）
            strategy: 强制使用的策略（None=自动选择）
            progress_callback: 进度回调 callback(message, progress)

        Returns:
            ConversionResult对象

        Raises:
            ConversionError: 所有策略都失败时
        """
        start_time = time.time()

        # 验证文件
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise ConversionError(f"文件不存在: {file_path}")

        if progress_callback:
            progress_callback("开始转换文档", 0.0)

        # 自动决定是否提取表格
        if extract_tables is None:
            extract_tables = self.enable_table_extraction

        # 确定转换策略优先级
        if strategy:
            strategies_to_try = [strategy]
        else:
            strategies_to_try = self._get_strategy_priority()

        # 依次尝试每个策略
        last_error = None
        for idx, strat in enumerate(strategies_to_try):
            if strat not in self._available_strategies:
                continue

            if progress_callback:
                progress_callback(f"尝试策略: {strat.value}", 0.2 + (idx * 0.3))

            try:
                logger.info(f"尝试使用策略: {strat.value}")
                result = self._convert_with_strategy(
                    file_path,
                    strat,
                    preserve_structure,
                    extract_tables
                )

                # 计算处理时间
                result.processing_time = time.time() - start_time

                if progress_callback:
                    progress_callback("转换完成", 1.0)

                logger.info(
                    f"✅ 转换成功: {strat.value}, "
                    f"质量={result.quality_score:.1f}, "
                    f"文本长度={len(result.text)}, "
                    f"耗时={result.processing_time:.2f}s"
                )

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"策略 {strat.value} 失败: {e}")

                # 如果不是最后一个策略，继续尝试
                if idx < len(strategies_to_try) - 1:
                    logger.info(f"降级到下一个策略...")
                    if self.retry_delay > 0:
                        time.sleep(self.retry_delay)

        # 所有策略都失败
        raise ConversionError(
            f"所有转换策略都失败了。最后错误: {last_error}"
        )

    def _get_strategy_priority(self) -> List[ConversionStrategy]:
        """获取策略优先级列表"""
        priority = []

        # 按照preferred_strategy优先
        if self.preferred_strategy in self._available_strategies:
            priority.append(self.preferred_strategy)

        # 添加其他可用策略
        for strat in [
            ConversionStrategy.UNSTRUCTURED,
            ConversionStrategy.MARKITDOWN,
            ConversionStrategy.PLAINTEXT
        ]:
            if strat not in priority and strat in self._available_strategies:
                priority.append(strat)

        return priority

    def _convert_with_strategy(
        self,
        file_path: str,
        strategy: ConversionStrategy,
        preserve_structure: bool,
        extract_tables: bool
    ) -> ConversionResult:
        """使用指定策略转换"""

        if strategy == ConversionStrategy.UNSTRUCTURED:
            return self._convert_with_unstructured(
                file_path, preserve_structure, extract_tables
            )
        elif strategy == ConversionStrategy.MARKITDOWN:
            return self._convert_with_markitdown(file_path)
        elif strategy == ConversionStrategy.PLAINTEXT:
            return self._convert_with_plaintext(file_path)
        else:
            raise ConversionError(f"未知策略: {strategy}")

    def _convert_with_unstructured(
        self,
        file_path: str,
        preserve_structure: bool,
        extract_tables: bool
    ) -> ConversionResult:
        """使用Unstructured转换"""
        from unstructured.partition.auto import partition

        # 解析文档
        elements = partition(filename=file_path)

        if not elements:
            raise ConversionError("Unstructured未提取到任何内容")

        # 提取文本
        if preserve_structure:
            text = "\n\n".join([
                str(elem).strip() for elem in elements
                if str(elem).strip()
            ])
        else:
            text = " ".join([
                str(elem).strip() for elem in elements
                if str(elem).strip()
            ])

        # 构建结构化元素列表
        structured_elements = None
        if self.enable_structure_detection:
            structured_elements = []
            for elem in elements:
                elem_dict = {
                    'type': type(elem).__name__,
                    'text': str(elem).strip()
                }

                # 提取元数据
                if hasattr(elem, 'metadata'):
                    meta = elem.metadata
                    if hasattr(meta, 'to_dict'):
                        elem_dict['metadata'] = meta.to_dict()
                    else:
                        elem_dict['metadata'] = {}
                else:
                    elem_dict['metadata'] = {}

                structured_elements.append(elem_dict)

        # 提取表格
        tables = None
        if extract_tables:
            tables = [
                str(elem) for elem in elements
                if type(elem).__name__ == 'Table'
            ]

        # 计算质量分数
        quality_score = self._calculate_quality_score(
            text, structured_elements, tables, strategy=ConversionStrategy.UNSTRUCTURED
        )

        # 生成元数据
        element_types = Counter([type(elem).__name__ for elem in elements])
        metadata = {
            'total_elements': len(elements),
            'element_types': dict(element_types),
            'has_tables': 'Table' in element_types,
            'has_images': 'Image' in element_types,
            'file_name': Path(file_path).name,
            'file_size': Path(file_path).stat().st_size
        }

        return ConversionResult(
            text=text,
            strategy_used=ConversionStrategy.UNSTRUCTURED,
            quality_score=quality_score,
            quality_level=self._score_to_quality_level(quality_score),
            elements=structured_elements,
            tables=tables,
            metadata=metadata,
            warnings=[]
        )

    def _convert_with_markitdown(self, file_path: str) -> ConversionResult:
        """使用MarkItDown转换"""
        from markitdown import MarkItDown

        converter = MarkItDown()
        result = converter.convert(str(file_path))

        text = result.text_content
        if not text or len(text) < self.min_text_length:
            raise ConversionError(f"提取的文本太短: {len(text)}字符")

        # 提取标题
        title = None
        if hasattr(result, 'title'):
            title = result.title
        else:
            title = Path(file_path).stem

        # 计算质量分数
        quality_score = self._calculate_quality_score(
            text, None, None, strategy=ConversionStrategy.MARKITDOWN
        )

        # 生成元数据
        metadata = {
            'title': title,
            'file_name': Path(file_path).name,
            'file_extension': Path(file_path).suffix,
            'file_size': Path(file_path).stat().st_size,
            'word_count': len(text.split())
        }

        warnings = ["MarkItDown不支持结构检测和表格提取"]

        return ConversionResult(
            text=text,
            strategy_used=ConversionStrategy.MARKITDOWN,
            quality_score=quality_score,
            quality_level=self._score_to_quality_level(quality_score),
            elements=None,
            tables=None,
            metadata=metadata,
            warnings=warnings
        )

    def _convert_with_plaintext(self, file_path: str) -> ConversionResult:
        """纯文本读取（兜底方案）"""

        # 尝试多种编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        text = None
        used_encoding = None

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                used_encoding = encoding
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if text is None:
            raise ConversionError("无法用任何编码读取文件")

        if len(text) < self.min_text_length:
            raise ConversionError(f"文件内容太少: {len(text)}字符")

        # 计算质量分数
        quality_score = self._calculate_quality_score(
            text, None, None, strategy=ConversionStrategy.PLAINTEXT
        )

        # 生成元数据
        metadata = {
            'file_name': Path(file_path).name,
            'file_size': Path(file_path).stat().st_size,
            'encoding': used_encoding,
            'word_count': len(text.split())
        }

        warnings = [
            "使用纯文本读取，可能丢失格式信息",
            "不支持二进制文件格式(PDF, DOCX等)"
        ]

        return ConversionResult(
            text=text,
            strategy_used=ConversionStrategy.PLAINTEXT,
            quality_score=quality_score,
            quality_level=self._score_to_quality_level(quality_score),
            elements=None,
            tables=None,
            metadata=metadata,
            warnings=warnings
        )

    def _calculate_quality_score(
        self,
        text: str,
        elements: Optional[List[Dict]],
        tables: Optional[List[str]],
        strategy: ConversionStrategy
    ) -> float:
        """
        计算转换质量分数(0-100)

        评分因素：
        - 文本长度 (30分)
        - 结构丰富度 (30分)
        - 表格提取 (20分)
        - 策略能力 (20分)
        """
        score = 0.0

        # 1. 文本长度评分 (30分)
        text_len = len(text)
        if text_len >= 1000:
            score += 30
        elif text_len >= 500:
            score += 25
        elif text_len >= 100:
            score += 20
        elif text_len >= self.min_text_length:
            score += 10

        # 2. 结构丰富度评分 (30分)
        if elements:
            element_types = set(e['type'] for e in elements)
            type_count = len(element_types)

            if type_count >= 5:
                score += 30
            elif type_count >= 3:
                score += 25
            elif type_count >= 2:
                score += 20
            else:
                score += 10
        else:
            # 没有结构信息，基于文本特征估计
            if '\n\n' in text:
                score += 15  # 有段落分隔
            if any(marker in text for marker in ['#', '##', '###']):
                score += 10  # 可能有标题

        # 3. 表格提取评分 (20分)
        if tables:
            table_count = len(tables)
            if table_count >= 3:
                score += 20
            elif table_count >= 1:
                score += 15
        elif elements:
            # 检查元素中是否有Table类型
            has_table_type = any(e['type'] == 'Table' for e in elements)
            if has_table_type:
                score += 10

        # 4. 策略能力评分 (20分)
        strategy_scores = {
            ConversionStrategy.UNSTRUCTURED: 20,
            ConversionStrategy.MARKITDOWN: 15,
            ConversionStrategy.PLAINTEXT: 5
        }
        score += strategy_scores.get(strategy, 0)

        return min(score, 100.0)

    def _score_to_quality_level(self, score: float) -> ConversionQuality:
        """分数转质量等级"""
        if score >= 90:
            return ConversionQuality.EXCELLENT
        elif score >= 70:
            return ConversionQuality.GOOD
        elif score >= 50:
            return ConversionQuality.FAIR
        else:
            return ConversionQuality.POOR

    def extract_tables(self, file_path: str) -> List[str]:
        """
        提取文档中的所有表格

        Args:
            file_path: 文件路径

        Returns:
            表格文本列表
        """
        try:
            result = self.convert(
                file_path,
                preserve_structure=False,
                extract_tables=True
            )
            return result.tables or []
        except Exception as e:
            logger.error(f"表格提取失败: {e}")
            return []

    def get_document_summary(self, file_path: str) -> Dict[str, Any]:
        """
        获取文档摘要

        Returns:
            {
                'text_length': 5000,
                'word_count': 1000,
                'element_count': 20,
                'element_types': {'Title': 2, 'NarrativeText': 15},
                'table_count': 3,
                'quality_score': 85.5,
                'quality_level': 'good',
                'strategy_used': 'unstructured'
            }
        """
        try:
            result = self.convert(
                file_path,
                preserve_structure=True,
                extract_tables=True
            )

            summary = {
                'text_length': len(result.text),
                'word_count': len(result.text.split()),
                'quality_score': result.quality_score,
                'quality_level': result.quality_level.value,
                'strategy_used': result.strategy_used.value
            }

            if result.elements:
                element_types = Counter(e['type'] for e in result.elements)
                summary['element_count'] = len(result.elements)
                summary['element_types'] = dict(element_types)

            if result.tables:
                summary['table_count'] = len(result.tables)

            if result.metadata:
                summary['file_metadata'] = result.metadata

            return summary

        except Exception as e:
            logger.error(f"获取文档摘要失败: {e}")
            return {}

    def batch_convert(
        self,
        file_paths: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[ConversionResult]:
        """
        批量转换文档

        Args:
            file_paths: 文件路径列表
            progress_callback: 进度回调 callback(current, total, message)

        Returns:
            转换结果列表
        """
        results = []
        total = len(file_paths)

        for idx, file_path in enumerate(file_paths, 1):
            try:
                if progress_callback:
                    progress_callback(idx, total, f"转换: {Path(file_path).name}")

                result = self.convert(file_path)
                results.append(result)

                logger.info(
                    f"[{idx}/{total}] ✅ {Path(file_path).name} - "
                    f"{result.strategy_used.value}, "
                    f"质量={result.quality_score:.1f}"
                )

            except Exception as e:
                logger.error(f"[{idx}/{total}] ❌ {Path(file_path).name}: {e}")
                # 添加失败结果
                results.append(ConversionResult(
                    text="",
                    strategy_used=ConversionStrategy.PLAINTEXT,
                    quality_score=0.0,
                    quality_level=ConversionQuality.POOR,
                    warnings=[f"转换失败: {str(e)}"]
                ))

        return results

    def is_supported(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        extension = Path(file_path).suffix.lower()

        # Unstructured支持的格式
        unstructured_formats = {
            '.pdf', '.docx', '.doc', '.pptx', '.ppt',
            '.xlsx', '.xls', '.html', '.htm', '.xml',
            '.txt', '.md', '.csv', '.json', '.rtf',
            '.odt', '.epub', '.msg', '.eml'
        }

        # MarkItDown支持的格式
        markitdown_formats = {
            '.pdf', '.docx', '.pptx', '.xlsx',
            '.html', '.txt', '.md', '.csv', '.json'
        }

        # 纯文本格式
        plaintext_formats = {'.txt', '.md', '.csv', '.json', '.xml', '.log'}

        if ConversionStrategy.UNSTRUCTURED in self._available_strategies:
            return extension in unstructured_formats
        elif ConversionStrategy.MARKITDOWN in self._available_strategies:
            return extension in markitdown_formats
        else:
            return extension in plaintext_formats


# 便捷函数

def create_converter(**kwargs) -> UnifiedDocumentConverter:
    """创建转换器实例"""
    return UnifiedDocumentConverter(**kwargs)


def convert_document(file_path: str, **kwargs) -> ConversionResult:
    """快速转换单个文档"""
    converter = UnifiedDocumentConverter()
    return converter.convert(file_path, **kwargs)


def batch_convert_documents(file_paths: List[str], **kwargs) -> List[ConversionResult]:
    """快速批量转换"""
    converter = UnifiedDocumentConverter()
    return converter.batch_convert(file_paths, **kwargs)
