"""
P3 LLM Service Integration - 增强现有 LLM 调用
为 FieldMind 提供智能路由和成本优化
"""

from typing import List, Dict, Any, Optional
import logging

# 导入 P3 LLM 服务组件
from app.services.llm.router import LLMRouter, RoutingStrategy
from app.services.llm.cost_tracker import CostTracker
from app.services.llm.openai_llm import OpenAILLM
from app.services.llm.anthropic_llm import AnthropicLLM
from app.services.llm.base import LLMMessage, MessageRole

logger = logging.getLogger(__name__)


class FieldMindLLMAdapter:
    """
    FieldMind LLM 适配器

    将 P3 LLM Service 集成到 FieldMind 现有架构中
    兼容 LangChain 接口
    """
    def __init__(self, strategy: str = "cost_optimized", use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化适配器

        Args:
            strategy: 路由策略 (cost_optimized, performance, balanced, smart)
        """
        import os

        # 获取 API keys
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

        # 初始化 LLM 提供商（只初始化有 API key 的）
        self.openai_llm = None
        self.anthropic_llm = None
        providers = {}

        if openai_api_key:
            self.openai_llm = OpenAILLM(api_key=openai_api_key)
            providers["openai"] = self.openai_llm
            logger.info("✅ OpenAI LLM 已初始化")

        if anthropic_api_key:
            self.anthropic_llm = AnthropicLLM(api_key=anthropic_api_key)
            providers["anthropic"] = self.anthropic_llm
            logger.info("✅ Anthropic LLM 已初始化")

        # 初始化成本追踪
        self.cost_tracker = CostTracker()

        # 初始化路由器（需要 providers 参数）
        if providers:
            self.router = LLMRouter(providers=providers, strategy=RoutingStrategy(strategy))
            logger.info(f"✅ P3 LLM 适配器已初始化，策略: {strategy}，提供商: {list(providers.keys())}")
        else:
            self.router = None
            logger.warning("⚠️ 没有可用的 LLM 提供商，请配置 API keys")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        聊天补全 - 兼容现有接口

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 指定模型（可选，不指定则自动路由）
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            {
                "content": "回复内容",
                "model": "使用的模型",
                "usage": {...},
                "cost": {...}
            }
        """
        try:
            # 转换消息格式
            llm_messages = [
                LLMMessage(role=MessageRole(msg["role"]), content=msg["content"])
                for msg in messages
            ]

            # 如果指定了模型，直接使用
            if model:
                provider, model_name = self._parse_model(model)
            else:
                # 使用智能路由选择最优模型
                route_result = self.router.route(llm_messages)
                provider = route_result["provider"]
                model_name = route_result["model"]

            # 选择对应的 LLM 提供商
            if provider == "openai":
                if not self.openai_llm:
                    raise ValueError("OpenAI LLM 未初始化，请检查 OPENAI_API_KEY")
                llm = self.openai_llm
            elif provider == "anthropic":
                if not self.anthropic_llm:
                    raise ValueError("Anthropic LLM 未初始化，请检查 ANTHROPIC_API_KEY")
                llm = self.anthropic_llm
            else:
                raise ValueError(f"不支持的提供商: {provider}")

            # 调用 LLM
            response = await llm.chat(
                messages=llm_messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # 记录成本
            self.cost_tracker.record_usage(
                model=f"{provider}/{model_name}",
                input_tokens=response.get("usage", {}).get("prompt_tokens", 0),
                output_tokens=response.get("usage", {}).get("completion_tokens", 0)
            )

            logger.info(
                f"LLM 调用成功: {provider}/{model_name}, "
                f"成本: ${response.get('cost', {}).get('total_cost', 0):.4f}"
            )

            return {
                "content": response.get("response", ""),
                "model": f"{provider}/{model_name}",
                "usage": response.get("usage", {}),
                "cost": response.get("cost", {})
            }

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise

    def _parse_model(self, model: str) -> tuple:
        """
        解析模型字符串

        Args:
            model: "gpt-4", "claude-3-5-sonnet", "openai/gpt-4"

        Returns:
            (provider, model_name)
        """
        if "/" in model:
            provider, model_name = model.split("/", 1)
            return provider, model_name

        # 根据模型名称推断提供商
        if model.startswith("gpt"):
            return "openai", model
        elif model.startswith("claude"):
            return "anthropic", model
        else:
            return "openai", model

    def get_cost_statistics(self) -> Dict[str, Any]:
        """
        获取成本统计

        Returns:
            {
                "total_cost": 总成本,
                "total_tokens": 总 token 数,
                "request_count": 请求次数,
                "breakdown": 按模型分类的统计
            }
        """
        return self.cost_tracker.get_statistics()

    def set_routing_strategy(self, strategy: str):
        """
        设置路由策略

        Args:
            strategy: cost_optimized, performance, balanced, smart
        """
        self.router.set_strategy(strategy)
        logger.info(f"路由策略已更新: {strategy}")


# 全局实例
_llm_adapter: Optional[FieldMindLLMAdapter] = None


def get_llm_adapter(strategy: str = "cost_optimized") -> FieldMindLLMAdapter:
    """
    获取全局 LLM 适配器实例

    Args:
        strategy: 路由策略

    Returns:
        FieldMindLLMAdapter 实例
    """
    global _llm_adapter

    if _llm_adapter is None:
        _llm_adapter = FieldMindLLMAdapter(strategy=strategy)

    return _llm_adapter


async def enhanced_chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    strategy: str = "cost_optimized"
) -> Dict[str, Any]:
    """
    增强的聊天补全函数 - 可直接在现有代码中使用

    这是一个便捷函数，可以直接替换现有的 OpenAI API 调用

    示例:
        # 原来的代码:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}]
        )

        # 新代码:
        response = await enhanced_chat_completion(
            messages=[{"role": "user", "content": "Hello"}]
        )
        # 自动选择最优模型，追踪成本
    """
    adapter = get_llm_adapter(strategy=strategy)
    return await adapter.chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
