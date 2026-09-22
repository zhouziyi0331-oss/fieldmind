"""
Hermes 治理框架集成测试

测试 GovernedHermes 的企业治理能力：
- 审计日志自动记录
- 数据血缘自动追踪
- 权限控制
- 阶段执行
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from sqlalchemy.orm import Session

from app.core.hermes_governance import (
    GovernedHermes,
    get_governed_hermes,
    governed_stage
)
from app.models.permission import PermissionAction, ResourceType
from app.core.hermes import DataQualityLevel, StageStatus


# ==================== 测试夹具 ====================

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def governed_hermes():
    """获取 GovernedHermes 实例"""
    return GovernedHermes()


@pytest.fixture
def sample_data():
    """测试数据"""
    return {
        "document_id": "doc_123",
        "text": "这是测试文档内容",
        "metadata": {"author": "test_user"}
    }


# ==================== 基础功能测试 ====================

def test_governed_hermes_initialization(governed_hermes):
    """测试 GovernedHermes 初始化"""
    assert governed_hermes is not None
    assert governed_hermes.enable_audit is True
    assert governed_hermes.enable_lineage is True
    assert governed_hermes.enable_permission_check is True


def test_configure_governance(governed_hermes):
    """测试治理配置"""
    # 修改配置
    governed_hermes.configure_governance(
        enable_audit=False,
        enable_lineage=False,
        enable_permission_check=False
    )

    assert governed_hermes.enable_audit is False
    assert governed_hermes.enable_lineage is False
    assert governed_hermes.enable_permission_check is False

    # 恢复默认配置
    governed_hermes.configure_governance(
        enable_audit=True,
        enable_lineage=True,
        enable_permission_check=True
    )


# ==================== 阶段注册测试 ====================

@pytest.mark.asyncio
async def test_register_governed_stage(governed_hermes):
    """测试治理化阶段注册"""

    async def test_handler(data: Dict, project_id: int, db: Session):
        return {"status": "processed", **data}

    # 注册阶段
    governed_hermes.register_governed_stage(
        name="test_stage",
        handler=test_handler,
        require_permission=PermissionAction.EDIT,
        resource_type=ResourceType.DOCUMENT
    )

    # 验证阶段已注册
    stage = governed_hermes.get_stage("test_stage")
    assert stage is not None
    assert stage.name == "test_stage"


@pytest.mark.asyncio
async def test_governed_stage_decorator(governed_hermes):
    """测试 @governed_stage 装饰器"""

    @governed_stage(
        stage_name="decorated_test_stage",
        require_permission=PermissionAction.VIEW,
        resource_type=ResourceType.PROJECT
    )
    async def decorated_handler(data: Dict, project_id: int, db: Session):
        return {"decorated": True, **data}

    # 验证阶段已注册
    stage = governed_hermes.get_stage("decorated_test_stage")
    assert stage is not None


# ==================== 权限检查测试 ====================

@pytest.mark.asyncio
async def test_permission_check_success(governed_hermes, mock_db):
    """测试权限检查 - 成功"""

    with patch('app.services.permission_service.PermissionService') as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.check_permission = AsyncMock(return_value=True)

        # 权限检查应该通过
        await governed_hermes._check_permission(
            user_id=123,
            action=PermissionAction.VIEW,
            resource_type=ResourceType.DOCUMENT,
            resource_id="doc_123",
            db=mock_db
        )


@pytest.mark.asyncio
async def test_permission_check_failure(governed_hermes, mock_db):
    """测试权限检查 - 失败"""

    with patch('app.services.permission_service.PermissionService') as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.check_permission = AsyncMock(return_value=False)

        # 权限检查应该抛出异常
        with pytest.raises(PermissionError):
            await governed_hermes._check_permission(
                user_id=123,
                action=PermissionAction.EDIT,
                resource_type=ResourceType.DOCUMENT,
                resource_id="doc_123",
                db=mock_db
            )


# ==================== 审计日志测试 ====================

@pytest.mark.asyncio
async def test_audit_logging(governed_hermes, mock_db):
    """测试审计日志记录"""

    with patch('app.services.audit_service.AuditService.create_log') as mock_create_log:
        mock_create_log.return_value = AsyncMock()

        await governed_hermes._record_audit(
            db=mock_db,
            stage_name="test_stage",
            project_id=1,
            user_id=123,
            result={"status": "success"},
            error=None,
            duration_ms=100
        )

        # 验证审计日志被创建
        mock_create_log.assert_called_once()


# ==================== 血缘追踪测试 ====================

@pytest.mark.asyncio
async def test_lineage_tracking(governed_hermes, mock_db):
    """测试血缘追踪"""

    with patch('app.services.lineage_service.DataLineageService') as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.create_lineage = AsyncMock()

        input_data = {"id": "input_123", "text": "input"}
        output_data = {"id": "output_456", "text": "output"}

        await governed_hermes._record_stage_lineage(
            db=mock_db,
            project_id=1,
            stage_name="test_stage",
            input_data=input_data,
            output_data=output_data,
            user_id=123
        )

        # 验证血缘记录被创建
        mock_instance.create_lineage.assert_called_once()


@pytest.mark.asyncio
async def test_extract_id(governed_hermes):
    """测试 ID 提取"""

    # 测试标准 ID 字段
    data1 = {"id": "123", "text": "test"}
    assert governed_hermes._extract_id(data1) == "123"

    data2 = {"packet_id": "packet_456", "text": "test"}
    assert governed_hermes._extract_id(data2) == "packet_456"

    data3 = {"document_id": "doc_789", "text": "test"}
    assert governed_hermes._extract_id(data3) == "doc_789"

    # 测试无 ID 的情况（应返回哈希）
    data4 = {"text": "test"}
    result = governed_hermes._extract_id(data4)
    assert result is not None


# ==================== 数据包处理测试 ====================

@pytest.mark.asyncio
async def test_create_governed_packet(governed_hermes, mock_db, sample_data):
    """测试创建治理化数据包"""

    with patch.object(governed_hermes, '_record_audit') as mock_audit:
        mock_audit.return_value = AsyncMock()

        packet = await governed_hermes.create_governed_packet(
            stage_name="test_stage",
            data=sample_data,
            project_id=1,
            user_id=123,
            db=mock_db
        )

        # 验证数据包创建
        assert packet is not None
        assert packet.project_id == 1
        assert packet.stage_name == "test_stage"
        assert packet.data == sample_data

        # 验证审计日志被调用
        mock_audit.assert_called_once()


@pytest.mark.asyncio
async def test_execute_governed_stage(governed_hermes, mock_db, sample_data):
    """测试执行治理化阶段"""

    # 注册测试阶段
    async def test_handler(data: Dict, project_id: int, db: Session, **kwargs):
        return {"status": "processed", **data}

    governed_hermes.register_governed_stage(
        name="execution_test_stage",
        handler=test_handler
    )

    # 创建数据包
    packet = await governed_hermes.create_packet(
        stage_name="execution_test_stage",
        data=sample_data,
        project_id=1
    )

    # 执行阶段
    with patch.object(governed_hermes, '_record_audit') as mock_audit:
        mock_audit.return_value = AsyncMock()

        result = await governed_hermes.execute_governed_stage(
            packet_id=packet.packet_id,
            stage_name="execution_test_stage",
            db=mock_db,
            user_id=123
        )

        # 验证结果
        assert result is not None
        assert result["status"] == "processed"
        assert "document_id" in result


# ==================== 血缘查询测试 ====================

@pytest.mark.asyncio
async def test_get_packet_lineage(governed_hermes, mock_db):
    """测试获取数据包血缘"""

    with patch('app.services.lineage_service.DataLineageService') as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.get_upstream_lineage = AsyncMock(return_value=[
            {"source_id": "upstream_1", "operation": "stage_1"}
        ])
        mock_instance.get_downstream_lineage = AsyncMock(return_value=[
            {"target_id": "downstream_1", "operation": "stage_2"}
        ])

        lineage = await governed_hermes.get_packet_lineage(
            packet_id="test_packet",
            db=mock_db,
            depth=5
        )

        # 验证返回结构
        assert "packet_id" in lineage
        assert "upstream" in lineage
        assert "downstream" in lineage
        assert "stages" in lineage
        assert len(lineage["upstream"]) == 1
        assert len(lineage["downstream"]) == 1


# ==================== 审计查询测试 ====================

@pytest.mark.asyncio
async def test_get_stage_audit_trail(governed_hermes, mock_db):
    """测试获取阶段审计轨迹"""

    with patch('app.services.audit_service.AuditService.get_logs') as mock_get_logs:
        mock_log = Mock()
        mock_log.to_dict.return_value = {
            "action": "EXECUTE",
            "stage": "test_stage",
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_get_logs.return_value = AsyncMock(return_value=[mock_log])

        trail = await governed_hermes.get_stage_audit_trail(
            stage_name="test_stage",
            project_id=1,
            db=mock_db,
            limit=100
        )

        # 验证审计轨迹
        assert isinstance(trail, list)


# ==================== 集成测试 ====================

@pytest.mark.asyncio
async def test_full_workflow_integration(governed_hermes, mock_db):
    """测试完整工作流集成"""

    # 注册工作流阶段
    @governed_stage(
        stage_name="stage_1",
        next_stages=["stage_2"]
    )
    async def stage_1_handler(data: Dict, project_id: int, db: Session):
        return {"stage": 1, **data}

    @governed_stage(
        stage_name="stage_2"
    )
    async def stage_2_handler(data: Dict, project_id: int, db: Session):
        return {"stage": 2, **data}

    # Mock 所有治理服务
    with patch('app.services.audit_service.AuditService.create_log') as mock_audit, \
         patch('app.services.lineage_service.DataLineageService') as mock_lineage_service:

        mock_audit.return_value = AsyncMock()
        mock_lineage_instance = mock_lineage_service.return_value
        mock_lineage_instance.create_lineage = AsyncMock()

        # 创建数据包
        packet = await governed_hermes.create_governed_packet(
            stage_name="stage_1",
            data={"input": "test"},
            project_id=1,
            user_id=123,
            db=mock_db
        )

        # 执行阶段 1
        result_1 = await governed_hermes.execute_governed_stage(
            packet_id=packet.packet_id,
            stage_name="stage_1",
            db=mock_db,
            user_id=123
        )

        assert result_1["stage"] == 1

        # 执行阶段 2
        result_2 = await governed_hermes.execute_governed_stage(
            packet_id=packet.packet_id,
            stage_name="stage_2",
            db=mock_db,
            user_id=123
        )

        assert result_2["stage"] == 2


# ==================== 性能测试 ====================

@pytest.mark.asyncio
async def test_governance_overhead(governed_hermes, mock_db):
    """测试治理开销"""
    import time

    async def dummy_handler(data: Dict, project_id: int, db: Session):
        await asyncio.sleep(0.001)  # 模拟处理时间
        return data

    # 注册阶段
    governed_hermes.register_governed_stage(
        name="perf_test_stage",
        handler=dummy_handler
    )

    # 创建数据包
    packet = await governed_hermes.create_packet(
        stage_name="perf_test_stage",
        data={"test": "data"},
        project_id=1
    )

    # Mock 治理服务
    with patch('app.services.audit_service.AuditService.create_log') as mock_audit, \
         patch('app.services.lineage_service.DataLineageService') as mock_lineage:

        mock_audit.return_value = AsyncMock()
        mock_lineage_instance = mock_lineage.return_value
        mock_lineage_instance.create_lineage = AsyncMock()

        # 测试执行时间
        start = time.time()
        await governed_hermes.execute_governed_stage(
            packet_id=packet.packet_id,
            stage_name="perf_test_stage",
            db=mock_db,
            user_id=123
        )
        duration = time.time() - start

        # 治理开销应该小于 100ms
        assert duration < 0.1


# ==================== 错误处理测试 ====================

@pytest.mark.asyncio
async def test_stage_execution_error_handling(governed_hermes, mock_db):
    """测试阶段执行错误处理"""

    async def failing_handler(data: Dict, project_id: int, db: Session):
        raise ValueError("Intentional error")

    governed_hermes.register_governed_stage(
        name="failing_stage",
        handler=failing_handler
    )

    packet = await governed_hermes.create_packet(
        stage_name="failing_stage",
        data={"test": "data"},
        project_id=1
    )

    with patch('app.services.audit_service.AuditService.create_log') as mock_audit:
        mock_audit.return_value = AsyncMock()

        # 执行应该抛出异常
        with pytest.raises(ValueError):
            await governed_hermes.execute_governed_stage(
                packet_id=packet.packet_id,
                stage_name="failing_stage",
                db=mock_db,
                user_id=123
            )

        # 但审计日志仍应记录（包含错误信息）
        mock_audit.assert_called()


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
