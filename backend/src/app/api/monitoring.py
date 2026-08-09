"""
监控和健康检查 API
提供系统状态和指标查询
"""

from fastapi import APIRouter
from typing import Dict, Any
import psutil
import os
from datetime import datetime
from pathlib import Path

from app.core.logging import logger

router = APIRouter(prefix="/monitoring", tags=["监控"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    健康检查端点

    返回系统各组件的健康状态
    """
    try:
        # 检查数据库连接
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "healthy",
            "database": db_status,
            "disk": "healthy"  # 可以添加磁盘空间检查
        }
    }


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    获取系统指标

    返回 CPU、内存、磁盘使用情况
    """
    # CPU 使用率
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # 内存使用
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_available_gb = memory.available / (1024 ** 3)

    # 磁盘使用
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    disk_free_gb = disk.free / (1024 ** 3)

    # 进程信息
    process = psutil.Process(os.getpid())
    process_memory_mb = process.memory_info().rss / (1024 ** 2)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
            "memory_available_gb": round(memory_available_gb, 2),
            "disk_percent": round(disk_percent, 2),
            "disk_free_gb": round(disk_free_gb, 2)
        },
        "process": {
            "pid": os.getpid(),
            "memory_mb": round(process_memory_mb, 2),
            "num_threads": process.num_threads()
        }
    }


@router.get("/logs/recent")
async def get_recent_logs(lines: int = 100) -> Dict[str, Any]:
    """
    获取最近的日志

    参数:
    - lines: 返回的日志行数（默认 100）
    """
    log_file = Path("/tmp/fieldmind_logs") / f"fieldmind_{datetime.now().strftime('%Y-%m-%d')}.log"

    if not log_file.exists():
        return {
            "logs": [],
            "message": "日志文件不存在"
        }

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines)
        }
    except Exception as e:
        logger.error(f"读取日志失败: {e}")
        return {
            "logs": [],
            "error": str(e)
        }


@router.get("/stats/api")
async def get_api_stats() -> Dict[str, Any]:
    """
    获取 API 调用统计

    从日志文件中统计 API 调用次数
    """
    api_log_file = Path("/tmp/fieldmind_logs") / f"api_{datetime.now().strftime('%Y-%m-%d')}.log"

    if not api_log_file.exists():
        return {
            "total_calls": 0,
            "message": "API 日志文件不存在"
        }

    try:
        with open(api_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 简单统计
        total_calls = len(lines)
        get_calls = sum(1 for line in lines if ' GET ' in line)
        post_calls = sum(1 for line in lines if ' POST ' in line)
        put_calls = sum(1 for line in lines if ' PUT ' in line)
        delete_calls = sum(1 for line in lines if ' DELETE ' in line)

        return {
            "total_calls": total_calls,
            "by_method": {
                "GET": get_calls,
                "POST": post_calls,
                "PUT": put_calls,
                "DELETE": delete_calls
            },
            "date": datetime.now().strftime('%Y-%m-%d')
        }
    except Exception as e:
        logger.error(f"读取 API 统计失败: {e}")
        return {
            "total_calls": 0,
            "error": str(e)
        }
