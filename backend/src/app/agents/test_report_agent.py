"""
ReportAgent 测试套件

测试Agent 6的报告生成能力
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from enum import Enum

from app.agents.report_agent import (
    ReportAgent,
    ReportLevel,
    ReportFormat,
    ReportStrategy,
    ReportMetadata,
    ReportSection,
    ReportResult
)


# ==================== Fixtures ====================

@pytest.fixture
def report_agent():
    """创建ReportAgent实例"""
    return ReportAgent(
        default_level=ReportLevel.DYNAMIC,
        default_strategy=ReportStrategy.AUTO,
        enable_anti_hallucination=True,
        enable_citation_check=True
    )


@pytest.fixture
def mock_db_session():
    """Mock数据库会话"""
    session = Mock()
    return session


@pytest.fixture
def sample_dynamic_report():
    """示例动态报告数据"""
    return {
        'title': '2020-2023年乡村振兴分析报告',
        'generated_at': '2026-08-13T10:00:00',
        'outline': [
            {'chapter': '1. 概述', 'type': 'overview'},
            {'chapter': '2. 产业发展', 'type': 'dimension'}
        ],
        'sections': [
            {
                'chapter': '1. 概述',
                'content': {
                    'text': '本报告基于10份文档分析',
                    'stats': {'document_count': 10}
                }
            },
            {
                'chapter': '2. 产业发展',
                'content': {
                    'text': '产业发展维度共出现45次',
                    'keywords': ['农业', '产业', '发展']
                }
            }
        ],
        'metadata': {
            'project_id': 1,
            'document_count': 10,
            'generation_mode': 'dynamic'
        }
    }


@pytest.fixture
def sample_llm_report():
    """示例LLM报告"""
    return """# 项目1一度分析报告

## 1. 材料来源与基本情况

本研究基于3份田野调查材料，涉及乡村振兴主题。

## 2. 核心关键词深度分析

**产业发展**：在材料中出现23次，是最核心的议题。"发展特色产业是关键"（来源：doc1.pdf P5）

## 3. 研究发现总结

通过材料分析，发现产业发展是核心议题。
"""


@pytest.fixture
def sample_facts_data():
    """示例facts数据"""
    return {
        'project_id': 1,
        'total_docs': 5,
        'total_chunks': 120,
        'total_words': 15000,
        'category_rank': [
            {'name': '产业发展', 'count': 45, 'percentage': 35.0}
        ],
        'top_speakers': [
            {'name': '张书记', 'count': 20}
        ],
        'evidence_samples': [
            {
                'text': '产业振兴是关键',
                'source': 'doc1.pdf',
                'timestamp': 10.5
            }
        ],
        'generated_at': '2026-08-13T10:00:00'
    }


# ==================== 测试类1: 初始化 ====================

class TestReportAgentInitialization:
    """测试ReportAgent初始化"""

    def test_default_initialization(self):
        """测试默认初始化"""
        agent = ReportAgent()

        assert agent.default_level == ReportLevel.DYNAMIC
        assert agent.default_strategy == ReportStrategy.AUTO
        assert agent.enable_anti_hallucination is True
        assert agent.enable_citation_check is True
        assert agent.max_report_length == 50000

    def test_custom_initialization(self):
        """测试自定义初始化"""
        agent = ReportAgent(
            default_level=ReportLevel.LEVEL_1,
            default_strategy=ReportStrategy.DATA_DRIVEN,
            enable_anti_hallucination=False,
            max_report_length=100000
        )

        assert agent.default_level == ReportLevel.LEVEL_1
        assert agent.default_strategy == ReportStrategy.DATA_DRIVEN
        assert agent.enable_anti_hallucination is False
        assert agent.max_report_length == 100000

    def test_services_lazy_loading(self, report_agent):
        """测试服务懒加载"""
        # 初始时服务未加载
        assert report_agent._dynamic_generator is None
        assert report_agent._llm_generator is None
        assert report_agent._anti_hallucination_generator is None


# ==================== 测试类2: 策略选择 ====================

class TestStrategySelection:
    """测试策略自动选择"""

    @patch('app.models.project.ProjectDocument')
    def test_select_data_driven_strategy(self, MockDoc, report_agent, mock_db_session):
        """测试选择数据驱动策略"""
        # Mock文档有data_profile
        mock_docs = [Mock(data_profile={'discovered_dimensions': []})]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_docs

        with patch.object(report_agent, '_get_llm_generator') as mock_llm:
            mock_llm.return_value.is_available.return_value = False

            strategy = report_agent._select_strategy(1, ReportLevel.DYNAMIC, mock_db_session)

            assert strategy == ReportStrategy.DATA_DRIVEN

    def test_select_comprehensive_strategy(self, report_agent, mock_db_session):
        """测试选择综合策略"""
        # Mock多个文档 + LLM可用
        mock_docs = [
            Mock(data_profile={'discovered_dimensions': [{'name': 'test'}]})
            for _ in range(5)
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_docs

        with patch.object(report_agent, '_get_llm_generator') as mock_llm:
            mock_llm.return_value.is_available.return_value = True

            strategy = report_agent._select_strategy(1, ReportLevel.LEVEL_2, mock_db_session)

            assert strategy == ReportStrategy.COMPREHENSIVE


# ==================== 测试类3: 服务加载 ====================

class TestServiceLoading:
    """测试各个报告服务的加载"""

    @patch('app.services.dynamic_report_generator.DynamicReportGenerator')
    def test_load_dynamic_generator(self, MockGenerator, report_agent, mock_db_session):
        """测试加载动态报告生成器"""
        generator = report_agent._get_dynamic_generator(mock_db_session)

        MockGenerator.assert_called_once_with(db=mock_db_session)
        assert generator is not None

    @patch('app.services.llm_report_generator.LLMReportGenerator')
    def test_load_llm_generator(self, MockGenerator, report_agent):
        """测试加载LLM报告生成器"""
        generator = report_agent._get_llm_generator()

        MockGenerator.assert_called_once()
        assert generator is not None

    @patch('app.services.anti_hallucination_report.AntiHallucinationReportGenerator')
    def test_load_anti_hallucination_generator(self, MockGenerator, report_agent):
        """测试加载反幻觉报告生成器"""
        generator = report_agent._get_anti_hallucination_generator()

        MockGenerator.assert_called_once()
        assert generator is not None


# ==================== 测试类4: 动态报告生成 ====================

class TestDynamicReportGeneration:
    """测试动态报告生成"""

    def test_generate_dynamic_report(self, report_agent, mock_db_session, sample_dynamic_report):
        """测试生成动态报告"""
        with patch.object(report_agent, '_get_dynamic_generator') as mock_get:
            mock_generator = Mock()
            mock_generator.generate_report.return_value = sample_dynamic_report
            mock_get.return_value = mock_generator

            result = report_agent._generate_dynamic_report(1, mock_db_session, ReportStrategy.DATA_DRIVEN)

            assert result['title'] == '2020-2023年乡村振兴分析报告'
            assert result['generation_mode'] == 'dynamic'
            assert 'sections' in result
            assert len(result['sections']) == 2

    def test_sections_to_text_conversion(self, report_agent, sample_dynamic_report):
        """测试章节转文本"""
        text = report_agent._sections_to_text(sample_dynamic_report['sections'])

        assert '概述' in text
        assert '产业发展' in text
        assert '10份文档' in text


# ==================== 测试类5: LLM报告生成 ====================

class TestLLMReportGeneration:
    """测试LLM报告生成"""

    def test_generate_level1_report(self, report_agent, mock_db_session, sample_llm_report):
        """测试生成一度报告"""
        mock_docs = [Mock(text_content='content', data_profile={})]

        with patch.object(report_agent, '_get_llm_generator') as mock_get:
            mock_generator = Mock()
            mock_generator.is_available.return_value = True
            mock_generator.generate_level1_report.return_value = sample_llm_report
            mock_get.return_value = mock_generator

            with patch('app.models.project.ProjectDocument'):
                mock_db_session.query.return_value.filter.return_value.all.return_value = mock_docs

                result = report_agent._generate_llm_report(
                    1, ReportLevel.LEVEL_1, mock_db_session, ReportStrategy.THEORY_BASED
                )

                assert result['generation_mode'] == 'llm_level_1'
                assert '材料来源' in result['raw_text']

    def test_llm_unavailable_fallback(self, report_agent, mock_db_session, sample_dynamic_report):
        """测试LLM不可用时降级"""
        with patch.object(report_agent, '_get_llm_generator') as mock_llm:
            mock_llm.return_value.is_available.return_value = False

            with patch.object(report_agent, '_generate_dynamic_report') as mock_dynamic:
                mock_dynamic.return_value = sample_dynamic_report

                result = report_agent._generate_llm_report(
                    1, ReportLevel.LEVEL_1, mock_db_session, ReportStrategy.THEORY_BASED
                )

                # 应该降级到动态报告
                mock_dynamic.assert_called_once()


# ==================== 测试类6: 反幻觉报告生成 ====================

class TestAntiHallucinationReportGeneration:
    """测试反幻觉报告生成"""

    def test_generate_anti_hallucination_report(self, report_agent, mock_db_session, sample_facts_data):
        """测试生成反幻觉报告"""
        with patch.object(report_agent, '_get_anti_hallucination_generator') as mock_get:
            mock_generator = Mock()
            mock_generator.generate_report_direct.return_value = "# 数据分析报告\n本次分析5份文档"
            mock_get.return_value = mock_generator

            with patch.object(report_agent, '_build_facts_data') as mock_facts:
                mock_facts.return_value = sample_facts_data

                result = report_agent._generate_anti_hallucination_report(1, mock_db_session)

                assert result['generation_mode'] == 'anti_hallucination'
                assert '数据分析报告' in result['raw_text']
                assert 'facts' in result

    def test_build_facts_data(self, report_agent, mock_db_session):
        """测试构建facts数据"""
        mock_docs = [
            Mock(text_content='content1', chunks=[1, 2]),
            Mock(text_content='content2', chunks=[3])
        ]

        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.return_value = mock_docs

            facts = report_agent._build_facts_data(1, mock_db_session)

            assert facts['project_id'] == 1
            assert facts['total_docs'] == 2
            assert facts['total_chunks'] == 3
            assert 'generated_at' in facts


# ==================== 测试类7: 章节解析 ====================

class TestSectionParsing:
    """测试报告章节解析"""

    def test_parse_predefined_sections(self, report_agent, sample_dynamic_report):
        """测试解析预定义章节"""
        sections = report_agent._parse_report_sections(sample_dynamic_report)

        assert len(sections) == 2
        assert sections[0].title == '1. 概述'
        assert sections[0].chapter_number == 1
        assert '10份文档' in sections[0].content

    def test_parse_text_sections_with_markdown(self, report_agent):
        """测试解析Markdown格式章节"""
        text = """## 第一章

这是第一章内容。

## 第二章

这是第二章内容。
"""
        sections = report_agent._parse_text_sections(text)

        assert len(sections) == 2
        assert sections[0].title == '第一章'
        assert '第一章内容' in sections[0].content

    def test_parse_text_sections_without_markdown(self, report_agent):
        """测试解析无Markdown标记的文本"""
        text = "这是完整的报告内容，没有章节标记。"

        sections = report_agent._parse_text_sections(text)

        assert len(sections) == 1
        assert sections[0].title == '完整报告'
        assert sections[0].content == text


# ==================== 测试类8: 反幻觉验证 ====================

class TestAntiHallucinationValidation:
    """测试反幻觉验证"""

    def test_validate_report_with_facts(self, report_agent, mock_db_session, sample_facts_data):
        """测试带facts的报告验证"""
        report_data = {
            'raw_text': '本次分析5份文档，共120个片段',
            'facts': sample_facts_data
        }

        with patch('app.services.anti_hallucination_report.HallucinationDetector') as MockDetector:
            MockDetector.validate_report.return_value = (True, [])

            errors = report_agent._validate_report(report_data, 1, mock_db_session)

            assert len(errors) == 0
            MockDetector.validate_report.assert_called_once()

    def test_validate_report_disabled(self, mock_db_session):
        """测试禁用验证"""
        agent = ReportAgent(enable_anti_hallucination=False)

        errors = agent._validate_report({}, 1, mock_db_session)

        assert len(errors) == 0


# ==================== 测试类9: 引用检查 ====================

class TestCitationCheck:
    """测试引用检查"""

    def test_check_citations_with_proper_sources(self, report_agent):
        """测试带正确引用的内容"""
        sections = [
            ReportSection(
                chapter_number=1,
                title='测试',
                content='"产业发展是关键"（来源：doc1.pdf P5）'
            )
        ]

        errors = report_agent._check_citations(sections)

        assert len(errors) == 0

    def test_check_citations_missing_sources(self, report_agent):
        """测试缺少引用的内容"""
        sections = [
            ReportSection(
                chapter_number=1,
                title='测试',
                content='"产业发展是关键" 这是一个重要观点。'
            )
        ]

        errors = report_agent._check_citations(sections)

        assert len(errors) > 0
        assert '缺少来源' in errors[0]

    def test_check_citations_disabled(self):
        """测试禁用引用检查"""
        agent = ReportAgent(enable_citation_check=False)

        sections = [ReportSection(1, 'test', '"quote" without source')]
        errors = agent._check_citations(sections)

        assert len(errors) == 0


# ==================== 测试类10: 格式导出 ====================

class TestFormatExport:
    """测试格式导出"""

    def test_export_markdown(self, report_agent):
        """测试导出Markdown"""
        sections = [
            ReportSection(1, '概述', '这是概述内容'),
            ReportSection(2, '分析', '这是分析内容')
        ]
        metadata = ReportMetadata(
            project_id=1,
            report_level=ReportLevel.DYNAMIC,
            report_format=ReportFormat.MARKDOWN,
            generated_at=datetime.now(),
            document_count=10,
            total_words=5000,
            generation_strategy=ReportStrategy.DATA_DRIVEN,
            validation_passed=True
        )

        markdown = report_agent._export_markdown(sections, metadata)

        assert '# 项目1分析报告' in markdown
        assert '## 1. 概述' in markdown
        assert '## 2. 分析' in markdown
        assert '✅ 通过' in markdown

    def test_export_json(self, report_agent):
        """测试导出JSON"""
        import json

        sections = [ReportSection(1, '测试', '内容')]
        metadata = ReportMetadata(
            project_id=1,
            report_level=ReportLevel.DYNAMIC,
            report_format=ReportFormat.JSON,
            generated_at=datetime.now(),
            document_count=5,
            total_words=1000,
            generation_strategy=ReportStrategy.DATA_DRIVEN
        )

        json_str = report_agent._export_json(sections, metadata)
        data = json.loads(json_str)

        assert data['metadata']['project_id'] == 1
        assert len(data['sections']) == 1
        assert data['sections'][0]['title'] == '测试'

    def test_export_html(self, report_agent):
        """测试导出HTML"""
        sections = [ReportSection(1, '测试', '内容')]
        metadata = ReportMetadata(
            project_id=1,
            report_level=ReportLevel.DYNAMIC,
            report_format=ReportFormat.HTML,
            generated_at=datetime.now(),
            document_count=5,
            total_words=1000,
            generation_strategy=ReportStrategy.DATA_DRIVEN
        )

        html = report_agent._export_html(sections, metadata)

        assert '<!DOCTYPE html>' in html
        assert '<h1>项目1分析报告</h1>' in html
        assert '<h2>1. 测试</h2>' in html


# ==================== 测试类11: 元数据构建 ====================

class TestMetadataBuilding:
    """测试元数据构建"""

    def test_build_metadata_complete(self, report_agent, mock_db_session):
        """测试构建完整元数据"""
        report_data = {
            'raw_text': '报告内容[来源：doc1.pdf]',
            'metadata': {'data_profile': True},
            'generation_mode': 'llm_level_1'
        }

        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.count.return_value = 10

            metadata = report_agent._build_metadata(
                project_id=1,
                report_level=ReportLevel.LEVEL_1,
                strategy=ReportStrategy.COMPREHENSIVE,
                report_data=report_data,
                validation_passed=True,
                db_session=mock_db_session
            )

            assert metadata.project_id == 1
            assert metadata.document_count == 10
            assert metadata.has_citations is True
            assert metadata.has_llm_generation is True
            assert metadata.validation_passed is True


# ==================== 测试类12: 集成测试 ====================

class TestReportAgentIntegration:
    """测试完整报告生成流程"""

    @patch('app.services.dynamic_report_generator.DynamicReportGenerator')
    @patch('app.models.project.ProjectDocument')
    def test_generate_report_success(
        self,
        MockDoc,
        MockGenerator,
        report_agent,
        mock_db_session,
        sample_dynamic_report
    ):
        """测试完整报告生成成功"""
        # Mock生成器
        mock_gen = Mock()
        mock_gen.generate_report.return_value = sample_dynamic_report
        MockGenerator.return_value = mock_gen

        # Mock文档查询
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        mock_db_session.query.return_value.filter.return_value.count.return_value = 10

        result = report_agent.generate_report(
            project_id=1,
            db_session=mock_db_session,
            report_level=ReportLevel.DYNAMIC,
            strategy=ReportStrategy.DATA_DRIVEN
        )

        assert result.success is True
        assert result.report_title == '2020-2023年乡村振兴分析报告'
        assert len(result.sections) == 2
        assert ReportFormat.MARKDOWN in result.export_formats

    def test_generate_report_failure_handling(self, report_agent, mock_db_session):
        """测试报告生成失败处理"""
        # Mock文档查询返回空列表
        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.return_value = []
            mock_db_session.query.return_value.filter.return_value.count.return_value = 0

            with patch.object(report_agent, '_generate_dynamic_report') as mock_gen:
                mock_gen.side_effect = Exception("生成失败")

                result = report_agent.generate_report(
                    project_id=1,
                    db_session=mock_db_session
                )

                assert result.success is False
                assert len(result.validation_errors) > 0
                assert '生成失败' in result.validation_errors[0]


# ==================== 测试类13: 边缘情况 ====================

class TestEdgeCases:
    """测试边缘情况"""

    def test_empty_project(self, report_agent, mock_db_session):
        """测试空项目"""
        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.return_value = []
            mock_db_session.query.return_value.filter.return_value.count.return_value = 0

            strategy = report_agent._select_strategy(1, ReportLevel.DYNAMIC, mock_db_session)

            assert strategy == ReportStrategy.DATA_DRIVEN

    def test_invalid_report_level(self, report_agent, mock_db_session):
        """测试无效的报告等级"""
        # Mock文档查询
        with patch('app.models.project.ProjectDocument'):
            mock_db_session.query.return_value.filter.return_value.all.return_value = []
            mock_db_session.query.return_value.filter.return_value.count.return_value = 0

            class InvalidLevel(str, Enum):
                INVALID = "invalid"

            # 无效等级会被捕获并返回失败结果
            result = report_agent.generate_report(
                project_id=1,
                db_session=mock_db_session,
                report_level=InvalidLevel.INVALID
            )

            # 应该返回失败结果而不是抛出异常
            assert result.success is False
            assert '不支持的报告等级' in result.validation_errors[0]

    def test_extract_keywords_from_empty_docs(self, report_agent):
        """测试从空文档提取关键词"""
        keywords = report_agent._extract_keywords_from_docs([])

        assert keywords == []

    def test_prepare_skill_results_from_empty_docs(self, report_agent):
        """测试从空文档准备skill结果"""
        results = report_agent._prepare_skill_results([])

        assert results == {}
