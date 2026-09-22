"""
LLM 成本统计 API
提供实时的 LLM 使用成本追踪
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.services.llm_adapter import get_llm_adapter

router = APIRouter(prefix="/llm-stats", tags=["LLM Statistics"])
logger = logging.getLogger(__name__)


@router.get("/cost")
async def get_cost_statistics() -> Dict[str, Any]:
    """
    获取 LLM 成本统计

    Returns:
        {
            "total_cost": 0.0,
            "total_tokens": 0,
            "request_count": 0,
            "breakdown": {
                "openai/gpt-4": {...},
                "anthropic/claude-3-5-sonnet": {...}
            },
            "daily_cost": 0.0,
            "budget_usage_percent": 0.0
        }
    """
    try:
        adapter = get_llm_adapter()
        stats = adapter.get_cost_statistics()

        # 添加预算使用百分比
        import os
        daily_budget = float(os.getenv("DAILY_BUDGET_USD", 100.0))
        budget_usage_percent = (stats.get("total_cost", 0) / daily_budget) * 100 if daily_budget > 0 else 0

        return {
            **stats,
            "daily_budget": daily_budget,
            "budget_usage_percent": round(budget_usage_percent, 2)
        }

    except Exception as e:
        logger.error(f"获取成本统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategy")
async def set_routing_strategy(strategy: str) -> Dict[str, str]:
    """
    设置 LLM 路由策略

    Args:
        strategy: cost_optimized, performance, balanced, smart

    Returns:
        {"status": "success", "strategy": "cost_optimized"}
    """
    valid_strategies = ["cost_optimized", "performance", "balanced", "smart"]

    if strategy not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"无效的策略。可选: {', '.join(valid_strategies)}"
        )

    try:
        adapter = get_llm_adapter()
        adapter.set_routing_strategy(strategy)

        return {
            "status": "success",
            "strategy": strategy,
            "message": f"路由策略已更新为 {strategy}"
        }

    except Exception as e:
        logger.error(f"设置路由策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy")
async def get_routing_strategy() -> Dict[str, str]:
    """
    获取当前 LLM 路由策略

    Returns:
        {"strategy": "cost_optimized"}
    """
    try:
        adapter = get_llm_adapter()
        return {
            "strategy": adapter.router.strategy
        }

    except Exception as e:
        logger.error(f"获取路由策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
