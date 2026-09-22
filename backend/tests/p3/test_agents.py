"""
Agent 系统测试
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from app.services.agents import (
    Agent,
    ReasoningAgent,
    AgentManager,
    AgentOrchestrator,
    AgentType,
    AgentStatus,
    ToolFactory,
    AgentAction
)


class TestAgent:
    """测试 Agent 基础功能"""

    def test_agent_creation(self):
        """测试创建 Agent"""
        tools = [ToolFactory.create_calculator_tool()]
        agent = Agent(
            agent_id="agent1",
            name="Test Agent",
            agent_type=AgentType.TASK,
            description="A test agent",
            tools=tools
        )

        assert agent.agent_id == "agent1"
        assert agent.name == "Test Agent"
        assert agent.status == AgentStatus.IDLE
        assert len(agent.tools) == 1

    def test_add_remove_tool(self):
        """测试添加和移除工具"""
        agent = Agent("agent1", "Test Agent", AgentType.TASK)

        # 添加工具
        tool = ToolFactory.create_calculator_tool()
        agent.add_tool(tool)
        assert "calculator" in agent.tools

        # 移除工具
        agent.remove_tool("calculator")
        assert "calculator" not in agent.tools

    async def test_execute_action(self):
        """测试执行动作"""
        tools = [ToolFactory.create_calculator_tool()]
        agent = Agent("agent1", "Test Agent", AgentType.TASK, tools=tools)

        action = AgentAction(
            action_id="action1",
            tool_name="calculator",
            parameters={"expression": "2 + 2"}
        )

        result = await agent.execute_action(action)
        assert result.result["result"] == 4
        assert result.error is None

    def test_agent_statistics(self):
        """测试 Agent 统计"""
        agent = Agent("agent1", "Test Agent", AgentType.TASK)
        agent.successful_actions = 10
        agent.failed_actions = 2
        agent.total_actions = 12

        stats = agent.get_statistics()
        assert stats["total_actions"] == 12
        assert stats["successful_actions"] == 10
        assert stats["success_rate"] == 10 / 12


class TestReasoningAgent:
    """测试推理型 Agent"""

    async def test_reasoning_agent(self):
        """测试推理 Agent"""
        tools = [
            ToolFactory.create_search_tool(),
            ToolFactory.create_calculator_tool()
        ]
        agent = ReasoningAgent(
            agent_id="reasoning1",
            name="Reasoning Agent",
            tools=tools
        )

        assert agent.agent_type == AgentType.TASK
        assert len(agent.tools) == 2

    async def test_think(self):
        """测试思考功能"""
        tools = [ToolFactory.create_search_tool()]
        agent = ReasoningAgent(
            agent_id="reasoning1",
            name="Reasoning Agent",
            tools=tools
        )

        actions = await agent.think("search for Python", {})
        assert len(actions) > 0
        assert actions[0].tool_name == "search"


class TestAgentManager:
    """测试 Agent 管理器"""

    def test_register_agent(self):
        """测试注册 Agent"""
        manager = AgentManager()
        agent = Agent("agent1", "Test Agent", AgentType.TASK)

        success = manager.register_agent(agent)
        assert success == True
        assert len(manager.agents) == 1

    def test_unregister_agent(self):
        """测试注销 Agent"""
        manager = AgentManager()
        agent = Agent("agent1", "Test Agent", AgentType.TASK)
        manager.register_agent(agent)

        success = manager.unregister_agent("agent1")
        assert success == True
        assert len(manager.agents) == 0

    def test_get_agent(self):
        """测试获取 Agent"""
        manager = AgentManager()
        agent = Agent("agent1", "Test Agent", AgentType.TASK)
        manager.register_agent(agent)

        retrieved = manager.get_agent("agent1")
        assert retrieved is not None
        assert retrieved.agent_id == "agent1"

    def test_list_agents(self):
        """测试列出 Agent"""
        manager = AgentManager()
        agent1 = Agent("agent1", "Agent 1", AgentType.TASK)
        agent2 = Agent("agent2", "Agent 2", AgentType.REACTIVE)
        manager.register_agent(agent1)
        manager.register_agent(agent2)

        # 列出所有
        all_agents = manager.list_agents()
        assert len(all_agents) == 2

        # 按类型过滤
        task_agents = manager.list_agents(agent_type=AgentType.TASK)
        assert len(task_agents) == 1

    async def test_execute_agent(self):
        """测试执行 Agent"""
        manager = AgentManager()
        tools = [ToolFactory.create_calculator_tool()]
        agent = ReasoningAgent(
            agent_id="agent1",
            name="Test Agent",
            tools=tools,
            max_iterations=2
        )
        manager.register_agent(agent)

        result = await manager.execute_agent(
            agent_id="agent1",
            task="calculate 5 + 3",
            background=False
        )

        assert "status" in result
        assert result["status"] in ["completed", "failed"]

    def test_pause_resume_cancel(self):
        """测试暂停、恢复、取消"""
        manager = AgentManager()
        agent = Agent("agent1", "Test Agent", AgentType.TASK)
        manager.register_agent(agent)
        agent.status = AgentStatus.RUNNING

        # 暂停
        manager.pause_agent("agent1")
        assert agent.status == AgentStatus.PAUSED

        # 恢复
        manager.resume_agent("agent1")
        assert agent.status == AgentStatus.RUNNING

        # 取消
        manager.cancel_agent("agent1")
        assert agent.status == AgentStatus.CANCELLED

    def test_manager_statistics(self):
        """测试管理器统计"""
        manager = AgentManager()
        agent1 = Agent("agent1", "Agent 1", AgentType.TASK)
        agent2 = Agent("agent2", "Agent 2", AgentType.REACTIVE)
        manager.register_agent(agent1)
        manager.register_agent(agent2)

        stats = manager.get_statistics()
        assert stats["total_agents"] == 2
        assert stats["idle_agents"] == 2


class TestToolFactory:
    """测试工具工厂"""

    def test_create_search_tool(self):
        """测试创建搜索工具"""
        tool = ToolFactory.create_search_tool()
        assert tool.name == "search"
        assert tool.executor is not None

    def test_create_calculator_tool(self):
        """测试创建计算器工具"""
        tool = ToolFactory.create_calculator_tool()
        assert tool.name == "calculator"
        assert tool.executor is not None

    def test_create_all_tools(self):
        """测试创建所有工具"""
        tools = ToolFactory.create_all_tools()
        assert len(tools) == 6
        tool_names = [t.name for t in tools]
        assert "search" in tool_names
        assert "calculator" in tool_names
        assert "llm" in tool_names


class TestTools:
    """测试工具执行"""

    async def test_calculator_tool(self):
        """测试计算器工具"""
        from app.services.agents.tools import calculator_tool

        result = await calculator_tool("2 + 2")
        assert result["success"] == True
        assert result["result"] == 4

    async def test_calculator_complex(self):
        """测试复杂计算"""
        from app.services.agents.tools import calculator_tool

        result = await calculator_tool("sqrt(16) + pow(2, 3)")
        assert result["success"] == True
        assert result["result"] == 12.0

    async def test_search_tool(self):
        """测试搜索工具"""
        from app.services.agents.tools import search_tool

        result = await search_tool("Python programming")
        assert result["query"] == "Python programming"
        assert "results" in result
        assert len(result["results"]) > 0


async def test_integration_agent_system():
    """集成测试：完整的 Agent 系统场景"""
    # 创建管理器
    manager = AgentManager()

    # 创建 Agent
    tools = [
        ToolFactory.create_calculator_tool(),
        ToolFactory.create_search_tool()
    ]
    agent = ReasoningAgent(
        agent_id="reasoning_agent",
        name="Reasoning Agent",
        tools=tools,
        max_iterations=3
    )

    # 注册
    success = manager.register_agent(agent)
    assert success == True

    # 执行任务
    result = await manager.execute_agent(
        agent_id="reasoning_agent",
        task="calculate 10 + 5",
        background=False
    )

    assert result["status"] in ["completed", "failed"]
    assert result["iterations"] >= 1

    # 获取统计
    stats = agent.get_statistics()
    assert stats["total_actions"] >= 0

    # 清理
    manager.unregister_agent("reasoning_agent")
    assert len(manager.agents) == 0


async def test_coordination():
    """测试 Agent 协调"""
    manager = AgentManager()

    # 创建多个 Agent
    for i in range(3):
        tools = [ToolFactory.create_calculator_tool()]
        agent = ReasoningAgent(
            agent_id=f"agent{i}",
            name=f"Agent {i}",
            tools=tools,
            max_iterations=2
        )
        manager.register_agent(agent)

    # 顺序执行
    result = await manager.coordinate_agents(
        agent_ids=["agent0", "agent1", "agent2"],
        task="calculate numbers",
        strategy="sequential"
    )

    assert result["strategy"] == "sequential"
    assert len(result["results"]) == 3


def run_async_test(coro):
    """运行异步测试"""
    return asyncio.run(coro)


if __name__ == "__main__":
    print("Running Agent system tests...")

    print("\n=== Testing Agent ===")
    test_agent = TestAgent()
    test_agent.test_agent_creation()
    test_agent.test_add_remove_tool()
    run_async_test(test_agent.test_execute_action())
    test_agent.test_agent_statistics()
    print("✓ Agent tests passed")

    print("\n=== Testing ReasoningAgent ===")
    test_reasoning = TestReasoningAgent()
    run_async_test(test_reasoning.test_reasoning_agent())
    run_async_test(test_reasoning.test_think())
    print("✓ ReasoningAgent tests passed")

    print("\n=== Testing AgentManager ===")
    test_manager = TestAgentManager()
    test_manager.test_register_agent()
    test_manager.test_unregister_agent()
    test_manager.test_get_agent()
    test_manager.test_list_agents()
    run_async_test(test_manager.test_execute_agent())
    test_manager.test_pause_resume_cancel()
    test_manager.test_manager_statistics()
    print("✓ AgentManager tests passed")

    print("\n=== Testing ToolFactory ===")
    test_factory = TestToolFactory()
    test_factory.test_create_search_tool()
    test_factory.test_create_calculator_tool()
    test_factory.test_create_all_tools()
    print("✓ ToolFactory tests passed")

    print("\n=== Testing Tools ===")
    test_tools = TestTools()
    run_async_test(test_tools.test_calculator_tool())
    run_async_test(test_tools.test_calculator_complex())
    run_async_test(test_tools.test_search_tool())
    print("✓ Tools tests passed")

    print("\n=== Running Integration Tests ===")
    run_async_test(test_integration_agent_system())
    run_async_test(test_coordination())
    print("✓ Integration tests passed")

    print("\n✅ All Agent system tests passed successfully!")
