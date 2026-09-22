"""
统一插件管理器

管理所有文件处理插件的注册、发现和执行
"""
from typing import Dict, Optional, List, Any, Type
from pathlib import Path
import importlib
import inspect
from abc import ABC, abstractmethod

from app.core.logging import logger


class BasePlugin(ABC):
    """插件基类"""

    plugin_name: str = "base"
    supported_extensions: List[str] = []

    @abstractmethod
    def process(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        处理文件

        Args:
            file_path: 文件路径
            **kwargs: 额外参数

        Returns:
            处理结果
        """
        pass

    @abstractmethod
    def validate(self, file_path: str) -> bool:
        """
        验证文件是否可以被此插件处理

        Args:
            file_path: 文件路径

        Returns:
            是否可以处理
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """获取插件元数据"""
        return {
            "name": self.plugin_name,
            "supported_extensions": self.supported_extensions,
            "description": self.__doc__ or "No description"
        }


class PluginManager:
    """统一插件管理器"""

    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.extension_map: Dict[str, str] = {}  # 扩展名 -> 插件名映射
        self._initialized = False

    def initialize(self):
        """初始化插件管理器"""
        if self._initialized:
            return

        logger.info("开始初始化插件管理器...")
        self.discover_plugins()
        self._initialized = True
        logger.info(f"插件管理器初始化完成，已加载 {len(self.plugins)} 个插件")

    def discover_plugins(self):
        """自动发现并加载所有插件"""
        from app.plugins.ingestion import (
            archive_plugin,
            audio_plugin,
            code_plugin,
            data_plugin,
            docx_plugin,
            email_plugin,
            excel_plugin,
            html_plugin,
            image_plugin,
            pdf_plugin,
            ppt_plugin,
            text_plugin,
            video_plugin
        )

        # 所有插件模块
        plugin_modules = [
            archive_plugin,
            audio_plugin,
            code_plugin,
            data_plugin,
            docx_plugin,
            email_plugin,
            excel_plugin,
            html_plugin,
            image_plugin,
            pdf_plugin,
            ppt_plugin,
            text_plugin,
            video_plugin
        ]

        # 自动注册插件
        for module in plugin_modules:
            # 查找模块中的插件类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BasePlugin) and
                    obj != BasePlugin):

                    try:
                        plugin_instance = obj()
                        self.register_plugin(plugin_instance)
                        logger.info(f"已注册插件: {plugin_instance.plugin_name}")
                    except Exception as e:
                        logger.error(f"注册插件失败 {name}: {e}")

    def register_plugin(self, plugin: BasePlugin):
        """
        注册插件

        Args:
            plugin: 插件实例
        """
        plugin_name = plugin.plugin_name

        if plugin_name in self.plugins:
            logger.warning(f"插件 {plugin_name} 已存在，将被覆盖")

        self.plugins[plugin_name] = plugin

        # 注册扩展名映射
        for ext in plugin.supported_extensions:
            ext_lower = ext.lower()
            if ext_lower in self.extension_map:
                logger.warning(f"扩展名 {ext} 已被插件 {self.extension_map[ext_lower]} 处理，"
                             f"现在将被 {plugin_name} 覆盖")
            self.extension_map[ext_lower] = plugin_name

        logger.debug(f"插件 {plugin_name} 注册成功，支持扩展名: {plugin.supported_extensions}")

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        根据名称获取插件

        Args:
            plugin_name: 插件名称

        Returns:
            插件实例
        """
        return self.plugins.get(plugin_name)

    def get_plugin_by_extension(self, extension: str) -> Optional[BasePlugin]:
        """
        根据文件扩展名获取插件

        Args:
            extension: 文件扩展名（如 .pdf）

        Returns:
            插件实例
        """
        ext_lower = extension.lower().lstrip('.')
        plugin_name = self.extension_map.get(ext_lower)

        if plugin_name:
            return self.plugins.get(plugin_name)

        return None

    def get_plugin_by_file(self, file_path: str) -> Optional[BasePlugin]:
        """
        根据文件路径自动选择插件

        Args:
            file_path: 文件路径

        Returns:
            插件实例
        """
        path = Path(file_path)
        extension = path.suffix

        return self.get_plugin_by_extension(extension)

    def process_file(
        self,
        file_path: str,
        plugin_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        处理文件

        Args:
            file_path: 文件路径
            plugin_name: 指定插件名称（可选，不指定则自动选择）
            **kwargs: 传递给插件的额外参数

        Returns:
            处理结果
        """
        if not self._initialized:
            self.initialize()

        # 选择插件
        if plugin_name:
            plugin = self.get_plugin(plugin_name)
            if not plugin:
                raise ValueError(f"插件 {plugin_name} 不存在")
        else:
            plugin = self.get_plugin_by_file(file_path)
            if not plugin:
                raise ValueError(f"没有找到可以处理文件 {file_path} 的插件")

        # 验证文件
        if not plugin.validate(file_path):
            raise ValueError(f"文件 {file_path} 无法被插件 {plugin.plugin_name} 处理")

        # 执行处理
        logger.info(f"使用插件 {plugin.plugin_name} 处理文件: {file_path}")

        try:
            result = plugin.process(file_path, **kwargs)
            result["plugin_used"] = plugin.plugin_name
            result["success"] = True
            return result
        except Exception as e:
            logger.error(f"插件 {plugin.plugin_name} 处理文件失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "plugin_used": plugin.plugin_name
            }

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的插件

        Returns:
            插件列表
        """
        if not self._initialized:
            self.initialize()

        return [plugin.get_metadata() for plugin in self.plugins.values()]

    def get_supported_extensions(self) -> List[str]:
        """
        获取所有支持的文件扩展名

        Returns:
            扩展名列表
        """
        if not self._initialized:
            self.initialize()

        return list(self.extension_map.keys())


# 全局插件管理器实例
plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """获取插件管理器实例"""
    if not plugin_manager._initialized:
        plugin_manager.initialize()
    return plugin_manager
