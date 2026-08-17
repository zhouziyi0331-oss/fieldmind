"""
Tests for SuperKnowledgeAgent

Focused test coverage for the elite knowledge graph agent.
"""

import pytest
import asyncio
import uuid
from typing import Dict, Any, List

from app.services.agents.super_knowledge_agent import (
    SuperKnowledgeAgent,
    KnowledgeGraphStrategy,
    KnowledgeQueryType,
    KnowledgeGraphResult
)
from app.services.agents.base_agent import AgentStatus, AgentTask, AgentRole
from app.services.agents.agent_mesh import AgentState
from app.services.plugins.plugin_registry import get_plugin_registry
from app.services.plugins.plugin_loader import PluginLoader, LoadStrategy, get_plugin_loader


@pytest.fixture
def setup_test_environment():
    """Setup test environment with registry and loader"""
    registry = get_plugin_registry()
    loader = get_plugin_loader()
    return registry, loader


@pytest.fixture
def knowledge_agent(setup_test_environment):
    """Create SuperKnowledgeAgent instance for testing"""
    registry, loader = setup_test_environment
    agent = SuperKnowledgeAgent(
        agent_id="test_knowledge_agent",
        registry=registry,
        loader=loader
    )
    return agent


# ==================== Agent Initialization Tests ====================

def test_agent_initialization(knowledge_agent):
    """Test SuperKnowledgeAgent initializes correctly"""
    assert knowledge_agent.agent_id == "test_knowledge_agent"
    assert knowledge_agent.status == AgentStatus.IDLE
    assert len(knowledge_agent.capabilities) == 8
    assert knowledge_agent.registry is not None
    assert knowledge_agent.loader is not None
    assert knowledge_agent.role == AgentRole.KNOWLEDGE


def test_agent_properties(knowledge_agent):
    """Test agent properties"""
    assert knowledge_agent.name == "超级知识图谱Agent"
    assert "知识图谱" in knowledge_agent.description
    assert knowledge_agent.role == AgentRole.KNOWLEDGE


def test_agent_capabilities(knowledge_agent):
    """Test agent has correct capabilities"""
    capabilities = knowledge_agent.capabilities
    assert 'entity_extraction' in capabilities
    assert 'relationship_mapping' in capabilities
    assert 'community_detection' in capabilities
    assert 'temporal_evolution' in capabilities
    assert 'semantic_search' in capabilities
    assert 'graph_reasoning' in capabilities
    assert 'multi_plugin_fusion' in capabilities
    assert 'automatic_fallback' in capabilities


def test_kg_capabilities_mapping(knowledge_agent):
    """Test knowledge graph capabilities are correctly mapped"""
    assert 'graph_rag' in knowledge_agent.kg_capabilities
    assert 'temporal_graph' in knowledge_agent.kg_capabilities
    assert 'cognitive_graph' in knowledge_agent.kg_capabilities

    assert knowledge_agent.kg_capabilities['graph_rag'] == 'graphrag'
    assert knowledge_agent.kg_capabilities['temporal_graph'] == 'graphiti'
    assert knowledge_agent.kg_capabilities['cognitive_graph'] == 'cognee'


# ==================== KnowledgeGraphResult Tests ====================

def test_knowledge_graph_result_creation():
    """Test KnowledgeGraphResult creation and initialization"""
    result = KnowledgeGraphResult()

    assert result.entities == []
    assert result.relationships == []
    assert result.communities == []
    assert result.temporal_events == []
    assert result.cognitive_insights == []
    assert result.source_plugins == []
    assert result.execution_time == 0.0
    assert result.confidence_score == 0.0


def test_knowledge_graph_result_merge():
    """Test merging two KnowledgeGraphResult objects"""
    result1 = KnowledgeGraphResult(
        entities=[{'name': 'Entity1', 'type': 'PERSON'}],
        relationships=[{'source': 'Entity1', 'target': 'Entity2', 'type': 'KNOWS'}],
        source_plugins=['graphrag'],
        confidence_score=0.9
    )

    result2 = KnowledgeGraphResult(
        entities=[{'name': 'Entity2', 'type': 'ORGANIZATION'}],
        relationships=[{'source': 'Entity2', 'target': 'Entity3', 'type': 'EMPLOYS'}],
        source_plugins=['graphiti'],
        confidence_score=0.8
    )

    merged = result1.merge(result2)

    assert len(merged.entities) == 2
    assert len(merged.relationships) == 2
    assert 'graphrag' in merged.source_plugins
    assert 'graphiti' in merged.source_plugins
    assert merged.confidence_score == 0.85  # Average of 0.9 and 0.8


def test_knowledge_graph_result_to_dict():
    """Test converting KnowledgeGraphResult to dict"""
    result = KnowledgeGraphResult(
        entities=[{'name': 'Entity1', 'type': 'PERSON'}],
        relationships=[{'source': 'Entity1', 'target': 'Entity2', 'type': 'KNOWS'}],
        confidence_score=0.9
    )
    result.entity_count = 1
    result.relationship_count = 1

    result_dict = result.to_dict()

    assert 'entities' in result_dict
    assert 'relationships' in result_dict
    assert 'confidence_score' in result_dict
    assert result_dict['entity_count'] == 1
    assert result_dict['relationship_count'] == 1


# ==================== Task Execution Tests ====================

def test_execute_entity_extraction_task(knowledge_agent):
    """Test executing entity extraction task"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='entity_extraction',
        input_data={
            'query_type': 'entity_extraction',
            'content': 'Apple Inc. was founded by Steve Jobs in Cupertino, California.',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = knowledge_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True
    assert 'entities' in result.output_data
    assert knowledge_agent.stats['total_queries'] == 1
    assert knowledge_agent.stats['successful_queries'] == 1


def test_execute_relationship_mapping_task(knowledge_agent):
    """Test executing relationship mapping task"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='relationship_mapping',
        input_data={
            'query_type': 'relationship_mapping',
            'content': 'Steve Jobs founded Apple Inc. Tim Cook became CEO after Steve Jobs.',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result = knowledge_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True
    assert 'relationships' in result.output_data


def test_execute_community_detection_task(knowledge_agent):
    """Test executing community detection task"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='community_detection',
        input_data={
            'query_type': 'community_detection',
            'content': 'Tech companies like Apple, Google, Microsoft. Social networks like Facebook, Twitter.',
            'strategy': 'hierarchical',
            'parameters': {}
        }
    )

    result = knowledge_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True


def test_execute_temporal_evolution_task(knowledge_agent):
    """Test executing temporal evolution task"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='temporal_evolution',
        input_data={
            'query_type': 'temporal_evolution',
            'content': 'Apple released iPhone in 2007. Then iPad in 2010. Apple Watch in 2015.',
            'strategy': 'temporal',
            'parameters': {}
        }
    )

    result = knowledge_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True


def test_execute_semantic_search_task(knowledge_agent):
    """Test executing semantic search task"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='semantic_search',
        input_data={
            'query_type': 'semantic_search',
            'content': 'Find all technology companies founded in Silicon Valley',
            'parameters': {}
        }
    )

    result = knowledge_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True


def test_execute_graph_reasoning_task(knowledge_agent):
    """Test executing graph reasoning task"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='graph_reasoning',
        input_data={
            'query_type': 'graph_reasoning',
            'content': 'What is the relationship between Apple and Steve Jobs?',
            'parameters': {}
        }
    )

    result = knowledge_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True


# ==================== Strategy Tests ====================

@pytest.mark.asyncio
async def test_comprehensive_strategy(knowledge_agent):
    """Test comprehensive strategy uses multiple plugins"""
    content = "Test document for comprehensive extraction"
    parameters = {}

    result = await knowledge_agent.extract_entities(
        content,
        KnowledgeGraphStrategy.COMPREHENSIVE,
        parameters
    )

    assert isinstance(result, KnowledgeGraphResult)
    assert len(result.source_plugins) >= 1
    assert result.execution_time > 0


@pytest.mark.asyncio
async def test_fast_strategy(knowledge_agent):
    """Test fast strategy uses single fastest plugin"""
    content = "Test document for fast extraction"
    parameters = {}

    result = await knowledge_agent.extract_entities(
        content,
        KnowledgeGraphStrategy.FAST,
        parameters
    )

    assert isinstance(result, KnowledgeGraphResult)
    assert 'graphrag' in result.source_plugins
    assert result.execution_time > 0


@pytest.mark.asyncio
async def test_cognitive_strategy(knowledge_agent):
    """Test cognitive strategy uses Cognee"""
    content = "Test document for cognitive extraction"
    parameters = {}

    result = await knowledge_agent.extract_entities(
        content,
        KnowledgeGraphStrategy.COGNITIVE,
        parameters
    )

    assert isinstance(result, KnowledgeGraphResult)
    assert 'cognee' in result.source_plugins


# ==================== Agent Status Tests ====================

def test_get_status(knowledge_agent):
    """Test getting agent status"""
    status = knowledge_agent.get_status()

    assert 'agent_id' in status
    assert 'status' in status
    assert 'statistics' in status
    assert 'loaded_plugins' in status
    assert 'available_capabilities' in status

    assert status['agent_id'] == 'test_knowledge_agent'
    assert isinstance(status['statistics'], dict)


def test_get_capabilities_info(knowledge_agent):
    """Test getting capabilities information"""
    info = knowledge_agent.get_capabilities_info()

    assert 'knowledge_graph_plugins' in info
    assert 'query_types' in info
    assert 'strategies' in info
    assert 'usage_statistics' in info

    # Check plugin info
    assert 'graphrag' in info['knowledge_graph_plugins']
    assert 'graphiti' in info['knowledge_graph_plugins']
    assert 'cognee' in info['knowledge_graph_plugins']

    # Check query types
    assert 'entity_extraction' in info['query_types']
    assert 'relationship_mapping' in info['query_types']

    # Check strategies
    assert 'comprehensive' in info['strategies']
    assert 'fast' in info['strategies']


# ==================== Statistics Tests ====================

def test_statistics_tracking(knowledge_agent):
    """Test that statistics are correctly tracked"""
    initial_queries = knowledge_agent.stats['total_queries']

    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='entity_extraction',
        input_data={
            'query_type': 'entity_extraction',
            'content': 'Test content',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    knowledge_agent.execute_task(task)

    assert knowledge_agent.stats['total_queries'] == initial_queries + 1
    assert knowledge_agent.stats['successful_queries'] >= 1
    assert knowledge_agent.stats['entities_extracted'] >= 0


def test_plugin_usage_tracking(knowledge_agent):
    """Test that plugin usage is tracked"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='entity_extraction',
        input_data={
            'query_type': 'entity_extraction',
            'content': 'Test content',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    knowledge_agent.execute_task(task)

    # Should have tracked graphrag usage (fast strategy uses graphrag)
    assert 'graphrag' in knowledge_agent.stats['plugin_usage']
    assert knowledge_agent.stats['plugin_usage']['graphrag'] >= 1


# ==================== Integration Tests ====================

def test_complete_workflow(knowledge_agent):
    """Test complete workflow from task to result"""
    # Step 1: Execute entity extraction
    task1 = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='entity_extraction',
        input_data={
            'query_type': 'entity_extraction',
            'content': 'Apple Inc. was founded by Steve Jobs in Cupertino.',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result1 = knowledge_agent.execute_task(task1)
    assert result1.status == AgentStatus.COMPLETED

    # Step 2: Execute relationship mapping
    task2 = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='relationship_mapping',
        input_data={
            'query_type': 'relationship_mapping',
            'content': 'Steve Jobs founded Apple. Tim Cook succeeded Steve Jobs.',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result2 = knowledge_agent.execute_task(task2)
    assert result2.status == AgentStatus.COMPLETED

    # Step 3: Check statistics
    assert knowledge_agent.stats['total_queries'] >= 2
    assert knowledge_agent.stats['successful_queries'] >= 2

    # Step 4: Get status
    status = knowledge_agent.get_status()
    assert status['status'] == AgentStatus.IDLE.value


def test_multiple_tasks_sequential(knowledge_agent):
    """Test executing multiple tasks sequentially"""
    tasks_data = [
        ('entity_extraction', 'Apple Inc.'),
        ('relationship_mapping', 'Steve Jobs founded Apple'),
        ('community_detection', 'Tech companies: Apple, Google, Microsoft')
    ]

    for query_type, content in tasks_data:
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type=query_type,
            input_data={
                'query_type': query_type,
                'content': content,
                'strategy': 'fast',
                'parameters': {}
            }
        )

        result = knowledge_agent.execute_task(task)
        assert result.status == AgentStatus.COMPLETED

    assert knowledge_agent.stats['total_queries'] >= 3


# ==================== Error Handling Tests ====================

def test_invalid_query_type(knowledge_agent):
    """Test handling invalid query type"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='invalid_type',
        input_data={
            'query_type': 'INVALID_QUERY_TYPE',
            'content': 'Test content',
            'parameters': {}
        }
    )

    result = knowledge_agent.execute_task(task)

    assert result.status == AgentStatus.FAILED
    assert result.success is False
    assert len(result.errors) > 0


def test_empty_content(knowledge_agent):
    """Test handling empty content"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='entity_extraction',
        input_data={
            'query_type': 'entity_extraction',
            'content': '',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = knowledge_agent.execute_task(task)

    # Should handle gracefully (either success with empty result or error)
    assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]
