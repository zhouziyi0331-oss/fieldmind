"""
增强的健康检查和系统状态监控
提供详细的系统健康状态、依赖服务检查和性能指标
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.services.cache_service import cache
from app.schemas.response import success_response

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.start_time = time.time()

    def check_database(self, db: Session) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            start = time.time()
            db.execute(text("SELECT 1"))
            latency = (time.time() - start) * 1000  # 毫秒

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "details": {"message": "Database connection OK"}
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def check_cache(self) -> Dict[str, Any]:
        """检查缓存服务"""
        try:
            # 测试缓存读写
            test_key = "_health_check_"
            test_value = {"timestamp": time.time()}

            cache.set(test_key, test_value, ttl=10)
            result = cache.get(test_key)

            if result and result.get("timestamp") == test_value["timestamp"]:
                stats = cache.get_stats()
                return {
                    "status": "healthy",
                    "backend": stats.get("backend", "unknown"),
                    "details": stats
                }
            else:
                return {
                    "status": "degraded",
                    "details": {"message": "Cache read/write test failed"}
                }

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024 ** 3)
            total_gb = disk.total / (1024 ** 3)
            percent_used = disk.percent

            status = "healthy"
            if percent_used > 90:
                status = "critical"
            elif percent_used > 80:
                status = "warning"

            return {
                "status": status,
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "percent_used": percent_used,
                "details": {
                    "message": f"{free_gb:.1f}GB free of {total_gb:.1f}GB"
                }
            }
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return {
                "status": "unknown",
                "error": str(e)
            }

    def check_memory(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024 ** 3)
            available_gb = memory.available / (1024 ** 3)
            percent_used = memory.percent

            status = "healthy"
            if percent_used > 90:
                status = "critical"
            elif percent_used > 80:
                status = "warning"

            return {
                "status": status,
                "total_gb": round(total_gb, 2),
                "available_gb": round(available_gb, 2),
                "percent_used": percent_used,
                "details": {
                    "message": f"{available_gb:.1f}GB available of {total_gb:.1f}GB"
                }
            }
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return {
                "status": "unknown",
                "error": str(e)
            }

    def check_cpu(self) -> Dict[str, Any]:
        """检查 CPU 使用"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            status = "healthy"
            if cpu_percent > 90:
                status = "critical"
            elif cpu_percent > 80:
                status = "warning"

            return {
                "status": status,
                "percent_used": cpu_percent,
                "cpu_count": cpu_count,
                "details": {
                    "message": f"{cpu_percent}% used on {cpu_count} CPUs"
                }
            }
        except Exception as e:
            logger.error(f"CPU check failed: {e}")
            return {
                "status": "unknown",
                "error": str(e)
            }

    def get_uptime(self) -> float:
        """获取运行时间（秒）"""
        return time.time() - self.start_time


# 全局健康检查器实例
health_checker = HealthChecker()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    基础健康检查（快速）
    用于负载均衡器和 Docker 健康检查
    """
    try:
        # 只检查数据库连接
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    详细健康检查
    包含所有依赖服务和系统资源
    """
    start_time = time.time()

    # 检查所有组件
    checks = {
        "database": health_checker.check_database(db),
        "cache": health_checker.check_cache(),
        "disk_space": health_checker.check_disk_space(),
        "memory": health_checker.check_memory(),
        "cpu": health_checker.check_cpu(),
    }

    # 计算总体状态
    overall_status = "healthy"
    critical_checks = [name for name, check in checks.items() if check.get("status") == "critical"]
    unhealthy_checks = [name for name, check in checks.items() if check.get("status") == "unhealthy"]
    warning_checks = [name for name, check in checks.items() if check.get("status") == "warning"]

    if critical_checks or unhealthy_checks:
        overall_status = "unhealthy"
    elif warning_checks:
        overall_status = "degraded"

    duration = (time.time() - start_time) * 1000  # 毫秒

    return success_response(data={
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": round(health_checker.get_uptime(), 2),
        "check_duration_ms": round(duration, 2),
        "checks": checks,
        "summary": {
            "critical": critical_checks,
            "unhealthy": unhealthy_checks,
            "warning": warning_checks,
        }
    })


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    就绪检查（Kubernetes Readiness Probe）
    检查服务是否准备好接收流量
    """
    try:
        # 检查关键依赖
        db.execute(text("SELECT 1"))

        # 可以添加更多检查，如：
        # - 必需的配置是否加载
        # - 必需的表是否存在
        # - 必需的缓存是否初始化

        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


@router.get("/health/live")
async def liveness_check():
    """
    存活检查（Kubernetes Liveness Probe）
    检查服务是否仍在运行
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": round(health_checker.get_uptime(), 2)
    }


@router.get("/status")
async def system_status():
    """
    系统状态概览
    提供系统运行时信息
    """
    from app.config import settings

    return success_response(data={
        "application": {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": round(health_checker.get_uptime(), 2),
        },
        "system": {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "memory_used_percent": psutil.virtual_memory().percent,
            "disk_used_percent": psutil.disk_usage('/').percent,
        },
        "services": {
            "cache_enabled": cache.enabled,
            "cache_backend": cache.get_stats().get("backend", "unknown"),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
