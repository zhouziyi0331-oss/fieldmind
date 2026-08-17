"""
Agent消息总线 - Agent协同网络的神经系统

设计理念：
1. 发布-订阅模式：Agent之间松耦合通信
2. 直接请求模式：Agent之间同步调用
3. 消息持久化：可追溯、可审计
4. 异步非阻塞：高性能

核心价值：
- Agent自主协作，无需中央调度
- 消息驱动，事件响应
- 可观测性：每条消息都有日志
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20


class MessageType(Enum):
    """消息类型"""
    EVENT = "event"           # 事件通知（发布-订阅）
    REQUEST = "request"       # 同步请求
    RESPONSE = "response"     # 请求响应
    BROADCAST = "broadcast"   # 广播消息


@dataclass
class AgentMessage:
    """Agent消息"""
    message_id: str
    message_type: MessageType
    topic: str                              # 主题，如 "entity.extracted"
    sender: str                             # 发送者Agent ID
    payload: Dict[str, Any]                 # 消息内容
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None    # 关联ID（用于追踪请求-响应）
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "topic": self.topic,
            "sender": self.sender,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class AgentRequest:
    """Agent请求"""
    request_id: str
    requester: str                          # 请求者Agent ID
    target_agent: str                       # 目标Agent ID
    action: str                             # 请求的动作
    params: Dict[str, Any]                  # 参数
    timeout: float = 30.0                   # 超时时间（秒）
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "requester": self.requester,
            "target_agent": self.target_agent,
            "action": self.action,
            "params": self.params,
            "timeout": self.timeout,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentResponse:
    """Agent响应"""
    response_id: str
    request_id: str                         # 对应的请求ID
    responder: str                          # 响应者Agent ID
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0             # 执行时间（秒）
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "responder": self.responder,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }


class AgentMessageBus:
    """
    Agent消息总线

    功能：
    1. 发布-订阅：Agent发布事件，订阅者自动接收
    2. 直接请求：Agent向另一个Agent发送请求并等待响应
    3. 广播：向所有Agent广播消息
    4. 消息持久化：保存消息历史供审计

    使用示例：
    ```python
    # 初始化
    bus = AgentMessageBus()

    # Agent订阅消息
    bus.subscribe("entity.extracted", knowledge_agent.on_entity_extracted)

    # Agent发布消息
    bus.publish(
        topic="entity.extracted",
        sender="knowledge_agent_001",
        payload={"entities": [...], "count": 10}
    )

    # Agent请求另一个Agent
    response = await bus.request(
        requester="summary_agent_001",
        target_agent="search_agent_002",
        action="enrich_entity",
        params={"entity_name": "NVIDIA"}
    )
    ```
    """

    def __init__(self, enable_persistence: bool = True):
        """
        初始化消息总线

        Args:
            enable_persistence: 是否启用消息持久化
        """
        # 订阅者注册表: {topic: [handler1, handler2, ...]}
        self._subscribers: Dict[str, List[Callable]] = {}

        # Agent注册表: {agent_id: agent_instance}
        self._agents: Dict[str, Any] = {}

        # 消息历史（内存存储，生产环境应使用Redis/数据库）
        self._message_history: List[AgentMessage] = []

        # 请求-响应映射: {request_id: Future}
        self._pending_requests: Dict[str, asyncio.Future] = {}

        # 配置
        self.enable_persistence = enable_persistence
        self.max_history_size = 10000  # 最多保存10000条消息

        # 统计
        self.stats = {
            "messages_published": 0,
            "messages_delivered": 0,
            "requests_sent": 0,
            "requests_completed": 0,
            "requests_failed": 0
        }

        logger.info("🚌 AgentMessageBus 初始化完成")

    def register_agent(self, agent_id: str, agent_instance: Any):
        """
        注册Agent到总线

        Args:
            agent_id: Agent唯一ID
            agent_instance: Agent实例
        """
        self._agents[agent_id] = agent_instance
        logger.info(f"✅ Agent注册: {agent_id}")

    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"❌ Agent注销: {agent_id}")

    def subscribe(self, topic: str, handler: Callable[[AgentMessage], Awaitable[None]]):
        """
        订阅主题

        Args:
            topic: 主题名称，如 "entity.extracted"
            handler: 消息处理函数，必须是异步函数

        主题命名规范：
        - entity.extracted: 实体提取完成
        - entity.enriched: 实体补充完成
        - search.completed: 搜索完成
        - graph.updated: 图谱更新
        - report.generated: 报告生成完成
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []

        self._subscribers[topic].append(handler)
        logger.info(f"📬 订阅主题: {topic} (处理函数: {handler.__name__})")

    def unsubscribe(self, topic: str, handler: Callable):
        """取消订阅"""
        if topic in self._subscribers:
            self._subscribers[topic].remove(handler)
            logger.info(f"📪 取消订阅: {topic}")

    async def publish(
        self,
        topic: str,
        sender: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        发布消息

        Args:
            topic: 主题
            sender: 发送者Agent ID
            payload: 消息内容
            priority: 优先级
            metadata: 元数据

        Returns:
            message_id: 消息ID
        """
        # 创建消息
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.EVENT,
            topic=topic,
            sender=sender,
            payload=payload,
            priority=priority,
            metadata=metadata or {}
        )

        # 持久化
        if self.enable_persistence:
            self._save_message(message)

        # 统计
        self.stats["messages_published"] += 1

        logger.info(
            f"📤 发布消息: {topic} "
            f"(发送者: {sender}, 优先级: {priority.name}, ID: {message.message_id})"
        )

        # 分发给订阅者
        await self._distribute_message(message)

        return message.message_id

    async def _distribute_message(self, message: AgentMessage):
        """分发消息给订阅者"""
        topic = message.topic

        if topic not in self._subscribers:
            logger.debug(f"📭 主题无订阅者: {topic}")
            return

        handlers = self._subscribers[topic]
        logger.info(f"📬 分发消息: {topic} → {len(handlers)} 个订阅者")

        # 并发调用所有订阅者
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._invoke_handler(handler, message))
            tasks.append(task)

        # 等待所有handler完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        self.stats["messages_delivered"] += success_count

        logger.info(f"✅ 消息分发完成: {success_count}/{len(handlers)} 成功")

    async def _invoke_handler(self, handler: Callable, message: AgentMessage):
        """调用handler处理消息"""
        try:
            handler_name = handler.__name__
            logger.debug(f"  ▶️ 调用handler: {handler_name}")

            # 调用handler
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)

            logger.debug(f"  ✅ Handler完成: {handler_name}")

        except Exception as e:
            logger.error(
                f"  ❌ Handler失败: {handler.__name__}, 错误: {e}",
                exc_info=True
            )
            raise

    async def request(
        self,
        requester: str,
        target_agent: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> AgentResponse:
        """
        向另一个Agent发送请求

        Args:
            requester: 请求者Agent ID
            target_agent: 目标Agent ID
            action: 请求的动作
            params: 参数
            timeout: 超时时间（秒）

        Returns:
            AgentResponse: 响应对象

        Raises:
            TimeoutError: 请求超时
            ValueError: 目标Agent不存在
        """
        # 检查目标Agent
        if target_agent not in self._agents:
            raise ValueError(f"目标Agent不存在: {target_agent}")

        # 创建请求
        request = AgentRequest(
            request_id=str(uuid.uuid4()),
            requester=requester,
            target_agent=target_agent,
            action=action,
            params=params or {},
            timeout=timeout
        )

        logger.info(
            f"📞 发送请求: {requester} → {target_agent}.{action} "
            f"(ID: {request.request_id})"
        )

        # 统计
        self.stats["requests_sent"] += 1

        # 创建Future等待响应
        future = asyncio.Future()
        self._pending_requests[request.request_id] = future

        try:
            # 发送请求消息
            await self.publish(
                topic=f"request.{target_agent}",
                sender=requester,
                payload={
                    "request_id": request.request_id,
                    "action": action,
                    "params": params or {}
                },
                priority=MessagePriority.HIGH,
                metadata={"type": "request"}
            )

            # 等待响应（带超时）
            response = await asyncio.wait_for(future, timeout=timeout)

            # 统计
            if response.success:
                self.stats["requests_completed"] += 1
                logger.info(f"✅ 请求完成: {request.request_id}")
            else:
                self.stats["requests_failed"] += 1
                logger.warning(f"⚠️ 请求失败: {request.request_id}, 错误: {response.error}")

            return response

        except asyncio.TimeoutError:
            self.stats["requests_failed"] += 1
            logger.error(f"⏱️ 请求超时: {request.request_id} ({timeout}秒)")

            # 清理
            del self._pending_requests[request.request_id]

            # 返回超时响应
            return AgentResponse(
                response_id=str(uuid.uuid4()),
                request_id=request.request_id,
                responder=target_agent,
                success=False,
                error=f"Request timeout after {timeout}s"
            )

        except Exception as e:
            self.stats["requests_failed"] += 1
            logger.error(f"❌ 请求异常: {request.request_id}, 错误: {e}", exc_info=True)

            # 清理
            if request.request_id in self._pending_requests:
                del self._pending_requests[request.request_id]

            # 返回错误响应
            return AgentResponse(
                response_id=str(uuid.uuid4()),
                request_id=request.request_id,
                responder=target_agent,
                success=False,
                error=str(e)
            )

    async def respond(self, request_id: str, responder: str, result: Any = None, error: Optional[str] = None):
        """
        响应请求

        Args:
            request_id: 请求ID
            responder: 响应者Agent ID
            result: 结果
            error: 错误信息
        """
        # 检查是否有待处理的请求
        if request_id not in self._pending_requests:
            logger.warning(f"⚠️ 未找到待处理的请求: {request_id}")
            return

        # 创建响应
        response = AgentResponse(
            response_id=str(uuid.uuid4()),
            request_id=request_id,
            responder=responder,
            success=error is None,
            result=result,
            error=error
        )

        # 设置Future结果
        future = self._pending_requests[request_id]
        future.set_result(response)

        # 清理
        del self._pending_requests[request_id]

        logger.info(f"📨 发送响应: {request_id} (成功: {response.success})")

    async def broadcast(
        self,
        sender: str,
        payload: Dict[str, Any],
        exclude_agents: Optional[List[str]] = None
    ):
        """
        广播消息给所有Agent

        Args:
            sender: 发送者Agent ID
            payload: 消息内容
            exclude_agents: 排除的Agent ID列表
        """
        exclude_agents = exclude_agents or []

        logger.info(f"📢 广播消息: {sender} → 所有Agent")

        # 发布到特殊的广播主题
        await self.publish(
            topic="broadcast",
            sender=sender,
            payload=payload,
            priority=MessagePriority.NORMAL,
            metadata={"exclude_agents": exclude_agents}
        )

    def _save_message(self, message: AgentMessage):
        """保存消息到历史"""
        self._message_history.append(message)

        # 限制历史大小
        if len(self._message_history) > self.max_history_size:
            self._message_history = self._message_history[-self.max_history_size:]

    def get_message_history(
        self,
        topic: Optional[str] = None,
        sender: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentMessage]:
        """
        获取消息历史

        Args:
            topic: 过滤主题
            sender: 过滤发送者
            limit: 返回数量限制

        Returns:
            消息列表
        """
        messages = self._message_history

        # 过滤
        if topic:
            messages = [m for m in messages if m.topic == topic]
        if sender:
            messages = [m for m in messages if m.sender == sender]

        # 限制数量
        return messages[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "subscribers_count": sum(len(handlers) for handlers in self._subscribers.values()),
            "topics_count": len(self._subscribers),
            "agents_count": len(self._agents),
            "pending_requests": len(self._pending_requests),
            "message_history_size": len(self._message_history)
        }

    def clear_history(self):
        """清空消息历史"""
        self._message_history.clear()
        logger.info("🗑️ 消息历史已清空")


# 全局消息总线实例
agent_message_bus = AgentMessageBus()
