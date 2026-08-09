"""
监控模块测试
Testing for Lock and Consistency Monitoring
"""

import pytest
import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from app.core.data.lock_monitor import (
    LockMonitor,
    MonitoredLockManager,
    LockStatus,
    LockEvent,
    LockMetrics,
    get_lock_monitor,
)

from app.core.data.consistency_monitor import (
    ConsistencyMonitor,
    ConsistencyMetrics,
    ConsistencyViolation,
    SyncEvent,
    SyncStatus,
    IntegrityValidator,
    DataRepairTask,
)

from app.core.data.locks import LockBackend
from app.core.data.consistency import (
    ConsistencyChecker,
    LastWriteWinsResolver,
    VersionVector,
    ConflictRecord,
)


class TestLockMonitor:
    """测试锁监控器"""

    @pytest.fixture
    def monitor(self):
        """创建监控器"""
        return LockMonitor(
            history_size=100,
            metrics_window=300,
            deadlock_detection_interval=1.0,
            timeout_warning_threshold=0.8
        )

    def test_record_acquire_event(self, monitor):
        """测试记录获取锁事件"""
        event = LockEvent(
            lock_key="test_lock",
            holder_id="holder_1",
            status=LockStatus.ACQUIRED,
            timestamp=time.time(),
            backend="redis",
            ttl=30.0,
            wait_time=0.5
        )

        monitor.record_event(event)

        # 验证事件被记录
        assert len(monitor.events) == 1
        assert monitor.events[0] == event

        # 验证指标更新
        metrics = monitor.get_metrics(lock_key="test_lock")
        assert len(metrics) == 1
        assert metrics[0].acquire_count == 1
        assert metrics[0].total_wait_time == 0.5
        assert "holder_1" in metrics[0].current_holders

    def test_record_release_event(self, monitor):
        """测试记录释放锁事件"""
        # 先获取
        acquire_event = LockEvent(
            lock_key="test_lock",
            holder_id="holder_1",
            status=LockStatus.ACQUIRED,
            timestamp=time.time(),
            backend="redis",
            ttl=30.0
        )
        monitor.record_event(acquire_event)

        # 再释放
        time.sleep(0.1)
        release_event = LockEvent(
            lock_key="test_lock",
            holder_id="holder_1",
            status=LockStatus.RELEASED,
            timestamp=time.time(),
            backend="redis"
        )
        monitor.record_event(release_event)

        # 验证指标
        metrics = monitor.get_metrics(lock_key="test_lock")[0]
        assert metrics.acquire_count == 1
        assert metrics.release_count == 1
        assert "holder_1" not in metrics.current_holders
        assert metrics.total_hold_time > 0

    def test_record_timeout_event(self, monitor):
        """测试记录超时事件"""
        event = LockEvent(
            lock_key="test_lock",
            holder_id="holder_1",
            status=LockStatus.TIMEOUT,
            timestamp=time.time(),
            backend="redis",
            wait_time=5.0
        )

        monitor.record_event(event)

        metrics = monitor.get_metrics(lock_key="test_lock")[0]
        assert metrics.timeout_count == 1

    def test_record_failure_event(self, monitor):
        """测试记录失败事件"""
        event = LockEvent(
            lock_key="test_lock",
            holder_id="holder_1",
            status=LockStatus.FAILED,
            timestamp=time.time(),
            backend="redis",
            metadata={"error": "Connection failed"}
        )

        monitor.record_event(event)

        metrics = monitor.get_metrics(lock_key="test_lock")[0]
        assert metrics.failure_count == 1

    def test_wait_queue_tracking(self, monitor):
        """测试等待队列跟踪"""
        monitor.record_wait_start("test_lock", "waiter_1", "redis")
        monitor.record_wait_start("test_lock", "waiter_2", "redis")

        wait_queues = monitor.get_wait_queues()
        assert "redis:test_lock" in wait_queues
        assert len(wait_queues["redis:test_lock"]) == 2

        # 获取锁后从队列移除
        event = LockEvent(
            lock_key="test_lock",
            holder_id="waiter_1",
            status=LockStatus.ACQUIRED,
            timestamp=time.time(),
            backend="redis"
        )
        monitor.record_event(event)

        wait_queues = monitor.get_wait_queues()
        assert len(wait_queues["redis:test_lock"]) == 1

    def test_metrics_calculation(self, monitor):
        """测试指标计算"""
        # 记录多个事件
        for i in range(5):
            acquire = LockEvent(
                lock_key="test_lock",
                holder_id=f"holder_{i}",
                status=LockStatus.ACQUIRED,
                timestamp=time.time(),
                backend="redis",
                wait_time=float(i)
            )
            monitor.record_event(acquire)

            time.sleep(0.05)

            release = LockEvent(
                lock_key="test_lock",
                holder_id=f"holder_{i}",
                status=LockStatus.RELEASED,
                timestamp=time.time(),
                backend="redis"
            )
            monitor.record_event(release)

        metrics = monitor.get_metrics(lock_key="test_lock")[0]
        assert metrics.acquire_count == 5
        assert metrics.release_count == 5
        assert metrics.avg_wait_time() == 2.0  # (0+1+2+3+4)/5
        assert metrics.max_wait_time == 4.0
        assert metrics.min_wait_time == 0.0
        assert metrics.success_rate() == 1.0

    def test_get_events_filtering(self, monitor):
        """测试事件过滤"""
        # 记录不同类型的事件
        events = [
            LockEvent("lock1", "h1", LockStatus.ACQUIRED, time.time(), "redis"),
            LockEvent("lock1", "h1", LockStatus.RELEASED, time.time(), "redis"),
            LockEvent("lock2", "h2", LockStatus.TIMEOUT, time.time(), "database"),
            LockEvent("lock1", "h3", LockStatus.FAILED, time.time(), "redis"),
        ]

        for event in events:
            monitor.record_event(event)

        # 按lock_key过滤
        lock1_events = monitor.get_events(lock_key="lock1")
        assert len(lock1_events) == 3

        # 按status过滤
        timeout_events = monitor.get_events(status=LockStatus.TIMEOUT)
        assert len(timeout_events) == 1

        # 按时间过滤
        since = time.time() - 1
        recent_events = monitor.get_events(since=since)
        assert len(recent_events) == 4

    @pytest.mark.asyncio
    async def test_deadlock_detection(self, monitor):
        """测试死锁检测"""
        # 模拟死锁场景: A持有L1等待L2, B持有L2等待L1
        # A持有L1
        monitor.active_locks["redis:lock1"]["holder_a"] = time.time()
        # B持有L2
        monitor.active_locks["redis:lock2"]["holder_b"] = time.time()
        # A等待L2
        monitor.wait_queues["redis:lock2"].append(("holder_a", time.time() - 5))
        # B等待L1
        monitor.wait_queues["redis:lock1"].append(("holder_b", time.time() - 5))

        deadlocks = await monitor.detect_deadlocks()
        assert len(deadlocks) > 0

        # 检查死锁候选
        dl = deadlocks[0]
        assert set(dl.holders) == {"holder_a", "holder_b"}
        assert set(dl.lock_keys) >= {"redis:lock1", "redis:lock2"}
        assert dl.confidence > 0

    @pytest.mark.asyncio
    async def test_timeout_warnings(self, monitor):
        """测试超时警告"""
        # 记录一个长时间持有的锁
        ttl = 10.0
        acquire_time = time.time() - (ttl * 0.9)  # 持有了90%的TTL

        monitor.active_locks["redis:test_lock"]["holder_1"] = acquire_time

        # 记录TTL信息
        event = LockEvent(
            lock_key="test_lock",
            holder_id="holder_1",
            status=LockStatus.ACQUIRED,
            timestamp=acquire_time,
            backend="redis",
            ttl=ttl
        )
        monitor.record_event(event)

        # 检查超时警告
        warnings = await monitor.check_timeout_warnings()
        assert len(warnings) > 0
        assert warnings[0]['lock_key'] == "test_lock"
        assert warnings[0]['holder_id'] == "holder_1"
        assert warnings[0]['remaining'] < ttl * 0.2

    def test_get_statistics(self, monitor):
        """测试全局统计"""
        # 记录一些事件
        for i in range(10):
            event = LockEvent(
                lock_key=f"lock_{i % 3}",
                holder_id=f"holder_{i}",
                status=LockStatus.ACQUIRED if i % 4 != 0 else LockStatus.FAILED,
                timestamp=time.time(),
                backend="redis"
            )
            monitor.record_event(event)

        stats = monitor.get_statistics()
        assert stats['total_locks'] == 3
        assert stats['total_acquires'] > 0
        assert stats['total_failures'] > 0
        assert 0 <= stats['avg_success_rate'] <= 1


class TestMonitoredLockManager:
    """测试带监控的锁管理器"""

    @pytest.mark.asyncio
    async def test_monitored_lock_acquire_release(self):
        """测试监控锁的获取和释放"""
        import redis.asyncio as redis

        monitor = LockMonitor()
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        manager = MonitoredLockManager(redis_client=redis_client, monitor=monitor)

        try:
            async with manager.lock("test_lock", ttl=5.0, backend=LockBackend.REDIS):
                # 锁被持有
                pass

            # 验证事件被记录
            events = monitor.get_events(lock_key="test_lock")
            assert len(events) >= 2  # 至少有acquire和release

            acquired = [e for e in events if e.status == LockStatus.ACQUIRED]
            released = [e for e in events if e.status == LockStatus.RELEASED]
            assert len(acquired) >= 1
            assert len(released) >= 1
        finally:
            await redis_client.close()


class TestConsistencyMonitor:
    """测试一致性监控器"""

    @pytest.fixture
    def monitor(self):
        """创建一致性监控器"""
        from unittest.mock import MagicMock

        # 创建模拟的session和checker
        mock_session = MagicMock()
        checker = ConsistencyChecker(
            session=mock_session,
            node_id="test_node"
        )
        resolver = LastWriteWinsResolver()
        return ConsistencyMonitor(
            checker=checker,
            resolver=resolver,
            history_size=100,
            metrics_window=300,
            check_interval=1.0,
            regions=["us-east", "us-west", "eu-central"]
        )

    def test_record_sync_event(self, monitor):
        """测试记录同步事件"""
        event = SyncEvent(
            entity_type="user",
            entity_id=1,
            source_region="us-east",
            target_region="us-west",
            status=SyncStatus.COMPLETED,
            timestamp=time.time(),
            sync_duration=0.5
        )

        monitor.record_sync_event(event)

        # 验证事件被记录
        assert len(monitor.events) == 1

        # 验证指标
        metrics = monitor.get_metrics(entity_type="user")
        assert len(metrics) == 1
        assert metrics[0].total_syncs == 1
        assert metrics[0].successful_syncs == 1
        assert metrics[0].total_sync_time == 0.5

    def test_record_conflict_event(self, monitor):
        """测试记录冲突事件"""
        event = SyncEvent(
            entity_type="user",
            entity_id=1,
            source_region="us-east",
            target_region="us-west",
            status=SyncStatus.CONFLICT,
            timestamp=time.time(),
            conflict_count=3
        )

        monitor.record_sync_event(event)

        metrics = monitor.get_metrics(entity_type="user")[0]
        assert metrics.conflict_syncs == 1
        assert metrics.total_conflicts == 3
        assert metrics.last_conflict is not None

    @pytest.mark.asyncio
    async def test_check_entity_consistency(self, monitor):
        """测试实体一致性检查"""
        data_by_region = {
            "us-east": {
                "id": 1,
                "name": "Alice",
                "email": "alice@example.com",
                "version": 5
            },
            "us-west": {
                "id": 1,
                "name": "Alice",
                "email": "alice@newdomain.com",  # 冲突
                "version": 5
            }
        }

        conflicts = await monitor.check_entity_consistency(
            "user", 1, data_by_region
        )

        assert len(conflicts) > 0
        email_conflicts = [c for c in conflicts if c.field_name == "email"]
        assert len(email_conflicts) > 0

    @pytest.mark.asyncio
    async def test_detect_missing_violations(self, monitor):
        """测试检测缺失副本"""
        expected_regions = {"us-east", "us-west", "eu-central"}
        actual_data = {
            "us-east": {1: {"id": 1, "name": "Alice"}},
            "us-west": {1: {"id": 1, "name": "Alice"}},
            "eu-central": {}  # 缺失实体1
        }

        violations = await monitor.detect_violations(
            "user", expected_regions, actual_data
        )

        missing_violations = [v for v in violations if v.violation_type == "missing"]
        assert len(missing_violations) == 1
        assert "eu-central" in missing_violations[0].regions

    @pytest.mark.asyncio
    async def test_detect_divergent_violations(self, monitor):
        """测试检测数据分歧"""
        expected_regions = {"us-east", "us-west"}
        actual_data = {
            "us-east": {1: {"id": 1, "name": "Alice", "email": "alice@old.com"}},
            "us-west": {1: {"id": 1, "name": "Alice", "email": "alice@new.com"}}
        }

        violations = await monitor.detect_violations(
            "user", expected_regions, actual_data
        )

        divergent_violations = [v for v in violations if v.violation_type == "divergent"]
        assert len(divergent_violations) > 0

    @pytest.mark.asyncio
    async def test_create_repair_task(self, monitor):
        """测试创建修复任务"""
        violation = ConsistencyViolation(
            entity_type="user",
            entity_id=1,
            violation_type="missing",
            regions=["eu-central"],
            detected_at=time.time(),
            details={"missing_from": ["eu-central"]},
            severity="high"
        )

        task = await monitor.create_repair_task(violation)

        assert task.violation == violation
        assert task.repair_strategy == "sync"  # 自动选择
        assert task.status == "pending"

    @pytest.mark.asyncio
    async def test_execute_repair_task(self, monitor):
        """测试执行修复任务"""
        violation = ConsistencyViolation(
            entity_type="user",
            entity_id=1,
            violation_type="missing",
            regions=["eu-central"],
            detected_at=time.time(),
            details={"missing_from": ["eu-central"]},
            severity="high"
        )

        task = await monitor.create_repair_task(violation, strategy="sync")
        success = await monitor.execute_repair_task(task)

        assert success
        assert task.status == "completed"
        assert task.result is not None
        assert task.completed_at is not None

    def test_metrics_calculation(self, monitor):
        """测试指标计算"""
        # 记录多个同步事件
        for i in range(10):
            status = SyncStatus.COMPLETED if i % 3 != 0 else SyncStatus.FAILED
            event = SyncEvent(
                entity_type="user",
                entity_id=i,
                source_region="us-east",
                target_region="us-west",
                status=status,
                timestamp=time.time(),
                sync_duration=0.1 if status == SyncStatus.COMPLETED else None
            )
            monitor.record_sync_event(event)

        metrics = monitor.get_metrics(entity_type="user")[0]
        assert metrics.total_syncs == 10
        assert metrics.successful_syncs > 0
        assert metrics.failed_syncs > 0
        assert 0 < metrics.success_rate() < 1
        assert metrics.avg_sync_time() > 0

    def test_get_statistics(self, monitor):
        """测试全局统计"""
        # 记录事件
        for i in range(20):
            event = SyncEvent(
                entity_type=f"type_{i % 3}",
                entity_id=i,
                source_region="us-east",
                target_region="us-west",
                status=SyncStatus.COMPLETED if i % 4 != 0 else SyncStatus.CONFLICT,
                timestamp=time.time(),
                conflict_count=2 if i % 4 == 0 else 0,
                sync_duration=0.1
            )
            monitor.record_sync_event(event)

        # 添加违规
        violation = ConsistencyViolation(
            entity_type="user",
            entity_id=1,
            violation_type="missing",
            regions=["eu-central"],
            detected_at=time.time(),
            details={}
        )
        monitor.violations.append(violation)

        stats = monitor.get_statistics()
        assert stats['total_entity_types'] == 3
        assert stats['total_syncs'] == 20
        assert stats['successful_syncs'] > 0
        assert stats['conflict_syncs'] > 0
        assert stats['total_conflicts'] > 0
        assert stats['active_violations'] == 1


class TestIntegrityValidator:
    """测试完整性验证器"""

    @pytest.fixture
    def validator(self):
        """创建验证器"""
        return IntegrityValidator()

    @pytest.mark.asyncio
    async def test_not_null_validator(self, validator):
        """测试非空验证"""
        validator.register_validator(
            "user",
            IntegrityValidator.not_null_validator("email")
        )

        # 有效数据
        valid_data = {"id": 1, "email": "alice@example.com"}
        violations = await validator.validate("user", valid_data)
        assert len(violations) == 0

        # 无效数据
        invalid_data = {"id": 1, "email": None}
        violations = await validator.validate("user", invalid_data)
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_type_validator(self, validator):
        """测试类型验证"""
        validator.register_validator(
            "user",
            IntegrityValidator.type_validator("age", int)
        )

        # 有效数据
        valid_data = {"id": 1, "age": 25}
        violations = await validator.validate("user", valid_data)
        assert len(violations) == 0

        # 无效数据
        invalid_data = {"id": 1, "age": "25"}
        violations = await validator.validate("user", invalid_data)
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_range_validator(self, validator):
        """测试范围验证"""
        validator.register_validator(
            "user",
            IntegrityValidator.range_validator("age", min_val=0, max_val=150)
        )

        # 有效数据
        valid_data = {"id": 1, "age": 25}
        violations = await validator.validate("user", valid_data)
        assert len(violations) == 0

        # 无效数据 - 超出范围
        invalid_data = {"id": 1, "age": 200}
        violations = await validator.validate("user", invalid_data)
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_regex_validator(self, validator):
        """测试正则验证"""
        validator.register_validator(
            "user",
            IntegrityValidator.regex_validator("email", r"^[\w\.-]+@[\w\.-]+\.\w+$")
        )

        # 有效数据
        valid_data = {"id": 1, "email": "alice@example.com"}
        violations = await validator.validate("user", valid_data)
        assert len(violations) == 0

        # 无效数据
        invalid_data = {"id": 1, "email": "not-an-email"}
        violations = await validator.validate("user", invalid_data)
        assert len(violations) == 1

    @pytest.mark.asyncio
    async def test_custom_validator(self, validator):
        """测试自定义验证器"""
        def custom_validator(data: dict) -> bool:
            # 年龄必须是偶数
            return data.get("age", 0) % 2 == 0

        custom_validator.__name__ = "even_age"
        validator.register_validator("user", custom_validator)

        # 有效数据
        valid_data = {"id": 1, "age": 24}
        violations = await validator.validate("user", valid_data)
        assert len(violations) == 0

        # 无效数据
        invalid_data = {"id": 1, "age": 25}
        violations = await validator.validate("user", invalid_data)
        assert len(violations) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
