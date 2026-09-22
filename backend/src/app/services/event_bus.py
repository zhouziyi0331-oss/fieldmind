"""
事件总线服务
Event Bus Service

统一的事件发布订阅机制，连接所有模块
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Any, Callable, Optional
import json
import uuid
import logging
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.database import SessionLocal
from app.models.unified_models import SystemEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    事件总线

    功能：
    1. 发布事件
    2. 订阅事件
    3. 异步事件处理
    4. 事件重试机制
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self._subscribers: Dict[str, List[Callable]] = {}
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._running = False

    def subscribe(self, event_type: str, handler: Callable):
        """
        订阅事件

        Args:
            event_type: 事件类型（如：'document.uploaded'）
            handler: 处理函数
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)
        logger.info(f"📥 订阅事件: {event_type} -> {handler.__name__}")

    def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        publisher: str,
        priority: int = 5,
        category: str = None
    ) -> str:
        """
        发布事件

        Args:
            event_type: 事件类型
            payload: 事件数据
            publisher: 发布者
            priority: 优先级（1-10，越小越高）
            category: 事件类别

        Returns:
            event_id: 事件 ID
        """
        db = SessionLocal()

        try:
            event_id = f"evt_{uuid.uuid4().hex[:16]}"

            # 自动推断类别
            if not category:
                category = event_type.split('.')[0]

            # 获取订阅者列表
            subscribers = list(self._subscribers.get(event_type, []))
            subscriber_names = [h.__name__ for h in subscribers]

            # 创建事件记录
            event = SystemEvent(
                event_id=event_id,
                event_type=event_type,
                event_category=category,
                payload=json.dumps(payload, ensure_ascii=False),
                publisher=publisher,
                subscribers=json.dumps(subscriber_names, ensure_ascii=False),
                status='published',
                priority=priority,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )

            db.add(event)
            db.commit()

            logger.info(f"📤 发布事件: {event_type} (ID: {event_id}, 订阅者: {len(subscribers)})")

            # 异步处理事件
            if subscribers:
                self._executor.submit(self._process_event, event_id, event_type, payload, subscribers)

            return event_id

        except Exception as e:
            db.rollback()
            logger.error(f"发布事件失败: {e}", exc_info=True)
            raise
        finally:
            db.close()

    def _process_event(
        self,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        subscribers: List[Callable]
    ):
        """
        处理事件（在后台线程中执行）

        Args:
            event_id: 事件 ID
            event_type: 事件类型
            payload: 事件数据
            subscribers: 订阅者列表
        """
        db = SessionLocal()
        consumed_by = []

        try:
            # 更新状态为处理中
            db.execute(text("""
                UPDATE system_events
                SET status = 'processing'
                WHERE event_id = :event_id
            """), {'event_id': event_id})
            db.commit()

            # 调用所有订阅者
            for handler in subscribers:
                try:
                    logger.info(f"🔄 处理事件: {event_type} -> {handler.__name__}")
                    handler(payload)
                    consumed_by.append(handler.__name__)
                    logger.info(f"✅ 处理完成: {event_type} -> {handler.__name__}")
                except Exception as e:
                    logger.error(f"❌ 处理失败: {event_type} -> {handler.__name__}: {e}", exc_info=True)

            # 更新状态为已消费
            db.execute(text("""
                UPDATE system_events
                SET status = 'consumed',
                    consumed_by = :consumed_by,
                    consumed_at = CURRENT_TIMESTAMP
                WHERE event_id = :event_id
            """), {
                'event_id': event_id,
                'consumed_by': json.dumps(consumed_by, ensure_ascii=False)
            })
            db.commit()

        except Exception as e:
            logger.error(f"处理事件失败: {e}", exc_info=True)

            # 更新状态为失败
            db.execute(text("""
                UPDATE system_events
                SET status = 'failed',
                    retry_count = retry_count + 1
                WHERE event_id = :event_id
            """), {'event_id': event_id})
            db.commit()
        finally:
            db.close()

    def start(self):
        """启动事件总线"""
        self._running = True
        logger.info("🚀 事件总线已启动")

    def stop(self):
        """停止事件总线"""
        self._running = False
        self._executor.shutdown(wait=True)
        logger.info("🛑 事件总线已停止")

    def get_pending_events(self, limit: int = 100) -> List[Dict]:
        """
        获取待处理事件（用于重试）

        Returns:
            待处理事件列表
        """
        db = SessionLocal()

        try:
            results = db.execute(text("""
                SELECT event_id, event_type, payload, retry_count, max_retries
                FROM system_events
                WHERE status = 'failed'
                  AND retry_count < max_retries
                  AND expires_at > CURRENT_TIMESTAMP
                ORDER BY priority, created_at
                LIMIT :limit
            """), {'limit': limit}).fetchall()

            return [
                {
                    'event_id': row[0],
                    'event_type': row[1],
                    'payload': json.loads(row[2]),
                    'retry_count': row[3],
                    'max_retries': row[4]
                }
                for row in results
            ]
        finally:
            db.close()

    def retry_failed_events(self):
        """重试失败的事件"""
        pending = self.get_pending_events()

        for event in pending:
            logger.info(f"🔄 重试事件: {event['event_type']} (尝试 {event['retry_count']}/{event['max_retries']})")

            subscribers = self._subscribers.get(event['event_type'], [])
            if subscribers:
                self._executor.submit(
                    self._process_event,
                    event['event_id'],
                    event['event_type'],
                    event['payload'],
                    subscribers
                )


# 全局事件总线实例
event_bus = EventBus()


# ============================================================
# 事件类型定义（常量）
# ============================================================

class EventTypes:
    """事件类型常量"""

    # 文档事件
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"

    # 流水线事件
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_STEP_COMPLETED = "pipeline.step_completed"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"

    # 知识事件
    ENTITIES_EXTRACTED = "knowledge.entities_extracted"
    EVENTS_EXTRACTED = "knowledge.events_extracted"
    RELATIONSHIPS_DISCOVERED = "knowledge.relationships_discovered"
    ONTOLOGY_BUILT = "knowledge.ontology_built"
    INFERENCE_COMPLETED = "knowledge.inference_completed"
    KNOWLEDGE_UNITS_CREATED = "knowledge.knowledge_units_created"

    # 知识图谱事件
    KG_NODE_CREATED = "kg.node_created"
    KG_EDGE_CREATED = "kg.edge_created"
    KG_UPDATED = "kg.updated"

    # 缩影事件
    SUMMARY_GENERATED = "summary.generated"
    SUMMARY_UPDATED = "summary.updated"

    # 分析事件
    ANALYSIS_COMPLETED = "analysis.completed"
    PATTERN_DISCOVERED = "analysis.pattern_discovered"

    # 技能事件
    SKILL_LEARNED = "skill.learned"
    SKILL_VALIDATED = "skill.validated"

    # 工作流事件
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"


# ============================================================
# 辅助函数
# ============================================================

def publish_event(
    event_type: str,
    payload: Dict[str, Any],
    publisher: str,
    priority: int = 5
) -> str:
    """
    发布事件的便捷函数

    Args:
        event_type: 事件类型
        payload: 事件数据
        publisher: 发布者
        priority: 优先级

    Returns:
        event_id: 事件 ID
    """
    return event_bus.publish(event_type, payload, publisher, priority)


def subscribe_event(event_type: str, handler: Callable):
    """
    订阅事件的便捷函数

    Args:
        event_type: 事件类型
        handler: 处理函数
    """
    event_bus.subscribe(event_type, handler)


# ============================================================
# 装饰器
# ============================================================

def event_handler(event_type: str):
    """
    事件处理器装饰器

    用法：
        @event_handler('document.uploaded')
        def handle_document_uploaded(payload):
            print(f"处理文档上传: {payload['document_id']}")
    """
    def decorator(func: Callable):
        event_bus.subscribe(event_type, func)
        return func
    return decorator


# ============================================================
# 初始化
# ============================================================

def init_event_bus():
    """初始化事件总线"""
    event_bus.start()
    logger.info("✅ 事件总线初始化完成")


def cleanup_event_bus():
    """清理事件总线"""
    event_bus.stop()
    logger.info("✅ 事件总线清理完成")
