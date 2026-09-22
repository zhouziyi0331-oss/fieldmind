"""
Plugin Interface - 插件统一接口定义

为所有插件定义统一的接口规范，使Agent能够以一致的方式调用不同插件。

设计理念:
1. 统一接口 - 所有插件通过相同的方法调用
2. 类型安全 - 使用类型提示和验证
3. 异步支持 - 支持同步和异步两种调用方式
4. 错误处理 - 统一的异常体系
5. 上下文传递 - 支持执行上下文和配置
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio


class PluginExecutionStatus(Enum):
    """插件执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class PluginError(Exception):
    """插件基础异常"""
    pass


class PluginNotFoundError(PluginError):
    """插件未找到"""
    pass


class PluginLoadError(PluginError):
    """插件加载失败"""
    pass


class PluginExecutionError(PluginError):
    """插件执行失败"""
    pass


class PluginTimeoutError(PluginError):
    """插件执行超时"""
    pass


class PluginValidationError(PluginError):
    """插件输入验证失败"""
    pass


@dataclass
class PluginContext:
    """插件执行上下文"""
    request_id: str                           # 请求ID
    agent_id: str                             # 调用Agent的ID
    capability_id: str                        # 使用的能力ID
    config: Dict[str, Any] = field(default_factory=dict)  # 配置参数
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    timeout: float = 60.0                     # 超时时间（秒）
    retry_count: int = 0                      # 重试次数
    max_retries: int = 3                      # 最大重试次数
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PluginInput:
    """插件输入数据"""
    capability_id: str                        # 能力ID
    input_type: str                           # 输入类型: "text", "url", "file", etc.
    data: Any                                 # 输入数据
    parameters: Dict[str, Any] = field(default_factory=dict)  # 参数
    context: Optional[PluginContext] = None   # 执行上下文


@dataclass
class PluginOutput:
    """插件输出数据"""
    capability_id: str                        # 能力ID
    output_type: str                          # 输出类型: "entities", "graph", "text", etc.
    data: Any                                 # 输出数据
    status: PluginExecutionStatus             # 执行状态
    execution_time: float = 0.0               # 执行时间（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    error: Optional[str] = None               # 错误信息
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "capability_id": self.capability_id,
            "output_type": self.output_type,
            "data": self.data,
            "status": self.status.value,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }


class PluginInterface(ABC):
    """
    插件统一接口（抽象基类）

    所有插件适配器必须实现此接口
    """

    def __init__(self, plugin_id: str, capability_id: str):
        """
        初始化插件接口

        Args:
            plugin_id: 插件ID
            capability_id: 能力ID
        """
        self.plugin_id = plugin_id
        self.capability_id = capability_id
        self._is_loaded = False
        self._module = None

    @abstractmethod
    def load(self) -> bool:
        """
        加载插件

        Returns:
            是否加载成功
        """
        pass

    @abstractmethod
    def unload(self) -> bool:
        """
        卸载插件

        Returns:
            是否卸载成功
        """
        pass

    @abstractmethod
    def validate_input(self, plugin_input: PluginInput) -> bool:
        """
        验证输入数据

        Args:
            plugin_input: 插件输入

        Returns:
            是否验证通过

        Raises:
            PluginValidationError: 验证失败
        """
        pass

    @abstractmethod
    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """
        同步执行插件

        Args:
            plugin_input: 插件输入

        Returns:
            插件输出

        Raises:
            PluginExecutionError: 执行失败
            PluginTimeoutError: 执行超时
        """
        pass

    @abstractmethod
    async def execute_async(self, plugin_input: PluginInput) -> PluginOutput:
        """
        异步执行插件

        Args:
            plugin_input: 插件输入

        Returns:
            插件输出

        Raises:
            PluginExecutionError: 执行失败
            PluginTimeoutError: 执行超时
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        获取插件支持的能力列表

        Returns:
            能力ID列表
        """
        pass

    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """
        获取输入数据的JSON Schema

        Returns:
            JSON Schema字典
        """
        pass

    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """
        获取输出数据的JSON Schema

        Returns:
            JSON Schema字典
        """
        pass

    @property
    def is_loaded(self) -> bool:
        """插件是否已加载"""
        return self._is_loaded

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            插件是否健康
        """
        return self._is_loaded and self._module is not None


class BasePluginAdapter(PluginInterface):
    """
    插件适配器基类

    提供通用的插件适配逻辑，子类只需实现特定的执行逻辑
    """

    def __init__(self, plugin_id: str, capability_id: str, module_path: Optional[str] = None):
        """
        初始化适配器

        Args:
            plugin_id: 插件ID
            capability_id: 能力ID
            module_path: 模块路径（可选）
        """
        super().__init__(plugin_id, capability_id)
        self.module_path = module_path
        self._supported_input_types: List[str] = []
        self._supported_output_types: List[str] = []

    def load(self) -> bool:
        """加载插件（基础实现）"""
        if self._is_loaded:
            return True

        try:
            # 子类可重写此方法实现具体的加载逻辑
            self._is_loaded = True
            return True
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin {self.plugin_id}: {e}")

    def unload(self) -> bool:
        """卸载插件（基础实现）"""
        if not self._is_loaded:
            return True

        try:
            self._module = None
            self._is_loaded = False
            return True
        except Exception as e:
            raise PluginLoadError(f"Failed to unload plugin {self.plugin_id}: {e}")

    def validate_input(self, plugin_input: PluginInput) -> bool:
        """验证输入数据"""
        # 检查能力ID
        if plugin_input.capability_id != self.capability_id:
            raise PluginValidationError(
                f"Capability mismatch: expected {self.capability_id}, got {plugin_input.capability_id}"
            )

        # 检查输入类型
        if self._supported_input_types and plugin_input.input_type not in self._supported_input_types:
            raise PluginValidationError(
                f"Unsupported input type: {plugin_input.input_type}. "
                f"Supported types: {self._supported_input_types}"
            )

        # 检查数据不为空
        if plugin_input.data is None:
            raise PluginValidationError("Input data cannot be None")

        return True

    def get_capabilities(self) -> List[str]:
        """获取支持的能力"""
        return [self.capability_id]

    def get_input_schema(self) -> Dict[str, Any]:
        """获取输入Schema（基础实现）"""
        return {
            "type": "object",
            "properties": {
                "capability_id": {"type": "string"},
                "input_type": {"type": "string", "enum": self._supported_input_types},
                "data": {},
                "parameters": {"type": "object"}
            },
            "required": ["capability_id", "input_type", "data"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """获取输出Schema（基础实现）"""
        return {
            "type": "object",
            "properties": {
                "capability_id": {"type": "string"},
                "output_type": {"type": "string", "enum": self._supported_output_types},
                "data": {},
                "status": {"type": "string"},
                "execution_time": {"type": "number"},
                "metadata": {"type": "object"}
            },
            "required": ["capability_id", "output_type", "data", "status"]
        }

    async def execute_async(self, plugin_input: PluginInput) -> PluginOutput:
        """
        异步执行（默认实现：在线程池中执行同步方法）

        子类可重写以实现真正的异步执行
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, plugin_input)


class MockPluginAdapter(BasePluginAdapter):
    """
    Mock插件适配器（用于测试）

    模拟插件执行，返回预定义的结果
    """

    def __init__(
        self,
        plugin_id: str,
        capability_id: str,
        mock_output: Optional[Any] = None,
        execution_time: float = 0.1
    ):
        super().__init__(plugin_id, capability_id)
        self.mock_output = mock_output or {"result": "mock_data"}
        self.mock_execution_time = execution_time
        self._supported_input_types = ["text", "url", "file"]
        self._supported_output_types = ["entities", "graph", "text", "json"]

    def execute(self, plugin_input: PluginInput) -> PluginOutput:
        """执行Mock插件"""
        import time

        # 验证输入
        self.validate_input(plugin_input)

        # 模拟执行
        start_time = time.time()
        time.sleep(self.mock_execution_time)

        # 返回Mock输出
        return PluginOutput(
            capability_id=self.capability_id,
            output_type="json",
            data=self.mock_output,
            status=PluginExecutionStatus.SUCCESS,
            execution_time=time.time() - start_time,
            metadata={"plugin_id": self.plugin_id, "mode": "mock"}
        )


# ==================== 工具函数 ====================

def create_plugin_context(
    agent_id: str,
    capability_id: str,
    request_id: Optional[str] = None,
    **kwargs
) -> PluginContext:
    """
    创建插件执行上下文

    Args:
        agent_id: Agent ID
        capability_id: 能力ID
        request_id: 请求ID（可选，自动生成）
        **kwargs: 其他参数

    Returns:
        PluginContext实例
    """
    import uuid

    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:8]}"

    return PluginContext(
        request_id=request_id,
        agent_id=agent_id,
        capability_id=capability_id,
        **kwargs
    )


def create_plugin_input(
    capability_id: str,
    input_type: str,
    data: Any,
    parameters: Optional[Dict[str, Any]] = None,
    context: Optional[PluginContext] = None
) -> PluginInput:
    """
    创建插件输入

    Args:
        capability_id: 能力ID
        input_type: 输入类型
        data: 输入数据
        parameters: 参数（可选）
        context: 执行上下文（可选）

    Returns:
        PluginInput实例
    """
    return PluginInput(
        capability_id=capability_id,
        input_type=input_type,
        data=data,
        parameters=parameters or {},
        context=context
    )
