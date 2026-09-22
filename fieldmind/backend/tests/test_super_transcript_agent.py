"""
测试 SuperTranscriptAgent

测试覆盖：
1. 基础属性测试（初始化、角色、能力）
2. TranscriptResult 测试（创建、合并）
3. 策略枚举测试
4. 任务执行测试（各种查询类型和策略）
5. 错误处理测试
6. 辅助方法测试
7. 集成测试

作者: Agent Mesh Team
日期: 2026-08-14
Phase: 2 Day 4
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.agents.base_agent import AgentRole, AgentStatus, AgentTask
from app.services.agents.super_transcript_agent import (
    SuperTranscriptAgent,
    TranscriptQueryType,
    TranscriptResult,
    TranscriptStrategy,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_plugin_registry():
    """模拟插件注册表"""
    registry = MagicMock()
    registry.get_plugins_by_capability.return_value = [
        {'plugin_id': 'markitdown', 'priority': 10},
        {'plugin_id': 'PDF-Guru', 'priority': 9},
    ]
    return registry


@pytest.fixture
def mock_plugin_loader():
    """模拟插件加载器"""
    loader = MagicMock()
    loader.load_plugin.return_value = MagicMock()
    return loader


@pytest.fixture
def transcript_agent(mock_plugin_registry, mock_plugin_loader):
    """创建 SuperTranscriptAgent 实例"""
    agent = SuperTranscriptAgent(
        agent_id="test_transcript_agent",
        registry=mock_plugin_registry,
        loader=mock_plugin_loader
    )
    return agent


# ============================================================================
# 测试 1: 基础属性测试
# ============================================================================

def test_agent_initialization(transcript_agent):
    """测试代理初始化"""
    assert transcript_agent.agent_id == "test_transcript_agent"
    assert transcript_agent.status == AgentStatus.IDLE
    assert transcript_agent.role == AgentRole.TRANSCRIPT
    assert len(transcript_agent.capabilities) == 8
    assert "format_conversion" in transcript_agent.capabilities
    assert "multi_plugin_fusion" in transcript_agent.capabilities


def test_agent_properties(transcript_agent):
    """测试代理属性"""
    assert transcript_agent.name == "超级文档转换代理"
    assert "markitdown" in transcript_agent.description
    assert "PDF-Guru" in transcript_agent.description
    assert transcript_agent.role == AgentRole.TRANSCRIPT


def test_agent_capabilities_complete(transcript_agent):
    """测试代理能力完整性"""
    expected_capabilities = [
        "format_conversion",
        "content_extraction",
        "batch_processing",
        "quality_optimization",
        "metadata_extraction",
        "structure_analysis",
        "multi_plugin_fusion",
        "automatic_fallback",
    ]
    for cap in expected_capabilities:
        assert cap in transcript_agent.capabilities


# ============================================================================
# 测试 2: TranscriptResult 测试
# ============================================================================

def test_transcript_result_creation():
    """测试创建 TranscriptResult"""
    result = TranscriptResult(
        markdown_content="# Title\n\nContent",
        plain_text="Title Content",
        page_count=5,
        word_count=100,
    )
    assert result.markdown_content == "# Title\n\nContent"
    assert result.plain_text == "Title Content"
    assert result.page_count == 5
    assert result.word_count == 100
    assert result.confidence_score == 0.0


def test_transcript_result_merge():
    """测试 TranscriptResult 合并"""
    result1 = TranscriptResult(
        markdown_content="Short content",
        plain_text="Short",
        images=[
            {'image_id': 'img1', 'url': '/img1.png'},
            {'image_id': 'img2', 'url': '/img2.png'},
        ],
        tables=[
            {'table_id': 'tbl1', 'content': 'Table 1'},
        ],
        page_count=3,
        word_count=50,
        source_plugins=['markitdown'],
        confidence_score=0.8,
    )

    result2 = TranscriptResult(
        markdown_content="This is much longer content with more details",
        plain_text="Much longer text",
        images=[
            {'image_id': 'img2', 'url': '/img2.png'},  # 重复
            {'image_id': 'img3', 'url': '/img3.png'},
        ],
        tables=[
            {'table_id': 'tbl2', 'content': 'Table 2'},
        ],
        page_count=5,
        word_count=80,
        source_plugins=['PDF-Guru'],
        confidence_score=0.9,
    )

    merged = result1.merge(result2)

    # 验证选择更长的内容
    assert merged.markdown_content == "This is much longer content with more details"
    assert merged.plain_text == "Much longer text"

    # 验证图片去重（应该有3个：img1, img2, img3）
    assert len(merged.images) == 3
    image_ids = [img['image_id'] for img in merged.images]
    assert 'img1' in image_ids
    assert 'img2' in image_ids
    assert 'img3' in image_ids

    # 验证表格去重
    assert len(merged.tables) == 2

    # 验证计数取最大值
    assert merged.page_count == 5
    assert merged.word_count == 80

    # 验证来源合并
    assert 'markitdown' in merged.source_plugins
    assert 'PDF-Guru' in merged.source_plugins

    # 验证置信度平均
    assert abs(merged.confidence_score - 0.85) < 0.01


def test_transcript_result_merge_with_empty():
    """测试与空结果合并"""
    result = TranscriptResult(
        markdown_content="Content",
        confidence_score=0.9,
    )
    empty = TranscriptResult()

    merged = result.merge(empty)
    assert merged.markdown_content == "Content"
    assert merged.confidence_score == 0.9


# ============================================================================
# 测试 3: 策略枚举测试
# ============================================================================

def test_transcript_strategy_enum():
    """测试策略枚举"""
    assert TranscriptStrategy.COMPREHENSIVE.value == "comprehensive"
    assert TranscriptStrategy.FAST.value == "fast"
    assert TranscriptStrategy.PROFESSIONAL.value == "professional"
    assert TranscriptStrategy.BATCH.value == "batch"
    assert TranscriptStrategy.REDUNDANT.value == "redundant"


def test_transcript_query_type_enum():
    """测试查询类型枚举"""
    assert TranscriptQueryType.FORMAT_CONVERSION.value == "format_conversion"
    assert TranscriptQueryType.CONTENT_EXTRACTION.value == "content_extraction"
    assert TranscriptQueryType.BATCH_PROCESSING.value == "batch_processing"
    assert TranscriptQueryType.QUALITY_OPTIMIZATION.value == "quality_optimization"
    assert TranscriptQueryType.METADATA_EXTRACTION.value == "metadata_extraction"
    assert TranscriptQueryType.STRUCTURE_ANALYSIS.value == "structure_analysis"


# ============================================================================
# 测试 4: 任务执行测试
# ============================================================================

def test_execute_format_conversion_task(transcript_agent):
    """测试格式转换任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='format_conversion',
        input_data={
            'query_type': 'format_conversion',
            'file_path': '/path/to/document.pdf',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'markdown_content' in result.output_data
    assert 'statistics' in result.output_data
    assert result.output_data['statistics']['page_count'] >= 0


def test_execute_content_extraction_task(transcript_agent):
    """测试内容提取任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='content_extraction',
        input_data={
            'query_type': 'content_extraction',
            'file_path': '/path/to/document.pdf',
            'strategy': 'professional',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'markdown_content' in result.output_data
    assert 'images' in result.output_data
    assert 'tables' in result.output_data


def test_execute_batch_processing_task(transcript_agent):
    """测试批量处理任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='batch_processing',
        input_data={
            'query_type': 'batch_processing',
            'files': ['/path/to/doc1.pdf', '/path/to/doc2.pdf', '/path/to/doc3.pdf'],
            'strategy': 'batch',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'markdown_content' in result.output_data
    assert result.output_data['statistics']['page_count'] > 0


def test_execute_quality_optimization_task(transcript_agent):
    """测试质量优化任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='quality_optimization',
        input_data={
            'query_type': 'quality_optimization',
            'file_path': '/path/to/complex.pdf',
            'strategy': 'professional',
            'parameters': {'preserve_formatting': True}
        }
    )

    result = transcript_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['confidence_score'] > 0


def test_execute_metadata_extraction_task(transcript_agent):
    """测试元数据提取任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='metadata_extraction',
        input_data={
            'query_type': 'metadata_extraction',
            'file_path': '/path/to/document.pdf',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'metadata' in result.output_data


def test_execute_structure_analysis_task(transcript_agent):
    """测试结构分析任务"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='structure_analysis',
        input_data={
            'query_type': 'structure_analysis',
            'file_path': '/path/to/document.pdf',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert 'markdown_content' in result.output_data


def test_execute_with_comprehensive_strategy(transcript_agent):
    """测试综合策略"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='format_conversion',
        input_data={
            'query_type': 'format_conversion',
            'file_path': '/path/to/document.pdf',
            'strategy': 'comprehensive',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    # 综合策略应该有多个来源插件
    assert len(result.output_data.get('source_plugins', [])) >= 1


def test_execute_with_redundant_strategy(transcript_agent):
    """测试冗余策略"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='format_conversion',
        input_data={
            'query_type': 'format_conversion',
            'file_path': '/path/to/document.pdf',
            'strategy': 'redundant',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['confidence_score'] > 0


# ============================================================================
# 测试 5: 错误处理测试
# ============================================================================

def test_execute_with_invalid_query_type(transcript_agent):
    """测试无效查询类型（应自动降级到默认）"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='invalid_type',
        input_data={
            'query_type': 'invalid_query_type',
            'file_path': '/path/to/document.pdf',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    # 应该降级到默认查询类型并成功执行
    assert result.status == AgentStatus.COMPLETED


def test_execute_with_invalid_strategy(transcript_agent):
    """测试无效策略（应自动降级到默认）"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='format_conversion',
        input_data={
            'query_type': 'format_conversion',
            'file_path': '/path/to/document.pdf',
            'strategy': 'invalid_strategy',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    # 应该降级到默认策略并成功执行
    assert result.status == AgentStatus.COMPLETED


def test_execute_with_missing_file_path(transcript_agent):
    """测试缺少文件路径"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='format_conversion',
        input_data={
            'query_type': 'format_conversion',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    # 应该处理空文件路径
    assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]


def test_execute_with_empty_input_data(transcript_agent):
    """测试空输入数据"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='format_conversion',
        input_data={}
    )

    result = transcript_agent.execute_task(task)

    # 应该使用默认值执行
    assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED]


def test_execute_with_exception_handling(transcript_agent):
    """测试异常处理"""
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='format_conversion',
        input_data=None  # 这会导致异常
    )

    result = transcript_agent.execute_task(task)

    # 应该捕获异常并在 output_data 中记录错误
    # AgentBase 的行为：即使有异常，状态仍然是 COMPLETED，但 output_data 包含 error
    assert result.status == AgentStatus.COMPLETED
    assert 'error' in result.output_data
    assert result.output_data['confidence_score'] == 0.0


# ============================================================================
# 测试 6: 辅助方法测试
# ============================================================================

def test_get_supported_formats(transcript_agent):
    """测试获取支持的格式"""
    formats = transcript_agent.get_supported_formats()
    assert 'pdf' in formats
    assert 'docx' in formats
    assert 'pptx' in formats
    assert 'xlsx' in formats
    assert 'html' in formats
    assert len(formats) > 0


def test_get_query_types(transcript_agent):
    """测试获取查询类型"""
    query_types = transcript_agent.get_query_types()
    assert 'format_conversion' in query_types
    assert 'content_extraction' in query_types
    assert 'batch_processing' in query_types
    assert len(query_types) == 6


def test_get_strategies(transcript_agent):
    """测试获取策略"""
    strategies = transcript_agent.get_strategies()
    assert 'comprehensive' in strategies
    assert 'fast' in strategies
    assert 'professional' in strategies
    assert 'batch' in strategies
    assert 'redundant' in strategies
    assert len(strategies) == 5


def test_recommend_strategy_for_batch(transcript_agent):
    """测试批量处理策略推荐"""
    strategy = transcript_agent.recommend_strategy(
        file_count=20,
        file_format='pdf',
        quality_priority=False
    )
    assert strategy == TranscriptStrategy.BATCH


def test_recommend_strategy_for_quality_pdf(transcript_agent):
    """测试高质量 PDF 策略推荐"""
    strategy = transcript_agent.recommend_strategy(
        file_count=1,
        file_format='pdf',
        quality_priority=True
    )
    assert strategy == TranscriptStrategy.PROFESSIONAL


def test_recommend_strategy_for_fast_single_file(transcript_agent):
    """测试快速单文件策略推荐"""
    strategy = transcript_agent.recommend_strategy(
        file_count=1,
        file_format='docx',
        quality_priority=False
    )
    assert strategy == TranscriptStrategy.FAST


def test_recommend_strategy_default(transcript_agent):
    """测试默认策略推荐"""
    strategy = transcript_agent.recommend_strategy(
        file_count=3,
        file_format='pdf',
        quality_priority=False
    )
    assert strategy == TranscriptStrategy.COMPREHENSIVE


# ============================================================================
# 测试 7: 集成测试
# ============================================================================

def test_full_workflow_single_file(transcript_agent):
    """测试完整工作流：单文件转换"""
    # 1. 创建任务
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='format_conversion',
        input_data={
            'query_type': 'format_conversion',
            'file_path': '/path/to/report.pdf',
            'strategy': 'professional',
            'parameters': {}
        }
    )

    # 2. 执行任务
    result = transcript_agent.execute_task(task)

    # 3. 验证结果
    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['markdown_content']
    assert result.output_data['confidence_score'] > 0
    assert result.output_data['processing_time'] > 0


def test_full_workflow_batch_files(transcript_agent):
    """测试完整工作流：批量文件转换"""
    # 1. 创建任务
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='batch_processing',
        input_data={
            'query_type': 'batch_processing',
            'files': [f'/path/to/doc{i}.pdf' for i in range(10)],
            'strategy': 'batch',
            'parameters': {}
        }
    )

    # 2. 执行任务
    result = transcript_agent.execute_task(task)

    # 3. 验证结果
    assert result.status == AgentStatus.COMPLETED
    assert result.output_data['statistics']['page_count'] > 0


def test_full_workflow_with_content_extraction(transcript_agent):
    """测试完整工作流：内容提取"""
    # 1. 创建任务
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='content_extraction',
        input_data={
            'query_type': 'content_extraction',
            'file_path': '/path/to/thesis.pdf',
            'strategy': 'comprehensive',
            'parameters': {'extract_images': True, 'extract_tables': True}
        }
    )

    # 2. 执行任务
    result = transcript_agent.execute_task(task)

    # 3. 验证结果
    assert result.status == AgentStatus.COMPLETED
    assert 'images' in result.output_data
    assert 'tables' in result.output_data


def test_lifecycle_complete(transcript_agent):
    """测试完整生命周期"""
    # 初始状态
    assert transcript_agent.status == AgentStatus.IDLE

    # 创建并执行任务
    task = AgentTask(
        task_id=str(uuid.uuid4()),
        task_type='format_conversion',
        input_data={
            'query_type': 'format_conversion',
            'file_path': '/path/to/document.pdf',
            'strategy': 'fast',
            'parameters': {}
        }
    )

    result = transcript_agent.execute_task(task)

    # 验证完成
    assert result.status == AgentStatus.COMPLETED
    assert transcript_agent.status == AgentStatus.COMPLETED


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
