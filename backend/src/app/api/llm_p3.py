"""
LLM API endpoints for unified LLM service access
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.middleware.auth import get_current_user
try:
    from app.models.user import User
except ImportError:
    from app.schemas.user import User
from app.services.llm.router import LLMRouter, RoutingStrategy
from app.services.llm.base import LLMMessage, LLMConfig, MessageRole
from app.services.llm.cost_tracker import CostTracker
from app.services.llm.openai_llm import OpenAILLM
from app.services.llm.anthropic_llm import AnthropicLLM
from fastapi.responses import StreamingResponse
import json
import os

router = APIRouter(prefix="/llm", tags=["llm"])

# Request/Response models
class ChatMessageRequest(BaseModel):
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    messages: List[ChatMessageRequest]
    provider: Optional[str] = Field(None, description="Specific provider (openai, anthropic) or None for auto-routing")
    model: Optional[str] = Field(None, description="Specific model or None for provider default")
    routing_strategy: Optional[str] = Field("balanced", description="Routing strategy: cost_optimized, performance_optimized, balanced, round_robin, fixed")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, description="Sampling temperature (0.0-2.0)")
    stream: bool = Field(False, description="Enable streaming response")
    project_id: Optional[int] = Field(None, description="Project ID for cost tracking")

class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    cost: float
    latency: float
    finish_reason: str

# Initialize services (lazy initialization)
_llm_router = None
_cost_tracker = None

def get_llm_router() -> LLMRouter:
    """Get or create LLM router instance"""
    global _llm_router
    if _llm_router is None:
        providers = {}

        # Initialize OpenAI if API key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            providers["openai"] = OpenAILLM(api_key=openai_key)

        # Initialize Anthropic if API key is available
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            providers["anthropic"] = AnthropicLLM(api_key=anthropic_key)

        if not providers:
            raise RuntimeError("No LLM providers configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")

        # Get default strategy from env or use balanced
        strategy_name = os.getenv("LLM_DEFAULT_STRATEGY", "balanced")
        strategy = RoutingStrategy(strategy_name)

        _llm_router = LLMRouter(providers=providers, strategy=strategy)

    return _llm_router

def get_cost_tracker() -> CostTracker:
    """Get or create cost tracker instance"""
    global _cost_tracker
    if _cost_tracker is None:
        budget_limit = os.getenv("LLM_BUDGET_LIMIT")
        _cost_tracker = CostTracker(
            budget_limit=float(budget_limit) if budget_limit else None
        )
    return _cost_tracker

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a chat request to LLM service with automatic routing
    """
    try:
        router_instance = get_llm_router()
        tracker = get_cost_tracker()

        # Convert request messages to LLMMessage format
        messages = []
        for msg in request.messages:
            role = MessageRole(msg.role.lower())
            messages.append(LLMMessage(role=role, content=msg.content))

        # Create LLM config
        config = LLMConfig(
            model=request.model or "gpt-3.5-turbo",
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        # Check budget if project_id is provided
        if request.project_id:
            budget_status = tracker.get_budget_status()
            if budget_status.get("has_limit") and budget_status.get("is_exceeded"):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Budget limit exceeded. Current: ${budget_status['total_cost']:.4f}"
                )

        # Route and execute chat
        if request.provider:
            # Use specific provider
            response = await router_instance.route_and_chat(
                messages=messages,
                config=config,
                preferred_provider=request.provider
            )
        else:
            # Use auto-routing with specified strategy
            strategy = RoutingStrategy(request.routing_strategy)
            router_instance.strategy = strategy
            response = await router_instance.route_and_chat(
                messages=messages,
                config=config
            )

        # Track usage
        tracker.record_usage(
            provider=response.provider,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            cost=response.cost,
            latency=response.latency,
            user_id=current_user.id,
            project_id=request.project_id
        )

        return ChatResponse(
            content=response.content,
            provider=response.provider,
            model=response.model,
            tokens_used=response.tokens_used,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            cost=response.cost,
            latency=response.latency,
            finish_reason=response.finish_reason
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"LLM service error: {str(e)}")

@router.get("/providers")
async def list_providers(current_user: User = Depends(get_current_user)):
    """
    List available LLM providers and their models
    """
    router_instance = get_llm_router()
    providers_info = {}

    for name, provider in router_instance.providers.items():
        providers_info[name] = {
            "name": name,
            "default_model": provider.default_model,
            "available": True
        }

    return {
        "providers": providers_info,
        "routing_strategies": ["cost_optimized", "performance_optimized", "balanced", "round_robin", "fixed"]
    }

@router.get("/usage/stats")
async def get_usage_stats(
    group_by: str = "provider",
    current_user: User = Depends(get_current_user)
):
    """
    Get usage statistics
    """
    if group_by not in ["provider", "user", "project"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid group_by parameter")

    tracker = get_cost_tracker()

    if group_by == "provider":
        stats = tracker.get_provider_stats()
    elif group_by == "user":
        stats = tracker.get_user_stats(current_user.id)
    else:
        stats = {}

    return {"stats": stats}

@router.get("/usage/top-users")
async def get_top_users(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Get top users by cost
    """
    tracker = get_cost_tracker()
    top_users = tracker.get_top_users(limit=limit)
    return {"top_users": top_users}

@router.get("/usage/top-projects")
async def get_top_projects(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Get top projects by cost
    """
    tracker = get_cost_tracker()
    top_projects = tracker.get_top_projects(limit=limit)
    return {"top_projects": top_projects}

@router.get("/budget/status")
async def get_budget_status(current_user: User = Depends(get_current_user)):
    """
    Get current budget status
    """
    tracker = get_cost_tracker()
    budget_status = tracker.get_budget_status()
    return budget_status
