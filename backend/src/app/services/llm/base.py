"""
基础 LLM 接口

定义所有 LLM 提供商需要实现的接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
from enum import Enum
import time


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class LLMMessage:
    """LLM 消息"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    provider: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    cost: float
    latency: float
    finish_reason: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMConfig:
    """LLM 配置"""
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    timeout: int = 60
    retry_attempts: int = 3
    stream: bool = False


class BaseLLM(ABC):
    """
    基础 LLM 类

    所有 LLM 提供商的实现都需要继承这个类
    """

    def __init__(self,
        api_key: str,
        base_url: Optional[str] = None,
        default_config: Optional[LLMConfig] = None,


        use_workflow_engine: bool = True):
        """
        初始化 LLM

        Args:
            api_key: API 密钥
            base_url: API 基础 URL（可选）
            default_config: 默认配置
        """
        self.api_key = api_key
        self.base_url = base_url
        self.default_config = default_config or LLMConfig(model=self.default_model)
        self._total_tokens = 0
        self._total_cost = 0.0

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商名称"""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """默认模型"""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """支持的模型列表"""
        pass

    @abstractmethod
    def get_model_cost(self, model: str) -> Dict[str, float]:
        """
        获取模型的成本（每 1K tokens）

        Returns:
            {"prompt": 价格, "completion": 价格}
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            config: 配置（可选，使用默认配置）
            **kwargs: 其他参数

        Returns:
            LLM 响应
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式聊天请求

        Args:
            messages: 消息列表
            config: 配置（可选）
            **kwargs: 其他参数

        Yields:
            响应内容片段
        """
        pass

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        计算请求成本

        Args:
            model: 模型名称
            prompt_tokens: prompt tokens 数量
            completion_tokens: completion tokens 数量

        Returns:
            成本（美元）
        """
        costs = self.get_model_cost(model)
        prompt_cost = (prompt_tokens / 1000.0) * costs.get("prompt", 0)
        completion_cost = (completion_tokens / 1000.0) * costs.get("completion", 0)
        return prompt_cost + completion_cost

    def update_usage(self, tokens: int, cost: float):
        """更新使用统计"""
        self._total_tokens += tokens
        self._total_cost += cost

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            "provider": self.provider_name,
            "total_tokens": self._total_tokens,
            "total_cost": self._total_cost
        }

    def reset_usage_stats(self):
        """重置使用统计"""
        self._total_tokens = 0
        self._total_cost = 0

    async def _retry_with_backoff(
        self,
        func,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        """
        带指数退避的重试机制

        Args:
            func: 要执行的异步函数
            max_attempts: 最大尝试次数
            initial_delay: 初始延迟（秒）
            backoff_factor: 退避因子
        """
        delay = initial_delay

        for attempt in range(max_attempts):
            try:
                return await func()
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise

                # 指数退避
                await asyncio.sleep(delay)
                delay *= backoff_factor

                # 记录重试
                import logging
                logging.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                    f"Retrying in {delay}s..."
                )






        # WorkflowEngine 集成


        self.use_workflow_engine = use_workflow_engine


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

import asyncio
