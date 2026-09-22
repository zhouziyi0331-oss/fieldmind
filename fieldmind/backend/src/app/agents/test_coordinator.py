"""
AgentCoordinator 测试套件

测试6Agent协调器的完整流水线
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from enum import Enum

from app.agents.coordinator import (
    AgentCoordinator,
    PipelineStage,
    PipelineMode,
    StageResult,
    PipelineResult
)


# ==================== Fixtures ====================

@pytest.fixture
def coordinator():
    """创建Coordinator实例"""
    return AgentCoordinator(
        default_mode=PipelineMode.FULL,
        enable_retry=True,
        max_retries=3,
        enable_checkpoint=True
    )


@pytest.fixture
def mock_db_session():
    """Mock数据库会话"""
    session = Mock()
    return session


@pytest.fixture
def sample_documents():
    """示例文档列表"""
    return [
        Mock(id=1, text_content='文档1内容', file_type='pdf', chunks=[1, 2], data_profile={'test': True}),
        Mock(id=2, text_content='文档2内容', file_type='docx', chunks=[3], data_profile=None)
    ]


# ==================== 测试类1: 初始化 ====================

class TestCoordinatorInitialization:
    """测试Coordinator初始化"""

    def test_default_initialization(self):
        """测试默认初始化"""
        coord = AgentCoordinator()

        assert coord.default_mode == PipelineMode.FULL
        assert coord.enable_retry is True
        assert coord.max_retries == 3
        assert coord.enable_checkpoint is True

    def test_custom_initialization(self):
        """测试自定义初始化"""
        coord = AgentCoordinator(
            default_mode=PipelineMode.QUICK,
            enable_retry=False,
            max_retries=5
        )

        assert coord.default_mode == PipelineMode.QUICK
        assert coord.enable_retry is False
        assert coord.max_retries == 5

    def test_agents_lazy_loading(self, coordinator):
        """测试Agent懒加载"""
        # 初始时所有Agent都未加载
        assert coordinator._document_agent is None
        assert coordinator._chunk_agent is None
        assert coordinator._analysis_agent is None
        assert coordinator._knowledge_agent is None
        assert coordinator._synthesis_agent is None
        assert coordinator._report_agent is None


# ==================== 测试类2: Agent加载 ====================

class TestAgentLoading:
    """测试各个Agent的懒加载"""

    @patch('app.agents.ingestion_agent.IngestionAgent')
    def test_load_document_agent(self, MockAgent, coordinator):
        """测试加载IngestionAgent (DocumentAgent)"""
        agent = coordinator._get_document_agent()

        MockAgent.assert_called_once()
        assert agent is not None

    @patch('app.agents.chunking_agent.ChunkingAgent')
    def test_load_chunk_agent(self, MockAgent, coordinator):
        """测试加载ChunkingAgent (ChunkAgent)"""
        agent = coordinator._get_chunk_agent()

        MockAgent.assert_called_once()
        assert agent is not None

    @patch('app.agents.vectorization_agent.VectorizationAgent')
    def test_load_analysis_agent(self, MockAgent, coordinator):
        """测试加载VectorizationAgent (AnalysisAgent)"""
        agent = coordinator._get_analysis_agent()

        MockAgent.assert_called_once()
        assert agent is not None

    @patch('app.agents.knowledge_agent.KnowledgeAgent')
    def test_load_knowledge_agent(self, MockAgent, coordinator):
        """测试加载KnowledgeAgent"""
        agent = coordinator._get_knowledge_agent()

        MockAgent.assert_called_once()
        assert agent is not None

    @patch('app.agents.synthesis_agent.SynthesisAgent')
    def test_load_synthesis_agent(self, MockAgent, coordinator):
        """测试加载SynthesisAgent"""
        agent = coordinator._get_synthesis_agent()

        MockAgent.assert_called_once()
        assert agent is not None

    @patch('app.agents.report_agent.ReportAgent')
    def test_load_report_agent(self, MockAgent, coordinator):
        """测试加载ReportAgent"""
        agent = coordinator._get_report_agent()

        MockAgent.assert_called_once()
        assert agent is not None


# ==================== 测试类3: 阶段确定 ====================

class TestStageDetermination:
    """测试阶段列表确定"""

    def test_determine_full_mode_stages(self, coordinator):
        """测试完整模式的阶段"""
        stages = coordinator._determine_stages(PipelineMode.FULL)

        assert len(stages) == 6
        assert PipelineStage.DOCUMENT_LOAD in stages
        assert PipelineStage.CHUNK in stages
        assert PipelineStage.ANALYSIS in stages
        assert PipelineStage.KNOWLEDGE in stages
        assert PipelineStage.SYNTHESIS in stages
        assert PipelineStage.REPORT in stages

    def test_determine_quick_mode_stages(self, coordinator):
        """测试快速模式的阶段（跳过知识图谱）"""
        stages = coordinator._determine_stages(PipelineMode.QUICK)

        assert len(stages) == 5
        assert PipelineStage.KNOWLEDGE not in stages
        assert PipelineStage.REPORT in stages

    def test_determine_analysis_only_stages(self, coordinator):
        """测试仅分析模式"""
        stages = coordinator._determine_stages(PipelineMode.ANALYSIS_ONLY)

        assert len(stages) == 3
        assert stages == [
            PipelineStage.DOCUMENT_LOAD,
            PipelineStage.CHUNK,
            PipelineStage.ANALYSIS
        ]

    def test_determine_report_only_stages(self, coordinator):
        """测试仅报告模式"""
        stages = coordinator._determine_stages(PipelineMode.REPORT_ONLY)

        assert len(stages) == 1
        assert stages == [PipelineStage.REPORT]

    def test_determine_custom_stages(self, coordinator):
        """测试自定义阶段"""
        custom = [PipelineStage.DOCUMENT_LOAD, PipelineStage.REPORT]
        stages = coordinator._determine_stages(PipelineMode.CUSTOM, custom)

        assert stages == custom


# ==================== 测试类4: 文档加载阶段 ====================

class TestDocumentLoadStage:
    """测试文档加载阶段"""

    @patch('app.models.project.ProjectDocument')
    def test_stage_document_load_success(self, MockDoc, coordinator, mock_db_session, sample_documents):
        """测试文档加载成功"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_documents

        output = coordinator._stage_document_load(1, mock_db_session)

        assert output['document_count'] == 2
        assert output['project_id'] == 1
        assert len(output['documents']) == 2

    @patch('app.models.project.ProjectDocument')
    def test_stage_document_load_empty(self, MockDoc, coordinator, mock_db_session):
        """测试空项目"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        output = coordinator._stage_document_load(1, mock_db_session)

        assert output['document_count'] == 0
        assert output['documents'] == []


# ==================== 测试类5: 分块阶段 ====================

class TestChunkStage:
    """测试分块阶段"""

    def test_stage_chunk_success(self, coordinator, mock_db_session, sample_documents):
        """测试分块成功"""
        # Mock前一阶段结果
        previous_results = {
            PipelineStage.DOCUMENT_LOAD: StageResult(
                stage=PipelineStage.DOCUMENT_LOAD,
                success=True,
                duration_seconds=1.0,
                output={'documents': sample_documents}
            )
        }

        with patch.object(coordinator, '_get_chunk_agent') as mock_get:
            mock_agent = Mock()
            # Mock ChunkingResult with chunks list
            mock_result = Mock()
            mock_chunk = Mock()
            mock_chunk.to_dict.return_value = {'chunk_id': 'test', 'text': 'test'}
            mock_result.chunks = [mock_chunk, mock_chunk, mock_chunk]  # 3 chunks per doc
            mock_agent.chunk_text.return_value = mock_result
            mock_get.return_value = mock_agent

            output = coordinator._stage_chunk(1, mock_db_session, previous_results)

            assert output['chunk_count'] == 6  # 2 docs * 3 chunks
            assert output['document_count'] == 2
            assert 'chunks' in output

    def test_stage_chunk_missing_document_load(self, coordinator, mock_db_session):
        """测试缺少文档加载阶段"""
        previous_results = {}

        with pytest.raises(ValueError, match="文档加载阶段未完成"):
            coordinator._stage_chunk(1, mock_db_session, previous_results)


# ==================== 测试类6: 分析阶段 ====================

class TestAnalysisStage:
    """测试分析阶段"""

    def test_stage_analysis_success(self, coordinator, mock_db_session, sample_documents):
        """测试分析成功"""
        # 创建mock chunks
        mock_chunk = Mock()
        mock_chunk.to_dict.return_value = {'chunk_id': 'test', 'text': 'test'}

        previous_results = {
            PipelineStage.DOCUMENT_LOAD: StageResult(
                stage=PipelineStage.DOCUMENT_LOAD,
                success=True,
                duration_seconds=1.0,
                output={'documents': sample_documents}
            ),
            PipelineStage.CHUNK: StageResult(
                stage=PipelineStage.CHUNK,
                success=True,
                duration_seconds=1.0,
                output={'chunks': [mock_chunk, mock_chunk], 'chunk_count': 2}
            )
        }

        with patch.object(coordinator, '_get_analysis_agent') as mock_get:
            mock_agent = Mock()
            # Mock VectorizationResult
            mock_result = Mock()
            mock_result.success_count = 2
            mock_result.failed_count = 0
            mock_result.embedding_model = 'bge-large-zh'
            mock_result.embedding_dim = 1024
            mock_agent.vectorize_chunks.return_value = mock_result
            mock_get.return_value = mock_agent

            output = coordinator._stage_analysis(1, mock_db_session, previous_results)

            assert output['vectorized_count'] == 2
            assert output['failed_count'] == 0
            assert output['embedding_model'] == 'bge-large-zh'


# ==================== 测试类7: 知识图谱阶段 ====================

class TestKnowledgeStage:
    """测试知识图谱阶段"""

    def test_stage_knowledge_success(self, coordinator, mock_db_session):
        """测试知识图谱构建成功"""
        with patch.object(coordinator, '_get_knowledge_agent') as mock_get:
            mock_agent = Mock()
            mock_agent.build_knowledge_graph.return_value = {
                'entity_count': 50,
                'relation_count': 120
            }
            mock_get.return_value = mock_agent

            previous_results = {}
            output = coordinator._stage_knowledge(1, mock_db_session, previous_results)

            assert output['entity_count'] == 50
            assert output['relation_count'] == 120


# ==================== 测试类8: 综合阶段 ====================

class TestSynthesisStage:
    """测试综合阶段"""

    def test_stage_synthesis_success(self, coordinator, mock_db_session):
        """测试综合合成成功"""
        with patch.object(coordinator, '_get_synthesis_agent') as mock_get:
            mock_result = Mock()
            mock_result.memory_fragments = [Mock(), Mock()]
            mock_result.citations = [Mock()]
            mock_result.context_summary = "综合摘要"

            mock_agent = Mock()
            mock_agent.prepare_synthesis_context.return_value = mock_result
            mock_get.return_value = mock_agent

            previous_results = {}
            output = coordinator._stage_synthesis(1, mock_db_session, previous_results)

            assert output['memory_count'] == 2
            assert output['citation_count'] == 1
            assert output['context_summary'] == "综合摘要"


# ==================== 测试类9: 报告阶段 ====================

class TestReportStage:
    """测试报告生成阶段"""

    def test_stage_report_success(self, coordinator, mock_db_session):
        """测试报告生成成功"""
        with patch.object(coordinator, '_get_report_agent') as mock_get:
            mock_result = Mock()
            mock_result.success = True
            mock_result.report_title = "项目1分析报告"
            mock_result.sections = [Mock(), Mock()]
            mock_result.metadata = Mock(validation_passed=True)
            mock_result.export_formats = {'markdown': 'content', 'json': 'content'}

            mock_agent = Mock()
            mock_agent.generate_report.return_value = mock_result
            mock_get.return_value = mock_agent

            previous_results = {}
            output = coordinator._stage_report(1, mock_db_session, previous_results, 'dynamic')

            assert output['success'] is True
            assert output['report_title'] == "项目1分析报告"
            assert output['section_count'] == 2
            assert output['validation_passed'] is True


# ==================== 测试类10: 阶段执行 ====================

class TestStageExecution:
    """测试单个阶段执行"""

    def test_execute_stage_success(self, coordinator, mock_db_session, sample_documents):
        """测试阶段执行成功"""
        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.return_value = sample_documents

            result = coordinator._execute_stage(
                stage=PipelineStage.DOCUMENT_LOAD,
                project_id=1,
                db_session=mock_db_session,
                previous_results={},
                report_level=None
            )

            assert result.success is True
            assert result.stage == PipelineStage.DOCUMENT_LOAD
            assert result.duration_seconds > 0
            assert 'document_count' in result.output

    def test_execute_stage_failure(self, coordinator, mock_db_session):
        """测试阶段执行失败"""
        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.side_effect = Exception("数据库错误")

            result = coordinator._execute_stage(
                stage=PipelineStage.DOCUMENT_LOAD,
                project_id=1,
                db_session=mock_db_session,
                previous_results={},
                report_level=None
            )

            assert result.success is False
            assert len(result.errors) > 0
            assert "数据库错误" in result.errors[0]


# ==================== 测试类11: 重试机制 ====================

class TestRetryMechanism:
    """测试重试机制"""

    def test_retry_stage_success_on_second_attempt(self, coordinator, mock_db_session, sample_documents):
        """测试第二次重试成功"""
        call_count = [0]

        def mock_execute(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return StageResult(
                    stage=PipelineStage.DOCUMENT_LOAD,
                    success=False,
                    duration_seconds=1.0,
                    output={},
                    errors=["第一次失败"]
                )
            else:
                return StageResult(
                    stage=PipelineStage.DOCUMENT_LOAD,
                    success=True,
                    duration_seconds=1.0,
                    output={'document_count': 2}
                )

        with patch.object(coordinator, '_execute_stage', side_effect=mock_execute):
            previous_results = {}
            success = coordinator._retry_stage(
                stage=PipelineStage.DOCUMENT_LOAD,
                project_id=1,
                db_session=mock_db_session,
                previous_results=previous_results,
                report_level=None
            )

            assert success is True
            assert call_count[0] == 2

    def test_retry_stage_all_attempts_fail(self, coordinator, mock_db_session):
        """测试所有重试都失败"""
        with patch.object(coordinator, '_execute_stage') as mock_execute:
            mock_execute.return_value = StageResult(
                stage=PipelineStage.DOCUMENT_LOAD,
                success=False,
                duration_seconds=1.0,
                output={},
                errors=["持续失败"]
            )

            previous_results = {}
            success = coordinator._retry_stage(
                stage=PipelineStage.DOCUMENT_LOAD,
                project_id=1,
                db_session=mock_db_session,
                previous_results=previous_results,
                report_level=None
            )

            assert success is False
            assert mock_execute.call_count == 3  # max_retries


# ==================== 测试类12: 完整流水线 ====================

class TestFullPipeline:
    """测试完整流水线执行"""

    @patch('app.models.project.ProjectDocument')
    def test_process_project_full_mode(self, MockDoc, coordinator, mock_db_session, sample_documents):
        """测试完整模式流水线"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_documents

        # Mock所有Agent
        with patch.object(coordinator, '_get_chunk_agent') as mock_chunk, \
             patch.object(coordinator, '_get_analysis_agent') as mock_analysis, \
             patch.object(coordinator, '_get_knowledge_agent') as mock_knowledge, \
             patch.object(coordinator, '_get_synthesis_agent') as mock_synthesis, \
             patch.object(coordinator, '_get_report_agent') as mock_report:

            # 配置mock返回值
            mock_chunk.return_value.chunk_document.return_value = [Mock(), Mock()]
            mock_analysis.return_value.analyze_document.return_value = {'success': True}
            mock_knowledge.return_value.build_knowledge_graph.return_value = {'entity_count': 10}

            mock_synthesis_result = Mock()
            mock_synthesis_result.memory_fragments = []
            mock_synthesis_result.citations = []
            mock_synthesis_result.context_summary = "摘要"
            mock_synthesis.return_value.prepare_synthesis_context.return_value = mock_synthesis_result

            mock_report_result = Mock()
            mock_report_result.success = True
            mock_report_result.report_title = "报告"
            mock_report_result.sections = []
            mock_report_result.metadata = Mock(validation_passed=True)
            mock_report_result.export_formats = {}
            mock_report.return_value.generate_report.return_value = mock_report_result

            result = coordinator.process_project(
                project_id=1,
                db_session=mock_db_session,
                mode=PipelineMode.FULL
            )

            assert result.success is True
            assert len(result.completed_stages) == 6
            assert result.project_id == 1
            assert result.total_duration_seconds > 0

    def test_process_project_quick_mode(self, coordinator, mock_db_session, sample_documents):
        """测试快速模式（跳过知识图谱）"""
        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.return_value = sample_documents

            with patch.object(coordinator, '_execute_stage') as mock_execute:
                mock_execute.return_value = StageResult(
                    stage=PipelineStage.DOCUMENT_LOAD,
                    success=True,
                    duration_seconds=1.0,
                    output={}
                )

                result = coordinator.process_project(
                    project_id=1,
                    db_session=mock_db_session,
                    mode=PipelineMode.QUICK
                )

                # 快速模式应该执行5个阶段
                assert len(result.completed_stages) == 5
                assert PipelineStage.KNOWLEDGE not in result.completed_stages


# ==================== 测试类13: 断点续传 ====================

class TestCheckpoint:
    """测试断点续传"""

    def test_start_from_specific_stage(self, coordinator, mock_db_session, sample_documents):
        """测试从指定阶段开始"""
        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.return_value = sample_documents

            with patch.object(coordinator, '_execute_stage') as mock_execute:
                mock_execute.return_value = StageResult(
                    stage=PipelineStage.REPORT,
                    success=True,
                    duration_seconds=1.0,
                    output={}
                )

                result = coordinator.process_project(
                    project_id=1,
                    db_session=mock_db_session,
                    mode=PipelineMode.FULL,
                    start_from_stage=PipelineStage.REPORT
                )

                # 应该只执行REPORT阶段
                assert len(result.completed_stages) == 1
                assert result.completed_stages[0] == PipelineStage.REPORT


# ==================== 测试类14: 流水线状态 ====================

class TestPipelineStatus:
    """测试流水线状态查询"""

    @patch('app.models.project.ProjectDocument')
    def test_get_pipeline_status(self, MockDoc, coordinator, mock_db_session, sample_documents):
        """测试获取流水线状态"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = sample_documents

        status = coordinator.get_pipeline_status(1, mock_db_session)

        assert status['project_id'] == 1
        assert status['document_count'] == 2
        assert status['stages']['document_load'] is True
        assert status['stages']['chunk'] is True
        assert status['stages']['analysis'] is True
        assert status['can_skip_to_report'] is True


# ==================== 测试类15: 边缘情况 ====================

class TestEdgeCases:
    """测试边缘情况"""

    def test_process_empty_project(self, coordinator, mock_db_session):
        """测试处理空项目"""
        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.return_value = []

            result = coordinator.process_project(
                project_id=1,
                db_session=mock_db_session,
                mode=PipelineMode.REPORT_ONLY
            )

            # 应该能完成但可能有警告
            assert result.project_id == 1

    def test_retry_disabled(self, mock_db_session):
        """测试禁用重试"""
        coord = AgentCoordinator(enable_retry=False)

        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.side_effect = Exception("错误")

            result = coord.process_project(
                project_id=1,
                db_session=mock_db_session
            )

            # 不重试，应该直接失败
            assert result.success is False

    def test_custom_stages_with_wrong_mode(self, coordinator):
        """测试自定义阶段但模式不是CUSTOM"""
        custom = [PipelineStage.DOCUMENT_LOAD]

        # 应该忽略custom_stages因为mode不是CUSTOM
        stages = coordinator._determine_stages(PipelineMode.FULL, custom)

        assert len(stages) == 6  # 使用FULL模式的阶段
