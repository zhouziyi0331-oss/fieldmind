"""
Phase 2.2 弹性机制测试套件

测试断路器、降级、请求去重等功能。
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch

from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    get_circuit_breaker,
    circuit_breaker
)
from app.core.degradation import (
    DegradationLevel,
    DegradationStrategy,
    DegradationConfig,
    DegradationManager,
    get_degradation_manager,
    with_degradation
)
from app.core.request_deduplication import (
    RequestDeduplicator,
    get_deduplicator,
    deduplicate,
    IdempotencyManager,
    get_idempotency_manager,
    idempotent
)
from app.core.errors import ServiceException, TimeoutException


class TestCircuitBreaker:
    """测试断路器功能"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_normal_operation(self):
        """测试断路器正常操作"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout=1.0
        )
        cb = CircuitBreaker("test_service", config)

        # 正常调用应该成功
        async def success_func():
            return "success"

        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED

        stats = cb.get_stats()
        assert stats["total_calls"] == 1
        assert stats["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """测试断路器在失败时打开"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout=1.0
        )
        cb = CircuitBreaker("test_service", config)

        # 连续失败
        async def fail_func():
            raise Exception("Service error")

        for i in range(3):
            try:
                await cb.call(fail_func)
            except Exception:
                pass

        # 断路器应该打开
        assert cb.state == CircuitBreakerState.OPEN

        # 再次调用应该被拒绝
        with pytest.raises(ServiceException) as exc_info:
            await cb.call(fail_func)

        assert "断路器已打开" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """测试断路器半开状态恢复"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            recovery_timeout=0.1,  # 短恢复时间用于测试
            timeout=1.0
        )
        cb = CircuitBreaker("test_service", config)

        # 触发断路器打开
        async def fail_func():
            raise Exception("Service error")

        for i in range(2):
            try:
                await cb.call(fail_func)
            except Exception:
                pass

        assert cb.state == CircuitBreakerState.OPEN

        # 等待恢复超时
        await asyncio.sleep(0.2)

        # 成功调用应该让断路器进入半开状态
        async def success_func():
            return "success"

        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitBreakerState.HALF_OPEN

        # 再次成功应该关闭断路器
        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout(self):
        """测试断路器超时处理"""
        config = CircuitBreakerConfig(
            failure_threshold=3,  # 需要3次失败
            failure_rate_threshold=1.0,  # 失败率阈值设为1.0
            timeout=0.1  # 短超时用于测试
        )
        cb = CircuitBreaker("test_timeout", config)

        # 慢函数
        async def slow_func():
            await asyncio.sleep(0.5)
            return "result"

        # 第一次应该超时
        with pytest.raises(TimeoutException):
            await cb.call(slow_func)
        assert cb.state == CircuitBreakerState.CLOSED

        # 第二次超时
        with pytest.raises(TimeoutException):
            await cb.call(slow_func)
        assert cb.state == CircuitBreakerState.CLOSED

        # 第三次超时，断路器应该打开
        with pytest.raises(TimeoutException):
            await cb.call(slow_func)
        assert cb.state == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_fallback(self):
        """测试断路器降级处理"""
        async def fallback():
            return "fallback_result"

        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test_service", config, fallback=fallback)

        # 触发断路器打开
        async def fail_func():
            raise Exception("Service error")

        for i in range(2):
            try:
                await cb.call(fail_func)
            except Exception:
                pass

        assert cb.state == CircuitBreakerState.OPEN

        # 断路器打开时应该使用降级处理
        result = await cb.call(fail_func)
        assert result == "fallback_result"

    def test_circuit_breaker_decorator(self):
        """测试断路器装饰器"""
        call_count = 0

        @circuit_breaker(name="decorator_test")
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Error")
            return "success"

        async def run_test():
            # 前两次失败
            for i in range(2):
                try:
                    await test_func()
                except Exception:
                    pass

            # 获取断路器状态
            cb = get_circuit_breaker("decorator_test")
            assert cb.state == CircuitBreakerState.OPEN

        asyncio.run(run_test())


class TestDegradation:
    """测试降级功能"""

    def test_degradation_manager_basic(self):
        """测试降级管理器基本功能"""
        manager = DegradationManager()

        # 注册降级配置
        config = DegradationConfig(
            level=DegradationLevel.NONE,
            strategy=DegradationStrategy.DEFAULT_VALUE,
            default_value="default"
        )
        manager.register_degradation("test_service", config)

        # 服务未降级
        assert not manager.is_degraded("test_service")

        # 手动降级
        manager.degrade_service("test_service", DegradationLevel.LOW, "测试降级")

        # 服务已降级
        assert manager.is_degraded("test_service")
        assert manager.get_effective_level("test_service") == DegradationLevel.LOW

        # 恢复服务
        manager.recover_service("test_service")
        assert not manager.is_degraded("test_service")

    def test_degradation_global_level(self):
        """测试全局降级级别"""
        manager = DegradationManager()

        config = DegradationConfig(level=DegradationLevel.NONE)
        manager.register_degradation("service1", config)
        manager.register_degradation("service2", config)

        # 设置全局降级级别
        manager.set_global_level(DegradationLevel.HIGH, "系统过载")

        # 所有服务都应该降级
        assert manager.is_degraded("service1")
        assert manager.is_degraded("service2")
        assert manager.get_effective_level("service1") == DegradationLevel.HIGH

    def test_degradation_cache(self):
        """测试降级缓存"""
        manager = DegradationManager()

        # 缓存数据
        manager.cache_data("test_service", "key1", "value1")

        # 获取缓存
        cached = manager.get_cached_data("test_service", "key1")
        assert cached == "value1"

        # 不存在的缓存
        cached = manager.get_cached_data("test_service", "key2")
        assert cached is None

    @pytest.mark.asyncio
    async def test_degradation_decorator_default_value(self):
        """测试降级装饰器 - 默认值策略"""
        manager = get_degradation_manager()

        config = DegradationConfig(
            level=DegradationLevel.NONE,
            strategy=DegradationStrategy.DEFAULT_VALUE,
            default_value="degraded_result"
        )

        @with_degradation("test_service", config)
        async def test_func():
            return "normal_result"

        # 正常调用
        result = await test_func()
        assert result == "normal_result"

        # 降级服务
        manager.degrade_service("test_service", DegradationLevel.LOW, "测试")

        # 降级后返回默认值
        result = await test_func()
        assert result == "degraded_result"

    @pytest.mark.asyncio
    async def test_degradation_decorator_cached_data(self):
        """测试降级装饰器 - 缓存数据策略"""
        manager = get_degradation_manager()

        config = DegradationConfig(
            level=DegradationLevel.NONE,
            strategy=DegradationStrategy.CACHED_DATA,
            default_value="default"
        )

        call_count = 0

        @with_degradation("cache_service", config, cache_result=True)
        async def test_func(param: str):
            nonlocal call_count
            call_count += 1
            return f"result_{param}_{call_count}"

        # 第一次调用
        result1 = await test_func("test")
        assert result1 == "result_test_1"

        # 降级服务
        manager.degrade_service("cache_service", DegradationLevel.LOW, "测试")

        # 降级后应该返回缓存的结果
        result2 = await test_func("test")
        assert result2 == "result_test_1"  # 返回缓存的第一次结果

    @pytest.mark.asyncio
    async def test_degradation_decorator_fallback(self):
        """测试降级装饰器 - 备用服务策略"""
        manager = get_degradation_manager()

        async def fallback_func():
            return "fallback_result"

        config = DegradationConfig(
            level=DegradationLevel.NONE,
            strategy=DegradationStrategy.FALLBACK_SERVICE,
            fallback_func=fallback_func
        )

        @with_degradation("fallback_service", config)
        async def test_func():
            return "normal_result"

        # 正常调用
        result = await test_func()
        assert result == "normal_result"

        # 降级服务
        manager.degrade_service("fallback_service", DegradationLevel.MEDIUM, "测试")

        # 降级后使用备用服务
        result = await test_func()
        assert result == "fallback_result"


class TestRequestDeduplication:
    """测试请求去重功能"""

    @pytest.mark.asyncio
    async def test_deduplicator_basic(self):
        """测试去重器基本功能"""
        dedup = RequestDeduplicator("test_dedup", window_seconds=60.0)
        dedup.start()

        call_count = 0

        async def test_func(param: str):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return f"result_{param}_{call_count}"

        # 第一次调用
        result1 = await dedup.execute(test_func, "test")
        assert result1 == "result_test_1"
        assert call_count == 1

        # 相同参数的第二次调用应该使用缓存
        result2 = await dedup.execute(test_func, "test")
        assert result2 == "result_test_1"  # 相同的结果
        assert call_count == 1  # 函数没有再次执行

        # 不同参数的调用
        result3 = await dedup.execute(test_func, "other")
        assert result3 == "result_other_2"
        assert call_count == 2

        await dedup.stop()

    @pytest.mark.asyncio
    async def test_deduplicator_concurrent_requests(self):
        """测试并发请求去重"""
        dedup = RequestDeduplicator("concurrent_test", window_seconds=60.0)
        dedup.start()

        call_count = 0

        async def slow_func(param: str):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.2)
            return f"result_{param}"

        # 并发发起多个相同请求
        tasks = [dedup.execute(slow_func, "test") for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # 所有请求应该返回相同结果
        assert all(r == "result_test" for r in results)

        # 函数应该只执行一次
        assert call_count == 1

        await dedup.stop()

    @pytest.mark.asyncio
    async def test_deduplicator_decorator(self):
        """测试去重装饰器"""
        call_count = 0

        @deduplicate(name="decorator_dedup", window_seconds=60.0)
        async def test_func(param: str):
            nonlocal call_count
            call_count += 1
            return f"result_{param}_{call_count}"

        # 第一次调用
        result1 = await test_func("test")
        assert result1 == "result_test_1"

        # 第二次调用应该返回缓存
        result2 = await test_func("test")
        assert result2 == "result_test_1"
        assert call_count == 1

        # 清理
        dedup = get_deduplicator("decorator_dedup")
        await dedup.stop()

    @pytest.mark.asyncio
    async def test_deduplicator_error_handling(self):
        """测试去重器错误处理"""
        dedup = RequestDeduplicator("error_test", window_seconds=60.0)
        dedup.start()

        async def error_func():
            raise ValueError("Test error")

        # 第一次调用失败
        with pytest.raises(ValueError):
            await dedup.execute(error_func)

        # 第二次调用也应该失败（缓存了异常）
        with pytest.raises(ValueError):
            await dedup.execute(error_func)

        await dedup.stop()


class TestIdempotency:
    """测试幂等性功能"""

    def test_idempotency_manager_basic(self):
        """测试幂等性管理器基本功能"""
        manager = IdempotencyManager(ttl=3600.0)

        # 第一次设置
        is_first, existing = manager.check_and_set("key1", "value1")
        assert is_first is True
        assert existing is None

        # 第二次设置
        is_first, existing = manager.check_and_set("key1", "value2")
        assert is_first is False
        assert existing == "value1"

    def test_idempotency_manager_expiration(self):
        """测试幂等键过期"""
        manager = IdempotencyManager(ttl=0.1)  # 0.1秒过期

        # 设置键
        manager.check_and_set("key1", "value1")

        # 等待过期
        time.sleep(0.2)

        # 过期后应该可以重新设置
        is_first, existing = manager.check_and_set("key1", "value2")
        assert is_first is True
        assert existing is None

    @pytest.mark.asyncio
    async def test_idempotency_decorator(self):
        """测试幂等性装饰器"""
        call_count = 0

        @idempotent(lambda order_id: f"order:{order_id}")
        async def create_order(order_id: str):
            nonlocal call_count
            call_count += 1
            return f"order_created_{call_count}"

        # 第一次调用
        result1 = await create_order("123")
        assert result1 == "order_created_1"
        assert call_count == 1

        # 第二次调用应该返回相同结果
        result2 = await create_order("123")
        assert result2 == "order_created_1"
        assert call_count == 1  # 函数没有再次执行

        # 不同ID的调用
        result3 = await create_order("456")
        assert result3 == "order_created_2"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_idempotency_error_retry(self):
        """测试幂等性错误重试"""
        call_count = 0

        @idempotent(lambda x: f"key:{x}")
        async def failing_func(x: str):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First attempt failed")
            return "success"

        # 第一次调用失败
        with pytest.raises(ValueError):
            await failing_func("test")

        assert call_count == 1

        # 第二次调用应该重试（因为第一次失败，幂等键被删除）
        result = await failing_func("test")
        assert result == "success"
        assert call_count == 2


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_degradation(self):
        """测试断路器与降级的集成"""
        # 设置降级配置
        degradation_manager = get_degradation_manager()
        degrade_config = DegradationConfig(
            level=DegradationLevel.NONE,
            strategy=DegradationStrategy.DEFAULT_VALUE,
            default_value="degraded"
        )

        # 状态变更回调：断路器打开时自动降级服务
        def on_state_change(old_state, new_state):
            if new_state == CircuitBreakerState.OPEN:
                degradation_manager.degrade_service("integrated_service", DegradationLevel.HIGH, "断路器打开")

        # 创建断路器
        cb_config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("integrated_service", cb_config, on_state_change=on_state_change)

        # 注册降级
        degradation_manager.register_degradation("integrated_service", degrade_config)

        @with_degradation("integrated_service", degrade_config)
        async def service_call():
            return "normal"

        # 触发断路器打开
        async def fail_func():
            raise Exception("Error")

        for i in range(2):
            try:
                await cb.call(fail_func)
            except Exception:
                pass

        # 断路器应该打开
        assert cb.state == CircuitBreakerState.OPEN

        # 服务应该自动降级
        assert degradation_manager.is_degraded("integrated_service")

        # 调用应该返回降级结果
        result = await service_call()
        assert result == "degraded"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
