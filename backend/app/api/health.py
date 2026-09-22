"""
健康检查和就绪检查端点
监控数据库、Redis、系统资源状态
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Dict, Any
import time
import psutil
from datetime import datetime

from app.core.database import get_db
from app.core.cache_manager import get_cache_manager

router = APIRouter()


class HealthStatus(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    uptime_seconds: float
    checks: Dict[str, Any]


class ComponentHealth(BaseModel):
    healthy: bool
    latency_ms: float
    details: Dict[str, Any] = {}


# 应用启动时间
START_TIME = time.time()


@router.get("/health", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查端点
    检查所有关键组件的健康状态
    """
    checks = {}
    overall_healthy = True

    # 1. 数据库健康检查
    db_health = await check_database(db)
    checks["database"] = db_health.dict()
    if not db_health.healthy:
        overall_healthy = False

    # 2. Redis健康检查
    redis_health = await check_redis()
    checks["redis"] = redis_health.dict()
    if not redis_health.healthy:
        overall_healthy = False

    # 3. 系统资源检查
    system_health = check_system_resources()
    checks["system"] = system_health.dict()
    if not system_health.healthy:
        overall_healthy = False

    # 4. 磁盘空间检查
    disk_health = check_disk_space()
    checks["disk"] = disk_health.dict()
    if not disk_health.healthy:
        overall_healthy = False

    return HealthStatus(
        status="healthy" if overall_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat() + "Z",
        uptime_seconds=time.time() - START_TIME,
        checks=checks
    )


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: Session = Depends(get_db)):
    """
    就绪检查端点
    用于Kubernetes readiness probe
    """
    try:
        # 检查数据库连接
        db.execute(text("SELECT 1"))

        # 检查Redis连接
        cache_manager = get_cache_manager()
        cache_manager.client.ping()

        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check():
    """
    存活检查端点
    用于Kubernetes liveness probe
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat() + "Z"}


async def check_database(db: Session) -> ComponentHealth:
    """检查数据库健康状态"""
    start = time.time()
    try:
        # 执行简单查询
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        # 获取连接池状态
        engine = db.get_bind()
        pool = engine.pool

        latency = (time.time() - start) * 1000

        return ComponentHealth(
            healthy=True,
            latency_ms=round(latency, 2),
            details={
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total_connections": pool.size() + pool.overflow()
            }
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            healthy=False,
            latency_ms=round(latency, 2),
            details={"error": str(e)}
        )


async def check_redis() -> ComponentHealth:
    """检查Redis健康状态"""
    start = time.time()
    try:
        cache_manager = get_cache_manager()

        # Ping Redis
        cache_manager.client.ping()

        # 获取Redis info
        info = cache_manager.client.info()

        latency = (time.time() - start) * 1000

        return ComponentHealth(
            healthy=True,
            latency_ms=round(latency, 2),
            details={
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
            }
        )
    except Exception as e:
        latency = (time.time() - start) * 1000
        return ComponentHealth(
            healthy=False,
            latency_ms=round(latency, 2),
            details={"error": str(e)}
        )


def check_system_resources() -> ComponentHealth:
    """检查系统资源"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        # 阈值检查
        cpu_healthy = cpu_percent < 90
        memory_healthy = memory.percent < 90

        return ComponentHealth(
            healthy=cpu_healthy and memory_healthy,
            latency_ms=0,
            details={
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory.percent, 2),
                "memory_available_mb": round(memory.available / 1024 / 1024, 2),
                "memory_total_mb": round(memory.total / 1024 / 1024, 2)
            }
        )
    except Exception as e:
        return ComponentHealth(
            healthy=False,
            latency_ms=0,
            details={"error": str(e)}
        )


def check_disk_space() -> ComponentHealth:
    """检查磁盘空间"""
    try:
        disk = psutil.disk_usage('/')

        # 磁盘使用率低于85%为健康
        disk_healthy = disk.percent < 85

        return ComponentHealth(
            healthy=disk_healthy,
            latency_ms=0,
            details={
                "disk_percent": round(disk.percent, 2),
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 2)
            }
        )
    except Exception as e:
        return ComponentHealth(
            healthy=False,
            latency_ms=0,
            details={"error": str(e)}
        )
