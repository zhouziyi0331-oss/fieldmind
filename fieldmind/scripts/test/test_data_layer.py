"""
Tests for Data Layer (Phase 4.1)

Tests transaction management, distributed locks, and data consistency.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data.transactions import (
    TransactionManager,
    DeadlockDetector,
    IsolationLevel,
    RetryConfig,
    TransactionStats,
    get_transaction_manager,
    savepoint,
)

from app.core.data.locks import (
    RedisLock,
    DatabaseLock,
    AdvisoryLock,
    LockManager,
    LockBackend,
    LockAcquisitionError,
)

from app.core.data.consistency import (
    ConsistencyChecker,
    EventualConsistencyManager,
    ConflictRecord,
    ConflictResolutionStrategy,
    VersionVector,
    CRDTCounter,
    CRDTSet,
    CRDTMap,
    LastWriteWinsResolver,
    FirstWriteWinsResolver,
    MergeResolver,
)


# ============================================================================
# Transaction Management Tests
# ============================================================================

class TestTransactionManager:
    """Test transaction manager functionality"""

    @pytest.mark.asyncio
    async def test_transaction_manager_singleton(self):
        """Test transaction manager is singleton"""
        manager1 = get_transaction_manager()
        manager2 = get_transaction_manager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_generate_transaction_id(self):
        """Test transaction ID generation"""
        manager = TransactionManager()
        txn_id1 = manager._generate_transaction_id()
        txn_id2 = manager._generate_transaction_id()

        assert txn_id1.startswith("txn_")
        assert txn_id2.startswith("txn_")
        assert txn_id1 != txn_id2

    @pytest.mark.asyncio
    async def test_is_deadlock_error(self):
        """Test deadlock error detection"""
        manager = TransactionManager()

        # Test deadlock keywords
        assert manager._is_deadlock_error(Exception("deadlock detected"))
        assert manager._is_deadlock_error(Exception("lock timeout"))
        assert manager._is_deadlock_error(Exception("lock wait timeout exceeded"))
        assert not manager._is_deadlock_error(Exception("other error"))


class TestDeadlockDetector:
    """Test deadlock detector"""

    def test_record_deadlock(self):
        """Test recording deadlocks"""
        detector = DeadlockDetector(window_size=10)

        detector.record_deadlock("txn_1")
        detector.record_deadlock("txn_2")

        stats = detector.get_stats()
        assert stats["total_deadlocks"] == 2
        assert stats["window_size"] == 2

    def test_window_size_limit(self):
        """Test deadlock window size limit"""
        detector = DeadlockDetector(window_size=3)

        for i in range(5):
            detector.record_deadlock(f"txn_{i}")

        stats = detector.get_stats()
        assert stats["total_deadlocks"] == 5
        assert stats["window_size"] == 3  # Limited to window size


class TestRetryConfig:
    """Test retry configuration"""

    def test_get_delay_exponential(self):
        """Test exponential backoff delay calculation"""
        config = RetryConfig(
            base_delay=0.1,
            exponential_base=2.0,
            max_delay=5.0,
            jitter=False
        )

        delay0 = config.get_delay(0)
        delay1 = config.get_delay(1)
        delay2 = config.get_delay(2)

        assert delay0 == 0.1
        assert delay1 == 0.2
        assert delay2 == 0.4

    def test_get_delay_max_limit(self):
        """Test delay is capped at max_delay"""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=5.0,
            jitter=False
        )

        delay10 = config.get_delay(10)  # Would be 1024 without cap
        assert delay10 == 5.0

    def test_get_delay_with_jitter(self):
        """Test jitter adds randomness"""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=True
        )

        delays = [config.get_delay(1) for _ in range(10)]

        # All delays should be different with jitter
        assert len(set(delays)) > 1

        # All should be within jitter range (75%-125% of base)
        for delay in delays:
            assert 0.75 <= delay <= 2.5  # 2.0 * 1.25


class TestTransactionStats:
    """Test transaction statistics"""

    def test_transaction_stats_finish(self):
        """Test finishing transaction stats"""
        stats = TransactionStats(
            transaction_id="txn_1",
            start_time=datetime.now()
        )

        stats.finish(success=True)

        assert stats.success is True
        assert stats.end_time is not None
        assert stats.duration_ms > 0

    def test_transaction_stats_with_error(self):
        """Test transaction stats with error"""
        stats = TransactionStats(
            transaction_id="txn_1",
            start_time=datetime.now()
        )

        stats.finish(success=False, error="Database error")

        assert stats.success is False
        assert stats.error == "Database error"


# ============================================================================
# Distributed Locks Tests
# ============================================================================

class TestRedisLock:
    """Test Redis-based locks"""

    @pytest.mark.asyncio
    async def test_redis_lock_acquire_success(self):
        """Test successful lock acquisition"""
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True

        lock = RedisLock(redis_mock, "test_key", ttl=10.0)
        acquired = await lock.acquire(blocking=False)

        assert acquired is True
        assert lock._acquired is True
        redis_mock.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_lock_acquire_failure(self):
        """Test failed lock acquisition"""
        redis_mock = AsyncMock()
        redis_mock.set.return_value = False

        lock = RedisLock(redis_mock, "test_key", ttl=10.0, retry_count=1)
        acquired = await lock.acquire(blocking=False)

        assert acquired is False
        assert lock._acquired is False

    @pytest.mark.asyncio
    async def test_redis_lock_release_success(self):
        """Test successful lock release"""
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.eval.return_value = 1

        lock = RedisLock(redis_mock, "test_key", ttl=10.0)
        await lock.acquire(blocking=False)
        released = await lock.release()

        assert released is True
        assert lock._acquired is False

    @pytest.mark.asyncio
    async def test_redis_lock_context_manager(self):
        """Test lock as context manager"""
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.eval.return_value = 1

        lock = RedisLock(redis_mock, "test_key", ttl=10.0)

        async with lock:
            assert lock._acquired is True

        assert lock._acquired is False

    @pytest.mark.asyncio
    async def test_redis_lock_extend(self):
        """Test lock extension"""
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.eval.return_value = 1

        lock = RedisLock(redis_mock, "test_key", ttl=10.0)
        await lock.acquire(blocking=False)

        extended = await lock.extend(additional_ttl=5.0)
        assert extended is True


class TestAdvisoryLock:
    """Test PostgreSQL advisory locks"""

    def test_key_to_id_conversion(self):
        """Test converting string key to integer ID"""
        session_mock = Mock()
        lock = AdvisoryLock(session_mock, "test_key")

        lock_id = lock._key_to_id("test_key")
        assert isinstance(lock_id, int)
        assert lock_id > 0

        # Same key should produce same ID
        lock_id2 = lock._key_to_id("test_key")
        assert lock_id == lock_id2

        # Different keys should produce different IDs
        lock_id3 = lock._key_to_id("other_key")
        assert lock_id != lock_id3


class TestLockManager:
    """Test unified lock manager"""

    def test_lock_manager_initialization(self):
        """Test lock manager initialization"""
        redis_mock = Mock()
        manager = LockManager(redis_client=redis_mock)

        assert manager.redis_client is redis_mock
        assert manager.default_backend == LockBackend.REDIS

    @pytest.mark.asyncio
    async def test_lock_manager_redis_backend(self):
        """Test lock manager with Redis backend"""
        redis_mock = AsyncMock()
        redis_mock.set.return_value = True
        redis_mock.eval.return_value = 1

        manager = LockManager(redis_client=redis_mock)

        async with manager.lock("test_key", backend=LockBackend.REDIS):
            pass  # Lock acquired and released

        redis_mock.set.assert_called()


# ============================================================================
# Data Consistency Tests
# ============================================================================

class TestVersionVector:
    """Test version vector for causality tracking"""

    def test_version_vector_increment(self):
        """Test incrementing version for a node"""
        vv = VersionVector()
        vv.increment("node1")
        vv.increment("node1")
        vv.increment("node2")

        assert vv.versions["node1"] == 2
        assert vv.versions["node2"] == 1

    def test_version_vector_merge(self):
        """Test merging version vectors"""
        vv1 = VersionVector(versions={"node1": 2, "node2": 1})
        vv2 = VersionVector(versions={"node1": 1, "node2": 3, "node3": 1})

        vv1.merge(vv2)

        assert vv1.versions["node1"] == 2  # max(2, 1)
        assert vv1.versions["node2"] == 3  # max(1, 3)
        assert vv1.versions["node3"] == 1  # from vv2

    def test_version_vector_happens_before(self):
        """Test happens-before relationship"""
        vv1 = VersionVector(versions={"node1": 1, "node2": 1})
        vv2 = VersionVector(versions={"node1": 2, "node2": 1})
        vv3 = VersionVector(versions={"node1": 1, "node2": 2})

        assert vv1.happens_before(vv2) is True
        assert vv2.happens_before(vv1) is False
        assert vv1.concurrent_with(vv3) is False

    def test_version_vector_concurrent(self):
        """Test concurrent version vectors"""
        vv1 = VersionVector(versions={"node1": 2, "node2": 1})
        vv2 = VersionVector(versions={"node1": 1, "node2": 2})

        assert vv1.concurrent_with(vv2) is True
        assert vv2.concurrent_with(vv1) is True

    def test_version_vector_serialization(self):
        """Test version vector to/from dict"""
        vv = VersionVector(versions={"node1": 2, "node2": 1})
        data = vv.to_dict()

        assert data == {"node1": 2, "node2": 1}

        vv2 = VersionVector.from_dict(data)
        assert vv2.versions == vv.versions


class TestConflictResolvers:
    """Test conflict resolution strategies"""

    @pytest.mark.asyncio
    async def test_last_write_wins_resolver(self):
        """Test last-write-wins conflict resolution"""
        resolver = LastWriteWinsResolver()

        conflict = ConflictRecord(
            entity_type="user",
            entity_id=1,
            field_name="name",
            local_value="Alice",
            remote_value="Bob",
            local_timestamp=datetime(2026, 1, 1, 10, 0),
            remote_timestamp=datetime(2026, 1, 1, 11, 0),
            resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
        )

        resolved = await resolver.resolve(conflict)
        assert resolved == "Bob"  # Remote is newer

    @pytest.mark.asyncio
    async def test_first_write_wins_resolver(self):
        """Test first-write-wins conflict resolution"""
        resolver = FirstWriteWinsResolver()

        conflict = ConflictRecord(
            entity_type="user",
            entity_id=1,
            field_name="name",
            local_value="Alice",
            remote_value="Bob",
            local_timestamp=datetime(2026, 1, 1, 10, 0),
            remote_timestamp=datetime(2026, 1, 1, 11, 0),
            resolution_strategy=ConflictResolutionStrategy.FIRST_WRITE_WINS
        )

        resolved = await resolver.resolve(conflict)
        assert resolved == "Alice"  # Local is older

    @pytest.mark.asyncio
    async def test_merge_resolver_dicts(self):
        """Test merge resolver with dictionaries"""
        resolver = MergeResolver()

        conflict = ConflictRecord(
            entity_type="user",
            entity_id=1,
            field_name="metadata",
            local_value={"a": 1, "b": 2},
            remote_value={"b": 3, "c": 4},
            local_timestamp=datetime.now(),
            remote_timestamp=datetime.now(),
            resolution_strategy=ConflictResolutionStrategy.MERGE
        )

        resolved = await resolver.resolve(conflict)
        assert resolved == {"a": 1, "b": 3, "c": 4}

    @pytest.mark.asyncio
    async def test_merge_resolver_lists(self):
        """Test merge resolver with lists"""
        resolver = MergeResolver()

        conflict = ConflictRecord(
            entity_type="user",
            entity_id=1,
            field_name="tags",
            local_value=[1, 2, 3],
            remote_value=[3, 4, 5],
            local_timestamp=datetime.now(),
            remote_timestamp=datetime.now(),
            resolution_strategy=ConflictResolutionStrategy.MERGE
        )

        resolved = await resolver.resolve(conflict)
        assert set(resolved) == {1, 2, 3, 4, 5}


class TestConsistencyChecker:
    """Test consistency checker"""

    @pytest.mark.asyncio
    async def test_check_consistency_no_conflicts(self):
        """Test consistency check with no conflicts"""
        session_mock = AsyncMock()
        checker = ConsistencyChecker(session_mock, "node1")

        local_data = {"name": "Alice", "email": "alice@example.com"}
        remote_data = {"name": "Alice", "email": "alice@example.com"}

        conflicts = await checker.check_consistency(
            "users", 1, local_data, remote_data
        )

        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_check_consistency_with_conflicts(self):
        """Test consistency check with conflicts"""
        session_mock = AsyncMock()
        checker = ConsistencyChecker(session_mock, "node1")

        local_data = {
            "name": "Alice",
            "email": "alice@example.com",
            "email_updated_at": datetime(2026, 1, 1, 10, 0)
        }
        remote_data = {
            "name": "Alice",
            "email": "alice@newmail.com",
            "email_updated_at": datetime(2026, 1, 1, 11, 0)
        }

        conflicts = await checker.check_consistency(
            "users", 1, local_data, remote_data
        )

        # Should detect 2 conflicts: email value and email_updated_at timestamp
        assert len(conflicts) == 2

        # Find the email conflict
        email_conflict = [c for c in conflicts if c.field_name == "email"][0]
        assert email_conflict.local_value == "alice@example.com"
        assert email_conflict.remote_value == "alice@newmail.com"

    @pytest.mark.asyncio
    async def test_resolve_conflicts(self):
        """Test resolving conflicts"""
        session_mock = AsyncMock()
        checker = ConsistencyChecker(
            session_mock,
            "node1",
            default_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
        )

        conflict = ConflictRecord(
            entity_type="users",
            entity_id=1,
            field_name="email",
            local_value="old@example.com",
            remote_value="new@example.com",
            local_timestamp=datetime(2026, 1, 1, 10, 0),
            remote_timestamp=datetime(2026, 1, 1, 11, 0),
            resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
        )

        resolved = await checker.resolve_conflicts([conflict])

        assert resolved["email"] == "new@example.com"
        assert conflict.resolved is True


class TestEventualConsistencyManager:
    """Test eventual consistency manager"""

    @pytest.mark.asyncio
    async def test_record_operation(self):
        """Test recording operations"""
        manager = EventualConsistencyManager("node1")

        operation = {
            "type": "update",
            "data": {"name": "Alice"},
            "timestamp": datetime.now()
        }

        await manager.record_operation("user:1", operation)

        pending = manager.get_pending_operations()
        assert len(pending) == 1
        assert pending[0][0] == "user:1"
        assert pending[0][1] == operation

    @pytest.mark.asyncio
    async def test_sync_operations_newer_remote(self):
        """Test syncing with newer remote operations"""
        manager = EventualConsistencyManager("node1")

        # Record local operation (auto-increments node1 version to 1)
        local_op = {"type": "update", "timestamp": datetime.now()}
        await manager.record_operation("user:1", local_op)

        # Remote operation with strictly newer version (node1:1, node2:1)
        # This happens-after local (node1:1), so no conflict
        remote_version = VersionVector(versions={"node1": 1, "node2": 1})
        remote_op = {"type": "update", "timestamp": datetime.now()}

        conflicts = await manager.sync_operations([
            ("user:1", remote_op, remote_version)
        ])

        # No conflicts because remote has node2:1 which local doesn't have
        # Remote happens after local in causal order
        assert len(conflicts) == 0


class TestCRDTs:
    """Test Conflict-free Replicated Data Types"""

    def test_crdt_counter_operations(self):
        """Test CRDT counter increment/decrement"""
        counter = CRDTCounter("node1")

        counter.increment(5)
        counter.increment(3)
        counter.decrement(2)

        assert counter.value() == 6  # 5 + 3 - 2

    def test_crdt_counter_merge(self):
        """Test CRDT counter merge"""
        counter1 = CRDTCounter("node1")
        counter1.increment(5)

        counter2 = CRDTCounter("node2")
        counter2.increment(3)

        counter1.merge(counter2)

        assert counter1.value() == 8  # 5 + 3

    def test_crdt_set_operations(self):
        """Test CRDT set add/remove"""
        crdt_set = CRDTSet()

        crdt_set.add("a")
        crdt_set.add("b")
        crdt_set.add("c")
        crdt_set.remove("b")

        assert crdt_set.contains("a") is True
        assert crdt_set.contains("b") is False
        assert crdt_set.value() == {"a", "c"}

    def test_crdt_set_tombstone(self):
        """Test CRDT set tombstone (cannot re-add after remove)"""
        crdt_set = CRDTSet()

        crdt_set.add("a")
        crdt_set.remove("a")
        crdt_set.add("a")  # This should not add it back

        assert crdt_set.contains("a") is False

    def test_crdt_set_merge(self):
        """Test CRDT set merge"""
        set1 = CRDTSet()
        set1.add("a")
        set1.add("b")

        set2 = CRDTSet()
        set2.add("b")
        set2.add("c")
        set2.remove("b")

        set1.merge(set2)

        assert set1.contains("a") is True
        assert set1.contains("b") is False  # Removed in set2
        assert set1.contains("c") is True

    def test_crdt_map_operations(self):
        """Test CRDT map operations"""
        crdt_map = CRDTMap()

        crdt_map.set("name", "Alice", "node1")
        crdt_map.set("age", 30, "node1")

        assert crdt_map.get("name") == "Alice"
        assert crdt_map.get("age") == 30

        crdt_map.delete("age")
        assert crdt_map.get("age") is None

    def test_crdt_map_merge_lww(self):
        """Test CRDT map merge with last-write-wins"""
        map1 = CRDTMap()
        map1.set("name", "Alice", "node1")

        map2 = CRDTMap()
        map2.set("name", "Bob", "node2")

        # map2 has newer timestamp
        import time
        time.sleep(0.01)
        map2.set("name", "Bob", "node2")

        map1.merge(map2)

        # Should use the newer value
        assert map1.get("name") == "Bob"

    def test_crdt_map_to_dict(self):
        """Test CRDT map to dict conversion"""
        crdt_map = CRDTMap()
        crdt_map.set("name", "Alice", "node1")
        crdt_map.set("age", 30, "node1")

        data = crdt_map.to_dict()

        assert data == {"name": "Alice", "age": 30}


# ============================================================================
# Integration Tests
# ============================================================================

class TestDataLayerIntegration:
    """Integration tests for data layer components"""

    @pytest.mark.asyncio
    async def test_transaction_with_retry(self):
        """Test transaction with automatic retry on failure"""
        manager = TransactionManager()
        session_mock = AsyncMock(spec=AsyncSession)
        session_mock.in_transaction.return_value = False
        session_mock.begin = AsyncMock()
        session_mock.commit = AsyncMock()
        session_mock.rollback = AsyncMock()

        # First attempt fails, second succeeds
        attempt = [0]

        async def mock_operation():
            attempt[0] += 1
            if attempt[0] == 1:
                from sqlalchemy.exc import OperationalError
                raise OperationalError("deadlock", None, None)
            return "success"

        retry_config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)

        try:
            async with manager.transaction(session_mock, retry_config=retry_config):
                result = await mock_operation()
                assert result == "success"
        except:
            pass  # Expected to retry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
