"""
动态发现引擎 - services层兼容模块
为了保持旧Agent的向后兼容性，从tools导入DynamicDiscoveryEngine
"""

from app.tools.knowledge.dynamic_discovery import DynamicDiscoveryEngine

__all__ = ['DynamicDiscoveryEngine']
