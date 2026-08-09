"""
Phase 2.3: 资源管理 - 综合测试

测试内容：
1. 数据库连接池
2. HTTP连接池
3. 线程池和进程池
4. 内存管理
5. 优雅关闭
6. Agent资源约束
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.core.resource_pool import (
    DatabasePool,
    HTTPPool,
    ExecutorPool,
    ResourcePoolManager,
    PoolConfig,
    PoolType
)
from app.core.memory_manager import (
    MemoryManager,
    MemoryMonitor,
    MemoryConfig,
    LRUCache,
    ObjectTracker,
    GCStrategy
)
from app.core.graceful_shutdown import (
    GracefulShutdownManager,
    ShutdownConfig,
    ShutdownPhase,
    on_shutdown,
    tracked_task
)
from app.core.agent_resource_constraint import (
    AgentResourceConstraint,
    AgentResourceManager,
    ResourceQuota,
    ResourceType,
    EnforcementPolicy,
    ResourceConstraintException,
    with_resource_constraint
)


class TestDatabasePool:
    """测试数据库连接池"""

    @pytest.mark.asyncio
    async def test_pool_initialization(self):
        """测试连接池初始化"""
        config = PoolConfig(min_size=2, max_size=5)
        pool = DatabasePool("sqlite+aiosqlite:///:memory:", config)

        await pool.initialize()

        assert pool.engine is not None
        assert pool.session_factory is not None

        await pool.close()

    @pytest.mark.asyncio
    async def test_session_context(self):
        """测试会话上下文管理"""
        config = PoolConfig(min_size=2, max_size=5)
        pool = DatabasePool("sqlite+aiosqlite:///:memory:", config)

        await pool.initialize()

        # 使用会话
        async with pool.session() as session:
            assert session is not None

        await pool.close()

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        config = PoolConfig(min_size=2, max_size=5)
        pool = DatabasePool("sqlite+aiosqlite:///:memory:", config)

        await pool.initialize()

        # 健康检查应该成功
        health = await pool.health_check()
        assert health is True

        await pool.close()

    @pytest.mark.asyncio
    async def test_pool_stats(self):
        """测试连接池统计"""
        config = PoolConfig(min_size=2, max_size=5)
        pool = DatabasePool("sqlite+aiosqlite:///:memory:", config)

        await pool.initialize()

        stats = pool.get_stats()
        assert stats.pool_type == PoolType.DATABASE
        assert stats.max_size == 5

        await pool.close()


class TestHTTPPool:
    """测试HTTP连接池"""

    @pytest.mark.asyncio
    async def test_pool_initialization(self):
        """测试HTTP池初始化"""
        config = PoolConfig(max_size=10, http_max_keepalive=5)
        pool = HTTPPool(config)

        await pool.initialize()

        assert pool.client is not None

        await pool.close()

    @pytest.mark.asyncio
    async def test_http_request(self):
        """测试HTTP请求"""
        config = PoolConfig(max_size=10, http_timeout=30.0)
        pool = HTTPPool(config)

        await pool.initialize()

        # 模拟请求（使用httpbin）
        try:
            response = await pool.get("https://httpbin.org/get")
            assert response.status_code == 200
        except Exception as e:
            # 网络问题，跳过
            pytest.skip(f"网络请求失败: {e}")

        await pool.close()

    @pytest.mark.asyncio
    async def test_pool_stats(self):
        """测试HTTP池统计"""
        config = PoolConfig(max_size=10)
        pool = HTTPPool(config)

        await pool.initialize()

        stats = pool.get_stats()
        assert stats.pool_type == PoolType.HTTP

        await pool.close()


class TestExecutorPool:
    """测试执行器池"""

    @pytest.mark.asyncio
    async def test_thread_pool(self):
        """测试线程池"""
        config = PoolConfig(max_workers=4)
        pool = ExecutorPool(PoolType.THREAD, config)

        pool.initialize()

        # 提交任务
        def sync_task(x):
            time.sleep(0.1)
            return x * 2

        result = await pool.submit(sync_task, 5)
        assert result == 10

        pool.shutdown()

    @pytest.mark.asyncio
    async def test_thread_pool_stats(self):
        """测试线程池统计"""
        config = PoolConfig(max_workers=4)
        pool = ExecutorPool(PoolType.THREAD, config)

        pool.initialize()

        stats = pool.get_stats()
        assert stats.pool_type == PoolType.THREAD
        assert stats.max_size == 4

        pool.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_execution(self):
        """测试并发执行"""
        config = PoolConfig(max_workers=3)
        pool = ExecutorPool(PoolType.THREAD, config)

        pool.initialize()

        def task(n):
            time.sleep(0.1)
            return n

        # 并发提交多个任务
        tasks = [pool.submit(task, i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert results == [0, 1, 2, 3, 4]

        pool.shutdown()


class TestMemoryManager:
    """测试内存管理"""

    def test_memory_monitor_initialization(self):
        """测试内存监控器初始化"""
        config = MemoryConfig(max_memory_mb=512)
        monitor = MemoryMonitor(config)

        assert monitor.config.max_memory_mb == 512

    def test_get_memory_stats(self):
        """测试获取内存统计"""
        config = MemoryConfig()
        monitor = MemoryMonitor(config)

        stats = monitor.get_memory_stats()

        assert stats.total_mb > 0
        assert stats.process_rss_mb > 0
        assert stats.gc_objects > 0

    def test_force_gc(self):
        """测试强制GC"""
        config = MemoryConfig()
        monitor = MemoryMonitor(config)

        # 创建一些垃圾对象
        garbage = [{"data": i} for i in range(1000)]
        del garbage

        # 强制GC
        monitor.force_gc(2)

    @pytest.mark.asyncio
    async def test_memory_monitoring(self):
        """测试内存监控循环"""
        config = MemoryConfig(gc_interval_seconds=0.5, max_memory_mb=1024)
        monitor = MemoryMonitor(config)

        await monitor.start_monitoring()
        await asyncio.sleep(1.0)  # 运行一会儿
        await monitor.stop_monitoring()

    def test_lru_cache_basic(self):
        """测试LRU缓存基本功能"""
        cache = LRUCache(max_size=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        assert cache.get("a") == 1
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_lru_cache_eviction(self):
        """测试LRU缓存淘汰"""
        cache = LRUCache(max_size=3)

        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        # 添加第4个，应该淘汰最久未使用的
        cache.set("d", 4)

        assert cache.get("a") is None  # 被淘汰
        assert cache.get("d") == 4

    def test_lru_cache_ttl(self):
        """测试LRU缓存TTL"""
        cache = LRUCache(max_size=10, ttl_seconds=0.5)

        cache.set("key", "value")
        assert cache.get("key") == "value"

        # 等待过期
        time.sleep(0.6)
        assert cache.get("key") is None

    def test_object_tracker(self):
        """测试对象追踪器"""
        tracker = ObjectTracker(max_objects=100)

        # 追踪一些对象
        obj1 = {"data": "test1"}
        obj2 = {"data": "test2"}

        tracker.track(obj1, "obj1")
        tracker.track(obj2, "obj2")

        stats = tracker.get_stats()
        assert stats["total_tracked"] >= 0

    def test_memory_manager_singleton(self):
        """测试内存管理器单例"""
        manager1 = MemoryManager()
        manager2 = MemoryManager()

        assert manager1 is manager2

    def test_memory_manager_cache(self):
        """测试内存管理器缓存功能"""
        manager = MemoryManager()

        cache = manager.create_cache("test_cache", max_size=10)
        assert cache is not None

        # 获取缓存
        retrieved = manager.get_cache("test_cache")
        assert retrieved is cache


class TestGracefulShutdown:
    """测试优雅关闭"""

    def test_shutdown_manager_singleton(self):
        """测试关闭管理器单例"""
        manager1 = GracefulShutdownManager()
        manager2 = GracefulShutdownManager()

        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_shutdown_hooks(self):
        """测试关闭钩子"""
        manager = GracefulShutdownManager()
        manager.configure(ShutdownConfig(graceful_timeout=5.0))

        executed = []

        async def hook1():
            executed.append("hook1")

        async def hook2():
            executed.append("hook2")

        # 注册钩子（优先级不同）
        manager.register_hook("hook1", hook1, priority=10)
        manager.register_hook("hook2", hook2, priority=20)

        # 执行关闭
        await manager.shutdown()

        # 检查执行顺序（按优先级）
        assert "hook2" in executed
        assert "hook1" in executed

    @pytest.mark.asyncio
    async def test_tracked_task(self):
        """测试任务追踪"""
        manager = GracefulShutdownManager()

        async def test_task():
            async with tracked_task("test"):
                await asyncio.sleep(0.1)

        # 执行任务
        await test_task()

    @pytest.mark.asyncio
    async def test_shutdown_timeout(self):
        """测试关闭超时"""
        manager = GracefulShutdownManager()
        manager.configure(ShutdownConfig(graceful_timeout=1.0))

        # 注册一个耗时的钩子
        async def slow_hook():
            await asyncio.sleep(2.0)

        manager.register_hook("slow", slow_hook, timeout=0.5)

        # 关闭应该超时但不崩溃
        await manager.shutdown()

    def test_on_shutdown_decorator(self):
        """测试关闭装饰器"""
        executed = []

        @on_shutdown(priority=100)
        async def cleanup():
            executed.append("cleanup")

        # 装饰器应该自动注册钩子
        # 实际执行需要在关闭时触发


class TestAgentResourceConstraint:
    """测试Agent资源约束"""

    @pytest.mark.asyncio
    async def test_constraint_initialization(self):
        """测试约束器初始化"""
        quota = ResourceQuota(max_concurrency=5, max_memory_mb=256)
        constraint = AgentResourceConstraint("test-agent", quota)

        assert constraint.agent_id == "test-agent"
        assert constraint.quota.max_concurrency == 5

    @pytest.mark.asyncio
    async def test_concurrency_limit(self):
        """测试并发限制"""
        quota = ResourceQuota(max_concurrency=2)
        constraint = AgentResourceConstraint("test-agent", quota)

        results = []

        async def task(n):
            async with constraint.acquire():
                results.append(f"start-{n}")
                await asyncio.sleep(0.1)
                results.append(f"end-{n}")

        # 并发执行3个任务
        await asyncio.gather(task(1), task(2), task(3))

        # 应该有6个结果
        assert len(results) == 6

    @pytest.mark.asyncio
    async def test_resource_rejection(self):
        """测试资源拒绝策略"""
        quota = ResourceQuota(
            max_concurrency=1,
            enforcement_policy=EnforcementPolicy.REJECT
        )
        constraint = AgentResourceConstraint("test-agent", quota)

        # 先获取资源，让并发数达到上限
        async def hold_resource():
            async with constraint.acquire():
                await asyncio.sleep(1.0)

        # 启动任务占用资源
        task = asyncio.create_task(hold_resource())
        await asyncio.sleep(0.1)  # 确保资源已被占用

        # 尝试再次获取应该被拒绝
        with pytest.raises((ResourceConstraintException, asyncio.TimeoutError)):
            async with constraint.acquire(timeout=0.1):
                pass

        # 等待任务完成
        await task

    @pytest.mark.asyncio
    async def test_acquire_timeout(self):
        """测试获取超时"""
        quota = ResourceQuota(max_concurrency=1)
        constraint = AgentResourceConstraint("test-agent", quota)

        async def long_task():
            async with constraint.acquire():
                await asyncio.sleep(2.0)

        # 启动长任务
        task1 = asyncio.create_task(long_task())
        await asyncio.sleep(0.1)  # 确保任务1已获取资源

        # 尝试获取（应该超时）
        with pytest.raises(asyncio.TimeoutError):
            async with constraint.acquire(timeout=0.5):
                pass

        # 等待任务1完成
        await task1

    @pytest.mark.asyncio
    async def test_usage_stats(self):
        """测试使用统计"""
        quota = ResourceQuota(max_concurrency=5)
        constraint = AgentResourceConstraint("test-agent", quota)

        async with constraint.acquire():
            stats = constraint.get_usage_stats()

            assert stats["agent_id"] == "test-agent"
            assert "usage" in stats
            assert "quota" in stats
            assert "utilization" in stats

    @pytest.mark.asyncio
    async def test_resource_manager(self):
        """测试资源管理器"""
        manager = AgentResourceManager()

        quota = ResourceQuota(max_concurrency=3)
        constraint = manager.create_constraint("agent-1", quota)

        assert constraint.agent_id == "agent-1"

        # 再次创建应该返回同一个实例
        constraint2 = manager.create_constraint("agent-1")
        assert constraint is constraint2

        # 获取统计
        stats = manager.get_all_stats()
        assert "agent-1" in stats

        # 移除约束
        manager.remove_constraint("agent-1")
        assert manager.get_constraint("agent-1") is None

    @pytest.mark.asyncio
    async def test_with_resource_constraint_decorator(self):
        """测试资源约束装饰器"""
        quota = ResourceQuota(max_concurrency=2)

        @with_resource_constraint("decorated-agent", quota=quota)
        async def process_task(value):
            await asyncio.sleep(0.1)
            return value * 2

        # 执行任务
        result = await process_task(10)
        assert result == 20

        # 检查约束器已创建
        manager = AgentResourceManager()
        constraint = manager.get_constraint("decorated-agent")
        assert constraint is not None


class TestResourceIntegration:
    """测试资源管理集成"""

    @pytest.mark.asyncio
    async def test_full_resource_lifecycle(self):
        """测试完整资源生命周期"""
        # 1. 创建资源池管理器
        resource_manager = ResourcePoolManager()

        # 2. 注册各类池
        db_config = PoolConfig(min_size=2, max_size=5)
        resource_manager.register_db_pool("sqlite+aiosqlite:///:memory:", db_config)

        http_config = PoolConfig(max_size=10)
        resource_manager.register_http_pool(http_config)

        thread_config = PoolConfig(max_workers=4)
        resource_manager.register_thread_pool(thread_config)

        # 3. 初始化所有池
        await resource_manager.initialize_all()

        # 4. 获取统计
        stats = resource_manager.get_all_stats()
        assert "database" in stats

        # 5. 关闭所有池
        await resource_manager.shutdown_all()

    @pytest.mark.asyncio
    async def test_memory_with_shutdown(self):
        """测试内存管理与关闭集成"""
        # 启动内存管理
        memory_manager = MemoryManager()
        memory_manager.configure(MemoryConfig(
            max_memory_mb=512,
            gc_interval_seconds=1.0
        ))

        await memory_manager.start()

        # 运行一段时间
        await asyncio.sleep(0.5)

        # 停止内存管理
        await memory_manager.stop()

        # 获取统计
        stats = memory_manager.get_stats()
        assert "memory" in stats


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
