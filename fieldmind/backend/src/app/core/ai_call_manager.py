"""
AI 调用管理器 - Week 2 Day 3-4
优化 Claude API 调用：批处理、重试、并发控制、Token 优化
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
import logging
import time
from dataclasses import dataclass
from enum import Enum
import backoff

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """模型层级"""
    HAIKU = "claude-3-haiku-20240307"
    SONNET = "claude-3-5-sonnet-20241022"
    OPUS = "claude-3-opus-20240229"


@dataclass
class APICallMetrics:
    """API 调用指标"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_duration: float = 0.0
    retry_count: int = 0

    @property
    def success_rate(self) -> float:
        return self.successful_calls / self.total_calls if self.total_calls > 0 else 0.0

    @property
    def avg_duration(self) -> float:
        return self.total_duration / self.total_calls if self.total_calls > 0 else 0.0


class AICallManager:
    """AI 调用管理器"""

    def __init__(
        self,
        api_key: str,
        max_concurrent: int = 5,
        rate_limit_per_min: int = 50,
        default_model: ModelTier = ModelTier.SONNET
    ):
        """
        初始化 AI 调用管理器

        Args:
            api_key: Anthropic API key
            max_concurrent: 最大并发数
            rate_limit_per_min: 每分钟速率限制
            default_model: 默认模型
        """
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=api_key)
        except ImportError:
            logger.error("❌ Anthropic SDK 未安装")
            self.client = None

        self.max_concurrent = max_concurrent
        self.rate_limit_per_min = rate_limit_per_min
        self.default_model = default_model

        # 并发控制
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # 速率限制（令牌桶算法）
        self.rate_limiter = asyncio.Semaphore(rate_limit_per_min)
        self._start_rate_limiter_refill()

        # 指标统计
        self.metrics = APICallMetrics()

        logger.info(
            f"✅ AI 调用管理器已初始化 "
            f"(并发: {max_concurrent}, 速率: {rate_limit_per_min}/min)"
        )

    def _start_rate_limiter_refill(self):
        """启动速率限制器补充任务"""
        async def refill():
            while True:
                await asyncio.sleep(60 / self.rate_limit_per_min)
                try:
                    self.rate_limiter.release()
                except ValueError:
                    pass

        asyncio.create_task(refill())

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=30
    )
    async def call_with_retry(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: Optional[ModelTier] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        带重试的 API 调用

        Args:
            messages: 消息列表
            system: 系统提示
            model: 模型选择
            max_tokens: 最大 token 数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            API 响应
        """
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        model_name = (model or self.default_model).value
        start_time = time.time()

        # 并发控制
        async with self.semaphore:
            # 速率限制
            async with self.rate_limiter:
                try:
                    self.metrics.total_calls += 1

                    # 调用 API
                    response = await self.client.messages.create(
                        model=model_name,
                        messages=messages,
                        system=system,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )

                    # 统计
                    duration = time.time() - start_time
                    self.metrics.successful_calls += 1
                    self.metrics.total_duration += duration

                    # Token 统计
                    usage = response.usage
                    total_tokens = usage.input_tokens + usage.output_tokens
                    self.metrics.total_tokens += total_tokens

                    # 成本估算
                    cost = self._estimate_cost(model_name, usage)
                    self.metrics.total_cost += cost

                    logger.debug(
                        f"API 调用成功: {model_name}, "
                        f"tokens: {total_tokens}, "
                        f"耗时: {duration:.2f}s"
                    )

                    return {
                        "response": response,
                        "text": response.content[0].text,
                        "usage": {
                            "input_tokens": usage.input_tokens,
                            "output_tokens": usage.output_tokens,
                            "total_tokens": total_tokens
                        },
                        "cost": cost,
                        "duration": duration
                    }

                except Exception as e:
                    self.metrics.failed_calls += 1
                    self.metrics.retry_count += 1
                    logger.error(f"API 调用失败: {e}")
                    raise

    def _estimate_cost(self, model: str, usage) -> float:
        """
        估算 API 成本

        Args:
            model: 模型名称
            usage: Token 使用情况

        Returns:
            成本（美元）
        """
        # 价格表（每百万 token）
        pricing = {
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
            "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
            "claude-3-opus-20240229": {"input": 15.0, "output": 75.0}
        }

        if model not in pricing:
            return 0.0

        input_cost = (usage.input_tokens / 1_000_000) * pricing[model]["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing[model]["output"]

        return input_cost + output_cost

    async def batch_call(
        self,
        batch_requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量并发调用

        Args:
            batch_requests: 请求列表，每个请求包含 messages 等参数

        Returns:
            响应列表
        """
        logger.info(f"开始批量调用: {len(batch_requests)} 个请求")

        tasks = [
            self.call_with_retry(**request)
            for request in batch_requests
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计失败
        failed = sum(1 for r in results if isinstance(r, Exception))
        if failed > 0:
            logger.warning(f"批量调用: {failed}/{len(results)} 失败")

        return results

    def compress_prompt(
        self,
        text: str,
        max_length: int = 4000,
        strategy: str = "truncate"
    ) -> str:
        """
        压缩提示词

        Args:
            text: 原始文本
            max_length: 最大长度
            strategy: 压缩策略 (truncate/summarize)

        Returns:
            压缩后的文本
        """
        if len(text) <= max_length:
            return text

        if strategy == "truncate":
            # 简单截断
            return text[:max_length] + "..."

        elif strategy == "summarize":
            # TODO: 使用模型总结
            # 暂时使用截断
            return text[:max_length] + "..."

        return text

    def optimize_context_window(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 100000
    ) -> List[Dict[str, str]]:
        """
        优化上下文窗口

        Args:
            messages: 消息列表
            max_tokens: 最大 token 数

        Returns:
            优化后的消息列表
        """
        # 简单实现：保留最近的消息
        total_length = sum(len(msg.get("content", "")) for msg in messages)

        if total_length <= max_tokens * 4:  # 粗略估算 4字符/token
            return messages

        # 保留系统消息和最近的用户消息
        optimized = []
        current_length = 0
        target_length = max_tokens * 4

        for msg in reversed(messages):
            msg_length = len(msg.get("content", ""))
            if current_length + msg_length <= target_length:
                optimized.insert(0, msg)
                current_length += msg_length
            else:
                break

        logger.info(
            f"上下文窗口优化: {len(messages)} → {len(optimized)} 消息"
        )

        return optimized

    async def smart_call(
        self,
        messages: List[Dict[str, str]],
        task_complexity: str = "medium",
        **kwargs
    ) -> Dict[str, Any]:
        """
        智能调用：根据任务复杂度自动选择模型

        Args:
            messages: 消息列表
            task_complexity: 任务复杂度 (simple/medium/complex)
            **kwargs: 其他参数

        Returns:
            API 响应
        """
        # 根据复杂度选择模型
        model_map = {
            "simple": ModelTier.HAIKU,
            "medium": ModelTier.SONNET,
            "complex": ModelTier.OPUS
        }

        model = model_map.get(task_complexity, ModelTier.SONNET)

        logger.debug(f"智能调用: 复杂度={task_complexity}, 模型={model.value}")

        return await self.call_with_retry(messages, model=model, **kwargs)

    def get_metrics(self) -> Dict[str, Any]:
        """获取调用指标"""
        return {
            "total_calls": self.metrics.total_calls,
            "successful_calls": self.metrics.successful_calls,
            "failed_calls": self.metrics.failed_calls,
            "success_rate": self.metrics.success_rate,
            "total_tokens": self.metrics.total_tokens,
            "total_cost": self.metrics.total_cost,
            "avg_duration": self.metrics.avg_duration,
            "retry_count": self.metrics.retry_count
        }

    def reset_metrics(self):
        """重置指标"""
        self.metrics = APICallMetrics()


# 全局实例
_ai_call_manager: Optional[AICallManager] = None


def get_ai_call_manager() -> AICallManager:
    """获取全局 AI 调用管理器"""
    global _ai_call_manager

    if _ai_call_manager is None:
        import os
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        _ai_call_manager = AICallManager(api_key=api_key)

    return _ai_call_manager
