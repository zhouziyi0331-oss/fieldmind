"""轻量级Agent消息总线。

当前用于让SuperAgents模块可导入、可运行；后续可替换为Redis或事件流实现。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20


@dataclass
class AgentMessage:
    topic: str
    payload: Dict[str, Any]
    sender: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)


class AgentMessageBus:
    """进程内发布订阅消息总线。"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[AgentMessage], Any]]] = {}
        self._history: List[AgentMessage] = []

    def subscribe(self, topic: str, handler: Callable[[AgentMessage], Any]) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        sender: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> AgentMessage:
        message = AgentMessage(topic=topic, payload=payload, sender=sender, priority=priority)
        self._history.append(message)

        for handler in self._subscribers.get(topic, []):
            try:
                handler(message)
            except Exception as e:
                logger.warning(f"Agent消息处理失败 topic={topic}: {e}")

        return message

    def history(self, topic: Optional[str] = None) -> List[AgentMessage]:
        if topic is None:
            return list(self._history)
        return [message for message in self._history if message.topic == topic]
