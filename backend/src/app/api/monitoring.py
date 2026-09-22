"""
监控和健康检查 API
提供系统状态和指标查询
"""

from fastapi import APIRouter
from typing import Dict, Any
import psutil
import os
import json
import re
from datetime import datetime
from pathlib import Path

from app.core.logging import logger
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/monitoring", tags=["监控"])


def _log_candidates() -> list[Path]:
    """按当前启动方式查找真实日志，兼容旧版目录但不伪造日志。"""
    root = Path(__file__).resolve().parents[3]
    candidates = [
        root / "logs" / "app.log",
        root / "logs" / "fieldmind.log",
        root / "src" / "logs" / "app.log",
        Path("/tmp/fieldmind_logs") / f"fieldmind_{datetime.now().strftime('%Y-%m-%d')}.log",
    ]
    configured = os.getenv("FIELDMIND_LOG_FILE") or os.getenv("LOG_FILE")
    if configured:
        candidates.insert(0, Path(configured).expanduser())
    for directory in (root / "logs", root / "src" / "logs", Path("/tmp/fieldmind_logs")):
        if directory.exists():
            candidates.extend(sorted(directory.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True))
    return list(dict.fromkeys(candidates))


def _parse_log_line(line: str) -> Dict[str, Any]:
    """把 JSON 日志或普通文本日志统一成诊断窗可读的结构。"""
    raw = line.strip()
    event: Dict[str, Any] = {
        "raw": raw,
        "timestamp": None,
        "level": "INFO",
        "source": "backend",
        "category": "system",
        "message": raw,
        "details": None,
        "request_id": None,
        "request_url": None,
        "status_code": None,
    }
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            details = parsed.get("details") or parsed.get("exception")
            if isinstance(details, (dict, list)):
                details = json.dumps(details, ensure_ascii=False)
            event["timestamp"] = parsed.get("timestamp") or parsed.get("time")
            event["level"] = str(parsed.get("level") or parsed.get("severity") or "INFO").upper()
            event["source"] = str(parsed.get("source") or parsed.get("logger") or "backend")
            event["category"] = str(parsed.get("category") or parsed.get("event_type") or "system")
            event["message"] = str(parsed.get("message") or parsed.get("msg") or raw)
            event["details"] = details
            event["request_id"] = parsed.get("request_id")
            event["request_url"] = parsed.get("request_url") or parsed.get("path") or parsed.get("endpoint")
            event["status_code"] = parsed.get("status_code")
            return event
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.match(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[T ][^ |]+)\s*[| -]+\s*"
        r"(?P<level>DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL)\s*[| -]+\s*(?P<message>.*)$",
        raw,
        re.IGNORECASE,
    )
    if match:
        event.update(match.groupdict())
        event["level"] = str(event["level"]).upper().replace("WARN", "WARNING")
    else:
        upper = raw.upper()
        event["level"] = "ERROR" if " ERROR " in f" {upper} " or "失败" in raw or "异常" in raw else (
            "WARNING" if " WARNING " in f" {upper} " or "警告" in raw else "INFO"
        )
    return event


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

    return success_response(
        data={
            "status": "healthy" if db_status == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "api": "healthy",
                "database": db_status,
                "disk": "healthy"
            }
        }
    )


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

    return success_response(
        data={
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
    )


@router.get("/logs/recent")
async def get_recent_logs(lines: int = 100) -> Dict[str, Any]:
    """
    获取最近的日志

    参数:
    - lines: 返回的日志行数（默认 100）
    """
    log_file = next((path for path in _log_candidates() if path.exists()), None)

    if log_file is None:
        return success_response(
            data={
                "lines": [],
                "logs": [],
                "events": [],
                "total_lines": 0
            },
            message="日志文件不存在"
        )

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        clean_lines = [line.strip() for line in recent_lines if line.strip()]
        return success_response(
            data={
                "lines": clean_lines,
                "logs": clean_lines,
                "events": [_parse_log_line(line) for line in clean_lines],
                "log_file": str(log_file),
                "total_lines": len(all_lines),
                "returned_lines": len(clean_lines),
                "read_at": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"读取日志失败: {e}")
        return error_response(message=str(e), data={"logs": []})


@router.get("/stats/api")
async def get_api_stats() -> Dict[str, Any]:
    """
    获取 API 调用统计

    从日志文件中统计 API 调用次数
    """
    api_log_file = Path("/tmp/fieldmind_logs") / f"api_{datetime.now().strftime('%Y-%m-%d')}.log"

    if not api_log_file.exists():
        return success_response(
            data={"total_calls": 0},
            message="API 日志文件不存在"
        )

    try:
        with open(api_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 简单统计
        total_calls = len(lines)
        get_calls = sum(1 for line in lines if ' GET ' in line)
        post_calls = sum(1 for line in lines if ' POST ' in line)
        put_calls = sum(1 for line in lines if ' PUT ' in line)
        delete_calls = sum(1 for line in lines if ' DELETE ' in line)

        return success_response(
            data={
                "total_calls": total_calls,
                "by_method": {
                    "GET": get_calls,
                    "POST": post_calls,
                    "PUT": put_calls,
                    "DELETE": delete_calls
                },
                "date": datetime.now().strftime('%Y-%m-%d')
            }
        )
    except Exception as e:
        logger.error(f"读取 API 统计失败: {e}")
        return error_response(message=str(e), data={"total_calls": 0})
