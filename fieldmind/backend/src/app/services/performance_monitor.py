"""
性能监控服务

提供API性能监控、业务指标监控、系统健康检查
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from functools import wraps
import psutil
import os

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = {
            "api_calls": {},           # API调用统计
            "processing_times": {},    # 处理时间统计
            "error_counts": {},        # 错误统计
            "file_processing": {},     # 文件处理统计
        }
        self.start_time = datetime.utcnow()

    def track_api_call(self, endpoint: str, duration_ms: float, status_code: int):
        """追踪API调用"""
        if endpoint not in self.metrics["api_calls"]:
            self.metrics["api_calls"][endpoint] = {
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "errors": 0
            }

        stats = self.metrics["api_calls"][endpoint]
        stats["count"] += 1
        stats["total_time"] += duration_ms
        stats["min_time"] = min(stats["min_time"], duration_ms)
        stats["max_time"] = max(stats["max_time"], duration_ms)

        if status_code >= 400:
            stats["errors"] += 1

    def track_file_processing(
        self,
        file_type: str,
        success: bool,
        duration_ms: float,
        file_size: int = 0
    ):
        """追踪文件处理"""
        if file_type not in self.metrics["file_processing"]:
            self.metrics["file_processing"][file_type] = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "total_time": 0,
                "total_size": 0
            }

        stats = self.metrics["file_processing"][file_type]
        stats["total"] += 1
        stats["total_time"] += duration_ms
        stats["total_size"] += file_size

        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1

    def get_api_metrics(self) -> Dict[str, Any]:
        """获取API指标"""
        metrics = {}

        for endpoint, stats in self.metrics["api_calls"].items():
            if stats["count"] > 0:
                metrics[endpoint] = {
                    "calls": stats["count"],
                    "avg_time_ms": stats["total_time"] / stats["count"],
                    "min_time_ms": stats["min_time"],
                    "max_time_ms": stats["max_time"],
                    "error_rate": stats["errors"] / stats["count"] if stats["count"] > 0 else 0
                }

        return metrics

    def get_file_processing_metrics(self) -> Dict[str, Any]:
        """获取文件处理指标"""
        metrics = {}

        for file_type, stats in self.metrics["file_processing"].items():
            if stats["total"] > 0:
                metrics[file_type] = {
                    "total": stats["total"],
                    "success": stats["success"],
                    "failed": stats["failed"],
                    "success_rate": stats["success"] / stats["total"] if stats["total"] > 0 else 0,
                    "avg_time_ms": stats["total_time"] / stats["total"],
                    "total_size_mb": stats["total_size"] / (1024 * 1024)
                }

        return metrics

    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            process = psutil.Process(os.getpid())

            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_mb": process.memory_info().rss / (1024 * 1024),
                "memory_percent": process.memory_percent(),
                "threads": process.num_threads(),
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
            }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}

    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return {
            "api_metrics": self.get_api_metrics(),
            "file_processing": self.get_file_processing_metrics(),
            "system": self.get_system_metrics(),
            "timestamp": datetime.utcnow().isoformat()
        }


# 全局监控器实例
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """获取监控器实例"""
    return _monitor


def track_performance(operation_name: str):
    """性能追踪装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                logger.debug(f"⏱️  {operation_name}: {duration_ms:.2f}ms")
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"❌ {operation_name} 失败 ({duration_ms:.2f}ms): {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                logger.debug(f"⏱️  {operation_name}: {duration_ms:.2f}ms")
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"❌ {operation_name} 失败 ({duration_ms:.2f}ms): {e}")
                raise

        # 判断是否是异步函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# =====================================================
# 业务指标收集器
# =====================================================

class BusinessMetricsCollector:
    """业务指标收集器"""

    def __init__(self, db_session):
        self.db = db_session

    def get_normalization_metrics(self) -> Dict[str, Any]:
        """获取规范化指标"""
        try:
            from sqlalchemy import func
            from app.models import (
                document_normalization_logs,
                file_normalized_content,
                file_completeness_checks
            )

            # 规范化日志统计
            log_stats = self.db.query(
                func.count(document_normalization_logs.id).label('total'),
                func.avg(document_normalization_logs.completeness_score).label('avg_completeness'),
                func.avg(document_normalization_logs.confidence).label('avg_confidence')
            ).first()

            # 按文件类型统计
            by_type = self.db.query(
                document_normalization_logs.file_type,
                func.count(document_normalization_logs.id).label('count')
            ).group_by(document_normalization_logs.file_type).all()

            # 完整性检查通过率
            check_stats = self.db.query(
                func.count(file_completeness_checks.id).label('total'),
                func.sum(file_completeness_checks.is_passed).label('passed')
            ).first()

            return {
                "total_processed": log_stats.total if log_stats else 0,
                "avg_completeness": float(log_stats.avg_completeness or 0) if log_stats else 0,
                "avg_confidence": float(log_stats.avg_confidence or 0) if log_stats else 0,
                "by_type": {row.file_type: row.count for row in by_type},
                "completeness_checks": {
                    "total": check_stats.total if check_stats else 0,
                    "passed": check_stats.passed if check_stats else 0,
                    "pass_rate": (check_stats.passed / check_stats.total) if check_stats and check_stats.total > 0 else 0
                }
            }

        except Exception as e:
            logger.error(f"获取规范化指标失败: {e}")
            return {}

    def get_knowledge_extraction_metrics(self) -> Dict[str, Any]:
        """获取知识提取指标"""
        try:
            from sqlalchemy import func

            # TODO: 查询 entities_unified, events_unified, relationships_unified
            # 这里需要根据实际表结构实现

            return {
                "entities_extracted": 0,
                "events_extracted": 0,
                "relationships_discovered": 0,
                "knowledge_units_created": 0
            }

        except Exception as e:
            logger.error(f"获取知识提取指标失败: {e}")
            return {}
