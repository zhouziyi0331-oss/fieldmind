"""
Anthropic Claude LLM 实现

支持 Claude 3.5 Sonnet, Claude 3 Opus 等模型
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


class AnthropicLLM(BaseLLM):
    """Anthropic Claude LLM 实现"""

    def __init__(self,
        api_key: str,
        base_url: Optional[str] = None,
        default_config: Optional[LLMConfig] = None,


        use_workflow_engine: bool = True):
        super().__init__(api_key, base_url, default_config)
        self._client = None

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    @property
    def supported_models(self) -> List[str]:
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def get_model_cost(self, model: str) -> Dict[str, float]:
        """
        获取模型成本（美元/1M tokens）

        数据来源：Anthropic 官方定价（2024）
        """
        costs = {
            "claude-3-5-sonnet-20241022": {"prompt": 3.0, "completion": 15.0},
            "claude-3-opus-20240229": {"prompt": 15.0, "completion": 75.0},
            "claude-3-sonnet-20240229": {"prompt": 3.0, "completion": 15.0},
            "claude-3-haiku-20240307": {"prompt": 0.25, "completion": 1.25},
        }
        # 转换为 1K tokens 的价格
        model_costs = costs.get(model, {"prompt": 0.0, "completion": 0.0})
        return {
            "prompt": model_costs["prompt"] / 1000.0,
            "completion": model_costs["completion"] / 1000.0
        }

    def _get_client(self):
        """获取或创建 Anthropic 客户端"""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Anthropic library not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    def _format_messages(self, messages: List[LLMMessage]) -> tuple:
        """
        格式化消息为 Anthropic 格式

        Returns:
            (system_prompt, formatted_messages)
        """
        system_prompt = None
        formatted = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            else:
                formatted.append({
                    "role": "user" if msg.role == MessageRole.USER else "assistant",
                    "content": msg.content
                })

        return system_prompt, formatted

    async def chat(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        config = config or self.default_config
        client = self._get_client()

        system_prompt, formatted_messages = self._format_messages(messages)

        # 准备请求参数
        request_params = {
            "model": config.model,
            "messages": formatted_messages,
            "max_tokens": config.max_tokens or 4096,
            "temperature": config.temperature,
            "top_p": config.top_p,
        }

        if system_prompt:
            request_params["system"] = system_prompt
        if config.stop:
            request_params["stop_sequences"] = config.stop

        # 添加额外参数
        request_params.update(kwargs)

        # 发送请求（带重试）
        async def _make_request():
            start_time = asyncio.get_event_loop().time()

            response = await client.messages.create(**request_params)

            latency = asyncio.get_event_loop().time() - start_time

            # 提取响应数据
            content = response.content[0].text if response.content else ""
            usage = response.usage

            prompt_tokens = usage.input_tokens
            completion_tokens = usage.output_tokens
            total_tokens = prompt_tokens + completion_tokens

            # 计算成本
            cost = self.calculate_cost(
                config.model,
                prompt_tokens,
                completion_tokens
            )

            # 更新统计
            self.update_usage(total_tokens, cost)

            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.provider_name,
                tokens_used=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost,
                latency=latency,
                finish_reason=response.stop_reason,
                metadata={
                    "response_id": response.id,
                    "type": response.type,
                }
            )

        try:
            return await self._retry_with_backoff(
                _make_request,
                max_attempts=config.retry_attempts
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
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

        system_prompt, formatted_messages = self._format_messages(messages)

        # 准备请求参数
        request_params = {
            "model": config.model,
            "messages": formatted_messages,
            "max_tokens": config.max_tokens or 4096,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": True,
        }

        if system_prompt:
            request_params["system"] = system_prompt
        if config.stop:
            request_params["stop_sequences"] = config.stop

        request_params.update(kwargs)

        try:
            async with client.messages.stream(**request_params) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        简化的生成接口，用于知识蒸馏等场景

        Args:
            prompt: 提示文本
            response_format: 响应格式 ("text" 或 "json")
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            生成的文本内容
        """
        messages = [
            LLMMessage(role=MessageRole.USER, content=prompt)
        ]

        config = LLMConfig(
            model=self.default_config.model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # 如果需要 JSON 格式，在系统提示中说明
        if response_format == "json":
            system_message = LLMMessage(
                role=MessageRole.SYSTEM,
                content="You must respond with valid JSON only. Do not include any explanatory text outside the JSON structure."
            )
            messages.insert(0, system_message)

        response = await self.chat(messages, config, **kwargs)
        return response.content




        # WorkflowEngine 集成


        self.use_workflow_engine = use_workflow_engine


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)

