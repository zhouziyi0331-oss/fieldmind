"""
IngestionAgent - 统一采集入口
负责接收文件、识别类型、调用对应插件、生成标准化元数据
"""

from typing import Dict, Any, Optional, BinaryIO
from datetime import datetime
from abc import ABC, abstractmethod

from app.core.logging import logger
from app.services.file_classifier import FileClassifier


class IngestionPlugin(ABC):
    """
    采集插件基类
    所有文件格式的采集插件必须继承此类
    """

    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> list:
        """支持的文件格式（扩展名列表）"""
        pass

    @abstractmethod
    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        采集文件内容

        Args:
            file_path: 文件路径
            metadata: 文件元数据

        Returns:
            Dict: 标准化输出
                {
                    "raw_text": str,              # 原始文本
                    "structured_metadata": dict,  # 结构化元数据
                    "content_type": str,          # 内容类型
                    "extraction_method": str,     # 提取方法
                    "confidence": float           # 提取置信度
                }
        """
        pass


class IngestionAgent:
    """
    统一采集代理
    职责：
    1. 接收上传的文件
    2. 识别文件类型
    3. 路由到对应的插件
    4. 生成标准化元数据
    5. 返回统一格式的数据
    """

    def __init__(self):
        self.plugins = {}
        self._register_plugins()

    def _register_plugins(self):
        """注册所有插件（18个）"""
        # 导入所有插件
        from app.plugins.ingestion.pdf_plugin import PDFPlugin
        from app.plugins.ingestion.docx_plugin import DOCXPlugin
        from app.plugins.ingestion.text_plugin import TextPlugin, MarkdownPlugin
        from app.plugins.ingestion.image_plugin import ImagePlugin
        from app.plugins.ingestion.audio_plugin import AudioPlugin
        from app.plugins.ingestion.video_plugin import VideoPlugin
        from app.plugins.ingestion.excel_plugin import ExcelPlugin, CSVPlugin
        from app.plugins.ingestion.ppt_plugin import PPTPlugin
        from app.plugins.ingestion.html_plugin import HTMLPlugin, RTFPlugin
        from app.plugins.ingestion.data_plugin import JSONPlugin, XMLPlugin
        from app.plugins.ingestion.archive_plugin import EPUBPlugin, ZIPPlugin
        from app.plugins.ingestion.email_plugin import EmailPlugin
        from app.plugins.ingestion.code_plugin import CodePlugin

        # 注册插件（18个）
        plugins_list = [
            # 文档类（5个）
            PDFPlugin(),
            DOCXPlugin(),
            PPTPlugin(),
            TextPlugin(),
            MarkdownPlugin(),

            # 网页/富文本（2个）
            HTMLPlugin(),
            RTFPlugin(),

            # 图片（1个）
            ImagePlugin(),

            # 音视频（2个）
            AudioPlugin(),
            VideoPlugin(),

            # 表格（2个）
            ExcelPlugin(),
            CSVPlugin(),

            # 数据格式（2个）
            JSONPlugin(),
            XMLPlugin(),

            # 电子书/压缩包（2个）
            EPUBPlugin(),
            ZIPPlugin(),

            # 邮件（1个）
            EmailPlugin(),

            # 代码（1个）
            CodePlugin(),
        ]

        for plugin in plugins_list:
            for fmt in plugin.supported_formats:
                self.plugins[fmt] = plugin

        logger.info(f"IngestionAgent: 已注册 {len(plugins_list)} 个插件，支持 {len(self.plugins)} 种格式")

    def ingest_file(
        self,
        file_path: str,
        filename: str,
        mime_type: str,
        file_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        采集文件（统一入口）

        Args:
            file_path: 文件路径
            filename: 文件名
            mime_type: MIME类型
            file_metadata: 文件元数据

        Returns:
            Dict: 标准化采集结果
                {
                    "file_id": str,
                    "filename": str,
                    "file_type": str,
                    "raw_text": str,
                    "structured_metadata": {
                        "total_words": int,
                        "total_sentences": int,
                        "language": str,
                        "duration": float,  # 音视频
                        "pages": int,       # 文档
                        ...
                    },
                    "extraction_info": {
                        "method": str,
                        "plugin": str,
                        "confidence": float,
                        "timestamp": datetime
                    }
                }
        """
        start_time = datetime.utcnow()

        logger.info(f"[IngestionAgent] 开始采集: {filename}")

        # 1. 文件分类
        classification = FileClassifier.classify(filename, mime_type)
        file_type = classification['type'].value
        file_extension = filename.split('.')[-1].lower()

        # 2. 选择插件
        plugin = self.plugins.get(file_extension)

        if not plugin:
            logger.warning(f"未找到插件: {file_extension}, 使用通用插件")
            plugin = self.plugins.get('txt')  # 降级到文本插件

        logger.info(f"使用插件: {plugin.plugin_name}")

        # 3. 调用插件采集
        try:
            plugin_result = plugin.ingest(
                file_path=file_path,
                metadata=file_metadata or {}
            )

            # 4. 构建标准化输出
            result = {
                "file_id": file_metadata.get('id') if file_metadata else None,
                "filename": filename,
                "file_type": file_type,
                "raw_text": plugin_result.get("raw_text", ""),
                "structured_metadata": plugin_result.get("structured_metadata", {}),
                "transcript": plugin_result.get("transcript"),
                "extraction_info": {
                    "method": plugin_result.get("extraction_method", "unknown"),
                    "plugin": plugin.plugin_name,
                    "confidence": plugin_result.get("confidence", 1.0),
                    "status": plugin_result.get(
                        "extraction_status",
                        "success" if plugin_result.get("raw_text") else "empty"
                    ),
                    "timestamp": start_time,
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                }
            }

            logger.info(
                f"[IngestionAgent] 采集完成: {filename}",
                text_length=len(result['raw_text']),
                plugin=plugin.plugin_name
            )

            return result

        except Exception as e:
            logger.error(f"[IngestionAgent] 采集失败: {e}", filename=filename)
            raise

    def get_supported_formats(self) -> Dict[str, str]:
        """获取所有支持的格式"""
        formats = {}
        for fmt, plugin in self.plugins.items():
            formats[fmt] = plugin.plugin_name
        return formats

    def list_plugins(self) -> list:
        """列出所有已注册的插件名称"""
        plugin_names = set()
        for plugin in self.plugins.values():
            plugin_names.add(plugin.plugin_name)
        return list(plugin_names)


# 全局实例
_ingestion_agent = None

def get_ingestion_agent() -> IngestionAgent:
    """获取全局 IngestionAgent 实例"""
    global _ingestion_agent
    if _ingestion_agent is None:
        _ingestion_agent = IngestionAgent()
    return _ingestion_agent
