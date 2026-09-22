"""
Week 2 - Day 5: 实现事件总线（EventBus）
这是实现数据主权架构的核心基础设施
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)


class Event:
    """事件对象"""

    def __init__(self, event_type: str, data: Dict[str, Any], source: str = "unknown"):
        self.event_id = self._generate_event_id()
        self.event_type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.now()
        self.processed_by = []

    def _generate_event_id(self) -> str:
        """生成事件 ID"""
        import uuid
        return f"evt_{uuid.uuid4().hex[:12]}"

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "processed_by": self.processed_by
        }


class EventBus:
    """
    事件总线：实现发布-订阅模式

    核心功能：
    1. 发布事件（publish）
    2. 订阅事件（on 装饰器）
    3. 事件日志记录
    4. 异步处理订阅者
    5. 错误处理和重试
    """

    def __init__(self, enable_logging: bool = True, max_log_size: int = 10000):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_log: List[Event] = []
        self.enable_logging = enable_logging
        self.max_log_size = max_log_size
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0
        }
        logger.info("EventBus 初始化完成")

    def publish(self, event_type: str, data: Dict[str, Any], source: str = "unknown") -> Event:
        """
        发布事件

        Args:
            event_type: 事件类型（如 "entity.created"）
            data: 事件数据
            source: 事件来源

        Returns:
            Event 对象
        """
        event = Event(event_type, data, source)

        # 记录事件日志
        if self.enable_logging:
            self._log_event(event)

        # 更新统计
        self.stats["events_published"] += 1

        # 通知所有订阅者
        if event_type in self.subscribers:
            logger.debug(f"事件 {event_type} 有 {len(self.subscribers[event_type])} 个订阅者")

            for subscriber in self.subscribers[event_type]:
                try:
                    # 异步执行订阅者
                    asyncio.create_task(self._execute_subscriber(subscriber, event))
                except RuntimeError:
                    # 如果没有运行中的事件循环，同步执行
                    try:
                        if asyncio.iscoroutinefunction(subscriber):
                            # 如果是异步函数，需要在新的事件循环中运行
                            asyncio.run(self._execute_subscriber(subscriber, event))
                        else:
                            # 同步函数直接执行
                            self._execute_subscriber_sync(subscriber, event)
                    except Exception as e:
                        logger.error(f"订阅者 {subscriber.__name__} 执行失败: {e}")
                        self.stats["events_failed"] += 1
        else:
            logger.debug(f"事件 {event_type} 没有订阅者")

        return event

    async def _execute_subscriber(self, subscriber: Callable, event: Event):
        """异步执行订阅者"""
        try:
            subscriber_name = subscriber.__name__
            logger.debug(f"执行订阅者: {subscriber_name} for event {event.event_type}")

            if asyncio.iscoroutinefunction(subscriber):
                await subscriber(event)
            else:
                subscriber(event)

            event.processed_by.append(subscriber_name)
            self.stats["events_processed"] += 1
            logger.debug(f"订阅者 {subscriber_name} 执行成功")

        except Exception as e:
            logger.error(f"订阅者 {subscriber.__name__} 处理事件 {event.event_type} 失败: {e}")
            self.stats["events_failed"] += 1
            raise

    def _execute_subscriber_sync(self, subscriber: Callable, event: Event):
        """同步执行订阅者"""
        try:
            subscriber_name = subscriber.__name__
            logger.debug(f"同步执行订阅者: {subscriber_name} for event {event.event_type}")

            subscriber(event)

            event.processed_by.append(subscriber_name)
            self.stats["events_processed"] += 1
            logger.debug(f"订阅者 {subscriber_name} 执行成功")

        except Exception as e:
            logger.error(f"订阅者 {subscriber.__name__} 处理事件 {event.event_type} 失败: {e}")
            self.stats["events_failed"] += 1

    def on(self, event_type: str):
        """
        订阅事件（装饰器）

        用法:
            @event_bus.on("entity.created")
            def handle_entity_created(event):
                ...

            @event_bus.on("entity.created")
            async def handle_entity_created_async(event):
                ...
        """

        def decorator(func: Callable):
            self.subscribers[event_type].append(func)
            logger.info(f"注册订阅者: {func.__name__} for event {event_type}")
            return func

        return decorator

    def _log_event(self, event: Event):
        """记录事件日志"""
        self.event_log.append(event)

        # 限制日志大小
        if len(self.event_log) > self.max_log_size:
            self.event_log = self.event_log[-self.max_log_size:]

    def get_event_log(self,
                     event_type: Optional[str] = None,
                     entity_id: Optional[str] = None,
                     limit: int = 100) -> List[Dict]:
        """
        获取事件日志

        Args:
            event_type: 筛选事件类型
            entity_id: 筛选包含此 entity_id 的事件
            limit: 返回最多多少条

        Returns:
            事件列表
        """
        filtered_events = self.event_log

        # 按事件类型筛选
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]

        # 按 entity_id 筛选
        if entity_id:
            filtered_events = [
                e for e in filtered_events
                if entity_id in str(e.data)
            ]

        # 限制数量
        filtered_events = filtered_events[-limit:]

        return [e.to_dict() for e in filtered_events]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "subscribers_count": sum(len(subs) for subs in self.subscribers.values()),
            "event_types": list(self.subscribers.keys()),
            "log_size": len(self.event_log)
        }

    def clear_log(self):
        """清空事件日志"""
        self.event_log.clear()
        logger.info("事件日志已清空")

    def unsubscribe(self, event_type: str, subscriber: Callable):
        """取消订阅"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(subscriber)
                logger.info(f"取消订阅: {subscriber.__name__} from event {event_type}")
            except ValueError:
                logger.warning(f"订阅者 {subscriber.__name__} 不存在于事件 {event_type}")


# 全局单例
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线单例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


# ===== 测试代码 =====

def test_event_bus():
    """测试事件总线"""
    print("=" * 60)
    print("测试事件总线")
    print("=" * 60)

    # 创建事件总线
    bus = EventBus(enable_logging=True)

    # 定义订阅者（同步）
    @bus.on("test.event")
    def sync_handler(event: Event):
        print(f"  同步处理器收到事件: {event.event_type}")
        print(f"    数据: {event.data}")

    # 定义订阅者（异步）
    @bus.on("test.event")
    async def async_handler(event: Event):
        print(f"  异步处理器收到事件: {event.event_type}")
        await asyncio.sleep(0.1)  # 模拟异步操作
        print(f"    异步处理完成")

    # 发布事件
    print("\n发布事件: test.event")
    event = bus.publish("test.event", {"name": "测试", "value": 123}, source="test")

    # 等待异步处理完成
    import time
    time.sleep(0.2)

    # 检查统计
    print("\n统计信息:")
    stats = bus.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 检查日志
    print("\n事件日志:")
    logs = bus.get_event_log(limit=5)
    for log in logs:
        print(f"  {log['event_type']} @ {log['timestamp']}")

    print("\n✅ 事件总线测试完成")


def test_entity_events():
    """测试实体相关事件"""
    print("\n" + "=" * 60)
    print("测试实体事件")
    print("=" * 60)

    bus = EventBus(enable_logging=True)

    # 模拟订阅者
    entity_created_count = 0
    entity_updated_count = 0

    @bus.on("entity.created")
    def on_entity_created(event: Event):
        nonlocal entity_created_count
        entity_created_count += 1
        print(f"  ✅ 实体创建: {event.data['entity_id']} - {event.data['name']}")

    @bus.on("entity.updated")
    def on_entity_updated(event: Event):
        nonlocal entity_updated_count
        entity_updated_count += 1
        print(f"  ✅ 实体更新: {event.data['entity_id']}")

    # 发布事件
    print("\n发布实体事件:")
    bus.publish("entity.created", {
        "entity_id": "ent_123456789abc",
        "name": "王大爷",
        "type": "person"
    }, source="test")

    bus.publish("entity.updated", {
        "entity_id": "ent_123456789abc",
        "mention_count": 10
    }, source="test")

    bus.publish("entity.created", {
        "entity_id": "ent_abcdef123456",
        "name": "山歌",
        "type": "concept"
    }, source="test")

    # 检查结果
    print(f"\n处理统计:")
    print(f"  entity.created 事件: {entity_created_count} 次")
    print(f"  entity.updated 事件: {entity_updated_count} 次")

    # 检查特定实体的日志
    print(f"\n查询特定实体的事件:")
    logs = bus.get_event_log(entity_id="ent_123456789abc")
    for log in logs:
        print(f"  {log['event_type']} @ {log['timestamp']}")

    print("\n✅ 实体事件测试完成")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行测试
    test_event_bus()
    test_entity_events()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)
