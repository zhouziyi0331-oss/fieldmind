"""
测试 Phase 6.3: 事件驱动架构

测试:
- 事件总线
- 事件溯源
- CQRS模式
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.integration import (
    # 事件总线
    Event, EventPriority, EventBus, EventBusConfig,
    EventRouter, EventAggregator,
    # 事件溯源
    EventStore, InMemoryEventStore, AggregateRoot,
    Repository, EventProjector, EventReplayer,
    StoredEvent, Snapshot,
    # CQRS
    Command, Query, CommandResult, QueryResult, CommandStatus,
    CommandHandler, QueryHandler, CommandBus, QueryBus,
    ReadModel, InMemoryReadModel, ReadModelProjector,
    CQRSFacade, CreateUserCommand, GetUserQuery, ListUsersQuery
)


# ==================== 事件总线测试 ====================

@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    """测试事件发布和订阅"""
    bus = EventBus()
    await bus.start()

    received_events = []

    def handler(event: Event):
        received_events.append(event)

    # 订阅
    handler_id = bus.subscribe("user.*", handler)

    # 发布事件
    event = Event(
        event_type="user.created",
        source="test",
        data={"user_id": "123"}
    )

    await bus.publish(event)
    await asyncio.sleep(0.1)  # 等待处理

    # 验证
    assert len(received_events) == 1
    assert received_events[0].event_type == "user.created"

    # 取消订阅
    assert bus.unsubscribe(handler_id)

    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_priority():
    """测试事件优先级"""
    bus = EventBus()
    await bus.start()

    received_order = []

    def handler(event: Event):
        received_order.append(event.event_type)

    bus.subscribe("*", handler)

    # 发布不同优先级的事件
    await bus.publish(Event(
        event_type="low",
        priority=EventPriority.LOW
    ))

    await bus.publish(Event(
        event_type="critical",
        priority=EventPriority.CRITICAL
    ))

    await bus.publish(Event(
        event_type="high",
        priority=EventPriority.HIGH
    ))

    await asyncio.sleep(0.5)
    await bus.stop()

    # 高优先级应该先处理
    assert received_order[0] == "critical"
    assert received_order[1] == "high"
    assert received_order[2] == "low"


@pytest.mark.asyncio
async def test_event_bus_pattern_matching():
    """测试事件模式匹配"""
    bus = EventBus()
    await bus.start()

    user_events = []
    order_events = []
    all_events = []

    bus.subscribe("user.*", lambda e: user_events.append(e))
    bus.subscribe("order.*", lambda e: order_events.append(e))
    bus.subscribe("*", lambda e: all_events.append(e))

    # 发布不同类型的事件
    await bus.publish(Event(event_type="user.created"))
    await bus.publish(Event(event_type="user.updated"))
    await bus.publish(Event(event_type="order.placed"))

    await asyncio.sleep(0.3)
    await bus.stop()

    assert len(user_events) == 2
    assert len(order_events) == 1
    assert len(all_events) == 3


@pytest.mark.asyncio
async def test_event_bus_filter():
    """测试事件过滤"""
    bus = EventBus()
    await bus.start()

    filtered_events = []

    def filter_func(event: Event) -> bool:
        return event.data.get("status") == "active"

    bus.subscribe(
        "user.*",
        lambda e: filtered_events.append(e),
        filter_func=filter_func
    )

    # 发布事件
    await bus.publish(Event(
        event_type="user.created",
        data={"status": "active"}
    ))

    await bus.publish(Event(
        event_type="user.created",
        data={"status": "inactive"}
    ))

    await asyncio.sleep(0.3)
    await bus.stop()

    # 只有active的应该被接收
    assert len(filtered_events) == 1
    assert filtered_events[0].data["status"] == "active"


@pytest.mark.asyncio
async def test_event_router():
    """测试事件路由器"""
    router = EventRouter()

    route1_called = []
    route2_called = []

    # 添加路由规则
    router.add_route(
        condition=lambda e: e.event_type.startswith("user"),
        target=lambda e: route1_called.append(e)
    )

    router.add_route(
        condition=lambda e: e.priority == EventPriority.HIGH,
        target=lambda e: route2_called.append(e)
    )

    # 路由事件
    event1 = Event(event_type="user.created")
    event2 = Event(event_type="order.placed", priority=EventPriority.HIGH)

    await router.route(event1)
    await router.route(event2)

    assert len(route1_called) == 1
    assert len(route2_called) == 1


@pytest.mark.asyncio
async def test_event_aggregator():
    """测试事件聚合器"""
    aggregator = EventAggregator(
        aggregation_key=lambda e: e.data.get("user_id"),
        aggregation_window=0.2,
        max_events=3
    )

    aggregated_events = []

    async def callback(events: List[Event]):
        aggregated_events.extend(events)

    # 添加事件
    for i in range(5):
        event = Event(
            event_type="user.action",
            data={"user_id": "123", "action": i}
        )
        await aggregator.add_event(event, callback)

    # 等待聚合
    await asyncio.sleep(0.5)

    # 应该有5个事件被聚合
    assert len(aggregated_events) == 5


# ==================== 事件溯源测试 ====================

class UserAggregate(AggregateRoot):
    """用户聚合（示例）"""

    def __init__(self, aggregate_id: str = None):
        super().__init__(aggregate_id)
        self.username = ""
        self.email = ""
        self.status = "pending"

    def get_aggregate_type(self) -> str:
        return "User"

    def apply_event(self, event: Event) -> None:
        if event.event_type == "user.created":
            self.username = event.data.get("username", "")
            self.email = event.data.get("email", "")
        elif event.event_type == "user.activated":
            self.status = "active"
        elif event.event_type == "user.deactivated":
            self.status = "inactive"

    def create(self, username: str, email: str):
        """创建用户"""
        event = Event(
            event_type="user.created",
            source=f"User:{self.aggregate_id}",
            data={"username": username, "email": email}
        )
        self.raise_event(event)

    def activate(self):
        """激活用户"""
        event = Event(
            event_type="user.activated",
            source=f"User:{self.aggregate_id}"
        )
        self.raise_event(event)

    def get_state(self) -> Dict[str, Any]:
        state = super().get_state()
        state.update({
            "username": self.username,
            "email": self.email,
            "status": self.status
        })
        return state


@pytest.mark.asyncio
async def test_event_store_append_and_get():
    """测试事件存储"""
    store = InMemoryEventStore()

    # 追加事件
    event = Event(
        event_type="user.created",
        data={"username": "john"}
    )

    stored = await store.append_event(
        aggregate_id="user-123",
        aggregate_type="User",
        event=event
    )

    assert stored.version == 1
    assert stored.aggregate_id == "user-123"

    # 获取事件
    events = await store.get_events("user-123")
    assert len(events) == 1
    assert events[0].event_type == "user.created"


@pytest.mark.asyncio
async def test_aggregate_root():
    """测试聚合根"""
    user = UserAggregate()

    # 创建用户
    user.create("john", "john@example.com")

    assert user.username == "john"
    assert user.email == "john@example.com"
    assert user.version == 1

    # 激活用户
    user.activate()

    assert user.status == "active"
    assert user.version == 2

    # 获取未提交事件
    uncommitted = user.get_uncommitted_events()
    assert len(uncommitted) == 2


@pytest.mark.asyncio
async def test_repository_save_and_load():
    """测试仓储保存和加载"""
    store = InMemoryEventStore()
    repo = Repository(store, snapshot_frequency=10)

    # 创建并保存聚合
    user = UserAggregate()
    user.create("john", "john@example.com")
    user.activate()

    await repo.save(user)

    # 加载聚合
    loaded_user = await repo.get_by_id(UserAggregate, user.aggregate_id)

    assert loaded_user is not None
    assert loaded_user.username == "john"
    assert loaded_user.email == "john@example.com"
    assert loaded_user.status == "active"
    assert loaded_user.version == 2


@pytest.mark.asyncio
async def test_snapshot():
    """测试快照"""
    store = InMemoryEventStore()
    repo = Repository(store, snapshot_frequency=2)

    # 创建聚合并触发快照
    user = UserAggregate()
    user.create("john", "john@example.com")
    user.activate()

    await repo.save(user)

    # 获取快照
    snapshot = await store.get_snapshot(user.aggregate_id)

    assert snapshot is not None
    assert snapshot.version == 2
    assert snapshot.state["username"] == "john"


@pytest.mark.asyncio
async def test_event_projector():
    """测试事件投影器"""
    store = InMemoryEventStore()
    projector = EventProjector(store)

    projection_results = {}

    # 注册投影函数
    def project_user_created(event: Event):
        projection_results[event.event_id] = {
            "type": "user_created",
            "username": event.data.get("username")
        }

    projector.register_projection("user.created", project_user_created)

    # 添加事件到存储
    event = Event(
        event_type="user.created",
        data={"username": "john"}
    )

    await store.append_event("user-123", "User", event)

    # 执行投影
    results = await projector.project_all()

    assert len(results) > 0


@pytest.mark.asyncio
async def test_event_replayer():
    """测试事件回放"""
    store = InMemoryEventStore()
    repo = Repository(store)
    replayer = EventReplayer(store, repo)

    # 创建用户历史
    user = UserAggregate()
    user.create("john", "john@example.com")
    await repo.save(user)

    # 回放到版本1
    replayed = await replayer.replay_to_version(
        UserAggregate,
        user.aggregate_id,
        1
    )

    assert replayed is not None
    assert replayed.username == "john"
    assert replayed.version == 1


# ==================== CQRS测试 ====================

class CreateUserCommandHandler(CommandHandler[CreateUserCommand]):
    """创建用户命令处理器"""

    def __init__(self, users: Dict[str, Dict]):
        self.users = users

    async def handle(self, command: CreateUserCommand) -> CommandResult:
        start_time = datetime.now()

        try:
            # 模拟创建用户
            user_id = f"user-{len(self.users) + 1}"
            self.users[user_id] = {
                "id": user_id,
                "username": command.username,
                "email": command.email
            }

            execution_time = (datetime.now() - start_time).total_seconds()

            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.SUCCEEDED,
                result={"user_id": user_id},
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )


class GetUserQueryHandler(QueryHandler[GetUserQuery, Dict]):
    """获取用户查询处理器"""

    def __init__(self, users: Dict[str, Dict]):
        self.users = users

    async def handle(self, query: GetUserQuery) -> QueryResult[Dict]:
        start_time = datetime.now()

        try:
            user = self.users.get(query.user_id)

            execution_time = (datetime.now() - start_time).total_seconds()

            return QueryResult(
                query_id=query.query_id,
                result=user,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return QueryResult(
                query_id=query.query_id,
                error=str(e),
                execution_time=execution_time
            )


@pytest.mark.asyncio
async def test_command_bus():
    """测试命令总线"""
    users = {}
    command_bus = CommandBus()

    # 注册处理器
    handler = CreateUserCommandHandler(users)
    command_bus.register_handler(CreateUserCommand, handler)

    # 执行命令
    command = CreateUserCommand(
        username="john",
        email="john@example.com"
    )

    result = await command_bus.execute(command)

    assert result.is_success()
    assert "user_id" in result.result
    assert len(users) == 1


@pytest.mark.asyncio
async def test_query_bus():
    """测试查询总线"""
    users = {"user-1": {"id": "user-1", "username": "john"}}
    query_bus = QueryBus()

    # 注册处理器
    handler = GetUserQueryHandler(users)
    query_bus.register_handler(GetUserQuery, handler)

    # 执行查询
    query = GetUserQuery(user_id="user-1")
    result = await query_bus.execute(query)

    assert result.is_success()
    assert result.result["username"] == "john"


@pytest.mark.asyncio
async def test_query_bus_cache():
    """测试查询缓存"""
    users = {"user-1": {"id": "user-1", "username": "john"}}
    query_bus = QueryBus()
    query_bus.set_cache_ttl(60.0)

    handler = GetUserQueryHandler(users)
    query_bus.register_handler(GetUserQuery, handler)

    # 第一次查询
    query = GetUserQuery(user_id="user-1")
    result1 = await query_bus.execute(query, use_cache=True)

    # 第二次查询（应该从缓存）
    result2 = await query_bus.execute(query, use_cache=True)

    assert result1.is_success()
    assert result2.is_success()
    assert result2.from_cache is True


@pytest.mark.asyncio
async def test_read_model():
    """测试读模型"""
    read_model = InMemoryReadModel()

    # 从事件更新
    event = Event(
        event_type="user.created",
        data={"id": "user-1", "username": "john"}
    )

    await read_model.update_from_event(event)

    # 查询
    user = await read_model.get("user-1")
    assert user is not None
    assert user["username"] == "john"

    # 条件查询
    results = await read_model.query({"username": "john"})
    assert len(results) == 1


@pytest.mark.asyncio
async def test_read_model_projector():
    """测试读模型投影器"""
    event_bus = EventBus()
    await event_bus.start()

    read_model = InMemoryReadModel()
    projector = ReadModelProjector(event_bus, read_model)

    # 启动投影
    projector.start(["user.*"])

    # 发布事件
    event = Event(
        event_type="user.created",
        data={"id": "user-1", "username": "john"}
    )

    await event_bus.publish(event, wait=True)

    # 验证读模型
    await asyncio.sleep(0.2)
    user = await read_model.get("user-1")
    assert user is not None

    projector.stop()
    await event_bus.stop()


@pytest.mark.asyncio
async def test_cqrs_facade():
    """测试CQRS门面"""
    # 设置
    event_bus = EventBus()
    await event_bus.start()

    event_store = InMemoryEventStore()
    repo = Repository(event_store)
    command_bus = CommandBus(event_bus)
    query_bus = QueryBus()

    facade = CQRSFacade(
        command_bus, query_bus, event_bus, event_store, repo
    )

    # 注册处理器
    users = {}
    facade.register_command_handler(
        CreateUserCommand,
        CreateUserCommandHandler(users)
    )
    facade.register_query_handler(
        GetUserQuery,
        GetUserQueryHandler(users)
    )

    # 执行命令
    command = CreateUserCommand(username="john", email="john@example.com")
    cmd_result = await facade.execute_command(command)

    assert cmd_result.is_success()

    # 执行查询
    user_id = cmd_result.result["user_id"]
    query = GetUserQuery(user_id=user_id)
    query_result = await facade.execute_query(query)

    assert query_result.is_success()
    assert query_result.result["username"] == "john"

    await event_bus.stop()


# ==================== 集成测试 ====================

@pytest.mark.asyncio
async def test_full_event_driven_flow():
    """测试完整的事件驱动流程"""
    # 1. 设置事件总线
    event_bus = EventBus()
    await event_bus.start()

    # 2. 设置事件存储和仓储
    event_store = InMemoryEventStore()
    repo = Repository(event_store)

    # 3. 创建聚合
    user = UserAggregate()
    user.create("john", "john@example.com")
    user.activate()

    # 4. 获取未提交的事件（在保存前）
    uncommitted_events = user.get_uncommitted_events()
    assert len(uncommitted_events) >= 2

    # 5. 保存聚合
    await repo.save(user)

    # 6. 发布事件到总线
    for event in uncommitted_events:
        await event_bus.publish(event)
    await asyncio.sleep(0.1)  # 等待处理

    # 7. 验证
    loaded = await repo.get_by_id(UserAggregate, user.aggregate_id)
    assert loaded.status == "active"

    metrics = event_bus.get_metrics()
    assert metrics.total_published >= 2

    await event_bus.stop()


@pytest.mark.asyncio
async def test_cqrs_with_event_sourcing():
    """测试CQRS与事件溯源集成"""
    # 设置基础设施
    event_bus = EventBus()
    await event_bus.start()

    event_store = InMemoryEventStore()
    repo = Repository(event_store)
    command_bus = CommandBus(event_bus)
    query_bus = QueryBus()

    facade = CQRSFacade(
        command_bus, query_bus, event_bus, event_store, repo
    )

    # 注册读模型
    read_model = InMemoryReadModel()
    facade.register_read_model(
        "users",
        read_model,
        ["user.*"]
    )

    # 发布用户创建事件
    event = Event(
        event_type="user.created",
        data={"id": "user-1", "username": "john", "email": "john@example.com"}
    )

    await event_bus.publish(event, wait=True)
    await asyncio.sleep(0.2)

    # 从读模型查询
    user = await read_model.get("user-1")
    assert user is not None
    assert user["username"] == "john"

    await event_bus.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
