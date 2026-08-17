"""
性能监控和日志系统
"""

import logging
import time
import functools
from typing import Callable, Any
from contextlib import contextmanager
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "./logs/app.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = []

    def record_metric(self, name: str, duration: float, metadata: dict = None):
        """记录性能指标"""
        metric = {
            'name': name,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.metrics.append(metric)
        logger.info(f"⏱️ {name}: {duration:.3f}s {metadata or ''}")

    def get_summary(self):
        """获取性能摘要"""
        if not self.metrics:
            return {}

        by_name = {}
        for metric in self.metrics:
            name = metric['name']
            if name not in by_name:
                by_name[name] = []
            by_name[name].append(metric['duration'])

        summary = {}
        for name, durations in by_name.items():
            summary[name] = {
                'count': len(durations),
                'total': sum(durations),
                'avg': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations)
            }

        return summary


# 全局监控器
performance_monitor = PerformanceMonitor()


def monitor_performance(name: str = None):
    """性能监控装饰器"""
    def decorator(func: Callable) -> Callable:
        metric_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                performance_monitor.record_metric(metric_name, duration)

        return wrapper
    return decorator


@contextmanager
def track_time(operation_name: str):
    """上下文管理器：跟踪代码块执行时间"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        performance_monitor.record_metric(operation_name, duration)


class StructuredLogger:
    """结构化日志器"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_event(self, event_type: str, message: str, **kwargs):
        """记录结构化事件"""
        log_entry = {
            'event_type': event_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))

    def log_error(self, error: Exception, context: dict = None):
        """记录错误"""
        log_entry = {
            'event_type': 'ERROR',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        self.logger.error(json.dumps(log_entry, ensure_ascii=False))

    def log_api_request(self, method: str, path: str, status_code: int, duration: float):
        """记录API请求"""
        log_entry = {
            'event_type': 'API_REQUEST',
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))

    def log_document_processing(self, document_id: int, stage: str, status: str, duration: float = None):
        """记录文档处理"""
        log_entry = {
            'event_type': 'DOCUMENT_PROCESSING',
            'document_id': document_id,
            'stage': stage,
            'status': status,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))


# 创建全局日志器
app_logger = StructuredLogger('fieldmind')


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.counters = {}
        self.gauges = {}

    def increment(self, name: str, value: int = 1):
        """增加计数器"""
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += value

    def set_gauge(self, name: str, value: float):
        """设置仪表值"""
        self.gauges[name] = value

    def get_metrics(self):
        """获取所有指标"""
        return {
            'counters': self.counters,
            'gauges': self.gauges,
            'timestamp': datetime.now().isoformat()
        }


# 全局指标收集器
metrics_collector = MetricsCollector()


# 使用示例
if __name__ == "__main__":
    # 测试性能监控
    @monitor_performance("test_function")
    def test_function():
        time.sleep(0.1)
        return "done"

    test_function()

    # 测试上下文管理器
    with track_time("test_operation"):
        time.sleep(0.2)

    # 测试结构化日志
    app_logger.log_event("TEST", "测试日志", user_id=123, action="upload")

    # 测试指标收集
    metrics_collector.increment("api_requests")
    metrics_collector.set_gauge("active_users", 42)

    # 输出摘要
    print("\n性能摘要:")
    print(json.dumps(performance_monitor.get_summary(), indent=2, ensure_ascii=False))

    print("\n指标:")
    print(json.dumps(metrics_collector.get_metrics(), indent=2, ensure_ascii=False))
