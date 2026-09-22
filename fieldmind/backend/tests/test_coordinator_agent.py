"""
Test suite for EnhancedCoordinatorAgent - Phase 2 Day 5

Tests cover:
- Agent initialization and properties
- Task categorization logic
- Coordination strategy selection
- Single agent execution
- Sequential workflow execution
- Parallel execution
- Redundant verification
- Performance metrics
- Agent recommendation
- Error handling
- Load balancing

Author: Claude + User
Date: 2026-08-14
"""

import pytest
import uuid
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from app.services.agents.base_agent import AgentTask, AgentStatus, AgentRole
from app.services.agents.agent_mesh import AgentResult
from app.services.agents.coordinator_agent import (
    EnhancedCoordinatorAgent,
    TaskCategory,
    CoordinationStrategy,
    AgentAllocation,
    CoordinationResult,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def coordinator():
    """Create coordinator agent instance"""
    return EnhancedCoordinatorAgent(agent_id="test_coordinator")


@pytest.fixture
def mock_knowledge_agent():
    """Mock SuperKnowledgeAgent"""
    mock_agent = Mock()
    mock_agent.name = "SuperKnowledgeAgent"
    mock_agent.execute_task.return_value = AgentResult(
        task_id=str(uuid.uuid4()),
        agent_id="mock_knowledge",
        status=AgentStatus.COMPLETED,
        output_data={
            'result': 'knowledge_graph',
            'confidence_score': 0.9,
        }
    )
    return mock_agent


@pytest.fixture
def mock_search_agent():
    """Mock SuperSearchAgent"""
    mock_agent = Mock()
    mock_agent.name = "SuperSearchAgent"
    mock_agent.execute_task.return_value = AgentResult(
        task_id=str(uuid.uuid4()),
        agent_id="mock_search",
        status=AgentStatus.COMPLETED,
        output_data={
            'result': 'search_results',
            'confidence_score': 0.85,
        }
    )
    return mock_agent


@pytest.fixture
def mock_summary_agent():
    """Mock SuperSummaryAgent"""
    mock_agent = Mock()
    mock_agent.name = "SuperSummaryAgent"
    mock_agent.execute_task.return_value = AgentResult(
        task_id=str(uuid.uuid4()),
        agent_id="mock_summary",
        status=AgentStatus.COMPLETED,
        output_data={
            'result': 'summary_content',
            'confidence_score': 0.88,
        }
    )
    return mock_agent


@pytest.fixture
def mock_transcript_agent():
    """Mock SuperTranscriptAgent"""
    mock_agent = Mock()
    mock_agent.name = "SuperTranscriptAgent"
    mock_agent.execute_task.return_value = AgentResult(
        task_id=str(uuid.uuid4()),
        agent_id="mock_transcript",
        status=AgentStatus.COMPLETED,
        output_data={
            'result': 'markdown_content',
            'confidence_score': 0.92,
        }
    )
    return mock_agent


# ============================================================================
# Basic Properties Tests
# ============================================================================

def test_coordinator_initialization(coordinator):
    """Test coordinator agent initialization"""
    assert coordinator.agent_id == "test_coordinator"
    assert coordinator.status == AgentStatus.IDLE
    assert coordinator.role == AgentRole.COORDINATOR
    assert coordinator.name == "增强协调代理"

    # Check capabilities
    assert len(coordinator.capabilities) == 9
    assert "intelligent_task_routing" in coordinator.capabilities
    assert "multi_agent_collaboration" in coordinator.capabilities
    assert "workflow_orchestration" in coordinator.capabilities


def test_agent_allocations(coordinator):
    """Test agent allocations initialized correctly"""
    assert len(coordinator.agent_allocations) == 4
    assert 'knowledge' in coordinator.agent_allocations
    assert 'search' in coordinator.agent_allocations
    assert 'summary' in coordinator.agent_allocations
    assert 'transcript' in coordinator.agent_allocations

    # Check allocation properties
    for key, allocation in coordinator.agent_allocations.items():
        assert isinstance(allocation, AgentAllocation)
        assert allocation.task_count == 0
        assert allocation.success_count == 0
        assert allocation.failure_count == 0
        assert allocation.agent_instance is None


def test_task_routing_map(coordinator):
    """Test task routing map configured correctly"""
    assert len(coordinator.task_routing) == 4
    assert coordinator.task_routing[TaskCategory.KNOWLEDGE_GRAPH] == 'knowledge'
    assert coordinator.task_routing[TaskCategory.WEB_SEARCH] == 'search'
    assert coordinator.task_routing[TaskCategory.DOCUMENT_SUMMARY] == 'summary'
    assert coordinator.task_routing[TaskCategory.FORMAT_CONVERSION] == 'transcript'


def test_workflow_templates(coordinator):
    """Test workflow templates defined"""
    assert len(coordinator.workflow_templates) == 3
    assert 'analyze_research_paper' in coordinator.workflow_templates
    assert 'build_knowledge_base' in coordinator.workflow_templates
    assert 'verify_content' in coordinator.workflow_templates

    # Check template structure
    template = coordinator.workflow_templates['analyze_research_paper']
    assert len(template) == 3
    assert template[0][0] == 'transcript'
    assert template[1][0] == 'summary'
    assert template[2][0] == 'knowledge'


# ============================================================================
# Task Categorization Tests
# ============================================================================

def test_categorize_task_explicit_category(coordinator):
    """Test task categorization with explicit category"""
    input_data = {'task_category': 'knowledge_graph'}
    category = coordinator._categorize_task(input_data)
    assert category == TaskCategory.KNOWLEDGE_GRAPH


def test_categorize_task_by_query_type_knowledge(coordinator):
    """Test categorization by knowledge-related keywords"""
    test_cases = [
        {'query_type': 'entity_extraction'},
        {'query_type': 'knowledge_graph_construction'},
        {'task_type': 'relation_extraction'},
    ]

    for input_data in test_cases:
        category = coordinator._categorize_task(input_data)
        assert category == TaskCategory.KNOWLEDGE_GRAPH


def test_categorize_task_by_query_type_search(coordinator):
    """Test categorization by search-related keywords"""
    test_cases = [
        {'query_type': 'web_search'},
        {'query_type': 'crawl_website'},
        {'task_type': 'browse_pages'},
    ]

    for input_data in test_cases:
        category = coordinator._categorize_task(input_data)
        assert category == TaskCategory.WEB_SEARCH


def test_categorize_task_by_query_type_summary(coordinator):
    """Test categorization by summary-related keywords"""
    test_cases = [
        {'query_type': 'document_summary'},
        {'query_type': 'extract_key_points'},
        {'task_type': 'memory_extraction'},
    ]

    for input_data in test_cases:
        category = coordinator._categorize_task(input_data)
        assert category == TaskCategory.DOCUMENT_SUMMARY


def test_categorize_task_by_query_type_transcript(coordinator):
    """Test categorization by transcript-related keywords"""
    test_cases = [
        {'query_type': 'format_conversion'},
        {'query_type': 'convert_to_markdown'},
        {'task_type': 'pdf_processing'},
    ]

    for input_data in test_cases:
        category = coordinator._categorize_task(input_data)
        assert category == TaskCategory.FORMAT_CONVERSION


def test_categorize_task_workflow_template(coordinator):
    """Test categorization for workflow template"""
    input_data = {'workflow_template': 'analyze_research_paper'}
    category = coordinator._categorize_task(input_data)
    assert category == TaskCategory.COMPLEX_WORKFLOW


def test_categorize_task_default(coordinator):
    """Test default categorization"""
    input_data = {'unknown_field': 'unknown_value'}
    category = coordinator._categorize_task(input_data)
    assert category == TaskCategory.COMPLEX_WORKFLOW


# ============================================================================
# Coordination Strategy Selection Tests
# ============================================================================

def test_select_strategy_explicit(coordinator):
    """Test explicit strategy selection"""
    input_data = {'coordination_strategy': 'parallel'}
    category = TaskCategory.KNOWLEDGE_GRAPH
    strategy = coordinator._select_coordination_strategy(category, input_data)
    assert strategy == CoordinationStrategy.PARALLEL


def test_select_strategy_complex_workflow_parallel(coordinator):
    """Test strategy for complex workflow with parallel flag"""
    input_data = {
        'workflow_template': 'build_knowledge_base',
        'parallel_execution': True,
    }
    category = TaskCategory.COMPLEX_WORKFLOW
    strategy = coordinator._select_coordination_strategy(category, input_data)
    assert strategy == CoordinationStrategy.PARALLEL


def test_select_strategy_complex_workflow_sequential(coordinator):
    """Test strategy for complex workflow without parallel flag"""
    input_data = {'workflow_template': 'analyze_research_paper'}
    category = TaskCategory.COMPLEX_WORKFLOW
    strategy = coordinator._select_coordination_strategy(category, input_data)
    assert strategy == CoordinationStrategy.SEQUENTIAL


def test_select_strategy_redundant_verification(coordinator):
    """Test redundant verification strategy"""
    input_data = {'redundant_verification': True}
    category = TaskCategory.DOCUMENT_SUMMARY
    strategy = coordinator._select_coordination_strategy(category, input_data)
    assert strategy == CoordinationStrategy.REDUNDANT


def test_select_strategy_default_single_agent(coordinator):
    """Test default single agent strategy"""
    input_data = {'query_type': 'simple_task'}
    category = TaskCategory.KNOWLEDGE_GRAPH
    strategy = coordinator._select_coordination_strategy(category, input_data)
    assert strategy == CoordinationStrategy.SINGLE_AGENT


# ============================================================================
# AgentAllocation Tests
# ============================================================================

def test_agent_allocation_metrics():
    """Test AgentAllocation metric calculations"""
    allocation = AgentAllocation(agent_type='TestAgent')

    # Initial state
    assert allocation.average_processing_time == 0.0
    assert allocation.success_rate == 0.0

    # After some tasks
    allocation.task_count = 10
    allocation.total_processing_time = 50.0
    allocation.success_count = 8
    allocation.failure_count = 2

    assert allocation.average_processing_time == 5.0
    assert allocation.success_rate == 0.8


# ============================================================================
# CoordinationResult Tests
# ============================================================================

def test_coordination_result_to_dict():
    """Test CoordinationResult serialization"""
    result = CoordinationResult(
        task_category=TaskCategory.KNOWLEDGE_GRAPH,
        coordination_strategy=CoordinationStrategy.SINGLE_AGENT,
        agents_involved=['SuperKnowledgeAgent'],
        primary_result={'data': 'test'},
        confidence_score=0.9,
    )

    result_dict = result.to_dict()

    assert result_dict['task_category'] == 'knowledge_graph'
    assert result_dict['coordination_strategy'] == 'single_agent'
    assert result_dict['agents_involved'] == ['SuperKnowledgeAgent']
    assert result_dict['primary_result'] == {'data': 'test'}
    assert result_dict['confidence_score'] == 0.9


# ============================================================================
# Single Agent Execution Tests
# ============================================================================

def test_execute_single_agent_knowledge(coordinator, mock_knowledge_agent):
    """Test single agent execution for knowledge graph"""
    coordinator.agent_allocations['knowledge'].agent_instance = mock_knowledge_agent

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='entity_extraction',
        input_data={'query_type': 'entity_extraction'}
    )

    result = coordinator.execute_task(task)

    # execute_task returns AgentResult, access output_data
    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data
    assert result_data['task_category'] == 'knowledge_graph'
    assert result_data['coordination_strategy'] == 'single_agent'
    assert 'SuperKnowledgeAgent' in result_data['agents_involved']
    assert result_data['confidence_score'] == 0.9
    assert 'Executed SuperKnowledgeAgent' in result_data['workflow_steps'][0]


def test_execute_single_agent_with_metrics_update(coordinator, mock_knowledge_agent):
    """Test that single agent execution updates metrics"""
    coordinator.agent_allocations['knowledge'].agent_instance = mock_knowledge_agent

    allocation = coordinator.agent_allocations['knowledge']
    initial_task_count = allocation.task_count

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='entity_extraction',
        input_data={'task_category': 'knowledge_graph'}
    )

    coordinator.execute_task(task)

    assert allocation.task_count == initial_task_count + 1
    assert allocation.success_count == 1
    assert allocation.total_processing_time > 0


def test_execute_single_agent_failure_handling(coordinator):
    """Test single agent execution with failure"""
    mock_agent = Mock()
    mock_agent.name = "FailingAgent"
    mock_agent.execute_task.side_effect = Exception("Agent failed")

    coordinator.agent_allocations['knowledge'].agent_instance = mock_agent

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='entity_extraction',
        input_data={'task_category': 'knowledge_graph'}
    )

    result = coordinator.execute_task(task)

    assert result.status == AgentStatus.COMPLETED  # Graceful degradation
    result_data = result.output_data
    assert 'errors' in result_data
    assert len(result_data['errors']) > 0
    assert 'FailingAgent failed' in result_data['errors'][0]

    # Check metrics updated
    allocation = coordinator.agent_allocations['knowledge']
    assert allocation.task_count == 1
    assert allocation.failure_count == 1


# ============================================================================
# Sequential Workflow Tests
# ============================================================================

def test_execute_sequential_workflow(coordinator, mock_transcript_agent,
                                     mock_summary_agent, mock_knowledge_agent):
    """Test sequential workflow execution"""
    coordinator.agent_allocations['transcript'].agent_instance = mock_transcript_agent
    coordinator.agent_allocations['summary'].agent_instance = mock_summary_agent
    coordinator.agent_allocations['knowledge'].agent_instance = mock_knowledge_agent

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='analyze_research_paper',
        input_data={
            'workflow_template': 'analyze_research_paper',
            'file_path': 'paper.pdf',
        }
    )

    result = coordinator.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data

    assert result_data['coordination_strategy'] == 'sequential'
    assert len(result_data['agents_involved']) == 3
    assert 'SuperTranscriptAgent' in result_data['agents_involved']
    assert 'SuperSummaryAgent' in result_data['agents_involved']
    assert 'SuperKnowledgeAgent' in result_data['agents_involved']

    # Check workflow steps
    assert len(result_data['workflow_steps']) == 3
    assert 'Step 1' in result_data['workflow_steps'][0]
    assert 'Step 2' in result_data['workflow_steps'][1]
    assert 'Step 3' in result_data['workflow_steps'][2]

    # Last agent's result is primary
    assert result_data['primary_result']['result'] == 'knowledge_graph'

    # Earlier results are auxiliary
    assert len(result_data['auxiliary_results']) == 2


def test_execute_sequential_with_step_failure(coordinator, mock_transcript_agent):
    """Test sequential workflow with step failure"""
    coordinator.agent_allocations['transcript'].agent_instance = mock_transcript_agent

    # Summary agent fails
    mock_failing_agent = Mock()
    mock_failing_agent.name = "FailingSummaryAgent"
    mock_failing_agent.execute_task.side_effect = Exception("Step failed")
    coordinator.agent_allocations['summary'].agent_instance = mock_failing_agent

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='analyze_research_paper',
        input_data={'workflow_template': 'analyze_research_paper'}
    )

    result = coordinator.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data

    # Should have error
    assert len(result_data['errors']) > 0
    assert 'Step 2' in result_data['errors'][0]
    assert 'failed' in result_data['errors'][0]

    # Should stop at failure
    assert len(result_data['agents_involved']) == 1  # Only first agent succeeded
    assert result_data['confidence_score'] < 1.0


def test_execute_sequential_unknown_template(coordinator):
    """Test sequential execution with unknown template"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='unknown_workflow',
        input_data={'workflow_template': 'unknown_template'}
    )

    result = coordinator.execute_task(task)

    # Should have error
    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data
    assert 'errors' in result_data
    assert len(result_data['errors']) > 0


# ============================================================================
# Parallel Execution Tests
# ============================================================================

def test_execute_parallel(coordinator, mock_search_agent, mock_transcript_agent):
    """Test parallel execution"""
    coordinator.agent_allocations['search'].agent_instance = mock_search_agent
    coordinator.agent_allocations['transcript'].agent_instance = mock_transcript_agent

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='parallel_task',
        input_data={
            'coordination_strategy': 'parallel',
            'parallel_agents': ['search', 'transcript'],
        }
    )

    result = coordinator.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data

    assert result_data['coordination_strategy'] == 'parallel'
    assert len(result_data['agents_involved']) == 2
    assert 'SuperSearchAgent' in result_data['agents_involved']
    assert 'SuperTranscriptAgent' in result_data['agents_involved']

    # Both results stored
    assert len(result_data['auxiliary_results']) == 2

    # Primary result is first successful
    assert result_data['primary_result'] is not None


def test_execute_parallel_with_one_failure(coordinator, mock_search_agent):
    """Test parallel execution with one agent failing"""
    coordinator.agent_allocations['search'].agent_instance = mock_search_agent

    # Transcript agent fails
    mock_failing = Mock()
    mock_failing.name = "FailingTranscriptAgent"
    mock_failing.execute_task.side_effect = Exception("Agent failed")
    coordinator.agent_allocations['transcript'].agent_instance = mock_failing

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='parallel_task',
        input_data={
            'coordination_strategy': 'parallel',
            'parallel_agents': ['search', 'transcript'],
        }
    )

    result = coordinator.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data

    # One success, one failure
    assert len(result_data['agents_involved']) == 1
    assert len(result_data['errors']) == 1
    assert result_data['confidence_score'] == 0.5  # 1/2 succeeded


def test_execute_parallel_no_agents_specified(coordinator):
    """Test parallel execution without specifying agents"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='parallel_task',
        input_data={'coordination_strategy': 'parallel'}
    )

    result = coordinator.execute_task(task)

    # Should have error
    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data
    assert 'errors' in result_data
    assert len(result_data['errors']) > 0


# ============================================================================
# Redundant Verification Tests
# ============================================================================

def test_execute_redundant_verification(coordinator, mock_summary_agent):
    """Test redundant verification execution"""
    coordinator.agent_allocations['summary'].agent_instance = mock_summary_agent

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='document_summary',
        input_data={
            'task_category': 'document_summary',
            'redundant_verification': True,
        }
    )

    result = coordinator.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data

    assert result_data['coordination_strategy'] == 'redundant'
    assert len(result_data['agents_involved']) == 2  # Same agent twice
    assert result_data['confidence_score'] >= 0.5  # At least some succeeded


# ============================================================================
# Performance Metrics Tests
# ============================================================================

def test_get_performance_metrics_initial(coordinator):
    """Test performance metrics in initial state"""
    metrics = coordinator.get_performance_metrics()

    assert len(metrics) == 4
    for agent_key in ['knowledge', 'search', 'summary', 'transcript']:
        assert agent_key in metrics
        assert metrics[agent_key]['task_count'] == 0
        assert metrics[agent_key]['success_rate'] == 0.0


def test_get_performance_metrics_after_tasks(coordinator, mock_knowledge_agent):
    """Test performance metrics after executing tasks"""
    coordinator.agent_allocations['knowledge'].agent_instance = mock_knowledge_agent

    # Execute multiple tasks
    for _ in range(3):
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type='entity_extraction',
            input_data={'task_category': 'knowledge_graph'}
        )
        coordinator.execute_task(task)

    metrics = coordinator.get_performance_metrics()

    assert metrics['knowledge']['task_count'] == 3
    assert metrics['knowledge']['success_count'] == 3
    assert metrics['knowledge']['success_rate'] == 1.0
    assert metrics['knowledge']['total_processing_time'] > 0


# ============================================================================
# Agent Recommendation Tests
# ============================================================================

def test_recommend_agent_knowledge_keywords(coordinator):
    """Test agent recommendation for knowledge-related task"""
    task_desc = "Extract entities and build knowledge graph"
    agent_key, score = coordinator.recommend_agent(task_desc)
    assert agent_key == 'knowledge'
    assert score > 0


def test_recommend_agent_search_keywords(coordinator):
    """Test agent recommendation for search-related task"""
    task_desc = "Search the web and crawl websites for information"
    agent_key, score = coordinator.recommend_agent(task_desc)
    assert agent_key == 'search'
    assert score > 0


def test_recommend_agent_summary_keywords(coordinator):
    """Test agent recommendation for summary-related task"""
    task_desc = "Summarize document and extract key points"
    agent_key, score = coordinator.recommend_agent(task_desc)
    assert agent_key == 'summary'
    assert score > 0


def test_recommend_agent_transcript_keywords(coordinator):
    """Test agent recommendation for transcript-related task"""
    task_desc = "Convert PDF to markdown format"
    agent_key, score = coordinator.recommend_agent(task_desc)
    assert agent_key == 'transcript'
    assert score > 0


def test_recommend_agent_with_performance_history(coordinator, mock_knowledge_agent):
    """Test recommendation considers performance history"""
    coordinator.agent_allocations['knowledge'].agent_instance = mock_knowledge_agent

    # Build performance history
    for _ in range(5):
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type='test',
            input_data={'task_category': 'knowledge_graph'}
        )
        coordinator.execute_task(task)

    # Now recommend for knowledge task
    agent_key, score = coordinator.recommend_agent("knowledge graph task")
    assert agent_key == 'knowledge'
    # Score should be boosted by performance
    assert score > 0.5


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_execute_task_with_invalid_input(coordinator):
    """Test task execution with invalid input"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='invalid_task',
        input_data=None
    )

    result = coordinator.execute_task(task)

    # Should complete with error (graceful degradation)
    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data
    assert 'errors' in result_data or 'warnings' in result_data


def test_create_agent_instance_invalid_key(coordinator):
    """Test creating agent with invalid key"""
    with pytest.raises(ValueError, match="Unknown agent key"):
        coordinator._create_agent_instance('invalid_key')


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_workflow_integration(coordinator, mock_transcript_agent,
                                   mock_summary_agent, mock_knowledge_agent):
    """Test full workflow from task to result"""
    # Setup all agents
    coordinator.agent_allocations['transcript'].agent_instance = mock_transcript_agent
    coordinator.agent_allocations['summary'].agent_instance = mock_summary_agent
    coordinator.agent_allocations['knowledge'].agent_instance = mock_knowledge_agent

    # Execute complete workflow
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='analyze_research_paper',
        input_data={
            'workflow_template': 'analyze_research_paper',
            'file_path': 'research_paper.pdf',
        }
    )

    result = coordinator.execute_task(task)

    # Verify complete workflow
    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data

    assert result_data['coordination_strategy'] == 'sequential'
    assert len(result_data['agents_involved']) == 3
    assert result_data['primary_result'] is not None
    assert len(result_data['auxiliary_results']) == 2
    assert result_data['confidence_score'] > 0.8
    assert result_data['total_processing_time'] > 0

    # Verify metrics updated for all agents
    metrics = coordinator.get_performance_metrics()
    assert metrics['transcript']['task_count'] == 1
    assert metrics['summary']['task_count'] == 1
    assert metrics['knowledge']['task_count'] == 1


def test_mixed_success_failure_workflow(coordinator):
    """Test workflow with mixed success and failure"""
    # First agent succeeds
    mock_success = Mock()
    mock_success.name = "SuccessAgent"
    mock_success.execute_task.return_value = AgentResult(
        task_id=str(uuid.uuid4()),
        agent_id="success",
        status=AgentStatus.COMPLETED,
        output_data={'result': 'success', 'confidence_score': 0.9}
    )
    coordinator.agent_allocations['transcript'].agent_instance = mock_success

    # Second agent fails
    mock_fail = Mock()
    mock_fail.name = "FailAgent"
    mock_fail.execute_task.side_effect = Exception("Failed")
    coordinator.agent_allocations['summary'].agent_instance = mock_fail

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='test_workflow',
        input_data={'workflow_template': 'analyze_research_paper'}
    )

    result = coordinator.execute_task(task)

    # Should have partial success
    assert result.status == AgentStatus.COMPLETED
    result_data = result.output_data

    assert len(result_data['agents_involved']) == 1
    assert len(result_data['errors']) > 0
    # Confidence score reflects partial completion (1/3 steps)
    assert result_data['confidence_score'] <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
