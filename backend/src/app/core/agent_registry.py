"""
Agent注册中心 (Agent Registry)

集中管理所有Agent实例，提供：
1. Agent注册和发现
2. Agent生命周期管理
3. Agent能力描述
4. Agent版本管理
5. 动态加载和卸载

支持插件化的Agent扩展
"""
import logging
from typing import Dict, Any, List, Optional, Type, Callable
from datetime import datetime
from abc import ABC, abstractmethod
import importlib
import inspect

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent基类"""

    # Agent元数据
    agent_type: str = "base"
    agent_name: str = "Base Agent"
    agent_version: str = "1.0.0"
    agent_description: str = "Base agent interface"

    # Agent能力
    capabilities: List[str] = []
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Agent

        Args:
            config: Agent配置
        """
        self.config = config or {}
        self.execution_count = 0
        self.last_execution_time = None
        self._initialized = False

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Agent任务

        Args:
            input_data: 输入数据

        Returns:
            执行结果
        """
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        验证输入数据

        Args:
            input_data: 输入数据

        Returns:
            是否有效
        """
        if not self.input_schema:
            return True

        # 简单验证：检查必需字段
        required_fields = self.input_schema.get('required', [])
        for field in required_fields:
            if field not in input_data:
                logger.warning(f"⚠️ 缺少必需字段: {field}")
                return False

        return True

    def initialize(self) -> bool:
        """
        初始化Agent（可选）

        Returns:
            是否成功
        """
        if self._initialized:
            return True

        try:
            # 子类可以覆盖此方法进行初始化
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"❌ Agent初始化失败: {e}")
            return False

    def cleanup(self):
        """清理Agent资源（可选）"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """获取Agent元数据"""
        return {
            'agent_type': self.agent_type,
            'agent_name': self.agent_name,
            'agent_version': self.agent_version,
            'agent_description': self.agent_description,
            'capabilities': self.capabilities,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'execution_count': self.execution_count,
            'last_execution_time': self.last_execution_time.isoformat() if self.last_execution_time else None
        }

    def _record_execution(self):
        """记录执行"""
        self.execution_count += 1
        self.last_execution_time = datetime.now()


class AgentRegistry:
    """Agent注册中心"""

    def __init__(self):
        """初始化注册中心"""
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._agent_factories: Dict[str, Callable] = {}
        self._agent_metadata: Dict[str, Dict[str, Any]] = {}

        logger.info("✅ Agent注册中心初始化")

    # ==================== Agent注册 ====================

    def register_agent(
        self,
        agent_type: str,
        agent_instance: BaseAgent,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        注册Agent实例

        Args:
            agent_type: Agent类型
            agent_instance: Agent实例
            metadata: 额外元数据

        Returns:
            是否成功
        """
        try:
            if agent_type in self._agents:
                logger.warning(f"⚠️ Agent类型 '{agent_type}' 已存在，将覆盖")

            # 初始化Agent
            if not agent_instance._initialized:
                if not agent_instance.initialize():
                    logger.error(f"❌ Agent '{agent_type}' 初始化失败")
                    return False

            self._agents[agent_type] = agent_instance

            # 存储元数据
            combined_metadata = agent_instance.get_metadata()
            if metadata:
                combined_metadata.update(metadata)
            self._agent_metadata[agent_type] = combined_metadata

            logger.info(f"✅ Agent已注册: {agent_type} ({agent_instance.agent_name})")

            return True

        except Exception as e:
            logger.error(f"❌ 注册Agent失败: {e}", exc_info=True)
            return False

    def register_agent_class(
        self,
        agent_type: str,
        agent_class: Type[BaseAgent],
        auto_instantiate: bool = False,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        注册Agent类（延迟实例化）

        Args:
            agent_type: Agent类型
            agent_class: Agent类
            auto_instantiate: 是否立即实例化
            config: 实例化配置

        Returns:
            是否成功
        """
        try:
            if not issubclass(agent_class, BaseAgent):
                logger.error(f"❌ {agent_class} 不是BaseAgent的子类")
                return False

            self._agent_classes[agent_type] = agent_class

            logger.info(f"✅ Agent类已注册: {agent_type} ({agent_class.__name__})")

            # 自动实例化
            if auto_instantiate:
                instance = agent_class(config)
                return self.register_agent(agent_type, instance)

            return True

        except Exception as e:
            logger.error(f"❌ 注册Agent类失败: {e}")
            return False

    def register_agent_factory(
        self,
        agent_type: str,
        factory_func: Callable[..., BaseAgent]
    ) -> bool:
        """
        注册Agent工厂函数

        Args:
            agent_type: Agent类型
            factory_func: 工厂函数

        Returns:
            是否成功
        """
        try:
            self._agent_factories[agent_type] = factory_func

            logger.info(f"✅ Agent工厂已注册: {agent_type}")

            return True

        except Exception as e:
            logger.error(f"❌ 注册Agent工厂失败: {e}")
            return False

    # ==================== Agent获取 ====================

    def get_agent(
        self,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None,
        create_if_not_exists: bool = True
    ) -> Optional[BaseAgent]:
        """
        获取Agent实例

        Args:
            agent_type: Agent类型
            config: 配置（用于创建新实例）
            create_if_not_exists: 如果不存在是否创建

        Returns:
            Agent实例
        """
        # 1. 优先返回已注册的实例
        if agent_type in self._agents:
            return self._agents[agent_type]

        # 2. 如果不需要创建，直接返回None
        if not create_if_not_exists:
            return None

        # 3. 尝试从工厂创建
        if agent_type in self._agent_factories:
            try:
                factory = self._agent_factories[agent_type]
                instance = factory(config) if config else factory()
                self.register_agent(agent_type, instance)
                return instance
            except Exception as e:
                logger.error(f"❌ 从工厂创建Agent失败: {e}")

        # 4. 尝试从类创建
        if agent_type in self._agent_classes:
            try:
                agent_class = self._agent_classes[agent_type]
                instance = agent_class(config)
                self.register_agent(agent_type, instance)
                return instance
            except Exception as e:
                logger.error(f"❌ 从类创建Agent失败: {e}")

        logger.warning(f"⚠️ Agent '{agent_type}' 未找到")
        return None

    def has_agent(self, agent_type: str) -> bool:
        """检查Agent是否存在"""
        return (
            agent_type in self._agents or
            agent_type in self._agent_classes or
            agent_type in self._agent_factories
        )

    # ==================== Agent发现 ====================

    def list_agents(
        self,
        capability: Optional[str] = None,
        include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        列出所有Agent

        Args:
            capability: 筛选具有特定能力的Agent
            include_metadata: 是否包含完整元数据

        Returns:
            Agent列表
        """
        agents = []

        # 已实例化的Agent
        for agent_type, agent in self._agents.items():
            metadata = agent.get_metadata()

            # 能力筛选
            if capability and capability not in metadata.get('capabilities', []):
                continue

            agent_info = {
                'agent_type': agent_type,
                'agent_name': metadata['agent_name'],
                'status': 'active',
                'execution_count': metadata['execution_count']
            }

            if include_metadata:
                agent_info['metadata'] = metadata

            agents.append(agent_info)

        # 已注册但未实例化的类
        for agent_type, agent_class in self._agent_classes.items():
            if agent_type not in self._agents:
                agent_info = {
                    'agent_type': agent_type,
                    'agent_name': agent_class.agent_name,
                    'status': 'registered',
                    'execution_count': 0
                }

                if include_metadata:
                    agent_info['metadata'] = {
                        'agent_version': agent_class.agent_version,
                        'agent_description': agent_class.agent_description,
                        'capabilities': agent_class.capabilities
                    }

                agents.append(agent_info)

        return agents

    def find_agents_by_capability(self, capability: str) -> List[str]:
        """
        根据能力查找Agent

        Args:
            capability: 能力名称

        Returns:
            Agent类型列表
        """
        matching_agents = []

        for agent_type in self._agents.keys():
            agent = self._agents[agent_type]
            if capability in agent.capabilities:
                matching_agents.append(agent_type)

        for agent_type, agent_class in self._agent_classes.items():
            if agent_type not in self._agents:
                if capability in agent_class.capabilities:
                    matching_agents.append(agent_type)

        return matching_agents

    def get_agent_metadata(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """获取Agent元数据"""
        if agent_type in self._agent_metadata:
            return self._agent_metadata[agent_type]

        # 尝试从类获取
        if agent_type in self._agent_classes:
            agent_class = self._agent_classes[agent_type]
            return {
                'agent_type': agent_type,
                'agent_name': agent_class.agent_name,
                'agent_version': agent_class.agent_version,
                'agent_description': agent_class.agent_description,
                'capabilities': agent_class.capabilities
            }

        return None

    # ==================== Agent生命周期管理 ====================

    def unregister_agent(self, agent_type: str) -> bool:
        """
        注销Agent

        Args:
            agent_type: Agent类型

        Returns:
            是否成功
        """
        try:
            if agent_type in self._agents:
                agent = self._agents[agent_type]
                agent.cleanup()
                del self._agents[agent_type]
                logger.info(f"✅ Agent已注销: {agent_type}")

            if agent_type in self._agent_metadata:
                del self._agent_metadata[agent_type]

            if agent_type in self._agent_classes:
                del self._agent_classes[agent_type]

            if agent_type in self._agent_factories:
                del self._agent_factories[agent_type]

            return True

        except Exception as e:
            logger.error(f"❌ 注销Agent失败: {e}")
            return False

    def reload_agent(
        self,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        重新加载Agent

        Args:
            agent_type: Agent类型
            config: 新配置

        Returns:
            是否成功
        """
        try:
            # 先注销
            self.unregister_agent(agent_type)

            # 重新创建
            agent = self.get_agent(agent_type, config, create_if_not_exists=True)

            if agent:
                logger.info(f"✅ Agent已重新加载: {agent_type}")
                return True
            else:
                logger.error(f"❌ Agent重新加载失败: {agent_type}")
                return False

        except Exception as e:
            logger.error(f"❌ 重新加载Agent失败: {e}")
            return False

    # ==================== 动态加载 ====================

    def load_agent_from_module(
        self,
        module_path: str,
        agent_class_name: str,
        agent_type: Optional[str] = None,
        auto_register: bool = True
    ) -> Optional[Type[BaseAgent]]:
        """
        从模块动态加载Agent类

        Args:
            module_path: 模块路径 (e.g., 'app.services.agents.knowledge_agent')
            agent_class_name: Agent类名
            agent_type: Agent类型（默认使用类的agent_type）
            auto_register: 是否自动注册

        Returns:
            Agent类
        """
        try:
            # 动态导入模块
            module = importlib.import_module(module_path)

            # 获取类
            agent_class = getattr(module, agent_class_name)

            if not issubclass(agent_class, BaseAgent):
                logger.error(f"❌ {agent_class_name} 不是BaseAgent的子类")
                return None

            # 确定agent_type
            if not agent_type:
                agent_type = agent_class.agent_type

            # 自动注册
            if auto_register:
                self.register_agent_class(agent_type, agent_class)

            logger.info(f"✅ 从模块加载Agent: {module_path}.{agent_class_name}")

            return agent_class

        except Exception as e:
            logger.error(f"❌ 从模块加载Agent失败: {e}", exc_info=True)
            return None

    def auto_discover_agents(
        self,
        package_path: str = "app.services.agents"
    ) -> int:
        """
        自动发现并注册Agent

        Args:
            package_path: 包路径

        Returns:
            发现的Agent数量
        """
        discovered_count = 0

        try:
            # 导入包
            package = importlib.import_module(package_path)

            # 遍历包中的所有模块
            import pkgutil
            for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                if ispkg:
                    continue

                module_path = f"{package_path}.{modname}"

                try:
                    module = importlib.import_module(module_path)

                    # 查找BaseAgent的子类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseAgent) and
                            obj is not BaseAgent and
                            obj.__module__ == module_path):

                            agent_type = obj.agent_type
                            self.register_agent_class(agent_type, obj)
                            discovered_count += 1

                except Exception as e:
                    logger.warning(f"⚠️ 无法加载模块 {module_path}: {e}")

            logger.info(f"✅ 自动发现 {discovered_count} 个Agent")

        except Exception as e:
            logger.error(f"❌ 自动发现Agent失败: {e}")

        return discovered_count

    # ==================== 状态和统计 ====================

    def get_registry_status(self) -> Dict[str, Any]:
        """获取注册中心状态"""
        return {
            'total_agents': len(self._agents) + len(self._agent_classes) + len(self._agent_factories),
            'active_agents': len(self._agents),
            'registered_classes': len(self._agent_classes),
            'registered_factories': len(self._agent_factories),
            'agents': self.list_agents(include_metadata=False),
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计"""
        stats = {
            'total_executions': 0,
            'agent_stats': {}
        }

        for agent_type, agent in self._agents.items():
            execution_count = agent.execution_count
            stats['total_executions'] += execution_count
            stats['agent_stats'][agent_type] = {
                'execution_count': execution_count,
                'last_execution_time': agent.last_execution_time.isoformat() if agent.last_execution_time else None
            }

        return stats

    def clear_all(self):
        """清空所有Agent"""
        for agent in self._agents.values():
            agent.cleanup()

        self._agents.clear()
        self._agent_classes.clear()
        self._agent_factories.clear()
        self._agent_metadata.clear()

        logger.info("✅ 所有Agent已清空")


# 全局单例
_registry_instance = None


def get_agent_registry() -> AgentRegistry:
    """获取Agent注册中心单例"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
    return _registry_instance
