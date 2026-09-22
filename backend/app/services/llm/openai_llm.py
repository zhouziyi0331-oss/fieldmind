"""
OpenAI LLM 实现

支持 GPT-4, GPT-3.5-turbo 等模型
"""
from typing import List, Optional, AsyncIterator, Dict, Any
import asyncio
import logging

from app.services.llm.base import (
    BaseLLM,
    LLMMessage,
    LLMResponse,
    LLMConfig,
    MessageRole
)

logger = logging.getLogger(__name__)


class OpenAILLM(BaseLLM):
    """OpenAI LLM 实现"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        default_config: Optional[LLMConfig] = None
    ):
        super().__init__(api_key, base_url, default_config)
        self._client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return "gpt-3.5-turbo"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4-turbo-preview",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]

    def get_model_cost(self, model: str) -> Dict[str, float]:
        """
        获取模型成本（美元/1K tokens）

        数据来源：OpenAI 官方定价（2024）
        """
        costs = {
            "gpt-4-turbo-preview": {"prompt": 0.01, "completion": 0.03},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
            "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
        }
        return costs.get(model, {"prompt": 0.0, "completion": 0.0})

    def _get_client(self):
        """获取或创建 OpenAI 客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url

                self._client = AsyncOpenAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "OpenAI library not installed. "
                    "Install with: pip install openai"
                )
        return self._client

    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """格式化消息为 OpenAI 格式"""
        formatted = []
        for msg in messages:
            formatted_msg = {
                "role": msg.role.value,
                "content": msg.content
            }
            if msg.name:
                formatted_msg["name"] = msg.name
            if msg.function_call:
                formatted_msg["function_call"] = msg.function_call
            formatted.append(formatted_msg)
        return formatted

    async def chat(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        config = config or self.default_config
        client = self._get_client()

        # 准备请求参数
        request_params = {
            "model": config.model,
            "messages": self._format_messages(messages),
            "temperature": config.temperature,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
        }

        if config.max_tokens:
            request_params["max_tokens"] = config.max_tokens
        if config.stop:
            request_params["stop"] = config.stop

        # 添加额外参数
        request_params.update(kwargs)

        # 发送请求（带重试）
        async def _make_request():
            start_time = asyncio.get_event_loop().time()

            response = await client.chat.completions.create(**request_params)

            latency = asyncio.get_event_loop().time() - start_time

            # 提取响应数据
            choice = response.choices[0]
            usage = response.usage

            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

            # 计算成本
            cost = self.calculate_cost(
                config.model,
                prompt_tokens,
                completion_tokens
            )

            # 更新统计
            self.update_usage(total_tokens, cost)

            return LLMResponse(
                content=choice.message.content or "",
                model=response.model,
                provider=self.provider_name,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency=latency,
                finish_reason=choice.finish_reason,
                metadata={
                    "response_id": response.id,
                    "created": response.created,
                }
            )

        try:
            return await self._retry_with_backoff(
                _make_request,
                max_attempts=config.retry_attempts
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """流式聊天请求"""
        config = config or self.default_config
        client = self._get_client()

        # 准备请求参数
        request_params = {
            "model": config.model,
            "messages": self._format_messages(messages),
            "temperature": config.temperature,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "stream": True,
        }

        if config.max_tokens:
            request_params["max_tokens"] = config.max_tokens
        if config.stop:
            request_params["stop"] = config.stop

        request_params.update(kwargs)

        try:
            stream = await client.chat.completions.create(**request_params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
