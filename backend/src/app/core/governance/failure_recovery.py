"""
故障恢复机制

提供企业级的故障检测、恢复和容错能力：
- 自动故障检测
- 健康检查
- 断路器模式
- 重试机制
- 降级策略
- 故障通知
"""

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import logging
import time

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean, Float
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CircuitState(str, Enum):
    """断路器状态"""
    CLOSED = "closed"  # 正常运行
    OPEN = "open"  # 断路（故障）
    HALF_OPEN = "half_open"  # 半开（尝试恢复）


class FailureType(str, Enum):
    """故障类型"""
    TIMEOUT = "timeout"
    EXCEPTION = "exception"
    RESOURCE_ERROR = "resource_error"
    VALIDATION_ERROR = "validation_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"


# ==================== 数据库模型 ====================

class FailureRecord(Base):
    """故障记录表"""
    __tablename__ = "failure_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    failure_id = Column(String(64), unique=True, nullable=False)

    service_name = Column(String(128), nullable=False, index=True)
    operation = Column(String(128), nullable=False)

    failure_type = Column(String(32), nullable=False)
    error_message = Column(Text)
    stack_trace = Column(Text)

    occurred_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)
    is_resolved = Column(Boolean, default=False)

    recovery_attempts = Column(Integer, default=0)
    recovery_strategy = Column(String(64))
    recovery_result = Column(JSON)

    project_id = Column(Integer, index=True)
    user_id = Column(Integer)

    context = Column(JSON)  # 故障上下文
    metadata = Column(JSON)


class HealthCheckLog(Base):
    """健康检查日志表"""
    __tablename__ = "health_check_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_id = Column(String(64), unique=True, nullable=False)

    service_name = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False)

    response_time_ms = Column(Float)
    error_message = Column(Text)

    checked_at = Column(DateTime, default=datetime.utcnow, index=True)

    details = Column(JSON)


# ==================== 断路器 ====================

@dataclass
class CircuitBreakerConfig:
    """断路器配置"""
    failure_threshold: int = 5  # 故障阈值
    success_threshold: int = 2  # 恢复阈值
    timeout: float = 30.0  # 超时时间（秒）
    reset_timeout: float = 60.0  # 重置时间（秒）


class CircuitBreaker:
    """
    断路器模式实现

    防止级联故障，自动隔离故障服务
    """

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.utcnow()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过断路器调用函数

        Args:
            func: 要调用的函数
            *args, **kwargs: 函数参数

        Returns:
            函数返回值

        Raises:
            CircuitBreakerOpenError: 断路器打开时
        """

        # 检查断路器状态
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    f"断路器 {self.name} 处于打开状态"
                )

        try:
            # 执行函数（带超时）
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )

            # 成功
            self._on_success()
            return result

        except asyncio.TimeoutError:
            self._on_failure(FailureType.TIMEOUT, "操作超时")
            raise

        except Exception as e:
            self._on_failure(FailureType.EXCEPTION, str(e))
            raise

    def _on_success(self):
        """处理成功调用"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()

    def _on_failure(self, failure_type: FailureType, message: str):
        """处理失败调用"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        logger.warning(
            f"断路器 {self.name} 故障: {failure_type.value} - {message} "
            f"({self.failure_count}/{self.config.failure_threshold})"
        )

        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self.failure_count >= self.config.failure_threshold:
            self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        if not self.last_failure_time:
            return False

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.reset_timeout

    def _transition_to_open(self):
        """转换到打开状态"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.utcnow()
        logger.error(f"⚠️ 断路器 {self.name} 已打开（故障隔离）")

    def _transition_to_half_open(self):
        """转换到半开状态"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.utcnow()
        logger.info(f"🔄 断路器 {self.name} 半开（尝试恢复）")

    def _transition_to_closed(self):
        """转换到关闭状态"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.utcnow()
        logger.info(f"✅ 断路器 {self.name} 已关闭（恢复正常）")

    def get_status(self) -> Dict[str, Any]:
        """获取断路器状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat()
        }


class CircuitBreakerOpenError(Exception):
    """断路器打开错误"""
    pass


# ==================== 重试机制 ====================

@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # 初始延迟（秒）
    max_delay: float = 60.0  # 最大延迟（秒）
    exponential_base: float = 2.0  # 指数退避基数
    jitter: bool = True  # 是否添加随机抖动


async def retry_with_backoff(
    func: Callable,
    config: RetryConfig = None,
    *args,
    **kwargs
) -> Any:
    """
    带指数退避的重试

    Args:
        func: 要执行的函数
        config: 重试配置
        *args, **kwargs: 函数参数

    Returns:
        函数返回值

    Raises:
        最后一次尝试的异常
    """
    config = config or RetryConfig()
    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            last_exception = e

            if attempt < config.max_attempts - 1:
                # 计算延迟时间
                delay = min(
                    config.initial_delay * (config.exponential_base ** attempt),
                    config.max_delay
                )

                # 添加随机抖动
                if config.jitter:
                    import random
                    delay *= (0.5 + random.random())

                logger.warning(
                    f"重试 {attempt + 1}/{config.max_attempts} 失败: {e}, "
                    f"等待 {delay:.2f}s 后重试"
                )

                await asyncio.sleep(delay)
            else:
                logger.error(f"重试失败，已达到最大尝试次数 {config.max_attempts}")

    raise last_exception


# ==================== 故障恢复服务 ====================

class FailureRecoveryService:
    """故障恢复服务"""

    def __init__(self, db: Session):
        self.db = db
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    def get_circuit_breaker(
        self,
        service_name: str,
        config: CircuitBreakerConfig = None
    ) -> CircuitBreaker:
        """获取或创建断路器"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(
                name=service_name,
                config=config
            )
        return self.circuit_breakers[service_name]

    async def record_failure(
        self,
        service_name: str,
        operation: str,
        failure_type: FailureType,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict] = None,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> FailureRecord:
        """记录故障"""
        import uuid

        record = FailureRecord(
            failure_id=f"fail_{uuid.uuid4().hex[:12]}",
            service_name=service_name,
            operation=operation,
            failure_type=failure_type.value,
            error_message=error_message,
            stack_trace=stack_trace,
            context=context or {},
            project_id=project_id,
            user_id=user_id
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        logger.error(
            f"❌ 故障记录: {service_name}.{operation} - {failure_type.value}"
        )

        return record

    async def attempt_recovery(
        self,
        failure_id: str,
        recovery_func: Callable,
        strategy: str = "retry"
    ) -> Dict[str, Any]:
        """尝试恢复"""
        record = self.db.query(FailureRecord).filter(
            FailureRecord.failure_id == failure_id
        ).first()

        if not record:
            raise ValueError(f"故障记录不存在: {failure_id}")

        record.recovery_attempts += 1
        record.recovery_strategy = strategy

        try:
            # 执行恢复函数
            result = await recovery_func()

            # 标记为已恢复
            record.is_resolved = True
            record.resolved_at = datetime.utcnow()
            record.recovery_result = {
                "status": "success",
                "result": result
            }

            self.db.commit()

            logger.info(f"✅ 故障已恢复: {failure_id}")

            return {
                "status": "recovered",
                "attempts": record.recovery_attempts,
                "result": result
            }

        except Exception as e:
            record.recovery_result = {
                "status": "failed",
                "error": str(e)
            }
            self.db.commit()

            logger.error(f"❌ 恢复失败: {failure_id} - {e}")

            return {
                "status": "failed",
                "attempts": record.recovery_attempts,
                "error": str(e)
            }

    async def health_check(
        self,
        service_name: str,
        check_func: Callable
    ) -> HealthStatus:
        """执行健康检查"""
        import uuid

        check_id = f"health_{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        try:
            await check_func()
            response_time_ms = (time.time() - start_time) * 1000
            status = HealthStatus.HEALTHY

            log = HealthCheckLog(
                check_id=check_id,
                service_name=service_name,
                status=status.value,
                response_time_ms=response_time_ms
            )

            self.db.add(log)
            self.db.commit()

            return status

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            status = HealthStatus.UNHEALTHY

            log = HealthCheckLog(
                check_id=check_id,
                service_name=service_name,
                status=status.value,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )

            self.db.add(log)
            self.db.commit()

            logger.warning(f"⚠️ 健康检查失败: {service_name} - {e}")

            return status

    def get_failure_statistics(
        self,
        service_name: Optional[str] = None,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """获取故障统计"""
        query = self.db.query(FailureRecord)

        if service_name:
            query = query.filter(FailureRecord.service_name == service_name)

        cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        query = query.filter(FailureRecord.occurred_at >= cutoff_time)

        records = query.all()

        total_failures = len(records)
        resolved_failures = sum(1 for r in records if r.is_resolved)
        failure_types = {}

        for record in records:
            failure_types[record.failure_type] = failure_types.get(record.failure_type, 0) + 1

        return {
            "total_failures": total_failures,
            "resolved_failures": resolved_failures,
            "unresolved_failures": total_failures - resolved_failures,
            "resolution_rate": resolved_failures / total_failures if total_failures > 0 else 0,
            "failure_types": failure_types,
            "time_range_hours": time_range_hours
        }

    def get_circuit_breaker_status(self) -> List[Dict[str, Any]]:
        """获取所有断路器状态"""
        return [
            cb.get_status()
            for cb in self.circuit_breakers.values()
        ]


# ==================== 降级策略 ====================

class DegradationStrategy:
    """降级策略"""

    @staticmethod
    async def fallback_to_cache(
        primary_func: Callable,
        cache_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """降级到缓存"""
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"主服务失败，降级到缓存: {e}")
            return await cache_func(*args, **kwargs)

    @staticmethod
    async def fallback_to_default(
        primary_func: Callable,
        default_value: Any,
        *args,
        **kwargs
    ) -> Any:
        """降级到默认值"""
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"服务失败，返回默认值: {e}")
            return default_value

    @staticmethod
    async def fallback_chain(
        funcs: List[Callable],
        *args,
        **kwargs
    ) -> Any:
        """降级链"""
        last_error = None

        for i, func in enumerate(funcs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"降级链 [{i+1}/{len(funcs)}] 失败: {e}")

        raise last_error


# ==================== 便捷装饰器 ====================

def with_circuit_breaker(service_name: str, config: CircuitBreakerConfig = None):
    """断路器装饰器"""
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里需要从某处获取 FailureRecoveryService
            # 简化版本，实际使用时需要依赖注入
            cb = CircuitBreaker(service_name, config)
            return await cb.call(func, *args, **kwargs)

        return wrapper

    return decorator


def with_retry(config: RetryConfig = None):
    """重试装饰器"""
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, config, *args, **kwargs)

        return wrapper

    return decorator
