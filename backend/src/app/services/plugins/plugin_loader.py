"""
Plugin Loader - 插件动态加载器

负责动态加载和管理插件模块，支持多种加载策略。

设计理念:
1. 动态加载 - 使用importlib动态导入Python模块
2. 隔离加载 - 每个插件在独立的命名空间中
3. 延迟加载 - 只在需要时加载，节省内存
4. 缓存管理 - 已加载模块缓存，避免重复加载
5. 错误恢复 - 加载失败时提供降级方案
"""

import os
import sys
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .plugin_interface import (
    PluginInterface,
    PluginLoadError,
    PluginNotFoundError
)
from .plugin_registry import (
    PluginRegistry,
    PluginMetadata,
    get_plugin_registry
)

logger = logging.getLogger(__name__)


class LoadStrategy(Enum):
    """加载策略"""
    EAGER = "eager"           # 立即加载
    LAZY = "lazy"             # 延迟加载
    ON_DEMAND = "on_demand"   # 按需加载


@dataclass
class LoadedPlugin:
    """已加载的插件信息"""
    plugin_id: str
    capability_id: str
    module: Any                                    # 加载的模块对象
    adapter: Optional[PluginInterface] = None      # 插件适配器
    load_time: datetime = field(default_factory=datetime.now)
    access_count: int = 0                          # 访问次数
    last_access: Optional[datetime] = None         # 最后访问时间
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginLoader:
    """
    插件动态加载器

    职责:
    1. 动态加载Python插件模块
    2. 管理已加载插件的缓存
    3. 提供插件的查找和实例化
    4. 处理加载错误和重试
    """

    def __init__(self,
        registry: Optional[PluginRegistry] = None,
        strategy: LoadStrategy = LoadStrategy.LAZY,


        use_workflow_engine: bool = True):
        """
        初始化加载器

        Args:
            registry: 插件注册表（可选，默认使用全局注册表）
            strategy: 加载策略
        """
        self.registry = registry or get_plugin_registry()
        self.strategy = strategy
        self._loaded_plugins: Dict[str, LoadedPlugin] = {}  # plugin_id -> LoadedPlugin
        self._capability_to_plugin: Dict[str, str] = {}     # capability_id -> plugin_id
        self._adapter_factories: Dict[str, Callable] = {}   # plugin_id -> adapter_factory

        logger.info(f"PluginLoader initialized with strategy: {strategy.value}")

    # ==================== 加载管理 ====================

    def load_plugin(
        self,
        plugin_id: str,
        capability_id: Optional[str] = None,
        force_reload: bool = False
    ) -> LoadedPlugin:
        """
        加载插件

        Args:
            plugin_id: 插件ID
            capability_id: 能力ID（可选，用于多能力插件）
            force_reload: 是否强制重新加载

        Returns:
            LoadedPlugin实例

        Raises:
            PluginNotFoundError: 插件不存在
            PluginLoadError: 加载失败
        """
        # 检查是否已加载
        if plugin_id in self._loaded_plugins and not force_reload:
            loaded = self._loaded_plugins[plugin_id]
            loaded.access_count += 1
            loaded.last_access = datetime.now()
            logger.debug(f"Plugin {plugin_id} already loaded, access_count: {loaded.access_count}")
            return loaded

        # 从注册表获取元数据
        metadata = self.registry.get_plugin(plugin_id)
        if not metadata:
            raise PluginNotFoundError(f"Plugin not found: {plugin_id}")

        # 确定能力ID
        if capability_id is None:
            if len(metadata.capabilities) > 0:
                capability_id = metadata.capabilities[0].capability_id
            else:
                raise PluginLoadError(f"Plugin {plugin_id} has no capabilities defined")

        logger.info(f"Loading plugin: {plugin_id} for capability: {capability_id}")

        try:
            # 加载模块
            module = self._load_module(metadata)

            # 创建LoadedPlugin对象
            loaded_plugin = LoadedPlugin(
                plugin_id=plugin_id,
                capability_id=capability_id,
                module=module,
                metadata={
                    "plugin_type": metadata.plugin_type.value,
                    "version": metadata.version,
                    "repo_path": metadata.repo_path
                }
            )

            # 缓存
            self._loaded_plugins[plugin_id] = loaded_plugin
            self._capability_to_plugin[capability_id] = plugin_id

            logger.info(f"Plugin {plugin_id} loaded successfully")
            return loaded_plugin

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            raise PluginLoadError(f"Failed to load plugin {plugin_id}: {e}")

    def unload_plugin(self, plugin_id: str) -> bool:
        """
        卸载插件

        Args:
            plugin_id: 插件ID

        Returns:
            是否卸载成功
        """
        if plugin_id not in self._loaded_plugins:
            logger.warning(f"Plugin {plugin_id} not loaded, cannot unload")
            return False

        try:
            loaded = self._loaded_plugins[plugin_id]

            # 卸载适配器
            if loaded.adapter and hasattr(loaded.adapter, 'unload'):
                loaded.adapter.unload()

            # 从缓存中移除
            del self._loaded_plugins[plugin_id]

            # 从能力映射中移除
            if loaded.capability_id in self._capability_to_plugin:
                del self._capability_to_plugin[loaded.capability_id]

            logger.info(f"Plugin {plugin_id} unloaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False

    def load_by_capability(
        self,
        capability_id: str,
        prefer_plugin_id: Optional[str] = None
    ) -> LoadedPlugin:
        """
        根据能力加载插件

        Args:
            capability_id: 能力ID
            prefer_plugin_id: 首选插件ID（可选）

        Returns:
            LoadedPlugin实例

        Raises:
            PluginNotFoundError: 没有插件提供该能力
            PluginLoadError: 加载失败
        """
        # 查询提供该能力的插件（按优先级排序）
        providers = self.registry.get_plugins_by_capability(capability_id)

        if not providers:
            raise PluginNotFoundError(f"No plugin provides capability: {capability_id}")

        # 如果指定了首选插件，尝试使用它
        if prefer_plugin_id:
            prefer_metadata = next(
                (p for p in providers if p.plugin_id == prefer_plugin_id),
                None
            )
            if prefer_metadata:
                providers.insert(0, providers.pop(providers.index(prefer_metadata)))

        # 尝试加载插件（按优先级顺序）
        last_error = None
        for metadata in providers:
            try:
                return self.load_plugin(metadata.plugin_id, capability_id)
            except Exception as e:
                logger.warning(f"Failed to load {metadata.plugin_id} for {capability_id}: {e}")
                last_error = e
                continue

        # 所有插件都加载失败
        raise PluginLoadError(
            f"Failed to load any plugin for capability {capability_id}. "
            f"Last error: {last_error}"
        )

    def _load_module(self, metadata: PluginMetadata) -> Any:
        """
        动态加载Python模块

        Args:
            metadata: 插件元数据

        Returns:
            加载的模块对象

        Raises:
            PluginLoadError: 加载失败
        """
        plugin_id = metadata.plugin_id
        repo_path = Path(metadata.repo_path)

        # 检查路径是否存在
        if not repo_path.exists():
            raise PluginLoadError(f"Plugin path does not exist: {repo_path}")

        # 尝试查找可导入的Python包或模块
        module_paths = self._find_python_modules(repo_path)

        if not module_paths:
            raise PluginLoadError(
                f"插件{plugin_id}的路径{repo_path}中未找到任何Python模块。"
                f"请检查插件是否包含有效的Python代码。"
            )

        # 尝试加载第一个找到的模块
        errors = []
        for module_path in module_paths[:3]:  # 只尝试前3个
            try:
                return self._import_module(plugin_id, module_path)
            except Exception as e:
                logger.debug(f"Failed to import {module_path}: {e}")
                errors.append(f"{module_path}: {str(e)}")
                continue

        # 所有尝试都失败，抛出异常
        error_details = "\n".join(errors)
        raise PluginLoadError(
            f"插件{plugin_id}的所有导入尝试均失败。\n"
            f"尝试的路径和错误：\n{error_details}"
        )

    def _find_python_modules(self, repo_path: Path) -> List[Path]:
        """
        查找仓库中的Python模块

        Args:
            repo_path: 仓库路径

        Returns:
            可能的模块路径列表
        """
        candidates = []

        # 1. 查找 __init__.py（包）
        init_files = list(repo_path.rglob('__init__.py'))
        for init_file in init_files[:5]:  # 限制数量
            if 'test' not in str(init_file).lower():
                candidates.append(init_file.parent)

        # 2. 查找 setup.py 同级的包名
        setup_py = repo_path / 'setup.py'
        if setup_py.exists():
            # 常见的包名是 src/<package_name> 或直接 <package_name>
            for subdir in ['src', repo_path.name]:
                package_dir = repo_path / subdir
                if package_dir.exists() and package_dir.is_dir():
                    candidates.append(package_dir)

        # 3. 查找 pyproject.toml 中的包
        pyproject = repo_path / 'pyproject.toml'
        if pyproject.exists():
            # 简单启发式：查找 src/ 或与仓库同名的目录
            src_dir = repo_path / 'src'
            if src_dir.exists():
                candidates.append(src_dir)

        # 4. 直接使用仓库根目录
        candidates.append(repo_path)

        return candidates

    def _import_module(self, plugin_id: str, module_path: Path) -> Any:
        """
        导入Python模块

        Args:
            plugin_id: 插件ID
            module_path: 模块路径

        Returns:
            导入的模块

        Raises:
            ImportError: 导入失败
        """
        # 添加到sys.path（如果还没有）
        parent_path = str(module_path.parent)
        if parent_path not in sys.path:
            sys.path.insert(0, parent_path)

        try:
            # 如果是包（有__init__.py）
            if (module_path / '__init__.py').exists():
                module_name = module_path.name
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    module_path / '__init__.py'
                )
            else:
                # 如果是单个模块
                module_name = plugin_id
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    module_path
                )

            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot create module spec for {module_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            return module

        except Exception as e:
            # 从sys.path移除
            if parent_path in sys.path:
                sys.path.remove(parent_path)
            raise ImportError(f"Failed to import {module_path}: {e}")

    # ==================== 查询接口 ====================

    def get_loaded_plugin(self, plugin_id: str) -> Optional[LoadedPlugin]:
        """获取已加载的插件"""
        return self._loaded_plugins.get(plugin_id)

    def get_plugin_by_capability(self, capability_id: str) -> Optional[LoadedPlugin]:
        """根据能力获取已加载的插件"""
        plugin_id = self._capability_to_plugin.get(capability_id)
        if plugin_id:
            return self._loaded_plugins.get(plugin_id)
        return None

    def is_loaded(self, plugin_id: str) -> bool:
        """检查插件是否已加载"""
        return plugin_id in self._loaded_plugins

    def get_all_loaded(self) -> Dict[str, LoadedPlugin]:
        """获取所有已加载的插件"""
        return self._loaded_plugins.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """获取加载器统计信息"""
        return {
            "total_loaded": len(self._loaded_plugins),
            "capabilities_mapped": len(self._capability_to_plugin),
            "strategy": self.strategy.value,
            "plugins": [
                {
                    "plugin_id": loaded.plugin_id,
                    "capability_id": loaded.capability_id,
                    "access_count": loaded.access_count,
                    "load_time": loaded.load_time.isoformat(),
                    "last_access": loaded.last_access.isoformat() if loaded.last_access else None
                }
                for loaded in self._loaded_plugins.values()
            ]
        }

    # ==================== 适配器管理 ====================

    def register_adapter_factory(
        self,
        plugin_id: str,
        factory: Callable[[str, str], PluginInterface]
    ):
        """
        注册适配器工厂函数

        Args:
            plugin_id: 插件ID
            factory: 工厂函数，接收(plugin_id, capability_id)，返回PluginInterface
        """
        self._adapter_factories[plugin_id] = factory
        logger.debug(f"Registered adapter factory for {plugin_id}")

    def create_adapter(
        self,
        plugin_id: str,
        capability_id: str
    ) -> Optional[PluginInterface]:
        """
        创建插件适配器

        Args:
            plugin_id: 插件ID
            capability_id: 能力ID

        Returns:
            PluginInterface实例，如果没有注册工厂则返回None
        """
        factory = self._adapter_factories.get(plugin_id)
        if factory:
            try:
                adapter = factory(plugin_id, capability_id)
                logger.debug(f"Created adapter for {plugin_id}")
                return adapter
            except Exception as e:
                logger.error(f"Failed to create adapter for {plugin_id}: {e}")
                return None
        return None

    def load_with_adapter(
        self,
        plugin_id: str,
        capability_id: str,
        adapter_factory: Optional[Callable] = None
    ) -> tuple[LoadedPlugin, Optional[PluginInterface]]:
        """
        加载插件并创建适配器

        Args:
            plugin_id: 插件ID
            capability_id: 能力ID
            adapter_factory: 适配器工厂（可选）

        Returns:
            (LoadedPlugin, PluginInterface) 元组
        """
        # 加载插件
        loaded = self.load_plugin(plugin_id, capability_id)

        # 创建适配器
        if adapter_factory:
            adapter = adapter_factory(plugin_id, capability_id)
        else:
            adapter = self.create_adapter(plugin_id, capability_id)

        # 关联适配器
        if adapter:
            loaded.adapter = adapter

        return loaded, adapter

    # ==================== 批量操作 ====================

    def load_all_for_capability(self, capability_id: str) -> List[LoadedPlugin]:
        """
        加载所有提供某能力的插件

        Args:
            capability_id: 能力ID

        Returns:
            LoadedPlugin列表
        """
        providers = self.registry.get_plugins_by_capability(capability_id)
        loaded_plugins = []

        for metadata in providers:
            try:
                loaded = self.load_plugin(metadata.plugin_id, capability_id)
                loaded_plugins.append(loaded)
            except Exception as e:
                logger.warning(f"Failed to load {metadata.plugin_id}: {e}")
                continue

        return loaded_plugins

    def unload_all(self) -> int:
        """
        卸载所有插件

        Returns:
            成功卸载的插件数量
        """
        plugin_ids = list(self._loaded_plugins.keys())
        count = 0

        for plugin_id in plugin_ids:
            if self.unload_plugin(plugin_id):
                count += 1

        return count

    # ==================== 缓存管理 ====================

    def clear_cache(self):
        """清空缓存"""
        self._loaded_plugins.clear()
        self._capability_to_plugin.clear()
        logger.info("Plugin cache cleared")

    def cleanup_idle_plugins(self, idle_minutes: int = 30):
        """
        清理空闲插件

        Args:
            idle_minutes: 空闲时间阈值（分钟）
        """
        from datetime import timedelta

        now = datetime.now()
        threshold = now - timedelta(minutes=idle_minutes)
        to_unload = []

        for plugin_id, loaded in self._loaded_plugins.items():
            last_access = loaded.last_access or loaded.load_time
            if last_access < threshold:
                to_unload.append(plugin_id)

        for plugin_id in to_unload:
            self.unload_plugin(plugin_id)

        if to_unload:
            logger.info(f"Cleaned up {len(to_unload)} idle plugins")






        # WorkflowEngine 集成


        self.use_workflow_engine = use_workflow_engine


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

# ==================== 工厂函数 ====================

_loader_instance: Optional[PluginLoader] = None


def get_plugin_loader(
    registry: Optional[PluginRegistry] = None,
    strategy: LoadStrategy = LoadStrategy.LAZY
) -> PluginLoader:
    """
    获取插件加载器单例

    Args:
        registry: 插件注册表（可选）
        strategy: 加载策略（可选）

    Returns:
        PluginLoader实例
    """
    global _loader_instance

    if _loader_instance is None:
        _loader_instance = PluginLoader(registry, strategy)

    return _loader_instance
