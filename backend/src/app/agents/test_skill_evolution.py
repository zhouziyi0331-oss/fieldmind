"""
测试Skill Evolution Service和Integration
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.skill_evolution_service import SkillEvolutionService, get_skill_evolution_service
from app.agents.skill_evolution_integration import SkillEvolutionIntegration, get_skill_evolution_integration
from app.models.skill_version import SkillVersion
from app.models.skill import Skill


@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def evolution_service():
    """创建SkillEvolutionService实例"""
    return SkillEvolutionService()


@pytest.fixture
def evolution_integration():
    """创建SkillEvolutionIntegration实例"""
    return SkillEvolutionIntegration()


@pytest.fixture
def sample_skill_version():
    """示例技能版本"""
    return SkillVersion(
        id=1,
        skill_id=100,
        project_id=1,
        user_id=1,
        version_number=1,
        version_tag="initial",
        skill_name="test_skill",
        skill_content="def test(): pass",
        skill_type="nlp",
        change_type="created",
        change_description="Initial creation",
        change_summary="首次创建",
        usage_count=10,
        success_count=8,
        failure_count=2,
        avg_execution_time=1.5,
        is_active=True,
        is_deprecated=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestSkillEvolutionService:
    """测试SkillEvolutionService"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        service1 = get_skill_evolution_service()
        service2 = get_skill_evolution_service()
        assert service1 is service2

    def test_create_initial_version(self, evolution_service, mock_db_session):
        """测试创建初始版本"""
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()
        mock_db_session.add = Mock()

        version = evolution_service.create_initial_version(
            db=mock_db_session,
            skill_id=100,
            project_id=1,
            skill_name="test_skill",
            skill_content="def test(): pass",
            skill_type="nlp",
            user_id=1,
        )

        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert version.version_number == 1
        assert version.change_type == "created"

    def test_record_adjustment(self, evolution_service, mock_db_session, sample_skill_version):
        """测试记录调整"""
        # Mock获取最新版本
        with patch.object(evolution_service, '_get_latest_version', return_value=sample_skill_version):
            mock_db_session.add = Mock()
            mock_db_session.commit = Mock()
            mock_db_session.refresh = Mock()

            new_version = evolution_service.record_adjustment(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
                new_skill_content="def test(): return True",
                adjustment_description="Added return value",
                user_id=1,
            )

            assert mock_db_session.add.called
            assert mock_db_session.commit.called
            # 检查旧版本被标记为非活跃
            assert not sample_skill_version.is_active

    def test_record_optimization(self, evolution_service, mock_db_session, sample_skill_version):
        """测试记录优化"""
        with patch.object(evolution_service, '_get_latest_version', return_value=sample_skill_version):
            mock_db_session.add = Mock()
            mock_db_session.commit = Mock()
            mock_db_session.refresh = Mock()

            new_version = evolution_service.record_optimization(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
                optimized_content="def test(): return True  # optimized",
                optimization_reason="Improved performance",
                optimization_metrics={"speed_improvement": 0.2},
            )

            assert mock_db_session.add.called
            assert mock_db_session.commit.called

    def test_record_usage(self, evolution_service, mock_db_session, sample_skill_version):
        """测试记录使用统计"""
        with patch.object(evolution_service, '_get_active_version', return_value=sample_skill_version):
            mock_db_session.commit = Mock()

            initial_usage = sample_skill_version.usage_count
            evolution_service.record_usage(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
                success=True,
                execution_time=2.0,
            )

            assert sample_skill_version.usage_count == initial_usage + 1
            assert sample_skill_version.success_count == 9
            assert mock_db_session.commit.called

    def test_generate_optimization_suggestions_low_success_rate(
        self, evolution_service, mock_db_session, sample_skill_version
    ):
        """测试生成优化建议 - 低成功率"""
        # 设置低成功率
        sample_skill_version.success_count = 3
        sample_skill_version.failure_count = 7

        with patch.object(evolution_service, '_get_active_version', return_value=sample_skill_version):
            suggestions = evolution_service.generate_optimization_suggestions(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
            )

            assert len(suggestions) > 0
            # 应该有低成功率警告
            low_success_suggestions = [s for s in suggestions if s['type'] == 'low_success_rate']
            assert len(low_success_suggestions) > 0
            assert low_success_suggestions[0]['severity'] == 'high'

    def test_generate_optimization_suggestions_high_execution_time(
        self, evolution_service, mock_db_session, sample_skill_version
    ):
        """测试生成优化建议 - 高执行时间"""
        sample_skill_version.avg_execution_time = 10.0

        with patch.object(evolution_service, '_get_active_version', return_value=sample_skill_version):
            suggestions = evolution_service.generate_optimization_suggestions(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
            )

            perf_suggestions = [s for s in suggestions if s['type'] == 'high_execution_time']
            assert len(perf_suggestions) > 0

    def test_deprecate_version(self, evolution_service, mock_db_session, sample_skill_version):
        """测试弃用版本"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_skill_version
        mock_db_session.query.return_value = mock_query
        mock_db_session.commit = Mock()

        evolution_service.deprecate_version(
            db=mock_db_session,
            version_id=1,
            reason="Outdated implementation"
        )

        assert sample_skill_version.is_deprecated
        assert not sample_skill_version.is_active
        assert sample_skill_version.deprecated_at is not None
        assert mock_db_session.commit.called

    def test_rollback_to_version(self, evolution_service, mock_db_session, sample_skill_version):
        """测试回滚到指定版本"""
        # 创建一个新版本作为当前版本
        current_version = SkillVersion(
            id=2,
            skill_id=100,
            project_id=1,
            version_number=2,
            skill_name="test_skill",
            skill_content="def test(): return False",
            change_type="updated",
            is_active=True,
        )

        with patch.object(evolution_service, 'get_version_by_number', return_value=sample_skill_version), \
             patch.object(evolution_service, '_get_latest_version', return_value=current_version):
            mock_db_session.add = Mock()
            mock_db_session.commit = Mock()
            mock_db_session.refresh = Mock()

            rollback_version = evolution_service.rollback_to_version(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
                target_version_number=1,
            )

            assert mock_db_session.add.called
            assert rollback_version.version_number == 3  # 新版本号
            assert rollback_version.skill_content == sample_skill_version.skill_content
            assert not current_version.is_active


class TestSkillEvolutionIntegration:
    """测试SkillEvolutionIntegration"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        integration1 = get_skill_evolution_integration()
        integration2 = get_skill_evolution_integration()
        assert integration1 is integration2

    @pytest.mark.asyncio
    async def test_track_skill_execution(
        self, evolution_integration, mock_db_session
    ):
        """测试追踪Skill执行"""
        with patch.object(
            evolution_integration.evolution_service,
            'record_usage',
            return_value=None
        ) as mock_record:
            execution_result = {
                "success": True,
                "execution_time": 1.5,
                "output": "test output"
            }

            await evolution_integration.track_skill_execution(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
                execution_result=execution_result,
            )

            mock_record.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_detect_skill_changes_no_change(
        self, evolution_integration, mock_db_session, sample_skill_version
    ):
        """测试自动检测Skill变更 - 无变更"""
        with patch.object(
            evolution_integration.evolution_service,
            'get_active_version',
            return_value=sample_skill_version
        ):
            result = await evolution_integration.auto_detect_skill_changes(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
                current_content=sample_skill_version.skill_content,  # 相同内容
            )

            assert result is None  # 无变更

    @pytest.mark.asyncio
    async def test_auto_detect_skill_changes_with_change(
        self, evolution_integration, mock_db_session, sample_skill_version
    ):
        """测试自动检测Skill变更 - 有变更"""
        new_version = SkillVersion(
            id=2,
            skill_id=100,
            project_id=1,
            version_number=2,
            skill_name="test_skill",
            skill_content="def test(): return True",
            change_type="adjusted",
        )

        with patch.object(
            evolution_integration.evolution_service,
            'get_active_version',
            return_value=sample_skill_version
        ), patch.object(
            evolution_integration.evolution_service,
            'record_adjustment',
            return_value=new_version
        ):
            result = await evolution_integration.auto_detect_skill_changes(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
                current_content="def test(): return True",  # 不同内容
                change_context={"user_id": 1, "change_reason": "Test change"},
            )

            assert result is not None
            assert result["version_number"] == 2

    @pytest.mark.asyncio
    async def test_get_skill_evolution_summary(
        self, evolution_integration, mock_db_session, sample_skill_version
    ):
        """测试获取技能演化摘要"""
        history = [sample_skill_version]
        suggestions = [
            {
                "type": "low_success_rate",
                "severity": "high",
                "message": "成功率较低"
            }
        ]

        with patch.object(
            evolution_integration.evolution_service,
            'get_version_history',
            return_value=history
        ), patch.object(
            evolution_integration.evolution_service,
            'get_active_version',
            return_value=sample_skill_version
        ), patch.object(
            evolution_integration.evolution_service,
            'generate_optimization_suggestions',
            return_value=suggestions
        ):
            summary = await evolution_integration.get_skill_evolution_summary(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
            )

            assert summary['skill_id'] == 100
            assert summary['project_id'] == 1
            assert summary['total_versions'] == 1
            assert summary['active_version'] is not None
            assert len(summary['optimization_suggestions']) == 1

    @pytest.mark.asyncio
    async def test_suggest_skill_optimization(
        self, evolution_integration, mock_db_session
    ):
        """测试建议Skill优化"""
        suggestions = [
            {
                "type": "low_success_rate",
                "severity": "high",
                "message": "成功率较低",
                "current_value": 0.5,
            }
        ]

        with patch.object(
            evolution_integration.evolution_service,
            'generate_optimization_suggestions',
            return_value=suggestions
        ):
            enhanced_suggestions = await evolution_integration.suggest_skill_optimization(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
            )

            assert len(enhanced_suggestions) > 0
            # 应该有增强的推荐行动
            assert 'recommended_actions' in enhanced_suggestions[0]

    @pytest.mark.asyncio
    async def test_export_skill_evolution_to_cognee(
        self, evolution_integration, mock_db_session, sample_skill_version
    ):
        """测试导出Skill演化历史到Cognee"""
        history = [sample_skill_version]

        with patch.object(
            evolution_integration.evolution_service,
            'get_version_history',
            return_value=history
        ):
            result = await evolution_integration.export_skill_evolution_to_cognee(
                db=mock_db_session,
                skill_id=100,
                project_id=1,
            )

            assert result['success']
            assert result['skill_id'] == 100
            assert result['entries_count'] > 0
            assert 'knowledge_entries' in result


class TestSkillVersionModel:
    """测试SkillVersion模型"""

    def test_skill_version_creation(self):
        """测试创建SkillVersion对象"""
        version = SkillVersion(
            skill_id=100,
            project_id=1,
            version_number=1,
            skill_name="test",
            skill_content="test content",
            change_type="created",
        )

        assert version.skill_id == 100
        assert version.version_number == 1
        assert version.change_type == "created"

    def test_success_rate_property(self):
        """测试成功率计算"""
        version = SkillVersion(
            skill_id=100,
            project_id=1,
            version_number=1,
            skill_name="test",
            skill_content="test",
            change_type="created",
            success_count=8,
            failure_count=2,
        )

        assert version.success_rate == 0.8

    def test_success_rate_no_usage(self):
        """测试无使用记录时的成功率"""
        version = SkillVersion(
            skill_id=100,
            project_id=1,
            version_number=1,
            skill_name="test",
            skill_content="test",
            change_type="created",
            success_count=0,
            failure_count=0,
        )

        assert version.success_rate is None

    def test_version_label_property(self):
        """测试版本标签"""
        version1 = SkillVersion(
            skill_id=100,
            project_id=1,
            version_number=1,
            skill_name="test",
            skill_content="test",
            change_type="created",
        )
        assert version1.version_label == "v1"

        version2 = SkillVersion(
            skill_id=100,
            project_id=1,
            version_number=2,
            version_tag="beta",
            skill_name="test",
            skill_content="test",
            change_type="created",
        )
        assert version2.version_label == "v2 (beta)"

    def test_to_dict(self):
        """测试转换为字典"""
        version = SkillVersion(
            skill_id=100,
            project_id=1,
            version_number=1,
            skill_name="test",
            skill_content="test content",
            change_type="created",
            usage_count=10,
            success_count=8,
            failure_count=2,
        )

        version_dict = version.to_dict()

        assert version_dict['skill_id'] == 100
        assert version_dict['version_number'] == 1
        assert version_dict['usage_count'] == 10
        assert 'skill_content' in version_dict
