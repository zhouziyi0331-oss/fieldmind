# Error Handling & Recovery 深度分析报告

**插件名称**: Error Handling & Recovery Systems  
**类别**: 错误处理和故障恢复  
**分析日期**: 2026-08-30

---

## 1. 插件概述

### 核心定位
错误处理与恢复系统为 LLM 应用提供健壮的容错能力，包括异常捕获、自动重试、降级策略、断路器等机制，确保系统在面对错误时能够优雅降级而非崩溃。

### 核心特点
- **异常分类**: 可恢复/不可恢复错误
- **重试策略**: 指数退避、抖动
- **断路器**: 防止级联失败
- **降级策略**: Fallback机制
- **错误上报**: 监控和告警
- **事务回滚**: 保证一致性

### 架构设计
```
Error Handling
├── Exception Handling (异常处理)
│   ├── Error Classification
│   ├── Error Context
│   ├── Stack Trace
│   └── Error Logging
├── Retry Mechanisms (重试机制)
│   ├── Exponential Backoff
│   ├── Jitter
│   ├── Max Attempts
│   └── Timeout
├── Circuit Breaker (断路器)
│   ├── Closed State
│   ├── Open State
│   ├── Half-Open State
│   └── Failure Threshold
├── Fallback Strategies (降级策略)
│   ├── Default Values
│   ├── Cache Fallback
│   ├── Alternative Services
│   └── Degraded Mode
├── Recovery (恢复机制)
│   ├── Auto Recovery
│   ├── Manual Recovery
│   ├── State Restoration
│   └── Checkpoint/Rollback
└── Monitoring (监控)
    ├── Error Metrics
    ├── Alerting
    ├── Error Tracking
    └── Health Checks
```

---

## 2. 核心概念

### 2.1 错误分类

```python
from enum import Enum
from typing import Optional

class ErrorSeverity(Enum):
    """错误严重性"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误类别"""
    TRANSIENT = "transient"  # 临时错误，可重试
    PERMANENT = "permanent"   # 永久错误，不可重试
    RATE_LIMIT = "rate_limit" # 速率限制
    TIMEOUT = "timeout"       # 超时
    VALIDATION = "validation" # 验证错误
    AUTHORIZATION = "authorization" # 授权错误

class ApplicationError(Exception):
    """应用错误基类"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retryable: bool = None,
        context: dict = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.retryable = retryable if retryable is not None else self._is_retryable()
        self.context = context or {}
        self.timestamp = datetime.utcnow()
    
    def _is_retryable(self) -> bool:
        """判断是否可重试"""
        return self.category in [
            ErrorCategory.TRANSIENT,
            ErrorCategory.TIMEOUT,
            ErrorCategory.RATE_LIMIT
        ]
    
    def to_dict(self) -> dict:
        """序列化"""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "retryable": self.retryable,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }

# 具体错误类型
class TransientError(ApplicationError):
    """临时错误"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            ErrorCategory.TRANSIENT,
            **kwargs
        )

class RateLimitError(ApplicationError):
    """速率限制错误"""
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(
            message,
            ErrorCategory.RATE_LIMIT,
            **kwargs
        )
        self.retry_after = retry_after
```

### 2.2 重试装饰器

```python
import time
import random
from functools import wraps

def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,)
):
    """
    带指数退避的重试装饰器
    
    参数:
    - max_attempts: 最大尝试次数
    - base_delay: 基础延迟（秒）
    - max_delay: 最大延迟（秒）
    - exponential_base: 指数基数
    - jitter: 是否添加抖动
    - retryable_exceptions: 可重试的异常类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                
                except retryable_exceptions as e:
                    last_exception = e
                    
                    # 检查是否可重试
                    if isinstance(e, ApplicationError) and not e.retryable:
                        raise
                    
                    # 最后一次尝试，不再重试
                    if attempt == max_attempts - 1:
                        raise
                    
                    # 计算延迟
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # 添加抖动
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    # 特殊处理速率限制
                    if isinstance(e, RateLimitError) and e.retry_after:
                        delay = e.retry_after
                    
                    logging.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator

# 使用
@retry_with_backoff(max_attempts=3, base_delay=1.0)
def call_api(endpoint: str):
    response = requests.get(endpoint)
    response.raise_for_status()
    return response.json()
```

### 2.3 断路器

```python
from enum import Enum
import threading

class CircuitState(Enum):
    """断路器状态"""
    CLOSED = "closed"     # 正常工作
    OPEN = "open"         # 断开，拒绝请求
    HALF_OPEN = "half_open" # 半开，尝试恢复

class CircuitBreaker:
    """断路器模式"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        参数:
        - failure_threshold: 失败阈值
        - recovery_timeout: 恢复超时（秒）
        - expected_exception: 预期的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """调用函数，带断路器保护"""
        with self.lock:
            # 检查状态
            if self.state == CircuitState.OPEN:
                # 检查是否可以尝试恢复
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logging.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """是否应该尝试恢复"""
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout
    
    def _on_success(self):
        """成功回调"""
        with self.lock:
            self.failure_count = 0
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logging.info("Circuit breaker reset to CLOSED")
    
    def _on_failure(self):
        """失败回调"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logging.error("Circuit breaker tripped to OPEN state")

class CircuitBreakerError(Exception):
    """断路器错误"""
    pass

# 使用
breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

def protected_call():
    return breaker.call(risky_function)
```

### 2.4 降级策略

```python
from typing import Callable, Any, Optional

class FallbackHandler:
    """降级处理器"""
    
    def __init__(self):
        self.fallback_chain = []
    
    def add_fallback(
        self,
        fallback_func: Callable,
        condition: Optional[Callable] = None
    ):
        """
        添加降级策略
        
        参数:
        - fallback_func: 降级函数
        - condition: 触发条件（返回True时执行此降级）
        """
        self.fallback_chain.append({
            'func': fallback_func,
            'condition': condition
        })
    
    def execute_with_fallback(
        self,
        primary_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """执行函数，带降级"""
        try:
            return primary_func(*args, **kwargs)
        
        except Exception as e:
            logging.warning(f"Primary function failed: {e}. Trying fallbacks...")
            
            # 尝试降级策略
            for fallback in self.fallback_chain:
                condition = fallback['condition']
                
                # 检查条件
                if condition and not condition(e):
                    continue
                
                try:
                    result = fallback['func'](*args, **kwargs)
                    logging.info("Fallback succeeded")
                    return result
                
                except Exception as fallback_error:
                    logging.warning(f"Fallback failed: {fallback_error}")
                    continue
            
            # 所有降级都失败
            logging.error("All fallbacks failed")
            raise

# 使用示例
fallback_handler = FallbackHandler()

# 添加降级策略
fallback_handler.add_fallback(
    fallback_func=lambda query: get_cached_result(query),
    condition=lambda e: isinstance(e, TimeoutError)
)

fallback_handler.add_fallback(
    fallback_func=lambda query: get_default_result(),
    condition=None  # 无条件，作为最后的fallback
)

# 执行
result = fallback_handler.execute_with_fallback(
    call_expensive_api,
    query="test"
)
```

### 2.5 事务和检查点

```python
class Transaction:
    """事务管理"""
    
    def __init__(self):
        self.operations = []
        self.committed = False
    
    def add_operation(
        self,
        do_func: Callable,
        undo_func: Callable,
        *args,
        **kwargs
    ):
        """添加操作"""
        self.operations.append({
            'do': do_func,
            'undo': undo_func,
            'args': args,
            'kwargs': kwargs,
            'executed': False
        })
    
    def execute(self):
        """执行事务"""
        try:
            # 执行所有操作
            for op in self.operations:
                op['do'](*op['args'], **op['kwargs'])
                op['executed'] = True
            
            self.committed = True
            return True
        
        except Exception as e:
            logging.error(f"Transaction failed: {e}. Rolling back...")
            self.rollback()
            raise
    
    def rollback(self):
        """回滚"""
        # 反向回滚已执行的操作
        for op in reversed(self.operations):
            if op['executed']:
                try:
                    op['undo'](*op['args'], **op['kwargs'])
                except Exception as e:
                    logging.error(f"Rollback failed for operation: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and not self.committed:
            self.rollback()
        return False

# 使用
with Transaction() as tx:
    tx.add_operation(
        do_func=lambda: database.insert(record),
        undo_func=lambda: database.delete(record.id)
    )
    
    tx.add_operation(
        do_func=lambda: cache.set(key, value),
        undo_func=lambda: cache.delete(key)
    )
    
    tx.execute()
```

---

## 3. 核心算法

### 3.1 指数退避算法

```python
def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> float:
    """
    计算指数退避延迟
    
    公式: delay = min(base_delay * exponential_base^attempt, max_delay)
    
    加入抖动避免"惊群效应"
    """
    # 基础指数退避
    delay = base_delay * (exponential_base ** attempt)
    
    # 限制最大延迟
    delay = min(delay, max_delay)
    
    # 添加抖动 (0.5 ~ 1.5倍)
    if jitter:
        jitter_factor = 0.5 + random.random()
        delay = delay * jitter_factor
    
    return delay

# 示例
# attempt 0: 1.0s
# attempt 1: 2.0s
# attempt 2: 4.0s
# attempt 3: 8.0s
# ...
# 加入抖动后变化范围: [0.5*delay, 1.5*delay]

# 时间复杂度: O(1)
```

### 3.2 断路器状态机

```python
def circuit_breaker_state_machine(
    breaker: CircuitBreaker,
    success: bool
) -> CircuitState:
    """
    断路器状态转换
    
    状态图:
    CLOSED --[failure_count >= threshold]--> OPEN
    OPEN --[timeout]--> HALF_OPEN
    HALF_OPEN --[success]--> CLOSED
    HALF_OPEN --[failure]--> OPEN
    """
    current_state = breaker.state
    
    if current_state == CircuitState.CLOSED:
        if not success:
            breaker.failure_count += 1
            
            if breaker.failure_count >= breaker.failure_threshold:
                return CircuitState.OPEN
        else:
            breaker.failure_count = 0
        
        return CircuitState.CLOSED
    
    elif current_state == CircuitState.OPEN:
        # 检查是否超时
        if breaker._should_attempt_reset():
            return CircuitState.HALF_OPEN
        
        return CircuitState.OPEN
    
    elif current_state == CircuitState.HALF_OPEN:
        if success:
            breaker.failure_count = 0
            return CircuitState.CLOSED
        else:
            return CircuitState.OPEN
    
    return current_state

# 时间复杂度: O(1)
```

### 3.3 错误预算算法

```python
class ErrorBudget:
    """
    错误预算
    
    允许一定比例的错误，超过后触发降级
    """
    
    def __init__(
        self,
        window_size: int = 100,
        error_threshold: float = 0.05  # 5%错误率
    ):
        self.window_size = window_size
        self.error_threshold = error_threshold
        
        self.results = deque(maxlen=window_size)
    
    def record_success(self):
        """记录成功"""
        self.results.append(True)
    
    def record_failure(self):
        """记录失败"""
        self.results.append(False)
    
    def is_budget_exhausted(self) -> bool:
        """检查错误预算是否耗尽"""
        if len(self.results) < self.window_size:
            return False
        
        error_count = sum(1 for r in self.results if not r)
        error_rate = error_count / len(self.results)
        
        return error_rate > self.error_threshold
    
    def get_error_rate(self) -> float:
        """获取当前错误率"""
        if not self.results:
            return 0.0
        
        error_count = sum(1 for r in self.results if not r)
        return error_count / len(self.results)

# 使用
budget = ErrorBudget(window_size=100, error_threshold=0.05)

def monitored_function():
    try:
        result = risky_operation()
        budget.record_success()
        return result
    except Exception as e:
        budget.record_failure()
        
        if budget.is_budget_exhausted():
            # 触发降级
            return fallback_function()
        
        raise

# 时间复杂度: O(1) 均摊
```

### 3.4 自动恢复算法

```python
class AutoRecoveryManager:
    """自动恢复管理器"""
    
    def __init__(self):
        self.recovery_strategies = []
        self.health_checks = []
    
    def add_recovery_strategy(
        self,
        name: str,
        check: Callable[[], bool],
        recover: Callable[[], bool]
    ):
        """
        添加恢复策略
        
        参数:
        - name: 策略名称
        - check: 健康检查函数
        - recover: 恢复函数
        """
        self.recovery_strategies.append({
            'name': name,
            'check': check,
            'recover': recover
        })
    
    def monitor_and_recover(self):
        """监控并恢复"""
        for strategy in self.recovery_strategies:
            try:
                # 健康检查
                is_healthy = strategy['check']()
                
                if not is_healthy:
                    logging.warning(
                        f"Health check failed for {strategy['name']}. "
                        f"Attempting recovery..."
                    )
                    
                    # 尝试恢复
                    recovered = strategy['recover']()
                    
                    if recovered:
                        logging.info(f"Recovery successful for {strategy['name']}")
                    else:
                        logging.error(f"Recovery failed for {strategy['name']}")
            
            except Exception as e:
                logging.error(f"Error in recovery strategy {strategy['name']}: {e}")
    
    def start_monitoring(self, interval: float = 60.0):
        """启动监控（后台线程）"""
        def monitor_loop():
            while True:
                self.monitor_and_recover()
                time.sleep(interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()

# 使用
recovery_manager = AutoRecoveryManager()

# 添加恢复策略
recovery_manager.add_recovery_strategy(
    name="database_connection",
    check=lambda: database.ping(),
    recover=lambda: database.reconnect()
)

recovery_manager.add_recovery_strategy(
    name="cache_connection",
    check=lambda: cache.ping(),
    recover=lambda: cache.reconnect()
)

# 启动监控
recovery_manager.start_monitoring(interval=30)

# 时间复杂度: O(n) - n为策略数量
```

### 3.5 级联故障防护

```python
class BulkheadIsolation:
    """
    舱壁隔离模式
    
    限制资源池大小，防止故障蔓延
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(max_concurrent)
        self.active_count = 0
        self.rejected_count = 0
    
    def execute(
        self,
        func: Callable,
        *args,
        timeout: float = None,
        **kwargs
    ):
        """执行函数，带隔离"""
        acquired = self.semaphore.acquire(blocking=False)
        
        if not acquired:
            self.rejected_count += 1
            raise BulkheadRejectionError("Bulkhead limit reached")
        
        try:
            self.active_count += 1
            
            if timeout:
                # 带超时执行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(func, *args, **kwargs)
                    return future.result(timeout=timeout)
            else:
                return func(*args, **kwargs)
        
        finally:
            self.active_count -= 1
            self.semaphore.release()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'max_concurrent': self.max_concurrent,
            'active_count': self.active_count,
            'rejected_count': self.rejected_count
        }

class BulkheadRejectionError(Exception):
    """舱壁拒绝错误"""
    pass

# 使用
bulkhead = BulkheadIsolation(max_concurrent=10)

def protected_call():
    return bulkhead.execute(expensive_operation, timeout=5.0)

# 时间复杂度: O(1)
```

---

## 4. 可复用组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Retry Decorator | 重试装饰器 | ⭐⭐⭐⭐⭐ |
| Circuit Breaker | 断路器 | ⭐⭐⭐⭐⭐ |
| Fallback Handler | 降级处理器 | ⭐⭐⭐⭐⭐ |
| Transaction Manager | 事务管理 | ⭐⭐⭐⭐⭐ |
| Error Budget | 错误预算 | ⭐⭐⭐⭐ |
| Auto Recovery | 自动恢复 | ⭐⭐⭐⭐⭐ |
| Bulkhead Isolation | 舱壁隔离 | ⭐⭐⭐⭐ |
| Error Classification | 错误分类 | ⭐⭐⭐⭐⭐ |
| Exponential Backoff | 指数退避 | ⭐⭐⭐⭐⭐ |
| Health Check | 健康检查 | ⭐⭐⭐⭐⭐ |

---

## 5. 核心学习

### 关键概念
1. **重试机制** - 指数退避+抖动
2. **断路器** - 防止级联失败
3. **降级策略** - 优雅降级
4. **事务管理** - 回滚保证一致性
5. **舱壁隔离** - 资源隔离

### 核心算法
1. 指数退避算法
2. 断路器状态机
3. 错误预算算法
4. 自动恢复算法
5. 舱壁隔离限流

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ 重试机制
- ⭐⭐⭐⭐⭐ 断路器模式
- ⭐⭐⭐⭐⭐ 降级策略
- ⭐⭐⭐⭐⭐ 事务管理
- ⭐⭐⭐⭐ 舱壁隔离

---

**分析完成时间**: 2026-08-30  
**已完成插件数**: 32/40 (80%)  
**剩余**: 8个插件
