"""
Agent Mesh - Agent网格协作层

统一管理所有Agent的生命周期、通信和数据共享
将8个专业Agent连接成一个协作网络

Author: FieldMind Team
Date: 2026-08-14
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .agent_message_bus import AgentMessageBus, MessagePriority
from .shared_context_pool import SharedContextPool, ContextScope
from .base_agent import AgentBase, AgentRole, AgentTask, AgentResult, AgentStatus


logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    """Agent运行状态"""
    IDLE = "idle"              # 空闲
    BUSY = "busy"              # 处理中
    WAITING = "waiting"        # 等待依赖
    ERROR = "error"            # 错误状态
    STOPPED = "stopped"        # 已停止


@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    role: AgentRole
    instance: AgentBase
    state: AgentState = AgentState.IDLE
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    subscribed_topics: Set[str] = field(default_factory=set)


@dataclass
class CollaborationMetrics:
    """协作指标"""
    total_messages: int = 0
    total_requests: int = 0
    agent_interactions: Dict[str, int] = field(default_factory=dict)  # agent_pair -> count
    average_response_time: float = 0.0
    collaboration_chains: List[List[str]] = field(default_factory=list)  # 协作链路


class AgentMesh:
    """
    Agent网格 - 协作层核心

    职责:
    1. Agent生命周期管理 (注册、启动、停止、健康检查)
    2. 消息路由和通信协调
    3. 共享数据访问控制
    4. 协作模式编排
    5. 性能监控和指标收集

    架构:
        AgentMesh
           ├── AgentMessageBus (消息总线)
           ├── SharedContextPool (共享上下文)
           └── Agents (8个专业Agent)
                ├── KnowledgeAgent
                ├── SearchAgent
                ├── SummaryAgent
                ├── TranscriptAgent
                ├── EntityAgent
                ├── RelationAgent
                ├── CoordinatorAgent
                └── (Future: More agents)
    """

    def __init__(
        self,
        message_bus: Optional[AgentMessageBus] = None,
        context_pool: Optional[SharedContextPool] = None
    ):
        """
        初始化Agent网格

        Args:
            message_bus: 消息总线实例 (默认创建新实例)
            context_pool: 共享上下文池实例 (默认创建新实例)
        """
        self.message_bus = message_bus or AgentMessageBus()
        self.context_pool = context_pool or SharedContextPool()

        # Agent注册表
        self._agents: Dict[str, AgentInfo] = {}

        # 协作指标
        self._metrics = CollaborationMetrics()

        # 运行状态
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None

        logger.info("AgentMesh initialized")

    # ==================== Agent生命周期管理 ====================

    def register_agent(
        self,
        agent: AgentBase,
        agent_id: Optional[str] = None,
        auto_subscribe: Optional[List[str]] = None
    ) -> str:
        """
        注册Agent到网格

        Args:
            agent: Agent实例
            agent_id: Agent唯一ID (默认使用role名称)
            auto_subscribe: 自动订阅的topic列表

        Returns:
            agent_id: Agent唯一标识
        """
        agent_id = agent_id or f"{agent.role.value}_agent"

        if agent_id in self._agents:
            logger.warning(f"Agent {agent_id} already registered, replacing")

        # 注入消息总线和上下文池
        agent.message_bus = self.message_bus
        agent.shared_context = self.context_pool

        # 创建Agent信息
        info = AgentInfo(
            agent_id=agent_id,
            role=agent.role,
            instance=agent
        )

        self._agents[agent_id] = info

        # 注册到消息总线
        self.message_bus.register_agent(agent_id, agent)

        # 自动订阅topics
        if auto_subscribe:
            for topic in auto_subscribe:
                self._subscribe_agent(agent_id, topic)

        logger.info(f"Agent registered: {agent_id} (role={agent.role.value})")
        return agent_id

    def unregister_agent(self, agent_id: str) -> bool:
        """
        注销Agent

        Args:
            agent_id: Agent ID

        Returns:
            是否成功注销
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent {agent_id} not found")
            return False

        info = self._agents[agent_id]

        # 取消所有订阅
        for topic in info.subscribed_topics:
            self.message_bus.unsubscribe(topic, agent_id)

        # 从注册表移除
        del self._agents[agent_id]

        logger.info(f"Agent unregistered: {agent_id}")
        return True

    def get_agent(self, agent_id: str) -> Optional[AgentBase]:
        """获取Agent实例"""
        info = self._agents.get(agent_id)
        return info.instance if info else None

    def get_agent_by_role(self, role: AgentRole) -> Optional[AgentBase]:
        """根据角色获取Agent"""
        for info in self._agents.values():
            if info.role == role:
                return info.instance
        return None

    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有Agent及状态"""
        return [
            {
                "agent_id": info.agent_id,
                "role": info.role.value,
                "state": info.state.value,
                "current_task": info.current_task,
                "tasks_completed": info.tasks_completed,
                "tasks_failed": info.tasks_failed,
                "subscribed_topics": list(info.subscribed_topics),
                "last_heartbeat": info.last_heartbeat.isoformat()
            }
            for info in self._agents.values()
        ]

    # ==================== 消息路由和通信 ====================

    def _subscribe_agent(self, agent_id: str, topic: str):
        """订阅topic到Agent"""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not registered")

        info = self._agents[agent_id]
        agent = info.instance

        # 创建处理函数
        async def handler(message):
            info.state = AgentState.BUSY
            try:
                # 调用Agent的处理方法
                await self._handle_message_for_agent(agent_id, agent, message)
                info.tasks_completed += 1
            except Exception as e:
                logger.error(f"Agent {agent_id} failed to handle message: {e}")
                info.tasks_failed += 1
                info.state = AgentState.ERROR
            finally:
                info.state = AgentState.IDLE
                info.last_heartbeat = datetime.now()

        # 订阅到消息总线
        self.message_bus.subscribe(topic, handler)
        info.subscribed_topics.add(topic)

        logger.info(f"Agent {agent_id} subscribed to topic: {topic}")

    async def _handle_message_for_agent(
        self,
        agent_id: str,
        agent: AgentBase,
        message: Any
    ):
        """
        为Agent处理消息

        将消息转换为AgentTask并执行
        """
        # 从消息构造任务
        task = AgentTask(
            task_id=str(message.message_id),
            task_type=message.topic,
            input_data=message.payload,
            context={}
        )

        # 执行任务
        result = await agent.execute_task(task)

        # 如果有结果，发布到上下文
        if result.status == AgentStatus.COMPLETED and result.output_data:
            output_topic = f"{message.topic}.completed"
            await self.message_bus.publish(
                topic=output_topic,
                sender=agent_id,
                payload=result.output_data,
                priority=MessagePriority.NORMAL
            )

    async def broadcast_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        sender: str = "system",
        priority: MessagePriority = MessagePriority.NORMAL
    ):
        """
        广播事件到所有订阅的Agent

        Args:
            event_type: 事件类型 (topic)
            payload: 事件数据
            sender: 发送者
            priority: 优先级
        """
        await self.message_bus.publish(
            topic=event_type,
            sender=sender,
            payload=payload,
            priority=priority
        )

        self._metrics.total_messages += 1
        logger.info(f"Event broadcasted: {event_type} from {sender}")

    async def request_agent(
        self,
        requester: str,
        target_agent_id: str,
        action: str,
        params: Dict[str, Any],
        timeout: float = 30.0
    ) -> Any:
        """
        向特定Agent发送同步请求

        Args:
            requester: 请求者ID
            target_agent_id: 目标Agent ID
            action: 请求的操作
            params: 参数
            timeout: 超时时间(秒)

        Returns:
            响应数据
        """
        if target_agent_id not in self._agents:
            raise ValueError(f"Target agent {target_agent_id} not found")

        response = await self.message_bus.request(
            requester=requester,
            target_agent=target_agent_id,
            action=action,
            params=params,
            timeout=timeout
        )

        self._metrics.total_requests += 1

        # 记录交互
        interaction_key = f"{requester}->{target_agent_id}"
        self._metrics.agent_interactions[interaction_key] = \
            self._metrics.agent_interactions.get(interaction_key, 0) + 1

        return response

    # ==================== 协作模式编排 ====================

    async def cascade_processing(
        self,
        agent_chain: List[str],
        initial_data: Dict[str, Any],
        context_key: str = "cascade_data"
    ) -> Dict[str, Any]:
        """
        级联处理模式: Agent1 -> Agent2 -> Agent3

        Args:
            agent_chain: Agent ID列表 (按顺序)
            initial_data: 初始数据
            context_key: 共享上下文的key

        Returns:
            最终处理结果
        """
        logger.info(f"Starting cascade processing: {' -> '.join(agent_chain)}")

        # 初始化共享上下文 (使用GLOBAL scope避免需要session_id)
        self.context_pool.set(
            key=context_key,
            value=initial_data,
            agent_id="system",
            scope=ContextScope.GLOBAL
        )

        current_data = initial_data

        for i, agent_id in enumerate(agent_chain):
            if agent_id not in self._agents:
                raise ValueError(f"Agent {agent_id} not found in chain")

            logger.info(f"Cascade step {i+1}/{len(agent_chain)}: {agent_id}")

            # 发送请求给当前Agent
            result = await self.request_agent(
                requester="cascade_coordinator",
                target_agent_id=agent_id,
                action="process",
                params={"data": current_data},
                timeout=60.0
            )

            # 更新共享上下文
            current_data = result
            self.context_pool.set(
                key=f"{context_key}_step_{i+1}",
                value=current_data,
                agent_id=agent_id,
                scope=ContextScope.GLOBAL
            )

        # 记录协作链
        self._metrics.collaboration_chains.append(agent_chain)

        logger.info(f"Cascade processing completed: {len(agent_chain)} steps")
        return current_data

    async def parallel_processing(
        self,
        agent_ids: List[str],
        input_data: Dict[str, Any],
        merge_strategy: str = "union"
    ) -> Dict[str, Any]:
        """
        并行处理模式: 多个Agent同时处理同一数据

        Args:
            agent_ids: Agent ID列表
            input_data: 输入数据
            merge_strategy: 结果合并策略 (union/intersection)

        Returns:
            合并后的结果
        """
        logger.info(f"Starting parallel processing: {agent_ids}")

        # 并发请求所有Agent
        tasks = [
            self.request_agent(
                requester="parallel_coordinator",
                target_agent_id=agent_id,
                action="process",
                params={"data": input_data},
                timeout=60.0
            )
            for agent_id in agent_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        merged = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_ids[i]} failed: {result}")
                continue

            if merge_strategy == "union":
                merged.update(result)
            elif merge_strategy == "intersection":
                if not merged:
                    merged = result
                else:
                    merged = {k: v for k, v in merged.items() if k in result}

        logger.info(f"Parallel processing completed: {len(agent_ids)} agents")
        return merged

    async def iterative_refinement(
        self,
        primary_agent: str,
        critic_agent: str,
        initial_data: Dict[str, Any],
        max_iterations: int = 3,
        quality_threshold: float = 0.9
    ) -> Dict[str, Any]:
        """
        迭代优化模式: 主Agent生成 -> 评判Agent审查 -> 循环改进

        Args:
            primary_agent: 主处理Agent ID
            critic_agent: 评判Agent ID
            initial_data: 初始数据
            max_iterations: 最大迭代次数
            quality_threshold: 质量阈值 (0-1)

        Returns:
            最终优化结果
        """
        logger.info(f"Starting iterative refinement: {primary_agent} <-> {critic_agent}")

        current_result = initial_data

        for iteration in range(max_iterations):
            logger.info(f"Iteration {iteration + 1}/{max_iterations}")

            # 主Agent处理
            result = await self.request_agent(
                requester="iterative_coordinator",
                target_agent_id=primary_agent,
                action="process",
                params={"data": current_result},
                timeout=60.0
            )

            # 评判Agent评估
            critique = await self.request_agent(
                requester="iterative_coordinator",
                target_agent_id=critic_agent,
                action="evaluate",
                params={"result": result},
                timeout=30.0
            )

            quality_score = critique.get("quality_score", 0.0)
            logger.info(f"Quality score: {quality_score}")

            if quality_score >= quality_threshold:
                logger.info(f"Quality threshold reached at iteration {iteration + 1}")
                return result

            # 使用反馈改进
            current_result = {
                **result,
                "feedback": critique.get("feedback", [])
            }

        logger.warning(f"Max iterations reached without meeting quality threshold")
        return current_result

    # ==================== 健康检查和监控 ====================

    async def start(self):
        """启动Agent网格"""
        if self._running:
            logger.warning("AgentMesh already running")
            return

        self._running = True

        # 启动健康检查
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info("AgentMesh started")

    async def stop(self):
        """停止Agent网格"""
        if not self._running:
            return

        self._running = False

        # 停止健康检查
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # 标记所有Agent为停止
        for info in self._agents.values():
            info.state = AgentState.STOPPED

        logger.info("AgentMesh stopped")

    async def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _perform_health_check(self):
        """执行健康检查"""
        now = datetime.now()

        for agent_id, info in self._agents.items():
            # 检查心跳超时 (5分钟)
            time_since_heartbeat = (now - info.last_heartbeat).total_seconds()

            if time_since_heartbeat > 300:
                logger.warning(f"Agent {agent_id} heartbeat timeout: {time_since_heartbeat}s")
                info.state = AgentState.ERROR

    def get_metrics(self) -> Dict[str, Any]:
        """获取协作指标"""
        return {
            "total_agents": len(self._agents),
            "active_agents": sum(1 for info in self._agents.values() if info.state != AgentState.STOPPED),
            "total_messages": self._metrics.total_messages,
            "total_requests": self._metrics.total_requests,
            "agent_interactions": self._metrics.agent_interactions,
            "collaboration_chains": self._metrics.collaboration_chains,
            "tasks_completed": sum(info.tasks_completed for info in self._agents.values()),
            "tasks_failed": sum(info.tasks_failed for info in self._agents.values())
        }

    def export_state(self) -> Dict[str, Any]:
        """导出完整状态 (用于调试和监控)"""
        return {
            "agents": self.list_agents(),
            "metrics": self.get_metrics(),
            "message_bus_stats": self.message_bus.get_statistics(),
            "context_pool_stats": {
                "total_keys": len(self.context_pool.list_all_keys()),
                "access_log_count": len(self.context_pool._access_logs)
            }
        }
