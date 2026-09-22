"""
API 管理接口
提供 API 网关的管理和监控功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.api_gateway import api_gateway
from app.database import get_db

router = APIRouter(prefix="/api-management", tags=["API 管理"])


# ===== Pydantic 模型 =====


class GatewayStats(BaseModel):
    """网关统计信息"""

    total_requests: int
    avg_response_time: float
    error_rate: float
    requests_by_endpoint: Dict[str, int]
    requests_by_status: Dict[str, int]


class APIMetric(BaseModel):
    """API 指标"""

    endpoint: str
    total_calls: int
    avg_response_time: float
    error_rate: float
    last_called: Optional[str]


class RequestLog(BaseModel):
    """请求日志"""

    timestamp: str
    method: str
    path: str
    client_ip: str
    status_code: int
    duration: float
    error: Optional[str] = None


class RateLimitReset(BaseModel):
    """限流重置请求"""

    key: str = Field(..., description="限流键（IP或用户ID）")


class GatewayConfig(BaseModel):
    """网关配置"""

    enabled: bool = Field(..., description="是否启用网关")
    rate_limit_requests: int = Field(100, description="时间窗口内最大请求数")
    rate_limit_window: int = Field(60, description="时间窗口（秒）")


# ===== API 端点 =====


@router.get("/stats", response_model=Dict[str, Any])
async def get_gateway_stats():
    """
    获取网关统计信息

    返回:
    - 总请求数
    - 平均响应时间
    - 错误率
    - 按端点分组的请求数
    - 按状态码分组的请求数
    """
    try:
        stats = api_gateway.get_stats()
        return {
            "code": 200,
            "message": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}",
        )


@router.get("/metrics", response_model=Dict[str, Any])
async def get_api_metrics(endpoint: Optional[str] = None):
    """
    获取 API 指标

    Args:
        endpoint: 可选，指定端点。不提供则返回所有端点

    返回:
    - 调用次数
    - 平均响应时间
    - 错误率
    - 最后调用时间
    """
    try:
        metrics = api_gateway.monitor.get_metrics(endpoint)
        return {
            "code": 200,
            "message": "success",
            "data": metrics,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取指标失败: {str(e)}",
        )


@router.get("/logs", response_model=Dict[str, Any])
async def get_request_logs(limit: int = 100):
    """
    获取最近的请求日志

    Args:
        limit: 返回数量，默认 100，最大 1000
    """
    if limit > 1000:
        limit = 1000

    try:
        logs = api_gateway.get_recent_logs(limit)
        return {
            "code": 200,
            "message": "success",
            "data": {"logs": logs, "count": len(logs)},
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日志失败: {str(e)}",
        )


@router.post("/rate-limit/reset", response_model=Dict[str, Any])
async def reset_rate_limit(request: RateLimitReset):
    """
    重置指定键的限流

    Args:
        key: 限流键（IP 地址或用户 ID）

    用途:
    - 手动解除某个 IP 的限流
    - 重置用户的请求配额
    """
    try:
        api_gateway.reset_rate_limit(request.key)
        return {
            "code": 200,
            "message": f"已重置 {request.key} 的限流",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置限流失败: {str(e)}",
        )


@router.get("/config", response_model=Dict[str, Any])
async def get_gateway_config():
    """
    获取网关配置

    返回当前网关的配置信息
    """
    return {
        "code": 200,
        "message": "success",
        "data": {
            "enabled": api_gateway.enabled,
            "rate_limit_requests": 100,  # 从配置读取
            "rate_limit_window": 60,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.put("/config", response_model=Dict[str, Any])
async def update_gateway_config(config: GatewayConfig):
    """
    更新网关配置

    Args:
        enabled: 是否启用网关
        rate_limit_requests: 时间窗口内最大请求数
        rate_limit_window: 时间窗口（秒）
    """
    try:
        api_gateway.enabled = config.enabled
        # TODO: 更新限流配置

        return {
            "code": 200,
            "message": "配置已更新",
            "data": config.dict(),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}",
        )


@router.get("/health", response_model=Dict[str, Any])
async def gateway_health_check():
    """
    网关健康检查

    返回网关服务的健康状态
    """
    return {
        "code": 200,
        "message": "success",
        "data": {
            "status": "healthy" if api_gateway.enabled else "disabled",
            "timestamp": datetime.now().isoformat(),
            "uptime": "N/A",  # TODO: 计算运行时间
        },
    }


@router.get("/endpoints", response_model=Dict[str, Any])
async def list_endpoints():
    """
    列出所有已注册的 API 端点

    返回系统中所有可用的 API 端点及其信息
    """
    # TODO: 从 FastAPI app 中提取所有路由
    from app.main import app

    endpoints = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                endpoints.append(
                    {
                        "method": method,
                        "path": route.path,
                        "name": route.name,
                        "tags": getattr(route, "tags", []),
                    }
                )

    return {
        "code": 200,
        "message": "success",
        "data": {"endpoints": endpoints, "total": len(endpoints)},
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/errors", response_model=Dict[str, Any])
async def get_recent_errors(limit: int = 50):
    """
    获取最近的错误日志

    Args:
        limit: 返回数量，默认 50
    """
    try:
        all_logs = api_gateway.get_recent_logs(1000)
        error_logs = [log for log in all_logs if log.get("status_code", 200) >= 400]

        return {
            "code": 200,
            "message": "success",
            "data": {"errors": error_logs[-limit:], "count": len(error_logs)},
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取错误日志失败: {str(e)}",
        )


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics():
    """
    获取性能指标

    返回系统性能相关的指标:
    - 最慢的端点
    - 最常调用的端点
    - 平均响应时间趋势
    """
    try:
        metrics = api_gateway.monitor.get_metrics()

        # 按响应时间排序
        sorted_by_time = sorted(
            metrics.items(),
            key=lambda x: x[1].get("avg_response_time", 0),
            reverse=True,
        )

        # 按调用次数排序
        sorted_by_calls = sorted(
            metrics.items(), key=lambda x: x[1].get("total_calls", 0), reverse=True
        )

        return {
            "code": 200,
            "message": "success",
            "data": {
                "slowest_endpoints": [
                    {"endpoint": k, **v} for k, v in sorted_by_time[:10]
                ],
                "most_called_endpoints": [
                    {"endpoint": k, **v} for k, v in sorted_by_calls[:10]
                ],
                "overall_avg_response_time": (
                    sum(m.get("avg_response_time", 0) for m in metrics.values())
                    / len(metrics)
                    if metrics
                    else 0
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能指标失败: {str(e)}",
        )
