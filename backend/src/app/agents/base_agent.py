"""
BaseAgent - 所有Agent的基类

设计原则：
1. 每个Agent独立运行，互不依赖
2. 输入输出标准化，便于串联
3. 内置日志和性能监控
4. 支持同步和异步执行
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Agent执行结果的标准格式"""

    agent_name: str                          # Agent名称
    success: bool                            # 是否成功
    data: Dict[str, Any]                    # 结果数据
    execution_time: float                   # 执行耗时（秒）
    confidence: float = 0.0                 # 结果置信度 0-1
    errors: List[str] = field(default_factory=list)   # 错误信息
    warnings: List[str] = field(default_factory=list) # 警告信息
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'agent_name': self.agent_name,
            'success': self.success,
            'data': self.data,
            'execution_time': self.execution_time,
            'confidence': self.confidence,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class BaseAgent(ABC):
    """
    Agent基类

    所有具体的Agent都应该继承这个类并实现 _execute() 方法
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Agent

        Args:
            config: Agent配置参数
        """
        self.config = config or {}
        self.agent_name = self.__class__.__name__
        self.logger = logging.getLogger(f"agent.{self.agent_name}")

    @abstractmethod
    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent的核心执行逻辑（子类必须实现）

        Args:
            input_data: 输入数据，格式由各Agent自定义

        Returns:
            处理结果字典

        Raises:
            Exception: 处理失败时抛出异常
        """
        pass

    def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        执行Agent（带监控和错误处理）

        Args:
            input_data: 输入数据

        Returns:
            AgentResult对象
        """
        start_time = time.time()
        errors = []
        warnings = []
        result_data = {}
        success = False
        confidence = 0.0

        try:
            self.logger.info(f"🤖 {self.agent_name} 开始执行")
            self.logger.debug(f"输入数据: {self._safe_log_input(input_data)}")

            # 输入验证
            validation_result = self._validate_input(input_data)
            if not validation_result['valid']:
                raise ValueError(f"输入验证失败: {validation_result['error']}")

            # 执行核心逻辑
            result_data = self._execute(input_data)

            # 输出验证
            if not isinstance(result_data, dict):
                raise TypeError(f"Agent返回值必须是dict，实际类型: {type(result_data)}")

            # 计算置信度（如果子类返回了confidence字段）
            confidence = result_data.pop('confidence', 0.0)

            # 提取警告信息（如果有）
            warnings = result_data.pop('warnings', [])

            success = True
            execution_time = time.time() - start_time

            self.logger.info(
                f"✅ {self.agent_name} 执行成功 "
                f"(耗时: {execution_time:.2f}s, 置信度: {confidence:.2f})"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            errors.append(error_msg)
            self.logger.error(f"❌ {self.agent_name} 执行失败: {error_msg}", exc_info=True)

        return AgentResult(
            agent_name=self.agent_name,
            success=success,
            data=result_data,
            execution_time=execution_time,
            confidence=confidence,
            errors=errors,
            warnings=warnings,
            metadata=self._get_metadata()
        )

    def _validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证输入数据（子类可覆盖以实现自定义验证）

        Args:
            input_data: 待验证的输入

        Returns:
            {'valid': bool, 'error': str}
        """
        if not isinstance(input_data, dict):
            return {'valid': False, 'error': f'输入必须是dict，实际类型: {type(input_data)}'}

        # 子类可以覆盖这个方法添加更多验证
        return {'valid': True, 'error': None}

    def _safe_log_input(self, input_data: Dict[str, Any]) -> str:
        """
        安全地记录输入数据（避免日志过长）

        Args:
            input_data: 输入数据

        Returns:
            安全的日志字符串
        """
        if 'text_content' in input_data:
            preview = input_data['text_content'][:100]
            return f"{{text_content: '{preview}...' ({len(input_data['text_content'])}字符), ...}}"
        return str(input_data)[:200]

    def _get_metadata(self) -> Dict[str, Any]:
        """
        获取Agent元数据（子类可覆盖）

        Returns:
            元数据字典
        """
        return {
            'agent_version': '1.0.0',
            'config': self.config
        }

    def get_required_inputs(self) -> List[str]:
        """
        返回该Agent需要的必需输入字段（子类可覆盖）

        Returns:
            必需字段列表
        """
        return []

    def get_output_schema(self) -> Dict[str, str]:
        """
        返回该Agent的输出schema（子类可覆盖）

        Returns:
            字段名 -> 类型描述的映射
        """
        return {}


class MockAgent(BaseAgent):
    """
    测试用的Mock Agent
    """

    def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """简单返回输入数据"""
        return {
            'message': 'MockAgent executed successfully',
            'input_received': list(input_data.keys()),
            'confidence': 1.0
        }
