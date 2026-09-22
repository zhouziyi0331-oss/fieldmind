"""
测试Super Agents V2整合

验证：
1. Agent协调器工作正常
2. Agent注册中心工作正常
3. 专业Agent实例化
4. 多Agent编排流程
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.agent_coordinator import AgentCoordinator, ExecutionMode, AgentTask, DependencyGraph
from app.core.agent_registry import AgentRegistry, BaseAgent
from app.services.agents.specialized_agents import (
    KnowledgeAgent, SearchAgent, SummaryAgent, TranscriptAgent, AnalysisAgent
)
from app.services.super_agents_service_v2 import SuperAgentsServiceV2


class TestDependencyGraph:
    """测试依赖图"""

    def test_add_task(self):
        """测试添加任务"""
        graph = DependencyGraph()
        graph.add_task("task1", [])
        graph.add_task("task2", ["task1"])

        assert graph.in_degree["task1"] == 0
        assert graph.in_degree["task2"] == 1

    def test_topological_sort(self):
        """测试拓扑排序"""
        graph = DependencyGraph()
        graph.add_task("task1", [])
        graph.add_task("task2", ["task1"])
        graph.add_task("task3", ["task1"])
        graph.add_task("task4", ["task2", "task3"])

        layers = graph.topological_sort()

        assert len(layers) == 3
        assert layers[0] == ["task1"]
        assert set(layers[1]) == {"task2", "task3"}
        assert layers[2] == ["task4"]

    def test_cycle_detection(self):
        """测试循环依赖检测"""
        graph = DependencyGraph()
        graph.add_task("task1", ["task2"])
        graph.add_task("task2", ["task1"])

        assert graph.has_cycle() == True


class TestAgentCoordinator:
    """测试Agent协调器"""

    @pytest.fixture
    def mock_registry(self):
        """Mock注册中心"""
        registry = Mock()
        mock_agent = Mock()
        mock_agent.execute.return_value = {"result": "success"}
        registry.get_agent.return_value = mock_agent
        return registry

    @pytest.fixture
    def coordinator(self, mock_registry):
        """创建协调器实例"""
        return AgentCoordinator(mock_registry)

    def test_initialization(self, coordinator):
        """测试初始化"""
        assert coordinator is not None
        assert coordinator.max_retries == 3
        assert coordinator.max_parallel_tasks == 10

    def test_parallel_execution(self, coordinator):
        """测试并行执行"""
        tasks = [
            {
                'task_id': 'task1',
                'agent_type': 'test',
                'input_data': {'data': 1}
            },
            {
                'task_id': 'task2',
                'agent_type': 'test',
                'input_data': {'data': 2}
            }
        ]

        result = coordinator.orchestrate(tasks, ExecutionMode.PARALLEL)

        assert result['success'] == True
        assert result['execution_record']['total_tasks'] == 2

    def test_sequential_execution(self, coordinator):
        """测试串行执行"""
        tasks = [
            {
                'task_id': 'task1',
                'agent_type': 'test',
                'input_data': {'data': 1}
            },
            {
                'task_id': 'task2',
                'agent_type': 'test',
                'input_data': {'data': 2}
            }
        ]

        result = coordinator.orchestrate(tasks, ExecutionMode.SEQUENTIAL)

        assert result['success'] == True
        assert result['execution_record']['total_tasks'] == 2

    def test_dependency_execution(self, coordinator):
        """测试依赖图执行"""
        tasks = [
            {
                'task_id': 'task1',
                'agent_type': 'test',
                'input_data': {'data': 1},
                'dependencies': []
            },
            {
                'task_id': 'task2',
                'agent_type': 'test',
                'input_data': {'data': 2},
                'dependencies': ['task1']
            }
        ]

        result = coordinator.orchestrate(tasks, ExecutionMode.DEPENDENCY)

        assert result['success'] == True
        assert result['execution_record']['total_tasks'] == 2


class TestAgentRegistry:
    """测试Agent注册中心"""

    @pytest.fixture
    def registry(self):
        """创建注册中心实例"""
        return AgentRegistry()

    def test_initialization(self, registry):
        """测试初始化"""
        assert registry is not None
        assert len(registry._agents) == 0

    def test_register_agent_instance(self, registry):
        """测试注册Agent实例"""
        class TestAgent(BaseAgent):
            agent_type = "test"
            agent_name = "Test Agent"

            def execute(self, input_data):
                return {"result": "test"}

        agent = TestAgent()
        success = registry.register_agent("test", agent)

        assert success == True
        assert registry.has_agent("test") == True

    def test_register_agent_class(self, registry):
        """测试注册Agent类"""
        class TestAgent(BaseAgent):
            agent_type = "test"
            agent_name = "Test Agent"

            def execute(self, input_data):
                return {"result": "test"}

        success = registry.register_agent_class("test", TestAgent)

        assert success == True
        assert registry.has_agent("test") == True

    def test_get_agent_with_auto_create(self, registry):
        """测试获取Agent（自动创建）"""
        class TestAgent(BaseAgent):
            agent_type = "test"
            agent_name = "Test Agent"

            def execute(self, input_data):
                return {"result": "test"}

        registry.register_agent_class("test", TestAgent)

        agent = registry.get_agent("test", create_if_not_exists=True)

        assert agent is not None
        assert agent.agent_type == "test"

    def test_list_agents(self, registry):
        """测试列出Agent"""
        class TestAgent(BaseAgent):
            agent_type = "test"
            agent_name = "Test Agent"
            capabilities = ["test_capability"]

            def execute(self, input_data):
                return {"result": "test"}

        registry.register_agent_class("test", TestAgent)

        agents = registry.list_agents()

        assert len(agents) > 0
        assert any(a['agent_type'] == 'test' for a in agents)

    def test_find_agents_by_capability(self, registry):
        """测试按能力查找Agent"""
        class TestAgent(BaseAgent):
            agent_type = "test"
            agent_name = "Test Agent"
            capabilities = ["special_capability"]

            def execute(self, input_data):
                return {"result": "test"}

        agent = TestAgent()
        registry.register_agent("test", agent)

        matching = registry.find_agents_by_capability("special_capability")

        assert "test" in matching


class TestSpecializedAgents:
    """测试专业Agent"""

    def test_knowledge_agent_initialization(self):
        """测试知识Agent初始化"""
        agent = KnowledgeAgent()

        assert agent.agent_type == "knowledge"
        assert "entity_extraction" in agent.capabilities
        assert "relation_extraction" in agent.capabilities

    def test_search_agent_initialization(self):
        """测试检索Agent初始化"""
        agent = SearchAgent()

        assert agent.agent_type == "search"
        assert "document_search" in agent.capabilities
        assert "semantic_search" in agent.capabilities

    def test_summary_agent_initialization(self):
        """测试摘要Agent初始化"""
        agent = SummaryAgent()

        assert agent.agent_type == "summary"
        assert "text_summarization" in agent.capabilities

    def test_transcript_agent_initialization(self):
        """测试转录Agent初始化"""
        agent = TranscriptAgent()

        assert agent.agent_type == "transcript"
        assert "audio_transcription" in agent.capabilities

    def test_analysis_agent_initialization(self):
        """测试分析Agent初始化"""
        agent = AnalysisAgent()

        assert agent.agent_type == "analysis"
        assert "sentiment_analysis" in agent.capabilities


class TestSuperAgentsServiceV2:
    """测试Super Agents服务V2"""

    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        return SuperAgentsServiceV2(mock_db)

    def test_initialization(self, service):
        """测试初始化"""
        assert service is not None
        assert service.registry is not None
        assert service.coordinator is not None

    def test_builtin_agents_registered(self, service):
        """测试内置Agent已注册"""
        agents = service.list_available_agents()

        agent_types = [a['agent_type'] for a in agents]

        assert 'knowledge' in agent_types
        assert 'search' in agent_types
        assert 'summary' in agent_types
        assert 'transcript' in agent_types
        assert 'analysis' in agent_types

    def test_execute_single_agent(self, service):
        """测试执行单个Agent"""
        # Mock Agent执行
        with patch.object(service.registry, 'get_agent') as mock_get:
            mock_agent = Mock()
            mock_agent.execute.return_value = {"test": "result"}
            mock_get.return_value = mock_agent

            result = service.execute_agent(
                agent_type='test',
                input_data={'data': 'test'}
            )

            assert result['success'] == True
            assert 'result' in result

    def test_get_service_status(self, service):
        """测试获取服务状态"""
        status = service.get_service_status()

        assert 'service' in status
        assert status['service'] == 'super_agents_v2'
        assert 'registry' in status
        assert 'coordinator' in status
        assert 'builtin_agents' in status


class TestIntegration:
    """测试完整集成"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    def test_end_to_end_workflow(self, mock_db):
        """测试端到端工作流"""
        service = SuperAgentsServiceV2(mock_db)

        # 验证所有组件已初始化
        assert service.registry is not None
        assert service.coordinator is not None

        # 验证内置Agent已注册
        agents = service.list_available_agents()
        assert len(agents) >= 5

    def test_knowledge_extraction_workflow(self, mock_db):
        """测试知识提取工作流"""
        service = SuperAgentsServiceV2(mock_db)

        # Mock Agent执行
        with patch.object(service.registry, 'get_agent') as mock_get:
            mock_agent = Mock()
            mock_agent.execute.return_value = {"entities": [], "summary": "test"}
            mock_get.return_value = mock_agent

            result = service.knowledge_extraction_workflow(
                text="测试文本"
            )

            assert result is not None
            # 工作流应该执行2个任务（knowledge + summary）


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
