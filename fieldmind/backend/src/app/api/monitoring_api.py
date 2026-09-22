"""
监控 API

提供系统监控、性能指标、健康检查端点
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.performance_monitor import get_monitor, BusinessMetricsCollector

router = APIRouter(prefix="/api/v1/monitoring", tags=["监控"])
logger = logging.getLogger(__name__)


# =====================================================
# Schemas
# =====================================================

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    uptime_seconds: float
    services: Dict[str, bool]


class MetricsResponse(BaseModel):
    """指标响应"""
    api_metrics: Dict[str, Any]
    file_processing: Dict[str, Any]
    system: Dict[str, Any]
    timestamp: str


# =====================================================
# API 1: 健康检查
# =====================================================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查端点

    检查系统各组件状态
    """
    monitor = get_monitor()
    system_metrics = monitor.get_system_metrics()

    # 检查数据库连接
    db_healthy = True
    try:
        db.execute("SELECT 1")
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        db_healthy = False

    # 检查外部服务（简单检查）
    services = {
        "database": db_healthy,
        "monitor": True,
        "api": True
    }

    # 判断整体状态
    overall_status = "healthy" if all(services.values()) else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version="1.0.0",
        uptime_seconds=system_metrics.get("uptime_seconds", 0),
        services=services
    )


# =====================================================
# API 2: 性能指标
# =====================================================

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    获取性能指标

    包括API调用、文件处理、系统资源等指标
    """
    monitor = get_monitor()
    return monitor.get_all_metrics()


# =====================================================
# API 3: 系统资源
# =====================================================

@router.get("/system-resources")
async def get_system_resources():
    """
    获取系统资源使用情况

    包括CPU、内存、磁盘等
    """
    import psutil
    import os

    try:
        process = psutil.Process(os.getpid())

        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=0.1),
                "count": psutil.cpu_count()
            },
            "memory": {
                "process_mb": process.memory_info().rss / (1024 * 1024),
                "process_percent": process.memory_percent(),
                "system_percent": psutil.virtual_memory().percent,
                "system_available_mb": psutil.virtual_memory().available / (1024 * 1024)
            },
            "disk": {
                "percent": psutil.disk_usage('/').percent,
                "free_gb": psutil.disk_usage('/').free / (1024 ** 3)
            },
            "process": {
                "threads": process.num_threads(),
                "open_files": len(process.open_files())
            }
        }

    except Exception as e:
        logger.error(f"获取系统资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# API 4: API调用统计
# =====================================================

@router.get("/api-stats")
async def get_api_stats():
    """
    获取API调用统计

    按端点分组的调用次数、响应时间、错误率
    """
    monitor = get_monitor()
    api_metrics = monitor.get_api_metrics()

    # 排序：按调用次数降序
    sorted_metrics = sorted(
        api_metrics.items(),
        key=lambda x: x[1].get("calls", 0),
        reverse=True
    )

    return {
        "total_endpoints": len(api_metrics),
        "endpoints": dict(sorted_metrics),
        "summary": {
            "total_calls": sum(m.get("calls", 0) for m in api_metrics.values()),
            "avg_response_time": sum(m.get("avg_time_ms", 0) for m in api_metrics.values()) / len(api_metrics) if api_metrics else 0
        }
    }
