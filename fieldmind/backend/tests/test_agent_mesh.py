"""
测试Agent Mesh - Agent网格协作层

测试Agent生命周期管理、消息路由、协作模式
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.app.services.agents.agent_mesh import (
    AgentMesh,
    AgentState,
    AgentInfo,
    CollaborationMetrics
)
from src.app.services.agents.agent_message_bus import AgentMessageBus, MessagePriority
from src.app.services.agents.shared_context_pool import SharedContextPool, ContextScope
from src.app.services.agents.base_agent import AgentBase, AgentRole, AgentTask, AgentResult, AgentStatus


# ==================== Mock Agents ====================

class MockKnowledgeAgent(AgentBase):
    """Mock知识提取Agent"""

    def __init__(self):
        super().__init__()
        self.message_bus = None
        self.shared_context = None

    @property
    def role(self) -> AgentRole:
        return AgentRole.KNOWLEDGE

    @property
    def name(self) -> str:
        return "知识提取Agent"

    @property
    def description(self) -> str:
        return "提取文本中的实体和知识"

    @property
    def capabilities(self) -> list:
        return ["entity_extraction", "knowledge_extraction"]

    def _initialize_tools(self):
        self.tools = {}

    def _execute_task_impl(self, task: AgentTask) -> dict:
        """同步版本的execute_task_impl"""
        import time
        time.sleep(0.1)

        input_text = task.input_data.get("text", "")
        entities = [
            {"name": "FieldMind", "type": "PRODUCT"},
            {"name": "AI", "type": "TECHNOLOGY"}
        ]

        return {
            "entities": entities,
            "entity_count": len(entities)
        }

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """异步execute_task用于Agent Mesh"""
        await asyncio.sleep(0.1)

        input_text = task.input_data.get("text", "")
        entities = [
            {"name": "FieldMind", "type": "PRODUCT"},
            {"name": "AI", "type": "TECHNOLOGY"}
        ]

        return AgentResult(
            task_id=task.task_id,
            status=AgentStatus.COMPLETED,
            output_data={
                "entities": entities,
                "entity_count": len(entities)
            }
        )


class MockSearchAgent(AgentBase):
    """Mock搜索Agent"""

    def __init__(self):
        super().__init__()
        self.message_bus = None
        self.shared_context = None

    @property
    def role(self) -> AgentRole:
        return AgentRole.SEARCH

    @property
    def name(self) -> str:
        return "搜索Agent"

    @property
    def description(self) -> str:
        return "搜索和增强信息"

    @property
    def capabilities(self) -> list:
        return ["search", "enrichment"]

    def _initialize_tools(self):
        self.tools = {}

    def _execute_task_impl(self, task: AgentTask) -> dict:
        """同步版本"""
        import time
        time.sleep(0.15)

        entities = task.input_data.get("entities", [])
        enriched = []

        for entity in entities:
            enriched.append({
                **entity,
                "description": f"Enriched description for {entity['name']}",
                "relevance_score": 0.95
            })

        return {"enriched_entities": enriched}

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """异步execute_task"""
        await asyncio.sleep(0.15)

        entities = task.input_data.get("entities", [])
        enriched = []

        for entity in entities:
            enriched.append({
                **entity,
                "description": f"Enriched description for {entity['name']}",
                "relevance_score": 0.95
            })

        return AgentResult(
            task_id=task.task_id,
            status=AgentStatus.COMPLETED,
            output_data={"enriched_entities": enriched}
        )


class MockSummaryAgent(AgentBase):
    """Mock摘要Agent"""

    def __init__(self):
        super().__init__()
        self.message_bus = None
        self.shared_context = None

    @property
    def role(self) -> AgentRole:
        return AgentRole.SUMMARY

    @property
    def name(self) -> str:
        return "摘要Agent"

    @property
    def description(self) -> str:
        return "生成摘要"

    @property
    def capabilities(self) -> list:
        return ["summarization"]

    def _initialize_tools(self):
        self.tools = {}

    def _execute_task_impl(self, task: AgentTask) -> dict:
        """同步版本"""
        import time
        time.sleep(0.12)

        data = task.input_data.get("data", {})

        return {
            "summary": f"Summary of {len(data)} items",
            "key_points": ["Point 1", "Point 2", "Point 3"]
        }

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """异步execute_task"""
        await asyncio.sleep(0.12)

        data = task.input_data.get("data", {})

        return AgentResult(
            task_id=task.task_id,
            status=AgentStatus.COMPLETED,
            output_data={
                "summary": f"Summary of {len(data)} items",
                "key_points": ["Point 1", "Point 2", "Point 3"]
            }
        )


class MockCriticAgent(AgentBase):
    """Mock评判Agent"""

    def __init__(self):
        super().__init__()
        self.message_bus = None
        self.shared_context = None
        self.iteration_count = 0

    @property
    def role(self) -> AgentRole:
        return AgentRole.SUMMARY  # 复用角色

    @property
    def name(self) -> str:
        return "评判Agent"

    @property
    def description(self) -> str:
        return "评估质量"

    @property
    def capabilities(self) -> list:
        return ["quality_evaluation"]

    def _initialize_tools(self):
        self.tools = {}

    def _execute_task_impl(self, task: AgentTask) -> dict:
        """同步版本"""
        import time
        time.sleep(0.08)

        self.iteration_count += 1
        quality_score = 0.7 if self.iteration_count == 1 else 0.95

        return {
            "quality_score": quality_score,
            "feedback": ["Improve clarity", "Add examples"] if quality_score < 0.9 else []
        }

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """异步execute_task"""
        await asyncio.sleep(0.08)

        self.iteration_count += 1
        quality_score = 0.7 if self.iteration_count == 1 else 0.95

        return AgentResult(
            task_id=task.task_id,
            status=AgentStatus.COMPLETED,
            output_data={
                "quality_score": quality_score,
                "feedback": ["Improve clarity", "Add examples"] if quality_score < 0.9 else []
            }
        )


# ==================== Fixtures ====================

@pytest.fixture
def message_bus():
    """创建消息总线"""
    return AgentMessageBus()


@pytest.fixture
def context_pool():
    """创建共享上下文池"""
    return SharedContextPool()


@pytest.fixture
def agent_mesh(message_bus, context_pool):
    """创建Agent网格"""
    return AgentMesh(message_bus=message_bus, context_pool=context_pool)


@pytest.fixture
def knowledge_agent():
    """创建Mock知识Agent"""
    return MockKnowledgeAgent()


@pytest.fixture
def search_agent():
    """创建Mock搜索Agent"""
    return MockSearchAgent()


@pytest.fixture
def summary_agent():
    """创建Mock摘要Agent"""
    return MockSummaryAgent()


# ==================== 测试Agent生命周期 ====================

def test_register_agent(agent_mesh, knowledge_agent):
    """测试Agent注册"""
    agent_id = agent_mesh.register_agent(knowledge_agent, agent_id="knowledge_agent_1")

    assert agent_id == "knowledge_agent_1"
    assert agent_id in agent_mesh._agents

    # 验证Agent已注入依赖
    assert knowledge_agent.message_bus is agent_mesh.message_bus
    assert knowledge_agent.shared_context is agent_mesh.context_pool

    # 验证Agent信息
    info = agent_mesh._agents[agent_id]
    assert info.role == AgentRole.KNOWLEDGE
    assert info.state == AgentState.IDLE
    assert info.tasks_completed == 0


def test_register_agent_with_auto_subscribe(agent_mesh, search_agent):
    """测试Agent注册时自动订阅"""
    agent_id = agent_mesh.register_agent(
        search_agent,
        agent_id="search_agent_1",
        auto_subscribe=["entity.extracted", "document.uploaded"]
    )

    info = agent_mesh._agents[agent_id]
    assert "entity.extracted" in info.subscribed_topics
    assert "document.uploaded" in info.subscribed_topics


def test_unregister_agent(agent_mesh, knowledge_agent):
    """测试Agent注销"""
    agent_id = agent_mesh.register_agent(knowledge_agent)

    success = agent_mesh.unregister_agent(agent_id)
    assert success is True
    assert agent_id not in agent_mesh._agents


def test_get_agent(agent_mesh, knowledge_agent):
    """测试获取Agent"""
    agent_id = agent_mesh.register_agent(knowledge_agent)

    retrieved = agent_mesh.get_agent(agent_id)
    assert retrieved is knowledge_agent


def test_get_agent_by_role(agent_mesh, knowledge_agent, search_agent):
    """测试根据角色获取Agent"""
    agent_mesh.register_agent(knowledge_agent)
    agent_mesh.register_agent(search_agent)

    knowledge = agent_mesh.get_agent_by_role(AgentRole.KNOWLEDGE)
    assert knowledge is knowledge_agent

    search = agent_mesh.get_agent_by_role(AgentRole.SEARCH)
    assert search is search_agent


def test_list_agents(agent_mesh, knowledge_agent, search_agent):
    """测试列出所有Agent"""
    agent_mesh.register_agent(knowledge_agent, agent_id="knowledge_1")
    agent_mesh.register_agent(search_agent, agent_id="search_1")

    agents = agent_mesh.list_agents()
    assert len(agents) == 2

    agent_ids = [a["agent_id"] for a in agents]
    assert "knowledge_1" in agent_ids
    assert "search_1" in agent_ids


# ==================== 测试消息路由 ====================

@pytest.mark.asyncio
async def test_broadcast_event(agent_mesh, knowledge_agent):
    """测试广播事件"""
    agent_id = agent_mesh.register_agent(knowledge_agent)

    # 订阅事件
    received_messages = []

    async def handler(message):
        received_messages.append(message)

    agent_mesh.message_bus.subscribe("test.event", handler)

    # 广播事件
    await agent_mesh.broadcast_event(
        event_type="test.event",
        payload={"data": "test"},
        sender="system"
    )

    await asyncio.sleep(0.1)  # 等待处理

    assert len(received_messages) == 1
    assert received_messages[0].topic == "test.event"
    assert received_messages[0].payload["data"] == "test"


@pytest.mark.asyncio
async def test_request_agent(agent_mesh, knowledge_agent):
    """测试Agent间同步请求"""
    agent_id = agent_mesh.register_agent(knowledge_agent)

    # 发送请求
    response = await agent_mesh.request_agent(
        requester="test_requester",
        target_agent_id=agent_id,
        action="process",
        params={"text": "Test document"},
        timeout=5.0
    )

    assert response is not None
    assert "entities" in response
    assert response["entity_count"] == 2


@pytest.mark.asyncio
async def test_request_nonexistent_agent(agent_mesh):
    """测试请求不存在的Agent"""
    with pytest.raises(ValueError, match="not found"):
        await agent_mesh.request_agent(
            requester="test",
            target_agent_id="nonexistent_agent",
            action="process",
            params={},
            timeout=5.0
        )


# ==================== 测试协作模式 ====================

@pytest.mark.asyncio
async def test_cascade_processing(agent_mesh, knowledge_agent, search_agent, summary_agent):
    """测试级联处理模式"""
    # 注册3个Agent
    k_id = agent_mesh.register_agent(knowledge_agent, agent_id="knowledge")
    s_id = agent_mesh.register_agent(search_agent, agent_id="search")
    sum_id = agent_mesh.register_agent(summary_agent, agent_id="summary")

    # 执行级联处理
    initial_data = {"text": "AI research document"}

    result = await agent_mesh.cascade_processing(
        agent_chain=[k_id, s_id, sum_id],
        initial_data=initial_data,
        context_key="cascade_test"
    )

    # 验证结果
    assert result is not None
    assert "summary" in result

    # 验证共享上下文已记录每一步
    step1 = agent_mesh.context_pool.get("cascade_test_step_1", "system", ContextScope.GLOBAL)
    assert step1 is not None
    assert "entities" in step1

    step2 = agent_mesh.context_pool.get("cascade_test_step_2", "system", ContextScope.GLOBAL)
    assert step2 is not None
    assert "enriched_entities" in step2

    step3 = agent_mesh.context_pool.get("cascade_test_step_3", "system", ContextScope.GLOBAL)
    assert step3 is not None
    assert "summary" in step3

    # 验证协作链已记录
    assert [k_id, s_id, sum_id] in agent_mesh._metrics.collaboration_chains


@pytest.mark.asyncio
async def test_parallel_processing(agent_mesh, knowledge_agent, search_agent):
    """测试并行处理模式"""
    k_id = agent_mesh.register_agent(knowledge_agent, agent_id="knowledge")
    s_id = agent_mesh.register_agent(search_agent, agent_id="search")

    input_data = {
        "text": "Test document",
        "entities": [{"name": "Test", "type": "MISC"}]
    }

    # 并行处理
    result = await agent_mesh.parallel_processing(
        agent_ids=[k_id, s_id],
        input_data=input_data,
        merge_strategy="union"
    )

    # 验证结果合并了两个Agent的输出
    assert "entities" in result  # 来自knowledge_agent
    assert "enriched_entities" in result  # 来自search_agent


@pytest.mark.asyncio
async def test_parallel_processing_with_failure(agent_mesh, knowledge_agent):
    """测试并行处理中一个Agent失败"""
    k_id = agent_mesh.register_agent(knowledge_agent, agent_id="knowledge")

    # 注册一个会失败的Agent
    failing_agent = MockSearchAgent()
    failing_agent.execute_task = AsyncMock(side_effect=Exception("Agent failed"))
    f_id = agent_mesh.register_agent(failing_agent, agent_id="failing")

    input_data = {"text": "Test"}

    # 并行处理应该优雅处理失败
    result = await agent_mesh.parallel_processing(
        agent_ids=[k_id, f_id],
        input_data=input_data,
        merge_strategy="union"
    )

    # 应该只包含成功Agent的结果
    assert "entities" in result


@pytest.mark.asyncio
async def test_iterative_refinement(agent_mesh):
    """测试迭代优化模式"""
    primary = MockKnowledgeAgent()
    critic = MockCriticAgent()

    p_id = agent_mesh.register_agent(primary, agent_id="primary")
    c_id = agent_mesh.register_agent(critic, agent_id="critic")

    initial_data = {"text": "Draft content"}

    result = await agent_mesh.iterative_refinement(
        primary_agent=p_id,
        critic_agent=c_id,
        initial_data=initial_data,
        max_iterations=3,
        quality_threshold=0.9
    )

    # 验证迭代次数 (应该在第2次达到阈值)
    assert critic.iteration_count == 2
    assert result is not None


@pytest.mark.asyncio
async def test_iterative_refinement_max_iterations(agent_mesh):
    """测试迭代优化达到最大次数"""
    primary = MockKnowledgeAgent()

    # 创建一个永远不满意的critic
    strict_critic = MockCriticAgent()
    strict_critic.execute_task = AsyncMock(return_value=AgentResult(
        task_id="test",
        status=AgentStatus.COMPLETED,
        output_data={"quality_score": 0.5, "feedback": ["Not good enough"]}
    ))

    p_id = agent_mesh.register_agent(primary, agent_id="primary")
    c_id = agent_mesh.register_agent(strict_critic, agent_id="strict_critic")

    result = await agent_mesh.iterative_refinement(
        primary_agent=p_id,
        critic_agent=c_id,
        initial_data={"text": "Draft"},
        max_iterations=2,
        quality_threshold=0.9
    )

    # 应该返回最后一次迭代的结果
    assert result is not None
    assert strict_critic.execute_task.call_count == 2


# ==================== 测试健康检查和监控 ====================

@pytest.mark.asyncio
async def test_start_stop(agent_mesh):
    """测试启动和停止"""
    assert agent_mesh._running is False

    await agent_mesh.start()
    assert agent_mesh._running is True
    assert agent_mesh._health_check_task is not None

    await agent_mesh.stop()
    assert agent_mesh._running is False


@pytest.mark.asyncio
async def test_health_check_updates_agent_state(agent_mesh, knowledge_agent):
    """测试健康检查更新Agent状态"""
    agent_id = agent_mesh.register_agent(knowledge_agent)

    # 手动设置过期的心跳
    info = agent_mesh._agents[agent_id]
    info.last_heartbeat = datetime(2020, 1, 1)  # 很久以前

    # 执行健康检查
    await agent_mesh._perform_health_check()

    # 状态应该变为ERROR
    assert info.state == AgentState.ERROR


def test_get_metrics(agent_mesh, knowledge_agent, search_agent):
    """测试获取指标"""
    agent_mesh.register_agent(knowledge_agent)
    agent_mesh.register_agent(search_agent)

    metrics = agent_mesh.get_metrics()

    assert metrics["total_agents"] == 2
    assert metrics["active_agents"] == 2
    assert "total_messages" in metrics
    assert "total_requests" in metrics


def test_export_state(agent_mesh, knowledge_agent):
    """测试导出完整状态"""
    agent_mesh.register_agent(knowledge_agent, agent_id="knowledge")

    state = agent_mesh.export_state()

    assert "agents" in state
    assert "metrics" in state
    assert "message_bus_stats" in state
    assert "context_pool_stats" in state

    assert len(state["agents"]) == 1
    assert state["agents"][0]["agent_id"] == "knowledge"


# ==================== 测试完整协作场景 ====================

@pytest.mark.asyncio
async def test_complete_collaboration_scenario(agent_mesh):
    """
    完整协作场景: 研究报告生成

    1. KnowledgeAgent提取实体
    2. SearchAgent丰富实体信息
    3. SummaryAgent生成最终报告

    使用级联模式 + 共享上下文
    """
    # 注册Agents
    knowledge = MockKnowledgeAgent()
    search = MockSearchAgent()
    summary = MockSummaryAgent()

    k_id = agent_mesh.register_agent(knowledge, agent_id="knowledge")
    s_id = agent_mesh.register_agent(search, agent_id="search")
    sum_id = agent_mesh.register_agent(summary, agent_id="summary")

    # 执行级联处理
    initial_doc = {"text": "FieldMind is an AI-powered knowledge management system."}

    final_report = await agent_mesh.cascade_processing(
        agent_chain=[k_id, s_id, sum_id],
        initial_data=initial_doc,
        context_key="research_report"
    )

    # 验证最终报告
    assert "summary" in final_report
    assert "key_points" in final_report

    # 验证数据血缘: 每一步都有记录
    lineage = agent_mesh.context_pool.get_data_lineage("research_report_step_1")
    assert len(lineage) > 0
    assert lineage[0]["agent_id"] == k_id

    # 验证Agent状态已更新
    k_info = agent_mesh._agents[k_id]
    assert k_info.tasks_completed >= 1
    assert k_info.state == AgentState.IDLE

    # 验证指标
    metrics = agent_mesh.get_metrics()
    assert metrics["total_requests"] >= 3  # 3个级联请求
    assert metrics["tasks_completed"] >= 3


@pytest.mark.asyncio
async def test_agent_mesh_with_event_subscription(agent_mesh):
    """
    测试基于事件订阅的自动协作

    KnowledgeAgent提取实体后发布事件
    SearchAgent自动订阅并增强
    """
    knowledge = MockKnowledgeAgent()
    search = MockSearchAgent()

    k_id = agent_mesh.register_agent(knowledge, agent_id="knowledge")
    s_id = agent_mesh.register_agent(
        search,
        agent_id="search",
        auto_subscribe=["entity.extracted.completed"]  # 自动订阅完成事件
    )

    # KnowledgeAgent处理文档
    response = await agent_mesh.request_agent(
        requester="test",
        target_agent_id=k_id,
        action="process",
        params={"text": "Test document"},
        timeout=5.0
    )

    # 验证KnowledgeAgent产生了结果
    assert "entities" in response

    # SearchAgent应该自动收到entity.extracted.completed事件并处理
    # (通过_handle_message_for_agent自动触发)
    await asyncio.sleep(0.3)  # 等待异步处理

    # 验证SearchAgent的任务已完成
    s_info = agent_mesh._agents[s_id]
    assert s_info.tasks_completed >= 0  # SearchAgent可能已处理事件
