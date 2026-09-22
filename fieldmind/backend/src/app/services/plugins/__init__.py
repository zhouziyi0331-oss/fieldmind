"""
Plugin Services Package

插件管理系统，负责扫描、注册、加载、适配GitHub插件。

核心组件:
- PluginRegistry: 插件注册表，扫描和管理插件元数据
- PluginLoader: 插件加载器，动态加载插件模块
- PluginInterface: 插件统一接口规范
- PluginAdapter: 具体插件的适配器实现
"""

from .plugin_registry import (
    PluginRegistry,
    PluginType,
    PluginStatus,
    PluginCapability,
    PluginMetadata,
    CapabilityIndex,
    get_plugin_registry
)

from .plugin_interface import (
    PluginInterface,
    BasePluginAdapter,
    MockPluginAdapter,
    PluginContext,
    PluginInput,
    PluginOutput,
    PluginExecutionStatus,
    PluginError,
    PluginNotFoundError,
    PluginLoadError,
    PluginExecutionError,
    PluginTimeoutError,
    PluginValidationError,
    create_plugin_context,
    create_plugin_input
)

from .plugin_loader import (
    PluginLoader,
    LoadStrategy,
    LoadedPlugin,
    get_plugin_loader
)

from .plugin_adapter import (
    GraphRAGAdapter,
    GraphitiAdapter,
    CogneeAdapter,
    Crawl4AIAdapter,
    FirecrawlAdapter,
    BrowserUseAdapter,
    RAGFlowAdapter,
    LightRAGAdapter,
    Mem0Adapter,
    MarkitdownAdapter,
    PDFGuruAdapter,
    HanLPAdapter,
    AdapterFactory
)

__all__ = [
    # Registry
    "PluginRegistry",
    "PluginType",
    "PluginStatus",
    "PluginCapability",
    "PluginMetadata",
    "CapabilityIndex",
    "get_plugin_registry",

    # Interface
    "PluginInterface",
    "BasePluginAdapter",
    "MockPluginAdapter",
    "PluginContext",
    "PluginInput",
    "PluginOutput",
    "PluginExecutionStatus",
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "PluginExecutionError",
    "PluginTimeoutError",
    "PluginValidationError",
    "create_plugin_context",
    "create_plugin_input",

    # Loader
    "PluginLoader",
    "LoadStrategy",
    "LoadedPlugin",
    "get_plugin_loader",

    # Adapters
    "GraphRAGAdapter",
    "GraphitiAdapter",
    "CogneeAdapter",
    "Crawl4AIAdapter",
    "FirecrawlAdapter",
    "BrowserUseAdapter",
    "RAGFlowAdapter",
    "LightRAGAdapter",
    "Mem0Adapter",
    "MarkitdownAdapter",
    "PDFGuruAdapter",
    "HanLPAdapter",
    "AdapterFactory"
]
