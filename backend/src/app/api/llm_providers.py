"""
LLM 提供商管理 API
用户可以查看、配置和测试 LLM 提供商
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.services.multi_provider_llm_manager import get_llm_manager, LLMProvider, RoutingStrategy

router = APIRouter(prefix="/llm-providers", tags=["LLM 提供商管理"])
logger = logging.getLogger(__name__)


class ProviderInfo(BaseModel):
    """提供商信息"""
    name: str = Field(..., description="提供商标识")
    display_name: str = Field(..., description="显示名称")
    is_available: bool = Field(..., description="是否已配置可用")
    default_model: Optional[str] = Field(None, description="默认模型")
    available_models: List[str] = Field(default_factory=list, description="可用模型列表")
    base_url: Optional[str] = Field(None, description="API 端点")


class ConfigGuide(BaseModel):
    """配置指南"""
    provider: str
    display_name: str
    official_website: str
    api_key_guide: str
    recommended_models: List[str]
    features: List[str]
    cost_range: str


class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[Dict[str, str]] = Field(..., description="消息列表")
    provider: Optional[str] = Field(None, description="指定提供商（可选）")
    model: Optional[str] = Field(None, description="指定模型（可选）")
    task_complexity: str = Field("medium", description="任务复杂度：simple/medium/complex")
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2000, gt=0, le=100000)


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    provider: str
    model: str
    usage: Dict[str, int]
    cost_usd: float
    latency_ms: int


class StrategyUpdateRequest(BaseModel):
    """路由策略更新请求"""
    strategy: RoutingStrategy = Field(..., description="路由策略")


@router.get("/", response_model=List[ProviderInfo])
async def get_providers():
    """
    获取所有可用的 LLM 提供商

    返回已配置的提供商列表及其状态
    """
    try:
        manager = get_llm_manager()
        providers = manager.get_available_providers()
        return providers
    except Exception as e:
        logger.error(f"获取提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config-guides", response_model=List[ConfigGuide])
async def get_config_guides():
    """
    获取所有提供商的配置指南

    帮助用户了解如何配置各个提供商
    """
    guides = [
        {
            "provider": "openai",
            "display_name": "OpenAI (GPT)",
            "official_website": "https://platform.openai.com/",
            "api_key_guide": "访问 https://platform.openai.com/api-keys 创建 API Key",
            "recommended_models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            "features": [
                "全球最强大的 GPT-4 模型",
                "响应速度快",
                "支持函数调用",
                "多模态能力（视觉）"
            ],
            "cost_range": "中等（$0.0005 - $0.06 / 1K tokens）"
        },
        {
            "provider": "anthropic",
            "display_name": "Anthropic (Claude)",
            "official_website": "https://console.anthropic.com/",
            "api_key_guide": "访问 https://console.anthropic.com/ 注册并获取 API Key",
            "recommended_models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
            "features": [
                "Claude 3.5 Sonnet 性能优异",
                "支持 200K 超长上下文",
                "安全性和准确性高",
                "适合复杂推理任务"
            ],
            "cost_range": "中等（$0.00025 - $0.075 / 1K tokens）"
        },
        {
            "provider": "deepseek",
            "display_name": "DeepSeek（深度求索）",
            "official_website": "https://platform.deepseek.com/",
            "api_key_guide": "访问 https://platform.deepseek.com/ 注册并获取 API Key",
            "recommended_models": ["deepseek-chat", "deepseek-coder"],
            "features": [
                "国产大模型，性价比极高",
                "中文理解能力强",
                "代码能力出色（deepseek-coder）",
                "响应速度快"
            ],
            "cost_range": "极低（$0.0001 - $0.0002 / 1K tokens）⭐"
        },
        {
            "provider": "kimi",
            "display_name": "Kimi（月之暗面）",
            "official_website": "https://platform.moonshot.cn/",
            "api_key_guide": "访问 https://platform.moonshot.cn/console/api-keys 获取 API Key",
            "recommended_models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
            "features": [
                "国产大模型，超长上下文",
                "支持最长 128K 上下文",
                "中文优化，理解深刻",
                "适合长文本处理"
            ],
            "cost_range": "较低（$0.0012 - $0.006 / 1K tokens）"
        }
    ]
    return guides


@router.post("/chat", response_model=ChatResponse)
async def chat_with_llm(request: ChatRequest):
    """
    使用 LLM 进行对话

    自动选择最合适的提供商，或使用用户指定的提供商
    """
    try:
        manager = get_llm_manager()

        # 选择提供商和模型
        if request.provider and request.model:
            provider = request.provider
            model = request.model
        else:
            provider, model = manager.select_provider(
                task_complexity=request.task_complexity,
                preferred_provider=request.provider
            )

        # 获取 LLM 实例
        if provider not in manager.providers:
            raise HTTPException(
                status_code=400,
                detail=f"提供商 {provider} 未配置，请先配置 API Key"
            )

        llm = manager.providers[provider]

        # 转换消息格式
        from app.services.llm.base import LLMMessage, MessageRole
        llm_messages = [
            LLMMessage(role=MessageRole(msg["role"]), content=msg["content"])
            for msg in request.messages
        ]

        # 调用 LLM
        import time
        start_time = time.time()

        response = await llm.chat(
            messages=llm_messages,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # 计算成本
        usage = response.get("usage", {})
        cost_usd = manager.calculate_cost(
            provider=provider,
            model=model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0)
        )

        return ChatResponse(
            content=response.get("content", ""),
            provider=provider,
            model=model,
            usage=usage,
            cost_usd=round(cost_usd, 6),
            latency_ms=latency_ms
        )

    except Exception as e:
        logger.error(f"LLM 对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy")
async def get_routing_strategy():
    """获取当前的路由策略"""
    manager = get_llm_manager()
    return {
        "strategy": manager.routing_strategy,
        "auto_routing": manager.auto_routing,
        "provider_priority": manager.provider_priority
    }


@router.post("/strategy")
async def update_routing_strategy(request: StrategyUpdateRequest):
    """更新路由策略"""
    try:
        manager = get_llm_manager()
        manager.routing_strategy = request.strategy
        return {
            "message": "路由策略已更新",
            "strategy": manager.routing_strategy
        }
    except Exception as e:
        logger.error(f"更新路由策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_llm_statistics():
    """
    获取 LLM 使用统计

    包括各提供商的使用次数、成本等信息
    """
    # TODO: 从数据库或缓存中获取统计信息
    return {
        "message": "统计功能开发中",
        "total_requests": 0,
        "total_cost_usd": 0.0,
        "providers": {}
    }


@router.post("/test/{provider}")
async def test_provider(provider: str):
    """
    测试指定提供商的连接

    用于验证 API Key 是否配置正确
    """
    try:
        manager = get_llm_manager()

        if provider not in manager.providers:
            raise HTTPException(
                status_code=400,
                detail=f"提供商 {provider} 未配置，请先在 .env 中配置对应的 API Key"
            )

        llm = manager.providers[provider]
        config = manager.provider_configs[provider]

        # 发送测试消息
        from app.services.llm.base import LLMMessage, MessageRole
        test_message = LLMMessage(role=MessageRole.USER, content="Hello")

        response = await llm.chat(
            messages=[test_message],
            model=config["default_model"],
            max_tokens=10
        )

        return {
            "success": True,
            "message": f"提供商 {provider} 连接成功",
            "provider": provider,
            "model": config["default_model"],
            "response_preview": response.get("content", "")[:50]
        }

    except Exception as e:
        logger.error(f"测试提供商 {provider} 失败: {e}")
        return {
            "success": False,
            "message": f"连接失败: {str(e)}",
            "provider": provider
        }
