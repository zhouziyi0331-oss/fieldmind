"""
测试 SuperSummaryAgent

测试覆盖：
1. Agent初始化和基础属性
2. SummaryResult数据类操作
3. 策略和查询类型枚举
4. 任务执行流程
5. 错误处理
6. 辅助方法
7. 集成测试

作者: FieldMind Team
日期: 2026-08-14
"""

import pytest
import uuid
from typing import Dict, Any

from app.services.agents.super_summary_agent import (
    SuperSummaryAgent,
    SummaryStrategy,
    SummaryQueryType,
    SummaryResult
)
from app.services.agents.base_agent import AgentRole, AgentStatus, AgentTask
from app.services.plugins.plugin_registry import get_plugin_registry
from app.services.plugins.plugin_loader import get_plugin_loader


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def summary_agent():
    """创建测试用SuperSummaryAgent实例"""
    registry = get_plugin_registry()
    loader = get_plugin_loader()
    agent = SuperSummaryAgent(
        agent_id="test_summary_agent",
        registry=registry,
        loader=loader
    )
    return agent


# ============================================================================
# 测试：Agent初始化和基础属性
# ============================================================================

def test_agent_initialization(summary_agent):
    """测试Agent初始化"""
    assert summary_agent.agent_id == "test_summary_agent"
    assert summary_agent.status == AgentStatus.IDLE
    assert summary_agent.role == AgentRole.SUMMARY
    assert len(summary_agent.capabilities) == 8
    assert "text_summarization" in summary_agent.capabilities
    assert "multi_plugin_fusion" in summary_agent.capabilities


def test_agent_name_and_description(summary_agent):
    """测试Agent名称和描述"""
    assert summary_agent.name == "超级总结代理"
    assert "ragflow" in summary_agent.description
    assert "LightRAG" in summary_agent.description
    assert "mem0" in summary_agent.description


def test_agent_role(summary_agent):
    """测试Agent角色"""
    assert summary_agent.role == AgentRole.SUMMARY


# ============================================================================
# 测试：SummaryResult数据类
# ============================================================================

def test_summary_result_initialization():
    """测试SummaryResult初始化"""
    result = SummaryResult()
    assert result.summary == ""
    assert result.key_points == []
    assert result.questions_answers == []
    assert result.chunks == []
    assert result.sources == []
    assert result.memory_context == {}
    assert result.metadata == {}
    assert result.source_plugins == []
    assert result.confidence_score == 0.0
    assert result.processing_time == 0.0


def test_summary_result_merge():
    """测试SummaryResult合并"""
    result1 = SummaryResult(
        summary="Short summary",
        key_points=["point1", "point2"],
        questions_answers=[
            {'question': 'q1', 'answer': 'a1'},
            {'question': 'q2', 'answer': 'a2'}
        ],
        sources=["source1", "source2"],
        source_plugins=["ragflow"],
        confidence_score=0.8
    )

    result2 = SummaryResult(
        summary="This is a much longer summary with more details",
        key_points=["point2", "point3"],  # point2 is duplicate
        questions_answers=[
            {'question': 'q1', 'answer': 'a1_different'},  # q1 is duplicate
            {'question': 'q3', 'answer': 'a3'}
        ],
        sources=["source2", "source3"],  # source2 is duplicate
        source_plugins=["LightRAG"],
        confidence_score=0.9
    )

    merged = result1.merge(result2)

    # Summary: 选择更长的
    assert merged.summary == "This is a much longer summary with more details"

    # Key points: 去重
    assert len(merged.key_points) == 3
    assert "point1" in merged.key_points
    assert "point2" in merged.key_points
    assert "point3" in merged.key_points

    # Questions/Answers: 按question去重
    assert len(merged.questions_answers) == 3
    questions = [qa['question'] for qa in merged.questions_answers]
    assert 'q1' in questions
    assert 'q2' in questions
    assert 'q3' in questions

    # Sources: 去重
    assert len(merged.sources) == 3
    assert "source1" in merged.sources
    assert "source2" in merged.sources
    assert "source3" in merged.sources

    # Source plugins: 合并
    assert set(merged.source_plugins) == {"ragflow", "LightRAG"}

    # Confidence score: 平均
    assert abs(merged.confidence_score - 0.85) < 0.01


def test_summary_result_to_dict():
    """测试SummaryResult转换为字典"""
    result = SummaryResult(
        summary="Test summary",
        key_points=["point1"],
        confidence_score=0.9,
        processing_time=1.5
    )

    result_dict = result.to_dict()

    assert result_dict['summary'] == "Test summary"
    assert result_dict['key_points'] == ["point1"]
    assert result_dict['confidence_score'] == 0.9
    assert result_dict['processing_time'] == 1.5


# ============================================================================
# 测试：策略和查询类型枚举
# ============================================================================

def test_summary_strategy_enum():
    """测试SummaryStrategy枚举"""
    assert SummaryStrategy.COMPREHENSIVE.value == "comprehensive"
    assert SummaryStrategy.FAST.value == "fast"
    assert SummaryStrategy.ENTERPRISE.value == "enterprise"
    assert SummaryStrategy.MEMORY_AWARE.value == "memory_aware"
    assert SummaryStrategy.REDUNDANT.value == "redundant"


def test_summary_query_type_enum():
    """测试SummaryQueryType枚举"""
    assert SummaryQueryType.TEXT_SUMMARIZATION.value == "text_summarization"
    assert SummaryQueryType.DOCUMENT_QA.value == "document_qa"
    assert SummaryQueryType.MULTI_LEVEL_SUMMARY.value == "multi_level_summary"
    assert SummaryQueryType.CONTEXT_AWARE_SUMMARY.value == "context_aware_summary"
    assert SummaryQueryType.PERSISTENT_MEMORY.value == "persistent_memory"
    assert SummaryQueryType.KNOWLEDGE_EXTRACTION.value == "knowledge_extraction"


# ============================================================================
# 测试：任务执行
# ============================================================================

def test_execute_text_summarization_task(summary_agent):
    """测试文本总结任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'text_summarization',
            'text': 'This is a long text that needs to be summarized.',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'summary' in result.output_data
    assert 'key_points' in result.output_data
    assert 'statistics' in result.output_data
    assert result.output_data['statistics']['query_type'] == 'text_summarization'
    assert result.output_data['statistics']['strategy'] == 'fast'


def test_execute_document_qa_task(summary_agent):
    """测试文档问答任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='document_qa',
        input_data={
            'query_type': 'document_qa',
            'query': 'What is the main topic?',
            'text': 'This is a document about AI and machine learning.',
            'strategy': 'enterprise',
            'parameters': {}
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'questions_answers' in result.output_data
    assert 'statistics' in result.output_data
    assert len(result.output_data['questions_answers']) > 0


def test_execute_multi_level_summary_task(summary_agent):
    """测试多级总结任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='multi_level_summary',
        input_data={
            'query_type': 'multi_level_summary',
            'text': 'Complex document with multiple sections and details.',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'summary' in result.output_data
    assert 'chunks' in result.output_data
    assert result.output_data['statistics']['strategy'] == 'comprehensive'


def test_execute_context_aware_summary_task(summary_agent):
    """测试上下文感知总结任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='context_aware_summary',
        input_data={
            'query_type': 'context_aware_summary',
            'text': 'Document requiring contextual understanding.',
            'strategy': 'memory_aware',
            'parameters': {}
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'memory_context' in result.output_data
    assert result.output_data['statistics']['strategy'] == 'memory_aware'


def test_execute_persistent_memory_task(summary_agent):
    """测试持久记忆任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='persistent_memory',
        input_data={
            'query_type': 'persistent_memory',
            'text': 'Information to be stored in persistent memory.',
            'strategy': 'memory_aware',
            'parameters': {}
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'memory_context' in result.output_data


def test_execute_knowledge_extraction_task(summary_agent):
    """测试知识提取任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='knowledge_extraction',
        input_data={
            'query_type': 'knowledge_extraction',
            'text': 'Text containing important knowledge and facts.',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'key_points' in result.output_data
    assert len(result.output_data['key_points']) > 0


def test_execute_comprehensive_strategy(summary_agent):
    """测试综合策略"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'text_summarization',
            'text': 'Text for comprehensive analysis.',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    stats = result.output_data['statistics']
    assert stats['strategy'] == 'comprehensive'
    # Comprehensive应该使用多个插件
    assert len(stats['plugins_used']) > 1


def test_execute_redundant_strategy(summary_agent):
    """测试冗余验证策略"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'text_summarization',
            'text': 'Text for redundant verification.',
            'strategy': 'redundant',
            'parameters': {}
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    stats = result.output_data['statistics']
    assert stats['strategy'] == 'redundant'


# ============================================================================
# 测试：错误处理
# ============================================================================

def test_execute_task_missing_query_type(summary_agent):
    """测试缺少query_type的任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'text': 'Some text',
            'strategy': 'fast'
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.FAILED
    assert len(result.errors) > 0
    assert 'Query type is required' in result.errors[0]


def test_execute_task_invalid_query_type(summary_agent):
    """测试无效的query_type"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'invalid_type',
            'text': 'Some text',
            'strategy': 'fast'
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.FAILED
    assert len(result.errors) > 0
    assert 'Invalid query type' in result.errors[0]


def test_execute_task_invalid_strategy(summary_agent):
    """测试无效的strategy"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'text_summarization',
            'text': 'Some text',
            'strategy': 'invalid_strategy'
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.FAILED
    assert len(result.errors) > 0
    assert 'Invalid strategy' in result.errors[0]


def test_execute_task_missing_text_for_summarization(summary_agent):
    """测试文本总结任务缺少text"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'text_summarization',
            'strategy': 'fast'
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.FAILED
    assert len(result.errors) > 0
    assert 'Text is required' in result.errors[0]


def test_execute_task_missing_query_for_document_qa(summary_agent):
    """测试文档问答任务缺少query"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='document_qa',
        input_data={
            'query_type': 'document_qa',
            'text': 'Some document',
            'strategy': 'fast'
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.FAILED
    assert len(result.errors) > 0
    assert 'Query is required' in result.errors[0]


# ============================================================================
# 测试：辅助方法
# ============================================================================

def test_get_plugin_for_capability(summary_agent):
    """测试根据能力获取插件"""
    assert summary_agent.get_plugin_for_capability('enterprise_rag') == 'ragflow'
    assert summary_agent.get_plugin_for_capability('lightweight_rag') == 'LightRAG'
    assert summary_agent.get_plugin_for_capability('persistent_memory') == 'mem0'
    assert summary_agent.get_plugin_for_capability('unknown_capability') is None


def test_get_available_strategies(summary_agent):
    """测试获取可用策略列表"""
    strategies = summary_agent.get_available_strategies()
    assert len(strategies) == 5
    assert 'comprehensive' in strategies
    assert 'fast' in strategies
    assert 'enterprise' in strategies
    assert 'memory_aware' in strategies
    assert 'redundant' in strategies


def test_get_available_query_types(summary_agent):
    """测试获取可用查询类型列表"""
    query_types = summary_agent.get_available_query_types()
    assert len(query_types) == 6
    assert 'text_summarization' in query_types
    assert 'document_qa' in query_types
    assert 'multi_level_summary' in query_types
    assert 'context_aware_summary' in query_types
    assert 'persistent_memory' in query_types
    assert 'knowledge_extraction' in query_types


def test_get_recommended_strategy(summary_agent):
    """测试推荐策略"""
    assert summary_agent.get_recommended_strategy(
        SummaryQueryType.TEXT_SUMMARIZATION
    ) == SummaryStrategy.FAST

    assert summary_agent.get_recommended_strategy(
        SummaryQueryType.DOCUMENT_QA
    ) == SummaryStrategy.ENTERPRISE

    assert summary_agent.get_recommended_strategy(
        SummaryQueryType.MULTI_LEVEL_SUMMARY
    ) == SummaryStrategy.COMPREHENSIVE

    assert summary_agent.get_recommended_strategy(
        SummaryQueryType.CONTEXT_AWARE_SUMMARY
    ) == SummaryStrategy.MEMORY_AWARE

    assert summary_agent.get_recommended_strategy(
        SummaryQueryType.KNOWLEDGE_EXTRACTION
    ) == SummaryStrategy.COMPREHENSIVE


# ============================================================================
# 测试：集成测试
# ============================================================================

def test_agent_lifecycle(summary_agent):
    """测试Agent生命周期"""
    # 初始状态
    assert summary_agent.status == AgentStatus.IDLE

    # 执行任务
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'text_summarization',
            'text': 'Test text',
            'strategy': 'fast'
        }
    )

    result = summary_agent.execute_task(task)

    # 任务完成后状态
    assert result.status == AgentStatus.COMPLETED
    assert summary_agent.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]


def test_multiple_tasks_sequential(summary_agent):
    """测试顺序执行多个任务"""
    # 第一个任务
    task1 = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'text_summarization',
            'text': 'First text',
            'strategy': 'fast'
        }
    )

    result1 = summary_agent.execute_task(task1)
    assert result1.status == AgentStatus.COMPLETED

    # 第二个任务
    task2 = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='document_qa',
        input_data={
            'query_type': 'document_qa',
            'query': 'What is this about?',
            'text': 'Second text',
            'strategy': 'enterprise'
        }
    )

    result2 = summary_agent.execute_task(task2)
    assert result2.status == AgentStatus.COMPLETED


def test_confidence_score_calculation(summary_agent):
    """测试置信度计算"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'text_summarization',
            'text': 'Test text',
            'strategy': 'comprehensive'
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'confidence_score' in result.output_data['statistics']
    # Comprehensive策略应该有较高置信度（多个插件）
    assert result.output_data['statistics']['confidence_score'] > 0.5


def test_processing_time_tracking(summary_agent):
    """测试处理时间跟踪"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='text_summarization',
        input_data={
            'query_type': 'text_summarization',
            'text': 'Test text',
            'strategy': 'fast'
        }
    )

    result = summary_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'processing_time' in result.output_data['statistics']
    assert result.output_data['statistics']['processing_time'] >= 0


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
