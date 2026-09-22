"""
插件系统集成层

目标：让规范化规则调用插件系统获取基础信息，然后添加AI增强

架构：
- 插件系统：基础文件解析（14个插件）
- 规范化层：AI增强 + 质量验证（5个规则）
- 集成层：连接两者，形成完整处理流程

处理流程：
上传文件 → 插件解析基础信息 → 规范化AI增强 → 输出完整文档
"""

from typing import Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PluginIntegrationService:
    """插件集成服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.plugin_manager = None
        self._init_plugin_manager()

    def _init_plugin_manager(self):
        """初始化插件管理器"""
        try:
            from app.core.plugin_manager import PluginManager
            self.plugin_manager = PluginManager()
            logger.info(f"✅ 插件管理器初始化成功，已加载 {len(self.plugin_manager.plugins)} 个插件")
        except Exception as e:
            logger.error(f"插件管理器初始化失败: {e}")
            self.plugin_manager = None

    def get_plugin_basic_info(
        self,
        file_path: str,
        file_content: bytes,
        file_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        调用插件获取文件基础信息

        Args:
            file_path: 文件路径
            file_content: 文件内容
            file_type: 文件类型（扩展名，如 mp3, pdf, jpg）

        Returns:
            插件返回的基础信息，如果失败返回 None
        """
        if not self.plugin_manager:
            logger.warning("插件管理器未初始化，跳过插件调用")
            return None

        try:
            # 根据文件类型查找对应的插件
            plugin = self._find_plugin_for_type(file_type)
            if not plugin:
                logger.warning(f"未找到处理 {file_type} 类型的插件")
                return None

            logger.info(f"调用插件: {plugin.__class__.__name__} 处理 {file_type} 文件")

            # 保存临时文件（插件需要文件路径）
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix=f'.{file_type}', delete=False) as f:
                f.write(file_content)
                temp_path = f.name

            # 调用插件处理
            result = plugin.process(temp_path)

            # 清理临时文件
            os.unlink(temp_path)

            logger.info(f"✅ 插件处理完成: {plugin.__class__.__name__}")
            return result

        except Exception as e:
            logger.error(f"插件调用失败: {e}", exc_info=True)
            return None

    def _find_plugin_for_type(self, file_type: str):
        """根据文件类型查找插件"""
        if not self.plugin_manager:
            return None

        file_type_lower = file_type.lower()

        # 遍历所有插件，找到支持该类型的插件
        for plugin in self.plugin_manager.plugins.values():
            if hasattr(plugin, 'supported_formats'):
                if file_type_lower in plugin.supported_formats:
                    return plugin

        return None

    def extract_metadata_from_plugin_result(
        self,
        plugin_result: Optional[Dict[str, Any]],
        file_type: str
    ) -> Dict[str, Any]:
        """
        从插件结果中提取元数据

        Args:
            plugin_result: 插件返回的结果
            file_type: 文件类型

        Returns:
            标准化的元数据字典
        """
        if not plugin_result:
            return {}

        metadata = {}

        try:
            # 音频文件元数据
            if file_type in ['mp3', 'wav', 'm4a', 'flac', 'ogg']:
                metadata['duration'] = plugin_result.get('duration', 0)
                metadata['sample_rate'] = plugin_result.get('sample_rate', 0)
                metadata['channels'] = plugin_result.get('channels', 0)
                metadata['bitrate'] = plugin_result.get('bitrate', 0)

            # 视频文件元数据
            elif file_type in ['mp4', 'avi', 'mov', 'mkv']:
                metadata['duration'] = plugin_result.get('duration', 0)
                metadata['resolution'] = plugin_result.get('resolution', {})
                metadata['fps'] = plugin_result.get('fps', 0)
                metadata['codec'] = plugin_result.get('codec', '')

            # 图片文件元数据
            elif file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                metadata['width'] = plugin_result.get('width', 0)
                metadata['height'] = plugin_result.get('height', 0)
                metadata['format'] = plugin_result.get('format', '')
                metadata['mode'] = plugin_result.get('mode', '')
                metadata['size'] = plugin_result.get('size', 0)

            # PDF文件元数据
            elif file_type == 'pdf':
                metadata['page_count'] = plugin_result.get('page_count', 0)
                metadata['author'] = plugin_result.get('author', '')
                metadata['title'] = plugin_result.get('title', '')

            # Word文件元数据
            elif file_type in ['docx', 'doc']:
                metadata['page_count'] = plugin_result.get('page_count', 0)
                metadata['paragraph_count'] = plugin_result.get('paragraph_count', 0)
                metadata['word_count'] = plugin_result.get('word_count', 0)

            # Excel文件元数据
            elif file_type in ['xlsx', 'xls', 'csv']:
                metadata['sheet_count'] = plugin_result.get('sheet_count', 0)
                metadata['row_count'] = plugin_result.get('row_count', 0)
                metadata['column_count'] = plugin_result.get('column_count', 0)

            # 通用元数据
            metadata['plugin_result'] = plugin_result
            metadata['extraction_method'] = 'plugin'

            logger.info(f"✅ 从插件结果提取元数据: {len(metadata)} 个字段")

        except Exception as e:
            logger.error(f"提取元数据失败: {e}")

        return metadata

    def extract_basic_content_from_plugin_result(
        self,
        plugin_result: Optional[Dict[str, Any]],
        file_type: str
    ) -> str:
        """
        从插件结果中提取基础文本内容

        Args:
            plugin_result: 插件返回的结果
            file_type: 文件类型

        Returns:
            基础文本内容
        """
        if not plugin_result:
            return ""

        try:
            # 音频：转录文本
            if file_type in ['mp3', 'wav', 'm4a', 'flac', 'ogg']:
                transcript = plugin_result.get('transcript', '')
                if transcript:
                    return transcript
                return ""

            # 视频：基础信息描述
            elif file_type in ['mp4', 'avi', 'mov', 'mkv']:
                duration = plugin_result.get('duration', 0)
                resolution = plugin_result.get('resolution', {})
                width = resolution.get('width', 0)
                height = resolution.get('height', 0)
                return f"视频文件：时长 {duration:.1f}秒，分辨率 {width}x{height}"

            # 图片：EXIF信息
            elif file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                exif = plugin_result.get('exif', {})
                if exif:
                    exif_text = "\n".join([f"{k}: {v}" for k, v in exif.items()])
                    return f"图片EXIF信息:\n{exif_text}"
                return ""

            # PDF/Word：提取的文本
            elif file_type in ['pdf', 'docx', 'doc']:
                text = plugin_result.get('text', '')
                return text

            # Excel：表格数据
            elif file_type in ['xlsx', 'xls', 'csv']:
                sheets = plugin_result.get('sheets', [])
                if sheets:
                    # 简单转换为文本
                    text = ""
                    for sheet in sheets:
                        text += f"## {sheet.get('name', 'Sheet')}\n\n"
                        rows = sheet.get('rows', [])
                        for row in rows[:10]:  # 只取前10行
                            text += " | ".join([str(cell) for cell in row]) + "\n"
                    return text
                return ""

            return ""

        except Exception as e:
            logger.error(f"提取基础内容失败: {e}")
            return ""


# 全局单例
_plugin_integration_service = None


def get_plugin_integration_service() -> PluginIntegrationService:
    """获取插件集成服务单例"""
    global _plugin_integration_service
    if _plugin_integration_service is None:
        _plugin_integration_service = PluginIntegrationService()
    return _plugin_integration_service
