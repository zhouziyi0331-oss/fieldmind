"""
Agent消息总线和共享上下文池 - 单元测试

测试：
1. 消息发布-订阅
2. Agent请求-响应
3. 上下文读写
4. 数据血缘追踪
5. 协同场景模拟
"""

import pytest
import asyncio
from datetime import datetime

from app.services.agents.agent_message_bus import (
    AgentMessageBus, AgentMessage, MessageType, MessagePriority,
    AgentRequest, AgentResponse
)
from app.services.agents.shared_context_pool import (
    SharedContextPool, ContextScope, AccessType
)


# ==================== 消息总线测试 ====================

@pytest.mark.asyncio
async def test_message_bus_publish_subscribe():
    """测试发布-订阅模式"""
    bus = AgentMessageBus()

    # 订阅计数器
    received_messages = []

    # 订阅处理函数
    async def handler(message: AgentMessage):
        received_messages.append(message)

    # 订阅主题
    bus.subscribe("entity.extracted", handler)

    # 发布消息
    await bus.publish(
        topic="entity.extracted",
        sender="knowledge_agent_001",
        payload={"entities": [{"name": "NVIDIA", "type": "ORG"}], "count": 1}
    )

    # 等待异步处理
    await asyncio.sleep(0.1)

    # 验证
    assert len(received_messages) == 1
    assert received_messages[0].topic == "entity.extracted"
    assert received_messages[0].sender == "knowledge_agent_001"
    assert received_messages[0].payload["count"] == 1


@pytest.mark.asyncio
async def test_message_bus_multiple_subscribers():
    """测试多个订阅者"""
    bus = AgentMessageBus()

    counter1 = []
    counter2 = []

    async def handler1(message: AgentMessage):
        counter1.append(message)

    async def handler2(message: AgentMessage):
        counter2.append(message)

    # 两个订阅者
    bus.subscribe("search.completed", handler1)
    bus.subscribe("search.completed", handler2)

    # 发布消息
    await bus.publish(
        topic="search.completed",
        sender="search_agent_001",
        payload={"results": []}
    )

    await asyncio.sleep(0.1)

    # 两个订阅者都应该收到
    assert len(counter1) == 1
    assert len(counter2) == 1


@pytest.mark.asyncio
async def test_message_bus_request_response():
    """测试请求-响应模式"""
    bus = AgentMessageBus()

    # 模拟目标Agent
    class MockSearchAgent:
        def __init__(self):
            self.agent_id = "search_agent_001"

    mock_agent = MockSearchAgent()
    bus.register_agent("search_agent_001", mock_agent)

    # 订阅请求主题并响应
    async def handle_request(message: AgentMessage):
        request_id = message.payload.get("request_id")
        action = message.payload.get("action")

        if action == "enrich_entity":
            # 模拟处理
            await asyncio.sleep(0.1)

            # 响应
            await bus.respond(
                request_id=request_id,
                responder="search_agent_001",
                result={"enriched": True, "source": "Wikipedia"}
            )

    bus.subscribe("request.search_agent_001", handle_request)

    # 发送请求
    response = await bus.request(
        requester="knowledge_agent_001",
        target_agent="search_agent_001",
        action="enrich_entity",
        params={"entity_name": "NVIDIA"},
        timeout=2.0
    )

    # 验证响应
    assert response.success is True
    assert response.result["enriched"] is True
    assert response.result["source"] == "Wikipedia"


@pytest.mark.asyncio
async def test_message_bus_request_timeout():
    """测试请求超时"""
    bus = AgentMessageBus()

    # 注册Agent但不响应
    class MockAgent:
        def __init__(self):
            self.agent_id = "slow_agent_001"

    bus.register_agent("slow_agent_001", MockAgent())

    # 发送请求（不会有响应）
    response = await bus.request(
        requester="test_agent",
        target_agent="slow_agent_001",
        action="slow_task",
        timeout=0.5  # 短超时
    )

    # 应该超时
    assert response.success is False
    assert "timeout" in response.error.lower()


# ==================== 共享上下文池测试 ====================

def test_context_pool_basic():
    """测试基本读写"""
    pool = SharedContextPool()
    pool.set_project(123)

    # 写入
    pool.set(
        key="entities",
        value=[{"name": "NVIDIA", "type": "ORG"}],
        agent_id="knowledge_agent_001"
    )

    # 读取
    entities = pool.get("entities", agent_id="search_agent_002")

    assert len(entities) == 1
    assert entities[0]["name"] == "NVIDIA"


def test_context_pool_scope_isolation():
    """测试作用域隔离"""
    pool = SharedContextPool()

    # 项目1
    pool.set_project(123)
    pool.set("data", "project_123_data", agent_id="agent_1")

    # 项目2
    pool.set_project(456)
    pool.set("data", "project_456_data", agent_id="agent_2")

    # 读取项目1的数据
    pool.set_project(123)
    data1 = pool.get("data", agent_id="agent_3")

    # 读取项目2的数据
    pool.set_project(456)
    data2 = pool.get("data", agent_id="agent_3")

    # 应该是隔离的
    assert data1 == "project_123_data"
    assert data2 == "project_456_data"


def test_context_pool_data_lineage():
    """测试数据血缘"""
    pool = SharedContextPool()
    pool.set_project(123)

    # Agent A 创建
    pool.set("entities", [], agent_id="agent_a")

    # Agent B 更新
    pool.set("entities", [{"name": "A"}], agent_id="agent_b")

    # Agent C 更新
    pool.set("entities", [{"name": "A"}, {"name": "B"}], agent_id="agent_c")

    # 获取血缘
    lineage = pool.get_data_lineage("entities")

    # 应该有3条记录
    assert len(lineage) == 3
    assert lineage[0]["agent_id"] == "agent_a"
    assert lineage[1]["agent_id"] == "agent_b"
    assert lineage[2]["agent_id"] == "agent_c"


def test_context_pool_version_tracking():
    """测试版本追踪"""
    pool = SharedContextPool()
    pool.set_project(123)

    # 初始版本
    pool.set("data", "v1", agent_id="agent_1")
    entry1 = pool.get_entry("data")
    assert entry1.version == 1

    # 更新
    pool.set("data", "v2", agent_id="agent_2")
    entry2 = pool.get_entry("data")
    assert entry2.version == 2

    # 再次更新
    pool.set("data", "v3", agent_id="agent_3")
    entry3 = pool.get_entry("data")
    assert entry3.version == 3


def test_context_pool_access_logs():
    """测试访问日志"""
    pool = SharedContextPool()
    pool.set_project(123)

    # 写入
    pool.set("test_key", "test_value", agent_id="agent_a")

    # 读取
    pool.get("test_key", agent_id="agent_b")
    pool.get("test_key", agent_id="agent_c")

    # 获取日志
    logs = pool.get_access_logs(key="test_key")

    # 应该有3条：1次写入，2次读取
    assert len(logs) == 3
    assert logs[0].access_type == AccessType.WRITE
    assert logs[1].access_type == AccessType.READ
    assert logs[2].access_type == AccessType.READ


# ==================== 协同场景测试 ====================

@pytest.mark.asyncio
async def test_collaborative_scenario_entity_enrichment():
    """
    测试协同场景：实体补充

    流程：
    1. KnowledgeAgent提取实体
    2. 发布entity.extracted消息
    3. SearchAgent自动订阅并爬取补充信息
    4. SearchAgent更新共享上下文
    """
    bus = AgentMessageBus()
    pool = SharedContextPool()
    pool.set_project(123)

    # 模拟KnowledgeAgent
    class MockKnowledgeAgent:
        async def extract_entities(self, text: str):
            entities = [
                {"name": "NVIDIA", "type": "ORG"},
                {"name": "Jensen Huang", "type": "PER"}
            ]

            # 写入上下文
            pool.set("entities", entities, agent_id="knowledge_agent_001")

            # 发布消息
            await bus.publish(
                topic="entity.extracted",
                sender="knowledge_agent_001",
                payload={"entities": entities, "count": len(entities)}
            )

            return entities

    # 模拟SearchAgent
    class MockSearchAgent:
        async def on_entity_extracted(self, message: AgentMessage):
            entities = message.payload.get("entities", [])

            # 模拟爬取补充信息
            enriched_entities = []
            for entity in entities:
                enriched = {
                    **entity,
                    "description": f"Description of {entity['name']}",
                    "source": "Wikipedia"
                }
                enriched_entities.append(enriched)

            # 更新上下文
            pool.set(
                "enriched_entities",
                enriched_entities,
                agent_id="search_agent_001"
            )

            # 发布完成消息
            await bus.publish(
                topic="entity.enriched",
                sender="search_agent_001",
                payload={"count": len(enriched_entities)}
            )

    # 初始化
    knowledge_agent = MockKnowledgeAgent()
    search_agent = MockSearchAgent()

    # SearchAgent订阅
    bus.subscribe("entity.extracted", search_agent.on_entity_extracted)

    # 执行流程
    entities = await knowledge_agent.extract_entities("NVIDIA CEO Jensen Huang...")

    # 等待异步处理
    await asyncio.sleep(0.2)

    # 验证结果
    enriched = pool.get("enriched_entities", agent_id="test")
    assert len(enriched) == 2
    assert "description" in enriched[0]
    assert enriched[0]["source"] == "Wikipedia"


@pytest.mark.asyncio
async def test_collaborative_scenario_parallel_processing():
    """
    测试协同场景：并行处理

    流程：
    1. CoordinatorAgent分发任务
    2. 多个Agent并行处理
    3. 结果汇总到共享上下文
    """
    bus = AgentMessageBus()
    pool = SharedContextPool()
    pool.set_project(123)

    # 共享文本
    text = "NVIDIA is a technology company founded by Jensen Huang."
    pool.set("text", text, agent_id="coordinator")

    # 模拟EntityAgent
    async def entity_agent_process(message: AgentMessage):
        text = pool.get("text", agent_id="entity_agent_001")
        entities = [{"name": "NVIDIA", "type": "ORG"}]
        pool.set("entities", entities, agent_id="entity_agent_001")
        await bus.publish(
            topic="entity.completed",
            sender="entity_agent_001",
            payload={"count": 1}
        )

    # 模拟RelationAgent
    async def relation_agent_process(message: AgentMessage):
        text = pool.get("text", agent_id="relation_agent_001")
        relations = [{"head": "NVIDIA", "relation": "founded_by", "tail": "Jensen Huang"}]
        pool.set("relations", relations, agent_id="relation_agent_001")
        await bus.publish(
            topic="relation.completed",
            sender="relation_agent_001",
            payload={"count": 1}
        )

    # 订阅
    bus.subscribe("task.entity_extract", entity_agent_process)
    bus.subscribe("task.relation_extract", relation_agent_process)

    # 并行分发任务
    await asyncio.gather(
        bus.publish("task.entity_extract", "coordinator", {}),
        bus.publish("task.relation_extract", "coordinator", {})
    )

    # 等待处理
    await asyncio.sleep(0.2)

    # 验证结果
    entities = pool.get("entities", agent_id="test")
    relations = pool.get("relations", agent_id="test")

    assert len(entities) == 1
    assert len(relations) == 1
    assert relations[0]["head"] == "NVIDIA"


def test_stats_and_monitoring():
    """测试统计和监控"""
    bus = AgentMessageBus()
    pool = SharedContextPool()

    # 一些操作
    pool.set_project(123)
    pool.set("key1", "value1", agent_id="agent_1")
    pool.get("key1", agent_id="agent_2")
    pool.get("key1", agent_id="agent_3")

    # 获取统计
    pool_stats = pool.get_stats()
    bus_stats = bus.get_stats()

    assert pool_stats["reads"] == 2
    assert pool_stats["writes"] == 1
    assert pool_stats["agents_active"] == 3


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
