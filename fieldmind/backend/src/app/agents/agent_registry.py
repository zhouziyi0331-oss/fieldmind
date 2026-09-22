"""
Agent 注册表
管理所有 Agent 的注册、发现和生命周期
"""
from typing import Dict, Type, Optional, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Agent 注册表 - 单例模式"""

    _instance = None
    _agents: Dict[str, Type] = {}
    _agent_metadata: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化注册表"""
        if not hasattr(self, '_initialized'):
            self._agents = {}
            self._agent_metadata = {}
            self._initialized = True
            logger.info("Agent 注册表已初始化")

    def register(
        self,
        name: str,
        agent_class: Type,
        description: str = "",
        version: str = "1.0.0",
        capabilities: List[str] = None,
        dependencies: List[str] = None
    ) -> None:
        """
        注册一个 Agent

        Args:
            name: Agent 名称（唯一标识）
            agent_class: Agent 类
            description: Agent 描述
            version: 版本号
            capabilities: Agent 能力列表
            dependencies: 依赖的其他 Agent
        """
        if name in self._agents:
            logger.warning(f"Agent '{name}' 已存在，将被覆盖")

        self._agents[name] = agent_class
        self._agent_metadata[name] = {
            "name": name,
            "class": agent_class.__name__,
            "description": description,
            "version": version,
            "capabilities": capabilities or [],
            "dependencies": dependencies or [],
            "registered_at": datetime.now().isoformat()
        }

        logger.info(f"✓ Agent '{name}' 注册成功")

    def unregister(self, name: str) -> bool:
        """
        注销一个 Agent

        Args:
            name: Agent 名称

        Returns:
            是否注销成功
        """
        if name not in self._agents:
            logger.warning(f"Agent '{name}' 不存在")
            return False

        del self._agents[name]
        del self._agent_metadata[name]
        logger.info(f"Agent '{name}' 已注销")
        return True

    def get(self, name: str) -> Optional[Type]:
        """
        获取 Agent 类

        Args:
            name: Agent 名称

        Returns:
            Agent 类，如果不存在返回 None
        """
        return self._agents.get(name)

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取 Agent 元数据

        Args:
            name: Agent 名称

        Returns:
            Agent 元数据，如果不存在返回 None
        """
        return self._agent_metadata.get(name)

    def list_all(self) -> List[str]:
        """
        列出所有已注册的 Agent 名称

        Returns:
            Agent 名称列表
        """
        return list(self._agents.keys())

    def list_by_capability(self, capability: str) -> List[str]:
        """
        根据能力筛选 Agent

        Args:
            capability: 能力名称

        Returns:
            具备该能力的 Agent 名称列表
        """
        return [
            name for name, metadata in self._agent_metadata.items()
            if capability in metadata.get("capabilities", [])
        ]

    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有 Agent 的元数据

        Returns:
            所有 Agent 的元数据字典
        """
        return self._agent_metadata.copy()

    def clear(self) -> None:
        """清空注册表（通常用于测试）"""
        self._agents.clear()
        self._agent_metadata.clear()
        logger.info("Agent 注册表已清空")

    def __len__(self) -> int:
        """返回已注册的 Agent 数量"""
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        """检查 Agent 是否已注册"""
        return name in self._agents


# 全局单例实例
agent_registry = AgentRegistry()


# 装饰器：自动注册 Agent
def register_agent(
    name: str,
    description: str = "",
    version: str = "1.0.0",
    capabilities: List[str] = None,
    dependencies: List[str] = None
):
    """
    Agent 注册装饰器

    使用示例:
    ```python
    @register_agent(
        name="chunking_agent",
        description="文档切分 Agent",
        capabilities=["document_processing", "chunking"]
    )
    class ChunkingAgent(BaseAgent):
        pass
    ```
    """
    def decorator(agent_class: Type):
        agent_registry.register(
            name=name,
            agent_class=agent_class,
            description=description,
            version=version,
            capabilities=capabilities,
            dependencies=dependencies
        )
        return agent_class
    return decorator


# 辅助函数
def get_agent(name: str) -> Optional[Type]:
    """快捷方式：获取 Agent 类"""
    return agent_registry.get(name)


def list_agents() -> List[str]:
    """快捷方式：列出所有 Agent"""
    return agent_registry.list_all()


def find_agents_by_capability(capability: str) -> List[str]:
    """快捷方式：根据能力查找 Agent"""
    return agent_registry.list_by_capability(capability)
