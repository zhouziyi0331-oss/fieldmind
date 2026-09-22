"""
P3 多提供商 LLM 管理器
支持用户自主配置 OpenAI、Claude、DeepSeek、Kimi
"""

import os
import logging
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    KIMI = "kimi"


class RoutingStrategy(str, Enum):
    """路由策略"""
    COST_OPTIMIZED = "cost_optimized"  # 成本优化
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # 性能优先
    BALANCED = "balanced"  # 平衡


class MultiProviderLLMManager:
    """
    多提供商 LLM 管理器

    根据用户配置自动初始化可用的提供商
    支持智能路由和成本追踪
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """初始化管理器，自动检测已配置的提供商"""
        self.providers: Dict[str, Any] = {}
        self.provider_configs: Dict[str, Dict] = {}

        # 加载配置并初始化提供商
        self._load_configurations()
        self._initialize_providers()

        # 加载路由策略
        self.routing_strategy = os.getenv("P3_ROUTING_STRATEGY", "balanced")
        self.auto_routing = os.getenv("P3_AUTO_ROUTING", "true").lower() == "true"

        # 提供商优先级
        priority_str = os.getenv("P3_PROVIDER_PRIORITY", "deepseek,kimi,openai,anthropic")
        self.provider_priority = [p.strip() for p in priority_str.split(",")]

        logger.info(f"✅ 多提供商 LLM 管理器已初始化")
        logger.info(f"   可用提供商: {list(self.providers.keys())}")
        logger.info(f"   路由策略: {self.routing_strategy}")
        logger.info(f"   优先级: {self.provider_priority}")

    def _load_configurations(self):
        """加载所有提供商的配置"""

        # OpenAI 配置
        if os.getenv("OPENAI_API_KEY"):
            self.provider_configs["openai"] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "default_model": os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
                "models": ["gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "cost_per_1k_tokens": {
                    "gpt-4": {"input": 0.03, "output": 0.06},
                    "gpt-4o": {"input": 0.005, "output": 0.015},
                    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
                    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
                }
            }
            logger.info("✓ OpenAI 配置已加载")

        # Anthropic (Claude) 配置
        if os.getenv("ANTHROPIC_API_KEY"):
            self.provider_configs["anthropic"] = {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
                "default_model": os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20241022"),
                "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
                "cost_per_1k_tokens": {
                    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
                    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
                    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
                }
            }
            logger.info("✓ Anthropic (Claude) 配置已加载")

        # DeepSeek 配置（国产）
        if os.getenv("DEEPSEEK_API_KEY"):
            self.provider_configs["deepseek"] = {
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                "default_model": os.getenv("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat"),
                "models": ["deepseek-chat", "deepseek-coder"],
                "cost_per_1k_tokens": {
                    "deepseek-chat": {"input": 0.0001, "output": 0.0002},  # 极低成本
                    "deepseek-coder": {"input": 0.0001, "output": 0.0002},
                }
            }
            logger.info("✓ DeepSeek 配置已加载（国产，性价比极高）")

        # Kimi (Moonshot) 配置（国产）
        if os.getenv("KIMI_API_KEY"):
            self.provider_configs["kimi"] = {
                "api_key": os.getenv("KIMI_API_KEY"),
                "base_url": os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
                "default_model": os.getenv("KIMI_DEFAULT_MODEL", "moonshot-v1-8k"),
                "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                "cost_per_1k_tokens": {
                    "moonshot-v1-8k": {"input": 0.0012, "output": 0.0012},
                    "moonshot-v1-32k": {"input": 0.0024, "output": 0.0024},
                    "moonshot-v1-128k": {"input": 0.006, "output": 0.006},
                }
            }
            logger.info("✓ Kimi (Moonshot) 配置已加载（国产，超长上下文）")

    def _initialize_providers(self):
        """初始化已配置的提供商"""
        from app.services.llm.openai_llm import OpenAILLM
        from app.services.llm.anthropic_llm import AnthropicLLM

        # 初始化 OpenAI
        if "openai" in self.provider_configs:
            try:
                config = self.provider_configs["openai"]
                self.providers["openai"] = OpenAILLM(
                    api_key=config["api_key"],
                    base_url=config.get("base_url")
                )
                logger.info("✅ OpenAI LLM 已初始化")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI 初始化失败: {e}")

        # 初始化 Anthropic
        if "anthropic" in self.provider_configs:
            try:
                config = self.provider_configs["anthropic"]
                self.providers["anthropic"] = AnthropicLLM(
                    api_key=config["api_key"],
                    base_url=config.get("base_url")
                )
                logger.info("✅ Anthropic (Claude) LLM 已初始化")
            except Exception as e:
                logger.warning(f"⚠️ Anthropic 初始化失败: {e}")

        # 初始化 DeepSeek（使用 OpenAI 兼容接口）
        if "deepseek" in self.provider_configs:
            try:
                config = self.provider_configs["deepseek"]
                self.providers["deepseek"] = OpenAILLM(
                    api_key=config["api_key"],
                    base_url=config["base_url"]
                )
                logger.info("✅ DeepSeek LLM 已初始化")
            except Exception as e:
                logger.warning(f"⚠️ DeepSeek 初始化失败: {e}")

        # 初始化 Kimi（使用 OpenAI 兼容接口）
        if "kimi" in self.provider_configs:
            try:
                config = self.provider_configs["kimi"]
                self.providers["kimi"] = OpenAILLM(
                    api_key=config["api_key"],
                    base_url=config["base_url"]
                )
                logger.info("✅ Kimi (Moonshot) LLM 已初始化")
            except Exception as e:
                logger.warning(f"⚠️ Kimi 初始化失败: {e}")

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """获取所有可用的提供商信息"""
        providers_info = []

        for provider_name, config in self.provider_configs.items():
            providers_info.append({
                "name": provider_name,
                "display_name": self._get_display_name(provider_name),
                "is_available": provider_name in self.providers,
                "default_model": config.get("default_model"),
                "available_models": config.get("models", []),
                "base_url": config.get("base_url"),
            })

        return providers_info

    def _get_display_name(self, provider: str) -> str:
        """获取提供商的显示名称"""
        names = {
            "openai": "OpenAI (GPT)",
            "anthropic": "Anthropic (Claude)",
            "deepseek": "DeepSeek（深度求索）",
            "kimi": "Kimi（月之暗面）",
        }
        return names.get(provider, provider)

    def select_provider(self, task_complexity: str = "medium", preferred_provider: Optional[str] = None) -> tuple[str, str]:
        """
        智能选择提供商和模型

        Args:
            task_complexity: 任务复杂度 (simple, medium, complex)
            preferred_provider: 用户指定的提供商（优先使用）

        Returns:
            (provider_name, model_name)
        """

        # 如果用户指定了提供商，优先使用
        if preferred_provider and preferred_provider in self.providers:
            config = self.provider_configs[preferred_provider]
            return preferred_provider, config["default_model"]

        # 根据策略选择
        if self.routing_strategy == "cost_optimized":
            return self._select_cheapest_provider(task_complexity)
        elif self.routing_strategy == "performance_optimized":
            return self._select_best_provider(task_complexity)
        else:  # balanced
            return self._select_balanced_provider(task_complexity)

    def _select_cheapest_provider(self, task_complexity: str) -> tuple[str, str]:
        """选择成本最低的提供商"""
        # 简单任务：优先国产（DeepSeek 最便宜）
        if task_complexity == "simple":
            if "deepseek" in self.providers:
                return "deepseek", "deepseek-chat"
            if "kimi" in self.providers:
                return "kimi", "moonshot-v1-8k"

        # 中等任务：GPT-4o-mini 或 Claude Haiku
        elif task_complexity == "medium":
            if "openai" in self.providers:
                return "openai", "gpt-4o-mini"
            if "anthropic" in self.providers:
                return "anthropic", "claude-3-haiku-20240307"

        # 复杂任务：Claude Sonnet 或 GPT-4o
        else:  # complex
            if "anthropic" in self.providers:
                return "anthropic", "claude-3-5-sonnet-20241022"
            if "openai" in self.providers:
                return "openai", "gpt-4o"

        # 回退到第一个可用的提供商
        return self._get_first_available_provider()

    def _select_best_provider(self, task_complexity: str) -> tuple[str, str]:
        """选择性能最好的提供商"""
        # 简单任务：GPT-4o-mini 或 DeepSeek
        if task_complexity == "simple":
            if "openai" in self.providers:
                return "openai", "gpt-4o-mini"
            if "deepseek" in self.providers:
                return "deepseek", "deepseek-chat"

        # 中等任务：Claude Sonnet 或 GPT-4o
        elif task_complexity == "medium":
            if "anthropic" in self.providers:
                return "anthropic", "claude-3-5-sonnet-20241022"
            if "openai" in self.providers:
                return "openai", "gpt-4o"

        # 复杂任务：Claude Opus 或 GPT-4
        else:  # complex
            if "anthropic" in self.providers:
                return "anthropic", "claude-3-opus-20240229"
            if "openai" in self.providers:
                return "openai", "gpt-4"

        return self._get_first_available_provider()

    def _select_balanced_provider(self, task_complexity: str) -> tuple[str, str]:
        """平衡选择（兼顾性能和成本）"""
        # 简单任务：DeepSeek
        if task_complexity == "simple":
            if "deepseek" in self.providers:
                return "deepseek", "deepseek-chat"
            if "kimi" in self.providers:
                return "kimi", "moonshot-v1-8k"

        # 中等任务：GPT-4o-mini 或 Kimi
        elif task_complexity == "medium":
            if "openai" in self.providers:
                return "openai", "gpt-4o-mini"
            if "kimi" in self.providers:
                return "kimi", "moonshot-v1-32k"

        # 复杂任务：Claude Sonnet 或 GPT-4o
        else:  # complex
            if "anthropic" in self.providers:
                return "anthropic", "claude-3-5-sonnet-20241022"
            if "openai" in self.providers:
                return "openai", "gpt-4o"

        return self._get_first_available_provider()

    def _get_first_available_provider(self) -> tuple[str, str]:
        """获取第一个可用的提供商"""
        # 按优先级顺序查找
        for provider_name in self.provider_priority:
            if provider_name in self.providers:
                config = self.provider_configs[provider_name]
                return provider_name, config["default_model"]

        # 如果优先级列表中没有，返回第一个可用的
        if self.providers:
            provider_name = list(self.providers.keys())[0]
            config = self.provider_configs[provider_name]
            return provider_name, config["default_model"]

        raise ValueError("没有可用的 LLM 提供商，请配置至少一个提供商的 API Key")

    def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        计算 LLM 调用成本

        Returns:
            成本（美元）
        """
        if provider not in self.provider_configs:
            return 0.0

        costs = self.provider_configs[provider].get("cost_per_1k_tokens", {}).get(model)
        if not costs:
            return 0.0

        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]

        return input_cost + output_cost


# 全局单例
_manager_instance: Optional[MultiProviderLLMManager] = None


def get_llm_manager() -> MultiProviderLLMManager:
    """获取 LLM 管理器单例"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MultiProviderLLMManager()
    return _manager_instance
