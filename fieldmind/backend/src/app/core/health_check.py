"""
健康检查系统 - Week 4 Day 3-4
系统健康状态检查、依赖检查、诊断工具
"""
from typing import Dict, Any, List, Optional
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentStatus(str, Enum):
    """组件状态"""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        """初始化健康检查器"""
        self.checks = {}
        logger.info("✅ 健康检查器已初始化")

    def register_check(
        self,
        name: str,
        check_func: callable,
        critical: bool = True
    ):
        """
        注册健康检查

        Args:
            name: 检查名称
            check_func: 检查函数，返回 (status, details)
            critical: 是否关键组件
        """
        self.checks[name] = {
            "func": check_func,
            "critical": critical
        }
        logger.info(f"✅ 已注册健康检查: {name}")

    async def check_health(self) -> Dict[str, Any]:
        """
        执行所有健康检查

        Returns:
            健康检查结果
        """
        start_time = time.time()
        results = {}
        critical_failures = 0
        degraded_count = 0

        # 执行每个检查
        for name, check_config in self.checks.items():
            try:
                status, details = await self._run_check(
                    check_config["func"]
                )

                results[name] = {
                    "status": status.value,
                    "critical": check_config["critical"],
                    "details": details
                }

                # 统计失败
                if status == ComponentStatus.DOWN and check_config["critical"]:
                    critical_failures += 1
                elif status == ComponentStatus.DEGRADED:
                    degraded_count += 1

            except Exception as e:
                logger.error(f"健康检查失败: {name} - {e}")
                results[name] = {
                    "status": ComponentStatus.DOWN.value,
                    "critical": check_config["critical"],
                    "details": {"error": str(e)}
                }
                if check_config["critical"]:
                    critical_failures += 1

        # 计算总体状态
        if critical_failures > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        duration = time.time() - start_time

        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "duration": duration,
            "checks": results
        }

    async def _run_check(self, check_func):
        """运行单个检查"""
        import asyncio

        if asyncio.iscoroutinefunction(check_func):
            return await check_func()
        else:
            return check_func()


# ==================== 预定义检查 ====================

async def check_database() -> tuple[ComponentStatus, Dict]:
    """检查数据库连接"""
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text

        db = SessionLocal()
        try:
            # 执行简单查询
            db.execute(text("SELECT 1"))
            return ComponentStatus.UP, {"message": "Database connected"}
        finally:
            db.close()

    except Exception as e:
        return ComponentStatus.DOWN, {"error": str(e)}


async def check_redis() -> tuple[ComponentStatus, Dict]:
    """检查 Redis 连接"""
    try:
        from app.core.cache_manager import get_cache_manager

        cache = get_cache_manager()
        if not cache.enabled:
            return ComponentStatus.DOWN, {"error": "Redis not enabled"}

        # 测试连接
        cache.set("health_check", "ok", ttl=10)
        value = cache.get("health_check")

        if value == "ok":
            return ComponentStatus.UP, {"message": "Redis connected"}
        else:
            return ComponentStatus.DEGRADED, {"warning": "Redis response mismatch"}

    except Exception as e:
        return ComponentStatus.DOWN, {"error": str(e)}


async def check_disk_space() -> tuple[ComponentStatus, Dict]:
    """检查磁盘空间"""
    try:
        import shutil

        stat = shutil.disk_usage("/")
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        percent_used = (stat.used / stat.total) * 100

        details = {
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "percent_used": round(percent_used, 2)
        }

        if free_gb < 1:
            return ComponentStatus.DOWN, {**details, "error": "Disk space critical"}
        elif free_gb < 5:
            return ComponentStatus.DEGRADED, {**details, "warning": "Low disk space"}
        else:
            return ComponentStatus.UP, details

    except Exception as e:
        return ComponentStatus.DOWN, {"error": str(e)}


async def check_memory() -> tuple[ComponentStatus, Dict]:
    """检查内存使用"""
    try:
        import psutil

        mem = psutil.virtual_memory()

        details = {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent
        }

        if mem.percent > 95:
            return ComponentStatus.DOWN, {**details, "error": "Memory critical"}
        elif mem.percent > 85:
            return ComponentStatus.DEGRADED, {**details, "warning": "High memory usage"}
        else:
            return ComponentStatus.UP, details

    except Exception as e:
        return ComponentStatus.DOWN, {"error": str(e)}


async def check_vectorization_service() -> tuple[ComponentStatus, Dict]:
    """检查向量化服务"""
    try:
        from app.services.optimized_vectorization_service import OptimizedVectorizationService

        service = OptimizedVectorizationService(
            model_path="./models/bge-large-zh-v1.5",
            batch_size=16,
            use_gpu=True
        )

        # 测试向量化
        test_text = ["测试"]
        embeddings = service.vectorize_batch(test_text, show_progress=False)

        if embeddings.shape[0] == 1:
            return ComponentStatus.UP, {
                "device": service.device,
                "embedding_dim": embeddings.shape[1]
            }
        else:
            return ComponentStatus.DEGRADED, {"warning": "Unexpected output shape"}

    except Exception as e:
        return ComponentStatus.DOWN, {"error": str(e)}


# ==================== 全局健康检查器 ====================

_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """获取全局健康检查器"""
    global _health_checker

    if _health_checker is None:
        _health_checker = HealthChecker()

        # 注册默认检查
        _health_checker.register_check("database", check_database, critical=True)
        _health_checker.register_check("redis", check_redis, critical=False)
        _health_checker.register_check("disk_space", check_disk_space, critical=True)
        _health_checker.register_check("memory", check_memory, critical=True)
        _health_checker.register_check("vectorization", check_vectorization_service, critical=False)

    return _health_checker


# ==================== FastAPI 端点 ====================

async def health_endpoint():
    """
    健康检查端点

    Returns:
        健康检查结果
    """
    checker = get_health_checker()
    result = await checker.check_health()

    # 根据状态返回 HTTP 状态码
    if result["status"] == HealthStatus.UNHEALTHY.value:
        status_code = 503
    elif result["status"] == HealthStatus.DEGRADED.value:
        status_code = 200  # 仍然可用，但有问题
    else:
        status_code = 200

    from fastapi import Response
    import json

    return Response(
        content=json.dumps(result, ensure_ascii=False),
        media_type="application/json",
        status_code=status_code
    )


async def readiness_endpoint():
    """
    就绪检查端点

    Returns:
        就绪状态
    """
    checker = get_health_checker()
    result = await checker.check_health()

    # 只检查关键组件
    critical_ok = all(
        check["status"] == ComponentStatus.UP.value
        for check in result["checks"].values()
        if check["critical"]
    )

    if critical_ok:
        return {"status": "ready"}
    else:
        from fastapi import Response
        return Response(
            content='{"status": "not ready"}',
            media_type="application/json",
            status_code=503
        )


async def liveness_endpoint():
    """
    存活检查端点

    Returns:
        存活状态
    """
    return {"status": "alive"}
