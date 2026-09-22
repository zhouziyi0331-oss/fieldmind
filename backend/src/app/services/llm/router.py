"""
LLM 路由器

根据策略选择最合适的 LLM 提供商和模型
"""
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

from app.services.llm.base import (
    BaseLLM,
    LLMMessage,
    LLMResponse,
    LLMConfig
)

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """路由策略"""
    COST_OPTIMIZED = "cost_optimized"  # 成本优化
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # 性能优化
    BALANCED = "balanced"  # 平衡
    ROUND_ROBIN = "round_robin"  # 轮询
    FIXED = "fixed"  # 固定提供商


class LLMRouter:
    """
    LLM 路由器

    根据不同的策略选择最合适的 LLM 提供商
    """
    def __init__(self, providers: Dict[str, BaseLLM], strategy: RoutingStrategy = RoutingStrategy.BALANCED, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化路由器

        Args:
            providers: LLM 提供商字典 {"provider_name": llm_instance}
            strategy: 路由策略
        """
        self.providers = providers
        self.strategy = strategy
        self._round_robin_index = 0

        # 提供商性能评分（基于经验值）
        self._performance_scores = {
            "openai": 0.9,
            "anthropic": 0.95,
            "zhipu": 0.8,
            "qwen": 0.85,
        }

    def select_provider(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        preferred_provider: Optional[str] = None
    ) -> BaseLLM:
        """
        选择合适的 LLM 提供商

        Args:
            messages: 消息列表
            config: 配置
            preferred_provider: 首选提供商

        Returns:
            选中的 LLM 实例
        """
        if preferred_provider and preferred_provider in self.providers:
            return self.providers[preferred_provider]

        if self.strategy == RoutingStrategy.FIXED:
            # 返回第一个可用的提供商
            return next(iter(self.providers.values()))

        elif self.strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._select_by_cost(messages, config)

        elif self.strategy == RoutingStrategy.PERFORMANCE_OPTIMIZED:
            return self._select_by_performance()

        elif self.strategy == RoutingStrategy.BALANCED:
            return self._select_balanced(messages, config)

        elif self.strategy == RoutingStrategy.ROUND_ROBIN:
            return self._select_round_robin()

        else:
            return next(iter(self.providers.values()))

    def _select_by_cost(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig]
    ) -> BaseLLM:
        """选择成本最低的提供商"""
        if not self.providers:
            raise ValueError("No providers available")

        # 估算 token 数量（粗略估计：1 token ≈ 4 字符）
        total_chars = sum(len(msg.content) for msg in messages)
        estimated_prompt_tokens = total_chars // 4
        estimated_completion_tokens = (config.max_tokens or 1000) if config else 1000

        min_cost = float('inf')
        best_provider = None

        for provider in self.providers.values():
            model = config.model if config else provider.default_model
            costs = provider.get_model_cost(model)

            total_cost = (
                (estimated_prompt_tokens / 1000.0) * costs.get("prompt", 0) +
                (estimated_completion_tokens / 1000.0) * costs.get("completion", 0)
            )

            if total_cost < min_cost:
                min_cost = total_cost
                best_provider = provider

        return best_provider or next(iter(self.providers.values()))

    def _select_by_performance(self) -> BaseLLM:
        """选择性能最好的提供商"""
        best_score = 0
        best_provider = None

        for name, provider in self.providers.items():
            score = self._performance_scores.get(name, 0.5)
            if score > best_score:
                best_score = score
                best_provider = provider

        return best_provider or next(iter(self.providers.values()))

    def _select_balanced(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig]
    ) -> BaseLLM:
        """平衡性能和成本"""
        if not self.providers:
            raise ValueError("No providers available")

        # 估算 token 数量
        total_chars = sum(len(msg.content) for msg in messages)
        estimated_prompt_tokens = total_chars // 4
        estimated_completion_tokens = (config.max_tokens or 1000) if config else 1000

        best_score = float('-inf')
        best_provider = None

        for name, provider in self.providers.items():
            model = config.model if config else provider.default_model
            costs = provider.get_model_cost(model)

            # 计算成本
            total_cost = (
                (estimated_prompt_tokens / 1000.0) * costs.get("prompt", 0) +
                (estimated_completion_tokens / 1000.0) * costs.get("completion", 0)
            )

            # 归一化成本（假设最高成本为 $0.1）
            normalized_cost = 1.0 - min(total_cost / 0.1, 1.0)

            # 性能评分
            performance = self._performance_scores.get(name, 0.5)

            # 综合评分（成本权重 0.4，性能权重 0.6）
            score = 0.4 * normalized_cost + 0.6 * performance

            if score > best_score:
                best_score = score
                best_provider = provider

        return best_provider or next(iter(self.providers.values()))

    def _select_round_robin(self) -> BaseLLM:
        """轮询选择提供商"""
        providers_list = list(self.providers.values())
        if not providers_list:
            raise ValueError("No providers available")

        provider = providers_list[self._round_robin_index % len(providers_list)]
        self._round_robin_index += 1

        return provider

    async def chat(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        发送聊天请求（自动路由）

        Args:
            messages: 消息列表
            config: 配置
            preferred_provider: 首选提供商
            **kwargs: 其他参数

        Returns:
            LLM 响应
        """
        provider = self.select_provider(messages, config, preferred_provider)

        logger.info(f"Routing request to provider: {provider.provider_name}")

        return await provider.chat(messages, config, **kwargs)

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        preferred_provider: Optional[str] = None,
        **kwargs
    ):
        """流式聊天请求（自动路由）"""
        provider = self.select_provider(messages, config, preferred_provider)

        logger.info(f"Routing streaming request to provider: {provider.provider_name}")

        async for chunk in provider.chat_stream(messages, config, **kwargs):
            yield chunk

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有提供商的使用统计"""
        stats = {}
        for name, provider in self.providers.items():
            stats[name] = provider.get_usage_stats()
        return stats

    def reset_all_stats(self):
        """重置所有提供商的统计"""
        for provider in self.providers.values():
            provider.reset_usage_stats()
